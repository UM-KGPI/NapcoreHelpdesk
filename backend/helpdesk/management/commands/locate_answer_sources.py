"""Where in the app's retrieval the passage that answers a question is lost.

For each question of a gold file (expected_source_patterns), the question is run as the answer view runs it
(api/views.py: English rendering, scope, retrieval with the view's top_k, min_score and min_results, the
relaxed retry, presence evidence, the example evidence, the cut to LLM_MAX_EVIDENCE_CHUNKS) and the rank of the
wanted source is read at every stage of retrieval through retrieval_gateway.retrieval_probe. Nothing is changed:
the probe only reads the candidates.

The only model call is the English rendering of a non-English question, which the app makes before retrieval
(llm_generator.english_search_query). Renderings are kept in a JSON file (--translations) so a rerun makes no
call; --no-model never calls the model (a question without a stored rendering is searched as asked, as the app
does when translation fails). The example generator runs with the model off: when the app would generate an
example with the model, that path is reported as not reproduced.

docs/plans/2026-11-14-retrieval-misses.md, step Q0.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from helpdesk.models import SourceChunk
from helpdesk.services import retrieval_gateway
from helpdesk.services.retrieval_gateway import retrieval_probe, retrieve_chunks_with_trace

BENCHMARKS = Path(__file__).resolve().parents[2] / "benchmarks"
DEFAULT_INPUT = BENCHMARKS / "answer-source-questions.yaml"

# The stages of one retrieval pass in order (retrieval_gateway._retrieve_chunks_once). Each is a list of
# passages; a passage is lost at the stage after the last one it is in.
PASS_STAGES = ("pool", "preselected", "scored", "min_score", "source_path_cap", "top_k", "coverage", "final")
# Then the whole question: the two passes merged, the scope coverage, the view's additions, the prompt.
QUESTION_STAGES = ("pass", "merged", "returned", "view", "prompt")
# Name of the step that loses a passage absent from a stage (and from every later one).
LOSS_STEP = {
    "pool": "not a candidate",
    "preselected": "preselection cap",
    "scored": "scope filter in scoring",
    "min_score": "min_score",
    "source_path_cap": "per-source-path cap",
    "top_k": "top_k cut (diversification)",
    "coverage": "coverage step",
    "final": "provisions / named examples",
    "merged": "merge of the two searches",
    "returned": "scope coverage",
    "view": "view additions (presence, example evidence)",
    "prompt": "prompt cut (LLM_MAX_EVIDENCE_CHUNKS)",
}
# Candidate generators, reported separately (only those the code has run for the question appear).
GENERATORS = (
    "vector",
    "vector_opt_in",
    "full_text",
    "rare_terms",
    "path_hints",
    "graph_examples",
    "ontology_definitions",
    "element_candidates",
    "graph_candidates",
    "xsd_definitions",
    "relation_paths",
    "provisions",
    "named_examples",
)


def _item_fields(item) -> tuple[str, str, str, float | None]:
    """(repository URL, source path, chunk id, score) of a SourceChunk, a ChunkDict or a chunk dict."""
    if isinstance(item, dict):
        get = item.get
        repo = get("repositoryUrl") or get("repository_url") or ""
        path = get("sourcePath") or get("source_path") or ""
        chunk_id = get("chunkId") or get("chunk_id") or ""
        score = get("_rankScore", get("score"))
    else:
        repo = getattr(item, "repository_url", "") or ""
        path = getattr(item, "source_path", "") or ""
        chunk_id = getattr(item, "chunk_id", "") or ""
        score = getattr(item, "vector_similarity", None)
    return str(repo), str(path), str(chunk_id), (float(score) if score is not None else None)


def source_key(repository_url: str, source_path: str) -> str:
    """What a gold pattern is matched against: "<repository URL>/<source path>$", lower case."""
    return f"{(repository_url or '').rstrip('/')}/{source_path or ''}$".lower()


def matches(patterns: list[str], repository_url: str, source_path: str) -> bool:
    key = source_key(repository_url, source_path)
    return any(pattern.lower() in key for pattern in patterns)


def _snapshot(items) -> list[tuple[str, str, str, float | None]]:
    return [_item_fields(item) for item in list(items or [])]


class StageRecorder:
    """The probe: keeps (repository, path, chunk id, score) of every stage of every retrieval pass."""

    def __init__(self):
        self.passes: list[dict] = []
        self.outer: dict[str, list] = {}

    def __call__(self, stage: str, items) -> None:
        if stage == "begin":
            self.passes.append({"args": dict(items), "query": {}, "stages": {}})
        elif stage == "query":
            self.passes[-1]["query"] = dict(items)
        elif stage in ("merged", "returned"):
            self.outer[stage] = _snapshot(items)
        elif self.passes:
            self.passes[-1]["stages"].setdefault(stage, []).extend(_snapshot(items))


def rank_in(rows: list | None, patterns: list[str]) -> int | None:
    """1-based rank of the first row matching a pattern; None when absent."""
    for index, (repo, path, _chunk_id, _score) in enumerate(rows or [], start=1):
        if matches(patterns, repo, path):
            return index
    return None


def lost_at(presence: list[tuple[str, bool]]) -> str | None:
    """The first stage after the last one the passage is in; None when it is in the last."""
    last = -1
    for index, (_stage, present) in enumerate(presence):
        if present:
            last = index
    if last == len(presence) - 1:
        return None
    return presence[last + 1][0]


def pass_report(recorded: dict, patterns: list[str]) -> dict:
    stages = recorded["stages"]
    generators = {
        name: {"rank": rank_in(stages[name], patterns), "size": len(stages[name])}
        for name in GENERATORS
        if name in stages
    }
    filters = {}
    for name in PASS_STAGES:
        rows = stages.get(name)
        if name == "pool" and rows is not None:
            # Added after scoring (definitions, relation paths, provisions, named examples) counts as a candidate.
            rows = rows + [row for extra in ("xsd_definitions", "relation_paths", "provisions", "named_examples") for row in stages.get(extra, [])]
        filters[name] = {"rank": rank_in(rows, patterns), "size": len(rows) if rows is not None else None}
    # A stage the pass did not reach (no candidates at all) counts as absent.
    presence = [(name, filters[name]["rank"] is not None) for name in PASS_STAGES]
    return {
        "question": recorded["args"].get("question"),
        "scope": recorded["args"].get("scope"),
        "concepts": recorded["query"].get("concepts", []),
        "bridgedConcepts": recorded["query"].get("bridgedConcepts", []),
        "rareTerms": recorded["query"].get("rareTerms", []),
        "generators": generators,
        "stages": filters,
        "rankAfterScoring": rank_in(stages.get("ranked"), patterns),
        "scoredCount": len(stages.get("ranked") or []),
        "lostAt": lost_at(presence),
        "furthest": max((i for i, (_n, p) in enumerate(presence) if p), default=-1),
    }


class SourceIndex:
    """The (id, repository, path, scope) of every indexed chunk, for matching gold patterns."""

    def __init__(self):
        self.rows = list(SourceChunk.objects.values_list("id", "repository_url", "source_path", "standards_scope"))

    def ids(self, patterns: list[str]) -> list[int]:
        return [row[0] for row in self.rows if matches(patterns, row[1], row[2])]

    def per_pattern(self, patterns: list[str]) -> dict[str, dict]:
        found = {}
        for pattern in patterns:
            rows = [row for row in self.rows if matches([pattern], row[1], row[2])]
            found[pattern] = {
                "chunks": len(rows),
                "paths": len({(row[1], row[2]) for row in rows}),
                "scopes": sorted({scope for row in rows for scope in (row[3] or [])}),
            }
        return found


def vector_rank(embedding, wanted_ids: list[int], scope: list[str] | None) -> int | None:
    """Exact rank by cosine similarity of the nearest wanted chunk among the chunks the scope searches
    (scope None: every indexed chunk); None when no wanted chunk is searched or vectors are unavailable."""
    CosineDistance = retrieval_gateway.CosineDistance
    if not embedding or not wanted_ids or CosineDistance is None:
        return None
    base = SourceChunk.objects.all() if scope == "all" else SourceChunk.objects.filter(retrieval_gateway._scope_query_filter(scope))
    nearest = (
        base.filter(id__in=wanted_ids)
        .annotate(distance=CosineDistance("embedding_vector", embedding))
        .order_by("distance")
        .values_list("distance", flat=True)
        .first()
    )
    if nearest is None:
        return None
    return base.annotate(distance=CosineDistance("embedding_vector", embedding)).filter(distance__lt=nearest).count() + 1


class Translations:
    """English renderings of non-English questions, as english_search_query gives them, kept in a file."""

    def __init__(self, path: Path | None, use_model: bool, fresh: bool):
        self.path = path
        self.use_model = use_model
        self.fresh = fresh
        self.stored: dict = {}
        if path and path.exists() and not fresh:
            self.stored = json.loads(path.read_text(encoding="utf-8"))
        self.calls = 0

    def english(self, question: str) -> tuple[str | None, str]:
        if question in self.stored and not self.fresh:
            return self.stored[question], "stored"
        if not self.use_model:
            return None, "not rendered (--no-model)"
        from helpdesk.services.llm_generator import english_search_query

        self.calls += 1
        rendering = english_search_query(question)
        self.stored[question] = rendering
        return rendering, "model"

    def save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.stored, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")


class BridgeTerms:
    """The vocabulary bridge's replies (the model terms for a question), kept in a file so that a rerun
    compares the later stages of retrieval on the same terms (Q1 of the plan).

    Each reply is stored with the seconds the call took, or the error it raised; a stored error is raised
    again, so a call that timed out stays a failed call (the bridge then adds nothing, as in the app)."""

    def __init__(self, path: Path | None, fresh: bool, use_model: bool = True):
        self.path = path
        self.use_model = use_model
        self.stored: dict = {}
        if path and path.exists() and not fresh:
            self.stored = json.loads(path.read_text(encoding="utf-8"))
        self.calls = 0

    @contextmanager
    def active(self):
        from helpdesk.services import vocabulary_bridge

        ask = vocabulary_bridge._ask_for_terms

        def stored_or_asked(question: str) -> list[str]:
            if question not in self.stored:
                if not self.use_model:
                    raise RuntimeError("not asked (--no-model)")
                self.calls += 1
                start = time.perf_counter()
                try:
                    self.stored[question] = {"terms": ask(question), "seconds": round(time.perf_counter() - start, 2)}
                except Exception as exc:  # recorded and raised again, as the bridge's own failure
                    self.stored[question] = {"error": str(exc)[:200], "seconds": round(time.perf_counter() - start, 2)}
            reply = self.stored[question]
            if "error" in reply:
                raise RuntimeError(reply["error"])
            return list(reply["terms"])

        vocabulary_bridge.bridged_question_concepts.cache_clear()
        vocabulary_bridge._ask_for_terms = stored_or_asked
        try:
            yield
        finally:
            vocabulary_bridge._ask_for_terms = ask
            vocabulary_bridge.bridged_question_concepts.cache_clear()

    def save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.stored, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def run_question(entry: dict, translations: Translations, index: SourceIndex, requested_scope: list[str] | None = None) -> dict:
    """One question as the answer view runs it, with the wanted source's rank at every stage.

    requested_scope: the request's standardsScope (the chat page always sends an empty one)."""
    requested_scope = list(requested_scope or [])
    from helpdesk.api import views
    from helpdesk.services.concept_presence import presence_evidence
    from helpdesk.services.faq_matcher import match_faq
    from helpdesk.services.netex_example_generator import (
        example_element_names,
        generate_netex_example,
        wants_generated_example,
    )
    from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
    from helpdesk.services.semantic_abstention import semantic_abstention_message
    from helpdesk.services import llm_generator

    question = entry["question"].strip()
    patterns = list(entry.get("expected_source_patterns") or [])
    english, english_origin = translations.english(question)

    # views._parse_question, with the rendering from the file instead of a second model call.
    semantic_query = parse_question_to_semantic_query(text=question, requested_scope=requested_scope)
    parsed_question = question
    if english and not requested_scope:
        english_query = parse_question_to_semantic_query(text=english, requested_scope=[])
        if views._parse_strength(english_query) > views._parse_strength(semantic_query):
            semantic_query, parsed_question = english_query, english
    scope, _ = select_effective_scope(semantic_query, requested_scope)
    with override_settings(RELEVANCE_CHECK_ENABLED=False):
        keyword_refusal = (
            semantic_abstention_message(
                semantic_query=semantic_query,
                effective_scope=scope,
                requested_scope=requested_scope,
                allow_abstain=True,
                question=parsed_question,
            )
            is not None
        )
    faq = match_faq(question=question, scope=scope)
    faq_route = bool(faq and faq["confidence"] >= 0.85 and faq.get("scope_match", True))

    top_k, min_score = 6, 0.62  # the web page's retrievalTopK and the view's default retrievalMinScore
    graph_rag = bool(settings.GRAPH_RAG_ENABLED)
    arguments = dict(
        question=question,
        top_k=top_k,
        scope=scope,
        graph_rag_enabled=graph_rag,
        min_results=views._min_evidence_results(),
        english_question=english,
    )
    recorder = StageRecorder()
    retrieval_start = time.perf_counter()
    with retrieval_probe(recorder):
        chunks, _trace = retrieve_chunks_with_trace(min_score=min_score, **arguments)
    relaxed = False
    if not chunks:
        relaxed = True
        recorder = StageRecorder()
        with retrieval_probe(recorder):
            chunks, _trace = retrieve_chunks_with_trace(min_score=min(min_score, 0.45), **arguments)
    retrieval_seconds = round(time.perf_counter() - retrieval_start, 2)

    returned_rows = _snapshot(chunks)
    returned_ids = {row[2] for row in returned_rows}
    presence = presence_evidence(question, scope, english)
    presence_chunk_ids = {c.get("chunkId") for c in presence}
    if presence:
        presence_ids = {c["chunkId"] for c in presence}
        chunks = (presence + [c for c in chunks if c.get("chunkId") not in presence_ids])[: max(top_k, len(presence))]
    example_path = "none"
    if chunks:
        wants_model_example = wants_generated_example(question, scope) or bool(english and wants_generated_example(english, scope))
        # The model off: the standard's own examples are found as in the app; a generated one is not made.
        with override_settings(LLM_ENABLED=False):
            generated_example = generate_netex_example(question, chunks, scope, english)
        if generated_example and generated_example.get("valid"):
            example_path = str(generated_example.get("origin") or "generated")
        elif wants_model_example:
            example_path = "model (not reproduced)"
        example_elements = example_element_names(generated_example)
        if example_elements:
            element_chunks, _ = views._example_element_evidence(
                generated_example,
                example_elements,
                chunks,
                _trace,
                lambda: retrieve_chunks_with_trace(
                    min_score=min(min_score, 0.45),
                    **{**arguments, "english_question": f"{english or question} {' '.join(example_elements)}"},
                ),
                search_question=english or question,
            )
            element_chunks = views._compose_example_evidence(
                question, english, generated_example, element_chunks, chunks, top_k
            )
            if element_chunks:
                chunks = element_chunks
    view_rows = _snapshot(chunks)
    prompt_rows = view_rows[: max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))]

    # The passes: the question as asked, its English rendering, then any scope-coverage passes.
    passes = [pass_report(recorded, patterns) for recorded in recorder.passes]
    main_passes = passes[: 2 if english else 1]
    best = max(main_passes, key=lambda report: report["furthest"]) if main_passes else None
    outer = {
        "pass": best is not None and best["lostAt"] is None,
        "merged": rank_in(recorder.outer.get("merged"), patterns) is not None if english else None,
        "returned": rank_in(recorder.outer.get("returned"), patterns) is not None,
        "view": rank_in(view_rows, patterns) is not None,
        "prompt": rank_in(prompt_rows, patterns) is not None,
    }
    question_presence = [(name, outer[name]) for name in QUESTION_STAGES if outer[name] is not None]
    if outer["prompt"]:
        question_lost = None
    elif not any(present for _name, present in question_presence):
        question_lost = best["lostAt"] if best else "pool"  # never got past its retrieval pass
    else:
        question_lost = lost_at(question_presence) or "prompt"
        if question_lost == "pass":  # added after the pass (presence, example evidence) but not kept
            question_lost = "prompt"

    wanted_ids = index.ids(patterns)
    searched_ids = (
        set(
            SourceChunk.objects.filter(retrieval_gateway._scope_query_filter(scope), id__in=wanted_ids).values_list(
                "id", flat=True
            )
        )
        if wanted_ids
        else set()
    )
    embedding_pass = next((recorded for recorded in recorder.passes[1:2] if english), recorder.passes[0] if recorder.passes else None)
    embedding = (embedding_pass or {}).get("query", {}).get("embedding")
    return {
        "id": entry.get("id"),
        "question": question,
        "kind": entry.get("kind") or entry.get("intent"),
        "language": entry.get("language", "en"),
        "unsure": bool(entry.get("unsure")),
        "patterns": patterns,
        "english": english,
        "englishFrom": english_origin if english or english_origin != "model" else "none",
        "requestedScope": requested_scope,
        "scope": scope,
        "keywordRefusal": keyword_refusal,
        "faqRoute": faq_route,
        "relaxedRetry": relaxed,
        "retrievalSeconds": retrieval_seconds,
        "bridgedConcepts": sorted({c for report in passes for c in report["bridgedConcepts"]}),
        "presenceAdded": len(presence),
        "examplePath": example_path,
        "wantedChunks": len(wanted_ids),
        "wantedInSearchedScope": len(searched_ids),
        "vectorRankInScope": vector_rank(embedding, sorted(searched_ids), scope) if searched_ids else None,
        "vectorRankAllSources": vector_rank(embedding, wanted_ids, "all"),
        "passes": passes,
        "bestPass": main_passes.index(best) if best else None,
        "merged": rank_in(recorder.outer.get("merged"), patterns),
        "returned": rank_in(recorder.outer.get("returned"), patterns),
        "view": rank_in(view_rows, patterns),
        "prompt": rank_in(prompt_rows, patterns),
        "found": outer["prompt"],
        "lostAt": None if outer["prompt"] else (question_lost or "prompt"),
        "promptSources": [row[1] for row in prompt_rows],
        # Every passage the view hands on, in order, with where it came from: the presence definitions, or the
        # retrieval's own rank (for reading what stands in front of a passage that is lost).
        "viewSources": [
            {
                "path": row[1],
                "wanted": matches(patterns, row[0], row[1]),
                "from": "presence" if row[2] in presence_chunk_ids else ("retrieval" if row[2] in returned_ids else "view"),
            }
            for row in view_rows
        ],
        "returnedSources": [{"path": row[1], "wanted": matches(patterns, row[0], row[1])} for row in returned_rows],
    }


