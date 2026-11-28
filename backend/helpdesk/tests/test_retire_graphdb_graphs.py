"""retire_graphdb_graphs: deletes the retired graphs and fails while NITS data remains."""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from helpdesk.management.commands import retire_graphdb_graphs as command
from helpdesk.services.graphdb_client import RETIRED_GRAPH_URIS

GRAPHDB_ON = {
    "GRAPHDB_ENABLED": True,
    "GRAPHDB_SPARQL_ENDPOINT": "http://graphdb:7200",
    "GRAPHDB_REPOSITORY": "napcore-helpdesk",
}


@override_settings(**GRAPHDB_ON)
class RetireGraphdbGraphsTests(SimpleTestCase):
    def _run(self, ask_result):
        out = StringIO()
        with patch.object(command, "delete_named_graph") as delete, patch.object(
            command, "execute_sparql_query", return_value=ask_result
        ) as ask:
            call_command("retire_graphdb_graphs", stdout=out)
        return delete, ask, out.getvalue()

    def test_deletes_every_retired_graph_and_passes_when_no_nits_is_left(self):
        delete, ask, out = self._run({"head": {}, "boolean": False})
        self.assertEqual([c.kwargs["graph_uri"] for c in delete.call_args_list], RETIRED_GRAPH_URIS)
        self.assertIn("https://napcore.eu/graph/core/napcore-its", RETIRED_GRAPH_URIS)
        self.assertIn("urn:graph:napcore-its", RETIRED_GRAPH_URIS)
        self.assertIn("https://napcore.eu/ontology/nits#", ask.call_args.kwargs["sparql_query"])
        self.assertIn("No NITS statements", out)

    def test_fails_when_nits_statements_remain(self):
        with self.assertRaisesMessage(CommandError, "still holds statements"):
            self._run({"head": {}, "boolean": True})

    def test_failure_lists_the_graphs_and_samples_that_hold_nits(self):
        graphs = {"results": {"bindings": [{"g": {"value": "https://napcore.eu/graph/old"}, "n": {"value": "12"}}]}}
        sample = {
            "results": {
                "bindings": [
                    {
                        "s": {"value": "https://napcore.eu/ontology/nits#Stop"},
                        "p": {"value": "http://www.w3.org/2000/01/rdf-schema#label"},
                        "o": {"value": "Stop"},
                    }
                ]
            }
        }
        out = StringIO()
        with patch.object(command, "delete_named_graph"), patch.object(
            command, "execute_sparql_query", side_effect=[None, {"boolean": True}, graphs, sample]
        ) as query:
            with self.assertRaisesMessage(CommandError, "still holds statements"):
                call_command("retire_graphdb_graphs", stdout=out)
        self.assertIn("GRAPH ?g", query.call_args_list[2].kwargs["sparql_query"])
        self.assertIn("12\thttps://napcore.eu/graph/old", out.getvalue())
        self.assertIn("sample: https://napcore.eu/ontology/nits#Stop", out.getvalue())

    def test_fails_when_the_check_cannot_run(self):
        with self.assertRaisesMessage(CommandError, "Could not check"):
            self._run(None)

    def test_fails_when_a_graph_cannot_be_deleted(self):
        with patch.object(command, "delete_named_graph", side_effect=OSError("timed out")):
            with self.assertRaisesMessage(CommandError, "Could not delete"):
                call_command("retire_graphdb_graphs", stdout=StringIO())

    @override_settings(GRAPHDB_ENABLED=False)
    def test_skips_when_graphdb_is_off(self):
        with patch.object(command, "delete_named_graph") as delete:
            call_command("retire_graphdb_graphs", stdout=StringIO())
        delete.assert_not_called()


def _counts(mapping):
    return {"results": {"bindings": [{"g": {"value": g}, "n": {"value": str(n)}} for g, n in mapping.items()]}}


@override_settings(**GRAPHDB_ON)
class RetireGraphdbGraphsOutputTests(SimpleTestCase):
    """What the command prints (the deploy log and deploy.sh read it); GraphDB is mocked."""

    def _run(self, counts, *args):
        out = StringIO()
        printed_before_delete = {}

        def fake_delete(**kw):
            printed_before_delete[kw["graph_uri"]] = f"Deleting {kw['graph_uri']}" in out.getvalue()

        with patch.object(command, "delete_named_graph", side_effect=fake_delete) as delete, patch.object(
            command,
            "execute_sparql_query",
            side_effect=lambda **kw: counts if "COUNT" in kw["sparql_query"] else {"boolean": False},
        ):
            call_command("retire_graphdb_graphs", *args, stdout=out)
        return delete, printed_before_delete, out.getvalue()

    def test_graphs_with_triples_are_printed_with_counts_before_they_are_deleted(self):
        first, second = RETIRED_GRAPH_URIS[0], RETIRED_GRAPH_URIS[1]
        delete, printed, out = self._run(_counts({first: 40, second: 2, "https://example.org/kept": 99}))
        self.assertIn(f"Deleting {first}: 40 triples", out)
        self.assertIn(f"Deleting {second}: 2 triples", out)
        self.assertNotIn("kept", out)
        self.assertTrue(printed[first] and printed[second])  # the line was out before the delete call
        self.assertIn("RETIRE-GRAPHS: deleted 2 graphs with 42 triples in total", out)
        self.assertEqual(delete.call_count, len(RETIRED_GRAPH_URIS))

    def test_absent_graphs_get_no_deleting_line_and_the_summary_says_nothing_was_deleted(self):
        delete, _, out = self._run(_counts({"https://example.org/other": 5}))
        self.assertNotIn("Deleting ", out)
        self.assertIn("Already absent or empty: " + RETIRED_GRAPH_URIS[0], out)
        self.assertIn("RETIRE-GRAPHS: nothing deleted: no retired graph holds triples", out)
        self.assertEqual(delete.call_count, len(RETIRED_GRAPH_URIS))

    def test_a_failing_count_query_still_deletes_and_says_the_count_was_unavailable(self):
        delete, _, out = self._run(None)
        self.assertEqual(delete.call_count, len(RETIRED_GRAPH_URIS))
        self.assertIn(f"Deleting {RETIRED_GRAPH_URIS[0]} (triple count unavailable)", out)
        self.assertIn("RETIRE-GRAPHS: deleted: triple count unavailable", out)
        self.assertNotRegex(out, r"RETIRE-GRAPHS: deleted [1-9]")  # deploy.sh restarts only on a counted deletion

    def test_dry_run_prints_the_same_and_deletes_nothing(self):
        first = RETIRED_GRAPH_URIS[0]
        delete, _, out = self._run(_counts({first: 7}), "--dry-run")
        delete.assert_not_called()
        self.assertIn(f"Would delete {first}: 7 triples", out)
        self.assertIn("RETIRE-GRAPHS: would delete 1 graphs with 7 triples in total", out)
        self.assertNotIn("No NITS statements", out)
