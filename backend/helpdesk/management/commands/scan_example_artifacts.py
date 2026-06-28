"""
Scan NeTEx (and future OpRa/SIRI) example XML directories and generate
draft example:ExampleArtifact TTL stanzas for human review.

Output goes to docs/ontology/examples/<standard>-examples.proposed.ttl.
It never touches the live TTL files or GraphDB — that stays a deliberate
human-reviewed step via make graphdb-load.

Usage:
    python manage.py scan_example_artifacts
    python manage.py scan_example_artifacts --netex-path /path/to/NeTEx
    python manage.py scan_example_artifacts --standard netex --top 8
    python manage.py scan_example_artifacts --dirs functions/stopPlace functions/timetable

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-06-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

# Classes to skip — enumeration containers and abstract base types that are
# not useful retrieval targets and would produce alignment noise.
_SKIP_PREFIXES = (
    "TypeOf",
    "Abstract",
    "General",
    "Version",
)
_SKIP_SUFFIXES = (
    "List",
    "Ref",
    "RefStructure",
    "Structure",
    "InSequence",
    "InContext",
)
_SKIP_EXACT = {
    # Frame containers — structural, not concept-bearing
    "PublicationDelivery",
    "CompositeFrame",
    "ResourceFrame",
    "SiteFrame",
    "ServiceFrame",
    "TimetableFrame",
    "FareFrame",
    "ServiceCalendarFrame",
    "InfrastructureFrame",
    "VehicleScheduleFrame",
    "GeneralFrame",
    # XML envelope / structural
    "dataObjects",
    "frames",
    "members",
    "KeyValue",
    "ValidBetween",
    "Extensions",
    "Extension",
    "alternativeTexts",
    "AlternativeText",
    # Property-like elements that are not concept classes
    "Name",
    "ShortName",
    "Description",
    "PrivateCode",
    "Url",
    "Date",
    "FromDate",
    "ToDate",
    "StartDate",
    "EndDate",
    "Presentation",
    "Colour",
    "TextColour",
    "PublicationTimestamp",
    "PublicationRequest",
    "RequestTimestamp",
    "ParticipantRef",
    "BookingUrl",
    "MinimumBookingPeriod",
    "LatestBookingTime",
    "DaysOfWeek",
    "CalendarDate",
    "keyList",
}

# Directories under examples/ that mix many concepts — flag for manual review
# rather than generating automatic stanzas.
_MANUAL_REVIEW_PREFIXES = (
    "standards/norway/",
    "standards/tap_tsi/",
    "standards/vdv452/",
    "ws_siri_request/",
    "functions/deprecation",
    "functions/variant",
    "functions/versioning",
    "functions/privateCodes",
    "functions/relations",
)

# CamelCase → readable label
def _label(name: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).lower()


def _is_skip(name: str) -> bool:
    if name in _SKIP_EXACT:
        return True
    for p in _SKIP_PREFIXES:
        if name.startswith(p):
            return True
    for s in _SKIP_SUFFIXES:
        if name.endswith(s):
            return True
    return False


def _local_name(tag: str) -> str:
    """Strip XML namespace URI from a tag like {http://...}Foo → Foo."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _extract_concepts(xml_path: Path, top: int) -> list[str]:
    """Return the top-N substantive element names from an XML file."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        return []
    counter: Counter = Counter()
    for elem in tree.iter():
        name = _local_name(elem.tag)
        if not name[0].isupper():
            continue
        if _is_skip(name):
            continue
        counter[name] += 1
    return [name for name, _ in counter.most_common(top)]


def _instance_name(rel_path: str) -> str:
    """Derive a safe TTL instance name from a relative file path."""
    stem = Path(rel_path).stem
    # Remove numeric prefix patterns like Netex_51.1_
    stem = re.sub(r"^[Nn]e[Tt]ex_[\d.]+_", "", stem)
    stem = re.sub(r"^ENTUR[-_]", "Entur", stem)
    # CamelCase from underscores/hyphens
    parts = re.split(r"[_\-\s]+", stem)
    camel = "".join(p.capitalize() for p in parts if p)
    # Prefix with NeTEx namespace token
    return f"nexample:NeTEx{camel}"


def _stanza(rel_path: str, concepts: list[str], dir_label: str, prefix: str) -> str:
    """Render one draft example:ExampleArtifact TTL stanza."""
    instance = _instance_name(rel_path)
    file_name = Path(rel_path).name
    dir_path = str(Path(rel_path).parent)
    primary_label = _label(Path(rel_path).stem)
    # Remove leading numeric pattern from label
    primary_label = re.sub(r"^netex[\s_]\d+[\.\d]*[\s_]?", "", primary_label).strip()

    concept_lines = "\n".join(
        f"    example:illustratesConcept {prefix}:{c} ;" for c in concepts
    )

    return f"""{instance}
    a example:ExampleArtifact ;
    rdfs:label "{primary_label}"@en ;
    skos:altLabel "{dir_label}"@en ;
    skos:altLabel "{file_name}"@en ;
{concept_lines}
    dct:source "{rel_path}" ;
    dct:source "{dir_path}" ;
    rdfs:comment "Draft: {dir_label} example — review illustratesConcept links before committing."@en .
"""


def _header(standard: str, ontology_iri: str) -> str:
    return f"""@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix {standard}: <https://{standard}.org.uk/{standard}/2.0#> .
@prefix example:  <https://napcore.eu/ontology/examples#> .
@prefix nexample: <https://napcore.eu/ontology/examples/{standard}#> .

# DRAFT — generated by manage.py scan_example_artifacts
# Review each illustratesConcept assignment before copying into the live TTL.
# Cross-check against the live file to avoid duplicates.
# Delete stanzas already present in {standard}-examples.ttl.

<{ontology_iri}/proposed>
    a owl:Ontology ;
    rdfs:comment "Draft proposed additions — not loaded into GraphDB."@en .

"""


class Command(BaseCommand):
    help = (
        "Scan example XML directories and write draft example:ExampleArtifact "
        "TTL stanzas for human review. Never modifies live ontology files or GraphDB."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--netex-path",
            type=Path,
            default=Path("/Users/andrejt/Research/repositories/git/NeTEx"),
            help="Path to NeTEx repository root (default: /Users/andrejt/Research/repositories/git/NeTEx)",
        )
        parser.add_argument(
            "--standard",
            default="netex",
            choices=["netex"],
            help="Standard to scan (only netex supported today).",
        )
        parser.add_argument(
            "--dirs",
            nargs="*",
            help=(
                "Limit scan to specific subdirectories under examples/ "
                "(e.g. functions/stopPlace functions/timetable). "
                "Default: all functions/ subdirectories."
            ),
        )
        parser.add_argument(
            "--top",
            type=int,
            default=6,
            help="Number of top concepts to extract per XML file (default: 6).",
        )
        parser.add_argument(
            "--output",
            type=Path,
            default=None,
            help=(
                "Output TTL path. Default: docs/ontology/examples/<standard>-examples.proposed.ttl"
            ),
        )

    def handle(self, *args, **options):
        standard = options["standard"]
        top = options["top"]
        netex_path: Path = options["netex_path"]
        target_dirs: list[str] | None = options.get("dirs")

        if not netex_path.exists():
            raise CommandError(f"NeTEx path does not exist: {netex_path}")

        examples_root = netex_path / "examples"
        if not examples_root.exists():
            raise CommandError(f"examples/ directory not found under {netex_path}")

        # Resolve output path
        repo_root = Path(__file__).resolve().parents[4]
        output_path: Path = options["output"] or (
            repo_root / "docs" / "ontology" / "examples" / f"{standard}-examples.proposed.ttl"
        )

        # Load existing live TTL to detect already-registered sources
        live_ttl = repo_root / "docs" / "ontology" / "examples" / f"{standard}-examples.ttl"
        existing_sources: set[str] = set()
        if live_ttl.exists():
            for line in live_ttl.read_text().splitlines():
                m = re.search(r'dct:source\s+"([^"]+)"', line)
                if m:
                    existing_sources.add(m.group(1))

        # Discover directories to scan
        if target_dirs:
            dirs_to_scan = [examples_root / d for d in target_dirs]
        else:
            # Default: all functions/ subdirectories (clean concept focus)
            dirs_to_scan = sorted(
                p for p in (examples_root / "functions").iterdir() if p.is_dir()
            )

        ontology_iri = f"https://napcore.eu/ontology/examples/{standard}"
        prefix = standard  # e.g. "netex"

        stanzas: list[str] = []
        manual_flags: list[str] = []
        skipped_sources: list[str] = []

        for dir_path in dirs_to_scan:
            if not dir_path.exists():
                self.stdout.write(self.style.WARNING(f"  skip (not found): {dir_path}"))
                continue

            rel_dir = str(dir_path.relative_to(netex_path / "examples"))

            # Flag cross-cutting standards/ directories for manual review
            if any(rel_dir.startswith(p) for p in _MANUAL_REVIEW_PREFIXES):
                manual_flags.append(rel_dir)
                continue

            xml_files = sorted(dir_path.rglob("*.xml"))
            if not xml_files:
                continue

            self.stdout.write(f"  scanning {rel_dir}/ ({len(xml_files)} XML files)")

            for xml_path in xml_files:
                rel_path = str(xml_path.relative_to(netex_path / "examples"))
                rel_path = f"examples/{rel_path}"

                # Skip already registered
                if rel_path in existing_sources or str(Path(rel_path).parent) in existing_sources:
                    skipped_sources.append(rel_path)
                    continue

                concepts = _extract_concepts(xml_path, top)
                if not concepts:
                    self.stdout.write(
                        self.style.WARNING(f"    no concepts extracted from {xml_path.name}")
                    )
                    continue

                dir_label = rel_dir.replace("/", " ").replace("functions ", "").replace("standards ", "")
                stanzas.append(_stanza(rel_path, concepts, dir_label, prefix))

        # Write output
        content = _header(standard, ontology_iri)
        if stanzas:
            content += "\n".join(stanzas)
        else:
            content += "# No new stanzas found — all examples already registered or skipped.\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"\nWrote {len(stanzas)} draft stanzas → {output_path}"))
        if skipped_sources:
            self.stdout.write(f"Skipped {len(skipped_sources)} already-registered sources.")
        if manual_flags:
            self.stdout.write(
                self.style.WARNING(
                    f"\nThe following directories were skipped (cross-cutting real-world "
                    f"examples — review manually):\n" + "\n".join(f"  examples/{d}" for d in manual_flags)
                )
            )
        self.stdout.write(
            "\nNext steps:\n"
            f"  1. Review {output_path.name}\n"
            "  2. Edit illustratesConcept links as needed\n"
            f"  3. Copy approved stanzas into {standard}-examples.ttl\n"
            "  4. make graphdb-load"
        )
