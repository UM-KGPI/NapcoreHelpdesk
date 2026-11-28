"""
Measure how a clarifying choice of scope would do (plan 2026-11-14-clarifying-choice, step C0).

Nothing here is used by the answer endpoints; it measures, it does not change behaviour.

Two steps, each writing JSON:

    derive  For each question, the scopes (values of STANDARDS_SCOPE_CHOICES) each way of deriving options
            would offer, ranked, with the time and model calls the way costs:
              retrieval        standards of the chunks the unscoped search finds (the search the app runs
                               when no scope is given; it leaves out the opt-in sources)
              retrieval_all    standards of the chunks a search over every source finds
              parse            candidateStandards of the semantic parse
              parse_discovered candidateStandards, then the standards the ontology recognised for the concept
              controller       the controller model asked which scopes the question may be about (one call;
                               only with --ask-controller, never in tests)
    ask     Each question through a running backend's answer endpoint, with each scope it is given and
            without one, several runs each; records answered or refused and the cited chunks.

Usage:
    python manage.py measure_scope_options derive --output options.json [--ask-controller]
    python manage.py measure_scope_options ask --options options.json --url http://localhost:8000 \
        --runs 3 --output answers.json [--every-scope-for must_refuse]
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib import request

import yaml
from django.core.management.base import BaseCommand, CommandError

from helpdesk.api.serializers import STANDARDS_SCOPE_CHOICES
from helpdesk.management.commands.benchmark_utils import local_benchmark_file, read_yaml_file

QUESTIONS_FILE = local_benchmark_file("refused-questions.yaml")
FITTING_FILE = local_benchmark_file("refused-questions-scopes.yaml")
OPTIONS = 3
RETRIEVAL_TOP_K = 12

# One line per scope, from the relevance check's description of the sources.
_SCOPE_DESCRIPTIONS = {
    "NeTEx": "static public-transport data (timetables, networks, lines, stops, fares, accessibility, vehicles, operators)",
    "SIRI": "real-time public-transport data exchange (vehicle monitoring, estimated timetables, stop and facility monitoring, situations, general messages)",
    "OpRa": "historical operational raw data of public transport (offer, demand, capacity, passenger counts, delays and cancellations)",
    "Transmodel": "the reference data model behind NeTEx, SIRI and OpRa",
    "EU legislation": "EU acts on transport data: MMTIS Delegated Regulation 2017/1926 and its 2024 amendment, ITS Directive 2010/40/EU, TEL TSI (which data must be provided through National Access Points, in which standards, and the terms they define)",
    "mobilityDCAT-AP": "the metadata profile for describing datasets on National Access Points",
    "NAPCORE": "NAPCORE's material on National Access Points and National Bodies (working groups, deliverables, data quality, compliance assessment)",
    "INSPIRE": "the EU spatial data rules, in particular the Transport Networks theme",
    "DATEX II": "road traffic and travel information (situations, traffic data, parking, charging points, traffic management, location referencing)",
    "TN-ITS": "road attribute updates for digital maps",
}

_CONTROLLER_PROMPT = """A helpdesk answers questions from the documentation of these sources:
{scopes}

Question: {question}

