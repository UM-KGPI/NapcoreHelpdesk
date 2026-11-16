"""
The prepared cut: pieces that are units of their source, fit what the embedder reads, and say where they sit.

Step 1 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md, design points 1 to 3:

1. A piece is a unit of its source: XML whole elements (the element cut of xml_example_cut); prose a section,
   else whole paragraphs, else whole sentences; a schema declaration (split at its lines only when it does not
   fit); Turtle whole statements. A piece is cut inside a sentence, a line or a text node only when that unit
   alone does not fit; such pieces are marked (Piece.inside).
2. A piece fits what the embedder reads: its embedded text (passage_text: source path, heading, text) is at most
   the embedder's cut in tokens, counted by the embedder's own counter (embeddings.count_embedded_tokens). One
   limit for every kind. The cut packs by summed counts of its parts and then counts every piece exactly; a piece
   that is over is cut again.
3. A piece says where it sits: one line of place, embedded and shown to the model. XML: `Element path: A / B`
   (none for a file's opening piece). Prose: the path of headings, after the line that names the document.

Design point 4 (search small, read large) is read_large.py: each piece stores its unit, its order in the file and
where its body lies in its text (structured_metadata["piece"]), so the unit around a found piece can be put
together at answer time.

Units are found by structure, for any document of a kind; nothing here names an element, a standard or a file.
Not used by default: the indexers cut as before. The command prepare_index applies this cut to a database named
on the command line.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-16  |  Modified: 2026-11-16
"""

from __future__ import annotations

import bisect
import math
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

from helpdesk.services.embeddings import count_embedded_tokens, passage_text

CUT_VERSION = 1
META_KEY = "piece"
PLACE_SEPARATOR = " › "
XML_PLACE_PREFIX = "Element path: "
XML_PATH_SEPARATOR = " / "
# A piece with fewer words than this (and no element) is near-empty: a heading without text.
MIN_WORDS = 3

_SENTENCE_END = re.compile(r"(?<=[.!?;:])\s+(?=\S)")
_WORD = re.compile(r"[^\W\d_]{2,}")
_LINE_END_PUNCTUATION = re.compile(r"[.!?:;]\s*$")
_NEXT_CHAR = re.compile(r"[ \t]*(\S?)")


# ------------------------------------------------------------------------------------------------ counting


class TokenCounter:
    """Token counts of embedded texts by the embedder's own counter, remembered per text.

    count(texts, kind) returns (counts, the embedder's cut) as embeddings.count_embedded_tokens; limit is that cut
    unless given. clear() forgets the remembered counts (call it between files)."""

    def __init__(self, count=None, limit: int | None = None):
        self._count = count or count_embedded_tokens
        self._cache: dict[str, int] = {}
        self.limit = limit
        self.requests = 0

    def counts(self, texts: list[str]) -> list[int]:
        missing = list(dict.fromkeys(t for t in texts if t not in self._cache))
        if missing:
            values, max_tokens = self._count(missing, "passage")
            self.requests += 1
            if self.limit is None:
                self.limit = int(max_tokens)
            self._cache.update(zip(missing, values))
        return [self._cache[t] for t in texts]

    def ensure_limit(self) -> int:
        if self.limit is None:
            self.counts([""])
        return int(self.limit)

    def clear(self) -> None:
        self._cache.clear()


# ------------------------------------------------------------------------------------------------ pieces


@dataclass
class Unit:
    """A unit of a source and what each of its pieces repeats.

    key: the unit within its file (read_large gathers the pieces of one key); head: what every piece of the unit
    starts with (the line naming the document and the line of place), "" for none; blocks: paragraphs in order,
    joined by joiner; fields: what every piece's row gets (label, quality, metadata, ...); block_fields: per block,
    updates to fields taken from the first block of a piece (a PDF page)."""

    key: str
    source_path: str
    heading: str
    head: str
    blocks: list[str]
    joiner: str = "\n"
    fields: dict = field(default_factory=dict)
    block_fields: list[dict] | None = None


@dataclass
class Piece:
    source_path: str
    heading: str
    head: str
    body: str
    unit: str
    inside: bool = False
    fields: dict = field(default_factory=dict)
    tail: str = ""  # stored after the body, not embedded (the XML semantic summary)
    tokens: int = 0
    estimate: float = 0.0  # the cut's estimate of tokens before the exact count (XML)

    @property
    def text(self) -> str:
        return self.head + self.body + self.tail

    @property
    def embedded(self) -> str:
        """The part of text that is embedded (passage_text adds the source path and heading)."""
        return self.head + self.body

    def embedding_input(self) -> str:
        return passage_text(self.source_path, self.heading, self.embedded)

    def metadata(self, seq: int) -> dict:
        start = len(self.head)
        return {"v": CUT_VERSION, "unit": self.unit, "seq": seq, "body": [start, start + len(self.body)]}


