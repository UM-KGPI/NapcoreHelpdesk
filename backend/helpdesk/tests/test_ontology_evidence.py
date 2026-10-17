from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services.ontology_evidence import (
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
        self.assertIn("nits:transmodelDefinitionStatus", sent_query)
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["tm_definition"], TM_DEFINITION)
        self.assertEqual(definitions[0]["tm_status"], "differs")

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
        self.assertIn("use the Transmodel definition as the reference", netex_chunk["text"])

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

    def test_unaligned_concept_is_unchanged(self):
        chunks = format_definitions_as_chunks(
            [self._netex_stop_place(tm_concept="", tm_label="", tm_definition="", tm_status="")]
        )

        self.assertEqual(len(chunks), 1)
        self.assertNotIn("Transmodel", chunks[0]["text"])
