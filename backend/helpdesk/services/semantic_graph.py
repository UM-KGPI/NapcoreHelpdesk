"""
Semantic graph construction and SPARQL pattern matching over ontology data.

Builds in-memory concept graphs from loaded ontology triples and executes
graph traversal queries to find related concepts, hierarchies, and
cross-standard alignments used during answer generation and rule evaluation.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-15  |  Modified: 2026-06-28
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Iterable

from helpdesk.models import SourceChunk

logger = logging.getLogger(__name__)


def _env_truthy(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


STRICT_ONTOLOGY_VALIDATION = _env_truthy("NAPCORE_ONTOLOGY_STRICT_VALIDATION", default=False)
SKIP_GRAPHDB_IMPORT = _env_truthy("NAPCORE_SKIP_GRAPHDB_IMPORT", default=False)


def _load_ontology_from_graphdb(endpoint_url: str) -> dict | None:
    """Load concept aliases from a live GraphDB SPARQL endpoint.

    Returns an ontology dict with namespaces/concepts keys, or None if
    GraphDB is unreachable or returns no concept data.
    """
    import json as _json
    from urllib.parse import quote_plus
    from urllib.request import Request, urlopen

    _IRI_PREFIX_MAP: dict[str, str] = {
        "https://netex.org.uk/netex/2.0#": "netex",
        "https://netex.org.uk/netex/2.0/": "netex",
        "http://napcore.example.org/ontology/netex#": "netex",
        "https://netex.org.uk/netex/2.0#": "netex",
        "https://netex.org.uk/netex/2.0/": "netex",
        "https://napcore.eu/ontology/netex#": "netex",
        "http://napcore.eu/ontology/netex#": "netex",
        "http://napcore.example.org/ontology/netex#": "netex",
        "https://transmodel-cen.eu/opra/1.0#": "opra",
        "https://transmodel-cen.eu/opra/1.0/": "opra",
        "https://napcore.eu/ontology/opra#": "opra",
        "http://napcore.eu/ontology/opra#": "opra",
        "http://napcore.example.org/ontology/opra#": "opra",
        "https://siri.org.uk/siri/1.3#": "siri",
        "https://siri.org.uk/siri/1.3/": "siri",
        "http://napcore.example.org/ontology/siri#": "siri",
        "https://transmodel-cen.eu/6.2/": "transmodel",
        "https://transmodel-cen.eu/6.2#": "transmodel",
    }

    def _iri_to_concept_id(iri: str) -> str | None:
        for prefix_iri, ns in _IRI_PREFIX_MAP.items():
            if iri.startswith(prefix_iri):
                return f"{ns}:{iri[len(prefix_iri):]}"
        return None

    def _sparql_get(sparql: str) -> list[dict]:
        url = f"{endpoint_url.rstrip('/')}?query={quote_plus(sparql)}"
        req = Request(url, headers={"Accept": "application/sparql-results+json"})
        try:
            with urlopen(req, timeout=60) as resp:
                data = _json.loads(resp.read())
                return [
                    {k: v.get("value", "") for k, v in b.items()}
                    for b in data.get("results", {}).get("bindings", [])
                ]
        except Exception as exc:
            logger.warning("GraphDB ontology load failed: %s", exc)
            return []

    # Labels for standard-specific concepts (netex, opra, siri, transmodel)
    labels_rows = _sparql_get(
        "SELECT ?concept ?label WHERE {"
        " ?concept <http://www.w3.org/2004/02/skos/core#prefLabel>|"
        "<http://www.w3.org/2004/02/skos/core#altLabel>|"
        "<http://www.w3.org/2000/01/rdf-schema#label> ?label ."
        " FILTER(!CONTAINS(STR(?concept), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?concept), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?concept), 'purl.org'))"
        " }"
    )
    if not labels_rows:
        return None

    # skos:related links declared directly in standards ontologies (e.g. SIRI ~99 links)
    skos_related_rows = _sparql_get(
        "SELECT DISTINCT ?concept ?related WHERE {"
        " ?concept <http://www.w3.org/2004/02/skos/core#related> ?related ."
        " FILTER(!CONTAINS(STR(?concept), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?concept), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?concept), 'purl.org'))"
        " FILTER(!CONTAINS(STR(?related), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?related), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?related), 'purl.org'))"
        " }"
    )

    # owl:ObjectProperty domain→range links (e.g. OpRa hasTrip, hasLeg, departFrom, …)
    object_property_rows = _sparql_get(
        "SELECT DISTINCT ?concept ?related WHERE {"
        " ?prop a <http://www.w3.org/2002/07/owl#ObjectProperty> ;"
        "       <http://www.w3.org/2000/01/rdf-schema#domain> ?concept ;"
        "       <http://www.w3.org/2000/01/rdf-schema#range> ?related ."
        " FILTER(!CONTAINS(STR(?concept), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?concept), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?concept), 'purl.org'))"
        " FILTER(!CONTAINS(STR(?related), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?related), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?related), 'purl.org'))"
        " }"
    )

    # rdfs:subClassOf links (e.g. netex:ServiceJourney -> netex:Journey). Bridges an
    # abstract/base concept to the concrete subtypes that carry its real properties
    # (ServiceJourney has lineRef, the abstract Journey base class does not), so a
    # question anchored on the abstract concept can still reach them one hop away.
    # Kept directed (class -> subclass, see "narrower" below): followed upward,
    # every class reaches framework roots like netex:DataManagedObject.
    subclass_rows = _sparql_get(
        "SELECT DISTINCT ?concept ?related WHERE {"
        " ?concept <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?related ."
        " FILTER(!CONTAINS(STR(?concept), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?concept), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?concept), 'purl.org'))"
        " FILTER(!CONTAINS(STR(?related), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?related), 'www.w3.org'))"
        " FILTER(!CONTAINS(STR(?related), 'purl.org'))"
        " }"
    )

    concepts: dict[str, dict] = {}
    for row in labels_rows:
        concept_id = _iri_to_concept_id(row.get("concept", ""))
        label = row.get("label", "").strip()
        if not concept_id or not label:
            continue
        entry = concepts.setdefault(concept_id, {"labels": [], "related_to": [], "narrower": []})
        if label not in entry["labels"]:
            entry["labels"].append(label)

    for row in subclass_rows:
        subclass_id = _iri_to_concept_id(row.get("concept", ""))
        superclass_id = _iri_to_concept_id(row.get("related", ""))
        if not subclass_id or not superclass_id or subclass_id == superclass_id:
            continue
        if subclass_id not in concepts or superclass_id not in concepts:
            continue
        narrower = concepts[superclass_id].setdefault("narrower", [])
        if subclass_id not in narrower:
            narrower.append(subclass_id)

    # Populate related_to from skos:related and owl:ObjectProperty domain→range.
    # Both directions are added so graph traversal is bidirectional.
    for row in (*skos_related_rows, *object_property_rows):
        concept_id = _iri_to_concept_id(row.get("concept", ""))
        related_id = _iri_to_concept_id(row.get("related", ""))
        if not concept_id or not related_id or concept_id == related_id:
            continue
        # Only link concepts that are known (appeared in labels query)
        if concept_id not in concepts or related_id not in concepts:
            continue
        related_list = concepts[concept_id].setdefault("related_to", [])
        if related_id not in related_list:
            related_list.append(related_id)
        # Reverse edge
        reverse_list = concepts[related_id].setdefault("related_to", [])
        if concept_id not in reverse_list:
            reverse_list.append(concept_id)

    _total_relations = sum(len(c.get("related_to", [])) for c in concepts.values()) // 2
    if _total_relations:
        logger.info("Loaded %d standards concept relations from GraphDB", _total_relations)

    namespaces = {
        "netex": "https://netex.org.uk/netex/2.0",
        "opra": "https://transmodel-cen.eu/opra/1.0",
        "siri": "https://siri.org.uk/siri/1.3",
        "transmodel": "https://transmodel-cen.eu/6.2",
    }
    return {"namespaces": namespaces, "concepts": concepts}


def _load_ontology() -> dict:
    """Load standards ontology exclusively from GraphDB.

    Returns dict with keys: namespaces, concepts, relationships.
    Raises RuntimeError when GraphDB is not configured or contains no concept
    data. This service intentionally avoids any YAML fallback.
    """
    if SKIP_GRAPHDB_IMPORT or not _env_truthy("GRAPHDB_ENABLED", default=False):
        logger.info("Skipping GraphDB ontology import; returning empty ontology for local checks.")
        return {"namespaces": {}, "concepts": {}, "relationships": []}

    endpoint = os.getenv("GRAPHDB_SPARQL_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError(
            "GRAPHDB_SPARQL_ENDPOINT is required. Local glossary-file fallback is disabled."
        )

    graphdb_result = _load_ontology_from_graphdb(endpoint)
    if graphdb_result and graphdb_result.get("concepts"):
        logger.info(
            "Loaded standards ontology from GraphDB: %d concepts",
            len(graphdb_result["concepts"]),
        )
        return graphdb_result

    raise RuntimeError(
        f"Failed to load standards ontology concepts from GraphDB endpoint: {endpoint}"
    )


def _build_concept_aliases_from_ontology(ontology: dict) -> dict[str, set[str]]:
    """Build GRAPH_CONCEPT_ALIASES from ontology concept labels.

    Converts concept IDs (with colons as is from YAML keys) to sets of labels.
    """
    aliases = {}
    concepts = ontology.get("concepts", {})
    for concept_id, concept_data in concepts.items():
        labels = concept_data.get("labels", [])
        if labels:
            aliases[concept_id] = set(labels)
    return aliases


_TRANSMODEL_ALIGN_ENTRY_PATTERN = re.compile(
    r"^(?P<std>[a-z]+):(?P<local>[A-Za-z0-9_]+)\s*\n\s*skos:exactMatch\s+tm:(?P<tm_class>[A-Z0-9_]+)\s*;",
    re.MULTILINE,
)


def _parse_transmodel_alignment_file(path: Path) -> dict[str, str]:
    """Parse one generated transmodel-<standard>-align.ttl file.

    Returns {"<standard>:<Class>": "transmodel:<TM_CLASS>"} for every
    skos:exactMatch entry. Pure text parsing (no rdflib dependency, no
    GraphDB) so this loads in every environment, GraphDB-enabled or not.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("Transmodel alignment file not found: %s", path)
        return {}

    mapping: dict[str, str] = {}
    for match in _TRANSMODEL_ALIGN_ENTRY_PATTERN.finditer(content):
        concept_id = f"{match.group('std')}:{match.group('local')}"
        mapping[concept_id] = f"transmodel:{match.group('tm_class')}"
    return mapping


