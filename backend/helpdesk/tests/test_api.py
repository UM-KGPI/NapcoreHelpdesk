from __future__ import annotations

import datetime as dt
import json
import copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import jwt
import yaml
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from jsonschema import Draft202012Validator, RefResolver
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase

from helpdesk.api.exceptions import custom_exception_handler
from helpdesk.api.views import _build_file_url, _rewrite_source_paths_as_evidence_markers, _select_citations
from helpdesk.services.llm_generator import LLMGenerationError
from helpdesk.models import (
    AnswerEvidenceLink,
    EditorialQueueItem,
    EditorialQueueTransition,
    EvidenceProvenance,
    FAQEntry,
    FAQVersion,
    QuestionEvent,
    RetrievalEvent,
)


class HelpdeskApiTests(APITestCase):
    """Verify API contracts for authentication, answer orchestration, and editorial routing."""

    @classmethod
    def setUpClass(cls):
        # Load OpenAPI once so each test can assert response payload compatibility.
        super().setUpClass()
        openapi_path = Path(__file__).resolve().parents[3] / "api" / "openapi.yaml"
        with open(openapi_path, "r", encoding="utf-8") as handle:
            cls.openapi = yaml.safe_load(handle)

    def _token(self, subject: str = "test-user", roles: list[str] | None = None) -> str:
        """Create a short-lived JWT that matches application auth settings."""
        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(minutes=30)).timestamp()),
        }
        if roles:
            payload["roles"] = roles
        if settings.JWT_ISSUER:
            payload["iss"] = settings.JWT_ISSUER
        if settings.JWT_AUDIENCE:
            payload["aud"] = settings.JWT_AUDIENCE
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def assert_matches_schema(self, schema_name: str, payload: dict) -> None:
        """Assert that a payload matches the referenced OpenAPI schema component."""
        normalized_openapi = self._normalized_openapi()
        schema = {"$ref": f"#/components/schemas/{schema_name}"}
        validator = Draft202012Validator(schema, resolver=RefResolver.from_schema(normalized_openapi))
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            messages = [f"{list(error.path)}: {error.message}" for error in errors]
            self.fail("Schema validation failed: " + json.dumps(messages, indent=2))

    def _normalized_openapi(self) -> dict:
        """Normalize nullable OpenAPI fields to JSON Schema Draft 2020-12 equivalents."""
        document = copy.deepcopy(self.openapi)

        def normalize(node):
            if isinstance(node, dict):
                if node.get("nullable") is True:
                    if "type" in node:
                        node_type = node["type"]
                        if isinstance(node_type, list):
                            if "null" not in node_type:
                                node["type"] = [*node_type, "null"]
                        else:
                            node["type"] = [node_type, "null"]
                    if "enum" in node and None not in node["enum"]:
                        node["enum"] = [*node["enum"], None]
                    node.pop("nullable", None)
                for value in node.values():
                    normalize(value)
            elif isinstance(node, list):
                for item in node:
                    normalize(item)

        normalize(document)
        return document

    def auth_headers(self, roles: list[str] | None = None):
        """Return standard authenticated headers used by endpoint tests."""
        return {
            "HTTP_AUTHORIZATION": f"Bearer {self._token(roles=roles)}",
        }

    def test_answer_requires_bearer_auth(self):
        """Ensure anonymous callers cannot access the answer endpoint."""
        response = self.client.post(
            reverse("answer-question"),
            {"question": "How do I use NeTEx?"},
            format="json",
            HTTP_X_REQUEST_ID="req-no-auth",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assert_matches_schema("ErrorResponse", response.data)
        self.assertEqual(response.data["error"]["code"], "UNAUTHORIZED")
        self.assertEqual(response.data["error"]["requestId"], "req-no-auth")

    def test_health_live_reports_ok_without_auth(self):
        """Ensure liveness endpoint is public and returns healthy state."""
        response = self.client.get(reverse("health-live"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["check"], "live")
        self.assertEqual(response.data["service"], settings.SERVICE_NAME)
        self.assertEqual(response.data["version"], settings.SERVICE_VERSION)
        self.assertEqual(response.data["buildRef"], settings.SERVICE_BUILD_REF)

    def test_health_ready_reports_ok_with_database_probe(self):
        """Ensure readiness endpoint reports healthy when database check succeeds."""
        response = self.client.get(reverse("health-ready"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["check"], "ready")
        self.assertEqual(response.data["database"], "ok")
        self.assertEqual(response.data["service"], settings.SERVICE_NAME)
        self.assertEqual(response.data["version"], settings.SERVICE_VERSION)
        self.assertEqual(response.data["buildRef"], settings.SERVICE_BUILD_REF)

    @override_settings(DEBUG=True, DEV_JWT_AUTO_ISSUE=True)
    def test_dev_token_endpoint_issues_token_in_debug(self):
        """Ensure local development can mint a JWT without manual shell commands."""
        response = self.client.post(reverse("auth-dev-token"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["tokenType"], "Bearer")
        self.assertGreater(response.data["expiresInSeconds"], 0)

    @override_settings(DEBUG=False, DEV_JWT_AUTO_ISSUE=True)
    def test_dev_token_endpoint_rejects_when_not_debug(self):
        """Ensure dev token mint endpoint cannot be used when debug mode is off."""
        response = self.client.post(reverse("auth-dev-token"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assert_matches_schema("ErrorResponse", response.data)

    def test_invalid_jwt_returns_openapi_error_response(self):
        """Ensure malformed JWTs return the standardized OpenAPI error payload."""
        response = self.client.post(
            reverse("answer-question"),
            {"question": "How do I use NeTEx?"},
            format="json",
            HTTP_X_REQUEST_ID="req-bad-jwt",
            HTTP_AUTHORIZATION="Bearer invalid.jwt.token",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assert_matches_schema("ErrorResponse", response.data)
        self.assertEqual(response.data["error"]["code"], "UNAUTHORIZED")
        self.assertEqual(response.data["error"]["requestId"], "req-bad-jwt")

    def test_permission_denied_exception_handler_returns_openapi_error(self):
        """Ensure permission-denied errors are serialized as a 403 OpenAPI error."""
        factory = APIRequestFactory()
        django_request = factory.get("/api/v1/questions/answer", HTTP_X_REQUEST_ID="req-forbidden")
        request = Request(django_request)

        response = custom_exception_handler(PermissionDenied("Forbidden"), {"request": request})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assert_matches_schema("ErrorResponse", response.data)
        self.assertEqual(response.data["error"]["code"], "FORBIDDEN")
        self.assertEqual(response.data["error"]["requestId"], "req-forbidden")

    def test_answer_returns_faq_mode_for_known_question(self):
        """Ensure known FAQ intent follows the FAQ-first path with citations."""
        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How to use NeTEx for exchanging a timetable?",
                "standardsScope": ["NeTEx"],
            },
            format="json",
            HTTP_X_REQUEST_ID="req-faq-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "faq")
        self.assertGreaterEqual(response.data["confidence"], 0.85)
        self.assertFalse(response.data["abstained"])
        self.assertTrue(response.data["citations"])
        self.assertTrue(response.data["trace"]["questionEventId"])
        self.assertTrue(
            FAQVersion.objects.filter(
                faq_entry__faq_entry_id=response.data["trace"]["matchedFaqEntryId"],
                is_published=True,
            ).exists()
        )

    @patch("helpdesk.api.views.decide_route_with_controller_llm")
    def test_answer_uses_controller_rag_when_no_faq_matches(self, controller_mock):
        """Controller route 'rag' is respected when no high-confidence FAQ entry exists."""

        controller_mock.return_value = SimpleNamespace(route="rag", intent="novel", confidence=0.9)

        # Use a question that has no matching FAQ entry so the controller decision
        # actually influences routing.  The FAQ-first gate no longer allows the
        # controller to override a *matched* FAQ, but when no FAQ matches the
        # controller's route preference is still used to disambiguate RAG vs abstain.
        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "Explain OpRa operational exchange setup sequence.",
                "standardsScope": ["OpRa"],
            },
            format="json",
            HTTP_X_REQUEST_ID="req-controller-rag-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        # Without a published FAQ for this OpRa question, mode falls through to RAG/abstain.
        self.assertIn(response.data["mode"], ("rag", "abstain"))
        self.assertIsNone(response.data["trace"]["matchedFaqEntryId"])

    @patch("helpdesk.api.views.decide_route_with_controller_llm")
    def test_answer_skips_controller_when_controller_profile_is_deterministic(self, controller_mock):
        """Controller is bypassed when the request asks deterministic intent routing."""

        controller_mock.return_value = SimpleNamespace(route="rag", intent="novel", confidence=0.9)

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How to use NeTEx for exchanging a timetable?",
                "standardsScope": ["NeTEx"],
                "generationProfile": "llm-ready",
                "controllerProfile": "deterministic-grounded",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-controller-disabled-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "faq")
        self.assertIsNotNone(response.data["trace"]["matchedFaqEntryId"])
        controller_mock.assert_not_called()

    def test_answer_returns_rag_mode_for_unknown_question(self):
        """Ensure unmatched intent falls back to RAG with retrieval trace IDs."""
        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "Explain OpRa operational exchange setup sequence.",
                "standardsScope": ["OpRa"],
            },
            format="json",
            HTTP_X_REQUEST_ID="req-rag-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "rag")
        self.assertFalse(response.data["abstained"])
        self.assertTrue(response.data["citations"])
        self.assertTrue(response.data["trace"]["retrievalEventIds"])

        question_event_id = int(response.data["trace"]["questionEventId"])
        self.assertGreaterEqual(
            RetrievalEvent.objects.filter(question_event_id=question_event_id).count(),
            1,
        )
        self.assertGreaterEqual(
            AnswerEvidenceLink.objects.filter(question_event_id=question_event_id).count(),
            1,
        )
        self.assertGreaterEqual(
            EvidenceProvenance.objects.filter(question_event_id=question_event_id).count(),
            1,
        )

    @override_settings(
        GRAPH_RAG_ENABLED=True,
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/repositories/helpdesk",
    )
    def test_answer_includes_graph_trace_when_graph_mode_enabled(self):
        """Ensure graph trace fields are populated when graph mode is requested and enabled."""
        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How are delayed journey statistics represented in OpRa examples?",
                "standardsScope": ["OpRa"],
                "options": {
                    "graphRagEnabled": True,
                    "retrievalTopK": 6,
                    "retrievalMinScore": 0.30,
                },
            },
            format="json",
            HTTP_X_REQUEST_ID="req-rag-graph-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertIn("graphExpansionHops", response.data["trace"])
        self.assertIn("graphConceptIds", response.data["trace"])
        self.assertIn("graphEvidenceCount", response.data["trace"])
        self.assertIn("graphScoreContribution", response.data["trace"])
        self.assertIn("repositoryCoverageCount", response.data["trace"])
        self.assertIn("conceptCoverageCount", response.data["trace"])
        self.assertIn("semanticAlignmentScore", response.data["trace"])
        self.assertIn("provenanceIds", response.data["trace"])
        self.assertIn("ruleHitsCount", response.data["trace"])
        self.assertIn("ruleConclusions", response.data["trace"])
        self.assertIn("ontologyVersions", response.data["trace"])
        self.assertGreaterEqual(response.data["trace"]["graphExpansionHops"], 0)
        self.assertGreaterEqual(response.data["trace"]["graphEvidenceCount"], 0)
        self.assertGreaterEqual(response.data["trace"]["repositoryCoverageCount"], 0)
        self.assertGreaterEqual(response.data["trace"]["conceptCoverageCount"], 0)
        self.assertGreaterEqual(response.data["trace"]["semanticAlignmentScore"], 0.0)

    @patch("helpdesk.api.views.parse_question_to_semantic_query")
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_uses_discovered_scope_and_exposes_semantic_query_trace(self, retrieve_mock, parse_mock):
        """When request scope is missing, semantic parsing provides candidate standards for retrieval."""

        parse_mock.return_value = SimpleNamespace(
            core_concept="nits:journey-pattern",
            ambiguous_core_concept=False,
            candidate_standards=["NeTEx", "OpRa"],
            as_dict=lambda: {
                "intent": "cross_standard_relation",
                "normativity": "unspecified",
                "coreConcept": "nits:journey-pattern",
                "coreConcepts": ["nits:journey-pattern"],
                "ambiguousCoreConcept": False,
                "candidateStandards": ["NeTEx", "OpRa"],
                "originalTerms": ["ServiceJourneyPattern"],
                "confidence": {"intent": 0.9, "concept": 0.95},
            },
        )
        retrieve_mock.return_value = (
            [
                {
                    "text": "ServiceJourneyPattern is aligned with OpRa journey concepts.",
                    "score": 0.84,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "docs/journey-pattern.md",
                    "chunkId": "chunk-1",
                    "label": "Journey Pattern",
                    "retrievalEventId": "re-test-semantic-001",
                }
            ],
            {
                "graphRagVariant": "control",
                "graphExpansionHops": 0,
                "graphExpansionSource": "none",
                "graphConceptIds": [],
                "graphCandidatesAdded": 0,
                "graphEvidenceCount": 0,
                "graphScoreContribution": 0.0,
                "graphProvenanceChainCount": 0,
                "semanticAlignmentScore": 0.73,
                "retrievalLatencyMs": 8.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How does ServiceJourneyPattern relate across standards?",
                "generationProfile": "deterministic-grounded",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-semantic-scope-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(retrieve_mock.call_args.kwargs.get("scope"), ["NeTEx", "OpRa"])
        self.assertEqual(response.data["trace"]["semanticQuery"]["coreConcept"], "nits:journey-pattern")
        self.assertEqual(
            response.data["trace"]["semanticQuery"]["candidateStandards"],
            ["NeTEx", "OpRa"],
        )

    @patch("helpdesk.api.views.parse_question_to_semantic_query")
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_returns_clarification_abstain_when_no_concept_match(self, retrieve_mock, parse_mock):
        """No concept match should trigger clarification abstain without retrieval."""

        parse_mock.return_value = SimpleNamespace(
            core_concept="nits:unknown-concept",
            ambiguous_core_concept=False,
            candidate_standards=[],
            as_dict=lambda: {
                "intent": "unknown",
                "normativity": "unspecified",
                "coreConcept": "nits:unknown-concept",
                "coreConcepts": [],
                "ambiguousCoreConcept": False,
                "candidateStandards": [],
                "originalTerms": ["unmapped"],
                "confidence": {"intent": 0.6, "concept": 0.45},
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {"question": "What is the xyz nonstandard token?"},
            format="json",
            HTTP_X_REQUEST_ID="req-semantic-no-concept-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "abstain")
        self.assertTrue(response.data["abstained"])
        self.assertEqual(response.data["trace"]["semanticFallback"], "NO_CONCEPT_MATCH")
        self.assertFalse(retrieve_mock.called)

    @patch("helpdesk.api.views.parse_question_to_semantic_query")
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_reduces_scope_when_core_concept_is_ambiguous(self, retrieve_mock, parse_mock):
        """Ambiguous core concept should reduce automatic scope to first candidate standard."""

        parse_mock.return_value = SimpleNamespace(
            core_concept="nits:journey-pattern",
            ambiguous_core_concept=True,
            candidate_standards=["NeTEx", "OpRa"],
            as_dict=lambda: {
                "intent": "cross_standard_relation",
                "normativity": "unspecified",
                "coreConcept": "nits:journey-pattern",
                "coreConcepts": ["nits:journey-pattern", "nits:journey-ref"],
                "ambiguousCoreConcept": True,
                "candidateStandards": ["NeTEx", "OpRa"],
                "originalTerms": ["JourneyPattern"],
                "confidence": {"intent": 0.9, "concept": 0.75},
            },
        )
        retrieve_mock.return_value = (
            [
                {
                    "text": "Journey pattern mapping details.",
                    "score": 0.82,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "docs/journey-pattern.md",
                    "chunkId": "chunk-ambiguity-1",
                    "label": "Journey Pattern",
                    "retrievalEventId": "re-test-ambiguity-001",
                }
            ],
            {
                "graphRagVariant": "control",
                "graphExpansionHops": 0,
                "graphExpansionSource": "none",
                "graphConceptIds": [],
                "graphCandidatesAdded": 0,
                "graphEvidenceCount": 0,
                "graphScoreContribution": 0.0,
                "graphProvenanceChainCount": 0,
                "semanticAlignmentScore": 0.7,
                "retrievalLatencyMs": 6.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How does journey pattern align across standards?",
                "generationProfile": "deterministic-grounded",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-semantic-ambiguity-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(retrieve_mock.call_args.kwargs.get("scope"), ["NeTEx"])
        self.assertTrue(response.data["trace"]["semanticDisambiguationRequired"])
        self.assertEqual(response.data["trace"]["semanticFallback"], "AMBIGUOUS_CORE_CONCEPT")

    @patch("helpdesk.api.views.parse_question_to_semantic_query")
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_marks_provisional_trace_for_partial_evidence(self, retrieve_mock, parse_mock):
        """Low-confidence sparse retrieval should be marked as provisional partial evidence."""

        parse_mock.return_value = SimpleNamespace(
            core_concept="nits:journey-pattern",
            ambiguous_core_concept=False,
            candidate_standards=["NeTEx", "OpRa"],
            as_dict=lambda: {
                "intent": "cross_standard_relation",
                "normativity": "unspecified",
                "coreConcept": "nits:journey-pattern",
                "coreConcepts": ["nits:journey-pattern"],
                "ambiguousCoreConcept": False,
                "candidateStandards": ["NeTEx", "OpRa"],
                "originalTerms": ["JourneyPattern"],
                "confidence": {"intent": 0.9, "concept": 0.85},
            },
        )
        retrieve_mock.return_value = (
            [
                {
                    "text": "Sparse chunk mentioning journey pattern once.",
                    "score": 0.58,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "docs/sparse.md",
                    "chunkId": "chunk-partial-1",
                    "label": "Sparse",
                    "retrievalEventId": "re-test-partial-001",
                }
            ],
            {
                "graphRagVariant": "control",
                "graphExpansionHops": 0,
                "graphExpansionSource": "none",
                "graphConceptIds": [],
                "graphCandidatesAdded": 0,
                "graphEvidenceCount": 1,
                "graphScoreContribution": 0.0,
                "graphProvenanceChainCount": 0,
                "repositoryCoverageCount": 1,
                "conceptCoverageCount": 1,
                "semanticAlignmentScore": 0.33,
                "retrievalLatencyMs": 5.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How does journey pattern relate across NeTEx and OpRa?",
                "generationProfile": "deterministic-grounded",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-semantic-partial-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "rag")
        self.assertTrue(response.data["trace"]["semanticProvisional"])
        self.assertEqual(response.data["trace"]["semanticFallback"], "PARTIAL_EVIDENCE")
        self.assertIn(
            response.data["trace"]["semanticProvisionalReason"],
            ["LOW_RETRIEVAL_CONFIDENCE", "LIMITED_EVIDENCE_COVERAGE", "CROSS_STANDARD_GAP"],
        )
        self.assertEqual(response.data["trace"]["evidenceCoverageLevel"], "low")

    @patch("helpdesk.api.views.parse_question_to_semantic_query")
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_reports_cross_standard_conflict_partitions(self, retrieve_mock, parse_mock):
        """Cross-standard normative mismatch should be surfaced in trace partitions."""

        parse_mock.return_value = SimpleNamespace(
            core_concept="nits:journey-pattern",
            ambiguous_core_concept=False,
            candidate_standards=["NeTEx", "OpRa"],
            as_dict=lambda: {
                "intent": "cross_standard_relation",
                "normativity": "unspecified",
                "coreConcept": "nits:journey-pattern",
                "coreConcepts": ["nits:journey-pattern"],
                "ambiguousCoreConcept": False,
                "candidateStandards": ["NeTEx", "OpRa"],
                "originalTerms": ["JourneyPattern"],
                "confidence": {"intent": 0.9, "concept": 0.9},
            },
        )
        retrieve_mock.return_value = (
            [
                {
                    "text": "NeTEx SHALL provide journey pattern exchange details.",
                    "score": 0.84,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "docs/netex-journey.md",
                    "chunkId": "chunk-conflict-1",
                    "label": "NeTEx Journey",
                    "retrievalEventId": "re-test-conflict-001",
                    "standardsScope": ["NeTEx"],
                },
                {
                    "text": "OpRa MAY exchange delayed journey reporting as optional extensions.",
                    "score": 0.81,
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "def456",
                    "sourcePath": "docs/opra-delay.md",
                    "chunkId": "chunk-conflict-2",
                    "label": "OpRa Delay",
                    "retrievalEventId": "re-test-conflict-002",
                    "standardsScope": ["OpRa"],
                },
            ],
            {
                "graphRagVariant": "control",
                "graphExpansionHops": 0,
                "graphExpansionSource": "none",
                "graphConceptIds": [],
                "graphCandidatesAdded": 0,
                "graphEvidenceCount": 2,
                "graphScoreContribution": 0.0,
                "graphProvenanceChainCount": 0,
                "repositoryCoverageCount": 2,
                "conceptCoverageCount": 1,
                "semanticAlignmentScore": 0.72,
                "retrievalLatencyMs": 6.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How do NeTEx and OpRa differ for journey pattern exchange?",
                "generationProfile": "deterministic-grounded",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-cross-conflict-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertTrue(response.data["trace"]["crossStandardConflict"])
        self.assertEqual(
            response.data["trace"]["crossStandardConflictType"],
            "NORMATIVE_STRENGTH_MISMATCH",
        )
        self.assertEqual(len(response.data["trace"]["crossStandardEvidencePartitions"]), 2)

    @override_settings(
        EVIDENCE_GATE_ENABLED=True,
        EVIDENCE_GATE_MIN_ALIGNMENT=0.6,
        EVIDENCE_GATE_MIN_CHUNKS=1,
        EVIDENCE_GATE_MIN_REPOSITORIES_MULTI_SCOPE=2,
    )
    @patch("helpdesk.api.views.parse_question_to_semantic_query")
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_abstains_when_evidence_gate_rejects_low_alignment(self, retrieve_mock, parse_mock):
        """Generic evidence gate should force abstention when alignment is too low."""

        parse_mock.return_value = SimpleNamespace(
            core_concept="nits:journey-pattern",
            ambiguous_core_concept=False,
            candidate_standards=["NeTEx"],
            confidence={"intent": 0.9, "concept": 0.95},
            as_dict=lambda: {
                "intent": "cross_standard_relation",
                "normativity": "unspecified",
                "coreConcept": "nits:journey-pattern",
                "coreConcepts": ["nits:journey-pattern"],
                "ambiguousCoreConcept": False,
                "candidateStandards": ["NeTEx"],
                "originalTerms": ["JourneyPattern"],
                "confidence": {"intent": 0.9, "concept": 0.95},
            },
        )
        retrieve_mock.return_value = (
            [
                {
                    "text": "Sparse mention with weak semantic match.",
                    "score": 0.81,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "abc123",
                    "sourcePath": "docs/weak.md",
                    "chunkId": "chunk-gate-1",
                    "label": "Weak",
                    "retrievalEventId": "re-test-gate-001",
                    "standardsScope": ["NeTEx"],
                }
            ],
            {
                "graphRagVariant": "control",
                "graphExpansionHops": 0,
                "graphExpansionSource": "none",
                "graphConceptIds": [],
                "graphCandidatesAdded": 0,
                "graphEvidenceCount": 1,
                "graphScoreContribution": 0.0,
                "graphProvenanceChainCount": 0,
                "repositoryCoverageCount": 1,
                "conceptCoverageCount": 1,
                "semanticAlignmentScore": 0.22,
                "retrievalLatencyMs": 5.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How does journey pattern map?",
                "generationProfile": "deterministic-grounded",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-evidence-gate-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "abstain")
        self.assertTrue(response.data["abstained"])
        self.assertEqual(response.data["trace"]["semanticFallback"], "PARTIAL_EVIDENCE")

    @override_settings(
        GRAPH_RAG_ENABLED=True,
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/repositories/helpdesk",
    )
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_uses_graph_when_enabled_and_option_omitted(self, retrieve_mock):
        """Graph retrieval runs whenever GRAPH_RAG_ENABLED=True, regardless of request options."""
        retrieve_mock.return_value = (
            [
                {
                    "text": "Delayed journey statistics are represented in OpRa examples.",
                    "score": 0.82,
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "abc123",
                    "sourcePath": "examples/DelayedAndCancelledJourneysWithEvents.xml",
                    "chunkId": "chunk-opra-1",
                    "label": "DelayedAndCancelledJourneysWithEvents.xml",
                    "retrievalEventId": "re-test-001",
                }
            ],
            {
                "graphRagVariant": "graph-rag",
                "graphExpansionHops": 1,
                "graphExpansionSource": "memory",
                "graphConceptIds": ["opra:delayed-journey"],
                "graphCandidatesAdded": 1,
                "graphEvidenceCount": 1,
                "graphScoreContribution": 0.2,
                "graphProvenanceChainCount": 1,
                "semanticAlignmentScore": 0.72,
                "retrievalLatencyMs": 12.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How are delayed journey statistics represented in OpRa examples?",
                "standardsScope": ["OpRa"],
                "options": {
                    "retrievalTopK": 6,
                    "retrievalMinScore": 0.30,
                },
            },
            format="json",
            HTTP_X_REQUEST_ID="req-rag-graph-variant-default-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertTrue(retrieve_mock.called)
        self.assertTrue(retrieve_mock.call_args.kwargs.get("graph_rag_enabled"))

    @override_settings(
        GRAPH_RAG_ENABLED=True,
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://graphdb.local/repositories/helpdesk",
    )
    @patch("helpdesk.api.views.retrieve_chunks_with_trace")
    def test_answer_ignores_explicit_graph_opt_out_when_enabled(self, retrieve_mock):
        """graphRagEnabled=false in request options is ignored — graph runs unconditionally when GRAPH_RAG_ENABLED=True."""
        retrieve_mock.return_value = (
            [
                {
                    "text": "Delayed journey statistics are represented in OpRa examples.",
                    "score": 0.82,
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "abc123",
                    "sourcePath": "examples/DelayedAndCancelledJourneysWithEvents.xml",
                    "chunkId": "chunk-opra-2",
                    "label": "DelayedAndCancelledJourneysWithEvents.xml",
                    "retrievalEventId": "re-test-002",
                }
            ],
            {
                "graphRagVariant": "control",
                "graphExpansionHops": 0,
                "graphExpansionSource": "none",
                "graphConceptIds": [],
                "graphCandidatesAdded": 0,
                "graphEvidenceCount": 0,
                "graphScoreContribution": 0.0,
                "graphProvenanceChainCount": 0,
                "semanticAlignmentScore": 0.65,
                "retrievalLatencyMs": 8.0,
            },
        )

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How are delayed journey statistics represented in OpRa examples?",
                "standardsScope": ["OpRa"],
                "options": {
                    "graphRagEnabled": False,
                    "retrievalTopK": 6,
                    "retrievalMinScore": 0.30,
                },
            },
            format="json",
            HTTP_X_REQUEST_ID="req-rag-graph-variant-optout-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertTrue(retrieve_mock.called)
        # graphRagEnabled:false must be ignored; graph is always active with GRAPH_RAG_ENABLED=True
        self.assertTrue(retrieve_mock.call_args.kwargs.get("graph_rag_enabled"))

    @override_settings(GRAPH_RAG_ENABLED=True, GRAPHDB_ENABLED=False, GRAPHDB_SPARQL_ENDPOINT="")
    def test_answer_rejects_graph_runtime_without_graphdb_configuration(self):
        with self.assertRaises(ImproperlyConfigured):
            self.client.post(
                reverse("answer-question"),
                {
                    "question": "How are delayed journey statistics represented in OpRa examples?",
                    "standardsScope": ["OpRa"],
                },
                format="json",
                HTTP_X_REQUEST_ID="req-rag-graph-misconfigured-001",
                **self.auth_headers(),
            )

    def test_select_citations_deduplicates_and_prefers_cross_repository_coverage(self):
        """Ensure citation selection mixes top evidence across repositories before filling extras."""
        citations = _select_citations(
            chunks=[
                {
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "1727ab3",
                    "sourcePath": "README.md",
                    "chunkId": "chunk-a",
                    "label": "README.md",
                    "score": 0.84,
                },
                {
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "3734861",
                    "sourcePath": "docs/ef-explicit-frame-hierarchy-model-summary.md",
                    "chunkId": "chunk-b",
                    "label": "docs/ef-explicit-frame-hierarchy-model-summary.md",
                    "score": 0.82,
                },
                {
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "3734861",
                    "sourcePath": "README.md",
                    "chunkId": "chunk-c",
                    "label": "README.md",
                    "score": 0.81,
                },
                {
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "3734861",
                    "sourcePath": "docs/ef-explicit-frame-hierarchy-model-summary.md",
                    "chunkId": "chunk-d",
                    "label": "docs/ef-explicit-frame-hierarchy-model-summary.md",
                    "score": 0.79,
                },
            ],
            max_citations=3,
        )

        self.assertEqual(len(citations), 3)
        self.assertEqual(citations[0]["sourcePath"], "docs/ef-explicit-frame-hierarchy-model-summary.md")
        self.assertEqual(citations[0]["commitSha"], "3734861")
        self.assertEqual(sum(1 for item in citations if item["sourcePath"] == "docs/ef-explicit-frame-hierarchy-model-summary.md"), 1)
        citation_repositories = {
            item["repositoryUrl"].split("/blob/")[0] if "/blob/" in item["repositoryUrl"] else item["repositoryUrl"]
            for item in citations
        }
        self.assertIn("https://github.com/OpRa-CEN/OpRa", citation_repositories)
        self.assertIn("https://github.com/TransmodelEcosystem/NeTEx", citation_repositories)

    def test_rewrite_source_paths_as_evidence_markers(self):
        answer = (
            "Based on retrieved approved-source evidence (for example: "
            "examples/functions/line/NeTEx_01_simple_line.xml, "
            "examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml), "
            "follow the profile guidance."
        )
        citations = [
            {
                "sourcePath": "examples/functions/line/NeTEx_01_simple_line.xml",
            },
            {
                "sourcePath": "examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml",
            },
        ]

        rewritten = _rewrite_source_paths_as_evidence_markers(answer_text=answer, citations=citations)

        self.assertIn("[E1]", rewritten)
        self.assertIn("[E2]", rewritten)
        self.assertNotIn("examples/functions/line/NeTEx_01_simple_line.xml", rewritten)
        self.assertNotIn("examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml", rewritten)

    @patch("helpdesk.api.views._resolve_commit_sha", return_value="3734861abcdef0123456789abcdef012345678")
    def test_build_file_url_expands_short_commit_sha(self, resolve_commit_sha_mock):
        """Ensure citation URLs use an expanded commit SHA when available."""
        url = _build_file_url(
            repo_url="https://github.com/OpRa-CEN/OpRa",
            commit_sha="3734861",
            source_path="docs/ef-explicit-frame-hierarchy-model-summary.md",
        )

        self.assertEqual(
            url,
            "https://github.com/OpRa-CEN/OpRa/blob/3734861abcdef0123456789abcdef012345678/docs/ef-explicit-frame-hierarchy-model-summary.md",
        )
        resolve_commit_sha_mock.assert_called_once_with(
            repo_url="https://github.com/OpRa-CEN/OpRa",
            commit_sha="3734861",
        )

    def test_build_file_url_maps_issue_path_to_issue_url(self):
        """Ensure synthetic indexed issue paths link to the actual GitHub issue page."""
        url = _build_file_url(
            repo_url="https://github.com/TransmodelEcosystem/NeTEx",
            commit_sha="2024-03-22T12:07:32Z",
            source_path="issues/691.md",
        )

        self.assertEqual(url, "https://github.com/TransmodelEcosystem/NeTEx/issues/691")

    @patch("helpdesk.api.views._resolve_commit_sha", return_value="unknown")
    @patch("helpdesk.api.views._resolve_repository_ref", return_value="")
    def test_build_file_url_uses_tree_ref_when_commit_is_unknown_for_transmodel_netex(
        self, resolve_repository_ref_mock, resolve_commit_sha_mock
    ):
        """Ensure unknown commit refs for Transmodel NeTEx cite canonical v2.0 blob paths."""
        url = _build_file_url(
            repo_url="https://github.com/TransmodelEcosystem/NeTEx",
            commit_sha="unknown",
            source_path="examples/functions/line/NeTEx_01_simple_line.xml",
        )

        self.assertEqual(
            url,
            "https://github.com/TransmodelEcosystem/NeTEx/blob/v2.0/examples/functions/line/NeTEx_01_simple_line.xml",
        )
        resolve_commit_sha_mock.assert_called_once_with(
            repo_url="https://github.com/TransmodelEcosystem/NeTEx",
            commit_sha="unknown",
        )
        resolve_repository_ref_mock.assert_called_once_with(repo_url="https://github.com/TransmodelEcosystem/NeTEx")

    @patch("helpdesk.api.views._resolve_commit_sha", return_value="unknown")
    @patch("helpdesk.api.views._resolve_repository_ref", return_value="")
    def test_build_file_url_uses_tree_ref_when_commit_is_unknown_for_netex_cen(
        self, resolve_repository_ref_mock, resolve_commit_sha_mock
    ):
        """Ensure unknown commit refs for NeTEx-CEN normalize to canonical v2.0 blob paths."""
        url = _build_file_url(
            repo_url="https://github.com/NeTEx-CEN/NeTEx",
            commit_sha="unknown",
            source_path="examples/functions/line/NeTEx_01_simple_line.xml",
        )

        self.assertEqual(
            url,
            "https://github.com/TransmodelEcosystem/NeTEx/blob/v2.0/examples/functions/line/NeTEx_01_simple_line.xml",
        )
        resolve_commit_sha_mock.assert_called_once_with(
            repo_url="https://github.com/NeTEx-CEN/NeTEx",
            commit_sha="unknown",
        )
        resolve_repository_ref_mock.assert_called_once_with(repo_url="https://github.com/NeTEx-CEN/NeTEx")

    @patch("helpdesk.api.views._resolve_commit_sha", return_value="unknown")
    @patch("helpdesk.api.views._resolve_repository_ref", return_value="")
    def test_build_file_url_uses_tree_ref_when_commit_is_unknown_for_opra(self, resolve_repository_ref_mock, resolve_commit_sha_mock):
        """Ensure unknown commit refs for OpRa use the stable 1.0rc tag."""
        url = _build_file_url(
            repo_url="https://github.com/OpRa-CEN/OpRa",
            commit_sha="unknown",
            source_path="examples/CancelledAndLateDatedVehicleJourneys.xml",
        )

        self.assertEqual(
            url,
            "https://github.com/OpRa-CEN/OpRa/blob/1.0rc/examples/CancelledAndLateDatedVehicleJourneys.xml",
        )
        resolve_commit_sha_mock.assert_called_once_with(
            repo_url="https://github.com/OpRa-CEN/OpRa",
            commit_sha="unknown",
        )
        resolve_repository_ref_mock.assert_called_once_with(repo_url="https://github.com/OpRa-CEN/OpRa")

    @patch("helpdesk.api.views._resolve_commit_sha", return_value="unknown")
    @patch("helpdesk.api.views._resolve_repository_ref", return_value="")
    def test_build_file_url_uses_main_when_unknown_and_repo_unmapped(self, resolve_repository_ref_mock, resolve_commit_sha_mock):
        """Ensure unknown refs on unmapped repositories avoid blob/unknown links."""
        url = _build_file_url(
            repo_url="https://github.com/example-org/example-repo",
            commit_sha="unknown",
            source_path="docs/spec.md",
        )

        self.assertEqual(url, "https://github.com/example-org/example-repo/blob/main/docs/spec.md")
        resolve_commit_sha_mock.assert_called_once_with(
            repo_url="https://github.com/example-org/example-repo",
            commit_sha="unknown",
        )
        resolve_repository_ref_mock.assert_called_once_with(repo_url="https://github.com/example-org/example-repo")

    @override_settings(LLM_ENABLED=True)
    @patch("helpdesk.api.views.generate_answer_llm")
    def test_answer_uses_llm_ready_profile_when_enabled(self, llm_mock):
        """Ensure llm-ready profile uses LLM generator when feature flag is enabled."""

        llm_mock.return_value = {
            "answer": "LLM grounded answer with [E1] citation marker.",
            "confidence": 0.88,
            "review_required": False,
            "provider": "openai-compatible",
            "model": "gpt-4o-mini",
        }

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "Explain OpRa operational exchange setup sequence.",
                "standardsScope": ["OpRa"],
                "generationProfile": "llm-ready",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-llm-ready-001",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "rag")
        self.assertIn("LLM grounded answer", response.data["answer"])
        self.assertTrue(llm_mock.called)

    @override_settings(LLM_ENABLED=True)
    @patch("helpdesk.api.views.generate_answer")
    @patch("helpdesk.api.views.generate_answer_llm")
    def test_answer_falls_back_to_deterministic_when_llm_errors(self, llm_mock, deterministic_mock):
        """Ensure llm-ready path gracefully falls back when LLM provider fails."""

        llm_mock.side_effect = LLMGenerationError("timeout")
        deterministic_mock.return_value = {
            "answer": "Deterministic fallback answer.",
            "confidence": 0.77,
            "review_required": True,
        }

        with self.assertLogs("helpdesk.api.views", level="WARNING") as logs:
            response = self.client.post(
                reverse("answer-question"),
                {
                    "question": "Explain OpRa operational exchange setup sequence.",
                    "standardsScope": ["OpRa"],
                    "generationProfile": "llm-ready",
                },
                format="json",
                HTTP_X_REQUEST_ID="req-llm-fallback-001",
                **self.auth_headers(),
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertEqual(response.data["mode"], "rag")
        self.assertEqual(response.data["answer"], "Deterministic fallback answer. [E1]")
        self.assertTrue(llm_mock.called)
        self.assertTrue(deterministic_mock.called)
        self.assertTrue(any("LLM generation failed; falling back to deterministic answer" in line for line in logs.output))

    def test_promotion_candidates_returns_aggregated_items(self):
        """Ensure repeated questions aggregate into promotion candidates."""
        for index in range(2):
            self.client.post(
                reverse("answer-question"),
                {"question": "How to use NeTEx for exchanging a timetable?"},
                format="json",
                HTTP_X_REQUEST_ID=f"req-prom-{index}",
                **self.auth_headers(),
            )

        response = self.client.get(
            reverse("promotion-candidates"),
            {"windowDays": 30, "minCount": 1},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("PromotionCandidatesResponse", response.data)
        self.assertEqual(response.data["windowDays"], 30)
        self.assertEqual(response.data["minCount"], 1)
        self.assertGreaterEqual(len(response.data["items"]), 1)

    @patch("helpdesk.services.semantic_clustering.build_text_embeddings_batch")
    def test_editorial_semantic_clusters_groups_paraphrases(self, embedding_batch_mock):
        """Semantic clustering should group related questions and keep outliers as singleton events."""
        now = timezone.now()
        questions = [
            "How do I reset my password?",
            "I forgot my login password",
            "Need account password help",
            "How to export NeTEx line timetable?",
        ]
        for index, question in enumerate(questions):
            event = QuestionEvent.objects.create(
                request_id=f"req-sc-{index}",
                question=question,
                mode="rag",
                confidence=0.5,
                answer="placeholder",
            )
            QuestionEvent.objects.filter(pk=event.pk).update(created_at=now - dt.timedelta(minutes=index))

        embedding_batch_mock.return_value = [
            [1.0, 0.0, 0.0],
            [0.96, 0.04, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
        ]

        response = self.client.get(
            reverse("editorial-semantic-clusters"),
            {
                "windowDays": 30,
                "minClusterSize": 2,
                "similarityThreshold": 0.8,
                "maxEvents": 50,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("EditorialSemanticClustersResponse", response.data)
        self.assertEqual(response.data["totalEvents"], 4)
        self.assertEqual(response.data["clusteredEvents"], 3)
        self.assertEqual(response.data["singletonEvents"], 1)
        self.assertEqual(len(response.data["clusters"]), 1)
        self.assertEqual(response.data["clusters"][0]["memberCount"], 3)
        self.assertIn("keywordAggregation", response.data["clusters"][0])
        self.assertIn("topKeywords", response.data["clusters"][0]["keywordAggregation"])

    def test_answer_feedback_persists_success_and_citation_click_signals(self):
        """Feedback endpoint should persist answer-success and citation-click telemetry."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "How to use NeTEx for exchanging a timetable?"},
            format="json",
            HTTP_X_REQUEST_ID="req-feedback-extended-source",
            **self.auth_headers(),
        )
        request_id = answer_response.data["trace"]["requestId"]

        response = self.client.post(
            reverse("answer-feedback"),
            {
                "requestId": request_id,
                "userLikes": True,
                "userDislikes": False,
                "answerSuccess": True,
                "citationClicksDelta": 2,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerFeedbackResponse", response.data)
        self.assertTrue(response.data["userLikes"])
        self.assertFalse(response.data["userDislikes"])
        self.assertTrue(response.data["answerSuccess"])
        self.assertEqual(response.data["citationClickCount"], 2)

        metrics_response = self.client.get(
            reverse("editorial-queue-metrics"),
            {"windowDays": 30, "slaHours": 72},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(metrics_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(metrics_response.data["feedbackWindow"]["answerSuccess"], 1)
        self.assertGreaterEqual(metrics_response.data["feedbackWindow"]["citationClicks"], 2)

    def test_answer_does_not_use_faq_for_single_keyword_overlap(self):
        """Ensure FAQ-first does not trigger on weak single-token overlap like only 'NeTEx'."""

        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "How should NeTEx stop assignments be modeled for complex interchanges?",
                "standardsScope": ["NeTEx"],
            },
            format="json",
            HTTP_X_REQUEST_ID="req-faq-single-token-overlap",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("AnswerResponse", response.data)
        self.assertNotEqual(response.data["mode"], "faq")

    def test_editorial_queue_routes_policy_review_to_review_status(self):
        """Ensure policy-review reasons route queue items directly to review status."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-editorial-source",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "POLICY_REVIEW",
                "priority": "high",
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_matches_schema("EditorialQueueResponse", response.data)
        self.assertTrue(response.data["queued"])
        self.assertEqual(response.data["status"], "review")
        self.assertTrue(response.data["queueItemId"])

    def test_editorial_transition_rejects_missing_role(self):
        """Ensure transition requests fail when caller lacks required workflow role."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-transition-source-1",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        queue_response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        transition_response = self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "submit_for_review",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-forbidden",
            **self.auth_headers(roles=["viewer"]),
        )

        self.assertEqual(transition_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assert_matches_schema("ErrorResponse", transition_response.data)
        self.assertEqual(transition_response.data["error"]["code"], "TRANSITION_FORBIDDEN")

    def test_editorial_transition_allows_valid_roles_and_records_audit(self):
        """Ensure valid role-based transitions update state and persist audit entries."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-transition-source-2",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        queue_response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        submit_response = self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "submit_for_review",
                "comment": "Ready for reviewer pass",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-submit",
            **self.auth_headers(roles=["editor"]),
        )
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(submit_response.data["status"], "review")

        approve_response = self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "approve",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-approve",
            **self.auth_headers(roles=["reviewer"]),
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_response.data["status"], "approved")

        publish_response = self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "publish",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-publish",
            **self.auth_headers(roles=["publisher"]),
        )
        self.assertEqual(publish_response.status_code, status.HTTP_200_OK)
        self.assertEqual(publish_response.data["status"], "published")

        self.assertEqual(
            EditorialQueueTransition.objects.filter(
                queue_item__queue_item_id=queue_response.data["queueItemId"]
            ).count(),
            3,
        )

    def test_editorial_publish_persists_faq_for_future_reuse(self):
        """Ensure publish transition stores a FAQ version from the approved answer."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "How should NeTEx timetable frames be prepared for exchange?"},
            format="json",
            HTTP_X_REQUEST_ID="req-transition-source-faq-publish",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]
        answer_text = answer_response.data["answer"]

        queue_response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "submit_for_review",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-faq-submit",
            **self.auth_headers(roles=["editor"]),
        )
        self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "approve",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-faq-approve",
            **self.auth_headers(roles=["reviewer"]),
        )
        publish_response = self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "publish",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-faq-publish",
            **self.auth_headers(roles=["publisher"]),
        )

        self.assertEqual(publish_response.status_code, status.HTTP_200_OK)
        self.assertEqual(publish_response.data["status"], "published")

        published_version = FAQVersion.objects.filter(answer=answer_text, is_published=True).order_by("-id").first()
        self.assertIsNotNone(published_version)
        self.assertTrue(published_version.faq_entry.is_active)
        self.assertIsInstance(published_version.citations, list)
        self.assertGreaterEqual(len(published_version.faq_entry.keyword_tokens), 1)
        self.assertGreaterEqual(FAQEntry.objects.filter(faq_entry_id=published_version.faq_entry.faq_entry_id).count(), 1)

    def test_editorial_transition_rejects_invalid_state_change(self):
        """Ensure impossible transitions return conflict instead of mutating state."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-transition-source-3",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        queue_response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        invalid_response = self.client.post(
            reverse("editorial-queue-transition"),
            {
                "queueItemId": queue_response.data["queueItemId"],
                "action": "publish",
            },
            format="json",
            HTTP_X_REQUEST_ID="req-transition-invalid",
            **self.auth_headers(roles=["publisher"]),
        )

        self.assertEqual(invalid_response.status_code, status.HTTP_409_CONFLICT)
        self.assert_matches_schema("ErrorResponse", invalid_response.data)
        self.assertEqual(invalid_response.data["error"]["code"], "INVALID_STATE_TRANSITION")

    def test_editorial_queue_list_returns_board_items_with_filters(self):
        """Ensure editorial board endpoint returns paginated queue rows and supports filters."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-board-source-1",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "POLICY_REVIEW",
                "priority": "high",
            },
            format="json",
            **self.auth_headers(),
        )

        response = self.client.get(
            reverse("editorial-queue"),
            {
                "status": "review",
                "priority": "high",
                "search": "operational exchange",
                "page": 1,
                "pageSize": 10,
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pageSize"], 10)
        self.assertGreaterEqual(response.data["total"], 1)
        self.assertGreaterEqual(len(response.data["items"]), 1)
        first = response.data["items"][0]
        self.assertEqual(first["status"], "review")
        self.assertEqual(first["priority"], "high")
        self.assertIn("question", first)
        self.assertIn("queueItemId", first)

    def test_editorial_queue_list_includes_role_based_allowed_actions(self):
        """Ensure board rows expose only actions permitted for the caller's roles."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-board-source-roles",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        editor_response = self.client.get(
            reverse("editorial-queue"),
            {"status": "draft", "page": 1, "pageSize": 10},
            format="json",
            **self.auth_headers(roles=["editor"]),
        )
        self.assertEqual(editor_response.status_code, status.HTTP_200_OK)
        self.assertIn("editor", editor_response.data["actorRoles"])
        self.assertGreaterEqual(len(editor_response.data["items"]), 1)
        self.assertEqual(
            editor_response.data["items"][0]["allowedActions"],
            ["submit_for_review"],
        )

        viewer_response = self.client.get(
            reverse("editorial-queue"),
            {"status": "draft", "page": 1, "pageSize": 10},
            format="json",
            **self.auth_headers(roles=["viewer"]),
        )
        self.assertEqual(viewer_response.status_code, status.HTTP_200_OK)
        self.assertEqual(viewer_response.data["items"][0]["allowedActions"], [])

    def test_editorial_queue_metrics_returns_kpi_distributions_and_aging(self):
        """Ensure board metrics endpoint returns status and aging aggregates."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OpRa operational exchange setup sequence."},
            format="json",
            HTTP_X_REQUEST_ID="req-metrics-source-1",
            **self.auth_headers(),
        )
        question_event_id = answer_response.data["trace"]["questionEventId"]

        draft_response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "LOW_CONFIDENCE",
                "priority": "normal",
            },
            format="json",
            **self.auth_headers(),
        )

        review_response = self.client.post(
            reverse("editorial-queue"),
            {
                "questionEventId": question_event_id,
                "reason": "POLICY_REVIEW",
                "priority": "high",
            },
            format="json",
            **self.auth_headers(),
        )

        # Force one item older than SLA threshold to validate overdue and aging counts.
        EditorialQueueItem.objects.filter(queue_item_id=draft_response.data["queueItemId"]).update(
            created_at=timezone.now() - dt.timedelta(hours=80)
        )
        EditorialQueueItem.objects.filter(queue_item_id=review_response.data["queueItemId"]).update(
            created_at=timezone.now() - dt.timedelta(hours=10)
        )

        response = self.client.get(
            reverse("editorial-queue-metrics"),
            {"windowDays": 30, "slaHours": 72},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["windowDays"], 30)
        self.assertEqual(response.data["slaHours"], 72)
        self.assertGreaterEqual(response.data["totalItems"], 2)
        self.assertGreaterEqual(response.data["unresolvedItems"], 2)
        self.assertGreaterEqual(response.data["overdueItems"], 1)
        self.assertGreaterEqual(response.data["byStatus"]["draft"], 1)
        self.assertGreaterEqual(response.data["byStatus"]["review"], 1)
        self.assertGreaterEqual(response.data["byPriority"]["high"], 1)
        self.assertGreaterEqual(response.data["byReason"]["POLICY_REVIEW"], 1)
        self.assertGreaterEqual(response.data["agingBuckets"]["gt72h"], 1)
