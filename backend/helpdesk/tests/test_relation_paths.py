from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import relation_paths as rp

NETEX = "https://netex.org.uk/netex/2.0#"


def _prop(local: str, domain: str, range_: str, xsd: str = "netex_part_2/x.xsd", mechanism: str = "reference") -> dict:
    return {
        "prop": f"{NETEX}{local}",
        "domain": f"{NETEX}{domain}",
        "range": f"{NETEX}{range_}",
        "comment": f"Extracted from: {xsd} ({mechanism})",
    }


def _sub(sub: str, sup: str) -> dict:
    return {"sub": f"{NETEX}{sub}", "super": f"{NETEX}{sup}"}


def _graph(extra_props=(), extra_subs=()):
    """Journey has no property to Line; its subclass ServiceJourney does (LineRef).
    Journey and Line both point to a generic hub, and Journey sits under a
    framework root that must never be climbed."""
    props = [
        _prop("lineRef_ServiceJourney", "ServiceJourney", "Line", "netex_part_2/part2_journeyTimes/netex_serviceJourney_version.xsd"),
        _prop("accessibilityAssessment_Journey", "Journey", "AccessibilityAssessment", mechanism="containment"),
        _prop("accessibilityAssessment_Line", "Line", "AccessibilityAssessment", mechanism="containment"),
        *[_prop(f"accessibilityAssessment_X{i}", f"X{i}", "AccessibilityAssessment", mechanism="containment") for i in range(20)],
        _prop("operatorRef_DataManagedObjectSibling", "Sibling", "Line"),
        *extra_props,
    ]
    subs = [
        _sub("ServiceJourney", "Journey"),
        _sub("Journey", "DataManagedObject"),
        _sub("Sibling", "DataManagedObject"),
        *extra_subs,
    ]
    return rp.build_relation_graph(props, subs)


class ElementNameTests(SimpleTestCase):
    def test_reference_strips_domain_suffix_and_capitalises(self):
        self.assertEqual(rp.element_name("lineRef_ServiceJourney", "ServiceJourney", "reference"), "LineRef")

    def test_containment_list_keeps_lower_case_wrapper(self):
        self.assertEqual(rp.element_name("journeys_Block", "Block", "containment-list"), "journeys")


class FindRelationPathsTests(SimpleTestCase):
    def test_line_and_journey_connect_through_service_journey_line_ref(self):
        paths = rp.find_relation_paths(_graph(), {"netex:Journey"}, {"netex:Line"})

        best = paths[0]
        self.assertEqual(best.down_from_source, (("netex:Journey", "netex:ServiceJourney"),))
        self.assertEqual([edge.element for edge in best.properties], ["LineRef"])
        self.assertEqual(best.cost, 1.5)

    def test_hub_path_never_beats_the_specific_one(self):
        """Journey and Line both contain an AccessibilityAssessment (a hub with 22
        neighbours); that shared hub must rank below, or be cut as a detour."""
        paths = rp.find_relation_paths(_graph(), {"netex:Journey"}, {"netex:Line"}, max_paths=5)

        self.assertNotIn("netex:AccessibilityAssessment", {e.range for e in paths[0].properties})
        for path in paths[1:]:
            self.assertGreaterEqual(path.cost, paths[0].cost)

    def test_never_climbs_to_a_superclass(self):
        """Journey -> DataManagedObject -> Sibling -> Line would be 3 edges, but the
        first step climbs, which is never allowed."""
        paths = rp.find_relation_paths(_graph(), {"netex:Journey"}, {"netex:Line"}, max_paths=10)

        for path in paths:
            nodes = {node for step in path.down_from_source + path.down_from_target for node in step}
            self.assertNotIn("netex:DataManagedObject", nodes)
            self.assertNotIn("netex:Sibling", {e.domain for e in path.properties})

    def test_works_in_either_direction(self):
        paths = rp.find_relation_paths(_graph(), {"netex:Line"}, {"netex:Journey"})

        self.assertEqual(paths[0].down_from_target, (("netex:Journey", "netex:ServiceJourney"),))
        self.assertEqual([edge.element for edge in paths[0].properties], ["LineRef"])

    def test_subtype_relation_is_returned_as_a_hierarchy_path(self):
        paths = rp.find_relation_paths(_graph(), {"netex:Journey"}, {"netex:ServiceJourney"})

        self.assertEqual(paths[0].properties, ())
        self.assertEqual(paths[0].down_from_source, (("netex:Journey", "netex:ServiceJourney"),))

    def test_costly_detour_is_dropped_when_a_direct_path_exists(self):
        """Line and ServiceJourney both reference an Operator, but ServiceJourney
        references Line directly: the shared-Operator detour must not be shown."""
        graph = _graph(extra_props=[
            _prop("operatorRef_Line", "Line", "Operator"),
            _prop("operatorRef_ServiceJourney", "ServiceJourney", "Operator"),
        ])

        paths = rp.find_relation_paths(graph, {"netex:Line"}, {"netex:ServiceJourney"}, max_paths=5)

        self.assertEqual([[e.element for e in p.properties] for p in paths], [["LineRef"]])

    def test_close_alternative_paths_are_kept(self):
        graph = _graph(extra_props=[_prop("lineRef_DeadRun", "DeadRun", "Line")], extra_subs=[_sub("DeadRun", "Journey")])

        paths = rp.find_relation_paths(graph, {"netex:Journey"}, {"netex:Line"}, max_paths=5)

        self.assertEqual(
            {p.down_from_source[-1][1] for p in paths if p.down_from_source and p.properties},
            {"netex:ServiceJourney", "netex:DeadRun"},
        )

    def test_unknown_concepts_give_no_paths(self):
        self.assertEqual(rp.find_relation_paths(_graph(), {"netex:Nope"}, {"netex:Line"}), [])

    def test_paths_longer_than_three_edges_are_dropped(self):
        props = [_prop("a_A", "A", "B"), _prop("b_B", "B", "C"), _prop("c_C", "C", "D"), _prop("d_D", "D", "E")]
        graph = rp.build_relation_graph(props, [])

        self.assertTrue(rp.find_relation_paths(graph, {"netex:A"}, {"netex:D"}))
        self.assertEqual(rp.find_relation_paths(graph, {"netex:A"}, {"netex:E"}), [])


