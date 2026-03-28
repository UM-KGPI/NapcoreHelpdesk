from __future__ import annotations

import hashlib
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache

import yaml
from helpdesk.models import IndexedSourceFile, IndexRunMetric, SourceChunk


DEFAULT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".xml", ".json"}
# Profile YAML files define coarse path include/exclude filters by standard/domain.
INDEX_PROFILE_DIR = Path(__file__).resolve().parents[1] / "index_profiles"


@dataclass
class IndexStats:
    scanned_files: int = 0
    skipped_files: int = 0
    created_chunks: int = 0
    updated_chunks: int = 0
    deleted_chunks: int = 0


@lru_cache(maxsize=32)
def load_profile_rules(profile: str) -> dict:
    """Load include/exclude rules from helpdesk/index_profiles/<profile>.yaml."""
    profile_file = INDEX_PROFILE_DIR / f"{profile}.yaml"
    if not profile_file.exists():
        raise ValueError(
            f"Index profile '{profile}' not found in {INDEX_PROFILE_DIR}. "
            f"Create {profile}.yaml or use an existing profile."
        )

    with open(profile_file, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    include_rules = data.get("include") or []
    exclude_rules = data.get("exclude") or []
    if not isinstance(include_rules, list) or not isinstance(exclude_rules, list):
        raise ValueError(f"Invalid profile format in {profile_file}: include/exclude must be lists")

    return {
        "include": [str(item) for item in include_rules],
        "exclude": [str(item) for item in exclude_rules],
    }


def validate_repository_allowed(repo_url: str, allowed_repositories: set[str]) -> None:
    """Guardrail: only approved source repositories may enter the retrieval index."""
    if repo_url not in allowed_repositories:
        allowed = ", ".join(sorted(allowed_repositories))
        raise ValueError(f"Repository URL '{repo_url}' is not allow-listed. Allowed: {allowed}")


def current_commit_sha(repo_path: Path) -> str:
    """Resolve current git commit for traceability; fallback to 'unknown' for non-git dirs."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def infer_scope(source_path: str, chunk_text: str) -> list[str]:
    """Heuristic scope tagging for retrieval filtering and analytics."""
    scope = set()
    blob = f"{source_path}\n{chunk_text}".lower()
    if "netex" in blob:
        scope.add("NeTEx")
    if "siri" in blob:
        scope.add("SIRI")
    if "transmodel" in blob:
        scope.add("Transmodel")
    if "ojp" in blob or "opra" in blob:
        scope.add("OJP/OpRa")
    if "datex" in blob:
        scope.add("DATEX II")
    return sorted(scope)


def iter_source_files(repo_path: Path, include_extensions: set[str]) -> list[Path]:
    """Walk repository files while excluding common non-source directories."""
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules", "dist", "build"}]
        for filename in filenames:
            path = Path(root) / filename
            if path.suffix.lower() in include_extensions:
                files.append(path)
    files.sort()
    return files


def _matches_profile(relative_path: str, include_rules: list[str], exclude_rules: list[str]) -> bool:
    """Apply coarse path-level profile filtering before expensive chunk processing."""
    path_lower = relative_path.lower()
    if include_rules:
        if not any(rule.lower() in path_lower for rule in include_rules):
            return False
    if any(rule.lower() in path_lower for rule in exclude_rules):
        return False
    return True


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split normalized text into overlapping chunks for retrieval indexing."""
    content = " ".join(text.split())
    if not content:
        return []

    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 5)

    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = min(len(content), start + chunk_size)
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(content):
            break
        start = max(0, end - chunk_overlap)
    return chunks


def build_chunk_id(repo_url: str, rel_path: str, index: int, chunk_text: str) -> str:
    raw = f"{repo_url}|{rel_path}|{index}|{chunk_text}".encode("utf-8")
    digest = hashlib.sha1(raw).hexdigest()  # nosec B324 - deterministic non-crypto ID only
    return f"src-{digest[:24]}"


def build_content_hash(content: str) -> str:
    """Content fingerprint used for incremental skip decisions."""
    return hashlib.sha1(content.encode("utf-8")).hexdigest()  # nosec B324 - deterministic non-crypto ID only


def _record_metric(
    *,
    repository_url: str,
    repository_path: Path,
    profile: str,
    incremental: bool,
    status: str,
    duration_ms: int,
    stats: IndexStats,
    error_message: str = "",
) -> None:
    """Persist index run telemetry for operational visibility and audits."""
    IndexRunMetric.objects.create(
        repository_url=repository_url,
        repository_path=str(repository_path),
        profile=profile,
        mode=IndexRunMetric.MODE_INCREMENTAL if incremental else IndexRunMetric.MODE_FULL,
        status=status,
        scanned_files=stats.scanned_files,
        skipped_files=stats.skipped_files,
        created_chunks=stats.created_chunks,
        updated_chunks=stats.updated_chunks,
        deleted_chunks=stats.deleted_chunks,
        duration_ms=duration_ms,
        error_message=error_message,
    )


