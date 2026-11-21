"""A question not in English is answered and checked in English; the checked answer is rendered last.

Plan docs/plans/2026-11-21-answer-in-english-translate-last.md, step 1. The model is mocked in every test.
"""

from __future__ import annotations

import json
import re
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

    CLASSIFY = "helpdesk.services.llm_generator._classify_question_language_with_llm"

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_short_question_is_named_once_and_the_naming_call_wins(self, chat):
        chat.return_value = _translation("Croatian")
        # langdetect reads this Slovenian question as Croatian, and so may the translation call.
        with patch(self.CLASSIFY, return_value="Slovenian") as classify:
            self.assertEqual(g.english_search_query(QUESTION), ENGLISH_QUESTION)
            self.assertEqual(g._answer_languages(QUESTION), (ENGLISH_QUESTION, "English", "Slovenian"))
            self.assertEqual(g._answer_languages(QUESTION), (ENGLISH_QUESTION, "English", "Slovenian"))
        classify.assert_called_once_with(QUESTION)
        self.assertEqual(chat.call_count, 1)
        key = g._language_key(QUESTION)
        self.assertEqual(request_timing.noted(("question_language", key)), "Slovenian")
        self.assertEqual(request_timing.noted(("english_question", key)), ENGLISH_QUESTION)

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_the_two_calls_run_at_the_same_time(self, chat):
        import threading

        both = threading.Barrier(2, timeout=5)

        def classify(_question):
            both.wait()
            return "Slovenian"

        def translate(**_kwargs):
            both.wait()  # would time out if the naming call ran only after the translation
            return _translation("Croatian")

        chat.side_effect = translate
        with patch(self.CLASSIFY, side_effect=classify):
            self.assertEqual(g._language_and_english_form(QUESTION), ("Slovenian", ENGLISH_QUESTION))

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_no_detected_language_names_first_and_an_english_question_is_not_translated(self, chat):
        with patch(self.CLASSIFY, return_value="English") as classify:
            self.assertIsNone(g.english_search_query("Kaj je SIRI?"))
            self.assertEqual(g._answer_languages("Kaj je SIRI?"), ("Kaj je SIRI?", "English", None))
        classify.assert_called_once()
        chat.assert_not_called()

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_failed_naming_call_takes_the_translation_name(self, chat):
        chat.return_value = _translation("Slovenian")
        with patch(self.CLASSIFY, return_value=None):
            self.assertEqual(g._language_and_english_form(QUESTION), ("Slovenian", ENGLISH_QUESTION))

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_long_detection_is_kept_without_a_naming_call(self, chat):
        question = "Kateri elementi v NeTEx opisujejo dostopnost postajališča za osebe na invalidskem vozičku?"
        chat.return_value = _translation("Croatian", "Which NeTEx elements describe step-free access?")
        with patch(self.CLASSIFY) as classify:
            language, english = g._language_and_english_form(question)
        classify.assert_not_called()
        self.assertEqual(language, "Slovenian")
        self.assertEqual(english, "Which NeTEx elements describe step-free access?")

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_an_english_question_makes_no_call(self, chat):
        with patch(self.CLASSIFY) as classify:
            self.assertIsNone(g.english_search_query("How is a stop place described in NeTEx?"))
            self.assertEqual(g._answer_languages("How is a stop place described in NeTEx?")[1:], ("English", None))
        chat.assert_not_called()
        classify.assert_not_called()

    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_the_naming_call_saying_english_makes_the_question_english(self, chat):
        chat.return_value = _translation("German", "How does SIRI use NeTEx?")
        with patch(self.CLASSIFY, return_value="English"):
            self.assertIsNone(g.english_search_query(QUESTION))
            self.assertEqual(g._answer_languages(QUESTION), (QUESTION, "English", None))

    @patch("helpdesk.services.llm_generator._request_chat_completion", side_effect=OSError("down"))
    def test_a_failed_translation_keeps_the_name_and_the_question(self, chat):
        with patch(self.CLASSIFY, return_value="Slovenian") as classify:
            self.assertIsNone(g.english_search_query(QUESTION))
            self.assertEqual(g._answer_languages(QUESTION), (QUESTION, "Slovenian", None))
        self.assertEqual(chat.call_count, 1)  # the answer path does not ask again
        classify.assert_called_once()

    def test_the_prompt_lists_the_detector_names(self):
        self.assertIn("Slovenian", g.TRANSLATION_AND_LANGUAGE_PROMPT)
        self.assertIn('"evidence"', g.TRANSLATION_AND_LANGUAGE_PROMPT)

    @override_settings(ANSWER_TRANSLATE_LAST_ENABLED=False)
    @patch("helpdesk.services.llm_generator.question_language", return_value="Slovenian")
    def test_switched_off_the_answer_is_in_the_question_language(self, _language):
        self.assertEqual(g._answer_languages(QUESTION), (QUESTION, "Slovenian", None))


def _marks(text: str) -> list[str]:
    return sorted(re.findall(r"\[E\d+\]", text))


