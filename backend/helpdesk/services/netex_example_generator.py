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
# One more attempt when an acceptable fragment (valid, with the values, only objects left unlinked) is already in
# hand: the attempt that writes the linking object often fails on its structure, and the acceptable one is kept
# either way (plan 2026-11-12 revision 2, R3). Never for hard errors alone.
SOFT_EXTRA_ATTEMPTS = 1
MAX_LOGGED_FRAGMENT_CHARS = 4000
MAX_EVIDENCE_CHUNKS = 6
MAX_EVIDENCE_CHARS = 1800
MAX_REPORTED_ERRORS = 5
VALIDATOR_TIMEOUT_SECONDS = 10

_EXAMPLE_WORDS = re.compile(r"\b(?:examples?|samples?|snippets?|fragments?|show\s+(?:me\s+)?(?:how|the\s+xml))\b", re.I)
# A request to produce XML without an example word (prod req-mwb6auo0-n3jh83, 2026-11-10: "Can you create an
# XML file modelling such TemplateServiceJourney?"; July: "give an XML snipped"). A producing verb, then in the
# same sentence XML (or NeTEx) and the kind of thing written, or "the/an XML" that is not about the schema
# itself ("write the XML header" asks how, "which XML schema" asks what).
_PRODUCING = r"(?:create|write|generate|produce|build|make|draft|give|provide|show|need|want|get)"
_XML_REQUEST = re.compile(
    rf"\b{_PRODUCING}\b[^.?!]{{0,60}}?\b(?:xml|netex)\s+(?:files?|documents?|code|snipp(?:et|ed)s?|fragments?|instances?|representations?)\b"
    r"|\b(?:create|write|generate|produce|build|draft)\b[^.?!]{0,40}?\b(?:an?|the|some|this|that|netex)\s+xml\b"
    r"(?!\s+(?:schemas?|elements?|attributes?|namespaces?|tags?|headers?|structure|declarations?|validation)\b)"
    r"|\bsnipped\b",
    re.I,
)
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


# A time ("08:30", "7:15:30") and a date ("2026-12-01") are one value each, not two or three numbers:
# "arriving at 08:30" asked for "08" and "30" as whole element contents, and ArrivalTime 08:30:00 failed
# the value check in every run (benchmark 2026-11-10: gen06, gen16, gen24).
_TIME = re.compile(r"(?<![\w:.])(\d{1,2}):(\d{2})(?::(\d{2}))?(?![\w:])")
_DATE = re.compile(r"(?<![\w-])\d{4}-\d{2}-\d{2}(?![\w-])")


def _time_value(match: re.Match) -> str:
    hours, minutes, seconds = match.groups()
    return f"{int(hours):02d}:{minutes}" + (f":{seconds}" if seconds else "")


# A number with a time unit ("3 minutes", "30 sec", "a 3-minute crossing") is one duration, written in the
# schema as an xs:duration (PT3M): not the bare number "3" (prod req-mwb6auo0-n3jh83, 2026-11-10: the value
# check wanted "3" as an element's whole content and the model wrote <Name>3</Name> to pass it) and not a
# count of parts ("3 minutes" found PassengersPerMinute and made the example a StopPlace).
_DURATION_UNITS = {"second": ("S", 1), "sec": ("S", 1), "minute": ("M", 60), "min": ("M", 60),
                   "hour": ("H", 3600), "hr": ("H", 3600), "day": ("D", 86400)}
_DURATION = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?|" + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True)) + r")[\s-]+"
    r"(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?)\b",
    re.I,
)


def _duration_unit(word: str) -> str:
    word = word.lower()
    return word[:-1] if word.endswith("s") and word[:-1] in _DURATION_UNITS else word


def durations(question: str) -> list[tuple[str, int, str]]:
    """The durations a question gives: (as written, seconds, xs:duration). "3 minutes" -> ("3 minutes", 180,
    "PT3M"); "1.5 hours" -> PT5400S (the schema allows a fraction only in the seconds); "2 days" -> P2D."""
    found = []
    for match in _DURATION.finditer(question or ""):
        number, unit = match.groups()
        amount = float(number) if number[:1].isdigit() else float(_NUMBER_WORD_VALUES[number.lower()])
        designator, factor = _DURATION_UNITS[_duration_unit(unit)]
        seconds = amount * factor
        if seconds <= 0 or seconds != int(seconds):
            continue
        if amount == int(amount):
            iso = f"P{int(amount)}D" if designator == "D" else f"PT{int(amount)}{designator}"
        else:
            iso = f"PT{int(seconds)}S"
        found.append((match.group(0), int(seconds), iso))
    return found


_ISO_DURATION = re.compile(r"(-)?P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?")


def duration_seconds(text: str) -> float | None:
    """Seconds of an xs:duration without years or months ("PT3M" -> 180, "PT1H30M" -> 5400), else None."""
    match = _ISO_DURATION.fullmatch((text or "").strip())
    if not match or (text or "").strip() in ("P", "PT") or (text or "").strip().endswith("T"):
        return None
    sign, days, hours, minutes, seconds = match.groups()
    if not any((days, hours, minutes, seconds)):
        return None
    total = int(days or 0) * 86400 + int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(seconds or 0)
    return -total if sign else total


def is_duration_value(value: str) -> bool:
    return duration_seconds(value) is not None


def requested_values(question: str) -> list[str]:
    """The concrete values a question gives, each of which the fragment must contain: quoted names,
    dates and times, durations (as xs:duration), numbers, and proper names written without quotes."""
    values = [(straight or curly).strip() for straight, curly in _QUOTED.findall(question or "")]
    unquoted = _QUOTED.sub(" ", question or "")
    values += _DATE.findall(unquoted)
    values += [_time_value(match) for match in _TIME.finditer(unquoted)]
    values += [iso for _, _, iso in durations(unquoted)]
    values += _NUMBER.findall(_DURATION.sub(" ", _TIME.sub(" ", _DATE.sub(" ", unquoted))))
    values += named_values(question)
    return list(dict.fromkeys(value for value in values if value))


_ZONE = r"(?:Z|[+-]\d{2}:\d{2})?"


def holds_value(text: str, value: str) -> bool:
    """Whether an element's or attribute's whole content is the value: equal, or the same time or date
    written as xsd:time / xsd:date / xsd:dateTime ("08:30" in 08:30:00, "2026-12-01" in 2026-12-01T00:00:00)."""
    text = (text or "").strip()
    if text == value:
        return True
    if value[:1] == "P" and (wanted := duration_seconds(value)) is not None:
        return duration_seconds(text) == wanted  # PT3M in PT180S or PT3M0S
    if re.fullmatch(r"\d{2}:\d{2}", value):
        return bool(re.fullmatch(re.escape(value) + r":00(?:\.0+)?" + _ZONE, text)
                    or re.fullmatch(r"\d{4}-\d{2}-\d{2}T" + re.escape(value) + r"(?::00(?:\.0+)?)?" + _ZONE, text))
    if re.fullmatch(r"\d{2}:\d{2}:\d{2}", value):
        return bool(re.fullmatch(re.escape(value) + r"(?:\.0+)?" + _ZONE, text)
                    or re.fullmatch(r"\d{4}-\d{2}-\d{2}T" + re.escape(value) + r"(?:\.0+)?" + _ZONE, text))
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return bool(re.fullmatch(re.escape(value) + _ZONE, text) or re.fullmatch(re.escape(value) + r"T[\d:.]+" + _ZONE, text))
    return False


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
        if _duration_unit(noun) in _DURATION_UNITS:
            continue  # "3 minutes" is a duration (durations), not three things
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


# A number written in digits directly before a kind of object ("2 service journeys") says how many of that object
# to write, not a value some element holds: asked for "2" as an element's whole content, the model wrote
# <Description>2</Description> or <PublicCode>2</PublicCode> on the Line (prod question "a line with 2 service
# journeys", 5 of 5 first attempts failed the value check, 2026-11-13). The same number in words ("two quays")
# was never a value. A number before a plain-valued element or before words that name no element ("50 seats",
# "120 spaces", "32 metres", "5 EUR") stays a value.
_DIGIT_COUNT = re.compile(r"(?<![\w.])(\d{1,4})(?![\w.])\s+([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,2})")


def _object_kinds(phrase: str) -> list[str] | None:
    """The object elements a noun phrase names by element name ("service journeys" -> [ServiceJourney]; an
    abstract one stands for its concrete objects), [] when it names an element that is not an object (a
    property such as Departure), None when it names no element. Only the element name counts, not the
    documentation search of resolve_element, which finds an element for nearly any word ("seats" ->
    CarModelProfile, "metres" -> AccessSpace)."""
    for name in element_for_noun(phrase):
        entries = concrete_elements(name)
        if entries:
            return [entry["name"] for entry in entries if entry.get("object")]
    return None


def object_counts(question: str) -> list[tuple[int, str, str, list[str]]]:
    """Numbers in digits that count objects: (count, number as written, noun phrase, object elements). "a line
    with 2 service journeys" -> [(2, "2", "service journeys", ["ServiceJourney"])]. The longest phrase of up to
    three words after the number that names an element decides; a number before anything else is a value."""
    unquoted = _QUOTED.sub(" . ", question or "")
    text = _DURATION.sub(" . ", _TIME.sub(" . ", _DATE.sub(" . ", unquoted)))
    found = []
    for match in _DIGIT_COUNT.finditer(text):
        number, words = match.group(1), match.group(2).split()
        if int(number) <= 0:
            continue
        for size in range(len(words), 0, -1):
            phrase = " ".join(words[:size])
            kinds = _object_kinds(phrase)
            if kinds is None:
                continue
            if kinds:
                found.append((int(number), number, phrase, kinds))
            break
    return found


def counted_out(values: list[str], question: str, counts: list[tuple[int, str, str, list[str]]]) -> list[str]:
    """The values without the numbers that only count objects ("2" in "a line with 2 service journeys"); a number
    the question also gives as a value elsewhere ("line 2 with 2 service journeys") stays."""
    if not counts:
        return list(values)
    text = _DURATION.sub(" ", _TIME.sub(" ", _DATE.sub(" ", _QUOTED.sub(" ", question or ""))))
    written = _NUMBER.findall(text)
    counting = [number for _, number, _, _ in counts]
    return [value for value in values if not (value in counting and written.count(value) <= counting.count(value))]


def object_count_places(fragment: str, counts: list[tuple[int, str, str, list[str]]], placed: set[str] = frozenset()) -> list[dict]:
    """Where the fragment has each counted number of objects, all in one parent: {"value": "2", "element":
    "ServiceJourney", "count": 2, "path": [...]}."""
    root = _parsed(fragment)
    if root is None:
        return []
    local = lambda tag: tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""  # noqa: E731
    parents = {child: parent for parent in root.iter() for child in parent}
    places = []
    for count, written, _, kinds in counts:
        if written in placed:
            continue
        for parent in root.iter():
            children = [child for child in parent if local(child.tag) in kinds]
            if len(children) != count:
                continue
            path, node = [], parent
            while node is not None and node is not root:
                path.append(local(node.tag))
                node = parents.get(node)
            places.append({"value": written, "element": local(children[0].tag), "count": count, "path": list(reversed(path))})
            break
    return places


def count_problems(fragment: str, counts: list[tuple[int, str, str, list[str]]]) -> list[str]:
    """The feedback for each counted number of objects the fragment does not have in one parent."""
    placed = {place["value"] for place in object_count_places(fragment, counts)}
    problems = []
    for count, written, phrase, kinds in counts:
        if written in placed:
            continue
        kind = kinds[0] if len(kinds) == 1 else " or ".join(kinds[:3])
        problems.append(
            f"the question counts {written} {phrase}: write exactly {count} {kind} objects, each with its own id, "
            f"together in the list the schema has for them; {written} is how many to write, not a value to put "
            "in an element"
        )
    return problems


def counts_line(counts: list[tuple[int, str, str, list[str]]]) -> str:
    """The counted objects for the model's prompt: "2 ServiceJourney (“2 service journeys”)"."""
    return ", ".join(
        f"{count} {kinds[0] if len(kinds) == 1 else ' or '.join(kinds[:3])} (“{written} {phrase}”)"
        for count, written, phrase, kinds in counts
    )


