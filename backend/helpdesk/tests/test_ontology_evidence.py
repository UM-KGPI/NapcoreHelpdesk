from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services.ontology_evidence import (
    indexed_commit_shas,
    format_definitions_as_chunks,
    retrieve_concept_definitions,
)

NETEX_STOP_PLACE = "https://netex.org.uk/netex/2.0#StopPlace"
TM_STOP_PLACE = "https://transmodel-cen.eu/6.2/STOP_PLACE"
TM_DEFINITION = "A place comprising one or more locations where vehicles may stop."
NETEX_DEFINITION = "Version of a named place where public transport may be accessed."


def _binding(**values: str) -> dict:
    return {key: {"type": "literal", "value": value} for key, value in values.items()}


class RetrieveConceptDefinitionsTests(SimpleTestCase):
    def test_merges_values_from_all_rows(self):
        """OPTIONALs multiply rows; the XSD source may be missing from the first one."""
        xsd_source = "netex_part_1/part1_ifopt/netex_ifopt_stopPlace_version.xsd"
        owl_class = "http://www.w3.org/2002/07/owl#Class"
        results = {
            "results": {
                "bindings": [
                    _binding(concept=NETEX_STOP_PLACE, type=owl_class, definition=NETEX_DEFINITION, altLabel="stopplace"),
                    _binding(
                        concept=NETEX_STOP_PLACE,
                        type=owl_class,
                        definition=NETEX_DEFINITION,
                        altLabel="stopplace",
                        source=f"Extracted from: {xsd_source}",
                    ),
                ]
            }
        }
        with patch("helpdesk.services.graphdb_client.execute_sparql_query", return_value=results):
            definitions = retrieve_concept_definitions(
                concept_ids={"netex:StopPlace"},
                endpoint="http://localhost:7200",
                repository="napcore",
            )

        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["xsd_source"], xsd_source)
        self.assertEqual(definitions[0]["altLabels"], ["stopplace"])

        chunk = format_definitions_as_chunks(definitions)[0]
        self.assertEqual(chunk["sourcePath"], f"xsd/{xsd_source}")  # not the netex_frame.xsd fallback

    def test_collects_aligned_transmodel_definition_and_status(self):
        results = {
            "results": {
                "bindings": [
                    _binding(
                        concept=NETEX_STOP_PLACE,
                        type="http://www.w3.org/2002/07/owl#Class",
                        definition=NETEX_DEFINITION,
                        tmConcept=TM_STOP_PLACE,
                        tmLabel="STOP PLACE",
                        tmDefinition=TM_DEFINITION,
                        tmStatus="differs",
                    )
                ]
            }
        }
        with patch(
            "helpdesk.services.graphdb_client.execute_sparql_query", return_value=results
        ) as query_mock:
            definitions = retrieve_concept_definitions(
                concept_ids={"netex:StopPlace"},
                endpoint="http://localhost:7200",
                repository="napcore",
            )

        sent_query = query_mock.call_args.kwargs["sparql_query"]
        self.assertIn("skos:exactMatch|^skos:exactMatch ?tmConcept", sent_query)
        self.assertIn("tmalign:transmodelDefinitionStatus", sent_query)
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["tm_definition"], TM_DEFINITION)
        self.assertEqual(definitions[0]["tm_status"], "differs")

    def test_definition_query_reads_only_the_current_graphs(self):
        with patch(
            "helpdesk.services.graphdb_client.execute_sparql_query", return_value={"results": {"bindings": []}}
        ) as query_mock:
            retrieve_concept_definitions(
                concept_ids={"opra:Opra"}, endpoint="http://localhost:7200", repository="napcore"
            )

        sent_query = query_mock.call_args.kwargs["sparql_query"]
        for graph in (
            "https://napcore.eu/graph/standards/opra",
            "https://napcore.eu/graph/standards/transmodel",
            "https://napcore.eu/graph/alignments/transmodel-netex",
        ):
            self.assertIn(f"FROM <{graph}>", sent_query)
        self.assertNotIn("urn:graph:", sent_query)

    def test_transmodel_concept_uses_rdfs_comment_as_definition(self):
        results = {
            "results": {
                "bindings": [
                    _binding(
                        concept=TM_STOP_PLACE,
                        type="http://www.w3.org/2002/07/owl#Class",
                        ownComment=TM_DEFINITION,
                    )
                ]
            }
        }
        with patch("helpdesk.services.graphdb_client.execute_sparql_query", return_value=results):
            definitions = retrieve_concept_definitions(
                concept_ids={"transmodel:STOP_PLACE"},
                endpoint="http://localhost:7200",
                repository="napcore",
            )

        self.assertEqual(definitions[0]["definition"], TM_DEFINITION)