def _load_transmodel_pivot_from_static_files() -> tuple[dict[str, str], dict[str, set[str]]]:
    """Build the Transmodel cross-standard pivot from the committed alignment TTLs.

    Standard concepts that share a direct skos:exactMatch to the same
    Transmodel class are treated as siblings. Sourced entirely from
    docs/ontology/alignments/transmodel-{netex,siri,opra}-align.ttl, which
    build_transmodel_alignment.py generates offline from the standards' own
    TTLs and never touches GraphDB -- so this pivot has no GraphDB-
    availability dependency at all and cannot go silently empty because
    GraphDB happened to be unreachable when this worker process started.
    """
    ontology_dir = Path(__file__).resolve().parents[3] / "docs" / "ontology" / "alignments"
    concept_to_transmodel: dict[str, str] = {}
    for standard in ("netex", "siri", "opra"):
        align_path = ontology_dir / f"transmodel-{standard}-align.ttl"
        concept_to_transmodel.update(_parse_transmodel_alignment_file(align_path))

    transmodel_to_concepts: dict[str, set[str]] = {}
    for concept_id, tm_id in concept_to_transmodel.items():
        transmodel_to_concepts.setdefault(tm_id, set()).add(concept_id)

    return concept_to_transmodel, transmodel_to_concepts


