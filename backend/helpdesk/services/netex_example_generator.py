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

import contextvars
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


_NUMBER_WORD_VALUES = {word: index for index, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split()
)}
_COUNTED = re.compile(r"\b(\d{1,3}|" + "|".join(sorted(_NUMBER_WORD_VALUES, key=len, reverse=True)) + r")\s+([A-Za-z][A-Za-z-]+)\b", re.I)
_INTERROGATIVE = re.compile(r"^\s*(?:how|what|which|why|when|where|who|is|are|does|do|can|could|should|explain|describe)\b", re.I)


def counted_shapes(question: str) -> list[tuple[int, str, str]]:
    """Counts the question gives for things ("two quays", "3 entrances"): (count, number as written, noun)."""
    shapes = []
    for number, noun in _COUNTED.findall(question or ""):
        count = int(number) if number.isdigit() else _NUMBER_WORD_VALUES[number.lower()]
        if count > 0:
            shapes.append((count, number, noun))
    return shapes


def element_for_noun(noun: str) -> list[str]:
    """Element names a (plural) noun may denote, most likely first: "quays" -> Quay, "stop places" -> StopPlace."""
    from helpdesk.services.schema_structure import candidate_element_names

    lowered = noun.lower()
    if lowered.endswith("ies") and len(lowered) > 4:
        singular = noun[:-3] + "y"
    elif lowered.endswith(("ses", "xes", "ches", "shes")):
        singular = noun[:-2]
    elif lowered.endswith("s") and not lowered.endswith("ss"):
        singular = noun[:-1]
    else:
        singular = noun
    return candidate_element_names(singular[:1].upper() + singular[1:])


def other_question(question: str) -> str:
    """The part of a question that asks something besides the example ("How do you describe a stop place in
    NeTEx?" in "How do you describe a stop place in NeTEx? Show me an example with two quays."), or ""."""
    parts = re.split(r"(?<=[?.!])\s+|\s*;\s*|,?\s+and\s+(?=(?:show|give|write|provide)\b)", (question or "").strip(), flags=re.I)
    asked = [p.strip() for p in parts if p.strip() and _INTERROGATIVE.match(p) and not _EXAMPLE_WORDS.search(p)]
    return " ".join(asked)


def asks_for_netex_example(question: str, scope: list[str] | None) -> bool:
    """A request for a NeTEx example, with or without values."""
    if not getattr(settings, "NETEX_EXAMPLE_GENERATOR_ENABLED", True):
        return False
    names = {(name or "").strip().lower() for name in scope or []}
    if "netex" not in names and "netex" not in (question or "").lower():
        return False
    return bool(_EXAMPLE_WORDS.search(question or ""))


def wants_generated_example(question: str, scope: list[str] | None) -> bool:
    """A request for a NeTEx example with concrete values ("a bus with 50 seats and 20 standing places")."""
    if not asks_for_netex_example(question, scope):
        return False
    return bool(requested_values(question) or counted_words(question) or wanted_parts(question))


MAX_EXAMPLE_CONCEPTS = 2


def concept_elements(question: str) -> list[str]:
    """The NeTEx elements of the classes the question is about, best first, that the standard's examples use: "How do I
    describe a lift in a station? Show me an example." -> LiftEquipment (prod req-mw8cczxw, 2026-11-08: a
    plain example request named no values or parts, so no example was made, though the standard's example
    files have lifts). The classes come from concept matching (concept_presence.presence_concepts); the
    first two are tried, as the nearest one is not always the one meant ("ticket machine": TICKET VALIDATOR
    EQUIPMENT, then TICKETING EQUIPMENT)."""
    from helpdesk.models import SourceChunk
    from helpdesk.services.concept_presence import presence_concepts
    from helpdesk.services.semantic_graph import TRANSMODEL_TO_CONCEPTS

    in_examples = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")
    found: list[str] = []
    for concept in presence_concepts(question)[:MAX_EXAMPLE_CONCEPTS]:
        own = [concept] if concept.startswith("netex:") else []
        for netex in own or sorted(c for c in TRANSMODEL_TO_CONCEPTS.get(concept, ()) if c.startswith("netex:")):
            name = netex.split(":", 1)[1]
            if name[:1].isupper() and name not in found and in_examples.filter(has_tag(name)).exists():
                found.append(name)
                break
    return found


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

_QUESTION_STOPWORDS = frozenset(
    "show give make write create example examples sample snippet fragment with and the for from that this what "
    "which have into where when please would could there about named called".split()
)


