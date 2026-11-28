"""Replay stored failed attempts of the NeTEx example generator through the validator, without a model call.

The attempt log keeps each attempt's fragment (since 0.97.197). Every distinct fragment whose attempt failed on a
structural problem (the schema's: order, a wrong parent, a missing required child, an undeclared element, a keyref,
…) is sent to the netex-validator as it is now; the report says, per error class of the stored attempt, how many
validate now (with the validator's repairs) and the diagnostics before (as stored) and after. A change to the
validator's repairs is measured with it before any benchmark run (plan 2026-11-13, P0).

Inputs: benchmark outputs (run_example_benchmark --output, {"runs": [...]}), exports of prod events (JSON lines,
each {"ex": {"attemptLog": [...]}}), and lists of failed attempts ([{"fragment", "cls"}]). A directory stands for
every *.json and *.jsonl file in it.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand

from helpdesk.services.netex_example_generator import MAX_LOGGED_FRAGMENT_CHARS, validate_fragment

STRUCTURAL = frozenset(
    {"order", "wrong-parent", "missing-required", "undeclared", "keyref", "abstract", "not-expected", "min-count"}
)
# The checkout's local benchmark files: next to backend/ on a host, /app/repo in the dev stack's backend container.
DEFAULT_CORPUS = next(
    (p for p in (Path(__file__).resolve().parents[4] / ".mylocal" / "bench", Path("/app/repo/.mylocal/bench")) if p.is_dir()),
    Path(".mylocal/bench"),
)


def stored_attempts(path: Path):
    """(source, attempt) for each stored attempt in a file: {"fragment", "errorClass", "diagnostics"}."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        for line in text.splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            example = record.get("ex") if isinstance(record, dict) else None
            for entry in (example or {}).get("attemptLog") or []:
                yield path.name, entry
        return
    try:
        data = json.loads(text)
    except ValueError:
        return
    rows = data.get("runs", []) if isinstance(data, dict) else data
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        if "fragment" in row and "cls" in row:  # a list of failed attempts
            yield path.name, {"fragment": row["fragment"], "errorClass": row["cls"], "diagnostics": row.get("diagnostics") or []}
            continue
        for entry in row.get("attemptLog") or []:
            if isinstance(entry, dict):
                yield path.name, entry


def corpus(paths: list[Path]) -> list[dict]:
    """The distinct stored fragments that failed on a structural class, first occurrence kept."""
    files = []
    for path in paths:
        files += sorted([*path.glob("*.json"), *path.glob("*.jsonl")]) if path.is_dir() else [path]
    seen: set[str] = set()
    found = []
    for path in files:
        for source, entry in stored_attempts(path):
            fragment = entry.get("fragment") or ""
            kind = entry.get("errorClass") or ""
            if not fragment or kind not in STRUCTURAL or fragment in seen:
                continue
            seen.add(fragment)
            found.append({
                "source": source, "errorClass": kind, "fragment": fragment,
                "before": [d for d in entry.get("diagnostics") or [] if isinstance(d, str)],
                # The log cuts a fragment at MAX_LOGGED_FRAGMENT_CHARS: a cut one is not well-formed.
                "truncated": len(fragment) >= MAX_LOGGED_FRAGMENT_CHARS,
            })
    return found


def replay(items: list[dict], validate=validate_fragment) -> dict:
    """Per stored error class: fragments, valid now, repaired (by kind of repair), diagnostics before and after."""
    by_class: dict[str, dict] = defaultdict(lambda: {
        "fragments": 0, "validNow": 0, "repaired": Counter(), "diagnosticsBefore": Counter(), "diagnosticsAfter": Counter(),
    })
    records = []
    for item in items:
        if item["truncated"]:
            continue
        result = validate(item["fragment"])
        row = by_class[item["errorClass"]]
        row["fragments"] += 1
        row["validNow"] += bool(result.get("valid"))
        repaired = result.get("repaired") or []
        repaired = [repaired] if isinstance(repaired, str) else list(repaired)
        row["repaired"].update(repaired)
        after = [d.get("kind", "") for d in result.get("diagnostics") or []]
        row["diagnosticsBefore"].update(item["before"])
        row["diagnosticsAfter"].update(after)
        records.append({
            "source": item["source"], "errorClass": item["errorClass"], "valid": bool(result.get("valid")),
            "repaired": repaired, "before": item["before"], "after": after,
            "errors": (result.get("errors") or [])[:2], "fragment": item["fragment"],
            **({"repairedFragment": result["fragment"]} if result.get("fragment") else {}),
        })
    total = {"fragments": 0, "validNow": 0, "repaired": Counter(), "diagnosticsBefore": Counter(), "diagnosticsAfter": Counter()}
    for row in by_class.values():
        for key, value in row.items():
            total[key] += value
    as_dict = lambda row: {k: (dict(v.most_common()) if isinstance(v, Counter) else v) for k, v in row.items()}  # noqa: E731
    return {
        "byClass": {kind: as_dict(row) for kind, row in sorted(by_class.items(), key=lambda kv: -kv[1]["fragments"])},
        "total": as_dict(total),
        "truncated": sum(1 for item in items if item["truncated"]),
        "records": records,
    }


class Command(BaseCommand):
    help = "Replay stored structurally failed example attempts through the validator: how many validate now."

    def add_arguments(self, parser):
        parser.add_argument("paths", nargs="*", help=f"Files or directories (default: {DEFAULT_CORPUS}).")
        parser.add_argument("--output", default="", help="Write the report with one record per fragment as JSON.")

    def handle(self, *args, **options):
        paths = [Path(p) for p in options["paths"]] or [DEFAULT_CORPUS]
        report = replay(corpus(paths))
        for kind, row in report["byClass"].items():
            self.stdout.write(
                f"{kind:17} fragments {row['fragments']:4}  valid now {row['validNow']:4}  repaired {row['repaired']}  "
                f"diagnostics {sum(row['diagnosticsBefore'].values())} -> {sum(row['diagnosticsAfter'].values())} "
                f"{row['diagnosticsAfter']}"
            )
        total = report["total"]
        self.stdout.write(
            f"\ntotal fragments {total['fragments']} | valid now {total['validNow']} | repaired {total['repaired']} | "
            f"diagnostics {sum(total['diagnosticsBefore'].values())} -> {sum(total['diagnosticsAfter'].values())} | "
            f"left out as cut by the log {report['truncated']}"
        )
        if options["output"]:
            Path(options["output"]).write_text(json.dumps(report, indent=1), encoding="utf-8")
