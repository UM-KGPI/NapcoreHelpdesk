"""The classes that own a property the question names.

Concept matching (semantic_graph.extract_graph_concepts) sees only class labels. "What is NeTEx
telling us about seat allocation in public transport vehicle?" matched only the context word
"vehicle" (netex:Vehicle): no class is labelled "seat allocation", so the retrieval graph boosted
vehicle chunks over the seat-allocation evidence (prod question 653, 2026-11-07). The words are a
property name all the same: netex:PassengerSpotAllocation and netex:VehicleJourneySpotAllocation
have the property seatAllocationMethod.

The index maps each pair of adjacent words in a property name (seatAllocationMethod: "seat
allocation", "allocation method") to the classes that are the property's rdfs:domain, all read
from the generated ontologies (no hand-made aliases). A pair of adjacent question words that no
matched label covers, found in the index, adds those classes to the question's concepts.

Single words and free definition text were tried first and dropped: on the retrieval benchmark,
words such as "records", "schema" or "planned" each found some class and pulled questions towards
it (English hit@5 0.837 -> 0.782). A two-word property name is model vocabulary; one word is not.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from helpdesk.services import semantic_graph

logger = logging.getLogger(__name__)

MAX_PROPERTY_CONCEPTS = 3
# A word pair in more classes' property names than this ("start time", "type of") names no topic.
MAX_CLASSES_PER_PAIR = 8

_RDFS_DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"

# English function words and question wording. General; nothing here is about one standard or question.
_STOP_WORDS = frozenset(
    """
    a about above after again against all also am an and another any are as at be because been before
    being below between both but by can cannot could did do does doing done down during each either else
    etc every few for from further given had has have having he her here hers him his how however if in
    into is it its itself just least less like may me might more most much must my neither no nor not of
    off on once one only or other otherwise our out over own per rather same shall she should since so
    some such than that the their them then there these they this those though through thus to too two
    under until up upon us used using very via was we were what when where whether which while who whom
    whose why will with within without would yes yet you your
    many kind kinds type types way ways thing things something anything everything
    tell telling told say says said show shows shown give gives explain explains describe describes
    described description define defines defined definition definitions mean means meaning
    example examples sample samples model models modelled modeled represent represents represented
    standard standards specification specifications schema schemas element elements field fields
    please need needs want wants know help use uses
    """.split()
)
_STANDARD_NAMES = frozenset(
    {"netex", "siri", "opra", "transmodel", "datex", "gtfs", "napcore", "mobilitydcat", "dcat", "inspire", "tnit", "tnits"}
)
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _stem(word: str) -> str:
    """Plural to singular, enough to join "seats" and "seat" ("categories" -> "category")."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("sses", "xes", "ches", "shes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def text_words(text: str) -> list[str]:
    """Content words of a question in order, stemmed. No camel-case split, so "NeTEx" stays one word."""
    words = []
    for word in re.findall(r"[a-z][a-z0-9]*", (text or "").lower()):
        if word in _STOP_WORDS or word in _STANDARD_NAMES or len(word) < 3:
            continue
        words.append(_stem(word))
    return words


def name_words(name: str) -> list[str]:
    """Content words of a property name: seatAllocationMethod_PassengerSpotAllocation -> seat, allocation, method."""
    local = (name or "").split(":", 1)[-1].split("_", 1)[0]
    return text_words(_CAMEL_BOUNDARY.sub(" ", local))


def word_pairs(words: list[str]) -> list[tuple[str, str]]:
    return list(zip(words, words[1:]))