def named_object_parts(question: str, asked: str = "") -> list[tuple[str, list[str]]]:
    """The parts the question wants the example to have that name an object element by its element name:
    "a line with a stop place departure" -> [("stop place", ["StopPlace"])]. The longest words that name an
    element decide, as for counts; a property ("a wait time") or words that name no element ("a price") are not
    checked here: the documentation search finds an element for nearly any word."""
    found = []
    for noun in wanted_parts(question):
        words = noun.split()
        for size in range(len(words), 0, -1):
            phrase = " ".join(words[:size])
            kinds = _object_kinds(phrase)
            if kinds is None:
                continue
            if kinds and asked not in kinds and all(phrase != seen for seen, _ in found):
                found.append((phrase, kinds))
            break
    return found


def part_problems(fragment: str, parts: list[tuple[str, list[str]]], asked: str = "") -> list[str]:
    """The feedback for each named part the fragment does not define. Accepted without this check, "a line
    with a stop place departure" came back as a Line alone (prod question, 5 of 5 answers, 2026-11-13)."""
    root = _parsed(fragment)
    if root is None or not parts:
        return []
    present = {tag.rsplit("}", 1)[-1] for node in root.iter() if isinstance(tag := node.tag, str)}
    problems = []
    for phrase, kinds in parts:
        if present.intersection(kinds):
            continue
        kind = kinds[0] if len(kinds) == 1 else " or ".join(kinds[:3])
        owner = f", linked to the {asked}" if asked else ""
        problems.append(
            f"the question wants a {phrase} in the example and the frame defines no {kind}: write a {kind} "
            f"object with its own id{owner}"
        )
    return problems


def parts_line(parts: list[tuple[str, list[str]]]) -> str:
    """The named parts for the model's prompt: "StopPlace (“stop place”)"."""
    return ", ".join(f"{kinds[0] if len(kinds) == 1 else ' or '.join(kinds[:3])} (“{phrase}”)" for phrase, kinds in parts)


def other_question(question: str) -> str:
    """The part of a question that asks something besides the example ("How do you describe a stop place in
    NeTEx?" in "How do you describe a stop place in NeTEx? Show me an example with two quays."), or ""."""
    parts = re.split(r"(?<=[?.!])\s+|\s*;\s*|,?\s+and\s+(?=(?:show|give|write|provide)\b)", (question or "").strip(), flags=re.I)
    asked = [p.strip() for p in parts if p.strip() and _INTERROGATIVE.match(p) and not _asks_for_xml(p)]
    return " ".join(asked)


def _asks_for_xml(text: str) -> bool:
    """An example word, or a request to produce XML ("create an XML file", "write the XML for …")."""
    return bool(_EXAMPLE_WORDS.search(text or "") or _XML_REQUEST.search(text or ""))


def asks_for_netex_example(question: str, scope: list[str] | None) -> bool:
    """A request for a NeTEx example, with or without values."""
    if not getattr(settings, "NETEX_EXAMPLE_GENERATOR_ENABLED", True):
        return False
    names = {(name or "").strip().lower() for name in scope or []}
    if "netex" not in names and "netex" not in (question or "").lower():
        return False
    return _asks_for_xml(question)


def wants_generated_example(question: str, scope: list[str] | None) -> bool:
    """A request for a NeTEx example with concrete values ("a bus with 50 seats and 20 standing places")."""
    if not asks_for_netex_example(question, scope):
        return False
    return bool(requested_values(question) or counted_words(question) or wanted_parts(question) or service_conditions(question))


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


def value_element_declarations(fragment: str, values: list[str], limit: int = 15) -> list[dict]:
    """Declarations found by the names of the elements that hold the question's values in a failed
    fragment ("5 EUR" in Amount and Currency -> their declared parents FareProductPrice, …): the question's
    own words ("fare product … 5 EUR") found nothing about prices on 2026-11-10."""
    from urllib import error, parse, request

    names = list(dict.fromkeys(place["element"].split("/@", 1)[0] for place in value_places(fragment, values)))
    names = [name for name in names if name and name not in _GENERIC_ELEMENTS and len(name) >= 4]
    if not names:
        return []
    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/declarations?" + parse.urlencode({"q": " ".join(names[:6])})
    try:
        with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            found = list(json.loads(response.read()).get("declarations") or [])
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("NeTEx value element declarations not available: %s", exc)
        return []
    return [d for d in found if d.get("name") in names][:limit]


def feedback_lines(checked: dict, errors: list[str]) -> list[str]:
    """The retry message's lines: the validator's diagnostics (what is wrong, in schema terms: the concrete
    elements for an abstract one, the parent's children in schema order, the missing required element),
    then any error no diagnostic covers; the plain errors alone from a validator without diagnostics."""
    diagnostics = [d for d in checked.get("diagnostics") or [] if d.get("detail")]
    if not diagnostics:
        return list(errors)
    covered = {(d.get("line"), d.get("element")) for d in diagnostics}
    lines = [f"line {d.get('line')}: {d['detail']}" for d in diagnostics]
    for error_text in errors:
        match = re.match(r"line (\d+): Element '([^']+)'", error_text)
        if match and (int(match.group(1)), match.group(2)) in covered:
            continue
        lines.append(error_text)
    return lines


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


_CLOCK = re.compile(r"(?:(\d{4}-\d{2}-\d{2})T)?(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?" + _ZONE)


def _clock_seconds(text: str) -> float | None:
    """Seconds of an xs:time or xs:dateTime ("10:03:00.0Z" -> 36180), else None."""
    from datetime import date

    match = _CLOCK.fullmatch((text or "").strip())
    if not match:
        return None
    day, hours, minutes, seconds = match.groups()
    offset = date.fromisoformat(day).toordinal() * 86400 if day else 0
    return offset + int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def times_apart(node, seconds: float):
    """Two time values in node's subtree that are the given duration apart: (earlier, later) elements, else
    None. A crossing "3 minutes from side to side" is written as a departure and an arrival 3 minutes later,
    not as a duration element (3 of 3 dev runs, 2026-11-10)."""
    stamped = [(value, child) for child in node.iter() if (value := _clock_seconds(child.text or "")) is not None]
    for index, (first, first_node) in enumerate(stamped):
        for second, second_node in stamped[index + 1:]:
            if abs(second - first) == seconds:
                return (first_node, second_node) if first < second else (second_node, first_node)
    return None


def duration_by_times(root, value: str, local=lambda tag: tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""):
    """For a duration value: the later of two time values the duration apart inside one object (an element
    with an id that is not a frame) of the parsed fragment, else None."""
    seconds = duration_seconds(value) if value[:1] == "P" else None
    if not seconds:
        return None
    for node in root.iter():
        if node.get("id") and not local(node.tag).endswith("Frame") and (pair := times_apart(node, seconds)):
            return pair[1]
    return None


def _parsed(fragment: str):
    from xml.etree import ElementTree

    try:
        return ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return None


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
        found = next((n for n in root.iter() if n is not root and holds_value(n.text or "", value)), None)
        if found is not None:
            places.append({"value": value, "element": local(found.tag), "path": path_of(found)})
            continue
        for node in root.iter():
            name = next((a for a, v in node.attrib.items() if holds_value(v, value)), None)
            if node is not root and name:
                places.append({"value": value, "element": f"{local(node.tag)}/@{name}", "path": path_of(node)})
                break
        else:
            later = duration_by_times(root, value)
            if later is not None:
                places.append({"value": value, "element": local(later.tag), "path": path_of(later)})
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
    r"\b(?:examples?|samples?|fragments?|xml(?:\s+(?:files?|documents?|code|snippets?))?)\s+(?:of|for)\s+(?:an?\s+|the\s+|one\s+)?(?P<subject>[A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){0,2}?)"
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


# --- the asked object: resolver, skeleton, check (plan P2 of 2026-11-10) ------------------------

# What the example is an example of, with more endings than _SUBJECT ("a route named …", "a passing time
# arriving at …", "a fare product for adult …", the end of the sentence). Also before the words that start
# where it goes or how it runs: "a bus line from Maribor to Ptuj that runs only on school days" had no subject
# (prod req-mwdzf8px-3qfhdl, 2026-11-12), so no asked object, skeleton or check. Not "to": "a point to point
# fare" would end at "point".
_SUBJECT_WIDE = re.compile(
    r"\b(?:examples?|samples?|fragments?|xml(?:\s+(?:files?|documents?|code|snippets?))?)\s+(?:of|for)\s+(?:an?\s+|the\s+|one\s+)?"
    r"(?P<subject>[A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){0,2}?)"
    r"(?=\s+(?:with|having|has|that|containing|including|for|in|named|called|operated|departing|arriving|at|on|of"
    r"|from|between|via|through|by|near|during|which|whose|where|when|running|serving|operating|connecting|using"
    r"|and|or)\b"
    r"|\s*$|\s*[,.?!;:])",
    re.I,
)
_LOOKUP_TTL_SECONDS = 3600.0
_CONCRETE_CACHE: dict[str, tuple[list[dict] | None, float]] = {}
_IN_EXAMPLES_CACHE: dict[str, tuple[bool, float]] = {}
_ASKED_CACHE: dict[str, tuple[str, float]] = {}


def concrete_elements(element: str) -> list[dict] | None:
    """The validator's /concrete answer: [{"name", "object"}] that may be written for the element (itself,
    or an abstract one's concrete members, most used first); None for an unknown element or no validator."""
    from urllib import error, parse, request

    cached = _CONCRETE_CACHE.get(element)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/concrete?" + parse.urlencode({"element": element})
    try:
        with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("concrete elements not available: %s", exc)
        return None  # not cached: the validator may be back for the next question
    found = list(payload.get("concrete") or []) if payload.get("found") else None
    _CONCRETE_CACHE[element] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


def _in_examples(name: str) -> bool:
    from helpdesk.models import SourceChunk

    cached = _IN_EXAMPLES_CACHE.get(name)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    found = SourceChunk.objects.filter(
        repository_url__icontains="netex", source_path__startswith="examples/"
    ).filter(has_tag(name)).exists()
    _IN_EXAMPLES_CACHE[name] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


def asked_subject(question: str) -> str:
    """The noun phrase the example is of ("fare product", "timetabled passing time"); "" for a proper name
    ("an example for Ljubljana Bus Station")."""
    match = _SUBJECT_WIDE.search(question or "")
    subject = match.group("subject").strip() if match else example_subject(question)
    words = subject.split()
    if len(words) > 1 and all(word[:1].isupper() for word in words):
        return ""
    return subject


def asked_element(question: str) -> str:
    """The NeTEx object element the question asks an example of, or "" when unsure.

    The subject phrase, then its endings ("tram vehicle type" -> "vehicle type"), each as element names
    (candidate_element_names); an abstract one ("FareProduct") stands for its concrete members, most used in
    the standard's examples first (PreassignedFareProduct). Accepted only when the element is an object (a
    versioned entity, not a property or a list wrapper) and the standard's example files use it. "coach",
    "bus" and proper names stay unresolved: no concept matching here (it gave FareClasses for a fare
    product and TaxiStand for a bus)."""
    from helpdesk.services.schema_structure import candidate_element_names

    key = (question or "").strip().lower()
    cached = _ASKED_CACHE.get(key)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    found = ""
    words = asked_subject(question).split()
    for start in range(len(words)):
        phrase = " ".join(words[start:])
        for name in candidate_element_names(phrase[:1].upper() + phrase[1:]):
            entries = concrete_elements(name)
            if entries is None:
                continue
            found = next((e["name"] for e in entries if e.get("object") and _in_examples(e["name"])), "")
            if found:
                break
        if found:
            break
    if not found:
        # No subject phrase: an object the question names by its element name ("map a ferry service into a
        # NeTEx TemplateServiceJourney … create an XML file", prod req-mwb6auo0-n3jh83, 2026-11-10).
        found = next(iter(named_elements(question)), "")
    _ASKED_CACHE[key] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