# Load ontologies at module initialization
_ONTOLOGY = _load_ontology()
GRAPH_CONCEPT_ALIASES = _build_concept_aliases_from_ontology(_ONTOLOGY)

# Static, GraphDB-independent cross-standard pivot (see docstring above).
CONCEPT_TO_TRANSMODEL, TRANSMODEL_TO_CONCEPTS = _load_transmodel_pivot_from_static_files()

_FALLBACK_GRAPH_CONCEPT_ALIASES = {
    "opra:DelayedJourney": {"delayed journey", "delayed journeys"},
    "opra:DelayStatistics": {"delay statistics", "delaystatistics", "delayed journey statistics"},
    "opra:LateDatedVehicleJourneyEntry": {
        "latedatedvehiclejourneyentry",
        "late dated vehicle journey entry",
        "late dated vehicle journey",
    },
    "netex:VehicleJourney": {"vehicle journey"},
    "netex:ScheduledStopPoint": {"scheduled stop point"},
    "netex:StopPlace": {"stop place"},
    "netex:ServiceJourneyPattern": {"service journey pattern"},
}


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _concept_namespace(concept_id: str) -> str:
    return (concept_id.split(":", 1)[0] if ":" in concept_id else "unknown").lower()




def _normalize_for_matching(text: str) -> str:
    """Lowercase and collapse non-alphanumeric runs for tolerant alias matching."""

    tokens = TOKEN_PATTERN.findall((text or "").lower())
    return " ".join(tokens)


