"""What an example request asks for, read by the model once and kept only where it is grounded.

Plan 2026-11-14-example-request-reading.md, step R0. One short model call turns the question into a small JSON
reading: the object the example is of (asked), the other objects it must have (each with a count when the
question gives one), the values it must hold, and the phrases that say how a service runs (conditions). Code
then keeps only what it can ground in the question and the schema (plan §2):

1. every phrase is in the question (after whitespace folding); an entry whose phrase is not there is dropped;
2. every value is in its phrase as written, or is the normal form the generator computes for it (a clock time,
   a date, a duration as xs:duration); else the value entry is dropped;
3. every kind and the asked object is an element the schema defines as an object (the validator's /concrete,
   object true; an abstract element stands for its concrete objects); an entry with an unknown kind, or a kind
   that is not an object, keeps its phrase and loses its kind; the object a value is "of" is checked the same way;
4. a count is a positive integer whose phrase holds that number in digits or as a number word; an entry whose
   count fails this keeps its kind and loses its count.

So a wrong reading can make a later check stricter or laxer, never put content into an example the question does
not have. The command read_example_requests measures it against the generator's patterns (R0). Since R1 the
generator adds the reading's objects to the counts and named parts its patterns find (request_reading_objects).
"""

from __future__ import annotations

import json
import logging
import re
import time

from django.conf import settings

logger = logging.getLogger(__name__)

READING_MAX_TOKENS = 600
MAX_CANDIDATE_NAMES = 40

# The form of the reading. The example is made up and names no NeTEx element: the model is asked for the form,
# not taught which words mean which element (plan §4).
_PROMPT = """You read a request for an example of an XML document in the NeTEx standard (public transport \
data) and state what it asks for. You do not write the example. Reply with one JSON object and nothing else:

{"asked": "<NeTEx element name of the object the example is of, or empty>",
 "objects": [{"kind": "<NeTEx element name>", "count": <integer or null>, "phrase": "<words copied from the request>"}],
 "values": [{"value": "<the value>", "phrase": "<words copied from the request>", "of": "<NeTEx element name or empty>"}],
 "conditions": [{"phrase": "<words copied from the request>"}]}

- "asked": the one object the request wants an example of, as the NeTEx element name (UpperCamelCase) of an \
object that has its own id. Empty when the request names none.
- "objects": the other objects the example must contain, each with its own id. "count" is how many the request \
asks for, only when it gives a number (in digits or in words); otherwise null. Do not list the asked object here.
- "values": the concrete data the example must hold: names, codes, texts, numbers that are measures, amounts or \
capacities, clock times, dates, days, durations, currencies. A number that says how many objects to write is a \
count, not a value. "value" is written as in the request, except: a clock time as HH:MM, a date as YYYY-MM-DD, a \
duration as an xs:duration such as PT10M. "of" is the element the value belongs to, if you know it.
- "conditions": phrases that say when or how a service runs and are not a single value.
- Every "phrase" is copied exactly from the request, in its language; never translate or reword it. Leave out \
anything the request does not say. Use empty lists when there is nothing.

Example request: Make a sample of a gadget called "Alpha" with three sprockets and a lever, started at 9:05 for \
2 hours, only when it rains.
Reply:
{"asked": "Gadget",
 "objects": [{"kind": "Sprocket", "count": 3, "phrase": "three sprockets"}, {"kind": "Lever", "count": null, "phrase": "a lever"}],
 "values": [{"value": "Alpha", "phrase": "called \\"Alpha\\"", "of": "Gadget"}, {"value": "09:05", "phrase": "at 9:05", "of": "Gadget"}, {"value": "PT2H", "phrase": "for 2 hours", "of": "Gadget"}],
 "conditions": [{"phrase": "only when it rains"}]}"""

_NUMBER_WORDS = {word: index for index, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split()
)}
_JSON_OBJECT = re.compile(r"\{.*\}", re.S)


def _folded(text: str) -> str:
    return " ".join((text or "").split())


def reading_messages(question: str, candidates: list[str] | None = None) -> list[dict]:
    """The model call's messages: the form, then the request (and, in the candidates variant, element names
    from the schema's declarations that match the request's words)."""
    user = f"Request:\n{question}"
    if candidates:
        user += "\n\nNeTEx element names whose name or documentation matches words of the request (they may not fit): " + ", ".join(candidates)
    return [{"role": "system", "content": _PROMPT}, {"role": "user", "content": user}]