def embedded_text(text: str, structured_metadata: dict | None) -> str:
    """The part of a stored chunk's text that is embedded: up to the end of its body for a piece of this cut (a
    text stored after it, the XML summary, is not embedded); the whole text for any other chunk."""
    meta = (structured_metadata or {}).get(META_KEY)
    if isinstance(meta, dict) and meta.get("v") == CUT_VERSION and isinstance(meta.get("body"), list):
        return text[: meta["body"][1]]
    return text


def place_head(lead: str, place: str) -> str:
    """The head of a prose piece: the line naming the document, the line of place, a blank line."""
    lines = [line for line in (lead, place) if line]
    return "\n".join(lines) + "\n\n" if lines else ""


def near_empty(body: str) -> bool:
    """A piece without an element and with fewer than MIN_WORDS words: a heading without text."""
    if re.search(r"<[A-Za-z_]", body):
        return False
    return len(_WORD.findall(body)) < MIN_WORDS


def sentence_spans(text: str, start: int = 0, end: int | None = None) -> list[tuple[int, int]]:
    """Spans of the sentences of text[start:end], without the space between them."""
    end = len(text) if end is None else end
    spans = []
    position = start
    for match in _SENTENCE_END.finditer(text, start, end):
        spans.append((position, match.start()))
        position = match.end()
    if position < end:
        spans.append((position, end))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def line_spans(text: str) -> list[tuple[int, int]]:
    """Spans of the lines of text that are units: a line that does not end a sentence and is followed by a line
    in lower case continues into it (wrapped text); other line breaks (list items, table rows, a new sentence on
    a new line) separate units."""
    spans = []
    start = 0
    for match in re.finditer(r"\n", text):
        before = text[start : match.start()].rstrip()
        following = _NEXT_CHAR.match(text, match.end())
        after = following.group(1) if following else ""
        if before and (_LINE_END_PUNCTUATION.search(before) or not after.islower()):
            spans.append((start, match.start()))
            start = match.end()
    spans.append((start, len(text)))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def _largest_fit(candidates: list[int], fits) -> int | None:
    """The largest candidate (ascending list) for which fits(candidate) holds, by bisection; None if none."""
    lo, hi, best = 0, len(candidates) - 1, None
    while lo <= hi:
        middle = (lo + hi) // 2
        if fits(candidates[middle]):
            best = candidates[middle]
            lo = middle + 1
        else:
            hi = middle - 1
    return best


def _word_runs(unit: Unit, block: str, start: int, end: int, counter: TokenCounter, limit: int) -> list[tuple[int, int]]:
    """A sentence that does not fit, in runs of whole words that fit (a word that does not fit alone: hard)."""

    def fits(stop: int) -> bool:
        return counter.counts([passage_text(unit.source_path, unit.heading, unit.head + block[position:stop])])[0] <= limit

    runs = []
    position = start
    while position < end:
        while position < end and block[position].isspace():
            position += 1
        if position >= end:
            break
        stops = [m.start() for m in re.finditer(r"\s+", block[position:end])]
        stops = [position + s for s in stops if s > 0] + [end]
        stop = _largest_fit(stops, fits)
        if stop is None:
            stop = _largest_fit(list(range(position + 1, stops[0] + 1)), fits) or position + 1
        runs.append((position, stop))
        position = stop
    return runs


