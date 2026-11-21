"""
Persists per-chunk retrieval telemetry as RetrievalEvent records.

Called after each RAG retrieval pass to record which source chunks were
scored, their similarity values, and the originating question event. Used
for analytics and downstream evidence auditability.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

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
                # `or ""`: a key present with None (chunk built from an object lacking the field) must not
                # fail the NOT NULL column; telemetry never costs an answer.
                "repository_url": chunk.get("repositoryUrl") or "",
                "commit_sha": chunk.get("commitSha") or "",
                "source_path": chunk.get("sourcePath") or "",
                "chunk_id": chunk.get("chunkId") or "",
                "score": float(chunk.get("score") or 0.0),
            },
        )
        retrieval_ids.append(retrieval_event_id)

    return retrieval_ids
