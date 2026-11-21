"""OWL properties are not concepts: the labels query leaves them out, the links between classes and the
property_terms index do not depend on them."""

from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services import property_terms

ENDPOINT = "http://graphdb.test:7200/repositories/napcore-helpdesk"
NETEX = "https://netex.org.uk/netex/2.0#"


class _Response:
    def __init__(self, bindings):
        self._body = json.dumps({"results": {"bindings": bindings}}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _row(**values):
    return {key: {"value": value} for key, value in values.items()}


class LabelsQueryTests(SimpleTestCase):
    def _load(self):
        sent = []

        def answer(request, timeout=None):
            sent.append(request.full_url)
            if "prefLabel" in request.full_url:
                # What GraphDB returns for the filtered query: the two classes, not the property between them.
                return _Response([_row(concept=NETEX + "Line", label="Line"), _row(concept=NETEX + "Network", label="Network")])
            if "ObjectProperty" in request.full_url and "domain" in request.full_url:
                return _Response([_row(concept=NETEX + "Line", related=NETEX + "Network")])
            return _Response([])

        with patch("urllib.request.urlopen", side_effect=answer):
            ontology = semantic_graph._load_ontology_from_graphdb(ENDPOINT)
        return ontology, sent

    def test_the_labels_query_leaves_properties_out_and_keeps_classes(self):
        from urllib.parse import unquote_plus

        _ontology, sent = self._load()
        labels = unquote_plus(next(url for url in sent if "prefLabel" in url))
        self.assertIn("owl#ObjectProperty", labels)
        self.assertIn("owl#DatatypeProperty", labels)
        self.assertIn("EXISTS { ?concept a <http://www.w3.org/2002/07/owl#Class> }", labels)

    def test_the_links_between_classes_are_read_without_the_property_as_a_concept(self):
        ontology, _sent = self._load()
        self.assertEqual(set(ontology["concepts"]), {"netex:Line", "netex:Network"})
        self.assertEqual(ontology["concepts"]["netex:Line"]["related_to"], ["netex:Network"])
        self.assertEqual(ontology["concepts"]["netex:Network"]["related_to"], ["netex:Line"])


class PropertyTermsWithoutPropertyConceptsTests(SimpleTestCase):
    def test_a_property_name_still_finds_its_class(self):
        aliases = {"netex:PassengerSpotAllocation": {"passenger spot allocation"}}
        rows = [{"p": NETEX + "seatAllocationMethod", "c": NETEX + "PassengerSpotAllocation"}]
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", aliases), \
                patch.dict("os.environ", {"GRAPHDB_SPARQL_ENDPOINT": ENDPOINT}), \
                patch.object(semantic_graph, "SKIP_GRAPHDB_IMPORT", False), \
                patch.object(property_terms, "_sparql_rows", return_value=rows):
            index = property_terms.PropertyIndex.build(property_terms._load_properties())
            self.assertEqual(index.concepts_for([("seat", "allocation")]), ["netex:PassengerSpotAllocation"])
