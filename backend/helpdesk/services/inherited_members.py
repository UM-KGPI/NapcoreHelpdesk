"""
A served class block shows the members the class inherits.

The record of a class (an attribute list and a list of relations to other classes) shows only the members the class
declares; the members it inherits from its supertypes sit in the records of those supertypes, which are not among the
six served passages. A question about what a class carries (which attribute says whether a charging point is
available, which relation leads to the impact of an accident) then finds the answer in none of the six.

With RETRIEVAL_INHERITED_MEMBERS set, a served passage that is the record of a class (see class_record) is followed by
the members its supertypes declare, each group headed by the supertype it comes from, the nearest supertype first.
The lines are those stored in the supertype's own record, copied as they are (type, multiplicity, definition,
relation and target); nothing is reworded or added but the group headings and one count line where the size limit
leaves lines out. Only the text of the served passage grows: the six passages, their order, their chunk ids, sources
and paths are those the search chose, and a line shown is cited through the passage it is shown in.

What makes a passage "the record of a class", without naming a standard: the rows of its source path in the index are
all pieces of the prepared cut that form a unit of their own path, and the joined text has a line "Subtype of: ..."
(the way the model reader writes the supertypes of a class). A supertype name is resolved to a record of the same
repository and the same folder whose path ends in that name (the model reader writes "Namespace.Name" where the bare
name repeats in the model). What cannot be resolved to exactly one record is left out.

Off (False) by default: passages are returned as before.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-24  |  Modified: 2026-11-24
"""

from __future__ import annotations

import re
import time

from helpdesk.services.prepared_cut import CUT_VERSION, META_KEY
from helpdesk.services.read_large import JOINER, _split

# Fixed before the first measurement (run folder b2, file b2-fixed-before-measuring.md).
MAX_RECORD_PIECES = 12  # a record of more pieces is not read (the longest class record of the model has fewer)
MAX_DEPTH = 10  # supertypes followed from a class
SUBTYPE_LINE = re.compile(r"^Subtype of: (.+)$", re.MULTILINE)
# A stored member line: an attribute ("- name (type, 0..1): definition") or a relation ("- role -> Target, 0..1").
_ATTRIBUTE = re.compile(r"^- \S+ \(")
_RELATION = re.compile(r"^- \S+ -> ")
COUNT_LINE = "(%d more inherited lines of %s not shown)"
HEADING = "Inherited from %s:"
# Characters added at most per block and per question (headings, lines, count lines and their line ends).
MAX_CHARS_PER_BLOCK = 2000
MAX_CHARS_PER_QUESTION = 4000


def enabled() -> bool:
    from django.conf import settings

    return bool(getattr(settings, "RETRIEVAL_INHERITED_MEMBERS", False))


def _rows_of_path(repository_url: str, source_path: str) -> list[tuple[str, dict]]:
    from helpdesk.models import SourceChunk

    return list(
        SourceChunk.objects.filter(repository_url=repository_url, source_path=source_path).values_list(
            "text", "structured_metadata"
        )[: MAX_RECORD_PIECES + 1]
    )


def _paths_ending_in(repository_url: str, folder: str, name: str) -> list[str]:
    """The source paths of the repository in the folder whose last segment is the name, or ends in '.name'."""
    from helpdesk.models import SourceChunk

    found = SourceChunk.objects.filter(
        repository_url=repository_url, source_path__startswith=f"{folder}/", source_path__endswith=name
    ).values_list("source_path", flat=True).distinct()
    result = []
    for path in set(found):
        last = path[len(folder) + 1 :]
        if "/" not in last and (last == name or last.endswith(f".{name}")):
            result.append(path)
    return sorted(result)


def joined_record(rows: list[tuple[str, dict]], source_path: str) -> str | None:
    """The joined text of the rows of a path when they are a record of the prepared cut (every row a piece whose unit
    is the path; the lead line once, then each body in order), else None. Same joining as whole_record."""
    if not rows or len(rows) > MAX_RECORD_PIECES:
        return None
    parts: dict[int, tuple[str, str]] = {}
    for text, metadata in rows:
        meta = (metadata or {}).get(META_KEY)
        if not isinstance(meta, dict) or meta.get("v") != CUT_VERSION or meta.get("unit") != source_path:
            return None
        if "seq" not in meta or "body" not in meta:
            return None
        parts[int(meta["seq"])] = _split(text, meta)
    if len(parts) != len(rows):
        return None
    order = sorted(parts)
    return parts[order[0]][0] + JOINER.join(parts[seq][1] for seq in order)


def supertype_names(record_text: str) -> list[str]:
    """The names on the 'Subtype of:' line of a record, in the order written."""
    match = SUBTYPE_LINE.search(record_text)
    if not match:
        return []
    return [name.strip() for name in match.group(1).split(",") if name.strip()]


def member_lines(record_text: str) -> list[str]:
    """The stored attribute and relation lines of a record, in their order (a line that is neither is not a member;
    the 'Values:' lines of an enumeration have no type and are not taken)."""
    return [line for line in record_text.split("\n") if _ATTRIBUTE.match(line) or _RELATION.match(line)]


def resolve(repository_url: str, source_path: str, name: str, find=_paths_ending_in) -> str | None:
    """The source path of the record the supertype name stands for, or None when there is not exactly one."""
    folder = source_path.rsplit("/", 1)[0] if "/" in source_path else ""
    if not folder:
        return None
    paths = find(repository_url, folder, name)
    return paths[0] if len(paths) == 1 else None


