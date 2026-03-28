from __future__ import annotations

import hashlib
import math


EMBEDDING_DIMENSION = 64


def build_text_embedding(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
    """Build deterministic lightweight text embeddings for MVP hybrid retrieval.

    This intentionally avoids external model calls so local/test environments can run
    the retrieval stack without network/provider dependencies.
    """

    vector = [0.0] * dimension
    tokens = [token.lower() for token in text.split() if len(token) > 2]
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimension
        # Map the next byte to [-1.0, 1.0] to encode token directionality.
        weight = (digest[2] / 127.5) - 1.0
        vector[index] += weight

    return _normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity between two vectors, guarding zero magnitudes."""

    if not left or not right or len(left) != len(right):
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
