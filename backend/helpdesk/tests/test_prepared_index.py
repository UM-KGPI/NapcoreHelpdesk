"""Tests of the cut version of each file: the indexers keep it, the command prepare_index changes it and back, a
stopped run ends as an uninterrupted one, and the prepared cut of every kind of source (plan
an internal plan (kept outside the repository), step 5). No model and no embedder: hash vectors
and a word counter in place of the embedder's tokenizer."""

from __future__ import annotations

import collections
import io
import os
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services import prepared_cut as pc
from helpdesk.services import prepared_index as pi
from helpdesk.services.index_builder import index_repository
from helpdesk.services.napcore_site import Snapshot
from helpdesk.services.regulations import Act, index_act

REPO = "https://github.com/TransmodelEcosystem/OpRa"
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org"}


def word_count(texts, kind="passage"):
    """Words and tags, plus 3 for the kind's prefix and the special tokens; the embedder's cut is 40."""
    return [3 + len(re.findall(r"[\w]+|<|>", t)) for t in texts], 40


def counter():
    return pc.TokenCounter(word_count, 40)


EXAMPLE = (
    '<?xml version="1.0"?>\n<PublicationDelivery>\n  <dataObjects>\n'
    + "".join(f'    <Journey id="j{i}">\n      <Name>Journey number {i} of the day</Name>\n    </Journey>\n' for i in range(12))
    + "  </dataObjects>\n</PublicationDelivery>\n"
)
SCHEMA = (
    '<?xml version="1.0"?>\n<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
    '  <xsd:element name="Journey" type="JourneyType">\n'
    "    <xsd:annotation><xsd:documentation>A planned journey of a vehicle on a line, with its calls at stops."
    "</xsd:documentation></xsd:annotation>\n  </xsd:element>\n"
    '  <xsd:complexType name="JourneyType">\n    <xsd:sequence>\n'
    '      <xsd:element name="Name" type="xsd:string"/>\n      <xsd:element name="Delay" type="xsd:duration"/>\n'
    "    </xsd:sequence>\n  </xsd:complexType>\n</xsd:schema>\n"
)
README = (
    "# Operating raw data\n\nThis repository holds the schema of operating raw data. It describes delays.\n\n"
    "## Examples\n\nThe examples show journeys. Each example is a whole delivery.\n\n"
    + " ".join(f"Sentence number {i} explains one more thing about the data." for i in range(12))
    + "\n"
)
TEXT = "First paragraph of a plain text file.\n\nSecond paragraph, which says a little more about it.\n"
HTML = "<html><body><h1>Guide</h1><p>A guide paragraph about frames.</p><h2>Part</h2><p>More text here.</p></body></html>\n"
TURTLE = "@prefix ex: <http://example.org/> .\nex:a a ex:Thing ; ex:name \"A thing\" .\nex:b a ex:Thing ; ex:name \"B thing\" .\n"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True, text=True).stdout.strip()


def make_repo(root: Path) -> Path:
    repo = root / "OpRa"
    (repo / "examples").mkdir(parents=True)
    (repo / "xsd").mkdir()
    (repo / "README.md").write_text(README, encoding="utf-8")
    (repo / "examples" / "journeys.xml").write_text(EXAMPLE, encoding="utf-8")
    (repo / "xsd" / "journey.xsd").write_text(SCHEMA, encoding="utf-8")
    (repo / "notes.txt").write_text(TEXT, encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "first")
    return repo


