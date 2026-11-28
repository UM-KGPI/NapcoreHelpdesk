"""A fixed mocked input for run_retrieval_benchmark, shared by the benchmark tests and used to record the
golden output of the default mode (golden/benchmark_default_*)."""
from __future__ import annotations

import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import yaml
from django.core.management import call_command

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
COMMAND = "helpdesk.management.commands.run_retrieval_benchmark"

QUESTIONS = {
    "questions": [
        {
            "id": "f001",
            "question": "first question",
            "intent": "explanation",
            "tags": ["a"],
            "expected_source_patterns": ["wanted"],
            "min_hits": 1,
            "top_k_threshold": 10,
        },
        {
            "id": "f002",
            "question": "second question",
            "intent": "example",
            "tags": ["b"],
            "expected_source_patterns": ["wanted", "other"],
            "min_hits": 2,
            "top_k_threshold": 20,
        },
        {
            "id": "f003",
            "question": "third question",
            "intent": "abstention",
            "tags": ["c"],
            "expected_source_patterns": [],
            "min_hits": 0,
            "top_k_threshold": 10,
        },
    ]
}


def chunk(path: str) -> dict:
    return {"sourcePath": path, "score": 0.9}


def fake_retrieve(question, top_k, min_score, scope, graph_rag_enabled, **_ignored):
    """Deterministic: ranks depend on the question and the mode, never on top_k (the lists are long)."""
    if question == "first question":
        paths = ["x/a.xml", "x/wanted.xml"] if not graph_rag_enabled else ["x/wanted.xml", "x/a.xml"]
    elif question == "second question":
        paths = [f"x/f{i}.xml" for i in range(7)] + ["x/wanted.xml", "x/other.xml"]
    else:
        paths = []
    chunks = [chunk(p) for p in paths]
    trace = {
        "graphExpansionSource": "memory" if graph_rag_enabled else "none",
        "graphCandidatesAdded": 2 if graph_rag_enabled else 0,
    }
    return chunks, trace


def run_default_mode(**options) -> tuple[str, str]:
    """Run the command on QUESTIONS with the fake retriever and a frozen clock; return (stdout, report text),
    with the temporary directory replaced by <TMP>."""
    out = io.StringIO()
    with TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        input_path = tmp / "questions.yaml"
        output_path = tmp / "report.json"
        input_path.write_text(yaml.safe_dump(QUESTIONS), encoding="utf-8")
        clock = MagicMock()
        clock.time.return_value = 100.0
        with patch(f"{COMMAND}.retrieve_chunks_with_trace", side_effect=fake_retrieve), patch(f"{COMMAND}.time", clock):
            call_command(
                "run_retrieval_benchmark",
                input=str(input_path),
                output=str(output_path),
                stdout=out,
                **options,
            )
        report = output_path.read_text(encoding="utf-8")
        resolved = str(tmp.resolve())
        text = out.getvalue()
    return (
        text.replace(resolved, "<TMP>").replace(tmp_dir, "<TMP>"),
        report.replace(resolved, "<TMP>").replace(tmp_dir, "<TMP>"),
    )
