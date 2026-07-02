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
import logging
import re
import ssl
from collections.abc import Generator
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)

from helpdesk.services.question_preprocessor import detect_question_language


class LLMGenerationError(Exception):
    """Raised when LLM generation cannot be completed safely."""


FENCED_CODE_BLOCK_PATTERN = re.compile(r"```([A-Za-z0-9_+-]*)\n(.*?)```", re.DOTALL)
CITATION_PATTERN = re.compile(r"\[E(\d+)\]")


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


def _validate_citations_to_chunks(answer: str, chunks: list[dict]) -> None:
    """
    Verify that each [E#] citation references a valid chunk index (1 to N).
    """
    citations = CITATION_PATTERN.findall(answer)
    if not citations:
        return  # No citations, nothing to validate

    max_chunk_idx = len(chunks)
    for citation_str in set(citations):
        try:
            citation_num = int(citation_str)
            if citation_num < 1 or citation_num > max_chunk_idx:
                raise LLMGenerationError(
                    f"Citation [E{citation_num}] is out of range. Valid citations: [E1] through [E{max_chunk_idx}]."
                )
        except ValueError as e:
            raise LLMGenerationError(f"Invalid citation format: {e}")


# Strong terms: specific enough that a match is meaningful evidence of grounding.
_STRONG_TERM_PATTERN = re.compile(
    r"`([^`]{4,})`"                                   # backtick-quoted identifiers
    r'|"([A-Za-z0-9_.:/\\@#-]{6,})"'                 # double-quoted technical strings (≥6 chars)
    r"|([A-Za-z0-9]{2,}:[A-Za-z0-9@_./-]{3,})"       # namespaced ids, e.g. stg:SCWW@86, netex:Line
    r"|([A-Za-z0-9_.-]{3,}-[A-Za-z0-9_.-]{2,})"      # hyphenated identifiers, e.g. 93-RED-y11-1
    r"|([A-Za-z0-9_-]+\.(?:xsd|xml|yaml|json|ttl))"  # file names with known extensions
)

# Weak terms: PascalCase/camelCase element names that appear across many chunks.
_WEAK_TERM_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z0-9]{2,}[A-Z][A-Za-z0-9]*)"   # PascalCase / camelCase
)

# Terms so generic they appear in virtually every NeTEx/standards document and
# must never be used as the sole grounding evidence for a citation.
_UBIQUITOUS_TERMS = frozenset({
    "netex", "nete", "opra", "siri", "datex", "transmodel", "nits",
    "line", "route", "stop", "trip", "service", "journey",
})


def _classify_terms(sentence: str) -> tuple[list[str], list[str]]:
    """
    Return (strong_terms, weak_terms) extracted from a sentence.

    Strong terms are specific identifiers unlikely to appear across many chunks
    (file names, namespaced IDs, hyphenated IDs, backtick-quoted strings).
    Weak terms are PascalCase/camelCase element names that may appear anywhere.
    """
    strong: list[str] = []
    for match in _STRONG_TERM_PATTERN.finditer(sentence):
        term = next((g for g in match.groups() if g), None)
        if term and len(term) >= 4 and term.lower() not in _UBIQUITOUS_TERMS:
            strong.append(term)

    weak: list[str] = []
    seen = set(t.lower() for t in strong)
    for match in _WEAK_TERM_PATTERN.finditer(sentence):
        term = match.group(1)
        if term and len(term) >= 4 and term.lower() not in _UBIQUITOUS_TERMS and term.lower() not in seen:
            weak.append(term)
            seen.add(term.lower())

    return list(dict.fromkeys(strong)), list(dict.fromkeys(weak))


def _extract_key_terms(sentence: str) -> list[str]:
    """Extract technical identifiers from a sentence for citation grounding checks."""
    strong, weak = _classify_terms(sentence)
    return list(dict.fromkeys(strong + weak))