def pack_unit(unit: Unit, counter: TokenCounter) -> list[Piece]:
    """The pieces of a unit: the whole unit if it fits; else whole blocks, packed; a block that does not fit is
    packed by sentences, a sentence that does not fit by words (marked inside). Every piece is counted exactly."""
    limit = counter.ensure_limit()
    blocks = [b for b in unit.blocks if b.strip()]
    if not blocks:
        return []

    def embedded(body: str) -> str:
        return passage_text(unit.source_path, unit.heading, unit.head + body)

    def piece(body: str, inside: bool, first_block: int, tokens: int) -> Piece:
        fields = dict(unit.fields)
        if unit.block_fields:
            fields.update(unit.block_fields[first_block])
        return Piece(unit.source_path, unit.heading, unit.head, body, unit.key, inside, fields, tokens=tokens)

    whole = unit.joiner.join(blocks)
    whole_count = counter.counts([embedded(whole)])[0]
    if whole_count <= limit:
        return [piece(whole, False, 0, whole_count)]
    base = counter.counts([embedded("")])[0]
    # Atoms: [block, start, end, level of the cut before it (0 block, 1 sentence, 2 inside a sentence), cost]
    atoms: list[list[int]] = []
    block_counts = counter.counts([embedded(b) for b in blocks])
    for index, (block, count) in enumerate(zip(blocks, block_counts)):
        if count <= limit:
            atoms.append([index, 0, len(block), 0, count - base])
            continue
        lines = line_spans(block)
        line_counts = counter.counts([embedded(block[s:e]) for s, e in lines])
        for line_number, ((ls, le), line_count) in enumerate(zip(lines, line_counts)):
            line_level = 0 if line_number == 0 else 1
            if line_count <= limit:
                atoms.append([index, ls, le, line_level, line_count - base])
                continue
            spans = sentence_spans(block, ls, le)
            span_counts = counter.counts([embedded(block[s:e]) for s, e in spans])
            for number, ((s, e), count) in enumerate(zip(spans, span_counts)):
                level = line_level if number == 0 else 1
                if count <= limit:
                    atoms.append([index, s, e, level, count - base])
                    continue
                runs = _word_runs(unit, block, s, e, counter, limit)
                run_counts = counter.counts([embedded(block[rs:re_]) for rs, re_ in runs])
                for run_number, ((rs, re_), run_count) in enumerate(zip(runs, run_counts)):
                    atoms.append([index, rs, re_, level if run_number == 0 else 2, run_count - base])

    def body_of(group: list[list[int]]) -> str:
        parts: list[str] = []
        current_block, current_start, current_end = None, 0, 0
        for block, start, end, _, _ in group:
            if block == current_block:
                current_end = end
                continue
            if current_block is not None:
                parts.append(blocks[current_block][current_start:current_end])
            current_block, current_start, current_end = block, start, end
        parts.append(blocks[current_block][current_start:current_end])
        return unit.joiner.join(parts)

    groups: list[list[list[int]]] = []
    current: list[list[int]] = []
    estimate = base
    for atom in atoms:
        cost = atom[4] + (1 if current else 0)
        if current and estimate + cost > limit:
            groups.append(current)
            current, estimate, cost = [], base, atom[4]
        current.append(atom)
        estimate += cost
    groups.append(current)

    while True:
        bodies = [body_of(g) for g in groups]
        counts = counter.counts([embedded(b) for b in bodies])
        over = [i for i, c in enumerate(counts) if c > limit and len(groups[i]) > 1]
        if not over:
            break
        for i in reversed(over):
            group = groups[i]
            total = sum(a[4] for a in group)
            best, best_score, running = 1, None, 0
            for k in range(1, len(group)):
                running += group[k - 1][4]
                score = (group[k][3], abs(running - total / 2))
                if best_score is None or score < best_score:
                    best, best_score = k, score
            groups[i : i + 1] = [group[:best], group[best:]]

    pieces = []
    for number, (group, body, count) in enumerate(zip(groups, bodies, counts)):
        following = groups[number + 1][0] if number + 1 < len(groups) else None
        inside = group[0][3] == 2 or (following is not None and following[3] == 2)
        pieces.append(piece(body, inside, group[0][0], count))
    return pieces


# ------------------------------------------------------------------------------------------------ XML


def xml_place(path: tuple[str, ...]) -> str:
    return f"{XML_PLACE_PREFIX}{XML_PATH_SEPARATOR.join(path)}\n" if path else ""


