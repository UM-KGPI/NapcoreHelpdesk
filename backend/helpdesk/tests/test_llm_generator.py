from __future__ import annotations

import io
import json
from unittest.mock import patch
from urllib import error

from django.test import SimpleTestCase

from helpdesk.services import llm_model_recovery
from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.llm_generator import (
    LLMGenerationError,
    _build_messages,
    _stream_request_chat_completion,
    _validate_no_unsupported_element_purpose_claims,
    generate_answer_llm,
)


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
    def setUp(self):
        # The model-recovery cache is a module-level dict shared across the
        # process; reset it so a correction discovered in one test doesn't
        # leak into the next.
        llm_model_recovery._corrected_model_cache.clear()
        llm_model_recovery._verified_ok_cache.clear()

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
        self.assertIn("fenced code block", messages[0]["content"])
        self.assertIn("single evidence block", messages[0]["content"])

    def _system_prompt(self, question: str) -> str:
        chunk = {
            "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
            "commitSha": "abc",
            "sourcePath": "xsd/netex_part_1/part1_ifopt/netex_ifopt_stopPlace_version.xsd",
            "chunkId": "chunk-1",
            "text": "StopPlace definition",
            "score": 0.91,
        }
        return _build_messages(question=question, chunks=[chunk], scope=[])[0]["content"]

    def test_definition_question_asks_for_the_definition_first_and_no_code(self):
        for question in ("what is a StopPlace?", "What is a ServiceJourney in NeTEx?", "Define Quay"):
            with self.subTest(question=question):
                prompt = self._system_prompt(question)
                self.assertIn("start with the definition of X", prompt)
                self.assertNotIn("Include a relevant code example", prompt)

    def test_questions_asking_for_structure_or_examples_keep_their_own_instructions(self):
        technical = self._system_prompt("What is the XML structure of a StopPlace?")
        self.assertIn("Include a relevant code example", technical)
        self.assertNotIn("start with the definition of X", technical)

        example = self._system_prompt("Show me a NeTEx XML example for stop points.")
        self.assertIn("single evidence block", example)
        self.assertNotIn("start with the definition of X", example)

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.llm_generator._build_ssl_context")
    @patch("helpdesk.services.llm_generator.settings")
    def test_generate_answer_llm_retries_with_github_token_on_models_401(
        self, settings_mock, ssl_context_mock, urlopen_mock, check_gateway_models_mock
    ):
        # This test is about the 401/GitHub-token fallback, not model-drift
        # preflight resolution -- keep the proactive probe out of the way so
        # it doesn't reach the network or interfere with the urlopen mock.
        check_gateway_models_mock.return_value = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}
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

    def _key_model_access_denied_error(self, url: str, authorized_model: str) -> error.HTTPError:
        body = (
            '{"error":{"message":"key not allowed to access model. This key can only '
            f"access models=['{authorized_model}']. Tried to access old-model-alias\","
            '"type":"key_model_access_denied","param":"model","code":"403"}}'
        ).encode("utf-8")
        return error.HTTPError(url=url, code=403, msg="Forbidden", hdrs=None, fp=io.BytesIO(body))

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.llm_generator._build_ssl_context")
    @patch("helpdesk.services.llm_generator.settings")
    def test_generate_answer_llm_self_heals_on_model_access_denied_403(
        self, settings_mock, ssl_context_mock, urlopen_mock, check_gateway_models_mock
    ):
        # This test covers the reactive (403-triggered) self-heal path; make
        # the proactive gateway probe report "unreachable" so resolution
        # falls through to it unchanged instead of hitting the network.
        check_gateway_models_mock.return_value = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}
        settings_mock.LLM_ENABLED = True
        settings_mock.LLM_PROVIDER = "openai-compatible"
        settings_mock.LLM_API_KEY = "sk-shared-key"
        settings_mock.GITHUB_API_TOKEN = ""
        settings_mock.LLM_API_BASE_URL = "https://litellm.lhrs.si/v1"
        settings_mock.LLM_TEMPERATURE = 0.0
        settings_mock.LLM_MAX_TOKENS = 220
        settings_mock.LLM_TIMEOUT_SECONDS = 4
        settings_mock.LLM_MODEL = "old-model-alias"
        settings_mock.LLM_VERIFY_SSL = True
        settings_mock.LLM_CA_BUNDLE = ""

        ssl_context_mock.return_value = object()
        url = "https://litellm.lhrs.si/v1/chat/completions"
        urlopen_mock.side_effect = [
            self._key_model_access_denied_error(url, "nvidia/Qwen3.6-35B-A3B-NVFP4"),
            _FakeResponse(
                {
                    "model": "nvidia/Qwen3.6-35B-A3B-NVFP4",
                    "choices": [{"message": {"content": "Use ServiceFrame with profile validation [E1]."}}],
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
                    "text": "Use ServiceFrame with profile validation.",
                    "score": 0.88,
                }
            ],
            scope=["NeTEx"],
        )

        self.assertIn("ServiceFrame", result["answer"])
        self.assertEqual(urlopen_mock.call_count, 2)
        first_body = json.loads(urlopen_mock.call_args_list[0].args[0].data)
        second_body = json.loads(urlopen_mock.call_args_list[1].args[0].data)
        self.assertEqual(first_body["model"], "old-model-alias")
        self.assertEqual(second_body["model"], "nvidia/Qwen3.6-35B-A3B-NVFP4")

        # A second call should skip straight to the corrected model -- no
        # second 403 round trip -- because the correction is now cached.
        # Echo the chunk's own wording so citation-grounding validation
        # passes cleanly on the first attempt (an unrelated rejection would
        # trigger an internal retry this test isn't mocking a response for).
        urlopen_mock.reset_mock()
        urlopen_mock.side_effect = [
            _FakeResponse(
                {
                    "model": "nvidia/Qwen3.6-35B-A3B-NVFP4",
                    "choices": [{"message": {"content": "Stops are represented as ScheduledStopPoint [E1]."}}],
                }
            ),
        ]
        generate_answer_llm(
            question="A different question about NeTEx stops?",
            chunks=[
                {
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc",
                    "sourcePath": "README.md",
                    "chunkId": "chunk-1",
                    "text": "Stops are represented as ScheduledStopPoint.",
                    "score": 0.88,
                }
            ],
            scope=["NeTEx"],
        )
        self.assertEqual(urlopen_mock.call_count, 1)
        only_body = json.loads(urlopen_mock.call_args_list[0].args[0].data)
        self.assertEqual(only_body["model"], "nvidia/Qwen3.6-35B-A3B-NVFP4")

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.llm_generator._build_ssl_context")
    def test_stream_request_chat_completion_self_heals_on_model_access_denied_403(
        self, ssl_context_mock, urlopen_mock, check_gateway_models_mock
    ):
        check_gateway_models_mock.return_value = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}
        ssl_context_mock.return_value = object()
        url = "https://litellm.lhrs.si/v1/chat/completions"

        class _FakeStreamResponse:
            def __init__(self, lines: list[bytes]):
                self._lines = lines

            def __iter__(self):
                return iter(self._lines)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        stream_lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            b"data: [DONE]\n",
        ]
        urlopen_mock.side_effect = [
            self._key_model_access_denied_error(url, "nvidia/Qwen3.6-35B-A3B-NVFP4"),
            _FakeStreamResponse(stream_lines),
        ]

        deltas = list(
            _stream_request_chat_completion(
                api_base_url="https://litellm.lhrs.si/v1",
                api_key="sk-shared-key",
                model="old-model-alias",
                timeout_seconds=4,
                temperature=0.0,
                max_tokens=220,
                messages=[{"role": "user", "content": "hi"}],
            )
        )

        self.assertEqual(deltas, ["Hello"])
        self.assertEqual(urlopen_mock.call_count, 2)
        first_body = json.loads(urlopen_mock.call_args_list[0].args[0].data)
        second_body = json.loads(urlopen_mock.call_args_list[1].args[0].data)
        self.assertEqual(first_body["model"], "old-model-alias")
        self.assertEqual(second_body["model"], "nvidia/Qwen3.6-35B-A3B-NVFP4")

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    @patch("helpdesk.services.llm_generator.request.urlopen")
    @patch("helpdesk.services.llm_generator._build_ssl_context")
    @patch("helpdesk.services.llm_generator.settings")
    def test_generate_answer_llm_rejects_fabricated_xml_example(
        self, settings_mock, ssl_context_mock, urlopen_mock, check_gateway_models_mock
    ):
        check_gateway_models_mock.return_value = {"reachable": False, "modelIds": None, "error": "probe disabled for test"}
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

        # Should list available examples instead of inventing XML
        self.assertIn("Yes, the following examples are available", result["answer"])
        self.assertIn("[E1]", result["answer"])
        self.assertIn("NeTEx_01_simple_line.xml", result["answer"])
        # Should not invent/fabricate XML structures
        self.assertNotIn("<", result["answer"])


