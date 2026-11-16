"""
Cut every indexed source again with the prepared cut (services/prepared_cut.py), in a database named on the
command line.

For step 1 of docs/plans/2026-11-15-sources-prepared-for-semantic-search.md: the cut is measured on a copy of
the dev database before any index is changed. The command refuses to run unless --database names the database
Django is connected to.

For each indexed file it reads the local source (repository checkouts given with --checkout; the snapshots in
docs/ for EU legislation, NAPCORE, DATEX II and INSPIRE), checks that today's cut of that source gives exactly
the indexed chunks (so only the cut changes, not the content; a file that differs is left as it is and
counted), cuts it anew, leaves out near-empty pieces and exact duplicates, embeds the pieces whose embedded text
is new (a piece whose embedded text equals an indexed chunk's keeps that vector) and replaces the file's chunks
in one transaction. A file already cut this way is skipped, so a stopped run can be started again. With --recut
a file already cut is cut again with today's cut and replaced only when its pieces change (a repair of the cut
applied to a copy built before it); --kinds limits it to the kinds the repair is for.

    python manage.py prepare_index --database napcore_helpdesk_copy \
        --checkout https://github.com/TransmodelEcosystem/NeTEx=/path/to/NeTEx ... [--dry-run] [--report out.json]

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-11-16  |  Modified: 2026-11-16
"""

from __future__ import annotations

import collections
import json
import re
import statistics
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from helpdesk.models import SourceChunk
from helpdesk.services import prepared_cut as pc
from helpdesk.services.embeddings import build_text_embeddings_batch, passage_text
from helpdesk.services.index_builder import (
    build_chunk_id,
    compute_chunk_quality,
    enrich_xml_example_text,
    extract_xsd_structured_metadata,
    infer_doc_type,
    infer_scope,
    split_structured,
)

EMBED_SLICE = 256  # pieces per call of build_text_embeddings_batch (it sends SERVICE_BATCH_SIZE per request)


class Job:
    """One file of the index (or one harvested document): its rows, how today's cut is reproduced, the new cut."""

    def __init__(self, kind: str, repository_url: str, source_paths: list[str] | None, reproduce, cut):
        self.kind = kind
        self.repository_url = repository_url
        self.source_paths = source_paths  # None: every row of the repository URL
        self.reproduce = reproduce  # () -> list of texts of today's cut
        self.cut = cut  # (counter) -> (pieces, rows fields) or None when the file keeps its cut

    def rows(self):
        rows = SourceChunk.objects.filter(repository_url=self.repository_url)
        if self.source_paths is not None:
            rows = rows.filter(source_path__in=self.source_paths)
        return rows.order_by("id")


def _heuristic_inside(kind: str, body: str) -> bool:
    """The audit's check whether a piece begins or ends inside a unit, from its text alone (an upper bound)."""
    text = body.strip()
    if not text:
        return False
    if kind.endswith(".xml"):
        return not (text.startswith("<") and text.endswith(">"))
    return text[0].islower() or not re.search(r"[.!?:;)\]\"'”’>]$", text)


