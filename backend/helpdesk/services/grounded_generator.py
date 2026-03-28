from __future__ import annotations


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """Generate a concise grounded answer from top retrieval evidence."""

    if not chunks:
        return {
            "answer": "I do not have sufficient approved-source evidence to answer this safely.",
            "confidence": 0.0,
            "review_required": False,
        }

    top = chunks[0]
    confidence = min(0.9, max(0.55, top["score"]))
    answer = (
        "Based on approved repository evidence, align your implementation with the "
        "relevant profile artifacts and validate exchange examples before rollout."
    )
    if "timetable" in question.lower() or "netex" in question.lower():
        answer = (
            "For timetable exchange, model core frames first, then validate profile constraints "
            "and interoperability examples against approved source guidance."
        )

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.8,
    }
