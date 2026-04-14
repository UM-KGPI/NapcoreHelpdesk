from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.neo4j_importer import build_neo4j_statements, submit_neo4j_statements


class Command(BaseCommand):
    help = "Import a semantic graph snapshot JSON into Neo4j (dry-run by default)."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True, help="Path to semantic graph snapshot JSON.")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Execute import to Neo4j. Without this flag, command performs dry-run only.",
        )
        parser.add_argument(
            "--database",
            default="",
            help="Neo4j database name override (defaults to NEO4J_DATABASE).",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"]).expanduser().resolve()
        apply_changes = bool(options["apply"])
        database = (options.get("database") or "").strip() or settings.NEO4J_DATABASE

        if not input_path.exists() or not input_path.is_file():
            raise CommandError(f"--input file not found: {input_path}")

        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise CommandError("Snapshot JSON must be an object")

        statements = build_neo4j_statements(payload)
        stats = payload.get("stats", {}) if isinstance(payload.get("stats"), dict) else {}

        self.stdout.write("Semantic graph Neo4j import plan:")
        self.stdout.write(f"input={input_path}")
        self.stdout.write(f"database={database}")
        self.stdout.write(f"statement_count={len(statements)}")
        self.stdout.write(f"concept_nodes={stats.get('conceptNodeCount', 0)}")
        self.stdout.write(f"chunk_nodes={stats.get('chunkNodeCount', 0)}")
        self.stdout.write(f"mention_edges={stats.get('mentionEdgeCount', 0)}")
        self.stdout.write(f"related_edges={stats.get('relatedEdgeCount', 0)}")

        if not apply_changes:
            self.stdout.write(self.style.WARNING("Dry-run only. Use --apply to execute Neo4j import."))
            return

        if not settings.NEO4J_ENABLED:
            raise CommandError("NEO4J_ENABLED is False. Enable it before running --apply.")
        if not settings.NEO4J_URI:
            raise CommandError("NEO4J_URI is required when running --apply.")
        if not settings.NEO4J_PASSWORD:
            raise CommandError("NEO4J_PASSWORD is required when running --apply.")

        try:
            result = submit_neo4j_statements(
                uri=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
                database=database,
                statements=statements,
            )
        except Exception as exc:  # pragma: no cover - network/runtime path
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Neo4j semantic graph import completed."))
        self.stdout.write(f"endpoint={result['endpoint']}")
        self.stdout.write(f"statement_count={result['statementCount']}")
