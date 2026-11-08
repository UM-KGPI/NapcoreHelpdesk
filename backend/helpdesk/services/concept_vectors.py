"""The ontology's classes found by meaning: "Where can a passenger buy tickets?" -> DISTRIBUTION CHANNEL.

Concept recognition matched label words (services/semantic_graph.py): "fare distribution" named no class, and
a paraphrase shares no word with any label. Here every class of the ontology (Transmodel, NeTEx, SIRI, OpRa,
TN-ITS) is embedded once, from its label, alternative labels and definition, with the same semantic embedder
retrieval uses; a question is matched to the nearest classes, constrained by the graph (a standard's own
classes, or Transmodel classes the standard implements).

Built by build_concept_vectors() (management command build_concept_vectors, the Celery task of the same
name at worker start and after the nightly source refresh). Without the embedder or the index, nothing is
returned and the callers keep their word matching.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-08  |  Modified: 2026-11-08
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

DIMENSION = 384
# The embedder also serves every question's search, one request at a time. A build batch makes questions wait
# behind it (prod 2026-11-08: 16 per batch kept the embedder at 2 CPUs and a question took 54 s instead of
# 14 s), so batches are small and each is followed by a pause as long as it took: the build uses at most
# about half of the embedder's time. A full build is a one-off; later builds embed only changed classes.
EMBED_BATCH = 4
BUILD_PAUSE_FACTOR = 1.0
_CLASSES_QUERY = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?c (MIN(?label) AS ?l) (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?alts) (MIN(?definition) AS ?d)
WHERE {
  ?c a owl:Class .
  OPTIONAL { ?c rdfs:label ?label }
  OPTIONAL { ?c skos:altLabel ?alt }
  OPTIONAL { { ?c rdfs:comment ?definition } UNION { ?c skos:definition ?definition } }
} GROUP BY ?c"""


