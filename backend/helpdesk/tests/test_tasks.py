from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings

from helpdesk.models import IndexRunMetric
from helpdesk.tasks import reindex_default_repository


class IndexTasksTests(TestCase):
    """Verify scheduled indexing task behavior in configured and unconfigured environments."""

    def test_reindex_default_repository_skips_when_not_configured(self):
        """Ensure the scheduler fails soft when repository config is missing."""
        with override_settings(INDEX_SCHEDULE_REPO_URL="", INDEX_SCHEDULE_REPO_PATH=""):
            result = reindex_default_repository()

        self.assertEqual(result["status"], "skipped")

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_reindex_default_repository_runs_incremental_index(self):
        """Ensure configured scheduler runs execute incremental index and record metrics."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "guide.md").write_text("NeTEx and SIRI exchange guidance", encoding="utf-8")

            with override_settings(
                INDEX_SCHEDULE_REPO_URL="https://github.com/TransmodelEcosystem/NeTEx",
                INDEX_SCHEDULE_REPO_PATH=str(repo_path),
                INDEX_SCHEDULE_PROFILE="netex",
            ):
                result = reindex_default_repository()

        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["created_chunks"], 1)
        self.assertEqual(IndexRunMetric.objects.filter(status=IndexRunMetric.STATUS_SUCCESS).count(), 1)
