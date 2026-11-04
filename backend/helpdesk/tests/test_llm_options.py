"""Optional OpenAI-compatible request fields (services/llm_options.py) for gateways that reject them."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from config.settings import _bool_or
from helpdesk.services.controller_llm import decide_route_with_controller_llm
from helpdesk.services.llm_generator import _request_chat_completion, stream_answer_llm
from helpdesk.services.llm_options import (
    answer_max_tokens,
    answer_request_options,
    controller_max_tokens,
    controller_request_options,
)

# A managed model-as-a-service profile: plain non-streaming chat calls only.
MAAS = {
    "LLM_JSON_MODE": False,
    "LLM_DISABLE_THINKING": False,
    "LLM_STREAMING": False,
    "LLM_REASONING_TOKEN_ALLOWANCE": 512,
    "CONTROLLER_LLM_JSON_MODE": False,
    "CONTROLLER_LLM_DISABLE_THINKING": False,
    "CONTROLLER_LLM_REASONING_TOKEN_ALLOWANCE": 256,
}
NO_PROBE = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}


def _ok_response(content: str) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
    return response


class OptionHelperTests(SimpleTestCase):
    @override_settings(LLM_JSON_MODE=True, LLM_DISABLE_THINKING=True, LLM_REASONING_TOKEN_ALLOWANCE=0)
    def test_defaults_send_json_mode_and_thinking_off(self):
        self.assertEqual(
            answer_request_options(),
            {"response_format": {"type": "json_object"}, "chat_template_kwargs": {"enable_thinking": False}},
        )
        self.assertEqual(answer_max_tokens(4000), 4000)

    @override_settings(**MAAS)
    def test_maas_profile_sends_neither_and_adds_the_reasoning_allowance(self):
        self.assertEqual(answer_request_options(), {})
        self.assertEqual(controller_request_options(), {})
        self.assertEqual(answer_max_tokens(4000), 4512)
        self.assertEqual(controller_max_tokens(96), 352)

    @override_settings(CONTROLLER_LLM_JSON_MODE=True, CONTROLLER_LLM_DISABLE_THINKING=True)
    def test_plain_text_controller_calls_skip_json_mode_only(self):
        self.assertEqual(controller_request_options(json_mode=False), {"chat_template_kwargs": {"enable_thinking": False}})

    def test_controller_switches_fall_back_to_the_llm_setting_when_unset(self):
        self.assertIs(_bool_or("", True), True)
        self.assertIs(_bool_or("  ", False), False)
        self.assertIs(_bool_or("False", True), False)
        self.assertIs(_bool_or("on", False), True)
        with self.assertRaises(ImproperlyConfigured):
            _bool_or("maybe", True)


@override_settings(LLM_VERIFY_SSL=True, LLM_CA_BUNDLE="")
@patch("helpdesk.services.llm_model_recovery.check_gateway_models", return_value=NO_PROBE)
@patch("helpdesk.services.llm_generator.request.urlopen")
class AnswerRequestBodyTests(SimpleTestCase):
    def _sent_body(self, urlopen_mock) -> dict:
        urlopen_mock.return_value.__enter__.return_value = _ok_response('{"answer": "ok"}')
        _request_chat_completion(
            api_base_url="https://llm.example.test/v1",
            api_key="k",
            model="m",
            timeout_seconds=5,
            temperature=0.2,
            max_tokens=answer_max_tokens(4000),
            messages=[{"role": "user", "content": "q"}],
        )
        return json.loads(urlopen_mock.call_args[0][0].data.decode("utf-8"))

    @override_settings(LLM_JSON_MODE=True, LLM_DISABLE_THINKING=True, LLM_REASONING_TOKEN_ALLOWANCE=0)
    def test_default_body_is_unchanged(self, urlopen_mock, _probe):
        body = self._sent_body(urlopen_mock)
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(body["max_tokens"], 4000)

    @override_settings(**MAAS)
    def test_maas_body_has_only_plain_fields(self, urlopen_mock, _probe):
        body = self._sent_body(urlopen_mock)
        self.assertNotIn("response_format", body)
        self.assertNotIn("chat_template_kwargs", body)
        self.assertNotIn("stream", body)
        self.assertEqual(body["max_tokens"], 4512)


class StreamingSwitchTests(SimpleTestCase):
    CHUNKS = [
        {
            "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
            "commitSha": "abc",
            "sourcePath": "docs/timetables.md",
            "chunkId": "chunk-1",
            "text": "Timetables are exchanged in a TimetableFrame.",
            "score": 0.9,
        }
    ]

    @override_settings(LLM_ENABLED=True, LLM_PROVIDER="openai-compatible", LLM_API_BASE_URL="https://llm.example.test", **MAAS)
    @patch("helpdesk.services.llm_generator._validate_grounded_example_output")
    @patch("helpdesk.services.llm_generator._validate_answer_language")
    @patch("helpdesk.services.llm_generator._validate_generated_answer")
    @patch("helpdesk.services.llm_generator._stream_request_chat_completion")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_streaming_off_uses_one_plain_request_and_still_streams_to_the_client(
        self, request_mock, stream_mock, _validate, _language, _example
    ):
        request_mock.return_value = {
            "choices": [{"message": {"content": '{"answer": "Timetables are exchanged in a TimetableFrame [E1]."}'}}]
        }

        events = list(stream_answer_llm(question="How are timetables exchanged in NeTEx?", chunks=self.CHUNKS, scope=["NeTEx"]))

        stream_mock.assert_not_called()
        self.assertEqual(request_mock.call_count, 1)
        self.assertEqual(request_mock.call_args.kwargs["max_tokens"], 4000 + 512)
        self.assertTrue(any(kind == "token" for kind, _ in events))
        self.assertEqual(events[-1][0], "done")
        self.assertEqual(events[-1][1]["answer"], "Timetables are exchanged in a TimetableFrame [E1].")


@override_settings(
    CONTROLLER_LLM_ENABLED=True,
    CONTROLLER_LLM_PROVIDER="openai-compatible",
    CONTROLLER_LLM_API_BASE_URL="https://llm.example.test/v1",
    CONTROLLER_LLM_API_MODEL="m",
    CONTROLLER_LLM_MAX_TOKENS=96,
    **MAAS,
)
class ControllerRequestBodyTests(SimpleTestCase):
    @patch("helpdesk.services.llm_model_recovery.check_gateway_models", return_value=NO_PROBE)
    @patch("helpdesk.services.controller_llm.request.urlopen")
    def test_maas_routing_body_has_only_plain_fields(self, urlopen_mock, _probe):
        urlopen_mock.return_value.__enter__.return_value = _ok_response(
            '{"route":"faq","intent":"definition","confidence":0.9}'
        )

        decision = decide_route_with_controller_llm(
            question="What is a NeTEx timetable?", requested_scope=["NeTEx"], semantic_query={"intent": "definition"}
        )

        self.assertEqual(decision.route, "faq")
        body = json.loads(urlopen_mock.call_args[0][0].data.decode("utf-8"))
        self.assertNotIn("response_format", body)
        self.assertNotIn("chat_template_kwargs", body)
        self.assertEqual(body["max_tokens"], 96 + 256)