def _readable(local_name: str) -> str:
    """DISTRIBUTION_CHANNEL -> "distribution channel", DistributionChannel -> "distribution channel"."""
    if "_" in local_name or local_name.isupper():
        return local_name.replace("_", " ").lower()
    return " ".join(re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", local_name)).lower()


def concept_text(label: str, alt_labels: list[str], definition: str) -> str:
    """What is embedded for a class: its name, other names and definition."""
    names = list(dict.fromkeys(n for n in [label, *alt_labels] if n))
    return f"{'; '.join(names)}. {definition}".strip()


def _sparql(query: str) -> list[dict]:
    request = urllib.request.Request(
        settings.GRAPHDB_SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": query}),
        headers={"Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())["results"]["bindings"]


def ontology_classes() -> list[dict]:
    """Every class of the ontology: {"concept_id", "standard", "label", "alt_labels", "definition", "implemented_by"}."""
    from helpdesk.services.semantic_graph import CONCEPT_TO_TRANSMODEL, TRANSMODEL_TO_CONCEPTS, iri_to_concept_id

    classes = []
    for row in _sparql(_CLASSES_QUERY):
        concept_id = iri_to_concept_id(row["c"]["value"])
        if not concept_id or ":" not in concept_id:
            continue
        standard, local = concept_id.split(":", 1)
        label = (row.get("l") or {}).get("value") or _readable(local)
        # Sorted: GROUP_CONCAT returns them in no fixed order, which changed the text hash between builds.
        alts = sorted({a for a in ((row.get("alts") or {}).get("value") or "").split("|") if a and a.lower() != label.lower()})
        if standard == "transmodel":
            implemented = sorted(TRANSMODEL_TO_CONCEPTS.get(concept_id, ()))
        else:
            # A standard's class is its own implementation; its Transmodel class, when aligned, names it too.
            implemented = [concept_id]
            transmodel = CONCEPT_TO_TRANSMODEL.get(concept_id)
            if transmodel:
                alts.append(_readable(transmodel.split(":", 1)[1]))
        classes.append(
            {
                "concept_id": concept_id,
                "standard": standard,
                "label": label[:255],
                "alt_labels": alts[:6],
                "definition": ((row.get("d") or {}).get("value") or "").strip(),
                "implemented_by": implemented,
            }
        )
    return classes


def _embed(texts: list[str], kind: str) -> list[list[float]]:
    url = settings.EMBEDDING_SERVICE_URL.rstrip("/") + "/embed"
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH):
        body = json.dumps({"texts": texts[start : start + EMBED_BATCH], "kind": kind}).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=getattr(settings, "EMBEDDING_SERVICE_TIMEOUT_SECONDS", 120)) as response:
            vectors += json.loads(response.read())["vectors"]
    return vectors


def build_concept_vectors() -> dict:
    """Bring the index in line with the ontology: embed new and changed classes, remove gone ones."""
    from helpdesk.models import ConceptVector

    classes = ontology_classes()
    if not classes:
        return {"status": "skipped", "reason": "no classes from GraphDB"}
    existing = {row.concept_id: row for row in ConceptVector.objects.all()}
    changed = []
    for item in classes:
        text = concept_text(item["label"], item["alt_labels"], item["definition"])
        item["text"] = text
        item["text_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        row = existing.get(item["concept_id"])
        if row is None or row.text_hash != item["text_hash"] or row.vector is None:
            changed.append(item)
    # Embedded and saved batch by batch: a failure keeps what was done, and the next run continues from there.
    import time

    for start in range(0, len(changed), EMBED_BATCH):
        batch = changed[start : start + EMBED_BATCH]
        started = time.monotonic()
        vectors = _embed([item["text"] for item in batch], "passage")
        if start + EMBED_BATCH < len(changed):
            time.sleep((time.monotonic() - started) * BUILD_PAUSE_FACTOR)
        for item, vector in zip(batch, vectors):
            ConceptVector.objects.update_or_create(
                concept_id=item["concept_id"],
                defaults={
                    "standard": item["standard"],
                    "label": item["label"],
                    "definition": item["definition"],
                    "implemented_by": item["implemented_by"],
                    "text_hash": item["text_hash"],
                    "vector": vector,
                },
            )
    # Alignment changes do not change the text: keep implemented_by current for every class.
    for item in classes:
        row = existing.get(item["concept_id"])
        if row is not None and row.implemented_by != item["implemented_by"] and item not in changed:
            ConceptVector.objects.filter(pk=row.pk).update(implemented_by=item["implemented_by"])
    gone = set(existing) - {item["concept_id"] for item in classes}
    if gone:
        ConceptVector.objects.filter(concept_id__in=gone).delete()
    return {"status": "ok", "classes": len(classes), "embedded": len(changed), "removed": len(gone)}


_FRAME_WORDS = frozenset(
    "how can could do does did is are was were be been being should would will to a an the in of for on at by with "
    "netex siri opra transmodel standard element elements class concept there have has any some you i we one it its "
    "define defined describe described model modelled modeled represent represented encode encoded express expressed "
    "specify specified support supports what which where when who why show me example examples please".split()
)


def question_subject(question: str) -> str:
    """The question without its frame ("How can fare distribution be defined in NeTEx?" -> "fare distribution"):
    the frame dominated a small embedding model's vector."""
    words = re.findall(r"[^\W\d_][\w'-]*", question or "")
    kept = [w for w in words if w.lower() not in _FRAME_WORDS]
    return " ".join(kept) or (question or "")


def index_status() -> dict:
    """How many classes the concept index holds (for /health/ready)."""
    from helpdesk.models import ConceptVector

    try:
        return {"conceptVectors": ConceptVector.objects.exclude(vector=None).count()}
    except Exception:
        return {"conceptVectors": None}


def semantic_concepts(question: str, standard: str = "netex", limit: int = 5, min_similarity: float = 0.0) -> list[dict]:
    """The classes nearest to the question by meaning that concern the standard: its own classes, or Transmodel
    classes it implements. [{"concept_id", "label", "similarity", "implemented_by"}], best first; [] without
    the embedder or the index."""
    from helpdesk.models import ConceptVector

    try:
        from pgvector.django import CosineDistance  # type: ignore
    except Exception:
        return []
    if not (question or "").strip():
        return []
    try:
        if not ConceptVector.objects.exclude(vector=None).exists():
            return []
    except Exception as exc:  # no index yet (a migration still to run) or no database: word matching
        logger.info("concept index unavailable: %s", exc)
        return []
    try:
        query_vector = _embed([question], "query")[0]
    except Exception as exc:  # embedder down: callers keep word matching
        logger.info("semantic concepts unavailable: %s", exc)
        return []
    rows = (
        ConceptVector.objects.exclude(vector=None)
        .annotate(similarity=1.0 - CosineDistance("vector", query_vector))
        .order_by("-similarity")[: limit * 8]
    )
    found = []
    for row in rows:
        concerns = row.standard == standard or any(c.startswith(f"{standard}:") for c in row.implemented_by or [])
        if not concerns or row.similarity < min_similarity:
            continue
        found.append({"concept_id": row.concept_id, "label": row.label, "similarity": round(float(row.similarity), 4), "implemented_by": row.implemented_by})
        if len(found) >= limit:
            break
    return found
