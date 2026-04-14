from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import yaml
import certifi
from helpdesk.models import IndexedSourceFile, IndexRunMetric, SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch


DEFAULT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".xml", ".xsd", ".json"}
DELETE_BATCH_SIZE = 500
XSD_NS = {"xs": "http://www.w3.org/2001/XMLSchema"}
# Profile YAML files define coarse path include/exclude filters by standard/domain.
INDEX_PROFILE_DIR = Path(__file__).resolve().parents[1] / "index_profiles"

# Global path filters applied to every profile, including newly added future repos.
GLOBAL_EXCLUDE_RULES = [
    ".tmp/",
    "/tmp/",
    "all_files_",
    "missing_in_xpr",
    "images",
    "assets",
    "media",
    "tests",
    "test",
    "node_modules",
]


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

    merged_excludes: list[str] = []
    for rule in [*exclude_rules, *GLOBAL_EXCLUDE_RULES]:
        text_rule = str(rule)
        if text_rule not in merged_excludes:
            merged_excludes.append(text_rule)

    return {
        "include": [str(item) for item in include_rules],
        "exclude": merged_excludes,
    }


def validate_repository_allowed(repo_url: str, allowed_repositories: set[str]) -> None:
    """Guardrail: only approved source repositories may enter the retrieval index."""
    if repo_url not in allowed_repositories:
        allowed = ", ".join(sorted(allowed_repositories))
        raise ValueError(f"Repository URL '{repo_url}' is not allow-listed. Allowed: {allowed}")


