from __future__ import annotations

import datetime as dt
import json
import threading
from unittest.mock import patch

import jwt
from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from helpdesk.services import fixed_text_language, request_timing
from helpdesk.services.semantic_abstention import INSUFFICIENT_EVIDENCE_MESSAGE, NOT_RELEVANT_MESSAGE

QUESTION = "Kaj so to metapodatki?"
ENGLISH = "What is metadata?"
SLOVENIAN = (
    "Ta služba za pomoč odgovarja na vprašanja o standardih NeTEx, SIRI, OpRa in Transmodel, DATEX II in TN-ITS, "
    "profilu mobilityDCAT-AP in zakonodaji EU. Preoblikujte vprašanje ali navedite standard, ki ga mislite."
)


def _reply(text: str) -> dict:
    return {"choices": [{"message": {"content": json.dumps({"text": text}, ensure_ascii=False)}}]}


def _render(text: str, question: str = QUESTION, english: str | None = ENGLISH) -> str:
    return fixed_text_language.in_question_language(text, question=question, english_question=english)


@override_settings(LLM_ENABLED=True, FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS=3.0)
@patch("helpdesk.services.llm_generator.question_language", return_value="Slovenian")
@patch("helpdesk.services.llm_generator._request_chat_completion")
class FixedTextLanguageTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        request_timing.start()

    def test_an_english_question_gets_the_text_without_a_model_call(self, chat_mock, language_mock):
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE, question="What is the weather tomorrow?", english=None), NOT_RELEVANT_MESSAGE)
        chat_mock.assert_not_called()
        language_mock.assert_not_called()

    def test_a_question_found_english_after_all_gets_the_text(self, chat_mock, language_mock):
        language_mock.return_value = "English"
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
        chat_mock.assert_not_called()

    def test_an_unknown_language_gets_the_text(self, chat_mock, language_mock):
        language_mock.return_value = None
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
        chat_mock.assert_not_called()

    def test_the_text_comes_in_the_question_language_and_once_per_language(self, chat_mock, _language):
        chat_mock.return_value = _reply(SLOVENIAN)
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), SLOVENIAN)
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE, question="Kakšno bo vreme jutri v Ljubljani?"), SLOVENIAN)
        self.assertEqual(chat_mock.call_count, 1)
        prompt = chat_mock.call_args.kwargs["messages"]
        self.assertIn("Slovenian", prompt[0]["content"])
        self.assertEqual(prompt[1]["content"], NOT_RELEVANT_MESSAGE)
        self.assertEqual(chat_mock.call_args.kwargs["model"], settings.FIXED_TEXT_TRANSLATION_MODEL)

    def test_another_text_or_language_is_rendered_anew(self, chat_mock, language_mock):
        chat_mock.side_effect = [_reply(SLOVENIAN), _reply("Nimam dovolj dokazov."), _reply("Ich habe nicht genug Belege.")]
        _render(NOT_RELEVANT_MESSAGE)
        self.assertEqual(_render(INSUFFICIENT_EVIDENCE_MESSAGE), "Nimam dovolj dokazov.")
        language_mock.return_value = "German"
        self.assertEqual(_render(INSUFFICIENT_EVIDENCE_MESSAGE, question="Wie wird das Wetter?"), "Ich habe nicht genug Belege.")
        self.assertEqual(chat_mock.call_count, 3)

    def test_an_unreachable_model_keeps_the_english_text_and_caches_nothing(self, chat_mock, _language):
        chat_mock.side_effect = ConnectionError("model unreachable")
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
        chat_mock.side_effect = None
        chat_mock.return_value = _reply(SLOVENIAN)
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), SLOVENIAN)

    def test_an_empty_or_unparsable_rendering_keeps_the_english_text(self, chat_mock, _language):
        for content in ('{"text": ""}', "not json", '{"other": 1}'):
            with self.subTest(content):
                chat_mock.return_value = {"choices": [{"message": {"content": content}}]}
                self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)

    def test_a_rendering_that_drops_a_standard_name_keeps_the_english_text(self, chat_mock, _language):
        chat_mock.return_value = _reply(SLOVENIAN.replace("NeTEx", "NETEKS"))
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)

    @override_settings(FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS=0.2)
    def test_a_slow_rendering_keeps_the_english_text_and_is_cached_when_it_arrives(self, chat_mock, _language):
        release = threading.Event()
        done = threading.Event()

        def slow(**_kwargs):
            release.wait(5)
            return _reply(SLOVENIAN)

        chat_mock.side_effect = slow
        original_set = fixed_text_language._cache_set

        def cache_set(key, value):
            original_set(key, value)
            done.set()

        with patch.object(fixed_text_language, "_cache_set", side_effect=cache_set):
            self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
            release.set()
            self.assertTrue(done.wait(5))
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), SLOVENIAN)
        self.assertEqual(chat_mock.call_count, 1)

    @override_settings(FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS=0.2)
    def test_refusals_while_a_rendering_is_under_way_share_its_call(self, chat_mock, _language):
        release = threading.Event()

        def slow(**_kwargs):
            release.wait(5)
            return _reply(SLOVENIAN)

        chat_mock.side_effect = slow
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
        release.set()
        for future in list(fixed_text_language._IN_FLIGHT.values()):
            future.result(5)
        self.assertEqual(chat_mock.call_count, 1)

    @override_settings(FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS=0)
    def test_a_zero_timeout_keeps_refusals_in_english(self, chat_mock, _language):
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE), NOT_RELEVANT_MESSAGE)
        chat_mock.assert_not_called()

    def test_a_failing_cache_still_renders(self, chat_mock, _language):
        chat_mock.return_value = _reply(SLOVENIAN)
        with patch.object(fixed_text_language.cache, "get", side_effect=ConnectionError("redis down")), patch.object(
            fixed_text_language.cache, "set", side_effect=ConnectionError("redis down")
        ):
            self.assertEqual(_render(NOT_RELEVANT_MESSAGE), SLOVENIAN)


