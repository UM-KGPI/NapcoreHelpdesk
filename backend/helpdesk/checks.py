"""
Django system checks for required helpdesk configuration.

Validates that all mandatory settings (JWT_SECRET, embedding endpoint, etc.)
are present at startup, failing loudly with descriptive errors rather than
silently misbehaving at request time.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from django.conf import settings
from django.core.checks import Error, register


@register()
def helpdesk_runtime_checks(app_configs, **kwargs):
    errors = []

    if getattr(settings, "GRAPH_RAG_ENABLED", False):
        if not getattr(settings, "GRAPHDB_ENABLED", False):
            errors.append(
                Error(
                    "GRAPH_RAG_ENABLED requires GRAPHDB_ENABLED=True.",
                    id="helpdesk.E001",
                )
            )
        if not str(getattr(settings, "GRAPHDB_SPARQL_ENDPOINT", "") or "").strip():
            errors.append(
                Error(
                    "GRAPH_RAG_ENABLED requires GRAPHDB_SPARQL_ENDPOINT to be configured.",
                    id="helpdesk.E002",
                )
            )

    return errors
