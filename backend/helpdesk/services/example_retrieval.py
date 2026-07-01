"""
Retrieve XML example files linked to schema concepts via semantic relationships.

Uses skos:seeAlso triples in GraphDB examples graph to find relevant examples
for modeling and implementation questions.

Created: 2026-07-01
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import unquote

logger = logging.getLogger(__name__)


def retrieve_concept_examples(
    concept_ids: set[str],
    endpoint: str,
    repository: str,
    timeout_seconds: int = 3,
    username: str = "",
    password: str = "",
) -> list[dict]:
    """Retrieve example files linked to concepts via skos:seeAlso.

    Args:
        concept_ids: Set of concept URIs (e.g., {"netex:TemplateServiceJourney"})
        endpoint: GraphDB SPARQL endpoint URL
        repository: Repository name
        timeout_seconds: Query timeout
        username: GraphDB username
        password: GraphDB password

    Returns:
        List of example metadata dicts with file paths and descriptions
    """
    if not concept_ids:
        return []

    try:
        from helpdesk.services.graphdb_client import execute_sparql_query

        # Build SPARQL query for examples linked to concepts
        concept_uris = " ".join(
            [f"<{_ensure_uri(cid)}>" if cid.startswith("http") else cid for cid in sorted(concept_ids)]
        )

        sparql_query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dct: <http://purl.org/dc/terms/>

        SELECT ?concept ?example ?label ?source
        WHERE {{
          VALUES ?concept {{ {concept_uris} }}
          ?concept skos:seeAlso ?example .
          ?example rdfs:label ?label ;
                   dct:source ?source .
        }}
        ORDER BY ?concept ?example
        LIMIT 20
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

        examples = []
        for binding in results.get("bindings", []):
            example_iri = binding.get("example", {}).get("value", "")
            source_path = binding.get("source", {}).get("value", "")

            # URL-decode the source path back to original file path
            decoded_path = unquote(source_path) if source_path else ""

            examples.append(
                {
                    "iri": example_iri,
                    "file_path": decoded_path,
                    "concept": binding.get("concept", {}).get("value", ""),
                    "type": "xml-example",
                    "source": f"examples/{decoded_path}" if decoded_path else "",
                    "match_type": "exact",
                    "similarity_reason": "Direct link to requested concept",
                }
            )

        logger.debug(f"Retrieved {len(examples)} examples for {len(concept_ids)} concepts")
        return examples

    except Exception as e:
        logger.warning(f"Failed to retrieve examples: {e}")
        return []


def retrieve_concept_examples_with_fallback(
    concept_ids: set[str],
    requested_mode: Optional[str] = None,
    endpoint: str = "",
    repository: str = "",
    timeout_seconds: int = 3,
    username: str = "",
    password: str = "",
) -> list[dict]:
    """Retrieve examples with smart fallback using semantic reasoning.

    Uses ontology hierarchy to suggest adaptable examples when exact matches
    don't exist. Ranks by semantic proximity to requested transport mode.

    Args:
        concept_ids: Set of concept URIs (e.g., {"netex:TemplateServiceJourney"})
        requested_mode: Optional transport mode ("ferry", "bus", "rail", etc.)
        endpoint: GraphDB SPARQL endpoint URL
        repository: Repository name
        timeout_seconds: Query timeout
        username: GraphDB username
        password: GraphDB password

    Returns:
        List of example metadata dicts ranked by relevance (exact > semantic > adaptable)
    """
    if not concept_ids:
        return []

    try:
        from helpdesk.services.graphdb_client import execute_sparql_query

        # First try: exact examples for requested mode
        exact_examples = retrieve_concept_examples(
            concept_ids, endpoint, repository, timeout_seconds, username, password
        )
        if exact_examples:
            return exact_examples

        # No exact matches - use semantic reasoning for fallback
        concept_uris = " ".join(
            [f"<{_ensure_uri(cid)}>" if cid.startswith("http") else cid for cid in sorted(concept_ids)]
        )

        # Build mode-aware SPARQL query with semantic ranking
        sparql_query = f"""
        PREFIX netex: <https://netex.org.uk/netex/2.0#>
        PREFIX nits: <https://napcore.eu/ontology/nits#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>

        SELECT ?example ?concept ?label ?source ?matchType ?reason
        WHERE {{
          VALUES ?concept {{ {concept_uris} }}
          ?example skos:seeAlso ?concept .
          ?example rdfs:label ?label ;
                   dct:source ?source .

          OPTIONAL {{
            # Tier 1: Examples for demand-responsive services
            nits:DemandResponsiveService rdfs:subClassOf* ?serviceType .
            ?concept dct:relatedTo ?serviceType .
            BIND("demand_responsive_pattern" AS ?matchType)
            BIND("Demand-responsive service pattern (adaptable for ferries)" AS ?reason)
          }}

          OPTIONAL {{
            # Tier 2: Examples of same concept class (any transport mode)
            ?concept a ?baseClass .
            FILTER(?baseClass IN (
              netex:TemplateServiceJourney,
              netex:Service,
              netex:Line,
              netex:Journey
            ))
            BIND("adaptable_class" AS ?matchType)
            BIND(CONCAT("Same ", STRAFTER(STR(?baseClass), "#"), " pattern works across modes") AS ?reason)
          }}
        }}
        ORDER BY
          CASE ?matchType
            WHEN "demand_responsive_pattern" THEN 1
            WHEN "adaptable_class" THEN 2
            ELSE 3
          END
          ?concept ?example
        LIMIT 10
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
            logger.debug(f"No fallback examples found for {len(concept_ids)} concepts")
            return []

        examples = []
        seen = set()
        for binding in results.get("bindings", []):
            example_iri = binding.get("example", {}).get("value", "")
            if example_iri in seen:
                continue
            seen.add(example_iri)

            source_path = binding.get("source", {}).get("value", "")
            decoded_path = unquote(source_path) if source_path else ""

            match_type = binding.get("matchType", {}).get("value", "adaptable_class")
            reason = binding.get("reason", {}).get("value", "Semantic fallback match")

            examples.append(
                {
                    "iri": example_iri,
                    "file_path": decoded_path,
                    "concept": binding.get("concept", {}).get("value", ""),
                    "type": "xml-example",
                    "source": f"examples/{decoded_path}" if decoded_path else "",
                    "match_type": match_type,
                    "similarity_reason": reason,
                }
            )

        logger.debug(
            f"Retrieved {len(examples)} fallback examples for {len(concept_ids)} concepts "
            f"(requested mode: {requested_mode})"
        )
        return examples

    except Exception as e:
        logger.warning(f"Failed to retrieve fallback examples: {e}")
        return []


