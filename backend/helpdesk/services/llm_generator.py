"""
LLM-based answer generation with synchronous and SSE streaming support.

Calls an OpenAI-compatible chat completion endpoint to synthesize answers
grounded in retrieved evidence chunks. Streaming delegates token deltas via
Server-Sent Events written directly into the Django response.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-29  |  Modified: 2026-06-28
"""

from __future__ import annotations

import json
from collections import OrderedDict
import logging
import re
import ssl
from collections.abc import Generator
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)

from helpdesk.services import anthropic_chat
from helpdesk.services.llm_options import answer_max_tokens, answer_request_options
from helpdesk.services.service_abbreviations import services_in_question
from helpdesk.services.question_preprocessor import (
    LANGDETECT_LANGUAGE_NAMES,
    detect_question_language,
    natural_word_count,
)
from helpdesk.services.llm_model_recovery import (
    extract_authorized_model,
    remember_correction,
    resolve_effective_model,
)


# An answer whose retry also failed validation is still served (e7dbeb4, d1950a9: a real on-topic answer beats
# the generic template), but it must not look like a validated one. It goes to editorial review and its
# confidence is capped below the review threshold (0.82) yet above the 0.72 at which views label an answer
# LOW_RETRIEVAL_CONFIDENCE: retrieval was fine, the answer failed validation.
UNVALIDATED_ANSWER_MAX_CONFIDENCE = 0.80


class LLMGenerationError(Exception):
    """Raised when LLM generation cannot be completed safely."""


FENCED_CODE_BLOCK_PATTERN = re.compile(r"```([A-Za-z0-9_+-]*)\n(.*?)```", re.DOTALL)
CITATION_PATTERN = re.compile(r"\[E(\d+)\]")


def _is_github_models_base_url(api_base_url: str) -> bool:
    base = (api_base_url or "").strip().lower()
    return "models.inference.ai.azure.com" in base


def _question_requests_verbatim_example(question: str) -> bool:
    question_lower = question.lower()
    asks_for_example = any(term in question_lower for term in ["example", "sample", "snippet"])
    asks_for_code = any(term in question_lower for term in ["xml", "json", "yaml", "code"])
    return asks_for_example and asks_for_code


_DEFINITION_QUESTION_RE = re.compile(r"\b(what\s+is|what\s+are|define|definition\s+of|meaning\s+of)\b")
_NOT_PURE_DEFINITION_TERMS = ("example", "sample", "snippet", "xml", "json", "yaml", "code", "show", "structure", "how")


def _question_asks_for_definition(question: str) -> bool:
    """True for "what is X?" questions that do not ask for examples, code or structure."""

    question_lower = question.lower()
    if not _DEFINITION_QUESTION_RE.search(question_lower):
        return False
    return not any(term in question_lower for term in _NOT_PURE_DEFINITION_TERMS)


def _question_about_xml_or_technical(question: str) -> bool:
    question_lower = question.lower()
    mentions_standard = any(term in question_lower for term in ["xml", "netex", "siri", "opra", "transmodel", "json", "code"])
    asks_how_or_explain = any(term in question_lower for term in ["how", "show", "what is", "explain", "example", "structure"])
    return mentions_standard or asks_how_or_explain


def _normalize_grounded_line(line: str) -> str:
    return " ".join(line.strip().lower().split())


def _extract_grounded_lines(text: str) -> set[str]:
    grounded_lines: set[str] = set()
    for raw_line in (text or "").splitlines():
        normalized = _normalize_grounded_line(raw_line)
        if len(normalized) < 8:
            continue
        if not any(marker in normalized for marker in ["<", ">", "/", "="]):
            continue
        grounded_lines.add(normalized)
    return grounded_lines


