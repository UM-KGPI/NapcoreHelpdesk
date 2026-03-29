from __future__ import annotations

import json
from urllib import error, request

from django.conf import settings


class LLMGenerationError(Exception):
    """Raised when LLM generation cannot be completed safely."""


def _build_messages(question: str, chunks: list[dict]) -> list[dict]:
    context_lines = []
    for index, chunk in enumerate(chunks[:6], start=1):
        context_lines.append(
            "\n".join(
                [
                    f"[E{index}] repository={chunk['repositoryUrl']}",
                    f"[E{index}] commit={chunk['commitSha']}",
                    f"[E{index}] source={chunk['sourcePath']}",
                    f"[E{index}] chunk={chunk['chunkId']}",
                    f"[E{index}] text={chunk['text']}",
                ]
            )
        )

    context = "\n\n".join(context_lines)

    system_prompt = (
        "You are a standards helpdesk assistant. Use ONLY the provided evidence blocks. "
        "If evidence is insufficient, say that you cannot answer safely. "
        "Respond in 3-5 concise sentences and include citation markers like [E1], [E2]."
    )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Evidence blocks:\n{context}\n\n"
        "Write a grounded answer with explicit [E#] markers tied to evidence blocks."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_answer_llm(question: str, chunks: list[dict]) -> dict:
    """Generate a grounded answer through a configurable OpenAI-compatible API."""

    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER != "openai-compatible":
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    if not settings.LLM_API_KEY:
        raise LLMGenerationError("LLM API key is not configured.")

    body = {
        "model": settings.LLM_MODEL,
        "messages": _build_messages(question=question, chunks=chunks),
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
    }

    req = request.Request(
        url=f"{settings.LLM_API_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
        },
    )

    try:
        with request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise LLMGenerationError(f"LLM HTTP error: {exc.code}") from exc
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise LLMGenerationError("LLM request failed.") from exc

    choices = payload.get("choices") or []
    if not choices:
        raise LLMGenerationError("LLM response has no choices.")

    message = choices[0].get("message", {})
    answer = (message.get("content") or "").strip()
    if not answer:
        raise LLMGenerationError("LLM response was empty.")

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.82,
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
    }
