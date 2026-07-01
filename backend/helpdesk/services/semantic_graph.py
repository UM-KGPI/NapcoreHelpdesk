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


def _validate_ontology_payload(
    ontology: dict,
    *,
    ontology_name: str,
    required_namespace: str | None = None,
) -> dict:
    """Validate and sanitize loaded ontology payload shape.

    This function enforces a minimal schema and returns a sanitized ontology.
    In non-strict mode callers can catch `ValueError` and fall back.
    """

    if not isinstance(ontology, dict):
        raise ValueError(f"{ontology_name} ontology payload must be a mapping")

    namespaces = ontology.get("namespaces") or {}
    if not isinstance(namespaces, dict):
        raise ValueError(f"{ontology_name} ontology namespaces must be a mapping")
    if required_namespace and required_namespace not in namespaces:
        raise ValueError(
            f"{ontology_name} ontology is missing required namespace '{required_namespace}'"
        )

    concepts = ontology.get("concepts") or {}
    if not isinstance(concepts, dict):
        raise ValueError(f"{ontology_name} ontology concepts must be a mapping")

    sanitized_concepts: dict[str, dict] = {}
    for concept_id, concept_data in concepts.items():
        if not isinstance(concept_id, str):
            logger.warning("Ignoring non-string concept id in %s ontology: %s", ontology_name, concept_id)
            continue
        if not isinstance(concept_data, dict):
            logger.warning("Ignoring malformed concept payload in %s ontology: %s", ontology_name, concept_id)
            continue

        labels = concept_data.get("labels")
        if labels is None:
            labels = []
        if not isinstance(labels, list) or any(not isinstance(item, str) for item in labels):
            logger.warning("Ignoring invalid labels for concept %s in %s ontology", concept_id, ontology_name)
            labels = []

        related_to = concept_data.get("related_to")
        if related_to is None:
            related_to = []
        if not isinstance(related_to, list) or any(not isinstance(item, str) for item in related_to):
            logger.warning("Ignoring invalid related_to for concept %s in %s ontology", concept_id, ontology_name)
            related_to = []

        maps_to_nits = concept_data.get("maps_to_nits")
        if maps_to_nits is not None and not isinstance(maps_to_nits, str):
            logger.warning("Ignoring non-string maps_to_nits for concept %s in %s ontology", concept_id, ontology_name)
            maps_to_nits = None

        maps_to_nch = concept_data.get("maps_to_nch")
        if maps_to_nch is not None and not isinstance(maps_to_nch, str):
            logger.warning("Ignoring non-string maps_to_nch for concept %s in %s ontology", concept_id, ontology_name)
            maps_to_nch = None

        synonym_of = concept_data.get("synonym_of")
        if synonym_of is not None and not isinstance(synonym_of, str):
            logger.warning("Ignoring non-string synonym_of for concept %s in %s ontology", concept_id, ontology_name)
            synonym_of = None

        sanitized = dict(concept_data)
        sanitized["labels"] = labels
        sanitized["related_to"] = related_to
        if maps_to_nits is None:
            sanitized.pop("maps_to_nits", None)
        else:
            sanitized["maps_to_nits"] = maps_to_nits
        if maps_to_nch is None:
            sanitized.pop("maps_to_nch", None)
        else:
            sanitized["maps_to_nch"] = maps_to_nch
        if synonym_of is None:
            sanitized.pop("synonym_of", None)
        else:
            sanitized["synonym_of"] = synonym_of

        sanitized_concepts[concept_id] = sanitized

    sanitized_ontology = dict(ontology)
    sanitized_ontology["namespaces"] = namespaces
    sanitized_ontology["concepts"] = sanitized_concepts
    return sanitized_ontology


