"""Tests for the prepared cut (services/prepared_cut.py) and reading a piece with its unit (services/read_large.py),
step 1 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md.

The embedder's counter is replaced by a counter that counts words plus a fixed overhead, so the tests run without
the embedding service; the cut only needs a count that grows with the text."""

from __future__ import annotations

import re
from unittest import mock

from django.test import SimpleTestCase, override_settings

from helpdesk.services import prepared_cut as pc
from helpdesk.services import read_large as rl


def word_count(texts, kind="passage"):
    """Words and tags, plus 3 for the kind's prefix and the special tokens."""
    return [3 + len(re.findall(r"[\w]+|<|>", t)) for t in texts], 40


def counter(limit=40):
    return pc.TokenCounter(word_count, limit)


class PackUnitTests(SimpleTestCase):
    def test_a_unit_that_fits_is_one_piece(self):
        unit = pc.Unit("u", "doc.md", "Intro", "Intro\n\n", ["One short paragraph.", "Another."], "\n\n")
        pieces = pc.pack_unit(unit, counter())
        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0].text, "Intro\n\nOne short paragraph.\n\nAnother.")
        self.assertFalse(pieces[0].inside)

    def test_whole_paragraphs_then_sentences(self):
        paragraphs = [" ".join(f"word{i}{j}" for j in range(12)) + "." for i in range(5)]
        unit = pc.Unit("u", "doc.md", "H", "H\n\n", paragraphs, "\n\n")
        c = counter(30)
        pieces = pc.pack_unit(unit, c)
        self.assertGreater(len(pieces), 1)
        for piece in pieces:
            self.assertLessEqual(c.counts([piece.embedding_input()])[0], 30)
            self.assertTrue(piece.text.startswith("H\n\n"))
            self.assertFalse(piece.inside)
        # Nothing lost, nothing repeated: the bodies give back the paragraphs.
        self.assertEqual(" ".join(" ".join(p.body.split()) for p in pieces), " ".join(" ".join(x.split()) for x in paragraphs))

    def test_a_long_sentence_is_cut_at_words_and_marked_inside(self):
        sentence = " ".join(f"w{i}" for i in range(80))
        unit = pc.Unit("u", "doc.txt", "", "", [sentence])
        c = counter(30)
        pieces = pc.pack_unit(unit, c)
        self.assertGreater(len(pieces), 2)
        self.assertTrue(all(p.inside for p in pieces))
        self.assertEqual(" ".join(p.body for p in pieces), sentence)
        for piece in pieces:
            self.assertLessEqual(c.counts([piece.embedding_input()])[0], 30)

    def test_sentences_cut_between_sentences_are_not_inside(self):
        block = " ".join(f"Sentence number {i} has five words." for i in range(20))
        pieces = pc.pack_unit(pc.Unit("u", "d", "", "", [block]), counter(30))
        self.assertGreater(len(pieces), 1)
        self.assertFalse(any(p.inside for p in pieces))
        self.assertTrue(all(p.body.endswith(".") for p in pieces))

    def test_block_fields_follow_the_first_block_of_a_piece(self):
        blocks = [" ".join(["text"] * 20) + "." for _ in range(4)]
        unit = pc.Unit("u", "d", "", "", blocks, "\n", {"q": 1}, [{"page": n} for n in range(4)])
        pieces = pc.pack_unit(unit, counter(30))
        self.assertEqual([p.fields["page"] for p in pieces], [0, 1, 2, 3])
        self.assertTrue(all(p.fields["q"] == 1 for p in pieces))

    @staticmethod
    def _lines(ends: set[int], count: int = 7) -> list[str]:
        """Lines of six words; those numbered in ends close a sentence."""
        return [" ".join(f"w{i}{j}" for j in range(6)) + ("." if i in ends else "") for i in range(count)]

    def test_a_piece_closes_at_a_sentence_end_within_the_share(self):
        # Limit 40 falls after the fifth line (inside a sentence); the fourth line ends a sentence and keeps
        # 31 of 40 (at least MIN_PIECE_SHARE), so the piece ends there.
        lines = self._lines({3})
        pieces = pc.pack_unit(pc.Unit("u", "d", "", "", lines, "\n"), counter(40))
        self.assertEqual(pieces[0].body, "\n".join(lines[:4]))
        self.assertEqual("\n".join(p.body for p in pieces), "\n".join(lines))

    def test_a_piece_keeps_its_cut_without_a_sentence_end_within_the_share(self):
        # The only sentence end is after the third line, below the share: the piece ends where the limit falls.
        lines = self._lines({2})
        pieces = pc.pack_unit(pc.Unit("u", "d", "", "", lines, "\n"), counter(40))
        self.assertEqual(pieces[0].body, "\n".join(lines[:5]))

    def test_a_piece_closes_before_a_list_item(self):
        lines = self._lines(set())
        lines[4] = "- " + lines[4]
        pieces = pc.pack_unit(pc.Unit("u", "d", "", "", lines, "\n"), counter(40))
        self.assertEqual(pieces[0].body, "\n".join(lines[:4]))

    def test_the_over_limit_split_prefers_a_sentence_end(self):
        # The estimate counts one token a line break, the counter two: six lines fit by estimate and are over by
        # count, so the group is split; the split takes the sentence end after the second line, not the middle.
        def newline_count(texts, kind="passage"):
            return [3 + len(re.findall(r"\w+", t)) + 2 * t.count("\n") for t in texts], 45

        lines = [" ".join(f"w{i}{j}" for j in range(5)) + ("." if i == 1 else "") for i in range(6)]
        pieces = pc.pack_unit(pc.Unit("u", "d", "", "", lines, "\n"), pc.TokenCounter(newline_count, 45))
        self.assertEqual([p.body for p in pieces], ["\n".join(lines[:2]), "\n".join(lines[2:])])

    def test_metadata_points_at_the_body(self):
        piece = pc.Piece("p", "h", "Lead\nPlace\n\n", "Body text.", "p#0", tail="\n\nsummary")
        meta = piece.metadata(7)
        start, end = meta["body"]
        self.assertEqual(piece.text[start:end], "Body text.")
        self.assertEqual((meta["seq"], meta["unit"], meta["v"]), (7, "p#0", pc.CUT_VERSION))
        self.assertNotIn("summary", piece.embedding_input())


