"""
Add the EA GUID of each class to docs/ontology/standards/transmodel.ttl.

Reads the GUIDs from the Transmodel Enterprise Architect model (.qea) and appends one tmalign:eaGuid per
class (e.g. "{8E3A5314-957E-4033-9057-F6F7530A0111}" for SINGLE JOURNEY) in a marked section at the end
of the file; a rerun replaces that section, so the result is the same each time. The triples above the
section are not changed.

Usage:
    python manage.py add_transmodel_guids --model /path/to/TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea
    python manage.py add_transmodel_guids --model ... --output /tmp/transmodel.ttl

Never touches GraphDB; load the graph with load_graphdb_ontologies afterwards and restart the backend
and the worker (docs/production-deployment.md, section 12.2).

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-26  |  Modified: 2026-10-26
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.transmodel_guids import add_guid_section, read_guids

_TRANSMODEL_TTL = Path(__file__).resolve().parents[4] / "docs" / "ontology" / "standards" / "transmodel.ttl"


class Command(BaseCommand):
    help = "Add the EA GUID of each class to transmodel.ttl, from the Transmodel EA model."

    def add_arguments(self, parser):
        parser.add_argument("--model", type=Path, required=True, help="Transmodel Enterprise Architect model (.qea).")
        parser.add_argument("--ttl", type=Path, default=_TRANSMODEL_TTL, help="transmodel.ttl to read.")
        parser.add_argument("--output", type=Path, default=None, help="Where to write (default: --ttl).")

    def handle(self, *args, **options):
        model: Path = options["model"]
        if not model.is_file():
            raise CommandError(f"Model not found: {model}")
        ttl: Path = options["ttl"]
        output: Path = options["output"] or ttl

        text, counts = add_guid_section(ttl.read_text(encoding="utf-8"), read_guids(model), model.name)
        output.write_text(text, encoding="utf-8")
        self.stdout.write(
            f"{output}: {counts['one']} classes with one GUID, {counts['several']} with several, {counts['none']} without"
        )
        if counts["missing"]:
            self.stdout.write("without a GUID: " + ", ".join(counts["missing"]))