# How a service runs, when the schema describes that with an object of its own and not with a value: the
# phrase and the element. A service that runs only when asked for ("the ferry operates … when there is
# demand", prod req-mwb6auo0-n3jh83, 2026-11-10) is a FLEXIBLE SERVICE, described by FlexibleServiceProperties
# ("Additional characteristics of a FLEXIBLE SERVICE"); the words alone resolve to TimeDemandTypeAssignment.
_SERVICE_CONDITIONS = (
    (
        re.compile(
            r"\b(?:on[\s-]demand|on\s+request|demand[\s-](?:responsive|driven|based)|dial[\s-]a[\s-]ride"
            r"|when\s+(?:there\s+is\s+(?:a\s+)?demand|(?:it\s+is\s+|they\s+are\s+)?(?:requested|booked|called))"
            r"|only\s+(?:if|when)\s+(?:requested|booked|passengers?\s+(?:ask|book|call)\w*)"
            r"|flexible\s+(?:services?|journeys?|timetables?|transport))\b",
            re.I,
        ),
        "FlexibleServiceProperties",
    ),
)
_STRUCTURE_CACHE: dict[str, tuple[dict | None, float]] = {}
MAX_CONDITION_CHILDREN = 16


def service_conditions(question: str) -> list[tuple[str, str]]:
    """How the question says the service runs, each with the element the schema describes it with:
    [("when there is demand", "FlexibleServiceProperties")]."""
    found = []
    for pattern, element in _SERVICE_CONDITIONS:
        match = pattern.search(question or "")
        if match:
            found.append((match.group(0), element))
    return found


def _structure(element: str) -> dict | None:
    from helpdesk.services.schema_structure import fetch_structure

    cached = _STRUCTURE_CACHE.get(element)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    found = fetch_structure(element)
    if found is not None:
        _STRUCTURE_CACHE[element] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


def _declared_parents(element: str) -> list[str]:
    from urllib import error, parse, request

    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/declarations?" + parse.urlencode({"q": element})
    try:
        with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            declarations = json.loads(response.read()).get("declarations") or []
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("declarations not available: %s", exc)
        return []
    return next((list(d.get("parents") or []) for d in declarations if d.get("name") == element), [])


_CONDITION_EXAMPLE_CACHE: dict[str, tuple[dict | None, float]] = {}
MAX_CONDITION_FILES = 20
MAX_CONDITION_EXAMPLE_LINES = 14


def condition_example(element: str, asked: str = "") -> dict | None:
    """Where the standard's example files write the element inside an object: {"parent", "after" (the sibling
    before it), "xml", "sourcePath"}, an object of the asked kind first. The model put FlexibleServiceProperties
    in the frame's list form inside the journey, given only the schema's parents (dev, 2026-11-10, 6 of 6 runs);
    the example shows it inside the ServiceJourney, right after calls."""
    from pathlib import Path

    from lxml import etree

    from helpdesk.models import SourceChunk

    key = f"{element}|{asked}"
    cached = _CONDITION_EXAMPLE_CACHE.get(key)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    base = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")
    rows = list(base.filter(has_tag(element)).values("source_path", "repository_url").distinct()[:MAX_CONDITION_FILES])
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, remove_blank_text=True, remove_comments=True)
    local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
    checkout_root = Path(getattr(settings, "SOURCE_CHECKOUT_DIR", "/app/repos"))
    found = None
    for row in sorted(rows, key=lambda r: r["source_path"]):
        path = checkout_root / row["repository_url"].rstrip("/").rsplit("/", 1)[-1] / row["source_path"]
        try:
            if path.stat().st_size > MAX_STANDARD_FILE_BYTES:
                continue
            root = etree.parse(str(path), parser).getroot()
        except (OSError, etree.XMLSyntaxError):
            continue
        for node in root.iter():
            parent = node.getparent()
            if local(node.tag) != element or parent is None or not parent.get("id") or not len(node):
                continue
            before = node.getprevious()
            while before is not None and not isinstance(before.tag, str):
                before = before.getprevious()
            text = etree.tostring(node, encoding="unicode")
            text = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", text)
            option = {
                "parent": local(parent.tag), "after": local(before.tag) if before is not None else "",
                "xml": "\n".join(indented_fragment(text).splitlines()[:MAX_CONDITION_EXAMPLE_LINES]),
                "sourcePath": row["source_path"],
            }
            if option["parent"] == asked:
                found = option
                break
            found = found or option
        if found is not None and found["parent"] == asked:
            break
    _CONDITION_EXAMPLE_CACHE[key] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


def conditions_block(conditions: list[tuple[str, str]], asked: str = "") -> str:
    """The prompt's lines for how the service runs: the element, where to write it (inside the asked object
    when the schema allows it there, at the place the standard's examples use), the shape the standard
    gives it, and its own children in the schema's words."""
    if not conditions:
        return ""
    lines = ["HOW THE SERVICE RUNS (model each in the element given, with the children that fit the question):"]
    for phrase, element in conditions:
        structure = _structure(element) or {}
        parents = _declared_parents(element)
        example = condition_example(element, asked)
        holder = asked if asked and asked in parents else (example or {}).get("parent", "")
        where = f"inside the {holder}" if holder else (f"in one of {', '.join(parents)}" if parents else "")
        if example and example.get("after") and holder:
            where += f", right after its {example['after']}"
        lines.append(
            f"- \u201c{phrase}\u201d: write one {element} element {where}; not a list wrapper, and no reference back to "
            f"the object it is in"
            + (f". {structure['documentation']}" if structure.get("documentation") else "")
        )
        if example:
            lines.append(
                f"  As the standard writes one ({example['sourcePath']}, inside a {example['parent']}; the shape and "
                "order only, its values are that file's, not the question's):"
            )
            lines.append(example["xml"])
        own = next((g for g in structure.get("groups") or [] if not g.get("inherited")), None)
        children = [c for c in (own or {}).get("children", []) if not c["name"].endswith("Ref")]
        if children:
            lines.append(f"  Children a {element} may have:")
        for child in children[:MAX_CONDITION_CHILDREN]:
            allowed = f" Allowed values: {', '.join(child['values'])}." if child.get("values") else ""
            lines.append(f"    {child['name']}: {(child.get('documentation') or '').strip()[:160]}{allowed}")
    return "\n".join(lines)


def condition_problems(fragment: str, conditions: list[tuple[str, str]]) -> list[str]:
    """For each condition, why the valid fragment does not model it: no such element, or one without
    content of its own (an empty FlexibleServiceProperties says nothing about how the service runs)."""
    root = _parsed(fragment)
    if root is None or not conditions:
        return []
    local = lambda tag: tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""  # noqa: E731
    problems = []
    for phrase, element in conditions:
        nodes = [node for node in root.iter() if local(node.tag) == element]
        if not nodes:
            problems.append(
                f"the question says the service runs “{phrase}”: describe that with a {element} (see HOW THE "
                f"SERVICE RUNS for where it goes), not in a Name or Description"
            )
        elif not any(len(node) for node in nodes):
            problems.append(
                f"the {element} for “{phrase}” is empty: give it the children from HOW THE SERVICE RUNS that "
                "say how the service runs"
            )
    return problems


def condition_places(fragment: str, conditions: list[tuple[str, str]]) -> list[dict]:
    """Where each condition is modelled: {"value": phrase, "element", "path"}."""
    root = _parsed(fragment)
    if root is None:
        return []
    local = lambda tag: tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""  # noqa: E731
    parents = {child: parent for parent in root.iter() for child in parent}
    places = []
    for phrase, element in conditions:
        node = next((n for n in root.iter() if local(n.tag) == element and len(n)), None)
        if node is None:
            continue
        path, up = [], parents.get(node)
        while up is not None and up is not root:
            path.append(local(up.tag))
            up = parents.get(up)
        places.append({"value": phrase, "element": element, "path": list(reversed(path))})
    return places


# An element name as written in the schema: two or more capitalised parts ("TemplateServiceJourney",
# "FlexibleLine"). One capitalised word ("Line", "Quay") is also an ordinary word at a sentence start.
_ELEMENT_NAME = re.compile(r"(?<![\w:])[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+(?![\w:])")


def named_elements(question: str) -> list[str]:
    """The NeTEx objects the question names by element name, most often named first, then in order of
    appearance: each an object (a versioned entity) the standard's example files use, an abstract one standing
    for its most used concrete member. Names that are a counted or wanted part ("a StopPlace with two
    AccessSpaces") are left out: the example is of the object that has them."""
    from collections import Counter

    tokens = _ELEMENT_NAME.findall(question or "")
    if not tokens:
        return []
    parts = {_singular(noun.split()[0]) for noun in wanted_parts(question)}
    parts |= {_singular(noun) for _, _, noun in counted_shapes(question)}
    counts = Counter(tokens)
    ordered = sorted(dict.fromkeys(tokens), key=lambda name: (-counts[name], tokens.index(name)))
    found: list[str] = []
    for name in ordered:
        if _singular(name) in parts:
            continue
        entries = concrete_elements(name)
        if not entries:
            continue
        member = next((e["name"] for e in entries if e.get("object") and _in_examples(e["name"])), "")
        if member and member not in found:
            found.append(member)
    return found


MAX_PART_FILES = 30
_PARTS_CACHE: dict[str, tuple[tuple[str, list[frozenset[str]]], float]] = {}


def _singular(noun: str) -> str:
    lowered = noun.lower()
    if lowered.endswith("ies") and len(lowered) > 4:
        return lowered[:-3] + "y"
    if lowered.endswith(("ses", "xes", "ches", "shes")):
        return lowered[:-2]
    if lowered.endswith("s") and not lowered.endswith("ss"):
        return lowered[:-1]
    return lowered


def part_holders(question: str) -> list[frozenset[str]]:
    """For each count the question gives ("49 seats", "1 wheelchair area"), the elements that may hold it:
    a name with a word starting with the noun (Seating, Wheelchair) and a declared type that accepts the
    number (SeatingCapacity, NumberOfWheelchairAreas, …). Counts of elements ("two quays") have no such
    holder and are left to the count check."""
    from urllib import error, parse, request

    counted = counted_shapes(question)
    if not counted:
        return []
    # A count of 0 or 1 is also a boolean ("1 wheelchair area" fitted WheelchairPassable, and a stop place
    # won): such counts are looked up as 2, which only number types accept.
    as_count = lambda count: str(max(count, 2))  # noqa: E731
    numbers = list(dict.fromkeys(as_count(count) for count, _, _ in counted))
    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/accepting?" + parse.urlencode([("value", n) for n in numbers[:12]])
    try:
        with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            accepting = json.loads(response.read()).get("accepting") or {}
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("part holders not available: %s", exc)
        return []
    sets = []
    for count, _, noun in counted:
        stem = _singular(noun)
        if len(stem) < 3:
            continue
        names = frozenset(
            name for name in accepting.get(as_count(count)) or []
            if any(word.startswith(stem) for word in _camel_words(name))
        )
        if names and names not in sets:
            sets.append(names)
    return sets


def _part_spread(groups: list[list]) -> int:
    """How far apart the parts sit in one object: the least, over one leaf of the first part as anchor, of
    the tree distances from it to the nearest leaf of each other part (0 for a single part)."""
    def path(node):
        return [node] + list(node.iterancestors())

    def distance(a, b) -> int:
        up = {node: depth for depth, node in enumerate(path(a))}
        for depth, node in enumerate(path(b)):
            if node in up:
                return up[node] + depth
        return 1 << 20

    if len(groups) < 2:
        return 0
    return min(
        sum(min(distance(anchor, other) for other in group[:20]) for group in groups[1:])
        for anchor in groups[0][:20]
    )


