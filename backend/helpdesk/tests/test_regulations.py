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
from helpdesk.services.question_parsing import (
    _legislation_term_covers,
    asks_for_named_standards,
    legal_status_standards,
    legislation_terms_in,
    named_acts,
    names_indexed_act,
    parse_question_to_semantic_query,
    standards_named_in_legislation_question,
)
from helpdesk.services.regulations import (
    ACTS,
    SCOPE,
    VOCABULARY_PATH,
    Act,
    _chunk_records,
    build_vocabulary,
    citation_title,
    extract_definitions,
    extract_provisions,
    index_act,
    is_regulation_url,
    legal_context,
    Section,
    parse_act,
    provisions_naming,
    render_provisions,
    render_vocabulary,
    select_sections,
    vocabulary_terms,
)
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


INSPIRE_DIRECTIVE = next(act for act in ACTS if act.celex.startswith("02007L0002"))
INSPIRE_REGULATION = next(act for act in ACTS if act.celex.startswith("02010R1089"))


class AnnexSectionTests(SimpleTestCase):
    """Only the configured annex sections of a broad act are indexed (INSPIRE: Transport Networks)."""

    SECTIONS = [
        Section("art_1", "Article 1 — Subject Matter and Scope", "a"),
        Section("rct_1", "Recitals", "b"),
        Section("anx_I", "Annex — 2. COMMON DATA TYPES", "c"),
        Section("anx_II", "Annex — 6. HYDROGRAPHY", "d"),
        Section("anx_II", "Annex — 7. TRANSPORT NETWORKS", "e"),
        Section("anx_II", "Annex — 7.2. Structure of the Spatial Data Theme Transport Networks", "f"),
        Section("anx_II", "Annex — 17. NOT TRANSPORT", "g"),
        Section("anx_IV", "Annex — 7.1. Elsewhere", "h"),
    ]

    def test_articles_recitals_and_listed_sections_are_kept(self):
        act = Act("x", "x", "consolidated", 0.8, annex_sections=(("anx_II", "7."),))
        self.assertEqual([s.text for s in select_sections(act, self.SECTIONS)], ["a", "b", "e", "f"])

    def test_without_a_selection_everything_is_kept(self):
        self.assertEqual(select_sections(ACTS[0], self.SECTIONS), self.SECTIONS)

    def test_inspire_regulation_keeps_only_transport_networks_from_its_annexes(self):
        sections = select_sections(INSPIRE_REGULATION, parse_act(INSPIRE_REGULATION.path.read_bytes()))
        annex = [s for s in sections if s.anchor.startswith("anx_")]
        self.assertTrue(annex)
        self.assertTrue(all(s.anchor == "anx_II" and s.heading.startswith("Annex — 7.") for s in annex))
        self.assertTrue(any("Transport" in s.text for s in annex))
        self.assertTrue(any(s.anchor == "art_7" for s in sections))
        self.assertLess(len(sections), 300)  # the whole act parses into ~1,800 sections

    def test_inspire_acts_are_named_by_name_and_number(self):
        self.assertIn(INSPIRE_DIRECTIVE.celex, named_acts("What does Article 7 of the INSPIRE Directive require?"))
        self.assertIn(INSPIRE_DIRECTIVE.celex, named_acts("Which data does Directive 2007/2/EC cover?"))
        self.assertIn(INSPIRE_REGULATION.celex, named_acts("What does Regulation 1089/2010 say about road links?"))
        self.assertNotIn(INSPIRE_DIRECTIVE.celex, named_acts("Which standards does the MMTIS regulation name?"))


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
            # a verbatim quote under the wrong article number (the paragraph number taken for the article)
            'Člen 4(4) določa: "National access points shall provide discovery services to data users".',
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

    def test_prompt_keeps_a_legislation_chunk_whole(self):
        # Art. 4 of MMTIS is ~1,700 characters; a 1,200 cut dropped (c) INSPIRE and paragraph 2.
        tail = (
            "(c) for the spatial network the requirements set out in Article 7 of Directive 2007/2/EC.\n"
            "2. The static, historic and observed travel and traffic data listed in point 1 of the Annex, for "
            "which NeTEx and DATEX II are applicable, shall be represented through minimum EU profiles."
        )
        article_4 = {**ARTICLE_3, "sourcePath": "02017R1926-20240304#art_4", "text": "x" * 1400 + "\n" + tail}
        standards_chunk = {**article_4, "docType": "documentation", "sourcePath": "README.md"}
        content = _build_messages(question="Which standards?", chunks=[article_4], max_chars_per_chunk=1200)[1]["content"]
        self.assertIn("Directive 2007/2/EC", content)
        self.assertIn("minimum EU profiles", content)
        content = _build_messages(question="Which standards?", chunks=[standards_chunk], max_chars_per_chunk=1200)[1]["content"]
        self.assertNotIn("Directive 2007/2/EC", content)

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


