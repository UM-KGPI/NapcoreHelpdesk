from collections import defaultdict
import datetime as dt
from datetime import timedelta
from pathlib import Path
import subprocess
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

from helpdesk.models import EditorialQueueItem, IndexRunMetric, QuestionEvent
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
from helpdesk.services.question_parsing import parse_question_to_semantic_query
from helpdesk.services.index_builder import index_repository
from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace
from helpdesk.services.retrieval_event_logger import log_retrieval_events

from .serializers import (
    AnswerRequestSerializer,
    EditorialQueueListQuerySerializer,
    EditorialQueueMetricsQuerySerializer,
    EditorialQueueRequestSerializer,
    EditorialQueueTransitionRequestSerializer,
    IndexRepositoryRequestSerializer,
    PromotionCandidatesQuerySerializer,
)


def _request_id(request):
    # Keep a stable correlation ID for traceability in logs, DB events, and error payloads.
    return request.headers.get("X-Request-Id") or f"req-{uuid4().hex[:12]}"


def _build_file_url(repo_url: str, commit_sha: str, source_path: str) -> str:
    """Construct a direct GitHub file URL pointing to the exact blob at a commit."""
    # Remove trailing .git if present, normalize the repo URL.
    repo_url = repo_url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    if source_path.startswith("issues/") and source_path.endswith(".md"):
        issue_number = Path(source_path).stem
        if issue_number.isdigit():
            return f"{repo_url}/issues/{issue_number}"

    resolved_commit_sha = _resolve_commit_sha(repo_url=repo_url, commit_sha=commit_sha)
    # Build the GitHub blob URL: https://github.com/OWNER/REPO/blob/COMMIT/PATH
    return f"{repo_url}/blob/{resolved_commit_sha}/{source_path}"


def _resolve_commit_sha(repo_url: str, commit_sha: str) -> str:
    """Expand short commit SHAs using the most recent indexed local repository path when available."""

    normalized = (commit_sha or "").strip()
    if len(normalized) >= 40 or not normalized or normalized == "placeholder":
        return normalized

    latest_run = IndexRunMetric.objects.filter(repository_url=repo_url).order_by("-created_at").first()
    if not latest_run:
        return normalized

    repository_path = Path(latest_run.repository_path).expanduser()
    if not repository_path.exists():
        return normalized

    try:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "rev-parse", normalized],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return normalized

    resolved = result.stdout.strip()
    return resolved or normalized


def _dominant_repository_url(chunks: list[dict]) -> str | None:
    if not chunks:
        return None

    repository_weights: dict[str, float] = defaultdict(float)
    for index, chunk in enumerate(chunks):
        repository_url = chunk.get("repositoryUrl")
        if not repository_url:
            continue
        repository_weights[repository_url] += float(chunk.get("score", 0.0)) * max(0.5, 1.0 - (index * 0.08))

    if not repository_weights:
        return None
    return max(repository_weights.items(), key=lambda item: item[1])[0]


def _select_citations(chunks: list[dict], max_citations: int) -> list[dict]:
    def citation_sort_key(chunk: dict) -> tuple:
        source_path = str(chunk.get("sourcePath", "")).lower()
        basename = source_path.rsplit("/", 1)[-1]
        is_docs_or_model = (
            source_path.startswith("docs/")
            or "/docs/" in source_path
            or "model-summary" in source_path
            or source_path.startswith("models/")
            or "/models/" in source_path
        )
        is_readme = basename.startswith("readme.")
        return (
            0 if is_docs_or_model else 1,
            0 if not is_readme else 1,
            -float(chunk.get("score", 0.0)),
            source_path,
        )

    selected: list[dict] = []
    selected_repositories: set[str] = set()
    seen_sources: set[tuple[str, str]] = set()
    sorted_chunks = sorted(chunks, key=citation_sort_key)

    # Pass 1: maximize repository coverage while keeping best-ranked sources per repo.
    for chunk in sorted_chunks:
        repository_url = chunk.get("repositoryUrl", "")
        source_path = chunk.get("sourcePath", "")
        source_key = (repository_url, source_path)
        if source_key in seen_sources:
            continue
        if repository_url in selected_repositories:
            continue

        seen_sources.add(source_key)
        selected_repositories.add(repository_url)
        selected.append(
            {
                "repositoryUrl": _build_file_url(
                    repo_url=repository_url,
                    commit_sha=chunk["commitSha"],
                    source_path=source_path,
                ),
                "commitSha": chunk["commitSha"],
                "sourcePath": source_path,
                "chunkId": chunk["chunkId"],
                "label": chunk.get("label"),
            }
        )
        if len(selected) >= max_citations:
            return selected

    # Pass 2: fill remaining slots by global ranking regardless of repository.
    for chunk in sorted_chunks:
        repository_url = chunk.get("repositoryUrl", "")
        source_path = chunk.get("sourcePath", "")
        source_key = (repository_url, source_path)
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        selected.append(
            {
                "repositoryUrl": _build_file_url(
                    repo_url=repository_url,
                    commit_sha=chunk["commitSha"],
                    source_path=source_path,
                ),
                "commitSha": chunk["commitSha"],
                "sourcePath": source_path,
                "chunkId": chunk["chunkId"],
                "label": chunk.get("label"),
            }
        )
        if len(selected) >= max_citations:
            break

    return selected


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


