"""
Generic Transmodel <-> standard class alignment.

Transmodel is the conceptual reference model; NeTEx, SIRI and OpRa implement
its concepts. This module pairs each standard class with the Transmodel class
of the same name (STOP_PLACE -> StopPlace), compares their definitions, and
renders the result as a SKOS alignment graph plus a review report.

Pure functions only (no RDF library): parsing the TTL files happens in the
build_transmodel_alignment management command.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-17  |  Modified: 2026-10-17
"""

from __future__ import annotations

import csv
import html
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

TRANSMODEL_NAMESPACE = "https://transmodel-cen.eu/6.2/"

STANDARD_NAMESPACES = {
    "netex": "https://netex.org.uk/netex/2.0#",
    "siri": "https://siri.org.uk/siri/1.3#",
    "opra": "https://transmodel-cen.eu/opra/1.0#",
}

STANDARD_LABELS = {"netex": "NeTEx", "siri": "SIRI", "opra": "OpRa"}

# Transmodel model classes are UPPER_SNAKE (STOP_PLACE). Other local names in
# transmodel.ttl are glossary terms (stop), placeholders (Alpha, Spare) or
# value lists (*_ALLOWED_VALUES) and are not alignment targets.
_MODEL_CLASS = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
_EXCLUDED_SUFFIXES = ("_ALLOWED_VALUES",)

# Share of words one definition must cover of the other (stop words ignored).
EQUIVALENT_COVERAGE = 0.80
CORE_COVERAGE = 0.85

_STOP_WORDS = frozenset(
    "a an the of or and to in for by on with be may is are which that as at "
    "from its it can such eg e g etc this these used".split()
)

STATUS_DESCRIPTIONS = {
    "equivalent": "same meaning, wording may differ",
    "extends": "Transmodel definition plus standard-specific notes",
    "differs": "different wording or scope; Transmodel is the reference",
    "missing": "one of the two definitions is empty",
}


@dataclass
class AlignmentRow:
    standard: str
    standard_class: str
    tm_class: str
    method: str  # "name-match" or "curated"
    status: str
    standard_coverage: float
    tm_coverage: float
    standard_definition: str
    tm_definition: str
    note: str = ""


@dataclass
class AlignmentPlan:
    standard: str
    rows: list[AlignmentRow] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)
    collisions: dict[str, list[str]] = field(default_factory=dict)


def is_model_class(tm_local_name: str) -> bool:
    return bool(_MODEL_CLASS.match(tm_local_name)) and not tm_local_name.endswith(_EXCLUDED_SUFFIXES)


def transmodel_to_camel(tm_local_name: str) -> str:
    """STOP_PLACE -> StopPlace (the naming NeTEx, SIRI and OpRa use)."""
    return "".join(part.capitalize() for part in tm_local_name.split("_") if part)


def clean_definition(text: str) -> str:
    """Strip HTML markup left over from the Transmodel EA export and collapse whitespace."""
    without_tags = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def _words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in _STOP_WORDS}


def definition_status(standard_definition: str, tm_definition: str) -> tuple[str, float, float]:
    """Compare a standard's definition with the Transmodel one.

    Returns (status, standard_coverage, tm_coverage):
    - standard_coverage: share of the standard's words found in the full Transmodel text
    - tm_coverage: share of the Transmodel core words (text before any NOTE) found in
      the standard's definition
    """
    standard_text = clean_definition(standard_definition)
    tm_text = clean_definition(tm_definition)
    tm_core = re.split(r"\bNOTE\d*\s*:", tm_text)[0]

    standard_words = _words(standard_text)
    tm_words = _words(tm_text)
    core_words = _words(tm_core)
    if not standard_words or not core_words:
        return "missing", 0.0, 0.0

    standard_coverage = len(standard_words & tm_words) / len(standard_words)
    tm_coverage = len(core_words & standard_words) / len(core_words)
    if tm_coverage >= CORE_COVERAGE:
        status = "equivalent" if standard_coverage >= EQUIVALENT_COVERAGE else "extends"
    else:
        status = "differs"
    return status, round(standard_coverage, 2), round(tm_coverage, 2)


