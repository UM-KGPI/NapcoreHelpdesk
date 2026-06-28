"""
Groups recent question events into semantic clusters for FAQ promotion analysis.

Uses embedding similarity to cluster questions asked within a rolling time
window. Clusters with high member counts and low helpfulness rates surface
as promotion candidates for the editorial queue.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-05-24  |  Modified: 2026-06-28
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.utils import timezone

from helpdesk.models import QuestionEvent
from helpdesk.services.embeddings import (
    build_text_embeddings_batch,
    cosine_similarity,
    normalize_text_tokens,
)


@dataclass
class _ClusterState:
    centroid: list[float]
    members: list[dict[str, Any]]
    member_vectors: list[list[float]]
    similarity_sum: float


def _average_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dimension = len(vectors[0])
    if dimension == 0:
        return []

    averaged = [0.0] * dimension
    for vector in vectors:
        for index, value in enumerate(vector):
            averaged[index] += value

    count = float(len(vectors))
    return [value / count for value in averaged]


def _cluster_validation_signal(member_count: int, average_similarity: float, lexical_cohesion: float) -> str:
    if member_count >= 5 and average_similarity >= 0.86 and lexical_cohesion >= 0.55:
        return "strong"
    if member_count >= 3 and average_similarity >= 0.78 and lexical_cohesion >= 0.35:
        return "medium"
    return "weak"


def _extract_ngrams(tokens: list[str], n: int) -> list[str]:
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i : i + n]) for i in range(0, len(tokens) - n + 1)]


def _build_keyword_aggregation(questions: list[str]) -> dict[str, Any]:
    token_counter: Counter[str] = Counter()
    bigram_counter: Counter[str] = Counter()
    question_tokens: list[list[str]] = []

    for question in questions:
        tokens = normalize_text_tokens(question)
        question_tokens.append(tokens)
        token_counter.update(tokens)
        bigram_counter.update(_extract_ngrams(tokens, 2))

    top_keywords = [{"token": token, "count": count} for token, count in token_counter.most_common(5)]
    top_bigrams = [
        {"ngram": ngram, "count": count}
        for ngram, count in bigram_counter.most_common(5)
        if count >= 2
    ]

    prominent_keywords = {item["token"] for item in top_keywords[:3]}
    if not prominent_keywords:
        lexical_cohesion = 0.0
    else:
        cohesive_questions = 0
        for tokens in question_tokens:
            if set(tokens) & prominent_keywords:
                cohesive_questions += 1
        lexical_cohesion = cohesive_questions / float(max(1, len(question_tokens)))

    return {
        "topKeywords": top_keywords,
        "topBigrams": top_bigrams,
        "lexicalCohesion": round(lexical_cohesion, 4),
    }


def _build_label_hint(keyword_aggregation: dict[str, Any]) -> str:
    top_tokens = [item["token"] for item in keyword_aggregation["topKeywords"][:3]]
    if not top_tokens:
        return "unlabeled-intent"

    return " ".join(top_tokens)


def build_semantic_clusters(*, window_days: int, min_cluster_size: int, similarity_threshold: float, max_events: int) -> dict[str, Any]:
    """Compute semantic clusters over recent QuestionEvent rows using transient embeddings.

    Embeddings are built in-memory for the current batch and are not persisted.
    """

    now = timezone.now()
    since = now - timedelta(days=window_days)

    events = list(
        QuestionEvent.objects.filter(created_at__gte=since)
        .order_by("-created_at")[:max_events]
        .values("id", "question", "created_at", "request_id", "mode", "review_required", "abstained")
    )

    if not events:
        return {
            "generatedAt": now.isoformat().replace("+00:00", "Z"),
            "windowDays": window_days,
            "minClusterSize": min_cluster_size,
            "similarityThreshold": similarity_threshold,
            "maxEvents": max_events,
            "totalEvents": 0,
            "clusteredEvents": 0,
            "singletonEvents": 0,
            "clusters": [],
        }

    questions = [str(item["question"]) for item in events]
    vectors = build_text_embeddings_batch(questions)

    clusters: list[_ClusterState] = []
    for event, vector in zip(events, vectors):
        best_index = -1
        best_similarity = -1.0

        for index, state in enumerate(clusters):
            similarity = cosine_similarity(vector, state.centroid)
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = index

        member = {
            "questionEventId": str(event["id"]),
            "question": str(event["question"]),
            "askedAt": event["created_at"].isoformat().replace("+00:00", "Z"),
            "requestId": str(event["request_id"]),
            "mode": str(event["mode"]),
            "reviewRequired": bool(event["review_required"]),
            "abstained": bool(event["abstained"]),
        }

        if best_index >= 0 and best_similarity >= similarity_threshold:
            state = clusters[best_index]
            state.members.append(member)
            state.member_vectors.append(vector)
            state.similarity_sum += best_similarity
            # Recompute centroid from assigned vectors for numerical stability.
            state.centroid = _average_vectors(state.member_vectors)
            continue

        clusters.append(_ClusterState(centroid=vector, members=[member], member_vectors=[vector], similarity_sum=1.0))

    cluster_items: list[dict[str, Any]] = []
    singleton_events = 0
    clustered_events = 0

    for index, state in enumerate(clusters):
        member_count = len(state.members)
        if member_count < min_cluster_size:
            singleton_events += member_count
            continue

        clustered_events += member_count
        sorted_members = sorted(state.members, key=lambda item: item["askedAt"], reverse=True)
        average_similarity = state.similarity_sum / float(member_count)

        keyword_aggregation = _build_keyword_aggregation([item["question"] for item in sorted_members])
        label_hint = _build_label_hint(keyword_aggregation)
        lexical_cohesion = float(keyword_aggregation["lexicalCohesion"])
        cluster_items.append(
            {
                "clusterId": f"sc-{index + 1}",
                "labelHint": label_hint,
                "validationSignal": _cluster_validation_signal(member_count, average_similarity, lexical_cohesion),
                "memberCount": member_count,
                "averageSimilarity": round(average_similarity, 4),
                "latestAskedAt": sorted_members[0]["askedAt"],
                "questionEventIds": [item["questionEventId"] for item in sorted_members],
                "sampleQuestions": [item["question"] for item in sorted_members[:3]],
                "keywordAggregation": keyword_aggregation,
                "members": sorted_members,
            }
        )

    cluster_items.sort(key=lambda item: (item["memberCount"], item["latestAskedAt"]), reverse=True)

    return {
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "windowDays": window_days,
        "minClusterSize": min_cluster_size,
        "similarityThreshold": similarity_threshold,
        "maxEvents": max_events,
        "totalEvents": len(events),
        "clusteredEvents": clustered_events,
        "singletonEvents": singleton_events,
        "clusters": cluster_items,
    }