def _validate_grounded_example_output(question: str, answer: str, chunks: list[dict], shown_fragment: str = "") -> None:
    if not _question_requests_verbatim_example(question):
        return

    code_blocks = FENCED_CODE_BLOCK_PATTERN.findall(answer or "")
    if not code_blocks:
        return

    evidence_lines: set[str] = set()
    for chunk in chunks:
        evidence_lines.update(_extract_grounded_lines(str(chunk.get("text", ""))))
    # The example shown above the answer is verbatim from the standard's files (or validated against the
    # schema): quoting it is not fabrication. It is no evidence chunk, so quoting it was rejected and the
    # whole answer dropped (lift question, 2026-11-09).
    evidence_lines.update(_extract_grounded_lines(shown_fragment or ""))

    for language, block in code_blocks:
        normalized_language = (language or "").strip().lower()
        if normalized_language and normalized_language not in {"xml", "json", "yaml", "yml", "txt"}:
            continue

        block_lines = [
            _normalize_grounded_line(line)
            for line in block.splitlines()
            if len(_normalize_grounded_line(line)) >= 8
            and any(marker in line for marker in ["<", ">", "/", "="])
            and line.strip() != OMISSION_MARKER  # added by complete_xml_elements, not quoted
        ]
        if not block_lines:
            continue

        matched_lines = sum(1 for line in block_lines if line in evidence_lines)
        if matched_lines < max(3, (len(block_lines) * 2 + 2) // 3):
            raise LLMGenerationError(
                "Generated example block is not grounded in retrieved evidence; refusing fabricated XML/example output."
            )


def _fix_out_of_range_citations(answer: str, max_chunk_idx: int) -> str:
    """Replace out-of-range citations with valid ones or remove them.

    If LLM hallucinates [E10] when only [E1-E6] exist, map [E10] to [E6]
    (the most recent valid citation) or remove the citation if it's the only content.
    """
    def replace_citation(match):
        citation_num = int(match.group(1))
        if citation_num > max_chunk_idx:
            # Map invalid citation to the nearest valid one
            valid_num = max(1, min(citation_num, max_chunk_idx))
            logger.info(f"[FIX_CITATION] Mapping [E{citation_num}] to [E{valid_num}] (max valid: {max_chunk_idx})")
            return f"[E{valid_num}]"
        return match.group(0)

    return re.sub(r"\[E(\d+)\]", replace_citation, answer)


def _validate_citations_to_chunks(answer: str, chunks: list[dict]) -> None:
    """
    Verify that each [E#] citation references a valid chunk index (1 to N).
    """
    citations = CITATION_PATTERN.findall(answer)
    if not citations:
        return  # No citations, nothing to validate

    max_chunk_idx = len(chunks)
    for citation_str in set(citations):
        try:
            citation_num = int(citation_str)
            if citation_num < 1 or citation_num > max_chunk_idx:
                raise LLMGenerationError(
                    f"Citation [E{citation_num}] is out of range. Valid citations: [E1] through [E{max_chunk_idx}]."
                )
        except ValueError as e:
            raise LLMGenerationError(f"Invalid citation format: {e}")


# Strong terms: specific enough that a match is meaningful evidence of grounding.
# Code spans are paired in order (see _code_spans): a pattern alternative could pair the closing backtick
# of one span with the opening backtick of the next and turn ") and departure (" into a term.
_CODE_SPAN_PATTERN = re.compile(r"`([^`\n]+)`")
_STRONG_TERM_PATTERN = re.compile(
    r'"([A-Za-z0-9_.:/\\@#-]{6,})"'                  # double-quoted technical strings (≥6 chars)
    r"|([A-Za-z][A-Za-z0-9]+:[A-Za-z0-9@_./-]{3,})"  # namespaced ids, e.g. stg:SCWW@86, netex:Line (not times like 14:32)
    r"|([A-Z0-9][A-Za-z0-9_.-]*-[A-Za-z0-9_.-]*[A-Z0-9])"  # hyphenated IDs with uppercase/digits, e.g. SCWW-86, UK-2022, 93-RED-y11-1
    r"|([A-Za-z0-9_-]+\.(?:xsd|xml|yaml|json|ttl))"  # file names with known extensions
    r"|((?:Article|Annex)\s+[0-9IVX]+(?:\(\w{1,4}\))*)"   # legal references, e.g. Article 4(1)(b), Annex II
    r"|(\(EU\)\s+(?:No\s+)?\d{2,4}/\d+|\d{4}/\d+/EU)"   # act numbers, e.g. (EU) 2017/1926, 2010/40/EU
    r"|((?:CEN/TS|CEN/TR|prEN|EN|ISO(?:/IEC)?|ETSI\s+(?:EN|TS))\s+\d{3,6}(?:-\d+)*(?::\d{4})?)"  # standards, e.g. EN 12896, CEN/TS 16614-1:2025
)

# A quotation of at least three words, in straight or typographic double quotes. Found verbatim in the cited
# block it is the strongest grounding there is, even when every word in it is a common one.
_QUOTATION_PATTERN = re.compile(r'["“]([^"“”]+?\s+[^"“”]+?\s+[^"“”]+?)["”]')


def _quotation_found(sentence: str, chunks: list[dict]) -> bool:
    """Whether a quotation in the sentence appears verbatim in one of the chunks."""
    quotes = [_comparable(q.strip(" .,;:")) for q in _QUOTATION_PATTERN.findall(sentence)]
    if not quotes:
        return False
    haystacks = [_comparable(str(chunk.get("text", ""))) for chunk in chunks]
    return any(quote and quote in haystack for quote in quotes for haystack in haystacks)

# Weak terms: PascalCase element names (single or multi-word) and ALL-CAPS
# Transmodel concept names, which the standards write in capitals by convention
# (e.g. "STOP PLACE", "TAXI RANK", "VEHICLE MEETING POINT").
# Matches: Time, Departure, DepartureTime, ScheduledStop, STOP PLACE, etc.
_WEAK_TERM_PATTERN = re.compile(
    r"\b([A-Z]{3,}(?:\s+[A-Z]{3,})*"      # ALL-CAPS Transmodel concepts, single or multi-word, whole words
    r"|[A-Z][a-z]+(?:[A-Z][a-z]+)*)\b"    # PascalCase: starts with uppercase, followed by lowercase(s)
)

# A single capitalised word is an element name ("Departure") only where English would not capitalise it
# anyway: not at the start of a sentence, list item, heading or bold label ("**What it measures:**"), and
# not a common English word. Otherwise "What", "This" or "None" were checked against the evidence.
_SENTENCE_START_BEFORE = re.compile(r"(?:^|[.!?:;]\s+|[-*•]\s+|\*\*\s*|\(\s*|[\"“'‘]\s*)$")
_COMMON_CAPITALISED_WORDS = frozenset(
    "a an the this that these those there their they it its what which who whom whose where when why how "
    "none some any each every all both other others another such same also only however therefore thus "
    "according based note see example examples here in on at for from with without into by of as if "
    "yes no not and or but so because while although though since unlike like".split()
)

# Terms so generic they appear in virtually every NeTEx/standards document and
# must never be used as the sole grounding evidence for a citation. This is a
# static list (no live ontology lookup); the labels/altLabels of every upper-ontology
# concept, pluralized, plus a small set of cross-standard names.
_UBIQUITOUS_TERMS = frozenset({
    "netex", "opra", "siri", "transmodel",
    "line", "lines", "route", "routes", "stop", "stops",
    "trip", "trips", "service", "services", "journey", "journeys",
    "network", "networks", "operator", "operators", "pattern", "patterns",
    "actor", "actors", "applies to network", "applies to networks",
    "authority", "authoritys", "belongs to ecosystem", "belongs to ecosystems",
    "characterises service", "characterises services", "consists of", "consists ofs",
    "data artifact", "data artifacts", "data consumer", "data consumers",
    "data exchange", "data exchanges", "data publisher", "data publishers",
    "data set", "data sets", "describes specification", "describes specifications",
    "disruption", "disruptions", "disturbance", "disturbances",
    "domain concept", "domain concepts", "event", "events",
    "exchanged between", "exchanged betweens", "governs",
    "has specification ontology", "has specification ontologys", "involves",
    "journey component", "journey components", "journey pattern", "journey patterns",
    "location", "locations", "netex ontology", "netex ontologys", "netexs",
    "operational intensity", "operational intensitys", "operational process",
    "opra ontology", "opra ontologys", "opras",
    "organisation", "organisations", "organization", "organizations",
    "process", "produces", "profile", "profiles", "provides",
    "public transport line", "public transport lines",
    "real-time information", "real-time informations",
    "responsibility", "responsibilitys", "role", "roles",
    "route line", "route lines", "schedule", "scheduled stop point",
    "scheduled stop points", "schedules",
    "service intensity", "service intensitys", "service metric", "service metrics",
    "siri ontology", "siri ontologys", "siris",
    "situation", "situations", "spatial entity", "spatial entitys",
    "specification ontology", "specification ontologys",
    "standards ecosystem", "standards ecosystems",
    "stop point", "stop points", "stopping place", "stopping places",
    "system", "systems", "technical specification", "technical specifications",
    "temporal entity", "temporal entitys", "timetable", "timetables",
    "transmodel ecosystem", "transmodel ecosystems",
    "transmodel ontology", "transmodel ontologys", "transmodels",
    "transport journey", "transport journey pattern", "transport journey patterns",
    "transport journeys", "transport line", "transport lines",
    "transport network", "transport networks", "uses",
})


def _classify_terms(sentence: str) -> tuple[list[str], list[str]]:
    """
    Return (strong_terms, weak_terms) extracted from a sentence.

    Strong terms are specific identifiers unlikely to appear across many chunks
    (file names, namespaced IDs, hyphenated IDs, backtick-quoted strings).
    Weak terms are PascalCase/camelCase element names that may appear anywhere.
    """
    strong: list[str] = []
    # Code spans first, paired in order. A backticked name is an identifier even when it is a common word
    # (`Journey` is a NeTEx element), so the ubiquitous-term filter does not apply to it.
    for span in _CODE_SPAN_PATTERN.findall(sentence):
        span = span.strip().strip("<>/").strip()
        if len(span) >= 4:
            strong.append(span)
    sentence = _CODE_SPAN_PATTERN.sub(" ", sentence)

    # Strip XML/HTML tag brackets but keep content so element names are found
    # e.g., "<Departure>" becomes " Departure "
    clean_sentence = re.sub(r"[<>]", " ", sentence)

    for match in _STRONG_TERM_PATTERN.finditer(clean_sentence):
        term = next((g for g in match.groups() if g), None)
        term = term.rstrip(".") if term else term  # "netex:Line." at the end of a sentence
        if term and len(term) >= 4 and term.lower() not in _UBIQUITOUS_TERMS:
            strong.append(term)

    weak: list[str] = []
    seen = set(t.lower() for t in strong)
    for match in _WEAK_TERM_PATTERN.finditer(clean_sentence):
        term = match.group(1)
        if not term or len(term) < 4 or term.lower() in _UBIQUITOUS_TERMS or term.lower() in seen:
            continue
        single_word = term[0].isupper() and term[1:].islower()
        if single_word and (
            term.lower() in _COMMON_CAPITALISED_WORDS
            or _SENTENCE_START_BEFORE.search(clean_sentence[: match.start()])
        ):
            continue
        weak.append(term)
        seen.add(term.lower())

    return list(dict.fromkeys(strong)), list(dict.fromkeys(weak))


def _extract_key_terms(sentence: str) -> list[str]:
    """Extract technical identifiers from a sentence for citation grounding checks."""
    strong, weak = _classify_terms(sentence)
    return list(dict.fromkeys(strong + weak))


# Article/annex references in the languages answers are written in; the number is checked against the chunk.
_LEGAL_REFERENCE_PATTERN = re.compile(
    r"\b(?:article|artikel|art\.|articolo|art[ií]culo|člen\w*|annex|anhang|annexe|allegato|anexo|prilog\w*)"
    r"\s+([0-9]+|[IVX]+)\b",
    re.IGNORECASE,
)
_QUOTED_SPAN_PATTERN = re.compile(r"[\"“‘'„«]([^\"”’'“»]{12,})[\"”’'“»]")
_CONTENT_WORD_PATTERN = re.compile(r"[^\W\d_]{4,}")


def _is_regulation_chunk(chunk: dict) -> bool:
    return (chunk.get("docType") or chunk.get("doc_type")) == "regulation"


def _is_napcore_chunk(chunk: dict) -> bool:
    return (chunk.get("docType") or chunk.get("doc_type")) == "napcore"


def _is_prose_chunk(chunk: dict) -> bool:
    """Legislation and NAPCORE documents: prose without element names, grounded by quotes and shared words."""
    return _is_regulation_chunk(chunk) or _is_napcore_chunk(chunk)


def _has_legislation_evidence(chunks: list[dict], max_chunks: int) -> bool:
    return any(_is_regulation_chunk(chunk) for chunk in chunks[:max_chunks])


def _has_napcore_evidence(chunks: list[dict], max_chunks: int) -> bool:
    return any(_is_napcore_chunk(chunk) for chunk in chunks[:max_chunks])


def _has_prose_evidence(chunks: list[dict], max_chunks: int) -> bool:
    return any(_is_prose_chunk(chunk) for chunk in chunks[:max_chunks])


# Tokens that survive translation: acronyms (NAP, ITS), act numbers (2017/1926) and other numbers.
_DISTINCTIVE_TOKEN_PATTERN = re.compile(r"\b(?:[A-Z]{2,}[A-Z0-9]*|\d{4}/\d+(?:/[A-Z]+)?|\d{3,})\b")


def _regulation_citation_grounded(sentence: str, chunk: dict) -> bool:
    """Whether a sentence citing an EU legislation chunk is supported by it (issue #91).

    Legal prose has no element names, so the term checks used for standards evidence do not apply. A
    sentence that names an article or annex number must name one the chunk is or mentions. Otherwise the
    sentence is grounded when it quotes at least three
    words of the chunk verbatim, shares two distinctive tokens with it (acronyms, act numbers: these
    survive translation), or shares at least 40% of its content words with it.
    """
    text = str(chunk.get("text", "")).lower()
    anchor = str(chunk.get("sourcePath", "")).lower().rsplit("#", 1)[-1]
    # A sentence that names an article or annex must name one the cited block is, or mentions: a right
    # quote under a wrong article number ("Article 4(4)" for a quote from Article 3(4)) is still wrong.
    numbers = [number.lower() for number in _LEGAL_REFERENCE_PATTERN.findall(sentence)]
    if numbers:
        return any(
            anchor in (f"art_{number}", f"anx_{number}") or f"article {number}" in text or f"annex {number}" in text
            for number in numbers
        )
    for quoted in _QUOTED_SPAN_PATTERN.findall(sentence):
        if len(quoted.split()) >= 3 and re.sub(r"\s+", " ", quoted.strip().lower()) in text:
            return True
    # An answer in another language paraphrases the English text; its acronyms and numbers stay the same.
    # Only the body counts: the act's own name and number head every chunk of that act.
    body = str(chunk.get("text", "")).split("\n", 1)[-1]
    if len({t for t in _DISTINCTIVE_TOKEN_PATTERN.findall(sentence) if t in body}) >= 2:
        return True
    words = {word.lower() for word in _CONTENT_WORD_PATTERN.findall(sentence)}
    if not words:
        return False
    return sum(1 for word in words if word in text) / len(words) >= 0.4


# A sentence about the evidence itself ("The evidence contains no formal definition", "[E2] and [E3] concern
# fare structures, so they do not answer the question") has no technical term to check and must not be
# rejected for it: the prompt asks the model to say what the evidence does not cover.
_EVIDENCE_NOUN = re.compile(
    r"\b(?:evidence|blocks?|excerpts?|examples?|definitions?|documentation|snippets?|sources?|schemas?|files?"
    r"|documented|described|describes?|defined|shown|listed|mentioned|descriptions?"
    r"|cited\s+(?:text|passage|provision|document)s?)\b",
    re.IGNORECASE,
)
_LIMIT_WORD = re.compile(
    r"\b(?:not|no|none|nothing|only|cannot|can't|doesn't|don't|isn't|aren't|without|truncated|lacks?|missing)\b",
    re.IGNORECASE,
)
_LEADING_CITATION = re.compile(r"^\s*(?:[-*•]\s+)?(?:\*\*)?\s*\[E\d+\]")


def _is_evidence_scope_statement(text: str) -> bool:
    """True for a sentence that describes the evidence's coverage, not a technical claim."""
    if _LEADING_CITATION.match(text):
        return True  # "[E2] is an example of an estimated timetable response."
    plain = CITATION_PATTERN.sub(" ", text)
    mentions_evidence = bool(_EVIDENCE_NOUN.search(plain)) or len(CITATION_PATTERN.findall(text)) > 1
    return mentions_evidence and bool(_LIMIT_WORD.search(plain))


# A citation followed by one of these is the subject of what follows: "[E1] describes GroupSave ticket
# discount conditions, [E2] discusses FARE PRICE".
_SUBJECT_CITATION_VERB = re.compile(
    r"^\s*\)?\s*(?:is|are|was|were|describes?|discusses?|concerns?|covers?|contains?|shows?|mentions?|defines?"
    r"|gives?|provides?|has|have|lists?|only|also|documents?|presents?|refers?)\b",
    re.IGNORECASE,
)


def _comparable(text: str) -> str:
    return re.sub(r"[\s_-]+", " ", text.lower())


def _has_words(text: str) -> bool:
    return bool(re.search(r"[^\W\d_]", text))


def _citation_segments(sentence: str) -> list[tuple[str, str]]:
    """(citation number, the text that citation supports).

    Normally the text since the previous citation: in "...a JOURNEY" [E1]; the SIRI element
    `AimedLatestPassengerAccessTime` [E3]" the element belongs to [E3], not [E1]. A citation used as a subject
    ("[E2] discusses FARE PRICE") or standing first supports the text after it; one that directly follows
    another ("`AbstractObject` [E1][E2]") shares that one's text; failing all, the whole sentence.
    """
    matches = list(CITATION_PATTERN.finditer(sentence))
    segments: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        previous_end = matches[index - 1].end() if index else 0
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(sentence)
        before = sentence[previous_end : match.start()]
        after = sentence[match.end() : next_start]
        if _SUBJECT_CITATION_VERB.match(after) and _has_words(after):
            own = after
        elif _has_words(before):
            own = before
        elif index and segments:
            own = segments[-1][1]  # "[E1][E2]": the same text
        elif _has_words(after):
            own = after  # a leading citation: "[E3] This block is an example, not the definition."
        else:
            own = CITATION_PATTERN.sub(" ", sentence)
        segments.append((match.group(1), own))
    return segments


# Share of a plain sentence's content words that its cited block must contain. A sentence that says in
# plain words what a definition or documentation says ("A journey pattern is an ordered list of scheduled
# stop points and timing points on a single route [E1]") names no element and was rejected as unspecific,
# although every word is the block's own (local replay 2026-11-07, see PLAIN_SENTENCE_MIN_OVERLAP use).
PLAIN_SENTENCE_MIN_OVERLAP = 0.6


def _plain_sentence_grounded(sentence: str, cited_chunks: list[dict]) -> bool:
    """Whether each citation's own text in a sentence without technical terms is worded from its block.

    Each citation is judged on the text it supports (_citation_segments); at least
    PLAIN_SENTENCE_MIN_OVERLAP of its content words (four or more letters) must occur in the cited block.
    """
    if not cited_chunks:
        return False
    segments = _citation_segments(sentence)
    if len(segments) != len(cited_chunks):
        segments = [("", CITATION_PATTERN.sub(" ", sentence))] * len(cited_chunks)
    for (_, own), chunk in zip(segments, cited_chunks):
        words = {word.lower() for word in _CONTENT_WORD_PATTERN.findall(CITATION_PATTERN.sub(" ", own))}
        if len(words) < 3:
            words = {word.lower() for word in _CONTENT_WORD_PATTERN.findall(CITATION_PATTERN.sub(" ", sentence))}
        if not words:
            return False
        text = str(chunk.get("text", "")).lower()
        if sum(1 for word in words if word in text) / len(words) < PLAIN_SENTENCE_MIN_OVERLAP:
            return False
        # Common words ("default", "false", "journey") occur in many blocks; three words in a row from the
        # sentence occur in the block it was worded from, rarely in another.
        if not _shares_word_run(own if len(_PLAIN_WORD.findall(own)) >= 3 else sentence, text):
            return False
    return True


_PLAIN_WORD = re.compile(r"[^\W_]+")


def _shares_word_run(sentence: str, text: str, length: int = 3) -> bool:
    """Whether `length` consecutive words of the sentence occur, in order and adjacent, in the text."""
    words = _PLAIN_WORD.findall(CITATION_PATTERN.sub(" ", sentence).lower())
    text_words = " " + " ".join(_PLAIN_WORD.findall(text)) + " "
    return any(f" {' '.join(words[i:i + length])} " in text_words for i in range(len(words) - length + 1))


def _validate_citation_grounding(answer: str, chunks: list[dict]) -> None:
    """
    Verify that each [E#] citation is grounded in the referenced chunk's text.

    For every sentence containing [E#] citations the check requires:
    - If the sentence contains STRONG terms (file names, namespaced/hyphenated
      IDs): at least one strong term must appear in the cited chunk. A match on
      only weak/generic terms (e.g. "NeTEx", "LineRef") is NOT sufficient when
      strong terms are present — this prevents hallucinated file names from
      passing because a generic standard name happens to match.
    - If the sentence contains ONLY weak terms: at least one weak term must
      appear in the cited chunk.

    Raises LLMGenerationError if a citation cannot be grounded.
    """
    # Split on sentence boundaries; keep trailing punctuation with its sentence.
    # `)` is deliberately not a boundary: splitting after a parenthetical like
    # "(e.g., a station)" orphans the rest of the sentence from its subject and
    # produces fragments that fail grounding checks spuriously.
    sentences = re.split(r"(?<=[.!?])\s+", answer.replace("\n", " "))

    for sentence in sentences:
        found_citations = CITATION_PATTERN.findall(sentence)
        if not found_citations:
            continue

        clean = CITATION_PATTERN.sub("", sentence)
        if not re.search(r"[^\W\d_]", clean):
            continue  # A citation on its own ("[E3].") supports the sentence before it.

        # Check if sentence contains code blocks (```) or XML tags - these are more lenient
        is_code_block = "```" in sentence or ("<" in sentence and ">" in sentence)

        # CRITICAL: For code blocks (XML/code examples), skip strict grounding validation
        # XML with specific values (e.g., <DepartureTime>09:54:00</DepartureTime>) should not fail
        # just because the exact value isn't in the evidence. The element name is sufficient proof.
        if is_code_block and found_citations:
            logger.debug(f"Accepting code block citation without strict grounding: {sentence[:100]}")
            continue  # Skip to next sentence - code blocks are inherently technical

        cited_chunks = [chunks[int(c) - 1] for c in found_citations if 0 < int(c) <= len(chunks)]
        if cited_chunks and all(_is_prose_chunk(chunk) for chunk in cited_chunks):
            # "The cited text in [E3] does not describe Transmodel." says what a block does not cover; it has
            # nothing of its own to ground, as for standards evidence below.
            if _is_evidence_scope_statement(sentence):
                continue
            # Each citation is checked against its own text only: a quote that ends in `." [E1]` is no
            # sentence boundary for the split above, so one "sentence" can carry an act's quote [E1] and a
            # NAPCORE page's quote [E2], and the whole of it matches neither block.
            segments = _citation_segments(sentence)
            for position, (citation_str, chunk) in enumerate(zip(found_citations, cited_chunks)):
                own = CITATION_PATTERN.sub("", segments[position][1]) if position < len(segments) else ""
                if _regulation_citation_grounded(own if _has_words(own) else clean, chunk):
                    continue
                if _is_napcore_chunk(chunk):
                    raise LLMGenerationError(
                        f"Citation [E{citation_str}] does not ground the claim: '{sentence[:150].strip()}'. "
                        f"The cited block [E{citation_str}] is the NAPCORE document "
                        f"'{str(chunk.get('heading') or chunk.get('sourcePath', 'unknown'))[:80]}': quote its wording "
                        "verbatim, or cite the block that states it."
                    )
                # Say which provision the block is: told only "name the article", the model repeated a
                # paragraph number as the article number.
                provision = str(chunk.get("heading") or chunk.get("sourcePath", "unknown")).split(" — ")[0]
                raise LLMGenerationError(
                    f"Citation [E{citation_str}] does not ground the claim: '{sentence[:150].strip()}'. "
                    f"The cited block [E{citation_str}] is {provision}: name that article with its own number "
                    "(a numbered paragraph inside it is not an article number), quote the provision verbatim, "
                    "or cite the block that states it."
                )
            continue

        strong_terms, weak_terms = _classify_terms(clean)

        # Extract ubiquitous terms that were filtered out (we still want to check these)
        ubiquitous_terms = []
        for term in clean.split():
            term_clean = term.strip('.,!?;:').lower()
            if term_clean in _UBIQUITOUS_TERMS and len(term_clean) >= 4:
                ubiquitous_terms.append(term_clean)

        # CRITICAL: Cited sentences MUST have specific technical content (strong or weak terms),
        # unless the sentence only describes what the evidence covers.
        if not strong_terms and not weak_terms:
            if _is_evidence_scope_statement(sentence):
                continue
            if _quotation_found(sentence, cited_chunks):
                continue  # 'The block states that "Many NeTEx concepts are taken directly from Transmodel" [E3].'
            if _plain_sentence_grounded(sentence, cited_chunks):
                continue  # "A journey pattern is an ordered list of scheduled stop points ... [E1]."
            if found_citations:  # Has citations but NO specific terms = potential hallucination
                # No citations, no terms, not code = hallucination
                raise LLMGenerationError(
                    f"Citation [E{found_citations[0]}] without specific technical content: "
                    f"'{sentence[:120].strip()}'. "
                    "Cited claims must reference specific file names, IDs, or concepts from evidence, "
                    "not generic language like 'follow the specification' or 'validate with examples'."
                )
            else:
                continue  # No citations, no terms - skip

        for citation_str, segment in _citation_segments(sentence):
            idx = int(citation_str) - 1
            if idx < 0 or idx >= len(chunks):
                continue  # Range already rejected by _validate_citations_to_chunks
            if _is_evidence_scope_statement(segment):
                continue  # "EstimatedCall: the evidence contains no formal definition [E1]" names what is absent.
            segment_strong, segment_weak = _classify_terms(segment)
            if segment_strong or segment_weak:
                strong_terms, weak_terms = segment_strong, segment_weak
            elif _is_evidence_scope_statement(sentence):
                continue  # "The evidence blocks [E1] through [E4] cover only ...": nothing of its own to check.
            else:
                strong_terms, weak_terms = _classify_terms(clean)

            chunk = chunks[idx]
            # "_", "-" and spaces compare equal: "TAP TSI" names the source path tap_tsi.
            haystack = _comparable(str(chunk.get("text", "")) + " " + str(chunk.get("sourcePath", "")))

            if strong_terms:
                # Strong terms present: require at least one strong match.
                # A weak-only match is not accepted — it would allow hallucinated
                # file names/IDs to pass because a generic term like "NeTEx" matches.
                grounded = any(_comparable(term) in haystack for term in strong_terms)
                if not grounded:
                    logger.debug(
                        f"Citation [E{citation_str}] grounding check FAILED: strong terms {strong_terms} not found in chunk source '{chunk.get('sourcePath', 'unknown')}'"
                    )
            elif weak_terms:
                grounded = any(_comparable(term) in haystack for term in weak_terms)
                if not grounded:
                    logger.debug(
                        f"Citation [E{citation_str}] grounding check FAILED: weak terms {weak_terms} not found in chunk source '{chunk.get('sourcePath', 'unknown')}'"
                    )
            else:
                # No strong or weak terms; check ubiquitous terms (these are more lenient)
                # Ubiquitous terms appear everywhere, so we just require at least one match
                grounded = any(_comparable(term) in haystack for term in ubiquitous_terms)
                if not grounded:
                    logger.debug(
                        f"Citation [E{citation_str}] grounding check FAILED: ubiquitous terms {ubiquitous_terms} not found in chunk source '{chunk.get('sourcePath', 'unknown')}'"
                    )

            if not grounded:
                all_checked_terms = strong_terms + weak_terms + ubiquitous_terms
                raise LLMGenerationError(
                    f"Citation [E{citation_str}] does not ground the claim: "
                    f"'{sentence[:150].strip()}'. "
                    f"Cited chunk source: '{chunk.get('sourcePath', 'unknown')}'. "
                    f"Terms checked: {all_checked_terms[:4]}. "
                    "The LLM may have cited the wrong evidence block or hallucinated content."
                )


# Element names start with a capital (StopPlace, LiftEquipment); a backticked value such as `indoors` or `true`
# is not an element (2026-11-09: "a `Covered` value (both are `indoors`)" was rejected as a claim about `indoors`).
_XML_ELEMENT_MENTION_PATTERN = re.compile(r"[<`]([A-Z][A-Za-z0-9]*)[>`]")

# Phrases that attribute a semantic purpose/meaning to an XML element. An
# element's own name is not its definition (e.g. "TimeDemandTypeRef" sounds
# like it marks demand-responsive service, but in Transmodel a TIME DEMAND
# TYPE is running-time-per-demand-level, unrelated to flexible/on-demand
# operation) — so a claim of this shape must be grounded in a chunk that
# actually *defines* the element, not merely one that contains it in an
# example.
_ELEMENT_PURPOSE_CLAIM_PATTERN = re.compile(
    r"\b(is used to|is how|is the way to|is used for|specifies? that|shows? that|indicates? (?:that|whether)|"
    r"tells? you|defines? whether|to mark|to indicate|to show|to specify|to represent|"
    r"used to (?:mark|indicate|show|flag|specify|represent))\b",
    re.IGNORECASE,
)
# Words that are a purpose claim only as a verb: "`X` marks the service as ...", not "the means of calling a
# lift" or "`BoardingUse` and `AlightingUse` flags." (both rejected 2026-11-09, emptying the lift answer).
# A verb here is not after an article or possessive and is followed by a word, not by punctuation.
_AMBIGUOUS_PURPOSE_VERB_PATTERN = re.compile(
    r"(?<![A-Za-z])(?<!\bthe )(?<!\ba )(?<!\ban )(?<!\bits )(?<!\btheir )(?<!\bthese )(?<!\bthose )"
    r"(indicates?|marks?|means?|represents?|denotes?|signifies?|flags?)(?=\s+[A-Za-z`<])",
    re.IGNORECASE,
)


def _has_purpose_claim(sentence: str) -> bool:
    return bool(_ELEMENT_PURPOSE_CLAIM_PATTERN.search(sentence) or _AMBIGUOUS_PURPOSE_VERB_PATTERN.search(sentence))

# Chunk doc types that can plausibly carry a definition/explanation of an
# element's purpose. "example" chunks are raw XML/JSON instances — the
# presence of an element there proves it exists, not what it means.
_DEFINITIONAL_DOC_TYPES = {"schema", "frame", "object", "ontology-definition", "ontology-relation", "guide"}


def _element_has_definition_in_evidence(element_name: str, chunks: list[dict]) -> bool:
    """True if some chunk in the full prompt evidence defines this element.

    Checked against the whole evidence set, not just the sentence's own
    citations: the model may cite the example it quotes XML from ([E3]) in
    the same sentence that explains the element's purpose, while the actual
    definition sits in a different, uncited evidence block ([E1]). As long
    as that definition is somewhere in the prompt, the claim is grounded —
    citing the wrong block for one clause is a citation-precision issue
    (see _validate_citation_grounding), not evidence of an invented meaning.
    """
    for chunk in chunks:
        doc_type = str(chunk.get("docType", "") or "").lower()
        if doc_type not in _DEFINITIONAL_DOC_TYPES:
            continue
        chunk_text = str(chunk.get("text", ""))
        if element_name.lower() in chunk_text.lower():
            return True
    return False


def _validate_no_unsupported_element_purpose_claims(answer: str, chunks: list[dict]) -> None:
    """
    Reject sentences that explain what an XML element "means" or "is used for"
    when no block in the evidence defines it — only shows it used in an example.

    An element's name is not its definition — the model must not infer intent
    (e.g. "on-demand operation") from a plausible-sounding name when nothing in
    the evidence actually defines that element's semantics. A claim is accepted
    as long as a definitional chunk for the element exists anywhere in the
    prompt evidence, even if the sentence's own citation points at an example
    instead — see _element_has_definition_in_evidence.

    Fenced code blocks (quoted XML/JSON snippets) are stripped before sentence
    splitting: a verbatim snippet can contain many element tags with no sentence
    punctuation between them, and without stripping, those tags bleed into
    whatever prose sentence precedes or follows the fence and get judged as if
    the model had made a purpose claim about each of them.
    """
    prose_only = FENCED_CODE_BLOCK_PATTERN.sub(" ", answer)
    sentences = re.split(r"(?<=[.!?])\s+", prose_only.replace("\n", " "))

    for sentence in sentences:
        if not _has_purpose_claim(sentence):
            continue

        element_names = _XML_ELEMENT_MENTION_PATTERN.findall(sentence)
        if not element_names:
            continue

        found_citations = CITATION_PATTERN.findall(sentence)
        if not found_citations:
            continue  # Uncited purpose claims are caught by other validators.

        ungrounded = [
            name for name in element_names if not _element_has_definition_in_evidence(name, chunks)
        ]

        if ungrounded:
            raise LLMGenerationError(
                f"Sentence attributes a purpose/meaning to element(s) {ungrounded} "
                f"but no evidence block defines them (only non-definitional evidence, "
                f"e.g. an example file, is available): "
                f"'{sentence[:150].strip()}'. "
                "An element's name is not its definition — do not infer what an element "
                "means or is used for unless some evidence block actually defines it."
            )


_RAW_FILENAME_PATTERN = re.compile(
    r"\b[A-Za-z0-9_][A-Za-z0-9_.\-]*\.(?:xml|xsd|yaml|yml|json|ttl|csv|rdf|owl)\b"
)

# Matches file paths with directory separators (e.g., "folder/file.xml" or "path/to/file.xsd")
_FILE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z0-9_\-./]*[/\\][A-Za-z0-9_.\-/\\]*\.(?:xml|xsd|yaml|yml|json|ttl|csv|rdf|owl)\b"
)