def _resolve_graph_rag_enabled(_options: dict) -> bool:
    """Graph retrieval runs unconditionally whenever GRAPH_RAG_ENABLED is true.

    Variant flags and per-request opt-out are not honoured: knowledge graph
    expansion should always apply so that reasoning is repo-independent.
    """
    return bool(settings.GRAPH_RAG_ENABLED)


def _request_actor_id(request):
    """Resolve actor identifier used in transition audit entries."""

    token = request.auth if isinstance(request.auth, dict) else {}
    subject = token.get("sub")
    if isinstance(subject, str) and subject.strip():
        return subject.strip()
    user = getattr(request, "user", None)
    username = getattr(user, "username", "") if user else ""
    return username or "unknown"


def _evidence_coverage_level(chunks: list[dict], avg_score: float) -> str:
    """Classify evidence coverage for traceability and provisional-answer signaling."""

    if len(chunks) >= 4 and avg_score >= 0.75:
        return "high"
    if len(chunks) >= 2 and avg_score >= 0.62:
        return "medium"
    return "low"


def _classify_partial_evidence(
    *,
    mode: str,
    abstained: bool,
    confidence: float,
    chunks: list[dict],
    graph_trace: dict,
    effective_scope: list[str],
) -> dict:
    """Return provisional-answer metadata for partial-evidence fallback behavior."""

    if mode != QuestionEvent.MODE_RAG or abstained:
        return {
            "semanticProvisional": False,
            "semanticProvisionalReason": None,
            "evidenceCoverageLevel": "high",
        }

    if not chunks:
        return {
            "semanticProvisional": True,
            "semanticProvisionalReason": "LIMITED_EVIDENCE_COVERAGE",
            "evidenceCoverageLevel": "low",
        }

    avg_score = sum(float(chunk.get("score", 0.0)) for chunk in chunks) / max(1, len(chunks))
    coverage_level = _evidence_coverage_level(chunks, avg_score)
    semantic_alignment = float(graph_trace.get("semanticAlignmentScore", 0.0))
    repository_coverage = int(graph_trace.get("repositoryCoverageCount", 0))

    reason = None
    if confidence < 0.72 or semantic_alignment < 0.40:
        reason = "LOW_RETRIEVAL_CONFIDENCE"
    elif len(chunks) < 2 or coverage_level == "low":
        reason = "LIMITED_EVIDENCE_COVERAGE"
    elif len(effective_scope) > 1 and repository_coverage < min(2, len(effective_scope)):
        reason = "CROSS_STANDARD_GAP"

    return {
        "semanticProvisional": reason is not None,
        "semanticProvisionalReason": reason,
        "evidenceCoverageLevel": coverage_level,
    }