class Command(BaseCommand):
    help = (
        "For each question of a gold file, report at which step of the app's retrieval the wanted source is "
        "lost (docs/plans/2026-11-14-retrieval-misses.md, Q0). Changes nothing; the only model call is the "
        "English rendering of non-English questions, kept in --translations."
    )

    def add_arguments(self, parser):
        parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Gold YAML (expected_source_patterns).")
        parser.add_argument("--output", default="", help="Write the per-question JSON report here.")
        parser.add_argument("--ids", nargs="*", default=None, help="Only these question ids.")
        parser.add_argument("--translations", default="", help="JSON file of English renderings, read and updated.")
        parser.add_argument("--no-model", action="store_true", help="Never call the model; unrendered questions are searched as asked, and the bridge adds nothing for a question without a stored reply.")
        parser.add_argument("--fresh-translations", action="store_true", help="Ask the model again instead of the stored renderings.")
        parser.add_argument(
            "--fitting-scope",
            action="store_true",
            help="Send each question's fitting_scope as the request's standardsScope (default: empty, as the chat page).",
        )
        parser.add_argument(
            "--bridge",
            choices=("on", "off"),
            default=None,
            help="Switch the vocabulary bridge (VOCABULARY_BRIDGE_ENABLED) on or off for this run (default: the setting).",
        )
        parser.add_argument("--bridge-terms", default="", help="JSON file of the bridge's replies, read and updated.")
        parser.add_argument("--fresh-bridge-terms", action="store_true", help="Ask the model again instead of the stored replies.")
        parser.add_argument("--check-sources", action="store_true", help="Only report how many indexed chunks each pattern matches.")

    def handle(self, *args, **options):
        input_path = Path(options["input"]).expanduser().resolve()
        if not input_path.exists():
            raise CommandError(f"Gold file not found: {input_path}")
        entries = (yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}).get("questions") or []
        entries = [e for e in entries if e.get("expected_source_patterns")]
        if options.get("ids"):
            wanted = set(options["ids"])
            entries = [e for e in entries if e.get("id") in wanted]
        if not entries:
            raise CommandError("No questions with expected_source_patterns.")
        index = SourceIndex()

        if options.get("check_sources"):
            for entry in entries:
                for pattern, found in index.per_pattern(entry["expected_source_patterns"]).items():
                    self.stdout.write(
                        f"{entry['id']}\t{pattern}\t{found['chunks']} chunks\t{found['paths']} paths\t{','.join(found['scopes'])}"
                    )
            return

        translations = Translations(
            Path(options["translations"]).expanduser() if options.get("translations") else None,
            use_model=not options.get("no_model"),
            fresh=bool(options.get("fresh_translations")),
        )
        bridge_terms = BridgeTerms(
            Path(options["bridge_terms"]).expanduser() if options.get("bridge_terms") else None,
            fresh=bool(options.get("fresh_bridge_terms")),
            use_model=not options.get("no_model"),
        )
        bridge = {} if options.get("bridge") is None else {"VOCABULARY_BRIDGE_ENABLED": options["bridge"] == "on"}
        reports = []
        for number, entry in enumerate(entries, start=1):
            requested = list(entry.get("fitting_scope") or []) if options.get("fitting_scope") else []
            with override_settings(**bridge), bridge_terms.active():
                report = run_question(entry, translations, index, requested)
            report["bridgeReplies"] = {
                text: bridge_terms.stored[text]
                for text in (report["question"], report["english"])
                if text and text in bridge_terms.stored
            }
            reports.append(report)
            best = report["passes"][report["bestPass"]] if report["bestPass"] is not None else {}
            self.stdout.write(
                f"[{number}/{len(entries)}] {report['id']}\t"
                f"{'FOUND' if report['found'] else 'lost: ' + LOSS_STEP.get(report['lostAt'], str(report['lostAt']))}\t"
                f"after scoring {best.get('rankAfterScoring')}/{best.get('scoredCount')}\t"
                f"vector {report['vectorRankInScope']} (all {report['vectorRankAllSources']})\t"
                f"scope {report['scope']}"
            )
        translations.save()
        bridge_terms.save()

        counts = Counter("found" if r["found"] else LOSS_STEP.get(r["lostAt"], str(r["lostAt"])) for r in reports)
        self.stdout.write("")
        self.stdout.write(f"Questions: {len(reports)}; renderings computed (english_search_query, English questions included): {translations.calls}")
        self.stdout.write(f"Vocabulary bridge: {options.get('bridge') or 'as set'}; replies asked of the model: {bridge_terms.calls}")
        for step, count in counts.most_common():
            self.stdout.write(f"  {count:4d}  {step}")
        if options.get("output"):
            output = Path(options["output"]).expanduser()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({"input": str(input_path), "questions": reports}, indent=1, ensure_ascii=False), encoding="utf-8")
            self.stdout.write(f"Report written: {output}")
