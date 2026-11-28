"""A record served whole (services/whole_record.py), and that the checks on a cited sentence still work on the joined
block. No database, no network, no model."""

from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from helpdesk.services import whole_record
from helpdesk.services.llm_generator import (
    CUT_MARKER,
    _build_messages,
    _sentence_purpose_error,
    _validate_citation_grounding,
    _validate_citations_to_chunks,
)
from helpdesk.services.prepared_cut import CUT_VERSION, META_KEY

PATH = "datex-model-v3.7/Situation.SituationRecord"
REPO = "https://docs.datex2.eu/downloads/modelv37/"
HEAD = "DATEX II class SituationRecord (namespace Situation)\n"
BODIES = [
    "Definition: Something that happens on the road.\nAttributes:\n- version (Integer, 1): The version.",
    "Associations:\n- (unnamed) -> LocationReference, 1\n- impact -> Impact, 0..1",
]


def _row(seq: int, body: str, unit: str = PATH, head: str = HEAD) -> tuple[str, dict]:
    text = head + body
    return text, {META_KEY: {"v": CUT_VERSION, "seq": seq, "body": [len(head), len(text)], "unit": unit}}


def _chunk(row: tuple[str, dict], path: str = PATH) -> dict:
    text, metadata = row
    return {
        "text": text, "structuredMetadata": metadata, "sourcePath": path, "repositoryUrl": REPO,
        "chunkId": f"c{metadata[META_KEY]['seq']}", "commitSha": "v3.7", "docType": "datex",
        "heading": HEAD.strip(), "label": "DATEX II class SituationRecord",
    }


ROWS = [_row(11, BODIES[0]), _row(12, BODIES[1])]


class RecordTextTests(SimpleTestCase):
    def test_pieces_join_in_order_with_the_lead_line_once(self):
        text = whole_record.record_text(list(reversed(ROWS)), PATH, 6)
        self.assertEqual(text, HEAD + BODIES[0] + "\n" + BODIES[1])
        self.assertEqual(text.count("DATEX II class SituationRecord"), 1)

    def test_a_file_of_more_pieces_than_the_setting_is_not_a_record(self):
        rows = [_row(i, f"Associations:\n- a{i} -> B, 1") for i in range(7)]
        self.assertIsNone(whole_record.record_text(rows, PATH, 6))
        self.assertIsNotNone(whole_record.record_text(rows[:6], PATH, 6))

    def test_one_piece_is_not_joined(self):
        self.assertIsNone(whole_record.record_text(ROWS[:1], PATH, 6))

    def test_a_piece_of_another_unit_or_without_the_cut_makes_it_no_record(self):
        self.assertIsNone(whole_record.record_text([ROWS[0], _row(12, BODIES[1], unit=PATH + "#other")], PATH, 6))
        self.assertIsNone(whole_record.record_text([ROWS[0], ("plain text", {})], PATH, 6))
        old = _row(12, BODIES[1])
        old[1][META_KEY]["v"] = CUT_VERSION + 1
        self.assertIsNone(whole_record.record_text([ROWS[0], old], PATH, 6))

    def test_a_long_record_is_not_joined(self):
        rows = [_row(1, "x" * 3000), _row(2, "y" * 3000)]
        self.assertIsNone(whole_record.record_text(rows, PATH, 6))
        self.assertIsNotNone(whole_record.record_text(rows, PATH, 6, chars_max=7000))


