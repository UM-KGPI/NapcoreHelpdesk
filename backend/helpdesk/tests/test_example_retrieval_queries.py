"""The SPARQL that example_retrieval sends to GraphDB must be valid SPARQL 1.1 (it once used SQL's CASE: HTTP 400)."""

from __future__ import annotations

import re
from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services import example_retrieval

CONCEPTS = {"netex:TemplateServiceJourney", "opra:DelayedJourney"}


def _rows(*matches):
    return {
        "results": {
            "bindings": [
                {
                    "example": {"value": f"https://napcore.eu/example/{i}"},
                    "concept": {"value": "https://netex.org.uk/netex/2.0#TemplateServiceJourney"},
                    "source": {"value": "examples%2Fa.xml"},
                    "matchType": {"value": match},
                }
                for i, match in enumerate(matches)
            ]
        }
    }


class FallbackQueryTests(SimpleTestCase):
    def _sent_queries(self, answers):
        sent = []

        def fake(*, sparql_query, **_):
            sent.append(sparql_query)
            return answers[len(sent) - 1]

        with patch("helpdesk.services.graphdb_client.execute_sparql_query", side_effect=fake):
            result = example_retrieval.retrieve_concept_examples_with_fallback(CONCEPTS, endpoint="http://g", repository="r")
        return sent, result

    def test_the_fallback_query_uses_no_sql_case_expression(self):
        sent, _ = self._sent_queries([None, None])  # no exact examples, then the fallback

        self.assertEqual(len(sent), 2)
        fallback = sent[1]
        self.assertIsNone(re.search(r"\b(CASE|WHEN|THEN|ELSE|END)\b", re.sub(r"#[^\n]*", "", fallback)))
        self.assertIn('IF(?matchType = "direct_example", 1, IF(?matchType = "template_realization", 2, 3))', fallback)

    def test_every_query_parses_as_sparql(self):
        from rdflib.plugins.sparql import prepareQuery

        sent, _ = self._sent_queries([None, None])
        for query in sent:
            prepareQuery(query)

    def test_fallback_rows_are_returned_deduplicated_in_the_order_given(self):
        rows = _rows("direct_example", "template_realization")
        rows["results"]["bindings"].append(rows["results"]["bindings"][0])  # the same example twice
        _, result = self._sent_queries([None, rows])

        self.assertEqual([r["match_type"] for r in result], ["direct_example", "template_realization"])

    def test_an_exact_match_sends_no_fallback_query(self):
        sent, result = self._sent_queries([_rows("direct_example")])

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(result), 1)
