from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from helpdesk.services.neo4j_importer import build_neo4j_schema_statements, build_neo4j_statements


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
        NEO4J_ENABLED=True,
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
        NEO4J_ENABLED=True,
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