def _stem(word: str) -> str:
    lowered = word.lower()
    return lowered[:-1] if lowered.endswith("s") and len(lowered) > 4 else lowered


def _question_words(question: str) -> list[str]:
    """The question's content words, singular ("seats" -> "seat"), for the schema declaration search."""
    stems: list[str] = []
    for word in re.findall(r"[^\W\d_]{4,}", question or ""):
        if word.lower() in _QUESTION_STOPWORDS or word.lower() in _NOT_NAMES:
            continue
        if _stem(word) not in stems:
            stems.append(_stem(word))
    return stems


def _counted_question_words(question: str) -> list[str]:
    """Words that follow a number ("49 seats", "1 wheelchair area" -> seat, wheelchair): the thing counted,
    which the schema holds in a number-valued element."""
    return list(dict.fromkeys(_stem(word) for word in re.findall(r"\d+\s+([^\W\d_]{4,})", question or "")))


def schema_declarations(question: str, limit: int = 40) -> list[dict]:
    """Element declarations of the NeTEx schema whose name or documentation matches the question's words,
    from the validator's index: {"name", "parents", "documentation"}. The evidence for the elements a
    question needs, independent of text retrieval ("coach with 49 seats" retrieved deck plans and no
    capacity element). Empty when the validator is unreachable."""
    from urllib import error, parse, request

    words = _question_words(question)
    if not words:
        return []
    query = {"q": " ".join(words), "c": " ".join(_counted_question_words(question))}
    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/declarations?" + parse.urlencode(query)
    try:
        with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            return list(json.loads(response.read()).get("declarations") or [])[:limit]
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("NeTEx schema declarations not available: %s", exc)
        return []


def declarations_block(declarations: list[dict]) -> str:
    lines = []
    for declaration in declarations:
        parents = declaration.get("parents") or []
        where = f" (child of {', '.join(parents)})" if parents else ""
        lines.append(f"- {declaration.get('name')}{where}: {declaration.get('documentation')}")
    return "SCHEMA DECLARATIONS (element, where it belongs, definition):\n" + "\n".join(lines)


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


_GENERIC_ELEMENTS = frozenset({"Name", "ShortName", "Description", "PrivateCode", "dataObjects"})


def main_object(example: dict | None) -> str:
    """The first element below the frame and its list wrapper (SiteFrame > stopPlaces > StopPlace): what the
    example is an example of."""
    xml = (example or {}).get("xml") or ""
    names = re.findall(r"<([A-Za-z][\w.-]*)[\s>/]", xml)
    for name in names[1:]:
        if name[:1].isupper():
            return name
    return ""


def value_element_names(example: dict | None) -> list[str]:
    """The elements that hold the question's values (SeatingCapacity, WheelchairPlaceCapacity), without
    generic ones (a Name holding "Ljubljana Bus Station" says nothing about the structure)."""
    if not example or not example.get("valid"):
        return []
    names = [str(p.get("element") or "").split("/@", 1)[0] for p in example.get("valuePlaces") or []]
    return list(dict.fromkeys(n for n in names if n and n not in _GENERIC_ELEMENTS))


def example_element_names(example: dict | None, limit: int = 10) -> list[str]:
    """The elements the answer text should be about: those holding the question's values first, then the
    example's other elements, outermost first, without the generic ones every object has. Empty when
    there is no valid example."""
    if not example or not example.get("valid"):
        return []
    names = value_element_names(example) + [str(note.get("name") or "") for note in example.get("elementNotes") or []]
    return list(dict.fromkeys(name for name in names if name and name not in _GENERIC_ELEMENTS))[:limit]


def count_places(fragment: str, question: str, placed: set[str] = frozenset()) -> list[dict]:
    """The question's counts the fragment satisfies: "two quays" -> {"value": "two", "element": "Quay",
    "count": 2, "path": [...]} when the fragment has exactly two Quay elements in one parent."""
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return []
    local = lambda tag: tag.rsplit("}", 1)[-1]  # noqa: E731
    parents = {child: parent for parent in root.iter() for child in parent}
    places = []
    for count, written, noun in counted_shapes(question):
        if written in placed:
            continue
        for element in element_for_noun(noun):
            for parent in root.iter():
                children = [c for c in parent if local(c.tag) == element]
                if len(children) != count:
                    continue
                path, node = [], parent
                while node is not None and node is not root:
                    path.append(local(node.tag))
                    node = parents.get(node)
                places.append({"value": written, "element": element, "count": count, "path": list(reversed(path))})
                break
            else:
                continue
            break
    return places


