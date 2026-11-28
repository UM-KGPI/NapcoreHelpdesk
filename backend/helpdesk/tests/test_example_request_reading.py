from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk.management.commands import read_example_requests as command
from helpdesk.services import example_request_reading as reading

# The schema as the tests see it: /concrete answers by element name. Made-up names, so no test depends on NeTEx.
_SCHEMA = {
    "Gadget": ["Gadget"],
    "Sprocket": ["Sprocket"],
    "AbstractPart": ["Sprocket", "Lever"],
    "Lever": ["Lever"],
    "Colour": [],  # defined, but a property, not an object
}


def _lookup(name: str) -> list[str]:
    return list(_SCHEMA.get(name, []))


def _reply(payload: dict) -> str:
    return "```json\n" + json.dumps(payload) + "\n```"


class GroundingTests(SimpleTestCase):
    question = 'Make a sample of a gadget called "Alpha"  with three sprockets, started at 9:05 for 2 hours, only when it rains.'

    def ground(self, payload: dict):
        return reading.ground(payload, self.question, _lookup)

    def test_a_phrase_must_be_in_the_question(self):
        grounded, dropped = self.ground({
            "objects": [{"kind": "Sprocket", "count": 3, "phrase": "three sprockets"},
                        {"kind": "Lever", "count": None, "phrase": "a lever"}],
            "values": [{"value": "Beta", "phrase": "called \"Beta\""}],
            "conditions": [{"phrase": "only when it rains"}, {"phrase": "only on Sundays"}],
        })
        self.assertEqual([o["kind"] for o in grounded["objects"]], ["Sprocket"])
        self.assertEqual(grounded["values"], [])
        self.assertEqual(grounded["conditions"], [{"phrase": "only when it rains"}])
        self.assertEqual(sorted((d["field"], d["rule"]) for d in dropped), [("conditions", 1), ("objects", 1), ("values", 1)])

    def test_whitespace_is_folded_before_the_phrase_is_looked_up(self):
        grounded, dropped = self.ground({"values": [{"value": "Alpha", "phrase": 'called "Alpha" with'}]})
        self.assertEqual([v["value"] for v in grounded["values"]], ["Alpha"])
        self.assertEqual(dropped, [])

    def test_a_value_is_in_its_phrase_or_is_its_normal_form(self):
        grounded, dropped = self.ground({"values": [
            {"value": "Alpha", "phrase": 'called "Alpha"'},
            {"value": "09:05", "phrase": "at 9:05"},
            {"value": "PT2H", "phrase": "for 2 hours"},
            {"value": "PT7200S", "phrase": "for 2 hours"},
            {"value": "PT3H", "phrase": "for 2 hours"},
            {"value": "Gamma", "phrase": 'called "Alpha"'},
        ]})
        self.assertEqual([v["value"] for v in grounded["values"]], ["Alpha", "09:05", "PT2H", "PT7200S"])
        self.assertEqual([(d["entry"]["value"], d["rule"]) for d in dropped], [("PT3H", 2), ("Gamma", 2)])

    def test_an_unknown_or_non_object_kind_is_stripped_and_the_entry_kept(self):
        grounded, dropped = self.ground({
            "asked": "Widget",
            "objects": [{"kind": "Cog", "count": 3, "phrase": "three sprockets"},
                        {"kind": "Colour", "count": None, "phrase": "a gadget"}],
            "values": [{"value": "Alpha", "phrase": 'called "Alpha"', "of": "Cog"}],
        })
        self.assertEqual(grounded["asked"], "")
        self.assertEqual([(o["kind"], o["count"], o["phrase"]) for o in grounded["objects"]],
                         [("", 3, "three sprockets"), ("", None, "a gadget")])
        self.assertEqual(grounded["values"][0]["of"], "")
        self.assertEqual([(d["field"], d["action"]) for d in dropped],
                         [("asked", "stripped"), ("objects", "kind stripped"), ("objects", "kind stripped"), ("values", "of stripped")])

    def test_an_abstract_kind_stands_for_its_concrete_objects(self):
        grounded, _ = self.ground({"asked": "AbstractPart"})
        self.assertEqual((grounded["asked"], grounded["askedKinds"]), ("AbstractPart", ["Sprocket", "Lever"]))

    def test_a_count_must_be_written_in_its_phrase(self):
        grounded, dropped = self.ground({"objects": [
            {"kind": "Sprocket", "count": 3, "phrase": "three sprockets"},
            {"kind": "Sprocket", "count": 2, "phrase": "three sprockets"},
            {"kind": "Lever", "count": 0, "phrase": "a gadget"},
            {"kind": "Gadget", "count": 1, "phrase": "a gadget"},
        ]})
        self.assertEqual([o["count"] for o in grounded["objects"]], [3, None, None, None])
        self.assertEqual([d["rule"] for d in dropped], [4, 4, 4])

    def test_count_in_phrase(self):
        self.assertTrue(reading.count_in_phrase(2, "with 2 trays"))
        self.assertTrue(reading.count_in_phrase(12, "twelve trays"))
        self.assertFalse(reading.count_in_phrase(2, "with 12 trays"))
        self.assertFalse(reading.count_in_phrase(True, "one tray"))
        self.assertFalse(reading.count_in_phrase("2", "2 trays"))


