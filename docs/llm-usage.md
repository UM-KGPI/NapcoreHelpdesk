# LLM Usage

LLM usage in this project is intentionally limited.

## Allowed LLM responsibilities

1. Parse intent and routing hints from the user question.
2. Compose the final answer from retrieved evidence.

## Not allowed

- Generating unsupported factual claims from model memory.
- Bypassing retrieval evidence and citation requirements.
- Expanding repository scope beyond approved sources.

## Controller and narration split

- Controller path: intent parsing and route/planning signals.
- Narration path: grounded answer composition using retrieved evidence.

## Guardrails

- FAQ-first, RAG-fallback runtime behavior.
- Citation-required responses for grounded output.
- Abstention when evidence is insufficient.
- Editorial review workflow for quality control before publication.

## Operational resilience

Both LLM paths call through a shared model-recovery layer
(`backend/helpdesk/services/llm_model_recovery.py`) that self-heals from
gateway model-alias drift: it proactively checks the gateway's live model
list before the first call in a process, and falls back to parsing the
gateway's own rejection error on any call that still fails. See
[Recent updates](recent-updates.md) for the incident this was built to
prevent.

Check current status — configured vs. gateway-authorized model, live
reachability, and whether the self-heal has already corrected anything —
at `GET /health/llm`. Public, unauthenticated, same as `/health/live` and
`/health/ready`.
