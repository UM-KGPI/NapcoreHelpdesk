from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "build_netex_ttl_with_properties.py"

NETEX_TTL = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix netex: <https://netex.org.uk/netex/2.0#> .

<https://netex.org.uk/netex/2.0>
    a owl:Ontology ;
    owl:versionInfo "0.3" .

netex:Line
    a owl:Class .

netex:Operator
    a owl:Class .
"""

XSD = """<?xml version="1.0"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:complexType name="Line_VersionStructure">
    <xsd:sequence>
      <xsd:element name="PublicCode" type="xsd:string"/>
      <xsd:element name="OperatorRef" type="OperatorRefStructure"/>
    </xsd:sequence>
  </xsd:complexType>
  <xsd:complexType name="Operator_VersionStructure"/>
  <xsd:complexType name="OperatorRefStructure"/>
</xsd:schema>
"""


def load_script():
    spec = importlib.util.spec_from_file_location("build_netex_ttl_with_properties", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NetexEnrichmentScriptTests(SimpleTestCase):
    def setUp(self):
        self.script = load_script()

    def _fixture(self, root: Path) -> tuple[Path, Path]:
        xsd_root = root / "xsd"
        (xsd_root / "netex_part_1").mkdir(parents=True)
        (xsd_root / "netex_part_1" / "line.xsd").write_text(XSD, encoding="utf-8")
        ttl = root / "netex.ttl"
        ttl.write_text(NETEX_TTL, encoding="utf-8")
        return ttl, xsd_root

    def test_runs_with_explicit_paths_and_writes_the_extracted_properties(self):
        with TemporaryDirectory() as tmp:
            ttl, xsd_root = self._fixture(Path(tmp))
            out = Path(tmp) / "out.ttl"
            ttl_path, out_path, root, subclass_only = self.script.parse_args(
                [str(ttl), str(out), "--netex-xsd-root", str(xsd_root)]
            )
            self.assertFalse(subclass_only)
            self.script.main(ttl_path, out_path, root)
            result = out.read_text(encoding="utf-8")

        self.assertIn("owl:DatatypeProperty", result)  # Line.PublicCode
        self.assertIn("owl:ObjectProperty", result)  # Line.OperatorRef -> Operator
        self.assertIn("netex:Line", result)

    def test_default_output_is_next_to_the_input_with_a_new_suffix(self):
        with TemporaryDirectory() as tmp:
            ttl, xsd_root = self._fixture(Path(tmp))
            _, out_path, _, _ = self.script.parse_args([str(ttl), "--netex-xsd-root", str(xsd_root)])
        self.assertEqual(out_path.name, "netex.ttl.new")

    def test_the_xsd_root_comes_from_the_environment_when_no_option_is_given(self):
        with TemporaryDirectory() as tmp:
            ttl, xsd_root = self._fixture(Path(tmp))
            with patch.dict(os.environ, {"NETEX_XSD_ROOT": str(xsd_root)}):
                _, _, root, _ = self.script.parse_args([str(ttl)])
        self.assertEqual(root, xsd_root)

    def test_a_missing_xsd_folder_or_ttl_is_a_clear_error_without_a_developer_path(self):
        with TemporaryDirectory() as tmp:
            ttl, _ = self._fixture(Path(tmp))
            with self.assertRaises(SystemExit):
                self.script.parse_args([str(ttl), "--netex-xsd-root", str(Path(tmp) / "nope")])
            with self.assertRaises(SystemExit):
                self.script.parse_args([str(Path(tmp) / "missing.ttl"), "--netex-xsd-root", str(Path(tmp))])
        self.assertNotIn("/Users/", SCRIPT.read_text(encoding="utf-8"))

    def test_main_emits_subclass_of_from_xsd_extension(self):
        with TemporaryDirectory() as tmp:
            ttl, xsd_root = self._fixture(Path(tmp))
            (xsd_root / "netex_part_1" / "flexible_line.xsd").write_text(
                '<?xml version="1.0"?>\n'
                '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
                '  <xsd:complexType name="FlexibleLine_VersionStructure">\n'
                '    <xsd:complexContent>\n'
                '      <xsd:extension base="Line_VersionStructure">\n'
                "        <xsd:sequence/>\n"
                "      </xsd:extension>\n"
                "    </xsd:complexContent>\n"
                "  </xsd:complexType>\n"
                "</xsd:schema>\n",
                encoding="utf-8",
            )
            ttl.write_text(ttl.read_text(encoding="utf-8") + "\nnetex:FlexibleLine\n    a owl:Class .\n", encoding="utf-8")
            out = Path(tmp) / "out.ttl"
            ttl_path, out_path, root, subclass_only = self.script.parse_args(
                [str(ttl), str(out), "--netex-xsd-root", str(xsd_root)]
            )
            self.script.main(ttl_path, out_path, root)
            result = out.read_text(encoding="utf-8")

        self.assertIn("netex:FlexibleLine rdfs:subClassOf netex:Line .", result)

    def test_subclass_only_appends_without_duplicating_existing_properties(self):
        with TemporaryDirectory() as tmp:
            ttl, xsd_root = self._fixture(Path(tmp))
            out = Path(tmp) / "out.ttl"
            ttl_path, out_path, root, subclass_only = self.script.parse_args(
                ["--subclass-only", str(ttl), str(out), "--netex-xsd-root", str(xsd_root)]
            )
            self.assertTrue(subclass_only)
            edge_count = self.script.append_subclass_section_only(ttl_path, out_path, root)
            result = out.read_text(encoding="utf-8")

        self.assertEqual(edge_count, 0)  # no xsd:extension in this fixture
        self.assertNotIn("owl:ObjectProperty", result)  # untouched: not re-emitted
        self.assertIn("netex:Line", result)  # original content preserved
