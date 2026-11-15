"""The piece of a file a passage gives the model (docs/plans/2026-11-15-right-piece-of-cited-file.md)."""

from __future__ import annotations

from django.db import connection
from django.test import TestCase, override_settings

from helpdesk.models import SourceChunk
from helpdesk.services.embeddings import build_text_embedding

REPO = "https://github.com/TransmodelEcosystem/OpRa"
PATH = "examples/CountExample.xml"


def _piece(chunk_id: str, text: str, path: str = PATH, heading: str = "") -> SourceChunk:
    return SourceChunk.objects.create(
        chunk_id=chunk_id,
        repository_url=REPO,
        commit_sha="abc",
        source_path=path,
        label=path,
        text=text,
        heading=heading,
        standards_scope=["OpRa"],
        quality_score=0.84,
        doc_type="example",
        chunk_type="schema_fragment",
        embedding_vector=build_text_embedding(text),
    )


def _passage(chunk: SourceChunk, score: float = 0.9) -> dict:
    return {
        "text": chunk.text,
        "score": score,
        "repositoryUrl": chunk.repository_url,
        "commitSha": chunk.commit_sha,
        "sourcePath": chunk.source_path,
        "chunkId": chunk.chunk_id,
        "label": chunk.label,
        "heading": chunk.heading,
        "docType": chunk.doc_type,
    }


OPENING = (
    '<Opra xmlns="https://transmodel-cen.eu/opra/1.0">\n<Description>Cancelled and late journeys.</Description>\n'
    "XML semantic summary:\n- concepts: opra, service delivery, description, cancelled dated vehicle journey entry"
)
COUNT = (
    "<LateDatedVehicleJourneyCount>\n<NumberOfOccurrences>69</NumberOfOccurrences>\n"
    "XML semantic summary:\n- concepts: late dated vehicle journey count, number of occurrences"
)
ENTRY = (
    "<LateDatedVehicleJourneyEntry>\n<DelayDuration>PT10M</DelayDuration>\n"
    "XML semantic summary:\n- concepts: late dated vehicle journey entry, delay duration"
)


