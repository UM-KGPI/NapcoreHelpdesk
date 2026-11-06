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
Created: 2026-11-01  |  Modified: 2026-11-05
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
    # Only these parts of the act's annexes and appendices are indexed: (anchor, section number) pairs,
    # e.g. ("anx_II", "7.") keeps section 7 of Annex II. None indexes every part. Articles and recitals
    # are always indexed. For acts that cover far more than mobility data (the INSPIRE rules have 34
    # spatial data themes; only Transport Networks concerns these standards).
    annex_sections: tuple[tuple[str, str], ...] | None = None

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
    # MMTIS Art. 4(1)(c): "for the spatial network the requirements set out in Article 7 of Directive
    # 2007/2/EC". Article 7 is implemented by Regulation 1089/2010, whose Annex II section 7 is the
    # Transport Networks theme. Ranked below the mobility acts: they support MMTIS, not replace it.
    Act(
        "02007L0002-20241126",
        "Directive 2007/2/EC (INSPIRE), consolidated text of 26 November 2024",
        "consolidated",
        0.8,
    ),
    Act(
        "02010R1089-20231119",
        "Regulation (EU) No 1089/2010 (INSPIRE spatial data interoperability), consolidated text of 19 November 2023",
        "consolidated",
        0.8,
        annex_sections=(("anx_II", "7."),),
    ),
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


def select_sections(act: Act, sections: list[Section]) -> list[Section]:
    """The sections of an act that are indexed: all of them, or only act.annex_sections of its annexes."""
    if act.annex_sections is None:
        return sections

    def kept(section: Section) -> bool:
        if not section.anchor.startswith(("anx_", "app_")):
            return True
        # "Annex — 7.2. Structure of …": the section number follows the first " — ".
        number = section.heading.partition(" — ")[2]
        return any(section.anchor == anchor and number.startswith(prefix) for anchor, prefix in act.annex_sections)

    return [section for section in sections if kept(section)]


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

    records = _chunk_records(act, select_sections(act, parse_act(content)))
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


def citation_title(source_path: str) -> str:
    """A readable name for a cited part of an indexed act ("MMTIS Art. 4"), or "" for other sources."""
    celex, _, anchor = (source_path or "").partition("#")
    act = next((a for a in ACTS if a.celex == celex), None)
    return provision_label(act, anchor) if act and anchor else ""


def is_regulation_url(url: str) -> bool:
    """True for an EUR-Lex link to one of the indexed acts (citation allow-list)."""
    base = url.split("#", 1)[0]
    return any(base == act.url for act in ACTS)


# ---- Vocabulary of the defined terms (issue #91, phase 2) -----------------------------------------
# Each act's definitions article ("'data holder' means …") becomes a SKOS concept in
# docs/regulations/eu-legislation-definitions.ttl, generated from the stored texts and never edited by
# hand. A question that uses a defined term gets the EU legislation scope even when it names no act.
# Terms that are also a label in the standards ontologies (e.g. a Transmodel concept) are marked
# shared and do not set the scope on their own: there the question may well be about the standard.

VOCABULARY_PATH = REGULATIONS_DIR / "eu-legislation-definitions.ttl"
VOCABULARY_NAMESPACE = "https://napcore.eu/ontology/eu-legislation#"
STANDARD_ONTOLOGIES_DIR = REGULATIONS_DIR.parent / "ontology" / "standards"
# The definitive texts: the amending acts' definitions are already in the consolidated texts.
_VOCABULARY_ACTS = {"02017R1926-20240304": "MMTIS", "02010L0040-20231220": "ITSD", "32026R0253": "TELTSI"}
_DEFINITION = re.compile(r"^(?:\(\w+\)\s*\|?\s*)?((?:‘[^’]+’(?:\s*,\s*|\s+or\s+)?)+)\s+means\s+(.+)$")
_QUOTED_TERM = re.compile(r"‘([^’]+)’")
_LABEL_IN_TTL = re.compile(r'(?:rdfs:label|skos:prefLabel|skos:altLabel)\s+"([^"]+)"')
_VOCABULARY_LABEL_LINE = re.compile(r'^skos:(?:prefLabel|altLabel) "([^"]+)"@en ;(?: # shared)?$')


