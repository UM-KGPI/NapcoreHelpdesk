"""
INSPIRE Transport Networks as a retrieval source: the data specification and its code lists.

MMTIS Art. 4(1)(c) requires, for the spatial network, the requirements of Article 7 of the INSPIRE
Directive 2007/2/EC; the legal texts are part of the EU legislation source (services/regulations.py).
This source adds what those rules point to:

- the Technical Guidelines "D2.8.I.7 Data Specification on Transport Networks" (CC BY 4.0), published as
  AsciiDoc in github.com/INSPIRE-MIF/technical-guidelines, pinned to a release tag;
- the INSPIRE registry entries of the code lists that specification uses (inspire.ec.europa.eu/codelist).

Built like the napcore.eu source (services/napcore_site.py): the files are fetched once on a development
machine into docs/inspire/, reviewed in git, and indexed from there, also on deploy, without network
access. The guidelines repository is 1.2 GB, too large for the shallow clones of the harvested sources.

The chunks belong to the opt-in scope "INSPIRE": searched only when a question names INSPIRE, so they
never crowd out the standards. Citations link to the line of the specification on GitHub and to the
code list in the registry.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-05  |  Modified: 2026-11-05
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.index_builder import build_chunk_embedding_text, build_content_hash

SCOPE = "INSPIRE"
DOC_TYPE = "inspire"
INSPIRE_DIR = Path(__file__).resolve().parents[3] / "docs" / "inspire"
SPEC_REPOSITORY = "https://github.com/INSPIRE-MIF/technical-guidelines"
SPEC_TAG = "v2025.1"
SPEC_REPO_PATH = "data/tn/dataspecification_tn.adoc"
SPEC_PATH = INSPIRE_DIR / "dataspecification_tn.adoc"
SPEC_TITLE = "INSPIRE Data Specification on Transport Networks – Technical Guidelines (D2.8.I.7)"
CODELISTS_PATH = INSPIRE_DIR / "codelists.json"
REGISTRY_URL = "https://inspire.ec.europa.eu/codelist/"
MAX_CHUNK_CHARS = 1500
# A section shorter than this joins the next one (headings with only an introductory sentence).
MIN_SECTION_CHARS = 120
# Part of the stored content hash: bump it when parsing or chunking changes, so the next run re-indexes.
PARSER_VERSION = "2"
_USER_AGENT = "NAPCORE-Helpdesk-indexer/1.0 (+https://kgpi.fgpa.um.si/napcore-helpdesk/)"
_CODELIST_REFERENCE = re.compile(r"inspire\.ec\.europa\.eu/codelist/([A-Za-z]+Value)\b")
# Chapters that are not the data model: map styling of the view services, the bibliography and the test
# suite. They name every spatial object type, so without a lower quality they outrank its definition.
_SECONDARY_CHAPTERS = ("Portrayal", "Bibliography", "Abstract Test Suite")


def spec_url(line: int | None = None) -> str:
    """The pinned specification on GitHub; with a line, its plain-text view at that line."""
    base = f"{SPEC_REPOSITORY}/blob/{SPEC_TAG}/{SPEC_REPO_PATH}"
    return f"{base}?plain=1#L{line}" if line else base


def is_inspire_url(url: str) -> bool:
    """True for a link to the pinned specification or to an INSPIRE registry code list (citation allow-list)."""
    url = url or ""
    return url.startswith(f"{SPEC_REPOSITORY}/blob/{SPEC_TAG}/{SPEC_REPO_PATH}") or url.startswith(REGISTRY_URL)


# ---- Fetching (development machine) ----------------------------------------------------------------


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:  # nosec B310 - fixed https hosts
        return response.read()


def codelist_names(spec_text: str) -> list[str]:
    """The code lists the specification links to the registry, in order of first mention."""
    return list(dict.fromkeys(_CODELIST_REFERENCE.findall(spec_text)))


def _registry_text(field) -> str:
    return re.sub(r"\s+", " ", (field or {}).get("text", "") if isinstance(field, dict) else str(field or "")).strip()


def compact_codelist(name: str, payload: dict) -> dict:
    """The parts of a registry entry that answers need: label, definition, description and the values."""
    codelist = payload.get("codelist", payload)
    values = []
    for item in codelist.get("containeditems", []):
        value = item.get("value", item)
        values.append(
            {
                "id": value.get("id", ""),
                "label": _registry_text(value.get("label")),
                "definition": _registry_text(value.get("definition")),
                "description": _registry_text(value.get("description")),
            }
        )
    return {
        "name": name,
        "id": codelist.get("id", f"{REGISTRY_URL}{name}"),
        "label": _registry_text(codelist.get("label")),
        "definition": _registry_text(codelist.get("definition")),
        "description": _registry_text(codelist.get("description")),
        "values": values,
    }


def fetch(out_dir: Path = INSPIRE_DIR, report=None) -> dict[str, int]:
    """Download the pinned specification and the registry entries of its code lists into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = f"https://raw.githubusercontent.com/INSPIRE-MIF/technical-guidelines/{SPEC_TAG}/{SPEC_REPO_PATH}"
    spec = _get(raw)
    (out_dir / SPEC_PATH.name).write_bytes(spec)
    codelists, failed = [], 0
    for name in codelist_names(spec.decode("utf-8")):
        try:
            payload = json.loads(_get(f"{REGISTRY_URL}{name}/{name}.en.json"))
            codelists.append(compact_codelist(name, payload))
            if report:
                report(f"fetched code list {name} ({len(codelists[-1]['values'])} values)")
        except Exception as error:  # a registry entry that is missing or malformed is reported, not fatal
            failed += 1
            if report:
                report(f"failed code list {name}: {error}")
        time.sleep(0.2)
    text = json.dumps({"source": REGISTRY_URL, "codelists": codelists}, ensure_ascii=False, indent=1) + "\n"
    (out_dir / CODELISTS_PATH.name).write_text(text, encoding="utf-8")
    return {"codelists": len(codelists), "failed": failed}


