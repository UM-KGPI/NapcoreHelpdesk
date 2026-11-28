"""
Change the cut of the indexed files, in a database named on the command line: the re-index of the plan
an internal plan (kept outside the repository) (step 5; steps 1 and the repair used it on copies).

--cut-version 1 (the default) cuts every file with the prepared cut (services/prepared_cut.py); --cut-version 0 cuts every
file back with the cut of before (index_builder.split_structured, the harvesters' record builders). Each row
stores the cut that made it (services/prepared_index.py), and the indexers keep a file's cut on every refresh,
so this command is the only thing that changes it.

For each indexed file it reads the local source (repository checkouts given with --checkout, at the indexed
commits; the snapshots in docs/ for EU legislation, NAPCORE, DATEX II and INSPIRE). A file of the cut of before
is first checked: today's cut of before of its source must give exactly its rows (so only the cut changes, not
the content); a file that differs is left as it is and counted. Then the file is cut with the asked version,
near-empty pieces and exact duplicates are left out (prepared cut), the pieces whose embedded text is new are
embedded (a piece whose embedded text equals one of the file's rows keeps that vector) and only then are the
file's rows replaced, in one transaction: the search never sees a file without rows. A file already at the asked
version is skipped, so a stopped run is started again with the same command. With --recut a file already of the
prepared cut is cut again with today's prepared cut and replaced only when its pieces change (a repair of the
cut); --kinds limits a run to some kinds.

    python manage.py prepare_index --database napcore_helpdesk_copy [--cut-version 1] \
        --checkout https://github.com/TransmodelEcosystem/NeTEx=/path/to/NeTEx ... [--dry-run] [--report out.json]

The command refuses to run unless --database names the database Django is connected to.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Created: 2026-11-16  |  Modified: 2026-11-18
"""

from __future__ import annotations

import collections
import json
import re
import statistics
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from helpdesk.models import IndexedSourceFile, SourceChunk
from helpdesk.services import prepared_cut as pc
from helpdesk.services import prepared_index as pi
from helpdesk.services.index_builder import (
    build_chunk_embedding_text,
    enrich_xml_example_text,
    infer_doc_type,
    old_cut_chunks,
    split_structured,
)


class Job:
    """One file of the index (or one harvested document): its rows, how today's cut of before is reproduced, the
    prepared cut, and the rows of the cut of before."""

    def __init__(self, kind: str, repository_url: str, source_paths: list[str] | None, reproduce, cut, old, defaults=None):
        self.kind = kind
        self.repository_url = repository_url
        self.source_paths = source_paths  # None: every row of the repository URL (a harvested document)
        self.reproduce = reproduce  # () -> list of texts of today's cut of before, None when the source is missing
        self.cut = cut  # (counter) -> (pieces, chunk_type) or None when the file cannot be cut by structure
        self.old = old  # () -> list of (row fields, embedding input) of the cut of before, None when missing
        self.defaults = defaults or {}  # row fields of a harvested document (doc_type, standards_scope)

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


def _harvested_old(records_of, *, doc_type: str, embedding_scope: list[str], url: str):
    """The rows of the cut of before of a harvested document, as its harvester writes them."""

    def old():
        rows = []
        for record in records_of():
            embedding_input = build_chunk_embedding_text(
                chunk_text=record["text"], doc_type=doc_type, chunk_type="prose", heading=record["heading"],
                standards_scope=embedding_scope, repository_url=url, source_path=record["source_path"],
            )
            rows.append((dict(record), embedding_input))
        return rows

    return old