@dataclass
class Definition:
    act: Act
    code: str  # MMTIS, ITSD or TELTSI
    anchor: str
    labels: list[str]  # the term first, then its other names (e.g. "Intelligent Transport Systems", "ITS")
    text: str


def _normalise_label(label: str) -> str:
    return re.sub(r"[\s_]+", " ", label).strip().lower()


def extract_definitions(act: Act, code: str) -> list[Definition]:
    """The defined terms of an act, from its definitions article (the article whose lines read "'x' means")."""
    sections = parse_act(act.path.read_bytes())
    definitions: list[Definition] = []
    for section in sections:
        for line in section.text.split("\n"):
            match = _DEFINITION.match(line.strip())
            if match:
                labels = _QUOTED_TERM.findall(match.group(1))
                definitions.append(Definition(act, code, section.anchor, labels, f"means {match.group(2)}"))
            elif definitions and definitions[-1].anchor == section.anchor and definitions[-1].text.endswith(":"):
                # A definition that ends in a list ("… the following:") continues on the next lines.
                definitions[-1].text += f" {line.strip()}"
    return definitions


def standards_labels() -> set[str]:
    labels: set[str] = set()
    for path in sorted(STANDARD_ONTOLOGIES_DIR.glob("*.ttl")):
        labels.update(_normalise_label(label) for label in _LABEL_IN_TTL.findall(path.read_text(encoding="utf-8")))
    return labels


