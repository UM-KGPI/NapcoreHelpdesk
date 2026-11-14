"""Measure the model's reading of example requests against a hand-written gold file and against today's patterns.

Plan 2026-11-14-example-request-reading.md, step R0. Each gold question is read --runs times by read_request (per
prompt variant) and once by the generator's patterns, and both are scored against the gold file by the same
rules. Needs LLM_ENABLED, the model, the database (the patterns' asked object looks in the indexed examples) and
a reachable NETEX_VALIDATOR_URL. Nothing here changes an answer.

Variants: "question" (the request alone) and "candidates" (the request plus the element names that
schema_declarations(question) finds).

Scoring, per question and field, 1 when right, else 0; a reading's score is the share of its runs that are right,
a field's score the mean over the questions. Names are expanded the same way on both sides: a name stands for
itself and for the concrete object elements the validator's /concrete gives for it (FareProduct ->
PreassignedFareProduct, ...), so two names match when their expansions share an element.

- asked: right when the gold has none and the reading has none, or when the reading's asked object matches one of
  the gold's names.
- objects (the gate's "objects with counts"): the reading's objects that have a kind, without those matching its
  own asked object, must pair one to one with the gold's objects: matching kind and equal count (null = no count).
  Any object left over on either side makes it wrong.
- counts: as objects, on the entries that have a count on each side only (reported, not gated).
- values: the reading's values must pair one to one with the gold's (an entry with a list of spellings takes any
  one). Values are compared after whitespace folding and case folding, with a clock time as HH:MM and a duration
  as its number of seconds (PT3M = PT180S = "3 minutes").
- conditions: right when both or neither have a condition phrase (reported, not gated).

A failed call or a reply without JSON is a wrong reading on every field. Entries marked unsure: true are scored
and reported apart and do not count in the gate; entries with lang (not English) are also reported apart, as the
patterns here read the question as typed while the app gives them its English rendering.

Gate R0: on asked, objects and values the reading scores at least the patterns' score and on at least one of them
clearly more (5 points or more); the --runs readings of a question are identical (asked, objects, values after
grounding) on at least 95% of the gated questions; median call time under 2 s.

--output writes every reading (raw reply, grounded reading, what grounding dropped, time) and every pattern
reading, so the scores can be recomputed with --rescore without new calls.
"""

from __future__ import annotations

import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError

DEFAULT_GOLD = Path(__file__).resolve().parents[2] / "benchmarks" / "example-request-readings.yaml"
FIELDS = ("asked", "objects", "values")
EXTRA_FIELDS = ("counts", "conditions")
CLEARLY_BETTER = 0.05
AGREEMENT_GATE = 0.95
MEDIAN_MS_GATE = 2000


# Patterns ------------------------------------------------------------------------------------------------------


def pattern_reading(question: str) -> dict:
    """What today's generator reads from the question, in the reading's shape: the asked object (asked_element,
    else asked_from_parts), counted objects (object_counts for digits; counted_shapes in words whose noun names
    an object), parts named by an object's element name (wanted_parts, longest words first, as PR #505's
    named_object_parts), values (requested_values without the counting numbers) and service condition phrases."""
    from helpdesk.services import netex_example_generator as g

    asked = g.asked_element(question) or g.asked_from_parts(question)[0]
    counts = g.object_counts(question)
    objects = [{"kinds": kinds, "count": count, "phrase": f"{written} {phrase}"} for count, written, phrase, kinds in counts]
    for count, written, noun in g.counted_shapes(question):
        if written.isdigit():
            continue  # digits: object_counts above (a digit before anything else is a value)
        kinds = g._object_kinds(noun)
        if kinds:
            objects.append({"kinds": kinds, "count": count, "phrase": f"{written} {noun}"})
    for noun in g.wanted_parts(question):
        words = noun.split()
        for size in range(len(words), 0, -1):
            kinds = g._object_kinds(" ".join(words[:size]))
            if kinds is None:
                continue
            if kinds and asked not in kinds:
                objects.append({"kinds": kinds, "count": None, "phrase": " ".join(words[:size])})
            break
    values = g.counted_out(g.requested_values(question), question, counts)
    return {
        "ok": True,
        "asked": asked,
        "objects": objects,
        "values": [{"value": value} for value in values],
        "conditions": [{"phrase": phrase} for phrase, _ in g.service_conditions(question)],
    }


