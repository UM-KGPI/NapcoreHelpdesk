"""
Scheduled refresh of the indexed standards repositories.

For each configured repository (NeTEx, SIRI, OpRa, mobilityDCAT-AP): fetch the remote default
branch into a persistent checkout, then run the incremental index with prune using that
repository's own profile and canonical URL. The checkout is a real git clone, so chunks record the
real commit SHA instead of "unknown". A repository that publishes its own ontology (mobilityDCAT-AP)
also gets that file loaded into its GraphDB graph when it changed. Every repository gets its own
result; one failing repository does not stop the others, and the caller learns about the failure.

The editor's Harvest & Index tab runs the same refresh for one repository (tasks.harvest_source).

The CI benchmark pins each repository to a commit and is not affected by this refresh.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-18  |  Modified: 2026-11-03
"""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from helpdesk.models import OntologyAssetVersion
from helpdesk.services.index_builder import index_repository, prune_alias_spellings
from helpdesk.services.ontology_registry import _content_hash, _extract_version_info
from helpdesk.services.repository_urls import canonical_repository_url

logger = logging.getLogger(__name__)

GIT_TIMEOUT_SECONDS = 900
# Pruning removes chunks of files missing from the checkout, so an empty or half-written
# checkout must never reach the index. The smallest indexed repository has about 70 files.
MIN_CHECKOUT_FILES = 20
LOCK_FILE_NAME = ".refresh.lock"


class SourceRefreshError(RuntimeError):
    """A repository could not be refreshed."""


@dataclass(frozen=True)
class SourceOntology:
    """An ontology the repository itself publishes, loaded as it is (no generation, no edits)."""

    key: str  # OntologyAssetVersion.ontology_key, shown in answer traces
    path: str  # Turtle file, relative to the checkout
    graph_uri: str


@dataclass(frozen=True)
class SourceRepository:
    name: str
    url: str  # identity stored on every chunk (the canonical repository URL)
    profile: str  # index profile under helpdesk/index_profiles
    clone_url: str = ""  # where to fetch from; defaults to url (tests use a local path)
    ontology: SourceOntology | None = None

    @property
    def fetch_url(self) -> str:
        return self.clone_url or self.url


MOBILITYDCAT_AP_ONTOLOGY = SourceOntology(
    key="mobilitydcat-ap",
    path="src/mobilitydcat-ap.ttl",
    graph_uri="https://napcore.eu/graph/standards/mobilitydcat-ap",
)


def configured_sources() -> list[SourceRepository]:
    """The repositories the knowledge base is built from."""

    return [
        SourceRepository("NeTEx", settings.SEED_REPO_NETEX, "netex"),
        SourceRepository("SIRI", settings.SEED_REPO_SIRI, "siri"),
        SourceRepository("OpRa", settings.SEED_REPO_OPRA, "opra"),
        SourceRepository(
            "mobilityDCAT-AP",
            settings.SEED_REPO_MOBILITYDCAT_AP,
            "mobilitydcat-ap",
            ontology=MOBILITYDCAT_AP_ONTOLOGY,
        ),
        SourceRepository("TN-ITS", settings.SEED_REPO_TNITS, "tn-its"),
    ]


def find_source(name: str) -> SourceRepository | None:
    wanted = name.strip().lower()
    return next((source for source in configured_sources() if source.name.lower() == wanted), None)