@override_settings(LLM_ENABLED=True)
class ReadRequestTests(SimpleTestCase):
    def test_the_reply_is_parsed_and_grounded(self):
        payload = {"asked": "Gadget", "objects": [{"kind": "Sprocket", "count": 3, "phrase": "three sprockets"}],
                   "values": [{"value": "Alpha", "phrase": '"Alpha"', "of": "Gadget"}], "conditions": []}
        with patch.object(reading, "_call_model", return_value=_reply(payload)) as call:
            result = reading.read_request('A gadget "Alpha" with three sprockets', lookup=_lookup)
        self.assertTrue(result["ok"])
        self.assertEqual(result["asked"], "Gadget")
        self.assertEqual(result["objects"][0]["count"], 3)
        self.assertEqual(result["values"][0]["value"], "Alpha")
        self.assertIsInstance(result["ms"], int)
        self.assertNotIn("candidates", call.call_args.args[0][1]["content"].lower())

    def test_candidates_go_into_the_request(self):
        with patch.object(reading, "_call_model", return_value="{}") as call:
            reading.read_request("A gadget", candidates=["Gadget", "Sprocket"], lookup=_lookup)
        self.assertIn("Gadget, Sprocket", call.call_args.args[0][1]["content"])

    def test_a_failed_call_or_a_reply_without_json_is_not_ok(self):
        with patch.object(reading, "_call_model", side_effect=RuntimeError("503")):
            failed = reading.read_request("A gadget", lookup=_lookup)
        with patch.object(reading, "_call_model", return_value="I cannot tell."):
            no_json = reading.read_request("A gadget", lookup=_lookup)
        self.assertFalse(failed["ok"])
        self.assertIn("503", failed["error"])
        self.assertFalse(no_json["ok"])
        self.assertEqual(no_json["objects"], [])

    def test_the_schema_lookup_down_is_a_failed_reading_not_an_unknown_kind(self):
        def down(name):
            raise reading.LookupUnavailable("refused")

        with patch.object(reading, "_call_model", return_value='{"asked": "Gadget"}'):
            result = reading.read_request("A gadget", lookup=down)
        self.assertFalse(result["ok"])
        self.assertIn("schema lookup", result["error"])

    def test_the_prompt_names_no_netex_element(self):
        from helpdesk.services.netex_example_generator import _ELEMENT_NAME

        names = set(_ELEMENT_NAME.findall(reading._PROMPT)) - {"UpperCamelCase", "NeTEx"}
        self.assertEqual(names, set())


