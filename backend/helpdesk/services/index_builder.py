"""
Orchestrates source repository ingestion and semantic chunk indexing.

Clones or updates a repository, splits content into overlapping chunks,
generates embeddings, and upserts SourceChunk records. Supports incremental
runs (skips unchanged files by content hash) and pruning of removed files.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-11-03
"""

from __future__ import annotations

import hashlib
import json
import logging
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
from html import unescape as html_unescape
from html.parser import HTMLParser

import yaml
import certifi
from helpdesk.models import IndexedSourceFile, IndexRunMetric, SourceChunk
from helpdesk.services.schema_overlap import extract_schema_references
from helpdesk.services.embeddings import build_text_embeddings_batch, passage_text, uses_semantic
from helpdesk.services.repository_urls import canonical_repository_url


MOBILITYDCAT_AP_SCOPE = "mobilityDCAT-AP"
TNITS_SCOPE = "TN-ITS"
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

logger = logging.getLogger(__name__)


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
    # File types the profile adds to DEFAULT_EXTENSIONS (mobilityDCAT-AP publishes HTML and Turtle).
    extensions = data.get("extensions") or []
    if not isinstance(include_rules, list) or not isinstance(exclude_rules, list) or not isinstance(extensions, list):
        raise ValueError(f"Invalid profile format in {profile_file}: include/exclude/extensions must be lists")

    merged_excludes: list[str] = []
    for rule in [*exclude_rules, *GLOBAL_EXCLUDE_RULES]:
        text_rule = str(rule)
        if text_rule not in merged_excludes:
            merged_excludes.append(text_rule)

    return {
        "include": [str(item) for item in include_rules],
        "exclude": merged_excludes,
        "extensions": {f".{str(item).lower().lstrip('.')}" for item in extensions},
    }


def validate_repository_allowed(repo_url: str, allowed_repositories: set[str]) -> None:
    """Guardrail: only approved source repositories may enter the retrieval index.

    Both sides are compared by canonical URL, so a known alias of an approved
    repository (for example SIRI-CEN/SIRI for TransmodelEcosystem/SIRI) is accepted.
    """
    approved = {canonical_repository_url(url) for url in allowed_repositories}
    if canonical_repository_url(repo_url) not in approved:
        allowed = ", ".join(sorted(allowed_repositories))
        raise ValueError(f"Repository URL '{repo_url}' is not allow-listed. Allowed: {allowed}")


