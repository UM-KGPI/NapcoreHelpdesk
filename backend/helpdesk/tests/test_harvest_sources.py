"""Harvesting from the editor (Harvest & Index) and the mobilityDCAT-AP source."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from helpdesk.models import OntologyAssetVersion, SourceChunk
from helpdesk.services.embeddings import build_text_embedding
from helpdesk.services.index_builder import infer_scope, load_profile_rules, split_html
from helpdesk.services.question_parsing import parse_question_to_semantic_query
from helpdesk.services.retrieval_gateway import _scope_matches
from helpdesk.services.source_refresh import (
    MOBILITYDCAT_AP_ONTOLOGY,
    SourceRepository,
    configured_sources,
    find_source,
    refresh_all_sources,
)
from helpdesk.tasks import harvest_source
from helpdesk.tests import test_api
from helpdesk.tests.test_source_refresh import _git, make_remote

MDCAT_URL = "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP"

PROPERTY_TABLE = """<table class="simple" id="table-properties-for-dataset">
<thead><tr><th><p>Property name and URI</p></th><th><p>Range</p></th><th><p>Card.</p></th><th><p>Definition</p></th></tr></thead>
<tbody>
<tr class="property" id="dataset-assessment-result">
<td><p>+assessment result</p><p><code>mobilitydcatap:assessmentResult</code></p></td>
<td><p><a href="#class-assessment"><code>mobilitydcatap:Assessment</code></a></p></td>
<td><p>0..1</p></td>
<td><p>The results and outcomes from an assessment process by an external organisation.</p></td>
</tr>
</tbody></table>"""

ONTOLOGY_TTL = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
<https://w3id.org/mobilitydcat-ap> a owl:Ontology ; owl:versionInfo "3.0.0"@en .
"""


def make_mobilitydcat_remote(root: Path) -> Path:
    """A repository laid out like mobilityDCAT-AP: spec page, property tables, examples, ontology, SHACL."""
    remote = make_remote(root, "mobilityDCAT-AP", files=20)
    (remote / "src" / "tables").mkdir(parents=True)
    (remote / "src" / "examples").mkdir()
    (remote / "src" / "shacl").mkdir()
    (remote / "src" / "index.html").write_text(
        "<html><body><section id='intro'><h2>Introduction</h2><p>mobilityDCAT-AP describes datasets on NAPs.</p>"
        "</section><script>var x = 1;</script></body></html>",
        encoding="utf-8",
    )
    (remote / "src" / "tables" / "properties-for-dataset.html").write_text(PROPERTY_TABLE, encoding="utf-8")
    (remote / "src" / "tables" / "class-dataset.html").write_text(
        "<table><tr><th>Definition</th><td>A dataset is a collection of data.</td></tr></table>", encoding="utf-8"
    )
    (remote / "src" / "examples" / "example-minimum.ttl").write_text("<a> <b> <c> .\n", encoding="utf-8")
    (remote / "src" / "mobilitydcat-ap.ttl").write_text(ONTOLOGY_TTL, encoding="utf-8")
    (remote / "src" / "shacl" / "shapes.ttl").write_text("<s> <p> <o> .\n", encoding="utf-8")
    _git(remote, "add", "-A")
    _git(remote, "commit", "-q", "-m", "spec")
    return remote


