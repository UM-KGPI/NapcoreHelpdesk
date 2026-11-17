"""Concepts of the ontology on the indexed pieces, and the pieces that carry a question's concepts by meaning.

Step 3 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md (design point 6, first and second part).

At indexing, each piece gets the classes of the ontology it is about, stored beside it in
structured_metadata["concepts"] (no new embedding):
- an XML example piece: the elements opened in its body that are classes of its standard (netex:StopPlace for
  <StopPlace ...> in a NeTEx example); the line of place and the summary stored after the body do not count;
- a schema declaration: the declared name, when it is a class of its standard;
- any other piece (prose, and a declaration besides its name): the classes whose label occurs in its text, kept
  only when the class is among the NEAREST_CONCEPTS classes nearest to the piece by meaning (the piece's stored
  vector against the concept vectors of services/concept_vectors.py), so a label word used in passing does not
  count.
Each class also brings the Transmodel class it is aligned to, so a question's Transmodel concept finds the pieces
of every standard that implements it.

At the question, with RETRIEVAL_CONCEPT_LABELS on, the QUESTION_CONCEPTS classes nearest to the question's
subject by meaning (in the standards of the scope) are found for every question, and the pieces that carry them,
nearest to the question first, are the graph candidates. This replaces the search of paths and labels by label
words (retrieval_gateway._graph_concept_candidates). Off by default: retrieval is as before.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-17  |  Modified: 2026-11-17
"""

from __future__ import annotations

import logging
import re
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

META_KEY = "concepts"
# A label word counts on a piece only when its class is among this many classes nearest to the piece by meaning.
NEAREST_CONCEPTS = 20
# The classes nearest to a question's subject by meaning whose pieces become candidates.
QUESTION_CONCEPTS = 5

# A standard's name in standards_scope -> the prefix of its classes in the ontology.
SCOPE_CONCEPT_PREFIX = {"netex": "netex", "siri": "siri", "opra": "opra", "tn-its": "tnits"}
_OPENED_ELEMENT = re.compile(r"<([A-Z][A-Za-z0-9_]*)[\s>/]")


def enabled() -> bool:
    return bool(getattr(settings, "RETRIEVAL_CONCEPT_LABELS", False))


def _is_class(concept_id: str) -> bool:
    local = concept_id.split(":", 1)[-1]
    return bool(local) and local[0].isupper()


def scope_prefixes(scope: list[str] | None) -> list[str]:
    """The concept prefixes of the standards named in a scope (["NeTEx", "SIRI"] -> ["netex", "siri"])."""
    return sorted({SCOPE_CONCEPT_PREFIX[s.strip().lower()] for s in scope or [] if (s or "").strip().lower() in SCOPE_CONCEPT_PREFIX})


def piece_body(text: str, structured_metadata: dict | None) -> str:
    """The body of a piece of the prepared cut (without the line of place before it and the summary after it);
    the whole text for any other chunk."""
    from helpdesk.services.prepared_cut import META_KEY as PIECE_KEY

    meta = (structured_metadata or {}).get(PIECE_KEY)
    if isinstance(meta, dict) and isinstance(meta.get("body"), list) and len(meta["body"]) == 2:
        start, end = meta["body"]
        return text[int(start) : int(end)]
    return text


def with_transmodel(concepts: set[str]) -> set[str]:
    """The classes and the Transmodel classes they are aligned to."""
    from helpdesk.services.semantic_graph import CONCEPT_TO_TRANSMODEL

    return concepts | {CONCEPT_TO_TRANSMODEL[c] for c in concepts if c in CONCEPT_TO_TRANSMODEL}


def element_concepts(body: str, prefixes: list[str], known: set[str] | dict) -> set[str]:
    """Classes of the given standards named by the elements opened in an XML body."""
    names = set(_OPENED_ELEMENT.findall(body or ""))
    return {f"{p}:{n}" for n in names for p in prefixes if f"{p}:{n}" in known}


def piece_concepts(
    *,
    text: str,
    doc_type: str,
    chunk_type: str,
    standards_scope: list[str] | None,
    structured_metadata: dict | None,
    nearest: set[str] | None,
    known: set[str] | dict,
    label_concepts=None,
) -> list[str]:
    """The classes a piece is about (see the module docstring), sorted.

    nearest: the NEAREST_CONCEPTS classes nearest to the piece by meaning (None: no vector, no label words);
    known: the ontology's concept ids; label_concepts(text, scope) -> concepts whose label occurs in the text
    (semantic_graph.extract_graph_concepts by default)."""
    prefixes = scope_prefixes(standards_scope)
    body = piece_body(text, structured_metadata)
    if doc_type == "example" and chunk_type == "schema_fragment":
        return sorted(with_transmodel(element_concepts(body, prefixes, known)))
    found: set[str] = set()
    declared = (((structured_metadata or {}).get("schema") or {}).get("declarationName") or "").strip()
    if declared:
        found |= {f"{p}:{declared}" for p in prefixes if f"{p}:{declared}" in known}
    if nearest:
        if label_concepts is None:
            from helpdesk.services.semantic_graph import extract_graph_concepts

            label_concepts = lambda t, scope: extract_graph_concepts(t, scope=scope)  # noqa: E731
        from helpdesk.services.semantic_graph import CONCEPT_TO_TRANSMODEL

        for concept in label_concepts(body, list(standards_scope or [])):
            if _is_class(concept) and (concept in nearest or CONCEPT_TO_TRANSMODEL.get(concept) in nearest):
                found.add(concept)
    return sorted(with_transmodel({c for c in found if _is_class(c)}))


