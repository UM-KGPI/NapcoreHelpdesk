"""
Index the DATEX II model and documentation pages stored in docs/datex/ as the DATEX II source.

Usage:
    python manage.py index_datex                    # index the stored files (deploy.sh runs this)
    python manage.py index_datex --fetch --out DIR  # fetch the pinned release's model and pages into DIR

A file whose content has not changed since the last run is skipped, so the command is cheap to repeat.
--fetch is for adding or refreshing the release (the repo's docs/ is read-only in the dev containers):
copy the files to docs/datex/ and review the diff before committing. Fetching needs network access;
indexing does not. deploy.sh starts the index detached, after napcore.eu and INSPIRE, with its output
in /tmp/index_datex.log of the backend container.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-06  |  Modified: 2026-11-06
"""

from __future__ import annotations

import fcntl
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services import datex

LOCK_PATH = "/tmp/index_datex.lock"


class Command(BaseCommand):
    help = "Index the DATEX II model and documentation pages stored in docs/datex/."

    def add_arguments(self, parser):
        parser.add_argument("--fetch", action="store_true", help="Fetch the pinned release's model and pages.")
        parser.add_argument("--out", help="Directory to fetch into (required with --fetch); no indexing.")

    def _progress(self, line: str) -> None:
        self.stdout.write(line)
        self.stdout.flush()

    def handle(self, *args, **options):
        if options["fetch"]:
            if not options["out"]:
                raise CommandError("--fetch needs --out DIR; copy the files to docs/datex/ and review them")
            out = Path(options["out"])
            elements = datex.fetch_model(out)
            self.stdout.write(f"DATEX II: model v{datex.VERSION} with {elements} elements")
            counts = datex.fetch_pages(out, report=self._progress)
            self.stdout.write(f"DATEX II: {counts['pages']} pages, {counts['empty']} empty, {counts['failed']} failed")
            return
        if not datex.MODEL_PATH.exists():
            raise CommandError(f"{datex.MODEL_PATH} is missing; run with --fetch --out DIR first")
        with open(LOCK_PATH, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.stdout.write("DATEX II: another index run is in progress; nothing done")
                return
            counts = datex.index_datex(report=self._progress)
        self.stdout.write(
            f"DATEX II: {counts['indexed']} indexed, {counts['unchanged']} unchanged, "
            f"{counts['removed']} removed, {counts['chunks']} chunks"
        )