def _load_ontology_from_graphdb(endpoint_url: str) -> dict | None:
    """Load concept aliases and NITS mappings from a live GraphDB SPARQL endpoint.

    Returns an ontology dict compatible with _validate_ontology_payload(), or
    None if GraphDB is unreachable or returns no concept data.
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
        "http://www.siri.org.uk/siri/2.1#": "siri",
        "http://www.siri.org.uk/siri/2.1/": "siri",
        "http://napcore.example.org/ontology/siri#": "siri",
        "https://datex.org/ontology/datex#": "datex",
        "http://datex.org/ontology/datex#": "datex",
        "http://napcore.example.org/ontology/datex#": "datex",
        "https://transmodel-cen.eu/6.2/": "transmodel",
        "https://transmodel-cen.eu/6.2#": "transmodel",
        "https://napcore.eu/ontology/nits#": "nits",
        "http://napcore.eu/ontology/nits#": "nits",
        "http://napcore.example.org/ontology/nits#": "nits",
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
            with urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read())
                return [
                    {k: v.get("value", "") for k, v in b.items()}
                    for b in data.get("results", {}).get("bindings", [])
                ]
        except Exception as exc:
            logger.warning("GraphDB ontology load failed: %s", exc)
            return []

    # Labels for standard-specific concepts (netex, opra, siri, datex, transmodel)
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

    # NITS mappings: standard concept → NITS core concept via subClassOf/equivalentClass
    nits_rows = _sparql_get(
        "SELECT DISTINCT ?concept ?nits WHERE {"
        " ?concept <http://www.w3.org/2002/07/owl#equivalentClass>|"
        "<http://www.w3.org/2000/01/rdf-schema#subClassOf>|"
        "^<http://www.w3.org/2002/07/owl#equivalentClass>|"
        "^<http://www.w3.org/2000/01/rdf-schema#subClassOf> ?nits ."
        " FILTER(CONTAINS(STR(?nits), '/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?concept), 'napcore.eu/ontology/nits'))"
        " FILTER(!CONTAINS(STR(?concept), 'www.w3.org'))"
        " }"
    )

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

    concepts: dict[str, dict] = {}
    for row in labels_rows:
        concept_id = _iri_to_concept_id(row.get("concept", ""))
        label = row.get("label", "").strip()
        if not concept_id or not label:
            continue
        entry = concepts.setdefault(concept_id, {"labels": [], "related_to": []})
        if label not in entry["labels"]:
            entry["labels"].append(label)

    # Collect all NITS mappings per concept, then pick the most specific one.
    # Root metaclasses (DomainConcept etc.) are used only when no specific mapping exists.
    _ABSTRACT_NITS_IDS = {
        "nits:DomainConcept",
        "nits:DataArtifact",
        "nits:Process",
        "nits:System",
        "nits:Actor",
    }
    nits_by_concept: dict[str, list[str]] = {}
    for row in nits_rows:
        concept_id = _iri_to_concept_id(row.get("concept", ""))
        nits_id = _iri_to_concept_id(row.get("nits", ""))
        if not concept_id or not nits_id or concept_id not in concepts:
            continue
        nits_by_concept.setdefault(concept_id, []).append(nits_id)

    for concept_id, nits_ids in nits_by_concept.items():
        specific = [n for n in nits_ids if n not in _ABSTRACT_NITS_IDS]
        concepts[concept_id]["maps_to_nits"] = specific[0] if specific else nits_ids[0]

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
        "siri": "http://www.siri.org.uk/siri/2.1",
        "datex": "https://datex.org/ontology/datex",
        "transmodel": "https://transmodel-cen.eu/6.2",
        "nits": "https://napcore.eu/ontology/nits",
    }
    return {"namespaces": namespaces, "concepts": concepts}


def _load_nits_ontology_from_graphdb(endpoint_url: str) -> dict | None:
    """Load NITS concepts and relations from a live GraphDB SPARQL endpoint."""

    import json as _json
    from urllib.parse import quote_plus
    from urllib.request import Request, urlopen

    def _iri_to_nits_concept_id(iri: str) -> str | None:
        if "/ontology/nits" not in iri:
            return None
        if "#" in iri:
            local = iri.rsplit("#", 1)[1]
        else:
            local = iri.rstrip("/").rsplit("/", 1)[-1]
        if not local:
            return None
        return f"nits:{local}"

    def _sparql_get(sparql: str) -> list[dict]:
        url = f"{endpoint_url.rstrip('/')}?query={quote_plus(sparql)}"
        req = Request(url, headers={"Accept": "application/sparql-results+json"})
        try:
            with urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read())
                return [
                    {k: v.get("value", "") for k, v in b.items()}
                    for b in data.get("results", {}).get("bindings", [])
                ]
        except Exception as exc:
            logger.warning("GraphDB NITS ontology load failed: %s", exc)
            return []

    labels_rows = _sparql_get(
        "SELECT ?concept ?label WHERE {"
        " ?concept <http://www.w3.org/2004/02/skos/core#prefLabel>|"
        "<http://www.w3.org/2004/02/skos/core#altLabel>|"
        "<http://www.w3.org/2000/01/rdf-schema#label> ?label ."
        " FILTER(CONTAINS(STR(?concept), '/ontology/nits'))"
        " }"
    )
    related_rows = _sparql_get(
        "SELECT DISTINCT ?concept ?related WHERE {"
        " ?concept <http://www.w3.org/2004/02/skos/core#related>|"
        "<http://www.w3.org/2000/01/rdf-schema#subClassOf>|"
        "<http://www.w3.org/2002/07/owl#equivalentClass> ?related ."
        " FILTER(CONTAINS(STR(?concept), '/ontology/nits'))"
        " FILTER(CONTAINS(STR(?related), '/ontology/nits'))"
        " }"
    )

    concepts: dict[str, dict] = {}

    for row in labels_rows:
        concept_id = _iri_to_nits_concept_id(row.get("concept", ""))
        label = row.get("label", "").strip()
        if not concept_id:
            continue
        entry = concepts.setdefault(concept_id, {"labels": [], "related_to": []})
        if label and label not in entry["labels"]:
            entry["labels"].append(label)

    for row in related_rows:
        concept_id = _iri_to_nits_concept_id(row.get("concept", ""))
        related_id = _iri_to_nits_concept_id(row.get("related", ""))
        if not concept_id or not related_id:
            continue
        entry = concepts.setdefault(concept_id, {"labels": [], "related_to": []})
        if related_id != concept_id and related_id not in entry["related_to"]:
            entry["related_to"].append(related_id)
        concepts.setdefault(related_id, {"labels": [], "related_to": []})

    if not concepts:
        return None

    return {
        "namespaces": {
            "nits": "https://napcore.eu/ontology/nits",
        },
        "concepts": concepts,
    }


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


def _load_nits_ontology() -> dict:
    """Load the dedicated NITS ontology used for cross-standard reasoning from GraphDB."""

    if SKIP_GRAPHDB_IMPORT or not _env_truthy("GRAPHDB_ENABLED", default=False):
        logger.info("Skipping GraphDB NITS import; returning empty ontology for local checks.")
        return {"namespaces": {}, "concepts": {}, "relationships": []}

    endpoint = os.getenv("GRAPHDB_SPARQL_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError(
            "GRAPHDB_SPARQL_ENDPOINT is required. Local NITS-file fallback is disabled."
        )

    graphdb_result = _load_nits_ontology_from_graphdb(endpoint)
    if graphdb_result and graphdb_result.get("concepts"):
        try:
            validated = _validate_ontology_payload(
                graphdb_result,
                ontology_name="nits",
                required_namespace="nits",
            )
            logger.info(
                "Loaded NITS ontology from GraphDB: %d concepts",
                len(validated.get("concepts", {})),
            )
            return validated
        except ValueError:
            raise

    raise RuntimeError(
        f"Failed to load NITS ontology concepts from GraphDB endpoint: {endpoint}"
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


# Load ontologies at module initialization
_ONTOLOGY = _load_ontology()
_NITS_ONTOLOGY = _load_nits_ontology()
GRAPH_CONCEPT_ALIASES = _build_concept_aliases_from_ontology(_ONTOLOGY)

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
    return (concept_id.split(":", 1)[0] if ":" in concept_id else "nits").lower()


def _concept_local_name(concept_id: str) -> str:
    return concept_id.split(":", 1)[1] if ":" in concept_id else concept_id


def _default_nits_concept_id(concept_id: str, concept_data: dict) -> str:
    labels = concept_data.get("labels") or []
    candidate = ""
    if labels:
        candidate = str(labels[0])
    if not candidate:
        local = _concept_local_name(concept_id)
        candidate = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", local)
    tokens = TOKEN_PATTERN.findall((candidate or "").lower())
    if not tokens:
        tokens = TOKEN_PATTERN.findall(_concept_local_name(concept_id).lower())
    slug = "-".join(tokens[:8]) if tokens else "concept"
    return f"nits:{slug}"


def _normalize_nits_target(raw_target: str, *, concept_id: str, field_name: str) -> str | None:
    target = (raw_target or "").strip()
    if not target:
        logger.warning("Ignoring empty %s mapping on concept %s", field_name, concept_id)
        return None

    namespace = _concept_namespace(target)
    local = _concept_local_name(target)
    if namespace not in {"nits", "nch"}:
        logger.warning(
            "Ignoring unsupported %s namespace for concept %s: %s",
            field_name,
            concept_id,
            target,
        )
        return None

    local_tokens = TOKEN_PATTERN.findall(local.lower())
    if not local_tokens:
        logger.warning(
            "Ignoring malformed %s mapping on concept %s: %s",
            field_name,
            concept_id,
            target,
        )
        return None

    return f"nits:{'-'.join(local_tokens[:8])}"


def _build_nits_label_index(nits_ontology: dict) -> dict[tuple[str, ...], str]:
    """Build normalized label token -> nits concept index for exact label alignment."""

    index: dict[tuple[str, ...], str] = {}
    concepts = nits_ontology.get("concepts", {}) if isinstance(nits_ontology, dict) else {}
    if not isinstance(concepts, dict):
        return index

    for nits_id, concept_data in concepts.items():
        if not isinstance(nits_id, str) or _concept_namespace(nits_id) not in {"nits", "nch"}:
            continue
        if not isinstance(concept_data, dict):
            continue

        local = _concept_local_name(nits_id)
        local_tokens = tuple(TOKEN_PATTERN.findall(local.lower()))
        if local_tokens:
            index.setdefault(local_tokens, f"nits:{'-'.join(local_tokens[:8])}")

        for label in concept_data.get("labels") or []:
            if not isinstance(label, str):
                continue
            tokens = tuple(TOKEN_PATTERN.findall(label.lower()))
            if tokens:
                index.setdefault(tokens, f"nits:{'-'.join(local_tokens[:8])}" if local_tokens else nits_id)

    return index


def _infer_nits_mapping_from_labels(concept_id: str, concept_data: dict, nits_label_index: dict[tuple[str, ...], str]) -> str | None:
    """Infer NITS mapping from exact normalized label matches to NITS labels."""

    if not nits_label_index:
        return None

    candidates: list[str] = []
    candidates.extend(label for label in (concept_data.get("labels") or []) if isinstance(label, str))
    candidates.append(_concept_local_name(concept_id))

    for candidate in candidates:
        tokens = tuple(TOKEN_PATTERN.findall(candidate.lower()))
        if not tokens:
            continue
        mapped = nits_label_index.get(tokens)
        if mapped:
            return mapped
    return None


def _build_concept_nits_mapping(ontology: dict, nits_ontology: dict | None = None) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Build concept -> NITS mapping and reverse NITS -> concepts index.

    Resolution order:
    1) explicit `maps_to_nits`
    2) explicit legacy `maps_to_nch`
    3) inherited from `synonym_of`
    4) deterministic fallback generated from label/local name
    """

    concepts = ontology.get("concepts", {})
    resolved: dict[str, str] = {}
    nits_label_index = _build_nits_label_index(nits_ontology or {})

    def _resolve(concept_id: str, visiting: set[str]) -> str:
        if concept_id in resolved:
            return resolved[concept_id]
        concept_data = concepts.get(concept_id, {})
        if _concept_namespace(concept_id) in {"nits", "nch"}:
            local = concept_id.split(":", 1)[1] if ":" in concept_id else concept_id
            resolved[concept_id] = f"nits:{local}"
            return resolved[concept_id]

        explicit = concept_data.get("maps_to_nits")
        if explicit is not None:
            if isinstance(explicit, str):
                target = _normalize_nits_target(explicit, concept_id=concept_id, field_name="maps_to_nits")
                if target:
                    resolved[concept_id] = target
                    return resolved[concept_id]
            else:
                logger.warning("Ignoring non-string maps_to_nits mapping on concept %s", concept_id)

        explicit = concept_data.get("maps_to_nch")
        if explicit is not None:
            if isinstance(explicit, str):
                target = _normalize_nits_target(explicit, concept_id=concept_id, field_name="maps_to_nch")
                if target:
                    resolved[concept_id] = target
                    return resolved[concept_id]
            else:
                logger.warning("Ignoring non-string maps_to_nch mapping on concept %s", concept_id)

        synonym_of = concept_data.get("synonym_of")
        if isinstance(synonym_of, str) and synonym_of in concepts and synonym_of not in visiting:
            mapped = _resolve(synonym_of, visiting | {concept_id})
            resolved[concept_id] = mapped
            return mapped
        if isinstance(synonym_of, str) and synonym_of in visiting:
            logger.warning(
                "Detected synonym cycle while resolving concept %s via %s; using fallback mapping",
                concept_id,
                synonym_of,
            )

        inferred = _infer_nits_mapping_from_labels(concept_id, concept_data, nits_label_index)
        if inferred:
            resolved[concept_id] = inferred
            return inferred

        fallback = _default_nits_concept_id(concept_id, concept_data)
        resolved[concept_id] = fallback
        return fallback

    for concept_id in concepts.keys():
        _resolve(concept_id, set())

    reverse: dict[str, set[str]] = {}
    for concept_id, nits_id in resolved.items():
        reverse.setdefault(nits_id, set()).add(concept_id)
    return resolved, reverse


