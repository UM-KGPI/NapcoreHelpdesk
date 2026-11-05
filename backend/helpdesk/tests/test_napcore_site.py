"""napcore.eu as the NAPCORE retrieval source (services/napcore_site.py)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import SourceChunk
from helpdesk.services import napcore_site
from helpdesk.services.llm_generator import LLMGenerationError, _validate_citation_grounding
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.question_parsing import (
    asks_for_named_standards,
    parse_question_to_semantic_query,
    standards_named_in_legislation_question,
)

PAGE = """url: https://napcore.eu/
title: About NAPCORE
modified: 2026-06-05T11:58:07

#### The world's largest cooperation of mobility data platforms
#### NAPCORE (National Access Point Coordination Organisation for Europe) coordinates more than 30 mobility data platforms.
The ITS Directive requires each Member State to establish a National Access Point.
"""

PDF = """url: https://napcore.eu/wp-content/uploads/2025/11/Guidelines-Compliance-Assessment_v3.pdf
title: Guidelines Compliance Assessment v3

[page 1]
Guidelines for Compliance Assessment
[page 2]
The National Body prepares national templates for self-declarations.
"""


class HtmlToTextTests(SimpleTestCase):
    def test_headings_lists_and_tables(self):
        text = napcore_site.html_to_text(
            "<h2>Quality</h2><p>NAPCORE <a href='#'>quality</a> frameworks.</p><ul><li>Parking</li><li>UVAR</li></ul>"
            "<table><tr><td>MMTIS</td><td>2017/1926</td></tr></table><script>var x=1;</script>"
        )
        self.assertEqual(text, "### Quality\nNAPCORE quality frameworks.\n- Parking\n- UVAR\nMMTIS | 2017/1926")


class ChunkTests(SimpleTestCase):
    def snapshot(self, text):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(text, encoding="utf-8")
            return napcore_site.read_snapshot(path)

    def test_text_in_headings_is_kept(self):
        records = napcore_site.chunk_records(self.snapshot(PAGE))
        self.assertEqual(len(records), 1)
        self.assertIn("coordinates more than 30 mobility data platforms", records[0]["text"])
        self.assertTrue(records[0]["text"].startswith("NAPCORE (napcore.eu): About NAPCORE"))
        self.assertEqual(records[0]["structured_metadata"]["sourceUrl"], "https://napcore.eu/")
        self.assertEqual(records[0]["source_path"], "napcore.eu/")
        self.assertEqual(records[0]["quality_score"], 0.85)

    def test_pdf_chunks_link_to_their_page(self):
        long_pdf = PDF + "\n".join(f"[page {n}]\n" + "Compliance assessment text. " * 30 for n in range(3, 6))
        records = napcore_site.chunk_records(self.snapshot(long_pdf))
        self.assertGreater(len(records), 1)
        self.assertTrue(records[0]["structured_metadata"]["sourceUrl"].endswith(".pdf#page=1"))
        self.assertTrue(records[-1]["structured_metadata"]["sourceUrl"].endswith("#page=5"))
        self.assertEqual(records[0]["quality_score"], 0.75)
        self.assertEqual(len({r["chunk_id"] for r in records}), len(records))

    def test_long_names_get_distinct_chunk_ids(self):
        base = "url: https://napcore.eu/wp-content/uploads/2022/08/NAPCORE-4.4.2.2-Approach-towards-napDCAT-AP-specification_v1.0-{}.pdf\ntitle: x\n\ntext"
        report = napcore_site.chunk_records(self.snapshot(base.format("Report")))
        roadmap = napcore_site.chunk_records(self.snapshot(base.format("Roadmap")))
        self.assertNotEqual(report[0]["chunk_id"], roadmap[0]["chunk_id"])

    def test_pdf_line_end_hyphens_are_joined(self):
        self.assertEqual(napcore_site.dehyphenate("national tem-\nplates; DATEX-\nII"), "national templates; DATEX-\nII")

    def test_a_pdf_and_a_post_with_the_same_name_do_not_collide(self):
        post = napcore_site.Document("https://napcore.eu/napcore-position-paper-mmtis/")
        pdf = napcore_site.Document("https://napcore.eu/wp-content/uploads/2024/02/NAPCORE-Position-paper-MMTIS.pdf")
        self.assertNotEqual(post.path.name.lower(), pdf.path.name.lower())


@override_settings(EMBEDDING_BACKEND="hash")
class IndexSiteTests(TestCase):
    def test_index_skip_unchanged_and_remove_missing(self):
        with TemporaryDirectory() as tmp:
            text_dir = Path(tmp)
            (text_dir / "home.md").write_text(PAGE, encoding="utf-8")
            (text_dir / "guidelines.pdf.md").write_text(PDF, encoding="utf-8")
            first = napcore_site.index_site(text_dir)
            self.assertEqual(first["indexed"], 2)
            self.assertTrue(SourceChunk.objects.filter(doc_type="napcore", standards_scope__contains=["NAPCORE"]).exists())
            self.assertEqual(napcore_site.index_site(text_dir)["unchanged"], 2)
            (text_dir / "guidelines.pdf.md").unlink()
            third = napcore_site.index_site(text_dir)
            self.assertEqual(third["removed"], 1)
            self.assertFalse(SourceChunk.objects.filter(repository_url__endswith=".pdf").exists())


class ScopeTests(SimpleTestCase):
    def scope(self, question):
        return parse_question_to_semantic_query(question).candidate_standards

    def test_napcore_questions_get_the_napcore_scope(self):
        self.assertIn("NAPCORE", self.scope("What is NAPCORE?"))
        self.assertIn("NAPCORE", self.scope("How should a National Body carry out compliance assessment?"))
        self.assertIn("NAPCORE", self.scope("Kakšna je vloga NAP kot imenika metapodatkov?"))

    def test_a_term_the_acts_define_still_gets_the_legislation(self):
        scope = self.scope("What is a national access point?")
        self.assertIn("NAPCORE", scope)
        self.assertIn("EU legislation", scope)

    def test_napcore_is_not_a_standard_for_the_legislation_rules(self):
        self.assertTrue(asks_for_named_standards("Which standards must NAPs use under the MMTIS regulation?", ["EU legislation"]))
        self.assertEqual(standards_named_in_legislation_question("Does MMTIS require NAPs?", ["EU legislation"]), [])

    def test_standards_questions_do_not(self):
        self.assertNotIn("NAPCORE", self.scope("What is a ScheduledStopPoint in NeTEx?"))
        self.assertNotIn("NAPCORE", self.scope("Show a snapshot of a SIRI message"))


class CitationTests(SimpleTestCase):
    def test_napcore_links_are_approved(self):
        self.assertTrue(napcore_site.is_napcore_url("https://napcore.eu/quality/"))
        self.assertTrue(napcore_site.is_napcore_url("https://www.napcore.eu/documents/D5.1.1_Final_NAP_data_insights.pdf#page=3"))
        self.assertFalse(napcore_site.is_napcore_url("https://napcore.eu.example.com/"))
        decision = evaluate_policy(
            answer_text="NAPCORE coordinates the NAPs [E1].",
            citations=[{"repositoryUrl": "https://napcore.eu/", "sourcePath": "napcore.eu/"}],
        )
        self.assertTrue(decision["allowed"], decision)

    def test_citation_titles(self):
        self.assertEqual(napcore_site.citation_title("02017R1926-20240304#art_4"), "")
        self.assertTrue(napcore_site.citation_title("napcore.eu/quality").startswith("NAPCORE: "))


GUIDELINES = {
    "text": "NAPCORE (napcore.eu): Guidelines Compliance Assessment v3\n\nThe National Body prepares national templates "
    "for self-declarations and accompanying documents and a repository for storing the submitted documents.",
    "sourcePath": "napcore.eu/wp-content/uploads/2025/11/Guidelines-Compliance-Assessment_v3.pdf",
    "docType": "napcore",
    "heading": "Guidelines Compliance Assessment v3",
}
TEL_TSI_APP_C = {
    "text": "Implementing Regulation (EU) 2026/253 (TEL TSI)\nAppendix C\n\n[P.7] EN 12896-1:2016 Public transport – Reference data model",
    "sourcePath": "32026R0253#app_C",
    "docType": "regulation",
    "heading": "Appendix C — C.4.A List of referenced standards",
}


class ProseGroundingTests(SimpleTestCase):
    def test_a_napcore_passage_is_grounded_by_its_wording(self):
        _validate_citation_grounding(
            "According to the guidelines, the National Body prepares national templates for self-declarations [E1].",
            [GUIDELINES],
        )

    def test_a_claim_the_napcore_block_does_not_make_is_rejected(self):
        with self.assertRaisesRegex(LLMGenerationError, "NAPCORE document"):
            _validate_citation_grounding("Fines of 10,000 euro apply to late submitters [E1].", [GUIDELINES])

    def test_a_sentence_about_what_a_prose_block_does_not_say_passes(self):
        # Prod 0.97.83: both attempts were rejected with "name that article with its own number".
        _validate_citation_grounding("The cited text in [E1] does not describe Transmodel.", [TEL_TSI_APP_C])
