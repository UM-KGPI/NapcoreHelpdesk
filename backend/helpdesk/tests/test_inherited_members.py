"""The members a class record inherits (services/inherited_members.py). No database, no network, no model: the
index is a dictionary of rows handed in as fetch and find."""

from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services import inherited_members as im
from helpdesk.services.llm_generator import chunk_evidence_text
from helpdesk.services.prepared_cut import CUT_VERSION, META_KEY

REPO = "https://example.org/model/"
FOLDER = "model-v1"


def _record(name: str, namespace: str, body: str) -> tuple[str, list[tuple[str, dict]]]:
    path = f"{FOLDER}/{namespace}.{name}"
    head = f"class {name} (namespace {namespace})\n"
    text = head + body
    return path, [(text, {META_KEY: {"v": CUT_VERSION, "seq": 1, "body": [len(head), len(text)], "unit": path}})]


def _index() -> dict[str, list[tuple[str, dict]]]:
    rows = {}
    for name, namespace, body in (
        ("Leaf", "A", "Definition: leaf.\nSubtype of: Mid\nAttributes:\n- own (String, 0..1): Own.\nAssociations:\n- (unnamed) -> Other, 0..1"),
        ("Mid", "A", "Definition: mid.\nSubtype of: B.Root\nAttributes:\n- midAttr (Integer, 1..1): Mid attribute.\nAssociations:\n- midLink -> Leaf, 0..*"),
        ("Root", "B", "Definition: root.\nAttributes:\n- rootAttr (Boolean, 0..1): Root attribute.\n- other (String, 0..1): More.\nAssociations:\n- link -> Mid, 1"),
        ("Root", "C", "Definition: another root with the same name.\nAttributes:\n- wrong (String, 0..1): Not this one."),
        ("Lonely", "A", "Definition: no supertype.\nAttributes:\n- x (String, 0..1): X."),
        ("Orphan", "A", "Definition: supertype missing.\nSubtype of: Missing\nAttributes:\n- y (String, 0..1): Y."),
    ):
        path, record = _record(name, namespace, body)
        rows[path] = record
    return rows


INDEX = _index()


def fetch(_repo: str, path: str) -> list[tuple[str, dict]]:
    return INDEX.get(path, [])


def find(_repo: str, folder: str, name: str) -> list[str]:
    return sorted(p for p in INDEX if p.rsplit("/", 1)[0] == folder and (p.rsplit("/", 1)[1] == name or p.endswith("." + name)))


class InheritedGroupsTest(SimpleTestCase):
    def test_chain_nearest_first_with_stored_lines(self):
        is_record, groups = im.inherited_groups(REPO, f"{FOLDER}/A.Leaf", fetch, find)
        self.assertTrue(is_record)
        self.assertEqual([g["name"] for g in groups], ["Mid", "B.Root"])
        self.assertEqual(groups[0]["lines"], ["- midAttr (Integer, 1..1): Mid attribute.", "- midLink -> Leaf, 0..*"])
        self.assertEqual(groups[1]["path"], f"{FOLDER}/B.Root")
        self.assertIn("- rootAttr (Boolean, 0..1): Root attribute.", groups[1]["lines"])
        self.assertNotIn("- wrong (String, 0..1): Not this one.", [l for g in groups for l in g["lines"]])

    def test_bare_name_with_two_matches_is_not_resolved(self):
        self.assertIsNone(im.resolve(REPO, f"{FOLDER}/A.Leaf", "Root", find))

    def test_record_without_supertype_or_with_a_missing_one(self):
        self.assertEqual(im.inherited_groups(REPO, f"{FOLDER}/A.Lonely", fetch, find), (False, []))
        is_record, groups = im.inherited_groups(REPO, f"{FOLDER}/A.Orphan", fetch, find)
        self.assertTrue(is_record)
        self.assertEqual(groups, [{"name": "Missing", "path": None, "depth": 1, "lines": None}])

    def test_rows_that_are_not_a_cut_record_are_not_read(self):
        self.assertIsNone(im.joined_record([("text", {})], f"{FOLDER}/A.Leaf"))
        rows = INDEX[f"{FOLDER}/A.Leaf"]
        self.assertIsNone(im.joined_record(rows, "other/path"))
        self.assertIsNone(im.joined_record(rows * (im.MAX_RECORD_PIECES + 1), f"{FOLDER}/A.Leaf"))


