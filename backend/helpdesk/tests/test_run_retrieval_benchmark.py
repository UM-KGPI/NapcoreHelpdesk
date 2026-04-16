from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml
from django.test import SimpleTestCase


def _minimal_chunk(source_path: str, score: float = 0.8) -> dict:
    return {
        "sourcePath": source_path,
        "score": score,
        "label": "",
        "repositoryUrl": "https://example.com",
        "standardsScope": [],
    }


class HitAtKTests(SimpleTestCase):
    """Unit tests for hit@k and MRR helper functions."""

    def _import(self):
        from helpdesk.management.commands.run_retrieval_benchmark import (
            _hit_at_k,
            _mrr_at_k,
        )
        return _hit_at_k, _mrr_at_k

    def test_hit_at_k_matches_substring(self):
        _hit_at_k, _ = self._import()
        chunks = [_minimal_chunk("examples/DelayedAndCancelledJourneysWithEvents.xml")]
        self.assertTrue(_hit_at_k(chunks, ["DelayedAndCancelled"], k=5, min_hits=1))

    def test_hit_at_k_misses_wrong_pattern(self):
        _hit_at_k, _ = self._import()
        chunks = [_minimal_chunk("examples/PlannedCapacity.xml")]
        self.assertFalse(_hit_at_k(chunks, ["DelayedAndCancelled"], k=5, min_hits=1))

    def test_hit_at_k_respects_k_boundary(self):
        _hit_at_k, _ = self._import()
        chunks = [
            _minimal_chunk("examples/other.xml"),
            _minimal_chunk("examples/other2.xml"),
            _minimal_chunk("examples/DelayedAndCancelled.xml"),
        ]
        self.assertFalse(_hit_at_k(chunks, ["DelayedAndCancelled"], k=2, min_hits=1))
        self.assertTrue(_hit_at_k(chunks, ["DelayedAndCancelled"], k=3, min_hits=1))

    def test_hit_at_k_min_hits_two(self):
        _hit_at_k, _ = self._import()
        chunks = [
            _minimal_chunk("examples/DelayedAndCancelled.xml"),
            _minimal_chunk("xsd/opra_framework/opra_delay.xsd"),
        ]
        self.assertTrue(_hit_at_k(chunks, ["DelayedAndCancelled", "opra_framework"], k=5, min_hits=2))
        self.assertFalse(_hit_at_k(chunks, ["DelayedAndCancelled", "missing_pattern"], k=5, min_hits=2))

    def test_hit_at_k_abstention_always_passes(self):
        _hit_at_k, _ = self._import()
        chunks: list[dict] = []
        self.assertTrue(_hit_at_k(chunks, [], k=10, min_hits=0))

    def test_mrr_at_k_first_rank(self):
        _, _mrr_at_k = self._import()
        chunks = [_minimal_chunk("examples/DelayedAndCancelled.xml")]
        self.assertAlmostEqual(_mrr_at_k(chunks, ["DelayedAndCancelled"], k=10), 1.0)

    def test_mrr_at_k_second_rank(self):
        _, _mrr_at_k = self._import()
        chunks = [
            _minimal_chunk("examples/other.xml"),
            _minimal_chunk("examples/DelayedAndCancelled.xml"),
        ]
        self.assertAlmostEqual(_mrr_at_k(chunks, ["DelayedAndCancelled"], k=10), 0.5)

    def test_mrr_at_k_no_match(self):
        _, _mrr_at_k = self._import()
        chunks = [_minimal_chunk("examples/nothing.xml")]
        self.assertAlmostEqual(_mrr_at_k(chunks, ["DelayedAndCancelled"], k=10), 0.0)

    def test_mrr_at_k_empty_patterns(self):
        _, _mrr_at_k = self._import()
        chunks = [_minimal_chunk("examples/anything.xml")]
        self.assertAlmostEqual(_mrr_at_k(chunks, [], k=10), 0.0)


