from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from helpdesk.services.question_parsing import SemanticQuery
from helpdesk.services.semantic_abstention import (
    LOW_CONFIDENCE_MESSAGE,
    NO_CONCEPT_MESSAGE,
    semantic_abstention_message,
)


def _query(*, concept="nits:unknown-concept", confidence=0.45, terms=("weather",), discovered=()):
    return SemanticQuery(
        intent="definition",
        normativity="unspecified",
        core_concept=concept,
        core_concepts=[] if concept == "nits:unknown-concept" else [concept],
        ambiguous_core_concept=False,
        candidate_standards=[],
        original_terms=list(terms),
        confidence={"intent": 0.6, "concept": confidence},
        discovered_standards=list(discovered),
    )


def _decide(query, *, scope=(), requested=None, allow=True):
    return semantic_abstention_message(
        semantic_query=query, effective_scope=list(scope), requested_scope=requested, allow_abstain=allow
    )


class SemanticAbstentionTests(SimpleTestCase):
    def test_unknown_concept_without_any_scope_hint_is_refused(self):
        self.assertEqual(_decide(_query()), NO_CONCEPT_MESSAGE)

    def test_unknown_concept_is_answered_when_a_standard_is_named_or_requested(self):
        self.assertIsNone(_decide(_query(), scope=["NeTEx"]))

    def test_a_standard_the_ontology_recognised_counts_as_a_hint(self):
        query = _query(concept="nits:Stop", confidence=0.95, discovered=["NeTEx"])
        self.assertIsNone(_decide(query))

    def test_a_capitalised_term_exempts_the_question(self):
        self.assertIsNone(_decide(_query(terms=("OpenStreetMap",))))

    def test_allow_abstain_false_never_refuses(self):
        self.assertIsNone(_decide(_query(), allow=False))

    def test_known_concept_with_low_confidence_and_no_hint_is_refused(self):
        query = _query(concept="nits:Stop", confidence=0.5)
        self.assertEqual(_decide(query), LOW_CONFIDENCE_MESSAGE)

    def test_low_confidence_is_not_refused_when_a_scope_was_requested(self):
        query = _query(concept="nits:Stop", confidence=0.5)
        self.assertIsNone(_decide(query, requested=["SIRI"], scope=["SIRI"]))

    def test_confidence_at_the_threshold_is_not_low(self):
        query = _query(concept="nits:Stop", confidence=0.60)
        self.assertIsNone(_decide(query))

    @override_settings(SEMANTIC_LOW_CONFIDENCE_THRESHOLD=0.9)
    def test_threshold_comes_from_settings(self):
        query = _query(concept="nits:Stop", confidence=0.8)
        self.assertEqual(_decide(query), LOW_CONFIDENCE_MESSAGE)
