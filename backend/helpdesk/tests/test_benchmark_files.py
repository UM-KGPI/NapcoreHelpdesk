"""Question and gold files that are not in the repository are found through HELPDESK_BENCHMARKS_DIR."""

from __future__ import annotations

import tempfile
from pathlib import Path

from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from helpdesk.management.commands.benchmark_utils import local_benchmark_file, read_yaml_file


class LocalBenchmarkFileTests(SimpleTestCase):
    def test_the_file_is_looked_up_in_the_configured_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(HELPDESK_BENCHMARKS_DIR=Path(tmp)):
                path = local_benchmark_file("some-questions.yaml")
                self.assertEqual(path, Path(tmp) / "some-questions.yaml")
                path.write_text("questions:\n  - id: s1\n    question: Invented?\n", encoding="utf-8")
                self.assertEqual(read_yaml_file(path)["questions"][0]["id"], "s1")

    def test_a_missing_file_is_a_clear_command_error_naming_the_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(HELPDESK_BENCHMARKS_DIR=Path(tmp)):
                with self.assertRaises(CommandError) as raised:
                    read_yaml_file(local_benchmark_file("absent.yaml"))
        self.assertIn("HELPDESK_BENCHMARKS_DIR", str(raised.exception))
        self.assertIn("absent.yaml", str(raised.exception))
