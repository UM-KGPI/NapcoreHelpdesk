from __future__ import annotations

import threading
from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services import llm_generator, request_timing, retrieval_gateway


class RequestTimingTests(SimpleTestCase):
    def test_nothing_is_recorded_outside_a_request(self):
        def outside():
            request_timing.add("llmMs", 5.0, "llmCalls")
            result.append(request_timing.snapshot())

        result: list = []
        thread = threading.Thread(target=outside)  # a new thread has no record
        thread.start()
        thread.join()
        self.assertEqual(result, [{}])

    def test_times_and_counts_add_up(self):
        request_timing.start()
        request_timing.add("llmMs", 1.25, "llmCalls")
        request_timing.add("llmMs", 2.0, "llmCalls")
        with request_timing.timed("parseMs"):
            pass
        snapshot = request_timing.snapshot()
        self.assertEqual(snapshot["llmMs"], 3.2)
        self.assertEqual(snapshot["llmCalls"], 2)
        self.assertIn("parseMs", snapshot)
        self.assertGreaterEqual(snapshot["totalMs"], 0.0)
        self.assertNotIn("_started", snapshot)

    def test_model_calls_record_time_calls_and_output_tokens(self):
        request_timing.start()
        reply = {"choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 42}}
        with patch.object(llm_generator, "_request_chat_completion_untimed", return_value=reply):
            self.assertIs(llm_generator._request_chat_completion(api_base_url="", api_key="", model="m", timeout_seconds=1,
                                                                  temperature=0.0, max_tokens=10, messages=[]), reply)
        snapshot = request_timing.snapshot()
        self.assertEqual((snapshot["llmCalls"], snapshot["llmOutputTokens"]), (1, 42))

    def test_a_streamed_call_is_timed_to_its_last_token(self):
        request_timing.start()
        with patch.object(llm_generator, "_stream_request_chat_completion_untimed", return_value=iter(["a", "b"])):
            self.assertEqual(list(llm_generator._stream_request_chat_completion()), ["a", "b"])
        self.assertEqual(request_timing.snapshot()["llmCalls"], 1)

    def test_retrieval_calls_are_counted(self):
        request_timing.start()
        with patch.object(retrieval_gateway, "_retrieve_chunks_with_trace_untimed", return_value=([], {})):
            retrieval_gateway.retrieve_chunks_with_trace(question="q", top_k=1, min_score=0.0)
            retrieval_gateway.retrieve_chunks_with_trace(question="q", top_k=1, min_score=0.0)
        self.assertEqual(request_timing.snapshot()["retrievalCalls"], 2)
