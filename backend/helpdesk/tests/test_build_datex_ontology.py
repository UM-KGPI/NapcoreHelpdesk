"""Tests for the build_datex_ontology command: a DATEX II model (Enterprise Architect .qea) to Turtle."""

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

from helpdesk.management.commands.build_datex_ontology import DATEX_NAMESPACE, build_turtle
from helpdesk.services import datex

RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
DATEX = rdflib.Namespace(DATEX_NAMESPACE)


def _qea_file(path: Path) -> None:
    """A tiny Enterprise Architect model with the tables and columns extract_model reads.

    Namespaces Situation and Other both define an Accident; Common holds Vehicle; Situation holds TrafficElement
    and the enumeration Severity."""
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE t_package (Package_ID INTEGER, Name TEXT, Parent_ID INTEGER);
        CREATE TABLE t_object (Object_ID INTEGER, Name TEXT, Object_Type TEXT, Stereotype TEXT, Package_ID INTEGER,
                               Note TEXT, PDATA1 TEXT);
        CREATE TABLE t_objectproperties (Object_ID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_attribute (ID INTEGER, Object_ID INTEGER, Name TEXT, Type TEXT, LowerBound TEXT,
                                  UpperBound TEXT, Pos INTEGER);
        CREATE TABLE t_attributetag (ElementID INTEGER, Property TEXT, Value TEXT, Notes TEXT);
        CREATE TABLE t_connector (Connector_ID INTEGER PRIMARY KEY, Connector_Type TEXT, Stereotype TEXT,
                                  Start_Object_ID INTEGER, End_Object_ID INTEGER, DestRole TEXT, DestCard TEXT,
                                  SourceRole TEXT, SourceCard TEXT, SourceIsAggregate INTEGER, DestIsAggregate INTEGER);
        INSERT INTO t_package VALUES (1, 'DATEX2System', 0), (2, 'Situation', 1), (3, 'Other', 1), (4, 'Common', 1);
        INSERT INTO t_object VALUES
            (10, 'Situation', 'Package', 'D2Namespace', 1, '', '2'),
            (11, 'Other', 'Package', 'D2Namespace', 1, '', '3'),
            (12, 'Common', 'Package', 'D2Namespace', 1, '', '4'),
            (20, 'Accident', 'Class', 'D2Class', 2, '', NULL),
            (21, 'TrafficElement', 'Class', 'D2Class', 2, '', NULL),
            (22, 'Severity', 'Enumeration', 'D2Enumeration', 2, '', NULL),
            (30, 'Accident', 'Class', 'D2Class', 3, '', NULL),
            (40, 'Vehicle', 'Class', 'D2Class', 4, '', NULL);
        INSERT INTO t_objectproperties VALUES
            (20, 'definition', 'An "unplanned" event with a \\ backslash.' || char(10) || 'on two lines.', NULL),
            (30, 'definition', 'An accident in the Other namespace.', NULL),
            (40, 'definition', 'A road vehicle.', NULL);
        INSERT INTO t_attribute VALUES
            (100, 20, 'reference', 'String', '0', '1', 1),
            (101, 20, 'severity', 'Severity', '0', '1', 2),
            (102, 22, 'low', '', '', '', 1),
            (103, 22, 'high', '', '', '', 2);
        INSERT INTO t_connector (Connector_Type, Stereotype, Start_Object_ID, End_Object_ID, DestRole, DestCard,
                                 SourceRole, SourceCard, SourceIsAggregate, DestIsAggregate) VALUES
            ('Generalization', NULL, 20, 21, NULL, NULL, NULL, NULL, 0, 0),
            ('Generalization', NULL, 40, 20, NULL, NULL, NULL, NULL, 0, 0),
            ('Aggregation', 'D2Relation', 20, 40, 'vehicleInvolved', '0..*', NULL, NULL, 0, 0),
            -- no role name on either end; the target is the Accident of the Other namespace (the name is ambiguous)
            ('Aggregation', 'D2Relation', 30, 40, NULL, NULL, NULL, '0..1', 0, 2),
            -- the same, to the Accident of Situation: the generated property name must not collide
            ('Aggregation', 'D2Relation', 20, 40, NULL, NULL, NULL, '1', 0, 2);
        """
    )
    db.commit()
    db.close()


def _graph(text: str) -> rdflib.Graph:
    graph = rdflib.Graph()
    graph.parse(data=text, format="turtle")
    return graph


def _element(name: str, namespace: str, **extra) -> dict:
    base = {"name": name, "kind": "class", "stereotype": "", "namespace": namespace, "package": "",
            "definition": f"Definition of {name}.", "supertypes": [], "members": [], "associations": []}
    base.update(extra)
    return base


class BuildTurtleTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.qea"
            _qea_file(path)
            cls.model = datex.extract_model(path)
        cls.text = build_turtle(cls.model)
        cls.attr_text = build_turtle(cls.model, attributes=True)
        cls.graph = _graph(cls.text)
        cls.attr_graph = _graph(cls.attr_text)

    def test_both_accident_classes_exist_under_their_namespace_iris(self):
        for namespace in ("Situation", "Other"):
            with self.subTest(namespace=namespace):
                cls_iri = DATEX[f"{namespace}.Accident"]
                self.assertIn((cls_iri, rdflib.RDF.type, OWL.Class), self.graph)
                self.assertIn((cls_iri, RDFS.label, rdflib.Literal("Accident", lang="en")), self.graph)
                self.assertTrue(list(self.graph.objects(cls_iri, SKOS.definition)))

    def test_definitions_are_written_as_skos_definition(self):
        definition = self.graph.value(DATEX["Situation.Accident"], SKOS.definition)
        self.assertIn("unplanned", str(definition))
        self.assertEqual(self.graph.value(DATEX["Other.Accident"], SKOS.definition),
                         rdflib.Literal("An accident in the Other namespace.", lang="en"))

    def test_subclass_is_written_for_the_resolved_supertype(self):
        self.assertIn((DATEX["Situation.Accident"], RDFS.subClassOf, DATEX["Situation.TrafficElement"]), self.graph)
        self.assertEqual(list(self.graph.objects(DATEX["Other.Accident"], RDFS.subClassOf)), [])

    def test_an_ambiguous_supertype_is_resolved_by_the_namespace_the_model_gives(self):
        # Vehicle (Common) has the Accident of Situation as its supertype; two Accident classes exist, none in Common.
        self.assertEqual(list(self.graph.objects(DATEX["Common.Vehicle"], RDFS.subClassOf)), [DATEX["Situation.Accident"]])
        header = [line for line in self.text.splitlines() if line.startswith("# unresolved:")]
        self.assertEqual(header, ["# unresolved: 0 supertypes, 0 associations"])

    def test_a_relation_without_a_role_name_becomes_a_property_named_after_its_target(self):
        # Vehicle owns both unnamed relations (Vehicle is the aggregate end): to Other.Accident and Situation.Accident
        props = {str(p): (str(d), str(r)) for p, d, r in (
            (p, self.graph.value(p, RDFS.domain), self.graph.value(p, RDFS.range))
            for p in self.graph.subjects(rdflib.RDF.type, OWL.ObjectProperty)) if str(d).endswith("Common.Vehicle")}
        self.assertEqual(sorted(r for _, r in props.values()), [str(DATEX["Other.Accident"]), str(DATEX["Situation.Accident"])])
        self.assertEqual(len(props), 2)  # two distinct IRIs: the second took the namespace of its target

    def test_an_older_model_without_namespaces_on_its_targets_still_builds(self):
        elements = [_element("Accident", "Situation", supertypes=["TrafficElement"],
                             associations=[{"role": "vehicleInvolved", "target": "Vehicle", "multiplicity": "0..*"}]),
                    _element("TrafficElement", "Situation"), _element("Vehicle", "Common")]
        graph = _graph(build_turtle({"version": "3.7", "elements": elements}))
        self.assertIn((DATEX["Situation.Accident"], RDFS.subClassOf, DATEX["Situation.TrafficElement"]), graph)
        self.assertIn((DATEX["Situation.Accident.vehicleInvolved"], RDFS.range, DATEX["Common.Vehicle"]), graph)

    def test_association_is_an_object_property_with_domain_and_range(self):
        prop = DATEX["Situation.Accident.vehicleInvolved"]
        self.assertIn((prop, rdflib.RDF.type, OWL.ObjectProperty), self.graph)
        self.assertIn((prop, RDFS.domain, DATEX["Situation.Accident"]), self.graph)
        self.assertIn((prop, RDFS.range, DATEX["Common.Vehicle"]), self.graph)

    def test_association_has_no_label_without_attributes(self):
        prop = DATEX["Situation.Accident.vehicleInvolved"]
        self.assertEqual(list(self.graph.objects(prop, RDFS.label)), [])
        self.assertEqual(list(self.graph.subjects(rdflib.RDF.type, OWL.DatatypeProperty)), [])

    def test_attributes_are_datatype_or_object_properties_with_attributes_option(self):
        prop = DATEX["Situation.Accident.vehicleInvolved"]
        self.assertEqual(self.attr_graph.value(prop, RDFS.label), rdflib.Literal("vehicleInvolved", lang="en"))

        reference = DATEX["Situation.Accident.reference"]
        self.assertIn((reference, rdflib.RDF.type, OWL.DatatypeProperty), self.attr_graph)
        self.assertIn((reference, RDFS.domain, DATEX["Situation.Accident"]), self.attr_graph)
        self.assertNotIn((reference, RDFS.range, None), self.attr_graph)

        severity = DATEX["Situation.Accident.severity"]
        self.assertIn((severity, rdflib.RDF.type, OWL.ObjectProperty), self.attr_graph)
        self.assertIn((severity, RDFS.domain, DATEX["Situation.Accident"]), self.attr_graph)
        self.assertIn((severity, RDFS.range, DATEX["Situation.Severity"]), self.attr_graph)

    def test_enumeration_literals_are_never_properties(self):
        for graph in (self.graph, self.attr_graph):
            for prop in set(graph.subjects(rdflib.RDF.type, OWL.DatatypeProperty)) | set(
                graph.subjects(rdflib.RDF.type, OWL.ObjectProperty)
            ):
                self.assertNotIn("Severity.", str(prop))
            self.assertNotIn(DATEX["Situation.Severity.low"], set(graph.subjects()))
            self.assertNotIn(DATEX["Situation.Severity.high"], set(graph.subjects()))

    def test_output_is_identical_across_runs(self):
        self.assertEqual(build_turtle(self.model), self.text)
        self.assertEqual(build_turtle(self.model, attributes=True), self.attr_text)

    def test_output_does_not_depend_on_element_order(self):
        reversed_model = dict(self.model, elements=list(reversed(self.model["elements"])))
        self.assertEqual(build_turtle(reversed_model), self.text)
        self.assertEqual(build_turtle(reversed_model, attributes=True), self.attr_text)

    def test_quotes_backslashes_and_newlines_are_escaped_and_round_trip(self):
        definition = 'He said "stop" \\ then\nwent on   with\tspaces.'
        model = {"version": "3.7", "elements": [_element("Quoted", "Situation", definition=definition)]}
        graph = _graph(build_turtle(model))
        value = str(graph.value(DATEX["Situation.Quoted"], SKOS.definition))
        self.assertEqual(value, re.sub(r"\s+", " ", definition).strip())


EA = rdflib.Namespace("https://napcore.eu/ontology/ea-model#")


def _member_qea_file(path: Path) -> None:
    """The model above with the column the class card reads: the attribute 'severity' is typed by the element
    Severity (22), 'reference' by a plain name."""
    _qea_file(path)
    db = sqlite3.connect(path)
    db.executescript(
        """
        ALTER TABLE t_attribute ADD COLUMN Classifier TEXT;
        UPDATE t_attribute SET Classifier = '0';
        UPDATE t_attribute SET Classifier = '22' WHERE ID = 101;
        INSERT INTO t_attributetag VALUES (100, 'definition', 'The reference.', NULL), (102, 'definition', 'Low.', NULL);
        """
    )
    db.commit()
    db.close()


class MembersTests(SimpleTestCase):
    """The option --members: the facts of a class card, in the same file, without a label and without a domain."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.qea"
            _member_qea_file(path)
            cls.plain_model = datex.extract_model(path)
            cls.model = datex.extract_model(path, member_facts=True)
        cls.stats: dict = {}
        cls.off = build_turtle(cls.model)
        cls.text = build_turtle(cls.model, members=True, stats=cls.stats)
        cls.old, cls.new = _graph(cls.off), _graph(cls.text)

    def test_with_the_option_off_the_file_is_the_one_the_model_without_member_facts_gives(self):
        self.assertEqual(self.off, build_turtle(self.plain_model))
        self.assertNotIn("ea:", self.off)
        for element in self.plain_model["elements"]:
            for member in element["members"]:
                self.assertNotIn("position", member)

    def test_every_old_triple_is_in_the_new_file_and_the_rest_is_in_the_ea_namespace(self):
        self.assertEqual([t for t in self.old if t not in self.new], [])
        extra = [t for t in self.new if t not in self.old]
        self.assertTrue(extra)
        self.assertTrue(all(str(p).startswith(str(EA)) for _s, p, _o in extra))

    def test_no_label_no_domain_no_range_and_no_class_or_property_on_a_member(self):
        old_subjects = set(self.old.subjects())
        for subject, predicate, _obj in self.new:
            if isinstance(subject, rdflib.BNode):
                self.assertTrue(str(predicate).startswith(str(EA)), predicate)
            elif predicate in (RDFS.label, SKOS.prefLabel, SKOS.altLabel, RDFS.domain, RDFS.range):
                self.assertIn(subject, old_subjects)
        self.assertEqual(set(self.new.subjects(RDFS.label)), set(self.old.subjects(RDFS.label)))
        self.assertEqual(set(self.new.subjects(rdflib.RDF.type, OWL.Class)), set(self.old.subjects(rdflib.RDF.type, OWL.Class)))
        self.assertEqual(
            set(self.new.subjects(rdflib.RDF.type, OWL.ObjectProperty)), set(self.old.subjects(rdflib.RDF.type, OWL.ObjectProperty))
        )

    def _attributes(self, subject):
        rows = {}
        for node in self.new.objects(subject, EA.attribute):
            rows[str(self.new.value(node, EA.name))] = {
                key: self.new.value(node, EA[key]) for key in ("position", "type", "typeName", "lowerBound", "upperBound", "definition")
            }
        return rows

    def test_an_attribute_has_its_place_type_bounds_and_definition(self):
        rows = self._attributes(DATEX["Situation.Accident"])
        self.assertEqual(set(rows), {"reference", "severity"})
        self.assertEqual(int(rows["reference"]["position"]), 1)
        self.assertEqual(rows["reference"]["typeName"], rdflib.Literal("String", lang="en"))
        self.assertIsNone(rows["reference"]["type"])
        self.assertEqual((str(rows["reference"]["lowerBound"]), str(rows["reference"]["upperBound"])), ("0", "1"))
        self.assertEqual(str(rows["reference"]["definition"]), "The reference.")
        self.assertEqual(int(rows["severity"]["position"]), 2)
        # typed by the element the classifier names, not by the name
        self.assertEqual(rows["severity"]["type"], DATEX["Situation.Severity"])
        self.assertIsNone(rows["severity"]["typeName"])

    def test_an_enumeration_has_values_with_places_and_no_attributes(self):
        severity = DATEX["Situation.Severity"]
        self.assertEqual(str(self.new.value(severity, EA.kind)), "enumeration")
        self.assertEqual(self._attributes(severity), {})
        values = {str(self.new.value(n, EA.name)): n for n in self.new.objects(severity, EA.value)}
        self.assertEqual(set(values), {"low", "high"})
        self.assertEqual(int(self.new.value(values["low"], EA.position)), 1)
        self.assertEqual(str(self.new.value(values["low"], EA.definition)), "Low.")
        self.assertEqual(str(self.new.value(DATEX["Situation.Accident"], EA.kind)), "class")

    def test_a_relation_has_its_bounds(self):
        prop = DATEX["Situation.Accident.vehicleInvolved"]
        self.assertEqual((str(self.new.value(prop, EA.lowerBound)), str(self.new.value(prop, EA.upperBound))), ("0", "*"))
        # the relations without a role name: the card of the end that gives it, "0..1" and "1"
        bounds = sorted(
            (str(self.new.value(p, EA.lowerBound)), str(self.new.value(p, EA.upperBound)))
            for p in self.new.subjects(RDFS.domain, DATEX["Common.Vehicle"])
        )
        self.assertEqual(bounds, [("0", "1"), ("1", "1")])

    def test_the_counts_are_reported(self):
        self.assertEqual(
            (self.stats["classes"], self.stats["attributes"], self.stats["values"], self.stats["typed_by_element"],
             self.stats["typed_by_enumeration"], self.stats["typed_by_name"], self.stats["relations"],
             self.stats["relations_with_bounds"], self.stats["relations_with_text_only"]),
            (5, 2, 2, 1, 1, 1, 3, 3, 0),
        )

    def test_a_typo_in_a_multiplicity_is_kept_as_text_and_a_missing_one_as_nothing(self):
        elements = [
            _element("A", "N", associations=[
                {"role": "x", "target": "B", "target_namespace": "N", "multiplicity": "O..*"},
                {"role": "y", "target": "B", "target_namespace": "N", "multiplicity": ""},
                {"role": "z", "target": "B", "target_namespace": "N", "multiplicity": "1..3"},
            ]),
            _element("B", "N"),
        ]
        graph = _graph(build_turtle({"version": "3.7", "elements": elements}, members=True))
        self.assertEqual(str(graph.value(DATEX["N.A.x"], EA.multiplicityText)), "O..*")
        self.assertIsNone(graph.value(DATEX["N.A.x"], EA.lowerBound))
        self.assertIsNone(graph.value(DATEX["N.A.y"], EA.lowerBound))
        self.assertIsNone(graph.value(DATEX["N.A.y"], EA.multiplicityText))
        self.assertEqual(str(graph.value(DATEX["N.A.z"], EA.upperBound)), "3")

    def test_a_model_read_without_member_facts_is_refused(self):
        with self.assertRaises(ValueError):
            build_turtle(self.plain_model, members=True)

    def test_output_is_identical_across_runs(self):
        self.assertEqual(build_turtle(self.model, members=True), self.text)


class CommandTests(SimpleTestCase):
    def test_members_option_writes_the_member_facts_and_prints_the_counts(self):
        with TemporaryDirectory() as tmp:
            qea, out = Path(tmp) / "model.qea", Path(tmp) / "datex.ttl"
            _member_qea_file(qea)
            stdout = StringIO()
            call_command("build_datex_ontology", "--qea", str(qea), "--members", "--out", str(out), stdout=stdout)
            self.assertEqual(out.read_text(encoding="utf-8"), build_turtle(datex.extract_model(qea, member_facts=True), members=True))
            self.assertIn("members: classes 5, attributes 2, values 2", stdout.getvalue())

    def test_members_option_needs_the_qea_file_and_does_not_go_with_attributes(self):
        with TemporaryDirectory() as tmp:
            qea = Path(tmp) / "model.qea"
            _member_qea_file(qea)
            with self.assertRaises(CommandError):
                call_command("build_datex_ontology", "--members", "--out", str(Path(tmp) / "x.ttl"), stdout=StringIO())
            with self.assertRaises(CommandError):
                call_command("build_datex_ontology", "--qea", str(qea), "--members", "--attributes",
                             "--out", str(Path(tmp) / "x.ttl"), stdout=StringIO())
            self.assertFalse((Path(tmp) / "x.ttl").exists())

    def test_the_default_run_is_unchanged_by_the_option(self):
        with TemporaryDirectory() as tmp:
            qea = Path(tmp) / "model.qea"
            _member_qea_file(qea)
            out = Path(tmp) / "plain.ttl"
            call_command("build_datex_ontology", "--qea", str(qea), "--out", str(out), stdout=StringIO())
            self.assertEqual(out.read_text(encoding="utf-8"), build_turtle(datex.extract_model(qea)))

    def test_qea_route_writes_the_turtle_file(self):
        with TemporaryDirectory() as tmp:
            qea = Path(tmp) / "model.qea"
            out_path = Path(tmp) / "out" / "datex.ttl"
            _qea_file(qea)
            stdout = StringIO()
            call_command("build_datex_ontology", "--qea", str(qea), "--out", str(out_path), stdout=stdout)
            text = out_path.read_text(encoding="utf-8")
            self.assertEqual(text, build_turtle(datex.extract_model(qea)))
            graph = _graph(text)
            self.assertIn((DATEX["Situation.Accident"], rdflib.RDF.type, OWL.Class), graph)
            self.assertIn(str(out_path), stdout.getvalue())

    def test_missing_model_file_raises_command_error(self):
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.json"
            with self.assertRaises(CommandError):
                call_command("build_datex_ontology", "--model", str(missing), "--out", str(Path(tmp) / "x.ttl"),
                             stdout=StringIO())
            self.assertFalse((Path(tmp) / "x.ttl").exists())