def load_curation(path: Path) -> list[dict]:
    """Read manual corrections: standard,standard_class,tm_class,action(add|exclude),note."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(line for line in handle if not line.lstrip().startswith("#"))
        ]
    for row in rows:
        if row.get("action") not in {"add", "exclude"}:
            raise ValueError(f"Curation row has invalid action (expected add|exclude): {row}")
    return rows


def plan_alignment(
    *,
    standard: str,
    standard_classes: dict[str, str],
    tm_classes: dict[str, str],
    curation: list[dict] | None = None,
) -> AlignmentPlan:
    """Align standard classes ({local name: definition}) to Transmodel classes.

    Name matches become candidate links; curation rows add links the names miss
    and exclude name matches that are wrong.
    """
    plan = AlignmentPlan(standard=standard)

    by_camel: dict[str, list[str]] = {}
    for tm_name in tm_classes:
        if is_model_class(tm_name):
            by_camel.setdefault(transmodel_to_camel(tm_name).lower(), []).append(tm_name)
    for camel, names in by_camel.items():
        if len(names) > 1:
            plan.collisions[camel] = sorted(names)

    curated = [row for row in (curation or []) if row.get("standard") == standard]
    excluded = {(row["standard_class"], row["tm_class"]) for row in curated if row["action"] == "exclude"}
    added = {row["standard_class"]: row for row in curated if row["action"] == "add"}

    for standard_class in sorted(standard_classes):
        standard_definition = standard_classes[standard_class]
        if standard_class in added:
            row = added[standard_class]
            tm_class, method, note = row["tm_class"], "curated", row.get("note", "")
            if tm_class not in tm_classes:
                raise ValueError(f"Curated Transmodel class not found: {tm_class} ({row})")
        else:
            candidates = sorted(by_camel.get(standard_class.lower(), []))
            # Deterministic tie-break on collisions; they are listed in the report.
            tm_class, method, note = (candidates[0], "name-match", "") if candidates else ("", "", "")
            if tm_class and (standard_class, tm_class) in excluded:
                tm_class = ""

        if not tm_class:
            plan.unmatched.append(standard_class)
            continue

        tm_definition = tm_classes[tm_class]
        status, standard_coverage, tm_coverage = definition_status(standard_definition, tm_definition)
        plan.rows.append(
            AlignmentRow(
                standard=standard,
                standard_class=standard_class,
                tm_class=tm_class,
                method=method,
                status=status,
                standard_coverage=standard_coverage,
                tm_coverage=tm_coverage,
                standard_definition=clean_definition(standard_definition),
                tm_definition=clean_definition(tm_definition),
                note=note,
            )
        )
    return plan


def render_turtle(plan: AlignmentPlan, *, generated_on: date | None = None) -> str:
    standard = plan.standard
    label = STANDARD_LABELS[standard]
    today = (generated_on or date.today()).isoformat()
    lines = [
        f"# GENERATED by `python manage.py build_transmodel_alignment` on {today}. Do not edit by hand:",
        "# correct links in transmodel-alignment-curation.csv and regenerate.",
        "",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl:  <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix dct:  <http://purl.org/dc/terms/> .",
        "@prefix nits: <https://napcore.eu/ontology/nits#> .",
        f"@prefix tm:   <{TRANSMODEL_NAMESPACE}> .",
        f"@prefix {standard}: <{STANDARD_NAMESPACES[standard]}> .",
        "",
        f"<https://napcore.eu/ontology/align/transmodel-{standard}>",
        "    a owl:Ontology ;",
        f'    dct:title "Transmodel-{label} Direct Alignment"@en ;',
        f'    dct:description "Class-level alignment from Transmodel (the conceptual reference) to {label}, '
        'generated by name and reviewed through curation. SKOS mapping properties only, so nothing '
        'enters OWL inference."@en ;',
        f'    dct:created "{today}"^^xsd:date ;',
        "    dct:license <https://creativecommons.org/licenses/by/4.0/> .",
        "",
        "nits:transmodelDefinitionStatus",
        "    a owl:AnnotationProperty ;",
        '    rdfs:label "Transmodel definition status"@en ;',
        "    skos:definition \"How a standard concept's definition compares to the definition of the "
        "Transmodel concept it is aligned to: "
        + "; ".join(f"{key} ({value})" for key, value in STATUS_DESCRIPTIONS.items())
        + '."@en .',
        "",
        "nits:alignmentMethod",
        "    a owl:AnnotationProperty ;",
        '    rdfs:label "alignment method"@en ;',
        '    skos:definition "How the link to Transmodel was made: name-match (generated, pending review) '
        'or curated (set by a reviewer)."@en .',
        "",
    ]
    for row in plan.rows:
        lines += [
            f"{standard}:{row.standard_class}",
            f"    skos:exactMatch tm:{row.tm_class} ;",
            f'    nits:transmodelDefinitionStatus "{row.status}" ;',
            f'    nits:alignmentMethod "{row.method}" .',
            "",
        ]
    return "\n".join(lines)


def _md(text: str, limit: int = 220) -> str:
    text = text.replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_report(plans: list[AlignmentPlan], *, generated_on: date | None = None) -> str:
    today = (generated_on or date.today()).isoformat()
    out = [
        "# Transmodel alignment report",
        "",
        f"Generated by `python manage.py build_transmodel_alignment` on {today}.",
        "Links are made by class name (STOP_PLACE → StopPlace) and are pending review.",
        "Correct them in `transmodel-alignment-curation.csv` and regenerate.",
        "",
        "Definition status is a word-overlap heuristic, not a semantic judgement:",
        "",
    ]
    out += [f"- **{key}**: {value}" for key, value in STATUS_DESCRIPTIONS.items()]
    out += ["", "## Summary", "", "| Standard | Classes | Aligned | equivalent | extends | differs | missing | Unmatched |",
            "|---|---|---|---|---|---|---|---|"]
    for plan in plans:
        counts = {key: sum(1 for row in plan.rows if row.status == key) for key in STATUS_DESCRIPTIONS}
        total = len(plan.rows) + len(plan.unmatched)
        out.append(
            f"| {STANDARD_LABELS[plan.standard]} | {total} | {len(plan.rows)} | {counts['equivalent']} | "
            f"{counts['extends']} | {counts['differs']} | {counts['missing']} | {len(plan.unmatched)} |"
        )

    for plan in plans:
        label = STANDARD_LABELS[plan.standard]
        differs = sorted((row for row in plan.rows if row.status == "differs"), key=lambda row: row.tm_coverage)
        out += [
            "",
            f"## {label}: definitions that differ from Transmodel ({len(differs)})",
            "",
            "Sorted by how little of the Transmodel core definition the standard's text covers.",
            "",
            f"| {label} class | Transmodel class | TM coverage | {label} definition | Transmodel definition |",
            "|---|---|---|---|---|",
        ]
        out += [
            f"| {row.standard_class} | {row.tm_class} | {row.tm_coverage:.2f} | "
            f"{_md(row.standard_definition)} | {_md(row.tm_definition)} |"
            for row in differs
        ]
        if plan.collisions:
            out += ["", f"### {label}: Transmodel name collisions (first one used)", ""]
            out += [f"- {', '.join(names)}" for names in plan.collisions.values()]
        out += ["", f"### {label}: classes without a Transmodel match ({len(plan.unmatched)})", ""]
        out.append(", ".join(plan.unmatched) if plan.unmatched else "None.")
    out.append("")
    return "\n".join(out)
