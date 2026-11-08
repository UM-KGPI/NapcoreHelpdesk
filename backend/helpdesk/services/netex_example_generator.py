"""NeTEx XML fragments generated for a question, validated against the NeTEx XSD.

"Show an example of a bus with 50 seats and 20 standing places" has no verbatim answer in the NeTEx
examples. The model writes one frame from the elements in the evidence (schema definitions and real
examples), the frame is wrapped in a minimal PublicationDelivery and validated against
NeTEx_publication.xsd from the indexed NeTEx checkout, and validator errors go back to the model for
another attempt. Only a fragment that validates and contains the question's values is returned; it is
labelled as generated, never presented as an example from the standard.

XSD validity checks structure, not modelling choices: a valid fragment can still put a value on a
less usual element. The evidence it was built from is cited with it.
"""

from __future__ import annotations

import json
import logging
import re
import time

from django.conf import settings

logger = logging.getLogger(__name__)

SCHEMA_ENTRY = "xsd/NeTEx_publication.xsd"
MAX_ATTEMPTS = 3
MAX_EVIDENCE_CHUNKS = 6
MAX_EVIDENCE_CHARS = 1800
MAX_REPORTED_ERRORS = 5
VALIDATOR_TIMEOUT_SECONDS = 10

_EXAMPLE_WORDS = re.compile(r"\b(?:examples?|samples?|snippets?|fragments?|show\s+(?:me\s+)?(?:how|the\s+xml))\b", re.I)
_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")
# Straight or curly double quotes, in pairs; an apostrophe ("don't") is no quote.
_QUOTED = re.compile(r'"([^"]{1,60})"|“([^”]{1,60})”')
_XML_BLOCK = re.compile(r"<(?P<tag>[A-Za-z][\w.-]*)[\s>].*</(?P=tag)>", re.S)


_NUMBER_WORDS = frozenset(
    "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
    "eighteen nineteen twenty".split()
)
_WORD = re.compile(r"[^\W\d_][\w'-]*|\S")
# Names of standards and formats: capitalised, but never a value of the example.
_NOT_NAMES = frozenset(
    "netex siri opra transmodel gtfs datex xml xsd json yaml epip nordic napcore mobilitydcat dcat inspire tn-its tnits".split()
)
_JOINING_WORDS = frozenset({"de", "la", "le", "van", "von", "der", "di", "del", "na", "pri", "ob", "&"})


def _is_name_word(word: str) -> bool:
    """A capitalised word ("Ljubljana", "LPP"), not an identifier with inner capitals ("VehicleType")."""
    if not word[:1].isupper() or word.lower() in _NOT_NAMES:
        return False
    if word.isupper() and len(word) <= 2:
        return False  # "SX", "ET": service abbreviations, not names
    return word.isupper() or not any(char.isupper() for char in word[1:])


def _is_concept_label(phrase: str) -> bool:
    """Whether the phrase is a model concept's label ("Stop Place"): a type, not a value."""
    from helpdesk.services.semantic_graph import GRAPH_CONCEPT_ALIASES, _normalize_for_matching

    normalized = _normalize_for_matching(phrase)
    return any(normalized == _normalize_for_matching(label) for labels in GRAPH_CONCEPT_ALIASES.values() for label in labels)


def named_values(question: str) -> list[str]:
    """Proper names written without quotes: runs of capitalised words that do not start a sentence
    ("Show me ... for Ljubljana Bus Station with two quays" -> "Ljubljana Bus Station")."""
    words = _WORD.findall(_QUOTED.sub(" . ", question or ""))
    names, current, sentence_start = [], [], True
    for word in words:
        if not sentence_start and (_is_name_word(word) or (current and word.lower() in _JOINING_WORDS)):
            current.append(word)
        else:
            while current and current[-1].lower() in _JOINING_WORDS:
                current.pop()
            if current:
                names.append(" ".join(current))
            current = []
        sentence_start = word in {".", "!", "?", ":"}
    if current:
        names.append(" ".join(current))
    label_words = _concept_label_words()
    return [
        name
        for name in names
        if not _is_concept_label(name) and not (" " not in name and not name.isupper() and name.lower() in label_words)
    ]


def _concept_label_words() -> frozenset[str]:
    """Words of the model concepts' labels: a single capitalised one ("Ferry") is vocabulary, not a name."""
    from helpdesk.services.semantic_graph import GRAPH_CONCEPT_ALIASES, _normalize_for_matching

    aliases = GRAPH_CONCEPT_ALIASES
    cached = getattr(_concept_label_words, "_cache", None)
    if cached is not None and cached[0] == len(aliases):
        return cached[1]
    words = frozenset(word for labels in aliases.values() for label in labels for word in _normalize_for_matching(label).split())
    _concept_label_words._cache = (len(aliases), words)
    return words


