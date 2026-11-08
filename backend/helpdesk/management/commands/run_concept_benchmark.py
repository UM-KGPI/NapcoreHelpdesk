"""Measure how the concepts a question is about are found (benchmarks/concept-questions.yaml).

Usage: python manage.py run_concept_benchmark [--input PATH] [--top 3]
Methods: words (label words and the head-word rule), semantic (whole question), subject (semantic, on the
question without its frame words), hybrid (words, else subject), app (presence_concepts, what answers use). A question passes when an expected
Transmodel class, or a standard's class aligned to it, is among the first --top concepts.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand

DEFAULT_INPUT = Path(__file__).resolve().parents[2] / "benchmarks" / "concept-questions.yaml"


def _transmodel(concept_id: str) -> str:
    from helpdesk.services.semantic_graph import CONCEPT_TO_TRANSMODEL

    return concept_id if concept_id.startswith("transmodel:") else CONCEPT_TO_TRANSMODEL.get(concept_id, concept_id)


class Command(BaseCommand):
    help = "Measure concept recognition: label words, semantic, and hybrid."

    def add_arguments(self, parser):
        parser.add_argument("--input", default=str(DEFAULT_INPUT))
        parser.add_argument("--top", type=int, default=3)

    def handle(self, *args, **options):
        from helpdesk.services.concept_presence import _labelled_concepts, head_word_concepts, presence_concepts
        from helpdesk.services.concept_vectors import question_subject, semantic_concepts
        from helpdesk.services.llm_generator import english_search_query

        questions = yaml.safe_load(Path(options["input"]).read_text(encoding="utf-8"))["questions"]
        top = options["top"]
        methods = {
            "words": lambda q: _labelled_concepts(q) or head_word_concepts(q),
            "semantic": lambda q: [c["concept_id"] for c in semantic_concepts(q, limit=top * 2)],
            "subject": lambda q: [c["concept_id"] for c in semantic_concepts(question_subject(q), limit=top * 2)],
        }
        methods["hybrid"] = lambda q: methods["words"](q) or methods["subject"](q)
        # What the app uses (presence_concepts): labels when the meaning agrees, literal first for
        # existence questions, then the nearest by meaning.
        methods["app"] = lambda q: presence_concepts(q)
        passed = {name: 0 for name in methods}
        for item in questions:
            question = item["question"]
            english = english_search_query(question) or question
            expected = {f"transmodel:{e}" for e in item["expected"]}
            row = []
            for name, method in methods.items():
                found = list(dict.fromkeys(_transmodel(c) for c in method(english)))[:top]
                ok = bool(expected & set(found))
                passed[name] += ok
                row.append(f"{name}={'✓' if ok else '✗'}{[f.split(':')[1] for f in found]}")
            self.stdout.write(f"{item['id']} {question[:58]:58} | " + " | ".join(row))
        total = len(questions)
        self.stdout.write("")
        self.stdout.write("hit@%d: " % top + "  ".join(f"{name} {passed[name]}/{total} ({passed[name] / total:.2f})" for name in methods))
