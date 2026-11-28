"""The reference ("oracle") cards of the class card and the questions that need one of their lines
(an internal plan (kept outside the repository), step 0).

The facts of the cards were checked against the Enterprise Architect files by direct SQL when they were written;
the model files are not in the repository, so this test checks only the form of the data: how many cards of which
kind, that each text fits the cap, that each question names a line of a card that is there.
"""

from __future__ import annotations

import unittest

import yaml
from django.test import SimpleTestCase

from helpdesk.management.commands.benchmark_utils import local_benchmark_file

CAP = 2400
NEW_QUESTIONS = ("dx18", "dx19", "tm01", "tm02", "tm03", "tm04")


ORACLE = local_benchmark_file("class-card-oracle.yaml")
QUESTIONS = local_benchmark_file("new-source-questions.yaml")


class ClassCardOracleTests(SimpleTestCase):
    """These tests check the form of the reference data itself, so they only make sense on the real files, which are
    kept outside the repository (HELPDESK_BENCHMARKS_DIR); without them every test is skipped, with this reason."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not (ORACLE.is_file() and QUESTIONS.is_file()):
            raise unittest.SkipTest(f"{ORACLE.name} and {QUESTIONS.name} are kept outside the repository (not found in {ORACLE.parent})")
        cls.cards = yaml.safe_load(ORACLE.read_text(encoding="utf-8"))["cards"]
        questions = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["questions"]
        cls.questions = {q["id"]: q for q in questions}

    def test_twelve_cards_of_the_planned_kinds(self):
        self.assertEqual(len(self.cards), 12)
        self.assertEqual(len({c["id"] for c in self.cards}), 12)
        self.assertEqual(sum(c["ontology"] == "DATEX II" for c in self.cards), 7)
        self.assertEqual(sum(c["ontology"] == "Transmodel" for c in self.cards), 5)
        # two with a long enumeration (more than 15 values: the card shows 15 and says how many are left out)
        long_enumeration = [c for c in self.cards if any("more, not shown" in line and ("values of" in line or line.startswith("Values (")) for line in c["text"])]
        self.assertGreaterEqual(len(long_enumeration), 2)
        # two with three or more supertype levels that carry members
        chains = [c for c in self.cards if len(c["inherited"]) >= 3]
        self.assertGreaterEqual(len(chains), 2)

    def test_every_card_fits_the_cap_and_is_closed_by_a_source_line(self):
        for card in self.cards:
            with self.subTest(card=card["id"]):
                self.assertEqual(card["length"], len("\n".join(card["text"])))
                self.assertLessEqual(card["length"], CAP)
                self.assertTrue(card["text"][0].startswith(card["ontology"]))
                self.assertTrue(card["text"][-1].startswith("Source: docs/ontology/standards/"))

    def test_a_card_that_cuts_something_says_so_in_its_last_line(self):
        for card in self.cards:
            with self.subTest(card=card["id"]):
                cut = any("more, not shown" in line for line in card["text"])
                self.assertEqual(cut, "left out:" in card["text"][-1])

    def test_each_new_question_names_a_line_of_an_oracle_card(self):
        by_id = {c["id"]: c for c in self.cards}
        for qid in NEW_QUESTIONS:
            with self.subTest(question=qid):
                question = self.questions[qid]
                self.assertIn(question["card"], by_id)
                self.assertIn(question["card_line"], by_id[question["card"]]["text"])
                self.assertTrue(question["expected_source_patterns"])
                self.assertTrue(question["question"].endswith("?"))

    def test_four_new_transmodel_questions_and_two_new_datex_questions(self):
        self.assertEqual([q for q in NEW_QUESTIONS if q.startswith("tm")], ["tm01", "tm02", "tm03", "tm04"])
        for qid in ("dx18", "dx19"):
            self.assertEqual(self.questions[qid]["fitting_scope"], ["DATEX II"])
        for qid in ("tm01", "tm02", "tm03", "tm04"):
            self.assertEqual(self.questions[qid]["fitting_scope"], ["Transmodel"])
