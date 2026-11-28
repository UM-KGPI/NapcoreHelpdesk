"""A chunk with None in a text field must not fail the answer: telemetry writes "" / 0.0 instead."""

from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services.example_retrieval import format_examples_as_chunks
from helpdesk.services.retrieval_event_logger import log_retrieval_events


class NullFieldTests(SimpleTestCase):
    def test_none_fields_are_written_as_empty(self):
        chunk = {
            "retrievalEventId": "re-1",
            "repositoryUrl": None,
            "commitSha": None,
            "sourcePath": None,
            "chunkId": None,
            "score": None,
        }
        with patch("helpdesk.services.retrieval_event_logger.RetrievalEvent.objects.update_or_create") as write:
            ids = log_retrieval_events(question_event=object(), chunks=[chunk])
        self.assertEqual(ids, ["re-1"])
        defaults = write.call_args.kwargs["defaults"]
        for field in ("repository_url", "commit_sha", "source_path", "chunk_id"):
            self.assertEqual(defaults[field], "")
        self.assertEqual(defaults["score"], 0.0)

    def test_values_are_kept(self):
        chunk = {"retrievalEventId": "re-2", "commitSha": "abc", "sourcePath": "a.xml", "score": 0.5}
        with patch("helpdesk.services.retrieval_event_logger.RetrievalEvent.objects.update_or_create") as write:
            log_retrieval_events(question_event=object(), chunks=[chunk])
        defaults = write.call_args.kwargs["defaults"]
        self.assertEqual((defaults["commit_sha"], defaults["source_path"], defaults["score"]), ("abc", "a.xml", 0.5))


class ExampleChunkCommitTests(SimpleTestCase):
    EXAMPLE = {"iri": "https://x/example/1", "file_path": "examples/a.xml", "concept": "https://x#Thing"}

    def test_commit_is_carried_when_known(self):
        with patch("helpdesk.services.example_retrieval._load_example_file_content", return_value=""):
            chunk = format_examples_as_chunks([self.EXAMPLE], commit_sha="c" * 40)[0]
        self.assertEqual(chunk["commit_sha"], "c" * 40)

    def test_commit_is_empty_not_missing_when_unknown(self):
        with patch("helpdesk.services.example_retrieval._load_example_file_content", return_value=""):
            chunk = format_examples_as_chunks([self.EXAMPLE])[0]
        self.assertEqual(chunk["commit_sha"], "")
