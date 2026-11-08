from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings


class RetrievalGatewayTests(TestCase):
    @override_settings(
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://localhost:7200",
        GRAPHDB_REPOSITORY="napcore-helpdesk",
        GRAPH_EXPANSION_MAX_CONCEPTS=1,
    )
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion_with_distance")
    def test_retrieval_caps_graph_expansion_concepts(self, expand_mock):
        """Expanded graph concepts are capped by GRAPH_EXPANSION_MAX_CONCEPTS."""
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        expand_mock.return_value = {
            "opra:DelayedJourney": 0,
            "opra:DelayStatistics": 1,
            "opra:LateDatedVehicleJourneyEntry": 1,
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

    def test_preselect_reserves_slots_for_lexical_leaders_cut_by_vector_order(self):
        """A strong lexical match ranked low by vector similarity still reaches scoring."""
        from types import SimpleNamespace

        from helpdesk.services.retrieval_gateway import _preselect_base_ids

        # Vector-ranked: ids 1..12 with weak lexical rank, id 99 last but the best lexical match.
        vector_ranked = [SimpleNamespace(id=i, lexical_rank=0.1) for i in range(1, 13)]
        vector_ranked.append(SimpleNamespace(id=99, lexical_rank=1.0))

        selected = _preselect_base_ids(vector_ranked, base_limit=8, lexical_reserve=8)
        self.assertEqual(len(selected), 8)
        self.assertIn(99, selected)  # reserve is capped at a quarter: 6 by vector, 2 lexical
        self.assertTrue({1, 2, 3, 4, 5, 6}.issubset(selected))

        self.assertEqual(_preselect_base_ids(vector_ranked, base_limit=8, lexical_reserve=0), set(range(1, 9)))

    def test_question_doc_type_hints_prefers_example_over_schema_for_example_xml(self):
        from helpdesk.services.retrieval_gateway import _question_doc_type_hints

        hints = _question_doc_type_hints("Show me an XML example for a simple line with stop points")

        self.assertIn("example", hints)
        self.assertNotIn("schema", hints)

    @override_settings(
        GRAPH_EXPANSION_MAX_CONCEPTS=64,
        GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=40,
    )
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion_with_distance")
    def test_example_xml_query_reduces_graph_candidate_cap(self, expand_mock):
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        expand_mock.return_value = {
            "netex:Line": 0,
            "netex:ScheduledStopPoint": 1,
            "netex:StopPlace": 1,
            "netex:Route": 1,
        }

        _chunks, trace = retrieve_chunks_with_trace(
            question="Show me a NeTEx XML example for a simple line with stop points.",
            top_k=6,
            min_score=0.0,
            graph_rag_enabled=True,
            scope=["NeTEx"],
        )

        self.assertEqual(trace["graphConceptCap"], 16)
        self.assertEqual(trace["graphCandidateCap"], 8)

    @override_settings(
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://localhost:7200",
        GRAPHDB_REPOSITORY="napcore-helpdesk",
        GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=6,
        RETRIEVAL_DIVERSITY_ENABLED=False,
    )
    @patch("helpdesk.services.retrieval_gateway.retrieve_concept_definitions", return_value=[])
    @patch("helpdesk.services.retrieval_gateway.retrieve_concept_examples_with_fallback", return_value=[])
    @patch("helpdesk.services.retrieval_gateway._postgres_hybrid_candidates")
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion_with_distance")
    @patch("helpdesk.services.retrieval_gateway.get_concept_canonical_terms")
    @patch("helpdesk.services.retrieval_gateway.extract_graph_concepts")
    def test_graph_candidate_ranking_keeps_specific_example_before_cap(
        self,
        extract_graph_concepts_mock,
        get_concept_canonical_terms_mock,
        expand_mock,
        postgres_candidates_mock,
        _examples_mock,
        _definitions_mock,
    ):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        postgres_candidates_mock.return_value = SourceChunk.objects.none()
        expand_mock.return_value = {"netex:Line": 0}
        get_concept_canonical_terms_mock.return_value = ["simple line"]

        def extract_graph_concepts_side_effect(text: str, **_kwargs) -> set[str]:
            return {"netex:Line"} if "line" in text.lower() else set()

        extract_graph_concepts_mock.side_effect = extract_graph_concepts_side_effect

        for idx in range(8):
            generic_text = f"Line example structure {idx} with network and route references."
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx",
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
            repository_url="https://github.com/TransmodelEcosystem/NeTEx",
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

    @override_settings(
        GRAPHDB_ENABLED=True,
        GRAPHDB_SPARQL_ENDPOINT="http://localhost:7200",
        GRAPHDB_REPOSITORY="napcore-helpdesk",
        TRANSMODEL_HTML_BASE_URL="https://helpdesk.example/transmodel",
    )
    @patch("helpdesk.services.retrieval_gateway.retrieve_concept_definitions")
    @patch("helpdesk.services.retrieval_gateway.retrieve_concept_examples_with_fallback", return_value=[])
    @patch("helpdesk.services.retrieval_gateway._postgres_hybrid_candidates")
    @patch("helpdesk.services.retrieval_gateway.query_graphdb_concept_expansion_with_distance", return_value={})
    @patch("helpdesk.services.retrieval_gateway.get_concept_canonical_terms", return_value=[])
    @patch("helpdesk.services.retrieval_gateway.extract_graph_concepts", return_value={"transmodel:STOP_PLACE"})
    def test_transmodel_definition_keeps_its_class_page_link(
        self,
        _extract_mock,
        _canonical_mock,
        _expand_mock,
        postgres_candidates_mock,
        _examples_mock,
        definitions_mock,
    ):
        """The candidate built from a definition chunk carries its sourceUrl through to the results (#151)."""
        from helpdesk.models import SourceChunk
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        postgres_candidates_mock.return_value = SourceChunk.objects.none()
        definitions_mock.return_value = [
            {
                "concept": "https://transmodel-cen.eu/6.2/STOP_PLACE",
                "type": "http://www.w3.org/2002/07/owl#Class",
                "definition": "A place comprising one or more locations where vehicles may stop.",
                "prefLabel": "STOP PLACE",
                "altLabels": [],
            }
        ]

        chunks, _trace = retrieve_chunks_with_trace(
            question="What is a stop place in Transmodel?",
            top_k=6,
            min_score=0.0,
            graph_rag_enabled=True,
        )

        (definition,) = [c for c in chunks if c.get("sourcePath") == "docs/ontology/standards/transmodel.ttl#STOP_PLACE"]
        self.assertEqual(
            definition["sourceUrl"],
            "https://helpdesk.example/transmodel/index.htm?guid=06B01244-7E43-4925-8610-0B0B61508E7D",
        )

    @patch("helpdesk.services.retrieval_gateway.extract_graph_concepts")
    def test_graph_score_boosts_exact_example_path_on_direct_concept_hit(self, extract_graph_concepts_mock):
        from helpdesk.services.retrieval_gateway import _graph_score_adjustment

        extract_graph_concepts_mock.return_value = {"netex:Line"}

        adjustment, graph_hit, matching_concepts = _graph_score_adjustment(
            graph_enabled=True,
            question_concepts={"netex:Line"},
            expanded_concepts={"netex:Line"},
            chunk_text="Simple line XML example",
            source_path="examples/functions/line/NeTEx_01_simple_line.xml",
            label="NeTEx simple line",
            heading="",
            hinted_doc_types={"example"},
        )

        self.assertTrue(graph_hit)
        self.assertEqual(matching_concepts, {"netex:Line"})
        self.assertGreaterEqual(adjustment, 0.20)

    def test_cap_gives_every_hop_level_a_share_instead_of_one_level_crowding_out_the_rest(self):
        """Regression test: investigating a weak "line and journey" production
        answer found a plain alphabetical sort over the whole expanded set let
        netex:Journey's hop-1 neighbors (dozens of them, via subClassOf
        fan-out) consume the entire cap, so netex:Line -- reached one hop
        further out, via netex:ServiceJourney's lineRef -- never survived
        truncation. Round-robin by hop level fixes that: every level present
        gets a share of the budget, so the farther, still-relevant concept is
        no longer automatically excluded just because a nearer level happens
        to have more members.

        Known residual gap, not fixed by this: round-robin only orders
        between hop levels. Within one level, a relevant concept can still
        lose a tiebreak to same-level siblings that merely sort earlier (here,
        netex:ServiceJourney itself can still be excluded if its own hop-1
        level has many other members alphabetically ahead of it) -- that
        needs ranking by relation type, not hop distance, which this function
        does not have the information to do.
        """
        from helpdesk.services.retrieval_gateway import _cap_expanded_concepts

        question_concepts = {"netex:Journey"}
        expanded_concepts = {
            "netex:Journey",
            "netex:AbstractGroupMember",  # hop 1, alphabetically before Line
            "netex:AcceptedDriverPermit",  # hop 1, alphabetically before Line
            "netex:Access",  # hop 1, alphabetically before Line
            "netex:ServiceJourney",  # hop 1
            "netex:Line",  # hop 2, via ServiceJourney's lineRef
        }
        concept_distances = {
            "netex:Journey": 0,
            "netex:AbstractGroupMember": 1,
            "netex:AcceptedDriverPermit": 1,
            "netex:Access": 1,
            "netex:ServiceJourney": 1,
            "netex:Line": 2,
        }

        capped = _cap_expanded_concepts(
            question_concepts=question_concepts,
            expanded_concepts=expanded_concepts,
            max_concepts=3,
            concept_distances=concept_distances,
        )

        # A plain alphabetical sort over the whole set would pick Journey (seed) +
        # the 2 alphabetically-first hop-1 concepts, excluding Line entirely.
        self.assertIn("netex:Line", capped)

    def test_cap_without_hop_separation_would_exclude_the_farther_concept(self):
        """Documents the failure mode the round-robin fix replaces: sorting
        the same scenario by distance alone (no per-level budget share) still
        lets a larger hop-1 bucket exhaust the cap before hop 2 is reached."""
        distances = {
            "netex:AbstractGroupMember": 1,
            "netex:AcceptedDriverPermit": 1,
            "netex:Access": 1,
            "netex:ServiceJourney": 1,
            "netex:Line": 2,
        }
        non_seeds = ["netex:AbstractGroupMember", "netex:AcceptedDriverPermit", "netex:Access", "netex:ServiceJourney", "netex:Line"]

        prioritized = sorted(non_seeds, key=lambda c: (distances[c], c))

        self.assertNotIn("netex:Line", prioritized[:2])  # excluded by a distance-only sort at this cap

    def test_cap_without_distances_falls_back_to_alphabetical(self):
        """No concept_distances means every non-seed concept is treated as
        equally near (the pre-existing behavior, preserved for any caller that
        doesn't have a distance ranking to give)."""
        from helpdesk.services.retrieval_gateway import _cap_expanded_concepts

        capped = _cap_expanded_concepts(
            question_concepts={"netex:Journey"},
            expanded_concepts={"netex:Journey", "netex:Access", "netex:Line"},
            max_concepts=2,
        )

        self.assertEqual(capped, {"netex:Journey", "netex:Access"})


class HybridCandidateCutoffTests(TestCase):
    """The hybrid query ranks text only for rows at or above the limit-th vector
    similarity. Its result must equal ranking every row, ties at the cutoff included."""

    @staticmethod
    def _vector(similarity: float) -> list[float]:
        # Cosine similarity to the unit query vector e0 is exactly `similarity`.
        vector = [0.0] * 1536
        vector[0] = similarity
        vector[1] = (1.0 - similarity * similarity) ** 0.5
        return vector

    def setUp(self):
        from helpdesk.models import SourceChunk

        def chunk(index: int, similarity: float, text: str) -> None:
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx",
                commit_sha="abc",
                source_path=f"examples/chunk_{index}.xml",
                chunk_id=f"cutoff-{index}",
                label=f"Chunk {index}",
                text=text,
                standards_scope=["NeTEx"],
                quality_score=0.5,
                doc_type="example",
                embedding_vector=self._vector(similarity),
            )

        index = 0
        for step in range(22):
            chunk(index, 0.99 - step * 0.01, f"Unrelated content {index}.")
            index += 1
        # Eight rows share the similarity at the 25-row cutoff; their order, and which
        # three of them make the cut, depends on the lexical rank alone.
        tie_texts = [
            "Stop place.",
            "A stop place with quays and a stop place entrance.",
            "Nothing relevant here.",
            "Quays of a stop place.",
            "Stop place, quays, stop place, quays.",
            "Something else.",
            "Place.",
            "Stop.",
        ]
        for text in tie_texts:
            chunk(index, 0.5, text)
            index += 1
        for _ in range(10):
            chunk(index, 0.1, "Stop place with quays far away in vector space.")
            index += 1

    def test_cutoff_keeps_the_same_rows_and_order_as_ranking_every_row(self):
        from django.contrib.postgres.search import SearchQuery, SearchRank
        from django.db import connection, models

        from helpdesk.models import SourceChunk
        from helpdesk.services import retrieval_gateway

        if connection.vendor != "postgresql" or not retrieval_gateway.HAS_NATIVE_PGVECTOR:
            self.skipTest("needs PostgreSQL with pgvector")

        question = "stop place with quays"
        query_vector = self._vector(1.0)
        top_k = 5  # limit = max(25, top_k * 5) = 25, inside the tie group

        full = list(
            SourceChunk.objects.annotate(
                lexical_rank=SearchRank(retrieval_gateway._search_vector(), SearchQuery(question)),
                vector_distance=retrieval_gateway.CosineDistance("embedding_vector", query_vector),
            )
            .annotate(vector_similarity=1.0 - models.F("vector_distance"))
            .order_by("-vector_similarity", "-lexical_rank", "id")[:25]
        )
        result = list(
            retrieval_gateway._postgres_hybrid_candidates(
                question=question, query_embedding=query_vector, top_k=top_k
            )
        )

        self.assertEqual(
            [(row.chunk_id, row.lexical_rank) for row in result],
            [(row.chunk_id, row.lexical_rank) for row in full],
        )
        # Three of the eight tied rows are kept, chosen by lexical rank.
        tied = [row for row in result if abs(row.vector_similarity - 0.5) < 1e-9]
        self.assertEqual(len(tied), 3)
        self.assertGreater(tied[0].lexical_rank, 0.0)


