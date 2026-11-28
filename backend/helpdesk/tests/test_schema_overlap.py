from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.schema_overlap import compute_overlap, extract_schema_references, format_overlap_chunk

CA = """<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:include schemaLocation="siri/siri_requests.xsd"/>
  <xsd:complexType name="CloneStructure">
    <xsd:sequence>
      <xsd:element name="DatedVehicleJourneyRef" type="FramedVehicleJourneyRefStructure"/>
      <xsd:element name="Note" type="xsd:string"/>
    </xsd:sequence>
  </xsd:complexType>
  <xsd:complexType name="CaDelivery"><xsd:complexContent><xsd:extension base="AbstractServiceDeliveryStructure"/></xsd:complexContent></xsd:complexType>
</xsd:schema>"""
VM = """<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:include schemaLocation="siri/siri_requests.xsd"/>
  <xsd:complexType name="Activity">
    <xsd:sequence><xsd:element name="VehicleJourneyRef" type="siri:FramedVehicleJourneyRefStructure"/></xsd:sequence>
  </xsd:complexType>
  <xsd:complexType name="VmDelivery"><xsd:complexContent><xsd:extension base="AbstractServiceDeliveryStructure"/></xsd:complexContent></xsd:complexType>
</xsd:schema>"""
OTHER = """<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:complexType name="D"><xsd:complexContent><xsd:extension base="AbstractServiceDeliveryStructure"/></xsd:complexContent></xsd:complexType>
</xsd:schema>"""


class ExtractSchemaReferencesTests(SimpleTestCase):
    def test_references_with_their_declarations_and_no_builtins(self):
        refs = extract_schema_references(CA)
        self.assertEqual(refs["includes"], ["siri_requests.xsd"])
        self.assertEqual(refs["uses"]["FramedVehicleJourneyRefStructure"], ["DatedVehicleJourneyRef"])
        self.assertNotIn("string", refs["uses"])

    def test_namespace_prefix_is_dropped(self):
        self.assertIn("FramedVehicleJourneyRefStructure", extract_schema_references(VM)["uses"])

    def test_malformed_xml_gives_nothing(self):
        self.assertEqual(extract_schema_references("<xsd:schema"), {})


class ComputeOverlapTests(SimpleTestCase):
    def setUp(self):
        self.references = {
            "xsd/siri_controlAction_service.xsd": extract_schema_references(CA),
            "xsd/siri_vehicleMonitoring_service.xsd": extract_schema_references(VM),
            "xsd/siri_a_service.xsd": extract_schema_references(OTHER),
            "xsd/siri_b_service.xsd": extract_schema_references(OTHER),
        }
        self.overlap = compute_overlap(
            ["xsd/siri_controlAction_service.xsd", "xsd/siri_vehicleMonitoring_service.xsd"],
            ["Control Actions", "Vehicle Monitoring"],
            self.references,
            "https://github.com/TransmodelEcosystem/SIRI",
            "unknown",
        )

    def test_specific_shared_type_is_the_overlap(self):
        self.assertEqual([name for name, _ in self.overlap.domain], ["FramedVehicleJourneyRefStructure"])
        self.assertEqual(self.overlap.domain[0][1], [["DatedVehicleJourneyRef"], ["VehicleJourneyRef"]])

    def test_type_used_by_almost_every_sibling_is_framework(self):
        self.assertEqual(self.overlap.framework, ["AbstractServiceDeliveryStructure"])
        self.assertEqual(self.overlap.common_includes, ["siri_requests.xsd"])

    def test_chunk_names_both_sides_and_has_its_own_path(self):
        chunk = format_overlap_chunk(self.overlap)
        self.assertIn("FramedVehicleJourneyRefStructure: in Control Actions by DatedVehicleJourneyRef; in Vehicle Monitoring by VehicleJourneyRef", chunk["text"])
        self.assertTrue(chunk["sourcePath"].endswith("#shared-structure"))
        self.assertIn("/blob/main/", chunk["repositoryUrl"])

    def test_missing_references_give_no_overlap(self):
        self.assertIsNone(compute_overlap(["a.xsd", "b.xsd"], ["A", "B"], {"a.xsd": {}}, "u", "c"))