class SplitHtmlTests(SimpleTestCase):
    def test_a_table_row_becomes_header_value_lines_named_after_the_file(self):
        chunks = split_html(PROPERTY_TABLE, max_chars=1200, source_name="src/tables/properties-for-dataset.html")
        self.assertEqual(len(chunks), 1)
        text, chunk_type, heading = chunks[0]
        self.assertEqual((chunk_type, heading), ("heading_section", "Properties for dataset"))
        self.assertTrue(text.startswith("Properties for dataset\n\n"))
        self.assertIn("Property name and URI: +assessment result mobilitydcatap:assessmentResult", text)
        self.assertIn("Card.: 0..1", text)
        self.assertIn("Definition: The results and outcomes", text)
        self.assertNotIn("<", text)

    def test_a_class_table_with_row_headers_becomes_label_value_lines(self):
        # Class tables run vertically: no header row, each row opens with its own <th>.
        html = (
            "<table><tbody><tr><th>Definition</th><td>A dataset is a collection of data.</td></tr>"
            "<tr><th>URI</th><td><p><code>dcat:Dataset</code></p></td></tr>"
            "<tr><th>Usage note</th><td> </td></tr></tbody></table>"
        )
        chunks = split_html(html, max_chars=1200, source_name="src/tables/class-dataset.html")
        self.assertEqual(
            chunks,
            [("Class dataset\n\nDefinition: A dataset is a collection of data.\n\nURI: dcat:Dataset", "heading_section", "Class dataset")],
        )

    def test_headings_start_sections_and_scripts_are_dropped(self):
        html = "<h2>Scope</h2><p>One.</p><p>Two.</p><h3>Context</h3><p>Three &amp; four.</p><script>x()</script>"
        chunks = split_html(html, max_chars=1200)
        self.assertEqual([(c[2], c[0]) for c in chunks], [("Scope", "Scope\n\nOne.\n\nTwo."), ("Context", "Context\n\nThree & four.")])

    def test_long_sections_are_packed_up_to_the_limit(self):
        html = "<h2>Long</h2>" + "".join(f"<p>{'word ' * 30}{i}</p>" for i in range(20))
        chunks = split_html(html, max_chars=400)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c[0]) <= 400 and c[2] == "Long" for c in chunks))


class MobilityDcatSourceTests(SimpleTestCase):
    def test_it_is_a_configured_source_with_its_own_ontology(self):
        source = find_source("mobilitydcat-ap")
        self.assertIsNotNone(source)
        self.assertEqual((source.url, source.profile, source.ontology), (MDCAT_URL, "mobilitydcat-ap", MOBILITYDCAT_AP_ONTOLOGY))
        self.assertEqual([s.name for s in configured_sources()][:3], ["NeTEx", "SIRI", "OpRa"])
        self.assertIsNone(find_source("nope"))

    def test_the_profile_adds_html_and_turtle(self):
        profile = load_profile_rules("mobilitydcat-ap")
        self.assertEqual(profile["extensions"], {".html", ".ttl"})
        self.assertEqual(load_profile_rules("netex")["extensions"], set())

    def test_chunks_are_tagged_by_repository_only(self):
        self.assertEqual(infer_scope("src/index.html", "DCAT-AP text", MDCAT_URL), ["mobilityDCAT-AP"])
        self.assertNotIn("mobilityDCAT-AP", infer_scope("docs/x.md", "a mobilityDCAT-AP note", "https://github.com/TransmodelEcosystem/NeTEx"))

    def test_it_is_searched_only_when_the_question_names_it(self):
        self.assertFalse(_scope_matches(["mobilityDCAT-AP"], None))
        self.assertTrue(_scope_matches(["mobilityDCAT-AP"], ["mobilityDCAT-AP"]))
        for question in ("What is a Distribution in mobilityDCAT-AP?", "Which DCAT-AP properties are mandatory?", "mobility DCAT dataset"):
            with self.subTest(question=question):
                self.assertIn("mobilityDCAT-AP", parse_question_to_semantic_query(question).candidate_standards)
        self.assertNotIn("mobilityDCAT-AP", parse_question_to_semantic_query("What is a ServiceJourney in NeTEx?").candidate_standards)


