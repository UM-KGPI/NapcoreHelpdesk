from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import concept_presence as presence


class ShapeTests(SimpleTestCase):
    def test_existence_questions(self):
        for question in [
            "Does a bus have drivers name described in NeTEx?",
            "Is there an element for a stop place entrance in NeTEx?",
            "Does NeTEx support parking spaces?",
            "Can NeTEx describe a lift?",
        ]:
            with self.subTest(question=question):
                self.assertTrue(presence.asks_whether_modelled(question))
        for question in ["What is a StopPlace in NeTEx?", "Show me a NeTEx example for a bus with 50 seats", "How are delays reported?"]:
            with self.subTest(question=question):
                self.assertFalse(presence.asks_whether_modelled(question))

    def test_singular_question(self):
        self.assertEqual(presence.singular_question("Does a bus have drivers name"), "Does a bus have driver name")
        self.assertEqual(presence.singular_question("entries and parking spaces"), "entry and parking space")


class ConceptTests(SimpleTestCase):
    def test_plural_concepts_and_aligned_standard_classes(self):
        aliases = {"transmodel:DRIVER": {"DRIVER"}, "netex:DriverTrip": {"driver trip"}, "netex:NeTEx": {"netex"}}
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", aliases), patch(
            "helpdesk.services.semantic_graph.CONCEPT_TO_TRANSMODEL", {"netex:DriverTrip": "transmodel:DRIVER_TRIP"}
        ), patch("helpdesk.services.concept_vectors.semantic_concepts", return_value=[]):
            self.assertEqual(presence.presence_concepts("Does a bus have drivers name described in NeTEx?"), ["transmodel:DRIVER"])
            self.assertEqual(presence.presence_concepts("Does NeTEx have driver trips?")[0], "transmodel:DRIVER_TRIP")


class EvidenceTests(SimpleTestCase):
    def test_not_for_other_questions_or_scopes(self):
        with patch.object(presence, "presence_concepts") as concepts:
            self.assertEqual(presence.presence_evidence("What is a StopPlace in NeTEx?", ["NeTEx"]), [])
            self.assertEqual(presence.presence_evidence("Does SIRI have a driver?", ["SIRI"]), [])
        concepts.assert_not_called()

    @override_settings(CONCEPT_PRESENCE_ENABLED=False)
    def test_can_be_switched_off(self):
        self.assertEqual(presence.presence_evidence("Does NeTEx support parking spaces?", ["NeTEx"]), [])

    def test_element_names_own_name_first_then_objects(self):
        declarations = {"declarations": [
            {"name": "DriverTripRef", "object": False}, {"name": "DriverTrip", "object": True},
            {"name": "DriverScheduleFrame", "object": True}, {"name": "ReachedFloorAnnouncement", "object": False},
        ]}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                import json

                return json.dumps(declarations).encode()

        with patch("helpdesk.services.schema_structure.fetch_structure", side_effect=lambda n: {"element": n} if n == "DriverRef" else None), patch(
            "urllib.request.urlopen", return_value=Response()
        ):
            self.assertEqual(presence._element_names("Driver"), ["DriverRef", "DriverTrip", "DriverScheduleFrame", "DriverTripRef"])


class PromptTests(SimpleTestCase):
    def test_existence_brief_only_for_existence_questions(self):
        from helpdesk.services.llm_generator import EXISTENCE_RULE, _build_messages

        chunk = {"repositoryUrl": "https://github.com/x/NeTEx", "commitSha": "a", "sourcePath": "xsd/a.xsd", "chunkId": "c", "text": "DriverRef"}
        user = _build_messages("Does NeTEx have a driver?", [chunk], existence=True)[1]["content"]
        self.assertTrue(user.endswith(EXISTENCE_RULE + "\n\nWrite your answer:"))
        self.assertNotIn("WHETHER THE STANDARD HAS IT", _build_messages("Does NeTEx have a driver?", [chunk])[1]["content"])


