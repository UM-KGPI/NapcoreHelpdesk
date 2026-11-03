"""
Background task definitions for async helpdesk operations.

Wraps long-running operations (repository refresh, semantic clustering) that
can be dispatched via a task queue rather than blocking an API request.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-11-03
"""

from __future__ import annotations

from celery import shared_task
from django.conf import settings

from helpdesk.services.source_refresh import SourceRefreshError, refresh_all_sources
from helpdesk.services.semantic_clustering import build_semantic_clusters


@shared_task(name="helpdesk.refresh_source_indexes")
def refresh_source_indexes() -> dict:
    """Scheduled refresh of every indexed standards repository (see services/source_refresh.py).

    A repository that fails is reported, the others still run; the task then fails so the
    problem shows up in the worker log instead of passing silently.
    """

    result = refresh_all_sources()
    if result["status"] in {"partial", "failed"}:
        failures = {name: row.get("error", "unknown error") for name, row in result["results"].items() if row["status"] != "ok"}
        raise SourceRefreshError(f"Source refresh {result['status']}: {failures or result.get('reason')}")
    return result


@shared_task(name="helpdesk.harvest_source", bind=True)
def harvest_source(self, name: str, full: bool = False) -> dict:
    """Harvest one configured source for the editor (Harvest & Index): fetch, index, load its ontology.

    Same path as the scheduled refresh, so both share the checkout and its lock. The result row is
    returned, not raised, so the editor can show why a harvest failed or was skipped.
    """

    if self.request.id and not self.request.is_eager:  # eager runs (tests) have no result backend
        self.update_state(state="STARTED", meta={"source": name})
    return refresh_all_sources(only=[name], full=full)


@shared_task(name="helpdesk.run_semantic_clustering_batch")
def run_semantic_clustering_batch() -> dict:
    """Scheduled semantic clustering batch over recent question events."""

    result = build_semantic_clusters(
        window_days=settings.SEMANTIC_CLUSTER_WINDOW_DAYS,
        min_cluster_size=settings.SEMANTIC_CLUSTER_MIN_SIZE,
        similarity_threshold=settings.SEMANTIC_CLUSTER_SIMILARITY_THRESHOLD,
        max_events=settings.SEMANTIC_CLUSTER_MAX_EVENTS,
    )
    return {
        "status": "ok",
        "generatedAt": result["generatedAt"],
        "windowDays": result["windowDays"],
        "totalEvents": result["totalEvents"],
        "clusteredEvents": result["clusteredEvents"],
        "singletonEvents": result["singletonEvents"],
        "clusterCount": len(result["clusters"]),
    }
