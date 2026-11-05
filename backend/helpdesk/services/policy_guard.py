"""
Policy-based content filtering for questions and answer candidates.

Evaluates questions and proposed answers against configured policy rules
before they are served or stored. A policy violation is raised as a signal
that the orchestration layer converts into an abstention response.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-11-01
"""

from __future__ import annotations

from django.conf import settings

from helpdesk.services.ontology_evidence import TRANSMODEL_SOURCE_URL
from helpdesk.services.inspire import is_inspire_url
from helpdesk.services.napcore_site import is_napcore_url
from helpdesk.services.regulations import is_regulation_url
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
    """True for the Transmodel definition evidence: the generated ontology file or a Transmodel class page.

    The file lives in this project's own repository, which is not an approved source repository, so it is
    matched by its exact file URL and not by repository. A class page is in the configured Transmodel HTML
    export (TRANSMODEL_HTML_BASE_URL), opened by GUID.
    """

    if raw_url.split("#", 1)[0].split("?", 1)[0] == TRANSMODEL_SOURCE_URL:
        return True
    html_base_url = getattr(settings, "TRANSMODEL_HTML_BASE_URL", "")
    return bool(html_base_url) and raw_url.startswith(f"{html_base_url}/index.htm?guid=")


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
        # EUR-Lex is not a repository; the acts are approved by being in the pinned list.
        if is_regulation_url(citation.get("repositoryUrl", "")):
            continue
        # napcore.eu is NAPCORE's own site; its documents are approved by being in the pinned list.
        if is_napcore_url(citation.get("repositoryUrl", "")):
            continue
        # The pinned INSPIRE specification and registry code lists are approved by being indexed from docs/inspire/.
        if is_inspire_url(citation.get("repositoryUrl", "")):
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
