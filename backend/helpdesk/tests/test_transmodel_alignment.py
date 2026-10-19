from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

from django.test import SimpleTestCase

from helpdesk.services.transmodel_alignment import (
    clean_definition,
    definition_status,
    is_model_class,
    load_curation,
    plan_alignment,
    render_report,
    render_turtle,
    transmodel_to_camel,
)

# Real definitions (NeTEx XSD vs Transmodel v6.2) for the three reference cases.
TM_STOP_PLACE = (
    "A place comprising one or more locations where vehicles may stop and where passengers may "
    "board or leave vehicles or prepare their trip.  NOTE: A STOP PLACE will usually have one or "
    "more well-known names."
)
NETEX_STOP_PLACE = (
    "Version of a named place where public transport may be accessed. May be a building complex "
    "(e.g. a station) or an on-street location. Can be a STOP PLACE, VEHICLE MEETING POINT, TAXI RANK."
)
TM_QUAY = (
    "A place such as platform, stance, or quay side where passengers have access to PT vehicles, "
    "Taxis, cars or other means of transportation.  NOTE1: A QUAY may serve one or more VEHICLE "
    "STOPPING PLACEs and be associated with one or more SCHEDULED STOP POINTS.  NOTE2: A QUAY may "
    "contain other sub QUAYs.  NOTE3: A child QUAY must be physically contained within its parent QUAY."
)
NETEX_QUAY = (
    "A place such as platform, stance, or quayside where passengers have access to PT vehicles, "
    "Taxi cars or other means of transportation. A QUAY may contain other sub QUAYs. A child QUAY "
    "must be physically contained within its parent QUAY."
)
TM_SCHEDULED_STOP_POINT = "A POINT where passengers can board or alight from vehicles."
NETEX_SCHEDULED_STOP_POINT = (
    "A POINT where passengers can board or alight from vehicles. It is open, which hierarchical "
    "level such a point has. It can represent a single door (BoardingPosition) or a whole ZONE. "
    "The association to the physical model is done with STOP ASSIGNMENTs."
)


class NamingTests(SimpleTestCase):
    def test_transmodel_to_camel(self):
        self.assertEqual(transmodel_to_camel("STOP_PLACE"), "StopPlace")
        self.assertEqual(transmodel_to_camel("TYPE_OF_STOP_PLACE"), "TypeOfStopPlace")

    def test_only_upper_snake_model_classes_are_targets(self):
        self.assertTrue(is_model_class("STOP_PLACE"))
        self.assertFalse(is_model_class("stop"))  # glossary term
        self.assertFalse(is_model_class("Alpha"))  # placeholder
        self.assertFalse(is_model_class("SERVICE_ZONE_USE_ALLOWED_VALUES"))


class DefinitionStatusTests(SimpleTestCase):
    def test_reference_cases(self):
        self.assertEqual(definition_status(NETEX_STOP_PLACE, TM_STOP_PLACE)[0], "differs")
        self.assertEqual(definition_status(NETEX_QUAY, TM_QUAY)[0], "equivalent")
        self.assertEqual(
            definition_status(NETEX_SCHEDULED_STOP_POINT, TM_SCHEDULED_STOP_POINT)[0], "extends"
        )

    def test_missing_when_either_side_empty(self):
        self.assertEqual(definition_status("", TM_QUAY)[0], "missing")
        self.assertEqual(definition_status(NETEX_QUAY, "")[0], "missing")

    def test_html_from_ea_export_is_ignored(self):
        tm = '<font color="#0f0f0f">A set of parameters controlling pricing calculations.</font>'
        self.assertEqual(clean_definition(tm), "A set of parameters controlling pricing calculations.")
        self.assertEqual(
            definition_status("A set of parameters controlling pricing calculations.", tm)[0], "equivalent"
        )


