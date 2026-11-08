from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import schema_structure as structure

STRUCTURE = {
    "found": True,
    "element": "StopPlace",
    "documentation": "Version of a named place where public transport may be accessed.",
    "source": "xsd/netex_part_1/part1_ifopt/netex_ifopt_stopPlace_version.xsd",
    "groups": [{"owner": "StopPlace", "inherited": False, "children": [{"name": "quays", "documentation": "QUAYs within the STOP PLACE."}]}],
    "attributes": [{"name": "id", "documentation": "Identifier of STOP PLACE.", "owner": "StopPlace"}],
}


class SubjectTests(SimpleTestCase):
    def test_question_shapes(self):
        cases = {
            "What does a StopPlace contain in NeTEx?": "StopPlace",
            "What elements does a Quay have?": "Quay",
            "Which attributes can a Line have in NeTEx?": "Line",
            "What can a VehicleType include?": "VehicleType",
            "Elements of a StopPlace": "StopPlace",
            "structure of ServiceJourney in NeTEx?": "ServiceJourney",
            "What is inside a stop place?": "stop place",
            "What does a stop place contain?": "stop place",
            "What is contained in NeTEx service journey?": "service journey",
            "What's in a Quay?": "Quay",
            "What goes into a VehicleType in NeTEx?": "VehicleType",
            "Which elements are part of a ServiceJourney?": "ServiceJourney",
            "What attributes belong to a Line?": "Line",
            "Explain what a StopPlace contains": "StopPlace",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(structure.structure_subject(question), expected)

    def test_other_questions_are_not_structure_questions(self):
        for question in ["What is a StopPlace in NeTEx?", "Show me a NeTEx example for a bus with 50 seats", "How are delays reported at a stop?", "What does NeTEx stand for?"]:
            with self.subTest(question=question):
                self.assertIsNone(structure.structure_subject(question))

    def test_candidate_names(self):
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", {"netex:StopPlace": {"stop place", "Stop Place"}}):
            self.assertEqual(structure.candidate_element_names("StopPlace"), ["StopPlace"])
            self.assertEqual(structure.candidate_element_names("stop place"), ["StopPlace"])
            self.assertEqual(structure.candidate_element_names("vehicle type"), ["VehicleType"])


@override_settings(NETEX_VALIDATOR_URL="http://validator:8091")
class StructureForQuestionTests(SimpleTestCase):
    def test_structure_for_a_netex_question(self):
        with patch.object(structure, "fetch_structure", side_effect=lambda element: dict(STRUCTURE) if element == "StopPlace" else None) as fetch:
            result = structure.schema_structure_for("What does a StopPlace contain in NeTEx?", None)
        self.assertEqual(result["element"], "StopPlace")
        self.assertNotIn("found", result)
        fetch.assert_called_once_with("StopPlace")

    def test_label_resolves_through_the_concept_aliases(self):
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", {"netex:StopPlace": {"stop place"}}), patch.object(
            structure, "fetch_structure", side_effect=lambda element: dict(STRUCTURE) if element == "StopPlace" else None
        ):
            self.assertEqual(structure.schema_structure_for("What does a stop place contain?", ["NeTEx"])["element"], "StopPlace")

    def test_not_in_netex_scope_or_not_that_shape(self):
        with patch.object(structure, "fetch_structure") as fetch:
            self.assertIsNone(structure.schema_structure_for("What does a StopPlace contain?", ["SIRI"]))
            self.assertIsNone(structure.schema_structure_for("What is a StopPlace in NeTEx?", ["NeTEx"]))
        fetch.assert_not_called()

    def test_unscoped_question_without_the_word_netex_gets_the_block(self):
        with patch.object(structure, "fetch_structure", return_value=dict(STRUCTURE)):
            self.assertEqual(structure.schema_structure_for("What does a StopPlace contain?", None)["element"], "StopPlace")

    def test_unknown_element_or_validator_down(self):
        with patch.object(structure, "fetch_structure", return_value=None):
            self.assertIsNone(structure.schema_structure_for("What does a Foo contain in NeTEx?", None))

    @override_settings(SCHEMA_STRUCTURE_ENABLED=False)
    def test_can_be_switched_off(self):
        with patch.object(structure, "fetch_structure") as fetch:
            self.assertIsNone(structure.schema_structure_for("What does a StopPlace contain in NeTEx?", None))
        fetch.assert_not_called()
