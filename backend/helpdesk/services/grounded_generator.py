"""
Deterministic answer generation from retrieved evidence chunks.

Assembles grounded answers by ranking and synthesizing retrieved source
chunks without LLM involvement. Used when the controller routes to the
deterministic-grounded generation profile.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations


def _repository_count(chunks: list[dict]) -> int:
    repositories = {
        str(chunk.get("repositoryUrl", "")).strip()
        for chunk in chunks
        if str(chunk.get("repositoryUrl", "")).strip()
    }
    return len(repositories)


def _build_minimal_grounded_answer(chunks: list[dict]) -> str:
    """Return a minimal deterministic fallback anchored in retrieved evidence."""
    marker_count = min(3, max(1, len(chunks)))
    marker_text = ", ".join(f"[E{index}]" for index in range(1, marker_count + 1))
    answer = (
        f"Based on retrieved approved-source evidence ({marker_text}), "
        "follow the relevant profile specification and validate implementation against published examples or test cases before deployment."
    )
    if _repository_count(chunks) >= 2:
        answer += " Evidence spans multiple repositories."
    return answer


def _build_example_list_answer(chunks: list[dict]) -> str:
    """Build answer listing example files found in retrieved evidence."""
    if not chunks:
        return "No examples found in available evidence."

    examples = []
    for i, chunk in enumerate(chunks[:5], 1):
        source_path = chunk.get("sourcePath", "").split("/")[-1]
        repo_url = chunk.get("repositoryUrl", "").split("/")[-1] if chunk.get("repositoryUrl") else "source"
        examples.append(f"[E{i}] {source_path} ({repo_url})")

    return f"Yes, the following examples are available:\n" + "\n".join(examples)


def _is_asking_for_examples(question: str) -> bool:
    """Detect if question asks for examples or availability."""
    q_lower = question.lower()
    return any(phrase in q_lower for phrase in ["example", "any", "is there", "do you have", "sample", "list"])


def _build_adaptive_answer(question: str, chunks: list[dict]) -> str:
    """
    Build a minimal deterministic fallback answer grounded in retrieved evidence.
    The primary generation path is expected to be LLM-first; this function exists
    as a resilient fallback when LLM generation is unavailable.
    """
    if _is_asking_for_examples(question):
        return _build_example_list_answer(chunks)
    return _build_minimal_grounded_answer(chunks)


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """
    Generate a deterministic grounded answer from top retrieval evidence.

    This is **not** an LLM call. It provides a minimal deterministic fallback:
    - Anchored in retrieved evidence metadata
    - Stable low-latency behavior during LLM failures
    - No domain-specific answer templates
    """

    if not chunks:
        return {
            "answer": "I do not have sufficient approved-source evidence to answer this safely.",
            "confidence": 0.0,
            "review_required": False,
        }

    top = chunks[0]
    # Confidence reflects retrieval score: higher relevance = higher confidence.
    # Capped at 0.9 for deterministic mode (leave room for LLM later) and floored at 0.55.
    confidence = min(0.9, max(0.55, top["score"]))

    # Build adaptive answer based on question patterns and chunk context.
    answer = _build_adaptive_answer(question=question, chunks=chunks)

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.8,
    }
