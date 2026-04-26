from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.llm_generator import LLMGenerationError, generate_answer_llm


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
                        "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
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
                    "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "examples/functions/line/NeTEx_01_simple_line.xml",
                    "chunkId": "chunk-1",
                    "label": "NeTEx_01_simple_line.xml",
                }
            ],
        )

        self.assertIn("cannot safely embed a fresh XML example", result["answer"])
        self.assertIn("NeTEx_01_simple_line.xml", result["answer"])
        self.assertIn("ScheduledStopPoint", result["answer"])
