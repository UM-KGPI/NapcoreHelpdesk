from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services import vocabulary_bridge

BRIDGE_ON = {
    "VOCABULARY_BRIDGE_ENABLED": True,
    "CONTROLLER_LLM_ENABLED": True,
    "CONTROLLER_LLM_API_BASE_URL": "http://llm.test/v1",
    "CONTROLLER_LLM_API_MODEL": "test-model",
}
ON_DEMAND = "I want to map a service into a NeTEx TemplateServiceJourney. The service operates when there is a demand."


class ParseTermsTests(SimpleTestCase):
    def test_reads_terms_from_json(self):
        self.assertEqual(vocabulary_bridge.parse_terms('{"terms": ["FLEXIBLE SERVICE PROPERTIES"]}'), ["FLEXIBLE SERVICE PROPERTIES"])

    def test_reads_terms_from_malformed_json(self):
        self.assertEqual(vocabulary_bridge.parse_terms('{": [": ["ELECTRIC VEHICLE CHARGING STATION"]}'), ["ELECTRIC VEHICLE CHARGING STATION"])

    def test_caps_the_number_of_terms(self):
        content = '{"terms": [' + ", ".join(f'"TERM {i}"' for i in range(10)) + "]}"
        self.assertEqual(len(vocabulary_bridge.parse_terms(content)), vocabulary_bridge.MAX_TERMS)


class BridgedQuestionConceptsTests(SimpleTestCase):
    def setUp(self):
        vocabulary_bridge.bridged_question_concepts.cache_clear()
        aliases = patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", {"netex:FlexibleServiceProperties": {"flexible service properties"}})
        aliases.start()
        self.addCleanup(aliases.stop)

    def test_off_by_default_and_makes_no_call(self):
        with patch.object(vocabulary_bridge, "_ask_for_terms") as ask:
            self.assertEqual(vocabulary_bridge.bridged_question_concepts(ON_DEMAND), frozenset())
        ask.assert_not_called()

    @override_settings(**BRIDGE_ON)
    def test_everyday_wording_reaches_the_class_the_llm_names(self):
        with patch.object(vocabulary_bridge, "_ask_for_terms", return_value=["TEMPLATE SERVICE JOURNEY", "FLEXIBLE SERVICE PROPERTIES"]):
            concepts = vocabulary_bridge.bridged_question_concepts(ON_DEMAND)
        self.assertEqual(concepts, frozenset({"netex:FlexibleServiceProperties"}))

    @override_settings(**BRIDGE_ON)
    def test_llm_failure_leaves_retrieval_unchanged(self):
        with patch.object(vocabulary_bridge, "_ask_for_terms", side_effect=TimeoutError("slow")):
            self.assertEqual(vocabulary_bridge.bridged_question_concepts(ON_DEMAND), frozenset())
