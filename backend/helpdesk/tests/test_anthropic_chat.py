"""Anthropic (Claude) provider: services/anthropic_chat.py and the request builders that route to it."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import anthropic
from django.test import SimpleTestCase, override_settings

from helpdesk.services import anthropic_chat
from helpdesk.services.anthropic_chat import AnthropicRequestError, chat_completion, to_messages_api, unwrap_json_fence
from helpdesk.services.controller_llm import decide_route_with_controller_llm
from helpdesk.services.llm_generator import _request_chat_completion, stream_answer_llm


def _response(text: str, stop_reason: str = "end_turn", stop_details=None) -> SimpleNamespace:
    return SimpleNamespace(
        model="claude-opus-5-5",
        stop_reason=stop_reason,
        stop_details=stop_details,
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
    )


def _fake_client(response=None, error=None) -> MagicMock:
    client = MagicMock()
    create = client.with_options.return_value.messages.create
    if error is not None:
        create.side_effect = error
    else:
        create.return_value = response
    return client


class MessageConversionTests(SimpleTestCase):
    def test_system_messages_move_to_the_system_field_and_turns_alternate(self):
        system, turns = to_messages_api(
            [
                {"role": "system", "content": "Answer in JSON."},
                {"role": "user", "content": "Q1"},
                {"role": "user", "content": "More context"},
                {"role": "assistant", "content": "A1"},
                {"role": "system", "content": "Fix the citations."},
                {"role": "user", "content": "Retry"},
            ]
        )
        self.assertEqual(system, "Answer in JSON.\n\nFix the citations.")
        self.assertEqual(
            turns,
            [
                {"role": "user", "content": "Q1\n\nMore context"},
                {"role": "assistant", "content": "A1"},
                {"role": "user", "content": "Retry"},
            ],
        )

    def test_a_trailing_assistant_turn_is_never_sent_as_prefill(self):
        _, turns = to_messages_api([{"role": "assistant", "content": "Earlier answer"}])
        self.assertEqual(turns[0]["role"], "user")
        self.assertEqual(turns[-1]["role"], "user")

    def test_fenced_json_is_unwrapped_and_plain_text_is_kept(self):
        self.assertEqual(unwrap_json_fence('```json\n{"answer": "x"}\n```'), '{"answer": "x"}')
        self.assertEqual(unwrap_json_fence('{"answer": "x"}'), '{"answer": "x"}')
        self.assertEqual(unwrap_json_fence("RELEVANT"), "RELEVANT")


class ChatCompletionTests(SimpleTestCase):
    def setUp(self):
        anthropic_chat._client.cache_clear()

    def test_request_has_effort_and_no_temperature_and_reply_has_the_openai_shape(self):
        client = _fake_client(_response('```json\n{"answer": "A [E1]"}\n```'))
        with patch("helpdesk.services.anthropic_chat._client", return_value=client):
            payload = chat_completion(
                api_key="k",
                model="claude-opus-5-5",
                messages=[{"role": "system", "content": "S"}, {"role": "user", "content": "Q"}],
                max_tokens=5000,
                timeout_seconds=30,
                effort="low",
                json_answer=True,
            )

        params = client.with_options.return_value.messages.create.call_args.kwargs
        self.assertEqual(params["system"], "S")
        self.assertEqual(params["output_config"], {"effort": "low"})
        self.assertEqual(params["max_tokens"], 5000)
        self.assertNotIn("temperature", params)
        self.assertEqual(client.with_options.call_args.kwargs, {"timeout": 30, "max_retries": 1})
        self.assertEqual(payload["choices"][0]["message"]["content"], '{"answer": "A [E1]"}')
        self.assertEqual(payload["usage"], {"prompt_tokens": 100, "completion_tokens": 20})

    def test_refusal_is_raised_so_callers_fall_back(self):
        client = _fake_client(_response("", stop_reason="refusal", stop_details=SimpleNamespace(category="cyber")))
        with patch("helpdesk.services.anthropic_chat._client", return_value=client):
            with self.assertRaisesRegex(AnthropicRequestError, "refusal, category=cyber"):
                chat_completion(api_key="k", model="m", messages=[{"role": "user", "content": "Q"}], max_tokens=10, timeout_seconds=5)

    def test_api_errors_become_one_error_type(self):
        error = anthropic.RateLimitError("rate limited", response=MagicMock(status_code=429, headers={}), body=None)
        with patch("helpdesk.services.anthropic_chat._client", return_value=_fake_client(error=error)):
            with self.assertRaisesRegex(AnthropicRequestError, "Anthropic API error 429"):
                chat_completion(api_key="k", model="m", messages=[{"role": "user", "content": "Q"}], max_tokens=10, timeout_seconds=5)


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

ANTHROPIC = {
    "LLM_ENABLED": True,
    "LLM_PROVIDER": "anthropic",
    "LLM_MODEL": "claude-opus-5-5",
    "ANTHROPIC_API_KEY": "sk-ant-test",
    "LLM_ANTHROPIC_EFFORT": "medium",
    "LLM_STREAMING": True,
    "LLM_REASONING_TOKEN_ALLOWANCE": 2000,
}


@override_settings(**ANTHROPIC)
class RoutingTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.anthropic_chat.chat_completion")
    def test_answer_requests_go_to_anthropic_not_the_gateway(self, chat_mock, urlopen_mock):
        chat_mock.return_value = {"choices": [{"message": {"content": "{}"}}]}

        _request_chat_completion(
            api_base_url="https://llm.example.test/v1",
            api_key="gateway-key",
            model="claude-opus-5-5",
            timeout_seconds=60,
            temperature=0.2,
            max_tokens=6000,
            messages=[{"role": "user", "content": "Q"}],
        )

        urlopen_mock.assert_not_called()
        kwargs = chat_mock.call_args.kwargs
        self.assertEqual(kwargs["api_key"], "sk-ant-test")
        self.assertEqual(kwargs["effort"], "medium")
        self.assertEqual(kwargs["max_tokens"], 6000)
        self.assertTrue(kwargs["json_answer"])

    @patch("helpdesk.services.llm_generator._validate_grounded_example_output")
    @patch("helpdesk.services.llm_generator._validate_answer_language")
    @patch("helpdesk.services.llm_generator._validate_generated_answer")
    @patch("helpdesk.services.llm_generator._stream_request_chat_completion")
    @patch("helpdesk.services.anthropic_chat.chat_completion")
    def test_the_stream_endpoint_buffers_one_anthropic_call(self, chat_mock, stream_mock, _v, _l, _e):
        chat_mock.return_value = {"choices": [{"message": {"content": '{"answer": "Timetables use a TimetableFrame [E1]."}'}}]}
        chunks = [
            {
                "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                "commitSha": "abc",
                "sourcePath": "docs/timetables.md",
                "chunkId": "chunk-1",
                "text": "Timetables are exchanged in a TimetableFrame.",
                "score": 0.9,
            }
        ]

        events = list(stream_answer_llm(question="How are timetables exchanged in NeTEx?", chunks=chunks, scope=["NeTEx"]))

        stream_mock.assert_not_called()
        self.assertEqual(chat_mock.call_count, 1)
        self.assertEqual(events[-1][0], "done")
        self.assertEqual(events[-1][1]["answer"], "Timetables use a TimetableFrame [E1].")

    @patch("helpdesk.services.anthropic_chat.chat_completion", side_effect=AnthropicRequestError("Anthropic API error 529"))
    def test_a_failed_anthropic_stream_call_raises_the_generation_error_the_caller_handles(self, _chat):
        from helpdesk.services.llm_generator import LLMGenerationError

        with patch("helpdesk.services.llm_generator._validate_generated_answer"):
            with self.assertRaises(LLMGenerationError):
                list(stream_answer_llm(question="How are timetables exchanged in NeTEx?", chunks=CHUNKS, scope=["NeTEx"]))


@override_settings(
    CONTROLLER_LLM_ENABLED=True,
    CONTROLLER_LLM_PROVIDER="anthropic",
    CONTROLLER_LLM_API_MODEL="claude-haiku-5-5",
    CONTROLLER_LLM_ANTHROPIC_EFFORT="low",
    CONTROLLER_LLM_MAX_TOKENS=96,
    CONTROLLER_LLM_REASONING_TOKEN_ALLOWANCE=500,
    ANTHROPIC_API_KEY="sk-ant-test",
)
class ControllerTests(SimpleTestCase):
    @patch("helpdesk.services.controller_llm.request.urlopen")
    @patch("helpdesk.services.anthropic_chat.chat_completion")
    def test_routing_uses_the_controller_model_and_effort(self, chat_mock, urlopen_mock):
        chat_mock.return_value = {"choices": [{"message": {"content": '{"route":"faq","intent":"definition","confidence":0.9}'}}]}

        decision = decide_route_with_controller_llm(
            question="What is a NeTEx timetable (anthropic test)?", requested_scope=["NeTEx"], semantic_query={}
        )

        self.assertEqual(decision.route, "faq")
        urlopen_mock.assert_not_called()
        kwargs = chat_mock.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-haiku-5-5")
        self.assertEqual(kwargs["effort"], "low")
        self.assertEqual(kwargs["max_tokens"], 96 + 500)


class HealthProbeTests(SimpleTestCase):
    @override_settings(**ANTHROPIC, CONTROLLER_LLM_ENABLED=False)
    @patch("helpdesk.services.anthropic_chat.check_models")
    def test_health_llm_probes_the_anthropic_models_list(self, check_mock):
        check_mock.return_value = {"reachable": True, "modelIds": ["claude-opus-5-5", "claude-haiku-5-5"], "error": None}

        response = self.client.get("/api/v1/health/llm")

        block = response.json()["llm"]
        self.assertEqual(block["backend"], "anthropic")
        self.assertEqual(block["apiBaseUrl"], "https://api.anthropic.com")
        self.assertTrue(block["configuredModelAuthorized"])
        self.assertEqual(block["status"], "ok")
