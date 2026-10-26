"""
Add the Transmodel part of each class to docs/ontology/standards/transmodel.ttl.

Reads the package tree from the Transmodel Enterprise Architect model (.qea) and appends one
tmalign:transmodelPart per class (e.g. "Part 10 - Alternative Modes (NM)") in a marked section at the
end of the file; a rerun replaces that section, so the result is the same each time. The triples above
the section are not changed.

Usage:
    python manage.py add_transmodel_parts --model /path/to/TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea
    python manage.py add_transmodel_parts --model ... --output /tmp/transmodel.ttl

Never touches GraphDB; load the graph with load_graphdb_ontologies afterwards and restart the backend
and the worker (docs/production-deployment.md, section 12.2).

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-26  |  Modified: 2026-10-26
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.transmodel_parts import add_part_section, read_parts

_TRANSMODEL_TTL = Path(__file__).resolve().parents[4] / "docs" / "ontology" / "standards" / "transmodel.ttl"


class Command(BaseCommand):
    help = "Add the Transmodel part of each class to transmodel.ttl, from the Transmodel EA model."

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

        text, counts = add_part_section(ttl.read_text(encoding="utf-8"), read_parts(model), model.name)
        output.write_text(text, encoding="utf-8")
        self.stdout.write(
            f"{output}: {counts['one']} classes with one part, {counts['several']} with several, {counts['none']} without"
        )
        if counts["missing"]:
            self.stdout.write("without a part: " + ", ".join(counts["missing"]))
