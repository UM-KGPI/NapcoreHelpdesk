from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError

from helpdesk.management.commands.benchmark_utils import DEFAULT_QUESTIONS_PATH
from helpdesk.services import semantic_graph
from helpdesk.services.answer_retrieval_defaults import (
    ANSWER_RETRIEVAL_MIN_SCORE,
    ANSWER_RETRIEVAL_TOP_K,
    answer_min_evidence_results,
)
from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

GATED_METRICS = ("hit_at_10", "mrr_at_10")

# Every line the command prints about the conditions or the ontology starts with one of these, so a log can
# be searched for them.
INFO_PREFIX = "BENCH-CONDITIONS:"
WARNING_PREFIX = "BENCH-WARNING:"
DEFAULT_TOP_K = 20


def ontology_state() -> dict:
    """How many concepts the process holds in its alias table (what question concept extraction and the
    passage boost read), and, when none, why."""
    concepts = len(semantic_graph.GRAPH_CONCEPT_ALIASES)
    reason = None
    if concepts == 0:
        if semantic_graph.SKIP_GRAPHDB_IMPORT:
            reason = "NAPCORE_SKIP_GRAPHDB_IMPORT is set, so the ontology load returns an empty table"
        elif not semantic_graph._env_truthy("GRAPHDB_ENABLED", default=False):
            reason = "GRAPHDB_ENABLED is off, so the ontology load returns an empty table"
        else:
            reason = "GraphDB returned no concepts with labels"
    return {"ontology_concepts": concepts, "ontology_empty": concepts == 0, "ontology_empty_reason": reason}


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
    app_conditions: dict | None = None,
) -> dict:
    """app_conditions (min_score, min_results) switches to the answer endpoint's retrieval call: k is top_k
    for every question, whatever the question's own threshold, and only the first k passages count."""
    expected_patterns: list[str] = question_dict.get("expected_source_patterns") or []
    min_hits: int = question_dict.get("min_hits", 1)
    q_threshold: int = question_dict.get("top_k_threshold", top_k)
    effective_k = max(top_k, q_threshold)

    start = time.time()
    if app_conditions is None:
        chunks, trace = retrieve_chunks_with_trace(
            question=question_dict["question"],
            top_k=effective_k,
            min_score=0.0,
            scope=scope,
            graph_rag_enabled=graph_rag_enabled,
        )
    else:
        chunks, trace = retrieve_chunks_with_trace(
            question=question_dict["question"],
            top_k=top_k,
            min_score=app_conditions["min_score"],
            scope=scope,
            graph_rag_enabled=graph_rag_enabled,
            min_results=app_conditions["min_results"],
        )
        chunks = chunks[:top_k]
    latency_ms = round((time.time() - start) * 1000, 1)

    if app_conditions is not None:
        return {
            "hit_at_5": _hit_at_k(chunks, expected_patterns, 5, min_hits),
            f"hit_at_{top_k}": _hit_at_k(chunks, expected_patterns, top_k, min_hits),
            f"mrr_at_{top_k}": _mrr_at_k(chunks, expected_patterns, top_k),
            "passages": len(chunks),
            "latency_ms": latency_ms,
            f"top_{top_k}_paths": [str(c.get("sourcePath") or "") for c in chunks],
            "graph_expansion_source": trace.get("graphExpansionSource", "none"),
            "graph_candidates_added": trace.get("graphCandidatesAdded", 0),
        }

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
            default=None,
            help=(
                f"Default top-k for retrieval (default {DEFAULT_TOP_K}; the per-question threshold can "
                "raise it). Not accepted with --app-conditions, which uses the answer endpoint's k."
            ),
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
            "--app-conditions",
            action="store_true",
            help=(
                "Measure what the answer endpoint serves: a fixed k for every question (the endpoint's "
                "retrievalTopK), its minimum score and its min_results, read from the same constants and "
                "settings the endpoint reads. Reports hit@5, hit@k and MRR@k, and how many questions end "
                "with fewer than k passages and with none. Refuses an empty ontology in graph mode unless "
                "--acknowledge-empty-ontology-is-not-the-app is given. Cannot be combined with "
                "--gate-against (the baseline is measured at the benchmark's own k)."
            ),
        )
        parser.add_argument(
            "--acknowledge-empty-ontology-is-not-the-app",
            action="store_true",
            help=(
                "With --app-conditions: run graph mode although the ontology holds no concepts. The numbers "
                "are then not the application's, and the report says so."
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
        app_conditions: bool = bool(options.get("app_conditions"))
        acknowledged_empty: bool = bool(options.get("acknowledge_empty_ontology_is_not_the_app"))
        if app_conditions and options["top_k"] is not None:
            raise CommandError("--top-k cannot be combined with --app-conditions: k is the answer endpoint's.")
        if acknowledged_empty and not app_conditions:
            raise CommandError("--acknowledge-empty-ontology-is-not-the-app only applies with --app-conditions.")
        top_k: int = ANSWER_RETRIEVAL_TOP_K if app_conditions else (DEFAULT_TOP_K if options["top_k"] is None else options["top_k"])
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

        if app_conditions and gate_path is not None:
            raise CommandError(
                "--gate-against cannot be combined with --app-conditions: the reference is measured at the "
                "benchmark's own k and has no figure for the endpoint's."
            )

        # Conditions of this run, written into the report and printed first.
        retrieval_args = (
            {"min_score": ANSWER_RETRIEVAL_MIN_SCORE, "min_results": answer_min_evidence_results()}
            if app_conditions
            else None
        )
        graph_requested = not baseline_only
        ontology = ontology_state()
        warnings: list[str] = []
        if graph_requested and ontology["ontology_empty"]:
            warnings.append(
                f"{WARNING_PREFIX} graph mode ran without ontology concepts: {ontology['ontology_empty_reason']}. "
                "Question concepts and the passage boost are missing, so these graph figures are not the "
                "application's."
            )
        if app_conditions and warnings and not acknowledged_empty:
            raise CommandError(
                warnings[0] + " --app-conditions measures the application's path and refuses to run this "
                "way; load the ontology (GraphDB reachable, NAPCORE_SKIP_GRAPHDB_IMPORT unset), "
                "or pass --acknowledge-empty-ontology-is-not-the-app."
            )
        conditions = {
            "mode": "app-conditions" if app_conditions else "benchmark",
            "fixed_k": top_k if app_conditions else None,
            "k_floor": None if app_conditions else top_k,
            "min_score": retrieval_args["min_score"] if app_conditions else 0.0,
            "min_results": retrieval_args["min_results"] if app_conditions else 0,
            "scope_mode": "app" if app_scope else ("explicit" if scope else "none"),
            "graph_requested": graph_requested,
            "empty_ontology_acknowledged": acknowledged_empty,
            **ontology,
            "warnings": warnings,
        }

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

        self.stdout.write(
            f"{INFO_PREFIX} mode={conditions['mode']} "
            + (
                f"fixed_k={top_k}"
                if app_conditions
                else f"k=max({top_k}, the question's own threshold)"
            )
            + f" min_score={conditions['min_score']} min_results={conditions['min_results']} "
            f"scope={conditions['scope_mode']} ontology_concepts={ontology['ontology_concepts']}"
        )
        for warning in warnings:
            self.stdout.write(self.style.WARNING(warning))

        # The metric the per-question lines and the improved/regressed counts use: hit@10 in the benchmark's
        # own mode, hit@k in the endpoint's.
        hit_k = top_k if app_conditions else 10
        hit_key, mrr_key = f"hit_at_{hit_k}", f"mrr_at_{hit_k}"
        per_question_results = []

        for idx, q in enumerate(questions, start=1):
            qid = q.get("id", f"q{idx:03d}")
            question_text = q.get("question", "")
            intent = q.get("intent", "")
            tags = q.get("tags") or []

            question_scope = scope
            needs_clarification = False
            if app_scope:
                semantic_query = parse_question_to_semantic_query(text=question_text, requested_scope=[])
                question_scope, needs_clarification = select_effective_scope(semantic_query, [])

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
                result_entry["scope_needs_clarification"] = needs_clarification

            if not graph_only:
                baseline = _run_question(
                    question_dict=q,
                    top_k=top_k,
                    graph_rag_enabled=False,
                    scope=question_scope,
                    app_conditions=retrieval_args,
                )
                result_entry["baseline"] = baseline
                if not quiet:
                    self.stdout.write(
                        f"    baseline: hit@{hit_k}={baseline[hit_key]} "
                        f"mrr@{hit_k}={baseline[mrr_key]:.3f} "
                        f"latency={baseline['latency_ms']}ms"
                    )

            if not baseline_only:
                graph = _run_question(
                    question_dict=q,
                    top_k=top_k,
                    graph_rag_enabled=True,
                    scope=question_scope,
                    app_conditions=retrieval_args,
                )
                result_entry["graph"] = graph
                if not quiet:
                    self.stdout.write(
                        f"    graph:    hit@{hit_k}={graph[hit_key]} "
                        f"mrr@{hit_k}={graph[mrr_key]:.3f} "
                        f"latency={graph['latency_ms']}ms "
                        f"expansion={graph['graph_expansion_source']}"
                    )

            per_question_results.append(result_entry)

        # Aggregate statistics
        def _agg_mode(mode_key: str) -> dict:
            mode_results = [r[mode_key] for r in per_question_results if mode_key in r]
            if not mode_results:
                return {}
            if app_conditions:
                return {
                    "hit_at_5": round(_aggregate(mode_results, "hit_at_5"), 4),
                    hit_key: round(_aggregate(mode_results, hit_key), 4),
                    mrr_key: round(_aggregate(mode_results, mrr_key), 4),
                    f"hit_count_at_{hit_k}": sum(1 for r in mode_results if r[hit_key]),
                    f"questions_with_fewer_than_{hit_k}_passages": sum(1 for r in mode_results if r["passages"] < hit_k),
                    "questions_with_no_passages": sum(1 for r in mode_results if r["passages"] == 0),
                    "mean_latency_ms": round(_aggregate(mode_results, "latency_ms"), 1),
                }
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
                and r["graph"][hit_key]
                and not r["baseline"][hit_key]
            )
            questions_regressed = sum(
                1
                for r in per_question_results
                if "baseline" in r
                and "graph" in r
                and r["baseline"][hit_key]
                and not r["graph"][hit_key]
            )
            aggregate["delta"] = {
                f"{hit_key}_delta": round(g[hit_key] - b[hit_key], 4),
                f"{mrr_key}_delta": round(g[mrr_key] - b[mrr_key], 4),
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
            "conditions": conditions,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Benchmark summary ==="))
        self.stdout.write(f"Questions run: {len(questions)}")
        if "baseline" in aggregate:
            b = aggregate["baseline"]
            self.stdout.write(
                f"Baseline  hit@{hit_k}={b[hit_key]:.3f} "
                f"mrr@{hit_k}={b[mrr_key]:.3f} "
                f"latency={b['mean_latency_ms']}ms"
            )
        if "graph" in aggregate:
            g = aggregate["graph"]
            self.stdout.write(
                f"Graph-RAG hit@{hit_k}={g[hit_key]:.3f} "
                f"mrr@{hit_k}={g[mrr_key]:.3f} "
                f"latency={g['mean_latency_ms']}ms"
            )
        if app_conditions:
            for mode_name in ("baseline", "graph"):
                if mode_name in aggregate:
                    a = aggregate[mode_name]
                    self.stdout.write(
                        f"{INFO_PREFIX} {mode_name} hit@5={a['hit_at_5']:.3f} "
                        f"hit_count@{hit_k}={a[f'hit_count_at_{hit_k}']} of {len(questions)} "
                        f"fewer_than_{hit_k}_passages={a[f'questions_with_fewer_than_{hit_k}_passages']} "
                        f"no_passages={a['questions_with_no_passages']}"
                    )
        if "delta" in aggregate:
            d = aggregate["delta"]
            self.stdout.write(
                f"Delta     hit@{hit_k}={d[f'{hit_key}_delta']:+.3f} "
                f"mrr@{hit_k}={d[f'{mrr_key}_delta']:+.3f} "
                f"latency_overhead={d['latency_overhead_ms']:+.0f}ms"
            )
            self.stdout.write(
                f"          improved={d['questions_improved_by_graph']} "
                f"regressed={d['questions_regressed_by_graph']}"
            )
        for warning in warnings:
            self.stdout.write(self.style.WARNING(warning))
        self.stdout.write(f"Report written: {output_path}")

        if gate_path is not None:
            reference = json.loads(gate_path.read_text(encoding="utf-8")).get("aggregate") or {}
            failures = check_regression(aggregate, reference, max_drop)
            if failures:
                for failure in failures:
                    self.stdout.write(self.style.ERROR(f"REGRESSION {failure}"))
                raise CommandError(f"{len(failures)} metric(s) regressed against {gate_path.name}")
            self.stdout.write(self.style.SUCCESS(f"Gate passed against {gate_path.name} (max drop {max_drop})"))
