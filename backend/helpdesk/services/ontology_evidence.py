"""
Retrieve semantic definitions and properties from ontology for concept queries.

Extracts skos:definition, rdfs:label, and other semantic properties from GraphDB
ontologies to provide authoritative definitions for schema concepts.

Created: 2026-07-01
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def retrieve_concept_definitions(
    concept_ids: set[str],
    endpoint: str,
    repository: str,
    timeout_seconds: int = 3,
    username: str = "",
    password: str = "",
) -> list[dict]:
    """Retrieve semantic definitions for concepts from ontology.

    Args:
        concept_ids: Set of concept URIs (e.g., {"netex:ServiceJourney"})
        endpoint: GraphDB SPARQL endpoint URL
        repository: Repository name
        timeout_seconds: Query timeout
        username: GraphDB username
        password: GraphDB password

    Returns:
        List of definition dicts with concept metadata
    """
    if not concept_ids:
        return []

    try:
        from helpdesk.services.graphdb_client import execute_sparql_query

        concept_uris = " ".join(
            [f"<{_ensure_uri(cid)}>" for cid in sorted(concept_ids)]
        )

        sparql_query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT ?concept ?definition ?prefLabel ?altLabel ?type
        WHERE {{
          VALUES ?concept {{ {concept_uris} }}
          ?concept a ?type .
          OPTIONAL {{ ?concept skos:definition ?definition . }}
          OPTIONAL {{ ?concept skos:prefLabel ?prefLabel . }}
          OPTIONAL {{ ?concept skos:altLabel ?altLabel . }}
        }}
        ORDER BY ?concept
        LIMIT 50
        """

        results = execute_sparql_query(
            sparql_query=sparql_query,
            endpoint=endpoint,
            repository=repository,
            timeout_seconds=timeout_seconds,
            username=username,
            password=password,
        )

        if not results:
            return []

        # Group results by concept
        concepts_data = {}
        for binding in results.get("results", {}).get("bindings", []):
            concept = binding.get("concept", {}).get("value", "")
            if not concept:
                continue

            if concept not in concepts_data:
                concepts_data[concept] = {
                    "concept": concept,
                    "type": binding.get("type", {}).get("value", ""),
                    "definition": binding.get("definition", {}).get("value", ""),
                    "prefLabel": binding.get("prefLabel", {}).get("value", ""),
                    "altLabels": [],
                }

            # Collect alternative labels
            alt_label = binding.get("altLabel", {}).get("value", "")
            if alt_label:
                concepts_data[concept]["altLabels"].append(alt_label)

        logger.info(f"Retrieved definitions for {len(concepts_data)} concepts from {len(concept_ids)} requested")
        return list(concepts_data.values())

    except Exception as e:
        logger.error(f"Failed to retrieve concept definitions: {e}", exc_info=True)
        return []


def format_definitions_as_chunks(definitions: list[dict]) -> list[dict]:
    """Convert ontology definitions to chunk format for LLM context.

    Each chunk represents a concept's semantic definition with metadata.
    """
    chunks = []

    for definition in definitions:
        concept = definition.get("concept", "")
        definition_text = definition.get("definition", "")
        pref_label = definition.get("prefLabel", "")
        alt_labels = definition.get("altLabels", [])
        concept_type = definition.get("type", "")

        # Skip if no definition available
        if not definition_text:
            continue

        # Extract standard and concept name from IRI
        standard, concept_name = _extract_concept_info(concept)

        # Build comprehensive chunk text
        chunk_text = f"""
CONCEPT DEFINITION: {concept_name}
Standard: {standard}
IRI: {concept}

Definition:
{definition_text}
"""

        if pref_label:
            chunk_text += f"\nPreferred Label: {pref_label}\n"

        if alt_labels:
            chunk_text += f"Alternative Labels: {', '.join(alt_labels)}\n"

        chunk_id_str = f"ontology-def-{concept_name.lower()}"
        chunk_id_int = hash(chunk_id_str) % (10 ** 8)

        chunk = {
            "id": chunk_id_int,
            "chunkId": chunk_id_str,
            "chunk_id": chunk_id_str,
            "retrievalEventId": f"ontology-{chunk_id_int}",
            "source_path": f"ontology/{standard}/{concept_name}",
            "label": f"Definition: {concept_name}",
            "text": chunk_text.strip(),
            "doc_type": "ontology-definition",
            "quality_score": 0.98,  # Highest quality - authoritative ontology source
            "standards_scope": [standard] if standard else [],
            "match_type": "semantic_definition",
            "similarity_reason": "Authoritative ontology definition",
            "repository_url": f"https://github.com/TransmodelEcosystem/{standard}",
            "embedding_vector": None,
            "heading": f"{concept_name} - {standard} Definition",
        }

        chunks.append(chunk)

    return chunks


def _extract_concept_info(concept_iri: str) -> tuple[str, str]:
    """Extract standard and concept name from ontology IRI.

    Args:
        concept_iri: Full IRI like "https://netex.org.uk/netex/2.0#ServiceJourney"

    Returns:
        Tuple of (standard, concept_name)
    """
    # Extract concept name (after #)
    if "#" in concept_iri:
        concept_name = concept_iri.split("#")[1]
    else:
        concept_name = concept_iri.split("/")[-1]

    # Extract standard
    if "netex" in concept_iri.lower():
        standard = "NeTEx"
    elif "opra" in concept_iri.lower():
        standard = "OpRa"
    elif "siri" in concept_iri.lower():
        standard = "SIRI"
    elif "transmodel" in concept_iri.lower():
        standard = "Transmodel"
    else:
        standard = "Ontology"

    return standard, concept_name


def _ensure_uri(concept_id: str) -> str:
    """Ensure concept_id is a full URI."""
    if concept_id.startswith("http"):
        return concept_id
    # Map common prefixes to URIs
    prefix_map = {
        "netex": "https://netex.org.uk/netex/2.0#",
        "opra": "https://transmodel-cen.eu/opra/1.0#",
        "siri": "https://siri.org.uk/siri/1.3#",
        "transmodel": "https://transmodel-cen.eu/6.2/",
        "nits": "https://napcore.eu/ontology/nits#",
    }
    for prefix, namespace in prefix_map.items():
        if concept_id.startswith(f"{prefix}:"):
            local_name = concept_id.split(":", 1)[1]
            return f"{namespace}{local_name}"
    return concept_id
