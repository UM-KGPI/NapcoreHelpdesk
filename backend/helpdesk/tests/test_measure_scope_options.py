from __future__ import annotations


import yaml
from django.test import SimpleTestCase

from helpdesk.api.serializers import STANDARDS_SCOPE_CHOICES
from helpdesk.management.commands.measure_scope_options import (
    BENCHMARKS,
    _scopes_named,
    _standards_in_rank_order,
)


class ScopeOptionHelpersTests(SimpleTestCase):
    def test_standards_come_in_the_order_of_their_first_chunk(self):
        chunks = [
            {"standardsScope": ["NeTEx"]},
            {"standardsScope": ["SIRI", "NeTEx"]},
            {"standardsScope": ["unknown"]},
            {"standardsScope": ["EU legislation"]},
        ]
        self.assertEqual(_standards_in_rank_order(chunks), ["NeTEx", "SIRI", "EU legislation"])

    def test_scope_names_are_read_from_a_json_list_in_order(self):
        self.assertEqual(_scopes_named('["EU legislation", "NeTEx", "DATEX II"]'), ["EU legislation", "NeTEx", "DATEX II"])
        self.assertEqual(_scopes_named("[]"), [])
        self.assertEqual(_scopes_named('["Netex"]'), [])

    def test_fitting_scopes_are_scope_values_of_answerable_questions(self):
        fitting = yaml.safe_load((BENCHMARKS / "refused-questions-scopes.yaml").read_text())["questions"]
        questions = yaml.safe_load((BENCHMARKS / "refused-questions.yaml").read_text())["questions"]
        answerable = {q["id"] for q in questions if q["expect"] == "answer"}
        self.assertEqual({row["id"] for row in fitting}, answerable)
        for row in fitting:
            self.assertTrue(row["fit"] and row["sources"], row["id"])
            self.assertTrue(set(row["fit"]) <= set(STANDARDS_SCOPE_CHOICES), row["id"])