class Command(BaseCommand):
    help = "Cut every indexed source again with the prepared cut, in the named database (plan step 1)."

    def add_arguments(self, parser):
        parser.add_argument("--database", required=True, help="Name of the database to write; must be the connected one.")
        parser.add_argument("--checkout", action="append", default=[], help="REPO_URL=PATH, once per repository.")
        parser.add_argument("--dry-run", action="store_true", help="Cut and count; write nothing.")
        parser.add_argument("--report", default="", help="Write the statistics per kind to this JSON file.")
        parser.add_argument("--kinds", default="", help="Only these kinds (comma-separated), for trials.")
        parser.add_argument("--max-files", type=int, default=0, help="Only this many files per kind, for trials.")
        parser.add_argument(
            "--recut", action="store_true",
            help="Cut files already cut again with today's cut; a file whose pieces stay the same is left as it is.",
        )

    # ------------------------------------------------------------------------------------------- jobs

    def _repository_jobs(self, roots: dict[str, Path]) -> list[Job]:
        jobs = []
        files = (
            SourceChunk.objects.filter(repository_url__in=list(roots))
            .values_list("repository_url", "source_path", "doc_type")
            .order_by("repository_url", "source_path")
            .distinct()
        )
        doc_types: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        for repo, path, doc_type in files:
            doc_types[(repo, path)].add(doc_type)
        for (repo, path), types in sorted(doc_types.items()):
            file = roots[repo] / path
            suffix = Path(path).suffix.lower()
            example = "example" in types
            kind = f"{'example' if example else sorted(types)[0]} {suffix}"
            jobs.append(Job(kind, repo, [path], self._repo_reproduce(file, path), self._repo_cut(file, repo, path, suffix, example)))
        return jobs

    @staticmethod
    def _read(file: Path) -> str | None:
        return file.read_text(encoding="utf-8", errors="ignore") if file.is_file() else None

    def _repo_reproduce(self, file: Path, path: str):
        def reproduce():
            raw = self._read(file)
            if raw is None:
                return None
            texts = []
            for text, chunk_type, heading in split_structured(raw, file.suffix, chunk_size=1200, chunk_overlap=200, source_name=path):
                if path.lower().endswith(".xml") and infer_doc_type(path, chunk_type, heading, text) == "example":
                    text = enrich_xml_example_text(chunk_text=text, source_path=path)
                texts.append(text)
            return texts

        return reproduce

    def _repo_cut(self, file: Path, repo: str, path: str, suffix: str, example: bool):
        def cut(counter: pc.TokenCounter):
            raw = self._read(file)
            if raw is None:
                return None
            chunk_type = "prose"
            units = None
            if suffix == ".xml":
                summary = (lambda body: enrich_xml_example_text(chunk_text=body, source_path=path)[len(body):]) if example else None
                try:
                    pieces, info = pc.cut_xml(raw, path, "", counter, unit=path, summary=summary)
                except ValueError:
                    return None
                self.xml_info[f"{'example' if example else 'schema'} .xml"].append(info)
                return pieces, "schema_fragment"
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
            return self._pack(units, counter), chunk_type

        return cut

    def _harvested_jobs(self) -> list[Job]:
        from helpdesk.services import datex, inspire, napcore_site, regulations

        jobs = []
        for act in regulations.ACTS:
            jobs.append(
                Job(
                    "regulation", act.url, None,
                    lambda act=act: [r["text"] for r in regulations._chunk_records(act, regulations.select_sections(act, regulations.parse_act(act.path.read_bytes())))],
                    lambda counter, act=act: (self._pack(pc.act_units(act), counter), "prose"),
                )
            )
        for path in sorted(napcore_site.TEXT_DIR.glob("*.md")):
            snapshot = napcore_site.read_snapshot(path)
            jobs.append(
                Job(
                    "napcore", snapshot.url, None,
                    lambda s=snapshot: [r["text"] for r in napcore_site.chunk_records(s)],
                    lambda counter, s=snapshot: (self._pack(pc.napcore_units(s), counter), "prose"),
                )
            )
        model = json.loads(datex.MODEL_PATH.read_text(encoding="utf-8"))
        jobs.append(
            Job(
                "datex model", datex.MODEL_PAGE_URL, None,
                lambda: [r["text"] for r in datex.model_records(model)],
                lambda counter: (self._pack(pc.datex_model_units(model), counter), "prose"),
            )
        )
        for path in sorted(datex.PAGES_DIR.glob("*.md")):
            snapshot = datex.read_snapshot(path)
            jobs.append(
                Job(
                    "datex page", snapshot.url, None,
                    lambda s=snapshot: [r["text"] for r in datex.page_records(s)],
                    lambda counter, s=snapshot: (self._pack(pc.datex_page_units(s), counter), "prose"),
                )
            )
        spec = inspire.SPEC_PATH.read_text(encoding="utf-8")
        jobs.append(
            Job(
                "inspire spec", inspire.spec_url(), None,
                lambda: [r["text"] for r in inspire.spec_records(spec)],
                lambda counter: (self._pack(pc.inspire_spec_units(spec), counter), "prose"),
            )
        )
        codelists = inspire.read_codelists()
        jobs.append(
            Job(
                "inspire codelist", inspire.REGISTRY_URL, None,
                lambda: [r["text"] for r in inspire.codelist_records(codelists)],
                lambda counter: (self._pack(pc.inspire_codelist_units(codelists), counter), "prose"),
            )
        )
        return jobs

    @staticmethod
    def _pack(units: list[pc.Unit], counter: pc.TokenCounter) -> list[pc.Piece]:
        # One request counts every whole unit of the file first; most units fit whole.
        counter.counts([passage_text(u.source_path, u.heading, u.head + u.joiner.join(b for b in u.blocks if b.strip())) for u in units])
        pieces = []
        for unit in units:
            pieces.extend(pc.pack_unit(unit, counter))
        return pieces

    # ------------------------------------------------------------------------------------------- run

    def handle(self, *args, **options):
        connected = connection.settings_dict["NAME"]
        self.stdout.write(f"connected to database {connected}")
        if options["database"] != connected:
            raise CommandError(f"--database {options['database']} is not the connected database {connected}.")
        roots = {}
        for item in options["checkout"]:
            url, _, path = item.partition("=")
            roots[url.rstrip("/")] = Path(path)
        dry = options["dry_run"]
        kinds = {k.strip() for k in options["kinds"].split(",") if k.strip()}
        self.xml_info: dict[str, list[dict]] = collections.defaultdict(list)

        jobs = self._repository_jobs(roots) + self._harvested_jobs()
        if kinds:
            jobs = [j for j in jobs if j.kind in kinds]
        if options["max_files"]:
            per_kind = collections.Counter()
            limited = []
            for job in jobs:
                per_kind[job.kind] += 1
                if per_kind[job.kind] <= options["max_files"]:
                    limited.append(job)
            jobs = limited

        counter = pc.TokenCounter()
        limit = counter.ensure_limit()
        self.stdout.write(f"{len(jobs)} files; the embedder reads {limit} tokens")
        stats: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        tokens: dict[str, list[int]] = collections.defaultdict(list)
        seen: dict[str, set[str]] = collections.defaultdict(set)
        started = time.monotonic()
        embedded_total = 0

        for number, job in enumerate(jobs, 1):
            kind = job.kind
            rows = list(job.rows().values("id", "chunk_id", "text", "heading", "source_path", "doc_type", "chunk_type",
                                          "commit_sha", "label", "standards_scope", "structured_metadata"))
            stats[kind]["files"] += 1
            stats[kind]["old rows"] += len(rows)
            if not rows:
                stats[kind]["no rows"] += 1
                continue
            already_cut = all((r["structured_metadata"] or {}).get(pc.META_KEY, {}).get("v") == pc.CUT_VERSION for r in rows)
            if already_cut and not options["recut"]:
                stats[kind]["already cut"] += 1
                for r in rows:
                    seen[r["doc_type"]].add(r["text"])
                continue
            # A file cut before was checked against its source then; its rows no longer hold the old cut to
            # check against again.
            if not already_cut:
                today = job.reproduce()
                if today is None or collections.Counter(today) != collections.Counter(r["text"] for r in rows):
                    stats[kind]["not covered: source differs from the index"] += 1
                    stats[kind]["rows kept as they are"] += len(rows)
                    continue
            counter.clear()
            result = job.cut(counter)
            if result is None:
                stats[kind]["not covered: cannot be cut by structure"] += 1
                stats[kind]["rows kept as they are"] += len(rows)
                continue
            pieces, chunk_type = result
            kept: list[pc.Piece] = []
            first = rows[0]
            for piece in pieces:
                if pc.near_empty(piece.body):
                    stats[kind]["near-empty left out"] += 1
                    continue
                # Of the body: the place line names headings that would read as markers of a kind.
                doc_type = first["doc_type"] if job.source_paths is None else infer_doc_type(
                    piece.source_path, chunk_type, piece.heading, piece.body)
                if piece.text in seen[doc_type]:
                    stats[kind]["duplicates left out"] += 1
                    continue
                seen[doc_type].add(piece.text)
                piece.fields.setdefault("doc_type", doc_type)
                kept.append(piece)
            stats[kind]["new rows"] += len(kept)
            stats[kind]["inside a unit"] += sum(p.inside for p in kept)
            stats[kind]["inside (text heuristic)"] += sum(_heuristic_inside(kind, p.body) for p in kept)
            stats[kind]["over the limit"] += sum(p.tokens > limit for p in kept)
            tokens[kind].extend(p.tokens for p in kept)
            if already_cut:
                if collections.Counter(p.text for p in kept) == collections.Counter(r["text"] for r in rows):
                    stats[kind]["cut again, unchanged"] += 1
                    continue
                stats[kind]["cut again, changed"] += 1
                stats[kind]["rows of changed files before"] += len(rows)
                stats[kind]["rows of changed files after"] += len(kept)
            if dry:
                if number % 50 == 0:
                    self.stdout.write(f"{number}/{len(jobs)} files, {time.monotonic() - started:.0f} s")
                continue
            embedded_total += self._write(job, rows, kept, chunk_type, stats[kind])
            elapsed = time.monotonic() - started
            if number % 20 == 0 or len(kept) > 500:
                self.stdout.write(
                    f"{number}/{len(jobs)} files ({kind}), {embedded_total} embedded, {elapsed:.0f} s, "
                    f"{embedded_total / max(elapsed, 1e-9):.1f} pieces/s"
                )

        report = {"limit": limit, "seconds": round(time.monotonic() - started), "countRequests": counter.requests,
                  "embedded": embedded_total, "kinds": {}}
        for kind in sorted(stats):
            counts = sorted(tokens[kind])
            entry = dict(stats[kind])
            if counts:
                entry["tokens median"] = statistics.median(counts)
                entry["tokens p90"] = counts[int(0.9 * (len(counts) - 1))]
                entry["tokens max"] = counts[-1]
                entry["share over the limit"] = round(entry.get("over the limit", 0) / len(counts), 4)
                entry["share inside a unit"] = round(entry.get("inside a unit", 0) / len(counts), 4)
                entry["share inside (text heuristic)"] = round(entry.get("inside (text heuristic)", 0) / len(counts), 4)
            if self.xml_info.get(kind):
                info = self.xml_info[kind]
                entry["xml rounds > 1"] = sum(i["rounds"] > 1 for i in info)
                entry["xml margin max"] = max(i["margin"] for i in info)
            report["kinds"][kind] = entry
        report["rows before"] = sum(s["old rows"] for s in stats.values())
        report["rows after"] = sum(s["new rows"] + s["rows kept as they are"] + (s["old rows"] if s["already cut"] else 0)
                                   for s in stats.values())
        text = json.dumps(report, indent=1, ensure_ascii=False)
        if options["report"]:
            Path(options["report"]).write_text(text + "\n", encoding="utf-8")
        self.stdout.write(text)

    def _write(self, job: Job, rows: list[dict], pieces: list[pc.Piece], chunk_type: str, stats) -> int:
        """Replace the job's rows by its pieces in one transaction; returns the number of pieces embedded."""
        first = rows[0]
        old_vectors = {passage_text(r["source_path"], r["heading"], r["text"]): r["id"] for r in rows}
        reuse = {p.embedding_input(): old_vectors[p.embedding_input()] for p in pieces if p.embedding_input() in old_vectors}
        vectors = {}
        if reuse:
            by_id = dict(SourceChunk.objects.filter(id__in=list(reuse.values())).values_list("id", "embedding_vector"))
            vectors = {text: by_id[i] for text, i in reuse.items()}
        missing = [p.embedding_input() for p in pieces if p.embedding_input() not in vectors]
        missing = list(dict.fromkeys(missing))
        for start in range(0, len(missing), EMBED_SLICE):
            batch = missing[start : start + EMBED_SLICE]
            vectors.update(zip(batch, build_text_embeddings_batch(batch)))
        stats["vectors kept"] += sum(p.embedding_input() in reuse for p in pieces)
        records = []
        for seq, piece in enumerate(pieces):
            fields = dict(piece.fields)
            doc_type = fields.pop("doc_type")
            metadata = dict(fields.pop("structured_metadata", {}) or {})
            metadata[pc.META_KEY] = piece.metadata(seq)
            text = piece.text
            if job.source_paths is not None:  # a repository file: as index_repository makes a chunk
                scope = infer_scope(piece.source_path, piece.body, job.repository_url)
                quality = compute_chunk_quality(source_path=piece.source_path, chunk_text=text, chunk_type=chunk_type,
                                                heading=piece.heading, doc_type=doc_type, standards_scope=scope)
                label = first["label"] or piece.source_path
            else:
                scope = first["standards_scope"]
                quality = fields.pop("quality_score")
                label = fields.pop("label", first["label"])
            records.append(
                SourceChunk(
                    repository_url=job.repository_url,
                    commit_sha=first["commit_sha"],
                    source_path=piece.source_path,
                    chunk_id=build_chunk_id(job.repository_url, piece.source_path, seq, text),
                    label=label,
                    text=text,
                    standards_scope=scope,
                    quality_score=quality,
                    chunk_type=first["chunk_type"] if job.source_paths is None else chunk_type,
                    doc_type=doc_type,
                    heading=piece.heading,
                    structured_metadata=metadata,
                    embedding_vector=vectors[piece.embedding_input()],
                    alternate_vector=None,
                )
            )
        with transaction.atomic():
            SourceChunk.objects.filter(id__in=[r["id"] for r in rows]).delete()
            # In file order, so primary keys follow the order of the pieces.
            SourceChunk.objects.bulk_create(records, batch_size=500)
        return len(missing)