# Detect a trailing JSON object that some LLMs append after the prose answer,
# e.g.  `{"answer": "...", "citations_used": ["E3"]}` or `{"citations": [...]}`.
_JSON_SUFFIX_PATTERN = re.compile(
    r"\s*\{[^{}]*\"(?:answer|citations|citations_used|sources|source_ids)[^{}]*\}\s*$",
    re.DOTALL,
)


def _strip_json_suffix(answer: str) -> str:
    """
    Remove a trailing JSON metadata object that some LLMs append to their prose.

    Several LLMs, when uncertain about output format, append a JSON summary
    like ``{"answer": "...", "citations_used": ["E3"]}`` after the prose text.
    This corrupts markdown rendering and duplicates content in the UI.
    """
    return _JSON_SUFFIX_PATTERN.sub("", answer).rstrip()


# A complete, correctly escaped "answer" string followed by another key or the end of
# the object. An unescaped quote inside the answer ends the string early, and then the
# lookahead fails, so a broken answer is never returned cut short.
_LENIENT_ANSWER_FIELD_PATTERN = re.compile(r'"answer"\s*:\s*("(?:[^"\\]|\\.)*")(?=\s*(?:,\s*"[^"]*"\s*:|\}))', re.DOTALL)


_EVIDENCE_FLAG_PATTERN = re.compile(r'"evidence_answers_question"\s*:\s*(true|false)')


