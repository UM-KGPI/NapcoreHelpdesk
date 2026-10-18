from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path

import yaml
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from helpdesk.management.commands.benchmark_utils import DEFAULT_QUESTIONS_PATH, load_benchmark_questions
from helpdesk.management.commands.run_retrieval_benchmark import check_regression

REFERENCE = {
    "baseline": {"hit_at_10": 0.80, "mrr_at_10": 0.40},
    "graph": {"hit_at_10": 0.90, "mrr_at_10": 0.50},
}


class CheckRegressionTests(SimpleTestCase):
    def test_no_failures_when_metrics_hold_or_improve(self):
        current = {
            "baseline": {"hit_at_10": 0.80, "mrr_at_10": 0.41},
            "graph": {"hit_at_10": 0.95, "mrr_at_10": 0.50},
        }
        self.assertEqual(check_regression(current, REFERENCE, max_drop=0.03), [])

    def test_small_drop_within_tolerance_passes(self):
        current = {"graph": {"hit_at_10": 0.88, "mrr_at_10": 0.48}}
        self.assertEqual(check_regression(current, REFERENCE, max_drop=0.03), [])

    def test_drop_beyond_tolerance_names_mode_and_metric(self):
        current = {"graph": {"hit_at_10": 0.85, "mrr_at_10": 0.50}}
        failures = check_regression(current, REFERENCE, max_drop=0.03)
        self.assertEqual(len(failures), 1)
        self.assertIn("graph hit_at_10", failures[0])
        self.assertIn("0.850", failures[0])

    def test_only_modes_present_in_both_are_compared(self):
        current = {"graph": {"hit_at_10": 0.90, "mrr_at_10": 0.50}}
        reference = {"baseline": {"hit_at_10": 0.99, "mrr_at_10": 0.99}, "graph": current["graph"]}
        self.assertEqual(check_regression(current, reference, max_drop=0.03), [])

    def test_latency_is_never_gated(self):
        current = {"graph": {"hit_at_10": 0.90, "mrr_at_10": 0.50, "mean_latency_ms": 99999.0}}
        reference = {"graph": {"hit_at_10": 0.90, "mrr_at_10": 0.50, "mean_latency_ms": 10.0}}
        self.assertEqual(check_regression(current, reference, max_drop=0.03), [])


class GateAgainstArgumentTests(SimpleTestCase):
    def test_missing_reference_file_is_an_error_before_any_question_runs(self):
        with self.assertRaisesMessage(CommandError, "Gate reference file not found"):
            call_command("run_retrieval_benchmark", gate_against="/nonexistent/reference.json")


class TrackedQuestionsTests(SimpleTestCase):
    def test_questions_file_is_tracked_next_to_the_app(self):
        self.assertTrue(DEFAULT_QUESTIONS_PATH.exists(), DEFAULT_QUESTIONS_PATH)
        self.assertEqual(DEFAULT_QUESTIONS_PATH.parent.name, "benchmarks")

    def test_questions_are_well_formed(self):
        questions = load_benchmark_questions()
        self.assertEqual(len(questions), 120)
        ids = [q["id"] for q in questions]
        self.assertEqual([i for i, n in Counter(ids).items() if n > 1], [])
        for question in questions:
            self.assertTrue(question["question"].strip(), question["id"])
            self.assertIn("intent", question, question["id"])
            if question["intent"] != "abstention":
                self.assertTrue(question.get("expected_source_patterns"), question["id"])

    def test_questions_file_parses_as_yaml_mapping(self):
        payload = yaml.safe_load(Path(DEFAULT_QUESTIONS_PATH).read_text(encoding="utf-8"))
        self.assertIsInstance(payload, dict)
        self.assertIn("questions", payload)
