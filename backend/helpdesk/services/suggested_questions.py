"""Questions to suggest under a refusal: related questions the sources answer.

Plan an internal plan (kept outside the repository), step S0. Tools only: nothing in the app calls this module yet;
the command measure_suggested_questions measures the ways below against the plan's gate.

- Way 1, written from passages: every indexed source is searched for the question (the opt-in sources too, which
  an unscoped question does not search), and one controller-model call writes, for each of up to three of the
  passages found, one whole question that this passage answers and that is as close as possible to the user's
  question, in the user's language. The model gets the question and the passages (text and where they are from),
  nothing else. Any failure gives no suggestions.
- Way 2, earlier answered questions: the nearest questions of a pool (questions answered and validated before) by
  the embedding of the question. No model call.
- Way 3: way 2's first, then way 1's, each question once.
- Way 4, the source named in words (measured on its own): one controller-model call names up to three sources
  that may answer the question (as the scope options of C0 did) and restates the user's question with that source
  named in it. The suggestion is sent unscoped, so it goes through the screen like any question.

The check before showing (`cheap_check`) needs no model call: the suggestion, read as the app reads an unscoped
question, passes the keyword screen, and its search returns at least one passage at the score the app requires.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from urllib import request

from django.conf import settings

logger = logging.getLogger(__name__)

MAX_SUGGESTIONS = 3
PASSAGE_TOP_K = 6
PASSAGE_TEXT_CHARS = 900
MAX_QUESTION_CHARS = 300
# The answer view's default retrievalMinScore and the web page's retrievalTopK.
APP_MIN_SCORE = 0.62
APP_TOP_K = 6
WRITE_MAX_TOKENS = 500

_PROMPT = """You help the users of a helpdesk on European transport data standards (NeTEx, SIRI, OpRa, \
Transmodel, DATEX II, TN-ITS), the mobilityDCAT-AP metadata profile, the EU legislation on transport data, \
INSPIRE and NAPCORE's material. The helpdesk could not answer the user's question. Below are passages from its \
sources that a search found near the question. Suggest questions the user can ask instead, which these passages \
answer.

Rules:
- At most one question per passage, for at most three passages. Choose the passages closest to what the user asked.
- Each question must be answered by its own passage, from what the passage says. Never write a question the \
passage does not answer, and do not repeat the user's question when the passage does not answer it.
- Keep each question as close as possible to the user's question: the same subject and intent, in the terms the \
passage uses.
- Each question stands alone: it can be read and asked without the user's question, and names the standard, act \
or profile it is about.
- Write each question in {language}. Also give each in English.
- If no passage is about the subject of the user's question, suggest nothing.

