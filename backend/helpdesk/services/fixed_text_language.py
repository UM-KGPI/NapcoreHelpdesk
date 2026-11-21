"""Fixed answer texts (refusals) in the language of the question.

The answer model writes in the question's language, but a refusal decided before or instead of it is a fixed
English text: "Kaj so to metapodatki?" got "This helpdesk answers questions about ...". For a question the
search translation found to be non-English, the model renders the fixed text into the question's language
once per (text, language); the rendering is kept in the Django cache (CACHE_URL, Redis on prod) under a key
made from the language, the model, the instruction and the text, so a changed text gets a new rendering. An English question, a question
whose language is unknown and every failure keep the English text. A rendering is checked before it is shown
(_rendering_problem: names, length, scripts, the app's own language detection); one that fails is asked for
once more, and when that fails too the English text is shown and the failure is remembered for ten minutes. The request waits for a rendering at most
FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS; a slower one is still cached when it arrives, for the next refusal.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import logging
import re
import threading
import unicodedata
from concurrent.futures import Future, ThreadPoolExecutor

from django.conf import settings
from django.core.cache import cache
from langdetect import LangDetectException, detect_langs

from helpdesk.services import request_timing
from helpdesk.services.question_preprocessor import LANGDETECT_LANGUAGE_NAMES, _strip_technical_terms

logger = logging.getLogger(__name__)

# A rendering stays valid while its text, the model and the instruction do not change (all are in the key);
# the keys of old ones expire on their own.
CACHE_SECONDS = 60 * 60 * 24 * 90
FAILED_CACHE_SECONDS = 10 * 60
RENDER_MODEL_TIMEOUT_SECONDS = 15
RENDER_ATTEMPTS = 2
MIN_LENGTH_RATIO = 0.4
MAX_LENGTH_RATIO = 2.5
# Names a rendering must keep as written when the English text has them, or the English text is kept. The
# instruction asks the same of MMTIS, ITS, TEL TSI and INSPIRE, but a rendering that writes them in their
# usual form in the language ("directive STI", "TSI TEL") is not refused for it.
KEPT_NAMES = ("NeTEx", "SIRI", "OpRa", "Transmodel", "DATEX II", "TN-ITS", "mobilityDCAT-AP")

_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fixed-text-language")
# Renderings under way, by cache key: a second refusal in the same language waits for the same call instead of
# starting another (and an unreachable model does not pile up calls).
_IN_FLIGHT: dict[str, Future] = {}
_IN_FLIGHT_LOCK = threading.Lock()


def _instruction(language: str) -> str:
    return (
        f"Translate the user's text into {language}. It is a fixed message of a helpdesk on transport data "
        "standards, shown to a user whose question it could not answer. Write it as a native speaker of "
        f"{language} would write such a message from scratch: natural, idiomatic sentences, not a word-for-word "
        "rendering; restructure a sentence where the English construction would sound translated. Address the "
        "user formally and politely, with the form used for a stranger, where the language has one. Keep the "
        "meaning: add nothing and leave nothing out, and make every sentence grammatical, with each negation "
        f"expressed once. Write only in the usual script of {language}. Keep every name and abbreviation of a "
        "standard, profile, act or organisation exactly as written (NeTEx, SIRI, OpRa, Transmodel, DATEX II, "
        "TN-ITS, mobilityDCAT-AP, MMTIS, ITS, TEL TSI, INSPIRE, NAPCORE ...); the words around them, such as "
        "Directive, National Access Point or National Body, take their usual form in the language. Work in two "
        "steps inside the JSON: first a draft, then read the draft as a native-speaking editor would and correct "
        "every grammatical error, repeated negation and word-for-word phrasing. Reply with JSON only: "
        '{"draft": "<first draft>", "text": "<the corrected final text>"}.'
    )


def _model() -> str:
    # The model of the app's ordinary calls (LLM_MODEL); _rendering_problem catches what it gets wrong.
    return getattr(settings, "FIXED_TEXT_TRANSLATION_MODEL", "") or settings.LLM_MODEL


def _cache_key(text: str, language: str) -> str:
    """From the language, the model, the instruction and the text: a change to any of them is rendered anew."""
    digest = hashlib.sha256(f"{language}\n{_model()}\n{_instruction(language)}\n{text}".encode("utf-8")).hexdigest()
    return f"fixed-text-language:{digest}"


def _cache_get(key: str) -> str | None:
    try:
        return cache.get(key)
    except Exception:
        logger.warning("Fixed-text cache read failed", exc_info=True)
        return None


def _failed_key(key: str) -> str:
    return f"{key}:failed"


def _cache_set(key: str, value: str, seconds: int) -> None:
    try:
        cache.set(key, value, seconds)
    except Exception:
        logger.warning("Fixed-text cache write failed", exc_info=True)


def _script(character: str) -> str:
    """The script of a letter from its Unicode name: LATIN, CYRILLIC, GREEK, CJK ..."""
    return unicodedata.name(character, "").split(" ")[0]


def _rendering_problem(text: str, language: str, rendered: str, finish_reason: str | None) -> str | None:
    """Why a rendering cannot be shown, or None. General checks, the same for every language."""
    if not rendered:
        return "empty"
    if finish_reason in ("max_tokens", "length"):
        return "cut off at the token limit"
    # Names: a standard's name must survive ("NETEKS" for NeTEx).
    missing = [n for n in KEPT_NAMES if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", text) and n not in rendered]
    if missing:
        return f"dropped {', '.join(missing)}"
    # Length: a cut-off text, a summary, or a text with added explanations is far from the English length.
    ratio = len(rendered) / max(1, len(text))
    if not MIN_LENGTH_RATIO <= ratio <= MAX_LENGTH_RATIO:
        return f"length {ratio:.2f} of the English text"
    # Scripts: no word may mix scripts (Cyrillic letters inside a Latin word), and a word in another script
    # than the text's own must come from the English text (a standard's name in a Greek text).
    words = re.findall(r"[^\W\d_]+", rendered)
    letters = [_script(c) for word in words for c in word]
    main_script = max(set(letters), key=letters.count) if letters else ""
    for word in words:
        scripts = {_script(c) for c in word}
        if len(scripts) > 1:
            return f"mixed scripts in {word!r}"
        if scripts != {main_script} and word not in text:
            return f"{word!r} is not in the text's script"
    # Language: the app's own detector must read the rendering as the target language, when it knows the
    # language at all (a broken or untranslated sentence reads as another language or as nothing certain).
    if language in LANGDETECT_LANGUAGE_NAMES.values():
        detected = _top_language(rendered)
        if detected != language:
            return f"detected as {detected or 'no language'}"
    return None


def _top_language(rendered: str) -> str | None:
    """The detector's first candidate, at any probability: the app's detect_question_language wants 0.90 for a
    question and so said "no language" for correct short Croatian and Dutch renderings (Croatian at 0.87 against
    Slovenian). Here the question is only whether the text reads as the target language and no other."""
    try:
        candidates = detect_langs(_strip_technical_terms(rendered))
    except LangDetectException:
        return None
    return LANGDETECT_LANGUAGE_NAMES.get(candidates[0].lang) if candidates else None


def _render_once(text: str, language: str) -> tuple[str, str | None]:
    from helpdesk.services.llm_generator import _request_chat_completion
    from helpdesk.services.llm_options import answer_max_tokens

    response = _request_chat_completion(
        api_base_url=(settings.LLM_API_BASE_URL or "").strip(),
        api_key=(settings.LLM_API_KEY or "").strip(),
        model=_model(),
        timeout_seconds=min(settings.LLM_TIMEOUT_SECONDS, RENDER_MODEL_TIMEOUT_SECONDS),
        temperature=0.0,
        max_tokens=answer_max_tokens(2000),
        messages=[{"role": "system", "content": _instruction(language)}, {"role": "user", "content": text}],
    )
    choice = response["choices"][0]
    content = choice["message"]["content"]
    # strict=False: the model sometimes puts a raw line break inside the string, which strict JSON refuses.
    payload = json.loads(re.search(r"\{.*\}", content, re.DOTALL).group(0), strict=False)
    return " ".join(str(payload.get("text") or "").split()), choice.get("finish_reason")


def _render(text: str, language: str) -> str | None:
    """The text in the language, or None when both attempts fail a call or a check."""
    for attempt in range(1, RENDER_ATTEMPTS + 1):
        try:
            rendered, finish_reason = _render_once(text, language)
        except Exception:
            logger.warning("Rendering a fixed text in %s failed (attempt %d)", language, attempt, exc_info=True)
            continue
        problem = _rendering_problem(text, language, rendered, finish_reason)
        if problem is None:
            return rendered
        logger.warning("Rendering a fixed text in %s refused (attempt %d): %s: %r", language, attempt, problem, rendered[:200])
    return None


def _render_and_cache(text: str, language: str, key: str) -> str | None:
    rendered = _render(text, language)
    if rendered:
        _cache_set(key, rendered, CACHE_SECONDS)
    else:
        # The English text for a while, then another try: not a call on every refusal while the model fails.
        _cache_set(_failed_key(key), "1", FAILED_CACHE_SECONDS)
    return rendered


def in_question_language(text: str, *, question: str, english_question: str | None) -> str:
    """The fixed text in the question's language; the text itself for an English question or on any failure.

    english_question is the search translation of the question (views._parse_question): None for an English
    question, so an English question costs nothing here. The language name is the one the search translation
    found in this request (llm_generator.question_language, also what the answer prompt is told), asked anew
    only when this request has none.
    """
    if not text or not english_question or not getattr(settings, "LLM_ENABLED", False):
        return text
    from helpdesk.services.llm_generator import _language_key, question_language

    language = request_timing.noted(("question_language", _language_key(question)))
    if language is None:
        try:
            language = question_language(question)
        except Exception:
            logger.warning("Question language unknown for a fixed text", exc_info=True)
            return text
    if not language or language == "English":
        return text
    # The time this costs the request, in its trace (timingsMs.fixedTextMs): a cache read, or the wait.
    with request_timing.timed("fixedTextMs"):
        return _rendered_or_text(text, language)


def _rendered_or_text(text: str, language: str) -> str:
    key = _cache_key(text, language)
    cached = _cache_get(key)
    if cached:
        return cached
    if _cache_get(_failed_key(key)):
        return text
    wait = float(getattr(settings, "FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS", 4.0))
    if wait <= 0:
        return text
    with _IN_FLIGHT_LOCK:
        future = _IN_FLIGHT.get(key)
        if future is None:
            future = _EXECUTOR.submit(contextvars.copy_context().run, _render_and_cache, text, language, key)
            _IN_FLIGHT[key] = future
            future.add_done_callback(lambda _done, key=key: _IN_FLIGHT.pop(key, None))
    try:
        return future.result(timeout=wait) or text
    except Exception:
        logger.warning("Rendering a fixed text in %s took over %.1f s; English text kept", language, wait)
        return text
