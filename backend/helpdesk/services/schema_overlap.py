"""Shared structure between two XSD schemas, as evidence for comparison questions.

"What are the overlaps between SIRI-CA and SIRI-VM?" has no answer in any single
text chunk: each declaration chunk shows one side, and the overlap is the set of
types both schemas use. Like the relation paths for NeTEx, the answer is computed
from the structure and handed to the model as one evidence chunk.

Part of the indexing pipeline: when a repository is indexed (every scheduled or
manual refresh), extract_schema_references stores each XSD's includes and
referenced types on its IndexedSourceFile row, at the indexed commit. Comparison
questions read those rows, so the evidence always matches the indexed version.

Generic for any pair of schema files in any indexed repository. Types that nearly
every sibling schema references (the request, delivery and subscription framework
of a SIRI service, for instance) are reported separately as common framework; the
threshold comes from the repository itself.
"""

from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

_XSD = "{http://www.w3.org/2001/XMLSchema}"
_BUILTIN_PREFIXES = ("xsd:", "xs:")
# A type referenced by at least this share of the sibling schemas is common framework.
FRAMEWORK_SHARE = 0.75
MAX_LISTED_TYPES = 12
MAX_USES_PER_SIDE = 5


def extract_schema_references(xsd_text: str) -> dict:
    """{"includes": [file names], "uses": {type: [declarations using it]}} of one schema.

    A reference is any type=, ref= or base= that is not a built-in XSD type; each is
    attributed to the nearest named declaration around it. Returns {} for text that
    is not well-formed XML."""
    try:
        root = ET.fromstring(xsd_text)
    except ET.ParseError:
        return {}
    includes: set[str] = set()
    uses: dict[str, set[str]] = {}
    stack: list[tuple[ET.Element, str]] = [(root, "")]
    while stack:
        node, owner = stack.pop()
        if node.tag in (f"{_XSD}include", f"{_XSD}import") and node.get("schemaLocation"):
            includes.add(os.path.basename(node.get("schemaLocation")))
        name = node.get("name") or owner
        for attribute in ("type", "ref", "base"):
            value = node.get(attribute)
            if value and not value.startswith(_BUILTIN_PREFIXES):
                uses.setdefault(value.split(":", 1)[-1], set()).add(node.get("name") or owner or "(schema)")
        for child in node:
            stack.append((child, name))
    return {"includes": sorted(includes), "uses": {t: sorted(names) for t, names in sorted(uses.items())}}


def _sibling_paths(schema_path: str, indexed_paths: list[str]) -> list[str]:
    """Schemas of the same kind: same directory and filename suffix (siri_*_service.xsd),
    else the same directory."""
    path = PurePosixPath(schema_path)
    same_dir = [p for p in indexed_paths if PurePosixPath(p).parent == path.parent]
    if "_" in path.name:
        suffix = "_" + path.name.rsplit("_", 1)[-1]
        same_kind = [p for p in same_dir if p.endswith(suffix)]
        if len(same_kind) >= 3:
            return same_kind
    return same_dir


@dataclass
class Overlap:
    paths: list[str]
    names: list[str]
    repository_url: str
    commit_sha: str
    domain: list[tuple[str, list[list[str]]]]
    framework: list[str]
    common_includes: list[str]


def compute_overlap(schema_paths: list[str], names: list[str], references_by_path: dict[str, dict], repository_url: str, commit_sha: str) -> Overlap | None:
    """Shared referenced types of two or more schemas, split into domain and framework.

    references_by_path holds the stored references of every indexed XSD of the
    repository (the siblings are needed to tell framework types apart)."""
    if len(schema_paths) < 2 or any(not references_by_path.get(path) for path in schema_paths):
        return None
    parsed = [references_by_path[path] for path in schema_paths]
    siblings = [references_by_path[p] for p in _sibling_paths(schema_paths[0], list(references_by_path)) if references_by_path[p]]

    shared = set.intersection(*(set(refs.get("uses", {})) for refs in parsed))
    framework: list[str] = []
    ranked: list[tuple[float, int, str, list[list[str]]]] = []
    for type_name in sorted(shared):
        share = sum(1 for refs in siblings if type_name in refs.get("uses", {})) / max(1, len(siblings))
        if share >= FRAMEWORK_SHARE:
            framework.append(type_name)
        else:
            uses = [refs["uses"][type_name] for refs in parsed]
            ranked.append((share, -sum(len(u) for u in uses), type_name, uses))
    # Types few sibling schemas use are the most specific overlap; list them first.
    ranked.sort()
    common_includes = sorted(set.intersection(*(set(refs.get("includes", [])) for refs in parsed)))
    return Overlap(
        paths=list(schema_paths),
        names=list(names),
        repository_url=repository_url,
        commit_sha=commit_sha if commit_sha and commit_sha != "unknown" else "main",
        domain=[(type_name, uses) for _share, _count, type_name, uses in ranked],
        framework=framework,
        common_includes=common_includes,
    )


def overlap_for_schemas(schema_paths: list[str], names: list[str]) -> Overlap | None:
    """compute_overlap from the stored references of the indexed repository."""
    from helpdesk.models import IndexedSourceFile

    first = IndexedSourceFile.objects.filter(source_path=schema_paths[0]).values("repository_url", "commit_sha").first()
    if first is None:
        return None
    rows = IndexedSourceFile.objects.filter(repository_url=first["repository_url"], source_path__endswith=".xsd")
    references = {row["source_path"]: row["schema_references"] for row in rows.values("source_path", "schema_references")}
    return compute_overlap(schema_paths, names, references, first["repository_url"], first["commit_sha"])


def format_overlap_chunk(overlap: Overlap) -> dict:
    files = [PurePosixPath(path).name for path in overlap.paths]
    sides = [f"{name} ({file})" for name, file in zip(overlap.names, files)]
    lines = [f"SHARED STRUCTURE between {' and '.join(sides)}, computed from the XSD schemas:"]
    if overlap.domain:
        lines.append("Types used by both (specific to them, not common to most schemas of this kind):")
        for type_name, uses in overlap.domain[:MAX_LISTED_TYPES]:
            parts = [f"in {name} by {', '.join(used_by[:MAX_USES_PER_SIDE])}" for name, used_by in zip(overlap.names, uses)]
            lines.append(f"- {type_name}: " + "; ".join(parts))
    else:
        lines.append("No types are shared beyond the common framework.")
    if overlap.common_includes:
        lines.append("Both include: " + ", ".join(overlap.common_includes) + ".")
    if overlap.framework:
        listed = overlap.framework[:MAX_LISTED_TYPES]
        lines.append(
            "Both also use the framework common to almost all schemas of this kind: "
            + ", ".join(listed)
            + (", and others." if len(overlap.framework) > len(listed) else ".")
        )
    chunk_id = "schema-overlap-" + "-".join(PurePosixPath(path).stem for path in overlap.paths).lower()
    return {
        "id": hash(chunk_id) % (10**8),
        "chunkId": chunk_id,
        # Its own path, so per-path caps and coverage never treat it as the schema itself.
        "sourcePath": f"{overlap.paths[0]}#shared-structure",
        "repositoryUrl": f"{overlap.repository_url.rstrip('/')}/blob/{overlap.commit_sha}/{overlap.paths[0]}",
        "commitSha": overlap.commit_sha,
        "label": "Shared structure: " + " ↔ ".join(overlap.names),
        "heading": "Shared structure: " + " ↔ ".join(files),
        "text": "\n".join(lines),
        "docType": "ontology-relation",
        "standardsScope": [],
    }