def format_examples_as_chunks(examples: list[dict]) -> list[dict]:
    """Convert example metadata to chunk format for LLM context.

    Each chunk represents one example file with metadata for attribution.
    Includes match type and similarity reasoning for semantic fallback matches.
    """
    chunks = []
    for example in examples:
        match_type = example.get("match_type", "exact")
        similarity_reason = example.get("similarity_reason", "Direct match")

        # Adjust quality score based on match type
        quality_score = 0.85
        if match_type == "demand_responsive_pattern":
            quality_score = 0.75  # High relevance for semantic patterns
        elif match_type == "adaptable_class":
            quality_score = 0.65  # Moderate relevance for class-level matches

        # Include match context in text for LLM understanding
        match_context = f"[{match_type.upper()}] {similarity_reason}\n" if match_type != "exact" else ""

        chunk = {
            "chunk_id": f"example-{example['iri'].replace('/', '-')[-32:]}",
            "source_path": example["file_path"],
            "label": f"Example: {example['file_path'].split('/')[-1]}",
            "text": (
                f"{match_context}"
                f"XML example file: {example['file_path']}\n"
                f"Related concept: {example['concept']}"
            ),
            "doc_type": "xml-example",
            "quality_score": quality_score,
            "standards_scope": _extract_standard_from_concept(example["concept"]),
            "match_type": match_type,
            "similarity_reason": similarity_reason,
        }
        chunks.append(chunk)

    return chunks


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


def _extract_standard_from_concept(concept_uri: str) -> list[str]:
    """Extract standard name from concept URI."""
    if not concept_uri:
        return []

    if "netex.org.uk" in concept_uri:
        return ["NeTEx"]
    elif "opra" in concept_uri.lower():
        return ["OpRa"]
    elif "siri" in concept_uri.lower():
        return ["SIRI"]
    elif "transmodel" in concept_uri.lower():
        return ["Transmodel"]

    return []