class SimilarityRankingSwitchTests(TestCase):
    """With semantic vectors, similarity decides the ranking; with hash vectors the
    quality-based ranking stays as it was."""

    @staticmethod
    def _vector(similarity: float) -> list[float]:
        vector = [0.0] * 1536
        vector[0] = similarity
        vector[1] = (1.0 - similarity * similarity) ** 0.5
        return vector

    def setUp(self):
        from helpdesk.models import SourceChunk

        text = "SIRI messages refer to NeTEx objects such as lines and stop points."
        for chunk_id, doc_type, quality, similarity, path in (
            ("example-1", "example", 0.84, 0.80, "examples/siri_request.xml"),
            ("readme-1", "readme", 0.73, 0.95, "README.md"),
        ):
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/SIRI",
                commit_sha="abc",
                source_path=path,
                chunk_id=chunk_id,
                label=chunk_id,
                text=text,
                standards_scope=["SIRI"],
                quality_score=quality,
                doc_type=doc_type,
                embedding_vector=self._vector(similarity),
            )

    def _ranked_ids(self):
        from helpdesk.services import retrieval_gateway

        with patch.object(retrieval_gateway, "build_text_embedding", return_value=self._vector(1.0)):
            chunks, _trace = retrieval_gateway.retrieve_chunks_with_trace(
                question="How does SIRI use NeTEx?", top_k=2, min_score=0.0, scope=["SIRI"], graph_rag_enabled=False
            )
        return [chunk["chunkId"] for chunk in chunks]

    def test_hash_keeps_the_quality_based_ranking(self):
        self.assertEqual(self._ranked_ids()[0], "example-1")

    @override_settings(EMBEDDING_BACKEND="semantic")
    def test_semantic_ranks_the_closer_chunk_first(self):
        self.assertEqual(self._ranked_ids()[0], "readme-1")