def _alias_matches_text(alias: str, normalized_text: str) -> bool:
    normalized_alias = _normalize_for_matching(alias)
    if not normalized_alias:
        return False

    alias_tokens = normalized_alias.split()

    # 1-2 char labels (e.g. transmodel:a label="a", transmodel:in label="in") are
    # too short to be semantically distinctive and produce false positives by
    # matching common English articles/prepositions in any question text.
    if len(alias_tokens) == 1 and len(normalized_alias) <= 2:
        return False

    # Single-token aliases must appear as complete words to avoid false substring matches.
    # "line" must not match "linetype"; "siri" must not match "expiry"; "when" must not
    # match "whenever".  The token-subset fallback below already handles multi-token
    # aliases like "type of line", so this guard only fires for single-token ones.
    if len(alias_tokens) == 1:
        return normalized_alias in set(normalized_text.split())

    # Multi-token aliases match by token subset, not substring: a raw substring check
    # (`normalized_alias in normalized_text`) would also match across a word boundary
    # it shouldn't -- e.g. alias "is on" is a substring of "what is onwardcall" (the
    # end of "is" plus the start of "onwardcall"), even though "on" is never a real
    # token in that text. The subset check already catches every genuine match a
    # substring check would (every word in the alias has to appear as its own token
    # somewhere in the text), including scattered phrase variants like "delayed
    # vehicle journeys" matching alias "delayed journey", without that false-positive
    # class.
    text_tokens = set(normalized_text.split())
    if set(alias_tokens).issubset(text_tokens):
        return True

    # A PascalCase class name typed with no internal space (e.g. "OnwardCall" for
    # alias "onward call") lowercases to one glued token ("onwardcall") with no
    # separator left to split on, so the subset check above can't see it. Checking
    # whether the alias's words concatenated form a single existing text token
    # covers this generally, for every multi-word alias, without touching how the
    # question text itself is tokenized -- unlike splitting camelCase in the text,
    # which would also wrongly split standard names like "NeTEx" into "Ne"/"TEx".
    return "".join(alias_tokens) in text_tokens


# A question word stands for a longer model word when the model word only adds
# a short prefix: "charging" for "recharging", "booking" for "prebooking". The
# word must be long enough to be distinctive, so "line" never matches "deadline".
_MIN_PREFIXED_WORD = 5
_MAX_MODEL_PREFIX = 3


def _word_variant_kind(model_word: str, question_word: str) -> str | None:
    """'exact' for the same word or a plural of it, 'prefixed' when the model
    word is the question word with a short prefix, otherwise None."""
    if model_word == question_word:
        return "exact"
    for left, right in ((model_word, question_word), (question_word, model_word)):
        if len(left) >= 3 and right in (left + "s", left + "es"):
            return "exact"
    for word in {question_word, question_word[:-1] if question_word.endswith("s") else question_word}:
        extra = len(model_word) - len(word)
        if len(word) >= _MIN_PREFIXED_WORD and 0 < extra <= _MAX_MODEL_PREFIX and model_word.endswith(word):
            return "prefixed"
    return None