def _build_nits_relations(nits_ontology: dict) -> dict[str, set[str]]:
    """Build bidirectional relation index from dedicated NITS ontology."""

    relations: dict[str, set[str]] = {}
    concepts = (nits_ontology.get("concepts", {}) or {})
    if not isinstance(concepts, dict):
        logger.warning("NITS ontology concepts payload is not a mapping. Ignoring relations.")
        return relations

    valid_concepts = {
        concept_id
        for concept_id in concepts.keys()
        if isinstance(concept_id, str) and _concept_namespace(concept_id) in {"nits", "nch"}
    }

    for concept_id, concept_data in concepts.items():
        if concept_id not in valid_concepts:
            logger.warning("Ignoring non-NITS concept ID in dedicated ontology: %s", concept_id)
            continue
        if not isinstance(concept_data, dict):
            logger.warning("Ignoring malformed concept payload for %s", concept_id)
            continue

        related = concept_data.get("related_to", []) or []
        if not isinstance(related, list):
            logger.warning("Ignoring non-list related_to for concept %s", concept_id)
            continue

        if concept_id not in relations:
            relations[concept_id] = set()
        for neighbor in related:
            if not isinstance(neighbor, str):
                logger.warning("Ignoring non-string relation target for concept %s", concept_id)
                continue
            if neighbor == concept_id:
                logger.warning("Ignoring self-loop relation on concept %s", concept_id)
                continue
            if neighbor not in valid_concepts:
                logger.warning(
                    "Ignoring relation from %s to unknown/non-NITS concept %s",
                    concept_id,
                    neighbor,
                )
                continue
            relations[concept_id].add(neighbor)
            relations.setdefault(neighbor, set()).add(concept_id)
    return relations