class Command(BaseCommand):
    help = "Change the cut of the indexed files to --cut-version (1: the prepared cut, 0: the cut of before), in the named database."

    def add_arguments(self, parser):
        parser.add_argument("--database", required=True, help="Name of the database to write; must be the connected one.")
        parser.add_argument("--checkout", action="append", default=[], help="REPO_URL=PATH, once per repository.")
        parser.add_argument(
            "--cut-version", type=int, default=pc.CUT_VERSION, choices=list(pi.VERSIONS),
            help=f"The cut to bring every file to: {pc.CUT_VERSION} the prepared cut (default), 0 the cut of before.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Cut and count; write nothing.")
        parser.add_argument("--report", default="", help="Write the statistics per kind to this JSON file.")
        parser.add_argument("--files-report", default="", help="Write the rows before and after of every file to this JSON file.")
        parser.add_argument("--kinds", default="", help="Only these kinds (comma-separated), for trials.")
        parser.add_argument("--max-files", type=int, default=0, help="Only this many files per kind, for trials.")
        parser.add_argument("--stop-after", type=int, default=0, help="Stop after writing this many files (to try a restart).")
        parser.add_argument(
            "--recut", action="store_true",
            help="Cut files already of the prepared cut again with today's cut; a file whose pieces stay the same is left as it is.",
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
        # A file the indexer recorded but without rows: every piece of it was a copy of another file's. It is
        # still a file of the index (the way back gives it its rows again).
        for repo, path in IndexedSourceFile.objects.filter(repository_url__in=list(roots)).values_list("repository_url", "source_path"):
            if (repo, path) not in doc_types and not path.startswith("issues/"):
                doc_types[(repo, path)].add(infer_doc_type(path, "prose", "", ""))
        for (repo, path), types in sorted(doc_types.items()):
            file = roots[repo] / path
            suffix = Path(path).suffix.lower()
            example = "example" in types
            kind = f"{'example' if example else sorted(types)[0]} {suffix}"
            jobs.append(Job(kind, repo, [path], self._repo_reproduce(file, path), self._repo_cut(file, path, example),
                            self._repo_old(file, repo, path)))
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

    def _repo_cut(self, file: Path, path: str, example: bool):
        def cut(counter: pc.TokenCounter):
            raw = self._read(file)
            if raw is None:
                return None
            suffix = Path(path).suffix.lower()
            info = self.xml_info[f"{'example' if example else 'schema'} .xml"] if suffix == ".xml" else None
            return pi.repository_file_cut(raw, path, example=example, counter=counter, xml_info=info)

        return cut

    def _repo_old(self, file: Path, repo: str, path: str):
        def old():
            raw = self._read(file)
            if raw is None:
                return None
            records, inputs = old_cut_chunks(raw, file.suffix, path, repo)
            rows = []
            for record, embedding_input in zip(records, inputs):
                rows.append(({
                    "chunk_id": record["chunk_id"], "source_path": path, "label": path, "text": record["chunk_text"],
                    "standards_scope": record["standards_scope"], "quality_score": record["quality_score"],
                    "chunk_type": record["chunk_type"], "doc_type": record["doc_type"], "heading": record["heading"],
                    "structured_metadata": record["structured_metadata"],
                }, embedding_input))
            return rows

        return old

    def _harvested_jobs(self) -> list[Job]:
        from helpdesk.services import datex, inspire, napcore_site, regulations

        jobs = []

        def add(kind, url, records_of, units_of, doc_type, scope):
            jobs.append(
                Job(
                    kind, url, None,
                    lambda: [r["text"] for r in records_of()],
                    lambda counter: (pi.pack(units_of(), counter), "prose"),
                    _harvested_old(records_of, doc_type=doc_type, embedding_scope=[scope], url=url),
                    {"doc_type": doc_type, "standards_scope": [scope]},
                )
            )

        for act in regulations.ACTS:
            add("regulation", act.url,
                lambda act=act: regulations._chunk_records(act, regulations.select_sections(act, regulations.parse_act(act.path.read_bytes()))),
                lambda act=act: pc.act_units(act), "regulation", regulations.SCOPE)
        for path in sorted(napcore_site.TEXT_DIR.glob("*.md")):
            snapshot = napcore_site.read_snapshot(path)
            add("napcore", snapshot.url, lambda s=snapshot: napcore_site.chunk_records(s), lambda s=snapshot: pc.napcore_units(s),
                napcore_site.DOC_TYPE, napcore_site.SCOPE)
        model = json.loads(datex.MODEL_PATH.read_text(encoding="utf-8"))
        add("datex model", datex.MODEL_PAGE_URL, lambda: datex.model_records(model), lambda: pc.datex_model_units(model),
            datex.DOC_TYPE, datex.SCOPE)
        for path in sorted(datex.PAGES_DIR.glob("*.md")):
            snapshot = datex.read_snapshot(path)
            add("datex page", snapshot.url, lambda s=snapshot: datex.page_records(s), lambda s=snapshot: pc.datex_page_units(s),
                datex.DOC_TYPE, datex.SCOPE)
        spec = inspire.SPEC_PATH.read_text(encoding="utf-8")
        add("inspire spec", inspire.spec_url(), lambda: inspire.spec_records(spec), lambda: pc.inspire_spec_units(spec),
            inspire.DOC_TYPE, inspire.SCOPE)
        codelists = inspire.read_codelists()
        add("inspire codelist", inspire.REGISTRY_URL, lambda: inspire.codelist_records(codelists),
            lambda: pc.inspire_codelist_units(codelists), inspire.DOC_TYPE, inspire.SCOPE)
        return jobs

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
        target = options["cut_version"]
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
        limit = counter.ensure_limit() if target == pc.CUT_VERSION else 0
        self.stdout.write(f"{len(jobs)} files; version {target}" + (f"; the embedder reads {limit} tokens" if limit else ""))
        stats: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        tokens: dict[str, list[int]] = collections.defaultdict(list)
        files_report: dict[str, dict] = {}
        # Duplicates are left out as files go, in the order of the jobs: a file already cut keeps its pieces' texts.
        seen = pi.SeenPieces(load=False)
        started = time.monotonic()
        embedded_total = 0
        written = 0

        for number, job in enumerate(jobs, 1):
            kind = job.kind
            rows = list(job.rows().values(*pi.OLD_ROW_FIELDS))
            stats[kind]["files"] += 1
            stats[kind]["old rows"] += len(rows)
            file_name = f"{job.repository_url}|{job.source_paths[0] if job.source_paths else ''}"
            if not rows and not (job.source_paths is not None
                                 or IndexedSourceFile.objects.filter(repository_url=job.repository_url).exists()):
                stats[kind]["not indexed"] += 1  # a snapshot in docs/ whose document was never indexed
                continue
            if not rows:
                stats[kind]["no rows (all pieces copies)"] += 1
            versions = {pi.row_version(r["structured_metadata"]) for r in rows}
            current = versions.pop() if len(versions) == 1 else None
            if current == target and not (options["recut"] and target == pc.CUT_VERSION):
                stats[kind]["already at the version"] += 1
                if target == pc.CUT_VERSION:
                    for r in rows:
                        seen.add(r["doc_type"], r["text"], pi.SeenPieces.file_key(job.repository_url, r["source_path"]))
                files_report[file_name] = {"kind": kind, "before": len(rows), "after": len(rows), "status": "at the version"}
                continue
            # A file of the cut of before is checked against its source: only the cut may change, not the content.
            if current == pi.OLD_CUT:
                today = job.reproduce()
                if today is None or collections.Counter(today) != collections.Counter(r["text"] for r in rows):
                    stats[kind]["not covered: source differs from the index"] += 1
                    stats[kind]["rows kept as they are"] += len(rows)
                    files_report[file_name] = {"kind": kind, "before": len(rows), "after": len(rows), "status": "source differs"}
                    continue
            if target == pc.CUT_VERSION:
                result = self._prepared(job, rows, counter, seen, stats[kind], tokens[kind], limit, recut=current == target)
            else:
                result = self._old(job, rows)
            if result is None:
                stats[kind]["not covered: cannot be cut by structure"] += 1
                stats[kind]["rows kept as they are"] += len(rows)
                files_report[file_name] = {"kind": kind, "before": len(rows), "after": len(rows), "status": "cannot be cut"}
                continue
            if result == "unchanged":
                files_report[file_name] = {"kind": kind, "before": len(rows), "after": len(rows), "status": "cut again, unchanged"}
                continue
            write, new_rows = result
            stats[kind]["new rows"] += new_rows
            files_report[file_name] = {"kind": kind, "before": len(rows), "after": new_rows, "status": "dry" if dry else "written"}
            if dry:
                if number % 50 == 0:
                    self.stdout.write(f"{number}/{len(jobs)} files, {time.monotonic() - started:.0f} s")
                continue
            embedded_total += write()
            written += 1
            elapsed = time.monotonic() - started
            if number % 20 == 0 or new_rows > 500:
                self.stdout.write(
                    f"{number}/{len(jobs)} files ({kind}), {embedded_total} embedded, {elapsed:.0f} s, "
                    f"{embedded_total / max(elapsed, 1e-9):.1f} pieces/s"
                )
            if options["stop_after"] and written >= options["stop_after"]:
                self.stdout.write(f"stopped after {written} files written, as asked")
                break

        report = {"version": target, "limit": limit, "seconds": round(time.monotonic() - started),
                  "countRequests": counter.requests, "embedded": embedded_total, "kinds": {}}
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
        report["rows after"] = sum(f["after"] for f in files_report.values())
        text = json.dumps(report, indent=1, ensure_ascii=False)
        if options["report"]:
            Path(options["report"]).write_text(text + "\n", encoding="utf-8")
        if options["files_report"]:
            Path(options["files_report"]).write_text(json.dumps(files_report, indent=0, ensure_ascii=False) + "\n", encoding="utf-8")
        self.stdout.write(text)

    @staticmethod
    def _first_of(job: Job) -> dict:
        """Row fields of a file without rows, from what the indexer recorded for it."""
        indexed = IndexedSourceFile.objects.filter(repository_url=job.repository_url).order_by("id")
        if job.source_paths is not None:
            indexed = indexed.filter(source_path=job.source_paths[0])
        recorded = indexed.first()
        commit = recorded.commit_sha if recorded else ""
        return {"doc_type": "", "chunk_type": "prose", "commit_sha": commit, "label": "", "standards_scope": [],
                **job.defaults}

    def _prepared(self, job: Job, rows: list[dict], counter, seen, stats, tokens, limit: int, *, recut: bool):
        """The prepared cut of a file: (write, rows after), "unchanged" for a recut that changes nothing, None."""
        counter.clear()
        result = job.cut(counter)
        if result is None:
            return None
        pieces, chunk_type = result
        first = rows[0] if rows else self._first_of(job)
        repository_file = job.source_paths is not None
        # Of the body: the place line names headings that would read as markers of a kind.
        kept = pi.keep_pieces(
            pieces, seen=seen, stats=stats,
            file_key=lambda p: pi.SeenPieces.file_key(job.repository_url, p.source_path),
            doc_type_of=lambda p: infer_doc_type(p.source_path, chunk_type, p.heading, p.body) if repository_file else first["doc_type"],
        )
        stats["inside a unit"] += sum(p.inside for p in kept)
        stats["inside (text heuristic)"] += sum(_heuristic_inside(job.kind, p.body) for p in kept)
        stats["over the limit"] += sum(p.tokens > limit for p in kept)
        tokens.extend(p.tokens for p in kept)
        if recut:
            if collections.Counter(p.text for p in kept) == collections.Counter(r["text"] for r in rows):
                stats["cut again, unchanged"] += 1
                return "unchanged"
            stats["cut again, changed"] += 1
            stats["rows of changed files before"] += len(rows)
            stats["rows of changed files after"] += len(kept)

        def write() -> int:
            before = stats["embedded"]
            pi.write_pieces(
                job.repository_url, rows, kept,
                chunk_type=chunk_type if repository_file else first["chunk_type"],
                commit_sha=first["commit_sha"], repository_file=repository_file,
                label=first["label"] or "", standards_scope=first["standards_scope"], stats=stats,
            )
            return stats["embedded"] - before

        return write, len(kept)

    def _old(self, job: Job, rows: list[dict]):
        """The cut of before of a file (the way back): (write, rows after), or None when its source is missing."""
        old = job.old()
        if old is None:
            return None
        first = rows[0] if rows else self._first_of(job)

        def write() -> int:
            vectors, embedded, _ = pi.vectors_for([text for _, text in old], [])
            records = []
            for fields, embedding_input in old:
                fields = dict(fields)
                records.append(
                    SourceChunk(
                        repository_url=job.repository_url,
                        commit_sha=first["commit_sha"],
                        standards_scope=fields.pop("standards_scope", first["standards_scope"]),
                        chunk_type=fields.pop("chunk_type", first["chunk_type"]),
                        doc_type=fields.pop("doc_type", first["doc_type"]),
                        embedding_vector=vectors[embedding_input],
                        alternate_vector=None,
                        **fields,
                    )
                )
            pi.replace_rows([r["id"] for r in rows], records)
            return embedded

        return write, len(old)
