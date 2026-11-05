"""Tests for the DATEX II source (services/datex.py) and the opt-in scope rule it needs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import SourceChunk
from helpdesk.services import datex
from helpdesk.services.embeddings import build_text_embedding
from helpdesk.services.napcore_site import Snapshot
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.question_parsing import QuestionParsingService
from helpdesk.services.regulations import STANDARD_IDENTIFIERS
from helpdesk.services.retrieval_gateway import _scope_matches


def _model_file(path: Path) -> None:
    """A tiny Enterprise Architect model with the tables and columns extract_model reads."""
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
        CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Stereotype TEXT, Package_ID INTEGER,
                               Note TEXT, PDATA1 TEXT);
        CREATE TABLE t_objectproperties (Object_ID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_attribute (ID INTEGER, Object_ID INTEGER, Name TEXT, Type TEXT, LowerBound TEXT,
                                  UpperBound TEXT, Pos INTEGER);
        CREATE TABLE t_attributetag (ElementID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_connector (Connector_Type TEXT, Stereotype TEXT, Start_Object_ID INTEGER, End_Object_ID INTEGER,
                                  DestRole TEXT, DestCard TEXT, SourceRole TEXT, SourceCard TEXT);
        INSERT INTO t_package VALUES (1, 'DATEX2System', 0), (2, 'Situation', 1), (3, 'Classes', 2);
        INSERT INTO t_object VALUES
            (10, 'Situation', 'Package', 'D2Namespace', 1, '', '2'),
            (20, 'Roadworks', 'Class', 'D2Class', 3, '', NULL),
            (21, 'OperatorAction', 'Class', 'D2Class', 3, '', NULL),
            (22, 'RoadworksScaleEnum', 'Enumeration', 'D2Enumeration', 3, '', NULL),
            (23, 'Impact', 'Class', 'D2Class', 3, '', NULL);
        INSERT INTO t_objectproperties VALUES
            (20, 'definition', 'Road maintenance and construction activities.', NULL),
            (22, 'definition', 'Grade of complexity of the roadworks.', NULL);
        INSERT INTO t_attribute VALUES
            (100, 20, 'roadworksScale', 'RoadworksScaleEnum', '0', '1', 1),
            (101, 22, 'major', '', '', '', 1);
        INSERT INTO t_attributetag VALUES
            (100, 'definition', 'Grade of complexity of the roadworks.', NULL),
            (101, 'definition', 'The roadworks scale is major.', NULL);
        INSERT INTO t_connector VALUES
            ('Generalization', NULL, 20, 21, NULL, NULL, NULL, NULL),
            ('Aggregation', 'D2Relation', 20, 23, 'impact', '0..1', NULL, NULL);
        """
    )
    db.commit()
    db.close()


class ModelTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.qea"
            _model_file(path)
            cls.model = datex.extract_model(path)
        cls.by_name = {e["name"]: e for e in cls.model["elements"]}

    def test_elements_carry_namespace_definition_and_members(self):
        roadworks = self.by_name["Roadworks"]
        self.assertEqual((roadworks["namespace"], roadworks["package"]), ("Situation", "Classes"))
        self.assertEqual(roadworks["definition"], "Road maintenance and construction activities.")
        self.assertEqual(roadworks["supertypes"], ["OperatorAction"])
        self.assertEqual(roadworks["members"][0]["multiplicity"], "0..1")
        self.assertEqual(roadworks["associations"], [{"role": "impact", "target": "Impact", "multiplicity": "0..1"}])

    def test_element_text_lists_attributes_and_enumeration_values(self):
        text = datex.element_text(self.by_name["Roadworks"])
        self.assertTrue(text.startswith("DATEX II class Roadworks (namespace Situation / Classes)"))
        self.assertIn("- roadworksScale (RoadworksScaleEnum, 0..1): Grade of complexity of the roadworks.", text)
        self.assertIn("- impact -> Impact, 0..1", text)
        self.assertIn("Values:\n- major: The roadworks scale is major.", datex.element_text(self.by_name["RoadworksScaleEnum"]))

    def test_records_are_namespace_qualified_and_cite_the_release(self):
        record = next(r for r in datex.model_records(self.model) if "Roadworks" in r["chunk_id"] and "Enum" not in r["chunk_id"])
        self.assertEqual(record["source_path"], f"datex-model-v{datex.VERSION}/Situation.Roadworks")
        self.assertEqual(record["structured_metadata"]["sourceUrl"], datex.MODEL_PAGE_URL)
        self.assertEqual(datex.citation_title(record["source_path"]), f"DATEX II v{datex.VERSION} Roadworks (Situation)")

    def test_long_elements_are_split_with_their_head_line(self):
        element = dict(self.by_name["Roadworks"], members=[
            {"name": f"attribute{i}", "type": "String", "multiplicity": "0..1", "definition": "x" * 90} for i in range(40)
        ])
        records = datex.model_records({"version": datex.VERSION, "elements": [element]})
        self.assertGreater(len(records), 1)
        self.assertTrue(all(len(r["text"]) <= datex.MAX_CHUNK_CHARS * 2 for r in records))
        self.assertTrue(records[1]["text"].startswith("DATEX II class Roadworks (namespace Situation / Classes) (continued)"))

    def test_the_stored_model_parses(self):
        model = json.loads(datex.MODEL_PATH.read_text(encoding="utf-8"))
        self.assertGreater(len(model["elements"]), 1000)
        self.assertTrue(all(e["namespace"] for e in model["elements"]))