def commit(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")


def index(repo: Path, **options):
    return index_repository(REPO, repo, {REPO}, include_extensions={".md", ".xml", ".xsd", ".txt"}, prune=True, **options)


def versions_by_file(**filters) -> dict[str, set[int]]:
    found: dict[str, set[int]] = collections.defaultdict(set)
    for path, meta in SourceChunk.objects.filter(**filters).values_list("source_path", "structured_metadata"):
        found[path].add(pi.row_version(meta))
    return dict(found)


def snapshot_of_rows(**filters):
    return sorted(
        (r["source_path"], r["text"], r["doc_type"], r["chunk_type"], str(r["structured_metadata"]))
        for r in SourceChunk.objects.filter(**filters).values("source_path", "text", "doc_type", "chunk_type", "structured_metadata")
    )


# ------------------------------------------------------------------------------------------------ the cut of every kind


class CutOfEveryKindTests(SimpleTestCase):
    """The prepared cut of each kind of source: pieces fit, carry their place, and give back the source's text."""

    def assert_fit(self, pieces, at_least=1):
        self.assertGreaterEqual(len(pieces), at_least)
        c = counter()
        for piece in pieces:
            self.assertLessEqual(c.counts([piece.embedding_input()])[0], 40, piece.embedding_input())
            self.assertEqual(piece.metadata(0)["v"], pc.CUT_VERSION)

    def test_repository_files_of_every_suffix(self):
        cases = {
            "examples/journeys.xml": (EXAMPLE, "schema_fragment"),
            "xsd/journey.xsd": (SCHEMA, "schema_fragment"),
            "README.md": (README, "prose"),
            "notes.txt": (TEXT, "prose"),
            "docs/guide.html": (HTML, "prose"),
            "model/things.ttl": (TURTLE, "prose"),
        }
        for path, (raw, chunk_type) in cases.items():
            with self.subTest(path=path):
                pieces, found_type = pi.repository_file_cut(raw, path, example=pi.is_example_path(path), counter=counter())
                self.assertEqual(found_type, chunk_type)
                self.assert_fit(pieces)

    def test_xml_example_pieces_give_back_the_document_and_carry_a_summary(self):
        pieces, _ = pi.repository_file_cut(EXAMPLE, "examples/journeys.xml", example=True, counter=counter())
        self.assertGreater(len(pieces), 2)
        self.assertTrue(all(p.body.lstrip().startswith("<") for p in pieces))
        self.assertTrue(any(p.head.startswith(pc.XML_PLACE_PREFIX) for p in pieces[1:]))
        joined = re.sub(r"\s+", "", "".join(p.body for p in pieces))
        self.assertEqual(joined, re.sub(r"\s+", "", EXAMPLE))
        self.assertTrue(all(p.tail for p in pieces))  # the summary, stored and not embedded

    def test_duplicates_and_near_empty_pieces_are_left_out_and_the_first_file_keeps_a_text(self):
        def piece(path, body):
            return pc.Piece(path, "", "", body, path)

        seen = pi.SeenPieces(load=False)
        first = pi.keep_pieces([piece("a.md", "Same words in both files."), piece("a.md", "Title"), piece("a.md", "Same words in both files.")],
                               seen=seen, file_key=lambda p: pi.SeenPieces.file_key("r", p.source_path), doc_type_of=lambda p: "guide")
        second = pi.keep_pieces([piece("b.md", "Same words in both files."), piece("b.md", "Other words of the second file.")],
                                seen=seen, file_key=lambda p: pi.SeenPieces.file_key("r", p.source_path), doc_type_of=lambda p: "guide")
        self.assertEqual([p.body for p in first], ["Same words in both files."])
        self.assertEqual([p.body for p in second], ["Other words of the second file."])
        # The first file is cut again without that text: the second file may keep it now.
        seen.forget("r", "a.md")
        self.assertFalse(seen.taken("guide", "Same words in both files."))

    def test_a_file_that_is_not_well_formed_is_not_cut(self):
        self.assertIsNone(pi.repository_file_cut("<a><b></a>", "examples/bad.xml", example=True, counter=counter()))

    def test_eu_act(self):
        from helpdesk.tests.test_regulations import XHTML

        act = Act("02017R1926-20240304", "Delegated Regulation (EU) 2017/1926 (MMTIS)", "consolidated", 0.9)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "act.xhtml"
            path.write_bytes(XHTML)
            with mock.patch.object(Act, "path", property(lambda self: path)):
                units = pc.act_units(act)
        headings = [u.heading for u in units]
        self.assertIn("Article 2 — Definitions", headings)
        self.assertTrue(all(u.head.startswith(act.name) for u in units))
        self.assert_fit(pi.pack(units, counter()), at_least=len(units))

    def test_inspire_specification(self):
        spec = ("= Data specification\n\n== Overview\n\n" + "The overview paragraph explains road links. " * 3
                + "\n\n=== Scope\n\nThe scope covers transport networks of every mode. " * 2 + "\n")
        units = pc.inspire_spec_units(spec)
        self.assertTrue(units)
        self.assertTrue(all(u.fields["structured_metadata"]["sourceUrl"] for u in units))
        self.assert_fit(pi.pack(units, counter()))

    def test_napcore_and_datex_pages(self):
        text = "# Metadata\nThe metadata of a national access point describe its data.\n## Profiles\nA profile narrows it.\n"
        napcore = pc.napcore_units(Snapshot(url="https://napcore.eu/metadata/", title="Metadata", text=text))
        self.assertTrue(napcore[0].head.startswith("NAPCORE (napcore.eu): Metadata"))
        self.assert_fit(pi.pack(napcore, counter()))
        datex = pc.datex_page_units(Snapshot(url="https://docs.datex2.eu/v3.7/levels/", title="Levels", text=text))
        self.assertTrue(datex[0].head.startswith("DATEX II v"))
        self.assert_fit(pi.pack(datex, counter()))


# ------------------------------------------------------------------------------------------------ the indexer keeps the cut


@override_settings(EMBEDDING_BACKEND="hash", ALLOWED_SOURCE_REPOSITORIES={REPO})
@mock.patch("helpdesk.services.prepared_cut.count_embedded_tokens", word_count)
class IndexerKeepsTheCutTests(TestCase):
    def test_an_index_of_before_stays_one(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            index(repo)
            self.assertEqual(set().union(*versions_by_file(repository_url=REPO).values()), {0})
            (repo / "README.md").write_text(README + "\nOne more line.\n", encoding="utf-8")
            (repo / "added.txt").write_text(TEXT, encoding="utf-8")
            commit(repo)
            index(repo, incremental=True)
            self.assertEqual(set().union(*versions_by_file(repository_url=REPO).values()), {0})

    @override_settings(INDEX_CUT_VERSION=1)
    def test_a_new_index_takes_the_configured_cut(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            stats = index(repo)
            by_file = versions_by_file(repository_url=REPO)
            self.assertEqual(set().union(*by_file.values()), {1})
            self.assertEqual(stats.created_chunks, SourceChunk.objects.filter(repository_url=REPO).count())
            self.assertEqual(IndexedSourceFile.objects.filter(repository_url=REPO).count(), 4)

    def test_a_refresh_keeps_each_files_cut_and_skips_unchanged_files(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            with override_settings(INDEX_CUT_VERSION=1):
                index(repo)
            untouched = set(SourceChunk.objects.filter(repository_url=REPO, source_path="notes.txt").values_list("id", flat=True))
            # INDEX_CUT_VERSION back to 0: files with rows keep their cut, a new file takes the repository's.
            (repo / "README.md").write_text(README + "\nOne more sentence about delays.\n", encoding="utf-8")
            (repo / "added.txt").write_text("A new file with its own words about vehicles.\n", encoding="utf-8")
            commit(repo)
            stats = index(repo, incremental=True)
            by_file = versions_by_file(repository_url=REPO)
            self.assertEqual(by_file["README.md"], {1})
            self.assertEqual(by_file["added.txt"], {1})
            self.assertEqual(stats.skipped_files, 3)
            self.assertEqual(
                set(SourceChunk.objects.filter(repository_url=REPO, source_path="notes.txt").values_list("id", flat=True)), untouched
            )
            self.assertIn("One more sentence about delays.",
                          " ".join(SourceChunk.objects.filter(repository_url=REPO, source_path="README.md").values_list("text", flat=True)))

    def test_old_rows_stay_when_the_new_pieces_cannot_be_embedded(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            with override_settings(INDEX_CUT_VERSION=1):
                index(repo)
            before = snapshot_of_rows(repository_url=REPO, source_path="README.md")
            (repo / "README.md").write_text(README + "\nChanged.\n", encoding="utf-8")
            commit(repo)
            with mock.patch("helpdesk.services.prepared_index.build_text_embeddings_batch", side_effect=RuntimeError("down")):
                with self.assertRaises(RuntimeError):
                    index(repo, incremental=True)
            self.assertEqual(snapshot_of_rows(repository_url=REPO, source_path="README.md"), before)


# ------------------------------------------------------------------------------------------------ the command


@override_settings(EMBEDDING_BACKEND="hash", ALLOWED_SOURCE_REPOSITORIES={REPO})
@mock.patch("helpdesk.services.prepared_cut.count_embedded_tokens", word_count)
class ReindexCommandTests(TestCase):
    def run_command(self, repo: Path, *args: str) -> str:
        out = io.StringIO()
        call_command("prepare_index", "--database", connection.settings_dict["NAME"], "--checkout", f"{REPO}={repo}",
                     "--kinds", "example .xml,readme .md,schema .xsd,guide .txt", *args, stdout=out)
        return out.getvalue()

    def test_to_the_prepared_cut_and_back(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            index(repo)
            before = sorted(SourceChunk.objects.filter(repository_url=REPO).values_list("chunk_id", "text", "source_path"))
            self.run_command(repo)
            self.assertEqual(set().union(*versions_by_file(repository_url=REPO).values()), {1})
            self.assertNotEqual(sorted(SourceChunk.objects.filter(repository_url=REPO).values_list("chunk_id", "text", "source_path")), before)
            # The way back is the same command with the old version.
            self.run_command(repo, "--cut-version", "0")
            after = sorted(SourceChunk.objects.filter(repository_url=REPO).values_list("chunk_id", "text", "source_path"))
            self.assertEqual(after, before)
            self.assertEqual(set().union(*versions_by_file(repository_url=REPO).values()), {0})

    def test_a_stopped_run_ends_as_an_uninterrupted_one(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            index(repo)
            self.run_command(repo)
            uninterrupted = snapshot_of_rows(repository_url=REPO)
            self.run_command(repo, "--cut-version", "0")
            out = self.run_command(repo, "--stop-after", "2")
            self.assertIn("stopped after 2 files", out)
            self.assertEqual(sum(v == {1} for v in versions_by_file(repository_url=REPO).values()), 2)
            self.run_command(repo)
            self.assertEqual(snapshot_of_rows(repository_url=REPO), uninterrupted)
            # A run on an index already at the version changes nothing.
            out = self.run_command(repo)
            self.assertIn('"already at the version": 1', out)
            self.assertEqual(snapshot_of_rows(repository_url=REPO), uninterrupted)

    def test_a_file_whose_source_differs_from_its_rows_is_left_as_it_is(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            index(repo)
            (repo / "notes.txt").write_text(TEXT + "\nNot indexed.\n", encoding="utf-8")
            before = snapshot_of_rows(repository_url=REPO, source_path="notes.txt")
            self.run_command(repo)
            self.assertEqual(snapshot_of_rows(repository_url=REPO, source_path="notes.txt"), before)

    def test_a_dry_run_writes_nothing(self):
        with TemporaryDirectory() as tmp:
            repo = make_repo(Path(tmp))
            index(repo)
            before = snapshot_of_rows(repository_url=REPO)
            self.run_command(repo, "--dry-run")
            self.assertEqual(snapshot_of_rows(repository_url=REPO), before)


# ------------------------------------------------------------------------------------------------ harvested documents


@override_settings(EMBEDDING_BACKEND="hash")
@mock.patch("helpdesk.services.prepared_cut.count_embedded_tokens", word_count)
class HarvestedDocumentKeepsItsCutTests(TestCase):
    ACT = Act("02017R1926-20240304", "Delegated Regulation (EU) 2017/1926 (MMTIS)", "consolidated", 0.9)

    def test_a_harvested_document_is_indexed_again_with_its_own_cut(self):
        from helpdesk.tests.test_regulations import XHTML

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "act.xhtml"
            path.write_bytes(XHTML)
            with mock.patch.object(Act, "path", property(lambda self: path)):
                self.assertEqual(index_act(self.ACT)[0], "indexed")
                self.assertEqual(set().union(*versions_by_file(repository_url=self.ACT.url).values()), {0})
                pi.index_harvested_document(self.ACT.url, pc.act_units(self.ACT), doc_type="regulation",
                                            commit_sha=self.ACT.celex, standards_scope=["EU legislation"], counter=counter())
                prepared = snapshot_of_rows(repository_url=self.ACT.url)
                self.assertEqual(set().union(*versions_by_file(repository_url=self.ACT.url).values()), {1})
                # The harvester runs again (its parser changed): the document keeps the prepared cut.
                with mock.patch("helpdesk.services.regulations.PARSER_VERSION", "test-next"):
                    self.assertEqual(index_act(self.ACT)[0], "indexed")
                self.assertEqual(snapshot_of_rows(repository_url=self.ACT.url), prepared)


class SettingsTests(SimpleTestCase):
    def test_the_configured_cut_is_the_old_one_by_default(self):
        self.assertEqual(pi.configured_version(), 0)

    @override_settings(INDEX_CUT_VERSION=7)
    def test_an_unknown_cut_is_refused(self):
        with self.assertRaises(ValueError):
            pi.configured_version()


class VectorIndexCommandTests(TestCase):
    def test_the_index_expression_is_the_querys(self):
        from helpdesk.management.commands.vector_index import index_sql
        from helpdesk.services.retrieval_gateway import _filled_numbers_distance

        with override_settings(VECTOR_INDEX_HALF_PRECISION=True):
            query_sql = _filled_numbers_distance([0.1] * 384, 384).sql
        expression = query_sql.split(" <=> ")[0]
        self.assertIn(f"(({expression}) halfvec_cosine_ops)", index_sql(384, True, 100))

    def test_refused_without_the_setting_or_for_another_database(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command("vector_index", "--database", "another", stdout=io.StringIO())
        with override_settings(VECTOR_INDEX_DIMENSIONS=0), self.assertRaises(CommandError):
            call_command("vector_index", "--database", connection.settings_dict["NAME"], stdout=io.StringIO())

    @override_settings(VECTOR_INDEX_DIMENSIONS=384, VECTOR_INDEX_HALF_PRECISION=True)
    def test_a_dry_run_names_the_statement_and_builds_nothing(self):
        out = io.StringIO()
        call_command("vector_index", "--database", connection.settings_dict["NAME"], "--dry-run", stdout=out)
        self.assertIn("CREATE INDEX IF NOT EXISTS sourcechunk_embedding_filled_ivfflat_idx", out.getvalue())
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_indexes WHERE indexname = 'sourcechunk_embedding_filled_ivfflat_idx'")
            self.assertEqual(cursor.fetchone()[0], 0)