class AnchorGroupTests(SimpleTestCase):
    def test_transmodel_and_standard_concepts_naming_the_same_thing_are_one_anchor(self):
        groups = rp.anchor_groups(
            {"netex:Line", "transmodel:LINE", "netex:Journey", "transmodel:JOURNEY", "transmodel:between"},
            concept_to_transmodel={"netex:Line": "transmodel:LINE", "netex:Journey": "transmodel:JOURNEY"},
            transmodel_to_concepts={"transmodel:LINE": {"netex:Line"}, "transmodel:JOURNEY": {"netex:Journey"}},
        )

        self.assertCountEqual(groups, [{"netex:Line"}, {"netex:Journey"}])


class RelationQuestionTests(SimpleTestCase):
    def test_detects_relationship_wording(self):
        for question in [
            "What is the relation between a line and a journey ?",
            "How is a Route related to a JourneyPattern?",
            "How do I link a stop place to a quay?",
            "Which XML element does a NeTEx ServiceJourney use to reference its Line?",
        ]:
            with self.subTest(question=question):
                self.assertTrue(rp.is_relation_question(question))

    def test_ignores_plain_definition_questions(self):
        self.assertFalse(rp.is_relation_question("What is a stop place?"))


class FormatTests(SimpleTestCase):
    def test_chunk_cites_the_xsd_and_names_the_element(self):
        paths = rp.find_relation_paths(_graph(), {"netex:Journey"}, {"netex:Line"})
        chunk = rp.format_relation_paths_as_chunks(paths[:1], commit_shas={"NeTEx": "abc123"})[0]

        self.assertIn("Path: Journey ⊃ ServiceJourney —LineRef→ Line", chunk["text"])
        self.assertIn("ServiceJourney is a subclass of Journey", chunk["text"])
        self.assertIn("xsd/netex_part_2/part2_journeyTimes/netex_serviceJourney_version.xsd", chunk["text"])
        self.assertEqual(chunk["sourcePath"], "docs/ontology/standards/netex.ttl#lineRef_ServiceJourney")
        self.assertEqual(
            chunk["repositoryUrl"],
            "https://github.com/TransmodelEcosystem/NeTEx/blob/abc123/"
            "xsd/netex_part_2/part2_journeyTimes/netex_serviceJourney_version.xsd",
        )
        self.assertEqual(chunk["docType"], "ontology-relation")


class RetrievalIntegrationTests(SimpleTestCase):
    @override_settings(GRAPHDB_ENABLED=True, GRAPHDB_SPARQL_ENDPOINT="http://localhost:7200", GRAPHDB_REPOSITORY="r")
    @patch("helpdesk.services.retrieval_gateway.supporting_subclass_chunks", return_value=[])
    @patch("helpdesk.services.retrieval_gateway.indexed_commit_shas", return_value={})
    @patch("helpdesk.services.retrieval_gateway.load_relation_graph")
    def test_relation_candidates_rank_above_scored_chunks(self, load_mock, _shas, _support):
        from helpdesk.services.retrieval_gateway import _relation_path_candidates

        load_mock.return_value = _graph()
        with patch("helpdesk.services.retrieval_gateway.CONCEPT_TO_TRANSMODEL", {}), patch(
            "helpdesk.services.retrieval_gateway.TRANSMODEL_TO_CONCEPTS", {}
        ):
            candidates = _relation_path_candidates({"netex:Journey", "netex:Line"})

        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["docType"], "ontology-relation")
        self.assertGreater(candidates[0]["_rankScore"], 2.0)
        self.assertIn("LineRef", candidates[0]["text"])

    @override_settings(GRAPHDB_ENABLED=False)
    def test_no_relation_candidates_without_graphdb(self):
        from helpdesk.services.retrieval_gateway import _relation_path_candidates

        self.assertEqual(_relation_path_candidates({"netex:Journey", "netex:Line"}), [])
