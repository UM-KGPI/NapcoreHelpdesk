from __future__ import annotations

from uuid import uuid4
from django.db import connection, models

try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
except Exception:  # pragma: no cover - only unavailable in non-postgres-only environments
    SearchQuery = None
    SearchRank = None
    SearchVector = None

from helpdesk.models import SourceChunk
from helpdesk.db_fields import HAS_NATIVE_PGVECTOR
from helpdesk.services.embeddings import build_text_embedding, cosine_similarity

try:
    from pgvector.django import CosineDistance  # type: ignore
except Exception:  # pragma: no cover - optional dependency in SQLite-only environments
    CosineDistance = None


DEFAULT_CHUNKS = [
    {
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-001",
        "label": "NeTEx profile overview",
        "text": "NeTEx profiles define interoperable structures for timetable and stop data.",
        "standards_scope": ["NeTEx", "Transmodel"],
        "quality_score": 0.84,
        "embedding_vector": build_text_embedding(
            "NeTEx profiles define interoperable structures for timetable and stop data."
        ),
    },
    {
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-002",
        "label": "SIRI context",
        "text": "SIRI supports real-time information exchange in public transport systems.",
        "standards_scope": ["SIRI"],
        "quality_score": 0.79,
        "embedding_vector": build_text_embedding(
            "SIRI supports real-time information exchange in public transport systems."
        ),
    },
    {
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-003",
        "label": "OJP/OpRa context",
        "text": "OJP/OpRa complements planning and operational data exchange flows.",
        "standards_scope": ["OJP/OpRa", "DATEX II"],
        "quality_score": 0.78,
        "embedding_vector": build_text_embedding(
            "OJP/OpRa complements planning and operational data exchange flows."
        ),
    },
]


def _ensure_seed_chunks() -> None:
    if SourceChunk.objects.exists():
        return

    for chunk in DEFAULT_CHUNKS:
        SourceChunk.objects.get_or_create(
            chunk_id=chunk["chunk_id"],
            defaults=chunk,
        )


def _token_overlap_score(question: str, chunk_text: str) -> float:
    question_tokens = {token for token in question.lower().split() if len(token) > 2}
    if not question_tokens:
        return 0.0
    chunk_tokens = {token for token in chunk_text.lower().split() if len(token) > 2}
    overlap = question_tokens.intersection(chunk_tokens)
    return len(overlap) / len(question_tokens)


def _postgres_fts_candidates(question: str, top_k: int):
    """Return FTS-ranked candidate queryset when PostgreSQL search is available."""

    if connection.vendor != "postgresql" or not all([SearchQuery, SearchRank, SearchVector]):
        return None

    search_query = SearchQuery(question)
    return (
        SourceChunk.objects.annotate(
            lexical_rank=SearchRank(SearchVector("text", config="english"), search_query)
        )
        .filter(lexical_rank__gt=0.0)
        .order_by("-lexical_rank")[: max(20, top_k * 4)]
    )


def _postgres_hybrid_candidates(question: str, query_embedding: list[float], top_k: int):
    """Return combined vector+lexical ranked candidates on PostgreSQL with pgvector."""

    if not (
        connection.vendor == "postgresql"
        and HAS_NATIVE_PGVECTOR
        and CosineDistance is not None
        and all([SearchQuery, SearchRank, SearchVector])
    ):
        return None

    search_query = SearchQuery(question)
    # Cosine distance is lower-is-better; convert to similarity with (1 - distance).
    return (
        SourceChunk.objects.annotate(
            lexical_rank=SearchRank(SearchVector("text", config="english"), search_query),
            vector_distance=CosineDistance("embedding_vector", query_embedding),
        )
        .annotate(vector_similarity=1.0 - models.F("vector_distance"))
        .order_by("-vector_similarity", "-lexical_rank")[: max(25, top_k * 5)]
    )


def _scope_matches(chunk_scope: list[str], requested_scope: list[str] | None) -> bool:
    if not requested_scope:
        return True
    return bool(set(chunk_scope).intersection(set(requested_scope)))


def retrieve_chunks(
    question: str,
    top_k: int,
    min_score: float,
    scope: list[str] | None = None,
) -> list[dict]:
    """Retrieve chunks using hybrid vector and lexical ranking.

    Ranking weights:
    - 50% vector similarity
    - 30% lexical relevance
    - 20% indexed quality score
    """

    _ensure_seed_chunks()

    query_embedding = build_text_embedding(question)

    postgres_candidates = _postgres_hybrid_candidates(
        question=question,
        query_embedding=query_embedding,
        top_k=top_k,
    )
    if postgres_candidates is None:
        postgres_candidates = _postgres_fts_candidates(question=question, top_k=top_k)

    if postgres_candidates is not None:
        chunk_iterable = postgres_candidates
    else:
        chunk_iterable = SourceChunk.objects.all().iterator()

    candidates = []
    for chunk in chunk_iterable:
        if not _scope_matches(chunk.standards_scope or [], scope):
            continue

        lexical_score = float(getattr(chunk, "lexical_rank", 0.0))
        if lexical_score <= 0.0:
            lexical_score = _token_overlap_score(question=question, chunk_text=chunk.text)
        lexical_score = max(0.0, min(1.0, lexical_score))

        chunk_embedding = chunk.embedding_vector or build_text_embedding(chunk.text)
        vector_score = max(0.0, cosine_similarity(query_embedding, chunk_embedding))
        quality_score = max(0.0, min(1.0, chunk.quality_score))

        hybrid_score = (vector_score * 0.5) + (lexical_score * 0.3) + (quality_score * 0.2)
        # Keep backward-compatible retrieval strength so known covered intents do not regress.
        legacy_score = (quality_score * 0.8) + (lexical_score * 0.2)
        score = min(1.0, max(hybrid_score, legacy_score))
        if score < min_score:
            continue

        candidates.append(
            {
                "text": chunk.text,
                "score": score,
                "repositoryUrl": chunk.repository_url,
                "commitSha": chunk.commit_sha,
                "sourcePath": chunk.source_path,
                "chunkId": chunk.chunk_id,
                "label": chunk.label,
                "retrievalEventId": f"re-{uuid4().hex[:8]}",
            }
        )

    candidates.sort(key=lambda value: value["score"], reverse=True)
    return candidates[:top_k]