def _is_class_concept(concept_id: str) -> bool:
    """Classes are named in PascalCase (netex:RechargingStation) or upper case
    (transmodel:RECHARGING_STATION); associations start lower case (transmodel:relatesTo)."""
    local = concept_id.split(":", 1)[-1]
    return bool(local) and local[0].isupper()


def _alias_matches_question(alias: str, normalized_text: str) -> bool:
    """Alias match for a user's question, tolerant of everyday wording.

    Besides the strict match used for indexing (_alias_matches_text), each word of
    a multi-word label may appear in the question as a plural or without a short
    prefix ("charging stations" for the label "recharging station"). At least one
    label word must appear as itself or its plural, so a label is never reached
    through prefix-stripped words alone."""
    if _alias_matches_text(alias, normalized_text):
        return True
    alias_tokens = _normalize_for_matching(alias).split()
    if len(alias_tokens) < 2:
        return False
    text_tokens = set(normalized_text.split())
    kinds = []
    for alias_token in alias_tokens:
        token_kinds = {_word_variant_kind(alias_token, text_token) for text_token in text_tokens} - {None}
        if not token_kinds:
            return False
        kinds.append("exact" if "exact" in token_kinds else "prefixed")
    return "exact" in kinds


def _build_graph_relations_from_ontology(ontology: dict) -> dict[str, set[str]]:
    """Build GRAPH_RELATIONS from ontology concept relationships.

    Creates bidirectional edges: if A.related_to includes B, then:
    - A -> B (explicit relationship)
    - B -> A (implicit reverse relationship)
    """
    relations = {}
    concepts = ontology.get("concepts", {})

    for concept_id, concept_data in concepts.items():
        related = concept_data.get("related_to", [])
        if related:
            if concept_id not in relations:
                relations[concept_id] = set()
            relations[concept_id].update(related)

    # Add reverse relationships (bidirectional)
    for concept_id, related_set in list(relations.items()):
        for related_concept in related_set:
            if related_concept not in relations:
                relations[related_concept] = set()
            relations[related_concept].add(concept_id)

    # Class -> subclass only, added after the reverse pass so it stays one-way:
    # an abstract concept reaches its concrete subtypes, but a subtype never
    # climbs to framework roots (netex:DataManagedObject has 92 subclasses).
    for concept_id, concept_data in concepts.items():
        narrower = concept_data.get("narrower", [])
        if narrower:
            relations.setdefault(concept_id, set()).update(narrower)

    # Cross-standard bridge: concepts mapped to the same Transmodel class are
    # treated as directly related so one-hop expansion can traverse standard
    # boundaries. See expand_graph_concepts for the matching pivot phase.
    for aligned_concepts in TRANSMODEL_TO_CONCEPTS.values():
        if len(aligned_concepts) < 2:
            continue
        sorted_ids = sorted(aligned_concepts)
        for concept_id in sorted_ids:
            relations.setdefault(concept_id, set())
            relations[concept_id].update({other for other in sorted_ids if other != concept_id})

    return relations


# Build graph relations from ontology
GRAPH_RELATIONS = _build_graph_relations_from_ontology(_ONTOLOGY)


def extract_graph_concepts(text: str, *, word_variants: bool = False) -> set[str]:
    """Concepts whose labels occur in the text.

    word_variants is for a user's question: class labels then also match plurals
    and words without a short prefix (see _alias_matches_question). Indexed chunk
    text keeps the strict match."""
    normalized_text = _normalize_for_matching(text)
    concepts: set[str] = set()
    for concept_id, aliases in (GRAPH_CONCEPT_ALIASES or _FALLBACK_GRAPH_CONCEPT_ALIASES).items():
        # Word variants are for class names only. Association labels such as
        # "relates to" or "used as" are verb phrases, and their verb forms would
        # match ordinary question wording.
        loose = word_variants and _is_class_concept(concept_id)
        matches = _alias_matches_question if loose else _alias_matches_text
        if any(matches(alias, normalized_text) for alias in aliases):
            concepts.add(concept_id)
    return concepts


