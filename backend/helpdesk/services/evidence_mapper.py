"""
Maps retrieval results to persisted AnswerEvidenceLink records.

Links each cited source chunk back to the originating QuestionEvent so
that editorial reviewers can inspect the exact evidence used to construct
an answer.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

from helpdesk.models import AnswerEvidenceLink, QuestionEvent


def map_evidence(question_event: QuestionEvent, answer_id: str, chunks: list[dict]) -> list[str]:
    """Persist answer-evidence links and return stable public link identifiers."""

    link_ids: list[str] = []
    for index, chunk in enumerate(chunks):
        link_id = f"el-{answer_id}-{index + 1}"

        # Extract base repository URL from potentially full blob URL
        repo_url = chunk.get("repositoryUrl", "")
        if "/blob/" in repo_url:
            # If the URL was already built by _select_citations, extract the base repo URL
            # e.g., "https://github.com/Owner/Repo/blob/ref/path" -> "https://github.com/Owner/Repo"
            repo_url = repo_url.split("/blob/")[0]

        AnswerEvidenceLink.objects.update_or_create(
            evidence_link_id=link_id,
            defaults={
                "question_event": question_event,
                "answer_id": answer_id,
                "repository_url": repo_url,
                "commit_sha": chunk.get("commitSha", ""),
                "source_path": chunk.get("sourcePath", ""),
                "chunk_id": chunk.get("chunkId", ""),
                "label": chunk.get("label") or "",
            },
        )
        link_ids.append(link_id)
    return link_ids
