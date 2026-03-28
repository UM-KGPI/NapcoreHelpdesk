from __future__ import annotations


def _contains_any(text: str, tokens: list[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def match_faq(question: str, scope: list[str] | None = None) -> dict | None:
    """Return a deterministic FAQ candidate for known intent patterns."""

    normalized_scope = set(scope or [])

    if _contains_any(question, ["timetable", "netex", "service frame"]):
        return {
            "faq_entry_id": "faq-netex-timetable-001",
            "confidence": 0.93,
            "answer": (
                "For NeTEx timetable exchange, start by defining ServiceFrame and "
                "TimetableFrame, then validate profile constraints before publishing."
            ),
            "citations": [
                {
                    "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
                    "commitSha": "placeholder",
                    "sourcePath": "README.md",
                    "chunkId": "faq-c-001",
                    "label": "NeTEx repository overview",
                }
            ],
            "review_required": False,
            "scope_match": "NeTEx" in normalized_scope or not normalized_scope,
        }

    if _contains_any(question, ["siri", "real-time", "realtime"]):
        return {
            "faq_entry_id": "faq-siri-realtime-001",
            "confidence": 0.89,
            "answer": (
                "For SIRI real-time exchange, align message subsets with agreed profile "
                "and publish monitored entities with stable identifiers."
            ),
            "citations": [
                {
                    "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
                    "commitSha": "placeholder",
                    "sourcePath": "README.md",
                    "chunkId": "faq-c-002",
                    "label": "Related profile guidance",
                }
            ],
            "review_required": True,
            "scope_match": "SIRI" in normalized_scope or not normalized_scope,
        }

    return None
