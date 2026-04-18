from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services.semantic_graph import (
    _build_concept_nits_mapping,
    _build_nits_relations,
    _validate_ontology_payload,
    expand_graph_concepts,
    get_concept_nits_ids,
)


class SemanticGraphMappingTests(SimpleTestCase):
    def test_opra_delayed_journey_aligns_to_vehicle_journey_cross_standard(self):
        with (
            patch.object(
                semantic_graph,
                "CONCEPT_TO_NITS",
                {
                    "opra:DelayedJourney": "nits:vehicle-journey",
                    "netex:VehicleJourney": "nits:vehicle-journey",
                },
            ),
            patch.object(
                semantic_graph,
                "NITS_TO_CONCEPTS",
                {
                    "nits:vehicle-journey": {
                        "opra:DelayedJourney",
                        "netex:VehicleJourney",
                    }
                },
            ),
            patch.object(semantic_graph, "NITS_RELATIONS", {}),
            patch.object(semantic_graph, "GRAPH_RELATIONS", {}),
        ):
            expanded = expand_graph_concepts({"opra:DelayedJourney"}, hops=1)

        self.assertIn("opra:DelayedJourney", expanded)
        self.assertIn("netex:VehicleJourney", expanded)

    def test_synonym_mapped_concepts_share_same_nits_identifier(self):
        with patch.object(
            semantic_graph,
            "CONCEPT_TO_NITS",
            {
                "opra:DelayedJourney": "nits:vehicle-journey",
                "netex:VehicleJourney": "nits:vehicle-journey",
            },
        ):
            nits_ids = get_concept_nits_ids({"opra:DelayedJourney", "netex:VehicleJourney"})

        self.assertEqual(len(nits_ids), 1)

    def test_nits_relation_expansion_links_delay_to_service_intensity_family(self):
        with (
            patch.object(
                semantic_graph,
                "CONCEPT_TO_NITS",
                {
                    "opra:DelayStatistics": "nits:delay",
                    "opra:TypeOfDelay": "nits:delay",
                    "opra:PlannedServiceIntensity": "nits:service-intensity",
                    "opra:ActualServiceIntensity": "nits:service-intensity",
                    "opra:ExpectedServiceIntensity": "nits:service-intensity",
                },
            ),
            patch.object(
                semantic_graph,
                "NITS_TO_CONCEPTS",
                {
                    "nits:delay": {
                        "opra:DelayStatistics",
                        "opra:TypeOfDelay",
                    },
                    "nits:service-intensity": {
                        "opra:PlannedServiceIntensity",
                        "opra:ActualServiceIntensity",
                        "opra:ExpectedServiceIntensity",
                    },
                },
            ),
            patch.object(
                semantic_graph,
                "NITS_RELATIONS",
                {
                    "nits:delay": {"nits:service-intensity"},
                    "nits:service-intensity": {"nits:delay"},
                },
            ),
            patch.object(semantic_graph, "GRAPH_RELATIONS", {}),
        ):
            expanded = expand_graph_concepts({"opra:DelayStatistics"}, hops=1)

        self.assertIn("opra:DelayStatistics", expanded)
        self.assertIn("opra:TypeOfDelay", expanded)
        self.assertTrue(
            {"opra:PlannedServiceIntensity", "opra:ActualServiceIntensity", "opra:ExpectedServiceIntensity"}
            .intersection(expanded)
        )

    def test_build_concept_nits_mapping_normalizes_explicit_targets_and_handles_cycles(self):
        ontology = {
            "concepts": {
                "demo:CapacityConcept": {
                    "labels": ["Capacity Concept"],
                    "maps_to_nch": "nch:Service Intensity",
                },
                "demo:CycleA": {
                    "labels": ["Cycle A"],
                    "synonym_of": "demo:CycleB",
                },
                "demo:CycleB": {
                    "labels": ["Cycle B"],
                    "synonym_of": "demo:CycleA",
                },
            }
        }

        mapping, reverse = _build_concept_nits_mapping(ontology)

        self.assertEqual(mapping["demo:CapacityConcept"], "nits:service-intensity")
        self.assertTrue(mapping["demo:CycleA"].startswith("nits:"))
        self.assertTrue(mapping["demo:CycleB"].startswith("nits:"))
        self.assertIn("demo:CapacityConcept", reverse["nits:service-intensity"])

    def test_build_nits_relations_ignores_invalid_targets_and_self_loops(self):
        relations = _build_nits_relations(
            {
                "concepts": {
                    "nits:alpha": {
                        "related_to": [
                            "nits:beta",
                            "nits:alpha",
                            "external:gamma",
                            42,
                        ]
                    },
                    "nits:beta": {
                        "related_to": "not-a-list",
                    },
                }
            }
        )

        self.assertIn("nits:beta", relations["nits:alpha"])
        self.assertNotIn("nits:alpha", relations["nits:alpha"])
        self.assertNotIn("external:gamma", relations["nits:alpha"])

    def test_validate_ontology_payload_sanitizes_invalid_concept_fields(self):
        validated = _validate_ontology_payload(
            {
                "namespaces": {"nits": "https://napcore.eu/ontology/nits#"},
                "concepts": {
                    "nits:journey": {
                        "labels": "not-a-list",
                        "related_to": ["nits:line", 42],
                        "example_sources": ["examples/a.xml", 1],
                        "maps_to_nits": 123,
                        "maps_to_nch": ["nch:journey"],
                        "synonym_of": {"bad": "type"},
                    }
                },
            },
            ontology_name="nits",
            required_namespace="nits",
        )

        concept = validated["concepts"]["nits:journey"]
        self.assertEqual(concept["labels"], [])
        self.assertEqual(concept["related_to"], [])
        self.assertEqual(concept["example_sources"], [])
        self.assertNotIn("maps_to_nits", concept)
        self.assertNotIn("maps_to_nch", concept)
        self.assertNotIn("synonym_of", concept)

    def test_validate_ontology_payload_requires_namespace_when_requested(self):
        with self.assertRaises(ValueError):
            _validate_ontology_payload(
                {
                    "namespaces": {"nch": "http://napcore.example.org/ontology/nch"},
                    "concepts": {},
                },
                ontology_name="nits",
                required_namespace="nits",
            )
