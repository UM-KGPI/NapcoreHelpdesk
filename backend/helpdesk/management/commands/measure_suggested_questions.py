"""Measure suggested questions for refused questions (docs/plans/2026-11-15-suggested-questions.md, S0).

Changes nothing in the app. Stages, each reading and writing JSON files in --output-dir:

- baseline: ask every question of refused-questions.yaml and the b-entries of answer-source-questions.yaml
  through the API (--api-url), --runs times; which are refused today and how (at the screen, after the search).
- pool: the "earlier answered questions" of way 2, frozen once: from the question log (--pool log: answered,
  validated, not disliked) or, as a stand-in, from the answerable benchmark questions asked once through the API
  (--pool benchmark: those answered and validated), each with its embedding.
- suggest: for each question refused today, the suggestions of the three ways (suggested_questions), the check
  before showing for each, and the seconds and model calls each step takes (one file per --run).
- score: every suggestion of a run asked through the API: answered or refused, and its citations.
- summary: the gate's numbers over the runs.

The wanted source of a question is the gold file's expected_source_patterns: an a-entry's for the
refused-questions entry it refers to (`ref`), a b-entry's own.
"""

from __future__ import annotations

import json
import statistics
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError

from helpdesk.management.commands.locate_answer_sources import matches

BENCHMARKS = Path(__file__).resolve().parents[2] / "benchmarks"
REFUSED_FILE = BENCHMARKS / "refused-questions.yaml"
GOLD_FILE = BENCHMARKS / "answer-source-questions.yaml"
BENCHMARK_FILE = BENCHMARKS / "benchmark-questions.yaml"
WAYS = ("written", "earlier", "both", "named")
EMPTY = {"suggestions": [], "calls": 0, "seconds": 0.0, "searchSeconds": 0.0, "error": None, "passages": []}
# Skip options for questions not about the sources, from what the app already knows about the refusal:
# none; the second opinion said IRRELEVANT; any refusal at the screen.
SKIPS = ("none", "irrelevant", "screen")
# The must-refuse questions the plan names as not about the sources (weather, bread, football, a poem, a capital,
# a laptop, "hi"), with the two the record found rightly refused as nonsense.
NOT_ABOUT_SOURCES = ("m01", "m02", "m03", "m07", "m08", "m09", "m10", "m11", "m12")


# ── Input ───────────────────────────────────────────────────────────────────


def load_questions() -> list[dict]:
    """The refused-questions entries (with the wanted source of their gold counterpart) and the gold b-entries."""
    refused = yaml.safe_load(REFUSED_FILE.read_text(encoding="utf-8"))["questions"]
    gold = yaml.safe_load(GOLD_FILE.read_text(encoding="utf-8"))["questions"]
    by_ref = {entry["ref"]: entry for entry in gold if entry.get("ref")}
    questions = []
    for entry in refused:
        counterpart = by_ref.get(entry["id"])
        group = "must_refuse" if entry.get("expect") == "abstain" else "wrongly_refused"
        questions.append(
            {
                "id": entry["id"],
                "question": entry["question"],
                "group": group,
                "patterns": list((counterpart or {}).get("expected_source_patterns") or []),
                "gold": (counterpart or {}).get("id"),
                "language": (counterpart or {}).get("language", "en"),
                "unsure": bool((counterpart or {}).get("unsure")),
                "notAboutSources": entry["id"] in NOT_ABOUT_SOURCES,
            }
        )
    for entry in gold:
        if entry.get("ref"):
            continue
        questions.append(
            {
                "id": entry["id"],
                "question": entry["question"],
                "group": "gold",
                "patterns": list(entry.get("expected_source_patterns") or []),
                "gold": entry["id"],
                "language": entry.get("language", "en"),
                "unsure": bool(entry.get("unsure")),
                "notAboutSources": False,
            }
        )
    return questions


# ── The API ─────────────────────────────────────────────────────────────────


def api_token(api_url: str) -> str:
    from urllib import request

    http_request = request.Request(
        api_url.rstrip("/") + "/auth/dev-token", data=b"{}", method="POST", headers={"Content-Type": "application/json"}
    )
    with request.urlopen(http_request, timeout=30) as response:
        return json.loads(response.read())["token"]