class NearEmptyTests(SimpleTestCase):
    def test_a_heading_without_text_is_near_empty(self):
        self.assertTrue(pc.near_empty("1.2 Scope"))
        self.assertTrue(pc.near_empty("---"))
        self.assertFalse(pc.near_empty("The scope of this part is defined here."))

    def test_a_piece_with_an_element_is_never_near_empty(self):
        self.assertFalse(pc.near_empty("<Name>X</Name>"))
        self.assertFalse(pc.near_empty("    </Exchanging>"))


class XmlCutTests(SimpleTestCase):
    DOCUMENT = (
        '<?xml version="1.0"?>\n<Root>\n  <!-- header comment -->\n  <frames>\n'
        + "".join(f'    <Item id="{i}">\n      <Name>Item number {i}</Name>\n    </Item>\n' for i in range(30))
        + "  </frames>\n  <Tail>end</Tail>\n</Root>\n"
    )

    def test_pieces_fit_carry_their_path_and_give_back_the_document(self):
        c = counter(40)
        pieces, info = pc.cut_xml(self.DOCUMENT, "examples/a.xml", "", c, unit="examples/a.xml")
        self.assertGreater(len(pieces), 3)
        for piece in pieces:
            self.assertLessEqual(piece.tokens, 40)
            self.assertEqual(piece.tokens, c.counts([piece.embedding_input()])[0])
        self.assertEqual(pieces[0].head, "")  # the opening piece has no place line
        inner = [p for p in pieces if p.head]
        self.assertTrue(all(p.head.startswith(pc.XML_PLACE_PREFIX + "Root") for p in inner))
        self.assertTrue(any(p.head == "Element path: Root / frames\n" for p in inner))
        self.assertEqual(re.sub(r"\s+", "", "".join(p.body for p in pieces)), re.sub(r"\s+", "", self.DOCUMENT))
        # Whole elements: every piece but the last part of the root starts at a tag.
        self.assertTrue(all(p.body.lstrip().startswith("<") for p in pieces))
        self.assertFalse(any(p.inside for p in pieces))

    def test_summary_is_stored_but_not_embedded(self):
        pieces, _ = pc.cut_xml(self.DOCUMENT, "a.xml", "", counter(40), unit="a.xml", summary=lambda body: "\n\nSUMMARY")
        self.assertTrue(all(p.text.endswith("SUMMARY") for p in pieces))
        self.assertTrue(all("SUMMARY" not in p.embedding_input() for p in pieces))

    def test_a_long_text_node_is_cut_and_marked_inside(self):
        document = "<Root>\n  <Description>" + " ".join(f"w{i}" for i in range(200)) + "</Description>\n</Root>\n"
        pieces, _ = pc.cut_xml(document, "a.xml", "", counter(40), unit="a.xml")
        self.assertGreater(len(pieces), 3)
        self.assertTrue(any(p.inside for p in pieces))
        self.assertTrue(all(p.tokens <= 40 for p in pieces))

    def test_not_well_formed_raises(self):
        with self.assertRaises(ValueError):
            pc.cut_xml("<Root><a></Root>", "a.xml", "", counter(), unit="a.xml")


