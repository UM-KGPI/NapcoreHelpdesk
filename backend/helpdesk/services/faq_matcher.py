from __future__ import annotations

from helpdesk.models import FAQEntry, FAQVersion


def _contains_any(text: str, tokens: list[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


DEFAULT_FAQS = [
    {
        "faq_entry_id": "faq-netex-timetable-001",
        "normalized_intent": "netex timetable exchange service frame",
        "standards_scope": ["NeTEx"],
        "keyword_tokens": ["timetable", "netex", "service frame"],
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
        "confidence": 0.93,
        "review_required": False,
    },
    {
        "faq_entry_id": "faq-siri-realtime-001",
        "normalized_intent": "siri realtime exchange profile",
        "standards_scope": ["SIRI"],
        "keyword_tokens": ["siri", "real-time", "realtime"],
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
        "confidence": 0.89,
        "review_required": True,
    },
]


def _seed_default_faqs() -> None:
    if FAQVersion.objects.filter(is_published=True).exists():
        return

    for payload in DEFAULT_FAQS:
        entry, _ = FAQEntry.objects.get_or_create(
            faq_entry_id=payload["faq_entry_id"],
            defaults={
                "normalized_intent": payload["normalized_intent"],
                "standards_scope": payload["standards_scope"],
                "keyword_tokens": payload["keyword_tokens"],
                "is_active": True,
            },
        )
        FAQVersion.objects.get_or_create(
            faq_entry=entry,
            version=1,
            defaults={
                "answer": payload["answer"],
                "citations": payload["citations"],
                "confidence": payload["confidence"],
                "review_required": payload["review_required"],
                "is_published": True,
            },
        )


def _faq_score(question: str, entry: FAQEntry) -> float:
    base_tokens = set(entry.keyword_tokens or [])
    if not base_tokens:
        base_tokens = {token for token in entry.normalized_intent.split() if len(token) > 2}
    if not base_tokens:
        return 0.0

    lower_question = question.lower()
    hits = sum(1 for token in base_tokens if token.lower() in lower_question)
    return hits / len(base_tokens)


def match_faq(question: str, scope: list[str] | None = None) -> dict | None:
    """Return highest-scoring published canonical FAQ candidate for the question."""

    _seed_default_faqs()

    normalized_scope = set(scope or [])

    candidates: list[tuple[float, FAQEntry, FAQVersion]] = []
    versions = (
        FAQVersion.objects.filter(is_published=True, faq_entry__is_active=True)
        .select_related("faq_entry")
        .order_by("faq_entry__faq_entry_id", "-version")
    )

    seen_entries: set[str] = set()
    for version in versions:
        if version.faq_entry.faq_entry_id in seen_entries:
            continue
        seen_entries.add(version.faq_entry.faq_entry_id)

        score = _faq_score(question=question, entry=version.faq_entry)
        if score <= 0:
            continue
        candidates.append((score, version.faq_entry, version))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, entry, version = candidates[0]

    entry_scope = set(entry.standards_scope or [])
    scope_match = bool(entry_scope.intersection(normalized_scope)) or not normalized_scope or not entry_scope

    return {
        "faq_entry_id": entry.faq_entry_id,
        "confidence": version.confidence,
        "answer": version.answer,
        "citations": version.citations,
        "review_required": version.review_required,
        "scope_match": scope_match,
    }
