"""Tests for the element cut of XML examples (services/xml_example_cut.py), step R0 of
an internal plan (kept outside the repository)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from django.test import SimpleTestCase

from helpdesk.services.index_builder import EXAMPLE_PATH_PREFIX, ExampleCut, example_xml_chunks
from helpdesk.services.xml_example_cut import cut_xml_example, parse_elements, piece_spans


def _joined(text: str, limit: int) -> str:
    return "".join(text[start:end] for start, end in piece_spans(text, limit))


def _tags(text: str) -> list[str]:
    return re.findall(r"<(/?[A-Za-z_][\w:.-]*)", text)


class CutPropertyMixin:
    def assertCovers(self, text: str, limit: int):
        spans = piece_spans(text, limit)
        self.assertEqual(_joined(text, limit), text)
        for (_, end), (start, _) in zip(spans, spans[1:]):
            self.assertEqual(end, start)
        # Every tag of the document is in exactly one piece.
        pieces = cut_xml_example(text, limit)
        self.assertEqual(sum((_tags(p.text) for p in pieces), []), _tags(text))


class SmallDocumentTests(CutPropertyMixin, SimpleTestCase):
    def test_file_smaller_than_a_piece_is_one_piece_without_path(self):
        text = '<?xml version="1.0"?>\n<Root>\n  <A>1</A>\n</Root>\n'
        pieces = cut_xml_example(text, 1200)
        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0].path, ())
        self.assertEqual(pieces[0].text, text.strip())
        self.assertCovers(text, 1200)

    def test_nesting_cuts_down_to_the_children_that_fit(self):
        inner = "".join(f"\n      <Leaf>{'x' * 40}</Leaf>" for _ in range(6))
        text = f"<Root>\n  <Outer>\n    <Middle>{inner}\n    </Middle>\n  </Outer>\n</Root>"
        pieces = cut_xml_example(text, 160)
        self.assertCovers(text, 160)
        self.assertGreater(len(pieces), 1)
        leaf_pieces = [p for p in pieces if p.text.lstrip().startswith("<Leaf>")]
        self.assertTrue(leaf_pieces)
        for piece in leaf_pieces:
            self.assertEqual(piece.path, ("Root", "Outer", "Middle"))
            # Whole elements only: every Leaf that opens in a piece closes in it.
            self.assertEqual(piece.text.count("<Leaf>"), piece.text.count("</Leaf>"))

    def test_long_run_of_equal_siblings_is_cut_into_runs_of_whole_siblings(self):
        stops = "".join(f'\n    <StopPoint id="s{i}"><Name>Stop {i}</Name></StopPoint>' for i in range(200))
        text = f"<Root>\n  <stops>{stops}\n  </stops>\n</Root>\n"
        limit = 600
        pieces = cut_xml_example(text, limit)
        self.assertCovers(text, limit)
        self.assertGreater(len(pieces), 10)
        for piece in pieces:
            self.assertEqual(piece.text.count("<StopPoint"), piece.text.count("</StopPoint>"))
            self.assertLessEqual(len(piece.text), limit + len("\n  </stops>\n</Root>"))
        self.assertTrue(all(p.path == ("Root", "stops") for p in pieces[1:]))

    def test_a_comment_goes_with_the_element_after_it(self):
        body = "".join(f"\n    <!-- item {i} -->\n    <Item>{'y' * 60}</Item>" for i in range(10))
        text = f"<Root>\n  <items>{body}\n  </items>\n</Root>"
        pieces = cut_xml_example(text, 200)
        self.assertCovers(text, 200)
        for piece in pieces[1:]:
            if "<Item>" in piece.text:
                self.assertTrue(piece.text.lstrip().startswith("<!-- item"))

    def test_markup_inside_comments_cdata_and_attributes_is_not_an_element(self):
        text = (
            '<?xml version="1.0"?>\n<!DOCTYPE r [ <!ENTITY e "v"> ]>\n<r a="x > y">\n'
            "  <!-- <NotAnElement> -->\n  <c><![CDATA[ <alsoNot> ]]></c>\n</r>"
        )
        root = parse_elements(text).children
        self.assertEqual([e.name for e in root], ["r"])
        self.assertEqual([e.name for e in root[0].children], ["c"])
        self.assertCovers(text, 30)

    def test_namespaces_and_prefixes_give_local_names_in_the_path(self):
        rows = "".join(f'\n      <gml:pos srsName="x">{i} {i}</gml:pos>' for i in range(20))
        text = (
            '<siri:Siri xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2">\n'
            f"  <siri:ServiceDelivery>\n    <gml:LineString>{rows}\n    </gml:LineString>\n"
            "  </siri:ServiceDelivery>\n</siri:Siri>"
        )
        pieces = cut_xml_example(text, 250)
        self.assertCovers(text, 250)
        self.assertIn(("Siri", "ServiceDelivery", "LineString"), {p.path for p in pieces})

    def test_an_element_larger_than_the_limit_without_children_is_cut_at_lines(self):
        lines = "\n".join(f"word{i} " * 8 for i in range(30))
        text = f"<Root>\n  <Description>\n{lines}\n  </Description>\n</Root>"
        pieces = cut_xml_example(text, 300)
        self.assertCovers(text, 300)
        self.assertGreater(len(pieces), 3)
        self.assertTrue(all(len(p.text) <= 300 for p in pieces))
        self.assertEqual(pieces[-1].path, ("Root", "Description"))

    def test_mixed_content_keeps_text_and_elements_in_order(self):
        text = "<Root>\n  <p>Some text <b>bold</b> more text " + "and words " * 40 + "<i>it</i> end</p>\n</Root>"
        self.assertCovers(text, 120)

    def test_closing_tags_stay_with_the_last_piece(self):
        body = "".join(f"\n        <X>{'z' * 50}</X>" for _ in range(8))
        text = f"<A>\n  <B>\n    <C>\n      <D>{body}\n      </D>\n    </C>\n  </B>\n</A>\n"
        pieces = cut_xml_example(text, 200)
        self.assertCovers(text, 200)
        self.assertTrue(pieces[-1].text.rstrip().endswith("</A>"))
        self.assertIn("<X>", pieces[-1].text)

    def test_a_document_that_is_not_well_formed_is_refused(self):
        with self.assertRaises(ValueError):
            cut_xml_example("<a><b></a>", 100)
        with self.assertRaises(ValueError):
            cut_xml_example("<a><b>", 100)


class ExampleChunkTests(SimpleTestCase):
    TEXT = "<Root>\n  <list>" + "".join(f"\n    <Item><Name>n{i}</Name></Item>" for i in range(40)) + "\n  </list>\n</Root>"

    def test_path_line_and_summary(self):
        chunks = example_xml_chunks(self.TEXT, "examples/a.xml", ExampleCut(max_chars=300, summary=True))
        later = chunks[1]
        self.assertTrue(later["text"].startswith(f"{EXAMPLE_PATH_PREFIX}Root / list\n<Item>") or later["text"].startswith(f"{EXAMPLE_PATH_PREFIX}Root / list\n    <Item>"))
        self.assertIn("XML semantic summary:", later["text"])
        # The summary names the piece's own elements, not the ancestors of the path line.
        self.assertNotIn("root", later["text"].split("XML semantic summary:")[1])
        self.assertEqual(later["path"], ("Root", "list"))

    def test_without_summary(self):
        chunks = example_xml_chunks(self.TEXT, "examples/a.xml", ExampleCut(max_chars=300, summary=False))
        self.assertFalse(any("XML semantic summary" in c["text"] for c in chunks))
        self.assertEqual("".join(c["body"] for c in chunks).replace("\n", "").replace(" ", ""), self.TEXT.replace("\n", "").replace(" ", ""))

    def test_not_well_formed_keeps_the_line_cut(self):
        chunks = example_xml_chunks("<a>\n  <b>\n</a>\n", "examples/bad.xml", ExampleCut(max_chars=300, summary=False))
        self.assertEqual([c["path"] for c in chunks], [()])


class RealExampleFilesTests(CutPropertyMixin, SimpleTestCase):
    """The pieces of every example file in the source checkouts give back the file. The checkouts are not in
    CI; set XML_CUT_EXAMPLE_DIRS (colon-separated directories) to run it."""

    def test_every_example_file_is_reproduced(self):
        dirs = [Path(d) for d in os.environ.get("XML_CUT_EXAMPLE_DIRS", "").split(":") if d]
        files = [f for d in dirs for f in sorted(d.rglob("*.xml"))]
        if not files:
            self.skipTest("no example directories given")
        for limit in (600, 1200):
            for path in files:
                text = path.read_text(encoding="utf-8", errors="ignore")
                try:
                    spans = piece_spans(text, limit)
                except ValueError:
                    continue  # not well formed: the line cut is kept for it
                with self.subTest(file=str(path), limit=limit):
                    self.assertEqual("".join(text[s:e] for s, e in spans), text)