def asked_from_parts(question: str) -> tuple[str, list[frozenset[str]]]:
    """The object a question asks for when its noun names none ("a coach with 49 seats and 1 wheelchair
    area", "a bus with 50 seats"): the object, directly in a frame's list, that holds elements for most of
    the counted parts (part_holders) in the standard's example files: VehicleType for SeatingCapacity and
    WheelchairPlaceCapacity. ("", []) when no file holds them. Returns the part holders too, for the skeleton."""
    from collections import Counter
    from pathlib import Path

    from lxml import etree

    from helpdesk.models import SourceChunk

    key = (question or "").strip().lower()
    cached = _PARTS_CACHE.get(key)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    sets = part_holders(question)
    found = ""
    if sets:
        base = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")
        paths: Counter = Counter()
        repositories: dict[str, str] = {}
        for names in sets:
            condition = None
            for name in sorted(names):
                condition = has_tag(name) if condition is None else condition | has_tag(name)
            for row in base.filter(condition).values("source_path", "repository_url").distinct()[:2000]:
                paths[row["source_path"]] += 1
                repositories[row["source_path"]] = row["repository_url"]
        local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False)
        checkout_root = Path(getattr(settings, "SOURCE_CHECKOUT_DIR", "/app/repos"))
        tally: Counter = Counter()
        closeness: dict[str, tuple[int, int]] = {}  # object name -> (parts covered, least spread)
        for source_path, _ in sorted(paths.items(), key=lambda item: (-item[1], item[0]))[:MAX_PART_FILES]:
            path = checkout_root / repositories[source_path].rstrip("/").rsplit("/", 1)[-1] / source_path
            try:
                if path.stat().st_size > MAX_STANDARD_FILE_BYTES:
                    continue
                root = etree.parse(str(path), parser).getroot()
            except (OSError, etree.XMLSyntaxError):
                continue
            leaves: dict = {}  # member -> set index -> its leaves
            for leaf in root.iter():
                name = local(leaf.tag)
                hits = [index for index, names in enumerate(sets) if name in names]
                if not hits:
                    continue
                member = next(
                    (a for a in leaf.iterancestors()
                     if a.getparent() is not None and a.getparent().getparent() is not None
                     and local(a.getparent().getparent().tag).endswith("Frame") and a.get("id")),
                    None,
                )
                if member is not None:
                    for index in hits:
                        leaves.setdefault(member, {}).setdefault(index, []).append(leaf)
            for member, by_set in leaves.items():
                spread = _part_spread(list(by_set.values()))
                name = local(member.tag)
                covered_now = len(by_set)
                best = closeness.get(name)
                if best is None or (covered_now, -spread) > (best[0], -best[1]):
                    closeness[name] = (covered_now, spread)
                tally[name] += 1
        # The object whose parts are described together wins: in a VehicleType SeatingCapacity and
        # WheelchairPlaceCapacity sit side by side in one PassengerCapacity; a StopPlace has seats and
        # wheelchair turning circles on unrelated equipment, far apart (and more stop places in the examples).
        ranked = sorted(closeness, key=lambda name: (-closeness[name][0], closeness[name][1], -tally[name], name))
        for name in ranked:
            entries = concrete_elements(name) or []
            if any(e.get("name") == name and e.get("object") for e in entries):
                found = name
                break
    result = (found, sets if found else [])
    _PARTS_CACHE[key] = (result, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return result


MAX_SKELETON_ELEMENTS = 40
# A linked object that holds the question's kind of value (a FareTable cell with the price of a fare
# product) gets a smaller budget: it shows where such values go, the asked object stays the main shape.
MAX_COMPANION_ELEMENTS = 24
MAX_SKELETON_FILES = 8
MAX_SKELETON_TRIES = 3
MAX_OBJECTS_PER_FILE = 20
MAX_SKELETON_SCAN_FILES = 120
# Up to how many objects (elements with an id) above a reference to the asked object a holder of the
# value may sit: a Cell (1), a FareTable around the cells (2-3) in the standard's fare files.
MAX_COMPANION_LEVELS = 3
_SKELETON_CACHE: dict[tuple, tuple[dict | None, float]] = {}

_HOLDERS_CACHE: dict[str, tuple[frozenset[str], float]] = {}
# A value that more elements accept says nothing about where it goes: a bare number fits some 280 (counts,
# orders, amounts); a currency code 2, a date 35, a time 52 (benchmark questions, 2026-11-10).
MAX_VALUE_HOLDERS = 60


def value_holders(values: list[str]) -> list[frozenset[str]] | None:
    """For each of the question's values the schema can place, the elements whose declared content is
    specific and accepts it (validator /accepting): "EUR" -> Currency, DefaultCurrency; "08:30" -> the time
    elements. Free text (a name) fits no specific element and a bare number too many (MAX_VALUE_HOLDERS):
    both are left out; values with the same holders count once. None without the validator."""
    from urllib import error, parse, request

    missing = [v for v in dict.fromkeys(values) if not ((c := _HOLDERS_CACHE.get(v)) and c[1] > time.monotonic())]
    if missing:
        url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/accepting?" + parse.urlencode([("value", v) for v in missing[:12]])
        try:
            with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read())
        except (error.URLError, OSError, ValueError) as exc:
            logger.info("value holders not available: %s", exc)
            return None
        if not payload.get("found"):
            return None
        for value, names in (payload.get("accepting") or {}).items():
            _HOLDERS_CACHE[value] = (frozenset(names), time.monotonic() + _LOOKUP_TTL_SECONDS)
    holders = [_HOLDERS_CACHE[v][0] for v in dict.fromkeys(values) if v in _HOLDERS_CACHE]
    return list(dict.fromkeys(h for h in holders if h and len(h) <= MAX_VALUE_HOLDERS))


def _holder_leaves(node, holders: list[frozenset[str]], local) -> dict:
    """The first leaf element under the node for each set of holders: {index: leaf}. An object (an element
    with an id) the question names as a part ("a stop place with a parking") is held by itself."""
    found: dict = {}
    for leaf in node.iter():
        if not isinstance(leaf.tag, str):
            continue
        if leaf.get("id") is None and (len(leaf) or not (leaf.text or "").strip()):
            continue
        name = local(leaf.tag)
        for index, names in enumerate(holders):
            if index not in found and name in names:
                found[index] = leaf
        if len(found) == len(holders):
            break
    return found


def _camel_words(name: str) -> list[str]:
    return [word.lower() for word in re.findall(r"[A-Z][a-z0-9]*", name)]


def _skeleton_tree(obj, local, protect=frozenset(), limit=MAX_SKELETON_ELEMENTS):
    """A copy of the object with at most two of each repeated child (a choice of at least two points
    keeps two), no comments, no attributes of other namespaces, and local names; the protected leaves (the
    holders of the question's kind of value) and the path to them stay."""
    from collections import Counter

    from lxml import etree

    on_path = set()
    for leaf in protect:
        on_path.add(leaf)
        on_path.update(leaf.iterancestors())
    pinned = set()

    def copy_of(node):
        attributes = {
            k: v for k, v in node.attrib.items()
            if not k.startswith("{") or k.startswith("{http://www.w3.org/XML/1998/namespace}")
        }
        new = etree.Element(local(node.tag), attrib=attributes)
        new.text = node.text if node.text and node.text.strip() else None
        if node in on_path:
            pinned.add(new)
        seen: Counter = Counter()
        for child in node:
            if not isinstance(child.tag, str):
                continue
            name = local(child.tag)
            if seen[name] >= 2 and child not in on_path:
                continue
            seen[name] += 1
            new.append(copy_of(child))
        return new

    tree = copy_of(obj)
    # Cut the deepest subtrees first until the skeleton is small enough to read.
    while sum(1 for _ in tree.iter()) > limit:
        removable = [e for e in tree.iter() if e is not tree and e not in pinned]
        if not removable:
            break
        deepest = max(removable, key=lambda e: sum(1 for _ in e.iterancestors()))
        deepest.getparent().remove(deepest)
    return tree


def _companion(obj, frame, missing: list[frozenset[str]], local):
    """The smallest object in the frame that refers to obj and holds leaves for the missing values, or
    (None, {}): the nearest objects (elements with an id) above each reference to obj, up to
    MAX_COMPANION_LEVELS, outside obj and not around it."""
    obj_id = obj.get("id")
    if not obj_id or not missing:
        return None, {}
    around = set(obj.iterancestors())
    inside = set(obj.iter())
    best, best_key, best_leaves = None, None, {}
    for ref in frame.iter():
        if not isinstance(ref.tag, str) or ref.get("ref") != obj_id or ref in inside:
            continue
        level = 0
        for holder in ref.iterancestors():
            if holder is frame or local(holder.tag).endswith("Frame"):
                break
            if holder.get("id") is None or holder in around:
                continue
            level += 1
            leaves = _holder_leaves(holder, missing, local)
            if leaves:
                key = (-len(leaves), sum(1 for _ in holder.iter()))
                if best_key is None or key < best_key:
                    best, best_key, best_leaves = holder, key, leaves
                if len(leaves) == len(missing):
                    break
            if level >= MAX_COMPANION_LEVELS:
                break
    return best, best_leaves


def _frame_object(obj, frame, missing: list[frozenset[str]], local):
    """Without a linked holder, an object the question names as a part that sits in the same frame
    (the Norwegian stop place file lists its parkings next to the stop place, with no reference to it), the
    smallest first: (object, {index: object}) or (None, {})."""
    inside = set(obj.iter())
    named = {index: names for index, names in enumerate(missing) if len(names) == 1}
    best, best_size, best_index = None, None, None
    for node in frame.iter():
        if not isinstance(node.tag, str) or node in inside or node.get("id") is None:
            continue
        index = next((i for i, names in named.items() if local(node.tag) in names), None)
        if index is None:
            continue
        size = sum(1 for _ in node.iter())
        if best_size is None or size < best_size:
            best, best_size, best_index = node, size, index
    if best is None:
        return None, {}
    return best, {best_index: best}


def skeleton_parts(root, element: str, holders: list[frozenset[str]], local):
    """The object of the element to show from one example file, its frame, and a linked object holding
    elements for the question's values the object itself lacks: (obj, frame, companion, protected leaves,
    how many of the values they place), or None. The object placing most values wins, the first on a tie."""
    best = None
    seen = 0
    for obj in root.iter():
        if not isinstance(obj.tag, str) or local(obj.tag) != element:
            continue
        frame = next((a for a in obj.iterancestors() if local(a.tag).endswith("Frame")), None)
        if frame is None:
            continue
        own = _holder_leaves(obj, holders, local)
        missing = [names for index, names in enumerate(holders) if index not in own]
        companion, extra = _companion(obj, frame, missing, local) if missing else (None, {})
        if companion is None and missing:
            companion, extra = _frame_object(obj, frame, missing, local)
        covered = len(own) + len(extra)
        if best is None or covered > best[4]:
            best = (obj, frame, companion, frozenset(own.values()), covered, frozenset(extra.values()))
        seen += 1
        if covered == len(holders) or seen >= MAX_OBJECTS_PER_FILE:
            break
    if best is None:
        return None
    obj, frame, companion, own_leaves, covered, extra_leaves = best
    return obj, frame, companion, own_leaves | extra_leaves, covered


def skeleton_xml(obj, frame, companion, protect, local) -> str:
    """The frame shell around the object (and the linked object), in the file's order, with list wrappers
    and ancestors without their references; a reference to an object the skeleton does not hold is shown
    version-less, as the prompt asks the model to write it (the file's versioned references made it write
    keyref-failing ones)."""
    from lxml import etree

    kept = [node for node in (obj, companion) if node is not None]
    path = {a for node in kept for a in node.iterancestors()}
    shell_attrib = lambda node: {  # noqa: E731
        k: v for k, v in node.attrib.items() if not k.endswith("Ref") and not k.startswith("{")
    }

    def shell(node):
        new = etree.Element(local(node.tag), attrib=shell_attrib(node))
        for child in node:
            if child is obj:
                new.append(_skeleton_tree(child, local, protect & set(child.iter())))
            elif child is companion:
                new.append(_skeleton_tree(child, local, protect & set(child.iter()), MAX_COMPANION_ELEMENTS))
            elif child in path:
                new.append(shell(child))
        return new

    top = shell(frame)
    defined = {node.get("id") for node in top.iter() if node.get("id")}
    for node in top.iter():
        if node.tag.endswith("Ref") and node.get("ref") and node.get("ref") not in defined:
            node.attrib.pop("version", None)
    return etree.tostring(top, encoding="unicode")


