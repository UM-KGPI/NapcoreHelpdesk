"""
LLM-based answer generation with synchronous and SSE streaming support.

Calls an OpenAI-compatible chat completion endpoint to synthesize answers
grounded in retrieved evidence chunks. Streaming delegates token deltas via
Server-Sent Events written directly into the Django response.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-29  |  Modified: 2026-06-28
"""

from __future__ import annotations

import json
import re
import ssl
from collections.abc import Generator
from urllib import error, request

from django.conf import settings


class LLMGenerationError(Exception):
    """Raised when LLM generation cannot be completed safely."""


FENCED_CODE_BLOCK_PATTERN = re.compile(r"```([A-Za-z0-9_+-]*)\n(.*?)```", re.DOTALL)


def _is_github_models_base_url(api_base_url: str) -> bool:
    base = (api_base_url or "").strip().lower()
    return "models.inference.ai.azure.com" in base


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


def _trim_chunk_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}\n...[truncated for latency]"


def _build_messages(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    max_chunks: int = 6,
    max_chars_per_chunk: int = 1800,
    faq_hint: str | None = None,
    language: str | None = None,
) -> list[dict]:
    context_lines = []
    for index, chunk in enumerate(chunks[:max_chunks], start=1):
        chunk_text = _trim_chunk_text(str(chunk.get("text", "")), max_chars=max_chars_per_chunk)
        context_lines.append(
            "\n".join(
                [
                    f"[E{index}] repository={chunk['repositoryUrl']}",
                    f"[E{index}] commit={chunk['commitSha']}",
                    f"[E{index}] source={chunk['sourcePath']}",
                    f"[E{index}] chunk={chunk['chunkId']}",
                    f"[E{index}] text={chunk_text}",
                ]
            )
        )

    context = "\n\n".join(context_lines)
    scope_text = ", ".join(scope) if scope else "all approved standards"

    _lang = (language or "").strip().lower()
    if _lang and _lang not in ("en", "english"):
        language_instruction = (
            f" Respond in {language}. Keep technical terms, class names, XML tags, and identifiers in English."
        )
    else:
        language_instruction = (
            " Detect the language of the question and respond in that same language."
            " Keep technical terms, class names, XML tags, and identifiers in English."
        )
    system_prompt = (
        "You are a standards helpdesk assistant. Prioritize provided evidence blocks and stay within the requested standards scope. "
        "Do not add external or uncited knowledge. Do not contradict evidence. "
        "If evidence is insufficient for claims that require citation, say that you cannot answer safely. "
        f"Respond in 4-7 concise sentences and include citation markers like [E1], [E2] for evidence-grounded statements.{language_instruction}"
    )
    if _question_requests_verbatim_example(question):
        system_prompt = (
            f"{system_prompt} "
            "For questions asking for examples or code: First, directly answer 'yes' or 'no' about availability. Then list the examples found in evidence with citations [E#]. "
            "When showing XML/JSON/YAML, include one fenced code block (```xml) of 6-20 lines from a single evidence block. "
            "Quote only verbatim excerpts from evidence blocks. Never synthesize or combine structures across sources. "
            "If asking for availability ('Is there any...?'), list all matching examples found in the evidence with their source paths and brief descriptions."
        )

    faq_section = ""
    if faq_hint:
        faq_section = (
            f"Editorial baseline (approved directional answer — enrich and ground it using the evidence blocks below, do not copy verbatim):\n{faq_hint}\n\n"
        )

    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Requested scope: {scope_text}\n\n"
        f"{faq_section}"
        f"Evidence blocks:\n{context}\n\n"
        "Write a scoped answer with explicit [E#] markers tied to evidence blocks only. "
        "If the evidence does not support the requested detail, explicitly say what is missing. "
    )

    if _question_requests_verbatim_example(question) and "?" in question and any(w in question.lower() for w in ["is there", "do you have", "any", "list"]):
        user_prompt += "(This question asks for examples: list ALL matching examples found in evidence with their source paths, then provide sample code if available.)"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _request_chat_completion(
    api_base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
    messages: list[dict],
) -> dict:
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = request.Request(
        url=f"{api_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )

    with request.urlopen(
        req,
        timeout=timeout_seconds,
        context=_build_ssl_context(),
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def generate_answer_llm(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    faq_hint: str | None = None,
    language: str | None = None,
) -> dict:
    """Generate a grounded answer through a configurable OpenAI-compatible API."""

    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER != "openai-compatible":
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    max_chunks = max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))
    max_chars_per_chunk = max(200, int(getattr(settings, "LLM_MAX_EVIDENCE_CHARS_PER_CHUNK", 1200)))
    messages = _build_messages(
        question=question,
        chunks=chunks,
        scope=scope,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
        faq_hint=faq_hint,
        language=language,
    )

    primary_base_url = (settings.LLM_API_BASE_URL or "").strip()
    primary_api_key = (settings.LLM_API_KEY or "").strip()

    request_targets = [
        {
            "api_base_url": primary_base_url,
            "api_key": primary_api_key,
            "model": settings.LLM_MODEL,
            "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        }
    ]

    # If the primary key cannot access GitHub Models, retry once with the
    # repository token.
    github_api_token = (getattr(settings, "GITHUB_API_TOKEN", "") or "").strip()
    if (
        _is_github_models_base_url(primary_base_url)
        and github_api_token
        and github_api_token != primary_api_key
    ):
        request_targets.append(
            {
                "api_base_url": primary_base_url,
                "api_key": github_api_token,
                "model": settings.LLM_MODEL,
                "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
            }
        )

    payload = None
    last_error = None
    try:
        for target in request_targets:
            try:
                payload = _request_chat_completion(
                    api_base_url=target["api_base_url"],
                    api_key=target["api_key"],
                    model=target["model"],
                    timeout_seconds=target["timeout_seconds"],
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    messages=messages,
                )
                break
            except error.HTTPError as exc:
                try:
                    error_body = exc.read().decode("utf-8")
                except Exception:  # pragma: no cover - best-effort diagnostics
                    error_body = ""
                detail = f"LLM HTTP error: {exc.code}"
                if error_body:
                    detail = f"{detail} - {error_body[:500]}"
                last_error = detail
            except Exception as exc:  # pragma: no cover - network/runtime dependent
                last_error = f"LLM request failed: {exc.__class__.__name__}: {exc}"
    except Exception as exc:
        raise LLMGenerationError(str(exc)) from exc

    if payload is None:
        raise LLMGenerationError(last_error or "LLM request failed.")

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
        "model": (payload.get("model") or request_targets[0]["model"]),
    }


