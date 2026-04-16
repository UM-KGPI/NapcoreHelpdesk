from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.graphdb_client import load_default_ontology_graphs


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

    def handle(self, *args, **options):
        apply_changes = bool(options.get("apply"))
        replace = bool(options.get("replace"))
        endpoint = (options.get("endpoint") or "").strip() or settings.GRAPHDB_SPARQL_ENDPOINT
        repository = (options.get("repository") or "").strip() or settings.GRAPHDB_REPOSITORY

        self.stdout.write("GraphDB ontology load plan:")
        self.stdout.write(f"endpoint={endpoint or '(unset)'}")
        self.stdout.write(f"repository={repository or '(unset)'}")
        self.stdout.write(f"replace={replace}")

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
            )
        except Exception as exc:  # pragma: no cover - network/runtime path
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("GraphDB ontology load completed."))
        for item in results:
            self.stdout.write(
                f"loaded file={item['filePath']} graph={item['graphUri']} replaced={item['replaced']}"
            )