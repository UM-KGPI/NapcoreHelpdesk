"""The purpose check of the sentence check: a passage's heading and a noun "flags" (plan 2026-11-21, section 15).
No database, no model."""

from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from helpdesk.services.llm_generator import _has_purpose_claim, _sentence_purpose_error

DATEX = [
    {
        "chunkId": "datex-lane",
        "sourcePath": "datex-model-v3.7/LocationReferencing.Lane",
        "docType": "datex",
        "heading": "DATEX II class Lane (namespace LocationReferencing)",
        "text": "Lane. A lane indicates a specific lane or group of lanes.",
    }
]
LANE = "The `Lane` class indicates a specific lane or group of lanes [E1]."


class PurposeTests(SimpleTestCase):
    def test_a_passage_whose_heading_names_the_element_defines_it(self):
        self.assertIsNone(_sentence_purpose_error(LANE, DATEX))

    def test_a_heading_names_the_element_as_a_whole_word(self):
        self.assertTrue(_sentence_purpose_error("The `Lan` class indicates a specific lane [E1].", DATEX))

    def test_a_heading_of_another_element_does_not_define_it(self):
        self.assertTrue(_sentence_purpose_error("The `Road` class indicates a specific lane [E1].", DATEX))

    @override_settings(SENTENCE_CHECK_PURPOSE_BY_HEADING_ENABLED=False)
    def test_the_setting_turns_the_heading_rule_off(self):
        self.assertTrue(_sentence_purpose_error(LANE, DATEX))

    def test_flags_after_a_noun_phrase_and_before_a_name_is_a_noun(self):
        self.assertFalse(_has_purpose_claim("Each interval has the boundary flags `StartIncluded` and `EndIncluded`."))

    def test_flags_after_a_name_or_before_a_word_is_a_verb(self):
        self.assertTrue(_has_purpose_claim("The `Cancellation` element flags whether the journey runs."))
        self.assertTrue(_has_purpose_claim("The element `Cancellation` flags `Delayed` as true."))

    @override_settings(SENTENCE_CHECK_PURPOSE_BY_HEADING_ENABLED=False)
    def test_the_setting_turns_the_noun_rule_off(self):
        self.assertTrue(_has_purpose_claim("Each interval has the boundary flags `StartIncluded` and `EndIncluded`."))