Which of these sources most likely answer the question? Name at most three, the most likely first, exactly as
written before the colon, as a JSON list, for example ["NeTEx", "SIRI"]. If none of them fits, answer []."""


def _load_questions(path: Path) -> list[dict]:
    return read_yaml_file(path)["questions"]


def _standards_in_rank_order(chunks: list[dict]) -> list[str]:
    """Scopes in the order their first chunk appears (a chunk of two standards gives both, in its order)."""
    ranked: list[str] = []
    for chunk in chunks:
        for standard in chunk.get("standardsScope") or []:
            if standard in STANDARDS_SCOPE_CHOICES and standard not in ranked:
                ranked.append(standard)
    return ranked


def _scopes_named(text: str) -> list[str]:
    """The scope names in a reply, in the order they appear."""
    found = []
    for name in sorted(STANDARDS_SCOPE_CHOICES, key=len, reverse=True):
        for match in re.finditer(rf'"{re.escape(name)}"', text or ""):
            found.append((match.start(), name))
    return list(dict.fromkeys(name for _, name in sorted(found)))


def ask_controller_for_scopes(question: str) -> list[str]:
    """One controller call (the relevance check's path): the scopes the question may be about."""
    from django.conf import settings

    from helpdesk.services.controller_llm import _uses_anthropic, anthropic_controller_call
    from helpdesk.services.llm_options import controller_max_tokens

    if not _uses_anthropic():
        raise CommandError("--ask-controller is measured with the Anthropic controller only.")
    scopes = "\n".join(f"- {name}: {_SCOPE_DESCRIPTIONS[name]}" for name in STANDARDS_SCOPE_CHOICES)
    payload = anthropic_controller_call(
        messages=[{"role": "user", "content": _CONTROLLER_PROMPT.format(scopes=scopes, question=question)}],
        max_tokens=controller_max_tokens(48),
        timeout_seconds=int(getattr(settings, "RELEVANCE_CHECK_TIMEOUT_SECONDS", 10)) + 10,
        json_answer=False,
    )
    return _scopes_named(payload["choices"][0]["message"]["content"])


class Command(BaseCommand):
    help = "Measure the scope options a clarifying choice would offer, and the answers with each (plan C0)."

    def add_arguments(self, parser):
        parser.add_argument("step", choices=["derive", "ask"])
        parser.add_argument(
            "--questions", type=Path, nargs="+", default=[QUESTIONS_FILE],
            help="Question files (YAML with a questions list of id/question).",
        )
        parser.add_argument("--ids", nargs="*", help="Only these question ids.")
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--ask-controller", action="store_true", help="derive: also ask the controller model.")
        parser.add_argument("--options", type=Path, help="ask: the derive output.")
        parser.add_argument("--fitting", type=Path, default=FITTING_FILE,
                            help="ask: the fitting scopes per question (also asked with).")
        parser.add_argument("--url", default="http://localhost:8000", help="ask: the backend under test.")
        parser.add_argument("--runs", type=int, default=3)
        parser.add_argument("--workers", type=int, default=4)
        parser.add_argument("--request-prefix", default="req-diag-c0")
        parser.add_argument(
            "--every-scope-for", nargs="*", default=["must_refuse"],
            help="ask: categories asked with every scope value instead of the offered ones.",
        )
        parser.add_argument("--no-baseline", action="store_true", help="ask: skip the unscoped runs.")

    def handle(self, *args, **options):
        questions = [q for path in options["questions"] for q in _load_questions(path)]
        if options["ids"]:
            questions = [q for q in questions if q["id"] in set(options["ids"])]
        if options["step"] == "derive":
            rows = [self._derive(q, options["ask_controller"]) for q in questions]
        else:
            rows = self._ask_all(questions, options)
        options["output"].write_text(json.dumps({"questions": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.stdout.write(f"wrote {options['output']} ({len(rows)} rows)")

    # derive -----------------------------------------------------------------------------------------------

    def _derive(self, item: dict, ask_controller: bool) -> dict:
        from helpdesk.api.views import _parse_question
        from helpdesk.services.retrieval_gateway import _retrieve_chunks_once, retrieve_chunks_with_trace

        question = item["question"]
        ways: dict[str, dict] = {}

        started = time.perf_counter()
        semantic_query, english, _ = _parse_question(question, [])
        parse_seconds = time.perf_counter() - started
        candidates = [s for s in semantic_query.candidate_standards if s in STANDARDS_SCOPE_CHOICES]
        discovered = [s for s in (semantic_query.discovered_standards or []) if s in STANDARDS_SCOPE_CHOICES]
        ways["parse"] = {"ranked": candidates, "seconds": 0.0, "modelCalls": 0}
        ways["parse_discovered"] = {
            "ranked": list(dict.fromkeys(candidates + discovered)), "seconds": 0.0, "modelCalls": 0,
        }

        started = time.perf_counter()
        chunks, _ = retrieve_chunks_with_trace(
            question=question, top_k=RETRIEVAL_TOP_K, min_score=0.0, scope=None, english_question=english,
        )
        ways["retrieval"] = {
            "ranked": _standards_in_rank_order(chunks), "seconds": round(time.perf_counter() - started, 2),
            "modelCalls": 0, "paths": [c.get("sourcePath") for c in chunks],
        }

        # Every source: the opt-in ones too. One search per wording, without the per-scope coverage step.
        started = time.perf_counter()
        every = list(STANDARDS_SCOPE_CHOICES)
        chunks_all, _ = _retrieve_chunks_once(question=question, top_k=RETRIEVAL_TOP_K, min_score=0.0, scope=every)
        if english:
            english_chunks, _ = _retrieve_chunks_once(question=english, top_k=RETRIEVAL_TOP_K, min_score=0.0, scope=every)
            merged, seen = [], set()
            for index in range(max(len(english_chunks), len(chunks_all))):
                for ranked in (english_chunks, chunks_all):
                    if index < len(ranked) and ranked[index].get("chunkId") not in seen:
                        seen.add(ranked[index].get("chunkId"))
                        merged.append(ranked[index])
            chunks_all = merged[:RETRIEVAL_TOP_K]
        ways["retrieval_all"] = {
            "ranked": _standards_in_rank_order(chunks_all), "seconds": round(time.perf_counter() - started, 2),
            "modelCalls": 0, "paths": [c.get("sourcePath") for c in chunks_all],
        }

        if ask_controller:
            started = time.perf_counter()
            try:
                ranked, error = ask_controller_for_scopes(english or question), None
            except Exception as exc:  # measured, not hidden
                ranked, error = [], str(exc)[:200]
            ways["controller"] = {
                "ranked": ranked, "seconds": round(time.perf_counter() - started, 2), "modelCalls": 1, "error": error,
            }

        self.stdout.write(f"{item['id']}: " + "  ".join(f"{k}={v['ranked'][:OPTIONS]}" for k, v in ways.items()))
        return {
            "id": item["id"], "category": item.get("category", ""), "question": question,
            "english": english, "parseSeconds": round(parse_seconds, 2), "ways": ways,
        }

    # ask --------------------------------------------------------------------------------------------------

    def _ask_all(self, questions: list[dict], options: dict) -> list[dict]:
        if not options["options"]:
            raise CommandError("ask needs --options (the derive output).")
        derived = {row["id"]: row for row in json.loads(options["options"].read_text())["questions"]}
        fitting = {}
        if options["fitting"] and options["fitting"].exists():
            fitting = {row["id"]: row for row in yaml.safe_load(options["fitting"].read_text())["questions"]}

        jobs = []
        for item in questions:
            if item.get("category") in options["every_scope_for"]:
                scopes = list(STANDARDS_SCOPE_CHOICES)
            else:
                offered = [s for way in derived.get(item["id"], {}).get("ways", {}).values() for s in way["ranked"][:OPTIONS]]
                scopes = list(dict.fromkeys(offered + list(fitting.get(item["id"], {}).get("fit", []))))
            if not options["no_baseline"]:
                scopes = [None] + scopes
            for scope in scopes:
                for run in range(options["runs"]):
                    jobs.append((item, scope, run))
        self.stdout.write(f"{len(jobs)} requests to {options['url']}")

        token = self._token(options["url"])
        counter = iter(range(1, len(jobs) + 1))

        def ask(job):
            item, scope, run = job
            number = next(counter)
            return self._ask_one(options["url"], token, item, scope, run, f"{options['request_prefix']}-{number}")

        with ThreadPoolExecutor(max_workers=options["workers"]) as pool:
            rows = []
            for row in pool.map(ask, jobs):
                rows.append(row)
                if len(rows) % 20 == 0:
                    self.stdout.write(f"  {len(rows)}/{len(jobs)}")
        return rows

    @staticmethod
    def _post(url: str, body: dict, headers: dict, timeout: int = 240) -> dict:
        http_request = request.Request(
            url, data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", **headers},
        )
        with request.urlopen(http_request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _token(self, base: str) -> str:
        return self._post(f"{base.rstrip('/')}/api/v1/auth/dev-token", {}, {})["token"]

    def _ask_one(self, base, token, item, scope, run, request_id) -> dict:
        body = {"question": item["question"]}
        if scope:
            body["standardsScope"] = [scope]
        started = time.perf_counter()
        try:
            payload = self._post(
                f"{base.rstrip('/')}/api/v1/questions/answer", body,
                {"Authorization": f"Bearer {token}", "X-Request-Id": request_id},
            )
            error = None
        except Exception as exc:
            payload, error = {}, str(exc)[:200]
        answer = payload.get("answer") or ""
        cited = set(re.findall(r"\[(E\d+)\]", answer))
        citations = [
            {"label": c.get("label"), "chunkId": c.get("chunkId"), "sourcePath": c.get("sourcePath"),
             "repositoryUrl": (c.get("repositoryUrl") or "").split("/blob/")[0], "cited": c.get("label") in cited}
            for c in payload.get("citations") or []
        ]
        return {
            "id": item["id"], "category": item.get("category", ""), "question": item["question"],
            "scope": scope, "run": run, "requestId": request_id, "seconds": round(time.perf_counter() - started, 1),
            "error": error, "abstained": payload.get("abstained"), "abstentionReason": payload.get("abstentionReason"),
            "mode": payload.get("mode"), "answer": answer, "citations": citations,
            "generatedExample": bool(payload.get("generatedExample")),
        }
