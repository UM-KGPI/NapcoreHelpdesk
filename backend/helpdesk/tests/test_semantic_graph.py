from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services.semantic_graph import (
    _build_concept_nits_mapping,
    _build_nits_relations,
    _parse_transmodel_alignment_file,
    _validate_ontology_payload,
    expand_graph_concepts,
    get_concept_nits_ids,
    get_concept_transmodel_ids,
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


    def test_extract_graph_concepts_can_match_example_alias_on_standard_concept(self):
        with patch.object(
            semantic_graph,
            "GRAPH_CONCEPT_ALIASES",
            {"netex:Line": {"simple line", "simple line xml"}},
        ):
            concepts = semantic_graph.extract_graph_concepts(
                "Show me a NeTEx XML example for a simple line with stop points."
            )

        self.assertIn("netex:Line", concepts)


class TransmodelPivotTests(SimpleTestCase):
    """The static, GraphDB-independent replacement for the NITS cross-standard
    pivot (Phase 0.1 of docs/ontology/NITS-REMOVAL-PLAN.md)."""

    def test_parse_transmodel_alignment_file_extracts_exact_match_pairs(self):
        import tempfile
        from pathlib import Path

        sample = (
            "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
            "@prefix tm:   <https://transmodel-cen.eu/6.2/> .\n"
            "@prefix netex: <https://netex.org.uk/netex/2.0#> .\n"
            "\n"
            "netex:StopPlace\n"
            "    skos:exactMatch tm:STOP_PLACE ;\n"
            '    tmalign:transmodelDefinitionStatus "differs" ;\n'
            '    tmalign:alignmentMethod "name-match" .\n'
            "\n"
            "netex:QuayList\n"
            "    skos:exactMatch tm:NOT_A_REAL_CLASS ;\n"
            '    tmalign:transmodelDefinitionStatus "equivalent" ;\n'
            '    tmalign:alignmentMethod "curated" .\n'
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "transmodel-netex-align.ttl"
            path.write_text(sample, encoding="utf-8")
            mapping = _parse_transmodel_alignment_file(path)

        self.assertEqual(
            mapping,
            {
                "netex:StopPlace": "transmodel:STOP_PLACE",
                "netex:QuayList": "transmodel:NOT_A_REAL_CLASS",
            },
        )

    def test_parse_transmodel_alignment_file_missing_file_returns_empty(self):
        from pathlib import Path

        self.assertEqual(_parse_transmodel_alignment_file(Path("/nonexistent/x.ttl")), {})

    def test_get_concept_transmodel_ids_resolves_only_known_concepts(self):
        with patch.object(
            semantic_graph,
            "CONCEPT_TO_TRANSMODEL",
            {"netex:DatedVehicleJourney": "transmodel:DATED_VEHICLE_JOURNEY"},
        ):
            resolved = get_concept_transmodel_ids({"netex:DatedVehicleJourney", "netex:Unrelated"})

        self.assertEqual(resolved, {"transmodel:DATED_VEHICLE_JOURNEY"})

    def test_expand_graph_concepts_bridges_standards_through_shared_transmodel_class(self):
        """Mirrors the NITS-pivot bridge test above, but for the static
        Transmodel pivot and with no live ontology/GraphDB data at all --
        this is the mechanism that keeps working when GRAPHDB_ENABLED=False."""
        with (
            patch.object(
                semantic_graph,
                "CONCEPT_TO_TRANSMODEL",
                {
                    "netex:DatedVehicleJourney": "transmodel:DATED_VEHICLE_JOURNEY",
                    "siri:DatedVehicleJourney": "transmodel:DATED_VEHICLE_JOURNEY",
                },
            ),
            patch.object(
                semantic_graph,
                "TRANSMODEL_TO_CONCEPTS",
                {"transmodel:DATED_VEHICLE_JOURNEY": {"netex:DatedVehicleJourney", "siri:DatedVehicleJourney"}},
            ),
            patch.object(semantic_graph, "CONCEPT_TO_NITS", {}),
            patch.object(semantic_graph, "NITS_TO_CONCEPTS", {}),
            patch.object(semantic_graph, "GRAPH_RELATIONS", {}),
        ):
            expanded = expand_graph_concepts({"netex:DatedVehicleJourney"}, hops=1)

        self.assertIn("siri:DatedVehicleJourney", expanded)

    def test_real_committed_alignment_files_bridge_netex_and_siri_dated_vehicle_journey(self):
        """Regression test against the actual committed alignment TTLs (not a
        mock): confirms the plan's own worked example -- a NeTEx vehicle-
        journey concept must still surface its SIRI sibling with
        GRAPHDB_ENABLED=False -- holds against real data, not just a
        synthetic fixture."""
        expanded = expand_graph_concepts({"netex:DatedVehicleJourney"}, hops=1)
        self.assertIn("siri:DatedVehicleJourney", expanded)
