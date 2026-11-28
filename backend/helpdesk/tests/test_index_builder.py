from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from helpdesk.models import IndexedSourceFile, IndexRunMetric, SourceChunk
from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.retrieval_gateway import retrieve_chunks


class SourceIndexBuilderTests(TestCase):
    """Verify indexing command guardrails, profile filtering, and incremental behavior."""

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_build_source_index_command_indexes_repository_files(self):
        """Ensure an allowed repository is indexed into chunks and run metrics."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "guide.md").write_text(
                "NeTEx timetable exchange guidance with references to SIRI and Transmodel.",
                encoding="utf-8",
            )
            (docs / "ignore.bin").write_bytes(b"binary")

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(repo_path),
                prune=True,
            )

        chunks = SourceChunk.objects.filter(repository_url="https://github.com/TransmodelEcosystem/NeTEx")
        self.assertGreater(chunks.count(), 0)
        self.assertTrue(chunks.filter(source_path="docs/guide.md").exists())

        scopes = set()
        for chunk in chunks:
            scopes.update(chunk.standards_scope)

        self.assertIn("NeTEx", scopes)
        self.assertIn("SIRI", scopes)
        self.assertIn("Transmodel", scopes)
        first_chunk = chunks.first()
        self.assertIsNotNone(first_chunk)
        self.assertTrue(isinstance(first_chunk.embedding_vector, list))
        self.assertGreater(len(first_chunk.embedding_vector), 0)
        self.assertIn(first_chunk.doc_type, {"guide", "readme", "schema", "example", "frame", "object"})
        self.assertNotEqual(first_chunk.quality_score, 0.75)
        self.assertTrue(IndexedSourceFile.objects.filter(source_path="docs/guide.md").exists())
        self.assertEqual(IndexRunMetric.objects.filter(status=IndexRunMetric.STATUS_SUCCESS).count(), 1)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/SIRI"})
    def test_build_source_index_stores_one_copy_for_repository_aliases(self):
        """Indexing a repository under an alias must not create a second copy of its chunks."""
        siri = "https://github.com/TransmodelEcosystem/SIRI"
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "guide.md").write_text("SIRI estimated timetable guidance.", encoding="utf-8")

            call_command("build_source_index", repo_url=siri, repo_path=str(repo_path), prune=True)
            first_ids = set(SourceChunk.objects.values_list("chunk_id", flat=True))
            call_command(
                "build_source_index",
                repo_url="https://github.com/SIRI-CEN/SIRI",
                repo_path=str(repo_path),
                prune=True,
            )

        self.assertTrue(first_ids)
        self.assertEqual(set(SourceChunk.objects.values_list("chunk_id", flat=True)), first_ids)
        self.assertEqual(set(SourceChunk.objects.values_list("repository_url", flat=True)), {siri})

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_build_source_index_command_rejects_unapproved_repository(self):
        """Ensure repositories outside the configured allow-list are rejected."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "README.md").write_text("content", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command(
                    "build_source_index",
                    repo_url="https://github.com/example/unapproved",
                    repo_path=str(repo_path),
                )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_build_source_index_command_rejects_unknown_profile(self):
        """Ensure unknown profile names fail fast during command validation."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "README.md").write_text("content", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command(
                    "build_source_index",
                    repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                    repo_path=str(repo_path),
                    profile="nonexistent-profile",
                )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_build_source_index_command_applies_netex_profile_filtering(self):
        """Ensure the NeTEx profile includes docs-like paths and excludes test paths."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            tests = repo_path / "tests"
            docs.mkdir(parents=True, exist_ok=True)
            tests.mkdir(parents=True, exist_ok=True)

            (docs / "netex.md").write_text("NeTEx profile doc", encoding="utf-8")
            (tests / "skip.md").write_text("NeTEx test doc", encoding="utf-8")

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(repo_path),
                profile="netex",
                prune=True,
            )

        self.assertTrue(SourceChunk.objects.filter(source_path="docs/netex.md").exists())
        self.assertFalse(SourceChunk.objects.filter(source_path="tests/skip.md").exists())

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_build_source_index_command_incremental_skips_unchanged_files(self):
        """Ensure incremental mode skips unchanged files on subsequent runs."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            guide = docs / "guide.md"
            guide.write_text("NeTEx timetable exchange", encoding="utf-8")

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(repo_path),
                incremental=True,
                prune=True,
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(repo_path),
                incremental=True,
                prune=True,
            )

        latest = IndexRunMetric.objects.order_by("-created_at").first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.mode, IndexRunMetric.MODE_INCREMENTAL)
        self.assertGreaterEqual(latest.skipped_files, 1)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_build_source_index_incremental_skips_when_head_changes_but_content_same(self):
        """Ensure per-file incremental logic does not re-upsert unchanged files on HEAD-only changes."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            guide = docs / "guide.md"
            guide.write_text("NeTEx timetable exchange", encoding="utf-8")

            with patch("helpdesk.services.index_builder.current_commit_sha", side_effect=["sha-old", "sha-new"]):
                call_command(
                    "build_source_index",
                    repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                    repo_path=str(repo_path),
                    incremental=True,
                    prune=True,
                )

                call_command(
                    "build_source_index",
                    repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                    repo_path=str(repo_path),
                    incremental=True,
                    prune=True,
                )

        latest = IndexRunMetric.objects.order_by("-created_at").first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.mode, IndexRunMetric.MODE_INCREMENTAL)
        self.assertGreaterEqual(latest.skipped_files, 1)
        self.assertEqual(latest.created_chunks, 0)
        self.assertEqual(latest.updated_chunks, 0)

        @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
        def test_build_source_index_summarizes_xsd_without_indexing_raw_schema_blob(self):
                """Ensure XSD files become compact schema summaries rather than raw schema windows."""
                with TemporaryDirectory() as tmp_dir:
                        repo_path = Path(tmp_dir)
                        xsd_dir = repo_path / "xsd"
                        xsd_dir.mkdir(parents=True, exist_ok=True)
                        (xsd_dir / "stops.xsd").write_text(
                                """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">
    <xs:element name=\"PassengerStopAssignment\">
        <xs:annotation>
            <xs:documentation>Links a scheduled stop point to a stop place.</xs:documentation>
        </xs:annotation>
        <xs:complexType>
            <xs:sequence>
                <xs:element name=\"ScheduledStopPointRef\" type=\"xs:string\"/>
                <xs:element name=\"StopPlaceRef\" type=\"xs:string\"/>
            </xs:sequence>
            <xs:attribute name=\"version\" type=\"xs:string\" use=\"required\"/>
        </xs:complexType>
    </xs:element>
</xs:schema>
""",
                                encoding="utf-8",
                        )

                        call_command(
                                "build_source_index",
                                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                                repo_path=str(repo_path),
                                profile="netex",
                                prune=True,
                        )

                chunk = SourceChunk.objects.get(source_path="xsd/stops.xsd")
                self.assertEqual(chunk.chunk_type, "schema_fragment")
                self.assertEqual(chunk.heading, "PassengerStopAssignment")
                self.assertIn("Schema declaration: element PassengerStopAssignment", chunk.text)
                self.assertIn("Direct child elements: ScheduledStopPointRef, StopPlaceRef", chunk.text)
                self.assertIn("Attributes: version (required)", chunk.text)
                self.assertEqual(
                    chunk.structured_metadata["schema"]["requiredChildElements"],
                    ["ScheduledStopPointRef", "StopPlaceRef"],
                )
                self.assertEqual(chunk.structured_metadata["schema"]["requiredAttributes"], ["version"])
                self.assertNotIn("<xs:schema", chunk.text)

        @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
        def test_build_source_index_summarizes_xsd_group_definitions(self):
                """xs:group declarations (e.g. ServiceJourneyGroup) must be chunked too, since
                the elements they reference are otherwise invisible to retrieval - only the
                thin complexType wrapper that points at the group gets indexed."""
                with TemporaryDirectory() as tmp_dir:
                        repo_path = Path(tmp_dir)
                        xsd_dir = repo_path / "xsd"
                        xsd_dir.mkdir(parents=True, exist_ok=True)
                        (xsd_dir / "serviceJourney.xsd").write_text(
                                """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">
    <xs:group name=\"ServiceJourneyReferencesGroup\">
        <xs:annotation>
            <xs:documentation>Reference elements for a SERVICE JOURNEY.</xs:documentation>
        </xs:annotation>
        <xs:sequence>
            <xs:element ref=\"LineRef\"/>
            <xs:element ref=\"DirectionType\" minOccurs=\"0\"/>
        </xs:sequence>
    </xs:group>
</xs:schema>
""",
                                encoding="utf-8",
                        )

                        call_command(
                                "build_source_index",
                                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                                repo_path=str(repo_path),
                                profile="netex",
                                prune=True,
                        )

                chunk = SourceChunk.objects.get(source_path="xsd/serviceJourney.xsd")
                self.assertEqual(chunk.chunk_type, "schema_fragment")
                self.assertEqual(chunk.heading, "ServiceJourneyReferencesGroup")
                self.assertIn("Schema declaration: group ServiceJourneyReferencesGroup", chunk.text)
                self.assertIn("Direct child elements: LineRef, DirectionType", chunk.text)
                self.assertEqual(
                    chunk.structured_metadata["schema"]["requiredChildElements"],
                    ["LineRef"],
                )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/OpRa"})
    def test_retrieve_chunks_matches_delayed_question_to_late_journey_docs(self):
        """Ensure retrieval handles common delayed-vs-late wording differences for OpRa docs."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "late-journeys.md").write_text(
                "The OpRa model defines how late journeys are represented for monitoring and reporting.",
                encoding="utf-8",
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(repo_path),
                profile="opra",
                prune=True,
            )

        chunks = retrieve_chunks(
            question="How to exchange raw data for delayed journeys in OpRa?",
            top_k=6,
            min_score=0.30,
            scope=["OpRa"],
        )

        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["repositoryUrl"], "https://github.com/TransmodelEcosystem/OpRa")
        self.assertEqual(chunks[0]["sourcePath"], "docs/late-journeys.md")

    def test_generate_answer_uses_evidence_driven_delayed_journey_template(self):
        """Ensure deterministic fallback remains evidence-grounded for delayed-journey asks."""
        result = generate_answer(
            question="How to exchange raw data for delayed journeys in OpRa?",
            chunks=[
                {
                    "text": "The OpRa model defines how late journeys are represented for monitoring and reporting.",
                    "score": 0.74,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/OpRa",
                    "commitSha": "abc123",
                    "sourcePath": "docs/late-journeys.md",
                    "chunkId": "chunk-1",
                    "label": "docs/late-journeys.md",
                }
            ],
        )

        self.assertIn("Based on retrieved approved-source evidence", result["answer"])
        self.assertIn("[E1]", result["answer"])
        self.assertNotIn("docs/late-journeys.md", result["answer"])
        self.assertIn("validate implementation", result["answer"])

    def test_generate_answer_combines_cross_repository_delay_exchange_evidence(self):
        """Ensure deterministic fallback reports cross-repository evidence span."""
        result = generate_answer(
            question="How can I exchange delayed vehicle journeys?",
            chunks=[
                {
                    "text": "Example payload for delayed and cancelled journeys with events.",
                    "score": 0.86,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/OpRa",
                    "commitSha": "abc123",
                    "sourcePath": "examples/DelayedAndCancelledJourneysWithEvents.xml",
                    "chunkId": "chunk-opra-example",
                    "label": "DelayedAndCancelledJourneysWithEvents.xml",
                },
                {
                    "text": "SIRI supports real-time exchange in public transport systems.",
                    "score": 0.81,
                    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
                    "commitSha": "def456",
                    "sourcePath": "README.md",
                    "chunkId": "chunk-generic",
                    "label": "README.md",
                },
            ],
        )

        self.assertIn("Based on retrieved approved-source evidence", result["answer"])
        self.assertIn("Evidence spans multiple repositories", result["answer"])

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/OpRa"})
    def test_retrieve_chunks_prefers_docs_model_content_over_readme(self):
        """Ensure generic README chunks rank below substantive docs/model content."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (repo_path / "README.md").write_text(
                "OpRa exchange overview for late journeys and delay reporting.",
                encoding="utf-8",
            )
            (docs / "late-journeys-model-summary.md").write_text(
                "DATED VEHICLE JOURNEY and DATED PASSING TIME are used to report late journeys and TYPE OF DELAY.",
                encoding="utf-8",
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(repo_path),
                profile="opra",
                prune=True,
            )

        chunks = retrieve_chunks(
            question="How to exchange raw data for delayed journeys in OpRa?",
            top_k=6,
            min_score=0.30,
            scope=None,
        )

        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["sourcePath"], "docs/late-journeys-model-summary.md")

    @override_settings(
        ALLOWED_SOURCE_REPOSITORIES={
            "https://github.com/TransmodelEcosystem/OpRa",
            "https://github.com/TransmodelEcosystem/NeTEx",
        }
    )
    def test_retrieve_chunks_prefers_explicit_opra_intent_without_scope(self):
        """Ensure explicit OpRa mention ranks OpRa chunks ahead of other standards when scope is empty."""
        with TemporaryDirectory() as opra_tmp_dir, TemporaryDirectory() as netex_tmp_dir:
            opra_path = Path(opra_tmp_dir)
            opra_docs = opra_path / "docs"
            opra_docs.mkdir(parents=True, exist_ok=True)
            (opra_docs / "late-journeys-model-summary.md").write_text(
                "The OpRa model reports late journeys with DATED VEHICLE JOURNEY, DATED PASSING TIME, and TYPE OF DELAY.",
                encoding="utf-8",
            )

            netex_path = Path(netex_tmp_dir)
            netex_examples = netex_path / "examples"
            netex_examples.mkdir(parents=True, exist_ok=True)
            (netex_examples / "delay-example.xml").write_text(
                "Example XML showing delay fields and journey records.",
                encoding="utf-8",
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(opra_path),
                profile="opra",
                prune=True,
            )
            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(netex_path),
                profile="default",
                prune=True,
            )

        chunks = retrieve_chunks(
            question="How to exchange raw data for delayed journeys in OpRa?",
            top_k=6,
            min_score=0.30,
            scope=None,
        )

        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["repositoryUrl"], "https://github.com/TransmodelEcosystem/OpRa")

    @override_settings(
        ALLOWED_SOURCE_REPOSITORIES={
            "https://github.com/TransmodelEcosystem/OpRa",
            "https://github.com/TransmodelEcosystem/NeTEx",
        }
    )
    def test_retrieve_chunks_finds_opra_example_by_filename_with_scope(self):
        """Ensure OpRa-scoped filename queries do not get starved by larger non-OpRa corpora."""
        with TemporaryDirectory() as opra_tmp_dir, TemporaryDirectory() as netex_tmp_dir:
            opra_path = Path(opra_tmp_dir)
            opra_examples = opra_path / "examples"
            opra_examples.mkdir(parents=True, exist_ok=True)
            (opra_examples / "DelayedAndCancelledJourneysWithEvents.xml").write_text(
                """<Opra>
  <Description>Operational journey event exchange payload.</Description>
  <LateDatedVehicleJourneyEntry />
</Opra>
""",
                encoding="utf-8",
            )

            netex_path = Path(netex_tmp_dir)
            netex_examples = netex_path / "examples"
            netex_examples.mkdir(parents=True, exist_ok=True)
            for idx in range(0, 80):
                (netex_examples / f"example-{idx}.xml").write_text(
                    "Example XML payload for generic interchange patterns and timetables.",
                    encoding="utf-8",
                )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(netex_path),
                profile="default",
                prune=True,
            )
            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(opra_path),
                profile="opra",
                prune=True,
            )

        chunks = retrieve_chunks(
            question="There is an example called DelayedAndCancelledJourneysWithEvents, can you find it?",
            top_k=6,
            min_score=0.30,
            scope=["OpRa"],
        )

        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["repositoryUrl"], "https://github.com/TransmodelEcosystem/OpRa")
        self.assertTrue(
            any(chunk["sourcePath"] == "examples/DelayedAndCancelledJourneysWithEvents.xml" for chunk in chunks)
        )

    @override_settings(
        ALLOWED_SOURCE_REPOSITORIES={
            "https://github.com/TransmodelEcosystem/OpRa",
            "https://github.com/TransmodelEcosystem/NeTEx",
        }
    )
    def test_retrieve_chunks_finds_opra_example_by_semantic_content(self):
        """Ensure delayed journey statistics queries match XML example semantics, not only filename hints."""
        with TemporaryDirectory() as opra_tmp_dir, TemporaryDirectory() as netex_tmp_dir:
            opra_path = Path(opra_tmp_dir)
            opra_examples = opra_path / "examples"
            opra_examples.mkdir(parents=True, exist_ok=True)
            (opra_examples / "DelayedAndCancelledJourneysWithEvents.xml").write_text(
                """<Opra>
  <ServiceDelivery>
    <OpraPayloadDelivery>
      <!-- Delayed Journey 1: Minor delay caused by previous late arrival -->
      <LateDatedVehicleJourneyEntry>
        <DelayDuration>PT5M</DelayDuration>
      </LateDatedVehicleJourneyEntry>
      <!-- Delayed Journey Statistics by route -->
      <DelayStatistics>
        <DelayedJourneyCount>4</DelayedJourneyCount>
      </DelayStatistics>
    </OpraPayloadDelivery>
  </ServiceDelivery>
</Opra>
""",
                encoding="utf-8",
            )

            netex_path = Path(netex_tmp_dir)
            netex_examples = netex_path / "examples"
            netex_examples.mkdir(parents=True, exist_ok=True)
            for idx in range(0, 80):
                (netex_examples / f"generic-{idx}.xml").write_text(
                    "Timetable example payload with stop points and service journey references.",
                    encoding="utf-8",
                )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(netex_path),
                profile="default",
                prune=True,
            )
            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(opra_path),
                profile="opra",
                prune=True,
            )

        chunks = retrieve_chunks(
            question="How are delayed journey statistics represented in OpRa examples?",
            top_k=6,
            min_score=0.30,
            scope=["OpRa"],
        )

        self.assertTrue(chunks)
        self.assertTrue(
            any(chunk["sourcePath"] == "examples/DelayedAndCancelledJourneysWithEvents.xml" for chunk in chunks)
        )

    @override_settings(
        ALLOWED_SOURCE_REPOSITORIES={
            "https://github.com/TransmodelEcosystem/OpRa",
            "https://github.com/TransmodelEcosystem/NeTEx",
        }
    )
    def test_retrieve_chunks_balances_delay_exchange_evidence_across_repositories(self):
        """Ensure retrieval keeps relevant evidence from multiple repositories for delay exchange intent."""
        with TemporaryDirectory() as opra_tmp_dir, TemporaryDirectory() as netex_tmp_dir:
            opra_path = Path(opra_tmp_dir)
            opra_examples = opra_path / "examples"
            opra_examples.mkdir(parents=True, exist_ok=True)
            (opra_examples / "DelayedAndCancelledJourneysWithEvents.xml").write_text(
                """<Opra>
  <LateDatedVehicleJourneyEntry />
  <DelayStatistics>
    <DelayedJourneyCount>4</DelayedJourneyCount>
  </DelayStatistics>
</Opra>
""",
                encoding="utf-8",
            )

            netex_path = Path(netex_tmp_dir)
            netex_docs = netex_path / "docs"
            netex_docs.mkdir(parents=True, exist_ok=True)
            (netex_docs / "siri-realtime-exchange.md").write_text(
                "SIRI real-time exchange updates delayed or cancelled vehicle journeys against planned timetable baselines.",
                encoding="utf-8",
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(opra_path),
                profile="opra",
                prune=True,
            )
            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/NeTEx",
                repo_path=str(netex_path),
                profile="default",
                prune=True,
            )

        chunks = retrieve_chunks(
            question="How can I exchange delayed vehicle journeys?",
            top_k=6,
            min_score=0.30,
            scope=None,
        )

        self.assertTrue(chunks)
        repository_urls = {chunk["repositoryUrl"] for chunk in chunks}
        self.assertIn("https://github.com/TransmodelEcosystem/OpRa", repository_urls)
        self.assertIn("https://github.com/TransmodelEcosystem/NeTEx", repository_urls)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/OpRa"})
    def test_index_builder_assigns_doc_type_from_paths(self):
        """Ensure chunk doc_type is assigned for README, examples, and schema sources."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            examples = repo_path / "examples"
            schema = repo_path / "schema"
            docs.mkdir(parents=True, exist_ok=True)
            examples.mkdir(parents=True, exist_ok=True)
            schema.mkdir(parents=True, exist_ok=True)

            (repo_path / "README.md").write_text("OpRa repository overview.", encoding="utf-8")
            (examples / "journey-example.xml").write_text("<root><item>example</item></root>", encoding="utf-8")
            (schema / "journey.xsd").write_text(
                """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">
  <xs:element name=\"Journey\" type=\"xs:string\"/>
