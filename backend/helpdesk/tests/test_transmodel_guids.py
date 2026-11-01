from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from helpdesk.services.transmodel_guids import SECTION_MARKER, add_guid_section, read_guid_section, read_guids

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
        CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Package_ID INTEGER, ea_guid TEXT);
        INSERT INTO t_package VALUES (1, 'Transmodel v6.2  2024', 0), (2, 'Part 10 - Alternative Modes (NM)', 1),
            (3, 'SJ Single Journey Service MODEL', 2), (4, 'Part 1 - Common Concepts (CC)', 1),
            (5, 'RC Vehicle Type MODEL', 4), (6, 'NeTEx XSD Physical Models 2023', 0),
            (7, 'Part 5 - Fare Management (FM)', 1);
        INSERT INTO t_object VALUES (8552, 'SINGLE JOURNEY', 'Class', 3, '{SJ}'), (1, 'SINGLE JOURNEY', 'Class', 6, '{NETEX-SJ}'),
            (6651, 'VEHICLE EQUIPMENT PROFILE', 'Class', 5, '{VEP-1}'),
            (12709, 'VEHICLE EQUIPMENT PROFILE', 'Class', 3, '{VEP-10}'),
            (3000, 'PRE-ASSIGNED FARE PRODUCT', 'Class', 7, '{PAFP}'), (3001, 'A NOTE', 'Note', 3, '{NOTE}');
        """
    )
    db.commit()
    db.close()
    return path


class TransmodelGuidTests(SimpleTestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        self.guids = read_guids(_model(Path(self._dir.name) / "model.qea"))

    def tearDown(self):
        self._dir.cleanup()

    def test_each_class_gets_its_own_guid(self):
        text, counts = add_guid_section(TTL, self.guids, "model.qea")

        self.assertIn('tm:SINGLE_JOURNEY tmalign:eaGuid "{SJ}" .', text)
        # Hyphens in the model name become underscores in the tm: name.
        self.assertIn('tm:PRE_ASSIGNED_FARE_PRODUCT tmalign:eaGuid "{PAFP}" .', text)
        # The same name twice: the suffixed class is the object with that id, the plain one the other.
        self.assertIn('tm:VEHICLE_EQUIPMENT_PROFILE tmalign:eaGuid "{VEP-1}" .', text)
        self.assertIn('tm:VEHICLE_EQUIPMENT_PROFILE_12709 tmalign:eaGuid "{VEP-10}" .', text)
        self.assertEqual(counts["missing"], ["UNKNOWN_CLASS"])

    def test_classes_of_other_models_in_the_file_are_ignored(self):
        self.assertEqual(list(self.guids["SINGLE_JOURNEY"].values()), ["{SJ}"])

    def test_a_rerun_replaces_the_section_and_keeps_the_rest(self):
        once, _ = add_guid_section(TTL, self.guids, "model.qea")
        twice, _ = add_guid_section(once, self.guids, "model.qea")

        self.assertEqual(once, twice)
        self.assertEqual(once.count(SECTION_MARKER), 1)
        self.assertTrue(once.startswith(TTL.rstrip()))

    def test_the_section_is_read_back_without_braces(self):
        text, _ = add_guid_section(TTL, self.guids, "model.qea")

        guids = read_guid_section(text)

        self.assertEqual(guids["SINGLE_JOURNEY"], "SJ")
        self.assertEqual(guids["VEHICLE_EQUIPMENT_PROFILE_12709"], "VEP-10")
        self.assertEqual(read_guid_section(TTL), {})
