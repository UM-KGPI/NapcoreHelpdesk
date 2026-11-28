from __future__ import annotations

import json
from contextlib import contextmanager
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.test import SimpleTestCase, override_settings

import helpdesk.services.semantic_graph as semantic_graph

ENDPOINT = "http://graphdb.test:7200/repositories/napcore-helpdesk"
CONCEPT = "https://netex.org.uk/netex/2.0#Line"


class _Response:
    def __init__(self, bindings):
        self._body = json.dumps({"results": {"bindings": bindings}}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _answer(request, timeout=None):
    """A GraphDB that answers: one label row for the labels query, nothing for the others."""
    if "prefLabel" in request.full_url:
        return _Response([{"concept": {"value": CONCEPT}, "label": {"value": "Line"}}])
    return _Response([])


def _refuse(request, timeout=None):
    raise URLError(ConnectionRefusedError(111, "Connection refused"))


class _Clock:
    """A fake clock: sleeping advances it, nothing really waits."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class _Run:
    """What a patched load saw: the fake clock, the mocked network call and the warnings logged."""

    def __init__(self, clock, opener, warning):
        self.clock = clock
        self.opener = opener
        self._warning = warning

    @property
    def sleeps(self):
        return self.clock.sleeps

    @property
    def warnings(self):
        return [call.args[0] % call.args[1:] for call in self._warning.call_args_list]


@contextmanager
def _patched(urlopen, *, enabled="True", wait=120):
    clock = _Clock()
    env = {"GRAPHDB_ENABLED": enabled, "GRAPHDB_SPARQL_ENDPOINT": ENDPOINT}
    with patch.dict("os.environ", env), patch.object(
        semantic_graph, "SKIP_GRAPHDB_IMPORT", False
    ), patch("urllib.request.urlopen", side_effect=urlopen) as opener, patch.object(
        semantic_graph.time, "sleep", side_effect=clock.sleep
    ), patch.object(semantic_graph.time, "monotonic", side_effect=clock.monotonic), patch.object(
        semantic_graph.logger, "warning"
    ) as warning, override_settings(GRAPHDB_STARTUP_WAIT_SECONDS=wait):
        yield _Run(clock, opener, warning)


class OntologyStartupWaitTests(SimpleTestCase):
    def test_refused_twice_then_answering_loads_and_logs_two_retries(self):
        calls = {"n": 0}

        def urlopen(request, timeout=None):
            calls["n"] += 1
            if calls["n"] <= 2:
                return _refuse(request)
            return _answer(request)

        with _patched(urlopen) as run:
            result = semantic_graph._load_ontology()

        self.assertIn("netex:Line", result["concepts"])
        retries = [m for m in run.warnings if "retry" in m.lower()]
        self.assertEqual(len(retries), 2)
        self.assertEqual(len(run.sleeps), 2)
        self.assertNotIn(ENDPOINT, " ".join(retries))

    def test_http_5xx_while_starting_is_retried(self):
        calls = {"n": 0}

        def urlopen(request, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise HTTPError(request.full_url, 503, "Service Unavailable", {}, None)
            return _answer(request)

        with _patched(urlopen) as run:
            result = semantic_graph._load_ontology()

        self.assertIn("netex:Line", result["concepts"])
        self.assertEqual(len(run.sleeps), 1)

    def test_http_4xx_is_not_retried(self):
        def urlopen(request, timeout=None):
            raise HTTPError(request.full_url, 401, "Unauthorized", {}, None)

        with _patched(urlopen) as run:
            with self.assertRaises(RuntimeError):
                semantic_graph._load_ontology()

        self.assertEqual(run.sleeps, [])
        self.assertEqual(run.opener.call_count, 1)

    def test_never_answering_fails_after_the_bound_naming_the_endpoint(self):
        with _patched(_refuse, wait=60) as run:
            with self.assertRaises(RuntimeError) as raised:
                semantic_graph._load_ontology()

        self.assertIn(ENDPOINT, str(raised.exception))
        self.assertGreater(len(run.sleeps), 1)
        self.assertLessEqual(sum(run.sleeps), 60)
        self.assertEqual(run.opener.call_count, len(run.sleeps) + 1)
        self.assertEqual(len([m for m in run.warnings if "retry" in m.lower()]), len(run.sleeps))

    def test_a_bound_of_zero_does_not_wait(self):
        with _patched(_refuse, wait=0) as run:
            with self.assertRaises(RuntimeError):
                semantic_graph._load_ontology()

        self.assertEqual(run.sleeps, [])
        self.assertEqual(run.opener.call_count, 1)

    def test_a_reload_asks_for_no_wait(self):
        with _patched(_refuse, wait=120) as run:
            with self.assertRaises(RuntimeError):
                semantic_graph._load_ontology(wait_seconds=0)

        self.assertEqual(run.sleeps, [])
        self.assertEqual(run.opener.call_count, 1)

    def test_disabled_by_setting_makes_no_call_and_no_sleep(self):
        with _patched(_refuse, enabled="False") as run:
            result = semantic_graph._load_ontology()

        self.assertEqual(result, {"namespaces": {}, "concepts": {}, "relationships": []})
        run.opener.assert_not_called()
        self.assertEqual(run.sleeps, [])

    def test_answering_at_once_makes_each_query_once_and_never_sleeps(self):
        with _patched(_answer) as run:
            result = semantic_graph._load_ontology()

        self.assertIn("netex:Line", result["concepts"])
        self.assertEqual(run.opener.call_count, 7)  # labels, related, object properties, subclasses, then directed relations, asserted subclasses, definitions
        self.assertEqual(run.sleeps, [])
        self.assertEqual(run.warnings, [])


RELATED = "https://netex.org.uk/netex/2.0#Network"


def _answer_except(failing_marker, failure):
    """A GraphDB that answers every ontology query but the one whose text holds `failing_marker`."""

    def urlopen(request, timeout=None):
        if failing_marker in request.full_url:
            raise failure(request)
        if "prefLabel" in request.full_url:
            return _Response(
                [
                    {"concept": {"value": CONCEPT}, "label": {"value": "Line"}},
                    {"concept": {"value": RELATED}, "label": {"value": "Network"}},
                ]
            )
        if "subClassOf" in request.full_url:
            return _Response([{"concept": {"value": CONCEPT}, "related": {"value": RELATED}}])
        return _Response([])

    return urlopen


def _http_400(request):
    return HTTPError(request.full_url, 400, "Bad Request", {}, None)


class OntologyPartialLoadTests(SimpleTestCase):
    """A later query of the ontology load that errors must not give a silently partial ontology."""

    # What tells each later query apart in the request URL (the query text is URL-encoded).
    LATER_QUERIES = {
        "skos:related": "core%23related",
        "object properties": "ObjectProperty",
        "subclasses": "subClassOf",
    }

    def test_a_later_query_error_at_start_up_fails_naming_the_query(self):
        for name, marker in self.LATER_QUERIES.items():
            with self.subTest(query=name), _patched(_answer_except(marker, _http_400)):
                with self.assertRaises(RuntimeError) as raised:
                    semantic_graph._load_ontology()
                self.assertIn(f"'{name}'", str(raised.exception))

    def test_a_later_query_failing_while_starting_is_waited_for_then_fails(self):
        def refuse(request):
            return URLError(ConnectionRefusedError(111, "Connection refused"))

        with _patched(_answer_except("subClassOf", refuse), wait=30) as run:
            with self.assertRaises(RuntimeError) as raised:
                semantic_graph._load_ontology()

        self.assertIn("'subclasses'", str(raised.exception))
        self.assertGreater(len(run.sleeps), 0)
        self.assertLessEqual(sum(run.sleeps), 30)

    def test_the_first_query_error_still_fails_and_is_named(self):
        with _patched(_answer_except("prefLabel", _http_400)):
            with self.assertRaises(RuntimeError) as raised:
                semantic_graph._load_ontology()
        self.assertIn("'labels'", str(raised.exception))
        self.assertIn(ENDPOINT, str(raised.exception))

    def test_a_later_query_with_no_rows_is_not_a_failure(self):
        with _patched(_answer) as run:  # related, object properties and subclasses all succeed empty
            result = semantic_graph._load_ontology()

        self.assertEqual(list(result["concepts"]), ["netex:Line"])
        self.assertEqual(result["concepts"]["netex:Line"]["narrower"], [])
        self.assertEqual(run.opener.call_count, 7)

    def test_all_queries_answering_builds_the_whole_ontology(self):
        with _patched(_answer_except("no-such-marker", _http_400)):
            result = semantic_graph._load_ontology()

        self.assertEqual(set(result["concepts"]), {"netex:Line", "netex:Network"})
        self.assertEqual(result["concepts"]["netex:Network"]["narrower"], ["netex:Line"])

    def test_a_re_read_with_a_failing_later_query_keeps_the_ontology_it_has(self):
        import datetime as dt

        read_at = dt.datetime(2026, 11, 6, 9, 0, tzinfo=dt.timezone.utc)
        live_aliases = {"netex:Line": {"line"}}
        live_relations = {"netex:Line": {"netex:Network"}}
        aggregate = patch(
            "helpdesk.models.OntologyAssetVersion.objects.aggregate",
            return_value={"latest": read_at + dt.timedelta(hours=1)},
        )
        with aggregate, patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", live_aliases), patch.object(
            semantic_graph, "GRAPH_RELATIONS", live_relations
        ), patch.object(semantic_graph, "_ONTOLOGY_READ_AT", read_at), patch.object(
            semantic_graph, "_last_ontology_check", -10_000.0  # long ago on the fake clock of _patched
        ), _patched(_answer_except("subClassOf", _http_400)), patch.object(semantic_graph.logger, "error") as error:
            reloaded = semantic_graph.reload_ontology_if_updated()
            read_at_after = semantic_graph._ONTOLOGY_READ_AT

        self.assertFalse(reloaded)
        self.assertEqual(live_aliases, {"netex:Line": {"line"}})
        self.assertEqual(live_relations, {"netex:Line": {"netex:Network"}})
        self.assertEqual(read_at_after, read_at)  # it will be tried again after the next load
        self.assertTrue(error.called)
