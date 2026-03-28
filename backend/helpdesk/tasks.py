from __future__ import annotations

from pathlib import Path

from celery import shared_task
from django.conf import settings

from helpdesk.services.index_builder import index_repository


@shared_task(name="helpdesk.reindex_default_repository")
def reindex_default_repository() -> dict:
    """Scheduled incremental re-index task using configured default repository values."""

    repo_url = settings.INDEX_SCHEDULE_REPO_URL
    repo_path = settings.INDEX_SCHEDULE_REPO_PATH
    profile = settings.INDEX_SCHEDULE_PROFILE

    if not repo_url or not repo_path:
        # Scheduler can run before env vars are configured; fail soft with structured reason.
        return {
            "status": "skipped",
            "reason": "INDEX_SCHEDULE_REPO_URL or INDEX_SCHEDULE_REPO_PATH not configured",
        }

    # Daily runs use incremental+prune to keep index fresh without full rebuild costs.
    stats = index_repository(
        repo_url=repo_url,
        repo_path=Path(repo_path).expanduser().resolve(),
        allowed_repositories=settings.ALLOWED_SOURCE_REPOSITORIES,
        profile=profile,
        incremental=True,
        prune=True,
    )

    return {
        "status": "ok",
        "repository": repo_url,
        "profile": profile,
        "scanned_files": stats.scanned_files,
        "skipped_files": stats.skipped_files,
        "created_chunks": stats.created_chunks,
        "updated_chunks": stats.updated_chunks,
        "deleted_chunks": stats.deleted_chunks,
    }
