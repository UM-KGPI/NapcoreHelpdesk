"""
Policy-based content filtering for questions and answer candidates.

Evaluates questions and proposed answers against configured policy rules
before they are served or stored. A policy violation is raised as a signal
that the orchestration layer converts into an abstention response.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-10-18
"""

from __future__ import annotations

from django.conf import settings

from helpdesk.services.ontology_evidence import TRANSMODEL_SOURCE_URL
from helpdesk.services.repository_urls import canonical_repository_url


_STRONG_CLAIM_MARKERS = (
    "always",
    "never",
    "guarantee",
    "guarantees",
    "fully compliant",
    "compliant",
    "must",
    "shall",
)

def _normalize_repository_url(raw_url: str) -> str:
    """Normalize citation URLs to repository roots for allow-list checks."""

    return canonical_repository_url(raw_url)


def _is_generated_ontology_source(raw_url: str) -> bool:
    """True for the generated Transmodel ontology file cited as definition evidence.

    It lives in this project's own repository, which is not an approved source repository, so it is
    matched by its exact file URL and not by repository.
    """

    return raw_url.split("#", 1)[0].split("?", 1)[0] == TRANSMODEL_SOURCE_URL


def evaluate_policy(answer_text: str, citations: list[dict]) -> dict:
    """Validate evidence grounding and repository allow-list policy."""

    approved_repositories = getattr(settings, "ALLOWED_SOURCE_REPOSITORIES", set())

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

    approved_canonical = {canonical_repository_url(url) for url in approved_repositories}
    for citation in citations:
        if _is_generated_ontology_source(citation.get("repositoryUrl", "")):
            continue
        repo_url = _normalize_repository_url(citation.get("repositoryUrl", ""))
        if repo_url not in approved_canonical:
            return {
                "allowed": False,
                "reason": "POLICY_BLOCK",
                "review_required": True,
            }

    if getattr(settings, "POLICY_STRICT_CLAIM_GUARD", False):
        lowered = answer_text.lower()
        has_strong_claim = any(marker in lowered for marker in _STRONG_CLAIM_MARKERS)
        if has_strong_claim and len(citations) < 2:
            return {
                "allowed": False,
                "reason": "INSUFFICIENT_EVIDENCE",
                "review_required": True,
            }

    return {
        "allowed": True,
        "reason": None,
        "review_required": True,
    }