TWO_PARAGRAPHS = (
    "SIRI reports the `Delay` of a journey [E1]. It is given in seconds [E1][E2].\n\n"
    "**Services:**\n- Stop Monitoring gives departures [E3].\n- Estimated Timetable gives journeys [E4]."
)
TWO_PARAGRAPHS_SL = [
    "SIRI poroča `Delay` vožnje.",
    "Podana je v sekundah.",
    "**Storitve:**",
    "Stop Monitoring daje odhode.",
    "Estimated Timetable daje vožnje.",
]


def _numbered(lines: list[str]) -> str:
    return "\n".join(f"{i}| {line}" for i, line in enumerate(lines, start=1))


class PiecesTests(SimpleTestCase):
    def test_pieces_carry_their_marks_and_the_model_sees_none(self):
        pieces, tail = g._pieces(TWO_PARAGRAPHS)
        self.assertEqual([p["marks"] for p in pieces], [["[E1]"], ["[E1]", "[E2]"], [], ["[E3]"], ["[E4]"]])
        self.assertFalse(any("[E" in p["text"] for p in pieces))
        self.assertEqual([p["paragraph"] for p in pieces], [0, 0, 1, 1, 1])
        self.assertEqual(tail, "")

    def test_marks_are_put_back_exactly(self):
        pieces, tail = g._pieces(TWO_PARAGRAPHS)
        text, by_paragraph = g._assembled(pieces, tail, dict(enumerate(TWO_PARAGRAPHS_SL, start=1)))
        self.assertFalse(by_paragraph)
        self.assertEqual(_marks(text), _marks(TWO_PARAGRAPHS))
        self.assertEqual(
            text,
            "SIRI poroča `Delay` vožnje [E1]. Podana je v sekundah [E1] [E2].\n\n"
            "**Storitve:**\n- Stop Monitoring daje odhode [E3].\n- Estimated Timetable daje vožnje [E4].",
        )

    def test_unmatched_pieces_put_the_marks_at_the_end_of_the_paragraph(self):
        pieces, tail = g._pieces(TWO_PARAGRAPHS)
        merged = {1: "SIRI poroča `Delay` vožnje, podano v sekundah.", 3: "**Storitve:**", 4: "Stop Monitoring.", 5: "ET."}
        text, by_paragraph = g._assembled(pieces, tail, merged)
        self.assertTrue(by_paragraph)
        self.assertEqual(_marks(text), _marks(TWO_PARAGRAPHS))
        self.assertTrue(text.startswith("SIRI poroča `Delay` vožnje, podano v sekundah [E1] [E1] [E2]."))

    def test_a_mark_in_the_middle_of_a_sentence_goes_to_its_end(self):
        english = "It covers Stop Monitoring [E1]; and Vehicle Monitoring [E2]."
        pieces, _ = g._pieces(english)
        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0]["moved"], 1)
        text, _ = g._assembled(pieces, "", {1: "Pokriva Stop Monitoring in Vehicle Monitoring."})
        self.assertEqual(text, "Pokriva Stop Monitoring in Vehicle Monitoring [E1] [E2].")

    def test_abbreviations_do_not_cut_a_sentence(self):
        pieces, _ = g._pieces("A stop (e.g. a quay) is a place [E1]. The next one [E2].")
        self.assertEqual([p["marks"] for p in pieces], [["[E1]"], ["[E2]"]])

    def test_code_blocks_stay_out(self):
        answer = "An example [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```\n\nThat is all [E2]."
        masked, blocks = g._masked(answer)
        pieces, tail = g._pieces(masked)
        self.assertEqual([p["text"] for p in pieces], ["An example:", "That is all."])
        text, _ = g._assembled(pieces, tail, {1: "Primer:", 2: "To je vse."})
        self.assertEqual(g._unmasked(text, blocks), "Primer [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```\n\nTo je vse [E2].")

    def test_the_monitor_lists_what_the_translation_lacks(self):
        english = 'See `Delay` and "static travel data" at https://example.org/a, 15 s [E1].'
        monitor = g._rendering_monitor(english, "Glej `Zamuda` in statični podatki na https://example.org/a, 15 s [E1].")
        self.assertEqual(monitor["missingCodeSpans"], ["Delay"])
        self.assertEqual(monitor["missingQuotes"], ["static travel data"])
        self.assertEqual(monitor["missingNumbers"], [])
        self.assertEqual(monitor["missingLinks"], [])


def _streaming(*texts: str):
    """A stand-in for _rendering_text_stream: each call yields the next text line by line."""
    texts = list(texts)

    def stream(_messages):
        text = texts.pop(0)
        for line in text.splitlines(keepends=True):
            yield line
        return "end_turn"

    return stream


