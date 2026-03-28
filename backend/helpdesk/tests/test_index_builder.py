from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from helpdesk.models import IndexedSourceFile, IndexRunMetric, SourceChunk


class SourceIndexBuilderTests(TestCase):
    """Verify indexing command guardrails, profile filtering, and incremental behavior."""

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_build_source_index_command_indexes_repository_files(self):
        """Ensure an allowed repository is indexed into chunks and run metrics."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "guide.md").write_text(
                "NeTEx timetable exchange guidance with references to SIRI and Transmodel.",
                encoding="utf-8",
            )
            (docs / "ignore.bin").write_bytes(b"binary")

            call_command(
                "build_source_index",
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                prune=True,
            )

        chunks = SourceChunk.objects.filter(repository_url="https://github.com/NeTEx-CEN/NeTEx")
        self.assertGreater(chunks.count(), 0)
        self.assertTrue(chunks.filter(source_path="docs/guide.md").exists())

        scopes = set()
        for chunk in chunks:
            scopes.update(chunk.standards_scope)

        self.assertIn("NeTEx", scopes)
        self.assertIn("SIRI", scopes)
        self.assertIn("Transmodel", scopes)
        first_chunk = chunks.first()
        self.assertIsNotNone(first_chunk)
        self.assertTrue(isinstance(first_chunk.embedding_vector, list))
        self.assertGreater(len(first_chunk.embedding_vector), 0)
        self.assertTrue(IndexedSourceFile.objects.filter(source_path="docs/guide.md").exists())
        self.assertEqual(IndexRunMetric.objects.filter(status=IndexRunMetric.STATUS_SUCCESS).count(), 1)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_build_source_index_command_rejects_unapproved_repository(self):
        """Ensure repositories outside the configured allow-list are rejected."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "README.md").write_text("content", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command(
                    "build_source_index",
                    repo_url="https://github.com/example/unapproved",
                    repo_path=str(repo_path),
                )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_build_source_index_command_rejects_unknown_profile(self):
        """Ensure unknown profile names fail fast during command validation."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "README.md").write_text("content", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command(
                    "build_source_index",
                    repo_url="https://github.com/NeTEx-CEN/NeTEx",
                    repo_path=str(repo_path),
                    profile="nonexistent-profile",
                )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_build_source_index_command_applies_netex_profile_filtering(self):
        """Ensure the NeTEx profile includes docs-like paths and excludes test paths."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            tests = repo_path / "tests"
            docs.mkdir(parents=True, exist_ok=True)
            tests.mkdir(parents=True, exist_ok=True)

            (docs / "netex.md").write_text("NeTEx profile doc", encoding="utf-8")
            (tests / "skip.md").write_text("NeTEx test doc", encoding="utf-8")

            call_command(
                "build_source_index",
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                profile="netex",
                prune=True,
            )

        self.assertTrue(SourceChunk.objects.filter(source_path="docs/netex.md").exists())
        self.assertFalse(SourceChunk.objects.filter(source_path="tests/skip.md").exists())

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_build_source_index_command_incremental_skips_unchanged_files(self):
        """Ensure incremental mode skips unchanged files on subsequent runs."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            guide = docs / "guide.md"
            guide.write_text("NeTEx timetable exchange", encoding="utf-8")

            call_command(
                "build_source_index",
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                incremental=True,
                prune=True,
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                incremental=True,
                prune=True,
            )

        latest = IndexRunMetric.objects.order_by("-created_at").first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.mode, IndexRunMetric.MODE_INCREMENTAL)
        self.assertGreaterEqual(latest.skipped_files, 1)