class _TokenMeasure:
    """The size of a span of an XML document in embedded tokens, estimated from the counts of its lines, with the
    place line of the element the span starts in (xml_example_cut._cut asks fits and cut_text)."""

    def __init__(self, text: str, document, source_path: str, heading: str, counter: TokenCounter, limit: int,
                 scale: float = 1.0):
        self.text, self.document, self.limit, self.scale = text, document, limit, scale
        self.source_path, self.heading, self.counter = source_path, heading, counter
        self.line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]
        lines = [text[s:e] for s, e in zip(self.line_starts, self.line_starts[1:] + [len(text)])]
        zero = counter.counts([""])[0]
        self.line_cost = [max(0, c - zero) for c in counter.counts([line.strip() for line in lines])]
        self.line_letters = [len(line) - sum(1 for ch in line if ch.isspace()) for line in lines]
        self.cumulative = [0]
        for cost in self.line_cost:
            self.cumulative.append(self.cumulative[-1] + cost)
        self._place_cost: dict[tuple[str, ...], int] = {}
        self.text_cuts: set[int] = set()

    def path_at(self, position: int) -> tuple[str, ...]:
        path: list[str] = []
        node = self.document
        while node.children:
            starts = [c.start for c in node.children] if not hasattr(node, "_starts") else node._starts
            if not hasattr(node, "_starts"):
                node._starts = starts
            index = bisect.bisect_left(starts, position) - 1
            if index < 0:
                break
            child = node.children[index]
            if not (child.head_end <= position <= child.tail_start):
                break
            path.append(child.name.rsplit(":", 1)[-1])
            node = child
        return tuple(path)

    def place_cost(self, path: tuple[str, ...]) -> int:
        if path not in self._place_cost:
            self._place_cost[path] = self.counter.counts(
                [passage_text(self.source_path, self.heading, xml_place(path))]
            )[0]
        return self._place_cost[path]

    def _partial(self, line: int, start: int, end: int) -> int:
        letters = self.line_letters[line]
        if not letters:
            return 0
        part = end - start - sum(1 for ch in self.text[start:end] if ch.isspace())
        return math.ceil(self.line_cost[line] * part / letters)

    def content(self, start: int, end: int) -> int:
        if end <= start:
            return 0
        first = bisect.bisect_right(self.line_starts, start) - 1
        last = bisect.bisect_right(self.line_starts, end - 1) - 1
        if first == last:
            return self._partial(first, start, end)
        first_end = self.line_starts[first + 1]
        return (
            self._partial(first, start, first_end)
            + self.cumulative[last] - self.cumulative[first + 1]
            + self._partial(last, self.line_starts[last], end)
        )

    def estimate(self, start: int, end: int) -> int:
        body = self.text[start:end]
        first = start + (len(body) - len(body.lstrip()))
        return math.ceil(self.scale * (self.place_cost(self.path_at(first)) + self.content(start, end)))

    def fits(self, start: int, end: int) -> bool:
        return self.estimate(start, end) <= self.limit

    def cut_text(self, text: str, start: int, end: int, out: list[list[int]]) -> None:
        """Cut [start, end), which is not an element (a long comment or text), between its units where one fits:
        at a line that ends a sentence or is followed by a line that does not continue it (a new item, a capital),
        else at the end of a sentence; else at a line end, a space or hard (these are marked inside a unit)."""
        part = start
        while part < end and not self.fits(part, end):
            # A piece that fits holds far fewer characters than this; candidates beyond it are not looked at.
            bound = min(end, part + 24 * self.limit)
            window = text[part:bound]
            fits = lambda stop: self.fits(part, stop)  # noqa: E731
            units, lines = [], []
            line_start = part
            for match in re.finditer(r"\n", window):
                stop = part + match.end()
                if stop >= end:
                    break
                before = text[line_start : stop - 1].rstrip(" \t")
                following = _NEXT_CHAR.match(text, stop, end)
                after = following.group(1) if following else ""
                (units if (not before or _LINE_END_PUNCTUATION.search(before) or not after.islower()) else lines).append(stop)
                line_start = stop
            sentences = [part + m.end() for m in _SENTENCE_END.finditer(window) if part + m.end() < end]
            best = _largest_fit(units, fits) or _largest_fit(sorted(set(sentences) - set(units)), fits)
            inside = best is None
            if best is None:
                best = _largest_fit(lines, fits)
            if best is None:
                line_end = text.find("\n", part, bound)
                line_end = bound if line_end < 0 else line_end + 1
                spaces = [part + m.end() for m in re.finditer(r"\s+", text[part:line_end]) if part + m.end() < line_end]
                best = _largest_fit(spaces, fits)
                if best is None:
                    best = _largest_fit(list(range(part + 1, line_end + 1)), fits) or part + 1
            out.append([part, best])
            if inside:
                self.text_cuts.add(best)
            part = best
        if part < end:
            out.append([part, end])


def cut_xml(text: str, source_path: str, heading: str, counter: TokenCounter, *, unit: str, fields: dict | None = None,
            summary=None, max_rounds: int = 8) -> tuple[list[Piece], dict]:
    """The element cut of an XML document by embedded tokens, every piece with its place line.

    Pieces are cut at element boundaries (xml_example_cut); each is counted exactly, and when one is over the
    limit the file is cut again with a smaller budget. summary(body) gives the text stored after a piece's body
    and not embedded. Raises ValueError for a document that is not well formed. Returns the pieces and
    {"rounds", "margin"}."""
    from helpdesk.services.xml_example_cut import _cut, parse_elements

    limit = counter.ensure_limit()
    document = parse_elements(text)
    margin, scale = 0, 1.0
    for rounds in range(1, max_rounds + 1):
        measure = _TokenMeasure(text, document, source_path, heading, counter, limit - margin, scale)
        spans: list[list[int]] = []
        _cut(text, document, 0, measure, spans)
        pieces: list[Piece] = []
        for start, end in spans:
            raw = text[start:end]
            if not raw.strip():
                continue
            first = start + (len(raw) - len(raw.lstrip()))
            body = raw.strip("\r\n").rstrip()
            inside = start in measure.text_cuts or end in measure.text_cuts
            piece = Piece(source_path, heading, xml_place(measure.path_at(first)), body, unit, inside, dict(fields or {}))
            piece.estimate = measure.estimate(start, end) / scale
            pieces.append(piece)
        counts = counter.counts([p.embedding_input() for p in pieces])
        for p, count in zip(pieces, counts):
            p.tokens = count
        over = max((c - limit for c in counts), default=0)
        if over <= 0 or margin >= limit // 2:
            break
        if rounds == 1:
            # The sum of line counts misses a few tokens a piece (line breaks, joins): the file's own ratio of
            # exact to estimated counts, taken high (the 95th of its pieces), corrects the next round.
            ratios = sorted(c / max(1, p.estimate) for p, c in zip(pieces, counts))
            scale = max(1.0, ratios[int(0.95 * (len(ratios) - 1))])
            continue
        margin += max(over, 2)
    if summary is not None:
        for p in pieces:
            p.tail = summary(p.body)
    return pieces, {"rounds": rounds, "margin": margin}


