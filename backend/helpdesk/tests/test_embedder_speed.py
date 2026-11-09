"""Embedder speed (2026-11-09): the model's threads follow the container's CPU limit, and unstored passages
(ontology definitions) are embedded once, not for every question."""

from __future__ import annotations

from unittest.mock import mock_open, patch

from django.test import SimpleTestCase, override_settings

from helpdesk import embedding_service
from helpdesk.services import embeddings


class CpuThreadsTests(SimpleTestCase):
    def test_threads_follow_the_cgroup_limit(self):
        with patch.dict("os.environ", {"EMBEDDER_THREADS": ""}), patch("builtins.open", mock_open(read_data="200000 100000\n")):
            self.assertEqual(embedding_service.cpu_threads(), (2, "CPU limit 2"))
        with patch.dict("os.environ", {"EMBEDDER_THREADS": ""}), patch("builtins.open", mock_open(read_data="150000 100000\n")):
            self.assertEqual(embedding_service.cpu_threads(), (2, "CPU limit 1.5"))  # rounded up

    def test_no_limit_or_no_cgroup_leaves_the_runtime_default(self):
        with patch.dict("os.environ", {"EMBEDDER_THREADS": ""}), patch("builtins.open", mock_open(read_data="max 100000\n")):
            self.assertEqual(embedding_service.cpu_threads(), (None, "runtime default, no CPU limit"))
        with patch.dict("os.environ", {"EMBEDDER_THREADS": ""}), patch("builtins.open", side_effect=OSError):
            self.assertEqual(embedding_service.cpu_threads(), (None, "runtime default"))

    def test_an_explicit_setting_wins(self):
        with patch.dict("os.environ", {"EMBEDDER_THREADS": "3"}):
            self.assertEqual(embedding_service.cpu_threads(), (3, "EMBEDDER_THREADS"))

    def test_a_cpu_count_passed_as_threads_may_be_fractional(self):
        # The compose files pass EMBEDDER_CPUS ("2.0", "1.5") as EMBEDDER_THREADS.
        for value, threads in (("2.0", 2), ("4", 4), ("1.5", 2)):
            with patch.dict("os.environ", {"EMBEDDER_THREADS": value}):
                self.assertEqual(embedding_service.cpu_threads(), (threads, "EMBEDDER_THREADS"))


class PassageCacheTests(SimpleTestCase):
    def setUp(self):
        embeddings._PASSAGE_CACHE.clear()

    def test_a_passage_is_embedded_once(self):
        with patch.object(embeddings, "build_text_embedding", return_value=[0.5, 0.25]) as embed:
            self.assertEqual(embeddings.cached_passage_embedding("StopPlace definition"), [0.5, 0.25])
            self.assertEqual(embeddings.cached_passage_embedding("StopPlace definition"), [0.5, 0.25])
        embed.assert_called_once()

    def test_kept_per_backend_and_bounded(self):
        with patch.object(embeddings, "build_text_embedding", side_effect=lambda text: [float(len(text))]) as embed:
            with override_settings(EMBEDDING_BACKEND="hash"):
                embeddings.cached_passage_embedding("a")
            with override_settings(EMBEDDING_BACKEND="semantic"):
                embeddings.cached_passage_embedding("a")
            self.assertEqual(embed.call_count, 2)
            with patch.object(embeddings, "PASSAGE_CACHE_SIZE", 3):
                for text in ("b", "c", "d", "e"):
                    embeddings.cached_passage_embedding(text)
                self.assertEqual(len(embeddings._PASSAGE_CACHE), 3)
