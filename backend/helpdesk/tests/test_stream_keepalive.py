from __future__ import annotations

import time

from django.test import SimpleTestCase

from helpdesk.api.views import KEEPALIVE_EVENT, with_keepalive


def _slow(events, pause):
    for event in events:
        time.sleep(pause)
        yield event


class KeepaliveTests(SimpleTestCase):
    def test_a_silent_step_is_filled_with_keepalive_comments(self):
        out = list(with_keepalive(_slow(["data: a\n\n", "data: b\n\n"], 0.25), 0.05))
        self.assertEqual([e for e in out if e != KEEPALIVE_EVENT], ["data: a\n\n", "data: b\n\n"])
        self.assertGreaterEqual(out.count(KEEPALIVE_EVENT), 4)
        self.assertTrue(KEEPALIVE_EVENT.startswith(":"))  # an SSE comment: ignored by clients

    def test_fast_streams_get_no_comments(self):
        self.assertEqual(list(with_keepalive(iter(["data: a\n\n"]), 5)), ["data: a\n\n"])

    def test_errors_in_the_stream_reach_the_response(self):
        def failing():
            yield "data: a\n\n"
            raise RuntimeError("boom")

        stream = with_keepalive(failing(), 1)
        self.assertEqual(next(stream), "data: a\n\n")
        with self.assertRaises(RuntimeError):
            next(stream)

    def test_interval_zero_runs_inline(self):
        events = iter(["data: a\n\n"])
        self.assertEqual(list(with_keepalive(events, 0)), ["data: a\n\n"])