def current_commit_sha(repo_path: Path) -> str:
    """Resolve full current git commit for traceability; fallback to 'unknown' for non-git dirs."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def infer_scope(source_path: str, chunk_text: str, repo_url: str = "") -> list[str]:
    """Heuristic scope tagging for retrieval filtering and analytics.
    
    Tags chunks based on content keywords and repository source.
    Repositories are auto-tagged regardless of content to ensure consistent retrieval.
    """
    scope = set()
    blob = f"{source_path}\n{chunk_text}".lower()
    repo_lower = repo_url.lower()
    
    # Auto-tag by source repository
    if "netex" in repo_lower:
        scope.add("NeTEx")
    if "siri" in repo_lower:
        scope.add("SIRI")
    if "opra" in repo_lower:
        scope.add("OpRa")
    if "ojp" in repo_lower:
        scope.add("OJP")
    if "datex" in repo_lower:
        scope.add("DATEX II")
    if "profile_documentation" in repo_lower or "hfjelstad" in repo_lower:
        scope.add("Profile Documentation")
    
    # Enhance with content-based detection
    if "netex" in blob and "NeTEx" not in scope:
        scope.add("NeTEx")
    if "siri" in blob and "SIRI" not in scope:
        scope.add("SIRI")
    if "transmodel" in blob and "Transmodel" not in scope:
        scope.add("Transmodel")
    if "opra" in blob and "OpRa" not in scope:
        scope.add("OpRa")
    if "ojp" in blob and "OJP" not in scope:
        scope.add("OJP")
    if "datex" in blob and "DATEX II" not in scope:
        scope.add("DATEX II")
    
    return sorted(scope)


def iter_source_files(repo_path: Path, include_extensions: set[str]) -> list[Path]:
    """Walk repository files while excluding common non-source directories."""
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo_path):
        filtered_dirs: list[str] = []
        for directory in dirs:
            if directory in {".git", ".venv", "node_modules", "dist", "build"}:
                continue

            directory_path = Path(root) / directory
            nested_git_marker = directory_path / ".git"
            # Skip nested git checkouts/submodules so source paths remain addressable
            # under the indexed repository URL on GitHub.
            if nested_git_marker.exists():
                continue

            filtered_dirs.append(directory)

        dirs[:] = filtered_dirs
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


def split_markdown(text: str, max_chars: int = 1200) -> list[tuple[str, str, str]]:
    """Split Markdown by headings. Returns (chunk_text, chunk_type, heading) tuples.

    Sections that exceed max_chars are sub-split as prose using split_text.
    If the document has no headings the whole text is treated as a single prose chunk.
    """
    lines = text.split("\n")
    sections: list[tuple[str, list[str]]] = []
    current_heading = ""
    current_lines: list[str] = []
    has_headings = False

    for line in lines:
        if re.match(r"^#{1,3}\s+\S", line):
            has_headings = True
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    results: list[tuple[str, str, str]] = []
    for heading, section_lines in sections:
        section_text = "\n".join(section_lines).strip()
        if not section_text:
            continue
        top_type = "heading_section" if has_headings and heading else "prose"
        if len(section_text) <= max_chars:
            results.append((section_text, top_type, heading))
        else:
            sub_chunks = split_text(section_text, max_chars, max(0, max_chars // 6))
            for chunk in sub_chunks:
                results.append((chunk, "prose", heading))

    return results


def split_xml(text: str, max_chars: int = 1200) -> list[tuple[str, str, str]]:
    """Split XML/XSD at element boundaries, preserving syntax and whitespace.

    Splits when a line at 2-space indentation starts a new element tag, then
    aggregates segments into max_chars-bounded chunks. Oversized single elements
    are line-split as a fallback.
    Returns (chunk_text, chunk_type, heading) tuples with chunk_type="schema_fragment".
    """
    lines = text.split("\n")
    segments: list[str] = []
    current: list[str] = []

    for line in lines:
        # Lines at the root level of the document body (0 or 2-space indent + tag start)
        # signal a new top-level declaration.
        if re.match(r"^(?:  )?<(?![\?!/])\w", line) and current:
            joined = "\n".join(current)
            if joined.strip():
                segments.append(joined)
            current = [line]
        else:
            current.append(line)

    if current:
        joined = "\n".join(current)
        if joined.strip():
            segments.append(joined)

    # Aggregate segments into max_chars chunks.
    results: list[tuple[str, str, str]] = []
    buffer = ""
    for seg in segments:
        if len(buffer) + len(seg) > max_chars and buffer:
            results.append((buffer.rstrip(), "schema_fragment", ""))
            buffer = seg
        else:
            buffer = (buffer + "\n" + seg).lstrip("\n") if buffer else seg

    if buffer.strip():
        results.append((buffer.rstrip(), "schema_fragment", ""))

    # Sub-split any chunk that is still very large (line-by-line fallback).
    final: list[tuple[str, str, str]] = []
    for chunk_text, chunk_type, heading in results:
        if len(chunk_text) <= max_chars * 3:
            final.append((chunk_text, chunk_type, heading))
        else:
            sub_buf = ""
            for l in chunk_text.split("\n"):
                if len(sub_buf) + len(l) > max_chars and sub_buf:
                    final.append((sub_buf.rstrip(), chunk_type, heading))
                    sub_buf = l
                else:
                    sub_buf = (sub_buf + "\n" + l).lstrip("\n") if sub_buf else l
            if sub_buf.strip():
                final.append((sub_buf.rstrip(), chunk_type, heading))

    return final


def _humanize_identifier(value: str) -> str:
    """Convert XML-ish identifiers to readable phrase tokens."""
    normalized = value.replace(":", " ").replace("_", " ").replace("-", " ")
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def _extract_xml_semantic_signals(chunk_text: str) -> list[str]:
    """Extract high-value XML concepts from element names and comments."""
    signals: list[str] = []

    # Capture tag names for semantic scaffolding.
    for tag in re.findall(r"</?([A-Za-z_][\w:.-]*)", chunk_text):
        phrase = _humanize_identifier(tag)
        if phrase and phrase not in signals:
            signals.append(phrase)

    # Capture human comments, often carrying scenario meaning in example XML files.
    for comment in re.findall(r"<!--\s*(.*?)\s*-->", chunk_text, flags=re.DOTALL):
        cleaned = " ".join(comment.split()).strip().lower()
        if cleaned and cleaned not in signals:
            signals.append(cleaned)

    return signals[:18]


def enrich_xml_example_text(*, chunk_text: str, source_path: str) -> str:
    """Append concise semantic summary for XML examples to improve content-based retrieval."""
    signals = _extract_xml_semantic_signals(chunk_text)
    if not signals:
        return chunk_text

    summary = (
        "XML semantic summary:\n"
        f"- source: {source_path}\n"
        f"- concepts: {', '.join(signals)}"
    )
    return f"{chunk_text}\n\n{summary}"


def _first_nonempty_text(values: list[str]) -> str:
    for value in values:
        cleaned = " ".join(value.split())
        if cleaned:
            return cleaned
    return ""


def _extract_xsd_documentation(node: ET.Element) -> str:
    texts = [
        doc.text or ""
        for doc in node.findall(".//xs:annotation/xs:documentation", XSD_NS)
        if (doc.text or "").strip()
    ]
    return _first_nonempty_text(texts)


def _extract_xsd_child_elements(node: ET.Element, limit: int = 12) -> list[str]:
    child_names: list[str] = []
    for child in node.findall("./xs:complexType/xs:sequence/xs:element", XSD_NS):
        name = child.get("ref") or child.get("name") or child.get("type") or ""
        name = name.strip()
        if name and name not in child_names:
            child_names.append(name)
        if len(child_names) >= limit:
            break

    if len(child_names) < limit:
        for child in node.findall("./xs:complexType/xs:choice/xs:element", XSD_NS):
            name = child.get("ref") or child.get("name") or child.get("type") or ""
            name = name.strip()
            if name and name not in child_names:
                child_names.append(name)
            if len(child_names) >= limit:
                break

    return child_names


def _extract_xsd_attributes(node: ET.Element, limit: int = 12) -> list[str]:
    attributes: list[str] = []
    for attr in node.findall("./xs:complexType/xs:attribute", XSD_NS):
        name = attr.get("ref") or attr.get("name") or attr.get("type") or ""
        name = name.strip()
        if not name:
            continue
        if attr.get("use"):
            name = f"{name} ({attr.get('use')})"
        if name not in attributes:
            attributes.append(name)
        if len(attributes) >= limit:
            break
    return attributes


def _build_xsd_summary_text(node: ET.Element, source_name: str) -> tuple[str, str] | None:
    declaration_type = node.tag.rsplit("}", 1)[-1]
    if declaration_type not in {"element", "complexType", "simpleType"}:
        return None

    declaration_name = (node.get("name") or node.get("ref") or "").strip()
    if not declaration_name:
        return None

    base_type = node.get("type") or ""
    if not base_type:
        restriction = node.find("./xs:simpleType/xs:restriction", XSD_NS)
        if restriction is not None:
            base_type = restriction.get("base", "")
    if not base_type:
        extension = node.find("./xs:complexContent/xs:extension", XSD_NS)
        if extension is not None:
            base_type = extension.get("base", "")

    documentation = _extract_xsd_documentation(node)
    children = _extract_xsd_child_elements(node)
    attributes = _extract_xsd_attributes(node)

    parts = [
        f"Schema declaration: {declaration_type} {declaration_name}",
        f"Defined in: {source_name}",
    ]
    if base_type:
        parts.append(f"Base or referenced type: {base_type}")
    if children:
        parts.append(f"Direct child elements: {', '.join(children)}")
    if attributes:
        parts.append(f"Attributes: {', '.join(attributes)}")
    if documentation:
        parts.append(f"Documentation: {documentation}")

    return "\n".join(parts), declaration_name


def split_xsd_summary(text: str, source_name: str, max_declarations: int = 250) -> list[tuple[str, str, str]]:
    """Parse XSD and emit compact schema summaries instead of raw schema text."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        fallback = split_text(text, chunk_size=800, chunk_overlap=120)
        return [(chunk, "schema_fragment", source_name) for chunk in fallback[:3]]

    chunks: list[tuple[str, str, str]] = []
    top_level_declarations = list(root.findall("./xs:element", XSD_NS))
    top_level_declarations.extend(root.findall("./xs:complexType", XSD_NS))
    top_level_declarations.extend(root.findall("./xs:simpleType", XSD_NS))

    for node in top_level_declarations[:max_declarations]:
        summary = _build_xsd_summary_text(node, source_name)
        if summary is None:
            continue
        summary_text, heading = summary
        chunks.append((summary_text, "schema_fragment", heading))

    if chunks:
        return chunks

    fallback = split_text(text, chunk_size=800, chunk_overlap=120)
    return [(chunk, "schema_fragment", source_name) for chunk in fallback[:3]]


