"""The answer check by sentence (plan 2026-11-21, step 2): every cited sentence gets a verdict, a failed sentence is
removed with its marks, and the answer is written again only when too little remains. The model is mocked."""

from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services.llm_generator import (
    PARTLY_CONFIRMED_NOTE,
    _sentence_spans,
    _sentence_verdicts,
    _too_little_remains,
    _without_sentences,
    generate_answer_llm,
    stream_answer_llm,
)
from helpdesk.services.semantic_abstention import INSUFFICIENT_EVIDENCE_MESSAGE

CHUNKS = [
    {
        "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
        "commitSha": "abc",
        "chunkId": "chunk-stop",
        "sourcePath": "xsd/netex_stopPlace_version.xsd",
        "docType": "schema",
        "text": "Schema declaration: element StopPlace. A StopPlace contains Quay elements.",
        "score": 0.9,
    },
    {
        "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
        "commitSha": "abc",
        "chunkId": "chunk-line",
        "sourcePath": "xsd/netex_line_version.xsd",
        "docType": "schema",
        "text": "Schema declaration: element Line. A Line has a PublicCode.",
        "score": 0.8,
    },
]
GOOD_1 = "A `StopPlace` contains `Quay` elements [E1]."
GOOD_2 = "A `Line` has a `PublicCode` [E2]."
BAD = "A `Platform` is the place where trains stop [E1]."
SETTINGS = dict(
    LLM_ENABLED=True,
    LLM_PROVIDER="openai-compatible",
    LLM_API_BASE_URL="https://llm.example.test",
    LLM_STREAMING=True,
    ANSWER_CHECK_BY_SENTENCE_ENABLED=True,
)
QUESTION = "How do I describe a stop place in NeTEx?"


class VerdictTests(SimpleTestCase):
    def test_a_sentence_is_not_cut_inside_a_parenthesis(self):
        answer = "A `StopPlace` (e.g. a station. It has quays) holds `Quay` elements [E1]. Next one [E2]."
        sentences = [answer[s:e] for s, e in _sentence_spans(answer)]
        self.assertEqual(sentences, ["A `StopPlace` (e.g. a station. It has quays) holds `Quay` elements [E1].", "Next one [E2]."])

    def test_an_unclosed_parenthesis_ends_with_its_line(self):
        answer = "One (open. Two [E1].\nThree [E2]. Four [E1]."
        self.assertEqual(len(_sentence_spans(answer)), 3)

    def test_every_cited_sentence_gets_a_verdict_and_the_same_draft_the_same_result(self):
        answer = f"{GOOD_1} {BAD} {GOOD_2}"
        first = _sentence_verdicts(answer, CHUNKS)
        self.assertEqual([bool(v["reason"]) for v in first], [False, True, False])
        self.assertEqual(first[1]["passages"], ["chunk-stop"])
        self.assertEqual(first, _sentence_verdicts(answer, CHUNKS))

    def test_a_removed_sentence_takes_its_marks_and_a_mark_standing_alone_after_it(self):
        answer = f"{GOOD_1} {BAD} [E2]. {GOOD_2}"
        kept = _without_sentences(answer, _sentence_verdicts(answer, CHUNKS))
        self.assertNotIn("Platform", kept)
        self.assertEqual(kept, f"{GOOD_1} {GOOD_2}")

    def test_an_empty_list_item_and_a_heading_without_content_are_removed(self):
        answer = f"## Stops\n\n- {GOOD_1}\n\n## Platforms\n\n- {BAD}\n\n## Lines\n\n{GOOD_2}"
        kept = _without_sentences(answer, _sentence_verdicts(answer, CHUNKS))
        self.assertEqual(kept, f"## Stops\n\n- {GOOD_1}\n\n## Lines\n\n{GOOD_2}")

    def test_a_label_whose_items_were_all_removed_goes(self):
        answer = f"{GOOD_1}\n\n**Platforms:**\n- {BAD}\n\n{GOOD_2}"
        kept = _without_sentences(answer, _sentence_verdicts(answer, CHUNKS))
        self.assertEqual(kept, f"{GOOD_1}\n\n{GOOD_2}")

    def test_fenced_code_is_never_cut(self):
        answer = f"{GOOD_1}\n\n```xml\n<StopPlace/>\n```\n\n{GOOD_2}"
        verdicts = [dict(v, reason="x") for v in _sentence_verdicts(answer, CHUNKS)]
        self.assertIn("```xml\n<StopPlace/>\n```", _without_sentences(answer, verdicts))

    def test_too_little_remains_below_half_or_with_no_cited_sentence(self):
        def verdicts(*failed):
            return [{"hasWords": True, "reason": "x" if f else None} for f in failed]

        self.assertFalse(_too_little_remains(verdicts(False, True)))  # one of two kept
        self.assertTrue(_too_little_remains(verdicts(True, True, False)))  # one of three
        self.assertTrue(_too_little_remains(verdicts(True)))
        self.assertFalse(_too_little_remains([]))  # no cited sentence at all: nothing was removed