def _validate_citation_grounding(answer: str, chunks: list[dict]) -> None:
    """
    Verify that each [E#] citation is grounded in the referenced chunk's text.

    For every sentence containing [E#] citations the check requires:
    - If the sentence contains STRONG terms (file names, namespaced/hyphenated
      IDs): at least one strong term must appear in the cited chunk. A match on
      only weak/generic terms (e.g. "NeTEx", "LineRef") is NOT sufficient when
      strong terms are present — this prevents hallucinated file names from
      passing because a generic standard name happens to match.
    - If the sentence contains ONLY weak terms: at least one weak term must
      appear in the cited chunk.

    Raises LLMGenerationError if a citation cannot be grounded.
    """
    # Split on sentence boundaries; keep trailing punctuation with its sentence.
    sentences = re.split(r"(?<=[.!?\u0029])\s+", answer.replace("\n", " "))

    for sentence in sentences:
        found_citations = CITATION_PATTERN.findall(sentence)
        if not found_citations:
            continue

        clean = CITATION_PATTERN.sub("", sentence)
        strong_terms, weak_terms = _classify_terms(clean)
        if not strong_terms and not weak_terms:
            continue  # No checkable technical terms — skip grounding check

        for citation_str in found_citations:
            idx = int(citation_str) - 1
            if idx < 0 or idx >= len(chunks):
                continue  # Range already rejected by _validate_citations_to_chunks

            chunk = chunks[idx]
            chunk_text_lower = str(chunk.get("text", "")).lower()
            chunk_source_lower = str(chunk.get("sourcePath", "")).lower()
            haystack = chunk_text_lower + " " + chunk_source_lower

            if strong_terms:
                # Strong terms present: require at least one strong match.
                # A weak-only match is not accepted — it would allow hallucinated
                # file names/IDs to pass because a generic term like "NeTEx" matches.
                grounded = any(term.lower() in haystack for term in strong_terms)
            else:
                grounded = any(term.lower() in haystack for term in weak_terms)

            if not grounded:
                raise LLMGenerationError(
                    f"Citation [E{citation_str}] does not ground the claim: "
                    f"'{sentence[:150].strip()}'. "
                    f"Cited chunk source: '{chunk.get('sourcePath', 'unknown')}'. "
                    f"Strong terms checked: {strong_terms[:4]}. Weak terms checked: {weak_terms[:4]}. "
                    "The LLM may have cited the wrong evidence block or hallucinated content."
                )


_RAW_FILENAME_PATTERN = re.compile(
    r"\b[A-Za-z0-9_][A-Za-z0-9_.\-]*\.(?:xml|xsd|yaml|yml|json|ttl|csv|rdf|owl)\b"
)


