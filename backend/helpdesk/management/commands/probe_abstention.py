"""
Show, for a set of questions, whether the semantic abstention rules would refuse them.

The retrieval benchmark measures what is found for questions that are answered; it cannot show which
questions are refused, because refusal happens before retrieval. This runs the real question parser
(GraphDB anchoring included when enabled) and the real abstention rules, without retrieval, the FAQ
or the LLM, and writes one decision per question as JSON so two runs can be diffed.

Usage:
    python manage.py probe_abstention --output probe.json
    python manage.py probe_abstention --questions extra.yaml --no-benchmark
    python manage.py probe_abstention --retrieval --output probe.json

With --retrieval each question is also retrieved as the answer view does (top_k 6, min score 0.62,
retry at 0.45 when nothing passes) and the inputs of the evidence gate are recorded: chunk count,
semantic alignment, repository coverage, best chunk score.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand

from django.conf import settings

from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace
from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
from helpdesk.services.semantic_abstention import (
    LOW_CONFIDENCE_MESSAGE,
    NO_CONCEPT_MESSAGE,
    semantic_abstention_message,
)

BENCHMARKS = Path(__file__).resolve().parent.parent.parent / "benchmarks"
_DECISIONS = {NO_CONCEPT_MESSAGE: "abstain_no_concept", LOW_CONFIDENCE_MESSAGE: "abstain_low_confidence"}


def _load(path: Path, category: str | None = None) -> list[dict]:
    questions = yaml.safe_load(path.read_text(encoding="utf-8"))["questions"]
    return [{"category": category, **q} if category else q for q in questions]


class Command(BaseCommand):
    help = "Report the semantic abstention decision for each probe question (no retrieval, no LLM)."

    def add_arguments(self, parser):
        parser.add_argument("--questions", type=Path, default=BENCHMARKS / "abstention-probe-questions.yaml")
        parser.add_argument(
            "--no-benchmark",
            action="store_true",
            help="Probe only --questions, not the retrieval benchmark questions as well.",
        )
        parser.add_argument(
            "--retrieval",
            action="store_true",
            help="Also retrieve each question and record the evidence-gate inputs (slower).",
        )
        parser.add_argument("--output", type=Path, help="Write the decisions as JSON to this path.")

    def handle(self, *args, **options):
        questions = _load(options["questions"])
        if not options["no_benchmark"]:
            questions += _load(BENCHMARKS / "benchmark-questions.yaml", category="benchmark")

        rows = []
        for item in questions:
            semantic = parse_question_to_semantic_query(text=item["question"], requested_scope=None)
            effective_scope, _ = select_effective_scope(semantic, None)
            message = semantic_abstention_message(
                semantic_query=semantic,
                effective_scope=effective_scope,
                requested_scope=None,
                allow_abstain=True,
            )
            decision = _DECISIONS.get(message, "answer")
            retrieval = self._retrieve(item["question"], effective_scope) if options["retrieval"] else {}
            rows.append(
                {
                    **retrieval,
                    "id": item["id"],
                    "category": item.get("category", ""),
                    "question": item["question"],
                    "decision": decision,
                    "expect": item.get("expect"),
                    "coreConcept": semantic.core_concept,
                    "conceptConfidence": (semantic.confidence or {}).get("concept"),
                    "scope": effective_scope,
                    "discoveredStandards": semantic.discovered_standards,
                }
            )

        by_category: dict[str, dict[str, int]] = {}
        for row in rows:
            counts = by_category.setdefault(row["category"], {})
            counts[row["decision"]] = counts.get(row["decision"], 0) + 1
        for category, counts in by_category.items():
            self.stdout.write(f"{category:20s} " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        for row in rows:
            if row["expect"] and (row["decision"] == "answer") != (row["expect"] == "answer"):
                self.stdout.write(f"  disagrees with expectation ({row['expect']}): {row['id']} {row['question']}")

        if options["output"]:
            options["output"].write_text(json.dumps({"questions": rows}, indent=2) + "\n", encoding="utf-8")
            self.stdout.write(f"wrote {options['output']}")

    @staticmethod
    def _retrieve(question: str, scope: list[str]) -> dict:
        graph_rag = bool(getattr(settings, "GRAPH_RAG_ENABLED", False))
        chunks, trace = retrieve_chunks_with_trace(
            question=question, top_k=6, min_score=0.62, scope=scope, graph_rag_enabled=graph_rag
        )
        relaxed = False
        if not chunks:
            relaxed = True
            chunks, trace = retrieve_chunks_with_trace(
                question=question, top_k=6, min_score=0.45, scope=scope, graph_rag_enabled=graph_rag
            )
        return {
            "chunks": len(chunks),
            "relaxedRetry": relaxed,
            "topScore": round(max((c.get("score", 0.0) for c in chunks), default=0.0), 4),
            "alignment": trace.get("semanticAlignmentScore"),
            "repositoryCoverage": trace.get("repositoryCoverageCount"),
        }