def _stream_request_chat_completion(
    api_base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
    messages: list[dict],
) -> Generator[str, None, None]:
    """Yield raw token delta strings from an OpenAI-compatible streaming chat completion."""
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = request.Request(
        url=f"{api_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    with request.urlopen(req, timeout=timeout_seconds, context=_build_ssl_context()) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            payload_str = line[len("data:"):].strip()
            if payload_str == "[DONE]":
                break
            try:
                chunk = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta", {}).get("content") or ""
            if delta:
                yield delta


def stream_answer_llm(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    faq_hint: str | None = None,
    language: str | None = None,
) -> Generator[tuple[str, object], None, None]:
    """
    Generator yielding (event_type, payload) tuples for streaming narration.

    Yields:
        ("token", delta_str) — for each token from the LLM.
        ("done", metadata_dict) — once after all tokens, with answer metadata.

    Raises LLMGenerationError on setup failure, network error, or grounding
    validation failure.  If raised after tokens have already been yielded,
    the caller should emit an SSE error event so the client can discard the
    partial text.
    """
    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER != "openai-compatible":
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    primary_base_url = (settings.LLM_API_BASE_URL or "").strip()
    primary_api_key = (settings.LLM_API_KEY or "").strip()
    if not primary_base_url:
        raise LLMGenerationError("LLM API base URL is not configured.")

    max_chunks = max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))
    max_chars_per_chunk = max(200, int(getattr(settings, "LLM_MAX_EVIDENCE_CHARS_PER_CHUNK", 1200)))
    messages = _build_messages(
        question=question,
        chunks=chunks,
        scope=scope,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
        faq_hint=faq_hint,
        language=language,
    )

    deltas: list[str] = []
    try:
        for delta in _stream_request_chat_completion(
            api_base_url=primary_base_url,
            api_key=primary_api_key,
            model=settings.LLM_MODEL,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=messages,
        ):
            deltas.append(delta)
            yield ("token", delta)
    except error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""
        detail = f"LLM HTTP error: {exc.code}"
        if error_body:
            detail = f"{detail} - {error_body[:500]}"
        raise LLMGenerationError(detail) from exc
    except error.URLError as exc:
        raise LLMGenerationError(f"LLM stream request failed: {exc.reason}") from exc

    full_answer = "".join(deltas)
    if not full_answer.strip():
        raise LLMGenerationError("LLM stream response was empty.")

    _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks)

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

    yield (
        "done",
        {
            "answer": full_answer,
            "confidence": confidence,
            "review_required": confidence < 0.82,
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
        },
    )
