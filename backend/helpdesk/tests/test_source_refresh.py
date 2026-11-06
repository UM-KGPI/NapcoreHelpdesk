from __future__ import annotations

import fcntl
import os
import subprocess
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services.index_builder import IndexStats, prune_alias_spellings
from helpdesk.services.source_refresh import (
    LOCK_FILE_NAME,
    SourceRefreshError,
    SourceRepository,
    refresh_all_sources,
    sync_checkout,
)
from helpdesk.tasks import refresh_source_indexes

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.org",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.org",
}


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True, text=True).stdout.strip()


def make_remote(root: Path, name: str, files: int = 30) -> Path:
    """A repository with `files` files on branch main, standing in for the GitHub remote."""
    remote = root / "remotes" / name
    remote.mkdir(parents=True)
    _git(remote, "init", "-q", "-b", "main")
    for index in range(files):
        (remote / f"file{index}.md").write_text(f"content {index}\n", encoding="utf-8")
    _git(remote, "add", "-A")
    _git(remote, "commit", "-q", "-m", "first")
    return remote


class SyncCheckoutTests(SimpleTestCase):
    def test_clones_then_fetches_new_commits_and_returns_the_real_sha(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = make_remote(root, "NeTEx")
            source = SourceRepository("NeTEx", "https://github.com/TransmodelEcosystem/NeTEx", "netex", str(remote))

            path, sha = sync_checkout(source, root / "repos")
            self.assertEqual(sha, _git(remote, "rev-parse", "HEAD"))
            self.assertEqual((path / "file0.md").read_text(encoding="utf-8"), "content 0\n")

            (remote / "file0.md").write_text("changed\n", encoding="utf-8")
            (remote / "added.md").write_text("new\n", encoding="utf-8")
            _git(remote, "add", "-A")
            _git(remote, "commit", "-q", "-m", "second")

            path, new_sha = sync_checkout(source, root / "repos")
            self.assertEqual(new_sha, _git(remote, "rev-parse", "HEAD"))
            self.assertNotEqual(new_sha, sha)
            self.assertEqual((path / "file0.md").read_text(encoding="utf-8"), "changed\n")
            self.assertTrue((path / "added.md").exists())

    def test_local_edits_in_the_checkout_are_discarded(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = SourceRepository("SIRI", "https://github.com/TransmodelEcosystem/SIRI", "siri", str(make_remote(root, "SIRI")))
            path, _ = sync_checkout(source, root / "repos")
            (path / "file1.md").write_text("tampered\n", encoding="utf-8")
            (path / "stray.txt").write_text("stray\n", encoding="utf-8")

            sync_checkout(source, root / "repos")

            self.assertEqual((path / "file1.md").read_text(encoding="utf-8"), "content 1\n")
            self.assertFalse((path / "stray.txt").exists())

    def test_refuses_a_directory_that_is_not_a_git_checkout(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "repos" / "OpRa").mkdir(parents=True)
            (root / "repos" / "OpRa" / "precious.txt").write_text("keep\n", encoding="utf-8")
            source = SourceRepository("OpRa", "https://github.com/TransmodelEcosystem/OpRa", "opra", str(make_remote(root, "OpRa")))

            with self.assertRaisesMessage(SourceRefreshError, "not a git checkout"):
                sync_checkout(source, root / "repos")
            self.assertTrue((root / "repos" / "OpRa" / "precious.txt").exists())

    def test_refuses_a_checkout_that_looks_empty(self):
        """Pruning deletes chunks of files that are missing, so a near-empty checkout must stop here."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = SourceRepository("OpRa", "https://github.com/TransmodelEcosystem/OpRa", "opra", str(make_remote(root, "OpRa", files=3)))
            with self.assertRaisesMessage(SourceRefreshError, "only 3 files"):
                sync_checkout(source, root / "repos")

    def test_unreachable_remote_is_a_refresh_error(self):
        with TemporaryDirectory() as tmp:
            source = SourceRepository("NeTEx", "https://github.com/TransmodelEcosystem/NeTEx", "netex", str(Path(tmp) / "missing"))
            with self.assertRaisesMessage(SourceRefreshError, "git clone failed"):
                sync_checkout(source, Path(tmp) / "repos")


class RefreshAllSourcesTests(TestCase):
    def _sources(self, root: Path) -> list[SourceRepository]:
        return [
            SourceRepository(name, f"https://github.com/TransmodelEcosystem/{name}", name.lower(), str(make_remote(root, name)))
            for name in ("NeTEx", "SIRI", "OpRa")
        ]

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_each_repository_is_indexed_incrementally_with_its_own_profile(self):
        calls = []

        def fake_index(**kwargs):
            calls.append(kwargs)
            return IndexStats(scanned_files=30, skipped_files=28, created_chunks=2)

        with TemporaryDirectory() as tmp, patch("helpdesk.services.source_refresh.index_repository", side_effect=fake_index):
            root = Path(tmp)
            result = refresh_all_sources(self._sources(root), checkout_root=root / "repos")

        self.assertEqual(result["status"], "ok")
        self.assertEqual([c["profile"] for c in calls], ["netex", "siri", "opra"])
        self.assertTrue(all(c["incremental"] and c["prune"] for c in calls))
        self.assertEqual(calls[1]["repo_url"], "https://github.com/TransmodelEcosystem/SIRI")
        row = result["results"]["SIRI"]
        self.assertEqual((row["status"], row["mode"], row["created_chunks"]), ("ok", "incremental", 2))
        self.assertEqual(len(row["commit"]), 40)

    def test_full_mode_indexes_every_file(self):
        calls = []
        with TemporaryDirectory() as tmp, patch(
            "helpdesk.services.source_refresh.index_repository", side_effect=lambda **kw: calls.append(kw) or IndexStats()
        ):
            root = Path(tmp)
            result = refresh_all_sources(self._sources(root), full=True, checkout_root=root / "repos")
        self.assertFalse(any(c["incremental"] for c in calls))
        self.assertEqual(result["results"]["NeTEx"]["mode"], "full")

    def test_one_failing_repository_does_not_stop_the_others(self):
        with TemporaryDirectory() as tmp, patch("helpdesk.services.source_refresh.index_repository", return_value=IndexStats()):
            root = Path(tmp)
            sources = self._sources(root)
            sources[1] = SourceRepository("SIRI", sources[1].url, "siri", str(root / "does-not-exist"))
            with self.assertLogs("helpdesk.services.source_refresh", level="ERROR"):
                result = refresh_all_sources(sources, checkout_root=root / "repos")

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["results"]["NeTEx"]["status"], "ok")
        self.assertEqual(result["results"]["OpRa"]["status"], "ok")
        self.assertEqual(result["results"]["SIRI"]["status"], "failed")
        self.assertIn("git clone failed", result["results"]["SIRI"]["error"])

    def test_an_index_failure_is_reported_for_that_repository_only(self):
        def flaky(**kwargs):
            if kwargs["profile"] == "opra":
                raise ValueError("boom")
            return IndexStats()

        with TemporaryDirectory() as tmp, patch("helpdesk.services.source_refresh.index_repository", side_effect=flaky):
            root = Path(tmp)
            with self.assertLogs("helpdesk.services.source_refresh", level="ERROR"):
                result = refresh_all_sources(self._sources(root), checkout_root=root / "repos")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["results"]["OpRa"]["error"], "ValueError: boom")

    def test_only_selects_repositories_and_an_empty_selection_fails(self):
        with TemporaryDirectory() as tmp, patch("helpdesk.services.source_refresh.index_repository", return_value=IndexStats()):
            root = Path(tmp)
            sources = self._sources(root)
            only_siri = refresh_all_sources(sources, only=["siri"], checkout_root=root / "repos")
            nothing = refresh_all_sources(sources, only=["nope"], checkout_root=root / "repos")
        self.assertEqual(list(only_siri["results"]), ["SIRI"])
        self.assertEqual(nothing["status"], "failed")

    def test_a_second_refresh_is_skipped_while_one_is_running(self):
        with TemporaryDirectory() as tmp, patch("helpdesk.services.source_refresh.index_repository") as index:
            root = Path(tmp)
            (root / "repos").mkdir()
            with open(root / "repos" / LOCK_FILE_NAME, "w") as held:
                fcntl.flock(held, fcntl.LOCK_EX)
                result = refresh_all_sources(self._sources(root), checkout_root=root / "repos")
            index.assert_not_called()
        self.assertEqual(result["status"], "skipped")


class RefreshTaskAndCommandTests(TestCase):
    def test_task_returns_the_result_when_everything_is_ok(self):
        ok = {"status": "ok", "results": {"NeTEx": {"status": "ok"}}}
        with patch("helpdesk.tasks.refresh_all_sources", return_value=ok):
            self.assertEqual(refresh_source_indexes(), ok)

    def test_task_fails_loudly_when_a_repository_failed(self):
        partial = {"status": "partial", "results": {"NeTEx": {"status": "ok"}, "SIRI": {"status": "failed", "error": "git clone failed: x"}}}
        with patch("helpdesk.tasks.refresh_all_sources", return_value=partial):
            with self.assertRaisesMessage(SourceRefreshError, "git clone failed: x"):
                refresh_source_indexes()

    def test_command_reports_each_repository_and_fails_on_errors(self):
        rows = {"SIRI": {"status": "ok", "mode": "full", "commit": "a" * 40, "scanned_files": 10, "skipped_files": 0,
                         "created_chunks": 5, "updated_chunks": 0, "deleted_chunks": 0, "alias_chunks_removed": 423,
                         "seconds": 1.2}}
        out = StringIO()
        with patch("helpdesk.management.commands.refresh_source_indexes.refresh_all_sources", return_value={"status": "ok", "results": rows}):
            call_command("refresh_source_indexes", "--only", "SIRI", "--full", stdout=out)
        self.assertIn("SIRI: ok full commit=aaaaaaaaaaaa", out.getvalue())
        self.assertIn("alias_removed=423", out.getvalue())

        failed = {"SIRI": {"status": "failed", "error": "RuntimeError: x", "seconds": 0.1}}
        with patch("helpdesk.management.commands.refresh_source_indexes.refresh_all_sources", return_value={"status": "failed", "results": failed}):
            with self.assertRaises(CommandError):
                call_command("refresh_source_indexes", stdout=StringIO(), stderr=StringIO())

    def test_command_rejects_an_unknown_repository_name(self):
        with self.assertRaisesMessage(CommandError, "Unknown repository: Nope"):
            call_command("refresh_source_indexes", "--only", "Nope", stdout=StringIO())


class RefreshWithTheRealIndexerTests(TestCase):
    """The real indexer against a real git remote: commit SHA, canonical URL, increments and pruning."""

    CANONICAL = "https://github.com/TransmodelEcosystem/SIRI"

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/SIRI"})
    def test_chunks_carry_the_real_commit_and_follow_the_remote(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = make_remote(root, "SIRI", files=25)
            source = SourceRepository("SIRI", self.CANONICAL, "default", str(remote))
            checkout = root / "repos"

            first = refresh_all_sources([source], checkout_root=checkout)
            self.assertEqual(first["status"], "ok", first)
            first_sha = _git(remote, "rev-parse", "HEAD")
            chunks = SourceChunk.objects.filter(repository_url=self.CANONICAL)
            self.assertGreaterEqual(chunks.count(), 25)
            self.assertEqual(set(chunks.values_list("commit_sha", flat=True)), {first_sha})

            # A change on the remote: one file edited, one added, one removed.
            (remote / "file0.md").write_text("edited content about SIRI estimated timetable\n", encoding="utf-8")
            (remote / "added.md").write_text("added file about stop monitoring\n", encoding="utf-8")
            (remote / "file1.md").unlink()
            _git(remote, "add", "-A")
            _git(remote, "commit", "-q", "-m", "second")

            second = refresh_all_sources([source], checkout_root=checkout)
            self.assertEqual(second["status"], "ok", second)
            row = second["results"]["SIRI"]
            self.assertEqual(row["commit"], _git(remote, "rev-parse", "HEAD"))
            self.assertGreaterEqual(row["skipped_files"], 20)  # unchanged files were not re-indexed
            self.assertGreaterEqual(row["deleted_chunks"], 1)  # the removed file was pruned
            paths = set(SourceChunk.objects.filter(repository_url=self.CANONICAL).values_list("source_path", flat=True))
            self.assertIn("added.md", paths)
            self.assertNotIn("file1.md", paths)


class AliasSpellingTests(TestCase):
    """Production indexed OpRa under OpRa-CEN/OpRa; the refresh indexes TransmodelEcosystem/OpRa."""

    OLD = "https://github.com/OpRa-CEN/OpRa"
    CANONICAL = "https://github.com/TransmodelEcosystem/OpRa"

    def _chunk(self, url, name):
        return SourceChunk.objects.create(
            repository_url=url, commit_sha="a" * 40, source_path=f"{name}.xsd", chunk_id=f"{url}-{name}", text="t",
            embedding_vector=[0.1] * 1536,
        )

    def test_old_spelling_is_removed_after_the_canonical_copy_exists(self):
        for name in ("a", "b"):
            self._chunk(self.OLD, name)
        IndexedSourceFile.objects.create(repository_url=self.OLD, source_path="a.xsd", commit_sha="a" * 40, content_hash="h")
        self._chunk(self.CANONICAL, "a")

        removed = prune_alias_spellings(self.CANONICAL)

        self.assertEqual(removed, 2)
        self.assertFalse(SourceChunk.objects.filter(repository_url=self.OLD).exists())
        self.assertFalse(IndexedSourceFile.objects.filter(repository_url=self.OLD).exists())
        self.assertEqual(SourceChunk.objects.filter(repository_url=self.CANONICAL).count(), 1)

    def test_the_only_copy_is_never_removed(self):
        self._chunk(self.OLD, "a")

        self.assertEqual(prune_alias_spellings(self.CANONICAL), 0)
        self.assertEqual(SourceChunk.objects.filter(repository_url=self.OLD).count(), 1)

    def test_other_repositories_and_the_canonical_copy_are_untouched(self):
        self._chunk(self.CANONICAL, "a")
        self._chunk("https://github.com/TransmodelEcosystem/SIRI", "s")
        self._chunk("https://github.com/SomeOrg/Other", "o")

        self.assertEqual(prune_alias_spellings(self.CANONICAL), 0)
        self.assertEqual(SourceChunk.objects.count(), 3)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/OpRa-CEN/OpRa"})
    def test_refresh_replaces_the_old_copy_and_reports_it(self):
        for name in ("a", "b", "c"):
            self._chunk(self.OLD, name)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = make_remote(root, "OpRa", files=25)
            source = SourceRepository("OpRa", self.CANONICAL, "default", str(remote))
            result = refresh_all_sources([source], checkout_root=root / "repos")

        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["results"]["OpRa"]["alias_chunks_removed"], 3)
        self.assertFalse(SourceChunk.objects.filter(repository_url=self.OLD).exists())
        self.assertGreaterEqual(SourceChunk.objects.filter(repository_url=self.CANONICAL).count(), 25)


class SourceOntologyConfigTests(SimpleTestCase):
    def test_tn_its_loads_its_own_owl_into_its_graph(self):
        from helpdesk.services.source_refresh import find_source

        ontology = find_source("TN-ITS").ontology
        self.assertEqual(ontology.path, "OWL/core/tnits-owl.ttl")
        self.assertEqual(ontology.graph_uri, "https://napcore.eu/graph/standards/tn-its")
        self.assertEqual(ontology.key, "tn-its")