def index_repository(
    repo_url: str,
    repo_path: Path,
    allowed_repositories: set[str],
    include_extensions: set[str] | None = None,
    profile: str = "default",
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    incremental: bool = False,
    prune: bool = False,
) -> IndexStats:
    """
    Ingest repository files into SourceChunk with optional profile filtering,
    incremental skipping, and prune support.
    """
    start_ts = time.perf_counter()
    include_exts = include_extensions or DEFAULT_EXTENSIONS
    stats = IndexStats()

    try:
        validate_repository_allowed(repo_url, allowed_repositories)

        selected_profile = load_profile_rules(profile)
        include_rules = (include_paths or []) + selected_profile["include"]
        exclude_rules = (exclude_paths or []) + selected_profile["exclude"]

        files = iter_source_files(repo_path, include_exts)
        commit_sha = current_commit_sha(repo_path)
        seen_chunk_ids: set[str] = set()

        for file_path in files:
            stats.scanned_files += 1
            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                stats.skipped_files += 1
                continue

            relative_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
            if not _matches_profile(relative_path, include_rules=include_rules, exclude_rules=exclude_rules):
                stats.skipped_files += 1
                continue

            # Skip unchanged files in incremental mode using (repo, path, commit, hash).
            content_hash = build_content_hash(raw_text)
            if incremental:
                indexed_file = IndexedSourceFile.objects.filter(
                    repository_url=repo_url,
                    source_path=relative_path,
                    commit_sha=commit_sha,
                    content_hash=content_hash,
                ).first()
                if indexed_file:
                    existing_chunk_ids = SourceChunk.objects.filter(
                        repository_url=repo_url,
                        source_path=relative_path,
                    ).values_list("chunk_id", flat=True)
                    seen_chunk_ids.update(existing_chunk_ids)
                    stats.skipped_files += 1
                    continue

            chunks = split_text(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            if not chunks:
                stats.skipped_files += 1
                continue

            # Track per-file chunk IDs so stale chunks for changed files can be removed.
            file_chunk_ids: set[str] = set()
            for index, chunk_text in enumerate(chunks):
                chunk_id = build_chunk_id(repo_url, relative_path, index, chunk_text)
                seen_chunk_ids.add(chunk_id)
                file_chunk_ids.add(chunk_id)

                defaults = {
                    "commit_sha": commit_sha,
                    "source_path": relative_path,
                    "label": relative_path,
                    "text": chunk_text,
                    "standards_scope": infer_scope(relative_path, chunk_text),
                    "quality_score": 0.75,
                }

                _, created = SourceChunk.objects.update_or_create(
                    chunk_id=chunk_id,
                    defaults={"repository_url": repo_url, **defaults},
                )
                if created:
                    stats.created_chunks += 1
                else:
                    stats.updated_chunks += 1

            removed_for_file, _ = (
                SourceChunk.objects.filter(repository_url=repo_url, source_path=relative_path)
                .exclude(chunk_id__in=file_chunk_ids)
                .delete()
            )
            stats.deleted_chunks += removed_for_file

            IndexedSourceFile.objects.update_or_create(
                repository_url=repo_url,
                source_path=relative_path,
                defaults={
                    "commit_sha": commit_sha,
                    "content_hash": content_hash,
                },
            )

        if prune:
            # Full prune removes chunks no longer seen in this run.
            deleted, _ = SourceChunk.objects.filter(repository_url=repo_url).exclude(chunk_id__in=seen_chunk_ids).delete()
            stats.deleted_chunks += deleted

            existing_paths = set(
                SourceChunk.objects.filter(repository_url=repo_url).values_list("source_path", flat=True)
            )
            IndexedSourceFile.objects.filter(repository_url=repo_url).exclude(source_path__in=existing_paths).delete()

        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        _record_metric(
            repository_url=repo_url,
            repository_path=repo_path,
            profile=profile,
            incremental=incremental,
            status=IndexRunMetric.STATUS_SUCCESS,
            duration_ms=duration_ms,
            stats=stats,
        )
        return stats
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_ts) * 1000)
        _record_metric(
            repository_url=repo_url,
            repository_path=repo_path,
            profile=profile,
            incremental=incremental,
            status=IndexRunMetric.STATUS_FAILED,
            duration_ms=duration_ms,
            stats=stats,
            error_message=str(exc),
        )
        raise
