from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import suggested_questions as sq


def _passage(path: str, text: str = "Some text.", scope=("NeTEx",)) -> dict:
    return {
        "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
        "sourcePath": path,
        "text": text,
        "heading": "",
        "standardsScope": list(scope),
        "score": 0.8,
    }


PASSAGES = [_passage("xsd/a.xsd", "A lift is equipment."), _passage("xsd/b.xsd"), _passage("README.md")]


def _reply(*items) -> str:
    return json.dumps({"suggestions": list(items)})


class ParseWrittenTests(SimpleTestCase):
    def test_keeps_one_question_per_passage_with_its_source(self):
        kept = sq.parse_written(
            _reply(
                {"passage": 1, "question": "How is lift equipment described in NeTEx?", "english": "How is lift equipment described in NeTEx?"},
                {"passage": 3, "question": "What does the README say?", "english": "What does the README say?"},
            ),
            PASSAGES,
            "How do I describe a lift?",
        )
        self.assertEqual([s["question"] for s in kept], ["How is lift equipment described in NeTEx?", "What does the README say?"])
        self.assertEqual(kept[0]["passage"]["sourcePath"], "xsd/a.xsd")
        self.assertEqual(kept[0]["way"], "written")

    def test_drops_unknown_passages_repeats_of_the_question_and_duplicates(self):
        kept = sq.parse_written(
            _reply(
                {"passage": 9, "question": "Out of range?"},
                {"passage": "x", "question": "Not a number?"},
                {"passage": 1, "question": "how do I describe a LIFT"},
                {"passage": 2, "question": "Kept?"},
                {"passage": 2, "question": "Second for the same passage?"},
                {"passage": 3, "question": "kept"},
                {"passage": 3, "question": ""},
            ),
            PASSAGES,
            "How do I describe a lift?",
        )
        self.assertEqual([s["question"] for s in kept], ["Kept?"])

    def test_at_most_three(self):
        passages = [_passage(f"xsd/{i}.xsd") for i in range(5)]
        reply = _reply(*({"passage": i + 1, "question": f"Question {i}?"} for i in range(5)))
        self.assertEqual(len(sq.parse_written(reply, passages, "original")), 3)

    def test_an_empty_list_is_no_suggestions_and_no_json_is_an_error(self):
        self.assertEqual(sq.parse_written('{"suggestions": []}', PASSAGES, "q"), [])
        with self.assertRaises(ValueError):
            sq.parse_written("I cannot help.", PASSAGES, "q")


class PassageMessagesTests(SimpleTestCase):
    def test_the_model_gets_the_question_and_the_passages_with_their_source_only(self):
        messages = sq.passage_messages("Kaj je vozni red?", PASSAGES, "Slovenian")
        system, user = messages[0]["content"], messages[1]["content"]
        self.assertIn("Write each question in Slovenian", system)
        self.assertIn("Kaj je vozni red?", user)
        self.assertIn("[1] From NeTEx: xsd/a.xsd", user)
        self.assertIn("A lift is equipment.", user)
        self.assertIn("[3] From NeTEx: README.md", user)

    def test_unknown_language_asks_for_the_question_s_language(self):
        system = sq.passage_messages("q", PASSAGES, None)[0]["content"]
        self.assertIn("the language of the user's question", system)

    def test_long_passages_are_cut(self):
        user = sq.passage_messages("q", [_passage("x", "word " * 1000)], "English")[1]["content"]
        self.assertLess(len(user), sq.PASSAGE_TEXT_CHARS + 200)


