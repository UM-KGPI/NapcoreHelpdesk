from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from helpdesk.management.commands.extract_xsd_ontology import _iter_xsd_files, resolve_repo_path


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


class ResolveRepoPathTests(SimpleTestCase):
    def test_option_beats_environment_beats_the_sibling_directory(self):
        with TemporaryDirectory() as tmp:
            from_option, from_env = Path(tmp) / "option", Path(tmp) / "env"
            from_option.mkdir()
            from_env.mkdir()
            with patch.dict(os.environ, {"NETEX_REPO_PATH": str(from_env)}):
                self.assertEqual(resolve_repo_path(str(from_option), name="NeTEx", env_var="NETEX_REPO_PATH"), from_option)
                self.assertEqual(resolve_repo_path(None, name="NeTEx", env_var="NETEX_REPO_PATH"), from_env)

    def test_without_option_or_environment_a_sibling_directory_of_the_repository_is_used(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "OpRa").mkdir()
            fake_repo_root = Path(tmp) / "NapcoreHelpdesk"
            with patch.dict(os.environ, {}, clear=False), patch(
                "helpdesk.management.commands.extract_xsd_ontology.REPO_ROOT", fake_repo_root
            ):
                os.environ.pop("OPRA_REPO_PATH", None)
                self.assertEqual(
                    resolve_repo_path(None, name="OpRa", env_var="OPRA_REPO_PATH"), Path(tmp) / "OpRa"
                )

    def test_a_missing_repository_says_how_to_point_to_it(self):
        with patch.dict(os.environ, {"SIRI_REPO_PATH": "/does/not/exist"}):
            with self.assertRaises(CommandError) as ctx:
                resolve_repo_path(None, name="SIRI", env_var="SIRI_REPO_PATH")
        message = str(ctx.exception)
        self.assertIn("--siri-path", message)
        self.assertIn("SIRI_REPO_PATH", message)
        self.assertNotIn("/Users/", message)


def _write_repo(root: Path, standard_dir: str, element: str) -> Path:
    """A minimal repository: one XSD with one documented element."""
    xsd_dir = root / "xsd" / standard_dir
    xsd_dir.mkdir(parents=True)
    (xsd_dir / "concept.xsd").write_text(
        '<?xml version="1.0"?>\n'
        '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
        f'  <xsd:element name="{element}"><xsd:annotation><xsd:documentation>'
        f"A {element} describes a transport concept used for exchanging public transport data."
        "</xsd:documentation></xsd:annotation></xsd:element>\n"
        "</xsd:schema>\n",
        encoding="utf-8",
    )
    return root


class ExtractCommandOptionTests(SimpleTestCase):
    def test_turtle_goes_to_the_requested_directory_without_any_developer_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            netex = _write_repo(root / "NeTEx", "netex_part_1", "StopPlace")
            opra = _write_repo(root / "OpRa", "opra_framework", "DelayIndicator")
            siri = _write_repo(root / "SIRI", "siri", "EstimatedCall")
            out_dir = root / "ttl"

            call_command(
                "extract_xsd_ontology",
                "--skip-example-xml",
                "--netex-path", str(netex),
                "--opra-path", str(opra),
                "--siri-path", str(siri),
                "--ttl-output-dir", str(out_dir),
                stdout=StringIO(),
            )

            written = sorted(path.name for path in out_dir.glob("*.ttl"))
            self.assertEqual(written, ["netex.ttl", "opra.ttl", "siri.ttl"])
            self.assertIn("netex:StopPlace", (out_dir / "netex.ttl").read_text(encoding="utf-8"))

    def test_a_missing_repository_is_an_error_naming_the_option(self):
        with TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"NETEX_REPO_PATH": ""}, clear=False):
                with self.assertRaises(CommandError) as ctx:
                    call_command("extract_xsd_ontology", "--netex-path", str(Path(tmp) / "nope"), stdout=StringIO())
        self.assertIn("--netex-path", str(ctx.exception))
