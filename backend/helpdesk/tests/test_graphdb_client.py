from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from helpdesk.services.graphdb_client import (
    _normalize_repository_endpoint,
    build_graph_scope_for_standards,
    load_default_ontology_graphs,
    query_graphdb_concept_expansion,
)


class GraphDbClientTests(TestCase):
    def test_normalize_repository_endpoint_appends_repo_when_needed(self):
        endpoint = _normalize_repository_endpoint(
            endpoint="http://localhost:7200",
            repository="napcore",
        )
        self.assertEqual(endpoint, "http://localhost:7200/repositories/napcore")

    def test_normalize_repository_endpoint_keeps_existing_repo_path(self):
        endpoint = _normalize_repository_endpoint(
            endpoint="http://localhost:7200/repositories/napcore",
            repository="ignored",
        )
        self.assertEqual(endpoint, "http://localhost:7200/repositories/napcore")

    def test_query_graphdb_concept_expansion_returns_related_and_seed_concepts(self):
        graphdb_response = {
            "head": {"vars": ["related"]},
            "results": {
                "bindings": [
                    {
                        "related": {
                            "type": "uri",
                            "value": "https://napcore.eu/ontology/opra#delay-statistics",
                        }
                    },
                    {
                        "related": {
                            "type": "uri",
                            "value": "https://napcore.eu/ontology/netex#VehicleJourney",
                        }
                    },
                ]
            },
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphdb_response).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.graphdb_client.urlopen", return_value=mock_response):
            result = query_graphdb_concept_expansion(
                concept_ids={"opra:delayed-journey"},
                hops=1,
                endpoint="http://localhost:7200",
                repository="napcore",
            )

        self.assertIn("opra:delayed-journey", result)
        self.assertIn("opra:delay-statistics", result)
        self.assertIn("netex:VehicleJourney", result)

    def test_query_graphdb_concept_expansion_uses_named_graph_scope_when_provided(self):
        graphdb_response = {
            "head": {"vars": ["related"]},
            "results": {"bindings": []},
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphdb_response).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.graphdb_client.urlopen", return_value=mock_response) as urlopen_mock:
            query_graphdb_concept_expansion(
                concept_ids={"netex:Service"},
                hops=1,
                endpoint="http://localhost:7200",
                repository="napcore",
                graph_uris=["https://napcore.eu/graph/standards/netex"],
            )

        request = urlopen_mock.call_args[0][0]
        sent_query = request.data.decode("utf-8")
        self.assertIn("VALUES ?g", sent_query)
        self.assertIn("GRAPH ?g", sent_query)

    def test_build_graph_scope_for_standards_adds_artifact_rules_only_when_requested(self):
        scoped_without_rules = build_graph_scope_for_standards(
            {"NeTEx", "SIRI"},
            include_artifact_rules=False,
        )
        self.assertIn("https://napcore.eu/graph/standards/netex", scoped_without_rules)
        self.assertIn("https://napcore.eu/graph/alignments/siri", scoped_without_rules)
        self.assertFalse(any("/artifact-rules/" in uri for uri in scoped_without_rules))

        scoped_with_rules = build_graph_scope_for_standards(
            {"NeTEx"},
            include_artifact_rules=True,
        )
        self.assertIn("https://napcore.eu/graph/artifact-rules/netex/v1.0", scoped_with_rules)

    def test_load_default_ontology_graphs_excludes_artifact_rules_by_default(self):
        with (
            patch("helpdesk.services.graphdb_client.upload_named_graph_turtle") as upload_mock,
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=""),
        ):
            upload_mock.side_effect = lambda **kwargs: {
                "graphUri": kwargs["graph_uri"],
                "statementEndpoint": "http://localhost:7200/repositories/napcore/statements",
                "replaced": kwargs["replace"],
            }

            results = load_default_ontology_graphs(
                endpoint="http://localhost:7200",
                repository="napcore",
                replace=False,
            )

        graph_uris = {item["graphUri"] for item in results}
        self.assertEqual(len(results), 11)
        self.assertFalse(any("/artifact-rules/" in uri for uri in graph_uris))

    def test_load_default_ontology_graphs_includes_selected_artifact_rules(self):
        with (
            patch("helpdesk.services.graphdb_client.upload_named_graph_turtle") as upload_mock,
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=""),
        ):
            upload_mock.side_effect = lambda **kwargs: {
                "graphUri": kwargs["graph_uri"],
                "statementEndpoint": "http://localhost:7200/repositories/napcore/statements",
                "replaced": kwargs["replace"],
            }

            results = load_default_ontology_graphs(
                endpoint="http://localhost:7200",
                repository="napcore",
                include_artifact_rules=True,
                artifact_rule_standards={"netex"},
                replace=False,
            )

        graph_uris = {item["graphUri"] for item in results}
        self.assertIn("https://napcore.eu/graph/artifact-rules/netex/v1.0", graph_uris)
        self.assertFalse(any("/artifact-rules/opra/" in uri for uri in graph_uris))

    def test_load_default_ontology_graphs_rejects_unknown_artifact_rule_standard(self):
        with self.assertRaisesMessage(ValueError, "Unsupported artifact-rule standards"):
            load_default_ontology_graphs(
                endpoint="http://localhost:7200",
                repository="napcore",
                include_artifact_rules=True,
                artifact_rule_standards={"unknown-standard"},
                replace=False,
            )
