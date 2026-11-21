"""Answer language: the prompt names the question's language, and an answer in another language is retried.

Claude Haiku 5.5 wrote 7 of 147 English benchmark answers in German, Dutch or French, the language of the
OpRa evidence (2026-11-04). The language check only looked at non-English questions, and its own
`except Exception` swallowed the rejection it raised, so nothing caught them.
"""

from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services.llm_generator import (
    LLMGenerationError,
    _build_messages,
    _validate_answer_language,
    generate_answer_llm,
)

GERMAN = (
    "Die Evidenz definiert PlannedFleetDimensions als Implementierung eines LOGGABLE OBJECT zur Aufzeichnung "
    "von Informationen über die geplante Flottengröße [E1]. Das Rahmenwerk beschreibt außerdem die Struktur."
)
ENGLISH = "A ScheduledStopPoint is a point where passengers can board or alight from vehicles [E1]."
CHUNKS = [
    {
        "repositoryUrl": "https://github.com/TransmodelEcosystem/OpRa",
        "commitSha": "abc",
        "sourcePath": "docs/fleet.md",
        "chunkId": "chunk-1",
        "text": "PlannedFleetDimensions records planned fleet dimensions per operator.",
        "score": 0.9,
    }
]


class LanguageCheckTests(SimpleTestCase):
    def test_a_german_answer_to_an_english_question_is_rejected(self):
        with self.assertRaisesRegex(LLMGenerationError, "Answer language is German, but the question is in English"):
            _validate_answer_language(GERMAN, "What OpRa data reports planned fleet dimensions?", "English")

    def test_an_english_answer_to_a_german_question_is_rejected(self):
        with self.assertRaisesRegex(LLMGenerationError, "question is in German"):
            _validate_answer_language(ENGLISH, "Was ist ein ScheduledStopPoint?", "German")

    def test_matching_or_unknown_languages_pass(self):
        _validate_answer_language(ENGLISH, "What is a ScheduledStopPoint?", "English")
        _validate_answer_language(ENGLISH, "What is a ScheduledStopPoint?", "en")
        _validate_answer_language(GERMAN, "Was ist ein ScheduledStopPoint?", "German")
        _validate_answer_language(ENGLISH, "SIRI?", None)

    @patch("helpdesk.services.question_preprocessor.detect_question_language", side_effect=RuntimeError("detector broke"))
    def test_a_detector_failure_is_logged_not_raised(self, _detect):
        _validate_answer_language(GERMAN, "What is it?", "English")


class PromptTests(SimpleTestCase):
    def test_an_english_question_gets_an_explicit_english_instruction(self):
        messages = _build_messages(question="What OpRa data reports planned fleet dimensions?", chunks=CHUNKS, detected_language="English")
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        self.assertIn("Respond in English, even when evidence blocks are in another language.", system)

    def test_an_unknown_language_keeps_the_generic_instruction(self):
        messages = _build_messages(question="SIRI?", chunks=CHUNKS, detected_language=None)
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        self.assertIn("Detect the language of the question and respond in that same language.", system)


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="openai-compatible", LLM_API_BASE_URL="https://llm.example.test")
class NonStreamingPathTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator._validate_grounded_example_output")
    @patch("helpdesk.services.llm_generator._validate_generated_answer")
    @patch("helpdesk.services.llm_generator.question_language", return_value="English")
    @patch("helpdesk.services.llm_generator._generate_answer_text")
    def test_a_wrong_language_answer_is_retried_with_the_language_named(self, generate_mock, _lang, _validate, _example):
        generate_mock.side_effect = [GERMAN, "PlannedFleetDimensions records planned fleet dimensions per operator [E1]."]

        result = generate_answer_llm(question="What OpRa data reports planned fleet dimensions?", chunks=CHUNKS, scope=["OpRa"])

        self.assertEqual(generate_mock.call_count, 2)
        retry_messages = generate_mock.call_args_list[1].kwargs["messages"]
        feedback = retry_messages[-1]["content"]
        self.assertIn("Answer language is German, but the question is in English", feedback)
        self.assertIn("CRITICAL LANGUAGE REQUIREMENT", feedback)
        self.assertTrue(result["answer"].startswith("PlannedFleetDimensions records"))


class QuestionDetectionTests(SimpleTestCase):
    """English questions that langdetect reads as another language once schema identifiers are stripped."""

    def test_english_fragments_that_langdetect_misreads_are_english(self):
        from helpdesk.services.question_preprocessor import detect_question_language

        for question in (
            "How do I exchange delay event data between systems using OpRa?",  # -> Dutch
            "What does a ResponseLateDatedVehicleJourneys OpRa message look like?",  # -> Afrikaans
            "How does CapacitySpecification work in OpRa schema?",  # -> Dutch
            "Does NeTEx support autonomous vehicle journey data modelling?",  # -> French
        ):
            with self.subTest(question=question):
                self.assertEqual(detect_question_language(question), "English")

    def test_non_english_questions_keep_their_language(self):
        from helpdesk.services.question_preprocessor import detect_question_language

        self.assertEqual(detect_question_language("Was ist eine verspätete Reise in OpRa und wie wird sie modelliert?"), "German")
        self.assertEqual(detect_question_language("Kaj je zamudena pot v OpRa in kako je modelirana?"), "Slovenian")
        self.assertIsNone(detect_question_language("Wie verwendet SIRI NeTEx?"))


class ShortQuestionLanguageTests(SimpleTestCase):
    """question_language(): a short non-English detection is confirmed by the LLM classifier."""

    CLASSIFIER = "helpdesk.services.llm_generator._classify_question_language_with_llm"

    def test_a_short_slovenian_question_langdetect_reads_as_italian_gets_the_classifier_language(self):
        # Prod 2026-11-05: langdetect said Italian at 0.99999 and the answer came back in Italian.
        from helpdesk.services.llm_generator import question_language
        from helpdesk.services.question_preprocessor import detect_question_language

        question = "Ali SIRI definira dela na cesti?"
        self.assertEqual(detect_question_language(question), "Italian")
        with patch(self.CLASSIFIER, return_value="Slovenian") as classify:
            self.assertEqual(question_language(question), "Slovenian")
        classify.assert_called_once_with(question)

    def test_a_classifier_failure_keeps_the_detected_language(self):
        from helpdesk.services.llm_generator import question_language

        with patch(self.CLASSIFIER, return_value=None):
            self.assertEqual(question_language("Ali SIRI definira dela na cesti?"), "Italian")

    def test_english_and_long_questions_make_no_classifier_call(self):
        from helpdesk.services.llm_generator import question_language

        with patch(self.CLASSIFIER) as classify:
            self.assertEqual(question_language("How does SIRI define roadworks?"), "English")
            self.assertEqual(question_language("Kaj je zamudena pot v OpRa in kako je modelirana v podatkovnem modelu?"), "Slovenian")
        classify.assert_not_called()
