from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase
from django.test import override_settings

from helpdesk.services.question_parsing import (
    QuestionParsingService,
    SemanticQuery,
    has_scope_hint,
    select_effective_scope,
)


class QuestionParsingServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = QuestionParsingService()

    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_builds_semantic_query_with_discovered_scope(
        self,
        extract_mock,
        expand_mock,
        transmodel_mock,
    ):
        extract_mock.return_value = {"opra:delayed-journey"}
        expand_mock.return_value = {"opra:delayed-journey", "netex:service-journey-pattern"}
        transmodel_mock.return_value = {"transmodel:journey-pattern"}

        semantic_query = self.service.parse(
            text="How SHALL delayed journeys be represented in ServiceJourneyPattern examples?",
            requested_scope=[],
        )

        self.assertEqual(semantic_query.intent, "normative_status")
        self.assertEqual(semantic_query.normativity, "mandatory")
        self.assertEqual(semantic_query.core_concept, "transmodel:journey-pattern")
        # No standard is named, so none is searched; what the ontology found is kept for the abstention rules.
        self.assertEqual(semantic_query.candidate_standards, [])
        self.assertEqual(semantic_query.discovered_standards, ["NeTEx", "OpRa"])
        self.assertIn("ServiceJourneyPattern", semantic_query.original_terms)
        self.assertGreaterEqual(semantic_query.confidence["concept"], 0.9)

    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_keeps_requested_scope_when_provided(self, extract_mock, expand_mock, transmodel_mock):
        extract_mock.return_value = {"netex:service-journey-pattern"}
        expand_mock.return_value = {"netex:service-journey-pattern", "opra:delayed-journey"}
        transmodel_mock.return_value = {"transmodel:journey-pattern"}

        semantic_query = self.service.parse(
            text="Compare ServiceJourneyPattern and delayed journeys.",
            requested_scope=["OpRa"],
        )

        self.assertEqual(semantic_query.intent, "comparison")
        self.assertEqual(semantic_query.candidate_standards, ["OpRa"])
        self.assertEqual(semantic_query.normativity, "unspecified")

    @patch.object(QuestionParsingService, "_discover_standards")
    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_scopes_to_standards_named_in_the_question(
        self, extract_mock, expand_mock, transmodel_mock, discover_mock
    ):
        """Graph discovery lists every standard for a core concept; the named one must win."""
        extract_mock.return_value = {"siri:estimated-vehicle-journey"}
        expand_mock.return_value = {"siri:estimated-vehicle-journey"}
        transmodel_mock.return_value = {"transmodel:journey"}
        discover_mock.return_value = ["NeTEx", "OpRa", "SIRI", "Transmodel"]

        named_one = self.service.parse(text="What is a SIRI EstimatedVehicleJourney used for?", requested_scope=[])
        named_two = self.service.parse(text="How does OpRa relate to NeTEx journeys?", requested_scope=[])
        named_none = self.service.parse(text="What is an EstimatedVehicleJourney used for?", requested_scope=[])

        self.assertEqual(named_one.candidate_standards, ["SIRI"])
        self.assertEqual(named_two.candidate_standards, ["NeTEx", "OpRa"])
        # No standard named: nothing is searched in particular, whatever the ontology lists.
        self.assertEqual(named_none.candidate_standards, [])
        self.assertEqual(named_none.discovered_standards, ["NeTEx", "OpRa", "SIRI", "Transmodel"])
        self.assertEqual(named_one.discovered_standards, ["NeTEx", "OpRa", "SIRI", "Transmodel"])

    @patch.object(QuestionParsingService, "_discover_standards")
    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_requested_scope_still_beats_named_standards(
        self, extract_mock, expand_mock, transmodel_mock, discover_mock
    ):
        extract_mock.return_value = {"siri:estimated-vehicle-journey"}
        expand_mock.return_value = {"siri:estimated-vehicle-journey"}
        transmodel_mock.return_value = {"transmodel:journey"}
        discover_mock.return_value = ["OpRa"]

        semantic_query = self.service.parse(
            text="What is a SIRI EstimatedVehicleJourney used for?", requested_scope=["OpRa"]
        )

        self.assertEqual(semantic_query.candidate_standards, ["OpRa"])

    @override_settings(GRAPHDB_ENABLED=True, GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/sparql")
    @patch("helpdesk.services.question_parsing.GraphDBConnector")
    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_prefers_graphdb_anchor_when_available(
        self,
        extract_mock,
        expand_mock,
        transmodel_mock,
        connector_cls_mock,
    ):
        extract_mock.return_value = {"opra:delayed-journey"}
        expand_mock.return_value = {"opra:delayed-journey"}
        transmodel_mock.return_value = {"transmodel:fallback"}

        connector = connector_cls_mock.return_value
        connector.anchor_term_to_core_concepts.return_value = [
            "https://transmodel-cen.eu/6.2/JourneyPattern"
        ]
        connector.discover_standards_for_core_concept.return_value = ["NeTEx", "SIRI"]

        semantic_query = self.service.parse(
            text="How should ServiceJourneyPattern be referenced?",
            requested_scope=[],
        )

        self.assertEqual(semantic_query.core_concept, "transmodel:JourneyPattern")
        self.assertEqual(semantic_query.candidate_standards, [])
        self.assertEqual(semantic_query.discovered_standards, ["NeTEx", "SIRI"])
        connector.anchor_term_to_core_concepts.assert_called()
        connector.discover_standards_for_core_concept.assert_called()

    @override_settings(GRAPHDB_ENABLED=True, GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/sparql")
    @patch("helpdesk.services.question_parsing.GraphDBConnector")
    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_falls_back_when_graphdb_returns_no_anchors(
        self,
        extract_mock,
        expand_mock,
        transmodel_mock,
        connector_cls_mock,
    ):
        extract_mock.return_value = {"netex:service-journey-pattern"}
        expand_mock.return_value = {"netex:service-journey-pattern"}
        transmodel_mock.return_value = {"transmodel:journey-pattern"}

        connector = connector_cls_mock.return_value
        connector.anchor_term_to_core_concepts.return_value = []
        connector.discover_standards_for_core_concept.return_value = []

        semantic_query = self.service.parse(
            text="Where is ServiceJourneyPattern defined?",
            requested_scope=[],
        )
        self.assertEqual(semantic_query.discovered_standards, ["NeTEx"])

        self.assertEqual(semantic_query.core_concept, "transmodel:journey-pattern")
        self.assertEqual(semantic_query.candidate_standards, [])

    @patch("helpdesk.services.question_parsing.get_concept_transmodel_ids")
    @patch("helpdesk.services.question_parsing.expand_graph_concepts")
    @patch("helpdesk.services.question_parsing.extract_graph_concepts")
    def test_parse_ranks_and_caps_core_concept_candidates(self, extract_mock, expand_mock, transmodel_mock):
        extract_mock.return_value = {"netex:line", "netex:network", "opra:service"}
        expand_mock.return_value = {
            "netex:line",
            "netex:network",
            "opra:service",
            "transmodel:abstract-delivery-element-responding-for",
            "transmodel:activation-point",
            "transmodel:expected-passenger-count",
            "transmodel:journey-pattern",
            "transmodel:line-network",
            "transmodel:service",
        }
        transmodel_mock.return_value = {
            "transmodel:abstract-delivery-element-responding-for",
            "transmodel:activation-point",
            "transmodel:expected-passenger-count",
            "transmodel:journey-pattern",
            "transmodel:line-network",
            "transmodel:service",
            "transmodel:network",
            "transmodel:line",
        }

        semantic_query = self.service.parse(
            text="How does service intensity relate to line and network concepts?",
            requested_scope=[],
        )

        self.assertLessEqual(len(semantic_query.core_concepts), 6)
        self.assertIn(
            semantic_query.core_concept,
            {"transmodel:line", "transmodel:network", "transmodel:line-network", "transmodel:service"},
        )

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
            core_concept="transmodel:Journey",
            core_concepts=["transmodel:Journey", "transmodel:Line"] if ambiguous else ["transmodel:Journey"],
            ambiguous_core_concept=ambiguous,
            candidate_standards=candidates,
            original_terms=[],
            confidence={},
        )

    def test_requested_scope_always_wins(self):
        query = self._query(["NeTEx", "SIRI"], ambiguous=True)
        self.assertEqual(select_effective_scope(query, ["OpRa"]), (["OpRa"], False))

    def test_ambiguous_question_keeps_every_named_standard_and_asks_to_clarify(self):
        """Candidate standards are the ones the question names; dropping one would
        answer "How does SIRI use NeTEx?" from NeTEx alone."""
        query = self._query(["NeTEx", "SIRI"], ambiguous=True)
        self.assertEqual(select_effective_scope(query, []), (["NeTEx", "SIRI"], True))

    def test_unambiguous_or_single_candidate_keeps_all_candidates(self):
        self.assertEqual(select_effective_scope(self._query(["NeTEx", "SIRI"], False), None), (["NeTEx", "SIRI"], False))
        self.assertEqual(select_effective_scope(self._query(["SIRI"], True), []), (["SIRI"], False))
        self.assertEqual(select_effective_scope(self._query([], True), []), ([], False))


class HasScopeHintTests(SimpleTestCase):
    def _query(self, discovered):
        return SemanticQuery(
            intent="definition",
            normativity="unspecified",
            core_concept="transmodel:Journey",
            core_concepts=["transmodel:Journey"],
            ambiguous_core_concept=False,
            candidate_standards=[],
            original_terms=[],
            confidence={},
            discovered_standards=discovered,
        )

    def test_a_requested_or_named_scope_is_a_hint(self):
        self.assertTrue(has_scope_hint(self._query([]), ["SIRI"]))

    def test_a_standard_the_ontology_recognised_is_a_hint_although_nothing_is_searched_in_particular(self):
        self.assertTrue(has_scope_hint(self._query(["NeTEx", "OpRa"]), []))

    def test_nothing_requested_named_or_recognised_is_no_hint(self):
        self.assertFalse(has_scope_hint(self._query([]), []))

    def test_a_query_object_without_the_field_counts_as_no_recognised_standard(self):
        class Legacy:
            pass

        self.assertFalse(has_scope_hint(Legacy(), []))
        self.assertTrue(has_scope_hint(Legacy(), ["OpRa"]))


class AnchorTermsTests(SimpleTestCase):
    """GraphDB anchors per term: queried in parallel, cached per term (0.64 s of parsing, 2026-11-09)."""

    def setUp(self):
        from helpdesk.services import question_parsing

        question_parsing._ANCHOR_CACHE.clear()

    class _Connector:
        endpoint_url = "http://graphdb.test/repositories/r"
        repository = "r"

        def __init__(self, anchors):
            self.anchors = anchors
            self.calls: list[str] = []

        def anchor_term_to_core_concepts(self, term):
            import time

            self.calls.append(term)
            time.sleep(0.05)
            return self.anchors.get(term, [])

    def test_each_term_gets_its_own_anchors_and_is_queried_once(self):
        from helpdesk.services.question_parsing import _anchor_terms

        connector = self._Connector({"stop place": ["tm#STOP_PLACE"], "quay": ["tm#QUAY"]})
        terms = ["stop place", "quay", "two"]

        first = _anchor_terms(connector, terms)
        second = _anchor_terms(connector, terms)

        self.assertEqual(first, {"stop place": ["tm#STOP_PLACE"], "quay": ["tm#QUAY"], "two": []})
        self.assertEqual(second, first)
        self.assertEqual(sorted(connector.calls), sorted(terms))  # the second call was served from the cache

    def test_terms_are_queried_in_parallel(self):
        import time

        from helpdesk.services.question_parsing import _anchor_terms

        connector = self._Connector({})
        started = time.perf_counter()
        _anchor_terms(connector, ["a", "b", "c", "d"])

        self.assertLess(time.perf_counter() - started, 0.15)  # four 0.05 s queries, not 0.2 s in a row

    def test_the_anchor_order_follows_the_terms(self):
        from helpdesk.services.question_parsing import QuestionParsingService

        connector = self._Connector({"quay": ["https://transmodel-cen.eu/6.2/QUAY"], "stop place": ["https://transmodel-cen.eu/6.2/STOP_PLACE"]})
        service = QuestionParsingService.__new__(QuestionParsingService)
        service._graphdb_connector = lambda: connector

        self.assertEqual(service._anchor_with_graphdb(["stop place", "quay"]), ["transmodel:STOP_PLACE", "transmodel:QUAY"])
