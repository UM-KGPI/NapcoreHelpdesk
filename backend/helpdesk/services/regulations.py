"""
EU legislation as a retrieval source (issue #91): the acts that govern the data the standards exchange.

The texts come from the EU Publications Office (Cellar) as XHTML, are stored under docs/regulations/
and indexed from there, one chunk per article, recital group or annex section. A published act never
changes (a new consolidated version gets a new CELEX number), so the files are fetched once, reviewed
in git and indexed without network access. Citations link to the article on EUR-Lex.

For an amended act the consolidated text is the one to read, so it ranks above the amending act;
the amending acts stay indexed for questions about what changed.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-01  |  Modified: 2026-11-01
"""

from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.index_builder import build_chunk_embedding_text, build_content_hash

SCOPE = "EU legislation"
REGULATIONS_DIR = Path(__file__).resolve().parents[3] / "docs" / "regulations"
CELLAR_URL = "https://publications.europa.eu/resource/celex/{celex}"
EURLEX_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex}"
# EUR-Lex answers scripted requests with an empty 202; Cellar serves the same XHTML to programs.
_FETCH_HEADERS = {"Accept": "application/xhtml+xml", "Accept-Language": "eng"}
MAX_CHUNK_CHARS = 1500
# Part of the stored content hash: bump it when parsing or chunking changes, so the next run re-indexes.
PARSER_VERSION = "1"

_NS = "{http://www.w3.org/1999/xhtml}"
# Section headings inside an annex: Official Journal acts and consolidated texts mark them differently.
_HEADING_CLASSES = ("oj-ti-grseq-1", "title-gr-seq-level-")
_ARTICLE_TITLE_CLASSES = ("oj-ti-art", "title-article-norm")
_ARTICLE_SUBTITLE_CLASSES = ("oj-sti-art", "stitle-article-norm")
_LIST_LABEL = re.compile(r"^(\(?[0-9ivxlcdm]{1,6}[.)]|\([a-z]{1,3}\)|[a-z]\)|—|–|-|•)$", re.I)


@dataclass(frozen=True)
class Act:
    celex: str
    name: str  # how answers name the act
    kind: str  # "consolidated", "act" or "amending"
    quality: float

    @property
    def url(self) -> str:
        return EURLEX_URL.format(celex=self.celex)

    @property
    def path(self) -> Path:
        return REGULATIONS_DIR / f"{self.celex}.xhtml"


# Pinned list: add an act (or a newer consolidated version) here, fetch it, review the file in git.
ACTS: tuple[Act, ...] = (
    Act(
        "02017R1926-20240304",
        "Delegated Regulation (EU) 2017/1926 (MMTIS), consolidated text of 4 March 2024",
        "consolidated",
        0.9,
    ),
    Act(
        "02010L0040-20231220",
        "Directive 2010/40/EU (ITS Directive), consolidated text of 20 December 2023",
        "consolidated",
        0.9,
    ),
    Act("32026R0253", "Implementing Regulation (EU) 2026/253 (TEL TSI)", "act", 0.9),
    Act(
        "32024R0490",
        "Delegated Regulation (EU) 2024/490 amending Delegated Regulation (EU) 2017/1926 (MMTIS)",
        "amending",
        0.6,
    ),
    Act("32023L2661", "Directive (EU) 2023/2661 amending Directive 2010/40/EU (ITS Directive)", "amending", 0.6),
)


@dataclass
class Section:
    anchor: str  # element id on EUR-Lex, e.g. "art_4"
    heading: str  # e.g. "Article 4 — Accessibility, exchange and re-use of static travel and traffic data"
    text: str


def fetch_act(act: Act) -> None:
    """Download the act's XHTML from Cellar into docs/regulations/."""
    request = urllib.request.Request(CELLAR_URL.format(celex=act.celex), headers=_FETCH_HEADERS)
    with urllib.request.urlopen(request, timeout=120) as response:  # nosec B310 - fixed https host
        content = response.read()
    ET.fromstring(content)  # refuse to store anything that is not well-formed XHTML
    act.path.write_bytes(content)