def _slug(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")


def _literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render_vocabulary(definitions: list[Definition], shared_labels: set[str]) -> str:
    lines = [
        "# EU legislation: defined terms (generated by build_legislation_vocabulary; do not edit)",
        "# Source: the definitions articles of " + ", ".join(sorted({d.act.celex for d in definitions})),
        "# '# shared' marks a label that is also a label in docs/ontology/standards/.",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix dct: <http://purl.org/dc/terms/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        f"@prefix eulex: <{VOCABULARY_NAMESPACE}> .",
        "",
    ]
    for definition in definitions:
        concept = f"{definition.code}-{_slug(definition.labels[0])}"
        lines.append(f"eulex:{concept} a skos:Concept ;")
        for index, label in enumerate(definition.labels):
            kind = "prefLabel" if index == 0 else "altLabel"
            shared = " # shared" if _normalise_label(label) in shared_labels else ""
            lines.append(f'    skos:{kind} "{_literal(label)}"@en ;{shared}')
        lines.append(f'    skos:definition "{_literal(definition.text)}"@en ;')
        lines.append(f"    dct:source <{definition.act.url}#{definition.anchor}> ;")
        lines.append(f'    skos:inScheme eulex:{definition.code} .')
        lines.append("")
    return "\n".join(lines)


# How the acts name the standards: by name or by CEN number. An act may give only the number and the
# formal title (TEL TSI: "EN 12896-1:2016 Public transport – Reference data model"), so both count.
STANDARD_NAMES = {
    "NeTEx": r"\bNeTEx\b",
    "SIRI": r"\bSIRI\b",
    "Transmodel": r"\bTransmodel\b",
    "OpRa": r"\bOpRa\b",
    "DATEX II": r"\bDATEX II\b",
}
# SIRI is published as both EN 15531 and CEN/TS 15531 parts.
STANDARD_NUMBERS = {
    "NeTEx": r"CEN/TS 16614",
    "SIRI": r"(?:CEN/TS|EN) 15531",
    "Transmodel": r"EN 12896",
    "DATEX II": r"(?:CEN/TS|EN) 16157",
}
STANDARD_IDENTIFIERS = {
    standard: "|".join(p for p in (name, STANDARD_NUMBERS.get(standard)) if p) for standard, name in STANDARD_NAMES.items()
}
_PROVISION_LINE = re.compile(
    r'^eulex:\S+ a eulex:Provision ; rdfs:label "([^"]+)"@en ; dct:source <([^#>]+CELEX:([^#>]+))#([^>]+)> ; '
    r"eulex:namesStandard (.+) \.$"
)


def extract_provisions() -> list[tuple[Act, str, list[str]]]:
    """Provisions of the definitive acts that name a standard: (act, anchor, standards), in act order."""
    provisions: list[tuple[Act, str, list[str]]] = []
    for act in ACTS:
        if act.celex not in _VOCABULARY_ACTS:
            continue
        named: dict[str, set[str]] = {}
        for section in parse_act(act.path.read_bytes()):
            for standard, pattern in STANDARD_IDENTIFIERS.items():
                if re.search(pattern, section.text):
                    named.setdefault(section.anchor, set()).add(standard)
        provisions.extend((act, anchor, sorted(standards)) for anchor, standards in named.items())
    return provisions


_ANCHOR_KINDS = {"art": "Art.", "app": "App.", "anx": "Annex", "rct": "Recital"}


def provision_label(act: Act, anchor: str) -> str:
    """A short name for a provision: the act's short name (in parentheses in its name) and the point,
    e.g. "MMTIS Art. 4", "TEL TSI App. C"."""
    if act.kind == "amending":
        # An amending act is named by its number: its recitals are not those of the act it amends.
        short = act.name.split(" amending ", 1)[0]
    else:
        names = [g for g in re.findall(r"\(([^()]*[A-Za-z][^()]*)\)", act.name) if g != "EU"]
        short = names[0] if names else act.celex
    kind, _, number = anchor.partition("_")
    point = _ANCHOR_KINDS.get(kind, kind)
    return f"{short} {point} {number}".strip() if not (kind == "anx" and number == "1") else f"{short} {point}"


def render_provisions(provisions: list[tuple[Act, str, list[str]]]) -> str:
    lines = [
        "",
        "# Provisions that name a standard (eulex:namesStandard), generated from the same acts.",
    ]
    for act, anchor, standards in provisions:
        names = " , ".join(f'"{s}"' for s in standards)
        lines.append(
            f'eulex:{_VOCABULARY_ACTS[act.celex]}-{anchor} a eulex:Provision ; rdfs:label "{provision_label(act, anchor)}"@en ; '
            f"dct:source <{act.url}#{anchor}> ; eulex:namesStandard {names} ."
        )
    return "\n".join(lines) + "\n"


def build_vocabulary() -> tuple[str, int, int]:
    """The vocabulary TTL, with the number of concepts and of shared labels."""
    shared_labels = standards_labels()
    definitions = [d for act in ACTS if act.celex in _VOCABULARY_ACTS for d in extract_definitions(act, _VOCABULARY_ACTS[act.celex])]
    text = render_vocabulary(definitions, shared_labels) + render_provisions(extract_provisions())
    return text, len(definitions), text.count("# shared\n")


def provisions_naming(standard: str, path: Path = VOCABULARY_PATH) -> list[str]:
    """Source paths ("<CELEX>#<anchor>") of the provisions that name a standard, in act order."""
    if not path.exists():
        return []
    return [f"{p['celex']}#{p['anchor']}" for p in _provisions(path) if standard in p["standards"]]


def _provisions(path: Path = VOCABULARY_PATH) -> list[dict]:
    if not path.exists():
        return []
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _PROVISION_LINE.match(line.strip())
        if match:
            label, url, celex, anchor, names = match.groups()
            found.append(
                {"label": label, "url": f"{url}#{anchor}", "celex": celex, "anchor": anchor,
                 "standards": re.findall(r'"([^"]+)"', names)}
            )
    return found


def legal_context(standards: list[str], path: Path = VOCABULARY_PATH) -> list[dict]:
    """The provisions that name any of the standards, as {"label", "url"} for a "Legal context" line."""
    return [
        {"label": p["label"], "url": p["url"]}
        for p in _provisions(path)
        if any(standard in p["standards"] for standard in standards)
    ]


def vocabulary_terms(path: Path = VOCABULARY_PATH) -> list[str]:
    """Labels that set the EU legislation scope: not shared with the standards, and either several
    words ("data holder") or an acronym ("ITS", matched case-sensitively by the caller)."""
    if not path.exists():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _VOCABULARY_LABEL_LINE.match(line.strip())
        if match and not line.rstrip().endswith("# shared"):
            label = match.group(1).replace('\\"', '"')
            if " " in label.strip() or (label.isupper() and len(label) >= 2):
                terms.append(label)
    return terms
