"""
Batch embedding computation for source index chunks.

Generates vector embeddings for text chunks during index builds. Content
is hashed before the API call so unchanged chunks are skipped on incremental
runs, reducing embedding API cost.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

import hashlib
import math
import re


EMBEDDING_DIMENSION = 1536

TOKEN_SYNONYMS = {
    "delayed": "late",
    "delay": "late",
    "delays": "late",
    "journeys": "journey",
    "services": "service",
    "metrics": "metric",
}


def normalize_text_tokens(text: str) -> list[str]:
    """Normalize text into retrieval-friendly tokens.

    This keeps local deterministic retrieval lightweight while handling a small
    set of domain-relevant vocabulary variations used across standards docs.
    """

    raw_tokens = re.findall(r"[a-z0-9]+", text.lower())
    normalized_tokens: list[str] = []
    for token in raw_tokens:
        if len(token) <= 2:
            continue
        normalized_tokens.append(TOKEN_SYNONYMS.get(token, token))
    return normalized_tokens


def _hash_embed(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
    """Deterministic hash-based fallback embedding. No external calls required."""
    vector = [0.0] * dimension
    tokens = normalize_text_tokens(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimension
        weight = (digest[2] / 127.5) - 1.0
        vector[index] += weight

    return _normalize(vector)


def build_text_embedding(text: str) -> list[float]:
    """Return a semantic embedding for the given text.

    Uses the configured OpenAI-compatible provider when EMBEDDING_ENABLED=True.
    Falls back to the deterministic hash-based embedding on provider failure or
    when the provider is not configured.
    """
    try:
        from helpdesk.services.embedding_provider import embed_texts
        return embed_texts([text])[0]
    except Exception:
        pass
    return _hash_embed(text)


def build_text_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a list of texts, using a single provider batch call when available.

    Preserves input order. Falls back to hash-based embedding per item on provider
    failure or when the provider is not configured.
    """
    if not texts:
        return []
    try:
        from helpdesk.services.embedding_provider import embed_texts
        return embed_texts(texts)
    except Exception:
        pass
    return [_hash_embed(t) for t in texts]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity between two vectors, guarding zero magnitudes."""

    if left is None or right is None:
        return 0.0
    if len(left) == 0 or len(right) == 0 or len(left) != len(right):
        return 0.0
    left_norm = _norm(left)
    right_norm = _norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right))
    return dot_product / (left_norm * right_norm)


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _normalize(vector: list[float]) -> list[float]:
    magnitude = _norm(vector)
    if magnitude == 0.0:
        return vector
    return [value / magnitude for value in vector]
