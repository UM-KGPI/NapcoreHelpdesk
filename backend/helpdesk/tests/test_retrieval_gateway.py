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


class RareTermCountQueryTests(TestCase):
    def test_counting_is_unordered_so_the_gin_index_answers_it(self):
        # With the default order (quality_score) PostgreSQL walked that index and built every chunk's
        # tsvector for a common term: 3.6 s instead of 9 ms for "place" in NeTEx (local 2026-11-08).
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from helpdesk.services import retrieval_gateway

        if connection.vendor != "postgresql":
            self.skipTest("text search needs PostgreSQL")
        with CaptureQueriesContext(connection) as queries:
            retrieval_gateway._rare_lexemes(["place", "quay"], ["NeTEx"])
        counts = [q["sql"] for q in queries.captured_queries if "to_tsquery" in q["sql"]]
        self.assertEqual(len(counts), 2)
        self.assertTrue(all("ORDER BY" not in sql for sql in counts))


class VectorIndexSearchTests(TestCase):
    """The nearest rows come through the ivfflat index (ORDER BY vector <=> query), and the result is the same
    as the exact scan's (docs/plans/2026-11-09-example-question-latency.md, P1)."""

    @staticmethod
    def _vector(first: float) -> list[float]:
        vector = [0.0] * 1536
        vector[0], vector[1] = first, (1.0 - first * first) ** 0.5
        return vector

    def setUp(self):
        from django.db import connection

        from helpdesk.models import SourceChunk
        from helpdesk.services import retrieval_gateway

        if connection.vendor != "postgresql" or not retrieval_gateway.HAS_NATIVE_PGVECTOR:
            self.skipTest("needs PostgreSQL with pgvector")
        for index in range(40):
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc", source_path=f"x/{index}.xsd",
                chunk_id=f"v-{index}", text=f"stop place {index}", standards_scope=["NeTEx"], embedding_vector=self._vector(index / 40),
            )

    def _result(self, **flags):
        from helpdesk.services import retrieval_gateway

        with override_settings(**flags):
            return [c.chunk_id for c in retrieval_gateway._postgres_hybrid_candidates(question="stop place", query_embedding=self._vector(1.0), top_k=5)]

    def test_same_result_as_the_exact_scan(self):
        exact = self._result(VECTOR_INDEX_SEARCH=False)
        self.assertEqual(len(exact), 25)
        self.assertEqual(self._result(VECTOR_INDEX_SEARCH=True), exact)

    def test_nearest_rows_are_ordered_by_the_raw_distance_operator(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            self._result(VECTOR_INDEX_SEARCH=True)
        sql = [q["sql"] for q in queries.captured_queries]
        self.assertTrue(any("ivfflat.iterative_scan" in s for s in sql))
        nearest = next(s for s in sql if "ORDER BY" in s and "<=>" in s and "LIMIT 50" in s)
        self.assertNotIn("1.0 -", nearest.split("ORDER BY", 1)[1])

    def test_a_database_error_falls_back_to_the_exact_scan(self):
        from django.db import DatabaseError

        from helpdesk.models import SourceChunk
        from helpdesk.services import retrieval_gateway

        with patch.object(retrieval_gateway.connection, "cursor", side_effect=DatabaseError("no iterative scans")):
            self.assertIsNone(retrieval_gateway._nearest_ids_by_index(SourceChunk.objects.all(), self._vector(1.0), 25))

    def _nearest_sql(self, **flags) -> str:
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            self._result(VECTOR_INDEX_SEARCH=True, **flags)
        return " | ".join(q["sql"] for q in queries.captured_queries)

    def test_whole_column_and_no_seqscan_setting_when_the_filled_numbers_setting_is_off(self):
        sql = self._nearest_sql()
        self.assertNotIn("subvector", sql)
        self.assertNotIn("enable_seqscan", sql)

    def test_filled_numbers_search_gives_the_exact_result(self):
        exact = self._result(VECTOR_INDEX_SEARCH=False)
        self.assertEqual(self._result(VECTOR_INDEX_SEARCH=True, VECTOR_INDEX_DIMENSIONS=384), exact)
        self.assertEqual(
            self._result(VECTOR_INDEX_SEARCH=True, VECTOR_INDEX_DIMENSIONS=384, VECTOR_INDEX_HALF_PRECISION=True), exact
        )

    def test_filled_numbers_query_is_written_as_the_index_expression(self):
        sql = self._nearest_sql(VECTOR_INDEX_DIMENSIONS=384)
        self.assertIn("subvector(embedding_vector, 1, 384)::vector(384) <=>", sql)
        self.assertIn("enable_seqscan", sql)
        half = self._nearest_sql(VECTOR_INDEX_DIMENSIONS=384, VECTOR_INDEX_HALF_PRECISION=True)
        self.assertIn("subvector(embedding_vector, 1, 384)::halfvec(384) <=>", half)

    def test_filled_numbers_setting_outside_the_column_is_off(self):
        from helpdesk.services import retrieval_gateway

        for value, expected in ((0, 0), (384, 384), (1536, 0), (-1, 0), ("x", 0), (None, 0)):
            with override_settings(VECTOR_INDEX_DIMENSIONS=value):
                self.assertEqual(retrieval_gateway._vector_index_dimensions(), expected, value)


@override_settings(GRAPH_ALIAS_MAX_CHUNKS=3, GRAPH_CANDIDATE_SCAN_LIMIT=400)
class GraphCandidateAliasBoundTests(TestCase):
    """Graph candidates skip aliases found in too many paths/labels (2026-11-09: "fare" matched 10,078 chunks)."""

    def setUp(self):
        from helpdesk.services import retrieval_gateway

        retrieval_gateway._ALIAS_MATCH_CACHE.clear()

    def _chunk(self, path: str, chunk_id: str, scope=("NeTEx",), quality: float = 0.9):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding

        return SourceChunk.objects.create(
            repository_url="https://github.com/TransmodelEcosystem/NeTEx",
            commit_sha="abc",
            source_path=path,
            chunk_id=chunk_id,
            label=path.rsplit("/", 1)[-1],
            # Text without the aliases: only the path/label (fast) search finds these chunks.
            text="An example passage.",
            standards_scope=list(scope),
            quality_score=quality,
            doc_type="example",
            embedding_vector=build_text_embedding("An example passage."),
        )

    def _candidates(self, aliases: dict, scope=("NeTEx",), question="Show me a fare zone example."):
        from helpdesk.services import retrieval_gateway

        with patch.object(retrieval_gateway, "GRAPH_CONCEPT_ALIASES", aliases):
            return retrieval_gateway._graph_concept_candidates(
                expanded_concepts=set(aliases), top_k=6, max_candidates=8, scope=list(scope), question=question
            )

    def test_an_over_frequent_alias_is_skipped_and_a_specific_one_kept(self):
        for idx in range(5):
            self._chunk(f"examples/fares/fare_product_{idx}.xml", f"fare-{idx}")
        zone = self._chunk("examples/fares/zonal_farezone.xml", "farezone")

        paths = [c.source_path for c in self._candidates({"netex:FareZone": {"farezone"}, "transmodel:fare": {"fare"}})]

        self.assertEqual(paths, [zone.source_path])

    def test_when_every_alias_is_over_frequent_the_longest_still_finds_candidates(self):
        for idx in range(5):
            self._chunk(f"examples/stops/stop_place_{idx}.xml", f"stop-{idx}")

        found = self._candidates({"netex:StopPlace": {"stop_place"}, "transmodel:stop": {"stop"}}, question="stop place")

        self.assertTrue(found)
        self.assertTrue(all("stop_place" in c.source_path for c in found))

    @override_settings(GRAPH_ALIAS_MAX_CHUNKS=0)
    def test_zero_turns_the_bound_off(self):
        for idx in range(5):
            self._chunk(f"examples/fares/fare_product_{idx}.xml", f"fare-{idx}")

        self.assertEqual(len(self._candidates({"transmodel:fare": {"fare"}})), 5)

    @override_settings(GRAPH_ALIAS_MAX_CHUNKS=0, GRAPH_CANDIDATE_SCAN_LIMIT=2)
    def test_the_scan_limit_ranks_only_the_highest_quality_rows(self):
        for idx in range(5):
            self._chunk(f"examples/fares/fare_product_{idx}.xml", f"fare-{idx}", quality=0.5 + idx / 10)

        ids = sorted(c.chunk_id for c in self._candidates({"transmodel:fare": {"fare"}}))

        self.assertEqual(ids, ["fare-3", "fare-4"])

    @override_settings(GRAPH_ALIAS_MAX_CHUNKS=0, GRAPH_CANDIDATE_SCAN_LIMIT=2)
    def test_the_path_search_never_asks_the_database_for_sorted_top_rows(self):
        # ORDER BY quality_score LIMIT made prod's planner walk the quality index over the whole table (3.3 s)
        # instead of the trigram indexes; the top rows are picked in Python.
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        for idx in range(5):
            self._chunk(f"examples/fares/fare_product_{idx}.xml", f"fare-{idx}", quality=0.5 + idx / 10)

        with CaptureQueriesContext(connection) as queries:
            self._candidates({"transmodel:fare": {"fare"}})

        path_searches = [
            q["sql"] for q in queries.captured_queries if 'UPPER("helpdesk_sourcechunk"."source_path"' in q["sql"]
        ]
        self.assertTrue(path_searches)
        self.assertFalse([sql for sql in path_searches if "ORDER BY" in sql and "LIMIT" in sql])

    def test_one_query_per_alias_and_none_once_cached(self):
        # All aliases OR-ed into one query made prod's planner scan the whole table (1.3 s).
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self._chunk("examples/fares/zonal_farezone.xml", "farezone")
        self._chunk("examples/fares/tariff_zone.xml", "tariffzone")
        aliases = {"netex:FareZone": {"farezone"}, "netex:TariffZone": {"tariff_zone"}}

        with CaptureQueriesContext(connection) as first:
            self._candidates(aliases)
        with CaptureQueriesContext(connection) as second:
            found = self._candidates(aliases)

        def alias_queries(captured):
            return [q["sql"] for q in captured if 'UPPER("helpdesk_sourcechunk"."label"' in q["sql"]]

        self.assertEqual(len(alias_queries(first.captured_queries)), 2)
        self.assertTrue(all(sql.count("LIKE") == 2 for sql in alias_queries(first.captured_queries)))
        self.assertFalse(alias_queries(second.captured_queries))
        self.assertEqual(sorted(c.chunk_id for c in found), ["farezone", "tariffzone"])

    @override_settings(GRAPH_ALIAS_MAX_CHUNKS=0, GRAPH_CANDIDATE_SCAN_LIMIT=10, GRAPH_CANDIDATES_PER_FILE=2)
    def test_one_large_high_quality_file_does_not_fill_the_candidates(self):
        from helpdesk.services import retrieval_gateway

        for idx in range(12):
            self._chunk("examples/stops/accessibility_station.xml", f"big-{idx}", quality=0.99)
        for name in ("two_quays", "simple_station"):
            self._chunk(f"examples/stops/{name}.xml", name, quality=0.5)

        with patch.object(retrieval_gateway, "_SCAN_ROWS_PER_FILE", 3):
            found = self._candidates({"netex:StopPlace": {"stops"}}, question="a stop place with two quays")

        files = [c.source_path for c in found]
        self.assertIn("examples/stops/two_quays.xml", files)
        self.assertIn("examples/stops/simple_station.xml", files)
        self.assertLessEqual(files.count("examples/stops/accessibility_station.xml"), 2)

    def test_the_frequency_is_counted_per_scope(self):
        from helpdesk.models import SourceChunk
        from helpdesk.services import retrieval_gateway

        for idx in range(5):
            self._chunk(f"examples/fares/fare_product_{idx}.xml", f"fare-{idx}", scope=("NeTEx",))
        self._chunk("examples/fares/fare_indicator.xml", "fare-opra", scope=("OpRa",))

        def too_frequent(scope):
            base = SourceChunk.objects.filter(retrieval_gateway._scope_query_filter(scope))
            return retrieval_gateway._alias_matches("fare", scope, base) is None

        self.assertTrue(too_frequent(["NeTEx"]))
        self.assertFalse(too_frequent(["OpRa"]))


class ElementCandidateCacheTests(TestCase):
    """Chunks showing an element the question names, looked up once per name (0.41 s per answer on prod)."""

    def setUp(self):
        from helpdesk.services import retrieval_gateway

        retrieval_gateway._ELEMENT_CANDIDATE_CACHE.clear()

    def _chunk(self, chunk_id: str, text: str, quality: float, doc_type: str = "example"):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding

        return SourceChunk.objects.create(
            repository_url="https://github.com/TransmodelEcosystem/NeTEx",
            commit_sha="abc",
            source_path=f"examples/{chunk_id}.xml",
            chunk_id=chunk_id,
            label=chunk_id,
            text=text,
            standards_scope=["NeTEx"],
            quality_score=quality,
            doc_type=doc_type,
            embedding_vector=build_text_embedding(text),
        )

    def test_highest_quality_chunks_showing_the_element_once_cached_without_a_tag_search(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from helpdesk.services import retrieval_gateway

        self._chunk("quay-low", '<Quay id="q1"/>', 0.5)
        self._chunk("quay-high", "<Quay>\n  <Name>A</Name>\n</Quay>", 0.9)
        self._chunk("quayref", '<QuayRef ref="q1"/>', 0.95)
        self._chunk("readme", "<Quay> in prose", 0.99, doc_type="readme")

        first = [c.chunk_id for c in retrieval_gateway._element_candidates(["Quay"])]
        with CaptureQueriesContext(connection) as queries:
            second = [c.chunk_id for c in retrieval_gateway._element_candidates(["Quay"])]

        self.assertEqual(first, ["quay-high", "quay-low"])
        self.assertEqual(second, first)
        self.assertEqual(len(queries.captured_queries), 1)  # rows by primary key only
        self.assertNotIn("LIKE", queries.captured_queries[0]["sql"])

    def test_a_chunk_removed_since_caching_is_skipped(self):
        from helpdesk.services import retrieval_gateway

        gone = self._chunk("quay-gone", "<Quay>gone</Quay>", 0.9)
        self._chunk("quay-kept", "<Quay>kept</Quay>", 0.8)
        retrieval_gateway._element_candidates(["Quay"])
        gone.delete()

        self.assertEqual([c.chunk_id for c in retrieval_gateway._element_candidates(["Quay"])], ["quay-kept"])


class ExampleNarrationEvidenceTests(TestCase):
    """The text next to a standard example is written from that example's own file (P7, 2026-11-09)."""

    def setUp(self):
        from helpdesk.services import retrieval_gateway

        retrieval_gateway._EXAMPLE_USE_CACHE.clear()

    def _chunk(self, path: str, chunk_id: str, text: str, quality: float = 0.8):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding

        return SourceChunk.objects.create(
            repository_url="https://github.com/TransmodelEcosystem/NeTEx",
            commit_sha="abc",
            source_path=path,
            chunk_id=chunk_id,
            label=path.rsplit("/", 1)[-1],
            text=text,
            standards_scope=["NeTEx"],
            quality_score=quality,
            doc_type="example",
            embedding_vector=build_text_embedding(text),
        )

    def test_examples_are_not_ordered_by_file_name(self):
        from helpdesk.services.retrieval_gateway import examples_using_elements

        self._chunk("examples/functions/DeckPlans-Example_train.xml", "deck", "<Quay id='d'/>", quality=0.9)
        self._chunk("examples/stops/BasicStopPlace-two-quays_example.xml", "two", "<Quay id='a'/>", quality=0.5)
        self._chunk("examples/stops/SimpleStation_quays.xml", "station", "<Quay id='s'/>", quality=0.5)

        preferred = examples_using_elements(["Quay"], prefer_path="examples/stops/BasicStopPlace-two-quays_example.xml")
        by_question = examples_using_elements(["Quay"], question="a station with two quays", limit=2)

        self.assertEqual(preferred[0]["chunkId"], "two")
        self.assertEqual([c["chunkId"] for c in by_question], ["two", "station"])

    def test_the_shown_example_chunk_is_the_one_holding_the_shown_object(self):
        from helpdesk.services.retrieval_gateway import shown_example_chunk

        path = "examples/stops/BasicStopPlace-two-quays_example.xml"
        self._chunk(path, "frame", "<SiteFrame id='f'><stopPlaces>", quality=0.9)
        self._chunk(path, "other", "<StopPlace id=\"xx:other\" version=\"1\">", quality=0.9)
        self._chunk(path, "shown", "<StopPlace id=\"xx:station_765\" version=\"1\"><quays>", quality=0.5)
        example = {
            "origin": "standard",
            "sourcePath": path,
            "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
            "xml": '<SiteFrame id="f"><stopPlaces><StopPlace id="xx:station_765" version="1"/></stopPlaces></SiteFrame>',
        }

        self.assertEqual(shown_example_chunk(example)["chunkId"], "shown")
        self.assertIsNone(shown_example_chunk({**example, "origin": "generated"}))


class ComposeExampleEvidenceTests(SimpleTestCase):
    def test_the_shown_examples_chunk_comes_first_even_when_retrieval_missed_it(self):
        from helpdesk.api import views

        own = {"chunkId": "own", "sourcePath": "examples/stops/BasicStopPlace-two-quays_example.xml"}
        deck = {"chunkId": "deck", "sourcePath": "examples/functions/DeckPlans-Example_train.xml"}
        retrieved = [{"chunkId": f"r{i}", "sourcePath": f"examples/r{i}.xml"} for i in range(6)]
        example = {"origin": "standard", "valid": True, "sourcePath": own["sourcePath"], "xml": "<SiteFrame><stopPlaces><StopPlace/>"}

        with patch("helpdesk.services.retrieval_gateway.examples_using_elements", return_value=[deck]), patch(
            "helpdesk.services.retrieval_gateway.shown_example_chunk", return_value=own
        ), patch.object(views, "other_question", return_value=False):
            composed = views._compose_example_evidence("Show a stop place with two quays", None, example, retrieved, retrieved, 6)

        self.assertEqual([c["chunkId"] for c in composed][:2], ["own", "deck"])
        self.assertEqual(len(composed), 6)


class PreselectByFileTests(SimpleTestCase):
    """_preselect_base_ids_by_file: files by their best piece's similarity, up to K pieces each, in a budget of
    rows or files; the lexical reserve keeps the same per-file limit."""

    @staticmethod
    def _pool(spec):
        """spec: (id, path, similarity[, lexical rank]) in any order."""
        from types import SimpleNamespace

        return [
            SimpleNamespace(id=row[0], source_path=row[1], vector_similarity=row[2],
                            lexical_rank=row[3] if len(row) > 3 else 0.0, quality_score=0.5)
            for row in spec
        ]

    def _select(self, pool, budget, per_file, count_files, reserve=0):
        from helpdesk.services.retrieval_gateway import _preselect_base_ids_by_file

        return _preselect_base_ids_by_file(pool, budget, reserve, per_file, count_files)

    def test_files_are_chosen_by_their_best_piece(self):
        # a.xml has the two most similar pieces; by row both slots would go to it.
        pool = self._pool([(1, "a.xml", 0.95), (2, "a.xml", 0.94), (3, "b.xsd", 0.90), (4, "c.md", 0.80),
                           (5, "b.xsd", 0.70)])
        self.assertEqual(self._select(pool, budget=2, per_file=1, count_files=False), {1, 3})
        self.assertEqual(self._select(pool, budget=2, per_file=1, count_files=True), {1, 3})

    def test_at_most_k_pieces_of_a_file(self):
        pool = self._pool([(i, "a.xml", 0.99 - i / 100) for i in range(1, 7)] + [(10, "b.xsd", 0.5)])
        self.assertEqual(self._select(pool, budget=4, per_file=2, count_files=False), {1, 2, 10})
        self.assertEqual(self._select(pool, budget=4, per_file=2, count_files=True), {1, 2, 10})

    def test_budget_in_rows(self):
        pool = self._pool([(i * 10 + j, f"f{i}.xml", 0.99 - i / 100 - j / 1000) for i in range(6) for j in range(3)])
        selected = self._select(pool, budget=5, per_file=2, count_files=False)
        self.assertEqual(selected, {0, 1, 10, 11, 20})  # the third file gets the one row left

    def test_budget_in_files(self):
        pool = self._pool([(i * 10 + j, f"f{i}.xml", 0.99 - i / 100 - j / 1000) for i in range(6) for j in range(3)])
        selected = self._select(pool, budget=3, per_file=2, count_files=True)
        self.assertEqual(selected, {0, 1, 10, 11, 20, 21})

    def test_a_file_with_fewer_than_k_pieces(self):
        pool = self._pool([(1, "a.xml", 0.9), (2, "b.xsd", 0.8), (3, "b.xsd", 0.7), (4, "c.md", 0.6)])
        self.assertEqual(self._select(pool, budget=3, per_file=3, count_files=True), {1, 2, 3, 4})
        self.assertEqual(self._select(pool, budget=3, per_file=3, count_files=False), {1, 2, 3})

    def test_ties_are_broken_deterministically(self):
        # Same similarity: the better lexical rank first, then the lower id; the input order does not matter.
        spec = [(7, "x.xml", 0.8, 0.1), (3, "y.xml", 0.8, 0.1), (9, "z.xml", 0.8, 0.5)]
        for order in (spec, list(reversed(spec))):
            self.assertEqual(self._select(self._pool(order), budget=2, per_file=1, count_files=True), {9, 3})

    def test_lexical_reserve_keeps_the_per_file_limit(self):
        # 8 slots, a quarter (2) for lexical leaders: 6 files by similarity, then the best lexical rows of files
        # not chosen yet; a second piece of a chosen file is skipped with K=1.
        pool = self._pool([(i, f"f{i}.xml", 0.9 - i / 100, 0.0) for i in range(1, 9)]
                          + [(20, "f1.xml", 0.5, 1.0), (21, "g.xml", 0.4, 0.9), (22, "h.xml", 0.3, 0.8)])
        self.assertEqual(self._select(pool, budget=8, per_file=1, count_files=False, reserve=8),
                         {1, 2, 3, 4, 5, 6, 21, 22})

    def test_rows_without_a_path_are_files_of_their_own(self):
        pool = self._pool([(1, "", 0.9), (2, "", 0.8), (3, "a.xml", 0.7)])
        self.assertEqual(self._select(pool, budget=3, per_file=1, count_files=True), {1, 2, 3})


class PreselectSwitchTests(TestCase):
    """RETRIEVAL_PRESELECT_PIECES_PER_FILE: 0 keeps the preselection by row; the gateway's preselected
    candidates are then exactly _preselect_base_ids on the same pool."""

    def setUp(self):
        from helpdesk.models import SourceChunk
        from helpdesk.services.embeddings import build_text_embedding

        rows = [("big.xml", 0.95 - i / 100, 0.1) for i in range(12)]  # one file in 12 pieces, the most similar
        rows += [(f"other{i}.xsd", 0.80 - i / 100, 0.3 - i / 100) for i in range(8)]
        self.pool = []
        for idx, (path, similarity, lexical) in enumerate(rows):
            text = f"Stop place passage {idx}."
            chunk = SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc",
                source_path=path, chunk_id=f"pre-{idx}", label=f"pre-{idx}", text=text,
                standards_scope=["NeTEx"], quality_score=0.5, doc_type="schema",
                embedding_vector=build_text_embedding(text),
            )
            chunk.vector_similarity = similarity
            chunk.lexical_rank = lexical
            self.pool.append(chunk)

    def _preselected(self):
        from helpdesk.services import retrieval_gateway

        seen = {}

        def probe(stage, items):
            if stage == "preselected":
                seen["ids"] = {int(chunk.id) for chunk in items}

        with patch.object(retrieval_gateway, "_postgres_hybrid_candidates", return_value=list(self.pool)), \
                patch.object(retrieval_gateway, "_path_hint_candidates", return_value=[]), \
                retrieval_gateway.retrieval_probe(probe):
            retrieval_gateway.retrieve_chunks_with_trace(
                question="stop place", top_k=5, min_score=0.0, scope=["NeTEx"], graph_rag_enabled=False
            )
        return seen["ids"]

    @override_settings(RETRIEVAL_SCORING_CANDIDATE_CAP=12, RETRIEVAL_LEXICAL_PRESELECT_RESERVE=8,
                       RETRIEVAL_PRESELECT_PIECES_PER_FILE=0)
    def test_off_is_the_preselection_by_row(self):
        from helpdesk.services import retrieval_gateway

        ordered = sorted(self.pool, key=lambda c: (c.vector_similarity, c.lexical_rank, c.quality_score), reverse=True)
        expected = retrieval_gateway._preselect_base_ids(ordered, 12, 8)
        with patch.object(retrieval_gateway, "_preselect_base_ids_by_file") as by_file:
            self.assertEqual(self._preselected(), expected)
        by_file.assert_not_called()
        self.assertEqual(len({c.source_path for c in self.pool if c.id in expected}), 4)  # 9 pieces of big.xml

    @override_settings(RETRIEVAL_SCORING_CANDIDATE_CAP=12, RETRIEVAL_LEXICAL_PRESELECT_RESERVE=8,
                       RETRIEVAL_PRESELECT_PIECES_PER_FILE=1, RETRIEVAL_PRESELECT_BUDGET="rows")
    def test_on_counts_files(self):
        selected = self._preselected()
        self.assertEqual(len(selected), 9)  # every file once: 9 files in the pool, 12 slots
        self.assertEqual(len({c.source_path for c in self.pool if c.id in selected}), 9)


class PreselectRowRangeTests(PreselectSwitchTests):
    """RETRIEVAL_PRESELECT_ROW_RANGE: with the preselection by file, the vector score is scaled over the rows the
    preselection by row would keep, so a row scored in both gets the same score as by row."""

    def _scores(self):
        from helpdesk.services import retrieval_gateway

        seen = {}

        def probe(stage, items):
            if stage == "scored":
                seen["scores"] = {item["chunkId"]: item["_rankScore"] for item in items if isinstance(item, dict)}

        with patch.object(retrieval_gateway, "_postgres_hybrid_candidates", return_value=list(self.pool)), \
                patch.object(retrieval_gateway, "_path_hint_candidates", return_value=[]), \
                patch.object(retrieval_gateway, "_lexical_recall_candidates", return_value=[]), \
                patch.object(retrieval_gateway, "question_rare_lexemes", return_value=[]), \
                patch.object(retrieval_gateway, "build_text_embedding", return_value=[1.0] + [0.0] * 1535), \
                retrieval_gateway.retrieval_probe(probe):
            retrieval_gateway.retrieve_chunks_with_trace(
                question="stop place", top_k=5, min_score=0.0, scope=["NeTEx"], graph_rag_enabled=False
            )
        return seen["scores"]

    def _run(self, per_file, row_range):
        with override_settings(EMBEDDING_BACKEND="semantic", RETRIEVAL_SCORING_CANDIDATE_CAP=12,
                               RETRIEVAL_LEXICAL_PRESELECT_RESERVE=8, RETRIEVAL_PRESELECT_PIECES_PER_FILE=per_file,
                               RETRIEVAL_PRESELECT_BUDGET="rows", RETRIEVAL_PRESELECT_ROW_RANGE=row_range):
            return self._scores()

    def test_row_range_gives_the_scores_of_the_preselection_by_row(self):
        by_row = self._run(0, False)
        by_file_row_range = self._run(1, True)
        by_file = self._run(1, False)
        shared = set(by_row) & set(by_file_row_range)
        self.assertTrue(shared)
        for chunk_id in shared:
            self.assertAlmostEqual(by_row[chunk_id], by_file_row_range[chunk_id], places=9)
        # Without it the range is that of the rows scored: by file it reaches lower, and the shared rows move.
        self.assertTrue(any(abs(by_row[c] - by_file[c]) > 1e-6 for c in set(by_row) & set(by_file)))
        self.assertNotEqual(set(by_file_row_range), set(by_row))  # the rows scored are those chosen by file


def _stop_word_lexemes(aliases):
    """_alias_lexemes as PostgreSQL's English configuration answers for these aliases: "with" is a stop word."""
    return {alias: (() if alias in {"with", "is for"} else (alias.split()[0],)) for alias in aliases}


class NoBoostConceptKindsTests(SimpleTestCase):
    """RETRIEVAL_CONCEPT_NO_BOOST_MATCHES: which question concepts give no concept boost."""

    def _no_boost(self, aliases, question, kinds):
        from helpdesk.services import retrieval_gateway, semantic_graph

        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", aliases), \
                patch.object(retrieval_gateway, "_alias_lexemes", side_effect=_stop_word_lexemes):
            found = semantic_graph.extract_graph_concepts(question, word_variants=True)
            return found, retrieval_gateway.no_boost_question_concepts(question, found, frozenset(kinds))

    def test_a_concept_matched_only_on_a_stop_word_gives_no_boost(self):
        found, no_boost = self._no_boost(
            {"transmodel:with": {"with"}, "netex:Lane": {"lane"}}, "An accident with a closed lane", {"stop"}
        )
        self.assertEqual(found, {"transmodel:with", "netex:Lane"})
        self.assertEqual(no_boost, {"transmodel:with"})

    def test_a_concept_also_matched_on_a_distinctive_alias_keeps_it(self):
        _found, no_boost = self._no_boost({"transmodel:with": {"with", "lane"}}, "An accident with a closed lane", {"stop"})
        self.assertEqual(no_boost, set())

    def test_a_stop_phrase_of_several_words_is_a_stop_match(self):
        _found, no_boost = self._no_boost({"transmodel:isFor": {"is for"}}, "What is for sale?", {"stop"})
        self.assertEqual(no_boost, {"transmodel:isFor"})

    def test_a_label_reached_only_through_plurals_is_loose(self):
        aliases = {"transmodel:CLASS_ATTRIBUTE": {"class attribute"}}
        question = "Which classes and attributes carry the location?"
        self.assertEqual(self._no_boost(aliases, question, {"stop"})[1], set())
        self.assertEqual(self._no_boost(aliases, question, {"stop", "loose"})[1], {"transmodel:CLASS_ATTRIBUTE"})
        # The same label written as it is: not loose.
        self.assertEqual(self._no_boost(aliases, "Which class attribute is it?", {"stop", "loose"})[1], set())

    def test_without_postgresql_no_alias_is_known_as_a_stop_word(self):
        from helpdesk.services import retrieval_gateway, semantic_graph

        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", {"transmodel:with": {"with"}}), \
                patch.object(retrieval_gateway.connection, "vendor", "sqlite"):
            self.assertEqual(
                retrieval_gateway.no_boost_question_concepts("lane with", {"transmodel:with"}, frozenset({"stop"})), set()
            )

    def test_the_setting(self):
        from helpdesk.services.retrieval_gateway import concept_no_boost_kinds

        for value, expected in (("", set()), ("stop", {"stop"}), (" Stop , loose ", {"stop", "loose"}), ("stop,other", {"stop"})):
            with override_settings(RETRIEVAL_CONCEPT_NO_BOOST_MATCHES=value):
                self.assertEqual(concept_no_boost_kinds(), frozenset(expected))

    def test_alias_matches_are_reported_in_a_fixed_order(self):
        from helpdesk.services import semantic_graph

        aliases = {"netex:Lane": {"lane", "lanes"}, "transmodel:with": {"with"}}
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", aliases):
            first = semantic_graph.question_alias_matches("lanes with a lane", ["transmodel:with", "netex:Lane"])
            second = semantic_graph.question_alias_matches("lanes with a lane", ["netex:Lane", "transmodel:with"])
        self.assertEqual(list(first.items()), list(second.items()))
        self.assertEqual(first, {"netex:Lane": [("lane", True), ("lanes", True)], "transmodel:with": [("with", True)]})


class NoBoostConceptPathTests(TestCase):
    """The setting in the gateway's own call: the concept boost a passage gets, with the setting off and on."""

    QUESTION = "How is an accident described with a closed lane?"
    ALIASES = {"transmodel:with": {"with"}, "netex:Accident": {"accident"}, "tnits:Among": {"with"}}

    def setUp(self):
        from helpdesk.models import SourceChunk

        self.pool = []
        for idx, (path, text) in enumerate((
            ("with.xsd", "A road closed with a barrier."),
            ("accident.xsd", "An accident on the road."),
            ("other.xsd", "Other passage about roads."),
        )):
            chunk = SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc", source_path=path,
                chunk_id=f"nb-{idx}", label=path, text=text, standards_scope=["NeTEx"], quality_score=0.5,
                doc_type="schema", embedding_vector=[1.0] + [0.0] * 1535,
            )
            chunk.vector_similarity = 0.9 - idx / 100
            chunk.lexical_rank = 0.1
            self.pool.append(chunk)

    def _run(self, setting, question=QUESTION, scope=("NeTEx",)):
        from helpdesk.services import retrieval_gateway, semantic_graph

        seen = {}

        def probe(stage, items):
            if stage == "scored":
                seen["graph"] = {i["chunkId"]: round(i["_graphContribution"], 6) for i in items if isinstance(i, dict)}

        with override_settings(RETRIEVAL_CONCEPT_NO_BOOST_MATCHES=setting, GRAPHDB_ENABLED=False), \
                patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", self.ALIASES), \
                patch.object(retrieval_gateway, "_alias_lexemes", side_effect=_stop_word_lexemes), \
                patch.object(retrieval_gateway, "_postgres_hybrid_candidates", return_value=list(self.pool)), \
                patch.object(retrieval_gateway, "_path_hint_candidates", return_value=[]), \
                patch.object(retrieval_gateway, "_lexical_recall_candidates", return_value=[]), \
                patch.object(retrieval_gateway, "question_rare_lexemes", return_value=[]), \
                patch.object(retrieval_gateway, "build_text_embedding", return_value=[1.0] + [0.0] * 1535), \
                retrieval_gateway.retrieval_probe(probe):
            chunks, trace = retrieval_gateway.retrieve_chunks_with_trace(
                question=question, top_k=3, min_score=0.0, scope=list(scope), graph_rag_enabled=True
            )
        return [c["chunkId"] for c in chunks], seen["graph"], trace

    def test_off_boosts_the_stop_word_concept_as_before(self):
        from helpdesk.services import retrieval_gateway

        with patch.object(retrieval_gateway, "no_boost_question_concepts") as no_boost:
            _ids, graph, trace = self._run("")
        no_boost.assert_not_called()
        self.assertAlmostEqual(graph["nb-0"], 0.20)
        self.assertAlmostEqual(graph["nb-1"], 0.20)
        self.assertEqual(trace["noBoostConceptIds"], [])

    def test_on_the_stop_word_concept_gives_no_boost_and_the_distinctive_one_keeps_it(self):
        _ids, graph, trace = self._run("stop")
        self.assertAlmostEqual(graph["nb-0"], 0.0)
        self.assertAlmostEqual(graph["nb-1"], 0.20)
        self.assertEqual(trace["noBoostConceptIds"], ["transmodel:with"])

    def test_a_question_without_such_a_concept_is_served_as_before(self):
        question = "How is an accident described on a closed road?"
        self.assertEqual(self._run("", question)[:2], self._run("stop,loose", question)[:2])

    def test_scope_handling_is_unchanged(self):
        # An opt-in source's concept is extracted only when the scope names the source, with the setting as without.
        self.assertEqual(self._run("stop")[2]["noBoostConceptIds"], ["transmodel:with"])
        self.assertEqual(self._run("stop", scope=("NeTEx", "TN-ITS"))[2]["noBoostConceptIds"], ["tnits:Among", "transmodel:with"])
        self.assertEqual(self._run("", scope=("NeTEx", "TN-ITS"))[2]["noBoostConceptIds"], [])

    def test_repeated_calls_give_the_same_order(self):
        self.assertEqual(self._run("stop")[:2], self._run("stop")[:2])
