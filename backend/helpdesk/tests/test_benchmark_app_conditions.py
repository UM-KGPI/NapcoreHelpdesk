from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml
from django.core.management import call_command
from django.test import SimpleTestCase

from helpdesk.services import semantic_graph
from helpdesk.tests.benchmark_fixture import COMMAND, GOLDEN_DIR, QUESTIONS, chunk, fake_retrieve, run_default_mode


def _run(questions: dict, retrieve, **options) -> dict:
    """Run the command with `retrieve` in place of the gateway; return the JSON report."""
    with TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / "questions.yaml"
        output_path = Path(tmp_dir) / "report.json"
        input_path.write_text(yaml.safe_dump(questions), encoding="utf-8")
        with patch(f"{COMMAND}.retrieve_chunks_with_trace", side_effect=retrieve):
            call_command(
                "run_retrieval_benchmark",
                input=str(input_path),
                output=str(output_path),
                quiet=True,
                stdout=options.pop("stdout", None) or open(os.devnull, "w"),
                **options,
            )
        return json.loads(output_path.read_text(encoding="utf-8"))


class CurrentBehaviourTests(SimpleTestCase):
    """What the benchmark command and the ontology switch do today; these hold in every mode and every
    environment, and were written against the code before the app-conditions mode existed."""

    def test_k_is_the_larger_of_top_k_and_the_questions_threshold_and_min_score_is_zero(self):
        seen = []

        def recording(question, top_k, min_score, scope, graph_rag_enabled, **kwargs):
            seen.append((question, top_k, min_score, kwargs.get("min_results", 0)))
            return fake_retrieve(question, top_k, min_score, scope, graph_rag_enabled)

        _run(QUESTIONS, recording, top_k=5, baseline_only=True)
        # thresholds are 10, 20, 10: the floor 5 loses to each of them
        self.assertEqual([k for _, k, _, _ in seen], [10, 20, 10])
        self.assertEqual({s for _, _, s, _ in seen}, {0.0})
        self.assertEqual({m for _, _, _, m in seen}, {0})

        seen.clear()
        _run(QUESTIONS, recording, top_k=25, baseline_only=True)
        self.assertEqual([k for _, k, _, _ in seen], [25, 25, 25])

    def test_report_carries_exactly_hit_5_10_20_and_mrr_10_20(self):
        report = _run(QUESTIONS, fake_retrieve, top_k=5)
        self.assertEqual(
            set(report["aggregate"]["baseline"]),
            {"hit_at_5", "hit_at_10", "hit_at_20", "mrr_at_10", "mrr_at_20", "mean_latency_ms"},
        )

    def test_skip_switch_returns_an_empty_ontology_whatever_graphdb_enabled_says(self):
        with patch.object(semantic_graph, "SKIP_GRAPHDB_IMPORT", True), patch.dict(
            os.environ, {"GRAPHDB_ENABLED": "True", "GRAPHDB_SPARQL_ENDPOINT": "http://unreachable.invalid/x"}
        ), patch("urllib.request.urlopen") as opener:
            ontology = semantic_graph._load_ontology()
        self.assertEqual(ontology, {"namespaces": {}, "concepts": {}, "relationships": []})
        opener.assert_not_called()

    def test_graphdb_disabled_also_returns_an_empty_ontology(self):
        with patch.object(semantic_graph, "SKIP_GRAPHDB_IMPORT", False), patch.dict(
            os.environ, {"GRAPHDB_ENABLED": "False"}
        ):
            ontology = semantic_graph._load_ontology()
        self.assertEqual(ontology["concepts"], {})

    def test_nothing_fills_the_table_afterwards_when_the_switch_was_set_at_import(self):
        # With the switch set at import the read time is None and the re-read returns at once.
        with patch.object(semantic_graph, "_ONTOLOGY_READ_AT", None):
            self.assertFalse(semantic_graph.reload_ontology_if_updated())


