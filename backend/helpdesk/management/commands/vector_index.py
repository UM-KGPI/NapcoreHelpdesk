"""
Build (or drop) the vector index on the numbers the embedder fills, the index the nearest-row search uses when
VECTOR_INDEX_DIMENSIONS is set (retrieval_gateway._filled_numbers_distance; plan
docs/plans/2026-11-15-sources-prepared-for-semantic-search.md, step 2b).

It is a command and not a migration on purpose: the index needs pgvector 0.7 or later (subvector, halfvec), and
building it is a decision per database, taken together with the settings that make the search use it. The
expression is written from the same settings as the query, so the two cannot differ. Like prepare_index, it
refuses to run unless --database names the database Django is connected to.

    python manage.py vector_index --database napcore_helpdesk [--lists 100] [--drop] [--dry-run]

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-18  |  Modified: 2026-11-18
"""

from __future__ import annotations

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

INDEX_NAME = "sourcechunk_embedding_filled_ivfflat_idx"
MIN_PGVECTOR = (0, 7, 0)


def index_sql(dimensions: int, half_precision: bool, lists: int) -> str:
    kind = "halfvec" if half_precision else "vector"
    return (
        f"CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON helpdesk_sourcechunk USING ivfflat "
        f"((subvector(embedding_vector, 1, {int(dimensions)})::{kind}({int(dimensions)})) {kind}_cosine_ops) "
        f"WITH (lists = {int(lists)})"
    )


def pgvector_version(cursor) -> tuple[int, ...] | None:
    cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    row = cursor.fetchone()
    if not row:
        return None
    return tuple(int(part) for part in row[0].split(".")[:3] if part.isdigit())


class Command(BaseCommand):
    help = "Build or drop the vector index on the filled numbers (VECTOR_INDEX_DIMENSIONS, VECTOR_INDEX_HALF_PRECISION)."

    def add_arguments(self, parser):
        parser.add_argument("--database", required=True, help="Name of the database; must be the connected one.")
        parser.add_argument("--lists", type=int, default=100, help="ivfflat lists (default 100, as measured).")
        parser.add_argument("--drop", action="store_true", help="Drop the index instead.")
        parser.add_argument("--dry-run", action="store_true", help="Print the statement and the checks; change nothing.")

    def handle(self, *args, **options):
        connected = connection.settings_dict["NAME"]
        if options["database"] != connected:
            raise CommandError(f"--database {options['database']} is not the connected database {connected}.")
        if connection.vendor != "postgresql":
            raise CommandError("The vector index needs PostgreSQL with pgvector.")
        with connection.cursor() as cursor:
            if options["drop"]:
                statement = f"DROP INDEX IF EXISTS {INDEX_NAME}"
                self.stdout.write(statement)
                if not options["dry_run"]:
                    cursor.execute(statement)
                return
            dimensions = int(getattr(settings, "VECTOR_INDEX_DIMENSIONS", 0) or 0)
            if not 0 < dimensions < 1536:
                raise CommandError("VECTOR_INDEX_DIMENSIONS is not set: the search would not use this index.")
            version = pgvector_version(cursor)
            if version is None or version < MIN_PGVECTOR:
                raise CommandError(f"pgvector {version} is older than 0.7: no subvector or halfvec.")
            statement = index_sql(dimensions, bool(getattr(settings, "VECTOR_INDEX_HALF_PRECISION", False)), options["lists"])
            self.stdout.write(f"pgvector {'.'.join(map(str, version))}; {statement}")
            if options["dry_run"]:
                return
            started = time.monotonic()
            cursor.execute("SET maintenance_work_mem = '256MB'")
            cursor.execute("SET max_parallel_maintenance_workers = 0")
            cursor.execute(statement)
            cursor.execute("ANALYZE helpdesk_sourcechunk")
            cursor.execute("SELECT pg_size_pretty(pg_relation_size(%s))", [INDEX_NAME])
            size = cursor.fetchone()[0]
        self.stdout.write(f"built in {time.monotonic() - started:.1f} s (with ANALYZE), {size}")
