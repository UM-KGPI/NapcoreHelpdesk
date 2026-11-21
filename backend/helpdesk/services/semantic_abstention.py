"""Decide whether a question is refused because no standards concept can be identified.

Two rules, both only for questions that name no standard, request no scope and have no capitalised
term (a CamelCase name suggests a concrete artifact). They were inline in the answer views; they live
here so both answer paths share them and a probe can run them without the LLM.
"""

from __future__ import annotations

from django.conf import settings

from helpdesk.services.question_parsing import UNKNOWN_CONCEPT_SENTINEL, has_scope_hint
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

# Not a keyword rule: the answer views refuse with it when nothing was retrieved or the policy blocks the answer.
INSUFFICIENT_EVIDENCE_MESSAGE = "I do not have sufficient approved-source evidence to answer this safely."


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


def _goes_to_relevance_check(keyword_message: str | None, effective_scope, question: str | None) -> bool:
    return bool(
        keyword_message is not None
        and question is not None
        and relevance_check_enabled()
        and not effective_scope
        and not has_artifact_term(question)
    )


def reaches_relevance_check(
    *, semantic_query, effective_scope, requested_scope, allow_abstain: bool, question: str | None = None
) -> bool:
    """Whether semantic_abstention_message puts this question to the relevance check. No model call.

    A question it put there and did not refuse got through by the check's RELEVANT alone: it names no
    standard and matched no standards concept, so a search of the core standards alone misses the sources
    that answer many of them (the acts, mobilityDCAT-AP, NAPCORE's material: 13 of 32 such questions measured
    on 2026-11-21 had their answer only there). The answer views search every source for it.
    """

    if not allow_abstain:
        return False
    message = _keyword_rule_message(
        semantic_query=semantic_query, effective_scope=effective_scope, requested_scope=requested_scope
    )
    return _goes_to_relevance_check(message, effective_scope, question)


def semantic_abstention_message(
    *, semantic_query, effective_scope, requested_scope, allow_abstain: bool, question: str | None = None
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
    """

    if not allow_abstain:
        return None
    message = _keyword_rule_message(
        semantic_query=semantic_query, effective_scope=effective_scope, requested_scope=requested_scope
    )
    if not _goes_to_relevance_check(message, effective_scope, question):
        return message
    verdict = is_relevant(question)
    if verdict is True:
        return None
    if verdict is False:
        return NOT_RELEVANT_MESSAGE
    return message