def _evidence_answers_question(text: str) -> bool | None:
    """The model's own verdict on whether the evidence answers the question, from its JSON response.

    False marks a non-answer ("the evidence does not contain ..."), whatever language it is written in;
    retrieval scores cannot tell, since the blocks were the best matches found. None when the response
    carries no verdict (plain text, an older prompt): callers then leave confidence as it is.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = _EVIDENCE_FLAG_PATTERN.search(text)
        return None if match is None else match.group(1) == "true"
    if isinstance(parsed, dict) and isinstance(parsed.get("evidence_answers_question"), bool):
        return parsed["evidence_answers_question"]
    return None


def _unwrap_json_answer(text: str) -> str:
    """
    Extract the prose answer from a JSON-mode LLM response.

    JSON mode makes the model emit ``{"answer": "...", "citations_used": [...]}``;
    this returns the "answer" field, unwrapping a double-encoded answer field and
    falling back to other common field names. Non-JSON input is returned as-is.
    Text that starts like a JSON object but does not parse is never returned: its
    answer field is recovered when it is intact, otherwise LLMGenerationError is
    raised so the caller retries or falls back instead of showing JSON fragments.
    """
    try:
        response_json = json.loads(text)
    except json.JSONDecodeError:
        if not text.lstrip().startswith("{"):
            logger.debug("[UNWRAP] Not JSON, treating as plain text")
            return text
        match = _LENIENT_ANSWER_FIELD_PATTERN.search(text)
        if match:
            try:
                answer = json.loads(match.group(1))
            except json.JSONDecodeError:
                answer = None
            if isinstance(answer, str) and answer.strip():
                logger.warning("[UNWRAP] Malformed JSON response; recovered its answer field")
                return answer
        raise LLMGenerationError("LLM response looks like JSON but cannot be parsed; its answer cannot be recovered.")
    if not isinstance(response_json, dict):
        return text

    answer = response_json.get("answer")
    if isinstance(answer, str):
        # Handle double-wrapped JSON: the answer field itself may be a JSON string.
        if answer.strip().startswith("{"):
            try:
                inner_json = json.loads(answer)
            except json.JSONDecodeError:
                return answer
            if isinstance(inner_json, dict) and isinstance(inner_json.get("answer"), str):
                logger.info(f"[UNWRAP] Double-wrapped answer extracted: {len(inner_json['answer'])} chars")
                return inner_json["answer"]
        return answer

    logger.warning(f"[UNWRAP] No 'answer' key, falling back. Keys: {list(response_json.keys())}")
    for key in ("text", "content", "response", "message"):
        if isinstance(response_json.get(key), str):
            logger.info(f"[UNWRAP] Using '{key}' field instead")
            return response_json[key]
    # Any other key (a model once emitted {": ": "<answer>"}): the prose is the
    # longest string value. Never return str(dict) -- the UI shows it verbatim.
    string_values = [value for value in response_json.values() if isinstance(value, str) and value.strip()]
    if string_values:
        return max(string_values, key=len)
    raise LLMGenerationError("LLM JSON response contains no answer text.")


def _strip_raw_filenames(answer: str, chunks: list[dict] | None = None) -> str:
    """
    Remove hallucinated file names from answer text, preserving evidence file names.

    File names whose basename appears in a chunk's sourcePath are legitimate and
    are kept in the answer.  Only file names NOT present in any evidence source
    path are removed — these are hallucinated-but-plausible inventions.

    Fenced code blocks are preserved entirely.
    """
    # Build allowlist of basenames from evidence source paths.
    allowed_basenames: set[str] = set()
    for chunk in (chunks or []):
        path = str(chunk.get("sourcePath", "") or chunk.get("source_path", ""))
        if path:
            allowed_basenames.add(path.rsplit("/", 1)[-1].lower())

    # Preserve code blocks during processing.
    # findall returns tuples when pattern has groups; use finditer for full match text.
    code_block_texts: list[str] = [m.group(0) for m in FENCED_CODE_BLOCK_PATTERN.finditer(answer)]
    temp_answer = FENCED_CODE_BLOCK_PATTERN.sub("__CODE_BLOCK__", answer)

    # Remove file paths (with directories) that are not in the allowlist.
    def _replace_if_not_allowed(m: re.Match) -> str:
        name = m.group(0).rsplit("/", 1)[-1].lower()
        return "" if name not in allowed_basenames else m.group(0)

    temp_answer = _FILE_PATH_PATTERN.sub(_replace_if_not_allowed, temp_answer)
    temp_answer = _RAW_FILENAME_PATTERN.sub(_replace_if_not_allowed, temp_answer)

    # Clean up excessive whitespace from removed names, preserving newlines
    # so markdown line structure (lists, paragraphs, headings) survives.
    temp_answer = re.sub(r"(?<=\S)[ \t]{2,}", " ", temp_answer)
    temp_answer = re.sub(r" +\n", "\n", temp_answer)
    temp_answer = re.sub(r"\n{3,}", "\n\n", temp_answer).strip()

    # Restore code blocks.
    for code_block in code_block_texts:
        temp_answer = temp_answer.replace("__CODE_BLOCK__", code_block, 1)

    return temp_answer


# Only [E#] markers are citations. The prompt also lists other candidates as [C#], and
# a model sometimes cites those; they have no citation entry and would show as text.
_NON_EVIDENCE_MARKER_PATTERN = re.compile(r"[ \t]*\[(?!E\d+\])[A-Z]\d+\]")
# Removing a file name the evidence does not contain can leave its backticks behind.
# A pair counts as empty only when it stands alone: ``code`` with double backticks keeps
# its delimiters.
_EMPTY_INLINE_CODE_PATTERN = re.compile(r"(?<![^\s(])`[ \t]*`(?![^\s.,;:)\]])")
_INTRODUCER_COMMA_PATTERN = re.compile(r"\b(such as|e\.g\.|including),", re.IGNORECASE)
# The same citation twice in a row ("[E1] [E1]", "[E2][E2]") says nothing more than once.
_REPEATED_CITATION_PATTERN = re.compile(r"\[E(\d+)\](?:[ \t]*\[E\1\])+")


OMISSION_MARKER = "<!-- … -->"
_XML_TAG = re.compile(r"<!--.*?-->|<\?.*?\?>|<(/?)([A-Za-z_][\w:.-]*)(?:\s[^<>]*?)?(/?)>", re.S)
_XML_FENCE = re.compile(r"```(?:xml)?[ \t]*\n(.*?)\n?```", re.S | re.I)


def complete_xml_elements(xml: str) -> str:
    """An XML excerpt made of whole elements: "" when it holds no element.

    A quoted snippet cut by a line limit starts inside an element ("</SeatEquipment>" first) or ends inside
    one (<Quay> opened, never closed). What comes before a closing tag whose element opened before the
    excerpt is dropped; elements still open at the end (or at a mismatched closing tag) are closed after a
    "<!-- … -->" line, so the verbatim content stays and the shortening is visible. Tags are matched by
    name with a stack: namespace prefixes and entities need no parsing.
    """
    stack: list[tuple[str, str]] = []  # (name, indentation of its opening line)
    start, end = 0, len(xml)
    for match in _XML_TAG.finditer(xml):
        closing, name, self_closing = match.group(1), match.group(2), match.group(3)
        if name is None or self_closing:
            continue
        if not closing:
            line_start = xml.rfind("\n", 0, match.start()) + 1
            stack.append((name, xml[line_start : match.start()] if not xml[line_start : match.start()].strip() else ""))
            continue
        if stack and stack[-1][0] == name:
            stack.pop()
        elif not stack:
            start = match.end()  # closes an element opened before the excerpt
        else:
            end = match.start()  # mismatched: stop here and close what is open
            break
    body = xml[start:end].strip("\n")
    if not re.search(r"<[A-Za-z_]", body):
        return ""
    if stack:
        indent = stack[-1][1] + "  "
        closers = "\n".join(f"{ind}</{name}>" for name, ind in reversed(stack))
        body = f"{body.rstrip()}\n{indent}{OMISSION_MARKER}\n{closers}"
    return body


def _complete_xml_snippets(answer: str) -> str:
    """Every ```xml block of an answer cut to whole elements; a block with none is removed."""

    def repair(match: re.Match) -> str:
        body = match.group(1)
        if "<" not in body:
            return match.group(0)
        whole = complete_xml_elements(body)
        return f"```xml\n{whole}\n```" if whole.strip() else ""

    return re.sub(r"\n{3,}", "\n\n", _XML_FENCE.sub(repair, answer)).strip()


def _strip_non_evidence_markup(answer: str) -> str:
    """Remove bracketed markers that are not evidence citations, repeated citations, and
    inline code spans left empty, outside code blocks, then tidy the punctuation they leave behind."""
    code_block_texts = [m.group(0) for m in FENCED_CODE_BLOCK_PATTERN.finditer(answer)]
    text = FENCED_CODE_BLOCK_PATTERN.sub("__CODE_BLOCK__", answer)
    text = _NON_EVIDENCE_MARKER_PATTERN.sub("", text)
    text = _REPEATED_CITATION_PATTERN.sub(r"[E\1]", text)
    text = _EMPTY_INLINE_CODE_PATTERN.sub("", text)
    text = re.sub(r"[ \t]+([,.;:)])", r"\1", text)
    text = re.sub(r"\([ \t]*,[ \t]*", "(", text)
    text = re.sub(r",[ \t]*(?=,)", "", text)
    text = re.sub(r"\([ \t]*\)", "", text)
    text = _INTRODUCER_COMMA_PATTERN.sub(r"\1", text)
    text = re.sub(r"(?<=\S)[ \t]{2,}", " ", text)
    for code_block in code_block_texts:
        text = text.replace("__CODE_BLOCK__", code_block, 1)
    return text


def _strip_stray_list_markers(answer: str) -> str:
    """
    Remove stray numeric list markers (e.g., "1\n") that appear before code blocks.

    Some LLMs generate markdown like "text:\n\n1\n```xml" instead of properly
    formatted lists. This strips the orphaned list number to prevent "1" from
    appearing on its own line in the rendered output.
    """
    # Remove numeric list markers (1, 2, etc.) that appear on their own line
    # immediately before a code fence (allowing optional whitespace).
    return re.sub(r"^\d+\n(?=```)", "", answer, flags=re.MULTILINE)


def _validate_no_raw_filenames(answer: str, chunks: list[dict] | None = None) -> None:
    """
    Reject answers that contain raw file names not present in the evidence.

    File names whose basename appears in a chunk's sourcePath are legitimate —
    they were retrieved from approved sources.  File names that are NOT in any
    evidence source path are hallucination-prone inventions and are rejected.

    Fenced code blocks are excluded — verbatim XML/JSON quoted from evidence
    may legitimately contain file names inside attributes or comments.
    """
    # Build allowlist of basenames from evidence source paths.
    allowed_basenames: set[str] = set()
    for chunk in (chunks or []):
        path = str(chunk.get("sourcePath", "") or chunk.get("source_path", ""))
        if path:
            allowed_basenames.add(path.rsplit("/", 1)[-1].lower())

    clean = FENCED_CODE_BLOCK_PATTERN.sub("", answer)
    matches = _RAW_FILENAME_PATTERN.findall(clean)
    hallucinated = [m for m in matches if m.lower() not in allowed_basenames]
    if hallucinated:
        raise LLMGenerationError(
            f"Answer contains file name(s) {hallucinated[:4]} not found in any "
            "evidence block — only file names from the provided evidence may be "
            "used; do not invent file names."
        )


def _is_pure_boilerplate(answer: str) -> bool:
    """Check if answer is the EXACT generic boilerplate we keep seeing.

    Only detects the specific boilerplate pattern, not just any answer containing
    words like "follow" or "specification" (which would create false positives).
    """
    # Remove citations to check the raw text
    clean = CITATION_PATTERN.sub("", answer).strip()
    clean_lower = clean.lower()

    # Only detect the EXACT boilerplate pattern we've seen repeatedly.
    # This is the deterministic fallback answer from grounded_generator.py
    exact_boilerplate_start = "based on retrieved approved-source evidence"

    # Check if it starts with the telltale boilerplate beginning
    if not clean_lower.startswith(exact_boilerplate_start):
        return False

    # Also check for the specific keywords that only appear in boilerplate
    must_have_keywords = [
        "follow the",  # "follow the specification" or "follow the relevant"
        "validate implementation",  # specific to boilerplate
        "published examples or test cases",  # specific phrase
    ]

    # All three keywords must be present for it to be the boilerplate
    has_all = all(keyword in clean_lower for keyword in must_have_keywords)
    return has_all


def _normalized_language(name: str | None) -> str:
    name = (name or "").strip().lower()
    return "english" if name == "en" else name


def _validate_answer_language(answer: str, question: str, target_language: str | None = None) -> None:
    """Reject an answer written in a different language than the question's (target_language).

    Both directions count: an English answer to a German question, and a German or Dutch answer to an
    English question (Claude Haiku 5.5 wrote 7 of 147 English benchmark answers in the language of the
    evidence, 2026-11-04). Nothing is checked when the question's language is unknown or the answer's
    language cannot be detected with confidence; the detector's own failures are logged, never raised.
    """
    target = _normalized_language(target_language)
    if not target:
        return
    try:
        from helpdesk.services.question_preprocessor import detect_question_language

        answer_language = _normalized_language(detect_question_language(answer))
    except Exception:
        logger.warning("Answer language detection failed", exc_info=True)
        return
    if answer_language and answer_language != target:
        raise LLMGenerationError(
            f"Answer language is {answer_language.title()}, but the question is in {target.title()}. "
            f"Write the whole answer in {target.title()}."
        )


def _validate_answer_has_specificity(answer: str) -> None:
    """
    Reject boilerplate/generic answers that contain only ubiquitous terms.

    Answers like "follow the specification and validate with examples" have no
    specific content and are hallucinated filler. This check ensures answers
    contain at least one specific technical term (file name, concept ID, or
    PascalCase element name) beyond generic language.
    """
    # First check: is this pure boilerplate?
    if _is_pure_boilerplate(answer):
        raise LLMGenerationError(
            f"Answer is pure boilerplate generic advice. Must include specific technical "
            f"content from evidence (XML elements, attributes, code snippets, etc.)"
        )

    # Check if answer contains any strong or weak terms
    strong_terms, weak_terms = _classify_terms(answer)

    if not strong_terms and not weak_terms:
        # Answer has NO specific technical terms - pure boilerplate
        # Check answer length; very short answers may be legitimately generic
        answer_clean = CITATION_PATTERN.sub("", answer).strip()
        if len(answer_clean) > 50:  # Only reject if it's substantial text
            raise LLMGenerationError(
                f"Answer contains only generic language with no specific technical content. "
                f"Answers must reference specific concepts, examples, or identifiers from evidence, "
                f"not generic advice. Answer: '{answer_clean[:100]}'"
            )


_KNOWN_STANDARD_REFS = {
    "SCWW", "LUAS", "NeTEx", "IFOPT", "SIRI", "GTFS", "TPEG",
    "Transmodel", "PRTC", "OGC"
}

_UNCITED_STANDARD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _KNOWN_STANDARD_REFS) + r"(?:[-_][\w\d]+)?)\b",
    re.IGNORECASE
)


def _validate_no_uncited_standards(answer: str, chunks: list[dict], all_candidates: list[dict] | None = None) -> None:
    """
    Reject answers that mention known standards (SCWW, LUAS, etc.) without [E#] citations.

    Only flags genuine standard names, not generic format descriptors. Allows mentions
    if the standard appears in the evidence blocks (even without citation), since the
    evidence provides grounding for that standard's existence.
    """
    # Build set of standards that are actually in the evidence or candidates
    available_standards = set()
    for chunk in chunks:
        text = str(chunk.get("text", "")).upper()
        for std in _KNOWN_STANDARD_REFS:
            if std.upper() in text:  # Case-insensitive comparison
                available_standards.add(std.upper())
    if all_candidates:
        for candidate in all_candidates:
            text = str(candidate.get("label", "")) + " " + str(candidate.get("sourcePath", ""))
            text = text.upper()
            for std in _KNOWN_STANDARD_REFS:
                if std.upper() in text:  # Case-insensitive comparison
                    available_standards.add(std.upper())

    # Find standards that are mentioned without citations
    # Check each standard mention to see if it's followed/preceded by a citation
    for match in _UNCITED_STANDARD_PATTERN.finditer(answer):
        std = match.group(1)
        std_start = match.start()
        std_end = match.end()

        # Look for citations near this standard mention (within 30 chars before/after)
        context_start = max(0, std_start - 30)
        context_end = min(len(answer), std_end + 30)
        context = answer[context_start:context_end]

        # Check if there's a citation in the context
        has_nearby_citation = bool(CITATION_PATTERN.search(context))

        # Only reject if: standard is mentioned without nearby citation AND standard not in evidence
        if not has_nearby_citation and std.upper() not in available_standards:
            raise LLMGenerationError(
                f"Answer mentions '{std}' without citation and it's not in provided evidence. "
                f"Either cite the source with [E#] or don't mention the standard."
            )


def _build_ssl_context() -> ssl.SSLContext:
    """Build SSL context for LLM provider calls, supporting custom CA bundles."""

    if not settings.LLM_VERIFY_SSL:
        return ssl._create_unverified_context()

    context = ssl.create_default_context()
    if settings.LLM_CA_BUNDLE:
        context.load_verify_locations(cafile=settings.LLM_CA_BUNDLE)
    return context


_FOCUS_TERM = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+\b")


def _question_focus_terms(question: str) -> list[str]:
    """CamelCase element names typed in the question (TemplateServiceJourney)."""
    return list(dict.fromkeys(_FOCUS_TERM.findall(question or "")))


TRIM_ALLOWANCE = 1.25
# Where a block was cut for the prompt. The model read the old "[truncated for latency]" and told users
# "the list is truncated"; CUT_RULE tells it the cut is a display limit, never to be mentioned.
CUT_MARKER = "[…]"
CUT_RULE = (
    f"A block may start or end with {CUT_MARKER}: it was shortened for this prompt only. Never mention that a "
    "block is cut, shortened or truncated, and do not conclude from it that the standard lacks something; "
    "answer from what the blocks show."
)


def _trim_chunk_text(text: str, max_chars: int, focus_terms: list[str] | tuple[str, ...] = ()) -> str:
    """Cut a chunk to max_chars, keeping an asked-for XML element inside the cut.

    Cutting from the start drops the element whenever it sits past the limit
    (an example chunk often opens with frames and references), and the model
    then says the evidence has no snippet. When the text contains <Term for a
    term from the question that the head cut would miss, cut a window that
    starts a little before it instead.
    """
    if max_chars <= 0:
        return text
    # A block only a little over the limit is kept whole: cutting the last few lines saves almost no
    # latency and drops the end of a list ("What is SIRI used for?", 2026-11-08: a 1,445-character
    # chunk cut at 1,200 lost SIRI-FM and SIRI-SX, and the answer said "the list is truncated").
    if len(text) <= max_chars * TRIM_ALLOWANCE:
        return text
    for term in focus_terms:
        match = re.search(rf"<{re.escape(term)}[\s>/]", text)
        if match and match.start() + 300 > max_chars:
            start = text.rfind("\n", 0, max(0, match.start() - max_chars // 5)) + 1
            excerpt = text[start : start + max_chars].rstrip()
            return f"{CUT_MARKER}\n{excerpt}\n{CUT_MARKER}"
    return f"{text[:max_chars].rstrip()}\n{CUT_MARKER}"


LANGUAGE_CLASSIFIER_TIMEOUT_SECONDS = 10


def _classify_question_language_with_llm(question: str) -> str | None:
    """Ask the LLM which language a question is written in; return a language name or None.

    For questions the word-based detector cannot judge: once schema identifiers are removed,
    "Wie verwendet SIRI NeTEx?" keeps only two words. The generic "respond in the question's
    language" instruction then gets an English answer, so the answer prompt needs the language
    named. Any failure or an unknown name returns None, which keeps that generic instruction.
    """
    base_url = (settings.LLM_API_BASE_URL or "").strip()
    if not base_url:
        return None
    messages = [
        {
            "role": "system",
            "content": (
                "Identify the natural language the user's question is written in. Ignore technical terms, "
                "acronyms and schema names such as SIRI, NeTEx or StopPlace. Closely related languages are easy "
                "to confuse (Slovenian, Croatian, Serbian and Bosnian; Czech and Slovak; Danish, Norwegian and "
                "Swedish; Spanish, Portuguese, Catalan and Italian): decide by the words, particles and spellings "
                "that belong to only one of them, not by the language family. Reply with JSON only, no other text: "
                '{"evidence": "<the words that decide, at most 10 words>", "language": "<English name of the language>"}.'
            ),
        },
        {"role": "user", "content": question},
    ]
    try:
        response = _request_chat_completion(
            api_base_url=base_url,
            api_key=(settings.LLM_API_KEY or "").strip(),
            model=settings.LANGUAGE_CLASSIFIER_MODEL,
            timeout_seconds=min(settings.LLM_TIMEOUT_SECONDS, LANGUAGE_CLASSIFIER_TIMEOUT_SECONDS),
            temperature=0.0,
            max_tokens=answer_max_tokens(60),
            messages=messages,
        )
        content = response["choices"][0]["message"]["content"]
        # The first JSON object: the model sometimes adds a second thought after it.
        name = str(json.loads(re.search(r"\{[^{}]*\}", content).group(0)).get("language", "")).strip().title()
    except Exception:
        logger.warning("LLM language classification failed for %r", question, exc_info=True)
        return None
    return name if name in LANGDETECT_LANGUAGE_NAMES.values() else None


# langdetect is confidently wrong on short questions in languages that share word forms: "Ali SIRI definira
# dela na cesti?" (Slovenian) -> Italian at 0.99999 (prod 2026-11-05, answered in Italian). Below this many
# words a non-English detection is confirmed by the LLM classifier; English needs no confirmation (its
# misreadings are caught by the function-word check), and longer questions are left to langdetect.
MIN_TRUSTED_DETECTION_WORDS = 8


# Questions the search translation found to be English already (see english_search_query), most recent last.
# langdetect read "Create a NeTEx XML example for a fare product for adult for 5 EUR." as Romanian at 0.99999,
# with 10 words and no English function word, and the answer came in Romanian (prod 2026-11-09).
_CONFIRMED_ENGLISH: "OrderedDict[str, None]" = OrderedDict()
_CONFIRMED_ENGLISH_SIZE = 512


def _language_key(question: str) -> str:
    return " ".join(question.split()).lower()


def question_language(question: str) -> str | None:
    """The question's language: the word-based detector, confirmed or replaced by the LLM where it is unreliable,
    and English when the search translation found the question English already."""
    if _language_key(question) in _CONFIRMED_ENGLISH:
        return LANGDETECT_LANGUAGE_NAMES["en"]
    detected = detect_question_language(question)
    if detected is None:
        return _classify_question_language_with_llm(question)
    if detected != LANGDETECT_LANGUAGE_NAMES["en"] and natural_word_count(question) < MIN_TRUSTED_DETECTION_WORDS:
        return _classify_question_language_with_llm(question) or detected
    return detected


SEARCH_TRANSLATION_TIMEOUT_SECONDS = 10


def english_search_query(question: str) -> str | None:
    """An English rendering of a non-English question, to search with next to the question itself.

    The sources are English. The multilingual embedding model places a Slovenian or German question near
    the right topic, but less sharply than the English wording, and the keyword half of the search only
    matches English words. None for English questions, when the language is unknown, when translation is
    off (SEARCH_TRANSLATION_ENABLED) or no LLM is configured, and on any failure: the search then runs
    with the question alone.
    """
    if not getattr(settings, "SEARCH_TRANSLATION_ENABLED", True) or not getattr(settings, "LLM_ENABLED", False):
        return None
    base_url = (settings.LLM_API_BASE_URL or "").strip()
    language = question_language(question)
    if not base_url or not language or language == "English":
        return None
    messages = [
        {
            "role": "system",
            "content": (
                "Translate the user's question into English for a search. Keep standard and schema names "
                "(NeTEx, SIRI, OpRa, Transmodel, StopPlace, MMTIS ...) unchanged. Any other abbreviation is "
                "translated like a word: write the English abbreviation of the term it stands for, as in "
                "PAN, PAP or NZP -> NAP (national access point) and STI or ITS -> ITS (intelligent transport "
                "systems). Also name the language the question is written in, ignoring those names. "
                'Reply with JSON only: {"language": "<English name of the question\'s language>", "text": "<English question>"}.'
            ),
        },
        {"role": "user", "content": question},
    ]
    try:
        response = _request_chat_completion(
            api_base_url=base_url,
            api_key=(settings.LLM_API_KEY or "").strip(),
            model=settings.LLM_MODEL,
            timeout_seconds=min(settings.LLM_TIMEOUT_SECONDS, SEARCH_TRANSLATION_TIMEOUT_SECONDS),
            temperature=0.0,
            max_tokens=answer_max_tokens(200),
            messages=messages,
        )
        content = response["choices"][0]["message"]["content"]
        source_language = ""
        try:
            payload = json.loads(content)
            source_language = str(payload.get("language") or "").strip().title()
            # The model sometimes names the key differently; take the first text it returns.
            text = payload.get("text") or next(
                (v for k, v in payload.items() if k != "language" and isinstance(v, str) and v.strip()), ""
            )
        except (ValueError, AttributeError):
            text = content
        text = str(text).strip()
    except Exception:
        logger.warning("English search query failed for %r", question, exc_info=True)
        return None
    if source_language == LANGDETECT_LANGUAGE_NAMES["en"]:
        # The word detector misread an English question: answer, check and search it as English.
        logger.info("Question detected as %s is English according to the translator: %r", language, question)
        _CONFIRMED_ENGLISH[_language_key(question)] = None
        _CONFIRMED_ENGLISH.move_to_end(_language_key(question))
        while len(_CONFIRMED_ENGLISH) > _CONFIRMED_ENGLISH_SIZE:
            _CONFIRMED_ENGLISH.popitem(last=False)
        return None
    return text if text and text.lower() != question.strip().lower() else None


LEGISLATION_RULE = (
    "Some evidence blocks are EU legislation; their first line names the act. For those blocks rule 9 does not "
    "apply. Instead, name the act and the article or annex point (e.g. 'Article 4(1)(b) of Delegated Regulation "
    "(EU) 2017/1926') and quote the relevant wording verbatim. Do not add obligations, dates or interpretations "
    "that the quoted text does not state. When a provision lists alternatives ('one of the following', 'or any "
    "format proven compatible'), say that it is one of the options and name the others; do not call a single "
    "option mandatory, and do not open the answer with a plain yes or no: open with what the provision requires. "
    "When an evidence block is a consolidated text and another is the act that amended it, "
    "quote the consolidated text."
)


NAPCORE_RULE = (
    "Some evidence blocks are NAPCORE documents (napcore.eu pages, NAPCORE deliverables and reports); their "
    "first line names the document. For those blocks rule 9 does not apply. Instead, name the document and quote "
    "or closely restate its wording. Do not add facts, figures, dates or recommendations that the block does not "
    "state, and do not present NAPCORE's guidance or positions as legal obligations."
)


# How the answer is put together, for every question type (prod question 653, 2026-11-07: the answer
# opened with what the evidence lacks, defined the context word "vehicle", and went block by block).
# The type rules above say what to start with; this says how the rest reads.
COMPOSITION_RULE = (
    "ANSWER COMPOSITION:\n"
    "- Start with one or two sentences that answer the question directly. If the evidence answers only part of "
    "it, start with that part; say what is missing only at the end, in one sentence.\n"
    "- When the evidence answers the question, end with the answer: add no sentence about what the evidence "
    "does not describe, and do not mention evidence blocks that are unrelated to the question.\n"
    "- The question's subject is what it asks about; the rest is context. In 'How are delays reported at a "
    "stop?' the subject is delays and 'stop' is context. Do not define, quote or describe a context concept.\n"
    "- Organise the answer by topic, not by evidence block: put together what several blocks say about the same "
    "thing. When the answer covers two or more topics, start each with a short bold lead-in.\n"
    "- Say what an element is for in plain words, then name it in backticks, e.g. 'the method used to allocate "
    "the seat (`SeatAllocationMethod`)'. The plain words must not say more than the evidence.\n"
    "- Leave out evidence that does not help answer the question, even if it is in the blocks.\n"
)


# When the answer comes with a fragment generated for the question and validated against the NeTEx XSD
# (services/netex_example_generator.py), the fragment and its schema notes are shown first and are the
# answer; the text adds only what the evidence says about the fragment's elements, and may be empty.
# (Prod req-mw7j8wr6-t4l19q, 2026-11-08: the text said "I cannot provide one" above a valid example.)
def generated_example_rule(elements: list[str], fragment: str = "", also_asks: str = "", origin: str = "generated") -> str:
    """The text's brief next to an example shown first: it sees the fragment, answers any other part of the
    question first (also_asks: "How do you describe a stop place in NeTEx?" next to "show me an example"),
    then adds how the standard's own examples fill the same elements."""
    shown = f"\n```xml\n{fragment.strip()}\n```\n" if fragment.strip() else " "
    where = {
        "standard": "taken from one of the standard's own example files",
        # Generation failed; the standard's object of the asked kind is shown instead (plan P5, 2026-11-10).
        "standard-without-values": (
            "taken from one of the standard's own example files because no example with the question's values "
            "validated against the schema; it does NOT contain the question's values. Say in one sentence, from the "
            "evidence, which element would hold each of the question's values, and do not claim the example holds them"
        ),
    }.get(origin, "generated for the question and validated against the NeTEx schema")
    first = (
        f"The question also asks: \u201c{also_asks.strip()}\u201d. Start by answering that, in two or three "
        "sentences from the evidence (definition blocks may be quoted); then "
        if also_asks.strip()
        else "Do not define these elements, and do not say what the evidence lacks. "
    )
    return (
        f"EXAMPLE ALREADY SHOWN: above your text the user sees this NeTEx fragment, {where}:{shown}"
        f"It uses these elements: {', '.join(elements)}. Above it the user is told "
        + ("that the example does not hold the question's values" if origin == "standard-without-values" else "which element holds each value or count of the question")
        + ", and below it each element's definition from the schema. Do not repeat "
        f"or describe the fragment. {first}"
        "write what the evidence adds about the elements that hold the question's values, as the standard's own "
        "examples use them: where they sit, which elements usually come with them, allowed values and types. "
        "Prefer evidence blocks that use those elements; leave out blocks that do not. At most four sentences "
        "for this part, each cited [E#], then at most one verbatim snippet in a ```xml block: one whole element "
        "from its opening to its closing tag, at most 12 lines, from one evidence block that uses the same "
        "elements. If the evidence adds nothing and there is no other part to answer, return exactly: "
        '{"answer": "", "citations_used": [], "evidence_answers_question": true}'
    )


EXISTENCE_RULE = (
    "WHETHER THE STANDARD HAS IT: the question asks whether the standard has or describes something. The first "
    "evidence blocks are the model's definition of that concept (with the standards that implement it, or the note "
    "that none does) and the schema elements named after it. Your first sentence answers Yes or No about the "
    "standard, not about the evidence: name the element or class that exists, or say that the standard has no "
    "element or class for it, and what it has instead (for example only a reference), citing [E#]. Then explain in "
    "at most three sentences. Do not describe example blocks that do not show the asked-for thing."
)


MODELLING_RULE = (
    "HOW THE STANDARD MODELS IT: the question asks how the standard defines or describes something. The first "
    "evidence blocks are the model's definitions of the concepts involved (with the standard's class that implements "
    "each) and the schema elements for them. Start by naming the classes or elements the standard uses for it and "
    "what each is, citing [E#]; then say how they relate and where they sit (frame, container, what refers to them) "
    "as far as the blocks say. Do not build the answer on example blocks about something else."
)


def schema_structure_rule(element: str) -> str:
    """When the schema's content model of the element is shown first (services/schema_structure.py)."""
    return (
        f"SCHEMA STRUCTURE ALREADY SHOWN: above your text the user sees what {element} contains according "
        "to the NeTEx schema: every child element, its own and the inherited ones, and its attributes, each "
        f"with its definition from the schema, and the definition of {element} itself. Do not define {element}, "
        "do not list, repeat or define those elements, and do not say what the evidence lacks. Write only what "
        f"the evidence adds about {element}: how the standard's own "
        "examples use it and which of its children they fill, constraints or usual values, and what refers to "
        "it. At most four sentences, each cited [E#], then at most one verbatim snippet (one whole element, at most 12 lines, in "
        "a ```xml block) from one evidence block. If the evidence adds nothing, return exactly: "
        '{"answer": "", "citations_used": [], "evidence_answers_question": true}'
    )


def _nothing_to_add(chunks: list[dict]) -> dict:
    """The text's result when the example and its schema notes already say what the evidence has."""
    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    return {
        "answer": "",
        "confidence": min(0.94, max(0.60, float(top_score))),
        "review_required": False,
        "answer_validated": True,
        "evidence_answers_question": True,
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
        "rejected_answer": None,
        "rejection_reason": None,
    }


def _build_messages(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    max_chunks: int = 6,
    max_chars_per_chunk: int = 1800,
    faq_hint: str | None = None,
    language: str | None = None,
    all_candidates: list[dict] | None = None,
    detected_language: str | None = None,
    example_elements: list[str] | None = None,
    structure_element: str | None = None,
    example_fragment: str = "",
    also_asks: str = "",
    example_origin: str = "generated",
    existence: bool | str = False,
) -> list[dict]:
    context_lines = []
    # With a generated example, trimming keeps its elements (those holding the question's values first) in view.
    focus_terms = list(dict.fromkeys(list(example_elements or []) + list(_question_focus_terms(question))))
    for index, chunk in enumerate(chunks[:max_chunks], start=1):
        # A legislation chunk is one article (or part of one), bounded when the act is indexed. Its
        # tail holds the last points of a list, so a cut dropped e.g. Art. 4(1)(c) and 4(2) of MMTIS
        # and the answer named fewer standards than the article does. NAPCORE chunks are bounded too.
        limit = 0 if _is_prose_chunk(chunk) else max_chars_per_chunk
        chunk_text = _trim_chunk_text(str(chunk.get("text", "")), max_chars=limit, focus_terms=focus_terms)
        context_lines.append(
            "\n".join(
                [
                    f"[E{index}] repository={chunk['repositoryUrl']}",
                    f"[E{index}] commit={chunk['commitSha']}",
                    f"[E{index}] source={chunk['sourcePath']}",
                    f"[E{index}] chunk={chunk['chunkId']}",
                    f"[E{index}] text={chunk_text}",
                ]
            )
        )

    context = "\n\n".join(context_lines)
    scope_text = ", ".join(scope) if scope else "all approved standards"

    # Build candidate reference index from all candidates (if provided)
    # This tells the LLM what sources are available in the database
    candidate_index = ""
    if all_candidates:
        candidate_lines = []
        for idx, candidate in enumerate(all_candidates[:20], start=1):  # Limit to top 20 for brevity
            source_path = candidate.get("sourcePath", "unknown")
            label = candidate.get("label", "")
            score = candidate.get("score", 0)
            label_display = f" - {label}" if label else ""
            candidate_lines.append(f"[C{idx}] {source_path}{label_display} (score: {score:.2f})")
        if candidate_lines:
            candidate_index = "AVAILABLE CANDIDATE REFERENCES (in database):\n" + "\n".join(candidate_lines) + "\n\n"

    # Detect the language from the question text itself rather than trusting the
    # client-supplied `language` (often just the browser/OS locale, unrelated to
    # what the user actually typed). With thinking mode disabled, the model has
    # no reasoning step of its own to fall back on for "detect the language"
    # instructions, so an explicit target language must be given here. Callers
    # that already detected the language pass it in to avoid a second detection.
    # When detection is inconclusive (e.g. a very short question), fall back to
    # the generic instruction below, not the browser locale: a French-locale
    # browser asking "Does SIRI-PT exist?" should not get a French answer.
    if detected_language is None:
        detected_language = detect_question_language(question)
    effective_language = detected_language

    _lang = (effective_language or "").strip().lower()
    if _lang in ("en", "english"):
        # Named, not "the question's language": with evidence in German or Dutch (OpRa), a model told
        # only to match the question drifted into the evidence's language.
        language_instruction = (
            " Respond in English, even when evidence blocks are in another language."
            " Keep technical terms, class names, XML tags, and identifiers as they appear in the evidence."
        )
    elif _lang:
        language_instruction = (
            f" Respond in {effective_language}. Keep technical terms, class names, XML tags, and identifiers in English."
        )
    else:
        language_instruction = (
            " Detect the language of the question and respond in that same language."
            " Keep technical terms, class names, XML tags, and identifiers in English."
        )
    composition = getattr(settings, "ANSWER_COMPOSITION_ENABLED", True)
    if composition:
        rule_6 = (
            "6. Do NOT infer beyond what is explicitly stated in the evidence; a restatement in plain words must "
            "not say more than the evidence does"
        )
        rule_9_names = (
            "   - The specific XML element and attribute names (e.g., <DepartureTime>, scheduleRelationship) that the "
            "evidence gives for the question's subject; do not list names that do not help answer the question"
        )
    else:
        rule_6 = "6. Do NOT paraphrase or infer beyond what is explicitly stated in the evidence"
        rule_9_names = (
            "   - Specific XML element names (e.g., <DepartureTime>, <Journey>, <Call>)\n"
            "   - Specific attribute names (e.g., scheduleRelationship, time)"
        )
    system_prompt = (
        "You are a standards helpdesk assistant. You have access to EXACTLY the evidence blocks listed below. "
        "You MUST output valid JSON only. Do not output any text outside the JSON structure.\n"
        f"\n🌍 LANGUAGE REQUIREMENT: {language_instruction}\n"
        "\nCRITICAL RULES:\n"
        "1. ONLY reference information that appears in the provided evidence blocks [E1] through [E#]\n"
        "2. EVERY factual claim MUST have a citation [E#] to the specific block containing that information\n"
        "3. Do NOT use any knowledge from your training data. Do NOT reference standards, examples, or concepts not in the provided blocks\n"
        "4. If you recognize a source from your training (e.g., known file or standard example) but it is not in [E#], do NOT mention it\n"
        "5. If you cannot answer from provided evidence, say so clearly — but write that sentence in the "
        "response language from the LANGUAGE REQUIREMENT above, not English (unless English is the response language)\n"
        f"{rule_6}\n"
        "7. Stay within requested standards scope\n"
        "8. NEVER write file names in answer text. Reference sources ONLY via [E#] citations.\n"        f"8a. {CUT_RULE}\n"
        "9. REQUIRED CONTENT — Your answer MUST include:\n"
        f"{rule_9_names}\n"
        "   - Citations [E#] pointing to the evidence block with that element\n"
        "   - If the evidence shows code examples, include the relevant snippet\n"
        "10. FORBIDDEN PATTERNS — NEVER generate:\n"
        "   - Generic advice like 'follow the specification'\n"
        "   - Phrases like 'validate implementation'\n"
        "   - 'Based on retrieved approved-source evidence, follow...'\n"
        "   - Vague recommendations without specific element names\n"
        "   - If you cannot find specific technical details in evidence, say so explicitly\n"
        "\n"
        "OUTPUT FORMAT (strict JSON):\n"
        '{"answer": "Your answer text here with [E1] [E2] citations inline.", "citations_used": ["E1", "E2"], '
        '"evidence_answers_question": true}'
        "\nSet evidence_answers_question to false only when the evidence blocks do not answer the question at all, "
        "so that your answer says it cannot answer it. Set it to true when they answer it fully or in part.\n"
        "\n\nMARKDOWN FORMATTING:\n"
        "- Use `backticks` for technical content: XML elements, attributes, filenames, class names, values.\n"
        "- Use triple backticks for code blocks: ```xml ... ```\n"
        "- Use **bold** for emphasis only, not for technical terms.\n"
        "- Standard markdown for lists, headers, and paragraphs.\n"
    )
    if example_elements or structure_element:
        pass  # the block's rule goes last in the user prompt, where the model follows it; no type rule here.
    elif _question_requests_verbatim_example(question):
        system_prompt = (
            f"{system_prompt} "
            "For questions asking for examples or code: First, directly answer 'yes' or 'no' about availability. Then list the examples found in evidence with citations [E#]. "
            "When showing XML/JSON/YAML, include one fenced code block (```xml) of 6-20 lines from a single evidence block, made of whole elements (each opening tag closed). "
            "Quote only verbatim excerpts from evidence blocks. Never synthesize or combine structures across sources. "
            "If asking for availability ('Is there any...?'), list all matching examples found in the evidence with their source paths and brief descriptions."
        )
    elif _question_asks_for_definition(question):
        system_prompt = (
            f"{system_prompt} "
            "For definition questions ('what is X?'): start with the definition of X, quoted from the definition "
            "evidence blocks and naming the standard each comes from. Then add at most a short paragraph on how X "
            "relates to other concepts (parent concept, what it contains or is part of) if the evidence says so. "
            "Use example (.xml) blocks only to illustrate in one sentence at most; do not walk through the details "
            "or mappings of an example file, and do not include code unless the question asks for it."
        )
    elif _question_about_xml_or_technical(question):
        system_prompt = (
            f"{system_prompt} "
            "For technical questions about XML, standards structures, or implementations: Include a relevant code example from the evidence if available. "
            "When showing XML/JSON structures, use one fenced code block (```xml) with 6-15 lines from the evidence, made of whole elements (each opening tag closed). "
            "Never synthesize or invent examples — only quote verbatim from the evidence blocks."
        )

    # Legislation is quoted by article, not described by XML elements (issue #91).
    if _has_legislation_evidence(chunks, max_chunks):
        system_prompt = f"{system_prompt} {LEGISLATION_RULE}"
    if _has_napcore_evidence(chunks, max_chunks):
        system_prompt = f"{system_prompt} {NAPCORE_RULE}"

    faq_section = ""
    if faq_hint:
        faq_section = (
            f"Editorial baseline (approved directional answer — enrich and ground it using the evidence blocks below, do not copy verbatim):\n{faq_hint}\n\n"
        )

    # Count evidence blocks to explicitly tell the LLM the valid citation range
    num_blocks = len(context_lines)
    citation_range_warning = (
        f"\n⚠️ CRITICAL CITATION RANGE: You have {num_blocks} evidence blocks: [E1] through [E{num_blocks}].\n"
        f"NEVER cite [E{num_blocks+1}], [E{num_blocks+2}], or any higher numbers. Only use [E1] through [E{num_blocks}].\n\n"
    )

    # Service abbreviations the question uses, as the standard's README defines
    # them. Without this the model guessed ("Cab Announcement" for SIRI-CA).
    named_services = services_in_question(question)
    abbreviation_note = ""
    if named_services:
        meanings = "; ".join(f"{service.abbreviation} = {service.name}" for service in named_services)
        abbreviation_note = (
            f"Abbreviations in the question, as defined in the standard's README: {meanings}. "
            "Do not expand any other abbreviation unless an evidence block defines it.\n\n"
        )

    user_prompt = (
        f"🌍 RESPOND IN: {effective_language if (effective_language or '').lower() not in ('', 'en', 'english') else 'English (detect question language)'}\n\n"
        f"Question:\n{question}\n\n"
        f"{abbreviation_note}"
        f"Requested scope: {scope_text}\n\n"
        f"{faq_section}"
        f"{candidate_index}"
        f"AVAILABLE EVIDENCE BLOCKS (only these may be cited):\n{context}"
        f"{citation_range_warning}"
        "STEP 1 — EVIDENCE MAPPING (do this silently before writing):\n"
        "For each fact you plan to state, identify the exact phrase in the evidence block that supports it. "
        "CRITICAL: Before mentioning ANY SPECIFIC EXAMPLE (like 'SCWW-86', 'LUAS Line 93', specific file names), "
        "verify that this exact example appears verbatim in one of the evidence blocks above. "
        "If you cannot find it, do NOT mention it at all. Instead, say so in the response language "
        "(not English, unless English is the response language). "
        "Do NOT cite sources from the candidate index unless they are also in [E#] evidence blocks.\n\n"
        "STEP 2 — WRITE YOUR ANSWER:\n"
        "- Answer ONLY using information from the evidence blocks above\n"
        "- Cite each fact with [E#] where # is the block number whose text contains that fact\n"
        "- Do NOT cite [E1] for information that is only in [E2], or vice versa\n"
        "- Do NOT reference anything outside these blocks or the candidate index\n"
        "- Do NOT mention specific examples unless they appear in the evidence blocks\n"
        "- Do NOT write file names anywhere in the answer — use only [E#] citation markers to reference sources\n"
        "- If a block is a schema definition file (.xsd), describe it as a 'definition', not an 'example'\n"
        "- If a block is an XML/JSON example file (.xml), describe it as an 'example'\n"
        "- If a requested detail is not in the evidence, explicitly state that — in the response language, not English "
        "(unless English is the response language)\n\n"
        f"{COMPOSITION_RULE + chr(10) if composition else ''}"
        f"{generated_example_rule(example_elements, example_fragment, also_asks, example_origin) + chr(10) + chr(10) if example_elements else ''}"
        f"{schema_structure_rule(structure_element) + chr(10) + chr(10) if structure_element else ''}"
        f"{(MODELLING_RULE if existence == 'how' else EXISTENCE_RULE) + chr(10) + chr(10) if existence and not example_elements and not structure_element else ''}"
        "Write your answer:"
    )

    if not example_elements and not structure_element and _question_requests_verbatim_example(question) and "?" in question and any(w in question.lower() for w in ["is there", "do you have", "any", "list"]):
        user_prompt += "(This question asks for examples: list ALL matching examples found in evidence with their source paths, then provide sample code if available.)"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


SUPPORTED_LLM_PROVIDERS = {"openai-compatible", anthropic_chat.PROVIDER}


def _request_chat_completion(*args, **kwargs) -> dict:
    """_request_chat_completion_untimed, with its time added to the request's timings (llmMs, llmCalls)."""
    from helpdesk.services import request_timing

    with request_timing.timed("llmMs", "llmCalls"):
        response = _request_chat_completion_untimed(*args, **kwargs)
    # Output tokens include thinking: a call's time follows them, not the prompt (2026-11-09: 530 tokens
    # took 2.3 s, 2,000 took 8 s).
    usage = response.get("usage") if isinstance(response, dict) else None
    if isinstance(usage, dict) and isinstance(usage.get("completion_tokens"), int):
        request_timing.add("llmOutputTokens", usage["completion_tokens"])
    return response


def _stream_request_chat_completion(*args, **kwargs) -> Generator[str, None, None]:
    """_stream_request_chat_completion_untimed, timed from the request to the last token (llmMs, llmCalls)."""
    import time

    from helpdesk.services import request_timing

    started = time.perf_counter()
    try:
        yield from _stream_request_chat_completion_untimed(*args, **kwargs)
    finally:
        request_timing.add("llmMs", (time.perf_counter() - started) * 1000, "llmCalls")


def _request_chat_completion_untimed(
    api_base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
    messages: list[dict],
    thinking: str = "adaptive",
) -> dict:
    if settings.LLM_PROVIDER == anthropic_chat.PROVIDER:
        # Claude through the official SDK; same response shape. Every caller here expects a JSON answer.
        return anthropic_chat.chat_completion(
            api_key=settings.ANTHROPIC_API_KEY,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            effort=settings.LLM_ANTHROPIC_EFFORT,
            json_answer=True,
            thinking=thinking,
        )

    def _send(model_to_use: str) -> dict:
        body = {
            "model": model_to_use,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # JSON mode (response_format) keeps the output to the JSON the validator checks, and
            # chat_template_kwargs switches off a reasoning model's thinking (it can otherwise spend the
            # whole budget before any answer). Both are optional per gateway: see services/llm_options.py.
            **answer_request_options(),
        }

        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = request.Request(
            url=f"{api_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers=headers,
        )

        with request.urlopen(
            req,
            timeout=timeout_seconds,
            context=_build_ssl_context(),
        ) as response:
            return json.loads(response.read().decode("utf-8"))

    # Resolve drift proactively against the live gateway (cached after the
    # first check per process) instead of only reacting after a 403.
    effective_model = resolve_effective_model(
        api_base_url=api_base_url,
        api_key=api_key,
        configured_model=model,
        verify_ssl=settings.LLM_VERIFY_SSL,
        ca_bundle=settings.LLM_CA_BUNDLE,
        source="answer_generation",
    )
    try:
        return _send(effective_model)
    except error.HTTPError as exc:
        if exc.code != 403:
            raise
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:  # pragma: no cover
            error_body = ""
        corrected_model = extract_authorized_model(error_body)
        if not corrected_model or corrected_model == effective_model:
            raise
        remember_correction(
            api_base_url=api_base_url,
            configured_model=model,
            corrected_model=corrected_model,
            source="answer_generation",
        )
        return _send(corrected_model)


def _generate_answer_text(
    chunks: list[dict],
    messages: list[dict],
    request_targets: list[dict],
    signals: dict | None = None,
    thinking: str = "adaptive",
) -> str:
    """Execute one LLM call and return the post-processed (unvalidated) answer text.

    `thinking` applies to Claude only: the first attempt passes LLM_ANTHROPIC_FIRST_ANSWER_THINKING,
    a retry keeps the default (adaptive).

    When `signals` is given, it receives "evidence_answers_question" (see _evidence_answers_question).

    Validation is deliberately separate (see _validate_generated_answer) so a
    rejected answer stays available verbatim for retry feedback instead of
    requiring another generation call.
    """
    payload = None
    last_error = None
    try:
        for target in request_targets:
            try:
                payload = _request_chat_completion(
                    api_base_url=target["api_base_url"],
                    api_key=target["api_key"],
                    model=target["model"],
                    timeout_seconds=target["timeout_seconds"],
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=answer_max_tokens(settings.LLM_MAX_TOKENS),
                    messages=messages,
                    thinking=thinking,
                )
                break
            except error.HTTPError as exc:
                try:
                    error_body = exc.read().decode("utf-8")
                except Exception:  # pragma: no cover
                    error_body = ""
                detail = f"LLM HTTP error: {exc.code}"
                if error_body:
                    detail = f"{detail} - {error_body[:500]}"
                last_error = detail
            except Exception as exc:  # pragma: no cover
                last_error = f"LLM request failed: {exc.__class__.__name__}: {exc}"
    except Exception as exc:
        raise LLMGenerationError(str(exc)) from exc

    if payload is None:
        raise LLMGenerationError(last_error or "LLM request failed.")

    choices = payload.get("choices") or []
    if not choices:
        raise LLMGenerationError("LLM response has no choices.")

    answer = (choices[0].get("message", {}).get("content") or "").strip()
    if not answer:
        raise LLMGenerationError("LLM response was empty.")

    logger.info(f"[LLM_RAW] Raw response (first 250 chars): {answer[:250]}")

    if signals is not None:
        signals["evidence_answers_question"] = _evidence_answers_question(answer)
    answer = _unwrap_json_answer(answer)

    # Strip trailing JSON metadata object before any other processing.
    answer = _strip_json_suffix(answer)

    # Strip hallucinated file names early; evidence file names are preserved.
    answer = _strip_raw_filenames(answer, chunks)

    # Strip stray list markers before code blocks (e.g., "1\n```" → "```")
    answer = _strip_stray_list_markers(answer)
    answer = _strip_non_evidence_markup(answer)
    answer = _complete_xml_snippets(answer)

    # Fix out-of-range citations before validation (LLM may hallucinate [E10] when only [E1-E6] exist)
    max_chunk_idx = len(chunks)
    answer = _fix_out_of_range_citations(answer, max_chunk_idx)

    return answer


def _validate_generated_answer(answer: str, chunks: list[dict]) -> None:
    """Run all grounding validators against a generated answer.

    Raises LLMGenerationError on the first failed check. Standards validation
    stays disabled: too many false positives on file name components; the
    citation grounding validator already catches real hallucinations.
    """
    try:
        _validate_citations_to_chunks(answer=answer, chunks=chunks)
        _validate_citation_grounding(answer=answer, chunks=chunks)
        _validate_no_raw_filenames(answer=answer, chunks=chunks)
        _validate_answer_has_specificity(answer=answer)
        _validate_no_unsupported_element_purpose_claims(answer=answer, chunks=chunks)
    except LLMGenerationError as exc:
        logger.info(f"[VALIDATE] Validation FAILED: {str(exc)[:150]}")
        raise
    logger.info("[VALIDATE] All validators PASSED")


def _append_feedback_message(
    messages: list[dict], rejected_answer: str, error_msg: str, legislation: bool = False
) -> list[dict]:
    """Return a new messages list with a feedback turn appended for retry.

    With EU legislation or NAPCORE documents in the evidence the fix asks for articles, documents and quotes,
    not XML elements (#91).
    """
    # Add specific guidance if the error is about file names
    file_name_hint = ""
    if "file name" in error_msg.lower() or "raw file" in error_msg.lower():
        file_name_hint = "\n- CRITICAL: Do NOT write file names or paths like 'example.xml' or 'schema/file.xsd'. Instead write: 'The example [E2]' or 'In the schema definition [E1]'. The [E#] reference tells readers where the actual file is."

    # Add specific guidance for invented examples
    example_hint = ""
    if "citation" in error_msg.lower() or "not in" in error_msg.lower() or "evidence" in error_msg.lower():
        example_hint = "\n- CRITICAL: Do NOT mention specific numbered examples (like 'SCWW-86' or 'LUAS Line 93') unless you find those EXACT examples in the evidence blocks. You can mention generic standard names if they appear in evidence, but NOT specific numbered instances you know from training."

    # Add specific guidance for unsupported element-purpose claims
    purpose_claim_hint = ""
    if "purpose/meaning" in error_msg.lower() or "is not its definition" in error_msg.lower():
        purpose_claim_hint = (
            "\n- CRITICAL: Do NOT explain what an XML element means or is used for based on its name. "
            "Check EVERY evidence block for a definition of that element, not just the block you quote "
            "XML from — if a different block ([E1], [E2], etc.) defines it, cite that definition block "
            "in the same sentence alongside the example citation, and KEEP any verbatim XML snippet from "
            "the evidence; do not drop content or evidence blocks that were already correct just because "
            "one claim needed a different citation. Only omit a purpose claim, or say the evidence does "
            "not define it, when no evidence block anywhere defines that element."
        )

    # Add specific guidance for language errors
    language_hint = ""
    if "language" in error_msg.lower() or "english" in error_msg.lower():
        language_hint = (
            "\n- CRITICAL LANGUAGE REQUIREMENT: write your entire answer in the language the rejection reason "
            "names (the question's language), whatever language the evidence blocks are in. Keep technical "
            "terms, class names, XML tags, and identifiers as they appear in the evidence."
        )

    if legislation:
        return messages + [
            {"role": "assistant", "content": rejected_answer},
            {
                "role": "user",
                "content": (
                    f"Your previous answer was REJECTED.\nRejected answer: {rejected_answer[:400]}\n"
                    f"Reason: {error_msg[:250]}\n\n"
                    "REQUIRED FIX — Your new answer MUST:\n"
                    "1. For EU legislation blocks, name the article or annex point in each cited sentence and "
                    "quote the provision verbatim (in English, as in the evidence); for NAPCORE documents, name "
                    "the document and quote its wording\n"
                    "2. Cite the block that states each claim; do not cite a block for what it does not say\n"
                    "3. Not mention XML elements, attributes or code unless a standards block shows them\n"
                    "4. Keep the response language of the question"
                    f"{language_hint}"
                ),
            },
        ]

    feedback = (
        f"Your previous answer was REJECTED. It did not meet requirements.\n"
        f"Rejected answer: {rejected_answer[:400]}\n"
        f"Reason: {error_msg[:250]}\n\n"
        "REQUIRED FIX — Your new answer MUST:\n"
        "1. Include SPECIFIC XML ELEMENT NAMES from the evidence (e.g., <DepartureTime>, <Journey>, <Call>)\n"
        "2. Cite EXACTLY which evidence block contains each element\n"
        "3. Do NOT give generic advice. Extract only technical facts from evidence.\n"
        "4. Do NOT say 'follow the specification' or 'validate implementation'\n"
        "5. If evidence shows code/XML, include a snippet with element names\n"
        "6. If you cannot find specific technical details, say so clearly — in the response language, not English "
        "(unless English is the response language)\n"
        "7. EVERY sentence must have [E#] citation to the exact evidence block"
        f"{file_name_hint}{example_hint}{purpose_claim_hint}{language_hint}"
    )
    return messages + [
        {"role": "assistant", "content": rejected_answer},
        {"role": "user", "content": feedback},
    ]


def generate_answer_llm(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    faq_hint: str | None = None,
    language: str | None = None,
    all_candidates: list[dict] | None = None,
    example_elements: list[str] | None = None,
    structure_element: str | None = None,
    example_fragment: str = "",
    also_asks: str = "",
    example_origin: str = "generated",
    existence: bool | str = False,
) -> dict:
    """Generate a grounded answer through a configurable OpenAI-compatible API.

    With `example_elements` (a valid generated example is shown first, using these elements), the text
    only adds what the evidence says about them and may be empty: see generated_example_rule.

    Attempts generation up to twice: the first attempt uses the standard prompt;
    if a grounding validator rejects the answer, a second attempt is made with
    explicit feedback explaining exactly what was wrong.  Both the rejected answer
    and the rejection reason are returned in the result dict for trace logging.
    """

    logger.info(f"[GENERATE_LLM_START] Question: {question[:80]}, chunks: {len(chunks)}")

    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER not in SUPPORTED_LLM_PROVIDERS:
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    max_chunks = max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))
    max_chars_per_chunk = max(200, int(getattr(settings, "LLM_MAX_EVIDENCE_CHARS_PER_CHUNK", 1200)))
    # Detected once: the prompt names it, and _validate_answer_language checks the answer against it.
    target_language = question_language(question)
    messages = _build_messages(
        question=question,
        chunks=chunks,
        scope=scope,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
        faq_hint=faq_hint,
        language=language,
        all_candidates=all_candidates,
        detected_language=target_language,
        example_elements=example_elements,
        structure_element=structure_element,
        example_fragment=example_fragment,
        also_asks=also_asks,
        example_origin=example_origin,
        existence=existence,
    )

    primary_base_url = (settings.LLM_API_BASE_URL or "").strip()
    primary_api_key = (settings.LLM_API_KEY or "").strip()

    request_targets = [
        {
            "api_base_url": primary_base_url,
            "api_key": primary_api_key,
            "model": settings.LLM_MODEL,
            "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        }
    ]

    github_api_token = (getattr(settings, "GITHUB_API_TOKEN", "") or "").strip()
    if (
        _is_github_models_base_url(primary_base_url)
        and github_api_token
        and github_api_token != primary_api_key
    ):
        request_targets.append(
            {
                "api_base_url": primary_base_url,
                "api_key": github_api_token,
                "model": settings.LLM_MODEL,
                "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
            }
        )

    rejected_answer: str | None = None
    rejection_reason: str | None = None
    answer_validated = True

    # First attempt: generation and validation run separately so the rejected
    # answer text (not just the validator's error) is available for retry feedback.
    answer: str | None = None
    signals: dict = {}
    try:
        answer = _generate_answer_text(
            chunks=chunks,
            messages=messages,
            request_targets=request_targets,
            signals=signals,
            thinking=settings.LLM_ANTHROPIC_FIRST_ANSWER_THINKING,
        )
        if (example_elements or structure_element) and not answer.strip():
            return _nothing_to_add(chunks)
        _validate_answer_language(answer=answer, question=question, target_language=target_language)
        _validate_generated_answer(answer=answer, chunks=chunks)
    except LLMGenerationError as first_error:
        rejected_answer = answer or ""
        rejection_reason = str(first_error)
        logger.warning(
            "LLM first attempt rejected by validator; retrying with feedback. Reason: %s",
            rejection_reason[:200],
            extra={"question": question[:120]},
        )
        # Second attempt with explicit correction feedback. If generation itself
        # failed (no answer produced), feedback about a rejected answer does not
        # apply — retry the original prompt instead.
        if rejected_answer:
            retry_messages = _append_feedback_message(
                messages=messages,
                rejected_answer=rejected_answer,
                error_msg=rejection_reason,
                legislation=_has_prose_evidence(chunks, max_chunks),
            )
        else:
            retry_messages = messages
        try:
            answer = _generate_answer_text(
                chunks=chunks, messages=retry_messages, request_targets=request_targets, signals=signals
            )
        except Exception as fatal_error:
            # Even the second attempt failed. This is a critical issue.
            # Return an honest error message instead of letting exception propagate to fallback.
            logger.error(
                "FATAL: Both LLM attempts failed. Cannot generate answer. Exception: %s",
                str(fatal_error)[:200],
                extra={"question": question[:120]},
                exc_info=True,
            )
            answer = (
                "I was unable to generate a proper answer due to technical issues with the LLM. "
                "The evidence retrieval worked, but the answer generation failed. "
                "Please try again or contact support."
            )
            confidence = 0.0
            # Return immediately to prevent fallback to generic boilerplate
            return {
                "answer": answer,
                "confidence": confidence,
                "review_required": True,
                "provider": settings.LLM_PROVIDER,
                "model": (request_targets[0]["model"]),
                "rejected_answer": rejected_answer,
                "rejection_reason": rejection_reason,
            }
        if (example_elements or structure_element) and not answer.strip():
            return _nothing_to_add(chunks)
        try:
            _validate_answer_language(answer=answer, question=question, target_language=target_language)
            _validate_generated_answer(answer=answer, chunks=chunks)
        except LLMGenerationError as retry_error:
            # Retry failed validation too, but it did produce an answer. Keep it
            # as-is rather than paying for a third generation call — the feedback
            # was the best guidance we could provide.
            logger.warning(
                "LLM retry failed validation too; using the retry answer as-is, marked for review. Reason: %s",
                str(retry_error)[:200],
                extra={"question": question[:120]},
            )
            rejection_reason = f"{rejection_reason} | retry also failed: {retry_error}"[:500]
            answer_validated = False

    _validate_grounded_example_output(question=question, answer=answer, chunks=chunks, shown_fragment=example_fragment)

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

    # Final safety: strip any remaining file names (in case validation passed but LLM still included them)
    answer = _strip_raw_filenames(answer, chunks)

    # FINAL ENFORCEMENT: If answer is still pure boilerplate despite all attempts,
    # replace it with an honest "unable to answer" message rather than returning generic advice
    is_boilerplate = _is_pure_boilerplate(answer)
    logger.info(f"[FINAL_CHECK] Boilerplate detected: {is_boilerplate}, answer_preview: {answer[:100]}")

    if is_boilerplate:
        logger.warning(
            "[BOILERPLATE_REPLACEMENT] Replacing boilerplate with honest message",
            extra={"question": question[:100]},
        )
        logger.warning(
            "FINAL ENFORCEMENT: Answer was detected as pure boilerplate at end of generation. "
            "Replacing with honest answer.",
            extra={"question": question[:120], "boilerplate_answer": answer[:200]},
        )
        answer = (
            "The provided evidence does not contain specific technical details about this topic. "
            "To answer this question properly, I would need evidence blocks that include specific "
            "XML element names, attribute definitions, or code examples."
        )
        confidence = 0.0
        review_required = True

    logger.info(
        f"[GENERATE_LLM_END] Returning answer with confidence {confidence}. "
        f"Answer preview: {answer[:80]}"
    )

    if not answer_validated:
        confidence = min(confidence, UNVALIDATED_ANSWER_MAX_CONFIDENCE)

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.82 or not answer_validated,
        "answer_validated": answer_validated,
        "evidence_answers_question": signals.get("evidence_answers_question"),
        "provider": settings.LLM_PROVIDER,
        "model": (request_targets[0]["model"]),
        "rejected_answer": rejected_answer,
        "rejection_reason": rejection_reason,
    }


