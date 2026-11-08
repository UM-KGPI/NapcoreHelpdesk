"""Run the NeTEx example generator over its benchmark questions and report validity, attempts and time.

Each question goes through retrieval as in the app (graph-RAG, app scope) and then the generator, which
calls the model and the netex-validator service. Needs LLM_ENABLED and a reachable NETEX_VALIDATOR_URL.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand

from helpdesk.services.netex_example_generator import generate_netex_example
from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

DEFAULT_QUESTIONS = Path(__file__).resolve().parents[2] / "benchmarks" / "example-generation-questions.yaml"


class Command(BaseCommand):
    help = "Measure the NeTEx example generator: valid fragments, attempts, model and validator time."

    def add_arguments(self, parser):
        parser.add_argument("--input", default=str(DEFAULT_QUESTIONS))
        parser.add_argument("--output", default="", help="Write per-question results as JSON.")

    def handle(self, *args, **options):
        questions = yaml.safe_load(Path(options["input"]).read_text(encoding="utf-8"))["questions"]
        rows = []
        for item in questions:
            question = item["question"]
            semantic_query = parse_question_to_semantic_query(text=question, requested_scope=[])
            scope, _ = select_effective_scope(semantic_query, [])
            chunks, _trace = retrieve_chunks_with_trace(question=question, top_k=6, min_score=0.62, scope=scope, graph_rag_enabled=True)
            result = generate_netex_example(question, chunks, scope) or {"valid": False, "attempts": 0, "errors": ["not triggered"]}
            rows.append({"id": item["id"], "question": question, **result})
            self.stdout.write(
                f"{item['id']} valid={result.get('valid')} attempts={result.get('attempts')} "
                f"model={result.get('generationMs', 0)} ms validator={result.get('validationMs', 0)} ms"
            )
        valid = [row for row in rows if row.get("valid")]
        self.stdout.write(
            f"\nvalid {len(valid)} of {len(rows)} | first attempt {sum(1 for row in valid if row['attempts'] == 1)} | "
            f"median model {statistics.median(row.get('generationMs', 0) for row in rows):.0f} ms | "
            f"median validator {statistics.median(row.get('validationMs', 0) for row in rows):.0f} ms"
        )
        if options["output"]:
            Path(options["output"]).write_text(json.dumps(rows, indent=1), encoding="utf-8")
