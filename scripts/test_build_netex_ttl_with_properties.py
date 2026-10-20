"""Unit tests for the subClassOf extraction in build_netex_ttl_with_properties.py.

Run directly: python -m unittest scripts.test_build_netex_ttl_with_properties
(no pytest/Django dependency; this script has no other test coverage).
"""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

from build_netex_ttl_with_properties import (
    SchemaIndex,
    compute_subclass_edges,
    find_extension_base,
)


def _complex_type(xml: str) -> ET.Element:
    return ET.fromstring(xml)


class FindExtensionBaseTests(unittest.TestCase):
    def test_extension_base_is_returned(self):
        ctype = _complex_type(
            '<xsd:complexType xmlns:xsd="http://www.w3.org/2001/XMLSchema" name="ServiceJourney_VersionStructure">'
            '  <xsd:complexContent>'
            '    <xsd:extension base="Journey_VersionStructure">'
            '      <xsd:sequence/>'
            '    </xsd:extension>'
            '  </xsd:complexContent>'
            "</xsd:complexType>"
        )
        self.assertEqual(find_extension_base(ctype), "Journey_VersionStructure")

    def test_restriction_is_not_treated_as_a_base(self):
        # A restriction narrows the value space; it is not a subtype relationship.
        ctype = _complex_type(
            '<xsd:complexType xmlns:xsd="http://www.w3.org/2001/XMLSchema" name="Foo">'
            '  <xsd:complexContent>'
            '    <xsd:restriction base="Bar_VersionStructure">'
            '      <xsd:sequence/>'
            '    </xsd:restriction>'
            '  </xsd:complexContent>'
            "</xsd:complexType>"
        )
        self.assertIsNone(find_extension_base(ctype))

    def test_no_complex_content_returns_none(self):
        ctype = _complex_type(
            '<xsd:complexType xmlns:xsd="http://www.w3.org/2001/XMLSchema" name="Flat">'
            "  <xsd:sequence/>"
            "</xsd:complexType>"
        )
        self.assertIsNone(find_extension_base(ctype))


class ComputeSubclassEdgesTests(unittest.TestCase):
    def test_service_journey_extends_journey(self):
        idx = SchemaIndex()
        idx.complex_types["ServiceJourney_VersionStructure"] = _complex_type(
            '<xsd:complexType xmlns:xsd="http://www.w3.org/2001/XMLSchema" name="ServiceJourney_VersionStructure">'
            '  <xsd:complexContent>'
            '    <xsd:extension base="Journey_VersionStructure">'
            '      <xsd:sequence/>'
            '    </xsd:extension>'
            '  </xsd:complexContent>'
            "</xsd:complexType>"
        )
        class_to_type = {"ServiceJourney": "ServiceJourney_VersionStructure"}
        ttl_classes = {"ServiceJourney", "Journey"}

        edges = compute_subclass_edges(class_to_type, idx, ttl_classes)

        self.assertEqual(edges, {"ServiceJourney": "Journey"})

    def test_base_not_in_ttl_classes_is_skipped(self):
        idx = SchemaIndex()
        idx.complex_types["Foo_VersionStructure"] = _complex_type(
            '<xsd:complexType xmlns:xsd="http://www.w3.org/2001/XMLSchema" name="Foo_VersionStructure">'
            '  <xsd:complexContent>'
            '    <xsd:extension base="UnknownBase_VersionStructure">'
            '      <xsd:sequence/>'
            '    </xsd:extension>'
            '  </xsd:complexContent>'
            "</xsd:complexType>"
        )
        class_to_type = {"Foo": "Foo_VersionStructure"}
        ttl_classes = {"Foo"}

        edges = compute_subclass_edges(class_to_type, idx, ttl_classes)

        self.assertEqual(edges, {})

    def test_self_extension_is_not_a_cycle(self):
        # Shouldn't happen in real NeTEx XSDs, but a class extending a base that
        # resolves to its own name must not produce a self-loop edge.
        idx = SchemaIndex()
        idx.complex_types["Foo_VersionStructure"] = _complex_type(
            '<xsd:complexType xmlns:xsd="http://www.w3.org/2001/XMLSchema" name="Foo_VersionStructure">'
            '  <xsd:complexContent>'
            '    <xsd:extension base="Foo_VersionStructure">'
            '      <xsd:sequence/>'
            '    </xsd:extension>'
            '  </xsd:complexContent>'
            "</xsd:complexType>"
        )
        class_to_type = {"Foo": "Foo_VersionStructure"}
        ttl_classes = {"Foo"}

        edges = compute_subclass_edges(class_to_type, idx, ttl_classes)

        self.assertEqual(edges, {})


if __name__ == "__main__":
    unittest.main()
