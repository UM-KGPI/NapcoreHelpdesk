from __future__ import annotations

import io
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib import error

from django.test import SimpleTestCase, override_settings

from helpdesk.services import llm_model_recovery
from helpdesk.services.controller_llm import (
    ControllerLLMError,
    _decide_route_cached,
    decide_route_with_controller_llm,
)


class ControllerLLMServiceTests(SimpleTestCase):
    def setUp(self):
        # Decisions are cached in-process; clear between tests so mocked
        # provider responses cannot leak across test cases.
        _decide_route_cached.cache_clear()
        llm_model_recovery._corrected_model_cache.clear()
        llm_model_recovery._verified_ok_cache.clear()
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
        CONTROLLER_LLM_PROVIDER="subprocess",
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
        CONTROLLER_LLM_PROVIDER="subprocess",
        CONTROLLER_LLM_EXECUTABLE="/bin/echo",
        CONTROLLER_LLM_MODEL_PATH="/tmp/model.gguf",
    )
    @patch("helpdesk.services.controller_llm.subprocess.run")
    def test_identical_questions_are_served_from_cache(self, run_mock):
        run_mock.return_value = SimpleNamespace(
            stdout='{"route":"faq"}',
            stderr="",
        )

        first = decide_route_with_controller_llm(
            question="What is a SIRI situation exchange?",
            requested_scope=["SIRI"],
            semantic_query={"intent": "definition"},
        )
        second = decide_route_with_controller_llm(
            question="What is a SIRI situation exchange?",
            requested_scope=["SIRI"],
            semantic_query={"intent": "definition"},
        )

        self.assertEqual(first, second)
        self.assertEqual(first.route, "faq")
        run_mock.assert_called_once()

    @override_settings(
        CONTROLLER_LLM_ENABLED=True,
        CONTROLLER_LLM_PROVIDER="subprocess",
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

    @override_settings(
        CONTROLLER_LLM_ENABLED=True,
        CONTROLLER_LLM_PROVIDER="openai-compatible",
        CONTROLLER_LLM_API_BASE_URL="https://llm.example.test/v1",
        CONTROLLER_LLM_API_MODEL="qwen3",
    )
    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    @patch("helpdesk.services.controller_llm.request.urlopen")
    def test_http_provider_disables_thinking_and_requests_json(self, urlopen_mock, check_gateway_models_mock):
        check_gateway_models_mock.return_value = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps(
            {
                "choices": [
                    {"message": {"content": '{"route":"faq","intent":"definition","confidence":0.9}'}}
                ]
            }
        ).encode("utf-8")
        urlopen_mock.return_value.__enter__.return_value = response_mock

        decision = decide_route_with_controller_llm(
            question="What is a NeTEx timetable?",
            requested_scope=["NeTEx"],
            semantic_query={"intent": "definition"},
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.route, "faq")

        sent_request = urlopen_mock.call_args[0][0]
        sent_body = json.loads(sent_request.data.decode("utf-8"))
        # Reasoning models must not burn the small token budget on hidden
        # chain-of-thought, and the reply must be parseable JSON.
        self.assertEqual(sent_body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(sent_body["response_format"], {"type": "json_object"})

    @override_settings(
        CONTROLLER_LLM_ENABLED=True,
        CONTROLLER_LLM_PROVIDER="openai-compatible",
        CONTROLLER_LLM_API_BASE_URL="https://litellm.lhrs.si/v1",
        CONTROLLER_LLM_API_MODEL="old-model-alias",
    )
    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    @patch("helpdesk.services.controller_llm.request.urlopen")
    def test_http_provider_self_heals_on_model_access_denied_403(self, urlopen_mock, check_gateway_models_mock):
        check_gateway_models_mock.return_value = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}
        error_body = (
            '{"error":{"message":"key not allowed to access model. This key can only '
            "access models=['nvidia/Qwen3.6-35B-A3B-NVFP4']. Tried to access "
            'old-model-alias","type":"key_model_access_denied","param":"model","code":"403"}}'
        ).encode("utf-8")
        forbidden = error.HTTPError(
            url="https://litellm.lhrs.si/v1/chat/completions",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=io.BytesIO(error_body),
        )
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps(
            {"choices": [{"message": {"content": '{"route":"rag","intent":"definition","confidence":0.8}'}}]}
        ).encode("utf-8")
        success = MagicMock()
        success.__enter__.return_value = response_mock
        success.__exit__.return_value = False
        urlopen_mock.side_effect = [forbidden, success]

        decision = decide_route_with_controller_llm(
            question="What is a NeTEx ScheduledStopPoint?",
            requested_scope=["NeTEx"],
            semantic_query={"intent": "definition"},
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.route, "rag")
        self.assertEqual(urlopen_mock.call_count, 2)
        first_body = json.loads(urlopen_mock.call_args_list[0].args[0].data)
        second_body = json.loads(urlopen_mock.call_args_list[1].args[0].data)
        self.assertEqual(first_body["model"], "old-model-alias")
        self.assertEqual(second_body["model"], "nvidia/Qwen3.6-35B-A3B-NVFP4")
