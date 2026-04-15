from __future__ import annotations

import hashlib
import re
from typing import Iterable

from helpdesk.models import SourceChunk


# Minimal Phase-PoC concept graph for graph-aware retrieval scoring.
GRAPH_CONCEPT_ALIASES = {
    "opra:delayed-journey": {
        "delayed journey",
        "delayed vehicle journey",
        "delayed vehicle journeys",
        "delayed journeys",
        "late journey",
        "late vehicle journey",
        "late journeys",
    },
    "opra:cancelled-journey": {
        "cancelled journey",
        "cancelled journeys",
        "canceled journey",
        "canceled journeys",
    },
    "opra:delay-statistics": {
        "delay statistic",
        "delay statistics",
        "delayedjourneycount",
    },
    "opra:late-dated-vehicle-journey-entry": {
        "latedatedvehiclejourneyentry",
        "late dated vehicle journey entry",
    },
    "opra:journey-events-example": {
        "delayedandcancelledjourneyswithevents",
        "journeys with events",
    },
}


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _normalize_for_matching(text: str) -> str:
    """Lowercase and collapse non-alphanumeric runs for tolerant alias matching."""

    tokens = TOKEN_PATTERN.findall((text or "").lower())
    return " ".join(tokens)


def _alias_matches_text(alias: str, normalized_text: str) -> bool:
    normalized_alias = _normalize_for_matching(alias)
    if not normalized_alias:
        return False
    if normalized_alias in normalized_text:
        return True

    # Fallback token-subset check catches variants like
    # "delayed vehicle journeys" when alias is "delayed journey".
    alias_tokens = set(normalized_alias.split())
    text_tokens = set(normalized_text.split())
    return bool(alias_tokens) and alias_tokens.issubset(text_tokens)

GRAPH_RELATIONS = {
    "opra:delayed-journey": {
        "opra:delay-statistics",
        "opra:late-dated-vehicle-journey-entry",
        "opra:journey-events-example",
    },
    "opra:cancelled-journey": {
        "opra:journey-events-example",
    },
    "opra:delay-statistics": {
        "opra:delayed-journey",
    },
    "opra:late-dated-vehicle-journey-entry": {
        "opra:delayed-journey",
    },
    "opra:journey-events-example": {
        "opra:delayed-journey",
        "opra:cancelled-journey",
    },
}


def extract_graph_concepts(text: str) -> set[str]:
    normalized_text = _normalize_for_matching(text)
    concepts: set[str] = set()
    for concept_id, aliases in GRAPH_CONCEPT_ALIASES.items():
        if any(_alias_matches_text(alias, normalized_text) for alias in aliases):
            concepts.add(concept_id)
    return concepts


def expand_graph_concepts(concepts: set[str], hops: int = 1) -> set[str]:
    expanded = set(concepts)
    frontier = set(concepts)
    for _ in range(max(0, hops)):
        next_frontier: set[str] = set()
        for concept_id in frontier:
            for neighbor in GRAPH_RELATIONS.get(concept_id, set()):
                if neighbor not in expanded:
                    expanded.add(neighbor)
                    next_frontier.add(neighbor)
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
                "namespace": "nch",
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
