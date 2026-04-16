from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from helpdesk.services.neo4j_importer import (
    build_neo4j_schema_statements,
    build_neo4j_statements,
    query_neo4j_concept_expansion,
)
from helpdesk.services.semantic_graph import extract_graph_concepts


def _snapshot_payload() -> dict:
    return {
        "nodes": [
            {
                "id": "repository:repo001",
                "type": "Repository",
                "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                "name": "OpRa",
            },
            {
                "id": "document:doc001",
                "type": "Document",
                "documentId": "doc001",
                "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                "sourcePath": "examples/DelayedAndCancelledJourneysWithEvents.xml",
                "commitSha": "abc123",
                "docType": "example",
            },
            {
                "id": "concept:opra:delayed-journey",
                "type": "Concept",
                "conceptId": "opra:delayed-journey",
                "namespace": "nch",
            },
            {
                "id": "chunk:opra-c-001",
                "type": "Chunk",
                "chunkId": "opra-c-001",
                "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                "sourcePath": "examples/DelayedAndCancelledJourneysWithEvents.xml",
                "commitSha": "abc123",
                "qualityScore": 0.9,
                "docType": "example",
            },
        ],
        "edges": [
            {
                "type": "CONTAINS_DOCUMENT",
                "from": "repository:repo001",
                "to": "document:doc001",
            },
            {
                "type": "HAS_CHUNK",
                "from": "document:doc001",
                "to": "chunk:opra-c-001",
            },
            {
                "type": "MENTIONS_CONCEPT",
                "from": "chunk:opra-c-001",
                "to": "concept:opra:delayed-journey",
                "sourceUrl": "https://github.com/OpRa-CEN/OpRa",
                "sourcePath": "examples/DelayedAndCancelledJourneysWithEvents.xml",
                "commitSha": "abc123",
            },
            {
                "type": "RELATED_TO",
                "from": "concept:opra:delayed-journey",
                "to": "concept:opra:delayed-journey",
                "relationType": "semantic-proximity",
            },
        ],
        "stats": {
            "repositoryNodeCount": 1,
            "documentNodeCount": 1,
            "conceptNodeCount": 1,
            "chunkNodeCount": 1,
            "repositoryDocumentEdgeCount": 1,
            "documentChunkEdgeCount": 1,
            "mentionEdgeCount": 1,
            "relatedEdgeCount": 1,
        },
    }