def value_places(fragment: str, values: list[str]) -> list[dict]:
    """Where each of the question's values sits in the validated fragment: {"value", "element", "path"},
    path being the element's ancestors from the frame down ("49" -> SeatingCapacity in ResourceFrame ›
    vehicleTypes › VehicleType › capacities › PassengerCapacity). An element's text wins over an
    attribute ("@id"); values found nowhere are left out. The lead of the answer is written from this,
    so it says exactly what the validated fragment does."""
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return []
    local = lambda tag: tag.rsplit("}", 1)[-1]  # noqa: E731
    parents = {child: parent for parent in root.iter() for child in parent}

    def path_of(node) -> list[str]:
        names = []
        node = parents.get(node)
        while node is not None and node is not root:
            names.append(local(node.tag))
            node = parents.get(node)
        return list(reversed(names))

    places = []
    for value in values:
        found = next((n for n in root.iter() if n is not root and (n.text or "").strip() == value), None)
        if found is not None:
            places.append({"value": value, "element": local(found.tag), "path": path_of(found)})
            continue
        for node in root.iter():
            name = next((a for a, v in node.attrib.items() if v.strip() == value), None)
            if node is not root and name:
                places.append({"value": value, "element": f"{local(node.tag)}/@{name}", "path": path_of(node)})
                break
    return places


MAX_STANDARD_EXAMPLE_LINES = 60
# An object with more elements than this is cut to an excerpt (about one screen of indented XML).
MAX_STANDARD_EXAMPLE_ELEMENTS = 45
MAX_STANDARD_FILE_BYTES = 3_000_000
MAX_STANDARD_FILES = 40


def _shape_count(obj, element: str, local) -> int:
    """How many `element`s the object has as children or inside one of its lowercase list wrappers
    (StopPlace > quays > Quay): NeTEx puts an object's related objects in such wrappers."""
    direct = sum(1 for child in obj if local(child.tag) == element)
    wrapped = sum(
        1 for wrapper in obj if isinstance(wrapper.tag, str) and local(wrapper.tag)[:1].islower()
        for child in wrapper if isinstance(child.tag, str) and local(child.tag) == element
    )
    return direct + wrapped


def has_tag(name: str):
    """A query condition: the chunk text has an element of exactly this name (<Quay> or <Quay ...>, not <QuayType>)."""
    from django.db.models import Q

    return Q(text__contains=f"<{name}>") | Q(text__contains=f"<{name} ") | Q(text__contains=f"<{name}\n") | Q(text__contains=f"<{name}/>")


_PART = re.compile(
    r"\b(?:with|having|has|have|containing|including|that\s+has)\s+(?:an?|one|some|any|several)\s+"
    r"([A-Za-z][\w-]*(?:\s+(?!and\b|or\b|in\b|for\b|with\b|of\b)[a-z][\w-]*)?)",
    re.I,
)
_SUBJECT = re.compile(
    r"\b(?:examples?|samples?|fragments?)\s+(?:of|for)\s+(?:an?\s+|the\s+|one\s+)?(?P<subject>[A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){0,2}?)"
    r"\s+(?:with|having|has|that|containing|including|for|in)\b",
    re.I,
)


def wanted_parts(question: str) -> list[str]:
    """Things the question wants the example to have, without a number: "a stop place with an elevator"
    -> ["elevator"]. At least one of each."""
    return [noun for noun in _PART.findall(question or "") if noun.lower() not in _QUESTION_STOPWORDS]


def example_subject(question: str) -> str:
    """What the example is an example of: "example for a stop place with an elevator" -> "stop place"."""
    match = _SUBJECT.search(question or "")
    return match.group("subject").strip() if match else ""


_RESOLVED: dict[str, str] = {}


def resolve_element(noun: str) -> str:
    """The schema element a noun denotes. Its name ("quays" -> Quay, "stop place" -> StopPlace) when that is an
    element of the standard's examples; else the first object element (a versioned entity with an id) whose
    documentation uses the word ("elevator" -> LiftEquipment, documented as a lift that is "a vertical ...
    elevator"), not a property such as ReachedFloorAnnouncement. "" when nothing fits."""
    from urllib import error, parse, request

    from helpdesk.models import SourceChunk

    key = noun.lower()
    if key in _RESOLVED:
        return _RESOLVED[key]
    in_examples = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")
    # A two-word noun ("deck plan") names DeckPlan before its first word names Deck.
    phrases = [noun] + ([noun.split()[0]] if " " in noun else [])
    found = next(
        (name for phrase in phrases for name in element_for_noun(phrase) if in_examples.filter(has_tag(name)).exists()),
        "",
    )
    if not found:
        url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/declarations?" + parse.urlencode({"q": _stem(noun)})
        try:
            with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
                declarations = json.loads(response.read()).get("declarations") or []
        except (error.URLError, OSError, ValueError):
            declarations = []
        found = next(
            (d["name"] for d in declarations if d.get("object") and in_examples.filter(has_tag(d["name"])).exists()),
            "",
        )
    _RESOLVED[key] = found
    return found


