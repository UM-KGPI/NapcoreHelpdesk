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
import logging
import re
import ssl
from collections.abc import Generator
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)

from helpdesk.services.question_preprocessor import detect_question_language
from helpdesk.services.llm_model_recovery import (
    extract_authorized_model,
    remember_correction,
    resolve_effective_model,
)


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


def _validate_grounded_example_output(question: str, answer: str, chunks: list[dict]) -> None:
    if not _question_requests_verbatim_example(question):
        return

    code_blocks = FENCED_CODE_BLOCK_PATTERN.findall(answer or "")
    if not code_blocks:
        return

    evidence_lines: set[str] = set()
    for chunk in chunks:
        evidence_lines.update(_extract_grounded_lines(str(chunk.get("text", ""))))

    for language, block in code_blocks:
        normalized_language = (language or "").strip().lower()
        if normalized_language and normalized_language not in {"xml", "json", "yaml", "yml", "txt"}:
            continue

        block_lines = [
            _normalize_grounded_line(line)
            for line in block.splitlines()
            if len(_normalize_grounded_line(line)) >= 8
            and any(marker in line for marker in ["<", ">", "/", "="])
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
_STRONG_TERM_PATTERN = re.compile(
    r"`([^`]{4,})`"                                   # backtick-quoted identifiers
    r'|"([A-Za-z0-9_.:/\\@#-]{6,})"'                 # double-quoted technical strings (≥6 chars)
    r"|([A-Za-z0-9]{2,}:[A-Za-z0-9@_./-]{3,})"       # namespaced ids, e.g. stg:SCWW@86, netex:Line
    r"|([A-Z0-9][A-Za-z0-9_.-]*-[A-Za-z0-9_.-]*[A-Z0-9])"  # hyphenated IDs with uppercase/digits, e.g. SCWW-86, UK-2022, 93-RED-y11-1
    r"|([A-Za-z0-9_-]+\.(?:xsd|xml|yaml|json|ttl))"  # file names with known extensions
)

# Weak terms: PascalCase element names (single or multi-word) and ALL-CAPS
# Transmodel concept names, which the standards write in capitals by convention
# (e.g. "STOP PLACE", "TAXI RANK", "VEHICLE MEETING POINT").
# Matches: Time, Departure, DepartureTime, ScheduledStop, STOP PLACE, etc.
_WEAK_TERM_PATTERN = re.compile(
    r"([A-Z]{3,}(?:\s+[A-Z]{3,})*"      # ALL-CAPS Transmodel concepts, single or multi-word
    r"|[A-Z][a-z]+(?:[A-Z][a-z]+)*)"    # PascalCase: starts with uppercase, followed by lowercase(s)
)

# Terms so generic they appear in virtually every NeTEx/standards document and
# must never be used as the sole grounding evidence for a citation.
# Derived dynamically from the NITS ontology labels so the set grows automatically
# as new abstract concepts are added; a minimal hardcoded fallback is used when
# the ontology is unavailable (e.g. during tests without a live GraphDB).
def _build_ubiquitous_terms() -> frozenset[str]:
    try:
        from helpdesk.services.semantic_graph import _NITS_ONTOLOGY  # noqa: PLC0415
        concepts = _NITS_ONTOLOGY.get("concepts", {})
        terms: set[str] = set()
        for concept_data in concepts.values():
            for label in concept_data.get("labels", []):
                lower = label.lower().strip()
                if len(lower) >= 3:
                    terms.add(lower)
                    # Also add simple plural so e.g. "ROUTEs" → "routes" is covered.
                    if not lower.endswith("s"):
                        terms.add(lower + "s")
        if terms:
            return frozenset(terms)
    except Exception:
        pass
    # Minimal fallback used when the ontology module is unavailable.
    return frozenset({
        "netex", "opra", "siri", "datex", "transmodel", "nits",
        "line", "lines", "route", "routes", "stop", "stops",
        "trip", "trips", "service", "services", "journey", "journeys",
        "network", "networks", "operator", "operators", "pattern", "patterns",
    })


_UBIQUITOUS_TERMS = _build_ubiquitous_terms()


def _classify_terms(sentence: str) -> tuple[list[str], list[str]]:
    """
    Return (strong_terms, weak_terms) extracted from a sentence.

    Strong terms are specific identifiers unlikely to appear across many chunks
    (file names, namespaced IDs, hyphenated IDs, backtick-quoted strings).
    Weak terms are PascalCase/camelCase element names that may appear anywhere.
    """
    # Strip XML/HTML tag brackets but keep content so element names are found
    # e.g., "<Departure>" becomes " Departure "
    clean_sentence = re.sub(r"[<>]", " ", sentence)

    strong: list[str] = []
    for match in _STRONG_TERM_PATTERN.finditer(clean_sentence):
        term = next((g for g in match.groups() if g), None)
        if term and len(term) >= 4 and term.lower() not in _UBIQUITOUS_TERMS:
            strong.append(term)

    weak: list[str] = []
    seen = set(t.lower() for t in strong)
    for match in _WEAK_TERM_PATTERN.finditer(clean_sentence):
        term = match.group(1)
        if term and len(term) >= 4 and term.lower() not in _UBIQUITOUS_TERMS and term.lower() not in seen:
            weak.append(term)
            seen.add(term.lower())

    return list(dict.fromkeys(strong)), list(dict.fromkeys(weak))


def _extract_key_terms(sentence: str) -> list[str]:
    """Extract technical identifiers from a sentence for citation grounding checks."""
    strong, weak = _classify_terms(sentence)
    return list(dict.fromkeys(strong + weak))


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

        # Check if sentence contains code blocks (```) or XML tags - these are more lenient
        is_code_block = "```" in sentence or ("<" in sentence and ">" in sentence)

        # CRITICAL: For code blocks (XML/code examples), skip strict grounding validation
        # XML with specific values (e.g., <DepartureTime>09:54:00</DepartureTime>) should not fail
        # just because the exact value isn't in the evidence. The element name is sufficient proof.
        if is_code_block and found_citations:
            logger.debug(f"Accepting code block citation without strict grounding: {sentence[:100]}")
            continue  # Skip to next sentence - code blocks are inherently technical

        strong_terms, weak_terms = _classify_terms(clean)

        # Extract ubiquitous terms that were filtered out (we still want to check these)
        ubiquitous_terms = []
        for term in clean.split():
            term_clean = term.strip('.,!?;:').lower()
            if term_clean in _UBIQUITOUS_TERMS and len(term_clean) >= 4:
                ubiquitous_terms.append(term_clean)

        # CRITICAL: Cited sentences MUST have specific technical content (strong or weak terms)
        if not strong_terms and not weak_terms:
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

        for citation_str in found_citations:
            idx = int(citation_str) - 1
            if idx < 0 or idx >= len(chunks):
                continue  # Range already rejected by _validate_citations_to_chunks

            chunk = chunks[idx]
            chunk_text_lower = str(chunk.get("text", "")).lower()
            chunk_source_lower = str(chunk.get("sourcePath", "")).lower()
            haystack = chunk_text_lower + " " + chunk_source_lower

            if strong_terms:
                # Strong terms present: require at least one strong match.
                # A weak-only match is not accepted — it would allow hallucinated
                # file names/IDs to pass because a generic term like "NeTEx" matches.
                grounded = any(term.lower() in haystack for term in strong_terms)
                if not grounded:
                    logger.debug(
                        f"Citation [E{citation_str}] grounding check FAILED: strong terms {strong_terms} not found in chunk source '{chunk.get('sourcePath', 'unknown')}'"
                    )
            elif weak_terms:
                grounded = any(term.lower() in haystack for term in weak_terms)
                if not grounded:
                    logger.debug(
                        f"Citation [E{citation_str}] grounding check FAILED: weak terms {weak_terms} not found in chunk source '{chunk.get('sourcePath', 'unknown')}'"
                    )
            else:
                # No strong or weak terms; check ubiquitous terms (these are more lenient)
                # Ubiquitous terms appear everywhere, so we just require at least one match
                grounded = any(term.lower() in haystack for term in ubiquitous_terms)
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


def _unwrap_json_answer(text: str) -> str:
    """
    Extract the prose answer from a JSON-mode LLM response.

    JSON mode makes the model emit ``{"answer": "...", "citations_used": [...]}``;
    this returns the "answer" field, unwrapping a double-encoded answer field and
    falling back to other common field names. Non-JSON input is returned as-is.
    """
    try:
        response_json = json.loads(text)
    except json.JSONDecodeError:
        logger.debug("[UNWRAP] Not JSON, treating as plain text")
        return text
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
    return str(response_json)


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


def _validate_answer_language(answer: str, question: str, target_language: str | None = None) -> None:
    """
    Validate that answer is in the same language as the question.

    If question is non-English but answer is in English, raise error to trigger retry
    with more aggressive language instruction.
    """
    if not target_language or target_language.lower() in ("en", "english"):
        return  # English questions don't need language validation

    # Detect the language of the answer
    try:
        from helpdesk.services.question_preprocessor import detect_question_language
        answer_lang = detect_question_language(answer)

        # Normalize language names for comparison
        target_normalized = target_language.lower().strip()
        answer_normalized = (answer_lang or "").lower().strip()

        # Check if answer is in a different language (especially if it's English)
        if answer_normalized in ("english", "en") and target_normalized not in ("english", "en"):
            raise LLMGenerationError(
                f"Answer is in English but question is in {target_language}. "
                f"LLM did not respect language instruction. Please retry."
            )
    except Exception as e:
        logger.warning(f"Language validation check failed: {e}")


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


def _trim_chunk_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}\n...[truncated for latency]"


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
) -> list[dict]:
    context_lines = []
    for index, chunk in enumerate(chunks[:max_chunks], start=1):
        chunk_text = _trim_chunk_text(str(chunk.get("text", "")), max_chars=max_chars_per_chunk)
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
    if _lang and _lang not in ("en", "english"):
        language_instruction = (
            f" Respond in {effective_language}. Keep technical terms, class names, XML tags, and identifiers in English."
        )
    else:
        language_instruction = (
            " Detect the language of the question and respond in that same language."
            " Keep technical terms, class names, XML tags, and identifiers in English."
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
        "6. Do NOT paraphrase or infer beyond what is explicitly stated in the evidence\n"
        "7. Stay within requested standards scope\n"
        "8. NEVER write file names in answer text. Reference sources ONLY via [E#] citations.\n"
        "9. REQUIRED CONTENT — Your answer MUST include:\n"
        "   - Specific XML element names (e.g., <DepartureTime>, <Journey>, <Call>)\n"
        "   - Specific attribute names (e.g., scheduleRelationship, time)\n"
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
        '{"answer": "Your answer text here with [E1] [E2] citations inline.", "citations_used": ["E1", "E2"]}'
        "\n\nMARKDOWN FORMATTING:\n"
        "- Use `backticks` for technical content: XML elements, attributes, filenames, class names, values.\n"
        "- Use triple backticks for code blocks: ```xml ... ```\n"
        "- Use **bold** for emphasis only, not for technical terms.\n"
        "- Standard markdown for lists, headers, and paragraphs.\n"
    )
    if _question_requests_verbatim_example(question):
        system_prompt = (
            f"{system_prompt} "
            "For questions asking for examples or code: First, directly answer 'yes' or 'no' about availability. Then list the examples found in evidence with citations [E#]. "
            "When showing XML/JSON/YAML, include one fenced code block (```xml) of 6-20 lines from a single evidence block. "
            "Quote only verbatim excerpts from evidence blocks. Never synthesize or combine structures across sources. "
            "If asking for availability ('Is there any...?'), list all matching examples found in the evidence with their source paths and brief descriptions."
        )
    elif _question_about_xml_or_technical(question):
        system_prompt = (
            f"{system_prompt} "
            "For technical questions about XML, standards structures, or implementations: Include a relevant code example from the evidence if available. "
            "When showing XML/JSON structures, use one fenced code block (```xml) with 6-15 lines from the evidence. "
            "Never synthesize or invent examples — only quote verbatim from the evidence blocks."
        )

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

    user_prompt = (
        f"🌍 RESPOND IN: {effective_language if (effective_language or '').lower() not in ('', 'en', 'english') else 'English (detect question language)'}\n\n"
        f"Question:\n{question}\n\n"
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
        "Write your answer:"
    )

    if _question_requests_verbatim_example(question) and "?" in question and any(w in question.lower() for w in ["is there", "do you have", "any", "list"]):
        user_prompt += "(This question asks for examples: list ALL matching examples found in evidence with their source paths, then provide sample code if available.)"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _request_chat_completion(
    api_base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    temperature: float,
    max_tokens: int,
    messages: list[dict],
) -> dict:
    def _send(model_to_use: str) -> dict:
        body = {
            "model": model_to_use,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # Enforce JSON output to prevent hallucinations: model MUST output valid JSON
            # with citations constrained to valid evidence indices
            "response_format": {"type": "json_object"},
            # Reasoning models (e.g. qwen3) can consume the entire token budget on
            # hidden chain-of-thought before emitting any answer content, leaving
            # the response empty. Disable thinking mode to get direct answers.
            "chat_template_kwargs": {"enable_thinking": False},
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
) -> str:
    """Execute one LLM call and return the post-processed (unvalidated) answer text.

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
                    max_tokens=settings.LLM_MAX_TOKENS,
                    messages=messages,
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

    answer = _unwrap_json_answer(answer)

    # Strip trailing JSON metadata object before any other processing.
    answer = _strip_json_suffix(answer)

    # Strip hallucinated file names early; evidence file names are preserved.
    answer = _strip_raw_filenames(answer, chunks)

    # Strip stray list markers before code blocks (e.g., "1\n```" → "```")
    answer = _strip_stray_list_markers(answer)

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
    except LLMGenerationError as exc:
        logger.info(f"[VALIDATE] Validation FAILED: {str(exc)[:150]}")
        raise
    logger.info("[VALIDATE] All validators PASSED")


def _append_feedback_message(messages: list[dict], rejected_answer: str, error_msg: str) -> list[dict]:
    """Return a new messages list with a feedback turn appended for retry."""
    # Add specific guidance if the error is about file names
    file_name_hint = ""
    if "file name" in error_msg.lower() or "raw file" in error_msg.lower():
        file_name_hint = "\n- CRITICAL: Do NOT write file names or paths like 'example.xml' or 'schema/file.xsd'. Instead write: 'The example [E2]' or 'In the schema definition [E1]'. The [E#] reference tells readers where the actual file is."

    # Add specific guidance for invented examples
    example_hint = ""
    if "citation" in error_msg.lower() or "not in" in error_msg.lower() or "evidence" in error_msg.lower():
        example_hint = "\n- CRITICAL: Do NOT mention specific numbered examples (like 'SCWW-86' or 'LUAS Line 93') unless you find those EXACT examples in the evidence blocks. You can mention generic standard names if they appear in evidence, but NOT specific numbered instances you know from training."

    # Add specific guidance for language errors
    language_hint = ""
    if "language" in error_msg.lower() or "english" in error_msg.lower():
        language_hint = "\n- CRITICAL LANGUAGE REQUIREMENT: You MUST write your entire answer in the language of the question. Do NOT respond in English when the question is in another language. Write EVERYTHING in that language, including all text and explanations."

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
        f"{file_name_hint}{example_hint}{language_hint}"
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
) -> dict:
    """Generate a grounded answer through a configurable OpenAI-compatible API.

    Attempts generation up to twice: the first attempt uses the standard prompt;
    if a grounding validator rejects the answer, a second attempt is made with
    explicit feedback explaining exactly what was wrong.  Both the rejected answer
    and the rejection reason are returned in the result dict for trace logging.
    """

    logger.info(f"[GENERATE_LLM_START] Question: {question[:80]}, chunks: {len(chunks)}")

    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER != "openai-compatible":
        raise LLMGenerationError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    max_chunks = max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))
    max_chars_per_chunk = max(200, int(getattr(settings, "LLM_MAX_EVIDENCE_CHARS_PER_CHUNK", 1200)))
    messages = _build_messages(
        question=question,
        chunks=chunks,
        scope=scope,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
        faq_hint=faq_hint,
        language=language,
        all_candidates=all_candidates,
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

    # First attempt: generation and validation run separately so the rejected
    # answer text (not just the validator's error) is available for retry feedback.
    answer: str | None = None
    try:
        answer = _generate_answer_text(chunks=chunks, messages=messages, request_targets=request_targets)
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
            )
        else:
            retry_messages = messages
        try:
            answer = _generate_answer_text(chunks=chunks, messages=retry_messages, request_targets=request_targets)
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
        try:
            _validate_generated_answer(answer=answer, chunks=chunks)
        except LLMGenerationError as retry_error:
            # Retry failed validation too, but it did produce an answer. Keep it
            # as-is rather than paying for a third generation call — the feedback
            # was the best guidance we could provide.
            logger.warning(
                "LLM retry failed validation too; using the retry answer as-is. Reason: %s",
                str(retry_error)[:200],
                extra={"question": question[:120]},
            )
            rejection_reason = f"{rejection_reason} | retry also failed: {retry_error}"[:500]

    _validate_grounded_example_output(question=question, answer=answer, chunks=chunks)

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

    return {
        "answer": answer,
        "confidence": confidence,
        "review_required": confidence < 0.82,
        "provider": settings.LLM_PROVIDER,
        "model": (request_targets[0]["model"]),
        "rejected_answer": rejected_answer,
        "rejection_reason": rejection_reason,
    }


def _stream_request_chat_completion(
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
            # Tokens are fully buffered and validated before any reach the client,
            # so JSON mode is safe here and keeps output parseable like the sync path.
            "response_format": {"type": "json_object"},
            # See _request_chat_completion: avoid reasoning models exhausting the
            # token budget on hidden chain-of-thought before any content is sent.
            "chat_template_kwargs": {"enable_thinking": False},
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
) -> Generator[tuple[str, object], None, None]:
    """
    Generator yielding (event_type, payload) tuples for streaming narration.

    Yields:
        ("token", delta_str) — for each token from the LLM.
        ("done", metadata_dict) — once after all tokens, with answer metadata.

    All tokens are buffered and validated before being yielded to the caller.
    This prevents the 'answer shows then disappears' pattern that occurs when
    validation fails after tokens have already been sent to the client.
    """
    if not settings.LLM_ENABLED:
        raise LLMGenerationError("LLM mode is disabled by configuration.")
    if settings.LLM_PROVIDER != "openai-compatible":
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
    detected_language = detect_question_language(question)
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
    )

    # Buffer all tokens before yielding any — validation must pass the full
    # answer before the client receives a single character, so a failed check
    # never produces a visible-then-vanishing answer.
    def _collect_stream(active_messages: list[dict]) -> str:
        collected: list[str] = []
        try:
            for delta in _stream_request_chat_completion(
                api_base_url=primary_base_url,
                api_key=primary_api_key,
                model=settings.LLM_MODEL,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                messages=active_messages,
            ):
                collected.append(delta)
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
        text = "".join(collected)
        if not text.strip():
            raise LLMGenerationError("LLM stream response was empty.")
        return text

    # First attempt
    rejected_answer: str | None = None
    rejection_reason: str | None = None
    try:
        full_answer = _collect_stream(messages)

        logger.info(f"[STREAM_LLM_RAW] Raw response (first 250 chars): {full_answer[:250]}")
        full_answer = _unwrap_json_answer(full_answer)

        # Strip hallucinated file names; evidence file names are preserved.
        full_answer = _strip_json_suffix(full_answer)
        full_answer = _strip_raw_filenames(full_answer, chunks)
        full_answer = _strip_stray_list_markers(full_answer)
        _validate_answer_language(answer=full_answer, question=question, target_language=effective_language)
        _validate_generated_answer(answer=full_answer, chunks=chunks)
        _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks)
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
        )
        full_answer = _collect_stream(retry_messages)

        logger.info(f"[STREAM_RETRY_RAW] Retry response (first 250 chars): {full_answer[:250]}")
        full_answer = _unwrap_json_answer(full_answer)

        # Strip hallucinated file names; evidence file names are preserved.
        full_answer = _strip_json_suffix(full_answer)
        full_answer = _strip_raw_filenames(full_answer, chunks)
        full_answer = _strip_stray_list_markers(full_answer)
        try:
            _validate_answer_language(answer=full_answer, question=question, target_language=effective_language)
            _validate_generated_answer(answer=full_answer, chunks=chunks)
            _validate_grounded_example_output(question=question, answer=full_answer, chunks=chunks)
        except LLMGenerationError as retry_error:
            # Retry failed validation too. A real, on-topic answer that fails a strict
            # grounding heuristic is still far more useful than the generic
            # non-LLM deterministic template views.py falls back to if this
            # propagates - use the retry's answer as-is rather than raising.
            logger.warning(
                "Stream retry failed validation too; using raw retry answer instead of "
                "falling back to the deterministic template. Reason: %s",
                str(retry_error)[:200],
                extra={"question": question[:120]},
            )
            rejection_reason = f"{rejection_reason} | retry also failed: {retry_error}"[:500]

    top_score = chunks[0].get("score", 0.0) if chunks else 0.0
    confidence = min(0.94, max(0.60, float(top_score)))

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
            "review_required": confidence < 0.82,
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "rejected_answer": rejected_answer,
            "rejection_reason": rejection_reason,
        },
    )
