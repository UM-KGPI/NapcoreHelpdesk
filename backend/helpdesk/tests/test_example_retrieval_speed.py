"""Speed changes in answering example questions (2026-11-09): each must leave the results as they were,
except that an example from the standard no longer gets a second full search."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from helpdesk.services import retrieval_gateway, semantic_graph


class ExampleElementEvidenceTests(SimpleTestCase):
    def test_standard_example_uses_definitions_and_the_first_search(self):
        from helpdesk.api import views

        search = MagicMock()
        first = [{"chunkId": "a"}, {"chunkId": "quay-def"}]
        definitions = {"Quay": {"chunkId": "quay-def"}, "StopPlace": {"chunkId": "sp-def"}}
        with patch.object(views, "definition_chunk", side_effect=lambda e: definitions.get(e)), patch.object(
            views, "value_element_names", return_value=["Quay"]
        ), patch.object(views, "main_object", return_value="StopPlace"), patch(
            "helpdesk.services.retrieval_gateway.examples_using_elements", return_value=[{"chunkId": "ex-sp"}, {"chunkId": "a"}]
        ):
            chunks, trace = views._example_element_evidence(
                {"origin": "standard"}, ["SiteFrame", "stopPlaces", "StopPlace", "Quay"], first, {"t": 1}, search
            )
        search.assert_not_called()
        self.assertEqual([c["chunkId"] for c in chunks], ["quay-def", "sp-def", "ex-sp", "a"])
        self.assertEqual(trace, {"t": 1})

    def test_generated_example_still_searches(self):
        from helpdesk.api import views

        search = MagicMock(return_value=(["x"], {"t": 2}))
        self.assertEqual(views._example_element_evidence({"origin": "generated"}, ["Quay"], [], {}, search), (["x"], {"t": 2}))
        search.assert_called_once()


class AliasScoringTests(SimpleTestCase):
    def test_same_scores_as_scoring_each_alias(self):
        chunk = SimpleNamespace(
            source_path="examples/functions/stopPlace/quays.xml", label="Stop place quays", heading="Quays",
            text="<StopPlace><quays><Quay/></quays></StopPlace> a scheduled stop point", doc_type="example",
        )
        for aliases in [{"quay"}, {"Stop Place", "line"}, {"scheduled stop point"}, {"", "  "}, {"bus station"}, set()]:
            expected = max(
                (
                    retrieval_gateway._graph_alias_match_score(
                        a, source_path=chunk.source_path, label=chunk.label, heading=chunk.heading, text=chunk.text
                    )
                    for a in aliases
                ),
                default=0.0,
            )
            # 0.15: the examples/ path bonus the rank score adds; no question, no hinted types.
            self.assertAlmostEqual(retrieval_gateway._graph_candidate_rank_score(chunk, aliases, "", set()) - 0.15, expected)


class TextConceptCacheTests(SimpleTestCase):
    def setUp(self):
        semantic_graph._TEXT_CONCEPT_CACHE.clear()

    def test_cached_until_the_table_the_reload_or_the_extractor_changes(self):
        extractor = MagicMock(return_value={"netex:Quay"})
        with patch.object(semantic_graph, "reload_ontology_if_updated", return_value=False):
            self.assertEqual(semantic_graph.extract_text_concepts_cached("a quay", extractor=extractor), {"netex:Quay"})
            semantic_graph.extract_text_concepts_cached("a quay", extractor=extractor)
            self.assertEqual(extractor.call_count, 1)
            with patch.object(semantic_graph, "_ALIAS_GENERATION", semantic_graph._ALIAS_GENERATION + 1):
                semantic_graph.extract_text_concepts_cached("a quay", extractor=extractor)
            self.assertEqual(extractor.call_count, 2)
            with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", {"netex:Quay": ["quay"]}):
                semantic_graph.extract_text_concepts_cached("a quay", extractor=extractor)
            self.assertEqual(extractor.call_count, 3)
            other = MagicMock(return_value=set())
            self.assertEqual(semantic_graph.extract_text_concepts_cached("a quay", extractor=other), set())

    def test_scope_is_part_of_the_key_and_results_are_copies(self):
        extractor = MagicMock(side_effect=lambda text, scope=None: {"x:A"} if scope else {"x:B"})
        with patch.object(semantic_graph, "reload_ontology_if_updated", return_value=False):
            self.assertEqual(semantic_graph.extract_text_concepts_cached("t", ["NeTEx"], extractor=extractor), {"x:A"})
            self.assertEqual(semantic_graph.extract_text_concepts_cached("t", None, extractor=extractor), {"x:B"})
            semantic_graph.extract_text_concepts_cached("t", None, extractor=extractor).add("x:C")
            self.assertEqual(semantic_graph.extract_text_concepts_cached("t", None, extractor=extractor), {"x:B"})


class DefinitionChunkTests(TestCase):
    def test_the_elements_own_declaration_before_a_shared_documentation(self):
        from helpdesk.models import SourceChunk
        from helpdesk.services.schema_structure import definition_chunk

        source = "xsd/netex_framework/netex_reusableComponents/netex_vehicleType_version.xsd"
        doc = "A classification of public transport vehicles according to the vehicle scheduling requirements"
        for chunk_id, element in (("c1", "VehicleModel"), ("c2", "VehicleType")):
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc", source_path=source,
                chunk_id=chunk_id, text=f"Schema declaration: element {element}\nDefined in: {source}\nDocumentation: {doc}",
                embedding_vector=[0.0] * 1535 + [1.0],
            )
        with patch("helpdesk.services.schema_structure.fetch_structure", return_value={"documentation": doc, "source": source}):
            self.assertEqual(definition_chunk("VehicleType")["chunkId"], "c2")
            self.assertEqual(definition_chunk("VehicleModel")["chunkId"], "c1")