class PortalTests(SimpleTestCase):
    PAGE = """<html><nav>menu</nav><article class="md-content__inner md-typeset">
    <!-- theme licence comment -->
    <h1 id="x">Situation and SituationPublication<a class="headerlink">¶</a></h1>
    <p>A situation publication can group several situations.</p></article><footer>f</footer></html>"""

    def test_the_article_is_the_page_text(self):
        title, text = datex.page_text(self.PAGE)
        self.assertEqual(title, "Situation and SituationPublication")
        self.assertIn("A situation publication can group several situations.", text)
        self.assertNotIn("menu", text)
        self.assertNotIn("licence", text)

    def test_sitemap_pages_are_read_at_the_pinned_release(self):
        sitemap = b"<urlset><url><loc>https://docs.datex2.eu/levels/mastering/situation/</loc></url>" \
                  b"<url><loc>https://docs.datex2.eu/downloads/modelv37/</loc></url></urlset>"
        self.assertEqual(datex.sitemap_pages(sitemap), [f"https://docs.datex2.eu/v{datex.VERSION}/levels/mastering/situation/"])

    def test_page_records_cite_the_page(self):
        url = f"https://docs.datex2.eu/v{datex.VERSION}/levels/mastering/situation/"
        snapshot = Snapshot(url=url, title="Situation", text="## Situation\nA situation publication groups situations.")
        [record] = datex.page_records(snapshot)
        self.assertEqual(record["structured_metadata"]["sourceUrl"], url)
        self.assertTrue(record["text"].startswith(f"DATEX II v{datex.VERSION} documentation: Situation"))


class ScopeTests(SimpleTestCase):
    def test_a_question_naming_datex_gets_the_scope(self):
        scan = QuestionParsingService()._scan_standard_keywords
        for question in ("How does DATEX II model roadworks?", "What is a VMS in Datex2?", "CEN/TS 16157 parking"):
            with self.subTest(question=question):
                self.assertIn("DATEX II", scan(question))
        self.assertNotIn("DATEX II", scan("How does SIRI model roadworks?"))

    def test_opt_in_chunks_stay_out_of_unscoped_search_unless_they_belong_to_a_core_standard(self):
        self.assertFalse(_scope_matches(["DATEX II"], None))
        self.assertTrue(_scope_matches(["DATEX II", "SIRI"], None))  # SIRI's copy of the DATEX II schema
        self.assertTrue(_scope_matches(["DATEX II"], ["DATEX II"]))
        self.assertTrue(_scope_matches(["DATEX II", "SIRI"], ["DATEX II"]))
        self.assertFalse(_scope_matches(["EU legislation"], None))

    def test_acts_naming_datex_ii_are_recognised(self):
        self.assertIn("DATEX II", STANDARD_IDENTIFIERS)
        self.assertRegex("the data for which NeTEx and DATEX II are applicable", STANDARD_IDENTIFIERS["DATEX II"])

    def test_portal_citations_are_allowed(self):
        url = f"https://docs.datex2.eu/v{datex.VERSION}/levels/mastering/situation/"
        self.assertTrue(evaluate_policy("Answer.", [{"repositoryUrl": url}])["allowed"])
        self.assertTrue(evaluate_policy("Answer.", [{"repositoryUrl": datex.MODEL_PAGE_URL}])["allowed"])


@override_settings(EMBEDDING_BACKEND="hash")
class IndexDatexTests(TestCase):
    def test_index_unscoped_search_filter_and_stale_pages(self):
        from helpdesk.services.retrieval_gateway import _scope_query_filter

        with TemporaryDirectory() as tmp:
            qea, model_path, pages = Path(tmp) / "m.qea", Path(tmp) / "model.json", Path(tmp) / "pages"
            _model_file(qea)
            model_path.write_text(json.dumps(datex.extract_model(qea)), encoding="utf-8")
            pages.mkdir()
            page = pages / "situation.md"
            page.write_text(f"url: {datex.PORTAL}/v{datex.VERSION}/s/\ntitle: S\n\n## S\nA situation groups records.\n")
            first = datex.index_datex(model_path, pages)
            self.assertEqual((first["indexed"], first["unchanged"]), (2, 0))
            self.assertEqual(datex.index_datex(model_path, pages)["unchanged"], 2)
            page.unlink()
            self.assertEqual(datex.index_datex(model_path, pages)["removed"], 1)
        self.assertTrue(SourceChunk.objects.filter(doc_type="datex", heading__contains="Roadworks").exists())
        self.assertFalse(SourceChunk.objects.filter(doc_type="datex", label__contains="documentation").exists())
        SourceChunk.objects.create(
            repository_url="https://github.com/TransmodelEcosystem/SIRI", commit_sha="x", source_path="xsd/datex2/a.xsd",
            chunk_id="siri-datex", label="a", text="a", standards_scope=["DATEX II", "SIRI"], quality_score=0.5,
            embedding_vector=build_text_embedding("a"),
        )
        unscoped = SourceChunk.objects.filter(_scope_query_filter(None))
        self.assertTrue(unscoped.filter(chunk_id="siri-datex").exists())
        self.assertFalse(unscoped.filter(doc_type="datex").exists())


class ChunkIdTests(SimpleTestCase):
    def test_pages_whose_names_share_a_long_prefix_get_distinct_chunk_ids(self):
        base = f"https://docs.datex2.eu/v{datex.VERSION}/recommended-profiles/" + "x" * 120
        ids = {
            datex.page_records(Snapshot(url=f"{base}{suffix}/", title="T", text="## T\nSome text."))[0]["chunk_id"]
            for suffix in ("a", "b")
        }
        self.assertEqual(len(ids), 2)
        self.assertTrue(all(len(i) <= 128 for i in ids))
