from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from helpdesk.models import IndexedSourceFile, IndexRunMetric, SourceChunk
from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.retrieval_gateway import retrieve_chunks


class SourceIndexBuilderTests(TestCase):
    """Verify indexing command guardrails, profile filtering, and incremental behavior."""

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
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
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                prune=True,
            )

        chunks = SourceChunk.objects.filter(repository_url="https://github.com/NeTEx-CEN/NeTEx")
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

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
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

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_build_source_index_command_rejects_unknown_profile(self):
        """Ensure unknown profile names fail fast during command validation."""
        with TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "README.md").write_text("content", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command(
                    "build_source_index",
                    repo_url="https://github.com/NeTEx-CEN/NeTEx",
                    repo_path=str(repo_path),
                    profile="nonexistent-profile",
                )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
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
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                profile="netex",
                prune=True,
            )

        self.assertTrue(SourceChunk.objects.filter(source_path="docs/netex.md").exists())
        self.assertFalse(SourceChunk.objects.filter(source_path="tests/skip.md").exists())

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
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
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                incremental=True,
                prune=True,
            )

            call_command(
                "build_source_index",
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(repo_path),
                incremental=True,
                prune=True,
            )

        latest = IndexRunMetric.objects.order_by("-created_at").first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.mode, IndexRunMetric.MODE_INCREMENTAL)
        self.assertGreaterEqual(latest.skipped_files, 1)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
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
                    repo_url="https://github.com/NeTEx-CEN/NeTEx",
                    repo_path=str(repo_path),
                    incremental=True,
                    prune=True,
                )

                call_command(
                    "build_source_index",
                    repo_url="https://github.com/NeTEx-CEN/NeTEx",
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

        @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
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
                                repo_url="https://github.com/NeTEx-CEN/NeTEx",
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
                self.assertNotIn("<xs:schema", chunk.text)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/OpRa-CEN/OpRa"})
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
                repo_url="https://github.com/OpRa-CEN/OpRa",
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
        self.assertEqual(chunks[0]["repositoryUrl"], "https://github.com/OpRa-CEN/OpRa")
        self.assertEqual(chunks[0]["sourcePath"], "docs/late-journeys.md")

    def test_generate_answer_uses_evidence_driven_delayed_journey_template(self):
        """Ensure delayed-journey questions use evidence-driven modelling terms, not the timetable template."""
        result = generate_answer(
            question="How to exchange raw data for delayed journeys in OpRa?",
            chunks=[
                {
                    "text": "The OpRa model defines how late journeys are represented for monitoring and reporting.",
                    "score": 0.74,
                    "repositoryUrl": "https://github.com/OpRa-CEN/OpRa",
                    "commitSha": "abc123",
                    "sourcePath": "docs/late-journeys.md",
                    "chunkId": "chunk-1",
                    "label": "docs/late-journeys.md",
                }
            ],
        )

        self.assertIn("Based on the retrieved evidence", result["answer"])
        self.assertIn("DATED VEHICLE JOURNEY", result["answer"])
        self.assertIn("TYPE OF DELAY", result["answer"])

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/OpRa-CEN/OpRa"})
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
                repo_url="https://github.com/OpRa-CEN/OpRa",
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
            "https://github.com/OpRa-CEN/OpRa",
            "https://github.com/NeTEx-CEN/NeTEx",
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
                repo_url="https://github.com/OpRa-CEN/OpRa",
                repo_path=str(opra_path),
                profile="opra",
                prune=True,
            )
            call_command(
                "build_source_index",
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
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
        self.assertEqual(chunks[0]["repositoryUrl"], "https://github.com/OpRa-CEN/OpRa")

    @override_settings(
        ALLOWED_SOURCE_REPOSITORIES={
            "https://github.com/OpRa-CEN/OpRa",
            "https://github.com/NeTEx-CEN/NeTEx",
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
                repo_url="https://github.com/NeTEx-CEN/NeTEx",
                repo_path=str(netex_path),
                profile="default",
                prune=True,
            )
            call_command(
                "build_source_index",
                repo_url="https://github.com/OpRa-CEN/OpRa",
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
        self.assertEqual(chunks[0]["repositoryUrl"], "https://github.com/OpRa-CEN/OpRa")
        self.assertTrue(
            any(chunk["sourcePath"] == "examples/DelayedAndCancelledJourneysWithEvents.xml" for chunk in chunks)
        )

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/OpRa-CEN/OpRa"})
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
                repo_url="https://github.com/OpRa-CEN/OpRa",
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

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/OpRa-CEN/OpRa"})
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
                repo_url="https://github.com/OpRa-CEN/OpRa",
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