@override_settings(**SETTINGS)
@patch("helpdesk.services.llm_generator._validate_answer_language")
@patch("helpdesk.services.llm_generator._answer_languages", return_value=(QUESTION, "English", None))
class NonStreamingTests(SimpleTestCase):
    def test_a_failed_sentence_is_removed_and_the_rest_served_without_a_rewrite(self, _lang, _check):
        with patch("helpdesk.services.llm_generator._generate_answer_text", return_value=f"{GOOD_1} {BAD} {GOOD_2}") as gen:
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)
        self.assertEqual(gen.call_count, 1)
        self.assertEqual(result["answer"], f"{GOOD_1} {GOOD_2}")
        self.assertTrue(result["answer_validated"])
        self.assertIsNone(result["rejection_reason"])
        removed = result["sentence_check"]["drafts"][0]["removed"]
        self.assertEqual([r["passages"] for r in removed], [["chunk-stop"]])
        self.assertNotIn(PARTLY_CONFIRMED_NOTE, result["answer"])

    def test_too_little_left_means_one_rewrite_with_the_removed_sentences_as_feedback(self, _lang, _check):
        drafts = [f"{BAD} A `Bay` is a part of it [E2]. {GOOD_2}", f"{GOOD_1} {GOOD_2}"]
        with patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=drafts) as gen:
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)
        self.assertEqual(gen.call_count, 2)
        feedback = gen.call_args_list[1].kwargs["messages"][-1]["content"]
        self.assertIn("Platform", feedback)
        self.assertIn("Removed sentences", feedback)
        self.assertEqual(result["answer"], f"{GOOD_1} {GOOD_2}")
        self.assertTrue(result["answer_validated"])
        self.assertNotIn(PARTLY_CONFIRMED_NOTE, result["answer"])

    def test_after_the_rewrite_the_confirmed_sentences_are_served_with_a_note(self, _lang, _check):
        drafts = [f"{BAD} A `Bay` is a part of it [E2]. {GOOD_2}", f"{GOOD_1} {BAD}"]
        with patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=drafts):
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)
        self.assertTrue(result["answer"].startswith(GOOD_1))
        self.assertNotIn("Platform", result["answer"])
        self.assertIn(PARTLY_CONFIRMED_NOTE, result["answer"])
        self.assertTrue(result["answer_validated"])
        self.assertTrue(result["review_required"])

    def test_no_confirmed_sentence_in_either_draft_is_the_refusal(self, _lang, _check):
        with patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=[BAD, BAD]):
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)
        self.assertEqual(result["answer"], INSUFFICIENT_EVIDENCE_MESSAGE)
        self.assertFalse(result["evidence_answers_question"])
        self.assertEqual(result["sentence_check"]["outcome"], "refused")

    def test_the_first_drafts_confirmed_sentences_stand_when_the_rewrite_keeps_none(self, _lang, _check):
        drafts = [f"{BAD} A `Bay` is a part of it [E2]. {GOOD_2}", BAD]
        with patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=drafts):
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)
        self.assertTrue(result["answer"].startswith(GOOD_2))
        self.assertIn(PARTLY_CONFIRMED_NOTE, result["answer"])

    def test_next_to_an_example_the_refusal_is_no_text(self, _lang, _check):
        with patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=[BAD, BAD]):
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS, example_elements=["StopPlace"])
        self.assertEqual(result["answer"], "")

    def test_a_question_not_in_english_gets_the_checked_text_translated_and_the_note_in_its_language(self, _lang, _check):
        def rendered(answer, language, question, english_question, stream):
            self.assertNotIn("Platform", answer)  # removal happens on the English draft, before the translation
            return f"PREVOD: {answer}", {"served": "rendering"}
            yield  # a generator, as _rendered_answer is

        drafts = [f"{BAD} A `Bay` is a part of it [E2]. {GOOD_2}", f"{GOOD_1} {BAD}"]
        with (
            patch("helpdesk.services.llm_generator._answer_languages", return_value=(QUESTION, "English", "Slovenian")),
            patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=drafts),
            patch("helpdesk.services.llm_generator._rendered_answer", side_effect=rendered),
            patch("helpdesk.services.fixed_text_language.in_question_language", return_value="OPOMBA") as fixed,
        ):
            result = generate_answer_llm(question="Kako opišem postajo?", chunks=CHUNKS)
        self.assertEqual(result["answer"], f"PREVOD: {GOOD_1}\n\n*OPOMBA*")
        self.assertEqual(fixed.call_args.args[0], PARTLY_CONFIRMED_NOTE)
        self.assertEqual(fixed.call_args.kwargs["english_question"], QUESTION)

    @override_settings(ANSWER_CHECK_BY_SENTENCE_ENABLED=False)
    def test_the_setting_off_rejects_the_whole_draft_as_before(self, _lang, _check):
        with patch("helpdesk.services.llm_generator._generate_answer_text", side_effect=[f"{GOOD_1} {BAD}", f"{GOOD_1} {BAD}"]) as gen:
            result = generate_answer_llm(question=QUESTION, chunks=CHUNKS)
        self.assertEqual(gen.call_count, 2)
        self.assertFalse(result["answer_validated"])
        self.assertIn("Platform", result["answer"])
        self.assertIsNone(result["sentence_check"])


