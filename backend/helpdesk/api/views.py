from collections import defaultdict
from datetime import timedelta
from uuid import uuid4

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from helpdesk.models import EditorialQueueItem, QuestionEvent
from helpdesk.services.editorial_router import route_to_editorial_queue
from helpdesk.services.evidence_mapper import map_evidence
from helpdesk.services.event_logger import log_question_event
from helpdesk.services.faq_matcher import match_faq
from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.retrieval_gateway import retrieve_chunks

from .serializers import (
    AnswerRequestSerializer,
    EditorialQueueRequestSerializer,
    PromotionCandidatesQuerySerializer,
)


def _request_id(request):
    # Keep a stable correlation ID for traceability in logs, DB events, and error payloads.
    return request.headers.get("X-Request-Id") or f"req-{uuid4().hex[:12]}"


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
                generated = generate_answer(question=question, chunks=chunks)
                answer_text = generated["answer"]
                confidence = generated["confidence"]
                review_required = generated["review_required"]
                citations = [
                    {
                        "repositoryUrl": chunk["repositoryUrl"],
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
        # Create traceable evidence-link IDs for downstream review and audit.
        evidence_link_ids = map_evidence(answer_id=answer_id, chunks=citations)

        # Persist the full orchestration outcome as question telemetry.
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
                    "retrievalEventIds": retrieval_event_ids,
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
