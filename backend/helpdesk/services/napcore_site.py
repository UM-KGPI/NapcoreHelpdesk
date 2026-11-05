"""
napcore.eu as a retrieval source: NAPCORE's own pages, news and published deliverables.

Built like the EU legislation source (services/regulations.py). A pinned list of URLs
(docs/napcore/sources.txt) is fetched once on a development machine: pages and posts through the
WordPress REST API, which returns the page content without the theme, and PDFs converted to text with
pypdf. The text snapshots go to docs/napcore/text/, are reviewed in git, and are indexed from there,
also on deploy, without network access. A refresh is the same fetch followed by a review of the diff.

The chunks belong to the opt-in scope "NAPCORE": they are searched only when a question is about
NAPCORE, NAPs, National Bodies or compliance assessment, so they never crowd out standards evidence.
Citations link to the page, or to the PDF page the passage starts on.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-05  |  Modified: 2026-11-05
"""

from __future__ import annotations

import hashlib
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services.embeddings import build_text_embeddings_batch
from helpdesk.services.index_builder import build_chunk_embedding_text, build_content_hash

SCOPE = "NAPCORE"
DOC_TYPE = "napcore"
SITE_URL = "https://napcore.eu"
NAPCORE_DIR = Path(__file__).resolve().parents[3] / "docs" / "napcore"
MANIFEST_PATH = NAPCORE_DIR / "sources.txt"
TEXT_DIR = NAPCORE_DIR / "text"
MAX_CHUNK_CHARS = 1500
# A heading starts a new chunk only after this much text (see chunk_snapshot).
MIN_SECTION_CHARS = 400
# Part of the stored content hash: bump it when parsing or chunking changes, so the next run re-indexes.
PARSER_VERSION = "2"
_USER_AGENT = "NAPCORE-Helpdesk-indexer/1.0 (+https://kgpi.fgpa.um.si/napcore-helpdesk/)"
_HOSTS = ("napcore.eu", "www.napcore.eu")
_PAGE_MARKER = re.compile(r"^\[page (\d+)\]$")


@dataclass(frozen=True)
class Document:
    url: str
    title: str = ""  # from the manifest; else the page title or the PDF file name

    @property
    def is_pdf(self) -> bool:
        return urllib.parse.urlparse(self.url).path.lower().endswith(".pdf")

    @property
    def name(self) -> str:
        """File name of the text snapshot, derived from the URL path ("metadata", "D5.1.1_Final_NAP_...")."""
        path = urllib.parse.unquote(urllib.parse.urlparse(self.url).path).strip("/")
        stem = path.rsplit("/", 1)[-1] if self.is_pdf else path.replace("/", "--")
        stem = re.sub(r"\.pdf$", "", stem, flags=re.IGNORECASE) or "home"
        return re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_")

    @property
    def path(self) -> Path:
        # ".pdf.md" keeps a PDF apart from a post with the same slug (names differing only in case collide on
        # case-insensitive file systems).
        return TEXT_DIR / f"{self.name}{'.pdf' if self.is_pdf else ''}.md"


def is_napcore_url(url: str) -> bool:
    """True for a link to napcore.eu (citation allow-list: the site is approved as a whole)."""
    return urllib.parse.urlparse(url or "").netloc.lower() in _HOSTS


def read_manifest(path: Path = MANIFEST_PATH) -> list[Document]:
    documents = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        url, _, title = (part.strip() for part in line.partition("|"))
        documents.append(Document(url=url, title=title))
    return documents


# ---- Fetching (development machine) ----------------------------------------------------------------


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:  # nosec B310 - pinned napcore.eu URLs
        return response.read()