class ScoreTests(SimpleTestCase):
    def test_every_evidence_block_has_a_score(self):
        definition = {"sourcePath": "docs/ontology/standards/transmodel.ttl#DRIVER", "chunkId": "d", "text": "DRIVER"}
        element = {"sourcePath": "xsd/a.xsd", "chunkId": "e", "text": "DriverRef", "score": 1.0}
        with patch.object(presence, "presence_concepts", return_value=["transmodel:DRIVER"]), patch(
            "helpdesk.services.retrieval_gateway.retrieve_concept_definitions", return_value=[{}]
        ), patch("helpdesk.services.retrieval_gateway.format_definitions_as_chunks", return_value=[dict(definition)]), patch(
            "helpdesk.services.retrieval_gateway.indexed_commit_shas", return_value={}
        ), patch.object(presence, "_element_names", return_value=["DriverRef"]), patch(
            "helpdesk.services.schema_structure.definition_chunk", return_value=dict(element)
        ):
            chunks = presence.presence_evidence("Does NeTEx have a driver?", ["NeTEx"])
        self.assertEqual([c["score"] for c in chunks], [1.0, 1.0])


class ModellingTests(SimpleTestCase):
    def test_question_kinds(self):
        self.assertEqual(presence.question_kind("How can fare distribution be defined in NeTEx?"), "how")
        self.assertEqual(presence.question_kind("How do you describe a parking in NeTEx?"), "how")
        self.assertEqual(presence.question_kind("Does NeTEx support parking spaces?"), "whether")
        self.assertEqual(presence.question_kind("What is a StopPlace in NeTEx?"), "")
        self.assertEqual(presence.question_kind("How are delays reported at a stop?"), "")

    def test_head_word_concepts_use_the_most_specific_word(self):
        aliases = {
            "transmodel:DISTRIBUTION_CHANNEL": {"DISTRIBUTION CHANNEL"},
            "transmodel:DISTRIBUTION_ASSIGNMENT": {"DISTRIBUTION ASSIGNMENT"},
            "transmodel:FARE_PRODUCT": {"FARE PRODUCT"},
            "transmodel:FARE_ZONE": {"FARE ZONE"},
            "transmodel:FARE_TABLE": {"FARE TABLE"},
            "transmodel:DISTRIBUTION_RIGHT": {"DISTRIBUTION RIGHT"},
        }
        implemented = {
            "transmodel:DISTRIBUTION_CHANNEL": {"netex:DistributionChannel"},
            "transmodel:DISTRIBUTION_ASSIGNMENT": {"netex:DistributionAssignment"},
            "transmodel:FARE_PRODUCT": {"netex:FareProduct"},
            "transmodel:FARE_ZONE": {"netex:FareZone"},
            "transmodel:FARE_TABLE": {"netex:FareTable"},
        }
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", aliases), patch(
            "helpdesk.services.semantic_graph.TRANSMODEL_TO_CONCEPTS", implemented
        ):
            # "fare" heads three implemented classes, "distribution" two: the more specific word wins;
            # DISTRIBUTION RIGHT is not implemented in NeTEx and is left out.
            self.assertEqual(
                presence.head_word_concepts("How can fare distribution be defined in NeTEx?"),
                ["transmodel:DISTRIBUTION_ASSIGNMENT", "transmodel:DISTRIBUTION_CHANNEL"],
            )

    def test_modelling_brief(self):
        from helpdesk.services.llm_generator import EXISTENCE_RULE, MODELLING_RULE, _build_messages

        chunk = {"repositoryUrl": "https://github.com/x/NeTEx", "commitSha": "a", "sourcePath": "xsd/a.xsd", "chunkId": "c", "text": "DistributionChannel"}
        user = _build_messages("How can fare distribution be defined in NeTEx?", [chunk], existence="how")[1]["content"]
        self.assertIn(MODELLING_RULE, user)
        self.assertNotIn(EXISTENCE_RULE, user)
