"""
Which cut a file of the index has, and how a file is cut and written with the prepared cut.

Step 5 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md. Every row stores the cut that made it:
a row of the prepared cut (prepared_cut.py) has structured_metadata["piece"]["v"] == CUT_VERSION, a row of the
cut of before (index_builder.split_structured and the harvesters' own record builders) has no such key and is
version 0. A file (a repository file, or a harvested document: one EU act, one page, the DATEX II model, ...)
has the version of its rows.

- The indexers cut a file again with the version its rows have, so a refresh never changes a file's version.
  A file without rows takes the version of most rows of its repository (or of its kind, for harvested
  documents); when those have no rows either, INDEX_CUT_VERSION (0 by default). So an index of the cut of
  before stays one, whatever the code.
- Changing the version of files is its own command, prepare_index --cut-version N: it cuts each file again with
  version N, embeds the new pieces and only then replaces the file's rows in one transaction, so the search
  never sees a file without rows; a file already at N is skipped, so a stopped run goes on where it stopped.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-18  |  Modified: 2026-11-18
"""

from __future__ import annotations

import collections
import hashlib
from pathlib import Path

from django.conf import settings
from django.db import transaction

from helpdesk.models import SourceChunk
from helpdesk.services import prepared_cut as pc
from helpdesk.services.embeddings import build_text_embeddings_batch, passage_text, uses_semantic

OLD_CUT = 0
VERSIONS = (OLD_CUT, pc.CUT_VERSION)
EMBED_SLICE = 256  # pieces per call of build_text_embeddings_batch (it sends SERVICE_BATCH_SIZE per request)


# ------------------------------------------------------------------------------------------------ versions


def row_version(structured_metadata: dict | None) -> int:
    meta = (structured_metadata or {}).get(pc.META_KEY)
    if isinstance(meta, dict) and isinstance(meta.get("v"), int):
        return meta["v"]
    return OLD_CUT


def rows_version(rows) -> int | None:
    """The version most of the rows (a queryset) have; None when there are none."""
    total = rows.count()
    if not total:
        return None
    prepared = rows.filter(**{f"structured_metadata__{pc.META_KEY}__v": pc.CUT_VERSION}).count()
    return pc.CUT_VERSION if prepared * 2 > total else OLD_CUT


def configured_version() -> int:
    """INDEX_CUT_VERSION: the cut of a file whose repository or kind has no rows yet."""
    version = int(getattr(settings, "INDEX_CUT_VERSION", OLD_CUT) or OLD_CUT)
    if version not in VERSIONS:
        raise ValueError(f"INDEX_CUT_VERSION {version} is not one of {VERSIONS}")
    return version


def group_version(rows) -> int:
    """The version for a new file of a group of rows (a repository, a kind of harvested document)."""
    found = rows_version(rows)
    return configured_version() if found is None else found


def document_version(repository_url: str, doc_type: str) -> int:
    """The version a harvested document is cut with: that of its rows, else that of its kind."""
    found = rows_version(SourceChunk.objects.filter(repository_url=repository_url))
    if found is not None:
        return found
    # Harvested kinds have doc types of their own (regulation, napcore, datex, inspire).
    return group_version(SourceChunk.objects.filter(doc_type=doc_type))


# ------------------------------------------------------------------------------------------------ duplicates


