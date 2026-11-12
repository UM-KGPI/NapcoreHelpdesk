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
        self.assertIn("https://napcore.eu/ontology/nits#", ask.call_args.kwargs["sparql_query"])
        self.assertIn("No NITS statements", out)

    def test_fails_when_nits_statements_remain(self):
        with self.assertRaisesMessage(CommandError, "still holds statements"):
            self._run({"head": {}, "boolean": True})

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
