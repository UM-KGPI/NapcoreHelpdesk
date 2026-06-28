"""
Runtime dependency checks for optional infrastructure services.

Verifies that GraphDB is reachable and required named graphs are loaded
before semantic operations are attempted. Used by the health-ready probe
and as a guard in the answer orchestration path.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-26  |  Modified: 2026-06-28
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def graph_runtime_issues() -> list[str]:
    issues: list[str] = []

    if getattr(settings, "GRAPH_RAG_ENABLED", False):
        if not getattr(settings, "GRAPHDB_ENABLED", False):
            issues.append("GRAPHDB_ENABLED must be True when GRAPH_RAG_ENABLED is enabled")
        if not str(getattr(settings, "GRAPHDB_SPARQL_ENDPOINT", "") or "").strip():
            issues.append("GRAPHDB_SPARQL_ENDPOINT must be configured when GRAPH_RAG_ENABLED is enabled")

    return issues


def ensure_graph_runtime_ready() -> None:
    issues = graph_runtime_issues()
    if issues:
        raise ImproperlyConfigured("Graph runtime is not ready: " + "; ".join(issues))