# ---- Parsing the AsciiDoc specification ------------------------------------------------------------

_HEADING = re.compile(r"^(={1,6})\s+(.+?)\s*$")
_ATTRIBUTE_LINE = re.compile(r"^:[\w-]+:")
_BLOCK_ATTRIBUTE = re.compile(r"^\[[^\]]*\]$")  # [cols=","], [NOTE], [[anchor]]
_TABLE_DELIMITER = re.compile(r"^[|!]===\s*$")
_SKIPPED_LINE = re.compile(r"^(?:image::?|toc::|//|ifdef::|endif::|ifndef::|include::|<<<|'''|-{4,}|\.{4,}|\+$)")
_NESTED_CELL = re.compile(r"!\s*")


@dataclass
class SpecSection:
    path: tuple[str, ...]  # headings from the document title down, e.g. (…, "Road Transport Networks", "RoadLink")
    line: int  # line of the heading in the file (1-based), for the citation link
    text: str


def _inline(text: str) -> str:
    """AsciiDoc inline markup reduced to text: footnotes, links, cross references, emphasis, admonition icons."""
    text = re.sub(r"footnote:\[([^\]]*)\]", r" (\1)", text)
    text = re.sub(r"(https?://[^\s\[]+)\[([^\]]*)\]", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"<<[^,>]+,([^>]+)>>", r"\1", text)
    text = re.sub(r"<<([^>]+)>>", r"\1", text)
    text = re.sub(r"\[\.\w+\]#([^#]*)#", r"\1", text)
    text = re.sub(r"(?<![\w*])\*\*?([^*]+?)\*\*?(?![\w*])", r"\1", text)
    text = re.sub(r"(?<![\w_])__?([^_]+?)__?(?![\w_])", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("{nbsp}", " ").replace("&#8203;", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def _table_line(line: str) -> str:
    """A table row as plain text: "!Definition: !A linear …" -> "Definition: A linear …"."""
    if line.startswith("!"):
        cells = [c.strip() for c in _NESTED_CELL.split(line[1:])]
        return ": ".join(c.rstrip(":") for c in cells if c) if len(cells) == 2 else " | ".join(c for c in cells if c)
    if line.startswith(("a|", "|")):
        cells = [c.strip() for c in line.lstrip("a").split("|")]
        return " | ".join(c for c in cells if c and c != "a")
    return line


def parse_spec(text: str) -> list[SpecSection]:
    """Split the specification into sections at its headings, as plain text."""
    sections: list[SpecSection] = []
    path: list[str] = []
    lines: list[str] = []
    start = 1

    def flush():
        body = "\n".join(lines).strip()
        if body:
            sections.append(SpecSection(tuple(path), start, re.sub(r"\n{3,}", "\n\n", body)))
        lines.clear()

    in_comment = False
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if line.startswith("////"):
            in_comment = not in_comment
            continue
        if in_comment:
            continue
        heading = _HEADING.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            path[:] = path[: level - 1] + [_inline(heading.group(2))]
            start = number
            continue
        stripped = line.strip()
        if (
            not stripped
            and lines
            and lines[-1] == ""
            or _ATTRIBUTE_LINE.match(stripped)
            or _BLOCK_ATTRIBUTE.match(stripped)
            or _TABLE_DELIMITER.match(stripped)
            or _SKIPPED_LINE.match(stripped)
            or stripped in ("a|", "|")
        ):
            continue
        if stripped.startswith(("NOTE:", "TIP:", "IMPORTANT:", "WARNING:", "CAUTION:")):
            kind, _, rest = stripped.partition(":")
            stripped = f"{kind.title()}: {rest.strip()}"
        lines.append(_inline(_table_line(stripped)) if stripped else "")
    flush()
    # The first heading is the document title and "Table of Contents" an empty list: neither is content.
    return [s for s in sections if len(s.path) > 1 or s.path[:1] != ("Table of Contents",)]


def _pieces(text: str) -> list[str]:
    """A section's text in pieces of at most MAX_CHUNK_CHARS, split between lines (or hard, inside one)."""
    pieces, current = [], ""
    for line in text.split("\n"):
        for part in [line[i : i + MAX_CHUNK_CHARS] for i in range(0, len(line), MAX_CHUNK_CHARS)] or [""]:
            if current and len(current) + len(part) + 1 > MAX_CHUNK_CHARS:
                pieces.append(current.strip())
                current = ""
            current = f"{current}\n{part}" if current else part
    if current.strip():
        pieces.append(current.strip())
    return pieces


def spec_chunks(sections: list[SpecSection]) -> list[tuple[str, str, int]]:
    """(heading path, text, line) per chunk: a chunk per section; short sections join the next one."""
    chunks: list[tuple[str, str, int]] = []
    carried: list[str] = []
    carried_line = None
    for section in sections:
        heading = " › ".join(section.path[1:]) or section.path[0]
        text = "\n".join(carried + [section.text]) if carried else section.text
        line = carried_line or section.line
        if len(text) < MIN_SECTION_CHARS:
            carried, carried_line = [f"{section.path[-1]}: {section.text}"], line
            continue
        carried, carried_line = [], None
        chunks.extend((heading, piece, line) for piece in _pieces(text))
    if carried:
        chunks.append((" › ".join(sections[-1].path[1:]), "\n".join(carried), carried_line))
    return chunks


def spec_records(spec_text: str) -> list[dict]:
    records = []
    for index, (heading, text, line) in enumerate(spec_chunks(parse_spec(spec_text))):
        secondary = heading.split(" › ", 1)[0].startswith(_SECONDARY_CHAPTERS)
        label = f"INSPIRE Transport Networks: {heading.rsplit(' › ', 1)[-1]}"
        records.append(
            {
                "chunk_id": f"inspire-tn-{index:04d}",
                "source_path": f"{SPEC_REPO_PATH}#L{line}",
                "label": label[:255],
                "heading": heading[:512],
                # The document's name leads the text, so the answer can name it and lexical search finds it.
                "text": f"{SPEC_TITLE}\n{heading}\n\n{text}",
                "quality_score": 0.5 if secondary else 0.85,
                "structured_metadata": {"sourceUrl": spec_url(line), "title": SPEC_TITLE, "tag": SPEC_TAG},
            }
        )
    return records


def codelist_records(codelists: list[dict]) -> list[dict]:
    """One chunk per code list (more if its values do not fit): definition, then each value with its definition."""
    records = []
    for codelist in codelists:
        name = codelist["name"]
        head = f"INSPIRE code list {name} ({codelist['label'] or name})"
        intro = "\n".join(t for t in (codelist["definition"], codelist["description"]) if t)
        values = []
        for value in codelist["values"]:
            code = value["id"].rsplit("/", 1)[-1]
            meaning = " ".join(t for t in (value["definition"], value["description"]) if t)
            values.append(f"- {code} ({value['label']}): {meaning}".rstrip(": "))
        body = intro + ("\n\nValues:\n" + "\n".join(values) if values else "")
        for part, piece in enumerate(_pieces(body)):
            records.append(
                {
                    "chunk_id": f"inspire-codelist-{name}-{part:02d}"[:128],
                    "source_path": f"codelist/{name}",
                    "label": f"INSPIRE code list: {name}"[:255],
                    "heading": head[:512],
                    "text": f"{head}\n\n{piece}",
                    "quality_score": 0.8,
                    "structured_metadata": {"sourceUrl": f"{REGISTRY_URL}{name}", "title": f"INSPIRE code list {name}"},
                }
            )
    return records


# ---- Indexing (also on deploy) ---------------------------------------------------------------------

EMBED_SLICE = 4
EMBED_PAUSE_SECONDS = 0.5


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a few texts at a time with pauses on prod's small embedder (see napcore_site._embed)."""
    from helpdesk.services.embeddings import semantic_enabled

    if not semantic_enabled():
        return build_text_embeddings_batch(texts)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_SLICE):
        vectors.extend(build_text_embeddings_batch(texts[start : start + EMBED_SLICE]))
        time.sleep(EMBED_PAUSE_SECONDS)
    return vectors


def _index_file(repository_url: str, path: Path, records: list[dict], commit: str) -> tuple[str, int]:
    content_hash = build_content_hash(f"parser {PARSER_VERSION}\n{path.read_text(encoding='utf-8')}")
    indexed = IndexedSourceFile.objects.filter(repository_url=repository_url, source_path=path.name).first()
    if indexed and indexed.content_hash == content_hash:
        return "unchanged", SourceChunk.objects.filter(repository_url=repository_url).count()
    embeddings = _embed(
        [
            build_chunk_embedding_text(
                chunk_text=record["text"],
                doc_type=DOC_TYPE,
                chunk_type="prose",
                heading=record["heading"],
                standards_scope=[SCOPE],
                repository_url=repository_url,
                source_path=record["source_path"],
            )
            for record in records
        ]
    )
    SourceChunk.objects.filter(repository_url=repository_url).delete()
    SourceChunk.objects.bulk_create(
        [
            SourceChunk(
                repository_url=repository_url,
                commit_sha=commit,
                standards_scope=[SCOPE],
                chunk_type="prose",
                doc_type=DOC_TYPE,
                embedding_vector=embedding,
                **record,
            )
            for record, embedding in zip(records, embeddings)
        ]
    )
    IndexedSourceFile.objects.update_or_create(
        repository_url=repository_url,
        source_path=path.name,
        defaults={"commit_sha": commit, "content_hash": content_hash},
    )
    return "indexed", len(records)


def read_codelists(path: Path = CODELISTS_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["codelists"]


def index_inspire(spec_path: Path = SPEC_PATH, codelists_path: Path = CODELISTS_PATH) -> dict[str, tuple[str, int]]:
    """Index the specification and the code lists whose files changed: {"spec": (status, chunks), …}."""
    spec_records_ = spec_records(spec_path.read_text(encoding="utf-8"))
    results = {"spec": _index_file(spec_url(), spec_path, spec_records_, SPEC_TAG)}
    results["codelists"] = _index_file(
        REGISTRY_URL, codelists_path, codelist_records(read_codelists(codelists_path)), "inspire-registry"
    )
    return results


@lru_cache(maxsize=1)
def _spec_headings() -> dict[str, str]:
    """Source path -> last heading of its section, for citation titles."""
    if not SPEC_PATH.exists():
        return {}
    return {
        f"{SPEC_REPO_PATH}#L{line}": heading.rsplit(" › ", 1)[-1]
        for heading, _, line in spec_chunks(parse_spec(SPEC_PATH.read_text(encoding="utf-8")))
    }


def citation_title(source_path: str) -> str:
    """A readable name for a cited INSPIRE passage ("INSPIRE Transport Networks: RoadLink"), else ""."""
    source_path = source_path or ""
    if source_path.startswith("codelist/"):
        return f"INSPIRE code list: {source_path.split('/', 1)[1]}"
    if source_path.startswith(f"{SPEC_REPO_PATH}#L"):
        heading = _spec_headings().get(source_path)
        return f"INSPIRE Transport Networks: {heading}" if heading else "INSPIRE Transport Networks"
    return ""