class WrittenSuggestionsTests(SimpleTestCase):
    def test_no_passages_no_call(self):
        with patch.object(sq, "_model_reply") as reply:
            result = sq.written_suggestions("q", [], "English")
        reply.assert_not_called()
        self.assertEqual(result, {"suggestions": [], "calls": 0, "seconds": 0.0, "error": None})

    def test_a_failed_call_gives_no_suggestions(self):
        with patch.object(sq, "_model_reply", side_effect=TimeoutError("slow")):
            result = sq.written_suggestions("q", PASSAGES, "English")
        self.assertEqual(result["suggestions"], [])
        self.assertEqual(result["calls"], 1)
        self.assertIn("slow", result["error"])

    def test_an_unusable_reply_gives_no_suggestions(self):
        with patch.object(sq, "_model_reply", return_value="no json here"):
            self.assertEqual(sq.written_suggestions("q", PASSAGES, "English")["suggestions"], [])

    def test_a_reply_is_parsed(self):
        with patch.object(sq, "_model_reply", return_value=_reply({"passage": 2, "question": "What is B?", "english": "What is B?"})):
            result = sq.written_suggestions("q", PASSAGES, "English")
        self.assertEqual([s["question"] for s in result["suggestions"]], ["What is B?"])
        self.assertIsNone(result["error"])

    @override_settings(CONTROLLER_LLM_PROVIDER="anthropic", CONTROLLER_LLM_API_MODEL="m", ANTHROPIC_API_KEY="k")
    def test_the_anthropic_controller_is_called_once_with_a_json_answer(self):
        payload = {"choices": [{"message": {"content": _reply({"passage": 1, "question": "What is A?"})}}]}
        with patch("helpdesk.services.controller_llm.anthropic_controller_call", return_value=payload) as call:
            result = sq.written_suggestions("q", PASSAGES, "English")
        self.assertEqual(call.call_count, 1)
        self.assertTrue(call.call_args.kwargs["json_answer"])
        self.assertEqual([s["question"] for s in result["suggestions"]], ["What is A?"])


class NearestAnsweredTests(SimpleTestCase):
    POOL = [
        {"question": "What is a quay?", "embedding": [1.0, 0.0]},
        {"question": "What is a stop place?", "embedding": [0.9, 0.1]},
        {"question": "what is a stop place", "embedding": [0.9, 0.1]},
        {"question": "How are fares defined?", "embedding": [0.0, 1.0]},
        {"question": "No embedding?", "embedding": None},
    ]

    def test_nearest_first_each_once_never_the_question_itself(self):
        kept = sq.nearest_answered("What is a quay?", [1.0, 0.0], self.POOL)
        self.assertEqual([s["question"] for s in kept], ["What is a stop place?", "How are fares defined?"])
        self.assertEqual(kept[0]["way"], "earlier")

    def test_limit(self):
        self.assertEqual(len(sq.nearest_answered("other", [1.0, 0.0], self.POOL, limit=1)), 1)


class CombinedTests(SimpleTestCase):
    def test_earlier_first_then_written_without_duplicates(self):
        earlier = [{"question": "A?"}, {"question": "B?"}]
        written = [{"question": "a"}, {"question": "C?"}, {"question": "D?"}]
        self.assertEqual([s["question"] for s in sq.combined(earlier, written)], ["A?", "B?", "C?"])


class AllScopesTests(SimpleTestCase):
    def test_every_source_is_searched_the_opt_in_ones_too(self):
        from helpdesk.services.retrieval_gateway import CORE_SCOPES, OPT_IN_SCOPES

        self.assertEqual(set(sq.all_scopes()), set(CORE_SCOPES) | set(OPT_IN_SCOPES))
        # More scopes than places: the scope-coverage passes (one search per missing scope) do not run.
        self.assertGreater(len(sq.all_scopes()), sq.PASSAGE_TOP_K)


