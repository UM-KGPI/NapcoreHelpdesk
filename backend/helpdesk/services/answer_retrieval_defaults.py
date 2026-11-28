"""What the answer endpoints ask retrieval for when a request does not say otherwise.

The web page sends the same values (frontend/src/App.tsx: retrievalTopK 6, retrievalMinScore 0.62). They
live here so the endpoints and the retrieval benchmark's --app-conditions mode read one place.
"""
from __future__ import annotations

from django.conf import settings

ANSWER_RETRIEVAL_TOP_K = 6
ANSWER_RETRIEVAL_MIN_SCORE = 0.62
ANSWER_MAX_CITATIONS = 5


def answer_min_evidence_results() -> int:
    """As many evidence blocks as the answer prompt shows, so a lone chunk above the score threshold
    does not leave the answer with one block (see retrieve_chunks_with_trace)."""
    return max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 6)))