# The concept vectors in memory: (ids, standards, implemented_by, unit-length matrix). Read once per process;
# the index changes only when the ontology does (build_concept_vectors), and a new process reads it again.
_INDEX: tuple | None = None
_INDEX_LOCK = threading.Lock()


def concept_index():
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    with _INDEX_LOCK:
        if _INDEX is None:
            import numpy as np

            from helpdesk.models import ConceptVector

            rows = list(ConceptVector.objects.exclude(vector=None).values_list("concept_id", "standard", "implemented_by", "vector"))
            if not rows:
                return None
            matrix = np.array([np.asarray(r[3], dtype=np.float32) for r in rows])
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            _INDEX = ([r[0] for r in rows], [r[1] for r in rows], [list(r[2] or []) for r in rows], matrix / norms)
    return _INDEX


def nearest_concepts(vector, count: int, prefixes: list[str] | None = None) -> list[str]:
    """The `count` classes nearest to a vector, best first; with prefixes, only classes that concern those
    standards (a standard's own class, or a Transmodel class one of them implements)."""
    import numpy as np

    index = concept_index()
    if index is None or vector is None:
        return []
    ids, standards, implemented, matrix = index
    v = np.asarray(list(vector)[: matrix.shape[1]], dtype=np.float32)
    norm = float(np.linalg.norm(v))
    if norm == 0.0:
        return []
    order = np.argsort(-(matrix @ (v / norm)))
    found = []
    for i in order:
        if prefixes and not (
            standards[i] in prefixes or any(c.split(":", 1)[0] in prefixes for c in implemented[i])
        ):
            continue
        found.append(ids[i])
        if len(found) >= count:
            break
    return found


def question_concepts(question: str, scope: list[str] | None) -> set[str]:
    """The concepts a question is about by meaning: the QUESTION_CONCEPTS classes nearest to its subject in the
    standards of the scope (every standard when the scope names none), with the classes that implement them and
    the Transmodel classes they are aligned to. Empty without the embedder or the concept index."""
    from helpdesk.services.concept_vectors import _embed, index_complete, question_subject

    try:
        if not index_complete() or concept_index() is None:
            return set()
        vector = _embed([question_subject(question)], "query")[0]
    except Exception as exc:  # the embedder or the index unavailable: no candidates by meaning
        logger.info("concepts by meaning unavailable: %s", exc)
        return set()
    prefixes = scope_prefixes(scope)
    ids, _standards, implemented, _matrix = concept_index()
    implemented_by = dict(zip(ids, implemented))
    found: set[str] = set()
    for concept in nearest_concepts(vector, QUESTION_CONCEPTS, prefixes or None):
        found.add(concept)
        found |= {c for c in implemented_by.get(concept, []) if not prefixes or c.split(":", 1)[0] in prefixes}
    return with_transmodel(found)


def labelled_candidates(concepts: set[str], query_embedding, scope: list[str] | None, limit: int, per_file: int) -> list:
    """The pieces in scope that carry any of the concepts, nearest to the query first, at most per_file from one
    file and limit in all."""
    from helpdesk.models import SourceChunk
    from helpdesk.services.retrieval_gateway import _nearest_ids_by_index, _scope_query_filter

    if not concepts or limit <= 0:
        return []
    filtered = SourceChunk.objects.filter(_scope_query_filter(scope)).filter(
        **{f"structured_metadata__{META_KEY}__has_any_keys": sorted(concepts)}
    )
    ids = _nearest_ids_by_index(filtered, query_embedding, limit * 2)
    if ids is None:  # the index search switched off: the exact order
        from pgvector.django import CosineDistance

        ids = list(filtered.order_by(CosineDistance("embedding_vector", list(query_embedding))).values_list("id", flat=True)[: limit * 4])
    rows = SourceChunk.objects.in_bulk(ids)
    selected, taken = [], {}
    for chunk_id in ids:
        chunk = rows.get(chunk_id)
        if chunk is None:
            continue
        key = (chunk.repository_url, chunk.source_path)
        if per_file > 0 and taken.get(key, 0) >= per_file:
            continue
        taken[key] = taken.get(key, 0) + 1
        selected.append(chunk)
        if len(selected) >= limit:
            break
    return selected