def _git(args: list[str], *, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip().splitlines()
        raise SourceRefreshError(f"git {args[0]} failed: {detail[-1] if detail else exc.returncode}") from exc
    except subprocess.TimeoutExpired as exc:
        raise SourceRefreshError(f"git {args[0]} timed out after {GIT_TIMEOUT_SECONDS} seconds") from exc
    return result.stdout.strip()


def _checkout_file_count(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file() and ".git" not in item.parts)


def sync_checkout(source: SourceRepository, checkout_root: Path) -> tuple[Path, str]:
    """Clone the repository if needed, else fetch it; return the checkout path and HEAD SHA.

    The checkout is shallow (depth 1) and always reset to the remote default branch.
    """

    path = checkout_root / source.name
    if (path / ".git").is_dir():
        _git(["fetch", "--depth", "1", "origin", "HEAD"], cwd=path)
        _git(["reset", "--hard", "FETCH_HEAD"], cwd=path)
        _git(["clean", "-fdx"], cwd=path)
    else:
        if path.exists() and any(path.iterdir()):
            raise SourceRefreshError(f"{path} exists but is not a git checkout; not touching it")
        checkout_root.mkdir(parents=True, exist_ok=True)
        _git(["clone", "--depth", "1", source.fetch_url, str(path)])

    sha = _git(["rev-parse", "HEAD"], cwd=path)
    files = _checkout_file_count(path)
    if files < MIN_CHECKOUT_FILES:
        raise SourceRefreshError(f"checkout has only {files} files; refusing to index it")
    return path, sha


# Uploading and reinferring a graph takes longer than the query timeout (GRAPHDB_TIMEOUT_SECONDS).
ONTOLOGY_UPLOAD_TIMEOUT_SECONDS = 120


def load_source_ontology(ontology: SourceOntology, checkout: Path, *, force: bool = False) -> dict:
    """Load the repository's ontology into its named graph when the file changed since the last load."""

    from helpdesk.services.graphdb_client import upload_named_graph_turtle

    file_path = checkout / ontology.path
    if not file_path.is_file():
        raise SourceRefreshError(f"ontology file {ontology.path} is missing from the checkout")
    content = file_path.read_text(encoding="utf-8")
    content_hash = _content_hash(content)
    row = {"key": ontology.key, "graph": ontology.graph_uri, "version": _extract_version_info(content)}
    if not settings.GRAPHDB_ENABLED or not settings.GRAPHDB_SPARQL_ENDPOINT:
        return {**row, "status": "skipped", "reason": "GraphDB is disabled"}
    previous = OntologyAssetVersion.objects.filter(ontology_key=ontology.key).first()
    if not force and previous and previous.content_hash == content_hash and previous.last_loaded_at:
        return {**row, "status": "unchanged"}

    upload_named_graph_turtle(
        endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
        repository=settings.GRAPHDB_REPOSITORY,
        graph_uri=ontology.graph_uri,
        turtle_content=content,
        username=getattr(settings, "GRAPHDB_USER", ""),
        password=getattr(settings, "GRAPHDB_PASSWORD", ""),
        timeout_seconds=ONTOLOGY_UPLOAD_TIMEOUT_SECONDS,
        replace=True,
    )
    OntologyAssetVersion.objects.update_or_create(
        ontology_key=ontology.key,
        defaults={
            "file_path": str(file_path),
            "graph_uri": ontology.graph_uri,
            "version": row["version"],
            "content_hash": content_hash,
            "graphdb_repository": settings.GRAPHDB_REPOSITORY,
            "last_loaded_at": timezone.now(),
        },
    )
    return {**row, "status": "loaded"}


def refresh_source(
    source: SourceRepository, checkout_root: Path, allowed_repositories: set[str], *, full: bool = False
) -> dict:
    """Fetch one repository, index it, and load its own ontology if it has one; return a result row."""

    path, sha = sync_checkout(source, checkout_root)
    stats = index_repository(
        repo_url=source.url,
        repo_path=path,
        allowed_repositories=allowed_repositories,
        profile=source.profile,
        incremental=not full,
        prune=True,
    )
    # After a successful index of the canonical URL, drop copies stored under an old spelling.
    alias_chunks_removed = prune_alias_spellings(canonical_repository_url(source.url))
    # The index ran first: a failed graph upload still leaves the text searchable, and the row fails.
    ontology = load_source_ontology(source.ontology, path, force=full) if source.ontology else None
    return {
        "repository": source.url,
        "profile": source.profile,
        "commit": sha,
        "mode": "full" if full else "incremental",
        "scanned_files": stats.scanned_files,
        "skipped_files": stats.skipped_files,
        "created_chunks": stats.created_chunks,
        "updated_chunks": stats.updated_chunks,
        "deleted_chunks": stats.deleted_chunks,
        "alias_chunks_removed": alias_chunks_removed,
        "ontology": ontology,
    }


def refresh_all_sources(
    sources: list[SourceRepository] | None = None,
    *,
    only: list[str] | None = None,
    full: bool = False,
    checkout_root: Path | None = None,
) -> dict:
    """Refresh each configured repository and report one result per repository.

    Returns {"status": "ok" | "partial" | "failed" | "skipped", "results": {name: row}}. A second
    refresh that starts while one is running is skipped (a lock file in the checkout directory).
    """

    sources = list(sources if sources is not None else configured_sources())
    if only:
        wanted = {name.lower() for name in only}
        sources = [source for source in sources if source.name.lower() in wanted]
    if not sources:
        return {"status": "failed", "reason": "no repositories selected", "results": {}}
    root = Path(checkout_root or settings.SOURCE_CHECKOUT_DIR)
    root.mkdir(parents=True, exist_ok=True)

    with open(root / LOCK_FILE_NAME, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logger.warning("Source refresh skipped: another refresh is running")
            return {"status": "skipped", "reason": "another refresh is running", "results": {}}

        results: dict[str, dict] = {}
        for source in sources:
            started = time.perf_counter()
            try:
                row = refresh_source(source, root, settings.ALLOWED_SOURCE_REPOSITORIES, full=full)
                row["status"] = "ok"
                logger.info("Source refresh %s ok: %s", source.name, row)
            except Exception as exc:  # one repository must not stop the others
                row = {"status": "failed", "repository": source.url, "error": f"{type(exc).__name__}: {exc}"}
                logger.exception("Source refresh %s failed", source.name)
            row["seconds"] = round(time.perf_counter() - started, 1)
            results[source.name] = row

    failed = [name for name, row in results.items() if row["status"] != "ok"]
    if not failed:
        status = "ok"
    elif len(failed) == len(results):
        status = "failed"
    else:
        status = "partial"
    return {"status": status, "results": results}
