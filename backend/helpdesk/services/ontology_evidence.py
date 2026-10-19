"""
Retrieve semantic definitions and properties from ontology for concept queries.

Extracts skos:definition, rdfs:label, and other semantic properties from GraphDB
ontologies to provide authoritative definitions for schema concepts.

Created: 2026-07-01
"""

from __future__ import annotations

import logging
from typing import Optional

from helpdesk.services.graphdb_client import TRANSMODEL_ALIGNED_STANDARDS
from helpdesk.services.transmodel_alignment import clean_definition

logger = logging.getLogger(__name__)

TRANSMODEL_NAMESPACE = "https://transmodel-cen.eu/6.2/"
TRANSMODEL_SOURCE_PATH = "docs/ontology/standards/transmodel.ttl"
TRANSMODEL_SOURCE_URL = (
    "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards/transmodel.ttl"
)

# Graphs the definition query reads. The repository also holds legacy urn:graph:* graphs from older loads;
# their rdfs:comment values differ (e.g. "Extracted from OpRa XSD source: opra.xsd. <definition>"), and
# reading them gave citations a source path that does not exist.
DEFINITION_GRAPHS = (
    "https://napcore.eu/graph/core/napcore-its",
    "https://napcore.eu/graph/standards/transmodel",
    *(f"https://napcore.eu/graph/standards/{standard}" for standard in TRANSMODEL_ALIGNED_STANDARDS),
    *(f"https://napcore.eu/graph/alignments/transmodel-{standard}" for standard in TRANSMODEL_ALIGNED_STANDARDS),
)