class WholeRecordsTests(SimpleTestCase):
    def test_the_served_piece_gets_the_whole_record_and_keeps_its_citation(self):
        asked = []

        def fetch(repo, path, limit):
            asked.append((repo, path, limit))
            return ROWS

        served = _chunk(ROWS[0])
        result, joined = whole_record.whole_records([served], 6, fetch=fetch)
        self.assertEqual(joined, 1)
        self.assertEqual(asked, [(REPO, PATH, 7)])
        chunk = result[0]
        self.assertIn("LocationReference", chunk["text"])
        self.assertTrue(chunk["wholeRecord"])
        self.assertEqual(chunk["pieceText"], served["text"])
        for key in ("chunkId", "sourcePath", "repositoryUrl", "commitSha", "heading"):
            self.assertEqual(chunk[key], served[key])

    def test_one_file_is_read_once_and_the_count_keeps_it_one_place(self):
        calls = []
        result, joined = whole_record.whole_records(
            [_chunk(ROWS[0]), _chunk(ROWS[1])], 6, fetch=lambda *a: calls.append(a) or ROWS
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(result), 2)

    def test_a_schema_sized_file_is_never_joined(self):
        many = [_row(i, f"Associations:\n- a{i} -> B, 1") for i in range(7)]
        result, joined = whole_record.whole_records([_chunk(many[0])], 6, fetch=lambda *a: many)
        self.assertEqual(joined, 0)
        self.assertNotIn("wholeRecord", result[0])

    def test_a_piece_whose_unit_is_not_its_path_is_not_read(self):
        part = _row(5, "Part of a section", unit="docs/guide.md#section")
        result, joined = whole_record.whole_records(
            [_chunk(part, path="docs/guide.md")], 6, fetch=lambda *a: self.fail("read the index")
        )
        self.assertEqual(joined, 0)
        self.assertEqual(result[0]["text"], part[0])

    def test_a_passage_that_is_not_a_piece_is_returned_as_it_is(self):
        plain = {"text": "plain", "sourcePath": PATH, "repositoryUrl": REPO, "chunkId": "p", "structuredMetadata": {}}
        self.assertEqual(whole_record.whole_records([plain], 6, fetch=lambda *a: self.fail("read the index"))[0], [plain])

    @override_settings(RETRIEVAL_WHOLE_RECORD_MAX_PIECES=0)
    def test_the_setting_off_is_todays_behaviour(self):
        self.assertEqual(whole_record.max_pieces(), 0)
        chunks = [_chunk(ROWS[0])]
        result, joined = whole_record.whole_records(chunks, fetch=lambda *a: self.fail("read the index"))
        self.assertEqual((result, joined), (chunks, 0))

    def test_a_record_the_reading_already_made_whole_is_not_marked(self):
        whole = _chunk(ROWS[0])
        whole["text"] = HEAD + BODIES[0] + "\n" + BODIES[1]
        result, joined = whole_record.whole_records([whole], 6, fetch=lambda *a: ROWS)
        self.assertEqual(joined, 0)


class JoinedBlockChecksTests(SimpleTestCase):
    """The prompt builder, the citation checks and the purpose check read the joined block as any block."""

    def setUp(self):
        self.piece = _chunk(ROWS[0])
        self.whole = whole_record.whole_records([self.piece], 6, fetch=lambda *a: ROWS)[0][0]

    def _context(self, chunk):
        messages = _build_messages("Which class holds the location of a situation record?", [chunk], max_chars_per_chunk=200, language="en")
        return "\n".join(str(m.get("content", "")) for m in messages)

    def test_a_joined_block_is_not_cut_by_the_room_of_a_block(self):
        self.assertGreater(len(self.whole["text"]), 200)
        self.assertIn("impact -> Impact, 0..1", self._context(self.whole))
        self.assertIn("[E1] chunk=c11", self._context(self.whole))
        plain = dict(self.whole)
        plain.pop("wholeRecord")
        plain["text"] = self.whole["text"] + "\n" + "z" * 400
        self.assertIn(CUT_MARKER, self._context(plain))

    def test_one_citation_to_the_joined_block_is_valid_and_out_of_range_is_not(self):
        _validate_citations_to_chunks("The class is `LocationReference` [E1].", [self.whole])
        with self.assertRaises(Exception):
            _validate_citations_to_chunks("The class is `LocationReference` [E2].", [self.whole])

    def test_a_sentence_grounded_in_the_joined_part_passes_and_fails_on_the_piece_alone(self):
        sentence = "A situation record holds its location in `LocationReference`, with multiplicity 1 [E1]."
        _validate_citation_grounding(sentence, [self.whole])
        with self.assertRaises(Exception):
            _validate_citation_grounding(sentence, [self.piece])

    def test_the_purpose_check_reads_the_heading_of_the_joined_block(self):
        sentence = "The `SituationRecord` class describes something that happens on the road [E1]."
        self.assertIsNone(_sentence_purpose_error(sentence, [self.whole]))