def skeleton_for(
    element: str, values: list[str] | None = None, parts: list[frozenset[str]] | None = None,
    objects: list[str] | None = None,
) -> dict | None:
    """An object of the element from the standard's example files, as a shape for the model, with its frame
    and list wrapper, at most two of each repeated child, cut to MAX_SKELETON_ELEMENTS.

    When the question gives values the schema places in specific elements (value_holders: 5 in Amount, EUR
    in Currency) and the object has none of those elements, the object linked to it that has them comes along (2026-11-10: the fare product skeleton had no
    price, as in 72 of the 73 example files with one, where the price is in a FareTable that refers to the
    product; the model's first attempt then wrote an abstract FarePrice). Files whose objects hold more of
    the kinds come first, then files whose name has more of the element's words; the first of
    MAX_SKELETON_TRIES skeletons that validates wins, else the first (a shape, not the answer).
    {"xml", "element", "sourcePath", "repositoryUrl", "valid", "companion"}; cached per element and holders
    for an hour (the files change at the nightly source refresh)."""
    from pathlib import Path

    from lxml import etree

    from helpdesk.models import SourceChunk

    holders = (value_holders(values) or []) if values else []
    # The elements for the question's counted parts (asked_from_parts) count as values do.
    holders = list(dict.fromkeys(holders + list(parts or [])))
    # Objects the question names as parts ("with a parking") count as values do: one inside the asked
    # object, or one linked to it (a Parking refers to its StopPlace by ParentSiteRef) comes along.
    holders = list(dict.fromkeys(holders + [frozenset([name]) for name in objects or [] if name != element]))
    key = (element, tuple(holders))
    cached = _SKELETON_CACHE.get(key)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    base = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")
    rows = {r["source_path"]: r for r in base.filter(has_tag(element)).values("source_path", "repository_url")[:5000]}
    # A file named after the asked object and the parts the question names ("StopPlace-with-...-parking")
    # comes first.
    words = _camel_words(element) + [w for name in objects or [] if name != element for w in _camel_words(name)]

    def name_score(source_path: str) -> int:
        name = re.sub(r"[^a-z0-9]", "", source_path.rsplit("/", 1)[-1].lower())
        return sum(1 for word in words if word in name)

    # With values every file is scored (72 fare product files parse and score in under a second; the
    # result is cached): the few whose object is linked to an Amount and a Currency rank low by name.
    ranked = sorted(rows.items(), key=lambda item: (-name_score(item[0]), item[0]))[: MAX_SKELETON_SCAN_FILES if holders else MAX_SKELETON_FILES]
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, remove_blank_text=True)
    local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
    checkout_root = Path(getattr(settings, "SOURCE_CHECKOUT_DIR", "/app/repos"))
    options = []
    for order, (source_path, row) in enumerate(ranked):
        path = checkout_root / row["repository_url"].rstrip("/").rsplit("/", 1)[-1] / source_path
        try:
            if path.stat().st_size > MAX_STANDARD_FILE_BYTES:
                continue
            tree = etree.parse(str(path), parser)
        except (OSError, etree.XMLSyntaxError):
            continue
        parts = skeleton_parts(tree.getroot(), element, holders, local)
        if parts is None:
            continue
        obj, frame, companion, protect, covered = parts
        linked = companion is not None and any(node.get("ref") == obj.get("id") for node in companion.iter())
        options.append((-covered, order, source_path, row, skeleton_xml(obj, frame, companion, protect, local),
                        local(companion.tag) if companion is not None else "", linked))
        if sum(1 for option in options if -option[0] == len(holders)) >= MAX_SKELETON_TRIES:
            break  # enough files place every value (without values: any file does); parse no more
    options.sort(key=lambda option: option[:2])
    candidates: list[dict] = []
    for _, _, source_path, row, fragment, companion, linked in options[:MAX_SKELETON_TRIES]:
        try:
            fragment, valid = _without_emptied(fragment)
        except ValidatorUnavailable:
            valid = False
        candidates.append({
            "xml": fragment, "element": element, "sourcePath": source_path,
            "repositoryUrl": row["repository_url"], "valid": valid, "companion": companion,
            "companionLinked": linked,
        })
        if valid:
            break
    found = next((c for c in candidates if c["valid"]), candidates[0] if candidates else None)
    _SKELETON_CACHE[key] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


_MISSING_CHILD = re.compile(r"Element '(?:\{[^}]*\})?([\w.-]+)': Missing child element")
MAX_SKELETON_REPAIRS = 3


def _without_emptied(fragment: str) -> tuple[str, bool]:
    """The skeleton validated, after dropping the elements the cut to MAX_SKELETON_ELEMENTS left without
    a child they need (privateCodes, AccessibilityAssessment, parkingProperties: 2026-11-10, five of six
    stop place skeletons with a parking failed only on these), up to MAX_SKELETON_REPAIRS rounds:
    (fragment, valid). Elements with text or with children stay."""
    from lxml import etree

    for _ in range(MAX_SKELETON_REPAIRS + 1):
        checked = validate_fragment(fragment)
        if checked.get("valid"):
            return fragment, True
        names = {m.group(1) for error in checked.get("errors") or [] if (m := _MISSING_CHILD.search(error))}
        if not names:
            break
        root = etree.fromstring(f"<root>{fragment}</root>")
        emptied = [
            node for node in root.iter()
            if node is not root and node.tag in names and not len(node) and not (node.text or "").strip()
        ]
        if not emptied:
            break
        for node in emptied:
            node.getparent().remove(node)
        fragment = "".join(etree.tostring(child, encoding="unicode") for child in root)
    return fragment, False


def skeleton_block(skeleton: dict) -> str:
    return (
        f"SKELETON: a {skeleton['element']}, the kind of object the question asks for, from the standard's example "
        f"file {skeleton['sourcePath']}, with its frame and list wrapper:\n{indented_fragment(skeleton['xml'])}\n"
        "Write the question's object in this shape: keep its nesting and element order; put the question's values in "
        "the elements that hold such values; drop optional elements the question does not need; keep every element "
        "the schema requires and the references (as version-less references when their target is not in the frame). "
        "Its ids are that file's: do not reuse them; give the objects you write ids of your own, named after what the "
        "question calls them ('hd:SSP_SideA' and 'hd:SSP_SideB' for the two sides of a river); references to the "
        "standard's shared codes (TypeOf…) may stay. An id names an object and holds none of the question's values: "
        "a name or code the question gives still goes in its own element. "
        "The skeleton keeps at most two of a repeated element: write as many as the question asks for."
        + (
            (
                f" The skeleton also holds a {skeleton['companion']} from the same file that refers to the "
                f"{skeleton['element']} and has elements for values like the question's: put such values where that "
                "file puts them."
                if skeleton.get("companionLinked", True) else
                f" The skeleton also holds a {skeleton['companion']} from the same frame, a part the question names: "
                f"write it where that file does, as its own object in the frame next to the {skeleton['element']}, "
                "not inside it."
            )
            if skeleton.get("companion") else ""
        )
    )


def missing_asked_object(root, element: str, local) -> str:
    """The feedback for a frame without the asked object. The check runs after the value check, so the frame
    already holds the question's values; when they sit in objects of another kind of frame than the one the
    standard puts the asked object in, no single frame holds both, and the model went back and forth between
    the two frames until it ran out of attempts (2026-11-14: a line with timed departures, a frame of journeys
    that refer to the line, then a frame with the line alone and no times; 1 of 10 generated). The feedback says
    which reference already points at the asked object and how two frames go together."""
    frames = [local(child.tag) for child in root if local(child.tag).endswith("Frame")]
    written = frames[0] if len(frames) == 1 else ""
    refs = sorted({
        node.get("ref") for node in root.iter()
        if local(node.tag) == f"{element}Ref" and node.get("ref")
    })
    referred = f", only a reference to one ({', '.join(refs)})" if refs else ""
    keep = (
        f" Keep the objects that hold the question's values. If the standard puts a {element} in another kind of "
        f"frame than this {written} (the SKELETON or the evidence examples show which), write a CompositeFrame "
        f"whose <frames> holds both: the {element} in its frame, the objects you wrote in this {written}."
        if written and written != "CompositeFrame" else ""
    )
    return (
        f"the question asks for a {element}; the frame has none{referred}. Write the {element} itself (the "
        f"SKELETON shows one) with the question's values in it or in objects it is linked to by references.{keep}"
    )


def asked_object_problem(fragment: str, element: str, values: list[str], question: str = "") -> str:
    """Why a valid fragment does not answer the question's object, or "": it has no such element, or none of
    the question's values sits in it or in an object linked to it by a reference (a Parking whose
    ParentSiteRef is the stop place, a DeckPlan the vehicle type refers to); 5 EUR in a price group that
    does not refer to the fare product fails (2026-11-10). Counts ("2 decks") are checked as counts, not here."""
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return ""
    local = lambda tag: tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""  # noqa: E731
    objects = [node for node in root.iter() if local(node.tag) == element]
    if not objects:
        return missing_asked_object(root, element, local)
    counted = {written for _, written, _ in counted_shapes(question)}
    wanted = [value for value in values if value not in counted]
    if not wanted:
        return ""
    parents = {child: parent for parent in root.iter() for child in parent}

    def owner(node):
        """The nearest enclosing object (an element with an id) that is not a frame."""
        while node is not None and node is not root:
            if node.get("id") and not local(node.tag).endswith("Frame"):
                return node
            node = parents.get(node)
        return None

    ids = {obj.get("id") for obj in objects if obj.get("id")}
    referred = {node.get("ref") for obj in objects for node in obj.iter() if node.get("ref")}
    linked = list(objects)
    for node in root.iter():
        if node.get("ref") in ids and (holder := owner(node)) is not None:
            linked.append(holder)  # refers to the asked object
        if node.get("id") in referred and node not in linked:
            linked.append(node)  # the asked object refers to it
    for obj in linked:
        for node in obj.iter():
            if any(holds_value(node.text or "", v) or any(holds_value(a, v) for a in node.attrib.values()) for v in wanted):
                return ""
        if any(is_duration_value(v) and times_apart(obj, duration_seconds(v)) for v in wanted):
            return ""  # a duration as two times that far apart in the object
    return (
        f"the question asks for a {element}: the values {', '.join(wanted)} are neither in it nor in an object that "
        f"refers to it or that it refers to. Put them in the {element}, or in an object linked to it by a reference, "
        "in the elements the schema has for such values."
    )


# --- objects linked to the asked object (plan 2026-11-12 P2) ------------------------------------

def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def unlinked_objects(fragment: str, asked: str) -> list[dict]:
    """Objects of the fragment (elements with an id that are not frames) not connected to the asked object:
    {"element", "id", "node"}. Connected: one inside the other (the nearest enclosing object), or a ref
    attribute equal to an object's id. Prod req-mwdzf8px-3qfhdl (2026-11-12): a Line, two stop points, a
    vehicle type and a day type, none referring to another; the conditions stood only in a Description.
    Empty without an asked object in the fragment."""
    from xml.etree import ElementTree

    if not asked:
        return []
    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return []
    parents = {child: parent for parent in root.iter() for child in parent}

    def owner(node):
        while node is not None and node is not root:
            if node.get("id") and not _local(node.tag).endswith("Frame"):
                return node
            node = parents.get(node)
        return None

    objects = [node for node in root.iter() if node.get("id") and not _local(node.tag).endswith("Frame")]
    by_id = {node.get("id"): node for node in objects}
    edges: dict[int, set[int]] = {id(node): set() for node in objects}

    def join(a, b):
        edges[id(a)].add(id(b))
        edges[id(b)].add(id(a))

    for node in objects:
        if (outer := owner(parents.get(node))) is not None:
            join(node, outer)
    for node in root.iter():
        target = by_id.get(node.get("ref"))
        if target is not None and (holder := owner(node)) is not None and holder is not target:
            join(holder, target)
    start = {id(node) for node in objects if _local(node.tag) == asked}
    if not start:
        return []
    seen, todo = set(start), list(start)
    while todo:
        for other in edges[todo.pop()] - seen:
            seen.add(other)
            todo.append(other)
    return [{"element": _local(n.tag), "id": n.get("id"), "node": n} for n in objects if id(n) not in seen]


