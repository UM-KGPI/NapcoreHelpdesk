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
