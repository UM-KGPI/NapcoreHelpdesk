"""A non-English question is also searched in English, and the two result lists are merged by rank."""

from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services.llm_generator import english_search_query
from helpdesk.services.question_parsing import UNKNOWN_CONCEPT_SENTINEL, parse_question_to_semantic_query
from helpdesk.services.retrieval_gateway import _merge_by_rank, retrieve_chunks_with_trace


def _reply(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


@override_settings(LLM_ENABLED=True, LLM_API_BASE_URL="https://llm.example/v1", SEARCH_TRANSLATION_ENABLED=True)
class EnglishSearchQueryTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator.question_language", return_value="Slovenian")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_non_english_question_gets_an_english_rendering(self, request, _language):
        request.return_value = _reply(json.dumps({"text": "What are the metadata in a NAP?"}))
        self.assertEqual(english_search_query("Kaj so metapodatki v NAP?"), "What are the metadata in a NAP?")

    @patch("helpdesk.services.llm_generator.question_language", return_value="German")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_a_differently_named_key_is_still_read(self, request, _language):
        request.return_value = _reply(json.dumps({"translation": "Which standard does MMTIS require?"}))
        self.assertEqual(english_search_query("Welchen Standard verlangt MMTIS?"), "Which standard does MMTIS require?")

    @patch("helpdesk.services.llm_generator.question_language", return_value="English")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_an_english_question_is_not_translated(self, request, _language):
        self.assertIsNone(english_search_query("What is a NAP?"))
        request.assert_not_called()

    @patch("helpdesk.services.llm_generator.question_language", return_value="Slovenian")
    @patch("helpdesk.services.llm_generator._request_chat_completion", side_effect=OSError("down"))
    def test_a_failure_leaves_the_question_alone(self, _request, _language):
        self.assertIsNone(english_search_query("Kaj so metapodatki v NAP?"))

    @override_settings(SEARCH_TRANSLATION_ENABLED=False)
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_switched_off(self, request):
        self.assertIsNone(english_search_query("Kaj so metapodatki v NAP?"))
        request.assert_not_called()


def _chunks(*ids: str) -> list[dict]:
    return [{"chunkId": chunk_id, "sourcePath": chunk_id} for chunk_id in ids]


class MergedSearchTests(SimpleTestCase):
    def test_lists_are_interleaved_english_first_without_repeats(self):
        merged = _merge_by_rank(_chunks("en1", "both", "en3"), _chunks("as1", "both", "as3"))
        self.assertEqual([c["chunkId"] for c in merged], ["en1", "as1", "both", "en3", "as3"])

    @patch("helpdesk.services.llm_generator.english_search_query", return_value="What are the metadata in a NAP?")
    @patch("helpdesk.services.retrieval_gateway._retrieve_chunks_once")
    def test_a_translated_question_is_searched_both_ways(self, once, _english):
        once.side_effect = lambda question, **_: (
            (_chunks("en1", "en2"), {"allCandidates": []})
            if question.startswith("What")
            else (_chunks("as1", "as2"), {"allCandidates": []})
        )
        chunks, trace = retrieve_chunks_with_trace("Kaj so metapodatki v NAP?", top_k=3, min_score=0.0)
        self.assertEqual([c["chunkId"] for c in chunks], ["en1", "as1", "en2"])
        self.assertEqual(trace["searchTranslation"], "What are the metadata in a NAP?")
        self.assertEqual(once.call_count, 2)

    @patch("helpdesk.services.llm_generator.english_search_query", return_value=None)
    @patch("helpdesk.services.retrieval_gateway._retrieve_chunks_once")
    def test_without_a_translation_there_is_one_search(self, once, _english):
        once.return_value = (_chunks("as1"), {"allCandidates": []})
        chunks, trace = retrieve_chunks_with_trace("What is a NAP?", top_k=3, min_score=0.0)
        self.assertEqual([c["chunkId"] for c in chunks], ["as1"])
        self.assertNotIn("searchTranslation", trace)
        self.assertEqual(once.call_count, 1)


GERMAN = "Welche Metadaten müssen Dateninhaber dem nationalen Zugangspunkt bereitstellen?"
ENGLISH = "Which metadata must data holders provide to the national access point?"
FRENCH = "Quelles métadonnées les détenteurs de données doivent-ils fournir au point d'accès national ?"


class ParseQuestionTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator.english_search_query", return_value=ENGLISH)
    def test_the_english_rendering_is_parsed_when_the_question_as_asked_matches_nothing(self, _english):
        from helpdesk.api.views import _parse_question

        semantic_query, english, parsed = _parse_question(GERMAN, [])
        self.assertEqual(english, ENGLISH)
        self.assertEqual(parsed, ENGLISH)
        self.assertIn("EU legislation", semantic_query.candidate_standards)  # "national access point"

    @patch("helpdesk.services.llm_generator.english_search_query", return_value="How does SIRI use NeTEx?")
    def test_a_question_that_already_names_a_standard_keeps_its_own_parse(self, _english):
        from helpdesk.api.views import _parse_question

        semantic_query, english, parsed = _parse_question("Wie verwendet SIRI NeTEx?", [])
        self.assertEqual(parsed, "Wie verwendet SIRI NeTEx?")
        self.assertEqual(english, "How does SIRI use NeTEx?")  # still searched in English
        self.assertEqual(sorted(semantic_query.candidate_standards), ["NeTEx", "SIRI"])

    @patch("helpdesk.services.llm_generator.english_search_query", return_value=ENGLISH)
    def test_the_english_rendering_is_parsed_when_it_finds_a_standard_the_question_does_not(self, _english):
        from helpdesk.api.views import _parse_question

        asked = parse_question_to_semantic_query(text=FRENCH)
        self.assertEqual(asked.candidate_standards, [])
        self.assertNotEqual(asked.core_concept, UNKNOWN_CONCEPT_SENTINEL)  # a concept through "point" alone
        semantic_query, _, parsed = _parse_question(FRENCH, [])
        self.assertEqual(parsed, ENGLISH)
        self.assertIn("EU legislation", semantic_query.candidate_standards)

    @patch("helpdesk.services.llm_generator.english_search_query", return_value=ENGLISH)
    def test_a_requested_scope_is_not_overridden(self, _english):
        from helpdesk.api.views import _parse_question

        _, _, parsed = _parse_question(GERMAN, ["NeTEx"])
        self.assertEqual(parsed, GERMAN)


class SuppliedRenderingTests(SimpleTestCase):
    @patch("helpdesk.services.llm_generator.english_search_query")
    @patch("helpdesk.services.retrieval_gateway._retrieve_chunks_once")
    def test_a_supplied_rendering_is_searched_without_translating_again(self, once, translate):
        once.side_effect = lambda question, **_: (_chunks(question[:2]), {"allCandidates": []})
        chunks, trace = retrieve_chunks_with_trace(GERMAN, top_k=3, min_score=0.0, english_question=ENGLISH)
        translate.assert_not_called()
        self.assertEqual([c["chunkId"] for c in chunks], ["Wh", "We"])
        self.assertEqual(trace["searchTranslation"], ENGLISH)

    @patch("helpdesk.services.llm_generator.english_search_query")
    @patch("helpdesk.services.retrieval_gateway._retrieve_chunks_once")
    def test_none_means_search_the_question_only(self, once, translate):
        once.return_value = (_chunks("as1"), {"allCandidates": []})
        retrieve_chunks_with_trace("What is a NAP?", top_k=3, min_score=0.0, english_question=None)
        translate.assert_not_called()
        self.assertEqual(once.call_count, 1)


class AccentedWordTests(SimpleTestCase):
    def test_accented_words_are_kept_whole(self):
        terms = parse_question_to_semantic_query(text=FRENCH).original_terms
        self.assertIn("métadonnées", terms)
        self.assertIn("détenteurs", terms)
        self.assertNotIn("tadonn", terms)