class CheapCheckTests(SimpleTestCase):
    def test_a_question_the_screen_refuses_is_not_searched(self):
        with patch("helpdesk.services.semantic_abstention._keyword_rule_message", return_value="refused"), patch(
            "helpdesk.services.retrieval_gateway.retrieve_chunks_with_trace"
        ) as retrieve, patch("helpdesk.services.question_parsing.parse_question_to_semantic_query"), patch(
            "helpdesk.services.question_parsing.select_effective_scope", return_value=([], False)
        ):
            result = sq.cheap_check("hi")
        retrieve.assert_not_called()
        self.assertFalse(result["passed"])
        self.assertFalse(result["screen"])

    def test_passes_with_a_passage_at_the_app_s_score_and_makes_no_model_call(self):
        chunks = [{"score": 0.5}, {"score": 0.7}]
        with patch("helpdesk.services.semantic_abstention._keyword_rule_message", return_value=None), patch(
            "helpdesk.services.retrieval_gateway.retrieve_chunks_with_trace", return_value=(chunks, {})
        ) as retrieve, patch("helpdesk.services.question_parsing.parse_question_to_semantic_query"), patch(
            "helpdesk.services.question_parsing.select_effective_scope", return_value=(["NeTEx"], False)
        ):
            result = sq.cheap_check("What is a quay in NeTEx?")
        self.assertTrue(result["passed"])
        self.assertEqual(result["passagesAboveScore"], 1)
        # No English rendering given: none is computed (None, not the gateway's default that translates).
        self.assertIsNone(retrieve.call_args.kwargs["english_question"])
        self.assertEqual(retrieve.call_args.kwargs["scope"], ["NeTEx"])

    def test_fails_without_a_passage_at_the_app_s_score(self):
        with patch("helpdesk.services.semantic_abstention._keyword_rule_message", return_value=None), patch(
            "helpdesk.services.retrieval_gateway.retrieve_chunks_with_trace", return_value=([{"score": 0.3}], {})
        ), patch("helpdesk.services.question_parsing.parse_question_to_semantic_query"), patch(
            "helpdesk.services.question_parsing.select_effective_scope", return_value=([], False)
        ):
            self.assertFalse(sq.cheap_check("q")["passed"])


class NamedSourceTests(SimpleTestCase):
    def test_keeps_restated_questions_with_a_known_source(self):
        reply = json.dumps(
            {
                "suggestions": [
                    {"source": "mobilityDCAT-AP", "question": "Kaj so metapodatki v mobilityDCAT-AP?", "english": "What are metadata in mobilityDCAT-AP?"},
                    {"source": "Unknown", "question": "Elsewhere?"},
                    {"source": "EU legislation", "question": "Kaj so to metapodatki?"},
                    {"source": "NAPCORE", "question": "kaj so metapodatki v mobilityDCAT-AP"},
                    {"source": "NAPCORE", "question": "Kaj so metapodatki po NAPCORE?"},
                ]
            }
        )
        kept = sq.parse_named(reply, "Kaj so to metapodatki?")
        self.assertEqual([s["source"] for s in kept], ["mobilityDCAT-AP", "NAPCORE"])
        self.assertEqual(kept[0]["way"], "named")
        self.assertEqual(kept[0]["english"], "What are metadata in mobilityDCAT-AP?")

    def test_the_model_gets_the_sources_and_the_question_only(self):
        system, user = (m["content"] for m in sq.named_messages("Kaj so to metapodatki?", "Slovenian"))
        for name in sq.SOURCE_DESCRIPTIONS:
            self.assertIn(f"- {name}: ", system)
        self.assertIn("Write each in Slovenian", system)
        self.assertEqual(user, "User's question:\nKaj so to metapodatki?")

    def test_a_failed_call_gives_no_suggestions(self):
        with patch.object(sq, "_model_reply", side_effect=OSError("down")):
            result = sq.named_suggestions("q", "English")
        self.assertEqual((result["suggestions"], result["calls"]), ([], 1))

    def test_the_sources_are_the_api_s_scope_values(self):
        from helpdesk.api.serializers import STANDARDS_SCOPE_CHOICES

        self.assertTrue(set(sq.SOURCE_DESCRIPTIONS) <= set(STANDARDS_SCOPE_CHOICES))