class ScoringTests(SimpleTestCase):
    def setUp(self):
        self.expand = command.Expander(lookup=_lookup)

    def score(self, predicted: dict, gold: dict) -> dict:
        return command.score_reading({"ok": True, **predicted}, gold, self.expand)

    def test_asked_matches_through_the_concrete_objects(self):
        gold = {"asked": "AbstractPart", "objects": [], "values": []}
        self.assertEqual(self.score({"asked": "Lever"}, gold)["asked"], 1)
        self.assertEqual(self.score({"asked": "Gadget"}, gold)["asked"], 0)
        self.assertEqual(self.score({"asked": ""}, {"asked": ""})["asked"], 1)
        self.assertEqual(self.score({"asked": "Gadget"}, {"asked": ""})["asked"], 0)
        self.assertEqual(self.score({"asked": "Gadget"}, {"asked": ["Sprocket", "Gadget"]})["asked"], 1)

    def test_objects_pair_one_to_one_on_kind_and_count(self):
        gold = {"asked": "Gadget", "objects": [{"kind": "Sprocket", "count": 3}, {"kind": "Lever", "count": None}]}
        right = {"asked": "Gadget", "objects": [{"kind": "Lever", "count": None}, {"kind": "Sprocket", "count": 3}]}
        wrong_count = {"asked": "Gadget", "objects": [{"kind": "Lever", "count": None}, {"kind": "Sprocket", "count": 2}]}
        extra = {"asked": "Gadget", "objects": right["objects"] + [{"kind": "Gadget", "count": None}, {"kind": "Sprocket", "count": None}]}
        kindless = {"asked": "Gadget", "objects": right["objects"] + [{"kind": "", "count": 4}]}
        self.assertEqual(self.score(right, gold)["objects"], 1)
        self.assertEqual(self.score(wrong_count, gold)["objects"], 0)
        self.assertEqual(self.score(wrong_count, gold)["counts"], 0)
        # the asked object listed again is ignored; a second sprocket is not
        self.assertEqual(self.score(extra, gold)["objects"], 0)
        self.assertEqual(self.score(kindless, gold)["objects"], 1)

    def test_pattern_objects_with_several_kinds_match_any(self):
        gold = {"objects": [{"kind": ["Sprocket", "Cog"], "count": 2}]}
        self.assertEqual(self.score({"objects": [{"kinds": ["Lever", "Sprocket"], "count": 2}]}, gold)["objects"], 1)

    def test_values_match_as_sets_with_normal_forms_and_spellings(self):
        gold = {"values": ["Alpha", "09:05", "PT2H", ["Beta", "Beta station"]]}
        right = {"values": [{"value": "beta station"}, {"value": "PT7200S"}, {"value": "9:05"}, {"value": " Alpha "}]}
        self.assertEqual(self.score(right, gold)["values"], 1)
        self.assertEqual(self.score({"values": right["values"] + [{"value": "3"}]}, gold)["values"], 0)
        self.assertEqual(self.score({"values": right["values"][:3]}, gold)["values"], 0)
        self.assertEqual(command.normal_value("2 hours"), command.normal_value("PT2H"))

    def test_a_failed_reading_is_wrong_on_every_field(self):
        scored = command.score_reading({"ok": False}, {"asked": "", "objects": [], "values": []}, self.expand)
        self.assertEqual(set(scored.values()), {0})

    def test_summary_scores_agreement_and_gate(self):
        gold = [
            {"id": "a", "question": "q1", "asked": "Gadget", "objects": [{"kind": "Sprocket", "count": 3}], "values": ["Alpha"]},
            {"id": "b", "question": "q2", "asked": "Lever", "objects": [], "values": []},
            {"id": "c", "question": "q3", "asked": "Gadget", "objects": [], "values": [], "unsure": True},
        ]
        good_a = {"ok": True, "asked": "Gadget", "objects": [{"kind": "Sprocket", "count": 3}], "values": [{"value": "Alpha"}], "ms": 900, "dropped": []}
        bad_a = {**good_a, "objects": [], "ms": 1100, "dropped": [{"rule": 3, "action": "kind stripped"}]}
        good_b = {"ok": True, "asked": "Lever", "objects": [], "values": [], "ms": 800, "dropped": []}
        result = {
            "gold": gold,
            "patterns": {
                "a": {"ok": True, "asked": "Gadget", "objects": [], "values": [{"value": "Alpha"}]},
                "b": {"ok": True, "asked": "", "objects": [], "values": []},
                "c": {"ok": True, "asked": "", "objects": [], "values": []},
            },
            "readings": {"question": {"a": [good_a, good_a, bad_a], "b": [good_b] * 3, "c": [good_b] * 3}},
        }
        summary = command.summarise(result, self.expand)
        out = summary["variants"]["question"]
        self.assertEqual(summary["patterns"]["gated"]["asked"], 0.5)
        self.assertEqual(out["gated"]["asked"], 1.0)
        self.assertAlmostEqual(out["gated"]["objects"], (2 / 3 + 1) / 2, places=3)
        self.assertEqual(out["gated"]["agreement"], 0.5)
        self.assertEqual(out["unsure"]["asked"], 0.0)
        self.assertEqual(out["grounding"]["byRule"]["3"], 1)
        self.assertEqual(out["gate"]["clearlyBetterOn"], ["asked", "objects"])
        self.assertFalse(out["gate"]["agreementOk"])
        self.assertFalse(out["gate"]["passed"])
        self.assertIn("read more than one way: a", command.report({**result, "runs": 3, "summary": summary}))