_LINK_CACHE: dict[tuple[str, str], tuple[dict | None, float]] = {}
MAX_LINK_FILES = 20
MAX_LINK_EXCERPT_LINES = 20
_REQUIRED_CACHE: dict[tuple[str, ...], tuple[list[tuple[frozenset[str], int]], float]] = {}


def required_slots(path: tuple[str, ...]) -> list[tuple[frozenset[str], int]]:
    """The required slots of the element at the end of a path from a global element (validator /required), each
    as the names that fill it and how many it needs; [] when unknown or the validator is unavailable."""
    from urllib import error, parse, request

    cached = _REQUIRED_CACHE.get(path)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/required?" + parse.urlencode({"path": "/".join(path)})
    try:
        with request.urlopen(url, timeout=VALIDATOR_TIMEOUT_SECONDS) as response:
            found = [
                (frozenset(slot.get("names") or []), int(slot.get("min") or 1))
                for slot in json.loads(response.read()).get("required") or []
            ]
    except (error.URLError, OSError, ValueError) as exc:
        logger.info("required children not available: %s", exc)
        return []
    _REQUIRED_CACHE[path] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


def _holder_shape(node, paths: list[list[str]], required=None) -> dict:
    """Where a linking object sits in a standard example ("place": its frame and list, ["TimetableFrame",
    "vehicleJourneys"]) and its shape cut to the paths to its references ("excerpt", at most
    MAX_LINK_EXCERPT_LINES lines). After the link feedback the model wrote the ServiceJourney in the
    ServiceFrame, under a list that does not exist there (gen33, 7 of 9 linked attempts; revision 4).

    The cut keeps, at every kept element, as many children as each slot its content model requires needs
    (`required(path)`: [(names, minimum)], default the validator's): cut to the paths alone a Call lost its ScheduledStopPointRef, and 16 of 16
    `Arrival` failures that followed said a Call needs one (plan 2026-11-13, B1). "requiredRefs" lists the
    references kept that way ({"parent", "ref"}), so the feedback can say which objects they need."""
    from copy import deepcopy

    from lxml import etree

    required = required_slots if required is None else required

    place, up = [], node.getparent()
    while up is not None:
        place.append(_local(up.tag))
        if place[-1].endswith("Frame"):
            break
        up = up.getparent()
    if not place or not place[-1].endswith("Frame"):
        place = []
    shape = deepcopy(node)
    # The elements themselves, not their id(): lxml frees an element's proxy when nothing holds it, so an id
    # taken on one access need not match the next.
    kept = [shape]
    for path in paths:
        current = shape
        for step in path:
            current = next((child for child in current if isinstance(child.tag, str) and _local(child.tag) == step), None)
            if current is None:
                break
            kept.append(current)

    def is_kept(element) -> bool:
        return any(element is other for other in kept)

    def path_of(element) -> tuple[str, ...]:
        steps = []
        while element is not None:
            steps.append(_local(element.tag))
            element = element.getparent()
        return tuple(reversed(steps))

    required_refs = []
    pending = list(kept)
    while pending:
        element = pending.pop(0)
        children = [child for child in element if isinstance(child.tag, str)]
        if not children:
            continue
        for names, minimum in required(path_of(element)):
            short = minimum - sum(1 for child in children if _local(child.tag) in names and is_kept(child))
            for child in [child for child in children if _local(child.tag) in names and not is_kept(child)][: max(0, short)]:
                kept.append(child)
                pending.append(child)
                item = {"parent": _local(element.tag), "ref": _local(child.tag)}
                if item["ref"].endswith("Ref") and len(item["ref"]) > 3 and item not in required_refs:
                    required_refs.append(item)
    for element in list(shape.iter()):
        if not is_kept(element) and element.getparent() is not None:
            element.getparent().remove(element)
    for element in shape.iter():
        element.tail = None
        if len(element):
            element.text = None
    text = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", etree.tostring(shape, encoding="unicode", with_tail=False))
    return {
        "place": list(reversed(place)),
        "excerpt": "\n".join(indented_fragment(text).splitlines()[:MAX_LINK_EXCERPT_LINES]),
        "requiredRefs": required_refs,
    }


def link_example(element: str, asked: str) -> dict | None:
    """How the standard's example files link an object of one kind to the asked one: {"holder", "toElement",
    "toAsked", "sourcePath"}, the paths from the holder to each reference ("toAsked" empty when the holder is
    the asked object, "toElement" empty when it is the element), and "holders": every object kind that holds
    both references, each with its paths and "files", the number of files that show it. The asked object or the element holding the
    other's reference first, else the kind in most files (a ServiceJourney with a LineRef and calls with
    ScheduledStopPointRefs; by size alone a Block won for a VehicleType). The validator's lists of parents are
    cut at a few names and stop at list wrappers (DayTypeRef -> dayTypes), so they cannot name the linking
    object; the examples can."""
    from pathlib import Path

    from lxml import etree

    from helpdesk.models import SourceChunk

    key = (element, asked)
    cached = _LINK_CACHE.get(key)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]
    ref_element, ref_asked = f"{element}Ref", f"{asked}Ref"
    base = SourceChunk.objects.filter(repository_url__icontains="netex", source_path__startswith="examples/")

    def files(*names):
        query = has_tag(names[0])
        for name in names[1:]:
            query |= has_tag(name)
        return dict(base.filter(query).values_list("source_path", "repository_url").distinct())

    with_element, with_asked = files(ref_element, element), files(ref_asked, asked)
    candidates = sorted(set(with_element) & set(with_asked))[:MAX_LINK_FILES]
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False, remove_comments=True)
    checkout_root = Path(getattr(settings, "SOURCE_CHECKOUT_DIR", "/app/repos"))
    direct = None
    bridges: dict[str, dict] = {}
    for source_path in candidates:
        path = checkout_root / with_element[source_path].rstrip("/").rsplit("/", 1)[-1] / source_path
        try:
            if path.stat().st_size > MAX_STANDARD_FILE_BYTES:
                continue
            root = etree.parse(str(path), parser).getroot()
        except (OSError, etree.XMLSyntaxError):
            continue
        # For each object, the path to the first reference of each kind inside it.
        reaches: dict = {}
        for node in root.iter():
            name = _local(node.tag)
            if name not in (ref_element, ref_asked):
                continue
            steps, up = [name], node.getparent()
            while up is not None:
                up_name = _local(up.tag)
                if up.get("id") and not up_name.endswith("Frame"):
                    reaches.setdefault(up, {}).setdefault(name, list(reversed(steps)))
                steps.append(up_name)
                up = up.getparent()
        in_file = set()
        for node, refs in reaches.items():
            name = _local(node.tag)
            if name == asked and ref_element in refs:
                direct = direct or {"holder": asked, "toElement": refs[ref_element], "toAsked": [], "sourcePath": source_path}
            elif name == element and ref_asked in refs:
                direct = direct or {"holder": element, "toElement": [], "toAsked": refs[ref_asked], "sourcePath": source_path}
            elif ref_element in refs and ref_asked in refs and name not in in_file:
                in_file.add(name)
                if name not in bridges:
                    bridges[name] = {
                        "holder": name, "toElement": refs[ref_element], "toAsked": refs[ref_asked], "sourcePath": source_path,
                        "files": 0, **_holder_shape(node, [refs[ref_element], refs[ref_asked]]),
                    }
                bridges[name]["files"] += 1
        if direct is not None:
            break
    found = direct or (max(bridges.values(), key=lambda entry: entry["files"]) if bridges else None)
    if found is not None:
        found = {**found, "holders": bridges}
    _LINK_CACHE[key] = (found, time.monotonic() + _LOOKUP_TTL_SECONDS)
    return found


def _asked_for(node, question: str, values: list[str]) -> bool:
    """Whether the question asks for this object: one of its values is in it, or a word of its element name or
    of its Name is in the question ("low-floor" -> a VehicleType named "Low-floor bus")."""
    texts = [text for n in node.iter() for text in [n.text or "", *n.attrib.values()] if text.strip()]
    if any(holds_value(text, value) for text in texts for value in values):
        return True
    asked_words = {_stem(word) for word in re.findall(r"[a-z]{4,}", (question or "").lower())}
    words = [w.lower() for w in _camel_words(_local(node.tag)) if len(w) >= 4]
    name = next((n.text or "" for n in node if _local(n.tag) == "Name"), "")
    words += re.findall(r"[a-z]{4,}", name.lower())
    return any(_stem(word) in asked_words for word in words)


def _defined_kinds(fragment: str) -> set[str]:
    """The element names of the fragment's elements that have an id: the kinds of object it defines."""
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(f'<root xmlns="{NETEX_NAMESPACE}">{fragment}</root>')
    except ElementTree.ParseError:
        return set()
    return {_local(node.tag) for node in root.iter() if node.get("id")}


def link_problems(fragment: str, asked: str, question: str = "", values: list[str] = ()) -> list[str]:
    """One feedback line per kind of object that nothing links to the asked object, with how the standard's
    examples link the two."""
    unlinked = unlinked_objects(fragment, asked)
    kinds = list(dict.fromkeys(item["element"] for item in unlinked))
    examples = {}
    for element in kinds:
        try:
            examples[element] = link_example(element, asked)
        except Exception as exc:  # the index unavailable: the plain request to link it
            logger.info("link example not available: %s", exc)
            examples[element] = None
    # One linking object for several kinds where the examples allow it (a ServiceJourney for the stop points
    # and the vehicle type), else each kind's own.
    from collections import Counter

    shared = Counter(name for example in examples.values() if example for name in example.get("holders") or {})
    problems = []
    shown: set[str] = set()
    defined = _defined_kinds(fragment)
    told: set[tuple[str, str]] = set()
    for element in kinds:
        items = [item for item in unlinked if item["element"] == element]
        ids = ", ".join(item["id"] for item in items[:3])
        line = f"the frame defines a {element} ({ids}) that nothing links to the {asked}. "
        shape = ""
        example = examples[element]
        if example and example["holder"] not in (asked, element) and len(example.get("holders") or {}) > 1:
            holders = example["holders"]
            example = holders[max(holders, key=lambda name: (shared[name], holders[name]["files"]))]
        if example is None:
            line += f"Link it to the {asked} by a reference, directly or through another object in the frame"
        elif example["holder"] == asked:
            line += f"Give the {asked} a reference to it, as the standard's examples do: {' > '.join([asked, *example['toElement']])}"
        elif example["holder"] == element:
            line += f"Give the {element} a reference to the {asked}, as the standard's examples do: {' > '.join([element, *example['toAsked']])}"
        else:
            holder = example["holder"]
            line += (
                f"The standard's examples link them through a {holder} ({example['sourcePath']}): "
                f"{' > '.join([holder, *example['toElement']])} and {' > '.join([holder, *example['toAsked']])}. "
                f"Write such a {holder} in the frame with both references"
            )
            if example.get("place"):
                line += f", where the example has it: {' > '.join([*example['place'], holder])}"
            if example.get("excerpt") and holder not in shown:
                shown.add(holder)
                shape = f"\n  Its shape there (the structure only, not the ids or values):\n{example['excerpt']}"
            # For each kind, also when the holder's shape was shown for another kind: the StopPlace's path through
            # a Call came second to the VehicleType's, and its Call lacked the ScheduledStopPointRef (B1 benchmark).
            for item in example.get("requiredRefs") or []:
                kind = item["ref"][: -len("Ref")]
                if kind and kind not in defined and (item["parent"], item["ref"]) not in told:
                    told.add((item["parent"], item["ref"]))
                    shape += f"\n  A {item['parent']} also needs a {item['ref']}: define a {kind} for each {item['parent']} and refer to it."
        if not any(_asked_for(item["node"], question, list(values)) for item in items):
            line += ", or remove it if the question does not need it"
        problems.append(line + "." + shape)
    return problems