# ------------------------------------------------------------------------------------------------ prose kinds


def paragraphs(text: str) -> list[str]:
    """Paragraphs of plain text: blocks between blank lines; inside a block, lines stay as they are."""
    return [block.strip("\n") for block in re.split(r"\n\s*\n", text) if block.strip()]


def joined_lines(lines: list[str]) -> list[str]:
    """Lines as paragraphs, where a line that does not end a sentence and is followed by a line in lower case
    (text wrapped at a fixed width, as in a PDF) continues the same paragraph."""
    blocks: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        if blocks and not _LINE_END_PUNCTUATION.search(blocks[-1]) and line.lstrip()[:1].islower():
            blocks[-1] = f"{blocks[-1]}\n{line}"
        else:
            blocks.append(line)
    return blocks


def markdown_units(text: str, source_path: str, *, fields: dict | None = None) -> list[Unit]:
    """A Markdown document by its headings (levels 1 to 3, as split_markdown): one unit per section, the path of
    headings as the place line, the paragraphs as blocks."""
    units: list[Unit] = []
    path: list[tuple[int, str]] = []
    lines: list[str] = []

    def flush():
        body = "\n".join(lines).strip()
        lines.clear()
        if not body:
            return
        place = PLACE_SEPARATOR.join(h for _, h in path)
        units.append(
            Unit(f"{source_path}#{len(units)}", source_path, path[-1][1] if path else "", place_head("", place),
                 paragraphs(body), "\n\n", dict(fields or {}))
        )

    for line in text.split("\n"):
        match = re.match(r"^(#{1,3})\s+(\S.*)$", line)
        if match:
            flush()
            level = len(match.group(1))
            path[:] = [p for p in path if p[0] < level] + [(level, match.group(2).strip())]
            continue
        lines.append(line)
    flush()
    return units


class _HtmlPathBlocks(HTMLParser):
    """(path of headings, block) pairs of an HTML document, as index_builder._HtmlBlocks with heading levels."""

    def __init__(self):
        from helpdesk.services.index_builder import _HtmlBlocks

        super().__init__(convert_charrefs=True)
        self._inner = _HtmlBlocks()
        self._path: list[tuple[int, str]] = []
        self._level = 0
        self.blocks: list[tuple[tuple[str, ...], str]] = []

    def _sync(self):
        while len(self.blocks) < len(self._inner.blocks):
            heading, block = self._inner.blocks[len(self.blocks)]
            names = tuple(h for _, h in self._path)
            self.blocks.append((names if names else ((heading,) if heading else ()), block))

    def handle_starttag(self, tag, attrs):
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and not self._inner._skip:
            self._level = int(tag[1])
        self._inner.handle_starttag(tag, attrs)
        self._sync()

    def handle_endtag(self, tag):
        heading_before = self._inner.heading
        in_heading = self._inner._in_heading
        self._inner.handle_endtag(tag)
        if in_heading and not self._inner._in_heading and tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            heading = self._inner.heading
            if heading or heading_before:
                self._path = [p for p in self._path if p[0] < self._level] + [(self._level, heading)]
        self._sync()

    def handle_data(self, data):
        self._inner.handle_data(data)

    def close(self):
        super().close()
        self._inner._flush_text()
        self._sync()


def html_units(text: str, source_path: str, *, fields: dict | None = None) -> list[Unit] | None:
    """An HTML document by its headings: one unit per section with the path of headings as the place line, its
    paragraphs and table rows as blocks. A fragment without headings takes its heading from the file name (as
    split_html). None when the markup cannot be read."""
    from pathlib import Path as _Path

    parser = _HtmlPathBlocks()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return None
    fallback = _Path(source_path).stem.replace("-", " ").replace("_", " ").strip().capitalize()
    units: list[Unit] = []
    current: tuple[str, ...] | None = None
    blocks: list[str] = []

    def flush():
        if blocks:
            names = current or (fallback,)
            units.append(
                Unit(f"{source_path}#{len(units)}", source_path, names[-1], place_head("", PLACE_SEPARATOR.join(names)),
                     list(blocks), "\n\n", dict(fields or {}))
            )
            blocks.clear()

    for names, block in parser.blocks:
        if names != current:
            flush()
            current = names
        blocks.append(block)
    flush()
    return units


