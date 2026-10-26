"""
Batch embedding computation for source index chunks.

Generates vector embeddings for text chunks during index builds and for
queries at retrieval time. By default (EMBEDDING_BACKEND=hash) the vectors are
deterministic hash embeddings computed locally. With EMBEDDING_BACKEND=semantic
they come from the embedding service (helpdesk/embedding_service.py), padded
with zeros to the column's dimension, which leaves cosine similarity unchanged.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-10-26
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from urllib.error import URLError
from urllib.request import Request, urlopen


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
    """Deterministic hash-based embedding. No external calls required."""
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


# Texts per request to the embedding service; a batch of 64 chunks takes seconds on 2 CPUs.
SERVICE_BATCH_SIZE = 64


class EmbeddingServiceError(RuntimeError):
    """The embedding service could not be reached or returned an unusable answer.

    Never answered with hash vectors instead: hash and semantic vectors are not
    comparable, so mixing them would silently break retrieval."""


def semantic_enabled() -> bool:
    from django.conf import settings

    return getattr(settings, "EMBEDDING_BACKEND", "hash") == "semantic"


def uses_semantic(backend: str | None = None) -> bool:
    """Whether to embed semantically: the given backend ("hash" or "semantic"), else the setting."""
    return semantic_enabled() if backend is None else backend == "semantic"


def passage_text(source_path: str, heading: str, text: str) -> str:
    """The text a semantic model embeds for an indexed chunk: where it is, then what it says."""
    return f"{source_path}\n{heading or ''}\n{text}"


def _service_embed(texts: list[str], kind: str) -> list[list[float]]:
    from django.conf import settings

    url = settings.EMBEDDING_SERVICE_URL.rstrip("/") + "/embed"
    vectors: list[list[float]] = []
    for start in range(0, len(texts), SERVICE_BATCH_SIZE):
        body = json.dumps({"texts": texts[start : start + SERVICE_BATCH_SIZE], "kind": kind}).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=settings.EMBEDDING_SERVICE_TIMEOUT_SECONDS) as response:
                batch = json.loads(response.read())["vectors"]
        except (URLError, OSError, ValueError, KeyError) as exc:
            raise EmbeddingServiceError(f"Embedding service at {url} failed: {exc}") from exc
        vectors.extend(batch)
    if len(vectors) != len(texts) or any(len(v) > EMBEDDING_DIMENSION for v in vectors):
        raise EmbeddingServiceError(f"Embedding service at {url} returned {len(vectors)} vectors for {len(texts)} texts.")
    return [list(map(float, v)) + [0.0] * (EMBEDDING_DIMENSION - len(v)) for v in vectors]


def build_text_embedding(text: str, kind: str = "passage") -> list[float]:
    """Return the embedding for one text: a question ("query") or indexed text ("passage")."""
    if semantic_enabled():
        return _service_embed([text], kind)[0]
    return _hash_embed(text)


def build_text_embeddings_batch(texts: list[str], kind: str = "passage", backend: str | None = None) -> list[list[float]]:
    """Return embeddings for a list of texts, preserving input order.

    backend overrides EMBEDDING_BACKEND, for re-embedding the index with the other backend."""
    if uses_semantic(backend):
        return _service_embed(list(texts), kind) if texts else []
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
