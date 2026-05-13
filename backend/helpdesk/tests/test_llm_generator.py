from __future__ import annotations

import io
import json
from unittest.mock import patch
from urllib import error

from django.test import SimpleTestCase

from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.llm_generator import LLMGenerationError, _build_messages, generate_answer_llm


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class LLMGeneratorTests(SimpleTestCase):
    def test_build_messages_requests_single_block_verbatim_snippet_when_available(self):
        messages = _build_messages(
            question="Show me a NeTEx XML example for stop points.",
            chunks=[
                {
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc",
                    "sourcePath": "examples/functions/line/NeTEx_01_simple_line.xml",
                    "chunkId": "chunk-1",
                    "text": "<Line id=\"line:1\">...",
                    "score": 0.91,
                }
            ],
            scope=["NeTEx"],
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("include one fenced block", messages[0]["content"])
        self.assertIn("single evidence block", messages[0]["content"])

    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.llm_generator._build_ssl_context")
    @patch("helpdesk.services.llm_generator.settings")
    def test_generate_answer_llm_retries_with_github_token_on_models_401(
        self, settings_mock, ssl_context_mock, urlopen_mock
    ):
        settings_mock.LLM_ENABLED = True
        settings_mock.LLM_PROVIDER = "openai-compatible"
        settings_mock.LLM_API_KEY = "primary-key-without-models-permission"
        settings_mock.GITHUB_API_TOKEN = "github-token-with-models-permission"
        settings_mock.LLM_API_BASE_URL = "https://models.inference.ai.azure.com"
        settings_mock.LLM_TEMPERATURE = 0.0
        settings_mock.LLM_MAX_TOKENS = 220
        settings_mock.LLM_TIMEOUT_SECONDS = 4
        settings_mock.LLM_MODEL = "gpt-4o-mini"
        settings_mock.LLM_VERIFY_SSL = True
        settings_mock.LLM_CA_BUNDLE = ""

        ssl_context_mock.return_value = object()
        unauthorized_body = (
            '{"error":{"code":"unauthorized","message":"The `models` permission is required to access this endpoint"}}'
        ).encode("utf-8")
        urlopen_mock.side_effect = [
            error.HTTPError(
                url="https://models.inference.ai.azure.com/chat/completions",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=io.BytesIO(unauthorized_body),
            ),
            _FakeResponse(
                {
                    "model": "gpt-4o-mini",
                    "choices": [
                        {
                            "message": {
                                "content": "Use ServiceFrame and TimetableFrame with profile validation [E1]."
                            }
                        }
                    ],
                }
            ),
        ]

        result = generate_answer_llm(
            question="How do I exchange timetables in NeTEx?",
            chunks=[
                {
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc",
                    "sourcePath": "README.md",
                    "chunkId": "chunk-1",
                    "text": "Use ServiceFrame and TimetableFrame with profile validation.",
                    "score": 0.88,
                }
            ],
            scope=["NeTEx"],
        )

        self.assertIn("ServiceFrame", result["answer"])
        self.assertEqual(result["model"], "gpt-4o-mini")
        self.assertEqual(urlopen_mock.call_count, 2)
        first_request = urlopen_mock.call_args_list[0].args[0]
        second_request = urlopen_mock.call_args_list[1].args[0]
        self.assertIn("models.inference.ai.azure.com", first_request.full_url)
        self.assertIn("models.inference.ai.azure.com", second_request.full_url)
        self.assertEqual(
            first_request.headers.get("Authorization"),
            "Bearer primary-key-without-models-permission",
        )
        self.assertEqual(
            second_request.headers.get("Authorization"),
            "Bearer github-token-with-models-permission",
        )

    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.llm_generator._build_ssl_context")
    @patch("helpdesk.services.llm_generator.settings")
    def test_generate_answer_llm_rejects_fabricated_xml_example(self, settings_mock, ssl_context_mock, urlopen_mock):
        settings_mock.LLM_ENABLED = True
        settings_mock.LLM_PROVIDER = "openai-compatible"
        settings_mock.LLM_API_KEY = "test-key"
        settings_mock.LLM_API_BASE_URL = "https://llm.example.test"
        settings_mock.LLM_TEMPERATURE = 0.0
        settings_mock.LLM_MAX_TOKENS = 500
        settings_mock.LLM_TIMEOUT_SECONDS = 10
        settings_mock.LLM_MODEL = "test-model"
        settings_mock.LLM_VERIFY_SSL = True
        settings_mock.LLM_CA_BUNDLE = ""

        ssl_context_mock.return_value = object()
        urlopen_mock.return_value = _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Here is an example.\n\n"
                                "```xml\n"
                                "<Network>\n"
                                "  <StopPlace id=\"stop_place_001\">\n"
                                "    <Name>Stop Place A</Name>\n"
                                "  </StopPlace>\n"
                                "  <Route id=\"route_001\"/>\n"
                                "</Network>\n"
                                "```"
                            )
                        }
                    }
                ]
            }
        )

        with self.assertRaises(LLMGenerationError):
            generate_answer_llm(
                question="Show me a NeTEx XML example for a simple line with stop points.",
                chunks=[
                    {
                        "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                        "commitSha": "abc",
                        "sourcePath": "examples/functions/line/NeTEx_01_simple_line.xml",
                        "chunkId": "chunk-1",
                        "text": (
                            "<Line id=\"line:1\">\n"
                            "  <Name>Simple line</Name>\n"
                            "</Line>\n"
                            "<ScheduledStopPoint id=\"ssp:1\">\n"
                            "  <Name>Alpha</Name>\n"
                            "</ScheduledStopPoint>"
                        ),
                        "score": 0.91,
                    }
                ],
                scope=["NeTEx"],
            )

    def test_generate_answer_for_structured_example_request_refuses_to_invent_xml(self):
        result = generate_answer(
            question="Show me a NeTEx XML example for a simple line with stop points.",
            chunks=[
                {
                    "text": "Simple line XML example with stop points, StopPlace and ScheduledStopPoint via PassengerStopAssignment.",
                    "score": 0.82,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "examples/functions/line/NeTEx_01_simple_line.xml",
                    "chunkId": "chunk-1",
                    "label": "NeTEx_01_simple_line.xml",
                }
            ],
        )

        self.assertIn("Based on retrieved approved-source evidence", result["answer"])
        self.assertIn("[E1]", result["answer"])
        self.assertNotIn("NeTEx_01_simple_line.xml", result["answer"])
        self.assertIn("validate implementation", result["answer"])