def turtle_units(text: str, source_path: str, counter: TokenCounter, *, fields: dict | None = None) -> list[Unit] | None:
    """Turtle by statements: runs of statements of the same rdf:type are one unit each (as split_turtle groups
    them), the types as heading; a statement that does not fit alone is its own unit, cut at its predicates, with
    its subject as the place line. None when the text has no statements."""
    from helpdesk.services.index_builder import _turtle_statements, _turtle_type

    statements = _turtle_statements(text)
    if not statements:
        return None
    limit = counter.ensure_limit()
    units: list[Unit] = []
    run: list[str] = []
    run_types: list[str] = []

    def flush():
        if run:
            heading = ", ".join(dict.fromkeys(t for t in run_types if t))
            units.append(Unit(f"{source_path}#{len(units)}", source_path, heading, "", list(run), "\n\n", dict(fields or {})))
            run.clear()
            run_types.clear()

    counts = counter.counts([passage_text(source_path, _turtle_type(s), s) for s in statements])
    for statement, count in zip(statements, counts):
        statement_type = _turtle_type(statement)
        if count > limit:
            flush()
            subject = statement.split(None, 1)[0]
            lines = [line for line in statement.split("\n") if line.strip()]
            units.append(
                Unit(f"{source_path}#{len(units)}", source_path, statement_type, f"Subject: {subject}\n", lines, "\n",
                     dict(fields or {}))
            )
            continue
        if run_types and statement_type and statement_type not in run_types:
            flush()
        run.append(statement)
        run_types.append(statement_type)
    flush()
    return units


def xsd_units(text: str, source_path: str, *, fields_for=None) -> list[Unit] | None:
    """A schema by declarations (split_xsd_summary): one unit per declaration, its first two lines (what it is,
    where it is defined) repeated by each piece when it must be cut, its other lines as blocks. A schema without
    declarations: its description lines as one unit. None for a schema that cannot be parsed (it keeps its cut)."""
    import xml.etree.ElementTree as ET

    from helpdesk.services.index_builder import _schema_has_declarations, split_xsd_summary

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    chunks = split_xsd_summary(text, source_name=source_path)
    units = []
    declarations = _schema_has_declarations(root)
    if not declarations:
        lines = [line for chunk, _, _ in chunks for line in chunk.split("\n")]
        heading = chunks[0][2] if chunks else source_path
        fields = fields_for(heading) if fields_for else {}
        return [Unit(f"{source_path}#0", source_path, heading, "", lines, "\n", fields)] if lines else []
    for chunk, _, heading in chunks:
        lines = chunk.split("\n")
        fields = fields_for(heading) if fields_for else {}
        # Lines of a "Child element documentation:" list stay lines; the head names the declaration.
        units.append(Unit(f"{source_path}#{len(units)}", source_path, heading, "\n".join(lines[:2]) + "\n", lines[2:], "\n", fields))
    return units


def text_units(text: str, source_path: str, *, fields: dict | None = None) -> list[Unit]:
    """Plain text without headings: one unit, its paragraphs as blocks."""
    blocks = paragraphs(text)
    return [Unit(f"{source_path}#0", source_path, "", "", blocks, "\n\n", dict(fields or {}))] if blocks else []


def snapshot_units(text: str, *, source_path: str, lead: str, title: str, min_section_chars: int, fields: dict,
                   page_url) -> list[Unit]:
    """A page or document snapshot (napcore_site, datex: lines, "#" headings, "[page N]" markers): a new unit at
    a heading once the current one has min_section_chars of text (the theme puts whole sentences in heading tags,
    so heading lines stay in the text, as chunk_snapshot does), the path of headings as the place line, lines as
    blocks (wrapped lines joined). page_url(page) gives the per-block fields of a PDF page."""
    marker = re.compile(r"^\[page (\d+)\]$")
    units: list[Unit] = []
    path: list[tuple[int, str]] = []
    lines: list[tuple[str, int | None]] = []
    page: int | None = None
    place = ""

    def flush():
        nonlocal place
        if lines:
            blocks, pages = [], []
            for line, line_page in lines:
                if blocks and not _LINE_END_PUNCTUATION.search(blocks[-1]) and line.lstrip()[:1].islower():
                    blocks[-1] = f"{blocks[-1]}\n{line}"
                else:
                    blocks.append(line)
                    pages.append(line_page)
            heading = (path[-1][1] if path else "") or title
            units.append(
                Unit(f"{source_path}#{len(units)}", source_path, heading[:512], place_head(lead, place), blocks, "\n",
                     dict(fields), [page_url(p) for p in pages])
            )
            lines.clear()

    for raw in text.splitlines():
        found = marker.match(raw.strip())
        if found:
            page = int(found.group(1))
            continue
        line = raw
        if line.startswith("#"):
            if sum(len(p) + 1 for p, _ in lines) >= min_section_chars:
                flush()
            level = len(line) - len(line.lstrip("#"))
            name = line.lstrip("#").strip()[:200]
            path[:] = [p for p in path if p[0] < level] + [(level, name)]
            place = PLACE_SEPARATOR.join(h for _, h in path if h)
            line = name
        if line.strip():
            lines.append((line, page))
    flush()
    return units


