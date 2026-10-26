"""
Re-embed every indexed chunk with the other embedding backend, then switch by swapping columns.

Each SourceChunk keeps two vectors: embedding_vector, which retrieval uses and which matches
EMBEDDING_BACKEND, and alternate_vector, the vector of the other backend (hash or semantic). This
command fills alternate_vector while retrieval keeps using embedding_vector, so production answers
as before during the long run. Switching is then one swap of the two columns, and swapping again
restores the previous vectors exactly.

Usage:
    python manage.py reembed_chunks --status   # how many chunks have both vectors
    python manage.py reembed_chunks            # fill the missing alternate vectors; resumable
    python manage.py reembed_chunks --swap     # fill what is still missing, then swap the columns

After --swap, set EMBEDDING_BACKEND to the other backend in the env file and restart the backend and
the worker at once; until then questions are embedded with the old backend (docs/production-deployment.md,
section 13). The index refresh empties alternate_vector of every chunk whose text it changes, so a later
run only embeds those.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-26  |  Modified: 2026-10-26
"""

from __future__ import annotations

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, models, transaction

from helpdesk.models import SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.index_builder import build_chunk_embedding_text

BATCH_SIZE = 128
VECTOR_INDEX = "sourcechunk_embedding_ivfflat_idx"
# The semantic model has 384 dimensions; its vectors are padded with zeros to the column's 1536.
SEMANTIC_DIMENSION = 384


def other_backend() -> str:
    return "hash" if getattr(settings, "EMBEDDING_BACKEND", "hash") == "semantic" else "semantic"


def vector_kind(vector) -> str:
    """'semantic' for a padded semantic vector, 'hash' for a hash vector, 'empty' for none."""
    if vector is None or len(vector) == 0 or not any(vector):
        return "empty"
    return "semantic" if not any(vector[SEMANTIC_DIMENSION:]) else "hash"


def fill_alternate_vectors(backend: str, log=lambda message: None) -> int:
    """Embed every chunk without an alternate vector with `backend`; return how many were embedded.

    Each batch is locked while it is embedded, so an index refresh that changes one of its chunks
    waits and then empties the vector again instead of being overwritten with a stale one."""
    done = 0
    started = time.monotonic()
    while True:
        pks = list(
            SourceChunk.objects.filter(alternate_vector__isnull=True).order_by("pk").values_list("pk", flat=True)[:BATCH_SIZE]
        )
        if not pks:
            return done
        with transaction.atomic():
            chunks = list(
                SourceChunk.objects.select_for_update()
                .filter(pk__in=pks, alternate_vector__isnull=True)
                .only("pk", "text", "doc_type", "chunk_type", "heading", "standards_scope", "repository_url", "source_path")
            )
            inputs = [
                build_chunk_embedding_text(
                    chunk_text=chunk.text,
                    doc_type=chunk.doc_type,
                    chunk_type=chunk.chunk_type,
                    heading=chunk.heading,
                    standards_scope=chunk.standards_scope,
                    repository_url=chunk.repository_url,
                    source_path=chunk.source_path,
                    backend=backend,
                )
                for chunk in chunks
            ]
            for chunk, vector in zip(chunks, build_text_embeddings_batch(inputs, backend=backend)):
                chunk.alternate_vector = vector
            SourceChunk.objects.bulk_update(chunks, ["alternate_vector"])
        done += len(chunks)
        elapsed = time.monotonic() - started
        log(f"{done} embedded, {SourceChunk.objects.filter(alternate_vector__isnull=True).count()} left ({done / max(elapsed, 1e-9):.1f}/s)")


def swap_vectors() -> int:
    """Swap embedding_vector and alternate_vector of every chunk in one transaction; return the row count.

    Refuses when a chunk still has no alternate vector: retrieval would then mix the two backends."""
    with transaction.atomic():
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                # Keeps the index refresh from changing chunks between the check and the swap.
                cursor.execute(f"LOCK TABLE {SourceChunk._meta.db_table} IN SHARE ROW EXCLUSIVE MODE")
        missing = SourceChunk.objects.filter(alternate_vector__isnull=True).count()
        if missing:
            raise CommandError(f"{missing} chunks have no alternate vector; run reembed_chunks again first.")
        # Both sides read the old row, so the values change places.
        swapped = SourceChunk.objects.update(
            embedding_vector=models.F("alternate_vector"), alternate_vector=models.F("embedding_vector")
        )
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_class WHERE relname = %s", [VECTOR_INDEX])
                if cursor.fetchone():
                    # The ivfflat lists were built from the old vectors.
                    cursor.execute(f"REINDEX INDEX {VECTOR_INDEX}")
    return swapped


class Command(BaseCommand):
    help = "Re-embed all chunks with the other embedding backend into alternate_vector; --swap switches the columns."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--status", action="store_true", help="Only report how many chunks have an alternate vector.")
        group.add_argument("--swap", action="store_true", help="Fill what is missing, then swap the two vector columns.")

    def _status(self):
        total = SourceChunk.objects.count()
        missing = SourceChunk.objects.filter(alternate_vector__isnull=True).count()
        sample = SourceChunk.objects.order_by("pk").values_list("embedding_vector", "alternate_vector")[:200]
        in_use = sorted({vector_kind(row[0]) for row in sample})
        alternate = sorted({vector_kind(row[1]) for row in sample if row[1] is not None})
        self.stdout.write(
            f"EMBEDDING_BACKEND={getattr(settings, 'EMBEDDING_BACKEND', 'hash')}; {total} chunks, "
            f"{total - missing} with an alternate vector, {missing} without.\n"
            f"Sample of 200: embedding_vector {'/'.join(in_use) or '-'}, alternate_vector {'/'.join(alternate) or '-'}."
        )

    def handle(self, *args, **options):
        if options["status"]:
            self._status()
            return
        backend = other_backend()
        self.stdout.write(f"Embedding missing alternate vectors with the {backend} backend.")
        filled = fill_alternate_vectors(backend, log=self.stdout.write)
        self.stdout.write(f"Filled {filled} alternate vectors.")
        if options["swap"]:
            swapped = swap_vectors()
            self.stdout.write(
                f"Swapped the vectors of {swapped} chunks: retrieval vectors are now {backend}.\n"
                f"Now set EMBEDDING_BACKEND={backend} and restart the backend and the worker."
            )