class UnitTests(SimpleTestCase):
    def test_markdown_heading_path(self):
        text = "# Title\nIntro text here.\n## Part\nPart text one.\n\nPart text two.\n### Detail\nDetail text.\n## Next\nNext text."
        units = pc.markdown_units(text, "README.md")
        self.assertEqual([u.head for u in units], ["Title\n\n", "Title › Part\n\n", "Title › Part › Detail\n\n", "Title › Next\n\n"])
        self.assertEqual(units[1].blocks, ["Part text one.", "Part text two."])
        self.assertEqual(units[2].heading, "Detail")

    def test_html_heading_path_and_table_rows(self):
        html = ("<h1>Guide</h1><p>Intro.</p><h2>Properties</h2><table><tr><th>Name</th><th>Range</th></tr>"
                "<tr><td>title</td><td>Literal</td></tr></table><h2>Other</h2><p>More.</p>")
        units = pc.html_units(html, "src/guide.html")
        self.assertEqual([u.head for u in units], ["Guide\n\n", "Guide › Properties\n\n", "Guide › Other\n\n"])
        self.assertEqual(units[1].blocks, ["Name: title\nRange: Literal"])

    def test_html_fragment_takes_the_file_name(self):
        units = pc.html_units("<table><tr><th>A</th></tr><tr><td>x y z</td></tr></table>", "src/tables/properties-for-dataset.html")
        self.assertEqual(units[0].heading, "Properties for dataset")

    def test_turtle_runs_by_type_and_a_long_statement_by_predicates(self):
        short = "ex:a a ex:T ;\n  rdfs:label \"a\" .\n\nex:b a ex:T ;\n  rdfs:label \"b\" .\n\nex:c a ex:U ;\n  rdfs:label \"c\" .\n"
        long = "ex:d a ex:U ;\n" + "".join(f'  ex:p{i} "value number {i}" ;\n' for i in range(30)) + '  rdfs:label "d" .\n'
        units = pc.turtle_units(short + "\n" + long, "codes.ttl", counter(40))
        self.assertEqual([u.heading for u in units], ["ex:T", "ex:U", "ex:U"])
        self.assertEqual(len(units[0].blocks), 2)
        self.assertEqual(units[2].head, "Subject: ex:d\n")
        pieces = pc.pack_unit(units[2], counter(40))
        self.assertGreater(len(pieces), 1)
        self.assertTrue(all(p.text.startswith("Subject: ex:d\n") for p in pieces))

    def test_xsd_declarations_keep_their_head(self):
        xsd = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
               '<xs:element name="Thing" type="ThingType"><xs:annotation><xs:documentation>A thing.</xs:documentation>'
               '</xs:annotation></xs:element></xs:schema>')
        units = pc.xsd_units(xsd, "xsd/a.xsd", fields_for=lambda heading: {"structured_metadata": {"h": heading}})
        self.assertEqual(len(units), 1)
        self.assertTrue(units[0].head.startswith("Schema declaration: element Thing\nDefined in: xsd/a.xsd"))
        self.assertEqual(units[0].fields["structured_metadata"], {"h": "Thing"})
        self.assertIsNone(pc.xsd_units("<not xml", "x.xsd"))

    def test_snapshot_sections_paths_pages_and_wrapped_lines(self):
        text = ("# Report\n[page 1]\nThe first line of a paragraph that wraps\nat a fixed width and ends here.\n"
                + "x" * 50 + ".\n## Part two\n[page 2]\nAnother paragraph.\n")
        units = pc.snapshot_units(text, source_path="napcore.eu/r.pdf", lead="NAPCORE: Report", title="Report",
                                  min_section_chars=20, fields={}, page_url=lambda page: {"page": page})
        self.assertEqual(len(units), 2)
        self.assertEqual(units[0].head, "NAPCORE: Report\nReport\n\n")
        self.assertEqual(units[1].head, "NAPCORE: Report\nReport › Part two\n\n")
        self.assertIn("wraps\nat a fixed width", units[0].blocks[1])
        self.assertEqual(units[1].block_fields, [{"page": 1}, {"page": 2}])

    def test_short_sections_join_the_next(self):
        text = "# A\n# B\nText of section B that is long enough.\n"
        units = pc.snapshot_units(text, source_path="p", lead="L", title="T", min_section_chars=20, fields={},
                                  page_url=lambda page: {})
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].blocks[0], "A")
        self.assertEqual(units[0].heading, "B")

    def test_a_wrapped_line_before_a_capital_or_digit_is_not_a_unit_boundary(self):
        # Eight lines wrapped at about 60 characters; the 3rd and 6th continue with a capital and a digit.
        lines = ["The data provider must describe every service in the catalogue and",
                 "keep the description up to date for the national access point and",
                 "Transmodel based exchange formats for all of the modes that are",
                 "in scope of the delegated regulation as published by the Commission",
                 "and for every update of the data that is made available through the",
                 "2024 version of the service interface that the provider operates.",
                 "A new sentence starts here and it also fills the line up to the width of",
                 "the text before it ends."]
        text = "\n".join(lines)
        units = pc.snapshot_units(text, source_path="p.pdf", lead="L", title="T", min_section_chars=10, fields={},
                                  page_url=lambda page: {})
        self.assertEqual(units[0].blocks, ["\n".join(lines[:6]), "\n".join(lines[6:])])

    def test_lines_after_a_sentence_end_list_items_and_table_rows_still_separate(self):
        lines = ["The data provider must describe every service in the catalogue and.",
                 "A new sentence starts on a line of its own and it fills the width of the line",
                 "- a list item that fills the width of the line and has no full stop at the end",
                 "1. a numbered item that fills the width of the line and has no full stop at all",
                 "Name | Package | Stereotype and a table row that fills the width of the line",
                 "Road | Transport | featureType and a second row that fills the width of the line"]
        self.assertEqual(pc.joined_lines(lines), lines)
        self.assertEqual(len(pc.line_spans("\n".join(lines))), len(lines))

    def test_code_and_markup_lines_that_fill_the_width_are_not_joined(self):
        # A long XML line in a code listing and a table delimiter fill the width the text is wrapped at; the next
        # line starts with markup, so the break is not a wrap.
        prose = "A line of text that is wrapped at the width the document uses and it carries on"
        lines = [prose, prose, prose,
                 "<se:Abstract>The fill is red and the outline is black and thin</se:Abstract>",
                 "</se:Description>",
                 "Network:Link is drawn as a line with a casing that is two pixels wide and black",
                 "!===",
                 "[cols=\"\",]"]
        self.assertEqual(pc.joined_lines(lines), ["\n".join(lines[:3]), *lines[3:]])
        self.assertEqual(len(pc.line_spans("\n".join(lines))), 6)

    def test_short_lines_without_a_sentence_end_are_not_joined(self):
        # A title, a key and a value are short lines: not wrapped text, so a capital starts a new unit.
        lines = ["Status: Final draft", "Version: 1.0", "Date: January 29, 2025", "Legal disclaimer"] * 3
        self.assertEqual(pc.joined_lines(lines), lines)

    def test_a_heading_line_is_never_joined_to_the_text_around_it(self):
        body = "A line of text that is wrapped at the width the document uses and carries on"
        text = f"# A heading that fills the width of the line as wide as the text does here and so\n{body}\n{body}\n{body}\n{body}\n"
        units = pc.snapshot_units(text, source_path="p.pdf", lead="L", title="T", min_section_chars=10, fields={},
                                  page_url=lambda page: {})
        self.assertEqual(units[0].blocks[0], "A heading that fills the width of the line as wide as the text does here and so")

    def test_inspire_codelist_and_datex_model_heads(self):
        units = pc.inspire_codelist_units([{"name": "XValue", "label": "X", "definition": "Kinds of X.", "description": "",
                                            "values": [{"id": "http://r/XValue/a", "label": "A", "definition": "first", "description": ""}]}])
        self.assertEqual(units[0].head, "INSPIRE code list XValue (X)\n\n")
        self.assertEqual(units[0].blocks, ["Kinds of X.", "Values:", "- a (A): first"])
        model = {"version": "3.7", "elements": [{"name": "C", "kind": "class", "namespace": "N", "package": "P",
                                                  "definition": "A class.", "supertypes": [], "members": [], "associations": []}]}
        units = pc.datex_model_units(model)
        self.assertEqual(units[0].head, "DATEX II class C (namespace N / P)\n")
        self.assertEqual(units[0].blocks, ["Definition: A class."])