def _pruned(obj, keep: set, local, max_leaves: int = 6):
    """A copy of obj with its simple children (at most max_leaves), the branches leading to the elements in
    keep, those elements whole, and a "…" comment where anything else was left out."""
    import copy

    from lxml import etree

    shell = etree.Element(obj.tag, attrib=dict(obj.attrib))
    shell.text = obj.text if obj.text and obj.text.strip() else None
    leaves, omitted = 0, False

    def mark():
        nonlocal omitted
        if not omitted:
            shell.append(etree.Comment(" … "))
            omitted = True

    for child in obj:
        if not isinstance(child.tag, str):
            continue
        if child in keep:
            shell.append(copy.deepcopy(child))
            omitted = False
        elif any(child is k or child in k.iterancestors() for k in keep):
            shell.append(_pruned(child, keep, local, max_leaves=3))
            omitted = False
        elif len(child) == 0 and "id" not in child.attrib and leaves < max_leaves and len((child.text or "").strip()) <= 120:
            shell.append(copy.deepcopy(child))
            leaves += 1
            omitted = False
        else:
            mark()
    return shell


def standard_example(
    question: str,
    scope: list[str] | None = None,
    element: str = "",
    exclude: frozenset = frozenset(),
    max_between: int | None = None,
) -> dict | None:
    """An object from the standard's own example files with the shape the question asks for, when the
    question gives counts or parts but no other values: "a stop place with two quays" (exactly two Quay),
    "a stop place with an elevator" (at least one LiftEquipment inside). Verbatim, so grounded by
    construction; generation is for values the standard's examples do not have. The object comes with its
    frame and list wrappers; a large one is cut to an excerpt keeping what the question asks for."""
    import copy
    from pathlib import Path

    from helpdesk.models import SourceChunk

    shapes, parts = counted_shapes(question), wanted_parts(question)
    if not shapes and not parts and not element:
        return None
    numbers = {written for _, written, _ in shapes}
    if [value for value in requested_values(question) if value not in numbers]:
        return None  # names or other values: the standard's examples will not have them
    exact = []  # (count, element)
    for count, _, noun in shapes:
        element = resolve_element(noun)
        if not element:
            return None
        exact.append((count, element))
    at_least = []  # (noun as asked, element)
    for noun in parts:
        element = resolve_element(noun)
        if not element:
            return None
        at_least.append((noun, element))
    subject = example_subject(question)
    # A plain example request ("show me an example of a lift"): an object of the element itself.
    plain = bool(element) and not shapes and not parts
    subject_element = element if plain else (resolve_element(subject) if subject else "")
    elements = [e for _, e in exact] + [e for _, e in at_least]
    # Files that use every element, each in any of their chunks: in a 4,000-line file the StopPlace and its
    # LiftEquipment sit in different chunks.
    base = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")
    files: dict = {}
    for index, element in enumerate(elements + ([subject_element] if subject_element else [])):
        rows = {r["source_path"]: r for r in base.filter(has_tag(element)).values("source_path", "repository_url", "commit_sha")[:5000]}
        files = rows if index == 0 else {path: row for path, row in files.items() if path in rows}
    # The standard's example files have descriptive names ("BasicStopPlace-two-quays_example.xml"): files
    # whose name has more of the question's words come first, and the search stops once a better-named
    # file can no longer follow.
    words = set(_question_words(question)) | {written.lower() for written in numbers} | {e.lower() for e in elements}

    def name_score(source_path: str) -> int:
        name = re.sub(r"[^a-z0-9]", "", source_path.rsplit("/", 1)[-1].lower())
        return sum(1 for word in words if re.sub(r"[^a-z0-9]", "", word) in name)

    ranked = sorted(files.items(), key=lambda item: (-name_score(item[0]), item[0]))
    from lxml import etree

    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, remove_blank_text=True)
    local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
    checkout_root = Path(getattr(settings, "SOURCE_CHECKOUT_DIR", "/app/repos"))
    best = None  # (score, excerpt?, -lines, fragment, row, object name)
    for source_path, row in [item for item in ranked if item[0] not in exclude][:MAX_STANDARD_FILES]:
        score = name_score(source_path)
        if best is not None and score < best[0]:
            break
        path = checkout_root / row["repository_url"].rstrip("/").rsplit("/", 1)[-1] / source_path
        try:
            if path.stat().st_size > MAX_STANDARD_FILE_BYTES:
                continue
            tree = etree.parse(str(path), parser)
        except (OSError, etree.XMLSyntaxError):
            continue
        for obj in tree.getroot().iter():
            name = local(obj.tag)
            if not name[:1].isupper() or (subject_element and name != subject_element):
                continue
            if any(_shape_count(obj, element, local) != count for count, element in exact):
                continue
            found_parts = [next((d for d in obj.iter() if d is not obj and local(d.tag) == element), None) for _, element in at_least]
            if any(part is None for part in found_parts):
                continue
            ancestors = [a for a in obj.iterancestors()]
            frame_index = next((i for i, a in enumerate(ancestors) if local(a.tag).endswith("Frame")), None)
            if frame_index is None:
                continue
            # Ancestors between the frame's list and the object are kept as shells without their other
            # children, which the schema may require (a SitePathLink's From and To before placeEquipments).
            if max_between is not None and frame_index - 1 > max_between:
                continue
            whole = copy.deepcopy(obj)
            # Size in elements: a parsed file without blank text serialises to one line.
            excerpt = sum(1 for e in obj.iter() if isinstance(e.tag, str)) > MAX_STANDARD_EXAMPLE_ELEMENTS
            if excerpt:
                keep = set(found_parts)
                for count, element in exact:
                    keep.update(
                        c for w in [obj] + [w for w in obj if isinstance(w.tag, str) and local(w.tag)[:1].islower()]
                        for c in w if isinstance(c.tag, str) and local(c.tag) == element
                    )
                whole = _pruned(obj, keep, local)
            chain = list(reversed(ancestors[: frame_index + 1]))  # frame ... direct parent
            # A shell's references (dataSourceRef="nptg:NaPTAN") point to objects the excerpt leaves out, and
            # the schema's keyrefs then fail; the object itself is kept whole.
            shell_attrib = lambda node: {k: v for k, v in node.attrib.items() if not k.endswith("Ref")}  # noqa: E731
            top = etree.Element(chain[0].tag, attrib=shell_attrib(chain[0]))
            current = top
            for node in chain[1:]:
                current = etree.SubElement(current, node.tag, attrib=shell_attrib(node))
            current.append(whole)
            for element in top.iter():
                if isinstance(element.tag, str):
                    element.tag = local(element.tag)
                    # Attributes of other namespaces (xsi:type) would be unbound once the namespace
                    # declarations go; xml:lang stays, its prefix is always bound.
                    for attribute in [a for a in element.attrib if a.startswith("{") and not a.startswith("{http://www.w3.org/XML/1998/namespace}")]:
                        del element.attrib[attribute]
            etree.cleanup_namespaces(top)
            fragment = re.sub(r'\sxmlns(?::\w+)?="[^"]*"', "", etree.tostring(top, encoding="unicode"))
            lines = sum(1 for e in top.iter() if isinstance(e.tag, str))
            if lines > MAX_STANDARD_EXAMPLE_ELEMENTS * 2:
                continue
            candidate = (score, not excerpt, -lines)
            if best is None or candidate > best[:3]:
                best = (score, not excerpt, -lines, fragment, row, name, excerpt)
    if best is None:
        return None
    fragment, row, name, excerpt = best[3:]
    return {
        "fragment": fragment,
        "object": name,
        "excerpt": excerpt,
        "sourcePath": row["source_path"],
        "repositoryUrl": row["repository_url"],
        "commitSha": row["commit_sha"],
        "sourceUrl": f"{row['repository_url'].rstrip('/')}/blob/{row['commit_sha']}/{row['source_path']}" if row["commit_sha"] else "",
    }


