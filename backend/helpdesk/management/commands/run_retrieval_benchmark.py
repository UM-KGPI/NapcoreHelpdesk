from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError

from helpdesk.management.commands.benchmark_utils import DEFAULT_QUESTIONS_PATH
from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

GATED_METRICS = ("hit_at_10", "mrr_at_10")


def _hit_at_k(
    chunks: list[dict],
    expected_patterns: list[str],
    k: int,
    min_hits: int,
) -> bool:
    """Return True if at least `min_hits` expected_patterns each match any chunk in top-k."""
    if min_hits == 0:
        return True  # abstention question: hit is vacuously satisfied
    top_k_paths = [str(c.get("sourcePath") or "") for c in chunks[:k]]
    matched = sum(
        1
        for pattern in expected_patterns
        if any(pattern.lower() in path.lower() for path in top_k_paths)
    )
    return matched >= min_hits


def _mrr_at_k(
    chunks: list[dict],
    expected_patterns: list[str],
    k: int,
) -> float:
    """Mean reciprocal rank of the first matching chunk within top-k. 0.0 if no match."""
    if not expected_patterns:
        return 0.0
    for rank, chunk in enumerate(chunks[:k], start=1):
        path = str(chunk.get("sourcePath") or "")
        if any(p.lower() in path.lower() for p in expected_patterns):
            return 1.0 / rank
    return 0.0


def _run_question(
    question_dict: dict,
    top_k: int,
    graph_rag_enabled: bool,
    scope: list[str] | None,
) -> dict:
    expected_patterns: list[str] = question_dict.get("expected_source_patterns") or []
    min_hits: int = question_dict.get("min_hits", 1)
    q_threshold: int = question_dict.get("top_k_threshold", top_k)
    effective_k = max(top_k, q_threshold)

    start = time.time()
    chunks, trace = retrieve_chunks_with_trace(
        question=question_dict["question"],
        top_k=effective_k,
        min_score=0.0,
        scope=scope,
        graph_rag_enabled=graph_rag_enabled,
    )
    latency_ms = round((time.time() - start) * 1000, 1)

    return {
        "hit_at_5": _hit_at_k(chunks, expected_patterns, 5, min_hits),
        "hit_at_10": _hit_at_k(chunks, expected_patterns, 10, min_hits),
        "hit_at_20": _hit_at_k(chunks, expected_patterns, 20, min_hits),
        "mrr_at_10": _mrr_at_k(chunks, expected_patterns, 10),
        "mrr_at_20": _mrr_at_k(chunks, expected_patterns, 20),
        "latency_ms": latency_ms,
        "top_5_paths": [str(c.get("sourcePath") or "") for c in chunks[:5]],
        "graph_expansion_source": trace.get("graphExpansionSource", "none"),
        "graph_candidates_added": trace.get("graphCandidatesAdded", 0),
    }


def _aggregate(results: list[dict], field: str) -> float:
    vals = [r[field] for r in results if field in r]
    if not vals:
        return 0.0
    return round(statistics.mean([float(v) for v in vals]), 4)


def check_regression(aggregate: dict, reference: dict, max_drop: float) -> list[str]:
    """Return one message per gated metric that dropped more than `max_drop` (absolute)
    below the reference, for every retrieval mode present in both aggregates."""
    failures = []
    for mode in ("baseline", "graph"):
        current, expected = aggregate.get(mode), reference.get(mode)
        if not current or not expected:
            continue
        for metric in GATED_METRICS:
            if metric not in current or metric not in expected:
                continue
            drop = round(float(expected[metric]) - float(current[metric]), 4)
            if drop > max_drop:
                failures.append(
                    f"{mode} {metric}: {current[metric]:.3f} vs reference {expected[metric]:.3f} "
                    f"(dropped {drop:.3f}, allowed {max_drop:.3f})"
                )
    return failures


