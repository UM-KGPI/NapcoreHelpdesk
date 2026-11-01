"""EU legislation as a retrieval source (issue #91)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import SourceChunk
from helpdesk.services.llm_generator import (
    LEGISLATION_RULE,
    _append_feedback_message,
    _build_messages,
    _regulation_citation_grounded,
)
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.question_parsing import parse_question_to_semantic_query
from helpdesk.services.regulations import ACTS, SCOPE, Act, _chunk_records, index_act, is_regulation_url, parse_act
from helpdesk.services.retrieval_gateway import _scope_matches

XHTML = b"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<div id="tit_1"><p>COMMISSION DELEGATED REGULATION (EU) 2017/1926</p></div>
<div id="rct_1"><p>(1) Recital one explains the purpose.</p></div>
<div id="rct_2"><p>(2) Recital two adds context.</p></div>
<div class="eli-subdivision" id="art_2">
  <p class="title-article-norm">Article 2</p>
  <div class="eli-title" id="art_2.tit_1"><p class="stitle-article-norm">Definitions</p></div>
  <div class="norm">The following definitions shall apply:
    <div class="grid-container grid-list">
      <div class="list grid-list-column-1"><p>(1)</p></div>
      <div class="grid-list-column-2"><p>&#8216;national access point&#8217; means a digital interface;</p></div>
    </div>
  </div>
  <p class="modref">&#9660;M1</p>
</div>
<div id="anx_1">
  <p class="title-gr-seq-level-1">1. STATIC DATA</p>
  <p class="norm">Location search.</p>
  <p class="title-gr-seq-level-1">2. DYNAMIC DATA</p>
  <p class="norm">Disruptions.</p>
</div>
<div id="app_C">
  <p class="oj-ti-grseq-1">C.4.A List of referenced standards</p>
  <table><tr><td><p>[P.1]</p></td><td><p>CEN/TS 16614-1:2025</p><p>NeTEx Part 1</p></td><td><p>4.9</p></td></tr></table>
</div>
</body></html>"""

ACT = Act("02017R1926-20240304", "Delegated Regulation (EU) 2017/1926 (MMTIS)", "consolidated", 0.9)


class ParseActTests(SimpleTestCase):
    def setUp(self):
        self.sections = {(s.anchor, s.heading): s.text for s in parse_act(XHTML)}

    def test_article_has_its_title_and_list_labels_joined_to_their_text(self):
        text = self.sections[("art_2", "Article 2 — Definitions")]
        self.assertIn("(1) ‘national access point’ means a digital interface;", text)
        self.assertNotIn("Definitions", text)  # the subtitle is the heading, not body text

    def test_consolidation_markers_are_dropped(self):
        self.assertNotIn("▼", " ".join(self.sections.values()))

    def test_annex_is_split_at_its_headings(self):
        self.assertIn(("anx_1", "Annex — 1. STATIC DATA"), self.sections)
        self.assertIn(("anx_1", "Annex — 2. DYNAMIC DATA"), self.sections)

    def test_appendix_table_rows_stay_one_line(self):
        text = self.sections[("app_C", "Appendix C — C.4.A List of referenced standards")]
        self.assertIn("[P.1] | CEN/TS 16614-1:2025 NeTEx Part 1 | 4.9", text)

    def test_recitals_are_grouped_and_linked_to_the_first(self):
        self.assertIn("Recital two", self.sections[("rct_1", "Recitals")])

    def test_chunk_links_to_the_article_on_eurlex(self):
        records = _chunk_records(ACT, parse_act(XHTML))
        article = next(r for r in records if r["source_path"] == "02017R1926-20240304#art_2")
        self.assertEqual(
            article["structured_metadata"]["sourceUrl"],
            "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02017R1926-20240304#art_2",
        )
        self.assertTrue(article["text"].startswith("Delegated Regulation (EU) 2017/1926 (MMTIS)\nArticle 2"))
        recitals = next(r for r in records if r["heading"] == "Recitals")
        self.assertEqual(recitals["quality_score"], 0.5)

    def test_every_pinned_act_file_parses(self):
        for act in ACTS:
            with self.subTest(act=act.celex):
                self.assertTrue(any(s.anchor.startswith("art_") for s in parse_act(act.path.read_bytes())))