def missing_value_error(value: str, question: str, fragment: str = "", values: list[str] | None = None) -> str:
    """The feedback for a value the valid fragment lacks. When the value sits in a Name or Description together
    with another of the question's values ("Maribor - Ptuj"), it also says where such a value goes: told only
    that a value must be an element's whole content, the model split the name into Name "Maribor" and ShortName
    "Ptuj" of the one Line (21 of 21 such examples followed this feedback; plan 2026-11-12 revision 4, T0)."""
    written = {iso: text for text, _, iso in durations(question)}
    if value in written:
        return (
            f"the duration {written[value]} ({value}) from the question is missing: write it as the xs:duration "
            f"{value} in an element that holds a duration, or as two times {written[value]} apart in the same "
            "object (a departure and an arrival), not as a number in a Name or Description text"
        )
    message = (
        f"the value {value} from the question is missing: it must be the whole content of an element "
        "or attribute that holds it, not part of a Name or Description text"
    )
    if joined := _joined_values(fragment, value, values or []):
        name, owner, text = joined
        message += (
            f". The {owner}'s {name} \u201c{text}\u201d joins it with other values from the question: if {value} is a "
            f"thing of its own (a place, a stop, an operator), give it its own object with {value} as its Name, "
            f"and link that object to the {owner}"
        )
    return message


def _naming_child(name: str) -> bool:
    return name.endswith("Name") or name == "Description"


def _joined_values(fragment: str, value: str, values: list[str]) -> tuple[str, str, str] | None:
    """The first Name or Description text in the fragment that holds the value and another of the values as
    words, with the element that owns it: ("Name", "Line", "Maribor - Ptuj")."""
    from xml.etree import ElementTree

    if not fragment:
        return None
    try:
        root = ElementTree.fromstring(fragment)
    except ElementTree.ParseError:
        return None

    def has(text: str, word: str) -> bool:
        return bool(re.search(rf"(?<![\w.]){re.escape(word)}(?![\w.])", text))

    others = [other for other in values if other != value]
    for owner in root.iter():
        for child in owner:
            name, text = _local(child.tag), (child.text or "").strip()
            if _naming_child(name) and has(text, value) and any(has(text, other) for other in others):
                return name, _local(owner.tag), text
    return None


def shared_name_values(fragment: str, values: list[str], question: str = "") -> list[dict]:
    """Objects that hold two or more different values from the question as the whole content of their naming
    children (Name, ShortName, Description, ...): {"element": "Line", "id": ..., "holders": {"Name": "Maribor",
    "ShortName": "Ptuj"}}. Such an object says the line is called Maribor and is short-named Ptuj, which is
    false (plan 2026-11-12 revision 4, T1). A child the question names ("short name") does not count."""
    from xml.etree import ElementTree

    try:
        root = ElementTree.fromstring(fragment)
    except ElementTree.ParseError:
        return []
    asked_words = (question or "").lower()
    found = []
    for node in root.iter():
        if not node.get("id"):
            continue
        holders: dict[str, str] = {}
        for child in node:
            name = _local(child.tag)
            words = " ".join(re.findall(r"[A-Z][a-z]*|[a-z]+", name)).lower()
            if not _naming_child(name) or words in asked_words:
                continue
            for value in values:
                if value not in holders.values() and holds_value(child.text or "", value):
                    holders[name] = value
                    break
        if len(holders) >= 2:
            found.append({"element": _local(node.tag), "id": node.get("id"), "holders": holders})
    return found


def shared_name_problems(fragment: str, values: list[str], question: str = "") -> list[str]:
    """The feedback for each object that holds two of the question's values as its names."""
    problems = []
    for item in shared_name_values(fragment, values, question):
        element, holders = item["element"], item["holders"]
        article = "an" if element[:1] in "AEIOU" else "a"
        problems.append(
            f"{' and '.join(holders.values())} from the question are written as the {' and '.join(holders)} of "
            f"the one {element}: {article} {element} has one name. Give each value that names something else "
            f"(a place, a stop, an operator) its own object with that value as its Name, and link that object "
            f"to the {element}"
        )
    return problems


def _unmet_values(fragment: str, values: list[str], question: str) -> list[str]:
    """Values the fragment does not hold: as the whole content of an element or attribute, or, for a number
    followed by a noun ("2 quays"), as that many elements of the noun's kind."""
    missing = missing_values(fragment, values)
    if not missing:
        return []
    counted = {p["value"] for p in count_places(fragment, question)}
    missing = [value for value in missing if value not in counted]
    if any(is_duration_value(value) for value in missing) and (root := _parsed(fragment)) is not None:
        # A duration met as two times that far apart in one object (a departure and an arrival).
        missing = [value for value in missing if not (is_duration_value(value) and duration_by_times(root, value) is not None)]
    return missing


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


def _places(fragment: str, values: list[str], question: str, counts: list[tuple[int, str, str, list[str]]] = ()) -> list[dict]:
    """Where the question's values go, then its counts (a number already placed as a value is not a count),
    then the parts it asks for."""
    places = value_places(fragment, values)
    places += object_count_places(fragment, list(counts), placed={p["value"] for p in places})
    places += count_places(fragment, question, placed={p["value"] for p in places})
    return written_durations(places + part_places(fragment, question), question)


def written_durations(places: list[dict], question: str) -> list[dict]:
    """Places with each duration shown as the question wrote it ("3 minutes", not PT3M)."""
    written = {iso: text for text, _, iso in durations(question)}
    return [{**place, "value": written.get(place["value"], place["value"])} for place in places]


def values_line(values: list[str], question: str) -> str:
    """The values for the model's prompt, a duration with how the schema writes it."""
    written = {iso: (text, seconds) for text, seconds, iso in durations(question)}
    return ", ".join(
        f"{written[v][0]} (an xs:duration {v} in an element the schema has for such a duration, or two times "
        f"{written[v][0]} apart in the same object)" if v in written else v
        for v in values
    )


def values_rule(values: list[str], asked: str = "", own_objects: bool = False) -> str:
    """The value rule for the first prompt, which the check enforces after an attempt anyway: `value` was the
    largest class of failed attempts (14 of 41, plan 2026-11-12 revision 3, S3). With own_objects (two or more
    values no element is known to hold, the skeleton skipped) also where such values go, so the model does not
    write them as the Name and ShortName of the one object (revision 4, T3)."""
    if not values:
        return ""
    rule = (
        "Write each value as the whole content of an element or attribute that holds it, not inside a longer "
        "Name or Description text."
    )
    if own_objects:
        target = f" the {asked}" if asked else " the object the question asks for"
        rule += (
            " Values that name different things (places, stops, operators) are not two names of one object: give "
            f"each its own object with that value as its Name, and link those objects to{target}."
        )
    return rule


def missing_values(fragment: str, values: list[str]) -> list[str]:
    """Requested values that are not the whole content of some element or attribute.

    A value mentioned inside a sentence does not count: "Bus with 50 seats" in a Description leaves
    the seats unmodelled, and the feedback sends the model back to put 50 in an element of its own.
    Only for fragments that validated (no DTD, no entities); an unparsable one falls back to words.
    """
    fields = _field_values(fragment)
    if fields is None:
        return [value for value in values if not re.search(rf"(?<![\w.]){re.escape(value)}(?![\w.])", fragment)]
    return [value for value in values if value not in fields and not any(holds_value(field, value) for field in fields)]


# --- generation ----------------------------------------------------------------------------------

_PROMPT = (
    "You write NeTEx XML for a standards helpdesk. Write ONE NeTEx frame (for example a ResourceFrame, "
    "ServiceFrame, SiteFrame or TimetableFrame, with version and id attributes) that shows what the question "
    "asks, using the values it gives. Put each object in the frame the evidence examples put it in (vehicle "
    "types, for example, in a ResourceFrame). Use only element and attribute names that appear in the schema "
    "declarations and the evidence blocks (schema definitions and example files), in the order the schema "
    "definitions give; put a declared element under one of the parents its declaration names. Give every element that "
    "needs one a version and an id; use the prefix 'hd:' for ids. Reference an object the question does not ask "
    "for with a ...Ref element that has a ref attribute and NO version attribute: it lies outside the fragment. "
    "Define an object in the frame only when the question asks for it or the schema requires it, and give a "
    "reference to an object defined in the frame the same version as that object. Every object defined in the "
    "frame is linked to the object the question asks for: one inside the other, or by a reference, directly or "
    "through another object in the frame.Do not add elements the "
    "question does not need. Use only the values the question gives; where the schema needs another value, use a plain placeholder "
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
    ("value", ("from the question is missing", "has one name")),
    ("count", ("the question counts",)),
    ("part", ("and the frame defines no",)),
    ("asked-object", ("the question asks for",)),
    ("link", ("that nothing links to the",)),
    ("condition", ("the question says the service runs", "is empty: give it the children")),
    ("model-error", ("generation failed",)),
)


def error_class(message: str) -> str:
    """The kind of a failed attempt's first error, from the validator's or the generator's wording:
    malformed, keyref, min-count, not-expected, value, count, part, asked-object, condition, model-error, or other."""
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


def standard_fallback(asked: str, scope: list[str] | None, values: list[str], last: dict) -> dict | None:
    """When no generated fragment validated: an object of the asked element from the standard's examples,
    labelled as not holding the question's values (holdsValues false, missingValues), so the user sees the
    shape instead of "no example". Found by the element alone (the question's values would rule every file
    out); valuePlaces then claim nothing for the values."""
    neutral = "example of " + " ".join(_camel_words(asked))
    found = _plain_standard_example(neutral, scope, [asked])
    if found is None:
        return None
    fragment_values = _field_values(re.sub(r"\s+(?=<)", "", found.get("xml") or "")) or set()
    return {
        **found,
        "holdsValues": False,
        "missingValues": [value for value in values if value not in fragment_values],
        "valuePlaces": [],
        "generationErrors": last.get("errors") or [],
        "generationAttempts": last.get("attempts", MAX_ATTEMPTS),
    }


def unlinked_text(example: dict | None) -> str:
    """The sentence shown under an example whose objects are not all linked to the asked one, the same as the
    frontend's (GeneratedExample.tsx, unlinkedObjectsText): "In this example nothing links the VehicleType and
    2 ScheduledStopPoints to the Line." "" when everything is linked."""
    unlinked = (example or {}).get("unlinkedObjects") or []
    asked = (example or {}).get("askedObject") or ""
    if not unlinked or not asked:
        return ""
    counts: dict[str, int] = {}
    for item in unlinked:
        counts[item["element"]] = counts.get(item["element"], 0) + 1
    parts = [f"{n} {name}s" if n > 1 else f"the {name}" for name, n in counts.items()]
    listed = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"In this example nothing links {listed} to the {asked}."


def example_origin(example: dict | None) -> str:
    """How the answer text is told about the shown example: generated, standard, or standard-without-values."""
    example = example or {}
    if example.get("origin") == "standard" and example.get("holdsValues") is False:
        return "standard-without-values"
    return example.get("origin") or "generated"


def generate_netex_example(
    question: str, chunks: list[dict], scope: list[str] | None = None, english_question: str | None = None
) -> dict | None:
    """A validated NeTEx fragment for the question (see _generate); when generation fails for a question
    whose object is known, the standard's example of that object, labelled as not holding the values."""
    result = _generate(question, chunks, scope, english_question)
    if not result or result.get("valid") or not result.get("askedObject") or not result.get("attempts"):
        return result
    try:
        fallback = standard_fallback(result["askedObject"], scope, requested_values(question), result)
    except Exception as exc:  # the index unavailable: report the failed generation as before
        logger.info("standard fallback not available: %s", exc)
        fallback = None
    if fallback is None:
        return result
    written = {iso: text for text, _, iso in durations(question)}
    fallback["missingValues"] = [written.get(value, value) for value in fallback.get("missingValues") or []]
    for key in ("askedObject", "attemptLog", "generationMs", "validationMs", "schemaDeclarations", "askedObjectMs"):
        if key in result:
            fallback.setdefault(key, result[key])
    fallback["generationMs"] = result.get("generationMs", 0)
    fallback["validationMs"] = result.get("validationMs", 0)
    return fallback


