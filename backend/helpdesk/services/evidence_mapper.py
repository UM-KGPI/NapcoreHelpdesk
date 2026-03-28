from __future__ import annotations

from helpdesk.models import AnswerEvidenceLink, QuestionEvent


def map_evidence(question_event: QuestionEvent, answer_id: str, chunks: list[dict]) -> list[str]:
    """Persist answer-evidence links and return stable public link identifiers."""

    link_ids: list[str] = []
    for index, chunk in enumerate(chunks):
        link_id = f"el-{answer_id}-{index + 1}"
        AnswerEvidenceLink.objects.update_or_create(
            evidence_link_id=link_id,
            defaults={
                "question_event": question_event,
                "answer_id": answer_id,
                "repository_url": chunk.get("repositoryUrl", ""),
                "commit_sha": chunk.get("commitSha", ""),
                "source_path": chunk.get("sourcePath", ""),
                "chunk_id": chunk.get("chunkId", ""),
                "label": chunk.get("label") or "",
            },
        )
        link_ids.append(link_id)
    return link_ids
