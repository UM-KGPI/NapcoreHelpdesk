from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from django.test import SimpleTestCase, TestCase, override_settings


def _chunk(chunk_id: str, path: str, text: str, repository: str = "https://github.com/TransmodelEcosystem/OpRa"):
    from helpdesk.models import SourceChunk
    from helpdesk.services.embeddings import build_text_embedding

    return SourceChunk.objects.create(
        chunk_id=chunk_id,
        repository_url=repository,
        commit_sha="abc",
        source_path=path,
        label=chunk_id,
        text=text,
        standards_scope=["OpRa"],
        quality_score=0.9,
        doc_type="schema",
        embedding_vector=build_text_embedding(text),
    )


@override_settings(LLM_ENABLED=False, SEARCH_TRANSLATION_ENABLED=False, GRAPHDB_ENABLED=False)
class RetrievalProbeTests(TestCase):
    def setUp(self):
        _chunk("probe-1", "xsd/opra_indicators/opra_lateDatedVehicleJourney_version.xsd", "Late dated vehicle journey delay entry.")
        _chunk("probe-2", "xsd/opra_indicators/opra_cancelledDatedVehicleJourney_version.xsd", "Cancelled dated vehicle journey entry.")
        _chunk("probe-3", "README.md", "OpRa exchanges operational raw data such as delays and cancellations.")

    def _retrieve(self):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        chunks, _trace = retrieve_chunks_with_trace(
            question="How are delayed journeys exchanged in OpRa?",
            top_k=3,
            min_score=0.0,
            scope=["OpRa"],
            graph_rag_enabled=False,
            min_results=2,
            english_question=None,
        )
        return [(c["chunkId"], round(float(c["score"]), 9)) for c in chunks]

    def test_the_probe_is_off_unless_set(self):
        from helpdesk.services import retrieval_gateway

        self.assertIsNone(retrieval_gateway._retrieval_probe.get())
        with retrieval_gateway.retrieval_probe(lambda stage, items: None):
            self.assertIsNotNone(retrieval_gateway._retrieval_probe.get())
        self.assertIsNone(retrieval_gateway._retrieval_probe.get())

    def test_the_probe_reads_every_stage_and_changes_no_result(self):
        from helpdesk.management.commands.locate_answer_sources import StageRecorder
        from helpdesk.services.retrieval_gateway import retrieval_probe

        without = self._retrieve()
        recorder = StageRecorder()
        with retrieval_probe(recorder):
            probed = self._retrieve()
        self.assertEqual(probed, without)
        self.assertEqual(self._retrieve(), without)
        self.assertEqual(len(recorder.passes), 1)
        stages = recorder.passes[0]["stages"]
        for stage in ("pool", "preselected", "scored", "min_score", "ranked", "source_path_cap", "top_k", "final"):
            self.assertIn(stage, stages)
        self.assertEqual([row[2] for row in stages["final"]], [chunk_id for chunk_id, _ in without])
        self.assertIn("returned", recorder.outer)