def candidate_names(question: str) -> list[str]:
    """Element names from schema_declarations(question), for the candidates variant of the prompt."""
    from helpdesk.services.netex_example_generator import schema_declarations

    names = [d.get("name") for d in schema_declarations(question) if d.get("name")]
    return list(dict.fromkeys(names))[:MAX_CANDIDATE_NAMES]


def _call_model(messages: list[dict], timeout_seconds: float | None = None) -> str:
    """The generator's client and model, without thinking, temperature 0 (an OpenAI-style gateway takes it; the
    Anthropic SDK path does not send sampling parameters) and a small max_tokens. timeout_seconds: the client's
    timeout per request (LLM_TIMEOUT_SECONDS by default)."""
    from helpdesk.services.llm_generator import _request_chat_completion

    response = _request_chat_completion(
        api_base_url=(settings.LLM_API_BASE_URL or "").strip(),
        api_key=(settings.LLM_API_KEY or "").strip(),
        model=settings.LLM_MODEL,
        timeout_seconds=timeout_seconds or settings.LLM_TIMEOUT_SECONDS,
        temperature=0.0,
        max_tokens=READING_MAX_TOKENS,
        messages=messages,
        thinking="disabled",
    )
    return str(response["choices"][0]["message"]["content"] or "")


def parse_reading(content: str) -> dict | None:
    """The JSON object in the reply (a fence or words around it are ignored), or None."""
    match = _JSON_OBJECT.search(content or "")
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


# Grounding ------------------------------------------------------------------------------------------------------


def phrase_in_question(phrase: str, question: str) -> bool:
    """Rule 1: the phrase is a substring of the question after whitespace folding."""
    phrase = _folded(phrase)
    return bool(phrase) and phrase in _folded(question)


def value_in_phrase(value: str, phrase: str) -> bool:
    """Rule 2: the value is in its phrase as written, or is the normal form the generator computes for a clock
    time, a date or a duration in the phrase ("at 9:05" -> 09:05, "for 2 hours" -> PT2H, or PT7200S)."""
    from helpdesk.services.netex_example_generator import _DATE, _TIME, _time_value, duration_seconds, durations

    value, phrase = _folded(str(value)), _folded(phrase)
    if not value:
        return False
    if value in phrase:
        return True
    if value in {_time_value(match) for match in _TIME.finditer(phrase)}:
        return True
    if value in _DATE.findall(phrase):
        return True
    wanted = duration_seconds(value)
    return wanted is not None and any(seconds == wanted for _, seconds, _ in durations(phrase))


class ObjectLookup:
    """Rule 3: which object elements a name stands for, from the validator's /concrete. [] for a name the
    schema does not define or that is not an object; the abstract one's concrete objects otherwise. Raises
    LookupUnavailable when the validator does not answer, so an outage is not read as "no such element"."""

    def __init__(self):
        self._cache: dict[str, list[str]] = {}

    def __call__(self, name: str) -> list[str]:
        from urllib import error, parse, request

        name = (name or "").strip()
        if not re.fullmatch(r"[A-Za-z][\w.-]*", name):
            return []
        if name in self._cache:
            return self._cache[name]
        url = settings.NETEX_VALIDATOR_URL.rstrip("/") + "/concrete?" + parse.urlencode({"element": name})
        try:
            with request.urlopen(url, timeout=10) as response:
                payload = json.loads(response.read())
        except (error.URLError, OSError, ValueError) as exc:
            raise LookupUnavailable(str(exc)) from exc
        found = [entry["name"] for entry in payload.get("concrete") or [] if entry.get("object")] if payload.get("found") else []
        self._cache[name] = found
        return found


class LookupUnavailable(Exception):
    pass


def count_in_phrase(count, phrase: str) -> bool:
    """Rule 4: a positive integer, written in the phrase in digits or as an (English) number word."""
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        return False
    words = re.findall(r"\d+|[^\W\d_]+", (phrase or "").lower())
    return str(count) in words or any(_NUMBER_WORDS.get(word) == count for word in words)