</xs:schema>
""",
                encoding="utf-8",
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(repo_path),
                profile="default",
                prune=True,
            )

        readme_chunk = SourceChunk.objects.filter(source_path="README.md").first()
        self.assertIsNotNone(readme_chunk)
        self.assertEqual(readme_chunk.doc_type, "readme")

        example_chunk = SourceChunk.objects.filter(source_path="examples/journey-example.xml").first()
        self.assertIsNotNone(example_chunk)
        self.assertEqual(example_chunk.doc_type, "example")

        schema_chunk = SourceChunk.objects.filter(source_path="schema/journey.xsd").first()
        self.assertIsNotNone(schema_chunk)
        self.assertEqual(schema_chunk.doc_type, "schema")

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/OpRa"})
    def test_index_builder_uses_doc_type_quality_signal(self):
        """Ensure quality scores differ across doc types instead of using one constant."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            docs = repo_path / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            (repo_path / "README.md").write_text("OpRa overview and quick links.", encoding="utf-8")
            (docs / "frame-guide.md").write_text(
                "# Service Frame\nThe frame defines relationships and constraints for journey exchange.",
                encoding="utf-8",
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/TransmodelEcosystem/OpRa",
                repo_path=str(repo_path),
                profile="default",
                prune=True,
            )

        readme_chunk = SourceChunk.objects.filter(source_path="README.md").first()
        frame_chunk = SourceChunk.objects.filter(source_path="docs/frame-guide.md").first()

        self.assertIsNotNone(readme_chunk)
        self.assertIsNotNone(frame_chunk)
        self.assertEqual(readme_chunk.doc_type, "readme")
        self.assertEqual(frame_chunk.doc_type, "frame")
        self.assertLess(readme_chunk.quality_score, frame_chunk.quality_score)