@override_settings(LLM_ENABLED=True, LLM_API_BASE_URL="http://llm.invalid", SEARCH_TRANSLATION_ENABLED=True)
class LanguageFromTheSearchTranslationTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        request_timing.start()

    @patch("helpdesk.services.llm_generator._classify_question_language_with_llm", return_value="Slovenian")
    @patch("helpdesk.services.llm_generator._request_chat_completion")
    def test_the_refusal_uses_the_language_the_search_translation_found(self, chat_mock, classify_mock):
        """The classifier is asked once in the request: by the search translation, not again by the refusal."""
        from helpdesk.services.llm_generator import english_search_query

        chat_mock.side_effect = [
            {"choices": [{"message": {"content": json.dumps({"language": "Slovenian", "text": ENGLISH})}}]},
            _reply(SLOVENIAN),
        ]
        english = english_search_query(QUESTION)
        self.assertEqual(english, ENGLISH)
        self.assertEqual(_render(NOT_RELEVANT_MESSAGE, english=english), SLOVENIAN)
        self.assertEqual(classify_mock.call_count, 1)
        self.assertIn("Slovenian", chat_mock.call_args.kwargs["messages"][0]["content"])

    @patch("helpdesk.services.llm_generator.question_language", return_value="German")
    @patch("helpdesk.services.llm_generator._request_chat_completion", return_value=_reply("Ich habe nicht genug Belege."))
    def test_without_a_noted_language_the_question_is_asked(self, _chat, language_mock):
        self.assertEqual(_render(INSUFFICIENT_EVIDENCE_MESSAGE, question="Wie wird das Wetter?"), "Ich habe nicht genug Belege.")
        language_mock.assert_called_once()


@override_settings(LLM_ENABLED=True, FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS=3.0)
@patch("helpdesk.api.views.semantic_abstention_message", return_value=NOT_RELEVANT_MESSAGE)
@patch("helpdesk.services.llm_generator.question_language", return_value="Slovenian")
@patch("helpdesk.services.llm_generator._request_chat_completion")
class RefusalLanguageApiTests(APITestCase):
    def setUp(self):
        cache.clear()

    def _headers(self) -> dict:
        now = dt.datetime.now(dt.timezone.utc)
        payload = {"sub": "test-user", "iat": int(now.timestamp()), "exp": int((now + dt.timedelta(minutes=30)).timestamp())}
        if settings.JWT_ISSUER:
            payload["iss"] = settings.JWT_ISSUER
        if settings.JWT_AUDIENCE:
            payload["aud"] = settings.JWT_AUDIENCE
        return {"HTTP_AUTHORIZATION": f"Bearer {jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)}"}

    def _ask(self, url_name: str, question: str) -> dict:
        response = self.client.post(
            reverse(url_name), {"question": question}, format="json", HTTP_X_REQUEST_ID=f"req-{url_name}", **self._headers()
        )
        if url_name == "answer-question":
            return response.data
        body = b"".join(response.streaming_content).decode("utf-8")
        return [json.loads(part[len("data:"):]) for part in body.split("\n\n") if part.startswith("data:")][-1]["answer"]

    def test_both_endpoints_refuse_in_the_question_language(self, chat_mock, _language, _screen):
        chat_mock.return_value = _reply(SLOVENIAN)
        with patch("helpdesk.services.llm_generator.english_search_query", return_value=ENGLISH):
            for url_name in ("answer-question", "answer-question-stream"):
                with self.subTest(url_name):
                    answer = self._ask(url_name, QUESTION)
                    self.assertEqual(answer["answer"], SLOVENIAN)
                    self.assertEqual(answer["mode"], "abstain")
                    self.assertTrue(answer["abstained"])
                    self.assertEqual(answer["abstentionReason"], "INSUFFICIENT_EVIDENCE")
                    self.assertEqual(answer["trace"]["semanticFallback"], "NO_CONCEPT_MATCH")
                    self.assertEqual(answer["citations"], [])
        self.assertEqual(chat_mock.call_count, 1)

    def test_both_endpoints_refuse_an_english_question_with_the_english_text(self, chat_mock, _language, _screen):
        with patch("helpdesk.services.llm_generator.english_search_query", return_value=None):
            for url_name in ("answer-question", "answer-question-stream"):
                with self.subTest(url_name):
                    self.assertEqual(self._ask(url_name, "What is the weather tomorrow?")["answer"], NOT_RELEVANT_MESSAGE)
        chat_mock.assert_not_called()

    def test_an_unreachable_model_refuses_with_the_english_text(self, chat_mock, _language, _screen):
        chat_mock.side_effect = ConnectionError("model unreachable")
        with patch("helpdesk.services.llm_generator.english_search_query", return_value=ENGLISH):
            for url_name in ("answer-question", "answer-question-stream"):
                with self.subTest(url_name):
                    answer = self._ask(url_name, QUESTION)
                    self.assertEqual(answer["answer"], NOT_RELEVANT_MESSAGE)
                    self.assertEqual(answer["mode"], "abstain")
