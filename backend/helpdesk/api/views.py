from collections import defaultdict
import datetime as dt
from datetime import timedelta
from uuid import uuid4

import jwt
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from helpdesk.models import EditorialQueueItem, QuestionEvent
from helpdesk.services.editorial_router import route_to_editorial_queue
from helpdesk.services.editorial_workflow import (
    WorkflowTransitionForbidden,
    WorkflowTransitionNotAllowed,
    allowed_actions_for_status,
    apply_transition,
)
from helpdesk.services.evidence_mapper import map_evidence
from helpdesk.services.event_logger import log_question_event
from helpdesk.services.faq_matcher import match_faq
from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.llm_generator import LLMGenerationError, generate_answer_llm
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.retrieval_gateway import retrieve_chunks
from helpdesk.services.retrieval_event_logger import log_retrieval_events

from .serializers import (
    AnswerRequestSerializer,
    EditorialQueueListQuerySerializer,
    EditorialQueueMetricsQuerySerializer,
    EditorialQueueRequestSerializer,
    EditorialQueueTransitionRequestSerializer,
    PromotionCandidatesQuerySerializer,
)


def _request_id(request):
    # Keep a stable correlation ID for traceability in logs, DB events, and error payloads.
    return request.headers.get("X-Request-Id") or f"req-{uuid4().hex[:12]}"


def _build_file_url(repo_url: str, commit_sha: str, source_path: str) -> str:
    """Construct a direct GitHub file URL pointing to the exact blob at a commit."""
    # Remove trailing .git if present, normalize the repo URL.
    repo_url = repo_url.rstrip("/").rstrip(".git")
    # Build the GitHub blob URL: https://github.com/OWNER/REPO/blob/COMMIT/PATH
    return f"{repo_url}/blob/{commit_sha}/{source_path}"



def _error_response(code, message, request_id, http_status=status.HTTP_400_BAD_REQUEST):
    # Central helper to preserve the OpenAPI ErrorResponse contract shape.
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
            }
        },
        status=http_status,
    )


def _request_roles(request):
    """Extract normalized role set from JWT claims plus local admin fallback."""

    roles = set()
    token = request.auth if isinstance(request.auth, dict) else {}

    role = token.get("role")
    if isinstance(role, str) and role.strip():
        roles.add(role.strip().lower())

    token_roles = token.get("roles", [])
    if isinstance(token_roles, str):
        token_roles = [token_roles]
    if isinstance(token_roles, list):
        for item in token_roles:
            if isinstance(item, str) and item.strip():
                roles.add(item.strip().lower())

    user = getattr(request, "user", None)
    if user and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
        roles.add("admin")

    return roles


def _request_actor_id(request):
    """Resolve actor identifier used in transition audit entries."""

    token = request.auth if isinstance(request.auth, dict) else {}
    subject = token.get("sub")
    if isinstance(subject, str) and subject.strip():
        return subject.strip()
    user = getattr(request, "user", None)
    username = getattr(user, "username", "") if user else ""
    return username or "unknown"


class HealthLiveView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Liveness reflects process availability without dependency checks.
        return Response(
            {
                "status": "ok",
                "service": "napcore-helpdesk",
                "check": "live",
            },
            status=status.HTTP_200_OK,
        )


class HealthReadyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Readiness requires successful DB connectivity before accepting traffic.
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response(
                {
                    "status": "degraded",
                    "service": "napcore-helpdesk",
                    "check": "ready",
                    "database": "unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "ok",
                "service": "napcore-helpdesk",
                "check": "ready",
                "database": "ok",
            },
            status=status.HTTP_200_OK,
        )


class DevTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Dev convenience endpoint to avoid manual token copy/paste after page reload.
        if not (settings.DEBUG and settings.DEV_JWT_AUTO_ISSUE):
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Dev token endpoint is disabled.",
                        "requestId": _request_id(request),
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "sub": settings.DEV_JWT_DEFAULT_SUBJECT,
            "roles": settings.DEV_JWT_DEFAULT_ROLES,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(minutes=settings.DEV_JWT_TTL_MINUTES)).timestamp()),
        }
        if settings.JWT_ISSUER:
            payload["iss"] = settings.JWT_ISSUER
        if settings.JWT_AUDIENCE:
            payload["aud"] = settings.JWT_AUDIENCE

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return Response(
            {
                "token": token,
                "tokenType": "Bearer",
                "expiresInSeconds": settings.DEV_JWT_TTL_MINUTES * 60,
                "subject": payload["sub"],
                "roles": payload["roles"],
            },
            status=status.HTTP_200_OK,
        )


class QuestionAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # This endpoint enforces explicit request IDs for end-to-end traceability.
        request_id = _request_id(request)
        if "X-Request-Id" not in request.headers:
            return _error_response(
                code="MISSING_HEADER",
                message="X-Request-Id header is required.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        options = data.get("options", {})
        question = data["question"].strip()
        scope = data.get("standardsScope", [])
        generation_profile = data.get("generationProfile", "deterministic-grounded")
        allow_abstain = options.get("allowAbstain", True)
        faq_min_confidence = options.get("faqMinConfidence", 0.85)
        max_citations = options.get("maxCitations", 5)
        retrieval_top_k = options.get("retrievalTopK", 6)
        retrieval_min_score = options.get("retrievalMinScore", 0.62)

        mode = QuestionEvent.MODE_RAG
        confidence = 0.0
        abstained = False
        abstention_reason = None
        review_required = True
        matched_faq_entry_id = None
        retrieval_event_ids = []
        evidence_link_ids = []
        citations = []
        retrieved_chunks = []

        # 1) FAQ-first: fast, deterministic, and usually high confidence.
        faq_match = match_faq(question=question, scope=scope)
        if faq_match and faq_match["confidence"] >= faq_min_confidence and faq_match.get("scope_match", True):
            mode = QuestionEvent.MODE_FAQ
            confidence = faq_match["confidence"]
            review_required = faq_match["review_required"]
            matched_faq_entry_id = faq_match["faq_entry_id"]
            answer_text = faq_match["answer"]
            citations = faq_match["citations"][:max_citations]
        else:
            # 2) RAG fallback: retrieve evidence, generate, then run policy gate.
            chunks = retrieve_chunks(
                question=question,
                top_k=retrieval_top_k,
                min_score=retrieval_min_score,
                scope=scope,
            )
            retrieved_chunks = chunks
            retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]

            if not chunks and allow_abstain:
                # Abstain if we cannot provide grounded evidence safely.
                mode = QuestionEvent.MODE_ABSTAIN
                confidence = 0.0
                abstained = True
                abstention_reason = QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
                review_required = False
                answer_text = "I do not have sufficient approved-source evidence to answer this safely."
            else:
                use_llm = generation_profile == "llm-ready" and settings.LLM_ENABLED
                if use_llm:
                    try:
                        generated = generate_answer_llm(question=question, chunks=chunks)
                    except LLMGenerationError:
                        generated = generate_answer(question=question, chunks=chunks)
                else:
                    generated = generate_answer(question=question, chunks=chunks)
                answer_text = generated["answer"]
                confidence = generated["confidence"]
                review_required = generated["review_required"]
                citations = [
                    {
                        "repositoryUrl": _build_file_url(
                            repo_url=chunk["repositoryUrl"],
                            commit_sha=chunk["commitSha"],
                            source_path=chunk["sourcePath"],
                        ),
                        "commitSha": chunk["commitSha"],
                        "sourcePath": chunk["sourcePath"],
                        "chunkId": chunk["chunkId"],
                        "label": chunk.get("label"),
                    }
                    for chunk in chunks[:max_citations]
                ]
                policy = evaluate_policy(answer_text=answer_text, citations=citations)
                if not policy["allowed"]:
                    if allow_abstain:
                        # Policy block -> abstain rather than returning potentially unsafe claims.
                        mode = QuestionEvent.MODE_ABSTAIN
                        confidence = 0.0
                        abstained = True
                        abstention_reason = policy["reason"]
                        review_required = policy["review_required"]
                        citations = []
                        answer_text = "I do not have sufficient approved-source evidence to answer this safely."
                    else:
                        return _error_response(
                            code="POLICY_BLOCK",
                            message="Request cannot be answered within policy constraints.",
                            request_id=request_id,
                            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        )
                else:
                    # Policy-approved RAG response.
                    mode = QuestionEvent.MODE_RAG
                    review_required = policy["review_required"] or review_required

        answer_id = f"ans-{uuid4().hex[:12]}"
        # Persist the orchestration outcome as a question event before child trace records.
        event = log_question_event(
            {
                "request_id": request_id,
                "question": question,
                "session_id": data.get("sessionId", ""),
                "user_id": data.get("userId", ""),
                "standards_scope": scope,
                "language": data.get("language", "en"),
                "mode": mode,
                "confidence": confidence,
                "answer": answer_text,
                "abstained": abstained,
                "abstention_reason": abstention_reason,
                "review_required": review_required,
                "matched_faq_entry_id": matched_faq_entry_id,
                "retrieval_event_ids": retrieval_event_ids,
                "evidence_link_ids": evidence_link_ids,
            }
        )

        # Persist retrieval/evidence rows and mirror their IDs into event trace arrays.
        persisted_retrieval_ids = log_retrieval_events(question_event=event, chunks=retrieved_chunks)
        evidence_link_ids = map_evidence(question_event=event, answer_id=answer_id, chunks=citations)
        event.retrieval_event_ids = persisted_retrieval_ids
        event.evidence_link_ids = evidence_link_ids
        event.save(update_fields=["retrieval_event_ids", "evidence_link_ids", "updated_at"])

        return Response(
            {
                "answerId": answer_id,
                "mode": mode,
                "confidence": confidence,
                "answer": answer_text,
                "citations": citations,
                "abstained": abstained,
                "abstentionReason": abstention_reason,
                "reviewRequired": review_required,
                "trace": {
                    "requestId": request_id,
                    "questionEventId": str(event.id),
                    "matchedFaqEntryId": matched_faq_entry_id,
                    "retrievalEventIds": persisted_retrieval_ids,
                    "evidenceLinkIds": evidence_link_ids,
                }
            },
            status=status.HTTP_200_OK,
        )


class PromotionCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Aggregate historical question events into candidate FAQ intents.
        serializer = PromotionCandidatesQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        window_days = data["windowDays"]
        min_count = data["minCount"]
        only_unresolved = data["onlyUnresolved"]
        since = timezone.now() - timedelta(days=window_days)

        events = QuestionEvent.objects.filter(created_at__gte=since)
        buckets = defaultdict(
            lambda: {
                "questionCount": 0,
                "lastAskedAt": None,
                "unresolved": False,
            }
        )

        for event in events:
            # Lightweight intent normalization by whitespace + lowercase collapsing.
            intent = " ".join(event.question.lower().strip().split())
            bucket = buckets[intent]
            bucket["questionCount"] += 1
            bucket["lastAskedAt"] = max(bucket["lastAskedAt"], event.created_at) if bucket["lastAskedAt"] else event.created_at
            bucket["unresolved"] = bucket["unresolved"] or event.review_required or event.abstained

        items = []
        for intent, bucket in buckets.items():
            if only_unresolved and not bucket["unresolved"]:
                continue

            count = bucket["questionCount"]
            if count >= min_count:
                action = "CREATE_FAQ_DRAFT"
            elif count >= max(2, min_count // 2):
                action = "REVIEW_EXISTING_FAQ"
            else:
                action = "MONITOR"

            items.append(
                {
                    "normalizedIntent": intent,
                    "questionCount": count,
                    "notHelpfulRate": 0.0,
                    "lastAskedAt": bucket["lastAskedAt"].isoformat().replace("+00:00", "Z"),
                    "recommendedAction": action,
                }
            )

        items.sort(key=lambda i: i["questionCount"], reverse=True)

        return Response(
            {
                "windowDays": window_days,
                "minCount": min_count,
                "items": items,
            },
            status=status.HTTP_200_OK,
        )


class EditorialQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return paginated board rows for editorial triage and state transitions.
        serializer = EditorialQueueListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        actor_roles = _request_roles(request)

        queryset = EditorialQueueItem.objects.select_related("question_event").all()

        status_value = data.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        reason = data.get("reason")
        if reason:
            queryset = queryset.filter(reason=reason)

        priority = data.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        search = data.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(question_event__question__icontains=search)
                | Q(question_event__request_id__icontains=search)
            )

        page = data["page"]
        page_size = data["pageSize"]
        total = queryset.count()
        offset = (page - 1) * page_size
        items = list(queryset[offset: offset + page_size])

        return Response(
            {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "actorRoles": sorted(actor_roles),
                "items": [
                    {
                        "queueItemId": str(item.queue_item_id),
                        "status": item.status,
                        "reason": item.reason,
                        "priority": item.priority,
                        "questionEventId": str(item.question_event_id),
                        "requestId": item.question_event.request_id,
                        "question": item.question_event.question,
                        "createdAt": item.created_at.isoformat().replace("+00:00", "Z"),
                        "updatedAt": item.updated_at.isoformat().replace("+00:00", "Z"),
                        "allowedActions": allowed_actions_for_status(
                            status=item.status,
                            actor_roles=actor_roles,
                        ),
                    }
                    for item in items
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        # Route already-generated answers to editorial review queues.
        request_id = _request_id(request)
        serializer = EditorialQueueRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            question_event = QuestionEvent.objects.get(pk=data["questionEventId"])
        except QuestionEvent.DoesNotExist:
            return _error_response(
                code="QUESTION_EVENT_NOT_FOUND",
                message="questionEventId does not reference an existing event.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if data["reason"] in {EditorialQueueItem.REASON_POLICY_REVIEW, EditorialQueueItem.REASON_USER_ESCALATION}:
            # High-risk reasons go directly to review state.
            status_value = EditorialQueueItem.STATUS_REVIEW
        else:
            status_value = EditorialQueueItem.STATUS_DRAFT

        item = route_to_editorial_queue({
            "question_event": question_event,
            "reason": data["reason"],
            "priority": data.get("priority", EditorialQueueItem.PRIORITY_NORMAL),
            "status": status_value,
        })

        return Response(
            {
                "queued": True,
                "queueItemId": str(item.queue_item_id),
                "status": item.status,
            },
            status=status.HTTP_200_OK,
        )


class EditorialQueueTransitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Enforce workflow transitions with explicit role checks and audit trail creation.
        request_id = _request_id(request)
        serializer = EditorialQueueTransitionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            item = EditorialQueueItem.objects.get(queue_item_id=data["queueItemId"])
        except EditorialQueueItem.DoesNotExist:
            return _error_response(
                code="QUEUE_ITEM_NOT_FOUND",
                message="queueItemId does not reference an existing queue item.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        actor_roles = _request_roles(request)
        actor_id = _request_actor_id(request)

        try:
            transition = apply_transition(
                queue_item=item,
                action=data["action"],
                actor_id=actor_id,
                actor_roles=actor_roles,
                comment=data.get("comment", ""),
            )
        except WorkflowTransitionNotAllowed as exc:
            return _error_response(
                code="INVALID_STATE_TRANSITION",
                message=str(exc),
                request_id=request_id,
                http_status=status.HTTP_409_CONFLICT,
            )
        except WorkflowTransitionForbidden as exc:
            return _error_response(
                code="TRANSITION_FORBIDDEN",
                message=str(exc),
                request_id=request_id,
                http_status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "queueItemId": str(item.queue_item_id),
                "status": item.status,
                "transition": {
                    "action": transition.action,
                    "fromStatus": transition.from_status,
                    "toStatus": transition.to_status,
                    "actorId": transition.actor_id,
                    "actorRoles": transition.actor_roles,
                },
            },
            status=status.HTTP_200_OK,
        )


class EditorialQueueMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Compute queue health KPIs for board-level monitoring widgets.
        serializer = EditorialQueueMetricsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        window_days = data["windowDays"]
        sla_hours = data["slaHours"]
        now = timezone.now()
        since = now - timedelta(days=window_days)
        queryset = EditorialQueueItem.objects.filter(created_at__gte=since)

        by_status = {
            status_value: queryset.filter(status=status_value).count()
            for status_value, _ in EditorialQueueItem.STATUS_CHOICES
        }
        by_priority = {
            priority_value: queryset.filter(priority=priority_value).count()
            for priority_value, _ in EditorialQueueItem.PRIORITY_CHOICES
        }
        by_reason = {
            reason_value: queryset.filter(reason=reason_value).count()
            for reason_value, _ in EditorialQueueItem.REASON_CHOICES
        }

        unresolved = queryset.exclude(status=EditorialQueueItem.STATUS_PUBLISHED)
        overdue_threshold = now - timedelta(hours=sla_hours)
        overdue_count = unresolved.filter(created_at__lt=overdue_threshold).count()

        age_0_24 = unresolved.filter(created_at__gte=now - timedelta(hours=24)).count()
        age_24_72 = unresolved.filter(
            created_at__lt=now - timedelta(hours=24),
            created_at__gte=now - timedelta(hours=72),
        ).count()
        age_over_72 = unresolved.filter(created_at__lt=now - timedelta(hours=72)).count()

        return Response(
            {
                "windowDays": window_days,
                "slaHours": sla_hours,
                "generatedAt": now.isoformat().replace("+00:00", "Z"),
                "totalItems": queryset.count(),
                "unresolvedItems": unresolved.count(),
                "overdueItems": overdue_count,
                "byStatus": by_status,
                "byPriority": by_priority,
                "byReason": by_reason,
                "agingBuckets": {
                    "lt24h": age_0_24,
                    "h24to72": age_24_72,
                    "gt72h": age_over_72,
                },
            },
            status=status.HTTP_200_OK,
        )
