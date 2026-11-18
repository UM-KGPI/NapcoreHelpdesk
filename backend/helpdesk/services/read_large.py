"""
Search small, read large: a passage that is a piece of the prepared cut is given to the model with as much of its
unit around it as fits the room a passage has (LLM_MAX_EVIDENCE_CHARS_PER_CHUNK).

Design point 4 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md. The search ranks the small pieces;
which passages are given does not change, nor their source, path or chunk id (so the citation points at the same
file). Only the text of a passage grows: the found piece whole, then the next and the previous piece of the same
unit in turn (structured_metadata["piece"]: unit, order in the file, where the body lies in the text) while they
fit, without gaps, under the place line of the first piece taken. A unit is what the cut made it: a section of
prose, a schema declaration, a run of Turtle statements, an XML document (its pieces in document order).

Off unless RETRIEVAL_READ_UNIT is set; passages that are not prepared pieces are returned unchanged.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-16  |  Modified: 2026-11-16
"""

from __future__ import annotations

from django.db.models import Q

from helpdesk.services.prepared_cut import CUT_VERSION, META_KEY

# Pieces fetched on each side of a found piece: enough for the room of a passage (pieces of at most 256 tokens are
# rarely under 200 characters).
WINDOW = 6
JOINER = "\n"


def enabled() -> bool:
    from django.conf import settings

    return bool(getattr(settings, "RETRIEVAL_READ_UNIT", False))


def _meta(chunk: dict) -> dict | None:
    meta = (chunk.get("structuredMetadata") or {}).get(META_KEY)
    if isinstance(meta, dict) and meta.get("v") == CUT_VERSION and "seq" in meta and "body" in meta:
        return meta
    return None


def _split(text: str, meta: dict) -> tuple[str, str]:
    start, end = meta["body"]
    return text[:start], text[start:end]


def unit_text(seq: int, pieces: dict[int, tuple[str, str]], budget: int) -> str:
    """The text of piece seq with the pieces around it: pieces maps a seq to (head, body) of the same unit."""
    head, body = pieces[seq]
    first, last = seq, seq
    size = len(head) + len(body)
    grow_after, grow_before = True, True
    while grow_after or grow_before:
        for side in ("after", "before"):
            if side == "after" and grow_after:
                candidate = last + 1
                if candidate in pieces and size + len(JOINER) + len(pieces[candidate][1]) <= budget:
                    last = candidate
                    size += len(JOINER) + len(pieces[candidate][1])
                else:
                    grow_after = False
            elif side == "before" and grow_before:
                candidate = first - 1
                if candidate in pieces:
                    new_head = pieces[candidate][0]
                    grown = size - len(pieces[first][0]) + len(new_head) + len(JOINER) + len(pieces[candidate][1])
                    if grown <= budget:
                        first = candidate
                        size = grown
                        continue
                grow_before = False
    return pieces[first][0] + JOINER.join(pieces[s][1] for s in range(first, last + 1))


def read_large(chunks: list[dict], budget: int | None = None) -> tuple[list[dict], int]:
    """chunks with the text of each prepared piece grown to its unit around it; returns them and how many grew.

    One query fetches the neighbours of every piece. The piece's own text stays in "pieceText"."""
    from django.conf import settings

    from helpdesk.models import SourceChunk

    if budget is None:
        budget = max(200, int(getattr(settings, "LLM_MAX_EVIDENCE_CHARS_PER_CHUNK", 1200)))
    targets = [(chunk, meta) for chunk in chunks if (meta := _meta(chunk))]
    if not targets:
        return chunks, 0
    condition = Q()
    for chunk, meta in targets:
        condition |= Q(
            repository_url=chunk.get("repositoryUrl", ""),
            source_path=chunk.get("sourcePath", ""),
            **{
                f"structured_metadata__{META_KEY}__unit": meta.get("unit"),
                f"structured_metadata__{META_KEY}__seq__gte": int(meta["seq"]) - WINDOW,
                f"structured_metadata__{META_KEY}__seq__lte": int(meta["seq"]) + WINDOW,
            },
        )
    units: dict[tuple, dict[int, tuple[str, str]]] = {}
    for repository_url, source_path, text, metadata in SourceChunk.objects.filter(condition).values_list(
        "repository_url", "source_path", "text", "structured_metadata"
    ):
        meta = (metadata or {}).get(META_KEY) or {}
        if meta.get("v") != CUT_VERSION:
            continue
        units.setdefault((repository_url, source_path, meta.get("unit")), {})[int(meta["seq"])] = _split(text, meta)
    grown = 0
    result = []
    for chunk in chunks:
        meta = _meta(chunk)
        if meta is None:
            result.append(chunk)
            continue
        pieces = dict(units.get((chunk.get("repositoryUrl", ""), chunk.get("sourcePath", ""), meta.get("unit")), {}))
        seq = int(meta["seq"])
        pieces[seq] = _split(str(chunk.get("text", "")), meta)
        text = unit_text(seq, pieces, budget)
        if text == "".join(pieces[seq]) and len(pieces) == 1:
            result.append(chunk)
            continue
        grown += 1
        result.append({**chunk, "text": text, "pieceText": chunk.get("text", "")})
    return result, grown