@override_settings(**SETTINGS)
@patch("helpdesk.services.llm_generator._validate_answer_language")
@patch("helpdesk.services.llm_generator._answer_languages", return_value=(QUESTION, "English", None))
class StreamingTests(SimpleTestCase):
    def test_the_stream_serves_what_passed_without_a_retry_status(self, _lang, _check):
        with patch(
            "helpdesk.services.llm_generator._stream_request_chat_completion", return_value=iter([f"{GOOD_1} {BAD}"])
        ):
            events = list(stream_answer_llm(question=QUESTION, chunks=CHUNKS))
        self.assertNotIn(("status", "retrying"), events)
        self.assertEqual("".join(e[1] for e in events if e[0] == "token"), GOOD_1)
        self.assertEqual(events[-1][1]["answer"], GOOD_1)
        self.assertTrue(events[-1][1]["answer_validated"])

    def test_the_stream_rewrites_once_and_sends_the_note_last(self, _lang, _check):
        drafts = [iter([BAD]), iter([f"{GOOD_1} {BAD}"])]
        with patch("helpdesk.services.llm_generator._stream_request_chat_completion", side_effect=drafts):
            events = list(stream_answer_llm(question=QUESTION, chunks=CHUNKS))
        self.assertIn(("status", "retrying"), events)
        tokens = [e[1] for e in events if e[0] == "token"]
        self.assertIn(PARTLY_CONFIRMED_NOTE, tokens[-1])
        done = events[-1][1]
        self.assertEqual(done["answer"], "".join(tokens))
        self.assertNotIn("Platform", done["answer"])
        self.assertEqual(len(done["sentence_check"]["drafts"]), 2)

    def test_the_stream_refusal(self, _lang, _check):
        with patch("helpdesk.services.llm_generator._stream_request_chat_completion", side_effect=[iter([BAD]), iter([BAD])]):
            events = list(stream_answer_llm(question=QUESTION, chunks=CHUNKS))
        self.assertEqual(events[-1][1]["answer"], INSUFFICIENT_EVIDENCE_MESSAGE)
        self.assertFalse(events[-1][1]["evidence_answers_question"])


