"""
Write the ontology's classes on every indexed piece (structured_metadata["concepts"], services/chunk_concepts.py),
in a database named on the command line. No embedding: prose pieces are compared by their stored vectors.

For step 3 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md: the labels are measured on a copy
of the dev database first. The command refuses to run unless --database names the database Django is connected
to. A piece that already carries the key is skipped unless --again, so a stopped run can be started again.

    python manage.py label_chunk_concepts --database napcore_helpdesk_copy [--again] [--report out.json]

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-17  |  Modified: 2026-11-17
"""

from __future__ import annotations

import collections
import json
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from helpdesk.models import SourceChunk
from helpdesk.services import chunk_concepts as cc

BATCH = 2000


class Command(BaseCommand):
    help = "Write the ontology's classes on every indexed piece (structured_metadata.concepts)."

    def add_arguments(self, parser):
        parser.add_argument("--database", required=True, help="Must equal the database Django is connected to.")
        parser.add_argument("--again", action="store_true", help="Label pieces that already carry labels too.")
        parser.add_argument("--report", default="", help="Write counts by kind to this JSON file.")

    def handle(self, *args, **options):
        if options["database"] != connection.settings_dict["NAME"]:
            raise CommandError(f"--database {options['database']} is not the connected database {connection.settings_dict['NAME']}")
        from helpdesk.services.semantic_graph import GRAPH_CONCEPT_ALIASES

        if cc.concept_index() is None:
            raise CommandError("no concept vectors: run build_concept_vectors first")
        known = set(GRAPH_CONCEPT_ALIASES) | set(cc.concept_index()[0])
        rows = SourceChunk.objects.order_by("id")
        if not options["again"]:
            rows = rows.exclude(structured_metadata__has_key=cc.META_KEY)
        counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        started = time.monotonic()
        ids = list(rows.values_list("id", flat=True))
        for start in range(0, len(ids), BATCH):
            batch_ids = ids[start : start + BATCH]
            updates = []
            batch = list(SourceChunk.objects.filter(id__in=batch_ids).only(
                "id", "text", "doc_type", "chunk_type", "standards_scope", "structured_metadata"
            ))
            # Vectors only for the pieces compared by meaning (an XML example piece is labelled by its elements).
            vectors = dict(
                SourceChunk.objects.filter(id__in=[c.id for c in batch])
                .exclude(doc_type="example", chunk_type="schema_fragment")
                .values_list("id", "embedding_vector")
            )
            for chunk in batch:
                vector = vectors.get(chunk.id)
                nearest = None
                if vector is not None and len(vector):
                    nearest = set(cc.nearest_concepts(vector, cc.NEAREST_CONCEPTS))
                concepts = cc.piece_concepts(
                    text=chunk.text,
                    doc_type=chunk.doc_type,
                    chunk_type=chunk.chunk_type,
                    standards_scope=chunk.standards_scope,
                    structured_metadata=chunk.structured_metadata,
                    nearest=nearest,
                    known=known,
                )
                kind = f"{chunk.doc_type}/{chunk.chunk_type}"
                counts[kind]["pieces"] += 1
                counts[kind]["labelled"] += bool(concepts)
                counts[kind]["labels"] += len(concepts)
                updates.append((chunk.id, json.dumps(concepts)))
            with connection.cursor() as cursor:
                values = ",".join(["(%s, %s::jsonb)"] * len(updates))
                cursor.execute(
                    "UPDATE helpdesk_sourcechunk AS t SET structured_metadata = "
                    f"t.structured_metadata::jsonb || jsonb_build_object('{cc.META_KEY}', v.c) "
                    f"FROM (VALUES {values}) AS v(id, c) WHERE t.id = v.id",
                    [x for pair in updates for x in pair],
                )
            self.stdout.write(f"{start + len(batch_ids)}/{len(ids)} pieces, {round(time.monotonic() - started)} s")
        report = {kind: dict(c) for kind, c in sorted(counts.items(), key=lambda kv: -kv[1]["pieces"])}
        report["seconds"] = round(time.monotonic() - started)
        if options["report"]:
            with open(options["report"], "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=1)
        self.stdout.write(json.dumps(report))