# Values of nits:transmodelDefinitionStatus (see alignments/transmodel-*-align.ttl).
_DEFINITION_STATUS_NOTES = {
    "differs": "The {standard} XSD definition differs from the Transmodel definition; "
    "use the Transmodel definition as the reference.",
    "extends": "The {standard} XSD definition repeats the Transmodel definition "
    "and adds {standard}-specific notes.",
    "equivalent": "The {standard} XSD definition matches the Transmodel definition.",
}


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
        from_graphs = "\n        ".join(f"FROM <{graph}>" for graph in DEFINITION_GRAPHS)

        sparql_query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX nits: <https://napcore.eu/ontology/nits#>

        SELECT ?concept ?definition ?prefLabel ?altLabel ?type ?source ?ownComment
               ?tmConcept ?tmLabel ?tmDefinition ?tmStatus
        {from_graphs}
        WHERE {{
          VALUES ?concept {{ {concept_uris} }}
          ?concept a ?type .
          OPTIONAL {{ ?concept skos:definition ?definition . }}
          OPTIONAL {{ ?concept skos:prefLabel ?prefLabel . }}
          OPTIONAL {{ ?concept skos:altLabel ?altLabel . }}
          OPTIONAL {{ ?concept rdfs:comment ?source . FILTER(CONTAINS(?source, "Extracted from")) }}
          # Transmodel stores its definitions as rdfs:comment, not skos:definition
          OPTIONAL {{
            ?concept rdfs:comment ?ownComment .
            FILTER(STRSTARTS(STR(?concept), "{TRANSMODEL_NAMESPACE}"))
          }}
          # Reference definition of the Transmodel concept this concept implements
          OPTIONAL {{
            ?concept skos:exactMatch|^skos:exactMatch ?tmConcept .
            FILTER(STRSTARTS(STR(?tmConcept), "{TRANSMODEL_NAMESPACE}"))
            ?tmConcept rdfs:comment ?tmDefinition .
            OPTIONAL {{ ?tmConcept rdfs:label ?tmLabel . }}
          }}
          OPTIONAL {{ ?concept nits:transmodelDefinitionStatus ?tmStatus . }}
        }}
        ORDER BY ?concept
        LIMIT 200
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

            # Extract XSD source file from rdfs:comment
            # Supports formats: "Extracted from: xsd/netex_part_1/..." or "Extracted from NeTEx XSD source: xsd/..."
            source_comment = binding.get("source", {}).get("value", "")
            xsd_source = ""
            if source_comment and "Extracted from" in source_comment:
                # Handle both "Extracted from: path" and "Extracted from NeTEx XSD source: path"
                if ":" in source_comment:
                    xsd_source = source_comment.split(":", 1)[1].strip()

            row_values = {
                "type": binding.get("type", {}).get("value", ""),
                "definition": (
                    binding.get("definition", {}).get("value", "")
                    or clean_definition(binding.get("ownComment", {}).get("value", ""))
                ),
                "prefLabel": binding.get("prefLabel", {}).get("value", ""),
                "xsd_source": xsd_source,  # Store XSD source file path
                "tm_concept": binding.get("tmConcept", {}).get("value", ""),
                "tm_label": binding.get("tmLabel", {}).get("value", ""),
                # Transmodel EA export leaves HTML (<font ...>) in some definitions
                "tm_definition": clean_definition(binding.get("tmDefinition", {}).get("value", "")),
                "tm_status": binding.get("tmStatus", {}).get("value", ""),
            }

            # OPTIONALs multiply rows (types x altLabels x ...) and a value can be
            # missing from the first row, so fill each field from any row that has it.
            entry = concepts_data.setdefault(
                concept, {"concept": concept, "altLabels": [], **dict.fromkeys(row_values, "")}
            )
            for field, value in row_values.items():
                if value and not entry[field]:
                    entry[field] = value

            # Collect alternative labels
            alt_label = binding.get("altLabel", {}).get("value", "")
            if alt_label and alt_label not in entry["altLabels"]:
                entry["altLabels"].append(alt_label)

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
    emitted_transmodel: set[str] = set()
    comparison_notes = _comparison_notes_by_transmodel_concept(definitions)

    for definition in definitions:
        concept = definition.get("concept", "")
        definition_text = definition.get("definition", "")
        pref_label = definition.get("prefLabel", "")
        alt_labels = definition.get("altLabels", [])
        concept_type = definition.get("type", "")
        xsd_source = definition.get("xsd_source", "")  # XSD file where definition came from
        tm_concept = definition.get("tm_concept", "")
        tm_definition = definition.get("tm_definition", "")

        # Extract standard and concept name from IRI
        standard, concept_name = _extract_concept_info(concept)

        # Transmodel is the reference: its definition goes before the standard's own
        if tm_concept and tm_definition and tm_concept not in emitted_transmodel:
            emitted_transmodel.add(tm_concept)
            chunks.append(
                _transmodel_definition_chunk(
                    tm_concept=tm_concept,
                    tm_label=definition.get("tm_label", ""),
                    tm_definition=tm_definition,
                    implemented_as=f"{standard} {concept_name}",
                    notes=comparison_notes.get(tm_concept, []),
                )
            )

        if standard == "Transmodel":
            if definition_text and concept not in emitted_transmodel:
                emitted_transmodel.add(concept)
                chunks.append(
                    _transmodel_definition_chunk(
                        tm_concept=concept,
                        tm_label=pref_label,
                        tm_definition=definition_text,
                        implemented_as="",
                        notes=comparison_notes.get(concept, []),
                    )
                )
            continue

        # Skip if no definition available
        if not definition_text:
            continue

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

        if tm_concept:
            tm_name = definition.get("tm_label", "") or tm_concept.rsplit("/", 1)[-1]
            chunk_text += f"Transmodel concept: {tm_name} (skos:exactMatch)\n"

        chunk_id_str = f"ontology-def-{concept_name.lower()}"
        chunk_id_int = hash(chunk_id_str) % (10 ** 8)

        # Determine repository and commit based on standard
        repo_name = standard
        # Use version tags for official schema releases
        version_map = {
            "NeTEx": "v2.0",
            "OpRa": "v1.0",
            "SIRI": "v2.1",
        }
        commit_sha = version_map.get(standard, "main")

        # Use XSD source file path if available, ensure xsd/ prefix
        # Source should be the actual XSD file: netex_part_2/.../file.xsd
        if xsd_source:
            if not xsd_source.startswith("xsd/"):
                source_path = f"xsd/{xsd_source}"
            else:
                source_path = xsd_source
        else:
            # Fallback to main schema file for the standard (not just directory)
            schema_name_map = {
                "NeTEx": "netex_framework/netex_frame.xsd",
                "OpRa": "opra.xsd",
                "SIRI": "siri.xsd",
            }
            schema_file = schema_name_map.get(standard, f"{standard.lower()}.xsd")
            source_path = f"xsd/{schema_file}"

        # Build blob URL pointing to the actual XSD file
        # Format: github.com/{owner}/{repo}/blob/{version}/{path}/file.xsd
        blob_url = f"https://github.com/TransmodelEcosystem/{repo_name}/blob/{commit_sha}/{source_path}"

        chunk = {
            "id": chunk_id_int,
            "chunkId": chunk_id_str,
            "chunk_id": chunk_id_str,
            "retrievalEventId": f"ontology-{chunk_id_int}",
            "sourcePath": source_path,  # Use camelCase to match LLM generator expectations
            "source_path": source_path,  # Also keep snake_case for compatibility
            "label": f"Definition: {concept_name}",
            "text": chunk_text.strip(),
            "doc_type": "ontology-definition",
            "quality_score": 0.98,  # Highest quality - authoritative ontology source
            "standards_scope": [standard] if standard else [],
            "match_type": "semantic_definition",
            "similarity_reason": "Authoritative definition from XSD schema",
            "repositoryUrl": blob_url,  # Use camelCase to match LLM generator expectations
            "repository_url": blob_url,  # Also keep snake_case for compatibility
            "commitSha": commit_sha,  # Use camelCase to match LLM generator expectations
            "commit_sha": commit_sha,  # Also keep snake_case for compatibility
            "embedding_vector": None,
            "heading": f"{concept_name} - {standard} Definition",
        }

        chunks.append(chunk)

    return chunks