@dataclass
class PropertyIndex:
    """Adjacent word pairs of property names, each with the classes that own such a property."""

    classes_by_pair: dict[tuple[str, str], set[str]] = field(default_factory=dict)

    @classmethod
    def build(cls, properties: list[tuple[str, str]]) -> "PropertyIndex":
        """properties: (property concept, class concept that is its rdfs:domain)."""
        classes_by_pair: dict[tuple[str, str], set[str]] = {}
        for property_id, class_id in properties:
            for pair in word_pairs(name_words(property_id)):
                classes_by_pair.setdefault(pair, set()).add(class_id)
        return cls(classes_by_pair=classes_by_pair)

    def concepts_for(self, pairs: list[tuple[str, str]], scope: list[str] | None = None, limit: int = MAX_PROPERTY_CONCEPTS) -> list[str]:
        """Owning classes of the question's word pairs that also have a word of the pair in their own
        name, rarest pair first: "seat allocation" (seatAllocationMethod) gives PassengerSpotAllocation.
        A class that only owns the property is left out, as the property is one detail of it: Reserving
        for "seat allocation", Parking for "real time" (realTimeOccupancy)."""
        ranked: list[tuple[int, str]] = []
        for pair in dict.fromkeys(pairs):
            owners = {c for c in self.classes_by_pair.get(pair, set()) if semantic_graph.concept_in_scope(c, scope)}
            if not owners or len(owners) > MAX_CLASSES_PER_PAIR:
                continue
            ranked.extend((len(owners), class_id) for class_id in owners if set(name_words(class_id)) & set(pair))
        ranked.sort()
        return list(dict.fromkeys(class_id for _, class_id in ranked))[:limit]


_index: PropertyIndex | None = None
_index_read_at = object()
_lock = threading.Lock()


def _sparql_rows(endpoint: str, sparql: str) -> list[dict]:
    request = Request(f"{endpoint.rstrip('/')}?query={quote_plus(sparql)}", headers={"Accept": "application/sparql-results+json"})
    with urlopen(request, timeout=120) as response:
        data = json.loads(response.read())
    return [{key: value.get("value", "") for key, value in row.items()} for row in data.get("results", {}).get("bindings", [])]


def _load_properties() -> list[tuple[str, str]]:
    endpoint = os.getenv("GRAPHDB_SPARQL_ENDPOINT", "").strip()
    if not endpoint or semantic_graph.SKIP_GRAPHDB_IMPORT:
        return []
    classes = {concept_id for concept_id in semantic_graph.GRAPH_CONCEPT_ALIASES if semantic_graph._is_class_concept(concept_id)}
    properties = []
    for row in _sparql_rows(endpoint, f"SELECT DISTINCT ?p ?c WHERE {{ ?p <{_RDFS_DOMAIN}> ?c }}"):
        property_id = semantic_graph.iri_to_concept_id(row.get("p", ""))
        class_id = semantic_graph.iri_to_concept_id(row.get("c", ""))
        if property_id and class_id in classes:
            properties.append((property_id, class_id))
    return properties


def property_index() -> PropertyIndex:
    """The index, built on first use and again after the ontology labels were re-read."""
    global _index, _index_read_at
    read_at = semantic_graph._ONTOLOGY_READ_AT
    if _index is not None and _index_read_at == read_at:
        return _index
    with _lock:
        if _index is None or _index_read_at != read_at:
            try:
                _index = PropertyIndex.build(_load_properties())
                logger.info("Property term index: %d word pairs", len(_index.classes_by_pair))
            except Exception:  # keep retrieval working without it
                logger.warning("Building the property term index failed", exc_info=True)
                _index = _index or PropertyIndex()
            _index_read_at = read_at
    return _index


def question_property_concepts(question: str, label_concepts: set[str], scope: list[str] | None = None) -> set[str]:
    """Classes owning a property named by two adjacent question words that no matched label covers."""
    covered: set[str] = set()
    for concept_id in label_concepts:
        for alias in semantic_graph.GRAPH_CONCEPT_ALIASES.get(concept_id, ()):
            covered.update(text_words(alias))
    pairs = [pair for pair in word_pairs(text_words(question)) if not set(pair) & covered]
    return set(property_index().concepts_for(pairs, scope=scope)) - set(label_concepts)