def _unmet_values(fragment: str, values: list[str], question: str) -> list[str]:
    """Values the fragment does not hold: as the whole content of an element or attribute, or, for a number
    followed by a noun ("2 quays"), as that many elements of the noun's kind."""
    missing = missing_values(fragment, values)
    if not missing:
        return []
    counted = {p["value"] for p in count_places(fragment, question)}
    return [value for value in missing if value not in counted]


def part_places(fragment: str, question: str) -> list[dict]:
    """Where the parts the question asks for sit: "an elevator" -> {"value": "an elevator", "element":
    "LiftEquipment", "path": [...]} for the first one in the fragment."""
    from xml.etree import ElementTree

    parts = [(m.group(0).split(None, 1)[1], noun) for m, noun in zip(_PART.finditer(question or ""), wanted_parts(question))]
    if not parts:
        return []
    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return []
    local = lambda tag: tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""  # noqa: E731
    parents = {child: parent for parent in root.iter() for child in parent}
    places = []
    for asked, noun in parts:
        element = resolve_element(noun)
        node = next((n for n in root.iter() if local(n.tag) == element), None) if element else None
        if node is None:
            continue
        path, up = [], parents.get(node)
        while up is not None and up is not root:
            path.append(local(up.tag))
            up = parents.get(up)
        places.append({"value": asked, "element": element, "path": list(reversed(path))})
    return places


