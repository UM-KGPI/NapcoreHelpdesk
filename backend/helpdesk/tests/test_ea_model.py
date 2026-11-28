"""Tests for the general Enterprise Architect reader (services/ea_model.py) on a small model built in the test."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from helpdesk.services import ea_model


def _model_file(path: Path) -> None:
    """Two roots; the first has two parts, one of them nested. Notes with line breaks; connectors of four kinds."""
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
        CREATE TABLE t_object (Object_ID INTEGER PRIMARY KEY, Name TEXT, Object_Type TEXT COLLATE NOCASE,
                               Stereotype TEXT, Package_ID INTEGER, Note TEXT, PDATA1 TEXT, ea_guid TEXT);
        CREATE TABLE t_objectproperties (Object_ID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_attribute (ID INTEGER, Object_ID INTEGER, Name TEXT, Type TEXT, LowerBound TEXT,
                                  UpperBound TEXT, Pos INTEGER);
        CREATE TABLE t_attributetag (ElementID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_connector (Connector_ID INTEGER PRIMARY KEY, Connector_Type TEXT, Start_Object_ID INTEGER,
                                  End_Object_ID INTEGER, DestRole TEXT, DestCard TEXT, SourceRole TEXT,
                                  SourceCard TEXT, SourceIsAggregate INTEGER, DestIsAggregate INTEGER);
        INSERT INTO t_package VALUES (1, 'Model  One', 0), (2, 'Part 1 Common', 1), (3, 'Sub', 2),
            (4, 'Glossary', 1), (5, 'Other Root', 0);
        INSERT INTO t_object VALUES
            (30, 'B', 'Class', '', 3, '  Line one' || char(13) || char(10) || 'line two  ', NULL, '{B}'),
            (10, 'A', 'Class', '', 2, 'A note<br/>with   a break', NULL, '{A}'),
            (20, 'G', 'Class', '', 4, '', NULL, '{G}'),
            (40, 'X', 'Class', '', 5, '', NULL, '{X}'),
            (50, 'E', 'Enumeration', '', 2, '', NULL, '{E}'),
            (60, 'N', 'Note', '', 2, '', NULL, '{N}');
        INSERT INTO t_objectproperties VALUES (10, 'definition', 'Tagged definition.', NULL);
        INSERT INTO t_attribute VALUES (1, 10, 'size', 'int', '0', '1', 1);
        INSERT INTO t_attributetag VALUES (1, 'definition', 'The size.', NULL);
        INSERT INTO t_connector (Connector_Type, Start_Object_ID, End_Object_ID, DestRole, DestCard, SourceRole,
                                 SourceCard, SourceIsAggregate, DestIsAggregate) VALUES
            ('Generalization', 30, 10, NULL, NULL, NULL, NULL, 0, 0),
            ('Association', 10, 30, 'b', '0..1', 'a', '1', 0, 0),
            ('Dependency', 10, 30, NULL, NULL, NULL, NULL, 0, 0),
            ('NoteLink', 60, 10, NULL, NULL, NULL, NULL, 0, 0),
            ('Association', 10, 40, 'x', NULL, NULL, NULL, 0, 0),
            ('Aggregation', 20, 10, NULL, NULL, NULL, NULL, 0, 2);
        """
    )
    db.commit()
    db.close()


