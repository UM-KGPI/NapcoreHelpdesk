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

    def test_paths_longer_than_four_edges_are_dropped(self):
        props = [
            _prop("a_A", "A", "B"),
            _prop("b_B", "B", "C"),
            _prop("c_C", "C", "D"),
            _prop("d_D", "D", "E"),
            _prop("e_E", "E", "F"),
        ]
        graph = rp.build_relation_graph(props, [])

        self.assertTrue(rp.find_relation_paths(graph, {"netex:A"}, {"netex:E"}, max_paths=10))
        self.assertEqual(rp.find_relation_paths(graph, {"netex:A"}, {"netex:F"}), [])


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


TM = "https://transmodel-cen.eu/6.2/"


def _definition(concept: str, label: str, comment: str) -> dict:
    return {"concept": f"{TM}{concept}", "label": label, "comment": comment}


def _journey_line_graph():
    """Journey to Line, as in NeTEx: two shortcuts, the Transmodel chain through
    JourneyPattern and Route, and a rival chain of the same length through
    CourseOfJourneys that Transmodel does not document at every step.
    JourneyPattern gets many extra neighbours so the cost ranking alone puts its
    chain last, which is what happened in production."""
    props = [
        _prop("lineRef_ServiceJourney", "ServiceJourney", "Line"),
        _prop("journeyPatternRef_ServiceJourney", "ServiceJourney", "JourneyPattern"),
        _prop("journeyPatternRef_VehicleJourney", "VehicleJourney", "JourneyPattern"),
        _prop("routeRef_JourneyPattern", "JourneyPattern", "Route"),
        _prop("lineRef_Route", "Route", "Line"),
        _prop("courseOfJourneysRef_ServiceJourney", "ServiceJourney", "CourseOfJourneys"),
        _prop("journeys_CourseOfJourneys", "CourseOfJourneys", "JourneyDesignator", mechanism="containment-list"),
        _prop("lineRef_JourneyDesignator", "JourneyDesignator", "Line"),
        *[_prop(f"x{i}_JourneyPattern", "JourneyPattern", f"Hub{i}") for i in range(30)],
    ]
    subs = [_sub("ServiceJourney", "Journey"), _sub("VehicleJourney", "Journey")]
    definitions = [
        _definition("SERVICE_JOURNEY", "SERVICE JOURNEY", "A passenger carrying VEHICLE JOURNEY. NOTE: The pattern of working is in principle defined by a SERVICE JOURNEY PATTERN."),
        _definition("VEHICLE_JOURNEY", "VEHICLE JOURNEY", "The planned movement of a vehicle from the start point to the end point of a JOURNEY PATTERN on a specified ROUTE."),
        _definition("JOURNEY_PATTERN", "JOURNEY PATTERN", "An ordered list of SCHEDULED STOP POINTs on a single ROUTE, describing the pattern of working."),
        _definition("ROUTE", "ROUTE", "An ordered list of located POINTs defining one single path through the network."),
        _definition("LINE", "LINE", "A group of ROUTEs which is generally known to the public by a similar name or number."),
        _definition("COURSE_OF_JOURNEYS", "COURSE OF JOURNEYS", "A part of a BLOCK composed of consecutive VEHICLE JOURNEYs, all operated on the same LINE."),
    ]
    transmodel_of = {
        "netex:ServiceJourney": "transmodel:SERVICE_JOURNEY",
        "netex:VehicleJourney": "transmodel:VEHICLE_JOURNEY",
        "netex:JourneyPattern": "transmodel:JOURNEY_PATTERN",
        "netex:Route": "transmodel:ROUTE",
        "netex:Line": "transmodel:LINE",
        "netex:CourseOfJourneys": "transmodel:COURSE_OF_JOURNEYS",
    }
    return rp.build_relation_graph(props, subs, definitions, transmodel_of)