def _places(fragment: str, values: list[str], question: str) -> list[dict]:
    """Where the question's values go, then its counts (a number already placed as a value is not a count),
    then the parts it asks for."""
    places = value_places(fragment, values)
    places += count_places(fragment, question, placed={p["value"] for p in places})
    return places + part_places(fragment, question)


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
    "types, for example, in a ResourceFrame). Use only element and attribute names that appear in the schema "
    "declarations and the evidence blocks (schema definitions and example files), in the order the schema "
    "definitions give; put a declared element under one of the parents its declaration names. Give every element that "
    "needs one a version and an id; use the prefix 'hd:' for ids. Every reference element (...Ref) must point "
    "to an object defined in the same frame: define that object too, even if the question does not mention it. "
    "Otherwise do not add elements the question does not "
    "need. Use only the values the question gives; where the schema needs another value, use a plain placeholder "
    "('Quay 1', 'Line 1'). Add no real-world facts the question does not give, such as coordinates, addresses, "
    "full names of organisations or opening times. The frame goes inside <dataObjects> of a PublicationDelivery; do not write the PublicationDelivery, "
    "an XML declaration or namespace declarations.\n"
    'Return ONLY JSON: {"xml": "<...Frame ...>...</...Frame>"}. The reply is the JSON object only, with no text '
    "before or after it."
)


def _evidence_text(chunks: list[dict]) -> tuple[str, list[dict]]:
    used = [chunk for chunk in chunks if "netex" in str(chunk.get("repositoryUrl", "")).lower()][:MAX_EVIDENCE_CHUNKS]
    blocks = [
        f"[E{index}] source={chunk.get('sourcePath', '')}\n{str(chunk.get('text', ''))[:MAX_EVIDENCE_CHARS]}"
        for index, chunk in enumerate(used, start=1)
    ]
    return "\n\n".join(blocks), used


def parse_reply(content: str) -> tuple[str, str]:
    """The frame in the model's reply and how it was found: "json" (a JSON object with "xml", anywhere in
    the reply: the model sometimes writes a sentence before it), "xml" (bare XML), or "" (nothing).

    The JSON object is read with raw_decode from each "{" in turn, so text before or after it and a
    fenced block do not matter. Only without one is the first XML element taken as written; JSON escapes
    in it (\\" and \\n, from a reply that was JSON but did not decode) are undone, else the validator saw
    `AttValue: " or ' expected` (2026-11-10: 1 of 33 attempts lost that way)."""
    text = content or ""
    decoder = json.JSONDecoder()
    position = text.find("{")
    while position != -1:
        try:
            payload, _ = decoder.raw_decode(text, position)
        except ValueError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("xml"), str) and payload["xml"].strip():
            return payload["xml"].strip(), "json"
        position = text.find("{", position + 1)
    match = _XML_BLOCK.search(text)
    if not match:
        return "", ""
    fragment = match.group(0).strip()
    if '\\"' in fragment:
        fragment = fragment.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\/", "/")
    return fragment, "xml"


def _extract_fragment(content: str) -> str:
    return parse_reply(content)[0]


_ERROR_CLASSES = (
    ("malformed", ("Not well-formed XML", "the reply contained no XML frame")),
    ("keyref", ("No match found for key-sequence",)),
    ("min-count", ("Missing child element(s)",)),
    ("not-expected", ("This element is not expected",)),
    ("value", ("from the question is missing",)),
    ("asked-object", ("the question asks for",)),
    ("model-error", ("generation failed",)),
)


def error_class(message: str) -> str:
    """The kind of a failed attempt's first error, from the validator's or the generator's wording:
    malformed, keyref, min-count, not-expected, value, asked-object, model-error, or other."""
    for name, markers in _ERROR_CLASSES:
        if any(marker in (message or "") for marker in markers):
            return name
    return "other" if message else ""


