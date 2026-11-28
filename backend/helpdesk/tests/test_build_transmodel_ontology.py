"""Tests for build_transmodel_ontology: a Transmodel Enterprise Architect model (.qea) to Turtle.

The real model is not public; the tests build a small one with the tables and columns the reader uses."""

from __future__ import annotations

import re
import sqlite3
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import rdflib
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from helpdesk.services import transmodel_model
from helpdesk.services.transmodel_guids import SECTION_MARKER, read_guid_section


def _qea_file(path: Path) -> None:
    """Root "Transmodel v6.2  2024" with Part 1, Part 9, Part 10 and the glossary (with a package below it); another
    model's root and the 2025 development root beside it.

    Object_ID is not the row id here and rows are inserted out of order, so the test sees whether the
    reader orders by Object_ID: the lower id of a repeated name keeps the plain IRI."""
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
        CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Stereotype TEXT, Package_ID INTEGER,
                               Note TEXT, ea_guid TEXT);
        CREATE TABLE t_connector (Connector_ID INTEGER PRIMARY KEY, Connector_Type TEXT, Start_Object_ID INTEGER,
                                  End_Object_ID INTEGER, DestRole TEXT, DestCard TEXT, SourceRole TEXT,
                                  SourceCard TEXT, SourceIsAggregate INTEGER, DestIsAggregate INTEGER);
        INSERT INTO t_package VALUES (1, 'Transmodel v6.2  2024', 0), (2, 'Part 1 - Common Concepts (CC)', 1),
            (3, 'RC Vehicle Type MODEL', 2), (4, 'Part 9 - Something', 1), (5, 'TM Glossary', 1),
            (6, 'NeTEx XSD Physical Models', 0), (7, 'Part 10 - Alternative Modes (NM)', 1),
            (8, 'Transmodel New Development 2025', 0), (9, 'Abbreviations', 5);
        INSERT INTO t_object VALUES
            (300, 'VEHICLE TYPE', 'Class', '', 7, 'Repeated name.', '{VT-10}'),
            (200, 'VEHICLE TYPE', 'Class', '', 3, 'A "type" of vehicle' || char(13) || char(10) || 'on two lines. ', '{VT}'),
            (210, 'TRANSPORT TYPE', 'Class', '', 3, '', '{TT}'),
            (220, 'PRE-ASSIGNED FARE PRODUCT', 'Class', '', 2, NULL, '{PAFP}'),
            (230, '3D MODEL', 'Class', '', 2, NULL, '{3D}'),
            (240, 'IN PART NINE', 'Class', '', 4, NULL, '{P9}'),
            (250, 'GLOSSARY TERM', 'Class', '', 5, NULL, '{GT}'),
            (260, 'SINGLE JOURNEY', 'Class', '', 6, NULL, '{NETEX-SJ}'),
            (270, 'A NOTE', 'Note', '', 3, NULL, '{NOTE}'),
            (280, '   ', 'Class', '', 3, NULL, '{BLANK}'),
            (290, 'NEW DEVELOPMENT', 'Class', '', 8, NULL, '{NEW}'),
            (295, 'SIRI', 'Class', '', 9, 'Service Interface for Real-time Information', '{SIRI}');
        INSERT INTO t_connector (Connector_Type, Start_Object_ID, End_Object_ID, DestRole, DestCard, SourceRole,
                                 SourceCard, SourceIsAggregate, DestIsAggregate) VALUES
            ('Generalization', 200, 210, NULL, NULL, NULL, NULL, 0, 0),
            ('Association', 200, 220, 'offered product', '0..*', NULL, '1', 0, 0),
            ('Aggregation', 230, 300, NULL, NULL, 'made of', NULL, 0, 0),
            ('Dependency', 200, 230, 'depends', NULL, NULL, NULL, 0, 0),
            ('Association', 200, 260, 'outside', NULL, NULL, NULL, 0, 0),
            ('Association', 200, 240, 'part nine', NULL, NULL, NULL, 0, 0),
            -- one role name, "for", on three class pairs: twice from VEHICLE TYPE, once from 3D MODEL
            ('Association', 200, 210, 'for', NULL, NULL, NULL, 0, 0),
            ('Association', 200, 220, 'for', NULL, NULL, NULL, 0, 0),
            ('Association', 230, 210, 'for', NULL, NULL, NULL, 0, 0);
        """
    )
    db.commit()
    db.close()


EA = rdflib.Namespace("https://napcore.eu/ontology/ea-model#")
TM = rdflib.Namespace("https://transmodel-cen.eu/6.2/")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")


def _member_qea_file(path: Path) -> None:
    """The model above with attributes (the columns the class card reads), an enumeration class by stereotype with
    values, and two more connectors: one with a typo in its multiplicity, one that replaces the multiplicity of the
    first between the same classes under the same name."""
    _qea_file(path)
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_attribute (ID INTEGER, Object_ID INTEGER, Name TEXT, Type TEXT, Classifier TEXT, LowerBound TEXT,
                                  UpperBound TEXT, Notes TEXT, Stereotype TEXT, Pos INTEGER);
        INSERT INTO t_object VALUES (310, 'MODE ALLOWED', 'Class', 'enumeration', 3, 'Values of a mode.', '{MODE}');
        INSERT INTO t_attribute VALUES
            (1, 200, 'Name', 'MultilingualString', '0', '0', '1', '  The name of the type.  ', NULL, 2),
            (2, 200, 'Id', 'VehicleTypeIdType', '0', '1', '1', 'Identifier of a VEHICLE TYPE.', 'UID', 1),
            (3, 200, 'Kind', 'TRANSPORT TYPE', '210', '0', '1', NULL, NULL, 3),
            (4, 200, 'Loose', '', '', '1', '*', NULL, NULL, 4),
            (5, 310, 'allowed', '', '0', '1', '1', 'Allowed.', 'enum', 1),
            (6, 310, 'forbidden', '', '0', '1', '1', NULL, 'enum', 2),
            (7, 280, 'IgnoredBlankClass', 'x', '0', '1', '1', NULL, NULL, 1);
        INSERT INTO t_connector (Connector_Type, Start_Object_ID, End_Object_ID, DestRole, DestCard, SourceRole,
                                 SourceCard, SourceIsAggregate, DestIsAggregate) VALUES
            ('Association', 210, 220, 'typo role', 'O..*', NULL, '1..', 0, 0),
            ('Association', 200, 220, 'offered product', '1..3', NULL, NULL, 0, 0);
        """
    )
    db.commit()
    db.close()


