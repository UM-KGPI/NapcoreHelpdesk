from __future__ import annotations

import io
import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.services import relevance_check
from helpdesk.services.relevance_check import has_artifact_term, is_relevant


def _response(content: str):
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
    return io.BytesIO(body)


LLM_SETTINGS = dict(
    CONTROLLER_LLM_API_BASE_URL="https://llm.invalid/v1",
    CONTROLLER_LLM_API_MODEL="m",
    CONTROLLER_LLM_API_KEY="k",
    CONTROLLER_LLM_VERIFY_SSL=True,
    CONTROLLER_LLM_PROVIDER="openai-compatible",
)


@override_settings(**LLM_SETTINGS)
@patch("helpdesk.services.relevance_check.resolve_effective_model", side_effect=lambda **kw: kw["configured_model"])
class IsRelevantTests(SimpleTestCase):
    def test_reads_the_verdict(self, _model):
        with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response("IRRELEVANT")):
            self.assertIs(is_relevant("What is the weather?"), False)
        with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response("RELEVANT")):
            self.assertIs(is_relevant("fares"), True)

    def test_irrelevant_is_not_mistaken_for_relevant_and_case_does_not_matter(self, _model):
        with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response("  Irrelevant.\n")):
            self.assertIs(is_relevant("GTFS question"), False)

    def test_unusable_replies_return_none(self, _model):
        for content in ("", "maybe", "I am not sure"):
            with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response(content)):
                self.assertIsNone(is_relevant("question"), content)

    def test_network_failure_returns_none_and_is_not_cached(self, _model):
        with patch("helpdesk.services.relevance_check.request.urlopen", side_effect=OSError("down")):
            self.assertIsNone(is_relevant("question"))
        with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response("RELEVANT")):
            self.assertIs(is_relevant("question"), True)

    def test_a_verdict_is_not_kept_a_repeated_question_is_asked_again(self, _model):
        with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response("IRRELEVANT")):
            self.assertIs(is_relevant("metadata"), False)
        replies = [_response("RELEVANT"), _response("RELEVANT")]
        with patch("helpdesk.services.relevance_check.request.urlopen", side_effect=replies) as urlopen:
            self.assertIs(is_relevant("  metadata "), True)
            self.assertIs(is_relevant("metadata"), True)
        self.assertEqual(urlopen.call_count, 2)

    def test_the_other_gateways_are_asked_at_temperature_zero(self, _model):
        with patch("helpdesk.services.relevance_check.request.urlopen", return_value=_response("RELEVANT")) as urlopen:
            is_relevant("fares")
        body = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(body["temperature"], 0.0)
        self.assertIn("Question: fares", body["messages"][0]["content"])

    @override_settings(CONTROLLER_LLM_API_BASE_URL="")
    def test_unconfigured_returns_none_without_a_call(self, _model):
        with patch("helpdesk.services.relevance_check.request.urlopen") as urlopen:
            self.assertIsNone(is_relevant("question"))
        urlopen.assert_not_called()


def _claude_reply(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


@override_settings(CONTROLLER_LLM_PROVIDER="anthropic", CONTROLLER_LLM_ANTHROPIC_EFFORT="low")
class ClaudePathTests(SimpleTestCase):
    def test_claude_answers_without_thinking(self):
        with patch("helpdesk.services.relevance_check.anthropic_controller_call", return_value=_claude_reply("RELEVANT")) as call:
            self.assertIs(is_relevant("Dataset licence?"), True)
        self.assertEqual(call.call_args.kwargs["thinking"], "disabled")
        self.assertIn("Question: Dataset licence?", call.call_args.kwargs["messages"][0]["content"])

    @override_settings(CONTROLLER_LLM_ANTHROPIC_EFFORT="xhigh")
    def test_above_effort_high_thinking_stays_on(self):
        # Claude rejects thinking "disabled" above effort high; the call would fail and the keyword refusal stand.
        with patch("helpdesk.services.relevance_check.anthropic_controller_call", return_value=_claude_reply("RELEVANT")) as call:
            is_relevant("fares")
        self.assertEqual(call.call_args.kwargs["thinking"], "adaptive")

    def test_each_ask_is_a_new_call(self):
        replies = [_claude_reply("IRRELEVANT"), _claude_reply("RELEVANT")]
        with patch("helpdesk.services.relevance_check.anthropic_controller_call", side_effect=replies) as call:
            self.assertIs(is_relevant("What is metadata?"), False)
            self.assertIs(is_relevant("What is metadata?"), True)
        self.assertEqual(call.call_count, 2)


class ArtifactTermTests(SimpleTestCase):
    def test_camel_case_terms_name_an_artifact(self):
        self.assertTrue(has_artifact_term("What is ServiceJourneyPattern?"))
        self.assertTrue(has_artifact_term("What is a PtSituationElement?"))

    def test_plain_words_acronyms_and_product_names_without_a_hump_do_not(self):
        self.assertFalse(has_artifact_term("How do I bake bread?"))
        self.assertFalse(has_artifact_term("Explain DATEX II traffic messages."))
        self.assertFalse(has_artifact_term(""))