# Scoring -------------------------------------------------------------------------------------------------------


class Expander:
    """A name and the concrete object elements it stands for (cached /concrete lookups)."""

    def __init__(self, lookup=None):
        from helpdesk.services.example_request_reading import ObjectLookup

        self.lookup = lookup or ObjectLookup()

    def __call__(self, names) -> frozenset[str]:
        if isinstance(names, str):
            names = [names]
        found: set[str] = set()
        for name in names or []:
            if name:
                found.add(name)
                found.update(self.lookup(name))
        return frozenset(found)


def normal_value(value) -> str:
    from helpdesk.services.netex_example_generator import _TIME, _time_value, duration_seconds, durations

    text = " ".join(str(value).split()).strip(" .,;:\"'“”")
    if (match := _TIME.fullmatch(text)) is not None:
        return _time_value(match)
    if (seconds := duration_seconds(text)) is not None:
        return f"duration:{seconds:g}"
    found = durations(text)
    if len(found) == 1 and found[0][0].strip().lower() == text.lower():
        return f"duration:{found[0][1]:g}"
    return text.casefold()


def _pairs(gold: list, predicted: list, match) -> bool:
    """Whether the two lists pair one to one under match(gold_item, predicted_item)."""
    if len(gold) != len(predicted):
        return False
    if not gold:
        return True
    first, rest = gold[0], gold[1:]
    return any(match(first, item) and _pairs(rest, predicted[:i] + predicted[i + 1:], match) for i, item in enumerate(predicted))


def predicted_objects(reading: dict, expand) -> list[tuple[frozenset, int | None]]:
    asked = expand(reading.get("asked") or "")
    found = []
    for entry in reading.get("objects") or []:
        names = entry.get("kinds") or []
        if entry.get("kind"):
            names = [entry["kind"], *names]
        kinds = expand(names)
        if not kinds or (asked and kinds & asked):
            continue
        found.append((kinds, entry.get("count")))
    return found


def score_reading(reading: dict, gold: dict, expand) -> dict:
    """{field: 1 or 0} for one reading against one gold entry (rules in the module docstring)."""
    if not reading.get("ok"):
        return {field: 0 for field in (*FIELDS, *EXTRA_FIELDS)}
    gold_asked = gold.get("asked") or ""
    asked_names = expand(gold_asked)
    predicted_asked = reading.get("asked") or ""
    asked_ok = (not predicted_asked) if not asked_names else bool(expand(predicted_asked) & asked_names)

    gold_objects = [(expand(item["kind"]), item.get("count")) for item in gold.get("objects") or []]
    objects = predicted_objects(reading, expand)
    same = lambda g, p: bool(g[0] & p[0]) and g[1] == p[1]  # noqa: E731
    objects_ok = _pairs(gold_objects, objects, same)
    counts_ok = _pairs([o for o in gold_objects if o[1] is not None], [o for o in objects if o[1] is not None], same)

    gold_values = [{normal_value(v) for v in (item if isinstance(item, list) else [item])} for item in gold.get("values") or []]
    values = list(dict.fromkeys(normal_value(entry["value"]) for entry in reading.get("values") or []))
    values_ok = _pairs(gold_values, values, lambda g, p: p in g)

    conditions_ok = bool(gold.get("conditions")) == bool(reading.get("conditions"))
    return {"asked": int(asked_ok), "objects": int(objects_ok), "values": int(values_ok), "counts": int(counts_ok), "conditions": int(conditions_ok)}


def signature(reading: dict) -> str:
    """The reading's content for the agreement measure: asked, objects (kind, count) and values, ordered."""
    if not reading.get("ok"):
        return "failed"
    objects = sorted((entry.get("kind") or "", entry.get("count") or 0) for entry in reading.get("objects") or [])
    values = sorted(normal_value(entry["value"]) for entry in reading.get("values") or [])
    return json.dumps([reading.get("asked") or "", objects, values])