DEFINITIONS_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<div id="art_2"><p class="title-article-norm">Article 2</p>
  <p>(1) &#8216;data holder&#8217; means a body that holds data;</p>
  <p>(2) &#8216;Intelligent Transport Systems&#8217; or &#8216;ITS&#8217; means systems;</p>
  <p>(3) &#8216;rail ticketing&#8217; means the process comprising the following:</p>
  <p>(a) booking;</p>
  <p>(4) &#8216;journey&#8217; means a trip;</p>
</div></body></html>""".encode()


class LegislationVocabularyTests(SimpleTestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        path = Path(self._dir.name) / "act.xhtml"
        path.write_bytes(DEFINITIONS_XHTML)
        self.patcher = patch.object(Act, "path", property(lambda self: path))
        self.patcher.start()
        self.definitions = extract_definitions(ACT, "MMTIS")

    def tearDown(self):
        self.patcher.stop()
        self._dir.cleanup()

    def test_definitions_with_other_names_and_continued_lists(self):
        by_term = {d.labels[0]: d for d in self.definitions}
        self.assertEqual(by_term["Intelligent Transport Systems"].labels, ["Intelligent Transport Systems", "ITS"])
        self.assertTrue(by_term["rail ticketing"].text.endswith("the following: (a) booking;"))
        self.assertEqual(by_term["data holder"].text, "means a body that holds data;")

    def test_scope_terms_skip_shared_and_single_words(self):
        with TemporaryDirectory() as tmp:
            vocabulary = Path(tmp) / "vocabulary.ttl"
            vocabulary.write_text(render_vocabulary(self.definitions, {"rail ticketing"}), encoding="utf-8")
            terms = vocabulary_terms(vocabulary)
        self.assertIn("data holder", terms)
        self.assertIn("ITS", terms)  # an acronym counts
        self.assertNotIn("rail ticketing", terms)  # shared with a standards label
        self.assertNotIn("journey", terms)  # a single ordinary word does not set the scope


class StoredVocabularyTests(SimpleTestCase):
    def test_the_stored_vocabulary_is_generated_from_the_stored_acts(self):
        text, _, _ = build_vocabulary()
        self.assertEqual(VOCABULARY_PATH.read_text(encoding="utf-8"), text, "run build_legislation_vocabulary")


class LegislationTermScopeTests(SimpleTestCase):
    def test_defined_terms_are_found(self):
        self.assertEqual(legislation_terms_in("Who is a data holder?"), ["data holder"])
        self.assertEqual(legislation_terms_in("What does ITS mean?"), ["ITS"])
        self.assertEqual(legislation_terms_in("kakšna je vloga nap?"), ["nap"])  # acronyms in any case
        self.assertEqual(legislation_terms_in("Is its value correct?"), [])  # unless a function word

    def test_the_term_must_cover_every_span_the_standards_concepts_matched(self):
        aliases = {"tm:TRAVEL": {"travel"}, "nx:Service": {"service"}, "tm:linkedTo": {"linked to"}}
        with patch("helpdesk.services.question_parsing.GRAPH_CONCEPT_ALIASES", aliases):
            self.assertTrue(_legislation_term_covers("What is static travel data?", ["tm:TRAVEL"]))
            # a concept matched on a word inside the term, as on prod for "service"
            self.assertTrue(_legislation_term_covers("What is a travel information service?", ["tm:TRAVEL", "nx:Service"]))
            self.assertTrue(_legislation_term_covers("Who is a data holder?", []))
            self.assertFalse(
                _legislation_term_covers("How are transport operators linked to lines?", ["tm:linkedTo"])
            )
            self.assertFalse(_legislation_term_covers("What is a cancelled journey?", []))  # no defined term

    def test_a_named_standard_keeps_the_question_with_the_standard(self):
        self.assertEqual(
            parse_question_to_semantic_query("Show example for transport operator in NeTEx.").candidate_standards,
            ["NeTEx"],
        )

    def test_acts_are_recognised_by_their_names_and_numbers_from_the_act_list(self):
        for question in ["What does MMTIS require?", "TEL-TSI fares", "the ITS Directive", "Verordnung 2017/1926"]:
            with self.subTest(question=question):
                self.assertTrue(names_indexed_act(question))
        self.assertFalse(names_indexed_act("Is there an API for NeTEx?"))  # a defined term, not an act


PROVISIONS_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<div id="art_4"><p class="title-article-norm">Article 4</p><p>(i) NeTEx CEN/TS 16614 and subsequent versions;</p></div>
<div id="art_5"><p class="title-article-norm">Article 5</p><p>(i) SIRI CEN/TS 15531 and subsequent versions;</p></div>
<div id="art_6"><p class="title-article-norm">Article 6</p><p>Data updates.</p></div>
</body></html>""".encode()