class ReadLargeTests(SimpleTestCase):
    def test_unit_text_grows_both_ways_within_the_budget(self):
        pieces = {n: ("Place\n\n", f"body {n} " + "x" * 30) for n in range(10)}
        text = rl.unit_text(5, pieces, budget=200)
        self.assertTrue(text.startswith("Place\n\nbody 3"))
        self.assertIn("body 5", text)
        self.assertLessEqual(len(text), 200)
        self.assertEqual(text.count("Place"), 1)

    def test_unit_text_stops_at_a_gap(self):
        pieces = {5: ("", "five"), 6: ("", "six"), 8: ("", "eight"), 4: ("", "four")}
        self.assertEqual(rl.unit_text(5, pieces, 1000), "four\nfive\nsix")

    def test_xml_place_line_of_the_first_piece_taken(self):
        pieces = {1: ("Element path: R / a\n", "<b/>"), 2: ("Element path: R / a / b\n", "<c/>")}
        self.assertEqual(rl.unit_text(2, pieces, 1000), "Element path: R / a\n<b/>\n<c/>")

    @override_settings(RETRIEVAL_PREPARED_INDEX=False)
    def test_off_by_default_and_plain_chunks_unchanged(self):
        self.assertFalse(rl.enabled())
        chunks = [{"text": "plain", "structuredMetadata": {}}]
        self.assertEqual(rl.read_large(chunks), (chunks, 0))

    def test_read_large_replaces_text_and_keeps_the_piece(self):
        meta = lambda seq: {"piece": {"v": pc.CUT_VERSION, "unit": "f#0", "seq": seq, "body": [7, 7 + len(f"body {seq}")]}}
        rows = [("r", "f", f"Place\n\nbody {n}", meta(n)) for n in (1, 3)]
        chunk = {"text": "Place\n\nbody 2", "repositoryUrl": "r", "sourcePath": "f", "chunkId": "c2",
                 "structuredMetadata": meta(2)}
        query = mock.MagicMock()
        query.values_list.return_value = rows
        with mock.patch("helpdesk.models.SourceChunk.objects.filter", return_value=query):
            result, grown = rl.read_large([chunk], budget=1200)
        self.assertEqual(grown, 1)
        self.assertEqual(result[0]["text"], "Place\n\nbody 1\nbody 2\nbody 3")
        self.assertEqual(result[0]["pieceText"], "Place\n\nbody 2")
        self.assertEqual(result[0]["chunkId"], "c2")
        self.assertEqual(chunk["text"], "Place\n\nbody 2")  # the caller's dict is not changed


class EmbeddedTextTests(SimpleTestCase):
    def test_a_piece_embeds_up_to_its_body_and_other_chunks_whole(self):
        piece = pc.Piece("p", "", "Element path: R\n", "<a/>", "p", tail="\n\nXML semantic summary")
        meta = {pc.META_KEY: piece.metadata(0)}
        self.assertEqual(pc.embedded_text(piece.text, meta), "Element path: R\n<a/>")
        self.assertEqual(pc.embedded_text("old chunk text", {"schema": {}}), "old chunk text")
