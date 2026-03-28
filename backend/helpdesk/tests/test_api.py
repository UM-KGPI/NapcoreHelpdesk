from __future__ import annotations

import datetime as dt
import json
import copy
from pathlib import Path

import jwt
import yaml
from django.conf import settings
from django.urls import reverse
from jsonschema import Draft202012Validator, RefResolver
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase

from helpdesk.api.exceptions import custom_exception_handler
from helpdesk.models import (
    AnswerEvidenceLink,
    EditorialQueueTransition,
    FAQVersion,
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

    def test_answer_returns_rag_mode_for_unknown_question(self):
        """Ensure unmatched intent falls back to RAG with retrieval trace IDs."""
        response = self.client.post(
            reverse("answer-question"),
            {
                "question": "Explain OJP operational exchange setup sequence.",
                "standardsScope": ["OJP/OpRa"],
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

    def test_editorial_queue_routes_policy_review_to_review_status(self):
        """Ensure policy-review reasons route queue items directly to review status."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OJP operational exchange setup sequence."},
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
            {"question": "Explain OJP operational exchange setup sequence."},
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
            {"question": "Explain OJP operational exchange setup sequence."},
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

    def test_editorial_transition_rejects_invalid_state_change(self):
        """Ensure impossible transitions return conflict instead of mutating state."""
        answer_response = self.client.post(
            reverse("answer-question"),
            {"question": "Explain OJP operational exchange setup sequence."},
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
            {"question": "Explain OJP operational exchange setup sequence."},
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
            {"question": "Explain OJP operational exchange setup sequence."},
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