def _git(repo_path: Path, *args: str) -> subprocess.CompletedProcess:
    """Run git in a checkout. The checkout may belong to another user (a host directory
    mounted into a container), so this path alone is trusted; otherwise git refuses it
    as "dubious ownership"."""
    return subprocess.run(
        ["git", "-c", f"safe.directory={repo_path}", "-C", str(repo_path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def current_commit_sha(repo_path: Path) -> str:
    """Resolve full current git commit for traceability; fallback to 'unknown' for non-git dirs."""
    try:
        return _git(repo_path, "rev-parse", "HEAD").stdout.strip() or "unknown"
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
    # Repository only: NeTEx and SIRI documents that mention DCAT are not about this profile.
    if "mobilitydcat-ap" in repo_lower:
        scope.add(MOBILITYDCAT_AP_SCOPE)
    # TN-ITS's own repository only; it is DATEX II Part 14, so a DATEX II question finds it too.
    if "tn-its" in repo_lower:
        scope.update({TNITS_SCOPE, "DATEX II"})
        return sorted(scope)
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
    return sorted(scope)


# .mylocal holds a contributor's local-only material: never published upstream or to production,
# so never indexed, even when the git listing below fails and the directory is walked instead.
_EXCLUDED_DIRECTORIES = {".git", ".venv", "node_modules", "dist", "build", ".mylocal"}


def _tracked_files(repo_path: Path) -> list[Path] | None:
    """Files the repository tracks, or None when the directory is not a usable git checkout.

    Untracked and gitignored files (a contributor's local notes, build output) are not
    part of the standard and are never published upstream, so they are not indexed.
    """
    if not (repo_path / ".git").exists():
        return None
    try:
        output = _git(repo_path, "ls-files", "-z").stdout
    except Exception:
        logger.warning("git ls-files failed for %s; indexing every file instead", repo_path, exc_info=True)
        return None
    return [repo_path / relative for relative in output.split("\0") if relative]


def iter_source_files(repo_path: Path, include_extensions: set[str]) -> list[Path]:
    """List the repository's source files, excluding common non-source directories.

    In a git checkout only tracked files are listed; nested checkouts and submodules are
    single gitlink entries there, not files, so they are skipped as in the walk below.
    """
    tracked = _tracked_files(repo_path)
    if tracked is not None:
        return sorted(
            path
            for path in tracked
            if path.suffix.lower() in include_extensions
            and not _EXCLUDED_DIRECTORIES.intersection(path.relative_to(repo_path).parts)
            and path.is_file()
        )

    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo_path):
        filtered_dirs: list[str] = []
        for directory in dirs:
            if directory in _EXCLUDED_DIRECTORIES:
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


_HTML_SKIPPED_TAGS = {"script", "style", "head", "nav", "svg"}
_HTML_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_HTML_BLOCK_TAGS = {"p", "div", "section", "li", "dt", "dd", "pre", "br", "blockquote", "figcaption", "caption"}


class _HtmlBlocks(HTMLParser):
    """Collect (heading, block) pairs from HTML: one block per paragraph and one per table row.

    A table row becomes "header: value" lines, so a property table row (name and URI, range,
    cardinality, definition, usage note) reads as one self-contained block. A row that starts with
    its own header cell (<th>Definition</th><td>...</td>, as in a class table) becomes "Definition: ...".
    Only a row of header cells alone is a column header row.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self.heading = ""
        self._skip = 0
        self._text: list[str] = []
        self._in_heading = False
        self._headers: list[str] = []
        self._row: list[tuple[bool, str]] | None = None  # (is header cell, text)
        self._cell: list[str] | None = None
        self._cell_is_header = False

    def _flush_text(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self._text)).strip()
        self._text = []
        if text:
            self.blocks.append((self.heading, text))

    def handle_starttag(self, tag, attrs):
        if tag in _HTML_SKIPPED_TAGS:
            self._skip += 1
        elif self._skip:
            return
        elif tag in _HTML_HEADING_TAGS:
            self._flush_text()
            self._in_heading = True
        elif tag == "tr":
            self._flush_text()
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell, self._cell_is_header = [], tag == "th"
        elif tag == "table":
            self._flush_text()
            self._headers = []
        elif tag in _HTML_BLOCK_TAGS:
            if self._cell is not None:
                self._cell.append(" ")
            else:
                self._flush_text()

    def handle_endtag(self, tag):
        if tag in _HTML_SKIPPED_TAGS:
            self._skip = max(0, self._skip - 1)
        elif self._skip:
            return
        elif tag in _HTML_HEADING_TAGS and self._in_heading:
            self.heading = re.sub(r"\s+", " ", "".join(self._text)).strip()
            self._text, self._in_heading = [], False
        elif tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append((self._cell_is_header, re.sub(r"\s+", " ", "".join(self._cell)).strip()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            row, self._row = self._row, None
            block = self._row_block(row)
            if block:
                self.blocks.append((self.heading, block))
        elif tag in _HTML_BLOCK_TAGS and self._cell is None:
            self._flush_text()

    def _row_block(self, row: list[tuple[bool, str]]) -> str:
        if row and all(is_header for is_header, _ in row):
            self._headers = [text for _, text in row]
            return ""
        if row and row[0][0]:  # a row header: <th>label</th><td>value</td>...
            values = " ".join(text for _, text in row[1:] if text)
            return f"{row[0][1]}: {values}" if values else ""
        return "\n".join(
            f"{self._headers[i]}: {text}" if i < len(self._headers) and self._headers[i] else text
            for i, (_, text) in enumerate(row)
            if text
        )

    def handle_data(self, data):
        if self._skip:
            return
        if self._cell is not None:
            self._cell.append(data)
        else:
            self._text.append(data)

    def close(self) -> None:
        super().close()
        self._flush_text()


def split_html(text: str, max_chars: int = 1200, source_name: str = "") -> list[tuple[str, str, str]]:
    """Split HTML into heading sections of readable text, with table rows kept whole.

    Blocks under the same heading are packed up to max_chars; a block longer than that is split as prose.
    A fragment without headings (an included table file) takes its heading from the file name. Each
    chunk starts with its heading, as a Markdown section does: a property table row names its class
    only there ("Properties for distribution").
    """
    parser = _HtmlBlocks()
    try:
        parser.feed(text)
        parser.close()
    except Exception:  # malformed markup: fall back to the tag-stripped text
        plain = re.sub(r"\s+", " ", html_unescape(re.sub(r"<[^>]+>", " ", text))).strip()
        return [(chunk, "prose", "") for chunk in split_text(plain, max_chars, max(0, max_chars // 6))]

    fallback_heading = Path(source_name).stem.replace("-", " ").replace("_", " ").strip().capitalize()
    results: list[tuple[str, str, str]] = []
    current_heading: str | None = None
    current: list[str] = []

    def titled(heading: str, text: str) -> str:
        return f"{heading}\n\n{text}" if heading else text

    def flush() -> None:
        if current:
            heading = current_heading or fallback_heading
            results.append((titled(heading, "\n\n".join(current)), "heading_section" if heading else "prose", heading))
            current.clear()

    for heading, block in parser.blocks:
        title = heading or fallback_heading
        budget = max_chars - len(title) - 2
        if heading != current_heading or (current and sum(len(b) + 2 for b in current) + len(block) > budget):
            flush()
            current_heading = heading
        if len(block) > budget:
            for piece in split_text(block, max(200, budget), max(0, budget // 6)):
                results.append((titled(title, piece), "prose", title))
            continue
        current.append(block)
    flush()
    return results


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


# Child elements and attributes live directly under xs:sequence/xs:choice for an
# xs:group declaration, but one level deeper (under xs:complexType) for a named
# complexType. Search both so group declarations aren't left empty.
_CHILD_ELEMENT_PATHS = (
    "./xs:complexType/xs:sequence/xs:element",
    "./xs:complexType/xs:choice/xs:element",
    "./xs:sequence/xs:element",
    "./xs:choice/xs:element",
    "./xs:sequence/xs:choice/xs:element",
)
_ATTRIBUTE_PATHS = (
    "./xs:complexType/xs:attribute",
    "./xs:attribute",
)


def _extract_xsd_child_elements(node: ET.Element, limit: int = 12) -> list[str]:
    child_names: list[str] = []
    for path in _CHILD_ELEMENT_PATHS:
        for child in node.findall(path, XSD_NS):
            name = child.get("ref") or child.get("name") or child.get("type") or ""
            name = name.strip()
            if name and name not in child_names:
                child_names.append(name)
            if len(child_names) >= limit:
                return child_names
    return child_names


_ENUMERATION_PATHS = (
    "./xs:restriction/xs:enumeration",
    "./xs:simpleType/xs:restriction/xs:enumeration",
)
_ENUMERATION_LIMIT = 60
_CHILD_DOCUMENTATION_CHARS = 200


def _own_documentation(node: ET.Element) -> str:
    """The node's own annotation, not one of a nested declaration."""
    return _first_nonempty_text(
        [doc.text or "" for doc in node.findall("./xs:annotation/xs:documentation", XSD_NS)]
    )


def _extract_xsd_enumerations(node: ET.Element, limit: int = _ENUMERATION_LIMIT) -> tuple[list[str], int]:
    """The allowed values of a simple type, each with its documentation, and how many were left out.

    The summary kept only the type's own documentation ("Allowed values for Seat Allocation Method."), so an
    answer could not name the values (prod question 653, 2026-11-07)."""
    values: list[str] = []
    total = 0
    for path in _ENUMERATION_PATHS:
        for enumeration in node.findall(path, XSD_NS):
            value = (enumeration.get("value") or "").strip()
            if not value:
                continue
            total += 1
            if len(values) >= limit:
                continue
            documentation = _own_documentation(enumeration)
            values.append(f"{value} ({documentation})" if documentation else value)
    return values, total - len(values)


def _extract_xsd_child_documentation(node: ET.Element, limit: int = 12) -> list[str]:
    """Documentation of the child elements declared in place; a referenced child has a chunk of its own.

    SeatingCapacity and StandingCapacity are declared inside CapacityGroup, so their meaning was in no chunk."""
    lines: list[str] = []
    for path in _CHILD_ELEMENT_PATHS:
        for child in node.findall(path, XSD_NS):
            name = (child.get("name") or "").strip()
            documentation = _own_documentation(child)
            if not name or not documentation:
                continue
            if len(documentation) > _CHILD_DOCUMENTATION_CHARS:
                documentation = documentation[: _CHILD_DOCUMENTATION_CHARS - 1].rstrip() + "…"
            lines.append(f"{name}: {documentation}")
            if len(lines) >= limit:
                return lines
    return lines


def _extract_xsd_attributes(node: ET.Element, limit: int = 12) -> list[str]:
    attributes: list[str] = []
    for path in _ATTRIBUTE_PATHS:
        for attr in node.findall(path, XSD_NS):
            name = attr.get("ref") or attr.get("name") or attr.get("type") or ""
            name = name.strip()
            if not name:
                continue
            if attr.get("use"):
                name = f"{name} ({attr.get('use')})"
            if name not in attributes:
                attributes.append(name)
            if len(attributes) >= limit:
                return attributes
    return attributes


def _extract_xsd_required_child_elements(node: ET.Element, limit: int = 12) -> list[str]:
    required_children: list[str] = []
    for path in _CHILD_ELEMENT_PATHS:
        for child in node.findall(path, XSD_NS):
            min_occurs = (child.get("minOccurs") or "1").strip()
            if min_occurs == "0":
                continue
            name = child.get("ref") or child.get("name") or child.get("type") or ""
            name = name.strip()
            if name and name not in required_children:
                required_children.append(name)
            if len(required_children) >= limit:
                return required_children
    return required_children


def _extract_xsd_required_attributes(node: ET.Element, limit: int = 12) -> list[str]:
    required_attributes: list[str] = []
    for path in _ATTRIBUTE_PATHS:
        for attr in node.findall(path, XSD_NS):
            if (attr.get("use") or "").strip() != "required":
                continue
            name = attr.get("ref") or attr.get("name") or attr.get("type") or ""
            name = name.strip()
            if name and name not in required_attributes:
                required_attributes.append(name)
            if len(required_attributes) >= limit:
                return required_attributes
    return required_attributes


def extract_xsd_structured_metadata(text: str, max_declarations: int = 250) -> dict[str, dict]:
    """Parse XSD and return declaration-level structured metadata keyed by heading/name."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}

    declarations = list(root.findall("./xs:element", XSD_NS))
    declarations.extend(root.findall("./xs:complexType", XSD_NS))
    declarations.extend(root.findall("./xs:simpleType", XSD_NS))
    declarations.extend(root.findall("./xs:group", XSD_NS))

    structured: dict[str, dict] = {}
    for node in declarations[:max_declarations]:
        declaration_type = node.tag.rsplit("}", 1)[-1]
        declaration_name = (node.get("name") or node.get("ref") or "").strip()
        if declaration_type not in {"element", "complexType", "simpleType", "group"} or not declaration_name:
            continue

        base_type = node.get("type") or ""
        if not base_type:
            restriction = node.find("./xs:simpleType/xs:restriction", XSD_NS)
            if restriction is not None:
                base_type = restriction.get("base", "")
        if not base_type:
            extension = node.find("./xs:complexContent/xs:extension", XSD_NS)
            if extension is not None:
                base_type = extension.get("base", "")

        structured[declaration_name] = {
            "schema": {
                "declarationType": declaration_type,
                "declarationName": declaration_name,
                "baseType": base_type,
                "childElements": _extract_xsd_child_elements(node),
                "requiredChildElements": _extract_xsd_required_child_elements(node),
                "attributes": _extract_xsd_attributes(node),
                "requiredAttributes": _extract_xsd_required_attributes(node),
                "documentation": _extract_xsd_documentation(node),
            }
        }
    return structured


def _build_xsd_summary_text(node: ET.Element, source_name: str) -> tuple[str, str] | None:
    declaration_type = node.tag.rsplit("}", 1)[-1]
    if declaration_type not in {"element", "complexType", "simpleType", "group"}:
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
    enumerations, more = _extract_xsd_enumerations(node)
    if enumerations:
        parts.append("Allowed values: " + "; ".join(enumerations) + (f"; … and {more} more" if more else ""))
    child_documentation = _extract_xsd_child_documentation(node)
    if child_documentation:
        parts.append("Child element documentation:\n" + "\n".join(f"- {line}" for line in child_documentation))

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
    top_level_declarations.extend(root.findall("./xs:group", XSD_NS))

    for node in top_level_declarations[:max_declarations]:
        summary = _build_xsd_summary_text(node, source_name)
        if summary is None:
            continue
        summary_text, heading = summary
        chunks.append((summary_text, "schema_fragment", heading))

    if chunks:
        return chunks

    # A schema without declarations (siri_all_functionalServices.xsd, netex_all_objects_*.xsd) includes other
    # schemas and says in its metadata what they are. Its raw text, cut into three 800-character windows, lost
    # most of that text and split words ("SIRI-ET E" | "stimated Timetable"), so the service names were
    # missing from the block that described the services (prod "What is SIRI used for?", 2026-11-07).
    document = _schema_document_chunks(root, source_name)
    if document:
        return document

    fallback = split_text(text, chunk_size=800, chunk_overlap=120)
    return [(chunk, "schema_fragment", source_name) for chunk in fallback[:3]]


SCHEMA_DOCUMENT_MAX_CHARS = 1500
# Metadata elements that describe what a schema is; the rest (Publisher, Rights, Category, Format) is boilerplate.
_SCHEMA_DOCUMENT_TAGS = ("Title", "Description")
_SCHEMA_LINE_BREAK_TAGS = {"p", "li", "br", "div", "ul", "ol"}


def _local_name(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _element_lines(element) -> list[str]:
    """An element's text as lines: one per paragraph and per list item ("- ...")."""
    parts: list[str] = []

    def walk(node) -> None:
        local = _local_name(node.tag)
        if local in _SCHEMA_LINE_BREAK_TAGS:
            parts.append("\n- " if local == "li" else "\n")
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                parts.append(child.tail)
        if local in _SCHEMA_LINE_BREAK_TAGS:
            parts.append("\n")

    walk(element)
    lines = [" ".join(line.split()) for line in "".join(parts).split("\n")]
    return [line for line in lines if line and line != "-"]


def _split_at_words(line: str, max_chars: int) -> list[str]:
    """A line in pieces of at most max_chars, cut between words (a single longer word stays whole)."""
    pieces: list[str] = []
    current = ""
    for word in line.split(" "):
        if current and len(current) + 1 + len(word) > max_chars:
            pieces.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        pieces.append(current)
    return pieces


def _schema_has_declarations(root) -> bool:
    return any(root.findall(f"./xs:{kind}", XSD_NS) for kind in ("element", "complexType", "simpleType", "group"))


def _schema_document_chunks(root, source_name: str) -> list[tuple[str, str, str]]:
    """Chunks of a declaration-less schema's own description: title, description, root documentation and the
    schemas it includes, packed at line boundaries."""
    lines: list[str] = []
    annotation = root.find("./xs:annotation", XSD_NS)
    if annotation is not None:
        # A Format block's Description ("XML schema, W3C Recommendation 2001") is about the file format.
        parents = {child: parent for parent in annotation.iter() for child in parent}
        for node in annotation.iter():
            local = _local_name(node.tag)
            if local not in _SCHEMA_DOCUMENT_TAGS or _local_name(parents.get(node, annotation).tag) == "Format":
                continue
            lines.extend(f"Title: {line}" if local == "Title" else line for line in _element_lines(node))
        for documentation in annotation.findall("./xs:documentation", XSD_NS):
            lines.extend(_element_lines(documentation))
    included = [
        Path(node.get("schemaLocation", "")).name
        for kind in ("include", "import")
        for node in root.findall(f"./xs:{kind}", XSD_NS)
        if node.get("schemaLocation")
    ]
    if included:
        lines.append(f"Schema {source_name} includes: " + ", ".join(dict.fromkeys(included)))
    if not lines:
        return []
    chunks: list[str] = []
    current = ""
    for line in lines:
        pieces = _split_at_words(line, SCHEMA_DOCUMENT_MAX_CHARS)
        for piece in pieces:
            if current and len(current) + 1 + len(piece) > SCHEMA_DOCUMENT_MAX_CHARS:
                chunks.append(current)
                current = ""
            current = f"{current}\n{piece}" if current else piece
    if current:
        chunks.append(current)
    return [(chunk, "schema_fragment", source_name) for chunk in chunks]


# Bumped when split_turtle changes: it is part of each Turtle file's content hash, so the next incremental
# index re-chunks .ttl files that have not changed themselves.
TURTLE_CHUNKER_VERSION = "1"
# The same for split_xsd_summary: 1 added enumeration values and the documentation of child elements.
XSD_CHUNKER_VERSION = "1"


# The same for the chunks of a schema without declarations (_schema_document_chunks). Kept apart from
# XSD_CHUNKER_VERSION so a change re-chunks (and re-embeds) only those files, 97 of 1,136, not every schema.
XSD_DOCUMENT_CHUNKER_VERSION = "1"


def chunker_marker(suffix: str, text: str = "") -> str:
    """Prefix of a file's content hash naming the chunker version, for the file types with a versioned chunker."""
    suffix = suffix.lower()
    if suffix == ".ttl":
        return f"turtle-chunker {TURTLE_CHUNKER_VERSION}\n"
    if suffix == ".xsd":
        marker = f"xsd-chunker {XSD_CHUNKER_VERSION}\n"
        if text:
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                return marker
            if not _schema_has_declarations(root):
                marker += f"xsd-document-chunker {XSD_DOCUMENT_CHUNKER_VERSION}\n"
        return marker
    return ""

_TURTLE_TYPE = re.compile(r"(?:^|[\s;])(?:a|rdf:type)\s+([A-Za-z][\w-]*:[\w.-]+|<[^>\s]+>)")


def _turtle_statements(text: str) -> list[str]:
    """Top-level Turtle statements (subject plus its predicates, up to the closing "."), prefixes dropped.

    A small scanner, not a parser: it skips strings (also triple-quoted), IRIs and comments, so a "." inside
    them or in a number does not end a statement."""
    statements: list[str] = []
    start = 0
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "#":
            newline = text.find("\n", i)
            i = n if newline < 0 else newline
            continue
        if ch in "\"'":
            quote = ch * 3 if text.startswith(ch * 3, i) else ch
            i += len(quote)
            while i < n and not text.startswith(quote, i):
                i += 2 if text[i] == "\\" else 1
            i += len(quote)
            continue
        if ch == "<":
            close = text.find(">", i)
            if close > 0 and not any(c.isspace() for c in text[i + 1 : close]):
                i = close + 1
                continue
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth = max(0, depth - 1)
        elif ch == "." and depth == 0 and (i + 1 == n or text[i + 1].isspace()):
            statement = text[start : i + 1].strip()
            if statement and not statement.lower().startswith(("@prefix", "@base", "prefix", "base")):
                statements.append(statement)
            start = i + 1
        i += 1
    tail = text[start:].strip()
    if tail:
        statements.append(tail)
    return statements


def _turtle_type(statement: str) -> str:
    match = _TURTLE_TYPE.search(statement)
    return match.group(1) if match else ""


def split_turtle(text: str, max_chars: int) -> list[tuple[str, str, str]]:
    """Chunks of whole resource descriptions, so a record (an example's dcat:CatalogRecord, a code list entry)
    is never cut in two. Consecutive statements of the same rdf:type are packed up to max_chars; a new type
    starts a new chunk. The heading names the types in the chunk. A statement longer than max_chars is split
    as prose. Text with no statements (not Turtle after all) falls back to prose."""
    statements = _turtle_statements(text)
    if not statements:
        return [(c, "prose", "") for c in split_text(text, chunk_size=max_chars, chunk_overlap=max_chars // 6)]
    results: list[tuple[str, str, str]] = []
    current: list[str] = []
    current_types: list[str] = []

    def flush() -> None:
        if current:
            heading = ", ".join(dict.fromkeys(t for t in current_types if t))
            results.append(("\n\n".join(current), "prose", heading))
        current.clear()
        current_types.clear()

    for statement in statements:
        statement_type = _turtle_type(statement)
        if len(statement) > max_chars:
            flush()
            for piece in split_text(statement, chunk_size=max_chars, chunk_overlap=max_chars // 6):
                results.append((piece, "prose", statement_type))
            continue
        size = sum(len(part) + 2 for part in current) + len(statement)
        new_type = bool(statement_type) and bool(current_types) and statement_type not in current_types
        if current and (size > max_chars or new_type):
            flush()
        current.append(statement)
        current_types.append(statement_type)
    flush()
    return results


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
    if ext in {".html", ".htm"}:
        return split_html(text, max_chars=chunk_size, source_name=source_name)
    if ext == ".ttl":
        return split_turtle(text, max_chars=chunk_size)
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
    backend: str | None = None,
) -> str:
    """Build contextual embedding input so vectors encode document role and provenance.

    A semantic model gets the location and the text only; the metadata lines steer the
    hash vectors. backend overrides EMBEDDING_BACKEND, as in build_text_embeddings_batch."""
    if uses_semantic(backend):
        return passage_text(source_path, heading, chunk_text)
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
    """Delete chunks in bounded batches to avoid large variable lists in a single query."""
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
    """Prune repository chunks using batched deletes."""
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


def prune_alias_spellings(canonical_url: str) -> int:
    """Delete the chunks and file records stored under another spelling of `canonical_url`.

    A repository indexed under an old name (OpRa-CEN/OpRa) and later under its canonical URL would
    otherwise keep two full copies, because pruning only looks at one URL. Nothing is deleted unless
    the canonical repository has chunks, so the only copy of a repository is never removed.
    Returns the number of chunks deleted.
    """

    stored = set(SourceChunk.objects.order_by().values_list("repository_url", flat=True).distinct())
    stored |= set(IndexedSourceFile.objects.order_by().values_list("repository_url", flat=True).distinct())
    aliases = sorted(url for url in stored if url != canonical_url and canonical_repository_url(url) == canonical_url)
    if not aliases or not SourceChunk.objects.filter(repository_url=canonical_url).exists():
        return 0

    deleted = 0
    for alias in aliases:
        chunk_ids = list(SourceChunk.objects.filter(repository_url=alias).values_list("chunk_id", flat=True))
        deleted += _delete_chunks_by_ids(alias, chunk_ids)
        IndexedSourceFile.objects.filter(repository_url=alias).delete()
    return deleted


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


def _is_github_rate_limit_error(error_text: str) -> bool:
    """Return True when GitHub API response indicates rate limiting."""
    lowered = error_text.lower()
    return "rate limit" in lowered


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
        try:
            payload, link_header = _github_api_get_json(
                next_url,
                github_token=github_token,
                verify_ssl=verify_ssl,
                ca_bundle=ca_bundle,
            )
        except ValueError as exc:
            if _is_github_rate_limit_error(str(exc)):
                logger.warning("GitHub issues ingestion stopped due to API rate limit for %s", repo_url)
                break
            raise
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
                try:
                    comments_payload, _ = _github_api_get_json(
                        comments_url,
                        github_token=github_token,
                        verify_ssl=verify_ssl,
                        ca_bundle=ca_bundle,
                    )
                except ValueError as exc:
                    if _is_github_rate_limit_error(str(exc)):
                        logger.warning(
                            "Skipping issue comments due to GitHub API rate limit for %s issue #%s",
                            repo_url,
                            number,
                        )
                        comments_payload = []
                    else:
                        raise
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
    stats = IndexStats()
    # One spelling per repository: chunk ids and stored URLs include it, so an
    # alias would otherwise index a second full copy of the same files.
    repo_url = canonical_repository_url(repo_url)

    try:
        validate_repository_allowed(repo_url, allowed_repositories)

        selected_profile = load_profile_rules(profile)
        include_rules = (include_paths or []) + selected_profile["include"]
        exclude_rules = (exclude_paths or []) + selected_profile["exclude"]
        include_exts = include_extensions or (DEFAULT_EXTENSIONS | selected_profile["extensions"])

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
            content_hash = build_content_hash(chunker_marker(file_path.suffix, raw_text) + raw_text)
            if incremental:
                indexed_file = IndexedSourceFile.objects.filter(
                    repository_url=repo_url,
                    source_path=relative_path,
                    content_hash=content_hash,
                ).first()
                if indexed_file:
                    # Files indexed before schema references existed get them now,
                    # so the next incremental refresh fills every XSD without a full run.
                    if file_path.suffix.lower() == ".xsd" and not indexed_file.schema_references:
                        indexed_file.schema_references = extract_schema_references(raw_text)
                        indexed_file.save(update_fields=["schema_references", "updated_at"])
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
            xsd_metadata = (
                extract_xsd_structured_metadata(raw_text)
                if file_path.suffix.lower() == ".xsd"
                else {}
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
                        "structured_metadata": xsd_metadata.get(heading, {}),
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
                    "structured_metadata": chunk_record["structured_metadata"],
                    "embedding_vector": chunk_embedding,
                    # Changed text: the other backend's vector is stale (reembed_chunks fills it again).
                    "alternate_vector": None,
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
                    "schema_references": (
                        extract_schema_references(raw_text) if file_path.suffix.lower() == ".xsd" else {}
                    ),
                },
            )

        if include_issues:
            try:
                issue_documents = fetch_github_issue_documents(
                    repo_url=repo_url,
                    github_token=github_token,
                    verify_ssl=github_verify_ssl,
                    ca_bundle=github_ca_bundle,
                )
            except ValueError as exc:
                if _is_github_rate_limit_error(str(exc)):
                    logger.warning("Skipping GitHub issues ingestion due to API rate limit for %s", repo_url)
                    issue_documents = []
                else:
                    raise
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
                            "structured_metadata": {},
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
                        "structured_metadata": issue_chunk_record["structured_metadata"],
                        "embedding_vector": chunk_embedding,
                        "alternate_vector": None,
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