class Command(BaseCommand):
    help = (
        "Run the P4 retrieval benchmark comparing graph-RAG vs baseline. "
        "Loads questions from backend/helpdesk/benchmarks/benchmark-questions.yaml (or --input), "
        "runs each question in both modes, and writes a JSON + summary report."
    )

    def add_arguments(self, parser):
        repo_root = Path(__file__).resolve().parents[4]
        parser.add_argument(
            "--input",
            default=str(DEFAULT_QUESTIONS_PATH),
            help="Path to benchmark YAML question file.",
        )
        parser.add_argument(
            "--output",
            default=str(repo_root / "docs" / "testing" / "benchmark-report.json"),
            help="Path to write the JSON benchmark report.",
        )
        parser.add_argument(
            "--top-k",
            type=int,
            default=20,
            help="Default top-k for retrieval (per-question threshold can override).",
        )
        parser.add_argument(
            "--scope",
            nargs="*",
            default=None,
            help="Optional standards scope filter passed to retrieve_chunks_with_trace.",
        )
        parser.add_argument(
            "--app-scope",
            action="store_true",
            help=(
                "Search with the scope the answer endpoints choose for each question (question "
                "parsing plus the ambiguity cut) instead of no scope. With GraphDB disabled the "
                "scope comes from named standards and in-memory concepts only."
            ),
        )
        parser.add_argument(
            "--tags",
            nargs="*",
            default=None,
            help="Run only questions whose tags list contains at least one of these tags.",
        )
        parser.add_argument(
            "--ids",
            nargs="*",
            default=None,
            help="Run only question IDs matching this list (e.g. q001 q002).",
        )
        parser.add_argument(
            "--baseline-only",
            action="store_true",
            help="Run only baseline retrieval (skip graph-RAG run).",
        )
        parser.add_argument(
            "--graph-only",
            action="store_true",
            help="Run only graph-RAG retrieval (skip baseline run).",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress per-question progress output.",
        )
        parser.add_argument(
            "--gate-against",
            default=None,
            help=(
                "Reference report/baseline JSON with an 'aggregate' section. Exit non-zero if "
                "hit@10 or MRR@10 dropped by more than --max-drop in any mode present in both."
            ),
        )
        parser.add_argument(
            "--max-drop",
            type=float,
            default=0.03,
            help="Allowed absolute drop per gated metric (default 0.03).",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"]).expanduser().resolve()
        output_path = Path(options["output"]).expanduser().resolve()
        top_k: int = options["top_k"]
        scope: list[str] | None = options.get("scope") or None
        app_scope: bool = bool(options.get("app_scope"))
        filter_tags: list[str] | None = options.get("tags") or None
        filter_ids: list[str] | None = options.get("ids") or None
        baseline_only: bool = bool(options.get("baseline_only"))
        graph_only: bool = bool(options.get("graph_only"))
        quiet: bool = bool(options.get("quiet"))
        gate_path = Path(options["gate_against"]).expanduser().resolve() if options.get("gate_against") else None
        max_drop: float = options["max_drop"]

        if gate_path is not None and not gate_path.exists():
            raise CommandError(f"Gate reference file not found: {gate_path}")

        if app_scope and scope:
            raise CommandError("--app-scope and --scope cannot be combined.")

        if not input_path.exists():
            raise CommandError(f"Benchmark question file not found: {input_path}")

        payload = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
        all_questions: list[dict] = payload.get("questions") or []
        if not all_questions:
            raise CommandError("No questions found in benchmark file.")

        # Apply filters
        questions = all_questions
        if filter_ids:
            id_set = set(filter_ids)
            questions = [q for q in questions if q.get("id") in id_set]
        if filter_tags:
            tag_set = set(filter_tags)
            questions = [q for q in questions if set(q.get("tags") or []).intersection(tag_set)]

        self.stdout.write(
            self.style.SUCCESS(f"Running benchmark: {len(questions)} questions, top_k={top_k}")
        )
        if scope:
            self.stdout.write(f"  scope filter: {scope}")
        if app_scope:
            self.stdout.write("  scope: chosen per question as the answer endpoints do")
        if baseline_only:
            self.stdout.write("  mode: baseline only")
        elif graph_only:
            self.stdout.write("  mode: graph-RAG only")
        else:
            self.stdout.write("  mode: both (baseline + graph-RAG)")

        per_question_results = []

        for idx, q in enumerate(questions, start=1):
            qid = q.get("id", f"q{idx:03d}")
            question_text = q.get("question", "")
            intent = q.get("intent", "")
            tags = q.get("tags") or []

            question_scope = scope
            cut_to_first = False
            if app_scope:
                semantic_query = parse_question_to_semantic_query(text=question_text, requested_scope=[])
                question_scope, cut_to_first = select_effective_scope(semantic_query, [])

            if not quiet:
                self.stdout.write(f"  [{idx}/{len(questions)}] {qid}: {question_text[:70]}...")

            result_entry: dict = {
                "id": qid,
                "question": question_text,
                "intent": intent,
                "tags": tags,
                "expected_source_patterns": q.get("expected_source_patterns") or [],
                "min_hits": q.get("min_hits", 1),
            }
            if app_scope:
                result_entry["scope"] = question_scope
                result_entry["scope_cut_to_first_candidate"] = cut_to_first

            if not graph_only:
                baseline = _run_question(
                    question_dict=q,
                    top_k=top_k,
                    graph_rag_enabled=False,
                    scope=question_scope,
                )
                result_entry["baseline"] = baseline
                if not quiet:
                    self.stdout.write(
                        f"    baseline: hit@10={baseline['hit_at_10']} "
                        f"mrr@10={baseline['mrr_at_10']:.3f} "
                        f"latency={baseline['latency_ms']}ms"
                    )

            if not baseline_only:
                graph = _run_question(
                    question_dict=q,
                    top_k=top_k,
                    graph_rag_enabled=True,
                    scope=question_scope,
                )
                result_entry["graph"] = graph
                if not quiet:
                    self.stdout.write(
                        f"    graph:    hit@10={graph['hit_at_10']} "
                        f"mrr@10={graph['mrr_at_10']:.3f} "
                        f"latency={graph['latency_ms']}ms "
                        f"expansion={graph['graph_expansion_source']}"
                    )

            per_question_results.append(result_entry)

        # Aggregate statistics
        def _agg_mode(mode_key: str) -> dict:
            mode_results = [r[mode_key] for r in per_question_results if mode_key in r]
            if not mode_results:
                return {}
            return {
                "hit_at_5": round(_aggregate(mode_results, "hit_at_5"), 4),
                "hit_at_10": round(_aggregate(mode_results, "hit_at_10"), 4),
                "hit_at_20": round(_aggregate(mode_results, "hit_at_20"), 4),
                "mrr_at_10": round(_aggregate(mode_results, "mrr_at_10"), 4),
                "mrr_at_20": round(_aggregate(mode_results, "mrr_at_20"), 4),
                "mean_latency_ms": round(_aggregate(mode_results, "latency_ms"), 1),
            }

        aggregate: dict = {}
        if not graph_only:
            aggregate["baseline"] = _agg_mode("baseline")
        if not baseline_only:
            aggregate["graph"] = _agg_mode("graph")

        # Compute graph vs baseline delta if both modes ran
        if "baseline" in aggregate and "graph" in aggregate:
            b = aggregate["baseline"]
            g = aggregate["graph"]
            questions_improved = sum(
                1
                for r in per_question_results
                if "baseline" in r
                and "graph" in r
                and r["graph"]["hit_at_10"]
                and not r["baseline"]["hit_at_10"]
            )
            questions_regressed = sum(
                1
                for r in per_question_results
                if "baseline" in r
                and "graph" in r
                and r["baseline"]["hit_at_10"]
                and not r["graph"]["hit_at_10"]
            )
            aggregate["delta"] = {
                "hit_at_10_delta": round(g["hit_at_10"] - b["hit_at_10"], 4),
                "mrr_at_10_delta": round(g["mrr_at_10"] - b["mrr_at_10"], 4),
                "latency_overhead_ms": round(g["mean_latency_ms"] - b["mean_latency_ms"], 1),
                "questions_improved_by_graph": questions_improved,
                "questions_regressed_by_graph": questions_regressed,
            }

        report = {
            "benchmark_input": str(input_path),
            "top_k": top_k,
            "scope": scope,
            "app_scope": app_scope,
            "total_questions": len(questions),
            "aggregate": aggregate,
            "questions": per_question_results,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Benchmark summary ==="))
        self.stdout.write(f"Questions run: {len(questions)}")
        if "baseline" in aggregate:
            b = aggregate["baseline"]
            self.stdout.write(
                f"Baseline  hit@10={b['hit_at_10']:.3f} "
                f"mrr@10={b['mrr_at_10']:.3f} "
                f"latency={b['mean_latency_ms']}ms"
            )
        if "graph" in aggregate:
            g = aggregate["graph"]
            self.stdout.write(
                f"Graph-RAG hit@10={g['hit_at_10']:.3f} "
                f"mrr@10={g['mrr_at_10']:.3f} "
                f"latency={g['mean_latency_ms']}ms"
            )
        if "delta" in aggregate:
            d = aggregate["delta"]
            self.stdout.write(
                f"Delta     hit@10={d['hit_at_10_delta']:+.3f} "
                f"mrr@10={d['mrr_at_10_delta']:+.3f} "
                f"latency_overhead={d['latency_overhead_ms']:+.0f}ms"
            )
            self.stdout.write(
                f"          improved={d['questions_improved_by_graph']} "
                f"regressed={d['questions_regressed_by_graph']}"
            )
        self.stdout.write(f"Report written: {output_path}")

        if gate_path is not None:
            reference = json.loads(gate_path.read_text(encoding="utf-8")).get("aggregate") or {}
            failures = check_regression(aggregate, reference, max_drop)
            if failures:
                for failure in failures:
                    self.stdout.write(self.style.ERROR(f"REGRESSION {failure}"))
                raise CommandError(f"{len(failures)} metric(s) regressed against {gate_path.name}")
            self.stdout.write(self.style.SUCCESS(f"Gate passed against {gate_path.name} (max drop {max_drop})"))