def _expand_nits_concepts(nits_ids: set[str], hops: int = 1) -> set[str]:
    expanded = set(nits_ids)
    frontier = set(nits_ids)
    for _ in range(max(0, hops)):
        next_frontier: set[str] = set()
        for concept_id in frontier:
            for neighbor in NITS_RELATIONS.get(concept_id, set()):
                if neighbor not in expanded:
                    expanded.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
        if not frontier:
            break
    return expanded


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

    if normalized_alias in normalized_text:
        return True

    # Token-subset fallback catches phrase variants like "delayed vehicle journeys"
    # matching alias "delayed journey".
    text_tokens = set(normalized_text.split())
    return bool(alias_tokens) and set(alias_tokens).issubset(text_tokens)


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

    # Cross-standard bridge: concepts mapped to the same NCH node are treated as
    # directly related so one-hop expansion can traverse standard boundaries.
    for aligned_concepts in NITS_TO_CONCEPTS.values():
        if len(aligned_concepts) < 2:
            continue
        sorted_ids = sorted(aligned_concepts)
        for concept_id in sorted_ids:
            relations.setdefault(concept_id, set())
            relations[concept_id].update({other for other in sorted_ids if other != concept_id})

    return relations


# Build NITS bridge indexes from glossary ontology
CONCEPT_TO_NITS, NITS_TO_CONCEPTS = _build_concept_nits_mapping(_ONTOLOGY, _NITS_ONTOLOGY)

