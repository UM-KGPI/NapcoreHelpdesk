"""Fixed answer texts (refusals) in the language of the question.

The answer model writes in the question's language, but a refusal decided before or instead of it is a fixed
English text: "Kaj so to metapodatki?" got "This helpdesk answers questions about ...". For a question the
search translation found to be non-English, the model renders the fixed text into the question's language
once per (text, language); the rendering is kept in the Django cache (CACHE_URL, Redis on prod) under a key
made from the language, the model, the instruction and the text, so a changed text gets a new rendering. An English question, a question
whose language is unknown and every failure keep the English text. The request waits for a rendering at most
FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS; a slower one is still cached when it arrives, for the next refusal.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import logging
import re
import threading
from concurrent.futures import Future, ThreadPoolExecutor

from django.conf import settings
from django.core.cache import cache

from helpdesk.services import request_timing

logger = logging.getLogger(__name__)

# A rendering stays valid while its text, the model and the instruction do not change (all are in the key);
# the keys of old ones expire on their own.
CACHE_SECONDS = 60 * 60 * 24 * 90
RENDER_MODEL_TIMEOUT_SECONDS = 15
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
        "standards, shown to a user whose question it could not answer. Write natural, idiomatic "
        f"{language} as a native speaker would, not a word-for-word rendering. Keep the meaning and the "
        "tone; add nothing and leave nothing out. Keep every name and abbreviation of a standard, profile, act "
        "or organisation exactly as written (NeTEx, SIRI, OpRa, Transmodel, DATEX II, TN-ITS, mobilityDCAT-AP, "
        "MMTIS, ITS, TEL TSI, INSPIRE, NAPCORE ...); the words around them, such as Directive, National Access "
        'Point or National Body, take their usual form in the language. Reply with JSON only: {"text": "<the '
        'translated text>"}.'
    )


def _model() -> str:
    # Sonnet by default with Claude (LANGUAGE_CLASSIFIER_MODEL): Haiku without thinking garbled sentences
    # ("keinem bekannten Konzept ... aufgrund nicht zuordnen", Cyrillic letters inside a Slovenian word).
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


def _cache_set(key: str, value: str) -> None:
    try:
        cache.set(key, value, CACHE_SECONDS)
    except Exception:
        logger.warning("Fixed-text cache write failed", exc_info=True)


def _keeps_names(text: str, rendered: str) -> bool:
    return all(name in rendered for name in KEPT_NAMES if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text))


def _render(text: str, language: str) -> str | None:
    """The text in the language, or None when the call fails, returns nothing or drops a name."""
    from helpdesk.services.llm_generator import _request_chat_completion
    from helpdesk.services.llm_options import answer_max_tokens

    messages = [{"role": "system", "content": _instruction(language)}, {"role": "user", "content": text}]
    try:
        response = _request_chat_completion(
            api_base_url=(settings.LLM_API_BASE_URL or "").strip(),
            api_key=(settings.LLM_API_KEY or "").strip(),
            model=_model(),
            timeout_seconds=min(settings.LLM_TIMEOUT_SECONDS, RENDER_MODEL_TIMEOUT_SECONDS),
            temperature=0.0,
            max_tokens=answer_max_tokens(2000),
            messages=messages,
        )
        content = response["choices"][0]["message"]["content"]
        rendered = str(json.loads(re.search(r"\{.*\}", content, re.DOTALL).group(0)).get("text") or "").strip()
    except Exception:
        logger.warning("Rendering a fixed text in %s failed", language, exc_info=True)
        return None
    if not rendered or not _keeps_names(text, rendered):
        logger.warning("Rendering a fixed text in %s was empty or dropped a name: %r", language, rendered[:200])
        return None
    return rendered


def _render_and_cache(text: str, language: str, key: str) -> str | None:
    rendered = _render(text, language)
    if rendered:
        _cache_set(key, rendered)
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
    wait = float(getattr(settings, "FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS", 3.0))
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
