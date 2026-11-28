"""
A record is served whole: a passage that belongs to a record the index holds in a few pieces is given to the model
with all the pieces of that record.

A DATEX II class is one unit of the prepared cut cut into several pieces (the definition and attributes in one, the
associations in another). The search ranks the pieces and one passage per file is served, so the piece with the
relation the question asks about could stay out of the answer. With RETRIEVAL_WHOLE_RECORD_MAX_PIECES set, a served
passage whose unit is its own source path (the cut made the whole file one unit) and whose file holds at most that
many pieces, together at most MAX_CHARS characters, is given with all its pieces in their order: one passage, one
place, one citation (chunk id, source and path stay those of the served piece). The text of the pieces is joined as
read_large joins them (the first piece's lead line once, then each piece's body). A file that holds more pieces
(a schema, a long page) or more characters is left as it is. The record is defined by what the index holds, not
by a name.

Off (0) by default: passages are returned as before.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-23  |  Modified: 2026-11-23
"""

from __future__ import annotations

from helpdesk.services.prepared_cut import CUT_VERSION, META_KEY
from helpdesk.services.read_large import JOINER, _meta, _split

# Longest text of a record that is joined (characters of its lead line and its pieces' bodies).
MAX_CHARS = 4500


def max_pieces() -> int:
    from django.conf import settings

    return max(0, int(getattr(settings, "RETRIEVAL_WHOLE_RECORD_MAX_PIECES", 0) or 0))


def _rows_of_file(repository_url: str, source_path: str, limit: int) -> list[tuple[str, dict]]:
    """At most limit rows (text, structured_metadata) of the file; one more than the largest record, so a larger file shows."""
    from helpdesk.models import SourceChunk

    return list(
        SourceChunk.objects.filter(repository_url=repository_url, source_path=source_path).values_list(
            "text", "structured_metadata"
        )[:limit]
    )


def record_text(rows: list[tuple[str, dict]], source_path: str, pieces_max: int, chars_max: int = MAX_CHARS) -> str | None:
    """The joined text of a file's rows when they are a record, else None.

    A record: 2 to pieces_max rows, every one a piece of the prepared cut whose unit is the file's own path, together at
    most chars_max characters (lead line once, then the bodies in order)."""
    if not 2 <= len(rows) <= pieces_max:
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
    joined = parts[order[0]][0] + JOINER.join(parts[seq][1] for seq in order)
    return joined if len(joined) <= chars_max else None


def whole_records(chunks: list[dict], pieces_max: int | None = None, fetch=_rows_of_file) -> tuple[list[dict], int]:
    """chunks with the text of each served piece of a record replaced by the whole record; returns them and how many grew.

    The piece's text before stays in "pieceText"; "wholeRecord" is the number of pieces joined (the prompt builder
    does not cut such a text: it is bounded by MAX_CHARS)."""
    pieces_max = max_pieces() if pieces_max is None else pieces_max
    if pieces_max < 2:
        return chunks, 0
    cache: dict[tuple[str, str], str | None] = {}
    grown = 0
    result = []
    for chunk in chunks:
        meta = _meta(chunk)
        path = chunk.get("sourcePath", "")
        if meta is None or meta.get("unit") != path:
            result.append(chunk)
            continue
        key = (chunk.get("repositoryUrl", ""), path)
        if key not in cache:
            cache[key] = record_text(fetch(key[0], path, pieces_max + 1), path, pieces_max)
        text = cache[key]
        if text is None or len(text) <= len(str(chunk.get("text", ""))):
            result.append(chunk)
            continue
        grown += 1
        result.append({**chunk, "text": text, "pieceText": chunk.get("pieceText", chunk.get("text", "")), "wholeRecord": True})
    return result, grown
