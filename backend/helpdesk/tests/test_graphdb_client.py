from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from helpdesk.services.graphdb_client import (
    _normalize_repository_endpoint,
    build_graph_scope_for_standards,
    load_default_ontology_graphs,
    query_graphdb_concept_expansion,
    query_graphdb_concept_expansion_with_distance,
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

    def test_expansion_follows_subclass_downward_only(self):
        """Inverse subClassOf (find subclasses) is in the path; forward subClassOf
        (climb to superclasses such as netex:DataManagedObject) is not."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"results": {"bindings": []}}).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.graphdb_client.urlopen", return_value=mock_response) as urlopen_mock:
            query_graphdb_concept_expansion(
                concept_ids={"netex:Journey"},
                hops=1,
                endpoint="http://localhost:7200",
                repository="napcore",
            )

        sent_query = urlopen_mock.call_args[0][0].data.decode("utf-8")
        subclass = "<http://www.w3.org/2000/01/rdf-schema#subClassOf>"
        self.assertIn(f"^{subclass}", sent_query)
        self.assertEqual(sent_query.count(subclass), 1)

    def test_expansion_reports_hop_distance(self):
        def response(iris):
            mock = MagicMock()
            bindings = [{"related": {"type": "uri", "value": iri}} for iri in iris]
            mock.read.return_value = json.dumps({"results": {"bindings": bindings}}).encode("utf-8")
            mock.__enter__ = lambda self: self
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        hop1 = response(["https://netex.org.uk/netex/2.0#ServiceJourney"])
        hop2 = response(["https://netex.org.uk/netex/2.0#Line"])
        with patch("helpdesk.services.graphdb_client.urlopen", side_effect=[hop1, hop2]):
            distances = query_graphdb_concept_expansion_with_distance(
                concept_ids={"netex:Journey"},
                hops=2,
                endpoint="http://localhost:7200",
                repository="napcore",
            )

        self.assertEqual(distances, {"netex:Journey": 0, "netex:ServiceJourney": 1, "netex:Line": 2})

    def test_query_graphdb_concept_expansion_scoped_query_includes_cross_standard_pivot(self):
        """Regression test for the cross-graph pivot bug.

        A property path inside `GRAPH ?g { ?seed path ?related }` resolves
        entirely within one graph per solution, so it can never connect a
        seed in one standard's alignment graph to a sibling concept in a
        different standard's alignment graph, even when both are in
        `graph_uris`. The scoped query must include a second, explicit
        two-hop branch (seed -> Transmodel concept, then Transmodel concept
        <- sibling concepts) that is not constrained to a single graph
        binding for both hops, or cross-standard concepts are silently
        unreachable.
        """
        graphdb_response = {"head": {"vars": ["related"]}, "results": {"bindings": []}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphdb_response).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.graphdb_client.urlopen", return_value=mock_response) as urlopen_mock:
            query_graphdb_concept_expansion(
                concept_ids={"opra:CancelledDatedVehicleJourneyCount"},
                hops=1,
                endpoint="http://localhost:7200",
                repository="napcore",
                graph_uris=[
                    "https://napcore.eu/graph/alignments/transmodel-opra",
                    "https://napcore.eu/graph/alignments/transmodel-netex",
                    "https://napcore.eu/graph/alignments/transmodel-siri",
                ],
            )

        sent_query = urlopen_mock.call_args[0][0].data.decode("utf-8")
        self.assertIn("UNION", sent_query)
        self.assertIn("?pivot", sent_query)
        self.assertIn("https://transmodel-cen.eu/6.2/", sent_query)
        # The two hops of the pivot branch must use independently-bound graph
        # variables (not both constrained to the same single ?g), otherwise
        # they collapse back into the single-graph-only bug this guards against.
        self.assertIn("?gPivot", sent_query)
        self.assertIn("?gSibling", sent_query)

    def test_query_graphdb_concept_expansion_pivot_branch_reaches_other_standards(self):
        """Simulates GraphDB returning results only from the pivot UNION branch
        (as if the direct-relation branch found nothing, which is the real-world
        case when a seed's only path to a sibling standard is through a shared
        Transmodel concept)."""
        graphdb_response = {
            "head": {"vars": ["related"]},
            "results": {
                "bindings": [
                    {"related": {"type": "uri", "value": "https://transmodel-cen.eu/6.2/JOURNEY"}},
                    {"related": {"type": "uri", "value": "https://netex.org.uk/netex/2.0#VehicleJourney"}},
                    {"related": {"type": "uri", "value": "https://siri.org.uk/siri/1.3#EstimatedVehicleJourney"}},
                ]
            },
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphdb_response).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.graphdb_client.urlopen", return_value=mock_response):
            result = query_graphdb_concept_expansion(
                concept_ids={"opra:CancelledDatedVehicleJourneyCount"},
                hops=1,
                endpoint="http://localhost:7200",
                repository="napcore",
                graph_uris=[
                    "https://napcore.eu/graph/alignments/transmodel-opra",
                    "https://napcore.eu/graph/alignments/transmodel-netex",
                    "https://napcore.eu/graph/alignments/transmodel-siri",
                ],
            )

        self.assertIn("netex:VehicleJourney", result)
        self.assertIn("siri:EstimatedVehicleJourney", result)

    def test_build_graph_scope_for_standards_adds_artifact_rules_only_when_requested(self):
        scoped_without_rules = build_graph_scope_for_standards(
            {"NeTEx", "SIRI"},
            include_artifact_rules=False,
        )
        self.assertIn("https://napcore.eu/graph/standards/netex", scoped_without_rules)
        self.assertIn("https://napcore.eu/graph/alignments/transmodel-siri", scoped_without_rules)
        self.assertFalse(any("/artifact-rules/" in uri for uri in scoped_without_rules))

        scoped_with_rules = build_graph_scope_for_standards(
            {"NeTEx"},
            include_artifact_rules=True,
        )
        self.assertIn("https://napcore.eu/graph/artifact-rules/netex/v1.0", scoped_with_rules)

    def test_build_graph_scope_for_standards_always_adds_transmodel_reference(self):
        """A NeTEx-only question must still reach tm: concepts and the direct
        Transmodel<->NeTEx alignment, because Transmodel is the reference."""
        scoped = build_graph_scope_for_standards({"NeTEx"}, include_artifact_rules=False)
        self.assertIn("https://napcore.eu/graph/standards/transmodel", scoped)
        self.assertNotIn("https://napcore.eu/graph/alignments/transmodel", scoped)  # retired
        for standard in ("netex", "siri", "opra"):
            self.assertIn(f"https://napcore.eu/graph/alignments/transmodel-{standard}", scoped)
        self.assertEqual(len(scoped), len(set(scoped)))

    def test_build_graph_scope_for_standards_stays_empty_without_standards(self):
        # Empty scope means "query all graphs"; adding reference graphs would narrow it.
        self.assertEqual(build_graph_scope_for_standards(set(), include_artifact_rules=False), [])

    def test_query_graphdb_concept_expansion_pivots_through_transmodel_only(self):
        graphdb_response = {"head": {"vars": ["related"]}, "results": {"bindings": []}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(graphdb_response).encode("utf-8")
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("helpdesk.services.graphdb_client.urlopen", return_value=mock_response) as urlopen_mock:
            query_graphdb_concept_expansion(
                concept_ids={"netex:StopPlace"},
                hops=1,
                endpoint="http://localhost:7200",
                repository="napcore",
                graph_uris=build_graph_scope_for_standards({"NeTEx"}, include_artifact_rules=False),
            )

        sent_query = urlopen_mock.call_args[0][0].data.decode("utf-8")
        self.assertIn("STRSTARTS(STR(?pivot), 'https://transmodel-cen.eu/6.2/')", sent_query)
        # The NITS pivot (and its abstract-root exclusion) is gone: Transmodel
        # is the only hub this branch pivots through now.
        self.assertNotIn("napcore.eu/ontology/nits", sent_query)
        self.assertNotIn("NOT IN (", sent_query)

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
        self.assertEqual(len(results), 8)
        for standard in ("netex", "siri", "opra"):
            self.assertIn(f"https://napcore.eu/graph/alignments/transmodel-{standard}", graph_uris)
        self.assertNotIn("https://napcore.eu/graph/alignments/transmodel", graph_uris)
        self.assertFalse(any("/artifact-rules/" in uri for uri in graph_uris))

    def test_load_default_ontology_graphs_deletes_retired_graphs_on_replace(self):
        with (
            patch("helpdesk.services.graphdb_client.upload_named_graph_turtle") as upload_mock,
            patch("helpdesk.services.graphdb_client.delete_named_graph") as delete_mock,
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=""),
        ):
            upload_mock.side_effect = lambda **kwargs: {"graphUri": kwargs["graph_uri"], "replaced": True}
            results = load_default_ontology_graphs(
                endpoint="http://localhost:7200",
                repository="napcore",
                replace=True,
            )

        self.assertEqual(delete_mock.call_count, 5)
        deleted_graph_uris = {call.kwargs["graph_uri"] for call in delete_mock.call_args_list}
        self.assertEqual(
            deleted_graph_uris,
            {
                "https://napcore.eu/graph/alignments/transmodel",
                "https://napcore.eu/graph/core/napcore-its",
                "https://napcore.eu/graph/alignments/netex",
                "https://napcore.eu/graph/alignments/opra",
                "https://napcore.eu/graph/alignments/siri",
            },
        )
        retired_results = results[-5:]
        self.assertTrue(all(item["retired"] for item in retired_results))
        self.assertEqual({item["graphUri"] for item in retired_results}, deleted_graph_uris)

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


class TnItsGraphScopeTests(TestCase):
    def test_tn_its_scope_reads_its_own_graph(self):
        from helpdesk.services.graphdb_client import build_graph_scope_for_standards

        graphs = build_graph_scope_for_standards({"tn-its"}, include_artifact_rules=False)
        # The TN-ITS graph first; the Transmodel reference graphs follow, as for every scoped query.
        self.assertEqual(graphs[0], "https://napcore.eu/graph/standards/tn-its")
        self.assertIn("https://napcore.eu/graph/standards/transmodel", graphs)

    def test_tn_its_concept_ids_round_trip(self):
        from helpdesk.services.graphdb_client import _iri_to_concept_id, _to_iri

        iri = "http://spec.tn-its.eu/owl/tnits-owl#RoadFeature"
        self.assertEqual(_iri_to_concept_id(iri), "tnits:RoadFeature")
        self.assertEqual(_to_iri("tnits:RoadFeature"), iri)