def split_structured(
    text: str,
    extension: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    source_name: str = "",
) -> list[tuple[str, str, str]]:
    """Route to the appropriate structure-aware splitter.

    Returns a list of (chunk_text, chunk_type, heading) tuples.
    chunk_type is one of: "prose", "heading_section", "schema_fragment".
    """
    ext = extension.lower()
    if ext == ".md":
        return split_markdown(text, max_chars=chunk_size)
    if ext == ".xml":
        return split_xml(text, max_chars=chunk_size)
    if ext == ".xsd":
        return split_xsd_summary(text, source_name=source_name or "schema")
    # Fallback: flat overlapping window, no structural metadata.
    chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return [(c, "prose", "") for c in chunks]


def infer_doc_type(source_path: str, chunk_type: str, heading: str, chunk_text: str) -> str:
    """Classify chunk intent to support retrieval ranking and diagnostics."""
    path_lower = source_path.lower()
    basename = Path(path_lower).name
    blob = f"{path_lower}\n{heading}\n{chunk_text[:500]}".lower()

    if basename.startswith("readme"):
        return "readme"
    if "/examples/" in path_lower or path_lower.startswith("examples/"):
        return "example"
    if chunk_type == "schema_fragment" or path_lower.endswith(".xsd"):
        return "schema"
    if any(marker in blob for marker in [" frame", "frame ", "frame:", "frame-"]):
        return "frame"
    if any(marker in blob for marker in [" object", "object ", "object:", "object-"]):
        return "object"
    return "guide"


