"""Report the retrieval yardstick by group from stored benchmark reports (no retrieval is run here).

Inputs are the JSON reports of the two benchmark commands, each given a label:
  --bench LABEL=FILE    run_retrieval_benchmark --app-conditions report (graph mode; found and MRR as the command
                        counts them, so an abstention question with no expected source counts as found; first place
                        by the expected patterns against the source path)
  --locate LABEL=FILE   locate_answer_sources report (rank in the prompt's six passages, patterns against
                        "<repository URL>/<source path>$")
Every label is a group. Further groups: --group NAME=ID,ID,... (ids as LABEL:ID), and, always, the questions that
name a standard, found by the same keyword patterns the answer endpoints use (question_parsing), as one group and
one per standard. Per group: questions, found in six, at first place, MRR@6, median retrieval time.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services import question_parsing

NAMES_STANDARD_GROUP = "names a standard"


def standards_named(text: str) -> list[str]:
    """The standards a question names by their own names (NeTEx, SIRI, OpRa, Transmodel, mobilityDCAT-AP, INSPIRE,
    DATEX II, TN-ITS), by the answer endpoints' keyword patterns. Sources that are not standards (EU legislation,
    NAPCORE) are left out."""
    return [
        name
        for name, pattern in question_parsing._STANDARD_KEYWORD_PATTERNS.items()
        if name not in question_parsing._NON_STANDARD_SCOPES and pattern.search(text or "")
    ]


def bench_rows(report: dict, label: str, mode: str = "graph") -> list[dict]:
    rows = []
    for entry in report.get("questions", []):
        result = entry.get(mode)
        if result is None:
            raise CommandError(f"{label}: question {entry.get('id')} has no '{mode}' result")
        patterns = [p.lower() for p in entry.get("expected_source_patterns") or []]
        paths = result.get("top_6_paths") or []
        rank = next((i for i, path in enumerate(paths, 1) if any(p in path.lower() for p in patterns)), None)
        rows.append({"key": f"{label}:{entry['id']}", "label": label, "question": entry.get("question", ""),
                     "rank": rank, "found": bool(result.get("hit_at_6")), "mrr": float(result.get("mrr_at_6", 0.0)),
                     "ms": float(result.get("latency_ms", 0.0))})
    return rows


def locate_rows(report: dict, label: str) -> list[dict]:
    rows = []
    for entry in report.get("questions", []):
        rows.append({"key": f"{label}:{entry['id']}", "label": label, "question": entry.get("question", ""),
                     "rank": entry.get("prompt"), "found": entry.get("prompt") is not None,
                     "mrr": 1.0 / entry["prompt"] if entry.get("prompt") else 0.0,
                     "ms": float(entry.get("retrievalSeconds") or 0.0) * 1000.0})
    return rows


def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    found = sum(1 for r in rows if r["found"])
    return {
        "questions": n,
        "found_in_six": found,
        "first_place": sum(1 for r in rows if r["rank"] == 1),
        "mrr_at_6": round(sum(r["mrr"] for r in rows) / n, 4) if n else None,
        "median_ms": round(statistics.median(r["ms"] for r in rows), 1) if n else None,
    }


def build_groups(rows: list[dict], extra: dict[str, list[str]]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["label"], []).append(row)
    by_key = {r["key"]: r for r in rows}
    for name, keys in extra.items():
        missing = [k for k in keys if k not in by_key]
        if missing:
            raise CommandError(f"group {name}: no result for {', '.join(missing[:5])}")
        groups[name] = [by_key[k] for k in keys]
    named = [(r, standards_named(r["question"])) for r in rows]
    groups[NAMES_STANDARD_GROUP] = [r for r, s in named if s]
    for standard in sorted({s for _, ss in named for s in ss}):
        groups[f"names {standard}"] = [r for r, ss in named if standard in ss]
    return groups


def parse_pairs(values: list[str] | None, what: str) -> list[tuple[str, str]]:
    pairs = []
    for value in values or []:
        if "=" not in value:
            raise CommandError(f"{what} needs NAME=VALUE, got {value!r}")
        name, _, rest = value.partition("=")
        pairs.append((name, rest))
    return pairs


class Command(BaseCommand):
    help = "Report the retrieval yardstick by group from stored benchmark reports."

    def add_arguments(self, parser):
        parser.add_argument("--bench", action="append", help="LABEL=run_retrieval_benchmark report (app conditions).")
        parser.add_argument("--locate", action="append", help="LABEL=locate_answer_sources report.")
        parser.add_argument("--group", action="append", help="NAME=LABEL:ID,LABEL:ID,... extra group by question ids.")
        parser.add_argument("--output", default=None, help="Write the table as JSON here.")

    def handle(self, *args, **options):
        rows: list[dict] = []
        for label, path in parse_pairs(options.get("bench"), "--bench"):
            rows += bench_rows(json.loads(Path(path).read_text(encoding="utf-8")), label)
        for label, path in parse_pairs(options.get("locate"), "--locate"):
            rows += locate_rows(json.loads(Path(path).read_text(encoding="utf-8")), label)
        if not rows:
            raise CommandError("Give at least one --bench or --locate report.")
        extra = {name: [k for k in keys.split(",") if k] for name, keys in parse_pairs(options.get("group"), "--group")}
        table = {name: summarise(members) for name, members in build_groups(rows, extra).items()}
        self.stdout.write("group\tquestions\tfound_in_six\tfirst_place\tmrr_at_6\tmedian_ms")
        for name, s in table.items():
            self.stdout.write(
                f"{name}\t{s['questions']}\t{s['found_in_six']}\t{s['first_place']}\t{s['mrr_at_6']}\t{s['median_ms']}"
            )
        if options.get("output"):
            out = Path(options["output"])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"groups": table, "questions": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
