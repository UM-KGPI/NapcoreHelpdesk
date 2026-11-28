"""Delete GraphDB graphs whose source file was removed, then check that no NITS data is left.

Usage: python manage.py retire_graphdb_graphs [--timeout 600] [--dry-run]
The NITS upper ontology was removed on 2026-10-20 (#83). Its graphs (graphdb_client.RETIRED_GRAPH_URIS) are also
deleted by `load_graphdb_ontologies --replace`, which reloads every ontology as well (the last three loads took
13 to 17 seconds, 2026-11-19). This deletes just the retired graphs (a no-op when they are already gone) and then
asks GraphDB, across all graphs, whether any statement still uses the NITS namespace. deploy.sh runs it on EVERY
deploy, so a graph added to the retired list is deleted by the next deploy; the deploy fails if NITS data is still
there; the failure first lists the named graphs that hold it (with counts) and a few sample statements.

Output: one line per retired graph that holds triples (name and count, printed before it is deleted), then one
summary line that starts with SUMMARY_PREFIX so that it can be found in a deploy log (deploy.sh reads it too).
The count is one query; if it fails the graphs are deleted as before and the summary says the count was unavailable.
--dry-run prints the same and deletes nothing (it skips the NITS check, which only makes sense after deleting).

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-11  |  Modified: 2026-11-12
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.graphdb_client import RETIRED_GRAPH_URIS, delete_named_graph, execute_sparql_query

# Fixed, greppable start of the summary line. deploy.sh matches it: change both together.
SUMMARY_PREFIX = "RETIRE-GRAPHS:"

_COUNT_QUERY = "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g"

NITS_NAMESPACE = "https://napcore.eu/ontology/nits#"

# Without GRAPH, GraphDB's default graph is the union of all named graphs, explicit and inferred.
NITS_ASK_QUERY = (
    "ASK { ?s ?p ?o FILTER("
    f'STRSTARTS(STR(?s), "{NITS_NAMESPACE}") || STRSTARTS(STR(?p), "{NITS_NAMESPACE}") '
    f'|| (isIRI(?o) && STRSTARTS(STR(?o), "{NITS_NAMESPACE}"))'
    ") }"
)


_NITS_FILTER = NITS_ASK_QUERY[len("ASK { ?s ?p ?o ") : -len(" }")]

# Named graphs that hold NITS statements (explicit statements only: GRAPH ?g never matches inferred ones).
NITS_GRAPHS_QUERY = (
    "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o " + _NITS_FILTER + " } } "
    "GROUP BY ?g ORDER BY DESC(?n) LIMIT 50"
)
NITS_SAMPLE_QUERY = "SELECT ?s ?p ?o WHERE { ?s ?p ?o " + _NITS_FILTER + " } LIMIT 5"


def _bindings(result) -> list[dict]:
    if not isinstance(result, dict):
        return []
    rows = result.get("results", {}).get("bindings", [])
    return [{key: cell.get("value", "") for key, cell in row.items()} for row in rows]


def _graph_counts(connection: dict) -> dict[str, int] | None:
    """Triples per named graph now in GraphDB, one query; None when it cannot be read."""
    result = execute_sparql_query(sparql_query=_COUNT_QUERY, **connection)
    try:
        return {row["g"]["value"]: int(row["n"]["value"]) for row in result["results"]["bindings"]}
    except (KeyError, ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = "Delete the retired GraphDB graphs (NITS) and fail if any NITS statement remains."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=600,
            help="Seconds to wait for each GraphDB request (deleting a graph can trigger reinference).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be deleted (graph names and triple counts) and delete nothing.",
        )

    def handle(self, *args, **options):
        if not settings.GRAPHDB_ENABLED:
            self.stdout.write("GRAPHDB_ENABLED is False; nothing to retire.")
            return
        endpoint = settings.GRAPHDB_SPARQL_ENDPOINT
        if not endpoint:
            raise CommandError("GRAPHDB_SPARQL_ENDPOINT is required.")
        connection = {
            "endpoint": endpoint,
            "repository": settings.GRAPHDB_REPOSITORY,
            "username": getattr(settings, "GRAPHDB_USER", ""),
            "password": getattr(settings, "GRAPHDB_PASSWORD", ""),
            "timeout_seconds": options["timeout"],
        }

        dry_run = bool(options.get("dry_run"))
        counts = _graph_counts(connection)
        deleted_graphs = 0
        deleted_triples = 0
        unknown_graphs = 0
        for graph_uri in RETIRED_GRAPH_URIS:
            if counts is None:
                unknown_graphs += 1
                self.stdout.write(f"{'Would delete' if dry_run else 'Deleting'} {graph_uri} (triple count unavailable)")
            elif counts.get(graph_uri, 0) > 0:
                deleted_graphs += 1
                deleted_triples += counts[graph_uri]
                self.stdout.write(
                    f"{'Would delete' if dry_run else 'Deleting'} {graph_uri}: {counts[graph_uri]} triples"
                )
            if dry_run:
                continue
            try:
                delete_named_graph(graph_uri=graph_uri, **connection)
            except Exception as exc:  # noqa: BLE001 - any failure means the graph may still be there
                raise CommandError(f"Could not delete {graph_uri}: {exc}") from exc
            if counts is not None and counts.get(graph_uri, 0) == 0:
                self.stdout.write(f"Already absent or empty: {graph_uri}")

        verb = "would delete" if dry_run else "deleted"
        if counts is None:
            summary = (
                f"{SUMMARY_PREFIX} {verb}: triple count unavailable "
                f"({unknown_graphs} retired graphs, each deleted if present)"
            )
        elif deleted_graphs:
            summary = f"{SUMMARY_PREFIX} {verb} {deleted_graphs} graphs with {deleted_triples} triples in total"
        else:
            summary = f"{SUMMARY_PREFIX} nothing {'to delete' if dry_run else 'deleted'}: no retired graph holds triples"
        self.stdout.write(summary)
        if dry_run:
            return

        result = execute_sparql_query(sparql_query=NITS_ASK_QUERY, **connection)
        if not isinstance(result, dict) or not isinstance(result.get("boolean"), bool):
            raise CommandError("Could not check GraphDB for NITS statements (no ASK result).")
        if result["boolean"]:
            self._report_leftovers(connection)
            raise CommandError(f"GraphDB still holds statements in {NITS_NAMESPACE}.")
        self.stdout.write(self.style.SUCCESS("No NITS statements in GraphDB."))

    def _report_leftovers(self, connection: dict) -> None:
        graphs = _bindings(execute_sparql_query(sparql_query=NITS_GRAPHS_QUERY, **connection))
        if graphs:
            self.stdout.write("Named graphs with NITS statements:")
            for row in graphs:
                self.stdout.write(f"  {row.get('n', '?')}\t{row.get('g', '?')}")
        else:
            self.stdout.write("No named graph holds NITS statements explicitly (inferred or default graph only).")
        for row in _bindings(execute_sparql_query(sparql_query=NITS_SAMPLE_QUERY, **connection)):
            self.stdout.write(f"  sample: {row.get('s', '')} {row.get('p', '')} {row.get('o', '')}")
