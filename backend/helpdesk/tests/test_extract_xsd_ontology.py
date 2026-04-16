from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from helpdesk.management.commands.extract_xsd_ontology import _iter_xsd_files


class ExtractXsdOntologyTests(SimpleTestCase):
    def test_iter_xsd_files_scans_full_netex_tree_and_excludes_siri(self):
        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            xsd_root = repo_root / "xsd"
            (xsd_root / "netex_part_1").mkdir(parents=True, exist_ok=True)
            (xsd_root / "netex_framework").mkdir(parents=True, exist_ok=True)
            (xsd_root / "siri").mkdir(parents=True, exist_ok=True)
            (xsd_root / "netex_part_1" / "line.xsd").write_text("", encoding="utf-8")
            (xsd_root / "netex_framework" / "facility.xsd").write_text("", encoding="utf-8")
            (xsd_root / "siri" / "request.xsd").write_text("", encoding="utf-8")

            files = _iter_xsd_files(repo_root, standard="netex", key_files_only=False)

        relative_paths = sorted(str(path.relative_to(xsd_root)) for path in files)
        self.assertEqual(
            relative_paths,
            [
                "netex_framework/facility.xsd",
                "netex_part_1/line.xsd",
            ],
        )

    def test_iter_xsd_files_scans_full_opra_tree(self):
        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            xsd_root = repo_root / "xsd"
            (xsd_root / "opra_framework").mkdir(parents=True, exist_ok=True)
            (xsd_root / "opra_service").mkdir(parents=True, exist_ok=True)
            (xsd_root / "opra_framework" / "indicator.xsd").write_text("", encoding="utf-8")
            (xsd_root / "opra_service" / "capacity.xsd").write_text("", encoding="utf-8")

            files = _iter_xsd_files(repo_root, standard="opra", key_files_only=False)

            relative_paths = sorted(str(path.relative_to(xsd_root)) for path in files)

        self.assertEqual(
            relative_paths,
            [
                "opra_framework/indicator.xsd",
                "opra_service/capacity.xsd",
            ],
        )

    def test_iter_xsd_files_scans_siri_tree_without_external_utility_groups(self):
        with TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            xsd_root = repo_root / "xsd"
            (xsd_root / "siri_model").mkdir(parents=True, exist_ok=True)
            (xsd_root / "siri").mkdir(parents=True, exist_ok=True)
            (xsd_root / "wsdl_model").mkdir(parents=True, exist_ok=True)
            (xsd_root / "gml").mkdir(parents=True, exist_ok=True)
            (xsd_root / "ifopt").mkdir(parents=True, exist_ok=True)
            (xsd_root / "siri_model" / "journey.xsd").write_text("", encoding="utf-8")
            (xsd_root / "siri" / "request.xsd").write_text("", encoding="utf-8")
            (xsd_root / "wsdl_model" / "producer.xsd").write_text("", encoding="utf-8")
            (xsd_root / "gml" / "base.xsd").write_text("", encoding="utf-8")
            (xsd_root / "ifopt" / "stop.xsd").write_text("", encoding="utf-8")

            files = _iter_xsd_files(repo_root, standard="siri", key_files_only=False)
            relative_paths = sorted(str(path.relative_to(xsd_root)) for path in files)

        self.assertEqual(
            relative_paths,
            [
                "siri/request.xsd",
                "siri_model/journey.xsd",
                "wsdl_model/producer.xsd",
            ],
        )
