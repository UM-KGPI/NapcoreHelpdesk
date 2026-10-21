"""Model terms for a question's everyday wording.

Concept matching only sees words that appear in ontology labels. A question that
describes a concept in other words ("the service operates when there is a demand"
for FLEXIBLE SERVICE PROPERTIES) matches nothing, and no label or definition in
NeTEx or Transmodel links the two. The controller LLM is asked for the model
terms the question refers to; only terms that match real class labels are kept
(see semantic_graph.concepts_named_by_terms), so an invented term adds nothing.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from urllib import request

from django.conf import settings

from helpdesk.services.controller_llm import _build_ssl_context
from helpdesk.services.llm_model_recovery import resolve_effective_model
from helpdesk.services import semantic_graph
from helpdesk.services.semantic_graph import (
    _normalize_for_matching,
    _word_variant_kind,
    concepts_named_by_terms,
)

logger = logging.getLogger(__name__)

MAX_TERMS = 6

_PROMPT = (
    "You map everyday wording in a public transport data question to the names of concepts in the "
    "Transmodel and NeTEx data models. List the model concept names, in the models' own wording "
    "(e.g. 'SCHEDULED STOP POINT', 'FLEXIBLE SERVICE PROPERTIES'), that the question refers to, "
    f"including concepts it describes in other words. At most {MAX_TERMS}. "
    'Return ONLY JSON: {"terms": ["..."]}.\n\nQuestion: '
)

# The model sometimes returns malformed JSON around otherwise good terms, so the
# terms are read as quoted strings rather than parsed as a JSON document.
_QUOTED_TERM = re.compile(r'"([A-Za-z][A-Za-z0-9 _-]{2,})"')


def _enabled() -> bool:
    return bool(
        getattr(settings, "VOCABULARY_BRIDGE_ENABLED", False)
        and getattr(settings, "CONTROLLER_LLM_ENABLED", False)
        and getattr(settings, "CONTROLLER_LLM_API_BASE_URL", "").strip()
        and getattr(settings, "CONTROLLER_LLM_API_MODEL", "").strip()
    )


def parse_terms(content: str) -> list[str]:
    terms = [term for term in _QUOTED_TERM.findall(content or "") if term.lower() != "terms"]
    return terms[:MAX_TERMS]


def _ask_for_terms(question: str) -> list[str]:
    base_url = settings.CONTROLLER_LLM_API_BASE_URL.strip()
    api_key = getattr(settings, "CONTROLLER_LLM_API_KEY", "").strip()
    model = resolve_effective_model(
        api_base_url=base_url,
        api_key=api_key,
        configured_model=settings.CONTROLLER_LLM_API_MODEL.strip(),
        verify_ssl=getattr(settings, "CONTROLLER_LLM_VERIFY_SSL", True),
        ca_bundle=getattr(settings, "CONTROLLER_LLM_CA_BUNDLE", "").strip(),
        source="vocabulary_bridge",
    )
    body = {
        "model": model,
        "messages": [{"role": "user", "content": _PROMPT + question}],
        "temperature": 0.0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
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
    timeout = int(getattr(settings, "VOCABULARY_BRIDGE_TIMEOUT_SECONDS", 3))
    with request.urlopen(http_request, timeout=timeout, context=_build_ssl_context()) as response:
        payload = json.loads(response.read().decode("utf-8"))
    choices = payload.get("choices") or []
    content = str((choices[0].get("message") or {}).get("content") or "") if choices else ""
    return parse_terms(content)


@lru_cache(maxsize=512)
def bridged_question_concepts(question: str) -> frozenset[str]:
    """Class concepts the question describes in its own words. Empty when the
    bridge is off or the LLM call fails; retrieval then works as before."""
    if not _enabled() or not (question or "").strip():
        return frozenset()
    try:
        terms = _ask_for_terms(question.strip())
    except Exception as exc:  # network, timeout, malformed payload
        logger.warning("Vocabulary bridge unavailable: %s", exc)
        return frozenset()
    return frozenset(
        concept_id for concept_id in concepts_named_by_terms(terms) if _described_in_other_words(concept_id, question)
    )


def _described_in_other_words(concept_id: str, question: str) -> bool:
    """False when the question already spells out most of one of the concept's labels.

    The bridge is for concepts the question describes without naming them. A
    concept whose label the question mostly spells out ("lines", "stop points")
    is either matched already or only loosely related, and adding it pulls in
    generic chunks: in the retrieval benchmark such additions moved OpRa and SIRI
    questions towards NeTEx evidence."""
    question_words = set(_normalize_for_matching(question).split())
    labels = (semantic_graph.GRAPH_CONCEPT_ALIASES or {}).get(concept_id) or set()
    label_words = [_normalize_for_matching(label).split() for label in labels]
    label_words = [words for words in label_words if words]
    # A glued alternative label ("scheduledstoppoint") is one word that never
    # occurs in a question; judge such a concept by its spaced labels.
    spaced = [words for words in label_words if len(words) > 1]
    for words in spaced or label_words:
        present = sum(1 for word in words if any(_word_variant_kind(word, q_word) for q_word in question_words))
        if present * 2 >= len(words):
            return False
    return bool(label_words)