TIMETABLE = {
    "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
    "commitSha": "abc",
    "chunkId": "chunk-timetable",
    "sourcePath": "examples/timetable.xml",
    "docType": "example",
    "text": "There are five stops: A, B, C, D, E. There are four journeys, two clockwise, two anticlockwise, both "
    "starting at A. Run times: A to B 15mn, B to C 15mn.",
}
OTHER = [
    {"chunkId": f"chunk-{n}", "sourcePath": f"xsd/other_{n}.xsd", "docType": "schema", "text": text}
    for n, text in enumerate(
        ["A Line has a PublicCode.", "A StopPlace contains Quay elements.", "A fare product has a price."]
    )
]


class CutTests(SimpleTestCase):
    def test_a_mark_after_the_full_stop_belongs_to_the_sentence_before(self):
        answer = "A `StopPlace` contains `Quay` elements. [E1] [E2] A `Line` has a `PublicCode`. [E2]"
        sentences = [answer[s:e] for s, e in _sentence_spans(answer)]
        self.assertEqual(
            sentences, ["A `StopPlace` contains `Quay` elements. [E1] [E2]", "A `Line` has a `PublicCode`. [E2]"]
        )

    def test_a_mark_followed_by_a_small_letter_is_the_subject_of_the_next_sentence(self):
        answer = "The blocks cover lines. [E2] describes a `Line` with a `PublicCode`."
        sentences = [answer[s:e] for s, e in _sentence_spans(answer)]
        self.assertEqual(sentences[1], "[E2] describes a `Line` with a `PublicCode`.")

    def test_no_cut_after_an_abbreviation_or_before_a_small_letter(self):
        answer = "Spots are seats, i.e. seats in that space [E1]. Use e.g. `Quay` here [E1]. Next one [E2]."
        self.assertEqual(len(_sentence_spans(answer)), 3)

    def test_a_blank_line_ends_a_sentence(self):
        answer = "A `StopPlace` holds quays [E1]\n\n**Lines** A `Line` has a `PublicCode` [E2]."
        self.assertEqual(len(_sentence_spans(answer)), 2)


class PlainSentenceTests(SimpleTestCase):
    def test_a_sentence_without_names_is_kept_when_its_facts_are_in_the_cited_passage(self):
        chunks = [TIMETABLE, *OTHER]
        answer = "Two clockwise and two anticlockwise journeys start at stop A, with 15 minutes per leg [E1]."
        self.assertIsNone(_sentence_verdicts(answer, chunks)[0]["reason"])

    def test_a_sentence_without_names_is_removed_when_its_facts_are_not_in_the_cited_passage(self):
        chunks = [TIMETABLE, *OTHER]
        answer = "Two clockwise and two anticlockwise journeys start at stop A, with 15 minutes per leg [E2]."
        self.assertIn("without specific technical content", _sentence_verdicts(answer, chunks)[0]["reason"])

    def test_a_number_not_in_the_cited_passage_removes_the_sentence(self):
        chunks = [TIMETABLE, *OTHER]
        answer = "Two clockwise and two anticlockwise journeys start at stop A, with 20 minutes per leg [E1]."
        self.assertIn("without specific technical content", _sentence_verdicts(answer, chunks)[0]["reason"])