@override_settings(
    ALLOWED_SOURCE_REPOSITORIES={MDCAT_URL},
    GRAPHDB_ENABLED=True,
    GRAPHDB_SPARQL_ENDPOINT="http://graphdb.test/repositories/napcore",
    GRAPHDB_REPOSITORY="napcore",
)
class HarvestWithOntologyTests(TestCase):
    """The real indexer and a real git remote; only the GraphDB upload is replaced."""

    def _source(self, remote: Path) -> SourceRepository:
        return SourceRepository("mobilityDCAT-AP", MDCAT_URL, "mobilitydcat-ap", str(remote), MOBILITYDCAT_AP_ONTOLOGY)

    def test_text_is_indexed_and_the_ontology_loaded_only_when_it_changed(self):
        with TemporaryDirectory() as tmp, patch("helpdesk.services.graphdb_client.upload_named_graph_turtle") as upload:
            root = Path(tmp)
            remote = make_mobilitydcat_remote(root)
            source = self._source(remote)

            first = refresh_all_sources([source], checkout_root=root / "repos")
            row = first["results"]["mobilityDCAT-AP"]
            self.assertEqual(row["status"], "ok", first)
            self.assertEqual(row["ontology"]["status"], "loaded")
            self.assertEqual(upload.call_args.kwargs["graph_uri"], "https://napcore.eu/graph/standards/mobilitydcat-ap")
            self.assertEqual(upload.call_args.kwargs["turtle_content"], ONTOLOGY_TTL)
            record = OntologyAssetVersion.objects.get(ontology_key="mobilitydcat-ap")
            self.assertEqual(record.version, "3.0.0")
            self.assertIsNotNone(record.last_loaded_at)

            chunks = SourceChunk.objects.filter(repository_url=MDCAT_URL)
            paths = set(chunks.values_list("source_path", flat=True))
            self.assertTrue({"src/index.html", "src/tables/properties-for-dataset.html", "src/examples/example-minimum.ttl"} <= paths)
            # The ontology is a graph, not text; SHACL shapes are not indexed.
            self.assertFalse({"src/mobilitydcat-ap.ttl", "src/shacl/shapes.ttl"} & paths)
            self.assertTrue(all(c.standards_scope == ["mobilityDCAT-AP"] for c in chunks))
            table = chunks.get(source_path="src/tables/properties-for-dataset.html")
            self.assertEqual(table.heading, "Properties for dataset")
            self.assertIn("Card.: 0..1", table.text)
            self.assertEqual(chunks.get(source_path="src/examples/example-minimum.ttl").doc_type, "example")
            self.assertIn("Definition: A dataset is a collection of data.", chunks.get(source_path="src/tables/class-dataset.html").text)

            second = refresh_all_sources([source], checkout_root=root / "repos")
            self.assertEqual(second["results"]["mobilityDCAT-AP"]["ontology"]["status"], "unchanged")
            self.assertEqual(upload.call_count, 1)

            full = refresh_all_sources([source], checkout_root=root / "repos", full=True)
            self.assertEqual(full["results"]["mobilityDCAT-AP"]["ontology"]["status"], "loaded")
            self.assertEqual(upload.call_count, 2)

    @override_settings(GRAPHDB_ENABLED=False)
    def test_without_graphdb_the_text_is_still_indexed(self):
        with TemporaryDirectory() as tmp, patch("helpdesk.services.graphdb_client.upload_named_graph_turtle") as upload:
            root = Path(tmp)
            result = refresh_all_sources([self._source(make_mobilitydcat_remote(root))], checkout_root=root / "repos")
        row = result["results"]["mobilityDCAT-AP"]
        self.assertEqual((row["status"], row["ontology"]["status"]), ("ok", "skipped"))
        upload.assert_not_called()
        self.assertTrue(SourceChunk.objects.filter(repository_url=MDCAT_URL).exists())

    def test_a_missing_ontology_file_fails_the_row_after_indexing(self):
        with TemporaryDirectory() as tmp, patch("helpdesk.services.graphdb_client.upload_named_graph_turtle"):
            root = Path(tmp)
            remote = make_mobilitydcat_remote(root)
            (remote / "src" / "mobilitydcat-ap.ttl").unlink()
            _git(remote, "commit", "-qam", "drop ontology")
            result = refresh_all_sources([self._source(remote)], checkout_root=root / "repos")
        row = result["results"]["mobilityDCAT-AP"]
        self.assertEqual(row["status"], "failed")
        self.assertIn("src/mobilitydcat-ap.ttl", row["error"])
        self.assertTrue(SourceChunk.objects.filter(repository_url=MDCAT_URL).exists())


class HarvestTaskTests(SimpleTestCase):
    def test_the_task_refreshes_only_the_named_source_and_returns_failures(self):
        failed = {"status": "failed", "results": {"SIRI": {"status": "failed", "error": "x"}}}
        with patch("helpdesk.tasks.refresh_all_sources", return_value=failed) as refresh:
            self.assertEqual(harvest_source.apply(args=["SIRI"], kwargs={"full": True}).get(), failed)
        refresh.assert_called_once_with(only=["SIRI"], full=True)