class _TextExtractor(HTMLParser):
    """WordPress post content as plain text: headings as Markdown, list items, table rows joined by " | "."""

    _BLOCKS = {"p", "div", "section", "article", "ul", "ol", "table", "tbody", "thead", "figure", "blockquote"}
    _SKIP = {"script", "style", "noscript", "svg", "iframe"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.buffer: list[str] = []
        self.prefix = ""
        self.skip_depth = 0
        self.cells: list[str] | None = None

    def _flush(self):
        text = " ".join("".join(self.buffer).split())
        if text:
            self.lines.append(f"{self.prefix}{text}")
        self.buffer, self.prefix = [], ""

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self.skip_depth += 1
        elif tag in self._BLOCKS or tag == "br":
            self._flush()
        elif re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self.prefix = "#" * min(int(tag[1]) + 1, 4) + " "
        elif tag == "li":
            self._flush()
            self.prefix = "- "
        elif tag == "tr":
            self._flush()
            self.cells = []
        elif tag in ("td", "th") and self.cells is not None:
            self.buffer = []

    def handle_endtag(self, tag):
        if tag in self._SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in ("td", "th") and self.cells is not None:
            self.cells.append(" ".join("".join(self.buffer).split()))
            self.buffer = []
        elif tag == "tr" and self.cells is not None:
            row = " | ".join(cell for cell in self.cells if cell)
            if row:
                self.lines.append(row)
            self.cells = None
        elif tag in self._BLOCKS or tag == "li" or re.fullmatch(r"h[1-6]", tag):
            self._flush()

    def handle_data(self, data):
        if not self.skip_depth:
            self.buffer.append(data)

    def text(self) -> str:
        self._flush()
        return "\n".join(self.lines)


def html_to_text(content: str) -> str:
    parser = _TextExtractor()
    parser.feed(content)
    return parser.text()


def _wordpress_item(url: str) -> dict:
    """The page or post at the URL, from the REST API (pages first: both share the slug namespace)."""
    slug = urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    for kind in ("pages", "posts"):
        query = urllib.parse.urlencode({"slug": slug, "_fields": "link,modified,title,content"} if slug else
                                       {"_fields": "link,modified,title,content", "per_page": 100})
        items = json.loads(_get(f"{SITE_URL}/wp-json/wp/v2/{kind}?{query}"))
        if not slug:  # the front page: the page whose link is the site root
            items = [item for item in items if item["link"].rstrip("/") == SITE_URL]
        for item in items:
            if item["link"].rstrip("/") == url.rstrip("/"):
                return item
    raise ValueError(f"No napcore.eu page or post at {url}")


def pdf_to_text(content: bytes) -> str:
    """The text of each page after a "[page N]" line; pages without text (scans, images) are left out."""
    from pypdf import PdfReader

    pages = []
    for number, page in enumerate(PdfReader(io.BytesIO(content)).pages, start=1):
        text = "\n".join(" ".join(line.split()) for line in (page.extract_text() or "").splitlines())
        text = re.sub(r"\n{2,}", "\n", text).strip()
        if text:
            pages.append(f"[page {number}]\n{text}")
    return dehyphenate("\n".join(pages))


def dehyphenate(text: str) -> str:
    """Join words a PDF hyphenated at a line end ("informa-" / "tion"): search and quotes need whole words."""
    return re.sub(r"(?<=[a-z])- ?\n(?=[a-z])", "", text)


def _pdf_title(document: Document, content: bytes) -> str:
    from pypdf import PdfReader

    title = ""
    try:
        title = str((PdfReader(io.BytesIO(content)).metadata or {}).get("/Title") or "").strip()
    except Exception:  # broken metadata: fall back to the file name
        title = ""
    # Office exports often leave "PowerPoint Presentation" or the template name as the title.
    if not title or len(title) < 8 or re.search(r"presentation|untitled|^microsoft|template", title, re.IGNORECASE):
        title = re.sub(r"[_-]+", " ", document.name).strip()
    return title


def fetch_document(document: Document) -> str:
    """Download the document and return its snapshot: a small header, a blank line, then the text."""
    if document.is_pdf:
        content = _get(document.url)
        title, modified, text = document.title or _pdf_title(document, content), "", pdf_to_text(content)
    else:
        item = _wordpress_item(document.url)
        title = document.title or html.unescape(re.sub(r"<[^>]+>", "", item["title"]["rendered"])).strip()
        modified, text = item["modified"], html_to_text(item["content"]["rendered"])
    header = [f"url: {document.url}", f"title: {title}"] + ([f"modified: {modified}"] if modified else [])
    return "\n".join(header) + "\n\n" + text.strip() + "\n"


def fetch_all(documents: list[Document]) -> list[tuple[Document, str]]:
    """Fetch every document into docs/napcore/text/; returns (document, "written" | "unchanged" | error)."""
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for document in documents:
        try:
            snapshot = fetch_document(document)
        except Exception as exc:  # one failing URL must not stop the others; the caller reports it
            results.append((document, f"failed: {exc}"))
            continue
        if document.path.exists() and document.path.read_text(encoding="utf-8") == snapshot:
            results.append((document, "unchanged"))
            continue
        document.path.write_text(snapshot, encoding="utf-8")
        results.append((document, "written"))
    return results


# ---- Indexing (also on deploy) ---------------------------------------------------------------------


@dataclass
class Snapshot:
    url: str
    title: str
    text: str


def read_snapshot(path: Path) -> Snapshot:
    header, _, text = path.read_text(encoding="utf-8").partition("\n\n")
    fields = dict(line.split(": ", 1) for line in header.splitlines() if ": " in line)
    return Snapshot(url=fields["url"], title=fields.get("title", path.stem), text=text)


def chunk_snapshot(snapshot: Snapshot) -> list[tuple[str, str, int | None]]:
    """(heading, text, first PDF page) per chunk: a new chunk at each heading, at most MAX_CHUNK_CHARS."""
    chunks: list[tuple[str, str, int | None]] = []
    current: list[str] = []
    heading, page, start_page = "", None, None

    def flush():
        nonlocal start_page
        if current:
            chunks.append((heading, "\n".join(current), start_page))
            current.clear()
        start_page = page

    for line in snapshot.text.splitlines():
        marker = _PAGE_MARKER.match(line.strip())
        if marker:
            page = int(marker.group(1))
            if not current:
                start_page = page
            continue
        if line.startswith("#"):
            # The site's theme puts whole sentences in heading tags, so a heading's text stays in the chunk; it
            # starts a new chunk only when the current one already has some substance.
            if sum(len(p) + 1 for p in current) >= MIN_SECTION_CHARS:
                flush()
            heading = line.lstrip("#").strip()[:200]
            line = line.lstrip("#").strip()
        for piece in [line[i : i + MAX_CHUNK_CHARS] for i in range(0, len(line), MAX_CHUNK_CHARS)] or [""]:
            if current and sum(len(p) + 1 for p in current) + len(piece) > MAX_CHUNK_CHARS:
                flush()
            if piece.strip():
                current.append(piece)
    flush()
    return chunks


def _source_path(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return "napcore.eu" + (urllib.parse.unquote(parsed.path).rstrip("/") or "/")


def chunk_records(snapshot: Snapshot) -> list[dict]:
    source_path = _source_path(snapshot.url)
    is_pdf = urllib.parse.urlparse(snapshot.url).path.lower().endswith(".pdf")
    # Readable prefix plus a hash of the whole path: long PDF names share their first 80 characters.
    readable = re.sub(r"[^a-z0-9]+", "-", source_path.lower().removeprefix("napcore.eu")).strip("-")[:60]
    key = f"{readable}-{hashlib.sha1(source_path.encode('utf-8')).hexdigest()[:8]}"
    records = []
    for index, (heading, text, page) in enumerate(chunk_snapshot(snapshot)):
        url = f"{snapshot.url}#page={page}" if page else snapshot.url
        label = f"NAPCORE: {snapshot.title}" + (f" — {heading}" if heading else "")
        records.append(
            {
                "chunk_id": f"napcore-{key}-{index:04d}",
                "source_path": source_path,
                "label": label[:255],
                "heading": (heading or snapshot.title)[:512],
                # The document's name leads the text, so the answer can name it and lexical search finds it.
                "text": f"NAPCORE (napcore.eu): {snapshot.title}\n{heading}\n\n{text}".replace("\n\n\n", "\n\n"),
                # The site's pages summarise; a long report's passage is narrower evidence for a general question.
                "quality_score": 0.75 if is_pdf else 0.85,
                "structured_metadata": {"sourceUrl": url, "title": snapshot.title},
            }
        )
    return records


# The first index embeds about 3,000 chunks. On prod the embedding service has 2 CPUs and embeds long chunks
# at about 0.5 per second, and every live question needs it for its query vector, so the index embeds a few
# texts at a time and pauses between them: a question waits seconds, not the half minute a batch of 16 takes.
EMBED_SLICE = 4
EMBED_PAUSE_SECONDS = 0.5


def _embed(texts: list[str]) -> list[list[float]]:
    from helpdesk.services.embeddings import semantic_enabled

    if not semantic_enabled():
        return build_text_embeddings_batch(texts)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_SLICE):
        vectors.extend(build_text_embeddings_batch(texts[start : start + EMBED_SLICE]))
        time.sleep(EMBED_PAUSE_SECONDS)
    return vectors


def index_site(text_dir: Path = TEXT_DIR, report=None) -> dict[str, int]:
    """Index every snapshot whose text changed; remove the chunks of documents no longer present.

    report(line) is called after each document that was (re)indexed, for progress output."""
    counts = {"indexed": 0, "unchanged": 0, "removed": 0, "chunks": 0}
    present_urls = set()
    for path in sorted(text_dir.glob("*.md")):
        snapshot = read_snapshot(path)
        present_urls.add(snapshot.url)
        content_hash = build_content_hash(f"parser {PARSER_VERSION}\n{path.read_text(encoding='utf-8')}")
        indexed = IndexedSourceFile.objects.filter(repository_url=snapshot.url, source_path=path.name).first()
        if indexed and indexed.content_hash == content_hash:
            counts["unchanged"] += 1
            counts["chunks"] += SourceChunk.objects.filter(repository_url=snapshot.url).count()
            continue
        records = chunk_records(snapshot)
        embeddings = _embed(
            [
                build_chunk_embedding_text(
                    chunk_text=record["text"],
                    doc_type=DOC_TYPE,
                    chunk_type="prose",
                    heading=record["heading"],
                    standards_scope=[SCOPE],
                    repository_url=snapshot.url,
                    source_path=record["source_path"],
                )
                for record in records
            ]
        )
        SourceChunk.objects.filter(repository_url=snapshot.url).delete()
        SourceChunk.objects.bulk_create(
            [
                SourceChunk(
                    repository_url=snapshot.url,
                    commit_sha="napcore.eu",
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
            repository_url=snapshot.url,
            source_path=path.name,
            defaults={"commit_sha": "napcore.eu", "content_hash": content_hash},
        )
        counts["indexed"] += 1
        counts["chunks"] += len(records)
        if report:
            report(f"indexed {len(records):4d} chunks  {path.name}")
    stale = SourceChunk.objects.filter(doc_type=DOC_TYPE).exclude(repository_url__in=present_urls)
    counts["removed"] = stale.values("repository_url").distinct().count()
    stale.delete()
    IndexedSourceFile.objects.filter(commit_sha="napcore.eu").exclude(repository_url__in=present_urls).delete()
    return counts


@lru_cache(maxsize=1)
def _titles(text_dir: Path = TEXT_DIR) -> dict[str, str]:
    """Source path -> document title, from the snapshot headers."""
    titles = {}
    for path in text_dir.glob("*.md"):
        snapshot = read_snapshot(path)
        titles[_source_path(snapshot.url)] = snapshot.title
    return titles


def citation_title(source_path: str) -> str:
    """A readable name for a cited napcore.eu document ("NAPCORE: Quality Online Repository"), else ""."""
    if not (source_path or "").startswith("napcore.eu"):
        return ""
    title = _titles().get(source_path) or source_path.rsplit("/", 1)[-1] or "napcore.eu"
    return f"NAPCORE: {title}"