def requested_values(question: str) -> list[str]:
    """The concrete values a question gives, each of which the fragment must contain: quoted names,
    numbers, and proper names written without quotes."""
    values = [(straight or curly).strip() for straight, curly in _QUOTED.findall(question or "")]
    values += _NUMBER.findall(_QUOTED.sub(" ", question or ""))
    values += named_values(question)
    return list(dict.fromkeys(value for value in values if value))


def counted_words(question: str) -> list[str]:
    """Number words ("two quays"): concrete for the trigger, but not text the fragment must contain."""
    return [word for word in re.findall(r"[a-z]+", (question or "").lower()) if word in _NUMBER_WORDS]


def wants_generated_example(question: str, scope: list[str] | None) -> bool:
    """A request for a NeTEx example with concrete values ("a bus with 50 seats and 20 standing places")."""
    if not getattr(settings, "NETEX_EXAMPLE_GENERATOR_ENABLED", True):
        return False
    names = {(name or "").strip().lower() for name in scope or []}
    if "netex" not in names and "netex" not in (question or "").lower():
        return False
    if not _EXAMPLE_WORDS.search(question or ""):
        return False
    return bool(requested_values(question) or counted_words(question))


# --- validation (netex-validator service, helpdesk/netex_validator_service.py) -------------------


class ValidatorUnavailable(RuntimeError):
    pass