class ReaderTests(SimpleTestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        self.path = Path(self._dir.name) / "model.qea"
        _model_file(self.path)

    def tearDown(self):
        self._dir.cleanup()

    def test_no_patterns_keep_every_element_of_the_types_in_object_id_order(self):
        model = ea_model.read_model(self.path, ea_model.Profile(element_types=("Class",)))
        self.assertEqual(list(model.elements), [10, 20, 30, 40])

    def test_package_patterns_all_have_to_match_the_whitespace_collapsed_path(self):
        profile = ea_model.Profile(element_types=("Class",), package_path_patterns=(r"model one", r"\bPart 1\b"))
        model = ea_model.read_model(self.path, profile)
        self.assertEqual(list(model.elements), [10, 30])
        self.assertEqual(model.package_path(3), "Model  One > Part 1 Common > Sub")
        root = ea_model.Profile(element_types=("Class",), package_path_patterns=(r"^Model One(?: > |$)",))
        self.assertEqual(list(ea_model.read_model(self.path, root).elements), [10, 20, 30])

    def test_an_excluded_package_leaves_out_everything_below_it(self):
        glossary = ea_model.Profile(element_types=("Class",), excluded_packages=("glossary",))
        self.assertEqual(list(ea_model.read_model(self.path, glossary).elements), [10, 30, 40])
        # Part 1 holds A directly and B in its sub-package; names compare with whitespace collapsed.
        part = ea_model.Profile(
            element_types=("Class",), package_path_patterns=(r"^Model One",), excluded_packages=("Part  1 Common",)
        )
        self.assertEqual(list(ea_model.read_model(self.path, part).elements), [20])

    def test_a_connector_is_kept_only_between_two_kept_elements(self):
        profile = ea_model.Profile(element_types=("Class",), package_path_patterns=(r"^Model One(?: > |$)",))
        model = ea_model.read_model(self.path, profile)
        self.assertEqual([(c.start, c.end) for c in model.generalizations], [(30, 10)])
        # The association to X (another root) is left out; the note link has no kept end.
        self.assertEqual([(c.type, c.start, c.end) for c in model.relations],
                         [("Association", 10, 30), ("Dependency", 10, 30), ("Aggregation", 20, 10)])

    def test_relation_types_either_listed_or_every_type_but_the_excluded(self):
        listed = ea_model.Profile(element_types=("Class",), relation_types=("association", "Aggregation"))
        self.assertEqual([c.type for c in ea_model.read_model(self.path, listed).relations],
                         ["Association", "Association", "Aggregation"])
        excluded = ea_model.Profile(element_types=("Class", "Note"), excluded_relations=("NoteLink", "Dependency"))
        self.assertEqual([c.type for c in ea_model.read_model(self.path, excluded).relations],
                         ["Association", "Association", "Aggregation"])

    def test_definition_from_the_tag_else_the_note_cleaned_as_the_profile_says(self):
        collapsed = ea_model.read_model(
            self.path, ea_model.Profile(element_types=("Class",), definition_tag="definition"), attributes=True
        )
        self.assertEqual(collapsed.elements[10].definition, "Tagged definition.")
        self.assertEqual(collapsed.elements[30].definition, "Line one line two")
        self.assertEqual(collapsed.attributes[10][0].definition, "The size.")
        stripped = ea_model.read_model(
            self.path, ea_model.Profile(element_types=("Class",), definition_text=ea_model.STRIPPED)
        )
        self.assertEqual(stripped.elements[10].definition, "A note<br/>with   a break")
        self.assertEqual(stripped.elements[30].definition, "Line one\r\nline two")
        self.assertEqual(stripped.elements[30].guid, "{B}")

    def test_a_model_without_guid_or_stereotype_columns_is_read(self):
        path = Path(self._dir.name) / "bare.qea"
        db = sqlite3.connect(path)
        db.executescript(
            """
            CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
            CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Package_ID INTEGER, Note TEXT);
            CREATE TABLE t_connector (Connector_ID INTEGER PRIMARY KEY, Connector_Type TEXT, Start_Object_ID INTEGER,
                                      End_Object_ID INTEGER, DestRole TEXT, DestCard TEXT, SourceRole TEXT,
                                      SourceCard TEXT, SourceIsAggregate INTEGER, DestIsAggregate INTEGER);
            INSERT INTO t_package VALUES (1, 'Root', 0);
            INSERT INTO t_object VALUES (1, 'A', 'Class', 1, NULL);
            """
        )
        db.commit()
        db.close()
        element = ea_model.read_model(path, ea_model.Profile(element_types=("Class",))).elements[1]
        self.assertEqual((element.name, element.guid, element.stereotype, element.definition), ("A", "", "", ""))

    def test_the_file_is_not_changed(self):
        before = self.path.read_bytes()
        ea_model.read_model(self.path, ea_model.Profile(element_types=("Class",)), attributes=True)
        self.assertEqual(self.path.read_bytes(), before)


def _attribute_file(path: Path) -> None:
    """One class with attributes in the model's order (Pos, then Name), an enumeration class by stereotype, a real
    enumeration, and a data type; the attribute table has the columns the class card reads."""
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
        CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Stereotype TEXT, Package_ID INTEGER,
                               Note TEXT);
        CREATE TABLE t_objectproperties (Object_ID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_attribute (ID INTEGER, Object_ID INTEGER, Name TEXT, Type TEXT, Classifier TEXT, LowerBound TEXT,
                                  UpperBound TEXT, Notes TEXT, Stereotype TEXT, Pos INTEGER);
        CREATE TABLE t_attributetag (ElementID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_connector (Connector_ID INTEGER PRIMARY KEY, Connector_Type TEXT, Start_Object_ID INTEGER,
                                  End_Object_ID INTEGER, DestRole TEXT, DestCard TEXT, SourceRole TEXT,
                                  SourceCard TEXT, SourceIsAggregate INTEGER, DestIsAggregate INTEGER);
        INSERT INTO t_package VALUES (1, 'Root', 0);
        INSERT INTO t_object VALUES
            (1, 'Thing', 'Class', '', 1, ''), (2, 'Mode', 'Class', 'Enumeration', 1, ''),
            (3, 'Kind', 'Enumeration', '', 1, ''), (4, 'Text', 'DataType', '', 1, '');
        INSERT INTO t_attribute VALUES
            (10, 1, 'second', 'Mode', '2', '0', '1', '  Notes of second.  ', 'AK', 2),
            (11, 1, 'first', 'Text', '4', '1', '*', 'Notes of first.', NULL, 1),
            (12, 1, 'plain', 'string', '0', '1', '1', NULL, NULL, 3),
            (13, 1, 'alsoSecond', '', '', '', '', '', '', 2),
            (20, 2, 'car', '', '0', '1', '1', 'A car.', 'enum', 1);
        INSERT INTO t_attributetag VALUES (11, 'definition', 'Tagged definition of first.', NULL);
        """
    )
    db.commit()
    db.close()


class MemberFactsTests(SimpleTestCase):
    def setUp(self):
        self._dir = TemporaryDirectory()
        self.path = Path(self._dir.name) / "attributes.qea"
        _attribute_file(self.path)

    def tearDown(self):
        self._dir.cleanup()

    def test_attributes_come_in_the_models_order_with_classifier_position_and_stereotype(self):
        profile = ea_model.Profile(element_types=("Class", "Enumeration", "DataType"))
        attributes = ea_model.read_model(self.path, profile, attributes=True).attributes[1]
        self.assertEqual([a.name for a in attributes], ["first", "alsoSecond", "second", "plain"])
        self.assertEqual([a.position for a in attributes], [1, 2, 3, 4])
        self.assertEqual([a.classifier for a in attributes], [4, 0, 2, 0])
        self.assertEqual([a.stereotype for a in attributes], ["", "", "AK", ""])
        self.assertEqual((attributes[0].lower, attributes[0].upper), ("1", "*"))

    def test_the_definition_is_the_tag_else_the_notes_as_the_profile_says(self):
        base = dict(element_types=("Class", "Enumeration", "DataType"))
        tag = ea_model.read_model(self.path, ea_model.Profile(definition_tag="definition", **base), attributes=True)
        self.assertEqual([a.definition for a in tag.attributes[1]], ["Tagged definition of first.", "", "", ""])
        notes = ea_model.read_model(
            self.path,
            ea_model.Profile(attribute_definition_from_notes=True, definition_text=ea_model.STRIPPED, **base),
            attributes=True,
        )
        self.assertEqual([a.definition for a in notes.attributes[1]], ["Notes of first.", "", "Notes of second.", ""])
        both = ea_model.read_model(
            self.path,
            ea_model.Profile(definition_tag="definition", attribute_definition_from_notes=True, **base),
            attributes=True,
        )
        self.assertEqual([a.definition for a in both.attributes[1]][:3], ["Tagged definition of first.", "", "Notes of second."])

    def test_a_model_without_the_new_columns_still_reads_with_empty_facts(self):
        path = Path(self._dir.name) / "old.qea"
        _model_file(path)
        model = ea_model.read_model(path, ea_model.Profile(element_types=("Class",), definition_tag="definition"), attributes=True)
        attribute = model.attributes[10][0]
        self.assertEqual((attribute.name, attribute.classifier, attribute.position, attribute.stereotype), ("size", 0, 1, ""))
        self.assertEqual(attribute.definition, "The size.")

    def test_element_kind_from_the_type_and_the_enumeration_stereotype(self):
        profile = ea_model.Profile(element_types=("Class", "Enumeration", "DataType"))
        model = ea_model.read_model(self.path, profile)
        self.assertEqual([ea_model.element_kind(e) for e in model.elements.values()],
                         ["class", "enumeration", "enumeration", "data type"])

    def test_multiplicity_text_is_a_number_pair_or_nothing(self):
        for text, bounds in (("1", ("1", "1")), ("0..1", ("0", "1")), ("1..*", ("1", "*")), ("*", ("0", "*")),
                             (" 0..* ", ("0", "*")), ("2..5", ("2", "5"))):
            self.assertEqual(ea_model.parse_multiplicity(text), bounds, text)
        for text in ("", None, "O..*", "0.*", "1..", "0:1", "n", "1..n"):
            self.assertIsNone(ea_model.parse_multiplicity(text), text)
