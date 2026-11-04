"""Ask the controller model whether a question is about the standards this helpdesk covers.

Used for questions that name no standard and no artifact, where keyword rules are unreliable. Any
failure returns None so the caller falls back to those keyword rules and the question is not blocked.
"""

from __future__ import annotations

from functools import lru_cache
import json
import logging
import re
from urllib import request

from django.conf import settings

from helpdesk.services.controller_llm import _build_ssl_context, _uses_anthropic, anthropic_controller_call
from helpdesk.services.llm_options import controller_max_tokens, controller_request_options
from helpdesk.services.llm_model_recovery import resolve_effective_model

logger = logging.getLogger(__name__)

# A CamelCase term (ServiceJourneyPattern, PtSituationElement) names a concrete artifact.
_CAMEL_CASE_TERM = re.compile(r"\b[A-Z][a-z]+[A-Z][A-Za-z]+\b")
_IRRELEVANT = re.compile(r"\birrelevant\b", re.IGNORECASE)
_RELEVANT = re.compile(r"\brelevant\b", re.IGNORECASE)

_PROMPT = """You screen questions for a helpdesk about European public-transport data standards:
- NeTEx: static data (timetables, networks, lines, stops, fares, accessibility, vehicles and operators).
- SIRI: real-time data exchange (vehicle monitoring, estimated and production timetables, stop monitoring, connection monitoring, facility monitoring such as lifts and escalators, situation exchange such as disruptions and roadworks, general messages).
- OpRa (Operational Raw Data): a format for exchanging historical operational data (offer, demand, capacity, efficiency, passenger counts, delays and cancellations).
- Transmodel: the reference model behind them.
- mobilityDCAT-AP (also DCAT-AP): the metadata profile for describing datasets on National Access Points (NAPs).

Decide whether the question can be answered from the documentation of those standards.
- "relevant": it is about public-transport data, concepts, messages or modelling that these standards cover, even if phrased briefly or in another language.
- "irrelevant": it is about something else (general knowledge, other software, other standards such as GTFS, DATEX II or OpenStreetMap) or it is too vague to tell what is being asked.

Question: {question}

Answer with exactly one word: RELEVANT or IRRELEVANT."""


def has_artifact_term(question: str) -> bool:
    return bool(_CAMEL_CASE_TERM.search(question or ""))


def _enabled() -> bool:
    return bool(getattr(settings, "RELEVANCE_CHECK_ENABLED", False))


def relevance_check_enabled() -> bool:
    return _enabled()


def _verdict(content: str) -> bool:
    """RELEVANT or IRRELEVANT, read from the reply.

    Plain text on purpose: with response_format=json_object the gateway's model garbles the key
    (`{": true}`), while the verdict itself stays right.
    """

    text = content or ""
    if _IRRELEVANT.search(text):
        return False
    if _RELEVANT.search(text):
        return True
    raise ValueError("reply is neither RELEVANT nor IRRELEVANT")


@lru_cache(maxsize=512)
def _ask(question: str) -> bool:
    if _uses_anthropic():
        payload = anthropic_controller_call(
            messages=[{"role": "user", "content": _PROMPT.format(question=question)}],
            max_tokens=controller_max_tokens(8),
            timeout_seconds=int(getattr(settings, "RELEVANCE_CHECK_TIMEOUT_SECONDS", 10)),
            json_answer=False,
        )
        return _verdict(payload["choices"][0]["message"]["content"])

    base_url = getattr(settings, "CONTROLLER_LLM_API_BASE_URL", "").strip()
    model = getattr(settings, "CONTROLLER_LLM_API_MODEL", "").strip()
    if not base_url or not model:
        raise ValueError("controller LLM is not configured")
    api_key = getattr(settings, "CONTROLLER_LLM_API_KEY", "").strip()

    effective_model = resolve_effective_model(
        api_base_url=base_url,
        api_key=api_key,
        configured_model=model,
        verify_ssl=getattr(settings, "CONTROLLER_LLM_VERIFY_SSL", True),
        ca_bundle=getattr(settings, "CONTROLLER_LLM_CA_BUNDLE", "").strip(),
        source="relevance_check",
    )
    body = {
        "model": effective_model,
        "messages": [{"role": "user", "content": _PROMPT.format(question=question)}],
        "temperature": 0.0,
        "max_tokens": controller_max_tokens(8),
        **controller_request_options(json_mode=False),
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    http_request = request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    timeout = int(getattr(settings, "RELEVANCE_CHECK_TIMEOUT_SECONDS", 10))
    with request.urlopen(http_request, timeout=timeout, context=_build_ssl_context()) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _verdict(payload["choices"][0]["message"]["content"])


def is_relevant(question: str) -> bool | None:
    """True or False when the model decides, None when it could not (never raises)."""

    try:
        return _ask(question.strip())
    except Exception:
        logger.warning("Relevance check failed; falling back to keyword rules", exc_info=True)
        return None