def _validate_no_raw_filenames(answer: str) -> None:
    """
    Reject answers that contain raw file names in prose (e.g. 'NeTEx_01.xml').

    The LLM must reference all sources exclusively via [E#] citation markers.
    Bare file names are banned even when they match an evidence source path —
    the reader must follow the [E#] link to discover the actual file, keeping
    answers traceable and preventing hallucinated-but-plausible file names from
    slipping through.

    Fenced code blocks are excluded — verbatim XML/JSON quoted from evidence
    may legitimately contain file names inside attributes or comments.
    """
    clean = FENCED_CODE_BLOCK_PATTERN.sub("", answer)
    matches = _RAW_FILENAME_PATTERN.findall(clean)
    if matches:
        raise LLMGenerationError(
            f"Answer contains raw file name(s) {matches[:4]} — sources must be "
            "referenced exclusively via [E#] citation markers, never by file name."
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
    all_candidates: list[dict] | None = None,
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

    # Build candidate reference index from all candidates (if provided)
    # This tells the LLM what sources are available in the database
    candidate_index = ""
    if all_candidates:
        candidate_lines = []
        for idx, candidate in enumerate(all_candidates[:20], start=1):  # Limit to top 20 for brevity
            source_path = candidate.get("sourcePath", "unknown")
            label = candidate.get("label", "")
            score = candidate.get("score", 0)
            label_display = f" - {label}" if label else ""
            candidate_lines.append(f"[C{idx}] {source_path}{label_display} (score: {score:.2f})")
        if candidate_lines:
            candidate_index = "AVAILABLE CANDIDATE REFERENCES (in database):\n" + "\n".join(candidate_lines) + "\n\n"

    # Detect the language from the question text itself rather than trusting the
    # client-supplied `language` (often just the browser/OS locale, unrelated to
    # what the user actually typed). With thinking mode disabled, the model has
    # no reasoning step of its own to fall back on for "detect the language"
    # instructions, so an explicit target language must be given here.
    detected_language = detect_question_language(question)
    effective_language = detected_language or language

    _lang = (effective_language or "").strip().lower()
    if _lang and _lang not in ("en", "english"):
        language_instruction = (
            f" Respond in {effective_language}. Keep technical terms, class names, XML tags, and identifiers in English."
        )
    else:
        language_instruction = (
            " Detect the language of the question and respond in that same language."
            " Keep technical terms, class names, XML tags, and identifiers in English."
        )
    system_prompt = (
        "You are a standards helpdesk assistant. You have access to EXACTLY the evidence blocks listed below. "
        "CRITICAL RULES:\n"
        "1. ONLY reference information that appears in the provided evidence blocks [E1] through [E#]\n"
        "2. EVERY factual claim MUST be followed by a citation [E#] to the specific block containing that information\n"
        "3. Do NOT use any knowledge from your training data. Do NOT reference standards, examples, or concepts not in the provided blocks or candidate index\n"
        "4. If you recognize a source from your training (e.g., a known file or standard example) but it is not in [E#] or the candidate index, do NOT mention it\n"
        "5. If you cannot answer from the provided evidence, say 'This information is not in the provided evidence blocks'\n"
        "6. Do NOT paraphrase or infer beyond what is explicitly stated in the evidence\n"
        "7. Stay within the requested standards scope\n"
        "8. Do NOT write file names (e.g. file.xml, schema.xsd) anywhere in the answer prose — reference all sources ONLY as [E#] citations\n"
        f"\nRespond in 4-7 concise sentences with explicit [E#] citations for every claim.{language_instruction}"
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
        f"{candidate_index}"
        f"AVAILABLE EVIDENCE BLOCKS (only these may be cited):\n{context}\n\n"
        "STEP 1 — EVIDENCE MAPPING (do this silently before writing):\n"
        "For each fact you plan to state, identify the exact phrase in the evidence block that supports it. "
        "If you cannot find supporting text in a specific block, do NOT cite that block — instead say "
        "'This is not in the provided evidence'. Do NOT cite sources from the candidate index unless they are also in [E#] evidence blocks.\n\n"
        "STEP 2 — WRITE YOUR ANSWER:\n"
        "- Answer ONLY using information from the evidence blocks above\n"
        "- Cite each fact with [E#] where # is the block number whose text contains that fact\n"
        "- Do NOT cite [E1] for information that is only in [E2], or vice versa\n"
        "- Do NOT reference anything outside these blocks or the candidate index\n"
        "- Do NOT write file names anywhere in the answer — use only [E#] citation markers to reference sources\n"
        "- If a block is a schema definition file (.xsd), describe it as a 'definition', not an 'example'\n"
        "- If a block is an XML/JSON example file (.xml), describe it as an 'example'\n"
        "- If a requested detail is not in the evidence, explicitly state 'This is not in the provided evidence'\n\n"
        "Write your answer:"
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
        # Reasoning models (e.g. qwen3) can consume the entire token budget on
        # hidden chain-of-thought before emitting any answer content, leaving
        # the response empty. Disable thinking mode to get direct answers.
        "chat_template_kwargs": {"enable_thinking": False},
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
def _run_llm_attempt(
    question: str,
    chunks: list[dict],
    messages: list[dict],
    request_targets: list[dict],
) -> str:
    """Execute one LLM call and validate the answer.  Returns the validated answer text."""
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
                except Exception:  # pragma: no cover
                    error_body = ""
                detail = f"LLM HTTP error: {exc.code}"
                if error_body:
                    detail = f"{detail} - {error_body[:500]}"
                last_error = detail
            except Exception as exc:  # pragma: no cover
                last_error = f"LLM request failed: {exc.__class__.__name__}: {exc}"
    except Exception as exc:
        raise LLMGenerationError(str(exc)) from exc

    if payload is None:
        raise LLMGenerationError(last_error or "LLM request failed.")

    choices = payload.get("choices") or []
    if not choices:
        raise LLMGenerationError("LLM response has no choices.")

    answer = (choices[0].get("message", {}).get("content") or "").strip()
    if not answer:
        raise LLMGenerationError("LLM response was empty.")

    _validate_citations_to_chunks(answer=answer, chunks=chunks)
    _validate_citation_grounding(answer=answer, chunks=chunks)
    _validate_no_raw_filenames(answer=answer)
    return answer


def _append_feedback_message(messages: list[dict], rejected_answer: str, error_msg: str) -> list[dict]:
    """Return a new messages list with a feedback turn appended for retry."""
    feedback = (
        f"Your previous answer was rejected by the grounding validator.\n"
        f"Rejected answer: {rejected_answer[:600]}\n"
        f"Reason: {error_msg[:300]}\n\n"
        "Please rewrite the answer following ALL rules strictly:\n"
        "- Use ONLY [E#] markers to reference sources — no file names, no invented identifiers\n"
        "- Only cite [E#] for a claim when that block's text directly contains the information\n"
        "- If the evidence does not support a claim, omit it or say 'This is not in the provided evidence'"
    )
    return messages + [
        {"role": "assistant", "content": rejected_answer},
        {"role": "user", "content": feedback},
    ]


def generate_answer_llm(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    faq_hint: str | None = None,
    language: str | None = None,
) -> dict:
    """Generate a grounded answer through a configurable OpenAI-compatible API.

    Attempts generation up to twice: the first attempt uses the standard prompt;
    if a grounding validator rejects the answer, a second attempt is made with
    explicit feedback explaining exactly what was wrong.  Both the rejected answer
    and the rejection reason are returned in the result dict for trace logging.
    """

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

    rejected_answer: str | None = None
    rejection_reason: str | None = None

    # First attempt
    try:
        answer = _run_llm_attempt(question=question, chunks=chunks, messages=messages, request_targets=request_targets)
    except LLMGenerationError as first_error:
        rejected_answer = first_error.args[0] if first_error.args else str(first_error)
        rejection_reason = str(first_error)
        logger.warning(
            "LLM first attempt rejected by validator; retrying with feedback. Reason: %s",
            rejection_reason[:200],
            extra={"question": question[:120]},
        )
        # Second attempt with explicit correction feedback
        retry_messages = _append_feedback_message(
            messages=messages,
            rejected_answer=rejected_answer,
            error_msg=rejection_reason,
        )
        answer = _run_llm_attempt(
            question=question, chunks=chunks, messages=retry_messages, request_targets=request_targets
        )
        # If this also raises, propagate to the caller

    _validate_grounded_example_output(question=question, answer=answer, chunks=chunks)

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.82,
        "provider": settings.LLM_PROVIDER,
        "model": (request_targets[0]["model"]),
        "rejected_answer": rejected_answer,
        "rejection_reason": rejection_reason,
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
        # See _request_chat_completion: avoid reasoning models exhausting the
        # token budget on hidden chain-of-thought before any content is sent.
        "chat_template_kwargs": {"enable_thinking": False},
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

    All tokens are buffered and validated before being yielded to the caller.
    This prevents the 'answer shows then disappears' pattern that occurs when
    validation fails after tokens have already been sent to the client.
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

    # Buffer all tokens before yielding any — validation must pass the full
    # answer before the client receives a single character, so a failed check
    # never produces a visible-then-vanishing answer.
    def _collect_stream(active_messages: list[dict]) -> str:
        collected: list[str] = []
        try:
            for delta in _stream_request_chat_completion(
                api_base_url=primary_base_url,
                api_key=primary_api_key,
                model=settings.LLM_MODEL,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                messages=active_messages,
            ):
                collected.append(delta)
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
        text = "".join(collected)
        if not text.strip():
            raise LLMGenerationError("LLM stream response was empty.")
        return text

    # First attempt
    rejected_answer: str | None = None
    rejection_reason: str | None = None
    try:
        full_answer = _collect_stream(messages)
        _validate_citations_to_chunks(answer=full_answer, chunks=chunks)
        _validate_citation_grounding(answer=full_answer, chunks=chunks)
        _validate_no_raw_filenames(answer=full_answer)
        _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks)
    except LLMGenerationError as first_error:
        rejected_answer = full_answer if "full_answer" in dir() else ""
        rejection_reason = str(first_error)
        logger.warning(
            "Stream first attempt rejected; retrying with feedback. Reason: %s",
            rejection_reason[:200],
            extra={"question": question[:120]},
        )
        retry_messages = _append_feedback_message(
            messages=messages,
            rejected_answer=rejected_answer,
            error_msg=rejection_reason,
        )
        full_answer = _collect_stream(retry_messages)
        _validate_citations_to_chunks(answer=full_answer, chunks=chunks)
        _validate_citation_grounding(answer=full_answer, chunks=chunks)
        _validate_no_raw_filenames(answer=full_answer)
        _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks)

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

    # Validation passed — now yield tokens so the client receives only valid content.
    for delta in full_answer:
        yield ("token", delta)

    yield (
        "done",
        {
            "answer": full_answer,
            "confidence": confidence,
            "review_required": confidence < 0.82,
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "rejected_answer": rejected_answer,
            "rejection_reason": rejection_reason,
        },
    )
