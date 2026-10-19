"""
Canonical repository URLs for the indexed standards.

The same GitHub repository can be reached under more than one URL (mirrors and
renames). Indexing stores the repository URL on every chunk and includes it in
the chunk id, so two spellings of one repository would index two full copies of
the same files. Everything that stores or compares a repository URL goes
through canonical_repository_url so each repository has exactly one spelling.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-18  |  Modified: 2026-10-18
"""

from __future__ import annotations

from urllib.parse import urlparse


REPOSITORY_ALIASES = {
    # NeTEx canonical mirror aliases used by citation URL fallback logic.
    "https://github.com/transmodelecosystem/netex": "https://github.com/TransmodelEcosystem/NeTEx",
    "https://github.com/netex-cen/netex": "https://github.com/TransmodelEcosystem/NeTEx",
    # SIRI: the main source is TransmodelEcosystem/SIRI; SIRI-CEN/SIRI redirects there.
    "https://github.com/transmodelecosystem/siri": "https://github.com/TransmodelEcosystem/SIRI",
    "https://github.com/siri-cen/siri": "https://github.com/TransmodelEcosystem/SIRI",
    # OpRa: OpRa-CEN/OpRa is the same GitHub repository (same id) as TransmodelEcosystem/OpRa.
    "https://github.com/transmodelecosystem/opra": "https://github.com/TransmodelEcosystem/OpRa",
    "https://github.com/opra-cen/opra": "https://github.com/TransmodelEcosystem/OpRa",
}


def canonical_repository_url(raw_url: str) -> str:
    """Normalize a repository or GitHub file URL to its canonical repository root.

    Supports both repository URLs and GitHub file URLs such as
    https://github.com/<owner>/<repo>/blob/<sha>/<path>. Known aliases map to
    the canonical spelling; any other URL keeps its own spelling.
    """

    parsed = urlparse(raw_url)
    if not parsed.scheme or not parsed.netloc:
        return raw_url.rstrip("/")

    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower() == "github.com" and len(path_parts) >= 2:
        owner, repo = path_parts[0], path_parts[1]
        normalized = f"{parsed.scheme}://{parsed.netloc}/{owner}/{repo}"
        return REPOSITORY_ALIASES.get(normalized.lower(), normalized)

    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return REPOSITORY_ALIASES.get(normalized.lower(), normalized)