@override_settings(EMBEDDING_BACKEND="hash")
class IndexActTests(TestCase):
    def test_index_is_skipped_when_the_file_is_unchanged(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{ACT.celex}.xhtml"
            path.write_bytes(XHTML)
            with patch.object(Act, "path", property(lambda self: path)):
                status, count = index_act(ACT)
                self.assertEqual(status, "indexed")
                self.assertEqual(SourceChunk.objects.filter(repository_url=ACT.url).count(), count)
                self.assertEqual(index_act(ACT)[0], "unchanged")
                with patch("helpdesk.services.regulations.PARSER_VERSION", "test-next"):
                    self.assertEqual(index_act(ACT)[0], "indexed")

        chunk = SourceChunk.objects.get(source_path=f"{ACT.celex}#art_2")
        self.assertEqual(chunk.standards_scope, [SCOPE])
        self.assertEqual(chunk.source_url, f"{ACT.url}#art_2")


class LegislationScopeTests(SimpleTestCase):
    def test_questions_naming_an_act_get_the_legislation_scope(self):
        for question in [
            "What is a NAP?",
            "kakšna je vloga nap kot metapodatkovnega imenika?",
            "Which standard does the TEL TSI require for fares?",
            "Was verlangt die Verordnung 2017/1926?",
        ]:
            with self.subTest(question=question):
                self.assertIn(SCOPE, parse_question_to_semantic_query(question).candidate_standards)

    def test_standards_questions_do_not(self):
        for question in ["What is a legal entity in NeTEx?", "How does SIRI use NeTEx?", "Kaj je vozni red?"]:
            with self.subTest(question=question):
                self.assertNotIn(SCOPE, parse_question_to_semantic_query(question).candidate_standards)

    def test_legislation_is_searched_only_when_the_scope_names_it(self):
        self.assertFalse(_scope_matches([SCOPE], None))
        self.assertFalse(_scope_matches([SCOPE], ["NeTEx"]))
        self.assertTrue(_scope_matches([SCOPE], ["NeTEx", SCOPE]))
        self.assertTrue(_scope_matches(["NeTEx"], None))


ARTICLE_3 = {
    "repositoryUrl": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02017R1926-20240304",
    "commitSha": "02017R1926-20240304",
    "chunkId": "reg-02017R1926-20240304-0003",
    "docType": "regulation",
    "sourcePath": "02017R1926-20240304#art_3",
    "text": (
        "Delegated Regulation (EU) 2017/1926 (MMTIS)\nArticle 3 — National access point\n\n"
        "1. Each Member State shall set up a national access point (NAP). It shall constitute a single point "
        "of access for users to the static travel data. 4. National access points shall provide discovery "
        "services to data users. The ITS services use them."
    ),
}


class LegislationAnswerTests(SimpleTestCase):
    def test_grounded_sentences(self):
        for sentence in [
            "Additionally, national access points shall provide discovery services to data users.",
            "Nach Artikel 3 muss jeder Mitgliedstaat einen nationalen Zugangspunkt einrichten.",
            'It is "a single point of access for users".',
            "NAP podpira storitve ITS.",  # acronyms survive translation
        ]:
            with self.subTest(sentence=sentence):
                self.assertTrue(_regulation_citation_grounded(sentence, ARTICLE_3))

    def test_ungrounded_sentences(self):
        for sentence in [
            "Gemäß Artikel 7 gelten Fristen bis 2030.",  # wrong article
            "A NAP must be certified by ISO before 2030 and audited yearly by Brussels.",
            "Die MMTIS-Verordnung 2017/1926 wurde geändert.",  # the act's own name heads every chunk
        ]:
            with self.subTest(sentence=sentence):
                self.assertFalse(_regulation_citation_grounded(sentence, ARTICLE_3))

    def test_prompt_has_the_legislation_rule_only_with_legislation_evidence(self):
        standards_chunk = {
            "text": "<Line/>",
            "docType": "example",
            "sourcePath": "a.xml",
            "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
            "commitSha": "abc",
            "chunkId": "c1",
        }
        with_law = _build_messages(question="What is a NAP?", chunks=[ARTICLE_3])[0]["content"]
        without = _build_messages(question="What is a Line?", chunks=[standards_chunk])[0]["content"]
        self.assertIn(LEGISLATION_RULE, with_law)
        self.assertNotIn(LEGISLATION_RULE, without)

    def test_retry_feedback_asks_for_articles_not_xml(self):
        feedback = _append_feedback_message([], "rejected", "reason", legislation=True)[-1]["content"]
        self.assertIn("article", feedback)
        self.assertNotIn("<DepartureTime>", feedback)


class LegislationPolicyTests(SimpleTestCase):
    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_policy_accepts_the_pinned_acts_only(self):
        self.assertTrue(is_regulation_url(f"{ACTS[0].url}#art_4"))
        self.assertTrue(evaluate_policy("Answer.", [{"repositoryUrl": f"{ACTS[0].url}#art_4"}])["allowed"])
        other = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679#art_1"
        self.assertFalse(evaluate_policy("Answer.", [{"repositoryUrl": other}])["allowed"])