def concepts_named_by_terms(terms: list[str]) -> set[str]:
    """Class concepts named by model terms, such as the terms an LLM gives for a
    question's everyday wording. Each term counts only for the class labels it
    matches with the most words, so "SCHEDULED STOP POINT" yields the scheduled
    stop point and not every concept labelled "point". A term that matches no
    label (an invented name) yields nothing."""
    concepts: set[str] = set()
    aliases_by_concept = GRAPH_CONCEPT_ALIASES or _FALLBACK_GRAPH_CONCEPT_ALIASES
    for term in terms:
        normalized_term = _normalize_for_matching(term)
        if not normalized_term:
            continue
        best_length, best = 0, set()
        for concept_id, aliases in aliases_by_concept.items():
            if not _is_class_concept(concept_id):
                continue
            for alias in aliases:
                length = len(_normalize_for_matching(alias).split())
                if length < best_length or not _alias_matches_question(alias, normalized_term):
                    continue
                if length > best_length:
                    best_length, best = length, set()
                best.add(concept_id)
        concepts |= best
    return concepts


def get_concept_canonical_terms(concept_ids: set[str]) -> list[str]:
    """Return the most representative phrase label for each concept ID.

    Picks the longest alias as the most specific canonical term for each
    concept.  Used to augment query text before embedding so the embedding
    space sees domain vocabulary aligned with indexed document language.
    """
    terms: list[str] = []
    for concept_id in sorted(concept_ids):  # sorted for determinism
        aliases = GRAPH_CONCEPT_ALIASES.get(concept_id, set())
        if aliases:
            terms.append(max(aliases, key=len))
    return terms


def get_concept_transmodel_ids(concept_ids: set[str]) -> set[str]:
    """Return resolved Transmodel concept IDs for ontology concept IDs.

    Looks up CONCEPT_TO_TRANSMODEL, which has no GraphDB dependency (see
    _load_transmodel_pivot_from_static_files).
    """

    return {
        CONCEPT_TO_TRANSMODEL[concept_id]
        for concept_id in concept_ids
        if concept_id in CONCEPT_TO_TRANSMODEL
    }


def _expand_transmodel_concepts(transmodel_ids: set[str]) -> set[str]:
    """Return the sibling glossary concepts sharing each given Transmodel ID.

    No multi-hop needed here: the alignment files only record direct
    skos:exactMatch pairs, not a Transmodel-internal relation graph, so a
    sibling group is already the full pivot in one step.
    """
    expanded: set[str] = set()
    for transmodel_id in transmodel_ids:
        expanded.update(TRANSMODEL_TO_CONCEPTS.get(transmodel_id, set()))
    return expanded


def expand_graph_concepts_with_distance(concepts: set[str], hops: int = 1) -> dict[str, int]:
    """Like expand_graph_concepts, but also returns each concept's hop distance
    from the seed set (0 for the seeds). Lets a caller truncate an oversized
    expansion by keeping the closest concepts first, instead of an arbitrary
    tiebreak (e.g. alphabetical) that lets unrelated far concepts crowd out
    relevant near ones whenever a seed has many direct neighbors.
    """
    distances: dict[str, int] = {concept_id: 0 for concept_id in concepts}

    for equivalent in _expand_transmodel_concepts(get_concept_transmodel_ids(set(distances))):
        distances.setdefault(equivalent, 0)

    frontier = set(distances)
    for hop in range(1, max(0, hops) + 1):
        next_frontier: set[str] = set()
        for concept_id in frontier:
            for neighbor in GRAPH_RELATIONS.get(concept_id, set()):
                if neighbor not in distances:
                    distances[neighbor] = hop
                    next_frontier.add(neighbor)

        # Keep Transmodel-equivalent concepts synchronized as the frontier grows.
        for equivalent in _expand_transmodel_concepts(get_concept_transmodel_ids(next_frontier)):
            if equivalent not in distances:
                distances[equivalent] = hop
                next_frontier.add(equivalent)

        frontier = next_frontier
        if not frontier:
            break
    return distances


def expand_graph_concepts(concepts: set[str], hops: int = 1) -> set[str]:
    return set(expand_graph_concepts_with_distance(concepts, hops=hops))