@override_settings(GRAPHDB_ENABLED=False, LLM_ENABLED=False)
class BestPieceOfFileTests(TestCase):
    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("text search needs PostgreSQL")

    def _choose(self, passages, question):
        from helpdesk.services.retrieval_gateway import _best_pieces_of_files

        return _best_pieces_of_files(passages, question)

    def test_the_piece_holding_more_question_terms_takes_the_place(self):
        opening = _piece("p-open", OPENING)
        _piece("p-count", COUNT)
        _piece("p-entry", ENTRY)
        result, replaced = self._choose([_passage(opening)], "How to model number of late journeys?")
        self.assertEqual(replaced, 1)
        self.assertEqual(result[0]["chunkId"], "p-count")
        self.assertIn("LateDatedVehicleJourneyCount", result[0]["text"])
        # The file, its score and its place stay; the retrieved piece is named.
        self.assertEqual(result[0]["sourcePath"], PATH)
        self.assertEqual(result[0]["score"], 0.9)
        self.assertEqual(result[0]["retrievedChunkId"], "p-open")

    def test_a_tie_keeps_the_retrieved_piece(self):
        entry = _piece("p-entry", ENTRY)
        _piece("p-count", COUNT)
        result, replaced = self._choose([_passage(entry)], "How are late journeys exchanged?")
        self.assertEqual(replaced, 0)
        self.assertEqual(result[0]["chunkId"], "p-entry")

    def test_camel_case_in_the_question_matches_the_spelled_out_summary(self):
        opening = _piece("p-open", OPENING)
        _piece("p-count", COUNT)
        result, _ = self._choose([_passage(opening)], "What is LateDatedVehicleJourneyCount?")
        self.assertEqual(result[0]["chunkId"], "p-count")

    def test_pieces_with_a_heading_are_left_alone(self):
        path = "xsd/opra_counts.xsd"
        declaration = _piece("d-1", "Schema declaration: element Opra. Documentation: root.", path=path, heading="Opra")
        _piece("d-2", "Schema declaration: element LateDatedVehicleJourneyCount. Documentation: number of late journeys.", path=path, heading="LateDatedVehicleJourneyCount")
        result, replaced = self._choose([_passage(declaration)], "How to model number of late journeys?")
        self.assertEqual(replaced, 0)
        self.assertEqual(result[0]["chunkId"], "d-1")

    def test_a_piece_already_among_the_passages_is_not_given_twice(self):
        opening = _piece("p-open", OPENING)
        count = _piece("p-count", COUNT)
        result, replaced = self._choose([_passage(count), _passage(opening)], "How to model number of late journeys?")
        self.assertEqual([p["chunkId"] for p in result], ["p-count", "p-open"])
        self.assertEqual(replaced, 0)

    def test_passages_that_are_not_indexed_pieces_are_kept(self):
        passage = {"chunkId": "def-1", "sourcePath": "docs/ontology/standards/transmodel.ttl#JOURNEY", "text": "A journey.", "heading": ""}
        unknown = {"chunkId": "gone", "sourcePath": PATH, "repositoryUrl": REPO, "text": "x", "heading": ""}
        _piece("p-count", COUNT)
        result, replaced = self._choose([passage, unknown], "How to model number of late journeys?")
        self.assertEqual(result, [passage, unknown])
        self.assertEqual(replaced, 0)

    def test_standard_names_alone_do_not_choose_a_piece(self):
        from helpdesk.services.retrieval_gateway import _piece_terms

        self.assertEqual(_piece_terms("What is OpRa in NeTEx?"), [])
        self.assertEqual(sorted(_piece_terms("number of late journeys")), ["journey", "late", "number"])

    def test_retrieval_applies_it_and_reports_it_in_the_trace(self):
        from unittest.mock import patch

        from helpdesk.services import retrieval_gateway

        opening = _piece("p-open", OPENING)
        _piece("p-count", COUNT)
        with patch.object(retrieval_gateway, "_diversified_top_k", lambda candidates, top_k, mmr_lambda: [
            {**_passage(opening), "_rankScore": 0.9, "_vectorScore": 0.9}
        ]):
            chunks, trace = retrieval_gateway._retrieve_chunks_once("How to model number of late journeys?", 1, 0.0)
        self.assertEqual(chunks[0]["chunkId"], "p-count")
        self.assertEqual(trace["filePiecesReplaced"], 1)
        with override_settings(RETRIEVAL_BEST_FILE_PIECE=False), patch.object(
            retrieval_gateway, "_diversified_top_k", lambda candidates, top_k, mmr_lambda: [
                {**_passage(opening), "_rankScore": 0.9, "_vectorScore": 0.9}
            ]
        ):
            chunks, trace = retrieval_gateway._retrieve_chunks_once("How to model number of late journeys?", 1, 0.0)
        self.assertEqual(chunks[0]["chunkId"], "p-open")
        self.assertEqual(trace["filePiecesReplaced"], 0)


class PiecesMeasureTests(TestCase):
    """The finer measure of locate_answer_sources: is the piece given the file's best piece."""

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("text search needs PostgreSQL")

    def test_given_opening_piece_is_not_the_best(self):
        from helpdesk.management.commands.locate_answer_sources import StageRecorder, pieces_report

        opening = _piece("p-open", OPENING)
        _piece("p-count", COUNT)
        _piece("p-entry", ENTRY)
        recorder = StageRecorder()
        recorder("begin", {"question": "q"})
        recorder("ranked", [_passage(opening)])
        rows = [(REPO, PATH, "p-open", 0.9)]
        entry = {"question": "How to model number of late journeys?", "note": "the LateDatedVehicleJourneyCount"}
        report = pieces_report(entry, None, rows, recorder, ["CountExample"])
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["chunks"], 3)
        self.assertEqual(report[0]["given"], [1])
        self.assertEqual(report[0]["best"], [2])
        self.assertFalse(report[0]["givenIsBest"])
        self.assertTrue(report[0]["givenIsOpening"])
        self.assertIsNone(report[0]["bestFurthestStage"])

    def test_unwanted_files_are_left_out_unless_every_file_is_asked(self):
        from helpdesk.management.commands.locate_answer_sources import StageRecorder, pieces_report

        _piece("p-open", OPENING)
        rows = [(REPO, PATH, "p-open", 0.9)]
        entry = {"question": "late journeys"}
        self.assertEqual(pieces_report(entry, None, rows, StageRecorder(), ["other"]), [])
        self.assertEqual(len(pieces_report(entry, None, rows, StageRecorder(), None)), 1)