def compute_chunk_quality(
    *,
    source_path: str,
    chunk_text: str,
    chunk_type: str,
    heading: str,
    doc_type: str,
    standards_scope: list[str],
) -> float:
    """Compute quality score from document intent and chunk-level evidence density."""
    base_scores = {
        "frame": 0.88,
        "object": 0.86,
        "schema": 0.84,
        "guide": 0.76,
        "example": 0.74,
        "readme": 0.62,
    }
    score = base_scores.get(doc_type, 0.72)

    word_count = len(chunk_text.split())
    if word_count < 20:
        score -= 0.12
    elif word_count < 60:
        score += 0.01
    elif word_count <= 280:
        score += 0.06
    elif word_count > 500:
        score -= 0.04

    if heading:
        score += 0.03
    if chunk_type == "heading_section":
        score += 0.03
    if standards_scope:
        score += 0.04
    if source_path.lower().startswith("issues/"):
        score -= 0.04

    return max(0.0, min(1.0, score))


def build_chunk_embedding_text(
    *,
    chunk_text: str,
    doc_type: str,
    chunk_type: str,
    heading: str,
    standards_scope: list[str],
    repository_url: str,
    source_path: str,
) -> str:
    """Build contextual embedding input so vectors encode document role and provenance."""
    scope = ", ".join(standards_scope) if standards_scope else "unspecified"
    return (
        f"doc_type: {doc_type}\n"
        f"chunk_type: {chunk_type}\n"
        f"scope: {scope}\n"
        f"repository: {repository_url}\n"
        f"source_path: {source_path}\n"
        f"heading: {heading or 'none'}\n\n"
        f"content:\n{chunk_text}"
    )


