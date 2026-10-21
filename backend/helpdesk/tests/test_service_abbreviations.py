from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services import retrieval_gateway, service_abbreviations
from helpdesk.services.service_abbreviations import build_services, expand_abbreviations, services_in_question

README = """
- Vehicle Monitoring (SIRI-VM), for the provision of information on the current location of vehicles,
- Connection Monitoriting (SIRI-CM), for informing a receiving system about a feeder arrival,
- Control Actions (SIRI-CA), for the exchange of information about decisions made by operators.
"""
PATHS = [
    "xsd/siri_vehicleMonitoring_service.xsd",
    "xsd/siri_connectionMonitoring_service.xsd",
    "xsd/siri_controlAction_service.xsd",
    "xsd/siri_controlAction_service.xsd",
    "xsd/siri_model/siri_journey.xsd",
]


class BuildServicesTests(SimpleTestCase):
    def setUp(self):
        self.table = build_services([README], PATHS)

    def test_reads_name_and_abbreviation_from_the_readme(self):
        self.assertEqual(self.table["SIRI-CA"].name, "Control Actions")
        self.assertEqual(self.table["SIRI-VM"].name, "Vehicle Monitoring")

    def test_links_each_service_to_its_schema_once(self):
        self.assertEqual(self.table["SIRI-CA"].schema_paths, ("xsd/siri_controlAction_service.xsd",))
        self.assertEqual(self.table["SIRI-VM"].schema_paths, ("xsd/siri_vehicleMonitoring_service.xsd",))

    def test_tolerates_a_spelling_slip_in_the_readme(self):
        self.assertEqual(self.table["SIRI-CM"].schema_paths, ("xsd/siri_connectionMonitoring_service.xsd",))


class QuestionTests(SimpleTestCase):
    table = build_services([README], PATHS)

    def test_finds_services_in_order_and_case_insensitively(self):
        found = services_in_question("Overlaps between siri-ca and SIRI-VM?", self.table)
        self.assertEqual([s.abbreviation for s in found], ["SIRI-CA", "SIRI-VM"])

    def test_unknown_abbreviation_is_ignored(self):
        self.assertEqual(services_in_question("What is SIRI-XY?", self.table), [])

    def test_expansion_adds_the_name_once(self):
        found = services_in_question("SIRI-CA and SIRI-VM", self.table)
        expanded = expand_abbreviations("SIRI-CA and SIRI-VM", found)
        self.assertEqual(expanded, "SIRI-CA (Control Actions) and SIRI-VM (Vehicle Monitoring)")
        self.assertEqual(expand_abbreviations(expanded, found), expanded)


class SourceCoverageTests(SimpleTestCase):
    def test_comparison_gets_a_chunk_from_each_service_schema(self):
        definition = {"docType": "ontology-definition", "sourcePath": "x.ttl"}
        vm = [{"docType": "schema", "sourcePath": "xsd/siri_vehicleMonitoring_service.xsd", "n": i} for i in range(4)]
        ca = {"docType": "schema", "sourcePath": "xsd/siri_controlAction_service.xsd"}
        selected = [definition, *vm]
        groups = [{"xsd/siri_controlAction_service.xsd"}, {"xsd/siri_vehicleMonitoring_service.xsd"}]

        result = retrieval_gateway._ensure_source_coverage(selected, selected + [ca], groups, top_k=4)

        self.assertIs(result[0], definition)
        self.assertEqual({c["sourcePath"] for c in result[1:3]}, {p for g in groups for p in g})

    def test_single_service_question_is_left_alone(self):
        selected = [{"sourcePath": "a"}, {"sourcePath": "b"}]
        self.assertEqual(retrieval_gateway._ensure_source_coverage(selected, selected, [{"b"}], 2), selected)

    def test_path_hints_use_the_service_schema(self):
        table = build_services([README], PATHS)
        with patch.object(service_abbreviations, "service_table", return_value=table):
            hints = retrieval_gateway._question_path_hints("What is SIRI-CA?")
        self.assertEqual(hints, {"xsd/siri_controlaction_service.xsd"})
