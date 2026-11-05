"""Tests for the INSPIRE Transport Networks source (services/inspire.py)."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import SourceChunk
from helpdesk.services import inspire
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.question_parsing import QuestionParsingService

SPEC = """// comment line
:title: D2.8.I.7 Data Specification on Transport Networks – Technical Guidelines
= D2.8.I.7 Data Specification on _Transport Networks_ – Technical Guidelines

== Scope

This document specifies a harmonised data specification for the spatial data theme *Transport Networks*.footnote:[See Annex I of Directive 2007/2/EC.]

=== Feature catalogue

====== RoadLink

[cols="",options="header",]
|===
|*RoadLink*
a|
[cols=","]
!===
!Subtype of: !TransportLink
!Definition: !A linear spatial object that describes the geometry and connectivity of a road network between two points in the network.
!Stereotypes: !«featureType»
!===

|===

====== Tiny

Short.

====== RoadNode

NOTE: A point spatial object that is used to represent connectivity between two road links, see https://inspire.ec.europa.eu/codelist/FormOfRoadNodeValue[FormOfRoadNodeValue].
"""

REGISTRY_ENTRY = {
    "codelist": {
        "id": "http://inspire.ec.europa.eu/codelist/FormOfWayValue",
        "label": {"text": "Form Of Way", "lang": "en"},
        "definition": {"text": "Classification based on the physical properties of the road link.", "lang": "en"},
        "containeditems": [
            {
                "value": {
                    "id": "http://inspire.ec.europa.eu/codelist/FormOfWayValue/bicycleRoad",
                    "label": {"text": "bicycle road"},
                    "definition": {"text": "Road where bicycles are the only vehicles allowed."},
                }
            }
        ],
    }
}


class ParseSpecTests(SimpleTestCase):
    def setUp(self):
        self.sections = inspire.parse_spec(SPEC)
        self.by_name = {s.path[-1]: s for s in self.sections}

    def test_sections_follow_the_headings_and_remember_their_line(self):
        road_link = self.by_name["RoadLink"]
        self.assertEqual(road_link.path[1:], ("Scope", "Feature catalogue", "RoadLink"))
        self.assertEqual(SPEC.splitlines()[road_link.line - 1], "====== RoadLink")

    def test_tables_become_key_value_lines(self):
        text = self.by_name["RoadLink"].text
        self.assertIn("Subtype of: TransportLink", text)
        self.assertIn("Definition: A linear spatial object", text)
        self.assertNotIn("!===", text)
        self.assertNotIn("[cols", text)

    def test_inline_markup_is_reduced_to_text(self):
        scope = self.by_name["Scope"].text
        self.assertIn("Transport Networks.", scope)
        self.assertIn("(See Annex I of Directive 2007/2/EC.)", scope)
        self.assertNotIn("*", scope)
        self.assertIn("Note: A point spatial object", self.by_name["RoadNode"].text)
        self.assertIn("FormOfRoadNodeValue", self.by_name["RoadNode"].text)

    def test_short_sections_join_the_next_chunk(self):
        chunks = inspire.spec_chunks(self.sections)
        road_node = next(text for heading, text, _ in chunks if heading.endswith("RoadNode"))
        self.assertTrue(road_node.startswith("Tiny: Short."))

    def test_records_cite_the_line_on_github_at_the_pinned_tag(self):
        record = next(r for r in inspire.spec_records(SPEC) if r["heading"].endswith("RoadLink"))
        line = record["source_path"].rsplit("#L", 1)[1]
        self.assertEqual(
            record["structured_metadata"]["sourceUrl"],
            f"https://github.com/INSPIRE-MIF/technical-guidelines/blob/{inspire.SPEC_TAG}/data/tn/"
            f"dataspecification_tn.adoc?plain=1#L{line}",
        )
        self.assertTrue(record["text"].startswith(inspire.SPEC_TITLE))

    def test_code_lists_are_found_in_the_links(self):
        self.assertEqual(inspire.codelist_names(SPEC), ["FormOfRoadNodeValue"])


class CodelistTests(SimpleTestCase):
    def test_registry_entry_is_compacted_and_chunked_with_its_values(self):
        compact = inspire.compact_codelist("FormOfWayValue", REGISTRY_ENTRY)
        self.assertEqual(compact["label"], "Form Of Way")
        self.assertEqual(compact["values"][0]["definition"], "Road where bicycles are the only vehicles allowed.")
        [record] = inspire.codelist_records([compact])
        self.assertIn("- bicycleRoad (bicycle road): Road where bicycles are the only vehicles allowed.", record["text"])
        self.assertEqual(record["structured_metadata"]["sourceUrl"], "https://inspire.ec.europa.eu/codelist/FormOfWayValue")
        self.assertEqual(inspire.citation_title(record["source_path"]), "INSPIRE code list: FormOfWayValue")

    def test_the_stored_files_parse(self):
        self.assertGreater(len(inspire.spec_records(inspire.SPEC_PATH.read_text(encoding="utf-8"))), 300)
        self.assertGreater(len(inspire.read_codelists()), 20)


class ScopeAndPolicyTests(SimpleTestCase):
    def test_a_question_naming_inspire_gets_the_scope(self):
        scan = QuestionParsingService()._scan_standard_keywords
        self.assertIn("INSPIRE", scan("How does INSPIRE model a road link?"))
        # The Directive's name names the act, not the specification.
        for question in ("What does the INSPIRE Directive require?", "Welche Netzdienste verlangt die INSPIRE-Richtlinie?",
                         "Kaj zahteva direktiva INSPIRE?"):
            with self.subTest(question=question):
                self.assertNotIn("INSPIRE", scan(question))
        self.assertIn("INSPIRE", scan("Does the INSPIRE Directive require the INSPIRE road link model?"))
        self.assertNotIn("INSPIRE", scan("How does NeTEx model a stop place?"))

    def test_citations_of_the_pinned_spec_and_registry_are_allowed(self):
        for url in (inspire.spec_url(12), "https://inspire.ec.europa.eu/codelist/FormOfWayValue"):
            with self.subTest(url=url):
                self.assertTrue(inspire.is_inspire_url(url))
                self.assertTrue(evaluate_policy("Answer.", [{"repositoryUrl": url}])["allowed"])
        self.assertFalse(inspire.is_inspire_url("https://github.com/INSPIRE-MIF/technical-guidelines/blob/main/x.adoc"))


@override_settings(EMBEDDING_BACKEND="hash")
class IndexInspireTests(TestCase):
    def test_index_is_skipped_when_unchanged_and_replaced_when_changed(self):
        with TemporaryDirectory() as tmp:
            spec, codelists = Path(tmp) / "dataspecification_tn.adoc", Path(tmp) / "codelists.json"
            spec.write_text(SPEC, encoding="utf-8")
            compact = inspire.compact_codelist("FormOfWayValue", REGISTRY_ENTRY)
            codelists.write_text(json.dumps({"codelists": [compact]}), encoding="utf-8")
            first = inspire.index_inspire(spec, codelists)
            self.assertEqual(first["spec"][0], "indexed")
            self.assertEqual(first["codelists"], ("indexed", 1))
            self.assertEqual(inspire.index_inspire(spec, codelists)["spec"][0], "unchanged")
            spec.write_text(SPEC.replace("RoadNode", "RailwayNode"), encoding="utf-8")
            self.assertEqual(inspire.index_inspire(spec, codelists)["spec"][0], "indexed")
        chunks = SourceChunk.objects.filter(standards_scope__contains=["INSPIRE"])
        self.assertTrue(chunks.filter(heading__endswith="RailwayNode").exists())
        self.assertFalse(chunks.filter(heading__endswith="RoadNode").exists())
        self.assertTrue(all(c.doc_type == "inspire" for c in chunks))