class SentenceNamingTests(SimpleTestCase):
    def test_plural_counts(self):
        self.assertTrue(rp._sentence_naming("A group of ROUTEs which is known.", "ROUTE"))

    def test_compound_ending_in_the_name_counts(self):
        self.assertTrue(rp._sentence_naming("Defined by a SERVICE JOURNEY PATTERN.", "JOURNEY PATTERN"))

    def test_compound_continuing_the_name_does_not(self):
        self.assertIsNone(rp._sentence_naming("A section of a LINE SECTION.", "LINE"))

    def test_lower_case_words_are_not_concept_names(self):
        self.assertIsNone(rp._sentence_naming("Vehicles follow the route along the line.", "ROUTE"))

    def test_returns_the_sentence_that_names_it(self):
        text = "First sentence. An ordered list on a single ROUTE, describing work. NOTE: other."
        self.assertEqual(rp._sentence_naming(text, "ROUTE"), "An ordered list on a single ROUTE, describing work.")


class DocumentedChainTests(SimpleTestCase):
    def test_journey_line_includes_the_transmodel_chain_regression(self):
        """Issue #108: the answer to "What is the relation between a line and a
        journey ?" must show the JourneyPattern, Route, Line chain."""
        paths = rp.find_relation_paths(_journey_line_graph(), {"netex:Journey"}, {"netex:Line"})

        chains = [p for p in paths if p.kind == "transmodel-chain"]
        self.assertEqual(len(chains), 1)
        self.assertEqual([e.element for e in chains[0].properties], ["JourneyPatternRef", "RouteRef", "LineRef"])
        self.assertTrue(any("on a single ROUTE" in q for q in chains[0].documentation))
        self.assertTrue(any("A group of ROUTEs" in q for q in chains[0].documentation))

    def test_shortcut_is_still_returned_as_a_direct_path(self):
        paths = rp.find_relation_paths(_journey_line_graph(), {"netex:Journey"}, {"netex:Line"})

        self.assertEqual(paths[0].kind, "direct")
        self.assertEqual([e.element for e in paths[0].properties], ["LineRef"])

    def test_chain_with_an_undocumented_step_is_not_added(self):
        paths = rp.find_relation_paths(_journey_line_graph(), {"netex:Journey"}, {"netex:Line"}, max_paths=1)

        for path in paths:
            self.assertNotIn("netex:CourseOfJourneys", {e.range for e in path.properties})

    def test_variants_through_different_subclasses_count_once(self):
        """ServiceJourney and VehicleJourney both reach JourneyPattern; that is
        one chain, not two."""
        paths = rp.find_relation_paths(_journey_line_graph(), {"netex:Journey"}, {"netex:Line"})

        self.assertEqual(sum(1 for p in paths if p.kind == "transmodel-chain"), 1)

    def test_without_definitions_no_chain_is_added(self):
        graph = _journey_line_graph()
        graph.definitions.clear()
        graph._documented.clear()

        paths = rp.find_relation_paths(graph, {"netex:Journey"}, {"netex:Line"})

        self.assertFalse(any(p.kind == "transmodel-chain" for p in paths))

    def test_chain_evidence_is_labelled_and_quotes_transmodel(self):
        paths = rp.find_relation_paths(_journey_line_graph(), {"netex:Journey"}, {"netex:Line"})
        chain = next(p for p in paths if p.kind == "transmodel-chain")

        chunk = rp.format_relation_paths_as_chunks([chain])[0]

        self.assertIn("Transmodel chain", chunk["text"].splitlines()[0])
        self.assertIn("Transmodel definitions documenting these steps:", chunk["text"])
        self.assertIn('LINE: "A group of ROUTEs', chunk["text"])
        self.assertTrue(chunk["label"].startswith("Transmodel chain"))

    def test_direct_path_evidence_is_labelled_as_direct_reference(self):
        paths = rp.find_relation_paths(_journey_line_graph(), {"netex:Journey"}, {"netex:Line"})

        chunk = rp.format_relation_paths_as_chunks([paths[0]])[0]

        self.assertIn("NeTEx direct reference", chunk["text"].splitlines()[0])