Reply with JSON only: {{"suggestions": [{{"passage": <passage number>, "question": "<the question in {language}>", \
"english": "<the same question in English>"}}]}}"""


def normalized(text: str) -> str:
    """For comparing questions: case and whitespace folded, end punctuation dropped."""
    return " ".join((text or "").casefold().split()).rstrip(" ?!.")


def same_question(left: str, right: str) -> bool:
    return normalized(left) == normalized(right)


# ── Way 1: from passages near the question ──────────────────────────────────


def all_scopes() -> list[str]:
    """Every source the index holds, the opt-in ones too (retrieval_gateway._scope_query_filter: a scope list
    selects the chunks of any of its standards, so this one selects every chunk with a scope)."""
    from helpdesk.services.retrieval_gateway import CORE_SCOPES, OPT_IN_SCOPES

    return list(CORE_SCOPES) + list(OPT_IN_SCOPES)


def passages_near(question: str, english: str | None = None, top_k: int = PASSAGE_TOP_K) -> list[dict]:
    """The best passages of all sources for the question, at the score the app requires (none below it).

    english: the question's English rendering when it has one (the app has it from parsing the question); both
    are searched, as the app searches. With every source in the scope, the scope-coverage passes do not run
    (their condition is top_k >= the number of scopes)."""
    from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace

    chunks, _trace = retrieve_chunks_with_trace(
        question=question,
        top_k=top_k,
        min_score=APP_MIN_SCORE,
        scope=all_scopes(),
        graph_rag_enabled=bool(getattr(settings, "GRAPH_RAG_ENABLED", False)),
        min_results=0,
        english_question=english,
    )
    return [chunk for chunk in chunks if float(chunk.get("score") or 0.0) >= APP_MIN_SCORE][:top_k]


def _where_from(passage: dict) -> str:
    scope = ", ".join(passage.get("standardsScope") or []) or "unknown source"
    place = passage.get("sourcePath") or ""
    heading = (passage.get("heading") or passage.get("label") or "").strip()
    return f"{scope}: {place}" + (f" ({heading})" if heading and heading not in place else "")


def passage_messages(question: str, passages: list[dict], language: str | None) -> list[dict]:
    """The model call's messages: the task, then the user's question and the numbered passages."""
    language_name = language or "the language of the user's question"
    blocks = []
    for number, passage in enumerate(passages, start=1):
        text = " ".join((passage.get("text") or "").split())[:PASSAGE_TEXT_CHARS]
        blocks.append(f"[{number}] From {_where_from(passage)}\n{text}")
    user = f"User's question:\n{question}\n\nPassages:\n\n" + "\n\n".join(blocks)
    return [
        {"role": "system", "content": _PROMPT.format(language=language_name)},
        {"role": "user", "content": user},
    ]


_JSON_OBJECT = re.compile(r"\{.*\}", re.S)


def parse_written(content: str, passages: list[dict], original: str) -> list[dict]:
    """The model's suggestions, kept only where they are usable: a known passage, a question of reasonable length
    that is not the user's question, each question and each passage once, at most MAX_SUGGESTIONS."""
    match = _JSON_OBJECT.search(content or "")
    if not match:
        raise ValueError("reply holds no JSON object")
    items = json.loads(match.group(0)).get("suggestions")
    if not isinstance(items, list):
        raise ValueError("reply has no suggestions list")
    kept: list[dict] = []
    seen_questions: set[str] = set()
    seen_passages: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            number = int(item.get("passage"))
        except (TypeError, ValueError):
            continue
        question = " ".join(str(item.get("question") or "").split())
        english = " ".join(str(item.get("english") or "").split())
        if not (1 <= number <= len(passages)) or not question or len(question) > MAX_QUESTION_CHARS:
            continue
        if same_question(question, original) or normalized(question) in seen_questions or number in seen_passages:
            continue
        passage = passages[number - 1]
        seen_questions.add(normalized(question))
        seen_passages.add(number)
        kept.append(
            {
                "question": question,
                "english": english if english and len(english) <= MAX_QUESTION_CHARS else None,
                "way": "written",
                "passage": {
                    "repositoryUrl": passage.get("repositoryUrl"),
                    "sourcePath": passage.get("sourcePath"),
                    "standardsScope": passage.get("standardsScope") or [],
                },
            }
        )
        if len(kept) >= MAX_SUGGESTIONS:
            break
    return kept


