from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase
from django.test import override_settings

from helpdesk.services.question_parsing import QuestionParsingService, SemanticQuery, select_effective_scope


class QuestionParsingServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = QuestionParsingService()

    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_builds_semantic_query_with_discovered_scope(
        self,
        extract_mock,
        expand_mock,
        nch_mock,
    ):
        extract_mock.return_value = {"opra:delayed-journey"}
        expand_mock.return_value = {"opra:delayed-journey", "netex:service-journey-pattern"}
        nch_mock.return_value = {"nits:journey-pattern"}

        semantic_query = self.service.parse(
            text="How SHALL delayed journeys be represented in ServiceJourneyPattern examples?",
            requested_scope=[],
        )

        self.assertEqual(semantic_query.intent, "normative_status")
        self.assertEqual(semantic_query.normativity, "mandatory")
        self.assertEqual(semantic_query.core_concept, "nits:journey-pattern")
        self.assertEqual(semantic_query.candidate_standards, ["NeTEx", "OpRa"])
        self.assertIn("ServiceJourneyPattern", semantic_query.original_terms)
        self.assertGreaterEqual(semantic_query.confidence["concept"], 0.9)

    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_keeps_requested_scope_when_provided(self, extract_mock, expand_mock, nch_mock):
        extract_mock.return_value = {"netex:service-journey-pattern"}
        expand_mock.return_value = {"netex:service-journey-pattern", "opra:delayed-journey"}
        nch_mock.return_value = {"nits:journey-pattern"}

        semantic_query = self.service.parse(
            text="Compare ServiceJourneyPattern and delayed journeys.",
            requested_scope=["OpRa"],
        )

        self.assertEqual(semantic_query.intent, "comparison")
        self.assertEqual(semantic_query.candidate_standards, ["OpRa"])
        self.assertEqual(semantic_query.normativity, "unspecified")

    @patch.object(QuestionParsingService, "_discover_standards")
    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_scopes_to_standards_named_in_the_question(
        self, extract_mock, expand_mock, nch_mock, discover_mock
    ):
        """Graph discovery lists every standard for a core concept; the named one must win."""
        extract_mock.return_value = {"siri:estimated-vehicle-journey"}
        expand_mock.return_value = {"siri:estimated-vehicle-journey"}
        nch_mock.return_value = {"nits:journey"}
        discover_mock.return_value = ["NeTEx", "OpRa", "SIRI", "Transmodel"]

        named_one = self.service.parse(text="What is a SIRI EstimatedVehicleJourney used for?", requested_scope=[])
        named_two = self.service.parse(text="How does OpRa relate to NeTEx journeys?", requested_scope=[])
        named_none = self.service.parse(text="What is an EstimatedVehicleJourney used for?", requested_scope=[])

        self.assertEqual(named_one.candidate_standards, ["SIRI"])
        self.assertEqual(named_two.candidate_standards, ["NeTEx", "OpRa"])
        # No standard named: the discovered candidates are unchanged.
        self.assertEqual(named_none.candidate_standards, ["NeTEx", "OpRa", "SIRI", "Transmodel"])

    @patch.object(QuestionParsingService, "_discover_standards")
    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_requested_scope_still_beats_named_standards(
        self, extract_mock, expand_mock, nch_mock, discover_mock
    ):
        extract_mock.return_value = {"siri:estimated-vehicle-journey"}
        expand_mock.return_value = {"siri:estimated-vehicle-journey"}
        nch_mock.return_value = {"nits:journey"}
        discover_mock.return_value = ["OpRa"]

        semantic_query = self.service.parse(
            text="What is a SIRI EstimatedVehicleJourney used for?", requested_scope=["OpRa"]
        )

        self.assertEqual(semantic_query.candidate_standards, ["OpRa"])

    @override_settings(GRAPHDB_ENABLED=True, GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/sparql")
    @patch("helpdesk.services.question_parsing.GraphDBConnector")
    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_prefers_graphdb_anchor_when_available(
        self,
        extract_mock,
        expand_mock,
        nch_mock,
        connector_cls_mock,
    ):
        extract_mock.return_value = {"opra:delayed-journey"}
        expand_mock.return_value = {"opra:delayed-journey"}
        nch_mock.return_value = {"nits:fallback"}

        connector = connector_cls_mock.return_value
        connector.anchor_term_to_core_concepts.return_value = [
            "https://napcore.eu/ontology/nits#JourneyPattern"
        ]
        connector.discover_standards_for_core_concept.return_value = ["NeTEx", "SIRI"]

        semantic_query = self.service.parse(
            text="How should ServiceJourneyPattern be referenced?",
            requested_scope=[],
        )

        self.assertEqual(semantic_query.core_concept, "nits:JourneyPattern")
        self.assertEqual(semantic_query.candidate_standards, ["NeTEx", "SIRI"])
        connector.anchor_term_to_core_concepts.assert_called()
        connector.discover_standards_for_core_concept.assert_called()

    @override_settings(GRAPHDB_ENABLED=True, GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/sparql")
    @patch("helpdesk.services.question_parsing.GraphDBConnector")
    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_falls_back_when_graphdb_returns_no_anchors(
        self,
        extract_mock,
        expand_mock,
        nch_mock,
        connector_cls_mock,
    ):
        extract_mock.return_value = {"netex:service-journey-pattern"}
        expand_mock.return_value = {"netex:service-journey-pattern"}
        nch_mock.return_value = {"nits:journey-pattern"}

        connector = connector_cls_mock.return_value
        connector.anchor_term_to_core_concepts.return_value = []
        connector.discover_standards_for_core_concept.return_value = []

        semantic_query = self.service.parse(
            text="Where is ServiceJourneyPattern defined?",
            requested_scope=[],
        )

        self.assertEqual(semantic_query.core_concept, "nits:journey-pattern")
        self.assertEqual(semantic_query.candidate_standards, ["NeTEx"])

    @patch("helpdesk.services.question_parsing.get_concept_nits_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_ranks_and_caps_core_concept_candidates(self, extract_mock, expand_mock, nch_mock):
        extract_mock.return_value = {"netex:line", "netex:network", "opra:service"}
        expand_mock.return_value = {
            "netex:line",
            "netex:network",
            "opra:service",
            "nits:abstract-delivery-element-responding-for",
            "nits:activation-point",
            "nits:expected-passenger-count",
            "nits:journey-pattern",
            "nits:line-network",
            "nits:service",
        }
        nch_mock.return_value = {
            "nits:abstract-delivery-element-responding-for",
            "nits:activation-point",
            "nits:expected-passenger-count",
            "nits:journey-pattern",
            "nits:line-network",
            "nits:service",
            "nits:network",
            "nits:line",
        }

        semantic_query = self.service.parse(
            text="How does service intensity relate to line and network concepts?",
            requested_scope=[],
        )

        self.assertLessEqual(len(semantic_query.core_concepts), 6)
        self.assertIn(semantic_query.core_concept, {"nits:line", "nits:network", "nits:line-network", "nits:service"})

    def test_extract_original_terms_keeps_informative_lowercase_tokens(self):
        terms = self.service._extract_original_terms(
            "Show me a NeTEx XML example for a simple line with stop points"
        )

        lowered = {value.lower() for value in terms}
        self.assertIn("netex", lowered)
        self.assertIn("line", lowered)
        self.assertIn("stop", lowered)
        self.assertIn("example", lowered)
        self.assertNotIn("show", lowered)


class SelectEffectiveScopeTests(SimpleTestCase):
    def _query(self, candidates, ambiguous):
        return SemanticQuery(
            intent="definition",
            normativity="unspecified",
            core_concept="nits:Journey",
            core_concepts=["nits:Journey", "nits:Line"] if ambiguous else ["nits:Journey"],
            ambiguous_core_concept=ambiguous,
            candidate_standards=candidates,
            original_terms=[],
            confidence={},
        )

    def test_requested_scope_always_wins(self):
        query = self._query(["NeTEx", "SIRI"], ambiguous=True)
        self.assertEqual(select_effective_scope(query, ["OpRa"]), (["OpRa"], False))

    def test_ambiguous_question_with_several_candidates_is_cut_to_the_first(self):
        query = self._query(["NeTEx", "SIRI"], ambiguous=True)
        self.assertEqual(select_effective_scope(query, []), (["NeTEx"], True))

    def test_unambiguous_or_single_candidate_keeps_all_candidates(self):
        self.assertEqual(select_effective_scope(self._query(["NeTEx", "SIRI"], False), None), (["NeTEx", "SIRI"], False))
        self.assertEqual(select_effective_scope(self._query(["SIRI"], True), []), (["SIRI"], False))
        self.assertEqual(select_effective_scope(self._query([], True), []), ([], False))
