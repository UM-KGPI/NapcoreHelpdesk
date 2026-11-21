"""A question not in English is answered and checked in English; the checked answer is rendered last.

Plan docs/plans/2026-11-21-answer-in-english-translate-last.md, step 1. The model is mocked in every test.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import anthropic_chat, llm_generator as g, request_timing

QUESTION = "Kako SIRI opisuje zamude?"
ENGLISH_QUESTION = "How does SIRI describe delays?"
CHUNKS = [
    {
        "repositoryUrl": "https://github.com/SIRI-CEN/SIRI",
        "commitSha": "abc",
        "sourcePath": "README.md",
        "chunkId": "chunk-1",
        "text": "SIRI-ET (Estimated Timetable) reports the Delay of a DatedVehicleJourney in real time.",
        "score": 0.9,
    }
]
DRAFT = "SIRI reports the `Delay` of a `DatedVehicleJourney` in the Estimated Timetable service (SIRI-ET) [E1]."
RENDERING = "SIRI poroča `Delay` za `DatedVehicleJourney` v storitvi ocenjenega voznega reda (SIRI-ET) [E1]."


def _reply(content: str) -> dict:
    return {"choices": [{"message": {"content": content}, "finish_reason": "end_turn"}]}


def _translation(language: str, text: str = ENGLISH_QUESTION) -> dict:
    return _reply(json.dumps({"evidence": "kako, opisuje", "language": language, "text": text}))


@override_settings(
    LLM_ENABLED=True, LLM_API_BASE_URL="https://llm.example.test", SEARCH_TRANSLATION_ENABLED=True,
    ANSWER_TRANSLATE_LAST_ENABLED=True,
)
class LanguageNamedOnceTests(SimpleTestCase):
    def setUp(self):
        g._CONFIRMED_ENGLISH.clear()
        request_timing.start()

    def tearDown(self):
        # A question found English is remembered in the process; other tests must not see it.
        g._CONFIRMED_ENGLISH.clear()

    @patch("helpdesk.services.llm_generator._classify_question_language_with_llm")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_short_question_gets_its_language_from_the_translation_call(self, chat, classify):
        chat.return_value = _translation("Slovenian")
        # langdetect reads this Slovenian question as Croatian; the call's name is used below eight words.
        self.assertEqual(g.english_search_query(QUESTION), ENGLISH_QUESTION)
        self.assertEqual(chat.call_count, 1)
        classify.assert_not_called()
        key = g._language_key(QUESTION)
        self.assertEqual(request_timing.noted(("question_language", key)), "Slovenian")
        self.assertEqual(request_timing.noted(("english_question", key)), ENGLISH_QUESTION)
        self.assertEqual(g._answer_languages(QUESTION), (ENGLISH_QUESTION, "English", "Slovenian"))
        self.assertEqual(chat.call_count, 1)

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_long_detection_is_kept(self, chat):
        question = "Kateri elementi v NeTEx opisujejo dostopnost postajališča za osebe na invalidskem vozičku?"
        chat.return_value = _translation("Croatian", "Which NeTEx elements describe step-free access?")
        language, english = g._language_and_english_form(question)
        self.assertEqual(language, "Slovenian")
        self.assertEqual(english, "Which NeTEx elements describe step-free access?")

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_an_english_question_makes_no_call(self, chat):
        self.assertIsNone(g.english_search_query("How is a stop place described in NeTEx?"))
        self.assertEqual(g._answer_languages("How is a stop place described in NeTEx?")[1:], ("English", None))
        chat.assert_not_called()

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_the_call_naming_english_makes_the_question_english(self, chat):
        question = "Wie verwendet SIRI NeTEx?"
        chat.return_value = _translation("English", question)
        self.assertIsNone(g.english_search_query(question))
        self.assertEqual(g._answer_languages(question), (question, "English", None))
        self.assertEqual(chat.call_count, 1)

    @patch("helpdesk.services.llm_generator._request_chat_completion", side_effect=OSError("down"))
    def test_a_failed_call_keeps_the_detection_and_the_question(self, chat):
        self.assertIsNone(g.english_search_query(QUESTION))
        self.assertEqual(g._answer_languages(QUESTION), (QUESTION, "Croatian", None))
        self.assertEqual(chat.call_count, 1)  # the answer path does not ask again

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_an_unknown_name_is_not_used_and_not_asked_again(self, chat):
        chat.return_value = _translation("Klingon", "What is SIRI?")
        self.assertEqual(g.english_search_query("Kaj je SIRI?"), "What is SIRI?")
        self.assertEqual(g._answer_languages("Kaj je SIRI?"), ("Kaj je SIRI?", None, None))
        self.assertEqual(chat.call_count, 1)

    def test_the_prompt_lists_the_detector_names(self):
        self.assertIn("Slovenian", g.TRANSLATION_AND_LANGUAGE_PROMPT)
        self.assertIn('"evidence"', g.TRANSLATION_AND_LANGUAGE_PROMPT)

    @override_settings(ANSWER_TRANSLATE_LAST_ENABLED=False)
    @patch("helpdesk.services.llm_generator.question_language", return_value="Slovenian")
    def test_switched_off_the_answer_is_in_the_question_language(self, _language):
        self.assertEqual(g._answer_languages(QUESTION), (QUESTION, "Slovenian", None))


class RenderingCheckTests(SimpleTestCase):
    def _problem(self, english, rendered, language="Slovenian"):
        return g._rendering_problem(english, rendered, language)

    def test_a_faithful_rendering_passes(self):
        self.assertIsNone(self._problem(DRAFT, RENDERING))

    def test_a_dropped_or_added_citation_mark_is_refused(self):
        self.assertIn("citation marks", self._problem(DRAFT, RENDERING.replace(" [E1]", "")))
        self.assertIn("citation marks", self._problem(DRAFT, RENDERING + " To velja tudi za SIRI-SX [E2]."))

    def test_a_translated_code_span_or_name_is_refused(self):
        self.assertIn("'Delay'", self._problem(DRAFT, RENDERING.replace("`Delay`", "`Zamuda`")))
        self.assertIn("SIRI-ET", self._problem(DRAFT, RENDERING.replace("SIRI-ET", "SIRI ET")))

    def test_a_new_name_is_refused(self):
        self.assertIn("ServiceJourney", self._problem(DRAFT, RENDERING.replace("storitvi", "storitvi ServiceJourney")))

    def test_a_changed_number_is_refused(self):
        english = "Article 4(1)(b) of Delegated Regulation (EU) 2017/1926 lists them [E1]."
        rendered = "Člen 4(2)(b) Delegirane uredbe (EU) 2017/1926 jih navaja [E1]."
        self.assertIn("numbers differ", self._problem(english, rendered))

    def test_a_quote_must_stay_verbatim(self):
        english = 'The regulation says "static travel data" [E1].'
        self.assertIsNone(self._problem(english, 'Uredba navaja „static travel data“ [E1].'))
        self.assertIn("quote", self._problem(english, 'Uredba navaja „statični potovalni podatki“ [E1].'))

    def test_a_rendering_in_another_language_is_refused(self):
        english = (
            "The `StopPlace` element describes a place where passengers board and alight, with its quays and "
            "entrances [E1]. Each quay is a `Quay` inside the stop place [E1]."
        )
        german = (
            "Das Element `StopPlace` beschreibt einen Ort, an dem Fahrgäste ein- und aussteigen, mit seinen "
            "Bahnsteigen und Eingängen [E1]. Jeder Bahnsteig ist ein `Quay` innerhalb der Haltestelle [E1]."
        )
        self.assertIn("Answer language is German", self._problem(english, german, "Slovenian"))
        self.assertIsNone(self._problem(english, german, "German"))

    def test_a_much_shorter_rendering_is_refused(self):
        english = DRAFT + " It is sent for every journey whose expected times differ from the plan." * 3
        self.assertIn("length", self._problem(english, RENDERING))

    def test_code_blocks_are_masked_and_put_back(self):
        answer = "An example [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```\n\nThat is all [E1]."
        masked, blocks = g._masked(answer)
        self.assertNotIn("<Delay>", masked)
        self.assertIn("⟦1⟧", masked)
        self.assertEqual(g._unmasked(masked, blocks), answer)
        self.assertIn("placeholder", self._problem(masked, masked.replace("⟦1⟧", "")))

    def test_streamed_text_is_held_back_only_at_an_open_placeholder(self):
        blocks = ["```xml\n<A/>\n```"]
        self.assertEqual(g._emitted("Primer [E1]:\n\n⟦", blocks), ("Primer [E1]:\n\n", "⟦"))
        self.assertEqual(g._emitted("⟦1⟧\n\nKonec", blocks), ("```xml\n<A/>\n```\n\nKonec", ""))


def _streaming(*texts: str):
    """A stand-in for _rendering_text_stream: each call yields the next text in two pieces."""
    texts = list(texts)

    def stream(_messages):
        text = texts.pop(0)
        yield text[: len(text) // 2]
        yield text[len(text) // 2 :]
        return "end_turn"

    return stream


@override_settings(
    LLM_ENABLED=True, LLM_PROVIDER="openai-compatible", LLM_API_BASE_URL="https://llm.example.test",
    LLM_STREAMING=False, SEARCH_TRANSLATION_ENABLED=True, ANSWER_TRANSLATE_LAST_ENABLED=True,
)
@patch("helpdesk.services.llm_generator._validate_grounded_example_output")
@patch("helpdesk.services.llm_generator._validate_generated_answer")
class AnswerPathTests(SimpleTestCase):
    def setUp(self):
        g._CONFIRMED_ENGLISH.clear()
        request_timing.start()
        key = g._language_key(QUESTION)
        request_timing.note(("question_language", key), "Slovenian")
        request_timing.note(("english_question", key), ENGLISH_QUESTION)
        request_timing.note(("translated", key), True)

    def _stream(self):
        return list(g.stream_answer_llm(question=QUESTION, chunks=CHUNKS, scope=["SIRI"]))

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_the_draft_is_english_and_the_rendering_is_streamed(self, chat, validate, _example):
        chat.return_value = _reply(json.dumps({"answer": DRAFT, "citations_used": ["E1"]}))
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(RENDERING)):
            events = self._stream()
        messages = chat.call_args.kwargs["messages"]
        self.assertIn("Respond in English", messages[0]["content"])
        self.assertIn(ENGLISH_QUESTION, messages[1]["content"])
        self.assertNotIn(QUESTION, messages[1]["content"])
        self.assertIs(validate.call_args.kwargs["inflected"], False)
        tokens = "".join(p for kind, p in events if kind == "token")
        done = events[-1][1]
        self.assertEqual(tokens, RENDERING)
        self.assertEqual(done["answer"], RENDERING)
        self.assertEqual(done["rendering"]["served"], "rendering")
        self.assertEqual(done["rendering"]["englishAnswer"], DRAFT)
        self.assertEqual(chat.call_count, 1)

    @patch("helpdesk.services.fixed_text_language.in_question_language", return_value="Prikazano v angleščini.")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_two_refused_renderings_serve_the_english_answer_with_a_note(self, chat, _note, _validate, _example):
        chat.return_value = _reply(json.dumps({"answer": DRAFT, "citations_used": ["E1"]}))
        broken = RENDERING.replace(" [E1]", "")
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(broken, broken)) as render:
            events = self._stream()
        done = events[-1][1]
        self.assertEqual(render.call_count, 2)
        self.assertIn("citation marks", render.call_args_list[1].args[0][0]["content"])
        self.assertEqual(done["answer"], f"{DRAFT}\n\n*Prikazano v angleščini.*")
        self.assertEqual(done["rendering"]["served"], "english")
        self.assertEqual(len(done["rendering"]["problems"]), 2)
        # Only the first attempt was streamed; the done event carries what is served.
        self.assertEqual("".join(p for kind, p in events if kind == "token"), broken)

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_code_block_is_not_sent_to_the_model(self, chat, _validate, _example):
        draft = "An example [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```"
        chat.return_value = _reply(json.dumps({"answer": draft, "citations_used": ["E1"]}))
        sent = []

        def stream(messages):
            sent.append(messages[1]["content"])
            yield "Primer [E1]:\n\n⟦"
            yield "1⟧"
            return "end_turn"

        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=stream):
            events = self._stream()
        self.assertNotIn("<Delay>", sent[0])
        self.assertEqual(events[-1][1]["answer"], "Primer [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```")

    @patch("helpdesk.services.llm_generator._generate_answer_text", return_value=DRAFT)
    def test_the_non_streaming_path_renders_too(self, generate, _validate, _example):
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(RENDERING)):
            result = g.generate_answer_llm(question=QUESTION, chunks=CHUNKS, scope=["SIRI"])
        self.assertEqual(result["answer"], RENDERING)
        self.assertEqual(result["rendering"]["served"], "rendering")
        self.assertIn(ENGLISH_QUESTION, generate.call_args.kwargs["messages"][1]["content"])


@override_settings(
    LLM_ENABLED=True, LLM_PROVIDER="openai-compatible", LLM_API_BASE_URL="https://llm.example.test",
    LLM_STREAMING=False, SEARCH_TRANSLATION_ENABLED=True,
)
@patch("helpdesk.services.llm_generator._validate_grounded_example_output")
@patch("helpdesk.services.llm_generator._validate_generated_answer")
class EnglishQuestionUnchangedTests(SimpleTestCase):
    """An English question: the same prompt and the same model calls with the setting on and off."""

    QUESTION = "How is a stop place described in NeTEx?"

    def _run(self, on: bool):
        request_timing.start()
        with override_settings(ANSWER_TRANSLATE_LAST_ENABLED=on), patch(
            "helpdesk.services.llm_generator._request_chat_completion",
            return_value=_reply(json.dumps({"answer": DRAFT, "citations_used": ["E1"]})),
        ) as chat, patch("helpdesk.services.llm_generator._rendering_text_stream") as render:
            g.english_search_query(self.QUESTION)
            events = list(g.stream_answer_llm(question=self.QUESTION, chunks=CHUNKS, scope=["NeTEx"]))
        render.assert_not_called()
        return [c.kwargs["messages"] for c in chat.call_args_list], events[-1][1]["answer"]

    def test_prompt_and_calls_are_identical(self, _validate, _example):
        self.assertEqual(self._run(True), self._run(False))


class AnthropicStreamTests(SimpleTestCase):
    def test_text_is_yielded_as_written_and_the_stop_reason_returned(self):
        stream = MagicMock()
        stream.__enter__.return_value.text_stream = iter(["Pri", "mer"])
        stream.__enter__.return_value.get_final_message.return_value = SimpleNamespace(stop_reason="end_turn")
        client = MagicMock()
        client.with_options.return_value.messages.stream.return_value = stream
        with patch.object(anthropic_chat, "_client", return_value=client):
            generator = anthropic_chat.stream_text(
                api_key="k", model="claude-haiku-5-5", messages=[{"role": "user", "content": "x"}],
                max_tokens=100, timeout_seconds=5,
            )
            parts = []
            while True:
                try:
                    parts.append(next(generator))
                except StopIteration as done:
                    stop = done.value
                    break
        self.assertEqual(parts, ["Pri", "mer"])
        self.assertEqual(stop, "end_turn")
        params = client.with_options.return_value.messages.stream.call_args.kwargs
        self.assertEqual(params["thinking"], {"type": "disabled"})