def _percentile(values: list[float], share: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(share * (len(ordered) - 1))))]


def summarise(result: dict, expand) -> dict:
    """Scores per variant and group (gated, unsure, other language), agreement, times and drops, and the gate."""
    gold = {entry["id"]: entry for entry in result["gold"]}
    groups = {
        "gated": [i for i, e in gold.items() if not e.get("unsure")],
        "gated_english": [i for i, e in gold.items() if not e.get("unsure") and not e.get("lang")],
        "unsure": [i for i, e in gold.items() if e.get("unsure")],
    }
    patterns = {i: score_reading(result["patterns"][i], gold[i], expand) for i in gold}
    summary = {"patterns": {}, "variants": {}}
    for group, ids in groups.items():
        summary["patterns"][group] = {
            field: round(statistics.mean(patterns[i][field] for i in ids), 3) if ids else None for field in (*FIELDS, *EXTRA_FIELDS)
        }
    for variant, readings in result["readings"].items():
        scored = {i: [score_reading(r, gold[i], expand) for r in readings[i]] for i in gold if i in readings}
        out: dict = {}
        for group, ids in groups.items():
            ids = [i for i in ids if i in scored]
            out[group] = {
                field: round(statistics.mean(statistics.mean(s[field] for s in scored[i]) for i in ids), 3) if ids else None
                for field in (*FIELDS, *EXTRA_FIELDS)
            }
            out[group]["agreement"] = (
                round(statistics.mean(len({signature(r) for r in readings[i]}) == 1 for i in ids), 3) if ids else None
            )
        times = [r["ms"] for i in scored for r in readings[i] if r.get("ms")]
        out["callMs"] = {"median": statistics.median(times) if times else None, "p90": _percentile(times, 0.9), "calls": len(times)}
        out["failedCalls"] = sum(not r.get("ok") for i in scored for r in readings[i])
        drops = [d for i in scored for r in readings[i] for d in r.get("dropped") or []]
        out["grounding"] = {
            "readingsWithDrops": sum(bool(r.get("dropped")) for i in scored for r in readings[i]),
            "byRule": {str(rule): sum(d["rule"] == rule for d in drops) for rule in (1, 2, 3, 4)},
            "byAction": {action: sum(d["action"] == action for d in drops) for action in sorted({d["action"] for d in drops})},
        }
        out["perQuestion"] = {
            i: {field: round(statistics.mean(s[field] for s in scored[i]), 2) for field in (*FIELDS, *EXTRA_FIELDS)}
            | {"agree": len({signature(r) for r in readings[i]}) == 1}
            for i in scored
        }
        reading, pattern = out["gated"], summary["patterns"]["gated"]
        not_worse = all(reading[f] >= pattern[f] for f in FIELDS)
        clearly = [f for f in FIELDS if reading[f] - pattern[f] >= CLEARLY_BETTER]
        out["gate"] = {
            "notWorseOnEach": not_worse,
            "clearlyBetterOn": clearly,
            "agreement": reading["agreement"],
            "agreementOk": reading["agreement"] is not None and reading["agreement"] >= AGREEMENT_GATE,
            "medianMsOk": out["callMs"]["median"] is not None and out["callMs"]["median"] < MEDIAN_MS_GATE,
        }
        out["gate"]["passed"] = bool(not_worse and clearly and out["gate"]["agreementOk"] and out["gate"]["medianMsOk"])
        summary["variants"][variant] = out
    summary["patternsPerQuestion"] = patterns
    return summary


# Command -------------------------------------------------------------------------------------------------------