def refusal_kind(status_code: int, payload: dict) -> str | None:
    """None when answered; else where it was refused: at the screen (the second opinion said irrelevant, or the
    keyword rules' message stands), nothing retrieved, the policy check, the answer model's verdict."""
    from helpdesk.services.semantic_abstention import LOW_CONFIDENCE_MESSAGE, NO_CONCEPT_MESSAGE, NOT_RELEVANT_MESSAGE

    if status_code == 422:
        return "policy"
    if status_code != 200:
        return f"error-{status_code}"
    if not payload.get("abstained"):
        return None
    answer = payload.get("answer") or ""
    if answer == NOT_RELEVANT_MESSAGE:
        return "screen-irrelevant"
    if answer in (NO_CONCEPT_MESSAGE, LOW_CONFIDENCE_MESSAGE):
        return "screen-keyword"
    if not (payload.get("trace") or {}).get("retrievalEventIds"):
        return "nothing-retrieved"
    return "verdict"


def ask(api_url: str, token: str, question: str, timeout: float = 240) -> dict:
    """The question posted as the chat page posts it (no scope); the outcome in short."""
    from urllib import error, request

    started = time.perf_counter()
    http_request = request.Request(
        api_url.rstrip("/") + "/questions/answer",
        data=json.dumps({"question": question}).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Request-Id": f"s0-{uuid.uuid4().hex[:12]}",
        },
    )
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            status_code, payload = response.status, json.loads(response.read())
    except error.HTTPError as exc:
        status_code, payload = exc.code, {}
    except Exception as exc:  # recorded as an error, never as an answer
        return {"status": 0, "error": str(exc)[:200], "refused": "error", "seconds": round(time.perf_counter() - started, 2)}
    kind = refusal_kind(status_code, payload)
    trace = payload.get("trace") or {}
    return {
        "status": status_code,
        "refused": kind,
        "mode": payload.get("mode"),
        "answer": (payload.get("answer") or "")[:1500],
        "citations": [
            {"repositoryUrl": c.get("repositoryUrl") or "", "sourcePath": c.get("sourcePath") or ""}
            for c in payload.get("citations") or []
        ],
        "validated": trace.get("llmAnswerValidated"),
        "searchTranslation": trace.get("searchTranslation"),
        "seconds": round(time.perf_counter() - started, 2),
        "timingsMs": trace.get("timingsMs"),
    }


def cites(outcome: dict, patterns: list[str]) -> bool:
    """Whether a citation is a wanted source. A citation's repositoryUrl is the link to the file (for a GitHub file
    ".../blob/<commit>/<path>"), so the repository is what stands before "/blob/"."""
    return any(
        matches(patterns, (c["repositoryUrl"] or "").split("/blob/")[0], c["sourcePath"])
        for c in outcome.get("citations") or []
    )


# ── Helpers ─────────────────────────────────────────────────────────────────


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


def percentile(values: list[float], share: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, int(share * len(ordered)))], 2)


def refused_today(baseline: dict) -> dict[str, dict]:
    """The questions refused in at least one baseline run, with how they were refused (the first refused run's
    kind, and every kind seen)."""
    result = {}
    for question in baseline["questions"]:
        kinds = [run["refused"] for run in question["runs"] if run["refused"]]
        if kinds:
            result[question["id"]] = {**question, "kind": kinds[0], "kinds": kinds, "refusedRuns": len(kinds)}
    return result


def skipped(kind: str, skip: str) -> bool:
    if skip == "irrelevant":
        return kind == "screen-irrelevant"
    if skip == "screen":
        return kind.startswith("screen")
    return False


def shown(suggestions: list[dict], limit: int = 3) -> list[dict]:
    return [s for s in suggestions if s["check"]["passed"]][:limit]


def way_suggestions(entry: dict, way: str, after_check: bool) -> list[dict]:
    """A question's suggestions of one way, before or after the check (way 3 is built from the others, after the
    check from those that passed it)."""
    from helpdesk.services.suggested_questions import combined

    if way == "named":
        named = entry.get("named", EMPTY)["suggestions"]
        return shown(named) if after_check else named
    written, earlier = entry["written"]["suggestions"], entry["earlier"]["suggestions"]
    if after_check:
        written, earlier = shown(written), shown(earlier)
    if way == "written":
        return written
    if way == "earlier":
        return earlier
    return combined(earlier, written)