SL = _numbered(TWO_PARAGRAPHS_SL)
SERVED = (
    "SIRI poroča `Delay` vožnje [E1]. Podana je v sekundah [E1] [E2].\n\n"
    "**Storitve:**\n- Stop Monitoring daje odhode [E3].\n- Estimated Timetable daje vožnje [E4]."
)
GERMAN = _numbered([
    "SIRI meldet die `Delay` einer Fahrt, die vom Fahrplan abweicht.",
    "Sie wird in Sekunden angegeben, und frühe Zeiten sind negativ.",
    "**Dienste:**",
    "Stop Monitoring liefert die Abfahrten an einer Haltestelle.",
    "Estimated Timetable liefert die erwarteten Fahrten.",
])


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

    def _stream(self, draft=TWO_PARAGRAPHS):
        with patch(
            "helpdesk.services.llm_generator._request_chat_completion",
            return_value=_reply(json.dumps({"answer": draft, "citations_used": ["E1"]})),
        ) as chat:
            events = list(g.stream_answer_llm(question=QUESTION, chunks=CHUNKS, scope=["SIRI"]))
        return chat, events

    def test_the_draft_is_english_and_the_translation_is_streamed_with_its_marks(self, validate, _example):
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(SL)) as render:
            chat, events = self._stream()
        messages = chat.call_args.kwargs["messages"]
        self.assertIn("Respond in English", messages[0]["content"])
        self.assertIn(ENGLISH_QUESTION, messages[1]["content"])
        self.assertIs(validate.call_args.kwargs["inflected"], False)
        sent = render.call_args.args[0][1]["content"]
        self.assertNotIn("[E", sent)
        self.assertTrue(sent.startswith("1| SIRI reports"))
        done = events[-1][1]
        self.assertEqual(done["answer"], SERVED)
        self.assertEqual("".join(p for kind, p in events if kind == "token"), SERVED)
        self.assertEqual(done["rendering"]["served"], "rendering")
        self.assertFalse(done["rendering"]["placedByParagraph"])
        self.assertEqual(done["rendering"]["englishAnswer"], TWO_PARAGRAPHS)

    def test_mismatched_pieces_are_translated_once_more_then_placed_by_paragraph(self, _validate, _example):
        short = _numbered(TWO_PARAGRAPHS_SL[:2] + ["**Storitve:** Stop Monitoring daje odhode in ET vožnje."])
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(short, short)) as render:
            _chat, events = self._stream()
        done = events[-1][1]
        self.assertEqual(render.call_count, 2)
        self.assertIn("lines 1 to 5", render.call_args_list[1].args[0][0]["content"])
        self.assertTrue(done["rendering"]["placedByParagraph"])
        self.assertEqual(_marks(done["answer"]), _marks(TWO_PARAGRAPHS))

    def test_a_matching_second_attempt_is_placed_by_piece(self, _validate, _example):
        short = _numbered(TWO_PARAGRAPHS_SL[:4])
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(short, SL)):
            _chat, events = self._stream()
        self.assertEqual(events[-1][1]["answer"], SERVED)
        self.assertFalse(events[-1][1]["rendering"]["placedByParagraph"])

    @patch("helpdesk.services.fixed_text_language.in_question_language", return_value="Prikazano v angleščini.")
    def test_a_wrong_language_twice_serves_the_english_answer_with_a_note(self, _note, _validate, _example):
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(GERMAN, GERMAN)) as render:
            _chat, events = self._stream()
        done = events[-1][1]
        self.assertEqual(render.call_count, 2)
        self.assertEqual(done["answer"], f"{TWO_PARAGRAPHS}\n\n*Prikazano v angleščini.*")
        self.assertEqual(done["rendering"]["served"], "english")
        self.assertIn("German", done["rendering"]["problems"][0])

    def test_a_wrong_language_once_is_translated_again(self, _validate, _example):
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(GERMAN, SL)):
            _chat, events = self._stream()
        self.assertEqual(events[-1][1]["answer"], SERVED)

    def test_nothing_else_refuses_a_translation(self, _validate, _example):
        # A translated code span is only recorded for monitoring.
        changed = SL.replace("`Delay`", "`Zamuda`")
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(changed)) as render:
            _chat, events = self._stream()
        done = events[-1][1]
        self.assertEqual(render.call_count, 1)
        self.assertEqual(done["rendering"]["served"], "rendering")
        self.assertEqual(done["rendering"]["monitor"]["missingCodeSpans"], ["Delay"])

    def test_a_code_block_is_not_sent_to_the_model(self, _validate, _example):
        draft = "An example [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```"
        sent = []

        def stream(messages):
            sent.append(messages[1]["content"])
            yield "1| Primer:"
            return "end_turn"

        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=stream):
            _chat, events = self._stream(draft)
        self.assertNotIn("<Delay>", sent[0])
        self.assertEqual(events[-1][1]["answer"], "Primer [E1]:\n\n```xml\n<Delay>PT5M</Delay>\n```")
        self.assertEqual("".join(p for kind, p in events if kind == "token"), events[-1][1]["answer"])

    @patch("helpdesk.services.llm_generator._generate_answer_text", return_value=TWO_PARAGRAPHS)
    def test_the_non_streaming_path_renders_too(self, generate, _validate, _example):
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=_streaming(SL)):
            result = g.generate_answer_llm(question=QUESTION, chunks=CHUNKS, scope=["SIRI"])
        self.assertEqual(result["answer"], SERVED)
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
