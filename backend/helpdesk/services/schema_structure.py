"""What an element contains, answered from the NeTEx schema itself.

"What does a StopPlace contain in NeTEx?" has an exact answer in the XSD (StopPlace's own child
elements, those inherited from Site, Zone and so on, and its attributes, each with its definition), but
text retrieval returns the element's definition and incidental mentions, so the model reported it could
not list them (local question req-mw7rpcmi, 2026-11-08). For a question of that shape the structure
comes from the validator's schema index (netex_validator_service.ElementDocs.structure), with no model
involved; the answer text then only adds what the evidence says about using the element.

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

TIMEOUT_SECONDS = 10

_SUBJECT = r"(?P<subject>[A-Za-z][\w]*(?:\s+[A-Za-z][\w]*){0,3}?)"
_ARTICLE = r"(?:a |an |the )?"
_TAIL = r"(?:\s+(?:in|of)\s+netex)?"
_STRUCTURE_QUESTIONS = [
    # "what elements does a StopPlace contain", "which attributes can a Quay have"
    re.compile(
        r"\b(?:what|which)\s+(?:child\s+)?(?:elements?|attributes?|children|fields|properties|parts|contents?)\s+"
        r"(?:does|do|can|may|must|should)\s+" + _ARTICLE + _SUBJECT + r"\s+(?:contain|have|include|hold|consist of)",
        re.I,
    ),
    # "what does a StopPlace contain", "what can a VehicleType include"
    re.compile(r"\bwhat\s+(?:does|do|can|may)\s+" + _ARTICLE + _SUBJECT + r"\s+(?:contain|consist of|include|hold)\b", re.I),
    # "elements of a StopPlace", "structure of StopPlace", "children of Quay", "attributes of a Line"
    re.compile(
        r"\b(?:child\s+elements?|elements?|attributes?|children|structure|content model|contents?)\s+of\s+"
        + _ARTICLE + _SUBJECT + _TAIL + r"\s*\??\s*$",
        re.I,
    ),
    # "what is inside a StopPlace", "what is contained in a ServiceJourney", "what goes into a Quay"
    re.compile(
        r"\bwhat(?:\s+is|'s|\s+are)?\s+(?:inside|in|contained\s+in|included\s+in|part\s+of|goes\s+(?:into|in))\s+"
        + _ARTICLE + _SUBJECT + _TAIL + r"\s*\??\s*$",
        re.I,
    ),
    # "what a StopPlace contains", "what an Operator consists of"
    re.compile(r"\bwhat\s+" + _ARTICLE + _SUBJECT + r"\s+(?:contains|includes|holds|consists\s+of|is\s+made\s+of)\b", re.I),
    # "which elements are in a StopPlace", "what attributes are part of a Line"
    re.compile(
        r"\b(?:what|which)\s+(?:child\s+)?(?:elements?|attributes?|children|fields|properties|parts)\s+(?:are|exist|belong)\s+"
        r"(?:in|inside|part\s+of|under|to)\s+" + _ARTICLE + _SUBJECT + _TAIL + r"\s*\??\s*$",
        re.I,
    ),
]
_STRIP_WORDS = frozenset({"element", "elements", "in", "netex", "the", "a", "an"})


def structure_subject(question: str) -> str | None:
    """The thing the question asks the content of, as written ("StopPlace", "stop place"); None when the
    question is not of that shape."""
    text = (question or "").strip()
    for pattern in _STRUCTURE_QUESTIONS:
        match = pattern.search(text)
        if match:
            words = [w for w in match.group("subject").split() if w.lower() not in _STRIP_WORDS]
            return " ".join(words) or None
    return None


def candidate_element_names(subject: str) -> list[str]:
    """Element names the subject may denote, most likely first: the identifier as written, the model
    concept whose label it is (stop place -> StopPlace), and the words joined in CamelCase."""
    from helpdesk.services.semantic_graph import GRAPH_CONCEPT_ALIASES, _normalize_for_matching

    names: list[str] = []
    words = subject.split()
    if len(words) == 1 and words[0][:1].isupper():
        names.append(words[0])
    normalized = _normalize_for_matching(subject)
    for concept_id, labels in GRAPH_CONCEPT_ALIASES.items():
        if any(normalized == _normalize_for_matching(label) for label in labels):
            local = concept_id.rsplit(":", 1)[-1]
            if local not in names:
                names.append(local)
    joined = "".join(word[:1].upper() + word[1:] for word in words)
    if joined not in names:
        names.append(joined)
    return names


def fetch_structure(element: str) -> dict | None:
    """The validator's /structure answer for a known element, else None (unknown, or validator down)."""
    from urllib import error, parse, request

    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/structure?" + parse.urlencode({"element": element})
    try:
        with request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("schema structure not available: %s", exc)
        return None
    if not payload.get("found"):
        return None
    payload.pop("found", None)
    return payload


def schema_structure_for(question: str, scope: list[str] | None, english_question: str | None = None) -> dict | None:
    """The schema structure block for a "what does X contain" question in NeTEx scope, else None."""
    if not getattr(settings, "SCHEMA_STRUCTURE_ENABLED", True):
        return None
    # The index is NeTEx's: not for a question scoped to other standards only. An unscoped question gets
    # the block when the element exists in NeTEx (the block says which schema it comes from).
    names = {(name or "").strip().lower() for name in scope or []}
    if names and "netex" not in names:
        return None
    # Another language ("Kaj vsebuje StopPlace?") is recognised on the English rendering made for retrieval.
    subject = structure_subject(question) or structure_subject(english_question or "")
    if not subject:
        return None
    for element in candidate_element_names(subject):
        structure = fetch_structure(element)
        if structure:
            structure.pop("found", None)
            return structure
    return None


def definition_chunk(element: str) -> dict | None:
    """The indexed chunk of the schema file that defines the element (its xsd:documentation is in it), as an
    evidence block: for "How do you describe a stop place?" next to an example, the definition can then be
    quoted and cited. None when the element or its chunk is not found."""
    structure = fetch_structure(element)
    documentation = ((structure or {}).get("documentation") or "").strip()
    if not structure or not structure.get("source") or len(documentation) < 12:
        return None
    from helpdesk.models import SourceChunk
    from helpdesk.services.retrieval_gateway import _added_candidate

    probe = " ".join(documentation.split()[:6])
    in_file = SourceChunk.objects.filter(source_path=structure["source"])
    chunk = (
        # The element's own declaration first: two elements can share their documentation (VehicleType and
        # VehicleModel), and the probe alone gave VehicleModel's block for VehicleType.
        in_file.filter(text__contains=f"element {element}\n").order_by("chunk_id").first()
        or in_file.filter(text__contains=probe).order_by("chunk_id").first()
        or in_file.filter(text__contains=element).order_by("chunk_id").first()
    )
    return _added_candidate(chunk, 1.0) if chunk else None
