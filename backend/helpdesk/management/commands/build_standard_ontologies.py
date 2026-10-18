from __future__ import annotations

import contextlib
import importlib.util
import shutil
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from helpdesk.management.commands.extract_xsd_ontology import REPO_ROOT, resolve_repo_path
from helpdesk.services.netex_recovery import (
    append_recovered_classes,
    collect_element_declarations,
    select_recoverable,
)

ENRICHMENT_SCRIPT = REPO_ROOT / "scripts" / "build_netex_ttl_with_properties.py"
MAX_RECOVERY_ROUNDS = 5


def load_enrichment_script():
    if not ENRICHMENT_SCRIPT.is_file():
        raise CommandError(f"Enrichment script not found: {ENRICHMENT_SCRIPT}")
    spec = importlib.util.spec_from_file_location("build_netex_ttl_with_properties", ENRICHMENT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_netex_ontology(extracted: Path, xsd_root: Path, output: Path, work_dir: Path, enrich) -> dict:
    """Enrich the extracted NeTEx ontology, recover the classes its properties point to, and repeat.

    Each round enriches the current text. Dangling property targets that pass the recovery rule are
    added as classes, which can expose new targets, so the loop runs until nothing is added.
    """

    declarations = collect_element_declarations(xsd_root)
    text = extracted.read_text(encoding="utf-8")
    known = set(enrich.load_ttl_classes(text))
    extracted_count = len(known)
    recovered: list[str] = []
    result = work_dir / "enriched.ttl"

    for round_number in range(1, MAX_RECOVERY_ROUNDS + 1):
        current = work_dir / f"round{round_number}.ttl"
        current.write_text(text, encoding="utf-8")
        with contextlib.redirect_stdout(StringIO()):
            dangling = enrich.main(current, result, xsd_root)
        names = select_recoverable(dangling, declarations, known)
        if not names:
            break
        text = append_recovered_classes(text, names, declarations, known)
        known |= set(names)
        recovered.extend(names)
    else:
        raise CommandError(f"NeTEx class recovery did not settle after {MAX_RECOVERY_ROUNDS} rounds")

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(result, output)
    return {"extracted_classes": extracted_count, "recovered": recovered, "rounds": round_number}


class Command(BaseCommand):
    help = (
        "Generate the OpRa, SIRI and NeTEx ontologies from their repositories, with no hand work: "
        "extract the concepts from the XSD, enrich NeTEx with properties, and recover the classes "
        "its properties point to."
    )

    def add_arguments(self, parser):
        parser.add_argument("--netex-path", type=Path, default=None, help="NeTEx repository (default: $NETEX_REPO_PATH, else ../NeTEx).")
        parser.add_argument("--opra-path", type=Path, default=None, help="OpRa repository (default: $OPRA_REPO_PATH, else ../OpRa).")
        parser.add_argument("--siri-path", type=Path, default=None, help="SIRI repository (default: $SIRI_REPO_PATH, else ../SIRI).")
        parser.add_argument(
            "--output-dir",
            type=Path,
            default=REPO_ROOT / "docs" / "ontology" / "standards",
            help="Where opra.ttl, siri.ttl and netex.ttl are written (default: docs/ontology/standards).",
        )

    def handle(self, *args, **options):
        netex = resolve_repo_path(options["netex_path"], name="NeTEx", env_var="NETEX_REPO_PATH")
        opra = resolve_repo_path(options["opra_path"], name="OpRa", env_var="OPRA_REPO_PATH")
        siri = resolve_repo_path(options["siri_path"], name="SIRI", env_var="SIRI_REPO_PATH")
        output_dir = Path(options["output_dir"])
        enrich = load_enrichment_script()

        with TemporaryDirectory() as tmp:
            work = Path(tmp)
            extracted = work / "extracted"
            call_command(
                "extract_xsd_ontology",
                "--merge", "--refresh-auto", "--skip-example-xml",
                "--netex-path", str(netex), "--opra-path", str(opra), "--siri-path", str(siri),
                "--ttl-output-dir", str(extracted),
                stdout=StringIO(),
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            for standard in ("opra", "siri"):
                shutil.copyfile(extracted / f"{standard}.ttl", output_dir / f"{standard}.ttl")
                self.stdout.write(f"{standard}.ttl written")
            stats = build_netex_ontology(extracted / "netex.ttl", netex / "xsd", output_dir / "netex.ttl", work, enrich)

        self.stdout.write(
            f"netex.ttl written: {stats['extracted_classes']} extracted classes + {len(stats['recovered'])} "
            f"recovered ({stats['rounds']} round(s))"
        )
        self.stdout.write("recovered: " + ", ".join(stats["recovered"]))
        self.stdout.write(self.style.SUCCESS("Standard ontologies generated."))
