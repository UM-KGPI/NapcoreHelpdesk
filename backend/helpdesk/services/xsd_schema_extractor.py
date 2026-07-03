"""
Retrieve XSD schema element definitions from harvested database.

ARCHITECTURE:
- At deployment time: python manage.py harvest_xsd_definitions
  This extracts all XSD definitions from local repositories and stores
  them as SourceChunk records in the database.

- At runtime: This module queries those harvested chunks.
  Zero dependency on repository file system access.

This separation allows production deployments without carrying repository copies.

Created: 2026-07-03
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def retrieve_schema_definitions_for_concepts(concept_names: list[str], standard: str = "NeTEx") -> list[dict]:
    """
    Retrieve XSD schema definitions from database (harvested by management command).

    Args:
        concept_names: List of element names (e.g., ["DepartureTime", "ArrivalTime"])
        standard: Standard name ("NeTEx", "SIRI", "OpRa")

    Returns:
        List of chunk dicts with schema definitions
    """
    from helpdesk.models import SourceChunk

    chunks = []

    for concept_name in concept_names:
        # Use same ID format as harvester: xsd-def-{standard}-{name}
        chunk_id = f"xsd-def-{standard.lower()}-{concept_name.lower()}"

        try:
            chunk = SourceChunk.objects.get(chunk_id=chunk_id, doc_type="xsd-definition")
            chunks.append({
                "id": chunk.id,
                "chunkId": chunk.chunk_id,
                "chunk_id": chunk.chunk_id,
                "retrievalEventId": f"xsd-{chunk.id}",
                "label": chunk.label,
                "text": chunk.text,
                "doc_type": chunk.doc_type,
                "quality_score": chunk.quality_score,
                "standards_scope": chunk.standards_scope or [standard],
                "match_type": "schema_definition",
                "similarity_reason": f"XSD schema definition for {concept_name}",
                "repositoryUrl": chunk.repository_url,
                "repository_url": chunk.repository_url,
                "commitSha": chunk.commit_sha,
                "commit_sha": chunk.commit_sha,
                "sourcePath": chunk.source_path,
                "source_path": chunk.source_path,
                "heading": chunk.heading,
            })
            logger.info(f"Retrieved XSD definition for {concept_name} from database")
        except SourceChunk.DoesNotExist:
            logger.debug(
                f"XSD definition not found for {concept_name}. "
                f"Run: python manage.py harvest_xsd_definitions"
            )
        except Exception as e:
            logger.debug(f"Error retrieving XSD definition for {concept_name}: {e}")

    return chunks
