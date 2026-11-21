"""
Generate the direct Transmodel <-> NeTEx/SIRI/OpRa alignment graphs.

Reads docs/ontology/standards/{transmodel,netex,siri,opra}.ttl, links each
standard class to the Transmodel class of the same name, applies the manual
corrections in alignments/transmodel-alignment-curation.csv, and writes:

- alignments/transmodel-<standard>-align.ttl      (skos:exactMatch + definition status)
- alignments/transmodel-alignment-report.md       (differing definitions, unmatched classes)
- alignments/transmodel-alignment-suggestions.md  (candidate matches for unmatched classes, for
                                                    review only; never written to the .ttl files)

Never touches GraphDB; load the graphs with load_graphdb_ontologies afterwards.

Usage:
    python manage.py build_transmodel_alignment
    python manage.py build_transmodel_alignment --standard netex --dry-run

Requires rdflib (offline tooling dependency, not needed at runtime).

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-17  |  Modified: 2026-10-20
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.transmodel_alignment import (
    STANDARD_LABELS,
    STANDARD_NAMESPACES,
    TRANSMODEL_NAMESPACE,
    load_curation,
    plan_alignment,
    render_report,
    render_suggestions_report,
    render_turtle,
    suggest_transmodel_candidates,
)

_ONTOLOGY_DIR = Path(__file__).resolve().parents[4] / "docs" / "ontology"


def _class_definitions(path: Path, namespace: str, definition_predicate) -> dict[str, str]:
    """Return {local name: definition} for every owl:Class in `namespace`."""
    import rdflib  # noqa: PLC0415 - offline tooling dependency
    from rdflib.namespace import OWL, RDF

    graph = rdflib.Graph()
    graph.parse(path, format="turtle")
    classes: dict[str, str] = {}
    for subject in graph.subjects(RDF.type, OWL.Class):
        iri = str(subject)
        if not iri.startswith(namespace):
            continue
        definition = graph.value(subject, definition_predicate)
        classes[iri[len(namespace):]] = str(definition) if definition is not None else ""
    return classes


class Command(BaseCommand):
    help = "Generate Transmodel <-> NeTEx/SIRI/OpRa alignment graphs and a review report."

    def add_arguments(self, parser):
        parser.add_argument(
            "--standard",
            choices=sorted(STANDARD_NAMESPACES),
            action="append",
            help="Standard(s) to align (repeatable). Default: all.",
        )
        parser.add_argument(
            "--ontology-dir",
            default=str(_ONTOLOGY_DIR),
            help="Ontology root containing standards/ and alignments/.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Print the summary (and the classes treated as service-operation types) without writing "
                "files. Skips the candidate suggestions, which take longer to compute."
            ),
        )

    def handle(self, *args, **options):
        try:
            from rdflib.namespace import RDFS, SKOS
        except ImportError as exc:
            raise CommandError("rdflib is required: pip install rdflib") from exc

        ontology_dir = Path(options["ontology_dir"]).expanduser().resolve()
        standards_dir = ontology_dir / "standards"
        alignments_dir = ontology_dir / "alignments"
        standards = options.get("standard") or sorted(STANDARD_NAMESPACES)

        tm_path = standards_dir / "transmodel.ttl"
        if not tm_path.exists():
            raise CommandError(f"Transmodel ontology not found: {tm_path}")
        tm_classes = _class_definitions(tm_path, TRANSMODEL_NAMESPACE, RDFS.comment)

        try:
            curation = load_curation(alignments_dir / "transmodel-alignment-curation.csv")
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        plans = []
        suggestion_plans = []
        for standard in standards:
            standard_path = standards_dir / f"{standard}.ttl"
            if not standard_path.exists():
                raise CommandError(f"Standard ontology not found: {standard_path}")
            standard_classes = _class_definitions(standard_path, STANDARD_NAMESPACES[standard], SKOS.definition)
            try:
                plan = plan_alignment(
                    standard=standard,
                    standard_classes=standard_classes,
                    tm_classes=tm_classes,
                    curation=curation,
                )
            except ValueError as exc:
                raise CommandError(str(exc)) from exc
            plans.append(plan)

            statuses = {}
            for row in plan.rows:
                statuses[row.status] = statuses.get(row.status, 0) + 1
            self.stdout.write(
                f"{STANDARD_LABELS[standard]}: {len(standard_classes)} classes, {len(plan.rows)} aligned "
                f"{dict(sorted(statuses.items()))}, {len(plan.unmatched)} unmatched, "
                f"{len(plan.service_operations)} service-operation types"
            )
            if options["dry_run"] and plan.service_operations:
                # Printed so the envelope filter can be eyeballed before a real run.
                self.stdout.write(
                    "  service-operation types (not counted as unmatched): " + ", ".join(plan.service_operations)
                )

            if not options["dry_run"]:
                out_path = alignments_dir / f"transmodel-{standard}-align.ttl"
                out_path.write_text(render_turtle(plan), encoding="utf-8")
                self.stdout.write(f"  wrote {out_path}")

                suggestions = suggest_transmodel_candidates(
                    standard=standard,
                    unmatched_classes={name: standard_classes[name] for name in plan.unmatched},
                    tm_classes=tm_classes,
                )
                suggestion_plans.append(suggestions)
                self.stdout.write(
                    f"  suggestions for {len(suggestions.classes)} of {len(plan.unmatched)} unmatched classes"
                )

        if not options["dry_run"]:
            report_path = alignments_dir / "transmodel-alignment-report.md"
            report_path.write_text(render_report(plans), encoding="utf-8")
            self.stdout.write(f"wrote {report_path}")
            suggestions_path = alignments_dir / "transmodel-alignment-suggestions.md"
            suggestions_path.write_text(render_suggestions_report(suggestion_plans), encoding="utf-8")
            self.stdout.write(f"wrote {suggestions_path}")