class MatchingTests(SimpleTestCase):
    def test_a_pattern_is_matched_against_repository_and_path_with_an_end_anchor(self):
        from helpdesk.management.commands.locate_answer_sources import matches

        opra = "https://github.com/TransmodelEcosystem/OpRa"
        netex = "https://github.com/TransmodelEcosystem/NeTEx"
        self.assertTrue(matches(["OpRa/README.md$"], opra, "README.md"))
        self.assertFalse(matches(["OpRa/README.md$"], netex, "README.md"))
        self.assertTrue(matches(["#art_1$"], "https://eur-lex.europa.eu/x", "02017R1926-20240304#art_1"))
        self.assertFalse(matches(["#art_1$"], "https://eur-lex.europa.eu/x", "02017R1926-20240304#art_10"))
        # A plain benchmark pattern (a part of the path) still matches.
        self.assertTrue(matches(["opra_lateDatedVehicleJourney"], opra, "xsd/opra_indicators/opra_lateDatedVehicleJourney_version.xsd"))

    def test_a_passage_is_lost_at_the_stage_after_the_last_it_is_in(self):
        from helpdesk.management.commands.locate_answer_sources import lost_at

        self.assertEqual(lost_at([("pool", False), ("preselected", False)]), "pool")
        self.assertEqual(lost_at([("pool", True), ("preselected", True), ("top_k", False)]), "top_k")
        # Added late (a provision) after being absent from the pool: not lost.
        self.assertIsNone(lost_at([("pool", False), ("top_k", False), ("final", True)]))

    def test_the_gold_file_has_patterns_a_scope_and_a_reason_for_every_question(self):
        from helpdesk.management.commands.locate_answer_sources import DEFAULT_INPUT as path

        if not path.is_file():
            self.skipTest(f"{path.name} is kept outside the repository (HELPDESK_BENCHMARKS_DIR); the test only checks that file")
        questions = yaml.safe_load(path.read_text(encoding="utf-8"))["questions"]
        self.assertEqual(len({q["id"] for q in questions}), len(questions))
        for question in questions:
            self.assertTrue(question["expected_source_patterns"], question["id"])
            self.assertTrue(question["fitting_scope"], question["id"])
            self.assertTrue(question["note"].strip(), question["id"])
            self.assertIn(question["kind"], {"everyday", "legislation", "profile", "overview", "element"}, question["id"])


class TranslationsTests(SimpleTestCase):
    def test_no_model_never_calls_the_model(self):
        from helpdesk.management.commands.locate_answer_sources import Translations

        with patch("helpdesk.services.llm_generator.english_search_query") as rendering:
            english, origin = Translations(None, use_model=False, fresh=False).english("Kaj je vozni red?")
        rendering.assert_not_called()
        self.assertIsNone(english)
        self.assertIn("no-model", origin)


@override_settings(
    VOCABULARY_BRIDGE_ENABLED=True,
    CONTROLLER_LLM_ENABLED=True,
    CONTROLLER_LLM_API_BASE_URL="http://controller.invalid",
    CONTROLLER_LLM_API_MODEL="m",
)
class BridgeTermsTests(SimpleTestCase):
    def test_a_stored_reply_is_used_without_asking_the_model(self):
        from helpdesk.management.commands.locate_answer_sources import BridgeTerms
        from helpdesk.services import vocabulary_bridge

        terms = BridgeTerms(None, fresh=False)
        terms.stored = {"q": {"terms": ["FARE PRODUCT"], "seconds": 1.0}}
        with patch("helpdesk.services.vocabulary_bridge.request.urlopen") as call, terms.active():
            self.assertEqual(vocabulary_bridge._ask_for_terms("q"), ["FARE PRODUCT"])
        call.assert_not_called()
        self.assertEqual(terms.calls, 0)

    def test_a_stored_failure_stays_a_failure(self):
        from helpdesk.management.commands.locate_answer_sources import BridgeTerms
        from helpdesk.services import vocabulary_bridge

        terms = BridgeTerms(None, fresh=False)
        terms.stored = {"q": {"error": "timed out", "seconds": 3.0}}
        with terms.active():
            self.assertEqual(vocabulary_bridge.bridged_question_concepts("q"), frozenset())

    def test_a_new_reply_is_asked_once_and_stored(self):
        from helpdesk.management.commands.locate_answer_sources import BridgeTerms
        from helpdesk.services import vocabulary_bridge

        terms = BridgeTerms(None, fresh=False)
        with patch.object(vocabulary_bridge, "_ask_for_terms", return_value=["TICKET"]) as ask, terms.active():
            vocabulary_bridge._ask_for_terms("q")
            vocabulary_bridge._ask_for_terms("q")
        ask.assert_called_once_with("q")
        self.assertEqual(terms.stored["q"]["terms"], ["TICKET"])
