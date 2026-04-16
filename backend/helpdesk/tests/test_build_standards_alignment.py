from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase


class BuildStandardsAlignmentCommandTests(SimpleTestCase):
    def test_command_generates_exact_close_and_related_matches(self):
        payload = {
            "concepts": {
                "opra:DelayedJourney": {
                    "maps_to_nch": "nch:vehicle-journey",
                    "synonym_of": "netex:VehicleJourney",
                    "related_to": ["netex:JourneyPattern", "opra:DelayStatistics"],
                },
                "netex:VehicleJourney": {
                    "maps_to_nits": "nits:vehicle-journey",
                    "related_to": ["opra:DelayedJourney"],
                },
            }
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "standards.yaml"
            output_path = tmp / "standards-alignment.ttl"
            import yaml

            input_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

            call_command(
                "build_standards_alignment",
                input=str(input_path),
                output=str(output_path),
                created_date="2026-04-16",
                ontology_version="0.3.0-test",
            )

            text = output_path.read_text(encoding="utf-8")

        self.assertIn('owl:versionInfo "0.3.0-test"', text)
        self.assertIn("opra:DelayedJourney skos:exactMatch nits:vehicle-journey .", text)
        self.assertIn("netex:VehicleJourney skos:exactMatch nits:vehicle-journey .", text)
        self.assertIn("opra:DelayedJourney skos:closeMatch netex:VehicleJourney .", text)
        self.assertIn("netex:JourneyPattern skos:relatedMatch opra:DelayedJourney .", text)

    def test_command_includes_siri_and_datex_core_anchors(self):
        payload = {
            "concepts": {
                "siri:VehicleMonitoring": {
                    "maps_to_nits": "nits:vehicle-journey",
                },
                "datex:TrafficEvent": {
                    "maps_to_nch": "nch:delay",
                },
            }
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "standards.yaml"
            output_path = tmp / "standards-alignment.ttl"
            import yaml

            input_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

            call_command(
                "build_standards_alignment",
                input=str(input_path),
                output=str(output_path),
                no_related=True,
            )

            text = output_path.read_text(encoding="utf-8")

        self.assertIn("siri:VehicleMonitoring skos:exactMatch nits:vehicle-journey .", text)
        self.assertIn("datex:TrafficEvent skos:exactMatch nits:delay .", text)

    def test_command_skips_related_when_flag_is_set(self):
        payload = {
            "concepts": {
                "opra:DelayStatistics": {
                    "maps_to_nch": "nch:delay",
                    "related_to": ["netex:VehicleJourney"],
                }
            }
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "standards.yaml"
            output_path = tmp / "standards-alignment.ttl"
            import yaml

            input_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

            call_command(
                "build_standards_alignment",
                input=str(input_path),
                output=str(output_path),
                no_related=True,
            )

            text = output_path.read_text(encoding="utf-8")

        self.assertIn("opra:DelayStatistics skos:exactMatch nits:delay .", text)
        self.assertNotIn("skos:relatedMatch", text)