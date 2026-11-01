"""
Generate docs/regulations/eu-legislation-definitions.ttl from the definitions articles of the stored acts.

Usage:
    python manage.py build_legislation_vocabulary          # write the file
    python manage.py build_legislation_vocabulary --check  # fail if the file is out of date

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-01  |  Modified: 2026-11-01
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.regulations import VOCABULARY_PATH, build_vocabulary


class Command(BaseCommand):
    help = "Generate the vocabulary of the EU acts' defined terms."

    def add_arguments(self, parser):
        parser.add_argument("--check", action="store_true", help="Fail if the stored file differs.")

    def handle(self, *args, **options):
        text, concepts, shared = build_vocabulary()
        if options["check"]:
            if not VOCABULARY_PATH.exists() or VOCABULARY_PATH.read_text(encoding="utf-8") != text:
                raise CommandError(f"{VOCABULARY_PATH} is out of date; run build_legislation_vocabulary")
            self.stdout.write("up to date")
            return
        VOCABULARY_PATH.write_text(text, encoding="utf-8")
        self.stdout.write(f"{concepts} concepts, {shared} labels shared with the standards -> {VOCABULARY_PATH}")