def _strip_new_lines(text: str) -> str:
    """The output of the default mode without the lines this change added (all start with a fixed prefix)."""
    return "".join(
        line for line in text.splitlines(keepends=True) if not line.startswith(("BENCH-CONDITIONS:", "BENCH-WARNING:"))
    )


def _strip_new_report_key(text: str) -> str:
    report = json.loads(text)
    report.pop("conditions")
    return json.dumps(report, indent=2)


class DefaultModeUnchangedTests(SimpleTestCase):
    """The default mode's output for a fixed mocked input is what it was before the app-conditions mode
    (golden/ was recorded from the code before the change); the only additions are the prefixed lines and
    the report's "conditions" key."""

    def _check(self, name, **options):
        stdout, report = run_default_mode(**options)
        golden_stdout = (GOLDEN_DIR / f"benchmark_{name}.stdout.txt").read_text(encoding="utf-8")
        golden_report = (GOLDEN_DIR / f"benchmark_{name}.report.json").read_text(encoding="utf-8")
        self.assertEqual(_strip_new_lines(stdout), golden_stdout)
        # the golden files end with the newline the pre-commit hook adds; the report itself has none
        self.assertEqual(_strip_new_report_key(report) + "\n", golden_report)

    def test_verbose_run(self):
        self._check("default_verbose")

    def test_quiet_run_with_top_k_below_the_thresholds(self):
        self._check("default_quiet", quiet=True, top_k=5)


APP_QUESTIONS = {
    "questions": [
        {
            "id": "a001",
            "question": "hit at rank 6",
            "expected_source_patterns": ["wanted"],
            "min_hits": 1,
            "top_k_threshold": 20,
        },
        {
            "id": "a002",
            "question": "hit at rank 7",
            "expected_source_patterns": ["wanted"],
            "min_hits": 1,
            "top_k_threshold": 20,
        },
        {
            "id": "a003",
            "question": "short list",
            "expected_source_patterns": ["wanted"],
            "min_hits": 1,
            "top_k_threshold": 10,
        },
        {
            "id": "a004",
            "question": "nothing",
            "expected_source_patterns": ["wanted"],
            "min_hits": 1,
            "top_k_threshold": 10,
        },
    ]
}


def _filler(n, wanted_at=None, total=None):
    paths = [f"x/f{i}.xml" for i in range(total or n)]
    if wanted_at is not None:
        paths[wanted_at - 1] = "x/wanted.xml"
    return [chunk(p) for p in paths]


def _app_retrieve(question, top_k, min_score, scope, graph_rag_enabled, min_results=0, **_):
    """Returns more than top_k passages for the first two questions (a leaky retriever), to show that only
    the first k count."""
    lists = {
        "hit at rank 6": _filler(9, wanted_at=6),
        "hit at rank 7": _filler(9, wanted_at=7),
        "short list": [chunk("x/a.xml"), chunk("x/wanted.xml"), chunk("x/b.xml")],
        "nothing": [],
    }
    return lists[question], {}


