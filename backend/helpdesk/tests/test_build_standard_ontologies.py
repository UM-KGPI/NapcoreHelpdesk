from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

NETEX_XSD = """<?xml version="1.0"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:element name="Line" type="Line_VersionStructure"><xsd:annotation><xsd:documentation>
    A Line groups routes that are known to the public by one name or number in public transport.
  </xsd:documentation></xsd:annotation></xsd:element>
  <xsd:complexType name="Line_VersionStructure">
    <xsd:sequence>
      <xsd:element name="PublicCode" type="xsd:string"/>
      <xsd:element name="OperatorRef" type="OperatorRefStructure"/>
    </xsd:sequence>
  </xsd:complexType>
  <xsd:complexType name="OperatorRefStructure"/>
  <xsd:element name="Operator" type="Operator_VersionStructure"/>
  <xsd:complexType name="Operator_VersionStructure"><xsd:annotation><xsd:documentation>Type for an Operator.</xsd:documentation></xsd:annotation></xsd:complexType>
</xsd:schema>
"""


def single_xsd_repo(root: Path, folder: str, text: str) -> Path:
    directory = root / "xsd" / folder
    directory.mkdir(parents=True)
    (directory / "concept.xsd").write_text(text, encoding="utf-8")
    return root


def simple_repo(root: Path, folder: str, element: str) -> Path:
    return single_xsd_repo(
        root,
        folder,
        f'<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"><xsd:element name="{element}"><xsd:annotation>'
        f"<xsd:documentation>A {element} describes a transport concept used for exchanging public transport data."
        "</xsd:documentation></xsd:annotation></xsd:element></xsd:schema>",
    )


class BuildStandardOntologiesTests(SimpleTestCase):
    def test_generates_all_three_ontologies_and_recovers_a_property_target(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            netex = single_xsd_repo(root / "NeTEx", "netex_part_1", NETEX_XSD)
            opra = simple_repo(root / "OpRa", "opra_framework", "DelayIndicator")
            siri = simple_repo(root / "SIRI", "siri", "EstimatedCall")
            out = root / "out"
            stdout = StringIO()

            call_command(
                "build_standard_ontologies",
                "--netex-path", str(netex), "--opra-path", str(opra), "--siri-path", str(siri),
                "--output-dir", str(out),
                stdout=stdout,
            )

            self.assertEqual(sorted(p.name for p in out.glob("*.ttl")), ["netex.ttl", "opra.ttl", "siri.ttl"])
            netex_ttl = (out / "netex.ttl").read_text(encoding="utf-8")

        self.assertIn("netex:Line", netex_ttl)
        # Operator is only a property target: it is recovered, with the definition of its type.
        self.assertIn("netex:Operator\n    a owl:Class", netex_ttl)
        self.assertIn('skos:definition "Type for an Operator."@en', netex_ttl)
        self.assertIn("(property-gap recovery)", netex_ttl)
        self.assertIn("owl:ObjectProperty", netex_ttl)  # Line.OperatorRef now has a class to point to
        self.assertIn("Operator", stdout.getvalue())

    def test_a_second_run_gives_the_same_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repos = [
                single_xsd_repo(root / "NeTEx", "netex_part_1", NETEX_XSD),
                simple_repo(root / "OpRa", "opra_framework", "DelayIndicator"),
                simple_repo(root / "SIRI", "siri", "EstimatedCall"),
            ]
            runs = []
            for name in ("one", "two"):
                out = root / name
                call_command(
                    "build_standard_ontologies",
                    "--netex-path", str(repos[0]), "--opra-path", str(repos[1]), "--siri-path", str(repos[2]),
                    "--output-dir", str(out), stdout=StringIO(),
                )
                runs.append({p.name: p.read_bytes() for p in out.glob("*.ttl")})
        self.assertEqual(runs[0], runs[1])

    def test_a_missing_repository_is_an_error_naming_the_option(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(CommandError) as ctx:
                call_command("build_standard_ontologies", "--netex-path", str(Path(tmp) / "nope"), stdout=StringIO())
        self.assertIn("--netex-path", str(ctx.exception))

    def test_a_missing_enrichment_script_is_a_clear_error(self):
        with TemporaryDirectory() as tmp:
            with patch("helpdesk.management.commands.build_standard_ontologies.ENRICHMENT_SCRIPT", Path(tmp) / "gone.py"):
                with self.assertRaisesMessage(CommandError, "Enrichment script not found"):
                    call_command("build_standard_ontologies", "--netex-path", tmp, "--opra-path", tmp, "--siri-path", tmp, stdout=StringIO())
