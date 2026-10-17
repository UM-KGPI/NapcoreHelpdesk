from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from helpdesk.services.ontology_evidence import (
    format_definitions_as_chunks,
    retrieve_concept_definitions,
)

NETEX_STOP_PLACE = "https://netex.org.uk/netex/2.0#StopPlace"
NETEX_DEFINITION = "Version of a named place where public transport may be accessed."
XSD_SOURCE = "netex_part_1/part1_ifopt/netex_ifopt_stopPlace_version.xsd"


def _binding(**values: str) -> dict:
    return {key: {"type": "literal", "value": value} for key, value in values.items()}


class RetrieveConceptDefinitionsTests(SimpleTestCase):
    def test_merges_values_from_all_rows(self):
        """OPTIONALs multiply rows; the XSD source may be missing from the first one."""
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
                        source=f"Extracted from: {XSD_SOURCE}",
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
        self.assertEqual(definitions[0]["xsd_source"], XSD_SOURCE)
        self.assertEqual(definitions[0]["altLabels"], ["stopplace"])

        chunk = format_definitions_as_chunks(definitions)[0]
        self.assertEqual(chunk["sourcePath"], f"xsd/{XSD_SOURCE}")  # not the netex_frame.xsd fallback
