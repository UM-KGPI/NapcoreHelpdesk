from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services.semantic_graph import (
    _parse_transmodel_alignment_file,
    expand_graph_concepts,
    get_concept_transmodel_ids,
)


class SemanticGraphMappingTests(SimpleTestCase):
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
        """The static Transmodel pivot, with no live ontology/GraphDB data at
        all -- this is the mechanism that keeps working when
        GRAPHDB_ENABLED=False."""
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