class HarvestApiTests(APITestCase):
    _token = test_api.HelpdeskApiTests._token
    _normalized_openapi = test_api.HelpdeskApiTests._normalized_openapi
    assert_matches_schema = test_api.HelpdeskApiTests.assert_matches_schema

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(Path(__file__).resolve().parents[3] / "api" / "openapi.yaml", encoding="utf-8") as handle:
            cls.openapi = yaml.safe_load(handle)

    def _headers(self, roles):
        return {"HTTP_AUTHORIZATION": f"Bearer {self._token(roles=roles)}"}

    def test_harvesting_requires_admin_or_publisher(self):
        for method, name, kwargs in (
            ("get", "admin-sources", {}),
            ("post", "admin-sources-harvest", {}),
            ("get", "admin-sources-harvest-job", {"job_id": "j1"}),
        ):
            with self.subTest(endpoint=name):
                response = getattr(self.client, method)(reverse(name, kwargs=kwargs), **self._headers(["editor"]))
                self.assertEqual(response.status_code, 403)

    def test_sources_list_what_is_indexed_and_the_ontology_version(self):
        SourceChunk.objects.create(
            repository_url=MDCAT_URL, commit_sha="c" * 40, source_path="src/index.html", chunk_id="m1", text="t",
            standards_scope=["mobilityDCAT-AP"], embedding_vector=build_text_embedding("t"),
        )
        OntologyAssetVersion.objects.create(
            ontology_key="mobilitydcat-ap", file_path="f", graph_uri=MOBILITYDCAT_AP_ONTOLOGY.graph_uri,
            version="3.0.0", content_hash="h",
        )
        response = self.client.get(reverse("admin-sources"), **self._headers(["publisher"]))
        self.assertEqual(response.status_code, 200)
        self.assert_matches_schema("SourcesResponse", response.json())
        rows = {row["name"]: row for row in response.json()["sources"]}
        self.assertEqual(set(rows), {"NeTEx", "SIRI", "OpRa", "mobilityDCAT-AP"})
        row = rows["mobilityDCAT-AP"]
        self.assertEqual((row["indexedChunks"], row["indexedCommit"]), (1, "c" * 40))
        self.assertEqual((row["ontology"]["version"], row["ontology"]["lastLoadedAt"]), ("3.0.0", None))
        self.assertIsNone(rows["NeTEx"]["ontology"])

    def test_harvest_is_queued_for_a_configured_source_only(self):
        with patch("helpdesk.tasks.harvest_source.delay", return_value=SimpleNamespace(id="job-1")) as delay:
            response = self.client.post(
                reverse("admin-sources-harvest"), {"source": "mobilitydcat-ap", "full": True}, format="json",
                **self._headers(["admin"]),
            )
            self.assertEqual(response.status_code, 202)
            self.assert_matches_schema("HarvestSourceAccepted", response.json())
            delay.assert_called_once_with("mobilityDCAT-AP", full=True)

            response = self.client.post(reverse("admin-sources-harvest"), {"source": "GTFS"}, format="json", **self._headers(["admin"]))
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"]["code"], "UNKNOWN_SOURCE")
            self.assertEqual(delay.call_count, 1)

    def test_job_states_map_to_queued_running_finished_and_error(self):
        report = {"status": "ok", "results": {"mobilityDCAT-AP": {"status": "ok"}}}
        cases = [
            ("PENDING", None, "queued", None, None),
            ("STARTED", None, "running", None, None),
            ("SUCCESS", report, "finished", report, None),
            ("FAILURE", RuntimeError("boom"), "error", None, "boom"),
        ]
        for celery_state, celery_result, state, result, error in cases:
            with self.subTest(state=celery_state), patch(
                "celery.result.AsyncResult", return_value=SimpleNamespace(state=celery_state, result=celery_result)
            ):
                response = self.client.get(reverse("admin-sources-harvest-job", kwargs={"job_id": "job-1"}), **self._headers(["publisher"]))
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assert_matches_schema("HarvestJobResponse", payload)
                self.assertEqual((payload["state"], payload["result"], payload["error"]), (state, result, error))
