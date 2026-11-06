"""
Index the INSPIRE Transport Networks specification and code lists in docs/inspire/ as the INSPIRE source.

Usage:
    python manage.py index_inspire                    # index the stored files (deploy.sh runs this)
    python manage.py index_inspire --fetch --out DIR  # fetch the pinned specification and its code lists into DIR

A file whose content has not changed since the last run is skipped, so the command is cheap to repeat.
--fetch is for adding or refreshing the files (the repo's docs/ is read-only in the dev containers):
copy them to docs/inspire/ and review the diff before committing. Fetching needs network access;
indexing does not. deploy.sh starts the index detached (about 600 chunks, roughly half an hour on
prod's embedder) with its output in /tmp/index_inspire.log of the backend container.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-05  |  Modified: 2026-11-05
"""

from __future__ import annotations

import fcntl
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services import inspire

LOCK_PATH = "/tmp/index_inspire.lock"


class Command(BaseCommand):
    help = "Index the INSPIRE Transport Networks specification and code lists stored in docs/inspire/."

    def add_arguments(self, parser):
        parser.add_argument("--fetch", action="store_true", help="Fetch the pinned specification and code lists.")
        parser.add_argument("--out", help="Directory to fetch into (required with --fetch); no indexing.")

    def handle(self, *args, **options):
        if options["fetch"]:
            if not options["out"]:
                raise CommandError("--fetch needs --out DIR; copy the files to docs/inspire/ and review them")
            counts = inspire.fetch(Path(options["out"]), report=self.stdout.write)
            self.stdout.write(f"INSPIRE: fetched the specification and {counts['codelists']} code lists")
            if counts["failed"]:
                self.stderr.write(f"{counts['failed']} code list(s) failed")
            return
        if not (inspire.SPEC_PATH.exists() and inspire.CODELISTS_PATH.exists()):
            raise CommandError(f"{inspire.INSPIRE_DIR} is incomplete; run with --fetch --out DIR first")
        with open(LOCK_PATH, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.stdout.write("INSPIRE: another index run is in progress; nothing done")
                return
            results = inspire.index_inspire()
        for part, (status, chunks) in results.items():
            self.stdout.write(f"INSPIRE {part}: {status}, {chunks} chunks")
