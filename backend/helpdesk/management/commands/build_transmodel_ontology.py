"""
Generate docs/ontology/standards/transmodel.ttl from the Transmodel Enterprise Architect model.

The model (.qea, an SQLite file) is not public; it is read in place, read-only, and never copied into the
repository. helpdesk.services.transmodel_model holds the profile and the rules; the output is deterministic
(no timestamp) and includes the EA GUID section, so the file is rebuilt from the model with this command alone.

Usage:
    python manage.py build_transmodel_ontology --qea /path/to/TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea
    python manage.py build_transmodel_ontology --qea ... --out /tmp/transmodel.ttl
    python manage.py build_transmodel_ontology --qea ... --members     # with the facts of a class card

Never touches GraphDB; load the graph with load_graphdb_ontologies afterwards.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-24  |  Modified: 2026-11-25
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.transmodel_model import build_turtle

DEFAULT_OUT = Path(__file__).resolve().parents[4] / "docs" / "ontology" / "standards" / "transmodel.ttl"


class Command(BaseCommand):
    help = "Write transmodel.ttl from the Transmodel Enterprise Architect model (generated only, deterministic)."

    def add_arguments(self, parser):
        parser.add_argument("--qea", type=Path, required=True, help="Transmodel Enterprise Architect model (.qea)")
        parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Turtle file to write")
        parser.add_argument(
            "--members",
            action="store_true",
            help="also write the facts of a class card (attributes, types, bounds, values), without labels",
        )

    def handle(self, *args, **options):
        qea: Path = options["qea"]
        if not qea.is_file():
            raise CommandError(f"model not found: {qea}")
        stats: dict = {}
        try:
            text = build_turtle(qea, members=bool(options["members"]), stats=stats)
        except ValueError as error:
            raise CommandError(str(error)) from error
        out: Path = options["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        classes = sum(1 for line in text.splitlines() if line.endswith(" a owl:Class ;"))
        properties = sum(1 for line in text.splitlines() if line.endswith(" a owl:ObjectProperty ;"))
        self.stdout.write(self.style.SUCCESS(f"wrote {out} ({classes} classes, {properties} object properties)"))
        if options["members"]:
            self.stdout.write("members: " + ", ".join(f"{key} {value}" for key, value in stats.items()))
