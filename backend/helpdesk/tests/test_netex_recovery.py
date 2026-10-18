from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from helpdesk.services.netex_recovery import (
    ElementDeclaration,
    append_recovered_classes,
    camel_to_words,
    collect_element_declarations,
    is_recoverable,
    render_class,
    select_recoverable,
)

XSD = """<?xml version="1.0"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:element name="DayType" type="DayType_VersionStructure" substitutionGroup="DataManagedObject">
    <xsd:annotation><xsd:documentation>A type of day
      with properties.</xsd:documentation></xsd:annotation>
  </xsd:element>
  <xsd:element name="SimplePoint" type="SimplePointStructure"/>
  <xsd:complexType name="SimplePointStructure">
    <xsd:annotation><xsd:documentation>Type for a Simple POINT.</xsd:documentation></xsd:annotation>
  </xsd:complexType>
  <xsd:element name="OnwardCall" type="OnwardCallStructure"/>
  <xsd:element name="privateCodes" type="PrivateCodesStructure"/>
  <xsd:element name="Vehicle_Dummy" type="xsd:string"/>
  <xsd:element name="StopView" type="xsd:string"/>
  <xsd:element name="StopInverse" type="xsd:string"/>
</xsd:schema>
"""


def write_xsd(root: Path, name: str = "types.xsd", text: str = XSD) -> Path:
    xsd_root = root / "xsd"
    xsd_root.mkdir(exist_ok=True)
    (xsd_root / name).write_text(text, encoding="utf-8")
    return xsd_root


class CollectDeclarationsTests(SimpleTestCase):
    def test_documentation_comes_from_the_element_then_its_type_then_nothing(self):
        with TemporaryDirectory() as tmp:
            declarations = collect_element_declarations(write_xsd(Path(tmp)))
        self.assertEqual(declarations["DayType"].documentation, "A type of day with properties.")  # whitespace normalised
        self.assertEqual(declarations["SimplePoint"].documentation, "Type for a Simple POINT.")
        self.assertEqual(declarations["OnwardCall"].documentation, "")
        self.assertEqual(declarations["DayType"].substitution_group, "DataManagedObject")
        self.assertEqual(declarations["DayType"].source, "types.xsd")

    def test_a_name_declared_twice_keeps_the_documented_declaration(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_xsd(root, "a.xsd", '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"><xsd:element name="Zone"/></xsd:schema>')
            xsd_root = write_xsd(
                root,
                "b.xsd",
                '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"><xsd:element name="Zone"><xsd:annotation>'
                "<xsd:documentation>An area.</xsd:documentation></xsd:annotation></xsd:element></xsd:schema>",
            )
            declarations = collect_element_declarations(xsd_root)
        self.assertEqual((declarations["Zone"].source, declarations["Zone"].documentation), ("b.xsd", "An area."))


class SelectionRuleTests(SimpleTestCase):
    def setUp(self):
        with TemporaryDirectory() as tmp:
            self.declarations = collect_element_declarations(write_xsd(Path(tmp)))

    def test_pascal_case_elements_are_recovered_but_placeholders_views_and_containers_are_not(self):
        recoverable = {name for name in self.declarations if is_recoverable(name, self.declarations.get(name))}
        self.assertEqual(recoverable, {"DayType", "SimplePoint", "OnwardCall"})
        self.assertFalse(is_recoverable("Undeclared", None))

    def test_only_dangling_targets_that_are_not_classes_yet_are_selected_in_a_stable_order(self):
        dangling = {"SimplePoint": 3, "DayType": 9, "Vehicle_Dummy": 5, "Line": 2, "Missing": 1}
        self.assertEqual(select_recoverable(dangling, self.declarations, known_classes={"Line"}), ["DayType", "SimplePoint"])


class RenderTests(SimpleTestCase):
    def test_camel_case_becomes_a_lower_case_label(self):
        self.assertEqual(camel_to_words("TimeDemandType"), "time demand type")
        self.assertEqual(camel_to_words("UicOperatingPeriod"), "uic operating period")
        self.assertEqual(camel_to_words("ParkingCapacity"), "parking capacity")

    def test_a_class_block_has_the_layout_the_extractor_uses_and_a_recovery_marker(self):
        declaration = ElementDeclaration("DayType", "netex_framework/day.xsd", 'A "type" of day.', "DataManagedObject")
        block = render_class(declaration, known_classes={"DataManagedObject"})
        self.assertTrue(block.startswith("netex:DayType\n    a owl:Class ;"))
        self.assertIn('skos:definition "A \\"type\\" of day."@en ;', block)
        self.assertIn("rdfs:subClassOf netex:DataManagedObject ;", block)
        self.assertIn('rdfs:comment "Extracted from: xsd/netex_framework/day.xsd (property-gap recovery)"@en .', block)

    def test_no_definition_and_no_subclass_when_none_is_known(self):
        block = render_class(ElementDeclaration("OnwardCall", "m.xsd", "", "siri:Something"), known_classes=set())
        self.assertNotIn("skos:definition", block)
        self.assertNotIn("rdfs:subClassOf", block)
        self.assertIn('skos:prefLabel "onward call"@en', block)

    def test_recovered_classes_are_appended_and_nothing_changes_when_there_are_none(self):
        declarations = {"DayType": ElementDeclaration("DayType", "d.xsd", "x", "")}
        self.assertEqual(append_recovered_classes("text\n", [], declarations, set()), "text\n")
        result = append_recovered_classes("text\n", ["DayType"], declarations, set())
        self.assertTrue(result.startswith("text\n\n# Classes recovered"))
        self.assertTrue(result.rstrip().endswith('(property-gap recovery)"@en .'))