def validate_fragment(fragment: str) -> dict:
    """{"valid", "errors", "schemaVersion", "commit", "elements"} from the validation service."""
    from urllib import error, request

    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/validate"
    body = json.dumps({"fragment": fragment}).encode("utf-8")
    http_request = request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(http_request, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except error.HTTPError as exc:
        raise ValidatorUnavailable(f"validator answered {exc.code}") from exc
    except (error.URLError, OSError, ValueError) as exc:
        raise ValidatorUnavailable(f"validator unreachable: {exc}") from exc


NETEX_NAMESPACE = "http://www.netex.org.uk/netex"


def _indented(xml: str) -> str:
    """The XML indented two spaces per level. Only for validated fragments: a DOCTYPE inside the
    wrapper makes the document malformed, so these hold no DTD or entities."""
    from xml.dom import minidom

    try:
        pretty = minidom.parseString(xml.encode("utf-8")).toprettyxml(indent="  ")
    except Exception:
        return xml
    lines = [line for line in pretty.splitlines() if line.strip()]
    return "\n".join(lines[1:] if lines and lines[0].startswith("<?xml") else lines)


def indented_fragment(fragment: str) -> str:
    """The frame indented, without a namespace declaration of its own (it sits inside dataObjects)."""
    lines = _indented(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>').splitlines()
    if len(lines) < 3 or not lines[0].startswith("<root"):
        return fragment.strip()
    return "\n".join(line[2:] if line.startswith("  ") else line for line in lines[1:-1])


def publication_document(fragment: str) -> str:
    """The validated document: a minimal PublicationDelivery around the frame (as the validator wraps it)."""
    from helpdesk.netex_validator_service import wrap_fragment

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + _indented(wrap_fragment(fragment)) + "\n"


def element_notes(elements: list[dict]) -> list[dict]:
    """What each element of the fragment is, in the schema's words: one note per element name, the
    first (outermost) occurrence's text. Grounded in the XSD, no model involved."""
    notes: dict[str, str] = {}
    for element in elements or []:
        name, text = str(element.get("name") or ""), str(element.get("documentation") or "").strip()
        if name and text and name not in notes:
            notes[name] = text
    return [{"name": name, "documentation": text} for name, text in notes.items()]


def _field_values(fragment: str) -> set[str] | None:
    """The whole text of every element and attribute of the fragment (None when it does not parse)."""
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return None
    fields: set[str] = set()
    for node in root.iter():
        fields.add((node.text or "").strip())
        fields.update(value.strip() for value in node.attrib.values())
    return fields


def missing_values(fragment: str, values: list[str]) -> list[str]:
    """Requested values that are not the whole content of some element or attribute.

    A value mentioned inside a sentence does not count: "Bus with 50 seats" in a Description leaves
    the seats unmodelled, and the feedback sends the model back to put 50 in an element of its own.
    Only for fragments that validated (no DTD, no entities); an unparsable one falls back to words.
    """
    fields = _field_values(fragment)
    if fields is None:
        return [value for value in values if not re.search(rf"(?<![\w.]){re.escape(value)}(?![\w.])", fragment)]
    return [value for value in values if value not in fields]


# --- generation ----------------------------------------------------------------------------------

_PROMPT = (
    "You write NeTEx XML for a standards helpdesk. Write ONE NeTEx frame (for example a ResourceFrame, "
    "ServiceFrame, SiteFrame or TimetableFrame, with version and id attributes) that shows what the question "
    "asks, using the values it gives. Put each object in the frame the evidence examples put it in (vehicle "
    "types, for example, in a ResourceFrame). Use only element and attribute names that appear in the evidence blocks "
    "(schema definitions and example files), in the order the schema definitions give. Give every element that "
    "needs one a version and an id; use the prefix 'hd:' for ids. Do not add elements the question does not "
    "need. Use only the values the question gives; where the schema needs another value, use a plain placeholder "
    "('Quay 1', 'Line 1'). Add no real-world facts the question does not give, such as coordinates, addresses, "
    "full names of organisations or opening times. The frame goes inside <dataObjects> of a PublicationDelivery; do not write the PublicationDelivery, "
    "an XML declaration or namespace declarations.\n"
    'Return ONLY JSON: {"xml": "<...Frame ...>...</...Frame>"}'
)


def _evidence_text(chunks: list[dict]) -> tuple[str, list[dict]]:
    used = [chunk for chunk in chunks if "netex" in str(chunk.get("repositoryUrl", "")).lower()][:MAX_EVIDENCE_CHUNKS]
    blocks = [
        f"[E{index}] source={chunk.get('sourcePath', '')}\n{str(chunk.get('text', ''))[:MAX_EVIDENCE_CHARS]}"
        for index, chunk in enumerate(used, start=1)
    ]
    return "\n\n".join(blocks), used


def _extract_fragment(content: str) -> str:
    try:
        payload = json.loads(content)
        if isinstance(payload, dict) and isinstance(payload.get("xml"), str):
            return payload["xml"].strip()
    except (ValueError, TypeError):
        pass
    match = _XML_BLOCK.search(content or "")
    return match.group(0).strip() if match else ""


def _ask_model(messages: list[dict]) -> str:
    from helpdesk.services.llm_generator import _request_chat_completion
    from helpdesk.services.llm_options import answer_max_tokens

    response = _request_chat_completion(
        api_base_url=(settings.LLM_API_BASE_URL or "").strip(),
        api_key=(settings.LLM_API_KEY or "").strip(),
        model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        temperature=0.0,
        max_tokens=answer_max_tokens(1600),
        messages=messages,
    )
    return str(response["choices"][0]["message"]["content"] or "")


def generate_netex_example(question: str, chunks: list[dict], scope: list[str] | None = None) -> dict | None:
    """A validated NeTEx fragment for the question, or a record of why there is none.

    Returns None when the question does not ask for one. Otherwise a dict with valid (bool), attempts,
    and, when valid, xml, schema, schemaVersion, elementNotes (each element in the schema's words) and
    evidenceChunkIds; when not valid, errors.
    """
    if not wants_generated_example(question, scope):
        return None
    if not getattr(settings, "LLM_ENABLED", False):
        return None
    evidence, used = _evidence_text(chunks)
    if not used:
        return {"valid": False, "attempts": 0, "errors": ["no NeTEx evidence to build the example from"]}
    values = requested_values(question)
    messages = [
        {"role": "system", "content": _PROMPT},
        {"role": "user", "content": f"Question:\n{question}\n\nValues to use: {', '.join(values)}\n\nEVIDENCE BLOCKS:\n{evidence}"},
    ]
    errors: list[str] = []
    # Time spent waiting for the model and for the validator, so the validator's share of an answer's
    # latency shows in the trace.
    timing = {"generationMs": 0, "validationMs": 0}

    def timed(key: str, call):
        started = time.perf_counter()
        try:
            return call()
        finally:
            timing[key] += round((time.perf_counter() - started) * 1000)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            content = timed("generationMs", lambda: _ask_model(messages))
        except Exception as exc:
            logger.warning("NeTEx example generation failed: %s", exc)
            return {"valid": False, "attempts": attempt, "errors": [f"generation failed: {exc}"[:200]], **timing}
        fragment = _extract_fragment(content)
        checked: dict = {}
        if not fragment:
            errors = ["the reply contained no XML frame"]
        else:
            try:
                checked = timed("validationMs", lambda: validate_fragment(fragment))
            except ValidatorUnavailable as exc:
                logger.warning("NeTEx example not validated: %s", exc)
                return {"valid": False, "attempts": attempt, "errors": [str(exc)[:200]], **timing}
            errors = list(checked.get("errors") or [])
            if checked.get("valid") and not errors:
                errors = [
                    f"the value {value} from the question is missing: it must be the whole content of an element "
                    "or attribute that holds it, not part of a Name or Description text"
                    for value in missing_values(fragment, values)
                ]
        if not errors:
            return {
                "valid": True,
                "attempts": attempt,
                "xml": indented_fragment(fragment),
                "document": publication_document(fragment),
                "schema": SCHEMA_ENTRY,
                "schemaVersion": checked.get("schemaVersion", ""),
                "schemaCommit": checked.get("commit", ""),
                "elementNotes": element_notes(checked.get("elements") or []),
                "evidenceChunkIds": [chunk.get("chunkId") for chunk in used],
                **timing,
            }
        messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": "The frame is not valid NeTEx:\n- " + "\n- ".join(errors)
                + "\nFix these errors and return the whole frame again as JSON {\"xml\": \"...\"}.",
            },
        ]
    return {"valid": False, "attempts": MAX_ATTEMPTS, "errors": errors, **timing}