_BLOCK_TAGS = {"p", "div", "table", "tbody", "thead", "tr", "ul", "ol", "li", "h1", "h2", "h3", "h4", "hr"}
# EUR-Lex consolidation markers (▼B, ▼M1, ►M2 … ◄) say which act a passage comes from; not text.
_CONSOLIDATION_MARKER = re.compile(r"[▼►]\s?[A-Z]\d*|◄")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", _CONSOLIDATION_MARKER.sub(" ", text)).strip()


def _text(element: ET.Element) -> str:
    return _clean("".join(element.itertext()))


def _has_class(element: ET.Element, prefixes: tuple[str, ...]) -> bool:
    classes = (element.get("class") or "").split()
    return any(c.startswith(prefix) for c in classes for prefix in prefixes)


def _blocks(element: ET.Element) -> list[tuple[str, bool]]:
    """Text of each block element in document order, as (text, is_heading).

    Consolidated texts put paragraph text directly in div elements as well as in p, so a block is
    any element from _BLOCK_TAGS: the text up to its next block child is one paragraph. Table cells
    of a row are joined with " | ".
    """
    blocks: list[tuple[str, bool]] = []
    buffer: list[str] = []
    heading_flag = [False]

    def flush():
        text = _clean("".join(buffer))
        if text:
            blocks.append((text, heading_flag[0]))
        buffer.clear()
        heading_flag[0] = False

    def walk(node: ET.Element, in_row: bool = False):
        tag = node.tag.replace(_NS, "")
        # Inside a table row only the row itself is a block, so a row stays one line.
        is_block = tag == "tr" or (tag in _BLOCK_TAGS and not in_row)
        if is_block:
            flush()
            heading_flag[0] = _has_class(node, _HEADING_CLASSES)
        if tag in ("td", "th") and "".join(buffer).strip():
            buffer.append(" | ")
        elif in_row and tag == "p" and "".join(buffer).strip():
            buffer.append(" ")
        if node.text:
            buffer.append(node.text)
        for child in node:
            walk(child, in_row or tag == "tr")
            if child.tail:
                buffer.append(child.tail)
        if is_block:
            flush()

    walk(element)
    return blocks