class LexicalRecallTests(TestCase):
    """With semantic vectors, chunks holding a question's rare term join the vector-ranked pool (prod
    2026-11-05: "Does SIRI define roadworks?" never reached the DATEX II RoadWorks definitions)."""

    def setUp(self):
        from helpdesk.models import SourceChunk

        def chunk(name: str, text: str) -> None:
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/SIRI",
                commit_sha="abc",
                source_path=f"xsd/{name}.xsd",
                chunk_id=f"recall-{name}",
                label=name,
                text=text,
                standards_scope=["SIRI"],
                quality_score=0.8,
                doc_type="schema",
                embedding_vector=[0.0] * 1536,
            )

        chunk("datex", "RoadWorks: highway maintenance, repair and construction works on a road.")
        for index in range(3):
            chunk(f"general_{index}", f"SIRI defines the service delivery {index}.")

    def test_standard_identity_concepts(self):
        from helpdesk.services.retrieval_gateway import _is_standard_identity_concept

        self.assertTrue(_is_standard_identity_concept("siri:Siri"))
        self.assertTrue(_is_standard_identity_concept("opra:Opra"))
        self.assertFalse(_is_standard_identity_concept("netex:Parking"))
        self.assertFalse(_is_standard_identity_concept("transmodel:fare"))

    def test_rare_terms_and_the_chunks_that_hold_them(self):
        from django.db import connection

        from helpdesk.services import retrieval_gateway

        if connection.vendor != "postgresql":
            self.skipTest("text search needs PostgreSQL")
        with patch.object(retrieval_gateway, "RARE_TERM_MAX_CHUNKS", 2):
            rare = retrieval_gateway.question_rare_lexemes("Does SIRI define roadworks?", ["SIRI"])
            recalled = retrieval_gateway._lexical_recall_candidates("Does SIRI define roadworks?", 8, ["SIRI"])
        self.assertEqual(rare, ["roadwork"])  # "siri" and "defin" are in every chunk
        self.assertEqual([chunk.source_path for chunk in recalled], ["xsd/datex.xsd"])
        self.assertGreater(recalled[0].lexical_rank, 0)

    def test_no_rare_term_recalls_nothing(self):
        from helpdesk.services import retrieval_gateway

        self.assertEqual(retrieval_gateway._lexical_recall_candidates("What is SIRI?", 8, ["SIRI"], rare=[]), [])


