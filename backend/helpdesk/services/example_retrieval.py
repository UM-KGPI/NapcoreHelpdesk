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
                }
            )

        logger.debug(f"Retrieved {len(examples)} examples for {len(concept_ids)} concepts")
        return examples

    except Exception as e:
        logger.warning(f"Failed to retrieve examples: {e}")
        return []


def format_examples_as_chunks(examples: list[dict]) -> list[dict]:
    """Convert example metadata to chunk format for LLM context.

    Each chunk represents one example file with metadata for attribution.
    """
    chunks = []
    for example in examples:
        chunk = {
            "chunk_id": f"example-{example['iri'].replace('/', '-')[-32:]}",
            "source_path": example["file_path"],
            "label": f"Example: {example['file_path'].split('/')[-1]}",
            "text": f"XML example file: {example['file_path']}\nRelated concept: {example['concept']}",
            "doc_type": "xml-example",
            "quality_score": 0.85,  # Examples are high-quality by default
            "standards_scope": _extract_standard_from_concept(example["concept"]),
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