def build_chunk_id(repo_url: str, rel_path: str, index: int, chunk_text: str) -> str:
    raw = f"{repo_url}|{rel_path}|{index}|{chunk_text}".encode("utf-8")
    digest = hashlib.sha1(raw).hexdigest()  # nosec B324 - deterministic non-crypto ID only
    return f"src-{digest[:24]}"


def _delete_chunks_by_ids(repository_url: str, chunk_ids: list[str], batch_size: int = DELETE_BATCH_SIZE) -> int:
    """Delete chunks in bounded batches to avoid SQLite variable limits."""
    if not chunk_ids:
        return 0

    deleted_total = 0
    for index in range(0, len(chunk_ids), batch_size):
        batch = chunk_ids[index : index + batch_size]
        deleted, _ = SourceChunk.objects.filter(
            repository_url=repository_url,
            chunk_id__in=batch,
        ).delete()
        deleted_total += deleted
    return deleted_total


def _delete_stale_source_chunks(
    repository_url: str,
    source_path: str,
    keep_chunk_ids: set[str],
) -> int:
    """Delete stale chunks for a single source file without large NOT IN SQL clauses."""
    existing_chunk_ids = list(
        SourceChunk.objects.filter(repository_url=repository_url, source_path=source_path).values_list("chunk_id", flat=True)
    )
    stale_chunk_ids = [chunk_id for chunk_id in existing_chunk_ids if chunk_id not in keep_chunk_ids]
    return _delete_chunks_by_ids(repository_url, stale_chunk_ids)


def _prune_repository_chunks(repository_url: str, seen_chunk_ids: set[str]) -> int:
    """Prune repository chunks using batched deletes to stay SQLite-compatible."""
    existing_chunk_ids = list(SourceChunk.objects.filter(repository_url=repository_url).values_list("chunk_id", flat=True))
    stale_chunk_ids = [chunk_id for chunk_id in existing_chunk_ids if chunk_id not in seen_chunk_ids]
    return _delete_chunks_by_ids(repository_url, stale_chunk_ids)


def _prune_indexed_source_files(repository_url: str) -> None:
    """Remove IndexedSourceFile rows with no remaining chunks, avoiding large SQL IN lists."""
    existing_paths = set(SourceChunk.objects.filter(repository_url=repository_url).values_list("source_path", flat=True))

    stale_ids: list[int] = []
    for indexed_file in IndexedSourceFile.objects.filter(repository_url=repository_url).only("id", "source_path").iterator():
        if indexed_file.source_path not in existing_paths:
            stale_ids.append(indexed_file.id)

    for index in range(0, len(stale_ids), DELETE_BATCH_SIZE):
        batch = stale_ids[index : index + DELETE_BATCH_SIZE]
        IndexedSourceFile.objects.filter(id__in=batch).delete()


def build_content_hash(content: str) -> str:
    """Content fingerprint used for incremental skip decisions."""
    return hashlib.sha1(content.encode("utf-8")).hexdigest()  # nosec B324 - deterministic non-crypto ID only


def _parse_github_owner_repo(repo_url: str) -> tuple[str, str]:
    """Extract owner/repo from a GitHub HTTPS URL."""
    parsed = urlparse(repo_url)
    if parsed.netloc.lower() != "github.com":
        raise ValueError(f"GitHub issues ingestion only supports github.com URLs: {repo_url}")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"Unable to parse GitHub owner/repo from URL: {repo_url}")

    owner, repo = parts[0], parts[1]
    repo = repo[:-4] if repo.endswith(".git") else repo
    if not owner or not repo:
        raise ValueError(f"Unable to parse GitHub owner/repo from URL: {repo_url}")

    return owner, repo


def _build_ssl_context(*, verify_ssl: bool, ca_bundle: str | None = None):
    """Build SSL context for GitHub API calls (certifi by default)."""
    if not verify_ssl:
        return ssl._create_unverified_context()  # nosec B323 - explicit dev override only

    cafile = ca_bundle or certifi.where()
    return ssl.create_default_context(cafile=cafile)


