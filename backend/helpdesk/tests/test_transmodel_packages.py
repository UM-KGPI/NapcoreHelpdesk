from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from helpdesk.services.transmodel_packages import SECTION_MARKER, add_package_section, read_package_paths

TTL = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix tm: <https://transmodel-cen.eu/6.2/> .

tm:SINGLE_JOURNEY a owl:Class .
tm:PRE_ASSIGNED_FARE_PRODUCT a owl:Class .
tm:VEHICLE_EQUIPMENT_PROFILE a owl:Class .
tm:VEHICLE_EQUIPMENT_PROFILE_12709 a owl:Class .
tm:UNKNOWN_CLASS a owl:Class .
"""


def _model(path: Path) -> Path:
    """A minimal Enterprise Architect model: t_package and t_object, as in a .qea file."""
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
        CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Package_ID INTEGER);
        INSERT INTO t_package VALUES (1, 'Transmodel v6.2  2024', 0), (2, 'Part 10 - Alternative Modes (NM)', 1),
            (3, 'SJ Single Journey Service MODEL', 2), (4, 'Part 1 - Common Concepts (CC)', 1),
            (5, 'RC Vehicle Type MODEL', 4), (6, 'NeTEx XSD Physical Models 2023', 0),
            (7, 'Part 5 - Fare Management (FM)', 1);
        INSERT INTO t_object VALUES (8552, 'SINGLE JOURNEY', 'Class', 3), (1, 'SINGLE JOURNEY', 'Class', 6),
            (6651, 'VEHICLE EQUIPMENT PROFILE', 'Class', 5), (12709, 'VEHICLE EQUIPMENT PROFILE', 'Class', 3),
            (3000, 'PRE-ASSIGNED FARE PRODUCT', 'Class', 7), (3001, 'A NOTE', 'Note', 3);
        """
    )
    db.commit()
    db.close()
    return path


class TransmodelPackageTests(SimpleTestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        self.paths = read_package_paths(_model(Path(self._dir.name) / "model.qea"))

    def tearDown(self):
        self._dir.cleanup()

    def test_each_class_gets_its_own_package(self):
        text, counts = add_package_section(TTL, self.paths, "model.qea")

        self.assertIn(
            'tm:SINGLE_JOURNEY tmalign:transmodelPackage "Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL" .',
            text,
        )
        # Hyphens in the model name become underscores in the tm: name.
        self.assertIn('tm:PRE_ASSIGNED_FARE_PRODUCT tmalign:transmodelPackage "Part 5 - Fare Management (FM)" .', text)
        # The same name twice: the suffixed class is the object with that id, the plain one the other.
        self.assertIn(
            'tm:VEHICLE_EQUIPMENT_PROFILE tmalign:transmodelPackage "Part 1 - Common Concepts (CC) > RC Vehicle Type MODEL" .',
            text,
        )
        self.assertIn(
            'tm:VEHICLE_EQUIPMENT_PROFILE_12709 tmalign:transmodelPackage "Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL" .',
            text,
        )
        self.assertEqual(counts["missing"], ["UNKNOWN_CLASS"])

    def test_classes_of_other_models_in_the_file_are_ignored(self):
        self.assertEqual(list(self.paths["SINGLE_JOURNEY"].values()), ["Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL"])

    def test_a_rerun_replaces_the_section_and_keeps_the_rest(self):
        once, _ = add_package_section(TTL, self.paths, "model.qea")
        twice, _ = add_package_section(once, self.paths, "model.qea")

        self.assertEqual(once, twice)
        self.assertEqual(once.count(SECTION_MARKER), 1)
        self.assertTrue(once.startswith(TTL.rstrip()))


class TransmodelPackageEvidenceTests(SimpleTestCase):
    def test_definition_evidence_names_the_package(self):
        from helpdesk.services.ontology_evidence import format_definitions_as_chunks

        chunks = format_definitions_as_chunks(
            [
                {
                    "concept": "https://transmodel-cen.eu/6.2/SINGLE_JOURNEY",
                    "definition": "The planned movement of any type of vehicle.",
                    "prefLabel": "SINGLE JOURNEY",
                    "package": "Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL",
                },
                {
                    "concept": "https://netex.org.uk/netex/2.0#SingleJourney",
                    "definition": "A JOURNEY of a VEHICLE.",
                    "tm_concept": "https://transmodel-cen.eu/6.2/SINGLE_JOURNEY_PATH",
                    "tm_definition": "A path for a SINGLE JOURNEY.",
                    "tm_package": "Part 10 - Alternative Modes (NM) > SJ Single Journey Path MODEL",
                },
            ]
        )
        texts = [chunk["text"] for chunk in chunks]

        self.assertTrue(any("Transmodel package: Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL" in t for t in texts))
        self.assertTrue(any("Transmodel package: Part 10 - Alternative Modes (NM) > SJ Single Journey Path MODEL" in t for t in texts))

    def test_query_results_carry_the_package(self):
        from unittest.mock import patch

        from helpdesk.services.ontology_evidence import retrieve_concept_definitions

        binding = {
            "concept": {"value": "https://transmodel-cen.eu/6.2/SINGLE_JOURNEY"},
            "type": {"value": "http://www.w3.org/2002/07/owl#Class"},
            "ownComment": {"value": "The planned movement of any type of vehicle."},
            "ownPackage": {"value": "Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL"},
        }
        with patch(
            "helpdesk.services.graphdb_client.execute_sparql_query", return_value={"results": {"bindings": [binding]}}
        ) as query:
            definitions = retrieve_concept_definitions({"transmodel:SINGLE_JOURNEY"}, endpoint="http://graphdb", repository="r")

        self.assertIn("tmalign:transmodelPackage", query.call_args.kwargs["sparql_query"])
        self.assertEqual(definitions[0]["package"], "Part 10 - Alternative Modes (NM) > SJ Single Journey Service MODEL")
