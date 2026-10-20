"""
Generic Transmodel <-> standard class alignment.

Transmodel is the conceptual reference model; NeTEx, SIRI and OpRa implement
its concepts. This module pairs each standard class with the Transmodel class
of the same name (STOP_PLACE -> StopPlace), compares their definitions, and
renders the result as a SKOS alignment graph plus a review report.

Classes without a name match are split into service-operation types (XSD
request/response envelopes, out of scope for conceptual alignment) and real
unmatched classes; for the latter, suggest_transmodel_candidates ranks possible
Transmodel matches by definition overlap for human review. Suggestions are
never written into the alignment graph.

Pure functions only (no RDF library): parsing the TTL files happens in the
build_transmodel_alignment management command.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-17  |  Modified: 2026-10-20
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

# XSD service-operation envelopes (SIRI/OpRa request, response, delivery, ...) and
# abstract base types. Transmodel is a conceptual model and has no counterpart for
# them, so they are reported apart instead of inflating the unmatched count.
SERVICE_OPERATION_PATTERN = re.compile(r"(?:Request|Response|Delivery|Discovery|Subscription|Error)$|^Abstract")

SUGGESTIONS_PER_CLASS = 3


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
    service_operations: list[str] = field(default_factory=list)
    collisions: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class CandidateSuggestion:
    tm_class: str
    score: float
    standard_coverage: float
    tm_coverage: float
    tm_definition: str


@dataclass
class ClassSuggestions:
    standard_class: str
    standard_definition: str
    candidates: list[CandidateSuggestion]


@dataclass
class SuggestionPlan:
    standard: str
    classes: list[ClassSuggestions] = field(default_factory=list)
    # No definition, or no word shared with any Transmodel definition.
    unscored: list[str] = field(default_factory=list)


def is_model_class(tm_local_name: str) -> bool:
    return bool(_MODEL_CLASS.match(tm_local_name)) and not tm_local_name.endswith(_EXCLUDED_SUFFIXES)


def is_service_operation_type(standard_class: str) -> bool:
    return bool(SERVICE_OPERATION_PATTERN.search(standard_class))


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
            if is_service_operation_type(standard_class):
                plan.service_operations.append(standard_class)
            else:
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


def suggest_transmodel_candidates(
    *,
    standard: str,
    unmatched_classes: dict[str, str],
    tm_classes: dict[str, str],
    top_n: int = SUGGESTIONS_PER_CLASS,
) -> SuggestionPlan:
    """Rank Transmodel classes as possible matches for standard classes the names missed.

    Scores every Transmodel model class with definition_status, the comparison the
    report already uses for matched pairs. Score is the harmonic mean of its two
    coverages, so a candidate has to share words in both directions. Classes are
    ordered by their best candidate. The result is for human review only.
    """
    plan = SuggestionPlan(standard=standard)
    targets = {name: definition for name, definition in tm_classes.items() if is_model_class(name)}

    for standard_class in sorted(unmatched_classes):
        standard_definition = unmatched_classes[standard_class]
        candidates: list[CandidateSuggestion] = []
        if _words(clean_definition(standard_definition)):
            for tm_class, tm_definition in targets.items():
                status, standard_coverage, tm_coverage = definition_status(standard_definition, tm_definition)
                if status == "missing" or not standard_coverage or not tm_coverage:
                    continue
                score = round(2 * standard_coverage * tm_coverage / (standard_coverage + tm_coverage), 2)
                candidates.append(
                    CandidateSuggestion(
                        tm_class=tm_class,
                        score=score,
                        standard_coverage=standard_coverage,
                        tm_coverage=tm_coverage,
                        tm_definition=clean_definition(tm_definition),
                    )
                )
        if not candidates:
            plan.unscored.append(standard_class)
            continue
        candidates.sort(key=lambda candidate: (-candidate.score, candidate.tm_class))
        plan.classes.append(
            ClassSuggestions(
                standard_class=standard_class,
                standard_definition=clean_definition(standard_definition),
                candidates=candidates[:top_n],
            )
        )

    plan.classes.sort(key=lambda item: (-item.candidates[0].score, item.standard_class))
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
        "@prefix tmalign: <https://napcore.eu/ontology/transmodel-alignment#> .",
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
        "tmalign:transmodelDefinitionStatus",
        "    a owl:AnnotationProperty ;",
        '    rdfs:label "Transmodel definition status"@en ;',
        "    skos:definition \"How a standard concept's definition compares to the definition of the "
        "Transmodel concept it is aligned to: "
        + "; ".join(f"{key} ({value})" for key, value in STATUS_DESCRIPTIONS.items())
        + '."@en .',
        "",
        "tmalign:alignmentMethod",
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
            f'    tmalign:transmodelDefinitionStatus "{row.status}" ;',
            f'    tmalign:alignmentMethod "{row.method}" .',
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
    out += [
        "",
        "Service-operation types (class names ending in Request, Response, Delivery, Discovery,",
        "Subscription or Error, or starting with Abstract) are XSD message envelopes and abstract",
        "base types with no conceptual counterpart in Transmodel. They are listed separately and not",
        "counted as unmatched.",
    ]
    out += ["", "## Summary", "",
            "| Standard | Classes | Aligned | equivalent | extends | differs | missing | Unmatched | Service-operation types |",
            "|---|---|---|---|---|---|---|---|---|"]
    for plan in plans:
        counts = {key: sum(1 for row in plan.rows if row.status == key) for key in STATUS_DESCRIPTIONS}
        total = len(plan.rows) + len(plan.unmatched) + len(plan.service_operations)
        out.append(
            f"| {STANDARD_LABELS[plan.standard]} | {total} | {len(plan.rows)} | {counts['equivalent']} | "
            f"{counts['extends']} | {counts['differs']} | {counts['missing']} | {len(plan.unmatched)} | "
            f"{len(plan.service_operations)} |"
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
        out += [
            "",
            f"### {label}: service-operation types, out of scope for conceptual alignment "
            f"({len(plan.service_operations)})",
            "",
        ]
        out.append(", ".join(plan.service_operations) if plan.service_operations else "None.")
    out.append("")
    return "\n".join(out)


def render_suggestions_report(plans: list[SuggestionPlan], *, generated_on: date | None = None) -> str:
    today = (generated_on or date.today()).isoformat()
    out = [
        "# Transmodel alignment suggestions",
        "",
        f"Generated by `python manage.py build_transmodel_alignment` on {today}.",
        "",
        "**Suggestions for human review, not alignment links.** Nothing in this file is written to the",
        "`transmodel-*-align.ttl` graphs. To accept a suggestion, add a row",
        "`<standard>,<standard class>,<TRANSMODEL_CLASS>,add,<note>` to `transmodel-alignment-curation.csv`",
        "and regenerate.",
        "",
        "For each class without a Transmodel name match (service-operation types excluded, see",
        f"`transmodel-alignment-report.md`), the {SUGGESTIONS_PER_CLASS} Transmodel classes whose definitions",
        "share the most words with it. **Score** is the harmonic mean of the two coverages from the",
        "report's definition comparison: the share of the standard's words found in the Transmodel",
        "definition (std cov) and the share of the Transmodel core words found in the standard's (TM cov).",
        "This is a word-overlap heuristic, not a semantic judgement; short definitions reach high scores on",
        "common words, so many suggestions will be wrong. Classes are sorted by their best score.",
        "",
        "## Summary",
        "",
        "| Standard | Classes without a match | With suggestions | No candidate |",
        "|---|---|---|---|",
    ]
    for plan in plans:
        out.append(
            f"| {STANDARD_LABELS[plan.standard]} | {len(plan.classes) + len(plan.unscored)} | "
            f"{len(plan.classes)} | {len(plan.unscored)} |"
        )

    for plan in plans:
        label = STANDARD_LABELS[plan.standard]
        out += [
            "",
            f"## {label} ({len(plan.classes)} classes)",
            "",
            f"| {label} class | {label} definition | # | Transmodel class | Score | std cov | TM cov | Transmodel definition |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for item in plan.classes:
            for rank, candidate in enumerate(item.candidates, start=1):
                first = rank == 1
                out.append(
                    f"| {item.standard_class if first else ''} | {_md(item.standard_definition, 160) if first else ''} | "
                    f"{rank} | {candidate.tm_class} | {candidate.score:.2f} | {candidate.standard_coverage:.2f} | "
                    f"{candidate.tm_coverage:.2f} | {_md(candidate.tm_definition, 160)} |"
                )
        if plan.unscored:
            out += [
                "",
                f"### {label}: no candidate, empty definition or no word shared with any Transmodel "
                f"definition ({len(plan.unscored)})",
                "",
            ]
            out.append(", ".join(plan.unscored))
    out.append("")
    return "\n".join(out)
