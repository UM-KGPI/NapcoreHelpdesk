from __future__ import annotations


def map_evidence(answer_id: str, chunks: list[dict]) -> list[str]:
    """Return stable evidence link identifiers for trace payloads."""

    return [f"el-{answer_id}-{index + 1}" for index, _ in enumerate(chunks)]
