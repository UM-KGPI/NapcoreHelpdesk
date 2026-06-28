"""
Publishes approved editorial queue items as canonical FAQ entries.

Converts an approved EditorialQueueItem into a persistent FAQEntry and
FAQVersion for use by the FAQ-first answer path. Re-publishing the same
question event is idempotent — existing entries are updated in place.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-05-15  |  Modified: 2026-06-28
"""

from __future__ import annotations

from hashlib import sha1
import re

from helpdesk.models import EditorialQueueItem, FAQEntry, FAQVersion
from helpdesk.services.question_parsing import parse_question_to_semantic_query

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_LOW_VALUE_TOKENS = {
    "about",
    "could",
    "does",
    "explain",
    "help",
    "into",
    "please",
    "should",
    "their",
    "there",
    "these",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
}


def _normalize_scope(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        candidate = item.strip()
        if not candidate or candidate in normalized:
            continue
        normalized.append(candidate)
    return normalized


def _extract_keyword_tokens(*, question: str, semantic_terms: list[str]) -> list[str]:
    tokens = list(semantic_terms)
    seen = {token.lower() for token in tokens}
    for token in _TOKEN_PATTERN.findall(question.lower()):
        if len(token) < 4 or token in _LOW_VALUE_TOKENS:
            continue
        if token in seen:
            continue
        tokens.append(token)
        seen.add(token)
        if len(tokens) >= 12:
            break
    return tokens


def _build_faq_entry_id(*, normalized_intent: str, standards_scope: list[str]) -> str:
    fingerprint = f"{normalized_intent}|{'|'.join(sorted(standards_scope))}"
    return f"faq-auto-{sha1(fingerprint.encode('utf-8')).hexdigest()[:12]}"


def _build_citations(queue_item: EditorialQueueItem) -> list[dict]:
    citations: list[dict] = []
    for link in queue_item.question_event.answer_evidence_links.all().order_by("created_at"):
        citations.append(
            {
                "repositoryUrl": link.repository_url,
                "commitSha": link.commit_sha,
                "sourcePath": link.source_path,
                "chunkId": link.chunk_id,
                "label": link.label,
            }
        )
    return citations


def publish_queue_item_to_faq(*, queue_item: EditorialQueueItem) -> FAQVersion:
    """Persist a published editorial answer as a reusable FAQ version."""

    question_event = queue_item.question_event
    question = (question_event.question or "").strip()
    answer = (question_event.answer or "").strip()
    if not question or not answer:
        raise ValueError("Published queue item is missing question or answer content")

    semantic = parse_question_to_semantic_query(
        text=question,
        requested_scope=question_event.standards_scope,
    )

    standards_scope = _normalize_scope(question_event.standards_scope)
    normalized_intent = f"{semantic.intent} {semantic.core_concept}".strip()
    if normalized_intent == "unknown nits:unknown-concept":
        normalized_intent = question.lower()[:512]

    faq_entry_id = question_event.matched_faq_entry_id or _build_faq_entry_id(
        normalized_intent=normalized_intent,
        standards_scope=standards_scope,
    )
    keyword_tokens = _extract_keyword_tokens(question=question, semantic_terms=semantic.original_terms)

    entry, _ = FAQEntry.objects.update_or_create(
        faq_entry_id=faq_entry_id,
        defaults={
            "normalized_intent": normalized_intent,
            "standards_scope": standards_scope,
            "keyword_tokens": keyword_tokens,
            "is_active": True,
        },
    )

    latest = FAQVersion.objects.filter(faq_entry=entry).order_by("-version").first()
    next_version = (latest.version + 1) if latest else 1

    return FAQVersion.objects.create(
        faq_entry=entry,
        version=next_version,
        answer=answer,
        citations=_build_citations(queue_item),
        confidence=float(question_event.confidence or 0.85),
        review_required=False,
        is_published=True,
    )
