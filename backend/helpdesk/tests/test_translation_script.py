"""Letters of a foreign script in a translated piece are translated once more, that piece alone (plan 2026-11-21,
section 13). The model is mocked in every test."""

from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import llm_generator as g

ENGLISH = "The example encodes stops with `StopPlace` [E1]. Times are given per journey [E2]."
CLEAN = "1| Primer zapiše postaje s `StopPlace`.\n2| Časi so podani za vsako vožnjo.\n"
MIXED = "1| Primer zapiše postaje s特定imi `StopPlace`.\n2| Časi so podani za vsako vožnjo.\n"
CYRILLIC = "1| Primer zapiše postaje s `StopPlace`.\n2| Časi so podani za vsako vozних vožnjo.\n"


def _calls(*replies: str):
    replies = list(replies)
    seen: list[list[dict]] = []

    def stream(messages):
        seen.append(messages)
        yield replies.pop(0)
        return "end_turn"

    return stream, seen


@override_settings(LLM_ENABLED=True, LLM_PROVIDER="openai-compatible", LLM_API_BASE_URL="https://llm.example.test")
@patch("helpdesk.services.llm_generator._validate_answer_language")
class ForeignScriptTests(SimpleTestCase):
    def render(self, *replies, english=ENGLISH, stream=True):
        call, seen = _calls(*replies)
        with patch("helpdesk.services.llm_generator._rendering_text_stream", side_effect=call):
            generator = g._rendered_answer(english, "Slovenian", "Kaj je primer?", "What is an example?", stream=stream)
            tokens = []
            while True:
                try:
                    tokens.append(next(generator))
                except StopIteration as done:
                    answer, record = done.value
                    break
        return answer, record, seen, "".join(t[1] for t in tokens)

    def test_a_clean_translation_makes_no_extra_call(self, _language):
        answer, record, seen, _ = self.render(CLEAN)
        self.assertEqual(len(seen), 1)
        self.assertEqual(record["foreignScript"], [])
        self.assertIn("`StopPlace` [E1]", answer)

    def test_a_mixed_script_word_is_translated_once_more_alone(self, _language):
        answer, record, seen, streamed = self.render(MIXED, "1| Primer zapiše postaje s posebnimi `StopPlace`.\n")
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[1][1]["content"], "1| The example encodes stops with `StopPlace`.")
        self.assertNotIn("特定", answer)
        self.assertNotIn("特定", streamed)  # the piece is checked before it is shown
        self.assertEqual(record["foreignScript"], [{"piece": 1, "scripts": ["CJK"], "retranslated": True, "fixed": True}])
        self.assertEqual(sorted(answer.count(m) for m in ("[E1]", "[E2]")), [1, 1])

    def test_cyrillic_letters_in_a_latin_word_are_found(self, _language):
        answer, record, _, _ = self.render(CYRILLIC, "1| Časi so podani za vsako vožnjo.\n", stream=False)
        self.assertEqual(record["foreignScript"][0]["scripts"], ["CYRILLIC"])
        self.assertNotIn("вознх", answer)
        self.assertNotIn("н", answer)

    def test_a_foreign_script_held_by_the_english_piece_passes(self, _language):
        english = "The Greek name is «Στάση» in the example [E1]. Times are given per journey [E2]."
        reply = "1| Grško ime je «Στάση» v primeru.\n2| Časi so podani za vsako vožnjo.\n"
        _, record, seen, _ = self.render(reply, english=english)
        self.assertEqual(len(seen), 1)
        self.assertEqual(record["foreignScript"], [])

    def test_a_fault_that_stays_serves_the_better_attempt_and_is_recorded(self, _language):
        answer, record, seen, _ = self.render(MIXED, "1| Primer 特定zapiše 特定postaje s特定imi `StopPlace`.\n")
        self.assertEqual(len(seen), 2)
        self.assertIn("s特定imi", answer)  # the first attempt has fewer foreign letters
        self.assertNotIn("特定zapiše", answer)
        self.assertEqual(record["foreignScript"][0]["fixed"], False)

    def test_scripts_are_read_from_letter_names_only(self, _language):
        self.assertEqual(dict(g._letter_scripts("artigo 3.º ok")), {"LATIN": 8})
        self.assertEqual(set(g._letter_scripts("s特定imi")), {"LATIN", "CJK"})