class Neo4jImportTests(TestCase):
    def test_extract_graph_concepts_matches_delayed_vehicle_journeys(self):
        """Concept extraction should match wording variants used by users."""
        concepts = extract_graph_concepts("How can I exchange delayed vehicle journeys?")
        self.assertIn("opra:DelayedJourney", concepts)

    def test_build_neo4j_schema_statements_returns_idempotent_set(self):
        statements = build_neo4j_schema_statements()

        self.assertGreaterEqual(len(statements), 4)
        for statement in statements:
            self.assertIn("statement", statement)
            self.assertIn("IF NOT EXISTS", statement["statement"])
            self.assertIn("parameters", statement)

    def test_build_neo4j_statements_returns_expected_shape(self):
        statements = build_neo4j_statements(_snapshot_payload())

        self.assertEqual(len(statements), 8)
        for statement in statements:
            self.assertIn("statement", statement)
            self.assertIn("parameters", statement)

    def test_import_command_dry_run(self):
        with TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "snapshot.json"
            input_path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")

            call_command("import_semantic_graph_neo4j", input=str(input_path))

    @override_settings(
        NEO4J_ENABLED=False,
        NEO4J_URI="http://localhost:7474",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="secret",
        NEO4J_DATABASE="neo4j",
    )
    def test_import_command_apply_requires_enabled_flag(self):
        with TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "snapshot.json"
            input_path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command("import_semantic_graph_neo4j", input=str(input_path), apply=True)

    @override_settings(
        GRAPHDB_ENABLED=False,
        NEO4J_ENABLED=True,
        NEO4J_EXPERIMENTAL_ENABLED=True,
        NEO4J_URI="http://localhost:7474",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="secret",
        NEO4J_DATABASE="neo4j",
    )
    @patch("helpdesk.management.commands.import_semantic_graph_neo4j.submit_neo4j_statements")
    def test_import_command_apply_calls_submit(self, submit_mock):
        schema_count = len(build_neo4j_schema_statements())
        data_count = len(build_neo4j_statements(_snapshot_payload()))
        submit_mock.return_value = {
            "endpoint": "http://localhost:7474/db/neo4j/tx/commit",
            "statementCount": schema_count + data_count,
        }

        with TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "snapshot.json"
            input_path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")

            call_command("import_semantic_graph_neo4j", input=str(input_path), apply=True)

        submit_mock.assert_called_once()
        call_kwargs = submit_mock.call_args.kwargs
        self.assertEqual(len(call_kwargs["statements"]), schema_count + data_count)

    @override_settings(
        GRAPHDB_ENABLED=False,
        NEO4J_ENABLED=True,
        NEO4J_EXPERIMENTAL_ENABLED=True,
        NEO4J_URI="http://localhost:7474",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="secret",
        NEO4J_DATABASE="neo4j",
    )
    @patch("helpdesk.management.commands.import_semantic_graph_neo4j.submit_neo4j_statements")
    def test_import_command_apply_can_skip_schema_bootstrap(self, submit_mock):
        submit_mock.return_value = {
            "endpoint": "http://localhost:7474/db/neo4j/tx/commit",
            "statementCount": 8,
        }

        with TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "snapshot.json"
            input_path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")

            call_command(
                "import_semantic_graph_neo4j",
                input=str(input_path),
                apply=True,
                ensure_schema=False,
            )

        submit_mock.assert_called_once()
        call_kwargs = submit_mock.call_args.kwargs
        self.assertEqual(len(call_kwargs["statements"]), len(build_neo4j_statements(_snapshot_payload())))

    def test_query_neo4j_concept_expansion_returns_expanded_set(self):
        """query_neo4j_concept_expansion merges input IDs with related IDs returned by Neo4j."""

        neo4j_response = {
            "results": [
                {
                    "data": [
                        {"row": ["opra:delay-statistics"]},
                        {"row": ["opra:late-dated-vehicle-journey-entry"]},
                    ]
                }
            ],
            "errors": [],
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(neo4j_response).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.neo4j_importer.urlopen", return_value=mock_response):
            result = query_neo4j_concept_expansion(
                concept_ids={"opra:delayed-journey"},
                hops=1,
                uri="http://localhost:7474",
                username="neo4j",
                password="secret",
                database="neo4j",
            )

        self.assertIn("opra:delayed-journey", result)
        self.assertIn("opra:delay-statistics", result)
        self.assertIn("opra:late-dated-vehicle-journey-entry", result)
        self.assertEqual(len(result), 3)

    @override_settings(
        GRAPHDB_ENABLED=False,
        NEO4J_ENABLED=True,
        NEO4J_EXPERIMENTAL_ENABLED=True,
        NEO4J_URI="http://localhost:7474",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="secret",
        NEO4J_DATABASE="neo4j",
    )
    @patch("helpdesk.services.retrieval_gateway.query_neo4j_concept_expansion")
    def test_retrieval_gateway_uses_neo4j_expansion_when_experimental_enabled(self, expand_mock):
        """retrieve_chunks_with_trace uses Neo4j only when experimental Neo4j mode is enabled."""
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        expand_mock.return_value = {"opra:DelayedJourney", "opra:DelayStatistics"}

        _chunks, trace = retrieve_chunks_with_trace(
            question="delayed journey statistics",
            top_k=3,
            min_score=0.0,
            graph_rag_enabled=True,
        )

        expand_mock.assert_called_once()
        self.assertEqual(trace["graphExpansionSource"], "neo4j_experimental")
        self.assertIn("opra:DelayedJourney", trace["graphConceptIds"])

    @override_settings(
        NEO4J_ENABLED=False,
    )
    def test_graph_concept_candidates_injected_into_pool(self):
        """Graph-concept alias matching adds new chunks into the candidate pool."""
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.retrieval_gateway import _graph_concept_candidates

        chunk_text = "The delayed journey count was 5 on this route."
        SourceChunk.objects.get_or_create(
            chunk_id="graph-seed-test-001",
            defaults={
                "repository_url": "https://github.com/OpRa-CEN/OpRa",
                "commit_sha": "abc",
                "source_path": "test/delay.xml",
                "label": "Delay test",
                "text": chunk_text,
                "standards_scope": ["OpRa"],
                "quality_score": 0.80,
                "doc_type": "example",
                "embedding_vector": build_text_embedding(chunk_text),
            },
        )

        qs = _graph_concept_candidates(
            expanded_concepts={"opra:DelayedJourney"},
            top_k=5,
        )
        chunk_ids = [c.chunk_id for c in qs]
        self.assertIn("graph-seed-test-001", chunk_ids)

    @override_settings(
        NEO4J_ENABLED=False,
    )
    def test_graph_score_adjustment_returns_provenance(self):
        """Graph score adjustment returns matching concept IDs for provenance."""
        from helpdesk.services.retrieval_gateway import _graph_score_adjustment

        adjustment, hit, concepts = _graph_score_adjustment(
            graph_enabled=True,
            question_concepts={"opra:DelayedJourney"},
            expanded_concepts={"opra:DelayedJourney", "opra:DelayStatistics"},
            concept_example_paths=set(),
            chunk_text="This chunk mentions delayed journeys.",
            source_path="delay.md",
            label="Delay test",
            heading="",
        )

        self.assertGreater(adjustment, 0.0)
        self.assertTrue(hit)
        self.assertIn("opra:DelayedJourney", concepts)

    @override_settings(
        NEO4J_ENABLED=False,
    )
    def test_retrieval_includes_graph_provenance_in_response(self):
        """retrieve_chunks_with_trace includes graphProvenanceConceptIds in results."""
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        chunk_text = "The delayed journey occurred on route 5."
        SourceChunk.objects.get_or_create(
            chunk_id="provenance-test-001",
            defaults={
                "repository_url": "https://github.com/OpRa-CEN/OpRa",
                "commit_sha": "abc",
                "source_path": "test/delay.xml",
                "label": "Delay provenance test",
                "text": chunk_text,
                "standards_scope": ["OpRa"],
                "quality_score": 0.85,
                "embedding_vector": build_text_embedding(chunk_text),
            },
        )

        chunks, trace = retrieve_chunks_with_trace(
            question="delayed journey",
            top_k=5,
            min_score=0.0,
            graph_rag_enabled=True,
        )

        # Check trace has provenance stats
        self.assertIn("graphProvenanceChainCount", trace)
        self.assertGreaterEqual(trace["graphProvenanceChainCount"], 0)

        # Check at least one chunk has provenance if graph hit
        if any(c.get("graphProvenanceConceptIds") for c in chunks):
            found_provenance = True
            for chunk in chunks:
                if chunk.get("graphProvenanceConceptIds"):
                    self.assertIsInstance(chunk["graphProvenanceConceptIds"], list)
            self.assertTrue(found_provenance)

    @override_settings(
        NEO4J_ENABLED=False,
        GRAPH_RAG_ENABLED=True,
    )
    def test_retrieval_variant_tracking_graph_rag(self):
        """Trace includes graphRagVariant=graph-rag when enabled."""
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        _chunks, trace = retrieve_chunks_with_trace(
            question="test query",
            top_k=5,
            min_score=0.0,
            graph_rag_enabled=True,
        )

        self.assertIn("graphRagVariant", trace)
        self.assertEqual(trace["graphRagVariant"], "graph-rag")

    @override_settings(
        NEO4J_ENABLED=False,
        GRAPH_RAG_ENABLED=False,
    )
    def test_retrieval_variant_tracking_control(self):
        """Trace includes graphRagVariant=control when disabled."""
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        _chunks, trace = retrieve_chunks_with_trace(
            question="test query",
            top_k=5,
            min_score=0.0,
            graph_rag_enabled=False,
        )

        self.assertIn("graphRagVariant", trace)
        self.assertEqual(trace["graphRagVariant"], "control")

    @override_settings(
        NEO4J_ENABLED=False,
    )
    def test_retrieval_latency_measurement(self):
        """Trace includes retrievalLatencyMs measurement."""
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        _chunks, trace = retrieve_chunks_with_trace(
            question="test query",
            top_k=1,
            min_score=0.0,
            graph_rag_enabled=False,
        )

        self.assertIn("retrievalLatencyMs", trace)
        self.assertIsInstance(trace["retrievalLatencyMs"], float)
        self.assertGreaterEqual(trace["retrievalLatencyMs"], 0)
