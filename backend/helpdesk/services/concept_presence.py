"""Evidence for "does the standard have X?" questions, from the model and the schema.

"Does a bus have drivers name described in NeTEx?" (prod req-mw804y0v, 2026-11-08) is answered by the
model itself: Transmodel defines DRIVER as "An EMPLOYEE whose usual work is to drive a public transport
vehicle", no NeTEx class is aligned to it, and NeTEx has only a DriverRef on dated journeys (plus the
driver-scheduling classes DriverTrip, DriverScheduleFrame). Text retrieval found bus timetable examples
instead, and the question's "drivers" did not match the label DRIVER (one-word plurals are left out of
retrieval on purpose: they crowded out the right chunks, benchmark 2026-10-25).

For a question of that shape only, the concept is recognised with plurals and its definition (which states
which standards implement it) and the definitions of the schema elements named after it go first among the
evidence. Retrieval ranking is not touched.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-08  |  Modified: 2026-11-08
"""

from __future__ import annotations

import json
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

MAX_ELEMENTS = 2
MAX_CONCEPTS = 2
TIMEOUT_SECONDS = 10

# "Does NeTEx have …", "Is there a … in NeTEx", "Can NeTEx describe …", "Does a bus have drivers name described"
_ASKS_WHETHER = re.compile(
    r"^\s*(?:does|do|did|is|are|can|could|may)\b.*\b(?:have|has|describe[sd]?|support[s]?|model(?:led|s)?|contain[s]?"
    r"|include[sd]?|cover[s]?|represent(?:ed|s)?|express(?:ed)?|exist[s]?|there|define[sd]?|allow[s]?)\b",
    re.I,
)


# "How can fare distribution be defined in NeTEx?", "How do you describe a parking in NeTEx?"
_ASKS_HOW = re.compile(
    r"^\s*how\s+(?:can|could|do|does|did|should|would|is|are|to)\b.*\b(?:define[sd]?|describe[sd]?|model(?:led|s)?"
    r"|represent(?:ed|s)?|encode[sd]?|express(?:ed)?|specif(?:y|ied)|modell?ing)\b",
    re.I,
)


def asks_whether_modelled(question: str) -> bool:
    """A yes/no question about whether something is in the standard."""
    return bool(_ASKS_WHETHER.search(question or ""))


def question_kind(question: str) -> str:
    """"whether" for "does the standard have X?", "how" for "how is X defined in the standard?", else ""."""
    if _ASKS_HOW.search(question or ""):
        return "how"
    return "whether" if asks_whether_modelled(question) else ""


_NOT_PLURAL = frozenset({"does", "goes", "this", "yes", "has", "was", "its", "always", "towards", "whereas", "news", "series", "species"})


def _singular(word: str) -> str:
    lowered = word.lower()
    if len(lowered) <= 3 or lowered in _NOT_PLURAL or lowered.endswith(("ss", "us", "is")):
        return word
    if lowered.endswith("ies"):
        return word[:-3] + "y"
    if lowered.endswith(("ches", "shes", "xes", "sses")):
        return word[:-2]
    if lowered.endswith("s"):
        return word[:-1]
    return word


def singular_question(question: str) -> str:
    """The question with its words in the singular ("drivers name" -> "driver name"), for concept lookup."""
    return re.sub(r"[A-Za-z]+", lambda m: _singular(m.group(0)), question or "")


def _is_class(concept_id: str) -> bool:
    local = concept_id.split(":", 1)[-1]
    return bool(local) and local[0].isupper() and concept_id not in {"netex:NeTEx", "siri:SIRI", "opra:OpRa"}


_QUESTION_WORDS = frozenset(
    "how can could does did should would define defined describe described model modelled models represent "
    "represented encode encoded express expressed specify specified there have has support netex siri opra "
    "transmodel standard element elements class classes data example examples which what where when your".split()
)


def head_word_concepts(question: str, standard: str = "netex", limit: int = 2) -> list[str]:
    """Transmodel classes named by a word that is no full label: those whose label begins with the word and
    that the standard implements ("fare distribution": DISTRIBUTION CHANNEL, DISTRIBUTION ASSIGNMENT). Of
    the question's words, the most specific one is used (the fewest such classes: "distribution", not
    "fare", which begins dozens), and of its classes the shortest labels."""
    from helpdesk.services.semantic_graph import GRAPH_CONCEPT_ALIASES, TRANSMODEL_TO_CONCEPTS

    words = [w.lower() for w in re.findall(r"[A-Za-z]+", singular_question(question)) if len(w) >= 3 and w.lower() not in _QUESTION_WORDS]
    best: list[str] | None = None
    for word in dict.fromkeys(words):
        heads = sorted(
            (
                concept
                for concept, labels in GRAPH_CONCEPT_ALIASES.items()
                if concept.startswith("transmodel:") and _is_class(concept)
                and any(label.lower().split()[:1] == [word] for label in labels)
                and any(c.startswith(f"{standard}:") for c in TRANSMODEL_TO_CONCEPTS.get(concept, ()))
            ),
            key=lambda c: (c.count("_"), c),
        )
        if heads and (best is None or len(heads) < len(best)):
            best = heads
    return (best or [])[:limit]


def _labelled_concepts(question: str) -> list[str]:
    """Classes whose full label the question names (plurals too), most specific first, as Transmodel classes."""
    from helpdesk.services.semantic_graph import CONCEPT_TO_TRANSMODEL, extract_graph_concepts

    found = extract_graph_concepts(singular_question(question)) | extract_graph_concepts(question)
    transmodel = set()
    for concept in found:
        if not _is_class(concept):
            continue
        tm = concept if concept.startswith("transmodel:") else CONCEPT_TO_TRANSMODEL.get(concept)
        if tm:
            transmodel.add(tm)
    # The most specific first, judged on the Transmodel names: DRIVER TRIP before DRIVER.
    return sorted(transmodel, key=lambda c: (-c.count("_"), -len(c), c))