# Output tokens of the last model call in this context, for the attempt log (0 when unknown).
_LAST_COMPLETION_TOKENS: contextvars.ContextVar[int] = contextvars.ContextVar("netex_example_completion_tokens", default=0)


def _ask_model(messages: list[dict]) -> str:
    from helpdesk.services.llm_generator import _request_chat_completion
    from helpdesk.services.llm_options import answer_max_tokens

    _LAST_COMPLETION_TOKENS.set(0)
    response = _request_chat_completion(
        api_base_url=(settings.LLM_API_BASE_URL or "").strip(),
        api_key=(settings.LLM_API_KEY or "").strip(),
        model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        temperature=0.0,
        max_tokens=answer_max_tokens(1600),
        messages=messages,
    )
    usage = response.get("usage") if isinstance(response, dict) else None
    if isinstance(usage, dict) and isinstance(usage.get("completion_tokens"), int):
        _LAST_COMPLETION_TOKENS.set(usage["completion_tokens"])
    return str(response["choices"][0]["message"]["content"] or "")


def _from_standard(
    question: str, scope: list[str] | None, element: str = "", exclude: frozenset = frozenset(), max_between: int | None = None
) -> dict | None:
    """The answer's example taken from the standard (standard_example), checked against the XSD and
    described like a generated one. None when the standard has no example with the question's shape."""
    started = time.perf_counter()
    try:
        found = standard_example(question, scope, element, exclude, max_between)
    except Exception as exc:  # a broken file or the index unavailable: generate instead
        logger.warning("standard example lookup failed: %s", exc)
        return None
    if found is None:
        return None
    fragment = found["fragment"]
    checked: dict = {}
    try:
        checked = validate_fragment(fragment)
    except ValidatorUnavailable as exc:
        logger.info("standard example not validated: %s", exc)
    return {
        "valid": True,
        "origin": "standard",
        "validated": bool(checked.get("valid")),
        "attempts": 0,
        "xml": indented_fragment(fragment),
        "document": publication_document(fragment),
        "schema": SCHEMA_ENTRY,
        "schemaVersion": checked.get("schemaVersion", ""),
        "schemaCommit": checked.get("commit", "") or found["commitSha"],
        "elementNotes": element_notes(checked.get("elements") or []),
        "valuePlaces": count_places(fragment, question) + part_places(fragment, question),
        "excerpt": bool(found.get("excerpt")),
        "sourcePath": found["sourcePath"],
        "sourceUrl": found["sourceUrl"],
        "repositoryUrl": found["repositoryUrl"],
        "evidenceChunkIds": [],
        "generationMs": round((time.perf_counter() - started) * 1000),
        "validationMs": 0,
        "schemaDeclarations": 0,
    }


MAX_PLAIN_EXAMPLE_FILES = 3


def _plain_standard_example(question: str, scope: list[str] | None, elements: list[str]) -> dict | None:
    """The first excerpt from the standard's examples that validates, for each element in turn and up to
    three files each; objects placed directly in a frame's list first, then those at most two levels below
    one (a stop place's placeEquipments), then any (a lift in Wimbledon's station sits on a path link, whose
    shell broke the schema). Without a valid one, the first excerpt found, shown as not
    valid."""
    first = None
    for element in elements:
        for max_between in (0, 2, None):
            exclude: frozenset = frozenset()
            for _ in range(MAX_PLAIN_EXAMPLE_FILES):
                found = _from_standard(question, scope, element, exclude, max_between)
                if found is None:
                    break
                if found["validated"]:
                    return found
                first = first or found
                exclude = exclude | {found["sourcePath"]}
    return first


