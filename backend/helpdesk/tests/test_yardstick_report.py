from __future__ import annotations

from django.core.management.base import CommandError
from django.test import SimpleTestCase

from helpdesk.management.commands import yardstick_report as yr


class StandardsNamedTests(SimpleTestCase):
    def test_names_standards_by_their_own_names(self):
        self.assertEqual(yr.standards_named("How does SIRI use NeTEx?"), ["NeTEx", "SIRI"])
        self.assertEqual(yr.standards_named("Describe an accident in DATEX II"), ["DATEX II"])

    def test_legislation_and_napcore_words_are_not_standards(self):
        self.assertEqual(yr.standards_named("What does the regulation say about a national access point?"), [])

    def test_no_name(self):
        self.assertEqual(yr.standards_named("How are lanes closed?"), [])


class RowsTests(SimpleTestCase):
    def test_bench_rank_from_top_paths(self):
        report = {"questions": [
            {"id": "q1", "question": "a", "expected_source_patterns": ["Foo.xsd"],
             "graph": {"top_6_paths": ["x/bar.xml", "x/foo.xsd"], "latency_ms": 10, "hit_at_6": True, "mrr_at_6": 0.5}},
            {"id": "q2", "question": "b", "expected_source_patterns": ["Nope"],
             "graph": {"top_6_paths": ["x/bar.xml"], "latency_ms": 30, "hit_at_6": False, "mrr_at_6": 0.0}},
            {"id": "q3", "question": "c", "expected_source_patterns": [], "min_hits": 0,
             "graph": {"top_6_paths": ["x/bar.xml"], "latency_ms": 30, "hit_at_6": True, "mrr_at_6": 0.0}},
        ]}
        rows = yr.bench_rows(report, "core")
        self.assertEqual([r["rank"] for r in rows], [2, None, None])
        self.assertEqual([r["found"] for r in rows], [True, False, True])  # the command's own hit flag
        self.assertEqual(yr.summarise(rows)["found_in_six"], 2)
        self.assertEqual(rows[0]["key"], "core:q1")

    def test_bench_missing_mode_is_an_error(self):
        with self.assertRaises(CommandError):
            yr.bench_rows({"questions": [{"id": "q1", "baseline": {}}]}, "core")

    def test_locate_rank_is_the_prompt_rank(self):
        report = {"questions": [{"id": "a01", "question": "q", "prompt": 1, "retrievalSeconds": 0.5},
                                {"id": "a02", "question": "r", "prompt": None, "retrievalSeconds": 1.5}]}
        rows = yr.locate_rows(report, "gold")
        self.assertEqual([r["rank"] for r in rows], [1, None])
        self.assertEqual(rows[1]["ms"], 1500.0)


class SummaryTests(SimpleTestCase):
    def test_summarise(self):
        rows = [{"rank": 1, "found": True, "mrr": 1.0, "ms": 10.0}, {"rank": 4, "found": True, "mrr": 0.25, "ms": 30.0},
                {"rank": None, "found": False, "mrr": 0.0, "ms": 20.0}]
        s = yr.summarise(rows)
        self.assertEqual((s["questions"], s["found_in_six"], s["first_place"]), (3, 2, 1))
        self.assertEqual(s["mrr_at_6"], round((1 + 0.25) / 3, 4))
        self.assertEqual(s["median_ms"], 20.0)

    def test_groups_by_label_extra_and_standard(self):
        rows = [
            {"key": "core:q1", "label": "core", "question": "What is SIRI?", "rank": 1, "found": True, "mrr": 1.0, "ms": 1.0},
            {"key": "core:q2", "label": "core", "question": "How are lanes closed?", "rank": None, "found": False, "mrr": 0.0, "ms": 1.0},
            {"key": "datex:d1", "label": "datex", "question": "Accident in DATEX II", "rank": 2, "found": True, "mrr": 0.5, "ms": 1.0},
        ]
        groups = yr.build_groups(rows, {"mix": ["core:q2", "datex:d1"]})
        self.assertEqual(len(groups["core"]), 2)
        self.assertEqual(len(groups["mix"]), 2)
        self.assertEqual(len(groups[yr.NAMES_STANDARD_GROUP]), 2)
        self.assertEqual(len(groups["names DATEX II"]), 1)

    def test_unknown_id_in_group_is_an_error(self):
        with self.assertRaises(CommandError):
            yr.build_groups([], {"g": ["core:zz"]})
