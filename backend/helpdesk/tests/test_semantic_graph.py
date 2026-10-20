from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services.semantic_graph import (
    _alias_matches_text,
    _normalize_for_matching,
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


class AliasMatchesTextTests(SimpleTestCase):
    """Regression coverage for the word-boundary bug found investigating a weak
    production answer to "What is OnwardCall?": a multi-word alias like "is on"
    is a plain substring of "what is onwardcall" (the end of "is" plus the start
    of "onwardcall"), even though "on" is never a real token in that text. The
    fix drops the substring check and relies solely on the token-subset check,
    which already requires every alias word to appear as its own token."""

    def test_multiword_alias_does_not_match_across_a_word_boundary(self):
        text = _normalize_for_matching("What is OnwardCall?")
        self.assertFalse(_alias_matches_text("is on", text))

    def test_multiword_alias_still_matches_as_separate_real_words(self):
        text = _normalize_for_matching("the light is on now")
        self.assertTrue(_alias_matches_text("is on", text))

    def test_multiword_alias_still_matches_scattered_out_of_order(self):
        text = _normalize_for_matching("what type of line is used")
        self.assertTrue(_alias_matches_text("type of line", text))

    def test_multiword_alias_matches_glued_camelcase_class_name(self):
        """"OnwardCall" typed with no space lowercases to one glued token
        ("onwardcall") the subset check alone can't split. Checking whether the
        alias's words concatenated form a single existing text token covers this
        for every multi-word alias, not just this one concept."""
        text = _normalize_for_matching("What is OnwardCall?")
        self.assertTrue(_alias_matches_text("onward call", text))

    def test_glued_match_does_not_reopen_the_word_boundary_bug(self):
        """"is on" joined is "ison", which must not equal "onwardcall"."""
        text = _normalize_for_matching("What is OnwardCall?")
        self.assertFalse(_alias_matches_text("is on", text))


class SubclassTraversalTests(SimpleTestCase):
    """rdfs:subClassOf is followed from a class to its subclasses only. Followed
    upward, netex:Journey reaches framework roots such as netex:DataManagedObject
    (92 subclasses), and the next hop floods the expansion with unrelated
    siblings."""

    def _relations(self):
        ontology = {
            "concepts": {
                "netex:DataManagedObject": {"labels": ["x"], "related_to": [], "narrower": ["netex:Journey", "netex:Unrelated"]},
                "netex:Journey": {"labels": ["x"], "related_to": [], "narrower": ["netex:ServiceJourney"]},
                "netex:ServiceJourney": {"labels": ["x"], "related_to": ["netex:Line"], "narrower": []},
                "netex:Line": {"labels": ["x"], "related_to": [], "narrower": []},
                "netex:Unrelated": {"labels": ["x"], "related_to": [], "narrower": []},
            }
        }
        with patch.object(semantic_graph, "TRANSMODEL_TO_CONCEPTS", {}):
            return semantic_graph._build_graph_relations_from_ontology(ontology)

    def test_abstract_class_reaches_its_subclass(self):
        self.assertIn("netex:ServiceJourney", self._relations()["netex:Journey"])

    def test_class_does_not_climb_to_its_superclass(self):
        self.assertNotIn("netex:DataManagedObject", self._relations().get("netex:Journey", set()))
        self.assertNotIn("netex:Journey", self._relations().get("netex:ServiceJourney", set()))

    def test_object_properties_stay_bidirectional(self):
        relations = self._relations()
        self.assertIn("netex:Line", relations["netex:ServiceJourney"])
        self.assertIn("netex:ServiceJourney", relations["netex:Line"])


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