class SeenPieces:
    """Texts of prepared pieces already kept, per doc_type, and the file that keeps each.

    The prepared cut leaves out a piece whose text equals a kept piece of the same doc_type (copies of one
    example in two folders, repeated frames in one file): the first file keeps it. load=True starts from the
    prepared rows in the database (an indexer writing one file); load=False starts empty and is filled as files
    are written (a run over every file, as the command)."""

    def __init__(self, *, load: bool):
        self._load = load
        self._owner: dict[tuple[str, str], str] = {}
        self._keys: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)

    @staticmethod
    def _digest(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()  # nosec B324 - equality of texts only

    @staticmethod
    def file_key(repository_url: str, source_path: str) -> str:
        return f"{repository_url}|{source_path}"

    def _ensure(self) -> None:
        """Load the prepared rows once, before the first question (so a file forgotten first is forgotten)."""
        if not self._load:
            return
        self._load = False
        from django.db.models.functions import MD5

        rows = (
            SourceChunk.objects.filter(**{f"structured_metadata__{pc.META_KEY}__v": pc.CUT_VERSION})
            .annotate(digest=MD5("text"))
            .values_list("doc_type", "digest", "repository_url", "source_path")
        )
        for doc_type, digest, repo, path in rows.iterator(chunk_size=5000):
            key = self.file_key(repo, path)
            self._owner.setdefault((doc_type, digest), key)
            self._keys[key].add((doc_type, digest))

    def forget(self, repository_url: str, source_path: str | None = None) -> None:
        """A file is cut again (a harvested document, of many source paths: source_path None): its old pieces
        no longer keep their texts."""
        self._ensure()
        prefix = self.file_key(repository_url, source_path or "")
        keys = [prefix] if source_path is not None else [k for k in self._keys if k.startswith(prefix)]
        for key in [k for k in keys if k in self._keys]:
            for item in self._keys.pop(key):
                if self._owner.get(item) == key:
                    del self._owner[item]

    def taken(self, doc_type: str, text: str) -> bool:
        self._ensure()
        return (doc_type, self._digest(text)) in self._owner

    def add(self, doc_type: str, text: str, file_key: str) -> None:
        self._ensure()
        item = (doc_type, self._digest(text))
        self._owner.setdefault(item, file_key)
        self._keys[file_key].add(item)


# ------------------------------------------------------------------------------------------------ cutting


def pack(units: list[pc.Unit], counter: pc.TokenCounter) -> list[pc.Piece]:
    """Pieces of prose units. One request counts every whole unit of the file first; most units fit whole."""
    counter.counts([passage_text(u.source_path, u.heading, u.head + u.joiner.join(b for b in u.blocks if b.strip())) for u in units])
    pieces: list[pc.Piece] = []
    for unit in units:
        pieces.extend(pc.pack_unit(unit, counter))
    return pieces


def repository_file_cut(raw: str, path: str, *, example: bool, counter: pc.TokenCounter, xml_info: list | None = None):
    """The prepared cut of one repository file: (pieces, chunk_type), or None when it cannot be cut by structure
    (an XML file that is not well formed, a schema that cannot be read)."""
    from helpdesk.services.index_builder import enrich_xml_example_text, extract_xsd_structured_metadata

    suffix = Path(path).suffix.lower()
    if suffix == ".xml":
        summary = (lambda body: enrich_xml_example_text(chunk_text=body, source_path=path)[len(body):]) if example else None
        try:
            pieces, info = pc.cut_xml(raw, path, "", counter, unit=path, summary=summary)
        except ValueError:
            return None
        if xml_info is not None:
            xml_info.append(info)
        return pieces, "schema_fragment"
    chunk_type = "prose"
    if suffix == ".xsd":
        metadata = extract_xsd_structured_metadata(raw)
        units = pc.xsd_units(raw, path, fields_for=lambda heading: {"structured_metadata": dict(metadata.get(heading, {}))})
        chunk_type = "schema_fragment"
    elif suffix == ".md":
        units = pc.markdown_units(raw, path)
    elif suffix in {".html", ".htm"}:
        units = pc.html_units(raw, path)
    elif suffix == ".ttl":
        units = pc.turtle_units(raw, path, counter)
    else:
        units = pc.text_units(raw, path)
    if units is None:
        return None
    return pack(units, counter), chunk_type


def is_example_path(path: str) -> bool:
    from helpdesk.services.index_builder import infer_doc_type

    return infer_doc_type(path, "prose", "", "") == "example"


def keep_pieces(pieces: list[pc.Piece], *, seen: SeenPieces, file_key, doc_type_of, stats=None) -> list[pc.Piece]:
    """Leave out near-empty pieces (headings without text) and pieces whose text a kept piece of the same
    doc_type already has; set each kept piece's doc_type (doc_type_of(piece)); file_key(piece) names its file."""
    stats = stats if stats is not None else collections.Counter()
    kept: list[pc.Piece] = []
    for piece in pieces:
        if pc.near_empty(piece.body):
            stats["near-empty left out"] += 1
            continue
        doc_type = doc_type_of(piece)
        if seen.taken(doc_type, piece.text):
            stats["duplicates left out"] += 1
            continue
        seen.add(doc_type, piece.text, file_key(piece))
        piece.fields.setdefault("doc_type", doc_type)
        kept.append(piece)
    return kept


# ------------------------------------------------------------------------------------------------ writing


def _old_embedding_input(row: dict) -> str:
    return passage_text(row["source_path"], row["heading"], pc.embedded_text(row["text"], row.get("structured_metadata")))


def vectors_for(inputs: list[str], old_rows: list[dict]) -> tuple[dict[str, list[float]], int, int]:
    """A vector for every embedding input: an old row's when it embedded the same text (semantic vectors only:
    a hash vector was made of other lines), else a new one. Returns (vectors, embedded, kept)."""
    vectors: dict[str, list[float]] = {}
    if uses_semantic() and old_rows:
        by_input = {_old_embedding_input(r): r["id"] for r in old_rows}
        reuse = {text: by_input[text] for text in inputs if text in by_input}
        if reuse:
            by_id = dict(SourceChunk.objects.filter(id__in=list(reuse.values())).values_list("id", "embedding_vector"))
            vectors = {text: by_id[i] for text, i in reuse.items()}
    kept = sum(text in vectors for text in inputs)
    missing = list(dict.fromkeys(text for text in inputs if text not in vectors))
    for start in range(0, len(missing), EMBED_SLICE):
        batch = missing[start : start + EMBED_SLICE]
        vectors.update(zip(batch, build_text_embeddings_batch(batch)))
    return vectors, len(missing), kept


OLD_ROW_FIELDS = ("id", "chunk_id", "text", "heading", "source_path", "doc_type", "chunk_type", "commit_sha", "label",
                  "standards_scope", "structured_metadata")


def piece_records(repository_url: str, pieces: list[pc.Piece], vectors: dict, *, chunk_type: str, commit_sha: str,
                  repository_file: bool, label: str = "", standards_scope: list[str] | None = None) -> list[SourceChunk]:
    """Rows of a file's kept pieces, in file order. A repository file's rows get scope and quality as
    index_repository gives a chunk; a harvested document's rows take label and quality from the piece."""
    from helpdesk.services.index_builder import build_chunk_id, compute_chunk_quality, infer_scope

    records = []
    for seq, piece in enumerate(pieces):
        fields = dict(piece.fields)
        doc_type = fields.pop("doc_type")
        metadata = dict(fields.pop("structured_metadata", {}) or {})
        metadata[pc.META_KEY] = piece.metadata(seq)
        text = piece.text
        if repository_file:
            scope = infer_scope(piece.source_path, piece.body, repository_url)
            quality = compute_chunk_quality(source_path=piece.source_path, chunk_text=text, chunk_type=chunk_type,
                                            heading=piece.heading, doc_type=doc_type, standards_scope=scope)
            row_label = label or piece.source_path
        else:
            scope = list(standards_scope or [])
            quality = fields.pop("quality_score")
            row_label = fields.pop("label", label)
        records.append(
            SourceChunk(
                repository_url=repository_url,
                commit_sha=commit_sha,
                source_path=piece.source_path,
                chunk_id=build_chunk_id(repository_url, piece.source_path, seq, text),
                label=row_label,
                text=text,
                standards_scope=scope,
                quality_score=quality,
                chunk_type=chunk_type,
                doc_type=doc_type,
                heading=piece.heading,
                structured_metadata=metadata,
                embedding_vector=vectors[piece.embedding_input()],
                alternate_vector=None,
            )
        )
    return records


def replace_rows(old_ids: list[int], records: list[SourceChunk]) -> None:
    """Replace a file's rows in one transaction (the new rows are embedded already), in file order."""
    with transaction.atomic():
        SourceChunk.objects.filter(id__in=old_ids).delete()
        SourceChunk.objects.bulk_create(records, batch_size=500)


def write_pieces(repository_url: str, old_rows: list[dict], pieces: list[pc.Piece], *, chunk_type: str, commit_sha: str,
                 repository_file: bool, label: str = "", standards_scope: list[str] | None = None, stats=None) -> list[SourceChunk]:
    """Embed a file's kept pieces (keeping the vector of an old row with the same embedded text) and replace
    its old rows with them. Returns the new rows."""
    vectors, embedded, kept = vectors_for([p.embedding_input() for p in pieces], old_rows)
    if stats is not None:
        stats["embedded"] += embedded
        stats["vectors kept"] += kept
    records = piece_records(repository_url, pieces, vectors, chunk_type=chunk_type, commit_sha=commit_sha,
                            repository_file=repository_file, label=label, standards_scope=standards_scope)
    replace_rows([r["id"] for r in old_rows], records)
    return records


# ------------------------------------------------------------------------------------------------ the indexers


def index_repository_file(repository_url: str, path: str, raw: str, commit_sha: str, *, counter: pc.TokenCounter,
                          seen: SeenPieces) -> list[SourceChunk] | None:
    """index_repository's path for a file of the prepared cut: cut, embed, replace. None when the file cannot be
    cut by structure (the caller then cuts it as before)."""
    example = is_example_path(path)
    counter.clear()
    result = repository_file_cut(raw, path, example=example, counter=counter)
    if result is None:
        return None
    pieces, chunk_type = result
    from helpdesk.services.index_builder import infer_doc_type

    seen.forget(repository_url, path)
    kept = keep_pieces(pieces, seen=seen, file_key=lambda p: SeenPieces.file_key(repository_url, p.source_path),
                       doc_type_of=lambda p: infer_doc_type(p.source_path, chunk_type, p.heading, p.body))
    old_rows = list(SourceChunk.objects.filter(repository_url=repository_url, source_path=path).values(*OLD_ROW_FIELDS))
    return write_pieces(repository_url, old_rows, kept, chunk_type=chunk_type, commit_sha=commit_sha,
                        repository_file=True, label=path)


def harvested_document(repository_url: str, doc_type: str, units, *, commit_sha: str, standards_scope: list[str]) -> int | None:
    """For a harvester: when the document is of the prepared cut (document_version), cut it with units() and
    write it; returns its number of rows. None when the document keeps the cut of before (the harvester's own)."""
    if document_version(repository_url, doc_type) != pc.CUT_VERSION:
        return None
    return len(index_harvested_document(repository_url, units(), doc_type=doc_type, commit_sha=commit_sha,
                                        standards_scope=standards_scope))


def index_harvested_document(repository_url: str, units: list[pc.Unit], *, doc_type: str, commit_sha: str,
                             standards_scope: list[str], counter: pc.TokenCounter | None = None,
                             seen: SeenPieces | None = None) -> list[SourceChunk]:
    """A harvested document's path for the prepared cut (the harvesters call it when document_version says so)."""
    counter = counter or pc.TokenCounter()
    seen = seen or SeenPieces(load=True)
    counter.clear()
    pieces = pack(units, counter)
    seen.forget(repository_url)
    kept = keep_pieces(pieces, seen=seen, file_key=lambda p: SeenPieces.file_key(repository_url, p.source_path),
                       doc_type_of=lambda p: doc_type)
    old_rows = list(SourceChunk.objects.filter(repository_url=repository_url).values(*OLD_ROW_FIELDS))
    return write_pieces(repository_url, old_rows, kept, chunk_type="prose", commit_sha=commit_sha,
                        repository_file=False, standards_scope=standards_scope)