class ProvisionLinkTests(SimpleTestCase):
    def test_provisions_that_name_a_standard_are_linked_to_it(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "act.xhtml"
            path.write_bytes(PROVISIONS_XHTML)
            act = Act(ACTS[0].celex, ACTS[0].name, "consolidated", 0.9)
            with patch.object(Act, "path", property(lambda self: path)), patch(
                "helpdesk.services.regulations.ACTS", (act,)
            ):
                provisions = extract_provisions()
            vocabulary = Path(tmp) / "vocabulary.ttl"
            vocabulary.write_text(render_provisions(provisions), encoding="utf-8")
            self.assertEqual(provisions_naming("NeTEx", vocabulary), [f"{act.celex}#art_4"])
            self.assertEqual(provisions_naming("SIRI", vocabulary), [f"{act.celex}#art_5"])
            self.assertEqual(provisions_naming("OpRa", vocabulary), [])


class LegalStatusQuestionTests(SimpleTestCase):
    aliases = {"tm:STOP_PLACE": {"stop place", "StopPlace"}, "tm:requiredBy": {"required by"}}

    def check(self, question, scope):
        with patch("helpdesk.services.question_parsing.GRAPH_CONCEPT_ALIASES", self.aliases):
            concepts = [c for c, names in self.aliases.items() if any(n.lower() in question.lower() for n in names)]
            return legal_status_standards(question, concepts, scope)

    def test_questions_about_a_standards_legal_status(self):
        self.assertEqual(self.check("Is NeTEx mandatory in the EU?", ["NeTEx"]), ["NeTEx"])
        self.assertEqual(self.check("Do I have to publish SIRI data?", ["SIRI"]), ["SIRI"])
        self.assertEqual(self.check("Is Transmodel required by law?", ["Transmodel"]), ["Transmodel"])  # relation
        self.assertEqual(self.check("Ali je NeTEx obvezen?", ["NeTEx"]), ["NeTEx"])

    def test_schema_questions_with_obligation_words_are_not(self):
        self.assertEqual(self.check("Which elements are mandatory in a NeTEx stop place?", ["NeTEx"]), [])
        self.assertEqual(self.check("Which attributes are required for a SIRI VehicleActivity?", ["SIRI"]), [])
        self.assertEqual(self.check("How does SIRI use NeTEx?", ["NeTEx", "SIRI"]), [])  # no obligation
        self.assertEqual(self.check("Is NeTEx mandatory under MMTIS?", ["NeTEx", SCOPE]), [])  # already scoped


@override_settings(EMBEDDING_BACKEND="hash")
class LinkedProvisionRetrievalTests(TestCase):
    def test_a_legal_status_question_gets_the_linked_provision_next_to_the_standards_evidence(self):
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        SourceChunk.objects.create(
            repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc", source_path="README.md",
            chunk_id="netex-readme", label="README", text="NeTEx is a CEN Technical Specification for timetables.",
            standards_scope=["NeTEx"], quality_score=0.8, doc_type="readme",
            embedding_vector=build_text_embedding("NeTEx is a CEN Technical Specification for timetables."),
        )
        SourceChunk.objects.create(
            repository_url=ACTS[0].url, commit_sha=ACTS[0].celex, source_path=f"{ACTS[0].celex}#art_4",
            chunk_id="reg-art4", label="Article 4", text="Article 4\n(i) NeTEx CEN/TS 16614 and subsequent versions;",
            standards_scope=[SCOPE], quality_score=0.9, doc_type="regulation",
            structured_metadata={"sourceUrl": f"{ACTS[0].url}#art_4"},
            embedding_vector=build_text_embedding("Article 4 NeTEx CEN/TS 16614"),
        )
        with patch("helpdesk.services.regulations.provisions_naming", return_value=[f"{ACTS[0].celex}#art_4"]):
            chunks, trace = retrieve_chunks_with_trace(
                question="Is NeTEx mandatory in the EU?", top_k=4, min_score=0.0, scope=["NeTEx"]
            )
        self.assertEqual(trace["legalStatusStandards"], ["NeTEx"])
        self.assertEqual([c["chunkId"] for c in chunks[:2]], ["netex-readme", "reg-art4"])
        self.assertEqual(chunks[1]["sourceUrl"], f"{ACTS[0].url}#art_4")


TEL_TSI = next(act for act in ACTS if "TEL TSI" in act.name)


class NamedStandardsQuestionTests(SimpleTestCase):
    def test_legislation_questions_about_standards_in_general(self):
        for question in [
            "Which standards are explicitly mentioned in the MMTIS regulation?",
            "Quelles normes le règlement MMTIS impose-t-il ?",
            "Welche Normen nennt die MMTIS-Verordnung?",
        ]:
            with self.subTest(question=question):
                self.assertTrue(asks_for_named_standards(question, [SCOPE]))

    def test_other_questions_are_not(self):
        self.assertFalse(asks_for_named_standards("Is NeTEx mandatory under MMTIS?", [SCOPE]))  # names one
        self.assertFalse(asks_for_named_standards("What is a NAP?", [SCOPE]))
        self.assertFalse(asks_for_named_standards("Which standards does Transmodel build on?", ["Transmodel"]))

    def test_the_acts_a_question_names(self):
        self.assertIn(ACTS[0].celex, named_acts("Which standards does the MMTIS regulation name?"))
        self.assertNotIn(TEL_TSI.celex, named_acts("Which standards does the MMTIS regulation name?"))
        self.assertEqual(named_acts("Which standards does the TEL TSI name?"), [TEL_TSI.celex])
        self.assertEqual(named_acts("Which standards do the acts name?"), [])


@override_settings(EMBEDDING_BACKEND="hash")
class NamedStandardsRetrievalTests(TestCase):
    PROVISIONS = {
        "NeTEx": [f"{ACTS[0].celex}#art_4", f"{TEL_TSI.celex}#app_C"],
        "Transmodel": [f"{ACTS[0].celex}#art_4", f"{TEL_TSI.celex}#app_C"],
        "SIRI": [f"{ACTS[0].celex}#art_5"],
        "OpRa": [],
    }

    def setUp(self):
        from helpdesk.services.embeddings import build_text_embedding

        for act, anchor, text in [
            (ACTS[0], "art_1", "Article 1 This Regulation establishes the necessary specifications and standards."),
            (ACTS[0], "art_4", "Article 4 (i) NeTEx CEN/TS 16614 and subsequent versions;"),
            (ACTS[0], "art_5", "Article 5 (ii) SIRI CEN/TS 15531 and subsequent versions;"),
            (TEL_TSI, "app_C", "Appendix C NeTEx and Transmodel profiles."),
        ]:
            SourceChunk.objects.create(
                repository_url=act.url, commit_sha=act.celex, source_path=f"{act.celex}#{anchor}",
                chunk_id=f"reg-{act.celex}-{anchor}", label=anchor, text=text, standards_scope=[SCOPE],
                quality_score=0.9, doc_type="regulation", embedding_vector=build_text_embedding(text),
            )

    def retrieve(self, question):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        with patch("helpdesk.services.regulations.provisions_naming", side_effect=lambda s: self.PROVISIONS.get(s, [])):
            chunks, _ = retrieve_chunks_with_trace(
                question=question, top_k=4, min_score=0.0, scope=[SCOPE], english_question=None
            )
        return [c["sourcePath"] for c in chunks]

    def test_the_provisions_that_name_standards_in_the_named_act_are_added(self):
        paths = self.retrieve("Which standards are explicitly mentioned in the MMTIS regulation?")
        # One provision per standard first: NeTEx's Art. 4 and SIRI's Art. 5, not NeTEx's second; a provision
        # that already ranks first is not added a second time.
        self.assertEqual(set(paths[:3]) >= {f"{ACTS[0].celex}#art_4", f"{ACTS[0].celex}#art_5"}, True)
        self.assertEqual(len(paths), len(set(paths)))

    def test_a_named_act_limits_the_provisions(self):
        paths = self.retrieve("Which standards does the TEL TSI name?")
        self.assertIn(f"{TEL_TSI.celex}#app_C", paths[:2])


class StandardInActQuestionTests(SimpleTestCase):
    def test_a_legislation_question_that_names_a_standard(self):
        self.assertEqual(
            standards_named_in_legislation_question("TEL TSI contains Transmodel related standards?", ["Transmodel", SCOPE]),
            ["Transmodel"],
        )
        self.assertEqual(
            standards_named_in_legislation_question("Does MMTIS require NeTEx or SIRI?", [SCOPE]), ["NeTEx", "SIRI"]
        )

    def test_other_questions_are_not(self):
        self.assertEqual(standards_named_in_legislation_question("What is Transmodel?", ["Transmodel"]), [])
        self.assertEqual(standards_named_in_legislation_question("What does MMTIS define?", [SCOPE]), [])


@override_settings(EMBEDDING_BACKEND="hash")
class StandardInActRetrievalTests(TestCase):
    """TEL TSI Appendix C names Transmodel only as "EN 12896-1:2016 … Reference data model", in the second
    chunk of a table whose first chunk lists the NeTEx parts (prod question req-mw2q8asj-0xxnna)."""

    def setUp(self):
        from helpdesk.services.embeddings import build_text_embedding

        heading = "Appendix C — C.4.A List of referenced standards"
        rows = [
            ("reg-tel-0001", "art_1", "Article 1", "Article 1 This Regulation establishes a TSI for telematics applications."),
            ("reg-tel-0247", "app_C", heading, "[P.1] CEN/TS 16614-1:2025 Public transport – Network and Timetable Exchange (NeTEx)"),
            ("reg-tel-0248", "app_C", heading, "[P.5] EN 15531-2:2022 Public transport – Service interface\n"
             "[P.7] EN 12896-1:2016 Public transport – Reference data model – Part 1: Common concepts"),
        ]
        for chunk_id, anchor, chunk_heading, text in rows:
            SourceChunk.objects.create(
                repository_url=TEL_TSI.url, commit_sha=TEL_TSI.celex, source_path=f"{TEL_TSI.celex}#{anchor}",
                chunk_id=chunk_id, label=anchor, heading=chunk_heading, text=text, standards_scope=[SCOPE],
                quality_score=0.9, doc_type="regulation", embedding_vector=build_text_embedding(text),
            )
        readme = ("NeTEx is published as CEN/TS 16614. It is based on Transmodel V6.2 (EN 12896 series) and SIRI "
                  "(CEN/TS 15531-4/-5 and EN 15531-1/-2/-3).")
        SourceChunk.objects.create(
            repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc", source_path="README.md",
            chunk_id="netex-readme", label="README", heading="Overview", text=readme,
            standards_scope=["NeTEx", "SIRI", "Transmodel"], quality_score=0.8, doc_type="readme",
            embedding_vector=build_text_embedding(readme),
        )

    def test_the_provision_its_sibling_and_the_standards_identity_are_added(self):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        with patch("helpdesk.services.regulations.provisions_naming",
                   side_effect=lambda s: [f"{TEL_TSI.celex}#app_C"] if s == "Transmodel" else []):
            chunks, trace = retrieve_chunks_with_trace(
                question="TEL TSI contains Transmodel related standards?", top_k=4, min_score=0.0,
                scope=[SCOPE], english_question=None,
            )
        ids = [c["chunkId"] for c in chunks]
        self.assertEqual(trace["legalStatusStandards"], ["Transmodel"])
        self.assertIn("reg-tel-0248", ids)  # names EN 12896
        self.assertIn("reg-tel-0247", ids)  # the rest of the list
        self.assertIn("netex-readme", ids)  # says EN 12896 is Transmodel

    def test_the_standard_numbers(self):
        from helpdesk.services.regulations import STANDARD_IDENTIFIERS
        import re

        self.assertRegex("EN 15531-2:2022 Public transport", STANDARD_IDENTIFIERS["SIRI"])
        self.assertRegex("CEN/TS 15531-4", STANDARD_IDENTIFIERS["SIRI"])
        self.assertRegex("EN 12896-1:2016", STANDARD_IDENTIFIERS["Transmodel"])
        self.assertIsNone(re.search(STANDARD_IDENTIFIERS["SIRI"], "EN 12896-1:2016"))


class LegalContextTests(SimpleTestCase):
    def test_provisions_naming_the_answers_standards_are_listed_with_short_labels(self):
        netex = legal_context(["NeTEx"])
        self.assertEqual([item["label"] for item in netex], ["MMTIS Art. 4", "TEL TSI App. C"])
        self.assertTrue(netex[0]["url"].endswith("CELEX:02017R1926-20240304#art_4"))
        # TEL TSI App. C names SIRI by number only (EN 15531-2:2022).
        self.assertEqual([item["label"] for item in legal_context(["SIRI"])], ["MMTIS Art. 5", "TEL TSI App. C"])
        self.assertEqual(legal_context(["OpRa"]), [])

    def test_the_line_is_shown_only_for_answers_about_a_named_standard(self):
        from helpdesk.api.views import _legal_context

        law = "Is NeTEx mandatory for timetable data?"
        self.assertEqual(len(_legal_context("rag", ["NeTEx"], law)), 2)
        self.assertEqual(_legal_context("abstain", ["NeTEx"], law), [])
        self.assertEqual(_legal_context("rag", [], law), [])
        self.assertEqual(_legal_context("rag", ["NeTEx", SCOPE], law), [])  # already about legislation

    def test_the_line_is_shown_only_for_questions_about_law(self):
        from helpdesk.api.views import _legal_context

        for question in [
            "What does a StopPlace contain in NeTEx?",
            "Show a NeTEx example of a coach with 49 seats and 1 wheelchair area",
            "How are delays reported at a stop?",
            "What is a VehicleType?",
        ]:
            with self.subTest(question=question):
                self.assertEqual(_legal_context("rag", ["NeTEx"], question), [])
        for question in [
            "Is NeTEx mandatory in the EU?",
            "Which regulation requires NeTEx?",
            "Do I have to publish NeTEx data to the national access point?",
            "What does MMTIS say about NeTEx?",
            "Is NeTEx required by the TEL TSI?",
            "Must a transport authority comply with NeTEx?",
        ]:
            with self.subTest(question=question):
                self.assertEqual(len(_legal_context("rag", ["NeTEx"], question)), 2)


class CitationTitleTests(SimpleTestCase):
    def test_cited_parts_of_acts_get_a_readable_title(self):
        self.assertEqual(citation_title("02017R1926-20240304#art_4"), "MMTIS Art. 4")
        self.assertEqual(citation_title("32026R0253#app_C"), "TEL TSI App. C")
        # an amending act is named by its number, not by the act it amends
        self.assertEqual(citation_title("32023L2661#rct_8"), "Directive (EU) 2023/2661 Recital 8")
        self.assertEqual(citation_title("xsd/netex_part_1/a.xsd"), "")

    def test_live_citations_carry_the_title(self):
        from helpdesk.api.views import _citations_from_prompt_order

        chunk = {**ARTICLE_3, "sourceUrl": f"{ARTICLE_3['repositoryUrl']}#art_3"}  # as indexed chunks carry it
        (citation,) = _citations_from_prompt_order([chunk], "A NAP is a point of access [E1].")
        self.assertEqual(citation["title"], "MMTIS Art. 3")


@override_settings(EMBEDDING_BACKEND="hash")
class MinimumEvidenceTests(TestCase):
    def setUp(self):
        from helpdesk.services.embeddings import build_text_embedding

        texts = [
            "National access points shall provide discovery services and metadata to data users.",
            "Member States shall reach an agreement on the metadata requirements.",
            "The travel and traffic data and the corresponding metadata shall be accessible.",
            "Data holders shall update the data in a timely manner.",
            "This Regulation shall enter into force on the twentieth day.",
        ]
        for index, text in enumerate(texts):
            SourceChunk.objects.create(
                repository_url=ACTS[0].url, commit_sha=ACTS[0].celex, source_path=f"{ACTS[0].celex}#art_{index + 1}",
                chunk_id=f"min-{index}", label=f"Article {index + 1}", text=text, standards_scope=[SCOPE],
                quality_score=0.9, doc_type="regulation", embedding_vector=build_text_embedding(text),
            )

    def retrieve(self, min_score, min_results=0):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        chunks, _ = retrieve_chunks_with_trace(
            question="What metadata does a national access point provide?", top_k=6, min_score=min_score,
            scope=[SCOPE], min_results=min_results,
        )
        return chunks

    def test_a_lone_chunk_above_the_threshold_is_joined_by_the_next_best(self):
        scores = sorted((c["score"] for c in self.retrieve(0.0)), reverse=True)
        threshold = (scores[0] + scores[1]) / 2  # only the best reaches it
        self.assertEqual(len(self.retrieve(threshold)), 1)
        self.assertEqual(len(self.retrieve(threshold, min_results=4)), 4)

    def test_nothing_is_added_when_no_chunk_reaches_the_threshold(self):
        self.assertEqual(self.retrieve(1.01, min_results=4), [])
