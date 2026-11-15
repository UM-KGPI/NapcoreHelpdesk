from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services.question_parsing import UNKNOWN_CONCEPT_SENTINEL, SemanticQuery
from helpdesk.services.semantic_abstention import (
    LOW_CONFIDENCE_MESSAGE,
    NO_CONCEPT_MESSAGE,
    NOT_RELEVANT_MESSAGE,
    semantic_abstention_message,
)


def _query(*, concept=UNKNOWN_CONCEPT_SENTINEL, confidence=0.45, terms=("weather",), discovered=()):
    return SemanticQuery(
        intent="definition",
        normativity="unspecified",
        core_concept=concept,
        core_concepts=[] if concept == UNKNOWN_CONCEPT_SENTINEL else [concept],
        ambiguous_core_concept=False,
        candidate_standards=[],
        original_terms=list(terms),
        confidence={"intent": 0.6, "concept": confidence},
        discovered_standards=list(discovered),
    )


def _decide(query, *, scope=(), requested=None, allow=True, question=None):
    return semantic_abstention_message(
        semantic_query=query,
        effective_scope=list(scope),
        requested_scope=requested,
        allow_abstain=allow,
        question=question,
    )


class SemanticAbstentionTests(SimpleTestCase):
    def test_unknown_concept_without_any_scope_hint_is_refused(self):
        self.assertEqual(_decide(_query()), NO_CONCEPT_MESSAGE)

    def test_unknown_concept_is_answered_when_a_standard_is_named_or_requested(self):
        self.assertIsNone(_decide(_query(), scope=["NeTEx"]))

    def test_a_standard_the_ontology_recognised_counts_as_a_hint(self):
        query = _query(concept="transmodel:STOP_PLACE", confidence=0.95, discovered=["NeTEx"])
        self.assertIsNone(_decide(query))

    def test_a_capitalised_term_exempts_the_question(self):
        self.assertIsNone(_decide(_query(terms=("OpenStreetMap",))))

    def test_allow_abstain_false_never_refuses(self):
        self.assertIsNone(_decide(_query(), allow=False))

    def test_known_concept_with_low_confidence_and_no_hint_is_refused(self):
        query = _query(concept="transmodel:STOP_PLACE", confidence=0.5)
        self.assertEqual(_decide(query), LOW_CONFIDENCE_MESSAGE)

    def test_low_confidence_is_not_refused_when_a_scope_was_requested(self):
        query = _query(concept="transmodel:STOP_PLACE", confidence=0.5)
        self.assertIsNone(_decide(query, requested=["SIRI"], scope=["SIRI"]))

    def test_confidence_at_the_threshold_is_not_low(self):
        query = _query(concept="transmodel:STOP_PLACE", confidence=0.60)
        self.assertIsNone(_decide(query))

    @override_settings(SEMANTIC_LOW_CONFIDENCE_THRESHOLD=0.9)
    def test_threshold_comes_from_settings(self):
        query = _query(concept="transmodel:STOP_PLACE", confidence=0.8)
        self.assertEqual(_decide(query), LOW_CONFIDENCE_MESSAGE)


@override_settings(RELEVANCE_CHECK_ENABLED=True)
@patch("helpdesk.services.semantic_abstention.is_relevant")
class RelevanceCheckHybridTests(SimpleTestCase):
    def test_a_question_naming_a_standard_is_answered_without_a_call(self, ask):
        self.assertIsNone(_decide(_query(), scope=["SIRI"], question="What is SIRI?"))
        ask.assert_not_called()

    def test_a_question_with_an_artifact_term_is_answered_without_a_call(self, ask):
        query = _query(terms=("ServiceJourneyPattern",))
        self.assertIsNone(_decide(query, question="What is ServiceJourneyPattern?"))
        ask.assert_not_called()

    def test_a_keyword_refusal_goes_to_the_model_and_its_verdict_decides(self, ask):
        ask.return_value = False
        self.assertEqual(_decide(_query(), question="What is the weather?"), NOT_RELEVANT_MESSAGE)
        ask.return_value = True
        # the keyword rules refuse this one; the model overrides them
        self.assertIsNone(_decide(_query(), question="How do I describe a lift in a station?"))
        low = _query(concept="transmodel:FARE", confidence=0.45, discovered=[])
        self.assertIsNone(_decide(low, question="fares"))

    def test_a_question_the_keyword_rules_answer_is_not_put_to_the_model(self, ask):
        ask.return_value = False
        answered = _query(concept="transmodel:TIMETABLE_FRAME", confidence=0.95, discovered=["NeTEx"])
        self.assertIsNone(_decide(answered, question="Any timetable from Slovenia?"))
        ask.assert_not_called()

    def test_a_model_failure_falls_back_to_the_keyword_rules(self, ask):
        ask.return_value = None
        self.assertEqual(_decide(_query(), question="What is the weather?"), NO_CONCEPT_MESSAGE)
        low = _query(concept="transmodel:FARE", confidence=0.45, discovered=[])
        self.assertEqual(_decide(low, question="fares"), LOW_CONFIDENCE_MESSAGE)

    def test_allow_abstain_false_makes_no_call(self, ask):
        self.assertIsNone(_decide(_query(), allow=False, question="What is the weather?"))
        ask.assert_not_called()

    @override_settings(RELEVANCE_CHECK_ENABLED=False)
    def test_disabled_check_leaves_the_keyword_rules_in_charge(self, ask):
        self.assertEqual(_decide(_query(), question="What is the weather?"), NO_CONCEPT_MESSAGE)
        ask.assert_not_called()