def ground(reading: dict, question: str, lookup=None) -> tuple[dict, list[dict]]:
    """The reading with only grounded entries, and what was dropped or stripped: [{"field", "entry", "rule",
    "action"}]. lookup(name) -> object elements (ObjectLookup by default)."""
    lookup = lookup or ObjectLookup()
    dropped: list[dict] = []

    def kinds_of(name: str) -> list[str]:
        return lookup(name) if name else []

    asked = str(reading.get("asked") or "").strip()
    asked_kinds = kinds_of(asked)
    if asked and not asked_kinds:
        dropped.append({"field": "asked", "entry": asked, "rule": 3, "action": "stripped"})
        asked = ""

    objects: list[dict] = []
    for entry in reading.get("objects") or []:
        if not isinstance(entry, dict):
            continue
        phrase = str(entry.get("phrase") or "")
        if not phrase_in_question(phrase, question):
            dropped.append({"field": "objects", "entry": entry, "rule": 1, "action": "dropped"})
            continue
        kind = str(entry.get("kind") or "").strip()
        kinds = kinds_of(kind)
        if kind and not kinds:
            dropped.append({"field": "objects", "entry": entry, "rule": 3, "action": "kind stripped"})
            kind = ""
        count = entry.get("count")
        if count is not None and not count_in_phrase(count, phrase):
            dropped.append({"field": "objects", "entry": entry, "rule": 4, "action": "count stripped"})
            count = None
        objects.append({"kind": kind, "kinds": kinds if kind else [], "count": count, "phrase": _folded(phrase)})

    values: list[dict] = []
    for entry in reading.get("values") or []:
        if not isinstance(entry, dict):
            continue
        phrase, value = str(entry.get("phrase") or ""), str(entry.get("value") if entry.get("value") is not None else "")
        if not phrase_in_question(phrase, question):
            dropped.append({"field": "values", "entry": entry, "rule": 1, "action": "dropped"})
            continue
        if not value_in_phrase(value, phrase):
            dropped.append({"field": "values", "entry": entry, "rule": 2, "action": "dropped"})
            continue
        of = str(entry.get("of") or "").strip()
        if of and not kinds_of(of):
            dropped.append({"field": "values", "entry": entry, "rule": 3, "action": "of stripped"})
            of = ""
        values.append({"value": _folded(value), "phrase": _folded(phrase), "of": of})

    conditions: list[dict] = []
    for entry in reading.get("conditions") or []:
        phrase = str((entry.get("phrase") if isinstance(entry, dict) else entry) or "")
        if not phrase_in_question(phrase, question):
            dropped.append({"field": "conditions", "entry": entry, "rule": 1, "action": "dropped"})
            continue
        conditions.append({"phrase": _folded(phrase)})

    grounded = {"asked": asked, "askedKinds": asked_kinds if asked else [], "objects": objects, "values": values, "conditions": conditions}
    return grounded, dropped


def read_request(question: str, candidates: list[str] | None = None, lookup=None, timeout_seconds: float | None = None) -> dict:
    """What the question asks an example of, read by the model and grounded (see the module docstring):
    {"ok", "asked", "askedKinds", "objects", "values", "conditions", "dropped", "ms", "raw", "error"}.
    ok is False when the call failed or its reply had no JSON object; the patterns are the fallback then."""
    empty = {"asked": "", "askedKinds": [], "objects": [], "values": [], "conditions": []}
    started = time.perf_counter()
    try:
        raw = _call_model(reading_messages(question, candidates), timeout_seconds)
    except Exception as exc:  # any failed call: the caller falls back to the patterns
        return {"ok": False, **empty, "dropped": [], "ms": round((time.perf_counter() - started) * 1000), "raw": "", "error": str(exc)[:300]}
    ms = round((time.perf_counter() - started) * 1000)
    parsed = parse_reading(raw)
    if parsed is None:
        return {"ok": False, **empty, "dropped": [], "ms": ms, "raw": raw[:2000], "error": "no JSON object in the reply"}
    try:
        grounded, dropped = ground(parsed, question, lookup)
    except LookupUnavailable as exc:
        return {"ok": False, **empty, "dropped": [], "ms": ms, "raw": raw[:2000], "error": f"schema lookup unavailable: {exc}"}
    return {"ok": True, **grounded, "dropped": dropped, "ms": ms, "raw": raw[:2000], "error": ""}
