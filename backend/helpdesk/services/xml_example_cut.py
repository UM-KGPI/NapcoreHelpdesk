"""
Cut an XML example file into pieces at element boundaries, each with its place in the document.

The index cuts XML examples by lines (index_builder.split_xml): the body of a file is cut every 1,200
characters, in the middle of elements, and a piece does not say where in the document it sits. This cut
follows the document's structure instead, for any XML document:

- the largest whole elements that fit the size limit make a piece;
- an element larger than the limit is cut into its children, and so on down;
- a long run of sibling elements is cut into runs of whole siblings;
- the comments, text and whitespace before an element go with that element;
- each piece knows the path of the elements it sits in, from the root (its place in the document).

The pieces of a file, put together in order, give back the file exactly: nothing is lost or repeated.
Two things can make a piece longer than the limit: the closing tags of the elements it ends (they stay with
the piece they close) and a single line of text longer than the limit that has no space to cut at.

The cut is not used by default: see index_builder.ExampleCut and the recut_examples command
(docs/plans/2026-11-15-xml-example-chunks.md, step R0).

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-15  |  Modified: 2026-11-15
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_NAME = re.compile(r"[^\s/>]+")
_END_TAG = re.compile(r"</\s*([^\s>]+)\s*>")


@dataclass
class _Element:
    name: str
    start: int  # first character of the start tag
    head_end: int  # just after the start tag
    tail_start: int = -1  # first character of the end tag (head_end for an empty element)
    end: int = -1  # just after the end tag
    children: list["_Element"] = field(default_factory=list)


@dataclass(frozen=True)
class XmlPiece:
    text: str  # the slice of the file, without blank lines at its ends
    path: tuple[str, ...]  # local names of the elements the piece starts in, from the root
    start: int
    end: int


def _local(name: str) -> str:
    return name.rsplit(":", 1)[-1]


def _skip_to(text: str, index: int, marker: str) -> int:
    found = text.find(marker, index)
    if found < 0:
        raise ValueError(f"unclosed markup at {index}")
    return found + len(marker)


def _start_tag_end(text: str, index: int) -> int:
    """Index just after the '>' of the start tag that begins at index; quoted values may hold '>'."""
    quote = ""
    i = index + 1
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            return i + 1
        i += 1
    raise ValueError(f"unclosed start tag at {index}")


def _doctype_end(text: str, index: int) -> int:
    """A DOCTYPE may hold an internal subset in brackets with its own '>' characters."""
    depth = 0
    i = index + 2
    while i < len(text):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == ">" and depth <= 0:
            return i + 1
        i += 1
    raise ValueError(f"unclosed declaration at {index}")


def parse_elements(text: str) -> _Element:
    """The element tree of a document with character offsets; the returned node stands for the document.

    Raises ValueError for a document that is not well formed (unclosed markup, mismatched end tag)."""
    document = _Element(name="", start=0, head_end=0)
    stack = [document]
    i = 0
    length = len(text)
    while True:
        i = text.find("<", i)
        if i < 0:
            break
        if text.startswith("<!--", i):
            i = _skip_to(text, i + 4, "-->")
        elif text.startswith("<![CDATA[", i):
            i = _skip_to(text, i + 9, "]]>")
        elif text.startswith("<?", i):
            i = _skip_to(text, i + 2, "?>")
        elif text.startswith("<!", i):
            i = _doctype_end(text, i)
        elif text.startswith("</", i):
            match = _END_TAG.match(text, i)
            if not match or len(stack) < 2 or match.group(1) != stack[-1].name:
                raise ValueError(f"unexpected end tag at {i}")
            element = stack.pop()
            element.tail_start, element.end = i, match.end()
            i = match.end()
        else:
            match = _NAME.match(text, i + 1)
            if not match:
                raise ValueError(f"bad start tag at {i}")
            head_end = _start_tag_end(text, i)
            element = _Element(name=match.group(0), start=i, head_end=head_end)
            stack[-1].children.append(element)
            if text[head_end - 2] == "/":
                element.tail_start = element.end = head_end
            else:
                stack.append(element)
            i = head_end
    if len(stack) != 1:
        raise ValueError("unclosed element")
    document.tail_start = document.end = length
    return document


def _cut_text(text: str, start: int, end: int, limit: int, out: list[list[int]]) -> None:
    """Cut [start, end) at line ends into parts of at most limit characters; a longer line at spaces, else hard."""
    part = start
    while end - part > limit:
        window = text[part : part + limit]
        cut = window.rfind("\n")
        if cut <= 0:
            cut = max(window.rfind(" "), window.rfind("\t"))
        if cut <= 0:
            cut = limit
        out.append([part, part + cut])
        part += cut
    if part < end:
        out.append([part, end])


def _closing_only(text: str, start: int, end: int) -> bool:
    """True when [start, end) holds nothing but whitespace and end tags."""
    return not _END_TAG.sub("", text[start:end]).strip()


def _cut(text: str, node: _Element, start: int, limit: int, out: list[list[int]]) -> None:
    """Append pieces covering [start, node.end) to out; start may lie before the node (its leading content)."""
    if node.end - start <= limit:
        out.append([start, node.end])
        return
    if not node.children:
        _cut_text(text, start, node.end, limit, out)
        return
    run = start  # where the piece being gathered begins
    taken = start  # how far the content has been given to a piece or to the run
    for child in node.children:
        if child.end - run <= limit:
            taken = child.end
            continue
        if child.end - child.start > limit and child.head_end - run <= limit:
            # The element is cut into its children; what was gathered before it opens its first piece.
            _cut(text, child, run, limit, out)
            run = taken = child.end
            continue
        if run < taken:
            out.append([run, taken])
            run = taken
        if child.end - run <= limit:
            taken = child.end
            continue
        if child.end - child.start <= limit:
            # What comes before the element (comments, text, the parent's start tag) does not fit with it.
            _cut_text(text, run, child.start, limit, out)
            run, taken = child.start, child.end
            continue
        _cut(text, child, run, limit, out)
        run = taken = child.end
    if run == taken and out and out[-1][1] == run and _closing_only(text, run, node.end):
        out[-1][1] = node.end  # closing tags stay with the piece they close
        return
    if node.end - run <= limit:
        out.append([run, node.end])
        return
    if run < taken:
        out.append([run, taken])
        run = taken
    if out and out[-1][1] == run and _closing_only(text, run, node.end):
        out[-1][1] = node.end
    else:
        _cut_text(text, run, node.end, limit, out)


def _path_at(document: _Element, position: int) -> tuple[str, ...]:
    """Local names of the elements open at position, from the root."""
    path: list[str] = []
    node = document
    while True:
        inner = next(
            (c for c in node.children if c.start < position and c.head_end <= position <= c.tail_start),
            None,
        )
        if inner is None:
            return tuple(path)
        path.append(_local(inner.name))
        node = inner


def cut_xml_example(text: str, max_chars: int) -> list[XmlPiece]:
    """Cut an XML document into pieces at element boundaries (see the module doc).

    Raises ValueError when the document is not well formed; the caller keeps the line cut then."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    document = parse_elements(text)
    spans: list[list[int]] = []
    _cut(text, document, 0, max_chars, spans)
    pieces: list[XmlPiece] = []
    for start, end in spans:
        body = text[start:end]
        stripped = body.strip()
        if not stripped:
            continue
        first = start + (len(body) - len(body.lstrip()))
        pieces.append(
            XmlPiece(
                text=body.strip("\r\n").rstrip(),
                path=_path_at(document, first),
                start=start,
                end=end,
            )
        )
    return pieces


def piece_spans(text: str, max_chars: int) -> list[tuple[int, int]]:
    """The raw spans of the cut, whitespace-only ones included: they cover the document exactly, in order."""
    document = parse_elements(text)
    spans: list[list[int]] = []
    _cut(text, document, 0, max_chars, spans)
    return [(s, e) for s, e in spans]