def _decide_scoped(question, *, unscoped, scope=("NeTEx",), allow=True):
    """A scoped request: the parse with the scope answers anyway; the screen judges the unscoped parse."""
    scoped = _query(discovered=())
    parse = MagicMock(return_value=(unscoped, question))
    message = semantic_abstention_message(
        semantic_query=scoped,
        effective_scope=list(scope),
        requested_scope=list(scope),
        allow_abstain=allow,
        question=question,
        parse_without_scope=parse,
    )
    return message, parse


@patch("helpdesk.services.semantic_abstention.is_relevant")
class ScopedQuestionTests(SimpleTestCase):
    @override_settings(RELEVANCE_CHECK_ENABLED=False)
    def test_with_the_check_off_a_scoped_question_is_answered_as_before(self, ask):
        message, parse = _decide_scoped("Is this mandatory?", unscoped=_query())
        self.assertIsNone(message)
        parse.assert_not_called()
        ask.assert_not_called()

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_a_scope_does_not_switch_the_screen_off(self, ask):
        ask.return_value = False
        message, parse = _decide_scoped("Is this mandatory?", unscoped=_query(), scope=("EU legislation",))
        self.assertEqual(message, NOT_RELEVANT_MESSAGE)
        parse.assert_called_once()
        ask.assert_called_once_with("Is this mandatory?")  # not told the scope

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_a_scoped_question_the_model_accepts_is_answered(self, ask):
        ask.return_value = True
        message, _ = _decide_scoped("How do I describe a lift in a station?", unscoped=_query())
        self.assertIsNone(message)

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_a_failed_call_answers_a_scoped_question_as_with_the_check_off(self, ask):
        ask.return_value = None
        message, _ = _decide_scoped("How do I describe a lift in a station?", unscoped=_query())
        self.assertIsNone(message)

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_a_scoped_question_the_keyword_rules_answer_unscoped_is_not_put_to_the_model(self, ask):
        ask.return_value = False
        names_a_standard = _query(concept="transmodel:STOP_PLACE", confidence=0.95, discovered=["NeTEx"])
        message, _ = _decide_scoped("Any timetable from Slovenia?", unscoped=names_a_standard, scope=("SIRI",))
        self.assertIsNone(message)
        ask.assert_not_called()

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_low_confidence_unscoped_goes_to_the_model_with_a_scope(self, ask):
        ask.return_value = False
        low = _query(concept="transmodel:FARE", confidence=0.45, discovered=[])
        message, _ = _decide_scoped("fares", unscoped=low)
        self.assertEqual(message, NOT_RELEVANT_MESSAGE)

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_allow_abstain_false_makes_no_call_with_a_scope(self, ask):
        message, parse = _decide_scoped("Is this mandatory?", unscoped=_query(), allow=False)
        self.assertIsNone(message)
        parse.assert_not_called()
        ask.assert_not_called()

    @override_settings(RELEVANCE_CHECK_ENABLED=True)
    def test_without_a_parse_given_the_question_is_parsed_without_the_scope(self, ask):
        ask.return_value = False
        with patch(
            "helpdesk.services.semantic_abstention.parse_question_to_semantic_query", return_value=_query()
        ) as parse:
            message = _decide(_query(), scope=["NeTEx"], requested=["NeTEx"], question="Is this mandatory?")
        self.assertEqual(message, NOT_RELEVANT_MESSAGE)
        parse.assert_called_once_with(text="Is this mandatory?", requested_scope=None)