class NamedExampleTests(TestCase):
    """An example asked for by type name is added after the best evidence (Turtle example chunks)."""

    REPO = "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP"

    def _chunk(self, path: str, chunk_id: str, heading: str, doc_type: str = "example", scope=None):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding

        text = f"<urn:{chunk_id}> a {heading.split(',')[0]} ."
        return SourceChunk.objects.create(
            repository_url=self.REPO,
            commit_sha="abc",
            source_path=path,
            chunk_id=chunk_id,
            label=path,
            heading=heading,
            text=text,
            standards_scope=scope or ["mobilityDCAT-AP"],
            doc_type=doc_type,
            embedding_vector=build_text_embedding(text),
        )

    def test_name_words_split_type_names(self):
        from helpdesk.services.retrieval_gateway import _name_words

        self.assertEqual(_name_words("dcat:CatalogRecord"), ["catalog", "record"])
        self.assertEqual(_name_words("mobilitydcatap:MobilityDataStandard"), ["mobility", "data", "standard"])
        self.assertEqual(_name_words("http://spec.tn-its.eu/owl/tnits-owl#RoadFeatureDataset"), ["road", "feature", "dataset"])

    def test_word_matches_spelling_variants_and_plurals_only_for_longer_words(self):
        from helpdesk.services.retrieval_gateway import _word_matches

        self.assertTrue(_word_matches("catalogue", "catalog"))
        self.assertTrue(_word_matches("records", "record"))
        self.assertTrue(_word_matches("record", "record"))
        self.assertFalse(_word_matches("data", "dataset"))
        self.assertFalse(_word_matches("map", "mapping"))

    def test_most_specific_type_wins_one_chunk_per_file(self):
        from helpdesk.services.retrieval_gateway import _named_example_candidates

        self._chunk("src/examples/example-complete.ttl", "c-catalog", "dcat:Catalog")
        self._chunk("src/examples/example-complete.ttl", "c-record", "dcat:CatalogRecord")
        self._chunk("src/examples/example-complete.ttl", "c-record-2", "dcat:CatalogRecord, foaf:Agent")
        self._chunk("src/examples/example-minimum.ttl", "m-record", "dcat:CatalogRecord")
        self._chunk("src/examples/example-minimum.ttl", "m-dataset", "dcat:Dataset")
        found = _named_example_candidates(
            "Can you show an example of a mobilityDCAT-AP catalogue record?", ["mobilityDCAT-AP"], score=0.9
        )
        self.assertEqual([c["chunkId"] for c in found], ["c-record", "m-record"])
        self.assertTrue(all(c["score"] == 0.9 for c in found))

    def test_nothing_without_a_named_type_scope_or_example_chunk(self):
        from helpdesk.services.retrieval_gateway import _named_example_candidates

        self._chunk("src/examples/example-complete.ttl", "c-record", "dcat:CatalogRecord")
        self._chunk("src/index.html", "spec", "Class catalogue record", doc_type="guide")
        self._chunk("other/example.ttl", "other", "dcat:CatalogRecord", scope=["TN-ITS"])
        question = "Can you show an example of a mobilityDCAT-AP catalogue record?"
        self.assertEqual(_named_example_candidates("Show an example of a mobilityDCAT-AP dataset.", ["mobilityDCAT-AP"], 0.9), [])
        self.assertEqual(_named_example_candidates(question, None, 0.9), [])
        self.assertEqual([c["chunkId"] for c in _named_example_candidates(question, ["mobilityDCAT-AP"], 0.9)], ["c-record"])

    def test_retrieval_adds_the_example_after_the_top_result(self):
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.models import SourceChunk
        from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

        for idx in range(4):
            text = f"Class catalogue record. A description of a dataset's entry in the catalogue. Part {idx}."
            SourceChunk.objects.create(
                repository_url=self.REPO, commit_sha="abc", source_path=f"src/tables/class-{idx}.html",
                chunk_id=f"spec-{idx}", label="Class catalogue record", heading="Class catalogue record",
                text=text, standards_scope=["mobilityDCAT-AP"], doc_type="guide", quality_score=0.92,
                embedding_vector=build_text_embedding(text),
            )
        self._chunk("src/examples/example-complete.ttl", "c-record", "dcat:CatalogRecord")
        chunks, _ = retrieve_chunks_with_trace(
            question="Can you show an example of a mobilityDCAT-AP catalogue record?",
            top_k=4, min_score=0.0, scope=["mobilityDCAT-AP"], english_question=None,
        )
        self.assertEqual(chunks[1]["chunkId"], "c-record")
        self.assertEqual(len(chunks), 4)