def _generate(
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
                # An object named by its element name ("write the XML for a NeTEx FlexibleLine") before the
                # nearest concepts.
                named = named_elements(question) or named_elements(text)
                elements = list(dict.fromkeys(named + concept_elements(text)))
            except Exception as exc:  # concept matching or the index unavailable: no example, as before
                logger.info("example concept not found: %s", exc)
                return None
            return _plain_standard_example(text, scope, elements)
    shape_question = question if counted_shapes(question) else (english or question)
    # How the service runs ("when there is demand"): generated, as the standard's own objects of the shape
    # need not model it.
    conditions = service_conditions(question) or service_conditions(english)
    found = None if conditions else _from_standard(shape_question, scope)
    if found is not None:
        return found
    if not getattr(settings, "LLM_ENABLED", False):
        return None
    # The object the question asks for and a skeleton of one from the standard's examples, so the model
    # starts from the right object and shape (2026-11-10: two of three valid fare examples held 5 EUR in a
    # price group with no fare product; no evidence chunk showed a vehicle type's capacities).
    asked_started = time.perf_counter()
    asked, skeleton, skeleton_skipped = "", None, ""
    try:
        asked = asked_element(shape_question)
        parts: list[frozenset[str]] = []
        if not asked:
            # No object named ("a coach with 49 seats"): the one that holds the counted parts.
            asked, parts = asked_from_parts(shape_question)
        counted = {written for _, written, _ in counted_shapes(question)}
        named = [name for noun in wanted_parts(shape_question) if (name := resolve_element(noun)) and name != asked]
        named += [element for _, element in conditions if element != asked and element not in named]
        skeleton_values = [v for v in requested_values(question) if v not in counted]
        # Two or more values no element is known to hold ("a bus line from Maribor to Ptuj") cannot all sit in
        # the asked object (one fits its Name), so they belong to other objects, and the asked object's shape
        # alone misleads: with Line_with_facilities.xml the model put the conditions into the line and ran out
        # of attempts (gen33: 5/8 generated with the skeleton, 5/5 without; plan 2026-11-12 revision 3, S1).
        if asked and len(skeleton_values) >= 2 and value_holders(skeleton_values) == []:
            skeleton_skipped = "values"
        skeleton = (
            skeleton_for(asked, skeleton_values, parts, named)
            if asked and not skeleton_skipped else None
        )
        if skeleton is not None:
            from helpdesk.services.retrieval_gateway import shown_example_chunk

            own = shown_example_chunk({"origin": "standard", **skeleton})
            if own is not None:
                chunks = [own] + [c for c in chunks if c.get("chunkId") != own.get("chunkId")]
    except Exception as exc:  # the index or the validator unavailable: generate without them
        logger.info("asked object not resolved: %s", exc)
    asked_ms = round((time.perf_counter() - asked_started) * 1000)
    evidence, used = _evidence_text(chunks)
    if not used:
        return {"valid": False, "attempts": 0, "errors": ["no NeTEx evidence to build the example from"]}
    # A number in digits that counts objects ("2 service journeys") is checked as that many objects, not as a value.
    try:
        counts = object_counts(question)
    except Exception as exc:  # the validator unavailable: the number stays a value, as before
        logger.info("object counts not available: %s", exc)
        counts = []
    values = counted_out(requested_values(question), question, counts)
    skeleton_part = skeleton_block(skeleton) + "\n\n" if skeleton else ""
    try:
        condition_part = conditions_block(conditions, asked)
    except Exception as exc:  # the validator unavailable: the condition is still checked
        logger.info("service condition structure not available: %s", exc)
        condition_part = "HOW THE SERVICE RUNS: " + "; ".join(f"\u201c{p}\u201d in a {e}" for p, e in conditions)
    condition_part = condition_part + "\n\n" if conditions else ""
    rule = values_rule(values, asked, own_objects=skeleton_skipped == "values")
    rule_part = rule + "\n" if rule else ""
    # A part named by an object's element name ("a line with a stop place") must be defined in the frame.
    try:
        named_parts = named_object_parts(shape_question, asked)
    except Exception as exc:  # the validator unavailable: the part is not checked, as before
        logger.info("named parts not available: %s", exc)
        named_parts = []
    to_write = ", ".join(filter(None, [counts_line(counts), parts_line(named_parts)]))
    if to_write:
        rule_part += f"Objects to write, each defined with its own id: {to_write}\n"
    messages = [
        {"role": "system", "content": _PROMPT},
        {"role": "user", "content": f"Question:\n{question}\n\nValues to use: {values_line(values, question)}\n{rule_part}\n{condition_part}{skeleton_part}EVIDENCE BLOCKS:\n{evidence}"},
    ]
    errors: list[str] = []
    # Schema declarations go only into the feedback after a failed attempt: given up front they lowered
    # the benchmark from 18 to 12 of 20 (elements from unrelated contexts tempt the model away from the
    # evidence); after a failure they supply the elements the evidence lacked.
    declarations: list[dict] | None = None
    # Time spent waiting for the model and for the validator, so the validator's share of an answer's
    # latency shows in the trace; and how many schema declarations the model was given.
    timing = {"generationMs": 0, "validationMs": 0, "schemaDeclarations": 0, "askedObjectMs": asked_ms}
    asked_fields = {
        "askedObject": asked, "skeletonSourcePath": (skeleton or {}).get("sourcePath", ""),
        "skeletonCompanion": (skeleton or {}).get("companion", ""),
        **({"skeletonSkipped": skeleton_skipped} if skeleton_skipped else {}),
        "serviceConditions": [{"phrase": phrase, "element": element} for phrase, element in conditions],
    }

    def timed(key: str, call):
        started = time.perf_counter()
        try:
            return call()
        finally:
            timing[key] += round((time.perf_counter() - started) * 1000)

    # One row per attempt (time, output tokens, how the reply parsed, the first error's class): the
    # example benchmark reports from it, and the trace shows why an example took three attempts.
    attempt_log: list[dict] = []

    def logged(
        attempt: int, started: float, parsed: str, attempt_errors: list[str], diagnostics: list | None = None, fragment: str = "",
        repaired: str = "",
    ) -> None:
        first = attempt_errors[0] if attempt_errors else ""
        kinds = [d.get("kind") for d in diagnostics or [] if d.get("kind")]
        attempt_log.append({
            "attempt": attempt,
            "ms": round((time.perf_counter() - started) * 1000),
            "completionTokens": _LAST_COMPLETION_TOKENS.get(),
            "parsed": parsed,
            "errorClass": (kinds[0] if kinds and attempt_errors else error_class(first)),
            "diagnostics": kinds,
            "error": first[:300],
            # What the model wrote, so a failed attempt can be read later (plan 2026-11-12 R0).
            "fragment": fragment[:MAX_LOGGED_FRAGMENT_CHARS],
            # "order": the validator sorted the children into schema order and the attempt went on with its frame
            # (revision 3, S2; since plan 2026-11-13 A1 also when other problems remain). "fragment" is what the
            # model wrote, before any repair.
            **({"repaired": repaired} if repaired else {}),
        })

    def accepted(fragment: str, checked: dict, unlinked: list[dict]) -> dict:
        return {
            "valid": True,
            "origin": "generated",
            "validated": True,
            "attempts": len(attempt_log),
            "xml": indented_fragment(fragment),
            "document": publication_document(fragment),
            "schema": SCHEMA_ENTRY,
            "schemaVersion": checked.get("schemaVersion", ""),
            "schemaCommit": checked.get("commit", ""),
            "elementNotes": element_notes(checked.get("elements") or []),
            "valuePlaces": _places(fragment, values, shape_question, counts) + condition_places(fragment, conditions),
            "evidenceChunkIds": [chunk.get("chunkId") for chunk in used],
            "attemptLog": attempt_log,
            **asked_fields,
            "askedObjectPresent": bool(asked) and not asked_object_problem(fragment, asked, []),
            **({"unlinkedObjects": unlinked} if unlinked else {}),
            **timing,
        }

    # Objects not linked to the asked one are a soft problem (plan 2026-11-12 R1): the attempt is retried to link
    # them, but a valid fragment that holds the values is never discarded for it. The one with the fewest
    # unlinked objects is kept and returned when no later attempt does better. Discarding it gave the standard's
    # example without the question's values (gen33: 5/5 generated on main, 0/5 with the hard check, R0).
    best: tuple[int, str, dict, list[dict]] | None = None

    def failed(result: dict) -> dict:
        if best is not None:
            return accepted(best[1], best[2], best[3])
        return result

    def last(attempt: int) -> bool:
        return attempt >= MAX_ATTEMPTS + (SOFT_EXTRA_ATTEMPTS if best is not None else 0)

    for attempt in range(1, MAX_ATTEMPTS + SOFT_EXTRA_ATTEMPTS + 1):
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
            if last(attempt):
                return failed({"valid": False, "attempts": attempt, "errors": errors, "attemptLog": attempt_log, **asked_fields, **timing})
            continue
        fragment, parsed = parse_reply(content)
        checked: dict = {}
        soft = False
        repaired = ""
        if not fragment:
            errors = ["the reply contained no XML frame"]
        else:
            try:
                checked = timed("validationMs", lambda: validate_fragment(fragment))
            except ValidatorUnavailable as exc:
                logger.warning("NeTEx example not validated: %s", exc)
                return failed({"valid": False, "attempts": attempt, "errors": [str(exc)[:200]], "attemptLog": attempt_log, **asked_fields, **timing})
            errors = list(checked.get("errors") or [])
            repairs = checked.get("repaired") or []
            repaired = ",".join([repairs] if isinstance(repairs, str) else repairs) if checked.get("fragment") else ""
            if repaired:
                # The validator put the children in schema order, valid or not (plan 2026-11-13, A1): go on with its
                # frame, and show the model that frame as its own reply, so any later feedback is about what it sees.
                as_written = fragment
                fragment = checked["fragment"]
                content = json.dumps({"xml": fragment})
            if checked.get("valid") and not errors:
                errors = [
                    missing_value_error(value, question, fragment, values)
                    for value in _unmet_values(fragment, values, shape_question)
                ] + count_problems(fragment, counts) + part_problems(fragment, named_parts, asked)
                # Hard: two of the values as the names of one object (Name "Maribor", ShortName "Ptuj" of a
                # Line) hold the values but state something false (plan 2026-11-12 revision 4, T1).
                if not errors:
                    errors = shared_name_problems(fragment, values, question)
                # Hard: the asked object is absent. Whether the values sit in it or in linked objects is the
                # link check's (soft) question.
                if not errors and asked and (problem := asked_object_problem(fragment, asked, [], shape_question)):
                    errors = [problem]
                if not errors:
                    errors = condition_problems(fragment, conditions)
                if not errors and asked:
                    errors = link_problems(fragment, asked, shape_question, values)
                    soft = bool(errors)
        logged(attempt, attempt_started, parsed, errors, checked.get("diagnostics"), as_written if repaired else fragment, repaired)
        if not errors:
            return accepted(fragment, checked, [])
        if soft:
            unlinked = [{"element": item["element"], "id": item["id"]} for item in unlinked_objects(fragment, asked)]
            if best is None or len(unlinked) < best[0]:
                best = (len(unlinked), fragment, checked, unlinked)
        if last(attempt):
            break
        if declarations is None:
            declarations = schema_declarations(question)
            if fragment:
                known = {d.get("name") for d in declarations}
                declarations += [d for d in value_element_declarations(fragment, values) if d.get("name") not in known]
            timing["schemaDeclarations"] = len(declarations)
        # Declarations after the diagnostics, without the elements the diagnostics already explain.
        explained = {d.get("element") for d in checked.get("diagnostics") or []}
        shown = [d for d in declarations if d.get("name") not in explained]
        schema_part = (
            "\n\n" + declarations_block(shown) + "\nPrefer these elements, under the parents given, for what the question asks."
            if shown and not soft
            else ""
        )
        opening = (
            "The frame is valid NeTEx and holds the question's values, but:" if soft else "The frame is not valid NeTEx:"
        )
        messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": opening + "\n- " + "\n- ".join(feedback_lines(checked, errors))
                + schema_part
                + "\nFix these errors and return the whole frame again as JSON {\"xml\": \"...\"}.",
            },
        ]
    return failed({"valid": False, "attempts": len(attempt_log), "errors": errors, "attemptLog": attempt_log, **asked_fields, **timing})