class RunRetrievalBenchmarkCommandTests(SimpleTestCase):
    """Integration tests for the management command against a mocked retrieval gateway."""

    def _fake_retrieve(self, question, top_k, min_score, scope, graph_rag_enabled):
        """Fake retriever: always returns the DelayedAndCancelled example as top chunk."""
        chunk = _minimal_chunk("examples/DelayedAndCancelledJourneysWithEvents.xml", score=0.9)
        trace = {
            "graphExpansionSource": "memory" if graph_rag_enabled else "none",
            "graphCandidatesAdded": 1 if graph_rag_enabled else 0,
        }
        return [chunk], trace

    def test_command_produces_report_with_hit(self):
        questions_payload = {
            "questions": [
                {
                    "id": "q001",
                    "question": "Show me a delayed journey example.",
                    "intent": "example",
                    "tags": ["opra", "delay"],
                    "expected_source_patterns": ["DelayedAndCancelled"],
                    "min_hits": 1,
                    "top_k_threshold": 10,
                }
            ]
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "questions.yaml"
            output_path = tmp / "report.json"
            input_path.write_text(yaml.safe_dump(questions_payload), encoding="utf-8")

            with patch(
                "helpdesk.management.commands.run_retrieval_benchmark.retrieve_chunks_with_trace",
                side_effect=self._fake_retrieve,
            ):
                from django.core.management import call_command

                call_command(
                    "run_retrieval_benchmark",
                    input=str(input_path),
                    output=str(output_path),
                    quiet=True,
                    top_k=10,
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["total_questions"], 1)
        self.assertIn("aggregate", report)
        self.assertIn("baseline", report["aggregate"])
        self.assertIn("graph", report["aggregate"])

        q_result = report["questions"][0]
        self.assertTrue(q_result["baseline"]["hit_at_10"])
        self.assertTrue(q_result["graph"]["hit_at_10"])
        self.assertAlmostEqual(q_result["baseline"]["mrr_at_10"], 1.0)

    def test_command_produces_delta_when_both_modes_run(self):
        questions_payload = {
            "questions": [
                {
                    "id": "q001",
                    "question": "How are delays tracked in OpRa?",
                    "intent": "explanation",
                    "tags": ["opra"],
                    "expected_source_patterns": ["DelayedAndCancelled"],
                    "min_hits": 1,
                    "top_k_threshold": 10,
                }
            ]
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "questions.yaml"
            output_path = tmp / "report.json"
            input_path.write_text(yaml.safe_dump(questions_payload), encoding="utf-8")

            with patch(
                "helpdesk.management.commands.run_retrieval_benchmark.retrieve_chunks_with_trace",
                side_effect=self._fake_retrieve,
            ):
                from django.core.management import call_command

                call_command(
                    "run_retrieval_benchmark",
                    input=str(input_path),
                    output=str(output_path),
                    quiet=True,
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("delta", report["aggregate"])
        delta = report["aggregate"]["delta"]
        self.assertIn("hit_at_10_delta", delta)
        self.assertIn("mrr_at_10_delta", delta)
        self.assertIn("latency_overhead_ms", delta)

    def test_command_tag_filter(self):
        questions_payload = {
            "questions": [
                {
                    "id": "q001",
                    "question": "OpRa delay question.",
                    "intent": "explanation",
                    "tags": ["opra", "delay"],
                    "expected_source_patterns": ["DelayedAndCancelled"],
                    "min_hits": 1,
                    "top_k_threshold": 5,
                },
                {
                    "id": "q002",
                    "question": "NeTEx line question.",
                    "intent": "explanation",
                    "tags": ["netex", "line"],
                    "expected_source_patterns": ["netex_line"],
                    "min_hits": 1,
                    "top_k_threshold": 5,
                },
            ]
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "questions.yaml"
            output_path = tmp / "report.json"
            input_path.write_text(yaml.safe_dump(questions_payload), encoding="utf-8")

            with patch(
                "helpdesk.management.commands.run_retrieval_benchmark.retrieve_chunks_with_trace",
                side_effect=self._fake_retrieve,
            ):
                from django.core.management import call_command

                call_command(
                    "run_retrieval_benchmark",
                    input=str(input_path),
                    output=str(output_path),
                    quiet=True,
                    tags=["opra"],
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["total_questions"], 1)
        self.assertEqual(report["questions"][0]["id"], "q001")

    def test_command_abstention_questions_always_hit(self):
        questions_payload = {
            "questions": [
                {
                    "id": "q091",
                    "question": "Is SIRI compatible with OpRa?",
                    "intent": "abstention",
                    "tags": ["siri", "opra"],
                    "expected_source_patterns": [],
                    "min_hits": 0,
                    "top_k_threshold": 10,
                }
            ]
        }

        def _empty_retrieve(question, top_k, min_score, scope, graph_rag_enabled):
            return [], {"graphExpansionSource": "none", "graphCandidatesAdded": 0}

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "questions.yaml"
            output_path = tmp / "report.json"
            input_path.write_text(yaml.safe_dump(questions_payload), encoding="utf-8")

            with patch(
                "helpdesk.management.commands.run_retrieval_benchmark.retrieve_chunks_with_trace",
                side_effect=_empty_retrieve,
            ):
                from django.core.management import call_command

                call_command(
                    "run_retrieval_benchmark",
                    input=str(input_path),
                    output=str(output_path),
                    quiet=True,
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))

        # Abstention: min_hits=0 so hit is always True
        self.assertTrue(report["questions"][0]["baseline"]["hit_at_10"])
        self.assertTrue(report["questions"][0]["graph"]["hit_at_10"])
