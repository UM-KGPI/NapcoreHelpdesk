"""
Index the EU legislation in docs/regulations/ (issue #91).

Usage:
    python manage.py index_regulations            # index the stored acts (deploy.sh runs this)
    python manage.py index_regulations --fetch    # download the pinned acts from Cellar first

An act whose file has not changed since the last run is skipped, so the command is cheap to repeat.
--fetch is for adding or updating an act: review the downloaded file in git before committing it.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-01  |  Modified: 2026-11-01
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.regulations import ACTS, fetch_act, index_act


class Command(BaseCommand):
    help = "Index the EU legislation stored in docs/regulations/ as a retrieval source."

    def add_arguments(self, parser):
        parser.add_argument("--fetch", action="store_true", help="Download the pinned acts from Cellar first.")

    def handle(self, *args, **options):
        for act in ACTS:
            if options["fetch"]:
                fetch_act(act)
                self.stdout.write(f"fetched {act.celex}")
            if not act.path.exists():
                raise CommandError(f"{act.path} is missing; run with --fetch")
            status, count = index_act(act)
            self.stdout.write(f"{status:9} {act.celex}  {count} chunks  {act.name}")