def _model_reply(messages: list[dict]) -> str:
    """One controller-model call, as relevance_check makes it (Anthropic, or the HTTP gateway)."""
    from helpdesk.services.controller_llm import _build_ssl_context, _uses_anthropic, anthropic_controller_call
    from helpdesk.services.llm_model_recovery import resolve_effective_model
    from helpdesk.services.llm_options import controller_max_tokens, controller_request_options

    timeout = int(getattr(settings, "SUGGESTED_QUESTIONS_TIMEOUT_SECONDS", 10))
    if _uses_anthropic():
        payload = anthropic_controller_call(
            messages=messages,
            max_tokens=controller_max_tokens(WRITE_MAX_TOKENS),
            timeout_seconds=timeout,
            json_answer=True,
        )
        return payload["choices"][0]["message"]["content"]

    base_url = getattr(settings, "CONTROLLER_LLM_API_BASE_URL", "").strip()
    model = getattr(settings, "CONTROLLER_LLM_API_MODEL", "").strip()
    if not base_url or not model:
        raise ValueError("controller LLM is not configured")
    api_key = getattr(settings, "CONTROLLER_LLM_API_KEY", "").strip()
    effective_model = resolve_effective_model(
        api_base_url=base_url,
        api_key=api_key,
        configured_model=model,
        verify_ssl=getattr(settings, "CONTROLLER_LLM_VERIFY_SSL", True),
        ca_bundle=getattr(settings, "CONTROLLER_LLM_CA_BUNDLE", "").strip(),
        source="suggested_questions",
    )
    body = {
        "model": effective_model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": controller_max_tokens(WRITE_MAX_TOKENS),
        **controller_request_options(json_mode=True),
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    http_request = request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    with request.urlopen(http_request, timeout=timeout, context=_build_ssl_context()) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def written_suggestions(question: str, passages: list[dict], language: str | None = None) -> dict:
    """Way 1's model call. {"suggestions": [...], "calls": 0 or 1, "seconds": ..., "error": None or text};
    never raises. No passages: no call and no suggestions."""
    if not passages:
        return {"suggestions": [], "calls": 0, "seconds": 0.0, "error": None}
    started = time.perf_counter()
    try:
        content = _model_reply(passage_messages(question, passages, language))
        suggestions = parse_written(content, passages, question)
        error = None
    except Exception as exc:  # a failed call shows no suggestions, never an error
        logger.warning("Suggested questions: the model call failed", exc_info=True)
        suggestions, error = [], str(exc)[:200]
    return {"suggestions": suggestions, "calls": 1, "seconds": round(time.perf_counter() - started, 3), "error": error}


# ── Way 4: the source named in words ────────────────────────────────────────

# One line per source, as the scope options of C0 described them (measure_scope_options).
SOURCE_DESCRIPTIONS = {
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

_NAMED_PROMPT = """A helpdesk answers questions from the documentation of these sources:
{sources}

The helpdesk could not answer the user's question. Name at most three of these sources that most likely answer \
it, the most likely first. For each, restate the user's question so that it names that source in its words, \
changing nothing else about what is asked. Write each in {language}, and also give it in English. If none of \
the sources fits the question, name none.

Reply with JSON only: {{"suggestions": [{{"source": "<the source exactly as written before the colon>", \
"question": "<the question in {language}>", "english": "<the same question in English>"}}]}}"""


def named_messages(question: str, language: str | None) -> list[dict]:
    sources = "\n".join(f"- {name}: {description}" for name, description in SOURCE_DESCRIPTIONS.items())
    return [
        {"role": "system", "content": _NAMED_PROMPT.format(sources=sources, language=language or "the language of the user's question")},
        {"role": "user", "content": f"User's question:\n{question}"},
    ]


def parse_named(content: str, original: str) -> list[dict]:
    """The restated questions, kept where the source is one of the list and the question is not the user's own."""
    match = _JSON_OBJECT.search(content or "")
    if not match:
        raise ValueError("reply holds no JSON object")
    items = json.loads(match.group(0)).get("suggestions")
    if not isinstance(items, list):
        raise ValueError("reply has no suggestions list")
    kept: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "").strip()
        question = " ".join(str(item.get("question") or "").split())
        english = " ".join(str(item.get("english") or "").split())
        if source not in SOURCE_DESCRIPTIONS or not question or len(question) > MAX_QUESTION_CHARS:
            continue
        if same_question(question, original) or normalized(question) in seen:
            continue
        seen.add(normalized(question))
        kept.append({"question": question, "english": english or None, "way": "named", "source": source})
        if len(kept) >= MAX_SUGGESTIONS:
            break
    return kept


def named_suggestions(question: str, language: str | None = None) -> dict:
    """Way 4's model call, as written_suggestions; never raises."""
    started = time.perf_counter()
    try:
        suggestions = parse_named(_model_reply(named_messages(question, language)), question)
        error = None
    except Exception as exc:
        logger.warning("Suggested questions: the model call failed", exc_info=True)
        suggestions, error = [], str(exc)[:200]
    return {"suggestions": suggestions, "calls": 1, "seconds": round(time.perf_counter() - started, 3), "error": error}


# ── Way 2: earlier answered questions ───────────────────────────────────────


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


def nearest_answered(question: str, embedding: list[float], pool: list[dict], limit: int = MAX_SUGGESTIONS) -> list[dict]:
    """The pool's questions nearest to the question by embedding, not the question itself, each once.

    pool: [{"question": ..., "embedding": [...]}], the questions answered, validated and not disliked before."""
    scored = sorted(
        ((_cosine(embedding, entry["embedding"]), entry) for entry in pool if entry.get("embedding")),
        key=lambda pair: pair[0],
        reverse=True,
    )
    kept: list[dict] = []
    seen = {normalized(question)}
    for similarity, entry in scored:
        key = normalized(entry["question"])
        if key in seen:
            continue
        seen.add(key)
        kept.append({"question": entry["question"], "english": None, "way": "earlier", "similarity": round(similarity, 4)})
        if len(kept) >= limit:
            break
    return kept


# ── Way 3 ───────────────────────────────────────────────────────────────────


def combined(earlier: list[dict], written: list[dict], limit: int = MAX_SUGGESTIONS) -> list[dict]:
    """Earlier answered questions first, then written ones, each question once."""
    kept: list[dict] = []
    seen: set[str] = set()
    for suggestion in list(earlier) + list(written):
        key = normalized(suggestion["question"])
        if key in seen:
            continue
        seen.add(key)
        kept.append(suggestion)
        if len(kept) >= limit:
            break
    return kept


# ── The check before showing ────────────────────────────────────────────────


def _parse_strength(semantic_query) -> tuple[int, bool]:
    """As api.views._parse_strength: more scopes first, then whether a concept matched."""
    from helpdesk.services.question_parsing import UNKNOWN_CONCEPT_SENTINEL

    return len(semantic_query.candidate_standards), semantic_query.core_concept != UNKNOWN_CONCEPT_SENTINEL


def cheap_check(question: str, english: str | None = None) -> dict:
    """Whether the app would get as far as answering the suggestion, judged without a model call.

    The suggestion is read as the app reads an unscoped question (api.views._parse_question, with the given
    English rendering instead of a model call), must pass the keyword rules of the screen (without the second
    opinion, which is a model call), and its search (scope as the app selects it) must return at least one
    passage at the app's score. The answer model's own verdict is not predicted here."""
    from helpdesk.services.question_parsing import parse_question_to_semantic_query, select_effective_scope
    from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace
    from helpdesk.services.semantic_abstention import _keyword_rule_message

    started = time.perf_counter()
    english = english if english and not same_question(english, question) else None
    semantic_query = parse_question_to_semantic_query(text=question, requested_scope=[])
    if english:
        english_query = parse_question_to_semantic_query(text=english, requested_scope=[])
        if _parse_strength(english_query) > _parse_strength(semantic_query):
            semantic_query = english_query
    scope, _ = select_effective_scope(semantic_query, [])
    screen = _keyword_rule_message(semantic_query=semantic_query, effective_scope=scope, requested_scope=[]) is None
    above = 0
    if screen:
        chunks, _trace = retrieve_chunks_with_trace(
            question=question,
            top_k=APP_TOP_K,
            min_score=APP_MIN_SCORE,
            scope=scope,
            graph_rag_enabled=bool(getattr(settings, "GRAPH_RAG_ENABLED", False)),
            min_results=0,
            english_question=english,
        )
        above = sum(1 for chunk in chunks if float(chunk.get("score") or 0.0) >= APP_MIN_SCORE)
    return {
        "passed": bool(screen and above),
        "screen": screen,
        "passagesAboveScore": above,
        "scope": list(scope or []),
        "seconds": round(time.perf_counter() - started, 3),
    }