class FormatDefinitionsAsChunksTests(SimpleTestCase):
    def _netex_stop_place(self, **overrides) -> dict:
        definition = {
            "concept": NETEX_STOP_PLACE,
            "type": "http://www.w3.org/2002/07/owl#Class",
            "definition": NETEX_DEFINITION,
            "prefLabel": "stop place",
            "altLabels": [],
            "xsd_source": "netex_part_1/part1_ifopt/netex_ifopt_stopPlace_version.xsd",
            "tm_concept": TM_STOP_PLACE,
            "tm_label": "STOP PLACE",
            "tm_definition": TM_DEFINITION,
            "tm_status": "differs",
        }
        definition.update(overrides)
        return definition

    def test_transmodel_definition_precedes_standard_definition(self):
        chunks = format_definitions_as_chunks([self._netex_stop_place()])

        self.assertEqual(len(chunks), 2)
        tm_chunk, netex_chunk = chunks
        self.assertEqual(tm_chunk["standards_scope"], ["Transmodel"])
        self.assertIn(TM_DEFINITION, tm_chunk["text"])
        self.assertIn("StopPlace", tm_chunk["text"])  # CamelCase form for citation grounding
        self.assertIn("Implemented as: NeTEx StopPlace", tm_chunk["text"])
        self.assertEqual(tm_chunk["doc_type"], "ontology-definition")
        self.assertIn("/blob/", tm_chunk["repositoryUrl"])

        self.assertEqual(netex_chunk["standards_scope"], ["NeTEx"])
        self.assertIn("Transmodel concept: STOP PLACE", netex_chunk["text"])
        # The comparison comes from the alignment data, so the Transmodel chunk carries it,
        # not the NeTEx chunk whose source file (the XSD) does not contain it.
        self.assertIn(
            "Comparison with NeTEx StopPlace: The NeTEx XSD definition differs from the Transmodel definition",
            tm_chunk["text"],
        )
        self.assertNotIn("differs from the Transmodel definition", netex_chunk["text"])

    def test_transmodel_definition_emitted_once_per_concept(self):
        tm_own = {
            "concept": TM_STOP_PLACE,
            "type": "http://www.w3.org/2002/07/owl#Class",
            "definition": TM_DEFINITION,
            "prefLabel": "",
            "altLabels": [],
            "xsd_source": "",
        }
        chunks = format_definitions_as_chunks([self._netex_stop_place(), tm_own])

        tm_chunks = [chunk for chunk in chunks if chunk["standards_scope"] == ["Transmodel"]]
        self.assertEqual(len(tm_chunks), 1)

    def test_comparison_note_kept_when_transmodel_definition_comes_first(self):
        tm_own = {
            "concept": TM_STOP_PLACE,
            "type": "http://www.w3.org/2002/07/owl#Class",
            "definition": TM_DEFINITION,
            "prefLabel": "",
            "altLabels": [],
            "xsd_source": "",
        }
        chunks = format_definitions_as_chunks([tm_own, self._netex_stop_place()])

        tm_chunk = next(chunk for chunk in chunks if chunk["standards_scope"] == ["Transmodel"])
        self.assertIn("Comparison with NeTEx StopPlace", tm_chunk["text"])

    def test_no_comparison_note_without_transmodel_definition(self):
        chunks = format_definitions_as_chunks([self._netex_stop_place(tm_definition="")])

        self.assertEqual(len(chunks), 1)
        self.assertNotIn("differs from the Transmodel definition", chunks[0]["text"])

    def test_definition_links_use_the_indexed_commit(self):
        opra = self._netex_stop_place(
            concept="https://transmodel-cen.eu/opra/1.0#Opra",
            xsd_source="xsd/opra.xsd",
            tm_concept="",
            tm_label="",
            tm_definition="",
            tm_status="",
        )
        sha = "3b829b76247bdd577b60abfcf6568c8f2a6d118b"

        indexed = format_definitions_as_chunks([opra], commit_shas={"OpRa": sha})[0]
        self.assertEqual(
            indexed["repositoryUrl"], f"https://github.com/TransmodelEcosystem/OpRa/blob/{sha}/xsd/opra.xsd"
        )
        self.assertEqual(indexed["commitSha"], sha)

        # Nothing indexed: OpRa has no v1.0 tag, so the fallback must not name one.
        fallback = format_definitions_as_chunks([opra])[0]
        self.assertEqual(
            fallback["repositoryUrl"], "https://github.com/TransmodelEcosystem/OpRa/blob/main/xsd/opra.xsd"
        )

    def test_indexed_commit_shas_is_empty_when_the_database_cannot_be_read(self):
        # SimpleTestCase forbids database queries, so the lookup must degrade to the fallback refs.
        self.assertEqual(indexed_commit_shas(), {})

    def test_unaligned_concept_is_unchanged(self):
        chunks = format_definitions_as_chunks(
            [self._netex_stop_place(tm_concept="", tm_label="", tm_definition="", tm_status="")]
        )

        self.assertEqual(len(chunks), 1)
        self.assertNotIn("Transmodel", chunks[0]["text"])
