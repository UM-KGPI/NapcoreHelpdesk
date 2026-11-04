"""An answer whose retry also failed validation is served (e7dbeb4, d1950a9) but marked: review required,
confidence capped at 0.80, answer_validated False. A validated answer is unchanged."""

from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services.llm_generator import (
    UNVALIDATED_ANSWER_MAX_CONFIDENCE,
    LLMGenerationError,
    generate_answer_llm,
    stream_answer_llm,
)

CHUNKS = [
    {
        "repositoryUrl": "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP",
        "commitSha": "abc",
        "sourcePath": "src/tables/class-dataset.html",
        "chunkId": "chunk-1",
        "text": "A dataset is a collection of data published or curated by a single source.",
        "score": 0.93,
    }
]
SETTINGS = {"LLM_ENABLED": True, "LLM_PROVIDER": "openai-compatible", "LLM_API_BASE_URL": "https://llm.example.test", "LLM_STREAMING": True}
QUESTION = "What is a Dataset in mobilityDCAT-AP?"


@override_settings(**SETTINGS)
@patch("helpdesk.services.llm_generator._validate_grounded_example_output")
@patch("helpdesk.services.llm_generator._validate_answer_language")
@patch("helpdesk.services.llm_generator.question_language", return_value="English")
class NonStreamingTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator._validate_generated_answer", side_effect=LLMGenerationError("no specific content"))
    @patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=["First [E1].", "Retry [E1]."])
    def test_a_twice_rejected_answer_is_served_but_marked(self, _gen, _val, _lang, _l, _e):
        result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)

        self.assertEqual(result["answer"], "Retry [E1].")
        self.assertFalse(result["answer_validated"])
        self.assertTrue(result["review_required"])
        self.assertEqual(result["confidence"], UNVALIDATED_ANSWER_MAX_CONFIDENCE)
        self.assertIn("retry also failed", result["rejection_reason"])

    @patch("helpdesk.services.llm_generator._validate_generated_answer")
    @patch("helpdesk.services.llm_generator._generate_answer_text", return_value="A dataset is a collection of data [E1].")
    def test_a_validated_answer_is_unchanged(self, _gen, _val, _lang, _l, _e):
        result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)

        self.assertTrue(result["answer_validated"])
        self.assertFalse(result["review_required"])
        self.assertEqual(result["confidence"], 0.93)


@override_settings(**SETTINGS)
@patch("helpdesk.services.llm_generator._validate_grounded_example_output")
@patch("helpdesk.services.llm_generator._validate_answer_language")
@patch("helpdesk.services.llm_generator.question_language", return_value="English")
class StreamingTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator._validate_generated_answer", side_effect=LLMGenerationError("no specific content"))
    @patch("helpdesk.services.llm_generator._stream_request_chat_completion", side_effect=[iter(["First [E1]."]), iter(["Retry [E1]."])])
    def test_a_twice_rejected_stream_answer_is_served_but_marked(self, _stream, _val, _lang, _l, _e):
        done = list(stream_answer_llm(question=QUESTION, chunks=CHUNKS))[-1]

        self.assertEqual(done[0], "done")
        self.assertEqual(done[1]["answer"], "Retry [E1].")
        self.assertFalse(done[1]["answer_validated"])
        self.assertTrue(done[1]["review_required"])
        self.assertEqual(done[1]["confidence"], UNVALIDATED_ANSWER_MAX_CONFIDENCE)

    @patch("helpdesk.services.llm_generator._validate_generated_answer")
    @patch("helpdesk.services.llm_generator._stream_request_chat_completion", return_value=iter(["A dataset is a collection [E1]."]))
    def test_a_validated_stream_answer_is_unchanged(self, _stream, _val, _lang, _l, _e):
        done = list(stream_answer_llm(question=QUESTION, chunks=CHUNKS))[-1]

        self.assertTrue(done[1]["answer_validated"])
        self.assertFalse(done[1]["review_required"])
        self.assertEqual(done[1]["confidence"], 0.93)
