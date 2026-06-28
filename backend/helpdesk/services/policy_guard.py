"""
Policy-based content filtering for questions and answer candidates.

Evaluates questions and proposed answers against configured policy rules
before they are served or stored. A policy violation is raised as a signal
that the orchestration layer converts into an abstention response.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

from django.conf import settings

from urllib.parse import urlparse


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

_REPOSITORY_ALIASES = {
    # NeTEx canonical mirror aliases used by citation URL fallback logic.
    "https://github.com/transmodelecosystem/netex": "https://github.com/TransmodelEcosystem/NeTEx",
    "https://github.com/netex-cen/netex": "https://github.com/TransmodelEcosystem/NeTEx",
}


def _normalize_repository_url(raw_url: str) -> str:
    """Normalize citation URLs to repository roots for allow-list checks.

    Supports both repository URLs and GitHub file URLs such as
    https://github.com/<owner>/<repo>/blob/<sha>/<path>.
    """

    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        return raw_url.rstrip("/")

    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower() == "github.com" and len(path_parts) >= 2:
        owner, repo = path_parts[0], path_parts[1]
        normalized = f"{parsed.scheme}://{parsed.netloc}/{owner}/{repo}"
        return _REPOSITORY_ALIASES.get(normalized.lower(), normalized)

    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return _REPOSITORY_ALIASES.get(normalized.lower(), normalized)


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

    for citation in citations:
        repo_url = _normalize_repository_url(citation.get("repositoryUrl", ""))
        if repo_url not in approved_repositories:
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