# ------------------------------------------------------------------------------------------------ harvested kinds


def act_units(act) -> list[Unit]:
    """An EU act (regulations.parse_act, without its size limit): an article, an annex or appendix section (a new
    one at each heading inside it) or a recital is a unit; its paragraphs are the blocks; the act's name and the
    section's heading lead every piece."""
    import xml.etree.ElementTree as ET

    from helpdesk.services import regulations as reg

    def act_paragraphs(div):
        label = ""
        for text, is_heading in reg._blocks(div):
            if reg._LIST_LABEL.match(text):
                label = f"{label} {text}".strip()
                continue
            yield (f"{label} {text}" if label else text), is_heading
            label = ""

    sections: list[tuple[reg.Section, list[str]]] = []

    def pack(anchor: str, heading: str, items, *, split_on_headings: bool):
        current: list[str] = []
        subheading = ""

        def flush():
            if current:
                title = f"{heading} — {subheading}" if subheading else heading
                sections.append((reg.Section(anchor=anchor, heading=title, text="\n".join(current)), list(current)))
                current.clear()

        for text, is_heading in items:
            if split_on_headings and is_heading:
                flush()
                subheading = text
            current.append(text)
        flush()

    root = ET.fromstring(act.path.read_bytes())
    for div in root.iter(f"{reg._NS}div"):
        anchor = div.get("id") or ""
        if "." in anchor:
            continue
        if anchor.startswith("rct_"):
            text = reg._text(div)
            if text:
                sections.append((reg.Section(anchor, "Recitals", text), [text]))
        elif anchor.startswith("art_"):
            titles = [reg._text(p) for p in div.iter(f"{reg._NS}p") if reg._has_class(p, reg._ARTICLE_TITLE_CLASSES)]
            subtitles = [reg._text(p) for p in div.iter(f"{reg._NS}p") if reg._has_class(p, reg._ARTICLE_SUBTITLE_CLASSES)]
            heading = " — ".join(t for t in (titles[:1] + subtitles[:1]) if t) or anchor
            body = [(text, False) for text, _ in act_paragraphs(div) if text not in titles[:1] + subtitles[:1]]
            pack(anchor, heading, body, split_on_headings=False)
        elif anchor.startswith("anx_"):
            pack(anchor, "Annex", act_paragraphs(div), split_on_headings=True)
        elif anchor.startswith("app_"):
            pack(anchor, f"Appendix {anchor.split('_', 1)[1]}", act_paragraphs(div), split_on_headings=True)
    kept = {id(s) for s in reg.select_sections(act, [s for s, _ in sections])}
    units = []
    for section, blocks in sections:
        if id(section) not in kept:
            continue
        fields = {
            "label": f"{act.name}, {section.heading}"[:255],
            "quality_score": act.quality if section.heading != "Recitals" else min(act.quality, 0.5),
            "structured_metadata": {"sourceUrl": f"{act.url}#{section.anchor}", "celex": act.celex, "actKind": act.kind},
        }
        units.append(
            Unit(f"{act.celex}#{section.anchor}#{len(units)}", f"{act.celex}#{section.anchor}", section.heading[:512],
                 place_head(act.name, section.heading), blocks, "\n", fields)
        )
    return units


def napcore_units(snapshot) -> list[Unit]:
    from helpdesk.services import napcore_site as site

    source_path = site._source_path(snapshot.url)
    is_pdf = snapshot.url.lower().split("?")[0].endswith(".pdf")
    units = snapshot_units(
        snapshot.text,
        source_path=source_path,
        lead=f"NAPCORE (napcore.eu): {snapshot.title}",
        title=snapshot.title,
        min_section_chars=site.MIN_SECTION_CHARS,
        fields={"quality_score": 0.75 if is_pdf else 0.85},
        page_url=lambda page: {
            "structured_metadata": {"sourceUrl": f"{snapshot.url}#page={page}" if page else snapshot.url, "title": snapshot.title}
        },
    )
    for unit in units:
        heading = unit.heading if unit.heading != snapshot.title else ""
        unit.fields["label"] = (f"NAPCORE: {snapshot.title}" + (f" — {heading}" if heading else ""))[:255]
    return units


