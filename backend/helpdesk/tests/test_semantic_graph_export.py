from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from helpdesk.models import SourceChunk
from helpdesk.services.embeddings import build_text_embedding


class SemanticGraphExportTests(TestCase):
    def test_export_semantic_graph_writes_nodes_and_edges(self):
        SourceChunk.objects.create(
            repository_url="https://github.com/OpRa-CEN/OpRa",
            commit_sha="abc123",
            source_path="examples/DelayedAndCancelledJourneysWithEvents.xml",
            chunk_id="opra-c-001",
            label="DelayedAndCancelledJourneysWithEvents.xml",
            text="Delayed journey and DelayStatistics with LateDatedVehicleJourneyEntry",
            standards_scope=["OpRa"],
            quality_score=0.92,
            doc_type="example",
            embedding_vector=build_text_embedding("Delayed journey and DelayStatistics"),
        )

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "semantic-graph.json"
            call_command("export_semantic_graph", output=str(output_path))

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("nodes", payload)
        self.assertIn("edges", payload)
        self.assertGreaterEqual(payload["stats"]["repositoryNodeCount"], 1)
        self.assertGreaterEqual(payload["stats"]["documentNodeCount"], 1)
        self.assertGreaterEqual(payload["stats"]["conceptNodeCount"], 1)
        self.assertGreaterEqual(payload["stats"]["chunkNodeCount"], 1)
        self.assertGreaterEqual(payload["stats"]["repositoryDocumentEdgeCount"], 1)
        self.assertGreaterEqual(payload["stats"]["documentChunkEdgeCount"], 1)
        self.assertGreaterEqual(payload["stats"]["mentionEdgeCount"], 1)
        self.assertEqual(payload["meta"]["repositoryUrl"], "all")

    def test_export_semantic_graph_respects_repo_filter(self):
        SourceChunk.objects.create(
            repository_url="https://github.com/OpRa-CEN/OpRa",
            commit_sha="abc123",
            source_path="examples/DelayedAndCancelledJourneysWithEvents.xml",
            chunk_id="opra-c-001",
            label="DelayedAndCancelledJourneysWithEvents.xml",
            text="Delayed journey and delay statistics payload",
            standards_scope=["OpRa"],
            quality_score=0.88,
            doc_type="example",
            embedding_vector=build_text_embedding("Delayed journey and delay statistics payload"),
        )
        SourceChunk.objects.create(
            repository_url="https://github.com/NeTEx-CEN/NeTEx",
            commit_sha="def456",
            source_path="docs/guide.md",
            chunk_id="netex-c-001",
            label="guide.md",
            text="General guide without graph semantic aliases",
            standards_scope=["NeTEx"],
            quality_score=0.81,
            doc_type="guide",
            embedding_vector=build_text_embedding("General guide without graph semantic aliases"),
        )

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "semantic-graph-opra.json"
            call_command(
                "export_semantic_graph",
                output=str(output_path),
                repo_url="https://github.com/OpRa-CEN/OpRa",
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["meta"]["repositoryUrl"], "https://github.com/OpRa-CEN/OpRa")
        self.assertEqual(payload["meta"]["chunkCountScanned"], 1)

    def test_export_semantic_graph_rejects_invalid_quality_bounds(self):
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "semantic-graph.json"
            with self.assertRaises(CommandError):
                call_command(
                    "export_semantic_graph",
                    output=str(output_path),
                    min_quality=1.5,
                )