class RenderTest(SimpleTestCase):
    def groups(self):
        return im.inherited_groups(REPO, f"{FOLDER}/A.Leaf", fetch, find)[1]

    def test_everything_fits(self):
        text, shown = im.render(self.groups(), 2000)
        self.assertEqual(text.split("\n")[0], "Inherited from Mid:")
        self.assertIn("Inherited from B.Root:", text)
        self.assertNotIn("not shown", text)
        self.assertEqual([g["name"] for g in shown], ["Mid", "B.Root"])

    def test_cap_takes_relations_first_and_shows_stored_order(self):
        groups = self.groups()
        full, _ = im.render(groups, 2000)
        cap = len(full) - 5
        text, shown = im.render(groups, cap)
        self.assertLessEqual(len(text), cap)
        self.assertIn("not shown)", text)
        kept = {line for g in shown for line in g["lines"]}
        self.assertIn("- link -> Mid, 1", kept)  # a relation is kept before an attribute
        self.assertNotIn("- other (String, 0..1): More.", kept)
        # the lines shown are in stored order within the group
        root = next(g for g in shown if g["name"] == "B.Root")
        self.assertEqual(root["lines"], [l for l in groups[1]["lines"] if l in root["lines"]])

    def test_nothing_fits(self):
        self.assertEqual(im.render(self.groups(), 10), ("", []))

    def test_cut_does_not_depend_on_anything_but_the_cap(self):
        self.assertEqual(im.render(self.groups(), 300), im.render(self.groups(), 300))


class WithInheritedTest(SimpleTestCase):
    def chunk(self, path: str) -> dict:
        text, metadata = INDEX[path][0]
        return {"text": text, "structuredMetadata": metadata, "sourcePath": path, "repositoryUrl": REPO, "chunkId": path}

    def test_appends_to_the_record_and_leaves_others(self):
        leaf, lonely = self.chunk(f"{FOLDER}/A.Leaf"), self.chunk(f"{FOLDER}/A.Lonely")
        block = {"text": "path block", "semanticPath": True, "chunkId": "p"}
        result, stats = im.with_inherited([lonely, leaf, block], 6, fetch, find)
        self.assertEqual(result[0], lonely)
        self.assertEqual(result[2], block)
        grown = result[1]
        self.assertTrue(grown["text"].startswith(leaf["text"] + "\nInherited from Mid:"))
        self.assertEqual(grown["chunkId"], leaf["chunkId"])
        self.assertEqual(grown["inheritedBaseChars"], len(leaf["text"]))
        self.assertEqual(stats["blocks"], 1)

    def test_only_the_first_passages_and_the_question_budget(self):
        leaves = [self.chunk(f"{FOLDER}/A.Leaf") for _ in range(4)]
        result, stats = im.with_inherited(leaves, 2, fetch, find)
        self.assertEqual([("Inherited" in c["text"]) for c in result], [True, True, False, False])
        self.assertLessEqual(stats["chars"], im.MAX_CHARS_PER_QUESTION)

    def test_prompt_trims_only_the_base_text(self):
        leaf = self.chunk(f"{FOLDER}/A.Leaf")
        result, _ = im.with_inherited([leaf], 6, fetch, find)
        shown = chunk_evidence_text(result[0], 200)
        self.assertTrue(shown.endswith(result[0]["text"][len(leaf["text"]) :]))
        self.assertEqual(chunk_evidence_text(leaf, 200), leaf["text"])