class ScopeCoverageTests(SimpleTestCase):
    @staticmethod
    def _chunk(cid, standard):
        return {"chunkId": cid, "sourcePath": cid, "standardsScope": [standard], "score": 1.0}

    def test_a_scope_crowded_out_gets_its_two_best_chunks_after_the_top_one(self):
        from unittest.mock import patch

        from helpdesk.services import retrieval_gateway as gateway

        crowded = [self._chunk(f"inspire-{i}", "INSPIRE") for i in range(6)]
        alone = [self._chunk("art_2", "EU legislation"), self._chunk("art_1", "EU legislation")]
        arguments = dict(top_k=6, min_score=0.45, scope=["INSPIRE", "EU legislation"], graph_rag_enabled=True, min_results=1)
        with patch.object(gateway, "_retrieve_chunks_once", return_value=(alone, {})) as once:
            chunks, trace = gateway._with_scope_coverage("What is INSPIRE?", crowded, {}, arguments)
        once.assert_called_once()
        self.assertEqual(once.call_args.kwargs["scope"], ["EU legislation"])
        self.assertEqual([c["chunkId"] for c in chunks], ["inspire-0", "art_2", "art_1", "inspire-1", "inspire-2", "inspire-3"])
        self.assertEqual([a["standard"] for a in trace["scopeCoverageAdded"]], ["EU legislation", "EU legislation"])

    def test_nothing_happens_when_every_scope_is_present_or_only_one_is_searched(self):
        from unittest.mock import patch

        from helpdesk.services import retrieval_gateway as gateway

        mixed = [self._chunk("a", "SIRI"), self._chunk("b", "NeTEx")]
        with patch.object(gateway, "_retrieve_chunks_once") as once:
            self.assertEqual(gateway._with_scope_coverage("q", mixed, {}, dict(top_k=6, scope=["SIRI", "NeTEx"]))[0], mixed)
            self.assertEqual(gateway._with_scope_coverage("q", mixed, {}, dict(top_k=6, scope=["SIRI"]))[0], mixed)
        once.assert_not_called()
