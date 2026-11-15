"""
Cut the indexed XML examples again at element boundaries, in a database named on the command line.

For step R0 of docs/plans/2026-11-15-xml-example-chunks.md: the element cut (services/xml_example_cut.py) is
measured on a copy of the dev database before any index is changed. The command refuses to run unless
--database names the database Django is connected to, so it cannot write to another one by mistake.

For each XML example in the index (doc_type example, .xml) it reads the file from the given checkout,
checks that the line cut of that file gives exactly the indexed chunks (so only the cut changes, not the
content), cuts it anew, embeds the pieces and replaces the file's chunks in one transaction. A file that is
already cut this way is skipped, so a stopped run can be started again. Other sources are not touched.

    python manage.py recut_examples --database napcore_helpdesk_copy \
        --checkout https://github.com/TransmodelEcosystem/NeTEx=/path/to/NeTEx [--max-chars 1200] [--no-summary]

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-15  |  Modified: 2026-11-15
"""

from __future__ import annotations

import collections
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from helpdesk.models import SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.index_builder import (
    ExampleCut,
    build_chunk_embedding_text,
    build_chunk_id,
    compute_chunk_quality,
    enrich_xml_example_text,
    example_xml_chunks,
    infer_doc_type,
    infer_scope,
    split_xml,
)


class Command(BaseCommand):
    help = "Re-cut the indexed XML examples at element boundaries in the named database (R0 measurement)."

    def add_arguments(self, parser):
        parser.add_argument("--database", required=True, help="Name of the database to write; must be the connected one.")
        parser.add_argument("--checkout", action="append", default=[], help="REPO_URL=PATH, once per repository.")
        parser.add_argument("--max-chars", type=int, default=1200)
        parser.add_argument("--no-summary", action="store_true", help="Do not append the XML semantic summary.")
        parser.add_argument("--dry-run", action="store_true", help="Count the pieces; write nothing.")

    def handle(self, *args, **options):
        connected = connection.settings_dict["NAME"]
        self.stdout.write(f"connected to database {connected}")
        if options["database"] != connected:
            raise CommandError(f"--database {options['database']} is not the connected database {connected}.")
        roots = {}
        for item in options["checkout"]:
            url, _, path = item.partition("=")
            roots[url.rstrip("/")] = Path(path)
        cut = ExampleCut(max_chars=options["max_chars"], summary=not options["no_summary"])

        examples = SourceChunk.objects.filter(doc_type="example", source_path__iendswith=".xml")
        files = sorted(set(examples.values_list("repository_url", "source_path").order_by()))
        stats = collections.Counter()
        started = time.monotonic()
        for number, (repo_url, source_path) in enumerate(files, 1):
            root = roots.get(repo_url.rstrip("/"))
            if root is None or not (root / source_path).is_file():
                stats["no checkout"] += 1
                continue
            raw = (root / source_path).read_text(encoding="utf-8", errors="ignore")
            existing = list(examples.filter(repository_url=repo_url, source_path=source_path))
            old_texts = collections.Counter(c.text for c in existing)
            line_cut = collections.Counter(
                enrich_xml_example_text(chunk_text=text, source_path=source_path) for text, _, _ in split_xml(raw)
            )
            new = example_xml_chunks(raw, source_path, cut)
            new_ids = [build_chunk_id(repo_url, source_path, i, c["text"]) for i, c in enumerate(new)]
            # Compared by text: a chunk id is built from the text before the summary, so ids alone would take
            # a one-piece file's old chunk (with its summary) for a new one without.
            if old_texts == collections.Counter(c["text"] for c in new) and {c.chunk_id for c in existing} == set(new_ids):
                stats["already cut"] += 1
                continue
            if old_texts != line_cut:
                stats["content differs from the index"] += 1
                continue
            stats["files"] += 1
            stats["pieces"] += len(new)
            if options["dry_run"]:
                continue
            commit_sha = existing[0].commit_sha
            label = existing[0].label or source_path
            records, inputs = [], []
            for chunk_id, chunk in zip(new_ids, new):
                scope = infer_scope(source_path, chunk["body"], repo_url)
                doc_type = infer_doc_type(source_path, "schema_fragment", "", chunk["body"])
                records.append(
                    SourceChunk(
                        repository_url=repo_url,
                        commit_sha=commit_sha,
                        source_path=source_path,
                        chunk_id=chunk_id,
                        label=label,
                        text=chunk["text"],
                        standards_scope=scope,
                        quality_score=compute_chunk_quality(
                            source_path=source_path,
                            chunk_text=chunk["text"],
                            chunk_type="schema_fragment",
                            heading="",
                            doc_type=doc_type,
                            standards_scope=scope,
                        ),
                        chunk_type="schema_fragment",
                        doc_type=doc_type,
                        heading="",
                        structured_metadata={},
                        alternate_vector=None,
                    )
                )
                inputs.append(
                    build_chunk_embedding_text(
                        chunk_text=chunk["text"],
                        doc_type=doc_type,
                        chunk_type="schema_fragment",
                        heading="",
                        standards_scope=scope,
                        repository_url=repo_url,
                        source_path=source_path,
                    )
                )
            for record, vector in zip(records, build_text_embeddings_batch(inputs)):
                record.embedding_vector = vector
            with transaction.atomic():
                SourceChunk.objects.filter(pk__in=[c.pk for c in existing]).delete()
                # In file order, so primary keys follow the order of the pieces.
                SourceChunk.objects.bulk_create(records, batch_size=500)
            if number % 10 == 0 or len(new) > 500:
                elapsed = time.monotonic() - started
                self.stdout.write(
                    f"{number}/{len(files)} files, {stats['pieces']} pieces, {elapsed:.0f} s, "
                    f"{stats['pieces'] / max(elapsed, 1e-9):.1f} pieces/s"
                )
        elapsed = time.monotonic() - started
        self.stdout.write(f"done in {elapsed:.0f} s: {dict(stats)}")
