"""
Report classes defined in standard ontology TTL files that have no alignment
entry in the corresponding nits-<standard>-align.ttl file.

Groups unaligned classes by heuristic NITS category and flags those needing
human judgment. Writes a markdown report — never modifies any TTL or GraphDB.

Usage:
    python manage.py ontology_alignment_gap
    python manage.py ontology_alignment_gap --standard netex
    python manage.py ontology_alignment_gap --standard netex --output /tmp/gap.md

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-06-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

# ---------------------------------------------------------------------------
# Heuristic NITS category assignment
# ---------------------------------------------------------------------------

# Ordered: first match wins.
_HEURISTIC_RULES: list[tuple[str, str, str]] = [
    # Skip candidates — not useful retrieval targets
    ("skip", "^TypeOf", "Enumeration/classifier type — bulk-align or skip"),
    ("skip", "List$", "XSD list container — not a retrieval target"),
    ("skip", "^Abstract", "Abstract base class — derives from parent alignment"),
    ("skip", "RefStructure$", "XSD reference structure helper"),
    ("skip", "Ref$", "XSD reference element — not a standalone concept"),
    # Spatial
    ("nits:SpatialEntity", "Zone", "Contains 'Zone'"),
    ("nits:SpatialEntity", "Area", "Contains 'Area'"),
    ("nits:SpatialEntity", "Place$", "Ends with 'Place'"),
    ("nits:SpatialEntity", "^Place", "Starts with 'Place'"),
    ("nits:SpatialEntity", "Space$", "Ends with 'Space'"),
    ("nits:SpatialEntity", "Link$", "Ends with 'Link' (path/access link)"),
    ("nits:SpatialEntity", "Path", "Contains 'Path'"),
    ("nits:SpatialEntity", "Point$", "Ends with 'Point'"),
    ("nits:SpatialEntity", "Entrance", "Contains 'Entrance'"),
    ("nits:SpatialEntity", "Section$", "Ends with 'Section'"),
    # Journey / movement
    ("nits:Journey", "Journey", "Contains 'Journey'"),
    ("nits:Journey", "Route$", "Ends with 'Route'"),
    ("nits:Journey", "Pattern$", "Ends with 'Pattern' (journey/service pattern)"),
    ("nits:Journey", "Run$", "Ends with 'Run' (vehicle run)"),
    # Organisation / actor
    ("nits:Organisation", "Operator", "Contains 'Operator'"),
    ("nits:Organisation", "Authority", "Contains 'Authority'"),
    ("nits:Organisation", "Organisation", "Contains 'Organisation'"),
    ("nits:Organisation", "Provider", "Contains 'Provider'"),
    # Timetable / temporal
    ("nits:Timetable", "Timetable", "Contains 'Timetable'"),
    ("nits:TemporalEntity", "DayType", "DayType scheduling concept"),
    ("nits:TemporalEntity", "Period$", "Ends with 'Period'"),
    ("nits:TemporalEntity", "Calendar", "Contains 'Calendar'"),
    ("nits:TemporalEntity", "Schedule$", "Ends with 'Schedule'"),
    # Stop
    ("nits:Stop", "^Stop", "Starts with 'Stop'"),
    ("nits:Stop", "Quay$", "Ends with 'Quay'"),
    # Real-time / monitoring
    ("nits:RealTimeInformation", "Monitored", "Contains 'Monitored'"),
    ("nits:RealTimeInformation", "Estimated", "Contains 'Estimated'"),
    # Network
    ("nits:Network", "Network", "Contains 'Network'"),
    ("nits:Network", "Group$", "Ends with 'Group' (network grouping)"),
    # Line / service
    ("nits:Line", "^Line", "Starts with 'Line'"),
    ("nits:Service", "^Service", "Starts with 'Service'"),
    # Data artifact — catch-all for domain data objects
    ("nits:DataArtifact", ".", "Default: treat as DataArtifact"),
]


def _heuristic(class_name: str) -> tuple[str, str]:
    """Return (nits_category, reason) for an unaligned class name."""
    for category, pattern, reason in _HEURISTIC_RULES:
        if re.search(pattern, class_name):
            return category, reason
    return "nits:DataArtifact", "Default catch-all"


def _extract_class_names(ttl_path: Path, prefix: str) -> set[str]:
    """Extract bare class names defined as `prefix:ClassName` in a TTL file."""
    names: set[str] = set()
    pattern = re.compile(rf"^{re.escape(prefix)}:([A-Za-z][A-Za-z0-9]*)")
    for line in ttl_path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line.strip())
        if m:
            names.add(m.group(1))
    return names


class Command(BaseCommand):
    help = (
        "Report NeTEx (or other standard) classes with no alignment entry, "
        "grouped by heuristic NITS category. Writes a markdown report only — "
        "never modifies TTL files or GraphDB."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--standard",
            default="netex",
            choices=["netex", "opra", "siri", "datex"],
            help="Standard to audit (default: netex).",
        )
        parser.add_argument(
            "--output",
            type=Path,
            default=None,
            help=(
                "Output markdown path. "
                "Default: docs/ontology/alignments/<standard>-alignment-gap.md"
            ),
        )
        parser.add_argument(
            "--ttl-align",
            type=Path,
            default=None,
            help="Override path to alignment TTL (default: docs/ontology/alignments/nits-<standard>-align.ttl).",
        )
        parser.add_argument(
            "--ttl-standard",
            type=Path,
            default=None,
            help="Override path to standard ontology TTL (default: docs/ontology/standards/<standard>.ttl).",
        )

    def handle(self, *args, **options):
        standard = options["standard"]
        repo_root = Path(__file__).resolve().parents[4]
        ontology_dir = repo_root / "docs" / "ontology"

        standard_ttl: Path = options["ttl_standard"] or (
            ontology_dir / "standards" / f"{standard}.ttl"
        )
        align_ttl: Path = options["ttl_align"] or (
            ontology_dir / "alignments" / f"nits-{standard}-align.ttl"
        )
        output_path: Path = options["output"] or (
            ontology_dir / "alignments" / f"{standard}-alignment-gap.md"
        )

        for p in (standard_ttl, align_ttl):
            if not p.exists():
                raise CommandError(f"File not found: {p}")

        # Extract defined classes and already-aligned classes
        all_classes = _extract_class_names(standard_ttl, standard)
        aligned_classes = _extract_class_names(align_ttl, standard)
        unaligned = sorted(all_classes - aligned_classes)

        self.stdout.write(
            f"{standard}.ttl: {len(all_classes)} classes | "
            f"aligned: {len(aligned_classes)} | "
            f"gap: {len(unaligned)}"
        )

        # Group by heuristic category
        groups: dict[str, list[tuple[str, str]]] = {}
        for cls in unaligned:
            category, reason = _heuristic(cls)
            groups.setdefault(category, []).append((cls, reason))

        # Build markdown report
        lines: list[str] = [
            f"# {standard.upper()} Alignment Gap Report",
            "",
            f"Standard ontology: `{standard_ttl.name}`  ",
            f"Alignment file: `{align_ttl.name}`  ",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total classes in {standard}.ttl | {len(all_classes)} |",
            f"| Already aligned | {len(aligned_classes)} |",
            f"| **Unaligned (gap)** | **{len(unaligned)}** |",
            "",
            "---",
            "",
            "## Proposed additions by NITS category",
            "",
            "> Copy the TTL block for a category into "
            f"`nits-{standard}-align.ttl` after review.  ",
            "> Delete or comment out lines you want to skip.",
            "",
        ]

        # Order: skip candidates first (so they're easy to ignore), then real categories
        category_order = ["skip"] + [
            c for c in sorted(groups) if c != "skip"
        ]

        for category in category_order:
            if category not in groups:
                continue
            entries = groups[category]
            if category == "skip":
                lines += [
                    f"### Skip candidates ({len(entries)} classes)",
                    "",
                    "These are enumeration types, list containers, or abstract base classes.",
                    "They are typically not useful retrieval targets.",
                    "You may bulk-align them all as `nits:DataArtifact` or leave them unaligned.",
                    "",
                    "```",
                    *[f"{standard}:{cls}  # {reason}" for cls, reason in entries],
                    "```",
                    "",
                ]
            else:
                lines += [
                    f"### {category} ({len(entries)} classes)",
                    "",
                    f"Suggested alignment: `rdfs:subClassOf {category}`",
                    "",
                    "```turtle",
                    f"# {standard.upper()} → {category}",
                    *[
                        f"{standard}:{cls}\n    rdfs:subClassOf {category} .  # {reason}"
                        for cls, reason in entries
                    ],
                    "```",
                    "",
                ]

        # Turtle snippet for the whole proposed addition
        lines += [
            "---",
            "",
            "## Full proposed TTL block (all non-skip classes)",
            "",
            "```turtle",
        ]
        for category, entries in sorted(groups.items()):
            if category == "skip":
                continue
            lines.append(f"# {category}")
            for cls, _ in entries:
                lines.append(f"{standard}:{cls}")
                lines.append(f"    rdfs:subClassOf {category} .")
                lines.append("")
        lines += [
            "```",
            "",
            "---",
            "",
            "## Next steps",
            "",
            "1. Review the proposed TTL block above",
            f"2. Copy approved lines into `nits-{standard}-align.ttl`",
            "3. Bump `owl:versionInfo` in the alignment file",
            "4. Run `make graphdb-load`",
            "5. Re-run this command to confirm gap is closed",
        ]

        report = "\n".join(lines)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Report written → {output_path}"))
        self.stdout.write(
            f"\nTop categories by gap size:\n"
            + "\n".join(
                f"  {cat}: {len(entries)}"
                for cat, entries in sorted(groups.items(), key=lambda x: -len(x[1]))
            )
        )