class TrackedSourceFilesTests(SimpleTestCase):
    """In a git checkout only tracked files are indexed: untracked and gitignored files
    (a contributor's local notes) are not part of the published standard."""

    def _git(self, repo, *args):
        import subprocess

        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    def test_git_checkout_lists_only_tracked_files(self):
        import shutil

        from helpdesk.services.index_builder import iter_source_files

        if not shutil.which("git"):
            self.skipTest("git is not installed")
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "xsd").mkdir()
            (repo / "xsd" / "netex_line.xsd").write_text("<xs:schema/>")
            (repo / "README.md").write_text("# NeTEx")
            (repo / ".gitignore").write_text(".mylocal/\n")
            (repo / ".mylocal").mkdir()
            (repo / ".mylocal" / "notes.md").write_text("local notes")
            self._git(repo, "init", "-q")
            self._git(repo, "add", "xsd/netex_line.xsd", "README.md", ".gitignore")
            (repo / "draft.md").write_text("untracked draft")

            files = iter_source_files(repo, {".xsd", ".md"})

        self.assertEqual([p.relative_to(repo).as_posix() for p in files], ["README.md", "xsd/netex_line.xsd"])

    def test_directory_without_git_is_walked(self):
        from helpdesk.services.index_builder import iter_source_files

        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "notes").mkdir()
            (repo / "notes" / "a.md").write_text("a")
            (repo / "node_modules").mkdir()
            (repo / "node_modules" / "b.md").write_text("b")
            (repo / ".mylocal").mkdir()
            (repo / ".mylocal" / "c.md").write_text("local notes")

            files = iter_source_files(repo, {".md"})

        self.assertEqual([p.relative_to(repo).as_posix() for p in files], ["notes/a.md"])

    def test_mylocal_is_skipped_when_git_listing_fails(self):
        from unittest.mock import patch

        from helpdesk.services import index_builder

        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            (repo / "README.md").write_text("# OpRa")
            (repo / ".mylocal").mkdir()
            (repo / ".mylocal" / "notes.md").write_text("local notes")

            with patch.object(index_builder, "_git", side_effect=RuntimeError("not a git repository")):
                files = index_builder.iter_source_files(repo, {".md"})

        self.assertEqual([p.relative_to(repo).as_posix() for p in files], ["README.md"])


