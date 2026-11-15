"""Decide whether a question is refused because no standards concept can be identified.

Two rules, both only for questions that name no standard and have no capitalised term (a CamelCase name
suggests a concrete artifact). A question with a requested scope is judged as described in
semantic_abstention_message. The rules were inline in the answer views; they live here so both answer paths
share them and a probe can run them without the LLM.
"""

from __future__ import annotations

from typing import Callable

from django.conf import settings

from helpdesk.services.question_parsing import (
    UNKNOWN_CONCEPT_SENTINEL,
    has_scope_hint,
    parse_question_to_semantic_query,
    select_effective_scope,
)
from helpdesk.services.relevance_check import has_artifact_term, is_relevant, relevance_check_enabled

NO_CONCEPT_MESSAGE = (
    "I could not map your question to a known standards concept yet. "
    "Please clarify by naming a concrete concept, artifact, or standard scope."
)
NOT_RELEVANT_MESSAGE = (
    "This helpdesk answers questions about the public-transport data standards NeTEx, SIRI, OpRa and "
    "Transmodel, the road traffic standards DATEX II and TN-ITS, the mobilityDCAT-AP metadata profile for National Access Points, the EU legislation "
    "that governs their data (MMTIS, ITS Directive, TEL TSI, and the INSPIRE rules for transport networks) and NAPCORE's material on National Access "
    "Points and National Bodies, and your "
    "question does not seem to be about them. Please rephrase it or name the standard, act or concept you mean."
)
LOW_CONFIDENCE_MESSAGE = (
    "I cannot safely determine the intended standards concept from this question yet. "
    "Please clarify the target concept or provide a standards scope."
)


def _concept_confidence(semantic_query):
    confidence = getattr(semantic_query, "confidence", None)
    if confidence is None and hasattr(semantic_query, "as_dict"):
        confidence = (semantic_query.as_dict() or {}).get("confidence")
    return (confidence or {}).get("concept")


def _has_capitalised_term(semantic_query) -> bool:
    return any(any(c.isupper() for c in term[1:]) for term in semantic_query.original_terms)


def _keyword_rule_message(*, semantic_query, effective_scope, requested_scope) -> str | None:
    """The keyword rules: no standards concept matched, or one matched with low confidence, and no hint of
    a standard. The capitalised-term check goes last in each rule, as it did when the rules were inline."""
    if (
        semantic_query.core_concept == UNKNOWN_CONCEPT_SENTINEL
        and not has_scope_hint(semantic_query, effective_scope)
        and not _has_capitalised_term(semantic_query)
    ):
        return NO_CONCEPT_MESSAGE
    threshold = float(getattr(settings, "SEMANTIC_LOW_CONFIDENCE_THRESHOLD", 0.60))
    concept_confidence = _concept_confidence(semantic_query)
    if (
        concept_confidence is not None
        and float(concept_confidence) < threshold
        and not requested_scope
        and not has_scope_hint(semantic_query, effective_scope)
        and not _has_capitalised_term(semantic_query)
    ):
        return LOW_CONFIDENCE_MESSAGE
    return None


def semantic_abstention_message(
    *,
    semantic_query,
    effective_scope,
    requested_scope,
    allow_abstain: bool,
    question: str | None = None,
    parse_without_scope: Callable[[], tuple[object, str]] | None = None,
) -> str | None:
    """The refusal message when the question should be refused, else None.

    The keyword rules decide first. They match ontology label words, so everyday wording ("a lift in a
    station", "seat capacity", "timetable") matches no concept and is refused although the sources cover
    it. With the relevance check enabled, a question the keyword rules refuse is put to the controller
    model as a second opinion: RELEVANT answers it, IRRELEVANT refuses it with the message that says what
    the helpdesk covers, and a failed call leaves the keyword refusal. A question the keyword rules let
    through is not asked about: until 2026-11-14 every question naming no standard and no artifact was put
    to the model, which then also refused questions the keyword rules answered ("Any timetable from
    Slovenia?", which has an example in NeTEx).

    A requested scope counts as a hint of a standard, so the keyword rules never refuse a scoped question,
    and a vague or off-topic question sent with a scope reached retrieval and the answer model. With the
    check enabled, a scoped question is judged as if asked without the scope (``parse_without_scope``, by
    default the question parsed without one): when the keyword rules would refuse it, the model is asked
    the same question as without a scope (told the scope, it accepted vague questions more often or
    rejected answerable ones, 2026-11-15), and only IRRELEVANT refuses it. With the check disabled, or when
    the call fails, a scoped question is answered as before: the keyword rules alone would also refuse
    questions a scope makes answerable ("a lift in a station" with NeTEx).
    """

    if not allow_abstain:
        return None
    if requested_scope:
        return _scoped_message(question=question, parse_without_scope=parse_without_scope)
    message = _keyword_rule_message(
        semantic_query=semantic_query, effective_scope=effective_scope, requested_scope=requested_scope
    )
    if message is None or question is None or not relevance_check_enabled():
        return message
    if effective_scope or has_artifact_term(question):
        return message
    verdict = is_relevant(question)
    if verdict is True:
        return None
    if verdict is False:
        return NOT_RELEVANT_MESSAGE
    return message


def _scoped_message(*, question, parse_without_scope) -> str | None:
    if question is None or not relevance_check_enabled():
        return None
    if parse_without_scope is None:
        unscoped_query, text = parse_question_to_semantic_query(text=question, requested_scope=None), question
    else:
        unscoped_query, text = parse_without_scope()
    unscoped_scope, _ = select_effective_scope(unscoped_query, None)
    message = _keyword_rule_message(semantic_query=unscoped_query, effective_scope=unscoped_scope, requested_scope=None)
    if message is None:
        return None
    if is_relevant(text) is False:
        return NOT_RELEVANT_MESSAGE
    return None
