from __future__ import annotations

import json
from urllib import error, request

from django.conf import settings


class EmbeddingProviderError(Exception):
    """Raised when provider embeddings cannot be produced safely."""


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Call the configured OpenAI-compatible embeddings API.

    Returns one embedding vector per input text, in the same order as the input list.

    Raises EmbeddingProviderError on configuration or API failure so callers
    can fall back to the hash-based embedding without surfacing the error.
    """
    if not getattr(settings, "EMBEDDING_ENABLED", False):
        raise EmbeddingProviderError("Embedding provider is disabled by configuration.")

    provider = getattr(settings, "EMBEDDING_PROVIDER", "openai-compatible")
    if provider != "openai-compatible":
        raise EmbeddingProviderError(f"Unsupported embedding provider: {provider}")

    api_key = getattr(settings, "EMBEDDING_API_KEY", "")
    if not api_key:
        raise EmbeddingProviderError("Embedding API key is not configured.")

    body = {
        "input": texts,
        "model": settings.EMBEDDING_MODEL,
    }
    req = request.Request(
        url=f"{settings.EMBEDDING_API_BASE_URL.rstrip('/')}/embeddings",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with request.urlopen(req, timeout=settings.EMBEDDING_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise EmbeddingProviderError(f"Embedding API HTTP error: {exc.code}") from exc
    except Exception as exc:
        raise EmbeddingProviderError("Embedding API request failed.") from exc

    data = payload.get("data") or []
    if len(data) != len(texts):
        raise EmbeddingProviderError(
            f"Embedding API returned {len(data)} embeddings for {len(texts)} inputs."
        )

    # OpenAI returns data sorted by index; sort defensively to guarantee input order.
    sorted_data = sorted(data, key=lambda item: item.get("index", 0))
    return [item["embedding"] for item in sorted_data]