def datex_page_units(snapshot) -> list[Unit]:
    from helpdesk.services import datex, napcore_site as site

    units = snapshot_units(
        snapshot.text,
        source_path=f"docs.datex2.eu/v{datex.VERSION}/{datex.page_name(snapshot.url)}",
        lead=f"DATEX II v{datex.VERSION} documentation: {snapshot.title}",
        title=snapshot.title,
        min_section_chars=site.MIN_SECTION_CHARS,
        fields={"quality_score": 0.8},
        page_url=lambda page: {"structured_metadata": {"sourceUrl": snapshot.url, "title": snapshot.title}},
    )
    for unit in units:
        heading = unit.heading
        unit.fields["label"] = (
            f"DATEX II documentation: {snapshot.title}" + (f" — {heading}" if heading and heading != snapshot.title else "")
        )[:255]
    return units


def datex_model_units(model: dict) -> list[Unit]:
    """A DATEX II model element (datex.element_text) is a unit: its first line (what it is) leads every piece,
    its definition and its attribute, value and association lines are the blocks."""
    from helpdesk.services import datex

    units = []
    for element in model["elements"]:
        if not element["name"]:
            continue
        key = f"{element['namespace']}.{element['name']}"
        lines = datex.element_text(element).split("\n")
        source_path = f"datex-model-v{model['version']}/{key}"
        fields = {
            "label": f"DATEX II {element['kind']} {element['name']} ({element['namespace']})"[:255],
            "quality_score": 0.85 if element["definition"] else 0.6,
            "structured_metadata": {
                "sourceUrl": datex.MODEL_PAGE_URL,
                "title": f"DATEX II v{model['version']} {element['name']}",
                "namespace": element["namespace"],
            },
        }
        units.append(Unit(source_path, source_path, lines[0][:512], lines[0] + "\n", lines[1:], "\n", fields))
    return units


def inspire_spec_units(spec_text: str) -> list[Unit]:
    """The INSPIRE specification by sections (inspire.spec_chunks, without its size limit): a section is a unit,
    short sections joined to the next as there; its paragraphs are the blocks; the document's title and the path
    of headings lead every piece."""
    from helpdesk.services import inspire

    sections = inspire.parse_spec(spec_text)
    found: list[tuple[str, str, int]] = []
    carried: list[str] = []
    carried_line = None
    for section in sections:
        heading = " › ".join(section.path[1:]) or section.path[0]
        text = "\n".join(carried + [section.text]) if carried else section.text
        line = carried_line or section.line
        if len(text) < inspire.MIN_SECTION_CHARS:
            carried, carried_line = [f"{section.path[-1]}: {section.text}"], line
            continue
        carried, carried_line = [], None
        found.append((heading, text, line))
    if carried:
        found.append((" › ".join(sections[-1].path[1:]), "\n".join(carried), carried_line))
    units = []
    for heading, text, line in found:
        secondary = heading.split(" › ", 1)[0].startswith(inspire._SECONDARY_CHAPTERS)
        fields = {
            "label": f"INSPIRE Transport Networks: {heading.rsplit(' › ', 1)[-1]}"[:255],
            "quality_score": 0.5 if secondary else 0.85,
            "structured_metadata": {"sourceUrl": inspire.spec_url(line), "title": inspire.SPEC_TITLE, "tag": inspire.SPEC_TAG},
        }
        source_path = f"{inspire.SPEC_REPO_PATH}#L{line}"
        units.append(Unit(f"{source_path}#{len(units)}", source_path, heading[:512],
                          place_head(inspire.SPEC_TITLE, heading), paragraphs(text), "\n\n", fields))
    return units


def inspire_codelist_units(codelists: list[dict]) -> list[Unit]:
    """An INSPIRE code list is a unit: its name leads every piece, its definition and its values are the blocks."""
    from helpdesk.services import inspire

    units = []
    for codelist in codelists:
        name = codelist["name"]
        head = f"INSPIRE code list {name} ({codelist['label'] or name})"
        lines = [t for t in (codelist["definition"], codelist["description"]) if t]
        values = []
        for value in codelist["values"]:
            code = value["id"].rsplit("/", 1)[-1]
            meaning = " ".join(t for t in (value["definition"], value["description"]) if t)
            values.append(f"- {code} ({value['label']}): {meaning}".rstrip(": "))
        if values:
            lines += ["Values:"] + values
        fields = {
            "label": f"INSPIRE code list: {name}"[:255],
            "quality_score": 0.8,
            "structured_metadata": {"sourceUrl": f"{inspire.REGISTRY_URL}{name}", "title": f"INSPIRE code list {name}"},
        }
        source_path = f"codelist/{name}"
        units.append(Unit(source_path, source_path, head[:512], head + "\n\n", lines, "\n", fields))
    return units