# Backward-compatible aliases to avoid breaking external imports/tests.
CONCEPT_TO_NCH = CONCEPT_TO_NITS
NCH_TO_CONCEPTS = NITS_TO_CONCEPTS

# Build relation graph from dedicated NITS ontology
NITS_RELATIONS = _build_nits_relations(_NITS_ONTOLOGY)
NCH_RELATIONS = NITS_RELATIONS

# Build graph relations from ontology
GRAPH_RELATIONS = _build_graph_relations_from_ontology(_ONTOLOGY)


def extract_graph_concepts(text: str) -> set[str]:
    normalized_text = _normalize_for_matching(text)
    concepts: set[str] = set()
    aliases_by_concept = GRAPH_CONCEPT_ALIASES or _FALLBACK_GRAPH_CONCEPT_ALIASES
    for concept_id, aliases in aliases_by_concept.items():
        if any(_alias_matches_text(alias, normalized_text) for alias in aliases):
            concepts.add(concept_id)
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


def get_concept_nits_ids(concept_ids: set[str]) -> set[str]:
    """Return resolved NITS concept IDs for ontology concept IDs."""

    return {
        CONCEPT_TO_NITS[concept_id]
        for concept_id in concept_ids
        if concept_id in CONCEPT_TO_NITS
    }