class SplitTurtleTests(SimpleTestCase):
    """Turtle files are chunked by whole resource descriptions (src-md05: an example's dcat:CatalogRecord was
    cut between two fixed-size chunks)."""

    EXAMPLE = """@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct: <http://purl.org/dc/terms/> .
# A comment with a full stop. Not a statement end.
<https://example.org/catalog> a dcat:Catalog ;
    dct:title "Example catalogue. With a dot."@en ;
    dcat:record <https://example.org/record> .

<https://example.org/record> a dcat:CatalogRecord ;
    dct:issued "2019-12-04"^^<http://www.w3.org/2001/XMLSchema#date> ;
    dct:description \"\"\"Multi-line.
    It ends a sentence .
    Still the same literal.\"\"\" .

<https://example.org/dataset> a dcat:Dataset ;
    dcat:spatialResolutionInMeters 1.5 ;
    dct:temporal [ a dct:PeriodOfTime ; dcat:startDate "2020-01-01" ] .
"""

    def test_each_resource_type_gets_its_own_chunk(self):
        from helpdesk.services.index_builder import split_turtle

        chunks = split_turtle(self.EXAMPLE, max_chars=1200)
        self.assertEqual([heading for _, _, heading in chunks], ["dcat:Catalog", "dcat:CatalogRecord", "dcat:Dataset"])
        record = chunks[1][0]
        self.assertTrue(record.startswith("<https://example.org/record> a dcat:CatalogRecord"))
        self.assertIn("Still the same literal.", record)  # a "." inside a literal does not end the statement
        self.assertIn("1.5", chunks[2][0])  # nor does a decimal point
        self.assertIn("dct:PeriodOfTime", chunks[2][0])  # nor one inside [ ... ]
        self.assertFalse(any("@prefix" in text for text, _, _ in chunks))

    def test_same_type_statements_are_packed_up_to_the_limit(self):
        from helpdesk.services.index_builder import split_turtle

        codes = "\n".join(f"<http://x/code{i}> a skos:Concept ; skos:prefLabel \"code {i}\" ." for i in range(30))
        chunks = split_turtle(codes, max_chars=300)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(text) <= 300 for text, _, _ in chunks))
        self.assertTrue(all(text.count("a skos:Concept") == text.count("skos:prefLabel") for text, _, _ in chunks))

    def test_dispatch_and_fallback(self):
        from helpdesk.services.index_builder import split_structured

        self.assertEqual(split_structured(self.EXAMPLE, ".ttl")[1][2], "dcat:CatalogRecord")
        self.assertTrue(split_structured("", ".ttl") == [] or all(t == "prose" for _, t, _ in split_structured("", ".ttl")))


