from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from django.core.management import call_command
from django.test import SimpleTestCase


class BuildFederatedOntologiesCommandTests(SimpleTestCase):
    def test_command_generates_standard_modules_from_glossary(self):
        payload = {
            "concepts": {
                "netex:VehicleJourney": {
                    "labels": ["vehicle journey", "journey"],
                    "description": "A scheduled vehicle journey.",
                    "maps_to_nch": "nch:vehicle-journey",
                    "parent": "transmodel:Journey",
                    "related_to": ["opra:DelayedJourney"],
                },
                "opra:DelayedJourney": {
                    "labels": ["delayed journey"],
                    "description": "An OpRa delayed journey concept.",
                    "synonym_of": "netex:VehicleJourney",
                    "related_to": ["netex:VehicleJourney"],
                },
                "siri:VehicleMonitoring": {
                    "labels": ["vehicle monitoring"],
                    "description": "SIRI vehicle monitoring service concept.",
                    "maps_to_nits": "nits:vehicle-journey",
                },
                "datex:TrafficEvent": {
                    "labels": ["traffic event"],
                    "description": "DATEX II traffic event concept.",
                    "maps_to_nits": "nits:delay",
                },
                "transmodel:Journey": {
                    "labels": ["journey"],
                },
            }
        }

        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "standards.yaml"
            output_dir = tmp / "ontology"
            input_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

            call_command(
                "build_federated_ontologies",
                input=str(input_path),
                output_dir=str(output_dir),
                created_date="2026-04-16",
                ontology_version="0.3.0-test",
            )

            netex_text = (output_dir / "netex-federated.ttl").read_text(encoding="utf-8")
            opra_text = (output_dir / "opra-federated.ttl").read_text(encoding="utf-8")
            siri_text = (output_dir / "siri-federated.ttl").read_text(encoding="utf-8")
            datex_text = (output_dir / "datex-federated.ttl").read_text(encoding="utf-8")

        self.assertIn('owl:versionInfo "0.3.0-test"', netex_text)
        self.assertIn("netex:VehicleJourney a skos:Concept", netex_text)
        self.assertIn("skos:exactMatch nits:vehicle-journey", netex_text)
        self.assertIn("skos:broader transmodel:Journey", netex_text)
        self.assertIn("skos:related opra:DelayedJourney", netex_text)
        self.assertIn("opra:DelayedJourney a skos:Concept", opra_text)
        self.assertIn("skos:closeMatch netex:VehicleJourney", opra_text)
        self.assertIn("siri:VehicleMonitoring a skos:Concept", siri_text)
        self.assertIn("skos:exactMatch nits:vehicle-journey", siri_text)
        self.assertIn("datex:TrafficEvent a skos:Concept", datex_text)
        self.assertIn("skos:exactMatch nits:delay", datex_text)