"""
Index the napcore.eu snapshots in docs/napcore/text/ as the NAPCORE source.

Usage:
    python manage.py index_napcore_site                # index the stored snapshots (deploy.sh runs this)
    python manage.py index_napcore_site --fetch        # fetch docs/napcore/sources.txt first
    python manage.py index_napcore_site --fetch --out DIR   # fetch into DIR (the repo's docs/ may be read-only)

A snapshot whose text has not changed since the last run is skipped, so the command is cheap to repeat.
Each document is stored as soon as it is embedded, so an interrupted run resumes where it stopped. deploy.sh
starts it detached (the first run embeds about 3,000 chunks, about 100 minutes on prod) with its output in
/tmp/index_napcore_site.log of the backend container; a lock keeps two runs from overlapping.
--fetch is for adding documents or refreshing them: review the diff of docs/napcore/text/ before
committing it. Fetching needs network access and pypdf; indexing needs neither.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-05  |  Modified: 2026-11-05
"""

from __future__ import annotations

import fcntl
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services import napcore_site


LOCK_PATH = "/tmp/index_napcore_site.lock"


class Command(BaseCommand):
    help = "Index the napcore.eu snapshots stored in docs/napcore/text/ as a retrieval source."

    def add_arguments(self, parser):
        parser.add_argument("--fetch", action="store_true", help="Fetch the pinned documents first.")
        parser.add_argument("--out", help="Write fetched snapshots here instead of docs/napcore/text/; no indexing.")

    def _progress(self, line: str) -> None:
        self.stdout.write(line)
        self.stdout.flush()

    def handle(self, *args, **options):
        if options["fetch"]:
            if options["out"]:
                napcore_site.TEXT_DIR = Path(options["out"])
            failed = 0
            for document, status in napcore_site.fetch_all(napcore_site.read_manifest()):
                failed += status.startswith("failed")
                self.stdout.write(f"{status[:60]:10} {document.url}")
            if failed:
                self.stderr.write(f"{failed} document(s) failed")
            if options["out"]:
                return
        if not napcore_site.TEXT_DIR.is_dir():
            raise CommandError(f"{napcore_site.TEXT_DIR} is missing; run with --fetch")
        with open(LOCK_PATH, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.stdout.write("NAPCORE: another index run is in progress; nothing done")
                return
            counts = napcore_site.index_site(napcore_site.TEXT_DIR, report=self._progress)
        self.stdout.write(
            f"NAPCORE: {counts['indexed']} indexed, {counts['unchanged']} unchanged, "
            f"{counts['removed']} removed, {counts['chunks']} chunks"
        )