class AppConditionsTests(SimpleTestCase):
    def setUp(self):
        patcher = patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", {"netex:Line": {"line"}})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_uses_the_endpoints_k_min_score_and_min_results_for_every_question(self):
        from helpdesk.api import views
        from helpdesk.services import answer_retrieval_defaults as shared

        seen = []

        def recording(question, top_k, min_score, scope, graph_rag_enabled, **kwargs):
            seen.append((top_k, min_score, kwargs.get("min_results")))
            return _app_retrieve(question, top_k, min_score, scope, graph_rag_enabled)

        with self.settings(LLM_MAX_EVIDENCE_CHUNKS=4):
            report = _run(APP_QUESTIONS, recording, app_conditions=True)
            self.assertEqual(set(seen), {(6, 0.62, 4)})
            self.assertEqual(views._min_evidence_results(), 4)
        self.assertEqual(len(seen), 8)  # four questions, both modes
        self.assertEqual((shared.ANSWER_RETRIEVAL_TOP_K, shared.ANSWER_RETRIEVAL_MIN_SCORE), (6, 0.62))
        conditions = report["conditions"]
        self.assertEqual(conditions["fixed_k"], 6)
        self.assertIsNone(conditions["k_floor"])
        self.assertEqual((conditions["min_score"], conditions["min_results"]), (0.62, 4))

    def test_the_endpoint_reads_the_same_constants(self):
        import inspect

        from helpdesk.api import views

        source = inspect.getsource(views)
        for literal in ('"retrievalTopK", 6', '"retrievalMinScore", 0.62', '"maxCitations", 5'):
            self.assertNotIn(literal, source)
        self.assertEqual(source.count('"retrievalTopK", ANSWER_RETRIEVAL_TOP_K'), 2)
        self.assertEqual(source.count('"retrievalMinScore", ANSWER_RETRIEVAL_MIN_SCORE'), 2)

    def test_hit_and_mrr_are_computed_over_exactly_k_passages(self):
        report = _run(APP_QUESTIONS, _app_retrieve, app_conditions=True, graph_only=True)
        graph = report["aggregate"]["graph"]
        by_id = {q["id"]: q["graph"] for q in report["questions"]}
        self.assertTrue(by_id["a001"]["hit_at_6"])
        self.assertAlmostEqual(by_id["a001"]["mrr_at_6"], 1 / 6)
        self.assertFalse(by_id["a002"]["hit_at_6"])  # rank 7 is outside the six
        self.assertEqual(by_id["a002"]["mrr_at_6"], 0.0)
        self.assertEqual(by_id["a002"]["passages"], 6)  # nine returned, six counted
        self.assertTrue(by_id["a003"]["hit_at_6"])
        self.assertAlmostEqual(by_id["a003"]["mrr_at_6"], 0.5)
        self.assertEqual(graph["hit_count_at_6"], 2)
        self.assertAlmostEqual(graph["hit_at_6"], 0.5)
        self.assertAlmostEqual(graph["mrr_at_6"], round((1 / 6 + 0 + 0.5 + 0) / 4, 4), places=4)
        # hit@5 sits beside it: rank 6 is outside five, the short list's rank 2 is inside
        self.assertAlmostEqual(graph["hit_at_5"], 0.25)
        self.assertNotIn("hit_at_10", graph)
        self.assertNotIn("hit_at_20", graph)

    def test_counts_of_short_and_empty_lists(self):
        report = _run(APP_QUESTIONS, _app_retrieve, app_conditions=True, baseline_only=True)
        baseline = report["aggregate"]["baseline"]
        # a003 has 3 passages and a004 has none: both are short, one is empty
        self.assertEqual(baseline["questions_with_fewer_than_6_passages"], 2)
        self.assertEqual(baseline["questions_with_no_passages"], 1)

    def test_report_records_conditions_and_the_concept_count(self):
        report = _run(APP_QUESTIONS, _app_retrieve, app_conditions=True)
        conditions = report["conditions"]
        self.assertEqual(conditions["mode"], "app-conditions")
        self.assertEqual(conditions["ontology_concepts"], 1)
        self.assertFalse(conditions["ontology_empty"])
        self.assertEqual(conditions["scope_mode"], "none")
        self.assertEqual(conditions["warnings"], [])
        self.assertEqual(report["top_k"], 6)

    def test_scope_mode_is_recorded(self):
        report = _run(APP_QUESTIONS, _app_retrieve, app_conditions=True, scope=["NeTEx"])
        self.assertEqual(report["conditions"]["scope_mode"], "explicit")

    def test_top_k_and_gate_cannot_be_combined_with_the_mode(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            _run(APP_QUESTIONS, _app_retrieve, app_conditions=True, top_k=10)
        with TemporaryDirectory() as tmp_dir:
            gate = Path(tmp_dir) / "gate.json"
            gate.write_text(json.dumps({"aggregate": {}}), encoding="utf-8")
            with self.assertRaises(CommandError):
                _run(APP_QUESTIONS, _app_retrieve, app_conditions=True, gate_against=str(gate))


class EmptyOntologyTests(SimpleTestCase):
    def _empty(self, *, skip=True):
        return patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", {}), patch.object(
            semantic_graph, "SKIP_GRAPHDB_IMPORT", skip
        )

    def test_default_mode_warns_in_graph_mode_and_marks_the_report_but_still_runs(self):
        from io import StringIO

        out = StringIO()
        a, b = self._empty()
        with a, b:
            report = _run(QUESTIONS, fake_retrieve, stdout=out)
        text = out.getvalue()
        warning_lines = [ln for ln in text.splitlines() if ln.startswith("BENCH-WARNING:")]
        self.assertTrue(warning_lines)  # at the start and again under the summary
        self.assertIn("graph mode ran without ontology concepts", warning_lines[0])
        self.assertIn("NAPCORE_SKIP_GRAPHDB_IMPORT", warning_lines[0])
        self.assertIn("ontology_concepts=0", text)
        self.assertEqual(report["conditions"]["ontology_concepts"], 0)
        self.assertTrue(report["conditions"]["ontology_empty"])
        self.assertEqual(len(report["conditions"]["warnings"]), 1)
        self.assertEqual(report["conditions"]["mode"], "benchmark")
        self.assertIn("graph", report["aggregate"])

    def test_the_reason_names_graphdb_disabled_when_the_switch_is_not_set(self):
        from io import StringIO

        out = StringIO()
        a, b = self._empty(skip=False)
        with a, b, patch.dict(os.environ, {"GRAPHDB_ENABLED": "False"}):
            _run(QUESTIONS, fake_retrieve, stdout=out)
        self.assertIn("GRAPHDB_ENABLED is off", out.getvalue())

    def test_baseline_only_does_not_warn(self):
        from io import StringIO

        out = StringIO()
        a, b = self._empty()
        with a, b:
            report = _run(QUESTIONS, fake_retrieve, stdout=out, baseline_only=True)
        self.assertNotIn("BENCH-WARNING:", out.getvalue())
        self.assertEqual(report["conditions"]["warnings"], [])
        self.assertTrue(report["conditions"]["ontology_empty"])

    def test_app_conditions_refuses_an_empty_ontology(self):
        from django.core.management.base import CommandError

        calls = []

        def recording(*args, **kwargs):
            calls.append(1)
            return _app_retrieve(*args, **kwargs)

        a, b = self._empty()
        with a, b, self.assertRaises(CommandError) as raised:
            _run(APP_QUESTIONS, recording, app_conditions=True)
        self.assertIn("BENCH-WARNING:", str(raised.exception))
        self.assertEqual(calls, [])  # refused before any retrieval

    def test_app_conditions_runs_with_the_explicit_acknowledgement_and_says_so(self):
        a, b = self._empty()
        with a, b:
            report = _run(
                APP_QUESTIONS,
                _app_retrieve,
                app_conditions=True,
                acknowledge_empty_ontology_is_not_the_app=True,
            )
        conditions = report["conditions"]
        self.assertTrue(conditions["empty_ontology_acknowledged"])
        self.assertTrue(conditions["ontology_empty"])
        self.assertEqual(len(conditions["warnings"]), 1)

    def test_baseline_only_app_conditions_needs_no_acknowledgement(self):
        a, b = self._empty()
        with a, b:
            report = _run(APP_QUESTIONS, _app_retrieve, app_conditions=True, baseline_only=True)
        self.assertIn("baseline", report["aggregate"])

    def test_acknowledgement_alone_is_an_error(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            _run(QUESTIONS, fake_retrieve, acknowledge_empty_ontology_is_not_the_app=True)
