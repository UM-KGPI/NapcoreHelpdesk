"""Ask the controller model whether a question is about the standards this helpdesk covers.

Used for questions that name no standard and no artifact, where keyword rules are unreliable. Any
failure returns None so the caller falls back to those keyword rules and the question is not blocked.
"""

from __future__ import annotations

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

# What the index holds, per source (written 2026-11-21 from the indexed files: the schema file topics of NeTEx,
# SIRI and OpRa, the specification pages of mobilityDCAT-AP, the DATEX II documentation and profiles, the TN-ITS code
# lists, the acts in the EU legislation source and the terms they define, the INSPIRE Transport Networks
# specification, the NAPCORE deliverables and pages). Keep it in step with the sources and with
# semantic_abstention.NOT_RELEVANT_MESSAGE, which names the same sources to the user.
_COVERAGE = """- NeTEx (XML schemas and example files): public-transport network and timetable data: stop places, quays, entrances, station equipment such as lifts, escalators and ticket machines, accessibility, parking, points of interest; networks, lines, routes, journey patterns, timetables, service and vehicle journeys, calendars and day types, vehicle and crew scheduling, vehicle types, seating and capacity, deck plans; fares, fare zones, fare products, prices, tickets and travel documents, sales; vehicle sharing, flexible and on-demand services; organisations, operators, responsibilities, versions.
- SIRI (XML schemas and example files): real-time data exchange: vehicle monitoring and positions, estimated and production timetables, stop monitoring and departures, connection monitoring, facility monitoring (lifts, escalators), situation exchange (disruptions, incidents, roadworks), general messages, control actions, subscriptions and discovery.
- OpRa (Operational Raw Data; XML schemas and example files): historical operational data: passenger counts (on-board devices, ticketing, external), vehicle occupancy, capacity, fleet and service dimensions, service intensity, late and cancelled journeys, delay classification, statistics.
- Transmodel: the reference data model and the concepts behind NeTEx, SIRI and OpRa.
- mobilityDCAT-AP (also DCAT-AP; the specification and its examples): the metadata that describes datasets on National Access Points: catalogues, catalogue records, datasets, dataset series, distributions and formats, licences and rights, publishers and other agents, quality annotations and assessments, controlled vocabularies, mandatory, recommended and optional properties, validation.
- DATEX II (its documentation, recommended profiles and schemas): road traffic and travel information: situations (roadworks, accidents, obstructions, weather on the road), traffic data, variable message signs, parking and truck parking, energy infrastructure and charging and refuelling points, traffic management and regulations, location referencing, data exchange; the profiles for the RTTI, SRTI and MMTIS data types.
- TN-ITS (code lists, schemas and examples): updates of road attributes for digital maps: speed limits, road signs, restrictions by vehicle type, road features.
- EU legislation: the MMTIS Delegated Regulation (EU) 2017/1926 and its 2024 amendment, the ITS Directive 2010/40/EU and its 2023 amendment, the TEL TSI (Regulation (EU) 2026/253), the INSPIRE Directive 2007/2/EC and Regulation (EU) No 1089/2010: which travel and traffic data must be made available, by whom (authorities, transport operators, infrastructure managers, other data holders), through National Access Points, in which standards and formats, with which metadata, updates, quality and conditions of reuse, and the terms these acts define (static, dynamic and historic data, metadata, data holder, data user, national access point, machine-readable format, interoperability, spatial data and others).
- INSPIRE (the Transport Networks data specification): road, rail, water, air and cable networks as spatial data, their data quality, metadata and code lists.
- NAPCORE (its deliverables and web pages): National Access Points and National Bodies: NAP architectures and metadata, data availability, data quality frameworks, data validation, compliance assessment and self-declarations, access node identifiers, the mapping of data standards, and the delegated regulations the NAPs implement (MMTIS, RTTI, SRTI, safe and secure truck parking)."""

_PROMPT = (
    """You screen questions for a helpdesk about European transport data. It answers only from these sources:
"""
    + _COVERAGE
    + """

Decide whether the question asks about a subject these sources hold.
The subject is what the question asks about. It counts only when the question itself names it, so that the sources could be searched for it: a kind of data, a data object, a message or exchange, a legal obligation or role, a process such as validation or compliance assessment, a term the sources define. A general word that the question only points at ("the procedure", "this file", "my document") is not a subject: the reader would have to ask "which one?". It becomes one when the question says what it belongs to ("the procedure for compliance assessment") or asks about it across these sources ("which data must be provided").
- "relevant": its subject is one of those above, or another subject of transport data, its exchange, description, quality or legal requirements that such documents describe; also when it has only two or three words, names no standard, or is in another language.
- "irrelevant": its subject is something else (general knowledge, travel information itself such as a departure time or a ticket price, other software, other standards such as GTFS or OpenStreetMap), or it has no subject of its own (it only greets or thanks, asks for help without saying with what, or only points at something it does not name).

Question: {question}

Answer with exactly one word: RELEVANT or IRRELEVANT."""
)


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


def _ask(question: str) -> bool:
    # Not cached: a verdict kept per process repeated a minority IRRELEVANT for every later asker until the
    # backend restarted. Without thinking (Claude) or at temperature 0 (the other gateways) the verdict is as
    # stable as the endpoint allows; Claude takes no temperature.
    if _uses_anthropic():
        payload = anthropic_controller_call(
            messages=[{"role": "user", "content": _PROMPT.format(question=question)}],
            max_tokens=controller_max_tokens(8),
            timeout_seconds=int(getattr(settings, "RELEVANCE_CHECK_TIMEOUT_SECONDS", 10)),
            json_answer=False,
            # Claude takes "disabled" only at effort high or below.
            thinking="disabled" if settings.CONTROLLER_LLM_ANTHROPIC_EFFORT in ("low", "medium", "high") else "adaptive",
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
