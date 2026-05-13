from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services.controller_llm import ControllerLLMError, decide_route_with_controller_llm


class ControllerLLMServiceTests(SimpleTestCase):
    @override_settings(CONTROLLER_LLM_ENABLED=False)
    def test_returns_none_when_disabled(self):
        decision = decide_route_with_controller_llm(
            question="How to use NeTEx timetable exchange?",
            requested_scope=["NeTEx"],
            semantic_query={"intent": "definition"},
        )
        self.assertIsNone(decision)

    @override_settings(
        CONTROLLER_LLM_ENABLED=True,
        CONTROLLER_LLM_EXECUTABLE="/bin/echo",
        CONTROLLER_LLM_MODEL_PATH="/tmp/model.gguf",
        CONTROLLER_LLM_DEVICE="none",
    )
    @patch("helpdesk.services.controller_llm.subprocess.run")
    def test_parses_valid_json_payload(self, run_mock):
        run_mock.return_value = SimpleNamespace(
            stdout='{"route":"rag","intent":"implementation_detail","confidence":0.87}',
            stderr="",
        )

        decision = decide_route_with_controller_llm(
            question="How to implement delayed journey exchange?",
            requested_scope=["OpRa"],
            semantic_query={"intent": "cross_standard_relation"},
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.route, "rag")
        self.assertEqual(decision.intent, "implementation_detail")
        self.assertGreaterEqual(decision.confidence, 0.8)

    @override_settings(
        CONTROLLER_LLM_ENABLED=True,
        CONTROLLER_LLM_EXECUTABLE="/bin/echo",
        CONTROLLER_LLM_MODEL_PATH="/tmp/model.gguf",
    )
    @patch("helpdesk.services.controller_llm.subprocess.run")
    def test_raises_on_invalid_route(self, run_mock):
        run_mock.return_value = SimpleNamespace(
            stdout='{"route":"abstain","intent":"unknown","confidence":0.5}',
            stderr="",
        )

        with self.assertRaises(ControllerLLMError):
            decide_route_with_controller_llm(
                question="Question",
                requested_scope=[],
                semantic_query={},
            )
