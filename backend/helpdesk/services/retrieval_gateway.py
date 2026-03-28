from __future__ import annotations

from uuid import uuid4

from helpdesk.models import SourceChunk


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
    """Retrieve chunks from persistent index and score by quality plus token overlap."""

    _ensure_seed_chunks()

    candidates = []
    for chunk in SourceChunk.objects.all().iterator():
        if not _scope_matches(chunk.standards_scope or [], scope):
            continue

        overlap_score = _token_overlap_score(question=question, chunk_text=chunk.text)
        score = min(1.0, (chunk.quality_score * 0.8) + (overlap_score * 0.2))
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