def get_concept_nch_ids(concept_ids: set[str]) -> set[str]:
    """Backward-compatible alias for older NCH naming."""

    return get_concept_nits_ids(concept_ids)


def expand_graph_concepts(concepts: set[str], hops: int = 1) -> set[str]:
    expanded = set(concepts)

    # Cross-standard phase: glossary -> NITS -> neighboring NITS -> glossary.
    seed_nits_ids = get_concept_nits_ids(expanded)
    expanded_nits_ids = _expand_nits_concepts(seed_nits_ids, hops=hops)
    for nits_id in expanded_nits_ids:
        expanded.update(NITS_TO_CONCEPTS.get(nits_id, set()))

    frontier = set(expanded)
    for _ in range(max(0, hops)):
        next_frontier: set[str] = set()
        for concept_id in frontier:
            for neighbor in GRAPH_RELATIONS.get(concept_id, set()):
                if neighbor not in expanded:
                    expanded.add(neighbor)
                    next_frontier.add(neighbor)

        # Keep NITS-equivalent concepts synchronized as the frontier grows.
        for nits_id in _expand_nits_concepts(get_concept_nits_ids(next_frontier), hops=1):
            for equivalent in NITS_TO_CONCEPTS.get(nits_id, set()):
                if equivalent not in expanded:
                    expanded.add(equivalent)
                    next_frontier.add(equivalent)

        frontier = next_frontier
        if not frontier:
            break
    return expanded


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
