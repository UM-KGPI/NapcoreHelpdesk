"""Citation grounding: false positives found in Claude Haiku/Sonnet answers (2026-11-04), and the real
problems the check must still catch.

Replaying 44 captured answers (30 benchmark questions on Haiku 5.5) through the validator: 17 of 21
rejections were false positives and now pass; all 23 accepted answers stay accepted.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.llm_generator import (
    LLMGenerationError,
    _citation_segments,
    _classify_terms,
    _validate_citation_grounding,
)


def _chunk(text: str, source: str = "xsd/opra.xsd") -> dict:
    return {"text": text, "sourcePath": source}


CAPACITY = _chunk("PlannedCapacity records planned capacity information per journey.", "xsd/opra_indicators/opra_capacity_version.xsd")
FARES = _chunk("NeTEx has several specialisations of FARE PRICE for GroupSave tickets.", "examples/functions/fares/rail/Netex_era_toc_uk.xml")
SIRI = _chunk("EstimatedVehicleJourney carries EstimatedCalls with AimedArrivalTime.", "xsd/siri_model/siri_estimatedVehicleJourney.xsd")


class TermExtractionTests(SimpleTestCase):
    def test_capitalised_ordinary_words_are_not_terms(self):
        strong, weak = _classify_terms("**What it measures:** This shows None of the Other parts. According to the schema")
        self.assertEqual(strong + weak, [])

    def test_element_names_still_are(self):
        strong, weak = _classify_terms("The block lists the Departure element and a ScheduledStopPoint in a STOP PLACE.")
        self.assertIn("Departure", weak)
        self.assertIn("ScheduledStopPoint", weak)

    def test_code_spans_are_paired_in_order(self):
        strong, _ = _classify_terms("It gives arrival (`a`) and departure (`d`) times and `DepartureTime` values.")
        self.assertEqual(strong, ["DepartureTime"])

    def test_a_backticked_common_word_is_an_identifier(self):
        strong, _ = _classify_terms("The `Journey` definition covers common properties of a JOURNEY.")
        self.assertEqual(strong, ["Journey"])

    def test_times_are_not_namespaced_ids(self):
        strong, _ = _classify_terms("B departs at 14:32. The element is netex:Line.")
        self.assertEqual(strong, ["netex:Line"])

    def test_all_caps_concepts_are_whole_words(self):
        _, weak = _classify_terms('Documented as "Dummy Supertype for LINE & FLEXIBLE LINe."')
        self.assertNotIn("FLEXIBLE LIN", weak)


class SegmentTests(SimpleTestCase):
    def test_each_citation_supports_the_text_before_it(self):
        segments = dict(_citation_segments("A JOURNEY has accounting links [E1]; the SIRI element `AimedArrivalTime` [E3]."))
        self.assertIn("accounting", segments["1"])
        self.assertIn("AimedArrivalTime", segments["3"])
        self.assertNotIn("AimedArrivalTime", segments["1"])

    def test_a_citation_as_subject_supports_the_text_after_it(self):
        segments = dict(_citation_segments("[E1] describes GroupSave conditions, [E2] discusses FARE PRICE."))
        self.assertIn("GroupSave", segments["1"])
        self.assertIn("FARE PRICE", segments["2"])

    def test_adjacent_citations_share_their_text(self):
        segments = dict(_citation_segments("The blocks cover `AbstractObject` [E1][E2], `FareStructureElement` [E3]."))
        self.assertIn("AbstractObject", segments["2"])
        self.assertNotIn("FareStructureElement", segments["2"])


class GroundingFalsePositiveTests(SimpleTestCase):
    def test_a_bold_label_word_is_not_checked(self):
        _validate_citation_grounding(
            "**What it measures:** The definition itself only says it records planned capacity information [E1].", [CAPACITY]
        )

    def test_an_honest_scope_sentence_passes(self):
        _validate_citation_grounding("The example concerns cancelled journeys, not capacity [E1].", [CAPACITY])
        _validate_citation_grounding("No XML snippet for this can be given from the evidence [E1].", [CAPACITY])
        _validate_citation_grounding("[E1] and [E2] concern other topics, so they do not answer the question.", [CAPACITY, FARES])

    def test_a_citation_on_its_own_line_passes(self):
        _validate_citation_grounding("PlannedCapacity records planned capacity [E1].\n[E1].", [CAPACITY])

    def test_a_term_named_as_absent_passes(self):
        _validate_citation_grounding("**EstimatedCall**: The evidence contains no formal definition [E1].", [FARES])

    def test_terms_are_checked_against_their_own_citation(self):
        _validate_citation_grounding(
            "GroupSave tickets have FARE PRICE specialisations [E1], and `EstimatedVehicleJourney` carries calls [E2].",
            [FARES, SIRI],
        )

    def test_underscores_and_spaces_compare_equal(self):
        tap = _chunk("Simple carrier example for fares data.", "examples/standards/tap_tsi/B1_NRT/Netex_sncf_b1_1.xml")
        _validate_citation_grounding("[E1] is a simple carrier example for TAP TSI fares data.", [tap])


class GroundingStillCatchesTests(SimpleTestCase):
    def test_generic_filler_is_rejected(self):
        with self.assertRaisesRegex(LLMGenerationError, "without specific technical content"):
            _validate_citation_grounding("You should follow the specification and validate it carefully [E1].", [CAPACITY])

    def test_a_hallucinated_element_is_rejected(self):
        with self.assertRaisesRegex(LLMGenerationError, "does not ground the claim"):
            _validate_citation_grounding("Capacity is reported in the `PlannedFleetSizeReport` element [E1].", [CAPACITY])

    def test_an_element_cited_to_the_wrong_block_is_rejected(self):
        with self.assertRaisesRegex(LLMGenerationError, r"Citation \[E1\] does not ground"):
            _validate_citation_grounding("`EstimatedVehicleJourney` carries the calls [E1].", [CAPACITY, SIRI])
