from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.llm_generator import _build_messages
from helpdesk.services.question_preprocessor import (
    detect_question_language,
    preprocess_question,
)


class DetectQuestionLanguageTests(SimpleTestCase):
    def test_short_english_questions_are_not_misdetected(self):
        # Once identifiers are stripped these leave one to five words, which
        # langdetect used to read as Spanish, French, Italian, Romanian, ...
        # "Does SIRI-PT existe?" is the typo'd question answered in Spanish.
        for question in [
            "Does SIRI-PT existe?",
            "Does SIRI-PT exist?",
            "Describe a TariffZone",
            "EPIP",
            "How do I model a ScheduledStopPoint?",
            "Explain DatedServiceJourney",
            "Generate a ServiceJourney example",
            "Create a Route",
            "Validate my NeTEx file",
            "Tutorial for NeTEx",
        ]:
            with self.subTest(question=question):
                self.assertIn(detect_question_language(question), (None, "English"))

    def test_detection_is_deterministic(self):
        results = {detect_question_language("Describe a TariffZone in detail please") for _ in range(20)}
        self.assertEqual(len(results), 1)

    def test_english_sentences_are_detected(self):
        for question in [
            "What is a stop place?",
            "What are the mandatory attributes of a Line?",
            "Can you give an example of a FareZone?",
        ]:
            with self.subTest(question=question):
                self.assertEqual(detect_question_language(question), "English")

    def test_short_non_english_questions_are_still_detected(self):
        for question, expected in [
            ("Hva er en StopPlace?", "Norwegian"),
            ("Was ist ein StopPlace?", "German"),
            ("Wie modelliere ich eine ServiceJourney?", "German"),
            ("Comment décrire une ServiceJourney en NeTEx ?", "French"),
            ("¿Cómo se modela una ServiceJourney?", "Spanish"),
            ("Kako opišem ServiceJourney v NeTEx?", "Slovenian"),
            ("Wat is een StopPlace?", "Dutch"),
        ]:
            with self.subTest(question=question):
                self.assertEqual(detect_question_language(question), expected)


class PreprocessQuestionTests(SimpleTestCase):
    def test_short_question_is_not_spellchecked_with_wrong_dictionary(self):
        # Previously: Spanish dictionary turned "existe" into "este", and the
        # French dictionary turned "exist" into "existe".
        self.assertEqual(preprocess_question("Does SIRI-PT existe?", "English"), "Does SIRI-PT existe?")
        self.assertEqual(preprocess_question("Does SIRI-PT exist?", "English"), "Does SIRI-PT exist?")

    def test_space_before_question_mark_does_not_crash(self):
        # A French typographic habit (space before "?") carried into an English
        # question isolates "?" as its own token; stripped of punctuation it's
        # the empty string, which used to crash the spellchecker correction path
        # with an IndexError on clean_word[0] (HTTP 500 in production).
        question = "What is the relation between a line and a journey ?"
        self.assertEqual(preprocess_question(question, "English"), question)


class PromptLanguageTests(SimpleTestCase):
    def _prompt_text(self, question: str, language: str) -> str:
        messages = _build_messages(question=question, chunks=[], language=language)
        return "\n".join(message["content"] for message in messages)

    def test_short_question_ignores_browser_locale(self):
        for question in ["Does SIRI-PT existe?", "Does SIRI-ST existe?"]:
            with self.subTest(question=question):
                text = self._prompt_text(question, language="Spanish")
                self.assertNotIn("Respond in Spanish", text)
                self.assertNotIn("RESPOND IN: None", text)
                self.assertIn("RESPOND IN: English (detect question language)", text)
                self.assertIn("Detect the language of the question and respond in that same language", text)

    def test_detected_non_english_question_gets_explicit_language(self):
        text = self._prompt_text("Wie modelliere ich eine ServiceJourney?", language="English")
        self.assertIn("Respond in German", text)