def _comparison_notes_by_transmodel_concept(definitions: list[dict]) -> dict[str, list[str]]:
    """How each standard's own definition compares with the Transmodel one, by Transmodel concept.

    The comparison comes from the alignment data, not from the standard's XSD, so it is carried by the
    Transmodel chunk. Cited from the XSD chunk it would point readers at a file that does not say it.
    Only concepts whose Transmodel chunk is emitted need a note.
    """

    notes: dict[str, list[str]] = {}
    for definition in definitions:
        tm_concept = definition.get("tm_concept", "")
        template = _DEFINITION_STATUS_NOTES.get(definition.get("tm_status", ""))
        if not (tm_concept and definition.get("tm_definition") and template):
            continue
        standard, concept_name = _extract_concept_info(definition.get("concept", ""))
        note = f"{standard} {concept_name}: " + template.format(standard=standard)
        if note not in notes.setdefault(tm_concept, []):
            notes[tm_concept].append(note)
    return notes


def _transmodel_definition_chunk(
    *,
    tm_concept: str,
    tm_label: str,
    tm_definition: str,
    implemented_as: str,
    notes: list[str] | None = None,
) -> dict:
    """Build the evidence chunk for a Transmodel reference definition."""
    local_name = tm_concept.rsplit("/", 1)[-1]
    label = tm_label or local_name.replace("_", " ")
    # Carry the CamelCase spelling too, so citations using either form are grounded
    camel_name = "".join(part.capitalize() for part in local_name.split("_"))

    chunk_text = f"""
CONCEPT DEFINITION: {label} ({camel_name})
Standard: Transmodel (conceptual reference model, v6.2)
IRI: {tm_concept}
"""
    if implemented_as:
        chunk_text += f"Implemented as: {implemented_as}\n"
    chunk_text += f"""
Definition:
{tm_definition}
"""
    for note in notes or []:
        chunk_text += f"Comparison with {note}\n"

    chunk_id_str = f"ontology-def-tm-{local_name.lower()}"
    chunk_id_int = hash(chunk_id_str) % (10 ** 8)
    # One path per concept: all Transmodel definitions live in one file, and the
    # per-source-path retrieval cap (RETRIEVAL_MAX_SAME_SOURCE_PATH) would
    # otherwise let only two of them survive.
    source_path = f"{TRANSMODEL_SOURCE_PATH}#{local_name}"
    return {
        "id": chunk_id_int,
        "chunkId": chunk_id_str,
        "chunk_id": chunk_id_str,
        "retrievalEventId": f"ontology-{chunk_id_int}",
        "sourcePath": source_path,
        "source_path": source_path,
        "label": f"Definition: {label} (Transmodel)",
        "text": chunk_text.strip(),
        "doc_type": "ontology-definition",
        "quality_score": 0.99,  # Transmodel is the reference above XSD-derived definitions
        "standards_scope": ["Transmodel"],
        "match_type": "semantic_definition",
        "similarity_reason": "Reference definition from the Transmodel conceptual model",
        "repositoryUrl": TRANSMODEL_SOURCE_URL,
        "repository_url": TRANSMODEL_SOURCE_URL,
        "commitSha": "main",
        "commit_sha": "main",
        "embedding_vector": None,
        "heading": f"{label} - Transmodel Definition",
    }


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
    if concept_iri.startswith(TRANSMODEL_NAMESPACE):
        standard = "Transmodel"
    elif "netex" in concept_iri.lower():
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