class ElementPurposeClaimValidationTests(SimpleTestCase):
    def _chunks(self):
        return [
            {
                "sourcePath": "xsd/netex_part_2/part2_journeyTimes/netex_serviceJourney_version.xsd",
                "docType": "schema",
                "text": "TemplateServiceJourney: a vehicle journey with frequencies.",
            },
            {
                "sourcePath": "xsd/netex_part_2/part2_journeyTimes/netex_flexibleService_version.xsd",
                "docType": "schema",
                "text": "FlexibleServiceProperties describes a flexible/demand-responsive service and BookingArrangements.",
            },
            {
                "sourcePath": "examples/functions/timetable/Netex_05.2_Bus_TemplateTimetable_RhythmicalFrequency.xml",
                "docType": "example",
                "text": "<TemplateServiceJourney><TimeDemandTypeRef ref=\"hde:TDT_45\"/></TemplateServiceJourney>",
            },
        ]

    def test_rejects_purpose_claim_grounded_only_in_an_example_chunk(self):
        answer = (
            "The <TimeDemandTypeRef> element is used to indicate that the service operates "
            "on demand [E3]."
        )
        with self.assertRaises(LLMGenerationError):
            _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_allows_purpose_claim_grounded_in_a_schema_chunk(self):
        answer = "`FlexibleServiceProperties` is used to indicate demand-responsive service [E2]."
        # Should not raise.
        _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_allows_mention_without_a_purpose_claim(self):
        answer = "The example [E3] contains a `TimeDemandTypeRef` element referencing `hde:TDT_45`."
        # Should not raise - no purpose/meaning verb attached to the element.
        _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_allows_definition_claim_for_element_the_definition_chunk_actually_names(self):
        answer = "`TemplateServiceJourney` is used to represent a vehicle journey with frequencies [E1]."
        # Should not raise - [E1] is a schema chunk that contains the element name.
        _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_allows_purpose_claim_when_definition_is_elsewhere_in_evidence_not_the_sentence_citation(self):
        # The sentence cites the example [E3] (where the XML snippet comes from), but a
        # definitional chunk for FlexibleServiceProperties exists elsewhere in the full
        # evidence set ([E2]). This must be accepted — the definition doesn't have to be
        # among this specific sentence's own citations.
        answer = "`FlexibleServiceProperties` is used to indicate demand-responsive service [E3]."
        # Should not raise.
        _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_still_rejects_when_no_evidence_block_anywhere_defines_the_element(self):
        # TimeDemandTypeRef has no definitional chunk anywhere in the evidence set (only
        # the example [E3] mentions it) - this must stay rejected regardless of which
        # citation the sentence uses.
        answer = (
            "The `TimeDemandTypeRef` element is used to indicate that the service operates "
            "on demand [E3]."
        )
        with self.assertRaises(LLMGenerationError):
            _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_fenced_code_block_elements_do_not_leak_into_a_neighboring_sentence(self):
        # A verbatim XML snippet has no sentence-ending punctuation between its tags, so
        # without stripping the fence first, every tag inside it bleeds into whatever
        # prose sentence surrounds it. None of these child elements (DepartureTime,
        # dayTypes, Arrival, ...) have definitions in this evidence set, so if they leaked
        # in, this would wrongly raise.
        answer = (
            "The TemplateServiceJourney is defined as a vehicle journey with frequencies [E1], "
            "and the following snippet is used to show its structure:\n"
            "```xml\n"
            "<TemplateServiceJourney>\n"
            "    <DepartureTime>10:20:00.0Z</DepartureTime>\n"
            "    <dayTypes><DayTypeRef ref=\"hde:DT_01\"/></dayTypes>\n"
            "    <calls><Call><Arrival><ForAlighting>false</ForAlighting></Arrival></Call></calls>\n"
            "</TemplateServiceJourney>\n"
            "```\n"
            "This matches the example in [E3]."
        )
        # Should not raise - the purpose claim ("is used to show its structure") is about
        # the snippet itself, not about the untagged child elements inside the fence.
        _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=self._chunks())

    def test_retry_feedback_asks_to_cite_definition_and_keep_snippet_not_drop_content(self):
        from helpdesk.services.llm_generator import _append_feedback_message

        messages = _append_feedback_message(
            messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}],
            rejected_answer="The `TimeDemandTypeRef` element is used to indicate demand [E3].",
            error_msg=(
                "Sentence attributes a purpose/meaning to element(s) ['TimeDemandTypeRef'] but no "
                "evidence block defines them: '...'. An element's name is not its definition — do "
                "not infer what an element means or is used for unless some evidence block actually "
                "defines it."
            ),
        )
        feedback_text = messages[-1]["content"]
        self.assertIn("Check EVERY evidence block", feedback_text)
        self.assertIn("KEEP any verbatim XML snippet", feedback_text)
        self.assertNotIn("either omit that claim", feedback_text)


