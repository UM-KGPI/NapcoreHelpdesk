from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from helpdesk.services.graphdb_client import (
    _normalize_repository_endpoint,
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
