"""The piece of a file a passage gives the model (docs/plans/2026-11-15-right-piece-of-cited-file.md)."""

from __future__ import annotations

from django.db import connection
from django.test import TestCase

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
