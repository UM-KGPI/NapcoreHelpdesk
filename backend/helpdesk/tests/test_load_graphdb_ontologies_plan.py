"""load_graphdb_ontologies prints the plan it would execute, from the code path that executes it."""

from __future__ import annotations

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from helpdesk.management.commands import load_graphdb_ontologies as command
from helpdesk.services import graphdb_client
from helpdesk.services.graphdb_client import RETIRED_GRAPH_URIS, plan_default_ontology_graphs

TTL = "@prefix ex: <http://example.org/> . ex:a ex:p ex:b . ex:b ex:p ex:c .\n"
STANDARD_GRAPHS = [
    "https://napcore.eu/graph/standards/transmodel",
    "https://napcore.eu/graph/standards/netex",
    "https://napcore.eu/graph/standards/opra",
    "https://napcore.eu/graph/standards/siri",
    "https://napcore.eu/graph/examples/catalog",
    "https://napcore.eu/graph/alignments/transmodel-netex",
    "https://napcore.eu/graph/alignments/transmodel-opra",
    "https://napcore.eu/graph/alignments/transmodel-siri",
]
GRAPHDB_ON = {"GRAPHDB_ENABLED": True, "GRAPHDB_SPARQL_ENDPOINT": "http://graphdb.test:7200", "GRAPHDB_REPOSITORY": "r"}


def _ontology_dir(skip: tuple[str, ...] = ()) -> str:
    root = Path(tempfile.mkdtemp())
    for sub, names in (
        ("standards", ["transmodel", "netex", "opra", "siri", "examples"]),
        ("alignments", [f"transmodel-{s}-align" for s in ("netex", "opra", "siri")]),
    ):
        (root / sub).mkdir()
        for name in names:
            if name not in skip:
                (root / sub / f"{name}.ttl").write_text(TTL)
    return str(root)


def _counts(mapping):
    return {"results": {"bindings": [{"g": {"value": g}, "n": {"value": str(n)}} for g, n in mapping.items()]}}


def _run(*args, ontology_dir=None, counts=None, **settings_kw):
    out = StringIO()
    with patch.dict("os.environ", {"NAPCORE_ONTOLOGY_DIR": ontology_dir or _ontology_dir()}), override_settings(
        **{**GRAPHDB_ON, **settings_kw}
    ), patch.object(command, "execute_sparql_query", return_value=counts) as query:
        call_command("load_graphdb_ontologies", *args, stdout=out)
    return out.getvalue(), query


class PlanTests(SimpleTestCase):
    def test_the_dry_run_lists_every_graph_with_its_file_and_triple_count(self):
        out, _ = _run("--replace")

        for graph in STANDARD_GRAPHS:
            self.assertIn(f"replace graph={graph} from file=", out)
        self.assertIn("netex.ttl (", out)
        self.assertIn("2 triples", out)  # counted locally from the file
        self.assertIn("Dry-run only", out)

    def test_the_dry_run_with_replace_lists_each_retired_graph_it_would_delete(self):
        out, _ = _run("--replace")

        for graph in RETIRED_GRAPH_URIS:
            self.assertIn(f"delete graph={graph}", out)

    def test_without_replace_the_graphs_are_appended_and_nothing_is_deleted(self):
        out, _ = _run()

        self.assertIn("append to graph=https://napcore.eu/graph/standards/netex", out)
        self.assertNotIn("delete graph=", out)
        self.assertIn("none (only --replace deletes them)", out)

    def test_current_triple_counts_from_graphdb_are_shown_when_the_query_answers(self):
        out, query = _run("--replace", counts=_counts({STANDARD_GRAPHS[1]: 27130, RETIRED_GRAPH_URIS[0]: 5}))

        self.assertEqual(query.call_count, 1)  # one cheap query for all graphs
        self.assertIn("27130 triples now in GraphDB", out)
        self.assertIn(f"delete graph={RETIRED_GRAPH_URIS[0]} (5 triples now)", out)
        self.assertIn(f"delete graph={RETIRED_GRAPH_URIS[1]} (0 triples now)", out)

    def test_an_unreadable_graphdb_does_not_stop_the_plan(self):
        out, _ = _run("--replace", counts=None)

        self.assertIn("current count unavailable", out)
        self.assertIn(f"replace graph={STANDARD_GRAPHS[0]}", out)

    def test_graphdb_disabled_makes_no_query(self):
        out, query = _run("--replace", GRAPHDB_ENABLED=False)

        query.assert_not_called()
        self.assertIn("current count unavailable", out)

    def test_a_missing_file_is_named_in_the_plan(self):
        out, _ = _run(ontology_dir=_ontology_dir(skip=("opra",)))

        self.assertIn("file MISSING", out)

    def test_artifact_rules_appear_only_when_asked_for(self):
        without, _ = _run()
        with_rules, _ = _run("--include-artifact-rules", "--artifact-rule-standards", "opra")

        self.assertNotIn("artifact-rules", without)
        self.assertIn("graph=https://napcore.eu/graph/artifact-rules/opra/v1.0", with_rules)
        self.assertNotIn("artifact-rules/netex", with_rules)

    def test_the_dry_run_changes_nothing_in_graphdb(self):
        with patch.object(graphdb_client, "urlopen") as urlopen:
            _run("--replace")
        urlopen.assert_not_called()


class PlanIsWhatTheLoadExecutesTests(SimpleTestCase):
    def test_the_load_uploads_and_deletes_exactly_the_planned_graphs(self):
        directory = _ontology_dir()
        with patch.dict("os.environ", {"NAPCORE_ONTOLOGY_DIR": directory}):
            plan = plan_default_ontology_graphs(replace=True)
            with patch.object(graphdb_client, "upload_named_graph_turtle", return_value={"replaced": True}) as upload, patch.object(
                graphdb_client, "delete_named_graph"
            ) as delete:
                graphdb_client.load_default_ontology_graphs(endpoint="http://g", repository="r", replace=True)

        self.assertEqual([c.kwargs["graph_uri"] for c in upload.call_args_list], [e["graphUri"] for e in plan["graphs"]])
        self.assertEqual([c.kwargs["graph_uri"] for c in delete.call_args_list], plan["retired"])

    def test_the_load_without_replace_appends_and_deletes_nothing(self):
        with patch.dict("os.environ", {"NAPCORE_ONTOLOGY_DIR": _ontology_dir()}):
            with patch.object(graphdb_client, "upload_named_graph_turtle", return_value={}) as upload, patch.object(
                graphdb_client, "delete_named_graph"
            ) as delete:
                graphdb_client.load_default_ontology_graphs(endpoint="http://g", repository="r", replace=False)

        self.assertTrue(all(c.kwargs["replace"] is False for c in upload.call_args_list))
        delete.assert_not_called()
