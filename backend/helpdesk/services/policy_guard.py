from __future__ import annotations


APPROVED_REPOSITORIES = {
    "https://github.com/NeTEx-CEN/NeTEx",
}


def evaluate_policy(answer_text: str, citations: list[dict]) -> dict:
    """Validate evidence grounding and repository allow-list policy."""

    if not answer_text.strip():
        return {
            "allowed": False,
            "reason": "UNKNOWN",
            "review_required": False,
        }

    if not citations:
        return {
            "allowed": False,
            "reason": "INSUFFICIENT_EVIDENCE",
            "review_required": False,
        }

    for citation in citations:
        repo_url = citation.get("repositoryUrl")
        if repo_url not in APPROVED_REPOSITORIES:
            return {
                "allowed": False,
                "reason": "POLICY_BLOCK",
                "review_required": True,
            }

    return {
        "allowed": True,
        "reason": None,
        "review_required": True,
    }
