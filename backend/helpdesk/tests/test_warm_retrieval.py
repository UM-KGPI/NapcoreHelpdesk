from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class WarmRetrievalTests(SimpleTestCase):
    def test_every_core_scope_is_searched_once(self):
        with patch("helpdesk.management.commands.warm_retrieval.retrieve_chunks_with_trace", return_value=([], {})) as search:
            call_command("warm_retrieval", stdout=StringIO())
        self.assertEqual([c.kwargs["scope"] for c in search.call_args_list], [["NeTEx"], ["SIRI"], ["OpRa"], ["Transmodel"], None])

    def test_a_failure_never_fails_the_command(self):
        out = StringIO()
        with patch("helpdesk.management.commands.warm_retrieval.retrieve_chunks_with_trace", side_effect=RuntimeError("db down")):
            call_command("warm_retrieval", stdout=out)
        self.assertIn("warm-up failed", out.getvalue())