class XsdSummaryValuesTests(SimpleTestCase):
    """XSD summaries carry enumeration values and the documentation of children declared in place."""

    XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.netex.org.uk/netex" targetNamespace="http://www.netex.org.uk/netex">
  <xsd:simpleType name="SeatAllocationMethodEnumeration">
    <xsd:annotation><xsd:documentation>Allowed values for Seat Allocation Method.</xsd:documentation></xsd:annotation>
    <xsd:restriction base="xsd:normalizedString">
      <xsd:enumeration value="autoAssigned">
        <xsd:annotation><xsd:documentation>A seat will be assigned automatically by an algorithm.</xsd:documentation></xsd:annotation>
      </xsd:enumeration>
      <xsd:enumeration value="seatMap"/>
    </xsd:restriction>
  </xsd:simpleType>
  <xsd:element name="Orientation">
    <xsd:annotation><xsd:documentation>Orientation of the seat.</xsd:documentation></xsd:annotation>
    <xsd:simpleType>
      <xsd:restriction base="xsd:string">
        <xsd:enumeration value="forwards"/>
        <xsd:enumeration value="backwards"/>
      </xsd:restriction>
    </xsd:simpleType>
  </xsd:element>
  <xsd:group name="CapacityGroup">
    <xsd:annotation><xsd:documentation>Capacity type Elements for a PASSENGER CAPACITY REQUIREMENT.</xsd:documentation></xsd:annotation>
    <xsd:sequence>
      <xsd:element name="SeatingCapacity" type="NumberOfPassengers" minOccurs="0">
        <xsd:annotation><xsd:documentation>The seating capacity of vehicles of the type.</xsd:documentation></xsd:annotation>
      </xsd:element>
      <xsd:element name="StandingCapacity" type="NumberOfPassengers" minOccurs="0"/>
      <xsd:element ref="PassengerCapacity" minOccurs="0"/>
    </xsd:sequence>
  </xsd:group>