class Command(BaseCommand):
    help = "Measure suggested questions for refused questions (plan 2026-11-15-suggested-questions.md, S0)."

    def add_arguments(self, parser):
        parser.add_argument("--stage", required=True, choices=("baseline", "pool", "suggest", "score", "summary"))
        parser.add_argument("--output-dir", required=True, help="Directory of the JSON files (read and written).")
        parser.add_argument("--api-url", default="http://localhost:8061/api/v1", help="The app's API base URL.")
        parser.add_argument("--runs", type=int, default=2, help="baseline: runs per question.")
        parser.add_argument("--run", type=int, default=1, help="suggest, score: the run number.")
        parser.add_argument("--pool", choices=("log", "benchmark"), default="benchmark", help="pool: where the earlier answered questions come from.")
        parser.add_argument("--ids", nargs="*", default=None, help="Only these question ids.")
        parser.add_argument("--summary-runs", default="", help="summary: only these runs (comma-separated).")
        parser.add_argument("--summary-name", default="summary", help="summary: the file name of the summary.")
        parser.add_argument(
            "--ways",
            default="written,earlier",
            help="suggest: the ways to run, of written, earlier, named (way 4, measured in runs of its own).",
        )

    def handle(self, *args, **options):
        out = Path(options["output_dir"]).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        stage = options["stage"]
        getattr(self, f"_{stage}")(out, options)

    # ── baseline ──

    def _baseline(self, out: Path, options: dict) -> None:
        questions = load_questions()
        if options.get("ids"):
            questions = [q for q in questions if q["id"] in set(options["ids"])]
        token = api_token(options["api_url"])
        for question in questions:
            question["runs"] = []
        for run in range(1, options["runs"] + 1):
            for number, question in enumerate(questions, start=1):
                outcome = ask(options["api_url"], token, question["question"])
                outcome["citesWanted"] = cites(outcome, question["patterns"]) if not outcome["refused"] else False
                question["runs"].append(outcome)
                self.stdout.write(
                    f"run {run} [{number}/{len(questions)}] {question['id']}\t{outcome['refused'] or 'answered'}\t{outcome['seconds']} s"
                )
            write_json(out / "baseline.json", {"apiUrl": options["api_url"], "questions": questions})
        today = refused_today({"questions": questions})
        for group in ("wrongly_refused", "gold", "must_refuse"):
            ids = [q["id"] for q in questions if q["group"] == group]
            refused_ids = [i for i in ids if i in today]
            self.stdout.write(f"{group}: refused in >= 1 of {options['runs']} runs: {len(refused_ids)} of {len(ids)}")

    # ── pool ──

    def _pool(self, out: Path, options: dict) -> None:
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.suggested_questions import normalized

        tested = {normalized(q["question"]) for q in load_questions()}
        entries: list[dict] = []
        if options["pool"] == "log":
            from helpdesk.models import QuestionEvent

            seen: set[str] = set()
            for event in QuestionEvent.objects.filter(abstained=False, user_dislikes=False).order_by("-created_at"):
                if (event.trace or {}).get("llmAnswerValidated") is not True:
                    continue
                key = normalized(event.question)
                if key in seen:
                    continue
                seen.add(key)
                entries.append({"question": " ".join(event.question.split()), "source": "log", "inTestSets": key in tested})
        else:
            benchmark = yaml.safe_load(BENCHMARK_FILE.read_text(encoding="utf-8"))["questions"]
            token = api_token(options["api_url"])
            for number, item in enumerate(benchmark, start=1):
                if item.get("intent") == "abstention":
                    continue
                outcome = ask(options["api_url"], token, item["question"])
                usable = not outcome["refused"] and outcome.get("validated") is True
                self.stdout.write(f"[{number}/{len(benchmark)}] {item['id']}\t{outcome['refused'] or 'answered'}\tvalidated {outcome.get('validated')}")
                entries.append(
                    {
                        "id": item["id"],
                        "question": item["question"],
                        "source": "benchmark",
                        "answered": not outcome["refused"],
                        "validated": outcome.get("validated"),
                        "usable": usable,
                        "inTestSets": normalized(item["question"]) in tested,
                    }
                )
        for entry in entries:
            entry.setdefault("usable", True)
            if entry["usable"]:
                entry["embedding"] = build_text_embedding(entry["question"], kind="query")
        write_json(out / f"pool-{options['pool']}.json", {"pool": options["pool"], "entries": entries})
        usable = [e for e in entries if e["usable"]]
        self.stdout.write(
            f"pool {options['pool']}: {len(entries)} distinct, {len(usable)} usable, "
            f"{sum(1 for e in usable if e['inTestSets'])} of them are questions of the test sets"
        )

    # ── suggest ──

    def _suggest(self, out: Path, options: dict) -> None:
        from helpdesk.services.embeddings import build_text_embedding
        from helpdesk.services.llm_generator import english_search_query, question_language
        from helpdesk.services import suggested_questions as sq

        ways = set(options["ways"].split(","))
        today = refused_today(read_json(out / "baseline.json"))
        pool_file = out / f"pool-{options['pool']}.json"
        pool = [e for e in read_json(pool_file)["entries"] if e.get("usable") and not e.get("inTestSets")]
        ids = [i for i in today if not options.get("ids") or i in set(options["ids"])]
        rows = []
        for number, question_id in enumerate(ids, start=1):
            question = today[question_id]
            text = question["question"]
            # Known to the app before the screen (api.views._parse_question): not counted as added.
            prepared = time.perf_counter()
            english = english_search_query(text)
            language = question_language(text)
            prepared = round(time.perf_counter() - prepared, 3)

            written, earlier, named = (json.loads(json.dumps(EMPTY)) for _ in range(3))
            passages = []
            if "written" in ways:
                started = time.perf_counter()
                passages = sq.passages_near(text, english)
                search_seconds = round(time.perf_counter() - started, 3)
                written = sq.written_suggestions(text, passages, language)
                written["searchSeconds"] = search_seconds
                written["passages"] = [
                    {"sourcePath": p.get("sourcePath"), "standardsScope": p.get("standardsScope"), "score": round(float(p.get("score") or 0), 3)}
                    for p in passages
                ]
            if "earlier" in ways:
                started = time.perf_counter()
                embedding = build_text_embedding(text, kind="query")
                earlier = {"suggestions": sq.nearest_answered(text, embedding, pool), "calls": 0}
                earlier["seconds"] = round(time.perf_counter() - started, 3)
            if "named" in ways:
                named = sq.named_suggestions(text, language)

            for suggestion in written["suggestions"] + named["suggestions"]:
                suggestion["check"] = sq.cheap_check(suggestion["question"], suggestion.get("english"))
            for suggestion in earlier["suggestions"]:
                suggestion["check"] = sq.cheap_check(suggestion["question"], None)
            rows.append(
                {
                    "id": question_id,
                    "question": text,
                    "group": question["group"],
                    "kind": question["kind"],
                    "kinds": question["kinds"],
                    "patterns": question["patterns"],
                    "unsure": question["unsure"],
                    "notAboutSources": question["notAboutSources"],
                    "language": language,
                    "english": english,
                    "preparedSeconds": prepared,
                    "written": written,
                    "earlier": earlier,
                    "named": named,
                }
            )
            self.stdout.write(
                f"[{number}/{len(ids)}] {question_id}\tpassages {len(passages)}\twritten {len(written['suggestions'])}"
                f" ({sum(s['check']['passed'] for s in written['suggestions'])} pass)\t"
                f"earlier {sum(s['check']['passed'] for s in earlier['suggestions'])} pass\t"
                f"named {len(named['suggestions'])} ({sum(s['check']['passed'] for s in named['suggestions'])} pass)\t"
                f"{written['searchSeconds']}+{written['seconds']}+{named['seconds']} s\t{written['error'] or ''}{named['error'] or ''}"
            )
        write_json(out / f"suggest-r{options['run']}.json", {"run": options["run"], "pool": options["pool"], "questions": rows})

    # ── score ──

    def _score(self, out: Path, options: dict) -> None:
        suggest_file = out / f"suggest-r{options['run']}.json"
        score_file = out / f"score-r{options['run']}.json"
        rows = read_json(suggest_file)["questions"]
        scored = read_json(score_file)["answers"] if score_file.exists() else {}
        texts = []
        for row in rows:
            for way in ("written", "earlier", "named"):
                for suggestion in row.get(way, EMPTY)["suggestions"]:
                    if suggestion["question"] not in texts:
                        texts.append(suggestion["question"])
        token = api_token(options["api_url"])
        for number, text in enumerate(texts, start=1):
            if text in scored:
                continue
            scored[text] = ask(options["api_url"], token, text)
            self.stdout.write(f"[{number}/{len(texts)}] {scored[text]['refused'] or 'answered'}\t{scored[text]['seconds']} s\t{text[:90]}")
            write_json(score_file, {"run": options["run"], "answers": scored})
        write_json(score_file, {"run": options["run"], "answers": scored})

    # ── summary ──

    def _summary(self, out: Path, options: dict) -> None:
        from helpdesk.services.question_preprocessor import detect_question_language
        from helpdesk.services.suggested_questions import normalized

        baseline = read_json(out / "baseline.json")
        today = refused_today(baseline)
        runs = sorted(int(p.stem.split("-r")[1]) for p in out.glob("suggest-r*.json") if (out / f"score-r{p.stem.split('-r')[1]}.json").exists())
        if options.get("summary_runs"):
            runs = [run for run in runs if run in {int(r) for r in options["summary_runs"].split(",")}]
        if not runs:
            raise CommandError("No run with both a suggest and a score file.")
        data = {run: (read_json(out / f"suggest-r{run}.json")["questions"], read_json(out / f"score-r{run}.json")["answers"]) for run in runs}

        summary: dict = {"runs": runs, "refusedToday": {}, "ways": {}, "check": {}, "time": {}, "mustRefuse": {}}
        groups = defaultdict(list)
        for question in baseline["questions"]:
            groups[question["group"]].append(question["id"])
        for group, ids in groups.items():
            refused = [i for i in ids if i in today]
            summary["refusedToday"][group] = {
                "asked": len(ids),
                "refused": len(refused),
                "refusedBoth": sum(1 for i in refused if today[i]["refusedRuns"] == len(today[i]["runs"])),
                "kinds": dict(Counter(today[i]["kind"] for i in refused)),
                "ids": refused,
            }
        wrong_ids = [i for i in today if today[i]["group"] in ("wrongly_refused", "gold")]

        def answered(text: str, answers: dict) -> bool:
            return not answers[text]["refused"]

        # Gate 1, 2 and 3 per way, per skip option, per run.
        for way in WAYS:
            for skip in SKIPS:
                key = f"{way}/{skip}"
                per_run = []
                for run in runs:
                    rows, answers = data[run]
                    useful, useful_before, shown_count, shown_dead = [], [], 0, 0
                    must = {}
                    for row in rows:
                        if skipped(row["kind"], skip):
                            continue
                        after = way_suggestions(row, way, after_check=True)
                        before = way_suggestions(row, way, after_check=False)
                        shown_count += len(after)
                        shown_dead += sum(1 for s in after if not answered(s["question"], answers))
                        if row["id"] in wrong_ids and row["patterns"]:
                            if any(answered(s["question"], answers) and cites(answers[s["question"]], row["patterns"]) for s in after):
                                useful.append(row["id"])
                            if any(answered(s["question"], answers) and cites(answers[s["question"]], row["patterns"]) for s in before):
                                useful_before.append(row["id"])
                        if row["group"] == "must_refuse" and after:
                            must[row["id"]] = [
                                {"question": s["question"], "answered": answered(s["question"], answers)} for s in after
                            ]
                    per_run.append(
                        {
                            "run": run,
                            "useful": len(useful),
                            "usefulIds": useful,
                            "usefulBeforeCheck": len(useful_before),
                            "wronglyRefused": len(wrong_ids),
                            "shown": shown_count,
                            "shownDead": shown_dead,
                            "mustRefuseWithSuggestions": must,
                        }
                    )
                summary["ways"][key] = per_run

        # The check: does passing it predict an answer when asked in full?
        for run in runs:
            rows, answers = data[run]
            table = Counter()
            for row in rows:
                for way in ("written", "earlier", "named"):
                    for s in row.get(way, EMPTY)["suggestions"]:
                        table[(s["check"]["passed"], answered(s["question"], answers))] += 1
            summary["check"][run] = {f"passed={p},answered={a}": n for (p, a), n in sorted(table.items())}

        # Time: seconds added to a refusal, per way and kind (screen / after the search), skip "none".
        times = defaultdict(list)
        for run in runs:
            rows, _answers = data[run]
            for row in rows:
                place = "screen" if row["kind"].startswith("screen") else "after search"
                written_s = row["written"]["searchSeconds"] + row["written"]["seconds"] + sum(s["check"]["seconds"] for s in row["written"]["suggestions"])
                earlier_s = row["earlier"]["seconds"] + sum(s["check"]["seconds"] for s in row["earlier"]["suggestions"])
                times[("written", place)].append(written_s)
                times[("earlier", place)].append(earlier_s)
                times[("both", place)].append(written_s + earlier_s)
                named_row = row.get("named", EMPTY)
                if named_row["calls"]:
                    times[("named", place)].append(named_row["seconds"] + sum(s["check"]["seconds"] for s in named_row["suggestions"]))
                times[("written search", place)].append(row["written"]["searchSeconds"])
                times[("written model", place)].append(row["written"]["seconds"])
                times[("check, each", place)].extend(s["check"]["seconds"] for w in ("written", "earlier", "named") for s in row.get(w, EMPTY)["suggestions"])
        summary["time"] = {
            f"{name} / {place}": {"n": len(values), "median": median(values), "p90": percentile(values, 0.9)}
            for (name, place), values in sorted(times.items())
        }
        summary["modelCalls"] = {
            run: {
                way: {
                    "calls": sum(r.get(way, EMPTY)["calls"] for r in data[run][0]),
                    "failed": sum(1 for r in data[run][0] if r.get(way, EMPTY)["error"]),
                }
                for way in ("written", "named")
            }
            for run in runs
        }

        # Stability of the written suggestions; language; difference from the original.
        stability = {}
        for question_id in today:
            sets = []
            for run in runs:
                row = next((r for r in data[run][0] if r["id"] == question_id), None)
                if row:
                    sets.append({normalized(s["question"]) for w in ("written", "named") for s in row.get(w, EMPTY)["suggestions"]})
            if len(sets) >= 2:
                union = set().union(*sets)
                common = set.intersection(*sets)
                stability[question_id] = {"distinct": len(union), "inEveryRun": len(common), "perRun": [len(s) for s in sets]}
        summary["stability"] = stability
        languages = []
        for run in runs:
            for row in data[run][0]:
                if (row.get("language") or "English") != "English":
                    for s in row["written"]["suggestions"] + row.get("named", EMPTY)["suggestions"]:
                        languages.append({"id": row["id"], "run": run, "asked": row["language"], "suggestion": s["question"], "detected": detect_question_language(s["question"])})
        summary["languages"] = languages
        summary["repeats"] = sum(
            1 for run in runs for row in data[run][0] for w in ("written", "named") for s in row.get(w, EMPTY)["suggestions"] if normalized(s["question"]) == normalized(row["question"])
        )
        write_json(out / f"{options['summary_name']}.json", summary)

        self.stdout.write(json.dumps({k: summary[k] for k in ("refusedToday", "check", "time", "modelCalls")}, indent=1, ensure_ascii=False))
        for key, per_run in summary["ways"].items():
            self.stdout.write(
                f"{key}: useful {[r['useful'] for r in per_run]} of {per_run[0]['wronglyRefused']} "
                f"(before check {[r['usefulBeforeCheck'] for r in per_run]}); shown {[r['shown'] for r in per_run]}, "
                f"dead {[r['shownDead'] for r in per_run]}; must-refuse with suggestions {[len(r['mustRefuseWithSuggestions']) for r in per_run]}"
            )
