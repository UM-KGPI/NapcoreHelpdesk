from __future__ import annotations

import datetime as dt
import json
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from helpdesk.api.views import _search_scope
from helpdesk.services.question_parsing import UNKNOWN_CONCEPT_SENTINEL, SemanticQuery
from helpdesk.services.retrieval_gateway import ALL_SOURCE_SCOPES, CORE_SCOPES, OPT_IN_SCOPES


def _query(*, concept=UNKNOWN_CONCEPT_SENTINEL, confidence=0.45, discovered=()):
    return SemanticQuery(
        intent="definition",
        normativity="unspecified",
        core_concept=concept,
        core_concepts=[] if concept == UNKNOWN_CONCEPT_SENTINEL else [concept],
        ambiguous_core_concept=False,
        candidate_standards=[],
        original_terms=["metadata"],
        confidence={"intent": 0.6, "concept": confidence},
        discovered_standards=list(discovered),
    )


@override_settings(RELEVANCE_CHECK_ENABLED=True)
class SearchScopeTests(SimpleTestCase):
    def test_every_source_is_every_core_and_opt_in_scope(self):
        self.assertEqual(set(ALL_SOURCE_SCOPES), set(CORE_SCOPES) | set(OPT_IN_SCOPES))

    def test_a_question_the_check_let_through_is_searched_in_every_source(self):
        self.assertEqual(_search_scope(_query(), [], [], True, "What is metadata?"), list(ALL_SOURCE_SCOPES))

    def test_a_question_naming_a_standard_keeps_its_scope(self):
        self.assertEqual(_search_scope(_query(), ["SIRI"], [], True, "What is SIRI?"), ["SIRI"])

    def test_a_question_the_keyword_rules_answer_is_searched_as_before(self):
        answered = _query(concept="transmodel:TIMETABLE_FRAME", confidence=0.95, discovered=["NeTEx"])
        self.assertEqual(_search_scope(answered, [], [], True, "Any timetable from Slovenia?"), [])

    def test_no_screen_no_widening(self):
        self.assertEqual(_search_scope(_query(), [], [], False, "What is metadata?"), [])
        with override_settings(RELEVANCE_CHECK_ENABLED=False):
            self.assertEqual(_search_scope(_query(), [], [], True, "What is metadata?"), [])


_EMPTY_TRACE = {
    "graphRagVariant": "control",
    "graphExpansionHops": 0,
    "graphExpansionSource": "none",
    "graphConceptIds": [],
    "graphCandidatesAdded": 0,
    "graphEvidenceCount": 0,
    "graphScoreContribution": 0.0,
    "allCandidates": [],
}


@override_settings(LLM_ENABLED=False)
@patch("helpdesk.services.llm_generator.english_search_query", return_value=None)
@patch("helpdesk.api.views.semantic_abstention_message", return_value=None)
@patch("helpdesk.api.views.retrieve_chunks_with_trace", return_value=([], _EMPTY_TRACE))
@patch("helpdesk.api.views.select_effective_scope", return_value=([], False))
class SearchScopeApiTests(APITestCase):
    def _headers(self) -> dict:
        now = dt.datetime.now(dt.timezone.utc)
        payload = {"sub": "test-user", "iat": int(now.timestamp()), "exp": int((now + dt.timedelta(minutes=30)).timestamp())}
        if settings.JWT_ISSUER:
            payload["iss"] = settings.JWT_ISSUER
        if settings.JWT_AUDIENCE:
            payload["aud"] = settings.JWT_AUDIENCE
        return {"HTTP_AUTHORIZATION": f"Bearer {jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)}"}

    def _ask(self, url_name: str, question: str) -> None:
        response = self.client.post(
            reverse(url_name), {"question": question}, format="json", HTTP_X_REQUEST_ID=f"req-{url_name}", **self._headers()
        )
        if url_name != "answer-question":
            b"".join(response.streaming_content)

    def test_both_endpoints_search_the_scope_search_scope_gives(self, _scope, retrieve, _screen, _english):
        for reached, expected in ((True, list(ALL_SOURCE_SCOPES)), (False, [])):
            for url_name in ("answer-question", "answer-question-stream"):
                with self.subTest(url_name, reached=reached):
                    retrieve.reset_mock()
                    with patch("helpdesk.api.views.reaches_relevance_check", return_value=reached):
                        self._ask(url_name, "What is metadata?")
                    self.assertTrue(retrieve.called)
                    for call in retrieve.call_args_list:
                        self.assertEqual(call.kwargs["scope"], expected)