def _stream_request_chat_completion_untimed(
    api_base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
    messages: list[dict],
) -> Generator[str, None, None]:
    """Yield raw token delta strings from an OpenAI-compatible streaming chat completion."""

    def _build_request(model_to_use: str) -> request.Request:
        body = {
            "model": model_to_use,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            # Tokens are fully buffered and validated before any reach the client, so JSON mode is
            # safe here. Same optional fields as _request_chat_completion.
            **answer_request_options(),
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return request.Request(
            url=f"{api_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers=headers,
        )

    # Resolve drift proactively against the live gateway (cached after the
    # first check per process) instead of only reacting after a 403.
    effective_model = resolve_effective_model(
        api_base_url=api_base_url,
        api_key=api_key,
        configured_model=model,
        verify_ssl=settings.LLM_VERIFY_SSL,
        ca_bundle=settings.LLM_CA_BUNDLE,
        source="answer_generation_stream",
    )
    try:
        response = request.urlopen(
            _build_request(effective_model), timeout=timeout_seconds, context=_build_ssl_context()
        )
    except error.HTTPError as exc:
        if exc.code != 403:
            raise
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:  # pragma: no cover
            error_body = ""
        corrected_model = extract_authorized_model(error_body)
        if not corrected_model or corrected_model == effective_model:
            raise
        remember_correction(
            api_base_url=api_base_url,
            configured_model=model,
            corrected_model=corrected_model,
            source="answer_generation_stream",
        )
        response = request.urlopen(
            _build_request(corrected_model), timeout=timeout_seconds, context=_build_ssl_context()
        )

    with response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            payload_str = line[len("data:"):].strip()
            if payload_str == "[DONE]":
                break
            try:
                chunk = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta", {}).get("content") or ""
            if delta:
                yield delta


def stream_answer_llm(
    question: str,
    chunks: list[dict],
    scope: list[str] | None = None,
    faq_hint: str | None = None,
    language: str | None = None,
    all_candidates: list[dict] | None = None,
    example_elements: list[str] | None = None,
    structure_element: str | None = None,
    example_fragment: str = "",
    also_asks: str = "",
    example_origin: str = "generated",
    existence: bool | str = False,
) -> Generator[tuple[str, object], None, None]:
    """
    Generator yielding (event_type, payload) tuples for streaming narration.

    Yields:
        ("status", "retrying") — before a retry when the first answer fails validation.
        ("token", delta_str) — for each token from the LLM.
        ("done", metadata_dict) — once after all tokens, with answer metadata.

    All tokens are buffered and validated before being yielded to the caller.
    This prevents the 'answer shows then disappears' pattern that occurs when
    validation fails after tokens have already been sent to the client.
    """
    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER not in SUPPORTED_LLM_PROVIDERS:
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    primary_base_url = (settings.LLM_API_BASE_URL or "").strip()
    primary_api_key = (settings.LLM_API_KEY or "").strip()
    if not primary_base_url:
        raise LLMGenerationError("LLM API base URL is not configured.")

    max_chunks = max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))
    max_chars_per_chunk = max(200, int(getattr(settings, "LLM_MAX_EVIDENCE_CHARS_PER_CHUNK", 1200)))
    # Detect once and share: _build_messages uses it for the prompt's language
    # instruction, and the _validate_answer_language() calls below compare
    # against it.
    detected_language = question_language(question)
    effective_language = detected_language
    messages = _build_messages(
        question=question,
        chunks=chunks,
        scope=scope,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
        faq_hint=faq_hint,
        language=language,
        all_candidates=all_candidates,
        detected_language=detected_language,
        example_elements=example_elements,
        structure_element=structure_element,
        example_fragment=example_fragment,
        also_asks=also_asks,
        example_origin=example_origin,
        existence=existence,
    )

    # Buffer all tokens before yielding any — validation must pass the full
    # answer before the client receives a single character, so a failed check
    # never produces a visible-then-vanishing answer.
    def _collect_stream(active_messages: list[dict], thinking: str = "adaptive") -> str:
        collected: list[str] = []
        try:
            if settings.LLM_STREAMING and settings.LLM_PROVIDER != anthropic_chat.PROVIDER:
                for delta in _stream_request_chat_completion(
                    api_base_url=primary_base_url,
                    api_key=primary_api_key,
                    model=settings.LLM_MODEL,
                    timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=answer_max_tokens(settings.LLM_MAX_TOKENS),
                    messages=active_messages,
                ):
                    collected.append(delta)
            else:
                # The gateway accepts only stream=false (LLM_STREAMING=False), or the provider is Anthropic.
                # Nothing is lost: the answer is buffered and validated before the client sees it either way.
                payload = _request_chat_completion(
                    api_base_url=primary_base_url,
                    api_key=primary_api_key,
                    model=settings.LLM_MODEL,
                    timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=answer_max_tokens(settings.LLM_MAX_TOKENS),
                    messages=active_messages,
                    thinking=thinking,
                )
                choices = payload.get("choices") or []
                collected.append(((choices[0].get("message") or {}).get("content") or "") if choices else "")
        except error.HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                error_body = ""
            detail = f"LLM HTTP error: {exc.code}"
            if error_body:
                detail = f"{detail} - {error_body[:500]}"
            raise LLMGenerationError(detail) from exc
        except error.URLError as exc:
            raise LLMGenerationError(f"LLM stream request failed: {exc.reason}") from exc
        except anthropic_chat.AnthropicRequestError as exc:
            raise LLMGenerationError(str(exc)) from exc
        text = "".join(collected)
        if not text.strip():
            raise LLMGenerationError("LLM stream response was empty.")
        return text

    # First attempt
    rejected_answer: str | None = None
    rejection_reason: str | None = None
    answer_validated = True
    evidence_answers_question: bool | None = None
    try:
        full_answer = _collect_stream(messages, thinking=settings.LLM_ANTHROPIC_FIRST_ANSWER_THINKING)

        logger.info(f"[STREAM_LLM_RAW] Raw response (first 250 chars): {full_answer[:250]}")
        evidence_answers_question = _evidence_answers_question(full_answer)
        full_answer = _unwrap_json_answer(full_answer)
        if (example_elements or structure_element) and not full_answer.strip():
            yield ("done", _nothing_to_add(chunks))
            return

        # Strip hallucinated file names; evidence file names are preserved.
        full_answer = _strip_json_suffix(full_answer)
        full_answer = _strip_raw_filenames(full_answer, chunks)
        full_answer = _strip_stray_list_markers(full_answer)
        full_answer = _strip_non_evidence_markup(full_answer)
        full_answer = _complete_xml_snippets(full_answer)
        _validate_answer_language(answer=full_answer, question=question, target_language=effective_language)
        _validate_generated_answer(answer=full_answer, chunks=chunks)
        _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks, shown_fragment=example_fragment)
    except LLMGenerationError as first_error:
        rejected_answer = full_answer if "full_answer" in dir() else ""
        rejection_reason = str(first_error)
        logger.warning(
            "Stream first attempt rejected; retrying with feedback. Reason: %s",
            rejection_reason[:200],
            extra={"question": question[:120]},
        )
        retry_messages = _append_feedback_message(
            messages=messages,
            rejected_answer=rejected_answer,
            error_msg=rejection_reason,
            legislation=_has_prose_evidence(chunks, max_chunks),
        )
        # The retry is a second full LLM call with nothing sent meanwhile; tell the
        # caller so the client connection does not sit silent through both calls.
        yield ("status", "retrying")
        full_answer = _collect_stream(retry_messages)

        logger.info(f"[STREAM_RETRY_RAW] Retry response (first 250 chars): {full_answer[:250]}")
        evidence_answers_question = _evidence_answers_question(full_answer)
        full_answer = _unwrap_json_answer(full_answer)
        if (example_elements or structure_element) and not full_answer.strip():
            yield ("done", _nothing_to_add(chunks))
            return

        # Strip hallucinated file names; evidence file names are preserved.
        full_answer = _strip_json_suffix(full_answer)
        full_answer = _strip_raw_filenames(full_answer, chunks)
        full_answer = _strip_stray_list_markers(full_answer)
        full_answer = _strip_non_evidence_markup(full_answer)
        full_answer = _complete_xml_snippets(full_answer)
        try:
            _validate_answer_language(answer=full_answer, question=question, target_language=effective_language)
            _validate_generated_answer(answer=full_answer, chunks=chunks)
            _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks, shown_fragment=example_fragment)
        except LLMGenerationError as retry_error:
            # Retry failed validation too. A real, on-topic answer that fails a strict
            # grounding heuristic is still far more useful than the generic
            # non-LLM deterministic template views.py falls back to if this
            # propagates - use the retry's answer as-is rather than raising.
            logger.warning(
                "Stream retry failed validation too; using raw retry answer instead of "
                "falling back to the deterministic template, marked for review. Reason: %s",
                str(retry_error)[:200],
                extra={"question": question[:120]},
            )
            rejection_reason = f"{rejection_reason} | retry also failed: {retry_error}"[:500]
            answer_validated = False

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))
    if not answer_validated:
        confidence = min(confidence, UNVALIDATED_ANSWER_MAX_CONFIDENCE)

    # Validation passed — now yield the buffered answer so the client receives
    # only valid content. Emit multi-character slices, not single characters:
    # each yield becomes one SSE event, and per-character events inflate the
    # event count by an order of magnitude for no smoother rendering.
    chunk_size = 24
    for start in range(0, len(full_answer), chunk_size):
        yield ("token", full_answer[start : start + chunk_size])

    yield (
        "done",
        {
            "answer": full_answer,
            "confidence": confidence,
            "review_required": confidence < 0.82 or not answer_validated,
            "answer_validated": answer_validated,
            "evidence_answers_question": evidence_answers_question,
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "rejected_answer": rejected_answer,
            "rejection_reason": rejection_reason,
        },
    )
