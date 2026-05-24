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