SEMANTIC_AGREEMENT_DEPTH = 20


def presence_concepts(question: str, kind: str | None = None) -> list[str]:
    """The classes the question is about, best first.

    Measured on benchmarks/concept-questions.yaml (26 questions, paraphrases and other languages; hit@3):
    label words 0.35, semantic on the whole question 0.46, semantic on the question's subject 0.81, the
    order below 0.88. Concepts named by label words (or by the head-word rule) count only when the meaning
    agrees: they are among the classes nearest to the subject by meaning. An existence question names the
    thing itself ("does a bus have a driver's name?"), so there the most specific label named literally
    goes first. The nearest classes by meaning fill the rest. Without the embedder or the concept index,
    label words and the head-word rule, as before.
    """
    from helpdesk.services.concept_vectors import question_subject, semantic_concepts
    from helpdesk.services.semantic_graph import CONCEPT_TO_TRANSMODEL

    labelled = _labelled_concepts(question)
    nearest = [
        c["concept_id"] if c["concept_id"].startswith("transmodel:") else CONCEPT_TO_TRANSMODEL.get(c["concept_id"], c["concept_id"])
        for c in semantic_concepts(question_subject(question), limit=SEMANTIC_AGREEMENT_DEPTH)
    ]
    if not nearest:
        return labelled or head_word_concepts(question)
    kind = kind if kind is not None else question_kind(question)
    agreeing = [c for c in (labelled or head_word_concepts(question)) if c in nearest]
    ordered = (labelled[:1] if kind == "whether" else []) + agreeing + nearest
    return list(dict.fromkeys(ordered))


def _element_names(word: str) -> list[str]:
    """Schema elements named after the concept (StopPlaceEntrance -> StopPlaceEntrance, StopPlaceEntranceRef;
    Driver -> DriverRef, DriverTrip, DriverScheduleFrame): its own name and reference first when they
    exist, then other objects named after it, then other references."""
    from urllib import error, parse, request

    from helpdesk.services.schema_structure import fetch_structure

    own = [name for name in (word, f"{word}Ref") if fetch_structure(name)]
    words = re.findall(r"[A-Z][a-z]+", word) or [word]
    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/declarations?" + parse.urlencode({"q": " ".join(words)})
    try:
        with request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            declarations = json.loads(response.read()).get("declarations") or []
    except (error.URLError, OSError, ValueError):
        declarations = []
    # "_Dummy" elements are the schema's abstract substitution-group heads (FareProduct_Dummy), not elements to use.
    named = [d for d in declarations if word.lower() in d["name"].lower() and d["name"] not in own and not d["name"].endswith("_Dummy")]
    named.sort(key=lambda d: (not d.get("object"), d["name"].endswith("Ref"), len(d["name"])))
    return list(dict.fromkeys(own + [d["name"] for d in named]))


def presence_evidence(question: str, scope: list[str] | None, english_question: str | None = None) -> list[dict]:
    """Evidence chunks for "does the standard have X?" and "how is X defined in the standard?": the
    Transmodel definition of X (with which standards implement it) and the definitions of the schema elements
    named after X; for up to two concepts. [] for other questions."""
    if not getattr(settings, "CONCEPT_PRESENCE_ENABLED", True):
        return []
    text = english_question or question
    if not question_kind(text):
        return []
    names = {(name or "").strip().lower() for name in scope or []}
    if names and "netex" not in names:
        return []
    concepts = presence_concepts(text)[:MAX_CONCEPTS]
    if not concepts:
        return []
    chunks: list[dict] = []
    try:
        from helpdesk.services.retrieval_gateway import format_definitions_as_chunks, indexed_commit_shas, retrieve_concept_definitions

        definitions = retrieve_concept_definitions(
            concept_ids=set(concepts),
            endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
            repository=settings.GRAPHDB_REPOSITORY,
            timeout_seconds=max(1, settings.GRAPHDB_TIMEOUT_SECONDS - 1),
            username=getattr(settings, "GRAPHDB_USER", ""),
            password=getattr(settings, "GRAPHDB_PASSWORD", ""),
        )
        formatted = format_definitions_as_chunks(definitions or [], commit_shas=indexed_commit_shas())
        # The Transmodel definition (it names the implementing class); a standard's own class has none.
        transmodel_defs = [c for c in formatted if "transmodel" in str(c.get("sourcePath", "")).lower()]
        chunks += (transmodel_defs or formatted)[: len(concepts)]
    except Exception as exc:  # the graph unavailable: the schema part still helps
        logger.info("concept definition not available: %s", exc)
    from helpdesk.services.schema_structure import definition_chunk

    # With one concept, its two main elements; with two, one element each.
    per_concept = MAX_ELEMENTS if len(concepts) == 1 else 1
    for concept in concepts:
        word = "".join(part.capitalize() for part in concept.split(":", 1)[1].split("_"))  # STOP_PLACE -> StopPlace
        added = 0
        for name in _element_names(word)[: per_concept * 2]:
            chunk = definition_chunk(name)
            if chunk and chunk["chunkId"] not in {c.get("chunkId") for c in chunks}:
                chunks.append(chunk)
                added += 1
            if added >= per_concept:
                break
    for chunk in chunks:
        chunk.setdefault("retrievalEventId", f"re-presence-{abs(hash(chunk.get('chunkId'))) % 10**8}")
        # Put first on purpose, like the schema's own blocks: the answer's confidence is read from the first
        # block's score, and a definition block without one dropped it to the 0.6 floor.
        if not chunk.get("score"):
            chunk["score"] = 1.0
    return chunks
