from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.graphdb_client import (
    RETIRED_GRAPH_URIS,
    execute_sparql_query,
    load_default_ontology_graphs,
    plan_default_ontology_graphs,
)
from helpdesk.services.ontology_registry import record_ontology_asset_versions


def count_turtle_triples(path) -> int | None:
    """Triples in a Turtle file, parsed locally; None when rdflib is missing (it is in requirements.txt, but a
    developer environment installed before that may lack it, and the plan is still useful without counts)."""
    try:
        import rdflib
    except ImportError:
        return None
    graph = rdflib.Graph()
    graph.parse(str(path), format="turtle")
    return len(graph)


_COUNT_QUERY = "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g"


def current_graph_counts(*, endpoint, repository, username, password, timeout_seconds) -> dict[str, int] | None:
    """Triples per named graph now in GraphDB, one query; None when it cannot be read."""
    if not endpoint or not settings.GRAPHDB_ENABLED:
        return None
    result = execute_sparql_query(
        sparql_query=_COUNT_QUERY,
        endpoint=endpoint,
        repository=repository,
        username=username,
        password=password,
        timeout_seconds=timeout_seconds,
    )
    if not result:
        return None
    try:
        return {
            row["g"]["value"]: int(row["n"]["value"]) for row in result.get("results", {}).get("bindings", [])
        }
    except (KeyError, ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = (
        "Load default ontology Turtle files into GraphDB named graphs "
        "(dry-run by default)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Execute upload. Without this flag, command runs as dry-run only.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            default=False,
            help="Clear target named graph before upload.",
        )
        parser.add_argument(
            "--endpoint",
            default="",
            help="GraphDB endpoint override (defaults to GRAPHDB_SPARQL_ENDPOINT).",
        )
        parser.add_argument(
            "--repository",
            default="",
            help="GraphDB repository override (defaults to GRAPHDB_REPOSITORY).",
        )
        parser.add_argument(
            "--include-artifact-rules",
            action="store_true",
            help=(
                "Also load artifact-derived rules ontologies. Disabled by default because "
                "these rules should only be active for standard-scoped normative reasoning."
            ),
        )
        parser.add_argument(
            "--artifact-rule-standards",
            default="",
            help="Comma-separated subset for artifact rules (netex,opra,siri).",
        )

    def _write_plan(self, plan: dict, counts: dict[str, int] | None) -> None:
        """Print what the load would do: each graph with its file, then each retired graph it would delete."""
        self.stdout.write("graphs to load:")
        for entry in plan["graphs"]:
            action = "replace" if entry["replace"] else "append to"
            graph_uri = entry["graphUri"]
            now = f"{counts.get(graph_uri, 0)} triples now in GraphDB" if counts is not None else "current count unavailable"
            if not entry["fileExists"]:
                source = "file MISSING (the load would stop here)"
            else:
                size = entry["filePath"].stat().st_size
                triples = count_turtle_triples(entry["filePath"])
                source = f"{size} bytes, " + (f"{triples} triples" if triples is not None else "triples not counted (rdflib not installed)")
            self.stdout.write(f"  {action} graph={graph_uri} from file={entry['filePath']} ({source}; {now})")
        if plan["retired"]:
            self.stdout.write("retired graphs to delete (no-op when absent):")
            for graph_uri in plan["retired"]:
                now = f"{counts.get(graph_uri, 0)} triples now" if counts is not None else "current count unavailable"
                self.stdout.write(f"  delete graph={graph_uri} ({now})")
        else:
            self.stdout.write(
                "retired graphs are listed and deleted only with --replace; "
                "this plan appends, so none is deleted (every deploy deletes them anyway, see retire_graphdb_graphs):"
            )
            for graph_uri in RETIRED_GRAPH_URIS:
                now = f"{counts.get(graph_uri, 0)} triples now" if counts is not None else "current count unavailable"
                self.stdout.write(f"  graph={graph_uri} ({now}) not deleted in append mode")

    def handle(self, *args, **options):
        apply_changes = bool(options.get("apply"))
        replace = bool(options.get("replace"))
        include_artifact_rules = bool(options.get("include_artifact_rules"))
        artifact_rule_standards_raw = (options.get("artifact_rule_standards") or "").strip()
        artifact_rule_standards = {
            item.strip().lower()
            for item in artifact_rule_standards_raw.split(",")
            if item.strip()
        }
        endpoint = (options.get("endpoint") or "").strip() or settings.GRAPHDB_SPARQL_ENDPOINT
        repository = (options.get("repository") or "").strip() or settings.GRAPHDB_REPOSITORY

        self.stdout.write("GraphDB ontology load plan:")
        self.stdout.write(f"endpoint={endpoint or '(unset)'}")
        self.stdout.write(f"repository={repository or '(unset)'}")
        self.stdout.write(f"replace={replace}")
        self.stdout.write(f"include_artifact_rules={include_artifact_rules}")
        if artifact_rule_standards:
            self.stdout.write(
                f"artifact_rule_standards={','.join(sorted(artifact_rule_standards))}"
            )

        try:
            plan = plan_default_ontology_graphs(
                replace=replace,
                include_artifact_rules=include_artifact_rules,
                artifact_rule_standards=artifact_rule_standards or None,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self._write_plan(
            plan,
            counts=current_graph_counts(
                endpoint=endpoint,
                repository=repository,
                username=getattr(settings, "GRAPHDB_USER", ""),
                password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                timeout_seconds=settings.GRAPHDB_TIMEOUT_SECONDS,
            ),
        )

        if not apply_changes:
            self.stdout.write(self.style.WARNING("Dry-run only. Use --apply to execute GraphDB upload."))
            return

        if not settings.GRAPHDB_ENABLED:
            raise CommandError("GRAPHDB_ENABLED is False. Enable it before running --apply.")
        if not endpoint:
            raise CommandError("GRAPHDB_SPARQL_ENDPOINT is required when running --apply.")

        try:
            results = load_default_ontology_graphs(
                endpoint=endpoint,
                repository=repository,
                timeout_seconds=settings.GRAPHDB_TIMEOUT_SECONDS,
                username=getattr(settings, "GRAPHDB_USER", ""),
                password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                replace=replace,
                include_artifact_rules=include_artifact_rules,
                artifact_rule_standards=artifact_rule_standards or None,
            )
            loaded_ontology_keys = {
                str(item.get("ontologyKey", "")).strip()
                for item in results
                if str(item.get("ontologyKey", "")).strip()
            }
            ontology_versions = record_ontology_asset_versions(
                graphdb_repository=repository,
                loaded=True,
                loaded_ontology_keys=loaded_ontology_keys,
            )
        except Exception as exc:  # pragma: no cover - network/runtime path
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("GraphDB ontology load completed."))
        for item in results:
            if item.get("retired"):
                self.stdout.write(f"deleted retired graph={item['graphUri']}")
                continue
            self.stdout.write(
                f"loaded file={item['filePath']} graph={item['graphUri']} replaced={item['replaced']}"
            )
        for item in ontology_versions:
            self.stdout.write(
                f"tracked ontology={item.ontology_key} version={item.version} hash={item.content_hash[:12]}"
            )