class MembersTests(SimpleTestCase):
    """The option members: the facts of a class card, in the same file, without a label and without a domain."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.qea"
            _member_qea_file(path)
            cls.off = transmodel_model.build_turtle(path)
            cls.stats: dict = {}
            cls.text = transmodel_model.build_turtle(path, members=True, stats=cls.stats)
            cls.again = transmodel_model.build_turtle(path, members=True)
        cls.old, cls.new = rdflib.Graph().parse(data=cls.off, format="turtle"), rdflib.Graph().parse(data=cls.text, format="turtle")

    def _members(self, subject, predicate):
        rows = {}
        for node in self.new.objects(subject, predicate):
            rows[str(self.new.value(node, EA.name))] = {
                key: self.new.value(node, EA[key]) for key in ("position", "type", "typeName", "lowerBound", "upperBound", "definition")
            }
        return rows

    def test_every_old_triple_is_in_the_new_file_and_the_rest_is_in_the_ea_namespace(self):
        self.assertEqual([t for t in self.old if t not in self.new], [])
        extra = [t for t in self.new if t not in self.old]
        self.assertTrue(extra)
        self.assertTrue(all(str(p).startswith(str(EA)) for _s, p, _o in extra))
        self.assertNotIn("ea:", self.off)
        self.assertEqual(self.text.count(SECTION_MARKER), 1)

    def test_nothing_that_makes_a_concept_or_a_relation_is_added(self):
        for subject, predicate, _obj in self.new:
            if isinstance(subject, rdflib.BNode):
                self.assertTrue(str(predicate).startswith(str(EA)), predicate)
        for predicate in (RDFS.label, RDFS.domain, RDFS.range, rdflib.RDF.type):
            self.assertEqual(set(self.new.subject_objects(predicate)), set(self.old.subject_objects(predicate)), predicate)
        self.assertEqual(sorted(self.new.subjects(rdflib.RDF.type, OWL.Class)), sorted(self.old.subjects(rdflib.RDF.type, OWL.Class)))

    def test_an_attribute_has_its_place_type_bounds_and_definition_from_its_notes(self):
        rows = self._members(TM.VEHICLE_TYPE, EA.attribute)
        self.assertEqual(set(rows), {"Id", "Name", "Kind", "Loose"})
        self.assertEqual({name: int(row["position"]) for name, row in rows.items()}, {"Id": 1, "Name": 2, "Kind": 3, "Loose": 4})
        self.assertEqual(str(rows["Name"]["definition"]), "The name of the type.")
        self.assertEqual(str(rows["Name"]["typeName"]), "MultilingualString")
        self.assertEqual((str(rows["Id"]["lowerBound"]), str(rows["Id"]["upperBound"])), ("1", "1"))
        self.assertEqual((str(rows["Loose"]["lowerBound"]), str(rows["Loose"]["upperBound"])), ("1", "*"))
        # typed by the class its classifier names; a member without a type has none; no definition, none written
        self.assertEqual(rows["Kind"]["type"], TM.TRANSPORT_TYPE)
        self.assertIsNone(rows["Kind"]["typeName"])
        self.assertIsNone(rows["Kind"]["definition"])
        self.assertIsNone(rows["Loose"]["type"])
        self.assertIsNone(rows["Loose"]["typeName"])
        self.assertEqual(str(self.new.value(TM.VEHICLE_TYPE, EA.kind)), "class")

    def test_a_class_with_the_enumeration_stereotype_has_values_and_no_attributes(self):
        self.assertEqual(str(self.new.value(TM.MODE_ALLOWED, EA.kind)), "enumeration")
        self.assertEqual(self._members(TM.MODE_ALLOWED, EA.attribute), {})
        values = self._members(TM.MODE_ALLOWED, EA.value)
        self.assertEqual({name: int(row["position"]) for name, row in values.items()}, {"allowed": 1, "forbidden": 2})
        self.assertEqual(str(values["allowed"]["definition"]), "Allowed.")
        # the attribute of a class that is not in the file is not written
        self.assertNotIn("IgnoredBlankClass", self.text)

    def test_a_relation_has_the_bounds_of_the_end_that_gives_it_and_the_later_connector_replaces_the_earlier(self):
        # VEHICLE TYPE -> PRE-ASSIGNED FARE PRODUCT "offered product": the first connector said 0..*, a later one 1..3
        prop = TM["offeredProduct.VEHICLE_TYPE"]
        self.assertEqual((str(self.new.value(prop, EA.lowerBound)), str(self.new.value(prop, EA.upperBound))), ("1", "3"))
        # the other way, without a role: the source end's card "1" of the first connector, the later one gives none
        back = TM["hasVEHICLETYPE.PRE_ASSIGNED_FARE_PRODUCT"]
        self.assertIsNone(self.new.value(back, EA.lowerBound))
        # a typo is kept as text, and no number is guessed from it
        typo = TM["typoRole.TRANSPORT_TYPE"]
        self.assertEqual(str(self.new.value(typo, EA.multiplicityText)), "O..*")
        self.assertIsNone(self.new.value(typo, EA.upperBound))
        typo_back = TM["hasTRANSPORTTYPE.PRE_ASSIGNED_FARE_PRODUCT"]
        self.assertEqual(str(self.new.value(typo_back, EA.multiplicityText)), "1..")

    def test_the_counts_are_reported(self):
        self.assertEqual(
            (self.stats["classes"], self.stats["enumerations"], self.stats["attributes"], self.stats["values"],
             self.stats["definitions"], self.stats["typed_by_element"], self.stats["typed_by_name"], self.stats["untyped"],
             self.stats["bounds"]),
            (7, 1, 4, 2, 3, 1, 2, 1, 6),
        )
        self.assertEqual(self.stats["relations"], len(list(self.new.subjects(RDFS.domain, None))))
        self.assertEqual(self.stats["relations_with_text_only"], 2)

    def test_output_is_identical_across_runs(self):
        self.assertEqual(self.text, self.again)


class TransmodelTurtleTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.qea"
            _qea_file(path)
            cls.text = transmodel_model.build_turtle(path)
            cls.again = transmodel_model.build_turtle(path)
            # The same root without the exclusion.
            cls.glossary = transmodel_model.build_turtle(
                path,
                transmodel_model.ea_model.Profile(
                    element_types=("Class",),
                    package_path_patterns=(r"^Transmodel v6\.2 2024(?: > |$)",),
                    definition_text=transmodel_model.ea_model.STRIPPED,
                    relation_types=("Association", "Aggregation"),
                ),
            )
        cls.classes = [line.split()[0] for line in cls.text.splitlines() if line.endswith(" a owl:Class ;")]

    def test_every_class_below_the_root_but_the_glossary_in_object_id_order(self):
        self.assertEqual(
            self.classes,
            ["tm:VEHICLE_TYPE", "tm:TRANSPORT_TYPE", "tm:PRE_ASSIGNED_FARE_PRODUCT", "tm:_3D_MODEL", "tm:IN_PART_NINE",
             "tm:VEHICLE_TYPE_300"],
        )
        # The glossary and the package below it, other roots, a note and a blank name are not classes of the file.
        for name in ("GLOSSARY_TERM", "SIRI", "SINGLE_JOURNEY", "NEW_DEVELOPMENT", "A_NOTE", "UnnamedClass"):
            self.assertNotIn(f"tm:{name} ", self.text)
        self.assertEqual(transmodel_model.PROFILE.excluded_packages, ("TM Glossary",))

    def test_label_comment_and_supertype(self):
        self.assertIn(
            'tm:VEHICLE_TYPE a owl:Class ;\n  rdfs:label "VEHICLE TYPE"\n'
            '  ; rdfs:comment "A \\"type\\" of vehicle  on two lines."\n'
            '  ; skos:definition "A \\"type\\" of vehicle  on two lines."\n'
            "  ; rdfs:subClassOf tm:TRANSPORT_TYPE\n  .",
            self.text,
        )
        self.assertIn('tm:TRANSPORT_TYPE a owl:Class ;\n  rdfs:label "TRANSPORT TYPE"\n  .', self.text)
        self.assertIn("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .", self.text)

    def test_associations_and_aggregations_give_a_relation_each_way(self):
        self.assertIn(
            'tm:offeredProduct.VEHICLE_TYPE a owl:ObjectProperty ;\n  rdfs:label "offered product" ;\n'
            "  rdfs:domain tm:VEHICLE_TYPE ;\n  rdfs:range tm:PRE_ASSIGNED_FARE_PRODUCT .",
            self.text,
        )
        # Without a role at that end: "has" and the target's name.
        self.assertIn(
            'tm:hasVEHICLETYPE.PRE_ASSIGNED_FARE_PRODUCT a owl:ObjectProperty ;\n  rdfs:label "has VEHICLE TYPE" ;\n'
            "  rdfs:domain tm:PRE_ASSIGNED_FARE_PRODUCT ;\n  rdfs:range tm:VEHICLE_TYPE .",
            self.text,
        )
        self.assertIn(
            "tm:madeOf.VEHICLE_TYPE_300 a owl:ObjectProperty ;\n  rdfs:label \"made of\" ;\n"
            "  rdfs:domain tm:VEHICLE_TYPE_300 ;\n  rdfs:range tm:_3D_MODEL .",
            self.text,
        )
        # A dependency is no relation; a connector to a class out of scope is left out.
        for role in ("depends", "outside"):
            self.assertNotIn(f"tm:{role}.", self.text)
        self.assertIn("tm:partNine.VEHICLE_TYPE a owl:ObjectProperty ;", self.text)

    def test_every_relation_has_its_own_iri_with_one_domain_and_one_range(self):
        blocks = re.findall(
            r"^tm:(\S+) a owl:ObjectProperty ;\n  rdfs:label .*\n  rdfs:domain tm:(\S+) ;\n  rdfs:range tm:(\S+) \.",
            self.text,
            re.M,
        )
        iris = [iri for iri, _, _ in blocks]
        self.assertEqual(len(iris), len(set(iris)))
        pairs = {iri: (domain, range_) for iri, domain, range_ in blocks}
        # The shared role keeps its pairing: the domain with two ranges takes the range into the IRI.
        self.assertEqual(pairs["for.VEHICLE_TYPE.TRANSPORT_TYPE"], ("VEHICLE_TYPE", "TRANSPORT_TYPE"))
        self.assertEqual(pairs["for.VEHICLE_TYPE.PRE_ASSIGNED_FARE_PRODUCT"], ("VEHICLE_TYPE", "PRE_ASSIGNED_FARE_PRODUCT"))
        self.assertEqual(pairs["for._3D_MODEL"], ("_3D_MODEL", "TRANSPORT_TYPE"))
        self.assertNotIn("for.VEHICLE_TYPE", pairs)
        self.assertEqual(list(pairs), sorted(pairs))

    def test_every_relation_iri_starts_lower_case_and_no_class_iri_does(self):
        from helpdesk.services.semantic_graph import _is_class_concept, concept_own_name

        relations = re.findall(r"^tm:(\S+) a owl:ObjectProperty ;", self.text, re.M)
        classes = re.findall(r"^tm:(\S+) a owl:Class ;", self.text, re.M)
        self.assertTrue(relations and classes)
        for local in relations:
            self.assertTrue(local[:1].islower(), local)
            self.assertFalse(_is_class_concept(f"transmodel:{local}"), local)
        for local in classes:
            # A model class name that starts with a digit (tm:_3D_MODEL) or in lower case is not one by the rule;
            # that is how the model names it, unchanged here.
            if local[:1].isupper():
                self.assertTrue(_is_class_concept(f"transmodel:{local}"), local)
        # The own name of a relation is its name, not one of its classes.
        self.assertEqual(concept_own_name("transmodel:for.VEHICLE_TYPE.TRANSPORT_TYPE"), "for")

    def test_relation_iris_name_the_range_only_when_needed(self):
        iris = transmodel_model.relation_iris(
            {("for", "A", "B"): "for", ("for", "A", "C"): "for", ("for", "D", "B"): "for", ("hasB", "A", "B"): "has B"}
        )
        self.assertEqual(
            iris,
            {"for.A.B": ("A", "B", "for"), "for.A.C": ("A", "C", "for"), "for.D": ("D", "B", "for"),
             "hasB.A": ("A", "B", "has B")},
        )

    def test_guid_section_one_per_class_and_no_timestamp(self):
        self.assertEqual(self.text.count(SECTION_MARKER), 1)
        self.assertEqual(
            read_guid_section(self.text),
            {"VEHICLE_TYPE": "VT", "TRANSPORT_TYPE": "TT", "PRE_ASSIGNED_FARE_PRODUCT": "PAFP", "_3D_MODEL": "3D",
             "IN_PART_NINE": "P9", "VEHICLE_TYPE_300": "VT-10"},
        )
        self.assertNotIn("# Generated:", self.text)
        self.assertEqual(self.text, self.again)
        self.assertTrue(self.text.startswith("# Transmodel RDF/Turtle Ontology\n# Source: model.qea\n"))

    def test_the_scope_is_profile_data(self):
        self.assertIn("tm:GLOSSARY_TERM a owl:Class ;", self.glossary)
        self.assertIn("tm:SIRI a owl:Class ;", self.glossary)
        self.assertIn("tm:IN_PART_NINE a owl:Class ;", self.glossary)
        self.assertNotIn("tm:SINGLE_JOURNEY ", self.glossary)


class CommandTests(SimpleTestCase):
    def test_members_option_writes_the_member_facts_and_prints_the_counts(self):
        with TemporaryDirectory() as tmp:
            qea, out = Path(tmp) / "model.qea", Path(tmp) / "transmodel.ttl"
            _member_qea_file(qea)
            stdout = StringIO()
            call_command("build_transmodel_ontology", "--qea", str(qea), "--members", "--out", str(out), stdout=stdout)
            self.assertEqual(out.read_text(encoding="utf-8"), transmodel_model.build_turtle(qea, members=True))
            self.assertIn("members: classes 7, enumerations 1, attributes 4, values 2", stdout.getvalue())

    def test_writes_the_file(self):
        with TemporaryDirectory() as tmp:
            qea, out = Path(tmp) / "model.qea", Path(tmp) / "out" / "transmodel.ttl"
            _qea_file(qea)
            stdout = StringIO()
            call_command("build_transmodel_ontology", "--qea", str(qea), "--out", str(out), stdout=stdout)
            self.assertIn("6 classes", stdout.getvalue())
            self.assertEqual(out.read_text(encoding="utf-8"), transmodel_model.build_turtle(qea))

    def test_a_model_without_transmodel_classes_is_refused(self):
        with TemporaryDirectory() as tmp:
            qea = Path(tmp) / "model.qea"
            db = sqlite3.connect(qea)
            db.executescript(
                """
                CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
                CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Package_ID INTEGER, Note TEXT);
                CREATE TABLE t_connector (Connector_ID INTEGER PRIMARY KEY, Connector_Type TEXT,
                    Start_Object_ID INTEGER, End_Object_ID INTEGER, DestRole TEXT, DestCard TEXT, SourceRole TEXT,
                    SourceCard TEXT, SourceIsAggregate INTEGER, DestIsAggregate INTEGER);
                INSERT INTO t_package VALUES (1, 'DATEX2System', 0);
                INSERT INTO t_object VALUES (1, 'Accident', 'Class', 1, NULL);
                """
            )
            db.commit()
            db.close()
            with self.assertRaises(CommandError):
                call_command("build_transmodel_ontology", "--qea", str(qea), "--out", str(Path(tmp) / "x.ttl"))
            with self.assertRaises(CommandError):
                call_command("build_transmodel_ontology", "--qea", str(Path(tmp) / "missing.qea"))
