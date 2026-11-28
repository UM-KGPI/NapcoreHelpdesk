"""DATEX II as an ontology source: the registry and the loader know its graph, its IRIs resolve to concept ids,
a DATEX concept is found in a question and, like those of NeTEx, SIRI and OpRa, is used for boosting. No network."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import rdflib
from django.test import SimpleTestCase

from helpdesk.management.commands.build_datex_ontology import DATEX_NAMESPACE
from helpdesk.services import graphdb_client, ontology_registry, semantic_graph

DATEX_GRAPH = "https://napcore.eu/graph/standards/datex"
TTL = Path(__file__).resolve().parents[3] / "docs" / "ontology" / "standards" / "datex.ttl"


def _datex_ontology() -> dict:
    """The concepts the loader's label query would read from the committed Turtle file."""
    graph = rdflib.Graph()
    graph.parse(str(TTL), format="turtle")
    concepts: dict[str, dict] = {}
    for predicate in (
        rdflib.URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"),
        rdflib.URIRef("http://www.w3.org/2004/02/skos/core#altLabel"),
        rdflib.RDFS.label,
    ):
        for subject, label in graph.subject_objects(predicate):
            concept_id = semantic_graph.iri_to_concept_id(str(subject))
            if concept_id:
                entry = concepts.setdefault(concept_id, {"labels": [], "related_to": [], "narrower": []})
                if str(label) not in entry["labels"]:
                    entry["labels"].append(str(label))
    return {"namespaces": {}, "concepts": concepts}


class DatexRegistryTests(SimpleTestCase):
    def test_default_plan_loads_datex_as_its_own_named_graph(self):
        plan = graphdb_client.plan_default_ontology_graphs(replace=False)
        entry = next(item for item in plan["graphs"] if item["ontologyKey"] == "datex")
        self.assertEqual(entry["graphUri"], DATEX_GRAPH)
        self.assertEqual(entry["filePath"].name, "datex.ttl")
        self.assertTrue(entry["fileExists"])
        graph_uris = [item["graphUri"] for item in plan["graphs"]]
        self.assertEqual(graph_uris.count(DATEX_GRAPH), 1)

    def test_only_limits_the_plan_and_deletes_no_retired_graph(self):
        plan = graphdb_client.plan_default_ontology_graphs(replace=True, only={"datex"})
        self.assertEqual([item["ontologyKey"] for item in plan["graphs"]], ["datex"])
        self.assertEqual(plan["retired"], [])

    def test_only_rejects_an_unknown_key(self):
        with self.assertRaises(ValueError):
            graphdb_client.plan_default_ontology_graphs(only={"datxe"})

    def test_registry_tracks_the_file_by_hash_and_version(self):
        items = {item["ontology_key"]: item for item in ontology_registry.collect_ontology_asset_versions()}
        self.assertEqual(items["datex"]["graph_uri"], DATEX_GRAPH)
        self.assertEqual(items["datex"]["version"], "v3.7")

    def test_the_file_is_the_generator_output_header_and_all(self):
        self.assertIn("do not edit", TTL.read_text(encoding="utf-8").splitlines()[0])


class DatexConceptTests(SimpleTestCase):
    def test_iri_resolves_to_a_namespace_qualified_concept_id(self):
        self.assertEqual(
            semantic_graph.iri_to_concept_id(DATEX_NAMESPACE + "Situation.Accident"), "datex:Situation.Accident"
        )
        self.assertEqual(graphdb_client._to_iri("datex:Situation.Accident"), DATEX_NAMESPACE + "Situation.Accident")

    def test_a_datex_concept_is_extracted_from_a_question_in_any_scope(self):
        aliases = semantic_graph._build_concept_aliases_from_ontology(_datex_ontology())
        question = "How do I describe an accident in DATEX II?"
        with mock.patch.dict(semantic_graph.GRAPH_CONCEPT_ALIASES, aliases, clear=True):
            semantic_graph._TEXT_CONCEPT_CACHE.clear()
            for scope in (["DATEX II"], ["NeTEx"], None):
                found = semantic_graph.extract_graph_concepts(question, word_variants=True, scope=scope)
                self.assertIn("datex:Situation.Accident", found, scope)
        semantic_graph._TEXT_CONCEPT_CACHE.clear()

    def test_datex_is_a_first_class_source_not_an_opt_in_one(self):
        # Like NeTEx, SIRI and OpRa: its concepts count for the boost and the expansion the gateway builds with
        # concepts_in_scope(question_concepts, None); TN-ITS stays the opt-in source.
        self.assertNotIn("datex", semantic_graph.OPT_IN_CONCEPT_SOURCES)
        concepts = {"datex:Situation.Accident", "netex:StopPlace", "tnits:Dataset"}
        self.assertEqual(
            semantic_graph.concepts_in_scope(concepts, None), {"datex:Situation.Accident", "netex:StopPlace"}
        )
        self.assertEqual(semantic_graph.concepts_in_scope(concepts, ["NeTEx"]), {"datex:Situation.Accident", "netex:StopPlace"})
