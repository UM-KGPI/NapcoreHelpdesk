"""Concepts on the pieces and the pieces that carry a question's concepts by meaning (services/chunk_concepts.py)."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.services import chunk_concepts as cc

KNOWN = {"netex:StopPlace", "netex:Quay", "netex:Name", "siri:StopPlace", "transmodel:STOP_PLACE", "netex:ParkingBay"}
ALIGNED = {"netex:StopPlace": "transmodel:STOP_PLACE", "siri:StopPlace": "transmodel:STOP_PLACE"}


class PieceConceptTests(SimpleTestCase):
    def _concepts(self, **kwargs):
        defaults = dict(doc_type="example", chunk_type="schema_fragment", standards_scope=["NeTEx"], structured_metadata={}, nearest=None, known=KNOWN)
        defaults.update(kwargs)
        with patch("helpdesk.services.semantic_graph.CONCEPT_TO_TRANSMODEL", ALIGNED):
            return cc.piece_concepts(**defaults)

    def test_an_xml_piece_carries_the_classes_of_the_elements_opened_in_its_body(self):
        head = "Element path: PublicationDelivery / ParkingBay\n"
        body = '<StopPlace id="x">\n<Quay/>\n<Unknown>a</Unknown>\n'
        tail = "\n\nXML semantic summary:\n- concepts: <ParkingBay>"
        meta = {"piece": {"v": 1, "seq": 3, "body": [len(head), len(head) + len(body)], "unit": "f.xml"}}
        concepts = self._concepts(text=head + body + tail, structured_metadata=meta)
        # ParkingBay is in the place line and the summary only: not in the body.
        self.assertEqual(concepts, ["netex:Quay", "netex:StopPlace", "transmodel:STOP_PLACE"])

    def test_the_standard_of_an_xml_piece_comes_from_its_scope(self):
        self.assertEqual(self._concepts(text="<StopPlace>", standards_scope=["SIRI"]), ["siri:StopPlace", "transmodel:STOP_PLACE"])
        self.assertEqual(self._concepts(text="<StopPlace>", standards_scope=["DATEX II"]), [])

    def test_a_schema_declaration_carries_its_declared_class(self):
        meta = {"schema": {"declarationName": "StopPlace"}}
        concepts = self._concepts(text="Schema declaration: element StopPlace", doc_type="schema", structured_metadata=meta)
        self.assertEqual(concepts, ["netex:StopPlace", "transmodel:STOP_PLACE"])

    def test_a_label_word_counts_on_prose_only_among_the_nearest_classes(self):
        words = lambda text, scope: {"netex:Quay", "netex:StopPlace", "transmodel:relatesTo"}  # noqa: E731
        kwargs = dict(text="A stop place has quays.", doc_type="napcore", chunk_type="prose", label_concepts=words)
        # Quay is not near the piece; StopPlace is near through its Transmodel class; associations never count.
        near = self._concepts(nearest={"transmodel:STOP_PLACE", "transmodel:relatesTo"}, **kwargs)
        self.assertEqual(near, ["netex:StopPlace", "transmodel:STOP_PLACE"])
        self.assertEqual(self._concepts(nearest=None, **kwargs), [])

    def test_scope_prefixes(self):
        self.assertEqual(cc.scope_prefixes(["NeTEx", "SIRI", "EU legislation", "TN-ITS"]), ["netex", "siri", "tnits"])
        self.assertEqual(cc.scope_prefixes(None), [])


class NearestConceptTests(SimpleTestCase):
    def setUp(self):
        matrix = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]], dtype=np.float32)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        index = (["siri:VehicleActivity", "transmodel:STOP_PLACE", "netex:Quay"], ["siri", "transmodel", "netex"],
                 [[], ["netex:StopPlace"], []], matrix)
        patcher = patch.object(cc, "_INDEX", index)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_nearest_first_and_only_the_standards_asked(self):
        self.assertEqual(cc.nearest_concepts([1.0, 0.0], 2), ["siri:VehicleActivity", "transmodel:STOP_PLACE"])
        # A Transmodel class counts for NeTEx when NeTEx implements it.
        self.assertEqual(cc.nearest_concepts([1.0, 0.0], 2, ["netex"]), ["transmodel:STOP_PLACE", "netex:Quay"])

    def test_question_concepts_bring_the_implementing_and_aligned_classes(self):
        with patch("helpdesk.services.concept_vectors.index_complete", return_value=True), patch(
            "helpdesk.services.concept_vectors._embed", return_value=[[1.0, 0.0]]
        ) as embed, patch.object(cc, "QUESTION_CONCEPTS", 1), patch("helpdesk.services.semantic_graph.CONCEPT_TO_TRANSMODEL", ALIGNED):
            found = cc.question_concepts("How is a stop place described in NeTEx?", ["NeTEx"])
        self.assertEqual(found, {"transmodel:STOP_PLACE", "netex:StopPlace"})
        # The subject of the question is embedded, not its frame.
        self.assertEqual(embed.call_args[0][0], ["stop place"])

    def test_no_concepts_without_the_embedder(self):
        with patch("helpdesk.services.concept_vectors.index_complete", return_value=True), patch(
            "helpdesk.services.concept_vectors._embed", side_effect=OSError("down")
        ):
            self.assertEqual(cc.question_concepts("stop place", None), set())


class LabelledCandidateTests(TestCase):
    @staticmethod
    def _vector(first: float) -> list[float]:
        vector = [0.0] * 1536
        vector[0], vector[1] = first, (1.0 - first * first) ** 0.5
        return vector

    def setUp(self):
        from django.db import connection

        from helpdesk.models import SourceChunk
        from helpdesk.services import retrieval_gateway

        if connection.vendor != "postgresql" or not retrieval_gateway.HAS_NATIVE_PGVECTOR:
            self.skipTest("needs PostgreSQL with pgvector")
        for index in range(12):
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc",
                source_path=f"x/{index // 3}.xml", chunk_id=f"c-{index}", text=f"piece {index}",
                standards_scope=["SIRI"] if index == 11 else ["NeTEx"], embedding_vector=self._vector(index / 12),
                structured_metadata={"concepts": ["netex:Quay"] if index % 2 else ["netex:StopPlace", "transmodel:STOP_PLACE"]},
            )

    def _ids(self, concepts, scope=("NeTEx",), limit=10, per_file=2, **flags):
        with override_settings(**flags):
            return [c.chunk_id for c in cc.labelled_candidates(set(concepts), self._vector(1.0), list(scope), limit=limit, per_file=per_file)]

    def test_only_carriers_in_scope_nearest_first(self):
        self.assertEqual(self._ids({"netex:Quay"}), ["c-9", "c-7", "c-5", "c-3", "c-1"])  # c-11 is SIRI

    def test_at_most_per_file_and_limit(self):
        self.assertEqual(self._ids({"netex:Quay", "transmodel:STOP_PLACE"}, per_file=1, limit=3), ["c-10", "c-8", "c-5"])

    def test_index_search_and_exact_order_agree(self):
        exact = self._ids({"transmodel:STOP_PLACE"}, VECTOR_INDEX_SEARCH=False)
        self.assertEqual(self._ids({"transmodel:STOP_PLACE"}, VECTOR_INDEX_SEARCH=True), exact)
        self.assertEqual(self._ids({"transmodel:STOP_PLACE"}, VECTOR_INDEX_SEARCH=True, VECTOR_INDEX_DIMENSIONS=384), exact)

    def test_nothing_without_concepts(self):
        self.assertEqual(self._ids(set()), [])


class GatewaySettingTests(TestCase):
    """RETRIEVAL_CONCEPT_LABELS off: the label-word search of paths runs as before and no concept is found by
    meaning; on: the labelled pieces are the graph candidates."""

    def _retrieve(self, **flags):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        with override_settings(GRAPHDB_ENABLED=False, **flags):
            return retrieve_chunks_with_trace(question="How is a stop place described in NeTEx?", top_k=5, min_score=0.0, scope=["NeTEx"], graph_rag_enabled=True)

    @patch("helpdesk.services.retrieval_gateway._graph_concept_candidates", return_value=[])
    @patch("helpdesk.services.chunk_concepts.labelled_candidates", return_value=[])
    @patch("helpdesk.services.chunk_concepts.question_concepts", return_value={"netex:StopPlace"})
    def test_off_keeps_the_label_word_search(self, by_meaning, labelled, words):
        self._retrieve()
        by_meaning.assert_not_called()
        labelled.assert_not_called()
        words.assert_called()

    @patch("helpdesk.services.retrieval_gateway._graph_concept_candidates", return_value=[])
    @patch("helpdesk.services.chunk_concepts.labelled_candidates", return_value=[])
    @patch("helpdesk.services.chunk_concepts.question_concepts", return_value={"netex:StopPlace"})
    def test_on_uses_the_labelled_pieces(self, by_meaning, labelled, words):
        self._retrieve(RETRIEVAL_CONCEPT_LABELS=True)
        by_meaning.assert_called()
        labelled.assert_called()
        self.assertEqual(labelled.call_args[0][0], {"netex:StopPlace"})
        words.assert_not_called()

    @patch("helpdesk.services.retrieval_gateway._graph_concept_candidates", return_value=[])
    @patch("helpdesk.services.chunk_concepts.question_concepts", return_value=set())
    def test_on_without_concepts_by_meaning_falls_back_to_the_label_words(self, by_meaning, words):
        self._retrieve(RETRIEVAL_CONCEPT_LABELS=True)
        words.assert_called()
