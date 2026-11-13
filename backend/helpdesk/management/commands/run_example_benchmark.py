"""Run the NeTEx example generator over its benchmark questions and report validity, attempts and time.

Each question goes through retrieval as in the app (graph-RAG, app scope) and then the generator, which
calls the model and the netex-validator service. Needs LLM_ENABLED and a reachable NETEX_VALIDATOR_URL.

Run-to-run variance is large (the fare-product question went 2/5 and 3/3 valid on consecutive nights with
the same code), so compare changes with --runs 3: retrieval runs once per question, the generator --runs
times. The output has one row per run with the generator's attempt log (time, output tokens, how the
reply parsed, the class of each failed attempt's first error) and a summary per question and overall.
"""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand

from helpdesk.services.netex_example_generator import generate_netex_example, requested_values, shared_name_values
from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

DEFAULT_QUESTIONS = Path(__file__).resolve().parents[2] / "benchmarks" / "example-generation-questions.yaml"


def summarize(rows: list[dict]) -> dict:
    """Valid, first-attempt and malformed counts, mean attempts and seconds, failed attempts by class."""
    valid = [row for row in rows if row.get("valid")]
    attempts = [entry for row in rows for entry in row.get("attemptLog") or []]
    resolved = [row for row in valid if row.get("askedObject")]
    generated = [row for row in valid if row.get("origin") == "generated"]
    return {
        "runs": len(rows),
        "valid": len(valid),
        # Of the valid runs whose asked object was resolved: how many fragments contain that object.
        "askedObjectResolved": len(resolved),
        "askedObjectPresent": sum(1 for row in resolved if row.get("askedObjectPresent")),
        "firstAttempt": sum(1 for row in valid if row.get("attempts") == 1),
        # Generated examples: how many the model wrote, how many leave an object unlinked to the asked one, and how
        # many hold two of the question's values as the names of one object (plan 2026-11-12 revision 4, T4).
        "generated": len(generated),
        "unlinked": sum(1 for row in generated if row.get("unlinkedObjects")),
        "sharedName": sum(
            1 for row in generated
            if shared_name_values(row.get("xml") or "", requested_values(row.get("question") or ""), row.get("question") or "")
        ),
        "meanAttempts": round(statistics.mean(row.get("attempts") or 0 for row in rows), 2) if rows else 0,
        "meanSeconds": round(statistics.mean(row.get("seconds") or 0 for row in rows), 1) if rows else 0,
        "failuresByClass": dict(Counter(entry["errorClass"] for entry in attempts if entry.get("errorClass")).most_common()),
        "notJson": sum(1 for entry in attempts if entry.get("parsed") != "json"),
        "completionTokens": sum(entry.get("completionTokens") or 0 for entry in attempts),
    }


class Command(BaseCommand):
    help = "Measure the NeTEx example generator: valid fragments, attempts, model and validator time."

    def add_arguments(self, parser):
        parser.add_argument("--input", default=str(DEFAULT_QUESTIONS))
        parser.add_argument("--output", default="", help="Write the runs and the summaries as JSON.")
        parser.add_argument("--runs", type=int, default=1, help="Generator runs per question (retrieval runs once).")
        parser.add_argument("--only", default="", help="Comma-separated question ids to run (default: all).")

    def handle(self, *args, **options):
        questions = yaml.safe_load(Path(options["input"]).read_text(encoding="utf-8"))["questions"]
        only = {value.strip() for value in options["only"].split(",") if value.strip()}
        if only:
            questions = [item for item in questions if item["id"] in only]
        runs = max(1, options["runs"])
        rows = []
        for item in questions:
            question = item["question"]
            semantic_query = parse_question_to_semantic_query(text=question, requested_scope=[])
            scope, _ = select_effective_scope(semantic_query, [])
            chunks, _trace = retrieve_chunks_with_trace(question=question, top_k=6, min_score=0.62, scope=scope, graph_rag_enabled=True)
            for run in range(1, runs + 1):
                started = time.perf_counter()
                result = generate_netex_example(question, chunks, scope) or {"valid": False, "attempts": 0, "errors": ["not triggered"]}
                seconds = round(time.perf_counter() - started, 1)
                rows.append({"id": item["id"], "run": run, "question": question, "seconds": seconds, **result})
                classes = [entry.get("errorClass") for entry in result.get("attemptLog") or [] if entry.get("errorClass")]
                self.stdout.write(
                    f"{item['id']} run {run} valid={result.get('valid')} origin={result.get('origin', '')} "
                    f"attempts={result.get('attempts')} {seconds} s asked={result.get('askedObject', '')} "
                    f"present={result.get('askedObjectPresent', '')} model={result.get('generationMs', 0)} ms "
                    f"validator={result.get('validationMs', 0)} ms failed={classes}"
                )
        per_question = {
            item["id"]: summarize([row for row in rows if row["id"] == item["id"]]) for item in questions
        }
        overall = summarize(rows)
        self.stdout.write("")
        for question_id, summary in per_question.items():
            self.stdout.write(
                f"{question_id}: valid {summary['valid']}/{summary['runs']}, first attempt {summary['firstAttempt']}, "
                f"attempts {summary['meanAttempts']}, {summary['meanSeconds']} s, asked object "
                f"{summary['askedObjectPresent']}/{summary['askedObjectResolved']}, generated {summary['generated']} "
                f"(unlinked {summary['unlinked']}, two values as names of one object {summary['sharedName']}), "
                f"failed {summary['failuresByClass']}"
            )
        self.stdout.write(
            f"\nvalid {overall['valid']} of {overall['runs']} | first attempt {overall['firstAttempt']} | "
            f"mean attempts {overall['meanAttempts']} | mean {overall['meanSeconds']} s | "
            f"median model {statistics.median(row.get('generationMs', 0) for row in rows):.0f} ms | "
            f"median validator {statistics.median(row.get('validationMs', 0) for row in rows):.0f} ms | "
            f"replies not JSON {overall['notJson']} | asked object {overall['askedObjectPresent']}/{overall['askedObjectResolved']} | "
            f"generated {overall['generated']} (unlinked {overall['unlinked']}, two values as names of one object "
            f"{overall['sharedName']}) | failed attempts {overall['failuresByClass']}"
        )
        if options["output"]:
            Path(options["output"]).write_text(
                json.dumps({"summary": overall, "perQuestion": per_question, "runs": rows}, indent=1), encoding="utf-8"
            )
