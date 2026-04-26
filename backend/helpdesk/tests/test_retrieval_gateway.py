from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings


class RetrievalGatewayTests(TestCase):
    @override_settings(
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://localhost:7200",
        GRAPHDB_REPOSITORY="napcore-helpdesk",
        GRAPH_EXPANSION_MAX_CONCEPTS=1,
    )
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion")
    def test_retrieval_caps_graph_expansion_concepts(self, expand_mock):
        """Expanded graph concepts are capped by GRAPH_EXPANSION_MAX_CONCEPTS."""
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        expand_mock.return_value = {
            "opra:DelayedJourney",
            "opra:DelayStatistics",
            "opra:LateDatedVehicleJourneyEntry",
        }

        _chunks, trace = retrieve_chunks_with_trace(
            question="How to exchange delayed journey metrics?",
            top_k=5,
            min_score=0.0,
            graph_rag_enabled=True,
        )

        self.assertEqual(trace["graphConceptCap"], 1)
        self.assertLessEqual(len(trace["graphConceptIds"]), 1)

    @override_settings(
        RETRIEVAL_MAX_SAME_SOURCE_PATH=1,
        RETRIEVAL_DIVERSITY_ENABLED=False,
    )
    def test_retrieval_caps_repeated_source_path_hits(self):
        """Top-k output is limited to configured max hits per source path."""
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        shared_path = "xsd/opra_service/opra_service_serviceIntensity.xsd"
        for idx in range(3):
            text = f"Service intensity delayed journey exchange sample {idx}."
            SourceChunk.objects.get_or_create(
                chunk_id=f"wave2-source-cap-{idx}",
                defaults={
                    "repository_url": "https://github.com/OpRa-CEN/OpRa",
                    "commit_sha": "abc",
                    "source_path": shared_path,
                    "label": f"shared-{idx}",
                    "text": text,
                    "standards_scope": ["OpRa"],
                    "quality_score": 0.90,
                    "doc_type": "schema",
                    "embedding_vector": build_text_embedding(text),
                },
            )

        other_text = "Service intensity delayed journey exchange independent evidence."
        SourceChunk.objects.get_or_create(
            chunk_id="wave2-source-cap-other",
            defaults={
                "repository_url": "https://github.com/OpRa-CEN/OpRa",
                "commit_sha": "abc",
                "source_path": "xsd/opra_service/opra_service_delays.xsd",
                "label": "independent",
                "text": other_text,
                "standards_scope": ["OpRa"],
                "quality_score": 0.88,
                "doc_type": "schema",
                "embedding_vector": build_text_embedding(other_text),
            },
        )

        chunks, trace = retrieve_chunks_with_trace(
            question="service intensity delayed journey exchange",
            top_k=5,
            min_score=0.0,
            scope=["OpRa"],
            graph_rag_enabled=False,
        )

        shared_count = sum(1 for chunk in chunks if chunk.get("sourcePath") == shared_path)
        self.assertLessEqual(shared_count, 1)
        self.assertEqual(trace["retrievalSourcePathCap"], 1)

    def test_question_doc_type_hints_prefers_example_over_schema_for_example_xml(self):
        from helpdesk.services.retrieval_gateway import _question_doc_type_hints

        hints = _question_doc_type_hints("Show me an XML example for a simple line with stop points")

        self.assertIn("example", hints)
        self.assertNotIn("schema", hints)

    @override_settings(
        GRAPH_EXPANSION_MAX_CONCEPTS=64,
        GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=40,
    )
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion")
    def test_example_xml_query_reduces_graph_candidate_cap(self, expand_mock):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        expand_mock.return_value = {
            "netex:Line",
            "netex:ScheduledStopPoint",
            "netex:StopPlace",
            "netex:Route",
        }

        _chunks, trace = retrieve_chunks_with_trace(
            question="Show me a NeTEx XML example for a simple line with stop points.",
            top_k=6,
            min_score=0.0,
            graph_rag_enabled=True,
            scope=["NeTEx"],
        )

        self.assertEqual(trace["graphConceptCap"], 16)
        self.assertEqual(trace["graphCandidateCap"], 12)

    @override_settings(
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://localhost:7200",
        GRAPHDB_REPOSITORY="napcore-helpdesk",
        GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=6,
        RETRIEVAL_DIVERSITY_ENABLED=False,
    )
    @patch("helpdesk.services.retrieval_gateway._postgres_hybrid_candidates")
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion")
    @patch("helpdesk.services.retrieval_gateway.get_concept_canonical_terms")
    @patch("helpdesk.services.retrieval_gateway.get_concept_example_paths")
    @patch("helpdesk.services.retrieval_gateway.extract_graph_concepts")
    def test_graph_candidate_ranking_keeps_specific_example_before_cap(
        self,
        extract_graph_concepts_mock,
        get_concept_example_paths_mock,
        get_concept_canonical_terms_mock,
        expand_mock,
        postgres_candidates_mock,
    ):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        postgres_candidates_mock.return_value = SourceChunk.objects.none()
        expand_mock.return_value = {"netex:Line"}
        get_concept_canonical_terms_mock.return_value = ["simple line"]
        get_concept_example_paths_mock.return_value = {"examples/functions/line/NeTEx_01_simple_line.xml"}

        def extract_graph_concepts_side_effect(text: str) -> set[str]:
            return {"netex:Line"} if "line" in text.lower() else set()

        extract_graph_concepts_mock.side_effect = extract_graph_concepts_side_effect

        for idx in range(8):
            generic_text = f"Line example structure {idx} with network and route references."
            SourceChunk.objects.create(
                repository_url="https://github.com/NeTEx-CEN/NeTEx",
                commit_sha="abc",
                source_path=f"examples/functions/line/line_structure_{idx}.xml",
                chunk_id=f"generic-line-{idx}",
                label=f"Line structure {idx}",
                text=generic_text,
                standards_scope=["NeTEx"],
                quality_score=0.95,
                doc_type="example",
                embedding_vector=build_text_embedding(generic_text),
            )

        canonical_text = "Simple line XML example with stop points, StopPlace and ScheduledStopPoint."
        SourceChunk.objects.create(
            repository_url="https://github.com/NeTEx-CEN/NeTEx",
            commit_sha="abc",
            source_path="examples/functions/line/NeTEx_01_simple_line.xml",
            chunk_id="canonical-simple-line",
            label="NeTEx simple line example",
            text=canonical_text,
            standards_scope=["NeTEx"],
            quality_score=0.35,
            doc_type="example",
            embedding_vector=build_text_embedding(canonical_text),
        )

        with patch(
            "helpdesk.services.retrieval_gateway.GRAPH_CONCEPT_ALIASES",
            {
                "netex:Line": {
                    "line",
                    "service line",
                    "simple line",
                    "simple line xml",
                    "NeTEx_01_simple_line.xml",
                }
            },
        ):
            chunks, trace = retrieve_chunks_with_trace(
                question="Show me a NeTEx XML example for a simple line with stop points.",
                top_k=6,
                min_score=0.0,
                scope=["NeTEx"],
                graph_rag_enabled=True,
            )

        source_paths = [chunk.get("sourcePath") for chunk in chunks]

        self.assertIn("examples/functions/line/NeTEx_01_simple_line.xml", source_paths)
        self.assertEqual(trace["graphCandidateCap"], 6)

    @patch("helpdesk.services.retrieval_gateway.extract_graph_concepts")
    def test_graph_score_boosts_exact_example_path_on_direct_concept_hit(self, extract_graph_concepts_mock):
        from helpdesk.services.retrieval_gateway import _graph_score_adjustment

        extract_graph_concepts_mock.return_value = {"netex:Line"}

        adjustment, graph_hit, matching_concepts = _graph_score_adjustment(
            graph_enabled=True,
            question_concepts={"netex:Line"},
            expanded_concepts={"netex:Line"},
            concept_example_paths={"examples/functions/line/NeTEx_01_simple_line.xml"},
            chunk_text="Simple line XML example",
            source_path="examples/functions/line/NeTEx_01_simple_line.xml",
            label="NeTEx simple line",
            heading="",
            hinted_doc_types={"example"},
        )

        self.assertTrue(graph_hit)
        self.assertEqual(matching_concepts, {"netex:Line"})
        self.assertGreaterEqual(adjustment, 0.50)
