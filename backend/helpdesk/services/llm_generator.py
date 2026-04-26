from __future__ import annotations

import json
import re
import ssl
from urllib import error, request

from django.conf import settings


class LLMGenerationError(Exception):
    """Raised when LLM generation cannot be completed safely."""


FENCED_CODE_BLOCK_PATTERN = re.compile(r"```([A-Za-z0-9_+-]*)\n(.*?)```", re.DOTALL)


def _question_requests_verbatim_example(question: str) -> bool:
    question_lower = question.lower()
    asks_for_example = any(term in question_lower for term in ["example", "sample", "snippet"])
    asks_for_code = any(term in question_lower for term in ["xml", "json", "yaml", "code"])
    return asks_for_example and asks_for_code


def _normalize_grounded_line(line: str) -> str:
    return " ".join(line.strip().lower().split())


def _extract_grounded_lines(text: str) -> set[str]:
    grounded_lines: set[str] = set()
    for raw_line in (text or "").splitlines():
        normalized = _normalize_grounded_line(raw_line)
        if len(normalized) < 8:
            continue
        if not any(marker in normalized for marker in ["<", ">", "/", "="]):
            continue
        grounded_lines.add(normalized)
    return grounded_lines


def _validate_grounded_example_output(question: str, answer: str, chunks: list[dict]) -> None:
    if not _question_requests_verbatim_example(question):
        return

    code_blocks = FENCED_CODE_BLOCK_PATTERN.findall(answer or "")
    if not code_blocks:
        return

    evidence_lines: set[str] = set()
    for chunk in chunks:
        evidence_lines.update(_extract_grounded_lines(str(chunk.get("text", ""))))

    for language, block in code_blocks:
        normalized_language = (language or "").strip().lower()
        if normalized_language and normalized_language not in {"xml", "json", "yaml", "yml", "txt"}:
            continue

        block_lines = [
            _normalize_grounded_line(line)
            for line in block.splitlines()
            if len(_normalize_grounded_line(line)) >= 8
            and any(marker in line for marker in ["<", ">", "/", "="])
        ]
        if not block_lines:
            continue

        matched_lines = sum(1 for line in block_lines if line in evidence_lines)
        if matched_lines < max(3, (len(block_lines) * 2 + 2) // 3):
            raise LLMGenerationError(
                "Generated example block is not grounded in retrieved evidence; refusing fabricated XML/example output."
            )


def _build_ssl_context() -> ssl.SSLContext:
    """Build SSL context for LLM provider calls, supporting custom CA bundles."""

    if not settings.LLM_VERIFY_SSL:
        return ssl._create_unverified_context()

    context = ssl.create_default_context()
    if settings.LLM_CA_BUNDLE:
        context.load_verify_locations(cafile=settings.LLM_CA_BUNDLE)
    return context


def _build_messages(question: str, chunks: list[dict], scope: list[str] | None = None) -> list[dict]:
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
    scope_text = ", ".join(scope) if scope else "all approved standards"

    system_prompt = (
        "You are a standards helpdesk assistant. Prioritize provided evidence blocks and stay within the requested standards scope. "
        "Do not add external or uncited knowledge. Do not contradict evidence. "
        "If evidence is insufficient for claims that require citation, say that you cannot answer safely. "
        "Respond in 4-7 concise sentences and include citation markers like [E1], [E2] for evidence-grounded statements."
    )
    if _question_requests_verbatim_example(question):
        system_prompt = (
            f"{system_prompt} "
            "For XML, JSON, YAML, or code-example requests, only quote verbatim or lightly trimmed excerpts that are directly present in the evidence blocks. "
            "Never synthesize a new example by combining structures across sources. "
            "If the evidence does not contain an exact usable snippet, say that you cannot provide an embedded example safely and point to the closest cited source file instead."
        )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Requested scope: {scope_text}\n\n"
        f"Evidence blocks:\n{context}\n\n"
        "Write a scoped answer with explicit [E#] markers tied to evidence blocks only. "
        "If the evidence does not support the requested detail, explicitly say what is missing."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_answer_llm(question: str, chunks: list[dict], scope: list[str] | None = None) -> dict:
    """Generate a grounded answer through a configurable OpenAI-compatible API."""

    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER != "openai-compatible":
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    if not settings.LLM_API_KEY:
        raise LLMGenerationError("LLM API key is not configured.")

    body = {
        "model": settings.LLM_MODEL,
        "messages": _build_messages(question=question, chunks=chunks, scope=scope),
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
        with request.urlopen(
            req,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            context=_build_ssl_context(),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:  # pragma: no cover - best-effort diagnostics
            error_body = ""
        detail = f"LLM HTTP error: {exc.code}"
        if error_body:
            detail = f"{detail} - {error_body[:500]}"
        raise LLMGenerationError(detail) from exc
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise LLMGenerationError(
            f"LLM request failed: {exc.__class__.__name__}: {exc}"
        ) from exc

    choices = payload.get("choices") or []
    if not choices:
        raise LLMGenerationError("LLM response has no choices.")

    message = choices[0].get("message", {})
    answer = (message.get("content") or "").strip()
    if not answer:
        raise LLMGenerationError("LLM response was empty.")

    _validate_grounded_example_output(question=question, answer=answer, chunks=chunks)

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.82,
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
    }