</xsd:schema>"""

    def _summaries(self, text=None):
        from helpdesk.services.index_builder import split_xsd_summary

        return {heading: chunk for chunk, _, heading in split_xsd_summary(text or self.XSD, source_name="x.xsd")}

    def test_enumeration_values_with_their_documentation(self):
        summary = self._summaries()["SeatAllocationMethodEnumeration"]
        self.assertIn("Documentation: Allowed values for Seat Allocation Method.", summary)
        self.assertIn(
            "Allowed values: autoAssigned (A seat will be assigned automatically by an algorithm.); seatMap", summary
        )

    def test_values_of_an_inline_simple_type(self):
        self.assertIn("Allowed values: forwards; backwards", self._summaries()["Orientation"])

    def test_long_enumerations_are_cut_with_a_count(self):
        values = "".join(f'<xsd:enumeration value="v{i}"/>' for i in range(65))
        text = self.XSD.replace('<xsd:enumeration value="seatMap"/>', values)
        summary = self._summaries(text)["SeatAllocationMethodEnumeration"]
        self.assertIn("v58", summary)
        self.assertNotIn("v59;", summary)
        self.assertTrue(summary.endswith("; … and 6 more"))

    def test_documentation_of_children_declared_in_place(self):
        summary = self._summaries()["CapacityGroup"]
        self.assertIn("Child element documentation:\n- SeatingCapacity: The seating capacity of vehicles of the type.", summary)
        self.assertNotIn("- StandingCapacity", summary)  # no documentation of its own
        self.assertNotIn("- PassengerCapacity", summary)  # a reference: documented in its own chunk
        self.assertNotIn("Allowed values", summary)

    def test_chunker_versions_are_part_of_the_content_hash(self):
        from helpdesk.services.index_builder import chunker_marker

        self.assertTrue(chunker_marker(".xsd").startswith("xsd-chunker "))
        self.assertTrue(chunker_marker(".XSD").startswith("xsd-chunker "))
        self.assertTrue(chunker_marker(".ttl").startswith("turtle-chunker "))
        self.assertEqual(chunker_marker(".xml"), "")


class XsdDocumentChunkTests(SimpleTestCase):
    """A schema without declarations is indexed from its own description (siri_all_functionalServices.xsd)."""

    XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:annotation><xsd:appinfo><Metadata xmlns="http://www.govtalk.gov.uk/CM/gms-xs">
    <Description><p>SIRI comprises a modular set of functional services.
      <ul><li>SIRI-PT Production Timetable: Exchanges planned timetables.</li><li>SIRI-ET Estimated Timetable: Exchanges real-time updates to timetables.</li></ul></p></Description>
    <Format><Description>XML schema, W3C Recommendation 2001</Description></Format>
    <Publisher>Somebody Ltd</Publisher>
    <Title>Current SIRI functional services</Title>
  </Metadata></xsd:appinfo></xsd:annotation>
  <xsd:include schemaLocation="siri_estimatedTimetable_service.xsd"/>
  <xsd:include schemaLocation="siri_productionTimetable_service.xsd"/>
</xsd:schema>"""

    def _chunks(self, text):
        from helpdesk.services.index_builder import split_xsd_summary

        return [chunk for chunk, _, _ in split_xsd_summary(text, source_name="siri_all_functionalServices.xsd")]

    def test_description_list_items_become_lines(self):
        text = "\n".join(self._chunks(self.XSD))
        self.assertIn("- SIRI-ET Estimated Timetable: Exchanges real-time updates to timetables.", text)
        self.assertIn("Title: Current SIRI functional services", text)

    def test_boilerplate_is_left_out(self):
        text = "\n".join(self._chunks(self.XSD))
        self.assertNotIn("W3C Recommendation", text)
        self.assertNotIn("Somebody Ltd", text)
        self.assertNotIn("<?xml", text)

    def test_included_schemas_are_listed(self):
        self.assertIn(
            "includes: siri_estimatedTimetable_service.xsd, siri_productionTimetable_service.xsd", self._chunks(self.XSD)[-1]
        )

    def test_long_text_is_packed_at_line_and_word_boundaries(self):
        items = "".join(f"<li>SIRI-X{i} Service number {i}: provides information.</li>" for i in range(120))
        text = self.XSD.replace("<li>SIRI-PT", items + "<li>SIRI-PT")
        chunks = self._chunks(text)
        self.assertGreater(len(chunks), 3)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 1500)
            for line in chunk.split("\n"):
                if line.startswith("- SIRI-X"):
                    self.assertTrue(line.endswith("provides information."), line)

    def test_only_declaration_less_schemas_get_the_document_marker(self):
        from helpdesk.services.index_builder import chunker_marker

        self.assertIn("xsd-document-chunker", chunker_marker(".xsd", self.XSD))
        with_type = self.XSD.replace("</xsd:schema>", '<xsd:simpleType name="X"><xsd:restriction base="xsd:string"/></xsd:simpleType></xsd:schema>')
        self.assertNotIn("xsd-document-chunker", chunker_marker(".xsd", with_type))
        self.assertEqual(chunker_marker(".xsd"), chunker_marker(".xsd", with_type))