class UnwrapJsonAnswerTests(SimpleTestCase):
    """Production showed {': ': '...'} as an answer: a JSON response with an
    unexpected key fell through to str(dict), which the UI rendered verbatim."""

    def test_answer_field_is_returned(self):
        from helpdesk.services.llm_generator import _unwrap_json_answer

        self.assertEqual(_unwrap_json_answer('{"answer": "LineRef.", "citations_used": ["E1"]}'), "LineRef.")

    def test_unexpected_key_returns_the_prose_not_the_dict(self):
        from helpdesk.services.llm_generator import _unwrap_json_answer

        result = _unwrap_json_answer('{": ": "The element is LineRef [E1].", "citations_used": "E1"}')

        self.assertEqual(result, "The element is LineRef [E1].")
        self.assertFalse(result.startswith("{"))

    def test_json_without_any_text_value_returns_the_raw_text(self):
        from helpdesk.services.llm_generator import _unwrap_json_answer

        self.assertEqual(_unwrap_json_answer('{"citations_used": ["E1"]}'), '{"citations_used": ["E1"]}')

    def test_plain_text_is_unchanged(self):
        from helpdesk.services.llm_generator import _unwrap_json_answer

        self.assertEqual(_unwrap_json_answer("Plain prose."), "Plain prose.")