def inherited_groups(
    repository_url: str, source_path: str, fetch=_rows_of_path, find=_paths_ending_in
) -> tuple[bool, list[dict]]:
    """(is a class record, groups): the groups are [{"name", "path", "depth", "lines"}] nearest supertype first
    (breadth first over the 'Subtype of:' lines), each with the member lines of that supertype's own record.

    A supertype that cannot be resolved to a record, or whose record is not read, is left out and its own
    supertypes are not followed ("unresolved" groups are returned with lines None so the diagnosis can count them)."""
    own = joined_record(fetch(repository_url, source_path), source_path)
    if own is None or not supertype_names(own):
        return False, []
    groups: list[dict] = []
    seen = {source_path}
    level = [(name, source_path) for name in supertype_names(own)]
    depth = 0
    while level and depth < MAX_DEPTH:
        depth += 1
        following: list[tuple[str, str]] = []
        for name, child_path in level:
            path = resolve(repository_url, child_path, name, find)
            if path is None or path in seen:
                groups.append({"name": name, "path": path, "depth": depth, "lines": None})
                continue
            seen.add(path)
            text = joined_record(fetch(repository_url, path), path)
            if text is None:
                groups.append({"name": name, "path": path, "depth": depth, "lines": None})
                continue
            groups.append({"name": name, "path": path, "depth": depth, "lines": member_lines(text)})
            following.extend((n, path) for n in supertype_names(text))
        level = following
    return True, groups


def _kind(line: str) -> str:
    return "relation" if _RELATION.match(line) else "attribute"


def render(groups: list[dict], max_chars: int) -> tuple[str, list[dict]]:
    """(text, shown) for the groups of one block within max_chars; ("", []) when no line fits.

    Lines are taken in priority order: the groups nearest first, inside a group the relation lines before the attribute
    lines, each in stored order, whole, while the running total stays within max_chars; the first line that does not
    fit ends the taking. The lines shown are put back in stored order per group; a group that loses lines ends with a
    count line. shown: [{"name", "path", "lines"}] for the groups with at least one line shown."""
    groups = [g for g in groups if g.get("lines")]
    order = [
        (gi, li)
        for gi, group in enumerate(groups)
        for kind in ("relation", "attribute")
        for li, line in enumerate(group["lines"])
        if _kind(line) == kind
    ]

    def build(kept: set[tuple[int, int]]) -> tuple[str, list[dict]]:
        out: list[str] = []
        shown: list[dict] = []
        for gi, group in enumerate(groups):
            lines = [line for li, line in enumerate(group["lines"]) if (gi, li) in kept]
            if not lines:
                continue
            out.append(HEADING % group["name"])
            out.extend(lines)
            if len(lines) < len(group["lines"]):
                out.append(COUNT_LINE % (len(group["lines"]) - len(lines), group["name"]))
            shown.append({"name": group["name"], "path": group["path"], "lines": lines})
        return "\n".join(out), shown

    kept: set[tuple[int, int]] = set()
    for item in order:
        if len(build(kept | {item})[0]) > max_chars:
            break
        kept.add(item)
    return build(kept) if kept else ("", [])


def with_inherited(chunks: list[dict], max_passages: int, fetch=_rows_of_path, find=_paths_ending_in) -> tuple[list[dict], dict]:
    """chunks with the inherited members appended to the text of each of the first max_passages passages that is the
    record of a class; returns them and {"blocks", "lines", "chars", "ms"}.

    The text before stays in "baseText" (the prompt builder trims only that part: "inheritedBaseChars" is its length);
    "inheritedGroups" holds what was added, per supertype. Path blocks and passages that are no cut record stay as
    they are; so do the order, the ids, the sources and the paths."""
    started = time.perf_counter()
    cache: dict[tuple[str, str], tuple[bool, list[dict]]] = {}
    left = MAX_CHARS_PER_QUESTION
    result: list[dict] = []
    seen_passages = 0
    stats = {"blocks": 0, "lines": 0, "chars": 0}
    for chunk in chunks:
        if chunk.get("semanticPath"):
            result.append(chunk)
            continue
        seen_passages += 1
        if seen_passages > max_passages or left <= 0:
            result.append(chunk)
            continue
        meta = ((chunk.get("structuredMetadata") or {}).get(META_KEY)) or {}
        repository_url, path = chunk.get("repositoryUrl", ""), chunk.get("sourcePath", "")
        if meta.get("v") != CUT_VERSION or meta.get("unit") != path:
            result.append(chunk)
            continue
        key = (repository_url, path)
        if key not in cache:
            cache[key] = inherited_groups(repository_url, path, fetch, find)
        is_record, groups = cache[key]
        if not is_record:
            result.append(chunk)
            continue
        text, shown = render(groups, min(MAX_CHARS_PER_BLOCK, left))
        if not text:
            result.append(chunk)
            continue
        base = str(chunk.get("text", ""))
        left -= len(text) + 1
        stats["blocks"] += 1
        stats["lines"] += sum(len(g["lines"]) for g in shown)
        stats["chars"] += len(text) + 1
        result.append({**chunk, "text": f"{base}\n{text}", "baseText": base, "inheritedBaseChars": len(base), "inheritedGroups": shown})
    stats["ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result, stats