def _infer_standard_from_chunk(chunk: dict, effective_scope: list[str]) -> str | None:
    chunk_scope = chunk.get("standardsScope") or chunk.get("standards_scope") or []
    if isinstance(chunk_scope, list):
        for standard in effective_scope:
            if standard in chunk_scope:
                return standard

    blob = "\n".join(
        [
            str(chunk.get("repositoryUrl", "")),
            str(chunk.get("sourcePath", "")),
            str(chunk.get("label", "")),
            str(chunk.get("text", "")),
        ]
    ).lower()
    aliases = {
        "NeTEx": ["netex"],
        "OpRa": ["opra"],
        "SIRI": ["siri"],
        "OJP": ["ojp"],
        "DATEX II": ["datex"],
        "Transmodel": ["transmodel"],
    }
    for standard in effective_scope:
        for alias in aliases.get(standard, []):
            if alias in blob:
                return standard
    return None


def _build_cross_standard_analysis(
    *,
    mode: str,
    effective_scope: list[str],
    chunks: list[dict],
) -> dict:
    """Build per-standard evidence partitions and detect contradiction signals."""

    if mode != QuestionEvent.MODE_RAG or len(effective_scope) < 2:
        return {
            "crossStandardConflict": False,
            "crossStandardConflictType": None,
            "crossStandardEvidencePartitions": [],
        }

    partitions: dict[str, list[dict]] = {standard: [] for standard in effective_scope}
    for chunk in chunks:
        standard = _infer_standard_from_chunk(chunk, effective_scope)
        if standard:
            partitions.setdefault(standard, []).append(chunk)

    partition_payload: list[dict] = []
    mandatory_standards: set[str] = set()
    optional_standards: set[str] = set()
    conflict_subject_detected = False

    for standard in effective_scope:
        standard_chunks = partitions.get(standard, [])
        if not standard_chunks:
            continue

        merged_text = "\n".join(str(chunk.get("text", "")).lower() for chunk in standard_chunks)
        signals = []
        if any(token in merged_text for token in ["shall", "must", "required"]):
            signals.append("mandatory")
            mandatory_standards.add(standard)
        if any(token in merged_text for token in ["may", "optional"]):
            signals.append("optional")
            optional_standards.add(standard)
        if any(token in merged_text for token in ["journey", "delay", "pattern", "timetable", "exchange"]):
            conflict_subject_detected = True

        top_paths = []
        for chunk in sorted(standard_chunks, key=lambda item: float(item.get("score", 0.0)), reverse=True)[:3]:
            source_path = str(chunk.get("sourcePath", "")).strip()
            if source_path and source_path not in top_paths:
                top_paths.append(source_path)

        avg_score = sum(float(chunk.get("score", 0.0)) for chunk in standard_chunks) / len(standard_chunks)
        partition_payload.append(
            {
                "standard": standard,
                "evidenceCount": len(standard_chunks),
                "avgScore": round(avg_score, 4),
                "topSourcePaths": top_paths,
                "normativitySignals": signals,
            }
        )

    conflict_type = None
    conflict_detected = False
    if mandatory_standards and optional_standards and conflict_subject_detected:
        conflict_detected = True
        conflict_type = "NORMATIVE_STRENGTH_MISMATCH"
    elif len(partition_payload) >= 2 and any(partition["evidenceCount"] == 0 for partition in partition_payload):
        conflict_detected = True
        conflict_type = "EVIDENCE_COVERAGE_ASYMMETRY"

    return {
        "crossStandardConflict": conflict_detected,
        "crossStandardConflictType": conflict_type,
        "crossStandardEvidencePartitions": partition_payload,
    }


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
        semantic_query = parse_question_to_semantic_query(text=question, requested_scope=scope)
        effective_scope = scope or semantic_query.candidate_standards
        semantic_disambiguation_required = False
        semantic_disambiguation_prompt = None
        semantic_fallback = None
        generation_profile = data.get("generationProfile", "llm-ready")
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
        graph_trace = {
            "graphRagVariant": "control",
            "graphExpansionHops": 0,
            "graphExpansionSource": "none",
            "graphConceptIds": [],
            "graphCandidatesAdded": 0,
            "graphEvidenceCount": 0,
            "graphScoreContribution": 0.0,
            "graphProvenanceChainCount": 0,
            "repositoryCoverageCount": 0,
            "conceptCoverageCount": 0,
            "semanticAlignmentScore": 0.0,
            "retrievalLatencyMs": 0.0,
        }
        faq_match = None

        # 1) FAQ-first: fast, deterministic, and usually high confidence.
        if not scope and semantic_query.ambiguous_core_concept and len(effective_scope) > 1:
            # Ambiguity fallback: reduce reasoning scope and ask for clarification.
            effective_scope = [effective_scope[0]]
            semantic_disambiguation_required = True
            semantic_disambiguation_prompt = (
                "Your question maps to multiple core concepts. "
                "Please clarify the intended standard or artifact type for a more precise answer."
            )
            semantic_fallback = "AMBIGUOUS_CORE_CONCEPT"

        faq_match = match_faq(question=question, scope=effective_scope)
        if faq_match and faq_match["confidence"] >= faq_min_confidence and faq_match.get("scope_match", True):
            mode = QuestionEvent.MODE_FAQ
            confidence = faq_match["confidence"]
            review_required = faq_match["review_required"]
            matched_faq_entry_id = faq_match["faq_entry_id"]
            answer_text = faq_match["answer"]
            citations = faq_match["citations"][:max_citations]
        elif semantic_query.core_concept == "nits:unknown-concept" and allow_abstain and not effective_scope:
            mode = QuestionEvent.MODE_ABSTAIN
            confidence = 0.0
            abstained = True
            abstention_reason = QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
            review_required = True
            semantic_fallback = "NO_CONCEPT_MATCH"
            answer_text = (
                "I could not map your question to a known standards concept yet. "
                "Please clarify by naming a concrete concept, artifact, or standard scope."
            )
            citations = []
        else:
            # 2) RAG fallback: retrieve evidence, generate, then run policy gate.
            graph_rag_enabled = _resolve_graph_rag_enabled(options)
            chunks, graph_trace = retrieve_chunks_with_trace(
                question=question,
                top_k=retrieval_top_k,
                min_score=retrieval_min_score,
                scope=effective_scope,
                graph_rag_enabled=graph_rag_enabled,
            )

            # Retry with a relaxed threshold to avoid abstaining on terse asks that still
            # have relevant evidence in indexed sources.
            relaxed_min_score = min(retrieval_min_score, 0.45)
            if not chunks and relaxed_min_score < retrieval_min_score:
                chunks, graph_trace = retrieve_chunks_with_trace(
                    question=question,
                    top_k=retrieval_top_k,
                    min_score=relaxed_min_score,
                    scope=effective_scope,
                    graph_rag_enabled=graph_rag_enabled,
                )

            # Retry with a wider candidate pool when the retrieved evidence is semantically
            # misaligned with the query (low mean cosine similarity).  This is a general
            # signal that keyword-trap chunks dominated the first pass.  We do not inspect
            # question content here; the alignment score alone drives the decision.
            _SEMANTIC_ALIGNMENT_RETRY_THRESHOLD = 0.35
            if chunks and graph_trace.get("semanticAlignmentScore", 1.0) < _SEMANTIC_ALIGNMENT_RETRY_THRESHOLD:
                wider_chunks, wider_trace = retrieve_chunks_with_trace(
                    question=question,
                    top_k=retrieval_top_k * 2,
                    min_score=relaxed_min_score,
                    scope=effective_scope,
                    graph_rag_enabled=graph_rag_enabled,
                )
                if wider_trace.get("semanticAlignmentScore", 0.0) > graph_trace.get("semanticAlignmentScore", 0.0):
                    chunks, graph_trace = wider_chunks, wider_trace

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
                        generated = generate_answer_llm(question=question, chunks=chunks, scope=effective_scope)
                    except LLMGenerationError:
                        generated = generate_answer(question=question, chunks=chunks)
                else:
                    generated = generate_answer(question=question, chunks=chunks)
                answer_text = generated["answer"]
                confidence = generated["confidence"]
                review_required = generated["review_required"]
                citations = _select_citations(chunks=chunks, max_citations=max_citations)
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
                "standards_scope": effective_scope,
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

        partial_evidence = _classify_partial_evidence(
            mode=mode,
            abstained=abstained,
            confidence=confidence,
            chunks=retrieved_chunks,
            graph_trace=graph_trace,
            effective_scope=effective_scope,
        )
        cross_standard_analysis = _build_cross_standard_analysis(
            mode=mode,
            effective_scope=effective_scope,
            chunks=retrieved_chunks,
        )
        if partial_evidence["semanticProvisional"] and semantic_fallback is None:
            semantic_fallback = "PARTIAL_EVIDENCE"

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
                    "graphExpansionHops": graph_trace["graphExpansionHops"],
                    "graphConceptIds": graph_trace["graphConceptIds"],
                    "graphEvidenceCount": graph_trace["graphEvidenceCount"],
                    "graphScoreContribution": graph_trace["graphScoreContribution"],
                    "repositoryCoverageCount": graph_trace.get("repositoryCoverageCount", 0),
                    "conceptCoverageCount": graph_trace.get("conceptCoverageCount", 0),
                    "semanticAlignmentScore": graph_trace.get("semanticAlignmentScore", 0.0),
                    "semanticQuery": semantic_query.as_dict(),
                    "semanticDisambiguationRequired": semantic_disambiguation_required,
                    "semanticDisambiguationPrompt": semantic_disambiguation_prompt,
                    "semanticFallback": semantic_fallback,
                    "semanticProvisional": partial_evidence["semanticProvisional"],
                    "semanticProvisionalReason": partial_evidence["semanticProvisionalReason"],
                    "evidenceCoverageLevel": partial_evidence["evidenceCoverageLevel"],
                    "crossStandardConflict": cross_standard_analysis["crossStandardConflict"],
                    "crossStandardConflictType": cross_standard_analysis["crossStandardConflictType"],
                    "crossStandardEvidencePartitions": cross_standard_analysis[
                        "crossStandardEvidencePartitions"
                    ],
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


class IndexRepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Trigger a source repository ingestion run against an already-cloned local path."""
        from pathlib import Path

        request_id = _request_id(request)

        # Restrict to admin or publisher roles to prevent accidental re-indexing.
        actor_roles = _request_roles(request)
        if not (actor_roles & {"admin", "publisher"}):
            return _error_response(
                code="FORBIDDEN",
                message="Indexing requires admin or publisher role.",
                request_id=request_id,
                http_status=status.HTTP_403_FORBIDDEN,
            )

        serializer = IndexRepositoryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        repo_url = data["repoUrl"].strip()
        repo_path = Path(data["repoPath"]).expanduser().resolve()
        auto_allow_repository = bool(data.get("autoAllowRepository", True))

        if not repo_path.exists() or not repo_path.is_dir():
            return _error_response(
                code="INVALID_REPO_PATH",
                message=f"repoPath does not exist or is not a directory: {repo_path}",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional convenience for operators: add repository URL to in-process allow-list.
        allowed_repositories = set(settings.ALLOWED_SOURCE_REPOSITORIES)
        auto_allowed = False
        if auto_allow_repository and repo_url not in allowed_repositories:
            allowed_repositories.add(repo_url)
            settings.ALLOWED_SOURCE_REPOSITORIES = allowed_repositories
            auto_allowed = True

        try:
            stats = index_repository(
                repo_url=repo_url,
                repo_path=repo_path,
                allowed_repositories=allowed_repositories,
                profile=data["profile"],
                incremental=data["incremental"],
                prune=data["prune"],
                include_issues=bool(data.get("includeIssues", False)),
                github_token=settings.GITHUB_API_TOKEN or None,
                github_verify_ssl=settings.GITHUB_API_VERIFY_SSL,
                github_ca_bundle=settings.GITHUB_CA_BUNDLE,
            )
        except ValueError as exc:
            return _error_response(
                code="INDEX_ERROR",
                message=str(exc),
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "ok",
                "requestId": request_id,
                "repositoryUrl": repo_url,
                "repositoryPath": str(repo_path),
                "profile": data["profile"],
                "incremental": data["incremental"],
                "prune": data["prune"],
                "autoAllowedRepository": auto_allowed,
                "scannedFiles": stats.scanned_files,
                "skippedFiles": stats.skipped_files,
                "createdChunks": stats.created_chunks,
                "updatedChunks": stats.updated_chunks,
                "deletedChunks": stats.deleted_chunks,
            },
            status=status.HTTP_200_OK,
        )