def generate_netex_example(
    question: str, chunks: list[dict], scope: list[str] | None = None, english_question: str | None = None
) -> dict | None:
    """A validated NeTEx fragment for the question, or a record of why there is none.

    Returns None when the question does not ask for one. Otherwise a dict with valid (bool), attempts,
    and, when valid, xml, schema, schemaVersion, elementNotes (each element in the schema's words) and
    evidenceChunkIds; when not valid, errors.
    """
    # A question in another language ("Pokaži mi NeTEx primer za avtobus s 50 sedeži") is recognised on the
    # English rendering the app already makes for retrieval; its values are read from the question itself.
    english = (english_question or "").strip()
    if not wants_generated_example(question, scope):
        if not english or not wants_generated_example(english, scope):
            # No values, counts or parts: an example of the class the question is about, verbatim from
            # the standard's example files (nothing to generate).
            text = english or question
            if not (asks_for_netex_example(question, scope) or asks_for_netex_example(text, scope)):
                return None
            try:
                elements = concept_elements(text)
            except Exception as exc:  # concept matching or the index unavailable: no example, as before
                logger.info("example concept not found: %s", exc)
                return None
            return _plain_standard_example(text, scope, elements)
    shape_question = question if counted_shapes(question) else (english or question)
    found = _from_standard(shape_question, scope)
    if found is not None:
        return found
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
    # Schema declarations go only into the feedback after a failed attempt: given up front they lowered
    # the benchmark from 18 to 12 of 20 (elements from unrelated contexts tempt the model away from the
    # evidence); after a failure they supply the elements the evidence lacked.
    declarations: list[dict] | None = None
    # Time spent waiting for the model and for the validator, so the validator's share of an answer's
    # latency shows in the trace; and how many schema declarations the model was given.
    timing = {"generationMs": 0, "validationMs": 0, "schemaDeclarations": 0}

    def timed(key: str, call):
        started = time.perf_counter()
        try:
            return call()
        finally:
            timing[key] += round((time.perf_counter() - started) * 1000)

    # One row per attempt (time, output tokens, how the reply parsed, the first error's class): the
    # example benchmark reports from it, and the trace shows why an example took three attempts.
    attempt_log: list[dict] = []

    def logged(attempt: int, started: float, parsed: str, attempt_errors: list[str]) -> None:
        first = attempt_errors[0] if attempt_errors else ""
        attempt_log.append({
            "attempt": attempt,
            "ms": round((time.perf_counter() - started) * 1000),
            "completionTokens": _LAST_COMPLETION_TOKENS.get(),
            "parsed": parsed,
            "errorClass": error_class(first),
            "error": first[:300],
        })

    for attempt in range(1, MAX_ATTEMPTS + 1):
        attempt_started = time.perf_counter()
        _LAST_COMPLETION_TOKENS.set(0)
        try:
            content = timed("generationMs", lambda: _ask_model(messages))
        except Exception as exc:
            # A timeout or a gateway error on one call (local question req-mw7r1cj5, 2026-11-08: the
            # gateway timed out once at 60 s) ends the example only when no attempt is left.
            logger.warning("NeTEx example generation failed (attempt %d): %s", attempt, exc)
            errors = [f"generation failed: {exc}"[:200]]
            logged(attempt, attempt_started, "", errors)
            if attempt == MAX_ATTEMPTS:
                return {"valid": False, "attempts": attempt, "errors": errors, "attemptLog": attempt_log, **timing}
            continue
        fragment, parsed = parse_reply(content)
        checked: dict = {}
        if not fragment:
            errors = ["the reply contained no XML frame"]
        else:
            try:
                checked = timed("validationMs", lambda: validate_fragment(fragment))
            except ValidatorUnavailable as exc:
                logger.warning("NeTEx example not validated: %s", exc)
                return {"valid": False, "attempts": attempt, "errors": [str(exc)[:200]], "attemptLog": attempt_log, **timing}
            errors = list(checked.get("errors") or [])
            if checked.get("valid") and not errors:
                errors = [
                    f"the value {value} from the question is missing: it must be the whole content of an element "
                    "or attribute that holds it, not part of a Name or Description text"
                    for value in _unmet_values(fragment, values, shape_question)
                ]
        logged(attempt, attempt_started, parsed, errors)
        if not errors:
            return {
                "valid": True,
                "origin": "generated",
                "validated": True,
                "attempts": attempt,
                "xml": indented_fragment(fragment),
                "document": publication_document(fragment),
                "schema": SCHEMA_ENTRY,
                "schemaVersion": checked.get("schemaVersion", ""),
                "schemaCommit": checked.get("commit", ""),
                "elementNotes": element_notes(checked.get("elements") or []),
                "valuePlaces": _places(fragment, values, shape_question),
                "evidenceChunkIds": [chunk.get("chunkId") for chunk in used],
                "attemptLog": attempt_log,
                **timing,
            }
        if declarations is None:
            declarations = schema_declarations(question)
            timing["schemaDeclarations"] = len(declarations)
        schema_part = (
            "\n\n" + declarations_block(declarations) + "\nPrefer these elements, under the parents given, for what the question asks."
            if declarations
            else ""
        )
        messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": "The frame is not valid NeTEx:\n- " + "\n- ".join(errors)
                + schema_part
                + "\nFix these errors and return the whole frame again as JSON {\"xml\": \"...\"}.",
            },
        ]
    return {"valid": False, "attempts": MAX_ATTEMPTS, "errors": errors, "attemptLog": attempt_log, **timing}
