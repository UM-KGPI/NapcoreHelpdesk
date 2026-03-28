from __future__ import annotations

from helpdesk.models import QuestionEvent, RetrievalEvent


def log_retrieval_events(question_event: QuestionEvent, chunks: list[dict]) -> list[str]:
    """Persist retrieval events for traceability and return event IDs."""

    retrieval_ids: list[str] = []
    for chunk in chunks:
        retrieval_event_id = chunk.get("retrievalEventId")
        if not retrieval_event_id:
            continue

        RetrievalEvent.objects.update_or_create(
            retrieval_event_id=retrieval_event_id,
            defaults={
                "question_event": question_event,
                "repository_url": chunk.get("repositoryUrl", ""),
                "commit_sha": chunk.get("commitSha", ""),
                "source_path": chunk.get("sourcePath", ""),
                "chunk_id": chunk.get("chunkId", ""),
                "score": float(chunk.get("score") or 0.0),
            },
        )
        retrieval_ids.append(retrieval_event_id)

    return retrieval_ids