class Command(BaseCommand):
    help = "Read the example requests of the gold file with the model and with the patterns, and score both."

    def add_arguments(self, parser):
        parser.add_argument("--gold", default=str(DEFAULT_GOLD))
        parser.add_argument("--runs", type=int, default=5)
        parser.add_argument("--variants", default="question,candidates", help="question, candidates, or both (comma-separated)")
        parser.add_argument("--ids", default="", help="comma-separated gold ids (default: all)")
        parser.add_argument("--workers", type=int, default=1, help="concurrent model calls (1 keeps call times undisturbed)")
        parser.add_argument("--output", default="", help="write every reading and the summary as JSON")
        parser.add_argument("--rescore", default="", help="score a previous --output file again, without new calls")

    def handle(self, *args, **options):
        from helpdesk.services.example_request_reading import candidate_names, read_request

        expand = Expander()
        if options["rescore"]:
            result = json.loads(Path(options["rescore"]).read_text())
            result["gold"] = _load_gold(options["gold"], options["ids"]) or result["gold"]
        else:
            gold = _load_gold(options["gold"], options["ids"])
            variants = [v.strip() for v in options["variants"].split(",") if v.strip()]
            if any(v not in ("question", "candidates") for v in variants):
                raise CommandError("variants are question and candidates")
            result = {"gold": gold, "runs": options["runs"], "patterns": {}, "readings": {v: {} for v in variants}, "candidates": {}}
            for entry in gold:
                result["patterns"][entry["id"]] = pattern_reading(entry["question"])
                if "candidates" in variants:
                    result["candidates"][entry["id"]] = candidate_names(entry["question"])
            for variant in variants:
                jobs = [
                    (entry["id"], entry["question"], result["candidates"].get(entry["id"]) if variant == "candidates" else None)
                    for entry in gold for _ in range(options["runs"])
                ]
                with ThreadPoolExecutor(max_workers=max(1, options["workers"])) as pool:
                    readings = list(pool.map(lambda job: (job[0], read_request(job[1], job[2])), jobs))
                for gold_id, reading in readings:
                    result["readings"][variant].setdefault(gold_id, []).append(reading)
                self.stderr.write(f"{variant}: {len(readings)} readings")
        result["summary"] = summarise(result, expand)
        if options["output"]:
            Path(options["output"]).write_text(json.dumps(result, indent=1, ensure_ascii=False))
        self.stdout.write(report(result))


def _load_gold(path: str, ids: str) -> list[dict]:
    entries = yaml.safe_load(Path(path).read_text())["readings"]
    wanted = {i.strip() for i in ids.split(",") if i.strip()}
    return [e for e in entries if not wanted or e["id"] in wanted]


def report(result: dict) -> str:
    summary = result["summary"]
    lines = [f"{len(result['gold'])} questions, {result.get('runs')} runs per variant"]
    header = f"{'':28}" + "".join(f"{f:>11}" for f in (*FIELDS, *EXTRA_FIELDS)) + f"{'agree':>8}"
    for group in ("gated", "gated_english", "unsure"):
        lines += ["", f"[{group}]", header]
        row = summary["patterns"][group]
        lines.append(f"{'patterns':28}" + "".join(f"{_pct(row[f]):>11}" for f in (*FIELDS, *EXTRA_FIELDS)))
        for variant, out in summary["variants"].items():
            row = out[group]
            lines.append(f"{'reading/' + variant:28}" + "".join(f"{_pct(row[f]):>11}" for f in (*FIELDS, *EXTRA_FIELDS)) + f"{_pct(row['agreement']):>8}")
    for variant, out in summary["variants"].items():
        lines += ["", f"reading/{variant}: call ms median {out['callMs']['median']}, p90 {out['callMs']['p90']}, "
                      f"{out['callMs']['calls']} calls, {out['failedCalls']} failed; grounding {out['grounding']}",
                  f"  gate: {out['gate']}"]
        disagree = [i for i, q in out["perQuestion"].items() if not q["agree"]]
        lines.append(f"  read more than one way: {', '.join(disagree) or 'none'}")
    return "\n".join(lines)


def _pct(value) -> str:
    return "-" if value is None else f"{100 * value:.0f}%"


__all__ = ["pattern_reading", "score_reading", "signature", "summarise", "normal_value", "Expander", "report"]