def build_semantic_graph_snapshot(chunks: Iterable[SourceChunk]) -> dict:
    repository_nodes: dict[str, dict] = {}
    document_nodes: dict[str, dict] = {}
    concept_nodes: dict[str, dict] = {}
    chunk_nodes: dict[str, dict] = {}
    repository_document_edges: list[dict] = []
    document_chunk_edges: list[dict] = []
    mention_edges: list[dict] = []

    for chunk in chunks:
        chunk_text = "\n".join(
            [chunk.text, chunk.source_path, chunk.label, getattr(chunk, "heading", "") or ""]
        )
        concepts = extract_graph_concepts(chunk_text)
        if not concepts:
            continue

        repository_key = hashlib.sha1(chunk.repository_url.encode("utf-8")).hexdigest()[:16]
        repository_id = f"repository:{repository_key}"
        document_key = hashlib.sha1(
            f"{chunk.repository_url}|{chunk.source_path}".encode("utf-8")
        ).hexdigest()[:20]
        document_id = f"document:{document_key}"

        repository_name = chunk.repository_url.rstrip("/").split("/")[-1] if chunk.repository_url else ""
        repository_nodes[repository_id] = {
            "id": repository_id,
            "type": "Repository",
            "repositoryUrl": chunk.repository_url,
            "name": repository_name,
        }
        document_nodes[document_id] = {
            "id": document_id,
            "type": "Document",
            "documentId": document_key,
            "repositoryUrl": chunk.repository_url,
            "sourcePath": chunk.source_path,
            "commitSha": chunk.commit_sha,
            "docType": getattr(chunk, "doc_type", "") or "",
        }

        chunk_nodes[chunk.chunk_id] = {
            "id": f"chunk:{chunk.chunk_id}",
            "type": "Chunk",
            "chunkId": chunk.chunk_id,
            "repositoryUrl": chunk.repository_url,
            "sourcePath": chunk.source_path,
            "commitSha": chunk.commit_sha,
            "qualityScore": float(chunk.quality_score),
            "standardsScope": chunk.standards_scope or [],
            "docType": getattr(chunk, "doc_type", "") or "",
        }

        repository_document_edges.append(
            {
                "type": "CONTAINS_DOCUMENT",
                "from": repository_id,
                "to": document_id,
            }
        )
        document_chunk_edges.append(
            {
                "type": "HAS_CHUNK",
                "from": document_id,
                "to": f"chunk:{chunk.chunk_id}",
            }
        )

        for concept_id in sorted(concepts):
            concept_nodes[concept_id] = {
                "id": f"concept:{concept_id}",
                "type": "Concept",
                "conceptId": concept_id,
                "namespace": _concept_namespace(concept_id),
            }
            mention_edges.append(
                {
                    "type": "MENTIONS_CONCEPT",
                    "from": f"chunk:{chunk.chunk_id}",
                    "to": f"concept:{concept_id}",
                    "sourceUrl": chunk.repository_url,
                    "sourcePath": chunk.source_path,
                    "commitSha": chunk.commit_sha,
                }
            )

    related_edges: list[dict] = []
    for source_concept, neighbors in GRAPH_RELATIONS.items():
        if source_concept not in concept_nodes:
            continue
        for target_concept in sorted(neighbors):
            if target_concept not in concept_nodes:
                continue
            related_edges.append(
                {
                    "type": "RELATED_TO",
                    "from": f"concept:{source_concept}",
                    "to": f"concept:{target_concept}",
                    "relationType": "semantic-proximity",
                }
            )

    return {
        "nodes": [
            *repository_nodes.values(),
            *document_nodes.values(),
            *concept_nodes.values(),
            *chunk_nodes.values(),
        ],
        "edges": [
            *repository_document_edges,
            *document_chunk_edges,
            *mention_edges,
            *related_edges,
        ],
        "stats": {
            "repositoryNodeCount": len(repository_nodes),
            "documentNodeCount": len(document_nodes),
            "conceptNodeCount": len(concept_nodes),
            "chunkNodeCount": len(chunk_nodes),
            "repositoryDocumentEdgeCount": len(repository_document_edges),
            "documentChunkEdgeCount": len(document_chunk_edges),
            "mentionEdgeCount": len(mention_edges),
            "relatedEdgeCount": len(related_edges),
        },
    }
