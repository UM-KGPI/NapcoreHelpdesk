from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.transmodel_guids import SECTION_MARKER, guid_section, read_guid_section

TTL = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix tm: <https://transmodel-cen.eu/6.2/> .

tm:SINGLE_JOURNEY a owl:Class .
"""


class TransmodelGuidTests(SimpleTestCase):
    def test_one_line_per_class_with_a_guid_in_the_order_given(self):
        section = guid_section(
            ["SINGLE_JOURNEY", "UNKNOWN_CLASS", "VEHICLE_EQUIPMENT_PROFILE_12709"],
            {"SINGLE_JOURNEY": ["{SJ}"], "VEHICLE_EQUIPMENT_PROFILE_12709": ["{VEP-10}"]},
            "model.qea",
        )

        self.assertTrue(section.startswith("\n" + SECTION_MARKER + "\n# Source: model.qea, classes below the"))
        self.assertIn("@prefix tmalign: <https://napcore.eu/ontology/transmodel-alignment#> .\n\n", section)
        lines = [line for line in section.splitlines() if line.startswith("tm:")]
        self.assertEqual(
            lines,
            [
                'tm:SINGLE_JOURNEY tmalign:eaGuid "{SJ}" .',
                'tm:VEHICLE_EQUIPMENT_PROFILE_12709 tmalign:eaGuid "{VEP-10}" .',
            ],
        )

    def test_the_section_is_read_back_without_braces(self):
        text = TTL + guid_section(
            ["SINGLE_JOURNEY", "VEHICLE_EQUIPMENT_PROFILE_12709"],
            {"SINGLE_JOURNEY": ["{SJ}"], "VEHICLE_EQUIPMENT_PROFILE_12709": ["{VEP-10}"]},
            "model.qea",
        )

        guids = read_guid_section(text)

        self.assertEqual(guids["SINGLE_JOURNEY"], "SJ")
        self.assertEqual(guids["VEHICLE_EQUIPMENT_PROFILE_12709"], "VEP-10")
        self.assertEqual(read_guid_section(TTL), {})