def _github_api_get_json(
    url: str,
    github_token: str | None = None,
    *,
    verify_ssl: bool = True,
    ca_bundle: str | None = None,
) -> tuple[object, str]:
    """Perform a GitHub API GET and return parsed JSON body + Link header."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "napcore-helpdesk-indexer",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    request = Request(url=url, headers=headers, method="GET")
    ssl_context = _build_ssl_context(verify_ssl=verify_ssl, ca_bundle=ca_bundle)
    try:
        with urlopen(request, timeout=30, context=ssl_context) as response:
            payload = response.read().decode("utf-8")
            link_header = response.headers.get("Link", "")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"GitHub API request failed ({exc.code}) for {url}: {details[:300]}") from exc
    except URLError as exc:
        raise ValueError(f"GitHub API request failed for {url}: {exc.reason}") from exc

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"GitHub API returned invalid JSON for {url}") from exc

    return parsed, link_header


def _extract_next_link(link_header: str) -> str | None:
    """Parse RFC5988 Link header and return rel=next URL if present."""
    if not link_header:
        return None

    for segment in link_header.split(","):
        if 'rel="next"' not in segment:
            continue
        match = re.search(r"<([^>]+)>", segment)
        if match:
            return match.group(1)
    return None


def fetch_github_issue_documents(
    repo_url: str,
    github_token: str | None = None,
    *,
    verify_ssl: bool = True,
    ca_bundle: str | None = None,
) -> list[dict[str, str]]:
    """Fetch GitHub issues and comments as indexable document blobs."""
    owner, repo = _parse_github_owner_repo(repo_url)

    documents: list[dict[str, str]] = []
    issue_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues?"
        + urlencode({"state": "all", "per_page": 100, "page": 1})
    )

    next_url: str | None = issue_url
    while next_url:
        payload, link_header = _github_api_get_json(
            next_url,
            github_token=github_token,
            verify_ssl=verify_ssl,
            ca_bundle=ca_bundle,
        )
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected GitHub issues API response for {repo_url}")

        for issue in payload:
            if not isinstance(issue, dict):
                continue
            if "pull_request" in issue:
                # Pull requests are tracked in issues API but are not issue discussion content.
                continue

            number = issue.get("number")
            if not number:
                continue

            title = str(issue.get("title") or "").strip()
            body = str(issue.get("body") or "").strip()
            labels = issue.get("labels") or []
            label_names = []
            if isinstance(labels, list):
                for label in labels:
                    if isinstance(label, dict):
                        name = str(label.get("name") or "").strip()
                        if name:
                            label_names.append(name)

            comments_text = ""
            comments_count = int(issue.get("comments") or 0)
            comments_url = str(issue.get("comments_url") or "").strip()
            if comments_count > 0 and comments_url:
                comments_payload, _ = _github_api_get_json(
                    comments_url,
                    github_token=github_token,
                    verify_ssl=verify_ssl,
                    ca_bundle=ca_bundle,
                )
                if isinstance(comments_payload, list):
                    comment_blocks = []
                    for comment in comments_payload:
                        if not isinstance(comment, dict):
                            continue
                        comment_body = str(comment.get("body") or "").strip()
                        if comment_body:
                            comment_blocks.append(comment_body)
                    comments_text = "\n\n".join(comment_blocks)

            combined_text = (
                f"Issue #{number}\n"
                f"Title: {title}\n"
                f"Labels: {', '.join(label_names)}\n\n"
                f"Body:\n{body}\n\n"
                f"Comments:\n{comments_text}"
            ).strip()

            documents.append(
                {
                    "source_path": f"issues/{number}.md",
                    "text": combined_text,
                    "commit_sha": str(issue.get("updated_at") or issue.get("created_at") or "issues"),
                }
            )

        next_url = _extract_next_link(link_header)

    return documents


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
    include_issues: bool = False,
    github_token: str | None = None,
    github_verify_ssl: bool = True,
    github_ca_bundle: str | None = None,
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

            # Skip unchanged files in incremental mode using per-file content fingerprint.
            # This avoids full re-upserts when repository HEAD changes but file content does not.
            content_hash = build_content_hash(raw_text)
            if incremental:
                indexed_file = IndexedSourceFile.objects.filter(
                    repository_url=repo_url,
                    source_path=relative_path,
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

            structured = split_structured(
                raw_text,
                file_path.suffix,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                source_name=relative_path,
            )
            if not structured:
                stats.skipped_files += 1
                continue

            # Track per-file chunk IDs so stale chunks for changed files can be removed.
            chunk_records: list[dict] = []
            embedding_inputs: list[str] = []
            for index, (chunk_text, chunk_type, heading) in enumerate(structured):
                chunk_id = build_chunk_id(repo_url, relative_path, index, chunk_text)
                standards_scope = infer_scope(relative_path, chunk_text, repo_url)
                doc_type = infer_doc_type(
                    source_path=relative_path,
                    chunk_type=chunk_type,
                    heading=heading,
                    chunk_text=chunk_text,
                )
                enriched_chunk_text = chunk_text
                if relative_path.lower().endswith(".xml") and doc_type == "example":
                    enriched_chunk_text = enrich_xml_example_text(
                        chunk_text=chunk_text,
                        source_path=relative_path,
                    )
                chunk_records.append(
                    {
                        "chunk_id": chunk_id,
                        "chunk_text": enriched_chunk_text,
                        "chunk_type": chunk_type,
                        "heading": heading,
                        "standards_scope": standards_scope,
                        "doc_type": doc_type,
                        "quality_score": compute_chunk_quality(
                            source_path=relative_path,
                            chunk_text=enriched_chunk_text,
                            chunk_type=chunk_type,
                            heading=heading,
                            doc_type=doc_type,
                            standards_scope=standards_scope,
                        ),
                    }
                )
                embedding_inputs.append(
                    build_chunk_embedding_text(
                        chunk_text=enriched_chunk_text,
                        doc_type=doc_type,
                        chunk_type=chunk_type,
                        heading=heading,
                        standards_scope=standards_scope,
                        repository_url=repo_url,
                        source_path=relative_path,
                    )
                )

            chunk_embeddings = build_text_embeddings_batch(embedding_inputs)
            file_chunk_ids: set[str] = set()
            for chunk_record, chunk_embedding in zip(chunk_records, chunk_embeddings):
                chunk_id = chunk_record["chunk_id"]
                seen_chunk_ids.add(chunk_id)
                file_chunk_ids.add(chunk_id)

                defaults = {
                    "commit_sha": commit_sha,
                    "source_path": relative_path,
                    "label": relative_path,
                    "text": chunk_record["chunk_text"],
                    "standards_scope": chunk_record["standards_scope"],
                    "quality_score": chunk_record["quality_score"],
                    "chunk_type": chunk_record["chunk_type"],
                    "doc_type": chunk_record["doc_type"],
                    "heading": chunk_record["heading"],
                    "embedding_vector": chunk_embedding,
                }

                _, created = SourceChunk.objects.update_or_create(
                    chunk_id=chunk_id,
                    defaults={"repository_url": repo_url, **defaults},
                )
                if created:
                    stats.created_chunks += 1
                else:
                    stats.updated_chunks += 1

            removed_for_file = _delete_stale_source_chunks(
                repository_url=repo_url,
                source_path=relative_path,
                keep_chunk_ids=file_chunk_ids,
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

        if include_issues:
            issue_documents = fetch_github_issue_documents(
                repo_url=repo_url,
                github_token=github_token,
                verify_ssl=github_verify_ssl,
                ca_bundle=github_ca_bundle,
            )
            for issue_doc in issue_documents:
                stats.scanned_files += 1

                source_path = issue_doc["source_path"]
                raw_text = issue_doc["text"]
                issue_commit_sha = issue_doc["commit_sha"]

                content_hash = build_content_hash(raw_text)
                if incremental:
                    indexed_issue = IndexedSourceFile.objects.filter(
                        repository_url=repo_url,
                        source_path=source_path,
                        content_hash=content_hash,
                    ).first()
                    if indexed_issue:
                        existing_chunk_ids = SourceChunk.objects.filter(
                            repository_url=repo_url,
                            source_path=source_path,
                        ).values_list("chunk_id", flat=True)
                        seen_chunk_ids.update(existing_chunk_ids)
                        stats.skipped_files += 1
                        continue

                # Issues are plain-text/markdown; use split_structured with .md routing.
                structured_issue = split_structured(
                    raw_text,
                    ".md",
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    source_name=source_path,
                )
                if not structured_issue:
                    stats.skipped_files += 1
                    continue

                file_chunk_ids: set[str] = set()
                issue_chunk_records: list[dict] = []
                issue_embedding_inputs: list[str] = []
                for index, (chunk_text, chunk_type, heading) in enumerate(structured_issue):
                    chunk_id = build_chunk_id(repo_url, source_path, index, chunk_text)
                    standards_scope = infer_scope(source_path, chunk_text, repo_url)
                    doc_type = infer_doc_type(
                        source_path=source_path,
                        chunk_type=chunk_type,
                        heading=heading,
                        chunk_text=chunk_text,
                    )
                    issue_chunk_records.append(
                        {
                            "chunk_id": chunk_id,
                            "chunk_text": chunk_text,
                            "chunk_type": chunk_type,
                            "heading": heading,
                            "standards_scope": standards_scope,
                            "doc_type": doc_type,
                            "quality_score": compute_chunk_quality(
                                source_path=source_path,
                                chunk_text=chunk_text,
                                chunk_type=chunk_type,
                                heading=heading,
                                doc_type=doc_type,
                                standards_scope=standards_scope,
                            ),
                        }
                    )
                    issue_embedding_inputs.append(
                        build_chunk_embedding_text(
                            chunk_text=chunk_text,
                            doc_type=doc_type,
                            chunk_type=chunk_type,
                            heading=heading,
                            standards_scope=standards_scope,
                            repository_url=repo_url,
                            source_path=source_path,
                        )
                    )

                issue_embeddings = build_text_embeddings_batch(issue_embedding_inputs)
                for issue_chunk_record, chunk_embedding in zip(issue_chunk_records, issue_embeddings):
                    chunk_id = issue_chunk_record["chunk_id"]
                    seen_chunk_ids.add(chunk_id)
                    file_chunk_ids.add(chunk_id)

                    defaults = {
                        "commit_sha": issue_commit_sha,
                        "source_path": source_path,
                        "label": source_path,
                        "text": issue_chunk_record["chunk_text"],
                        "standards_scope": issue_chunk_record["standards_scope"],
                        "quality_score": issue_chunk_record["quality_score"],
                        "chunk_type": issue_chunk_record["chunk_type"],
                        "doc_type": issue_chunk_record["doc_type"],
                        "heading": issue_chunk_record["heading"],
                        "embedding_vector": chunk_embedding,
                    }

                    _, created = SourceChunk.objects.update_or_create(
                        chunk_id=chunk_id,
                        defaults={"repository_url": repo_url, **defaults},
                    )
                    if created:
                        stats.created_chunks += 1
                    else:
                        stats.updated_chunks += 1

                removed_for_issue = _delete_stale_source_chunks(
                    repository_url=repo_url,
                    source_path=source_path,
                    keep_chunk_ids=file_chunk_ids,
                )
                stats.deleted_chunks += removed_for_issue

                IndexedSourceFile.objects.update_or_create(
                    repository_url=repo_url,
                    source_path=source_path,
                    defaults={
                        "commit_sha": issue_commit_sha,
                        "content_hash": content_hash,
                    },
                )

        if prune:
            # Full prune removes chunks no longer seen in this run.
            deleted = _prune_repository_chunks(repository_url=repo_url, seen_chunk_ids=seen_chunk_ids)
            stats.deleted_chunks += deleted
            _prune_indexed_source_files(repository_url=repo_url)

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
