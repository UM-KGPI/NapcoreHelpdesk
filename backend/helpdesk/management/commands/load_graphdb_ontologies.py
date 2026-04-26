from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.graphdb_client import load_default_ontology_graphs
from helpdesk.services.ontology_registry import record_ontology_asset_versions


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
            help="Comma-separated subset for artifact rules (netex,opra,siri,datex).",
        )

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
            self.stdout.write(
                f"loaded file={item['filePath']} graph={item['graphUri']} replaced={item['replaced']}"
            )
        for item in ontology_versions:
            self.stdout.write(
                f"tracked ontology={item.ontology_key} version={item.version} hash={item.content_hash[:12]}"
            )