class PlanAlignmentTests(SimpleTestCase):
    TM_CLASSES = {
        "STOP_PLACE": TM_STOP_PLACE,
        "QUAY": TM_QUAY,
        "SCHEDULED_STOP_POINT": TM_SCHEDULED_STOP_POINT,
        "stop": "a place where vehicles stop",
    }

    def test_aligns_by_name_and_reports_unmatched(self):
        plan = plan_alignment(
            standard="netex",
            standard_classes={"StopPlace": NETEX_STOP_PLACE, "Quay": NETEX_QUAY, "QuayList": "", "Stop": ""},
            tm_classes=self.TM_CLASSES,
        )
        aligned = {row.standard_class: (row.tm_class, row.status, row.method) for row in plan.rows}
        self.assertEqual(aligned["StopPlace"], ("STOP_PLACE", "differs", "name-match"))
        self.assertEqual(aligned["Quay"], ("QUAY", "equivalent", "name-match"))
        # "Stop" must not match the lowercase glossary term tm:stop
        self.assertEqual(plan.unmatched, ["QuayList", "Stop"])

    def test_curation_adds_and_excludes(self):
        curation = [
            {"standard": "netex", "standard_class": "Quay", "tm_class": "QUAY", "action": "exclude", "note": ""},
            {"standard": "netex", "standard_class": "Stop", "tm_class": "STOP_PLACE", "action": "add", "note": "x"},
            {"standard": "siri", "standard_class": "StopPlace", "tm_class": "QUAY", "action": "exclude", "note": ""},
        ]
        plan = plan_alignment(
            standard="netex",
            standard_classes={"StopPlace": NETEX_STOP_PLACE, "Quay": NETEX_QUAY, "Stop": ""},
            tm_classes=self.TM_CLASSES,
            curation=curation,
        )
        aligned = {row.standard_class: (row.tm_class, row.method) for row in plan.rows}
        self.assertEqual(aligned, {"StopPlace": ("STOP_PLACE", "name-match"), "Stop": ("STOP_PLACE", "curated")})
        self.assertEqual(plan.unmatched, ["Quay"])

    def test_curated_unknown_transmodel_class_is_an_error(self):
        curation = [{"standard": "netex", "standard_class": "Quay", "tm_class": "NOPE", "action": "add", "note": ""}]
        with self.assertRaisesMessage(ValueError, "Curated Transmodel class not found"):
            plan_alignment(
                standard="netex", standard_classes={"Quay": NETEX_QUAY}, tm_classes=self.TM_CLASSES, curation=curation
            )

    def test_load_curation_skips_comments_and_validates_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "curation.csv"
            path.write_text(
                "# comment\nstandard,standard_class,tm_class,action,note\nnetex,Quay,QUAY,exclude,wrong\n",
                encoding="utf-8",
            )
            self.assertEqual(load_curation(path)[0]["action"], "exclude")
            path.write_text("standard,standard_class,tm_class,action,note\nnetex,Quay,QUAY,drop,\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_curation(path)
            self.assertEqual(load_curation(Path(tmp) / "absent.csv"), [])


class RenderTests(SimpleTestCase):
    def test_turtle_and_report(self):
        plan = plan_alignment(
            standard="netex",
            standard_classes={"StopPlace": NETEX_STOP_PLACE, "QuayList": ""},
            tm_classes={"STOP_PLACE": TM_STOP_PLACE},
        )
        turtle = render_turtle(plan, generated_on=date(2026, 10, 17))
        self.assertIn("netex:StopPlace\n    skos:exactMatch tm:STOP_PLACE ;", turtle)
        self.assertIn('tmalign:transmodelDefinitionStatus "differs" ;', turtle)
        self.assertIn("@prefix netex: <https://netex.org.uk/netex/2.0#> .", turtle)

        report = render_report([plan], generated_on=date(2026, 10, 17))
        self.assertIn("| NeTEx | 2 | 1 | 0 | 0 | 1 | 0 | 1 |", report)
        self.assertIn("| StopPlace | STOP_PLACE |", report)
        self.assertIn("QuayList", report)