def _sentences(text: str) -> list[str]:
    """A paragraph longer than MAX_CHUNK_CHARS split at sentence ends (or hard, if it has none)."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    parts, current = [], ""
    for sentence in re.split(r"(?<=[.;:])\s+", text):
        if current and len(current) + len(sentence) + 1 > MAX_CHUNK_CHARS:
            parts.append(current)
            current = ""
        current = f"{current} {sentence}".strip()
    parts.append(current)
    return [piece[i : i + MAX_CHUNK_CHARS] for piece in parts for i in range(0, len(piece), MAX_CHUNK_CHARS)]


def _paragraphs(element: ET.Element):
    """Blocks with list labels such as "(1)" or "(a)" joined to the text that follows them."""
    label = ""
    for text, is_heading in _blocks(element):
        if _LIST_LABEL.match(text):
            label = f"{label} {text}".strip()
            continue
        text = f"{label} {text}" if label else text
        label = ""
        for piece in _sentences(text):
            yield piece, is_heading


def _pack(anchor: str, heading: str, paragraphs, *, split_on_headings: bool) -> list[Section]:
    """Group paragraphs into sections of at most MAX_CHUNK_CHARS, starting a new one at each heading."""
    sections: list[Section] = []
    current: list[str] = []
    subheading = ""

    def flush():
        if current:
            title = f"{heading} — {subheading}" if subheading else heading
            sections.append(Section(anchor=anchor, heading=title, text="\n".join(current)))
            current.clear()

    for text, is_heading in paragraphs:
        if split_on_headings and is_heading:
            flush()
            subheading = text
        elif current and sum(len(p) for p in current) + len(text) > MAX_CHUNK_CHARS:
            flush()
        current.append(text)
    flush()
    return sections


def parse_act(xhtml: bytes) -> list[Section]:
    """Split an act into articles, recital groups, and annex and appendix sections."""
    root = ET.fromstring(xhtml)
    sections: list[Section] = []
    recitals: list[tuple[str, str]] = []
    for div in root.iter(f"{_NS}div"):
        anchor = div.get("id") or ""
        if "." in anchor:
            continue
        if anchor.startswith("rct_"):
            recitals.extend((anchor, piece) for piece in _sentences(_text(div)))
        elif anchor.startswith("art_"):
            titles = [_text(p) for p in div.iter(f"{_NS}p") if _has_class(p, _ARTICLE_TITLE_CLASSES)]
            subtitles = [_text(p) for p in div.iter(f"{_NS}p") if _has_class(p, _ARTICLE_SUBTITLE_CLASSES)]
            heading = " — ".join(t for t in (titles[:1] + subtitles[:1]) if t) or anchor
            body = [(text, False) for text, _ in _paragraphs(div) if text not in titles[:1] + subtitles[:1]]
            sections.extend(_pack(anchor, heading, body, split_on_headings=False))
        elif anchor.startswith("anx_"):
            sections.extend(_pack(anchor, "Annex", _paragraphs(div), split_on_headings=True))
        elif anchor.startswith("app_"):
            # Appendices of an annex (TEL TSI Appendix C lists the referenced standards)
            heading = f"Appendix {anchor.split('_', 1)[1]}"
            sections.extend(_pack(anchor, heading, _paragraphs(div), split_on_headings=True))
    # Recitals explain why a provision exists; grouped so each chunk has enough context.
    group: list[tuple[str, str]] = []
    for recital in recitals:
        if group and sum(len(t) for _, t in group) + len(recital[1]) > MAX_CHUNK_CHARS:
            sections.append(Section(group[0][0], "Recitals", "\n".join(t for _, t in group)))
            group = []
        group.append(recital)
    if group:
        sections.append(Section(group[0][0], "Recitals", "\n".join(t for _, t in group)))
    return sections


def _chunk_records(act: Act, sections: list[Section]) -> list[dict]:
    records = []
    for index, section in enumerate(sections):
        # The act name leads the text so the answer can name the act, and lexical search finds it.
        text = f"{act.name}\n{section.heading}\n\n{section.text}"
        records.append(
            {
                "chunk_id": f"reg-{act.celex}-{index:04d}",
                "source_path": f"{act.celex}#{section.anchor}",
                "label": f"{act.name}, {section.heading}"[:255],
                "heading": section.heading[:512],
                "text": text,
                "quality_score": act.quality if section.heading != "Recitals" else min(act.quality, 0.5),
                "structured_metadata": {
                    "sourceUrl": f"{act.url}#{section.anchor}",
                    "celex": act.celex,
                    "actKind": act.kind,
                },
            }
        )
    return records


def index_act(act: Act) -> tuple[str, int]:
    """Index one act from its file: ("unchanged" | "indexed", number of chunks)."""
    content = act.path.read_bytes()
    content_hash = build_content_hash(f"parser {PARSER_VERSION}\n{content.decode('utf-8')}")
    indexed = IndexedSourceFile.objects.filter(repository_url=act.url, source_path=act.path.name).first()
    if indexed and indexed.content_hash == content_hash:
        return "unchanged", SourceChunk.objects.filter(repository_url=act.url).count()

    records = _chunk_records(act, parse_act(content))
    embeddings = build_text_embeddings_batch(
        [
            build_chunk_embedding_text(
                chunk_text=record["text"],
                doc_type="regulation",
                chunk_type="prose",
                heading=record["heading"],
                standards_scope=[SCOPE],
                repository_url=act.url,
                source_path=record["source_path"],
            )
            for record in records
        ]
    )
    SourceChunk.objects.filter(repository_url=act.url).delete()
    SourceChunk.objects.bulk_create(
        [
            SourceChunk(
                repository_url=act.url,
                commit_sha=act.celex,
                standards_scope=[SCOPE],
                chunk_type="prose",
                doc_type="regulation",
                embedding_vector=embedding,
                **record,
            )
            for record, embedding in zip(records, embeddings)
        ]
    )
    IndexedSourceFile.objects.update_or_create(
        repository_url=act.url,
        source_path=act.path.name,
        defaults={"commit_sha": act.celex, "content_hash": content_hash},
    )
    return "indexed", len(records)


def is_regulation_url(url: str) -> bool:
    """True for an EUR-Lex link to one of the indexed acts (citation allow-list)."""
    base = url.split("#", 1)[0]
    return any(base == act.url for act in ACTS)
