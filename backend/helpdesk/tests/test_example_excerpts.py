from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.example_retrieval import concept_excerpt
from helpdesk.services.llm_generator import _question_focus_terms, _trim_chunk_text
from helpdesk.services.retrieval_gateway import (
    _concept_element_boost,
    _ensure_element_coverage,
    concept_element_names,
)

HEADER = "<PublicationDelivery>\n" + "\n".join(f"  <Frame{i}/>" for i in range(400)) + "\n"
TSJ = '<TemplateServiceJourney version="1" id="x:1">\n  <Name>Journey</Name>\n</TemplateServiceJourney>\n'


class ConceptExcerptTests(SimpleTestCase):
    def test_excerpt_shows_the_element_deep_in_the_file(self):
        content = HEADER + TSJ + "</PublicationDelivery>\n"
        self.assertNotIn("<TemplateServiceJourney", content[:2000])

        excerpt = concept_excerpt(content, "TemplateServiceJourney")

        self.assertIn("<TemplateServiceJourney", excerpt)
        self.assertLessEqual(len(excerpt), 2000)

    def test_falls_back_to_the_head_when_the_element_is_absent(self):
        content = HEADER
        self.assertEqual(concept_excerpt(content, "TemplateServiceJourney"), content[:2000])

    def test_does_not_match_a_longer_element_with_the_same_prefix(self):
        content = HEADER + "<TemplateServiceJourneyRef ref='x'/>\n"
        self.assertEqual(concept_excerpt(content, "TemplateServiceJourney"), content[:2000])


class PromptTrimTests(SimpleTestCase):
    def test_cut_keeps_an_element_named_in_the_question(self):
        text = HEADER + TSJ
        terms = _question_focus_terms("Can you give a NeTEx TemplateServiceJourney XML snippet?")

        trimmed = _trim_chunk_text(text, max_chars=1200, focus_terms=terms)

        self.assertIn("<TemplateServiceJourney", trimmed)

    def test_head_cut_unchanged_when_element_already_fits(self):
        text = TSJ + HEADER
        trimmed = _trim_chunk_text(text, max_chars=1200, focus_terms=["TemplateServiceJourney"])
        self.assertTrue(trimmed.startswith("<TemplateServiceJourney"))


class ElementRankingTests(SimpleTestCase):
    def test_element_names_come_from_standard_concepts_only(self):
        names = concept_element_names({"netex:TemplateServiceJourney", "transmodel:TEMPLATE_SERVICE_JOURNEY", "transmodel:when"})
        self.assertEqual(names, ["TemplateServiceJourney"])

    def test_boost_only_for_chunks_with_the_opening_tag(self):
        names = ["TemplateServiceJourney"]
        self.assertGreater(_concept_element_boost("example", TSJ, names), 0)
        self.assertEqual(_concept_element_boost("example", "<!-- a template service journey example -->", names), 0)
        self.assertEqual(_concept_element_boost("ontology-definition", TSJ, names), 0)

    def test_each_asked_element_gets_a_chunk_right_after_the_definitions(self):
        definition = {"docType": "ontology-definition", "text": "TemplateServiceJourney definition"}
        tsj_a = {"docType": "example", "text": TSJ}
        tsj_b = {"docType": "example", "text": TSJ + "<!-- b -->"}
        unrelated = {"docType": "example", "text": "<Line/>"}
        flexible = {"docType": "example", "text": "<FlexibleServiceProperties id='f'/>"}
        selected = [definition, tsj_a, tsj_b, unrelated, flexible]

        result = _ensure_element_coverage(selected, selected, ["FlexibleServiceProperties", "TemplateServiceJourney"], top_k=6)

        self.assertIs(result[0], definition)
        self.assertEqual({id(c) for c in result[1:3]}, {id(flexible), id(tsj_a)})

    def test_single_element_questions_are_left_alone(self):
        selected = [{"docType": "example", "text": "<Line/>"}, {"docType": "example", "text": TSJ}]
        self.assertEqual(_ensure_element_coverage(selected, selected, ["TemplateServiceJourney"], 6), selected)
