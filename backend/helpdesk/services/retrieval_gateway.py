"""
Vector similarity search gateway over indexed source chunks.

Executes pgvector cosine similarity queries against SourceChunk records,
applies standards scope and quality score filters, and returns ranked
chunks with retrieval trace metadata for evidence attribution.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from __future__ import annotations

import logging
import re
import time
from uuid import uuid4
from django.db import connection, models
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
except Exception:  # pragma: no cover - unavailable when postgres search extras are missing
    SearchQuery = None
    SearchRank = None
    SearchVector = None

from helpdesk.models import SourceChunk
from helpdesk.db_fields import HAS_NATIVE_PGVECTOR
from helpdesk.services.embeddings import build_text_embedding, cosine_similarity, normalize_text_tokens
from helpdesk.services.example_retrieval import (
    format_examples_as_chunks,
    retrieve_concept_examples_with_fallback,
)
from helpdesk.services.graphdb_client import (
    build_graph_scope_for_standards,
    query_graphdb_concept_expansion,
)
from helpdesk.services.semantic_graph import (
    GRAPH_CONCEPT_ALIASES,
    expand_graph_concepts,
    extract_graph_concepts,
    get_concept_canonical_terms,
)

try:
    from pgvector.django import CosineDistance  # type: ignore
except Exception:  # pragma: no cover - optional dependency when pgvector package is missing
    CosineDistance = None


DEFAULT_CHUNKS = [
    {
        "repository_url": settings.SEED_REPO_NETEX,
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-001",
        "label": "NeTEx profile overview",
        "text": "NeTEx profiles define interoperable structures for timetable and stop data.",
        "standards_scope": ["NeTEx", "Transmodel"],
        "quality_score": 0.84,
        "doc_type": "readme",
        "embedding_vector": build_text_embedding(
            "NeTEx profiles define interoperable structures for timetable and stop data."
        ),
    },
    {
        "repository_url": settings.SEED_REPO_SIRI,
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-002",
        "label": "SIRI context",
        "text": "SIRI supports real-time information exchange in public transport systems.",
        "standards_scope": ["SIRI"],
        "quality_score": 0.79,
        "doc_type": "readme",
        "embedding_vector": build_text_embedding(
            "SIRI supports real-time information exchange in public transport systems."
        ),
    },
    {
        "repository_url": settings.SEED_REPO_OPRA,
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-003",
        "label": "OpRa context",
        "text": "OpRa defines operational and performance metrics exchange profiles for transport networks.",
        "standards_scope": ["OpRa"],
        "quality_score": 0.78,
        "doc_type": "readme",
        "embedding_vector": build_text_embedding(
            "OpRa defines operational and performance metrics exchange profiles for transport networks."
        ),
    },
]


def _ensure_seed_chunks() -> None:
    if SourceChunk.objects.exists():
        return

    for chunk in DEFAULT_CHUNKS:
        SourceChunk.objects.get_or_create(
            chunk_id=chunk["chunk_id"],
            defaults=chunk,
        )


def _token_overlap_score(question: str, chunk_text: str) -> float:
    question_tokens = set(normalize_text_tokens(question))
    if not question_tokens:
        return 0.0
    chunk_tokens = set(normalize_text_tokens(chunk_text))
    overlap = question_tokens.intersection(chunk_tokens)
    return len(overlap) / len(question_tokens)


def _scope_query_filter(scope: list[str] | None):
    """Build JSON scope filter compatible with PostgreSQL JSON array fields."""

    if not scope:
        return models.Q()

    scoped_filter = models.Q()
    for standard in scope:
        scoped_filter |= models.Q(standards_scope__contains=[standard])
    return scoped_filter


def _search_vector():
    """Search across text and source metadata to support filename/path lookups."""

    return (
        SearchVector("text", config="english", weight="A")
        + SearchVector("source_path", config="english", weight="A")
        + SearchVector("label", config="english", weight="B")
        + SearchVector("heading", config="english", weight="B")
    )


PATH_HINT_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{7,}")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _question_path_hints(question: str) -> set[str]:
    """Extract likely filename/path identifiers from user text."""

    hints: set[str] = set()
    for token in PATH_HINT_PATTERN.findall(question):
        normalized = token.strip().strip(".,:;!?()[]{}\"'").lower()
        if not normalized:
            continue
        if (
            normalized.endswith((".xml", ".xsd", ".md"))
            or "_" in normalized
            or "-" in normalized
            or "/" in normalized
            or any(ch.isdigit() for ch in normalized)
        ):
            hints.add(normalized)
    return hints


def _path_hint_candidates(question: str, top_k: int, scope: list[str] | None = None):
    """Return path-matching candidates for explicit filename/example-name queries."""

    hints = _question_path_hints(question)
    if not hints:
        return SourceChunk.objects.none()

    path_filter = models.Q()
    for hint in hints:
        path_filter |= models.Q(source_path__icontains=hint)

    # Standard path hint limit
    return SourceChunk.objects.filter(_scope_query_filter(scope)).filter(path_filter)[: max(15, top_k * 3)]


def _path_score_adjustment(question: str, source_path: str) -> float:
    """Boost chunks when query includes explicit filename/path-like hints."""

    lower_path = (source_path or "").lower()
    bonus = 0.0
    for hint in _question_path_hints(question):
        if hint in lower_path:
            bonus = max(bonus, 0.20 if len(hint) >= 16 else 0.12)

    if "example" in question.lower() and "/examples/" in f"/{lower_path}":
        bonus += 0.04

    return min(0.24, bonus)


def _source_path_intent_adjustment(hinted_doc_types: set[str], source_path: str) -> float:
    """Apply intent-aware path nudges for stable ranking on tied candidates."""

    if not hinted_doc_types:
        return 0.0

    lower_path = (source_path or "").lower().lstrip("/")
    adjustment = 0.0

    if "example" in hinted_doc_types:
        if lower_path.startswith("examples/"):
            adjustment += 0.12
        if lower_path.startswith("issues/"):
            adjustment -= 0.25
        if lower_path.endswith(".xsd"):
            # Hard penalty: quality-score-heavy XSD chunks (quality_score ~0.97
            # → legacy_score ~0.78) survived the 0.62 min_score threshold with
            # only -0.08 here.  -0.20 pushes them to ~0.52 → filtered out.
            adjustment -= 0.20

    return adjustment


def _postgres_fts_candidates(question: str, top_k: int, scope: list[str] | None = None):
    """Return FTS-ranked candidate queryset when PostgreSQL search is available."""

    if connection.vendor != "postgresql" or not all([SearchQuery, SearchRank, SearchVector]):
        return None

    search_query = SearchQuery(question)
    filtered = SourceChunk.objects.filter(_scope_query_filter(scope))
    return (
        filtered.annotate(
            lexical_rank=SearchRank(_search_vector(), search_query)
        )
        .filter(lexical_rank__gt=0.0)
        .order_by("-lexical_rank")[: max(20, top_k * 4)]
    )


def _postgres_hybrid_candidates(
    question: str,
    query_embedding: list[float],
    top_k: int,
    scope: list[str] | None = None,
):
    """Return combined vector+lexical ranked candidates on PostgreSQL with pgvector."""

    if not (
        connection.vendor == "postgresql"
        and HAS_NATIVE_PGVECTOR
        and CosineDistance is not None
        and all([SearchQuery, SearchRank, SearchVector])
    ):
        return None

    search_query = SearchQuery(question)
    filtered = SourceChunk.objects.filter(_scope_query_filter(scope))
    # Cosine distance is lower-is-better; convert to similarity with (1 - distance).
    return (
        filtered.annotate(
            lexical_rank=SearchRank(_search_vector(), search_query),
            vector_distance=CosineDistance("embedding_vector", query_embedding),
        )
        .annotate(vector_similarity=1.0 - models.F("vector_distance"))
        .only(
            "id",
            "text",
            "repository_url",
            "commit_sha",
            "source_path",
            "chunk_id",
            "label",
            "heading",
            "standards_scope",
            "chunk_type",
            "doc_type",
            "structured_metadata",
            "quality_score",
        )
        .order_by("-vector_similarity", "-lexical_rank")[: max(25, top_k * 5)]
    )


def _scope_matches(chunk_scope: list[str], requested_scope: list[str] | None) -> bool:
    if not requested_scope:
        return True
    return bool(set(chunk_scope).intersection(set(requested_scope)))


def _normalize_tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


def _is_delay_exchange_intent(question: str) -> bool:
    question_lower = question.lower()
    has_delay = any(marker in question_lower for marker in ["delay", "delayed", "late", "cancel"])
    has_journey = "journey" in question_lower
    has_exchange = any(marker in question_lower for marker in ["exchange", "exchanging", "share"])
    return has_delay and has_journey and has_exchange


def _intent_score_adjustment(
    question: str,
    repository_url: str,
    source_path: str,
    label: str,
    chunk_text: str,
) -> float:
    """Apply repository-neutral semantic boosts for known high-value intent patterns."""

    if not _is_delay_exchange_intent(question):
        return 0.0

    del repository_url  # Explicitly keep intent scoring source-neutral.
    lower_path = (source_path or "").lower()
    lower_label = (label or "").lower()
    lower_text = (chunk_text or "").lower()
    semantic_blob = "\n".join([lower_path, lower_label, lower_text])
    bonus = 0.0

    if any(term in semantic_blob for term in ["delayed", "late", "cancelled", "canceled"]):
        bonus += 0.05
    if any(term in semantic_blob for term in ["journey", "vehicle journey", "dated vehicle journey"]):
        bonus += 0.05
    if any(term in semantic_blob for term in ["exchange", "service delivery", "monitoring", "estimated timetable", "situation"]):
        bonus += 0.05
    if "example" in lower_path or lower_path.startswith("examples/"):
        bonus += 0.02

    return min(0.15, bonus)


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = left.intersection(right)
    union = left.union(right)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _diversified_top_k(candidates: list[dict], top_k: int, mmr_lambda: float) -> list[dict]:
    """Greedy MMR-like selection to reduce near-duplicate evidence concentration."""

    if len(candidates) <= top_k:
        return candidates

    for candidate in candidates:
        candidate["_diversityTokens"] = set(
            _normalize_tokens(
                "\n".join(
                    [
                        candidate.get("sourcePath", ""),
                        candidate.get("label", ""),
                        candidate.get("repositoryUrl", ""),
                    ]
                )
            )
        )

    selected: list[dict] = []
    remaining = list(candidates)
    while remaining and len(selected) < top_k:
        best_idx = 0
        best_score = float("-inf")
        for idx, candidate in enumerate(remaining):
            novelty_penalty = 0.0
            if selected:
                novelty_penalty = max(
                    _jaccard_similarity(candidate["_diversityTokens"], chosen["_diversityTokens"])
                    for chosen in selected
                )
            mmr_score = (mmr_lambda * candidate["_rankScore"]) - ((1.0 - mmr_lambda) * novelty_penalty)
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(remaining.pop(best_idx))

    for candidate in selected:
        candidate.pop("_diversityTokens", None)

    return selected


def _cap_expanded_concepts(
    *,
    question_concepts: set[str],
    expanded_concepts: set[str],
    max_concepts: int,
) -> set[str]:
    """Cap expanded graph concepts to reduce query drift and noisy fan-out."""

    if max_concepts <= 0:
        return set()
    if len(expanded_concepts) <= max_concepts:
        return expanded_concepts

    prioritized = sorted(
        expanded_concepts,
        key=lambda concept_id: (concept_id not in question_concepts, concept_id),
    )
    return set(prioritized[:max_concepts])


def _apply_source_path_cap(candidates: list[dict], max_per_source_path: int) -> list[dict]:
    """Limit repeated hits from the same source path before final selection."""

    if max_per_source_path <= 0:
        return candidates

    kept: list[dict] = []
    per_path_count: dict[str, int] = {}
    for candidate in candidates:
        source_path = str(candidate.get("sourcePath", "") or "")
        current_count = per_path_count.get(source_path, 0)
        if source_path and current_count >= max_per_source_path:
            continue
        kept.append(candidate)
        if source_path:
            per_path_count[source_path] = current_count + 1
    return kept


DOC_TYPE_BASE_ADJUSTMENTS = {
    "frame": 0.10,
    "object": 0.09,
    "schema": 0.07,
    "guide": 0.05,
    "example": 0.02,
    "readme": -0.10,
}

DOC_TYPE_HINTS = {
    "frame": {"frame", "frames", "hierarchy"},
    "object": {"object", "objects", "entity", "entities"},
    "schema": {"schema", "xsd", "xml", "element", "elements", "attribute", "attributes"},
    "example": {"example", "examples", "sample", "samples"},
    "readme": {"overview", "introduction"},
    "guide": {"guide", "guidance", "tutorial", "how", "howto"},
}


_DEFINITIONAL_QUESTION_RE = re.compile(
    r"\b(what\s+is|what\s+are|define|definition\s+of|what\s+does|explain|describe|meaning\s+of)\b"
)


def _question_doc_type_hints(question: str) -> set[str]:
    lower_question = question.lower()
    hinted: set[str] = set()
    for doc_type, markers in DOC_TYPE_HINTS.items():
        if any(marker in lower_question for marker in markers):
            hinted.add(doc_type)

    # "example XML" usually asks for an instance/example artifact, not schema/XSD definition.
    asks_example_xml = "example" in lower_question and "xml" in lower_question
    asks_schema_definition = "xsd" in lower_question or "schema" in lower_question
    if asks_example_xml and not asks_schema_definition:
        hinted.add("example")
        hinted.discard("schema")

    # Definitional questions ("what is X", "define X") prefer schema chunks that carry
    # formal concept definitions, not example instances.
    if _DEFINITIONAL_QUESTION_RE.search(lower_question) and "example" not in hinted:
        hinted.add("schema")

    return hinted


def _doc_type_score_adjustment(hinted_doc_types: set[str], doc_type: str) -> float:
    adjustment = DOC_TYPE_BASE_ADJUSTMENTS.get(doc_type, 0.0)
    if hinted_doc_types:
        if doc_type in hinted_doc_types:
            adjustment += 0.08
        elif doc_type == "readme":
            adjustment -= 0.05
        elif "example" in hinted_doc_types and doc_type in {"schema", "frame", "object"}:
            # When users explicitly ask for examples, avoid schema-heavy dominance.
            adjustment -= 0.10
        elif doc_type not in hinted_doc_types:
            adjustment -= 0.03
    return adjustment


def _build_query_embedding_input(
    question: str,
    hinted_standards: set[str],
    hinted_doc_types: set[str],
    expanded_concept_terms: list[str] | None = None,
) -> str:
    standards = ", ".join(sorted(hinted_standards)) if hinted_standards else "unspecified"
    doc_types = ", ".join(sorted(hinted_doc_types)) if hinted_doc_types else "unspecified"
    concept_line = (
        f"query_concepts: {', '.join(expanded_concept_terms)}\n"
        if expanded_concept_terms
        else ""
    )
    return (
        f"query_scope: {standards}\n"
        f"query_doc_types: {doc_types}\n"
        f"{concept_line}"
        f"question: {question}"
    )


def _build_chunk_embedding_input(chunk: SourceChunk) -> str:
    standards_scope = chunk.standards_scope or []
    scope = ", ".join(standards_scope) if standards_scope else "unspecified"
    return (
        f"doc_type: {getattr(chunk, 'doc_type', 'guide') or 'guide'}\n"
        f"chunk_type: {getattr(chunk, 'chunk_type', 'prose') or 'prose'}\n"
        f"scope: {scope}\n"
        f"repository: {chunk.repository_url}\n"
        f"source_path: {chunk.source_path}\n"
        f"heading: {getattr(chunk, 'heading', '') or 'none'}\n\n"
        f"content:\n{chunk.text}"
    )


STANDARD_HINTS = {
    "NeTEx": {"netex"},
    "SIRI": {"siri"},
    "Transmodel": {"transmodel"},
    "OpRa": {"opra"},
}

_STANDARD_SCOPE_ALIASES = {
    "netex": "netex",
    "siri": "siri",
    "opra": "opra",
}

# Namespace-root and structural predicate concepts that are so broad they appear in virtually
# every document and should not trigger the graph score boost on their own.
_GENERIC_GRAPH_CONCEPTS: frozenset[str] = frozenset({
    "netex:NeTEx",
    "siri:SIRI",
    "transmodel:when",
    "transmodel:usedIn",
    "transmodel:NeTEx",
})


def _is_normative_constraint_question(question: str) -> bool:
    lower_question = (question or "").lower()
    return bool(
        re.search(
            r"\b(mandatory|optional|required|must|shall|minoccurs|maxoccurs|cardinality)\b",
            lower_question,
        )
    )


def _is_mapping_relationship_question(question: str) -> bool:
    """Detect questions about cross-standard relationships, alignments, or comparisons."""
    lower_question = (question or "").lower()
    return bool(
        re.search(
            r"\b(difference|relationship|compare|comparison|mapping|aligned|alignment|correspond|equivalent|same\s+as|relates?\s+to|between|cross-standard)\b",
            lower_question,
        )
    )


def _is_abstention_question(question: str) -> bool:
    """Detect questions likely to benefit from abstention (out-of-scope, weak evidence)."""
    lower_question = (question or "").lower()
    return bool(
        re.search(
            r"\b(unsupported|not\s+supported|out\s+of\s+scope|beyond\s+scope|not\s+applicable|undefined|unspecified|unknown|ambiguous|unclear)\b",
            lower_question,
        )
    )


def _is_explanation_question(question: str) -> bool:
    """Detect questions seeking detailed explanation or background."""
    lower_question = (question or "").lower()
    return bool(
        re.search(
            r"\b(explain|what\s+is|define|definition|background|overview|concept|understand|how\s+does|semantics?|meaning)\b",
            lower_question,
        )
    )


def _is_example_driven_question(question: str) -> bool:
    """Detect questions requesting examples, use cases, or illustrations.

    Also includes definition/explanation questions about schema concepts,
    as examples provide concrete evidence for what things ARE.
    """
    lower_question = (question or "").lower()

    # Explicit example-seeking keywords
    if re.search(
        r"\b(example|instance|use\s+case|sample|illustration|concrete|demonstrate|show|list|enumerate|snippet|xml|code|pattern|template|model|structure|how\s+to)\b",
        lower_question,
    ):
        return True

    # Definition questions about schema elements should also retrieve examples
    # Examples are powerful for understanding "what is X" for schema concepts
    if re.search(
        r"\b(what\s+is|what\s+are|define|definition|explain|describe|tell\s+me|information\s+about)\b",
        lower_question,
    ):
        return True

    return False


def _active_graphdb_standards(
    *,
    scope: list[str] | None,
    hinted_standards: set[str],
) -> set[str]:
    names: set[str] = set()

    for standard in hinted_standards:
        alias = _STANDARD_SCOPE_ALIASES.get((standard or "").strip().lower())
        if alias:
            names.add(alias)

    for standard in scope or []:
        alias = _STANDARD_SCOPE_ALIASES.get((standard or "").strip().lower())
        if alias:
            names.add(alias)

    return names


def _graph_score_adjustment(
    graph_enabled: bool,
    question_concepts: set[str],
    expanded_concepts: set[str],
    chunk_text: str,
    source_path: str,
    label: str,
    heading: str,
    hinted_doc_types: set[str] | None = None,
) -> tuple[float, bool, set[str]]:
    """Score adjustment for graph reasoning with provenance tracking.

    Returns:
        (adjustment_score, is_graph_hit, matching_concept_ids)
    """
    if not graph_enabled:
        return 0.0, False, set()

    chunk_concepts = extract_graph_concepts(
        "\n".join([chunk_text, source_path, label, heading])
    )
    if not chunk_concepts:
        return 0.0, False, set()

    lowered_path = (source_path or "").lower().strip()

    # Filter out namespace-root and structural predicate concepts that are too broad to
    # indicate genuine relevance — they appear in virtually every document of the standard.
    specific_chunk_concepts = chunk_concepts - _GENERIC_GRAPH_CONCEPTS
    specific_question_concepts = question_concepts - _GENERIC_GRAPH_CONCEPTS
    specific_expanded_concepts = expanded_concepts - _GENERIC_GRAPH_CONCEPTS

    direct_overlap = specific_chunk_concepts.intersection(specific_question_concepts)
    if direct_overlap:
        bonus = 0.0
        if "example" in (hinted_doc_types or set()) and lowered_path.startswith("examples/"):
            bonus += 0.06
        return 0.20 + bonus, True, direct_overlap

    expanded_overlap = specific_chunk_concepts.intersection(specific_expanded_concepts)
    if expanded_overlap:
        bonus = 0.0
        if lowered_path.startswith("examples/"):
            bonus += 0.08
        return 0.10 + bonus, True, expanded_overlap

    return 0.0, False, set()


def _alias_token_subset_match(alias: str, value: str) -> bool:
    alias_tokens = set(_normalize_tokens(alias))
    if not alias_tokens:
        return False
    value_tokens = set(_normalize_tokens(value))
    return alias_tokens.issubset(value_tokens)


def _graph_alias_match_score(
    alias: str,
    *,
    source_path: str,
    label: str,
    heading: str,
    text: str,
) -> float:
    alias_lower = (alias or "").strip().lower()
    if not alias_lower:
        return 0.0

    alias_token_count = len(_normalize_tokens(alias_lower))
    specificity = min(0.75, (alias_token_count * 0.12) + (min(len(alias_lower), 24) * 0.01))

    normalized_source_path = (source_path or "").lower()
    normalized_label = (label or "").lower()
    normalized_heading = (heading or "").lower()
    normalized_text = (text or "").lower()

    if alias_lower in normalized_source_path or _alias_token_subset_match(alias_lower, source_path):
        return 1.10 + specificity
    if alias_lower in normalized_label or _alias_token_subset_match(alias_lower, label):
        return 0.85 + specificity
    if alias_lower in normalized_heading or _alias_token_subset_match(alias_lower, heading):
        return 0.75 + specificity
    if alias_lower in normalized_text or _alias_token_subset_match(alias_lower, text):
        return 0.40 + specificity
    return 0.0


def _graph_candidate_rank_score(
    chunk: SourceChunk,
    aliases: set[str],
    question: str,
    hinted_doc_types: set[str],
) -> float:
    source_path = chunk.source_path or ""
    label = chunk.label or ""
    heading = getattr(chunk, "heading", "") or ""
    text = chunk.text or ""
    lowered_path = source_path.lower().strip()
    doc_type = (getattr(chunk, "doc_type", "") or "").lower()

    score = max(
        (
            _graph_alias_match_score(
                alias,
                source_path=source_path,
                label=label,
                heading=heading,
                text=text,
            )
            for alias in aliases
        ),
        default=0.0,
    )

    if question:
        score += _token_overlap_score(
            question=question,
            chunk_text="\n".join([source_path, label, heading, text]),
        ) * 0.75

        lower_question = question.lower()
        if "xml" in lower_question:
            if lowered_path.endswith(".xml"):
                score += 0.35
            elif lowered_path.endswith(".xsd"):
                score -= 0.12

        for hint in _question_path_hints(question):
            if hint in lowered_path:
                score += 0.80

    if "example" in hinted_doc_types:
        if doc_type == "example":
            score += 0.60
        elif doc_type == "schema":
            score -= 0.10
    elif "schema" in hinted_doc_types and doc_type == "schema":
        score += 0.20

    if lowered_path.startswith("examples/"):
        score += 0.15

    return score


def _graph_concept_candidates(
    expanded_concepts: set[str],
    top_k: int,
    max_candidates: int | None = None,
    scope: list[str] | None = None,
    question: str = "",
    hinted_doc_types: set[str] | None = None,
):
    """Return DB chunks whose text mentions any alias of the expanded concept set.

    Builds an OR filter across all aliases for each concept ID present in
    *expanded_concepts*, then ranks the raw matches before applying the final
    candidate cap. Restricts candidates to schema/example chunks to avoid broad
    markdown keyword hits dominating graph-mode reranking.
    Returns an empty list when *expanded_concepts* is empty.
    """

    if not expanded_concepts:
        return []

    fast_alias_filter = models.Q()
    text_alias_filter = models.Q()
    candidate_aliases: set[str] = set()
    ranked_aliases: list[tuple[int, int, str]] = []
    question_tokens = {token for token in TOKEN_PATTERN.findall((question or "").lower()) if len(token) >= 3}

    for concept_id in expanded_concepts:
        for alias in GRAPH_CONCEPT_ALIASES.get(concept_id, set()):
            normalized_alias = alias.strip()
            if len(normalized_alias) < 3:
                continue

            alias_tokens = {token for token in TOKEN_PATTERN.findall(normalized_alias.lower()) if len(token) >= 3}
            overlap_score = len(alias_tokens.intersection(question_tokens)) if question_tokens else 0
            specificity_score = min(len(normalized_alias), 120)
            ranked_aliases.append((overlap_score, specificity_score, normalized_alias))

    if not ranked_aliases:
        return []

    ranked_aliases.sort(key=lambda value: (value[0], value[1]), reverse=True)
    alias_cap = max(8, min(40, top_k * 6))

    selected_aliases: list[str] = []
    seen_aliases: set[str] = set()
    for overlap_score, _specificity_score, alias in ranked_aliases:
        dedupe_key = alias.lower()
        if dedupe_key in seen_aliases:
            continue

        # Keep high-overlap aliases first; once the cap is reached, stop.
        selected_aliases.append(alias)
        seen_aliases.add(dedupe_key)
        if len(selected_aliases) >= alias_cap:
            break

    for alias in selected_aliases:
        candidate_aliases.add(alias)
        fast_alias_filter |= models.Q(source_path__icontains=alias)
        fast_alias_filter |= models.Q(label__icontains=alias)
        text_alias_filter |= models.Q(text__icontains=alias)

    if not fast_alias_filter and not text_alias_filter:
        return []

    resolved_max_candidates = max_candidates if max_candidates is not None else max(10, top_k * 2)
    candidate_limit = max(0, resolved_max_candidates)
    if candidate_limit == 0:
        return []

    base_queryset = (
        SourceChunk.objects.filter(_scope_query_filter(scope))
        .filter(doc_type__in=["schema", "example"])
        .only("id", "text", "source_path", "label", "heading", "doc_type", "quality_score")
    )

    # Fast path: rely on source path / label matches first (usually enough for concrete example queries).
    ranked_candidates = []
    seen_chunk_ids: set[int] = set()
    for chunk in base_queryset.filter(fast_alias_filter):
        rank_score = _graph_candidate_rank_score(
            chunk=chunk,
            aliases=candidate_aliases,
            question=question,
            hinted_doc_types=hinted_doc_types or set(),
        )
        ranked_candidates.append((rank_score, float(chunk.quality_score), int(chunk.id), chunk))
        seen_chunk_ids.add(int(chunk.id))

    # Slow fallback: scan chunk text only when fast fields did not provide enough candidates.
    if len(ranked_candidates) < candidate_limit and text_alias_filter:
        remaining = max(0, candidate_limit - len(ranked_candidates))
        # Keep the expensive text scan tightly bounded; path/label hits are preferred.
        fallback_scan_limit = min(max(remaining * 2, candidate_limit), max(12, candidate_limit * 2))
        fallback_queryset = base_queryset.filter(text_alias_filter)
        if seen_chunk_ids:
            fallback_queryset = fallback_queryset.exclude(id__in=seen_chunk_ids)
        for chunk in fallback_queryset.order_by("-quality_score")[:fallback_scan_limit]:
            rank_score = _graph_candidate_rank_score(
                chunk=chunk,
                aliases=candidate_aliases,
                question=question,
                hinted_doc_types=hinted_doc_types or set(),
            )
            ranked_candidates.append((rank_score, float(chunk.quality_score), int(chunk.id), chunk))

    ranked_candidates.sort(key=lambda value: (value[0], value[1], value[2]), reverse=True)
    return [chunk for _rank_score, _quality_score, _chunk_id, chunk in ranked_candidates[:candidate_limit]]


def _question_standard_hints(question: str) -> set[str]:
    """Extract standards explicitly referenced in the user question."""
    lower_question = question.lower()
    hinted: set[str] = set()
    for standard, markers in STANDARD_HINTS.items():
        if any(marker in lower_question for marker in markers):
            hinted.add(standard)
    return hinted


def _standard_score_adjustment(
    hinted_standards: set[str],
    chunk_scope: list[str],
    repository_url: str,
    source_path: str,
) -> float:
    """Prefer chunks aligned with standards mentioned in the question."""
    if not hinted_standards:
        return 0.0

    adjustment = 0.0
    lower_blob = f"{repository_url}\n{source_path}".lower()
    chunk_scope_set = set(chunk_scope or [])

    if chunk_scope_set.intersection(hinted_standards):
        adjustment += 0.12

    for hinted_standard in hinted_standards:
        markers = STANDARD_HINTS.get(hinted_standard, set())
        if any(marker in lower_blob for marker in markers):
            adjustment += 0.08
            break

    if chunk_scope_set and not chunk_scope_set.intersection(hinted_standards):
        adjustment -= 0.06

    return adjustment


def retrieve_chunks(
    question: str,
    top_k: int,
    min_score: float,
    scope: list[str] | None = None,
) -> list[dict]:
    chunks, _trace = retrieve_chunks_with_trace(
        question=question,
        top_k=top_k,
        min_score=min_score,
        scope=scope,
        graph_rag_enabled=False,
    )
    return chunks


def retrieve_chunks_with_trace(
    question: str,
    top_k: int,
    min_score: float,
    scope: list[str] | None = None,
    graph_rag_enabled: bool = False,
) -> tuple[list[dict], dict]:
    """Retrieve chunks using hybrid vector and lexical ranking.

    Ranking weights:
    - 50% vector similarity
    - 30% lexical relevance
    - 20% indexed quality score
    """
    retrieval_start_time = time.time()
    retrieval_start_perf = time.perf_counter()
    stage_timing_ms: dict[str, float] = {}

    def _record_stage(stage_key: str, stage_start: float) -> None:
        elapsed_ms = (time.perf_counter() - stage_start) * 1000
        stage_timing_ms[stage_key] = round(stage_timing_ms.get(stage_key, 0.0) + elapsed_ms, 1)

    stage_start = time.perf_counter()
    _ensure_seed_chunks()
    _record_stage("seedChunkEnsureMs", stage_start)

    graph_expansion_max_concepts = max(1, int(getattr(settings, "GRAPH_EXPANSION_MAX_CONCEPTS", 64)))
    graph_expansion_max_candidates = max(1, int(getattr(settings, "GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS", 40)))
    retrieval_scoring_candidate_cap = max(12, int(getattr(settings, "RETRIEVAL_SCORING_CANDIDATE_CAP", 40)))
    graph_preselect_multiplier = max(1, int(getattr(settings, "RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER", 2)))
    source_path_cap = max(1, int(getattr(settings, "RETRIEVAL_MAX_SAME_SOURCE_PATH", 2)))
    mmr_lambda = float(getattr(settings, "RETRIEVAL_MMR_LAMBDA", 0.92))
    mmr_lambda = max(0.0, min(1.0, mmr_lambda))
    retrieval_diversity_enabled = bool(getattr(settings, "RETRIEVAL_DIVERSITY_ENABLED", True))
    keyword_trap_penalty = float(getattr(settings, "RETRIEVAL_KEYWORD_TRAP_PENALTY", 0.6))
    keyword_trap_penalty = max(0.0, min(1.0, keyword_trap_penalty))

    hinted_standards = _question_standard_hints(question)
    hinted_doc_types = _question_doc_type_hints(question)

    asks_example_xml = "example" in hinted_doc_types and "xml" in question.lower() and "xsd" not in question.lower()
    if graph_rag_enabled and asks_example_xml:
        # Reduce semantic fan-out for concrete example requests to avoid schema-heavy drift.
        graph_expansion_max_concepts = min(graph_expansion_max_concepts, 16)
        graph_expansion_max_candidates = min(graph_expansion_max_candidates, max(12, top_k * 2))

    # Apply intent-aware constraints to reduce graph candidate fan-out based on query semantics.
    # These constraints target the observed dominant bottlenecks: graphCandidateQueryMs and candidateScoringMs.
    if graph_rag_enabled:
        if _is_mapping_relationship_question(question):
            # Reduce fan-out for cross-standard mapping/relationship queries
            graph_expansion_max_candidates = min(graph_expansion_max_candidates, max(8, top_k))
        elif _is_abstention_question(question):
            # Reduce fan-out for out-of-scope/weak-evidence queries
            graph_expansion_max_candidates = min(graph_expansion_max_candidates, max(6, int(top_k * 0.8)))
        elif _is_explanation_question(question):
            # Slightly reduce fan-out for detailed explanation queries
            graph_expansion_max_candidates = min(graph_expansion_max_candidates, max(10, top_k + 2))
        elif _is_example_driven_question(question):
            # Reduce fan-out for concrete example/use-case queries
            graph_expansion_max_candidates = min(graph_expansion_max_candidates, max(8, top_k))

    # Concept extraction happens BEFORE embedding so canonical domain terms
    # are present in the query vector and align with indexed document vocabulary.
    stage_start = time.perf_counter()
    question_concepts = extract_graph_concepts(question) if graph_rag_enabled else set()
    _record_stage("conceptExtractMs", stage_start)

    graph_expansion_source = "none"
    if graph_rag_enabled and question_concepts:
        stage_start = time.perf_counter()
        graphdb_enabled = getattr(settings, "GRAPHDB_ENABLED", False)

        if graphdb_enabled:
            try:
                active_standards = _active_graphdb_standards(
                    scope=scope,
                    hinted_standards=hinted_standards,
                )
                graph_scope = build_graph_scope_for_standards(
                    active_standards,
                    include_artifact_rules=_is_normative_constraint_question(question),
                )
                expanded_concepts = query_graphdb_concept_expansion(
                    concept_ids=question_concepts,
                    hops=1,
                    endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
                    repository=settings.GRAPHDB_REPOSITORY,
                    username=getattr(settings, "GRAPHDB_USER", ""),
                    password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                    timeout_seconds=settings.GRAPHDB_TIMEOUT_SECONDS,
                    graph_uris=graph_scope or None,
                )
                graph_expansion_source = "graphdb"
            except Exception:
                expanded_concepts = expand_graph_concepts(question_concepts, hops=1)
                graph_expansion_source = "memory_fallback"
        else:
            expanded_concepts = expand_graph_concepts(question_concepts, hops=1)
            graph_expansion_source = "memory"
        expanded_concepts = _cap_expanded_concepts(
            question_concepts=question_concepts,
            expanded_concepts=expanded_concepts,
            max_concepts=graph_expansion_max_concepts,
        )
        _record_stage("graphExpandMs", stage_start)
        graph_expansion_hops = 1
    else:
        expanded_concepts = set()
        graph_expansion_hops = 0
        stage_timing_ms["graphExpandMs"] = 0.0

    # Placeholder for example retrieval (moved after chunk_iterable initialization)
    example_chunks_added = 0

    stage_start = time.perf_counter()
    canonical_concept_terms = get_concept_canonical_terms(expanded_concepts) if expanded_concepts else []
    _record_stage("conceptMetadataMs", stage_start)

    stage_start = time.perf_counter()
    query_embedding = build_text_embedding(
        _build_query_embedding_input(
            question=question,
            hinted_standards=hinted_standards,
            hinted_doc_types=hinted_doc_types,
            expanded_concept_terms=canonical_concept_terms if canonical_concept_terms else None,
        )
    )
    _record_stage("queryEmbeddingMs", stage_start)

    stage_start = time.perf_counter()
    postgres_candidates = _postgres_hybrid_candidates(
        question=question,
        query_embedding=query_embedding,
        top_k=top_k,
        scope=scope,
    )
    if postgres_candidates is None:
        postgres_candidates = _postgres_fts_candidates(question=question, top_k=top_k, scope=scope)
    _record_stage("postgresCandidateQueryMs", stage_start)

    stage_start = time.perf_counter()
    if postgres_candidates is not None:
        chunk_iterable = list(postgres_candidates)
        existing_ids = {chunk.id for chunk in chunk_iterable}
        for hinted_chunk in _path_hint_candidates(question=question, top_k=top_k, scope=scope):
            if hinted_chunk.id not in existing_ids:
                chunk_iterable.append(hinted_chunk)
    else:
        chunk_iterable = list(SourceChunk.objects.all())
        existing_ids = {chunk.id for chunk in chunk_iterable}
    _record_stage("pathHintMergeMs", stage_start)

    # Retrieve XML examples linked to concepts when appropriate (with semantic fallback)
    stage_start = time.perf_counter()
    if graph_rag_enabled and _is_example_driven_question(question) and question_concepts:
        try:
            graphdb_enabled = getattr(settings, "GRAPHDB_ENABLED", False)
            if graphdb_enabled:
                example_files = retrieve_concept_examples_with_fallback(
                    concept_ids=question_concepts,
                    requested_mode=None,
                    endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
                    repository=settings.GRAPHDB_REPOSITORY,
                    timeout_seconds=max(1, settings.GRAPHDB_TIMEOUT_SECONDS - 1),
                    username=getattr(settings, "GRAPHDB_USER", ""),
                    password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                )
                if example_files:
                    example_chunks = format_examples_as_chunks(example_files)
                    example_chunks_added = len(example_chunks)
                    # Add examples to the retrieval results (will be scored like other chunks)
                    if not isinstance(chunk_iterable, list):
                        chunk_iterable = list(chunk_iterable)
                    for example_chunk in example_chunks:
                        chunk_iterable.append(type('ExampleChunk', (), example_chunk)())
        except Exception as e:
            logger.debug(f"Failed to retrieve examples: {e}")
    _record_stage("exampleRetrievalMs", stage_start)

    graph_candidates_added = 0
    graph_candidate_ids: list[int] = []
    stage_start = time.perf_counter()
    # Exclude namespace-root and structural predicate concepts from candidate lookup:
    # their aliases (e.g. "netex", "when") match thousands of documents and flood
    # the candidate pool with irrelevant chunks before specific concepts get a slot.
    specific_expanded_concepts = expanded_concepts - _GENERIC_GRAPH_CONCEPTS
    if graph_rag_enabled and specific_expanded_concepts:
        if not isinstance(chunk_iterable, list):
            chunk_iterable = list(chunk_iterable)
            existing_ids = {chunk.id for chunk in chunk_iterable}
        for graph_chunk in _graph_concept_candidates(
            expanded_concepts=specific_expanded_concepts,
            top_k=top_k,
            max_candidates=graph_expansion_max_candidates,
            scope=scope,
            question=question,
            hinted_doc_types=hinted_doc_types,
        ):
            if graph_chunk.id not in existing_ids:
                chunk_iterable.append(graph_chunk)
                existing_ids.add(graph_chunk.id)
                graph_candidates_added += 1
                graph_candidate_ids.append(int(graph_chunk.id))
    _record_stage("graphCandidateQueryMs", stage_start)

    stage_start = time.perf_counter()
    selected_graph_ids: set[int] = set()
    if len(chunk_iterable) > retrieval_scoring_candidate_cap:
        graph_preselect_limit = min(
            len(graph_candidate_ids),
            max(top_k, top_k * graph_preselect_multiplier),
        )
        selected_graph_ids = set(graph_candidate_ids[:graph_preselect_limit])

        base_candidates = [chunk for chunk in chunk_iterable if int(chunk.id) not in selected_graph_ids]
        base_candidates.sort(
            key=lambda chunk: (
                float(getattr(chunk, "vector_similarity", 0.0) or 0.0),
                float(getattr(chunk, "lexical_rank", 0.0) or 0.0),
                float(getattr(chunk, "quality_score", 0.0) or 0.0),
            ),
            reverse=True,
        )

        base_limit = max(0, retrieval_scoring_candidate_cap - len(selected_graph_ids))
        selected_base_ids = {int(chunk.id) for chunk in base_candidates[:base_limit]}

        chunk_iterable = [
            chunk
            for chunk in chunk_iterable
            if int(chunk.id) in selected_base_ids or int(chunk.id) in selected_graph_ids
        ]
    _record_stage("candidatePreselectMs", stage_start)

    stage_start = time.perf_counter()
    candidates = []
    for chunk in chunk_iterable:
        if not _scope_matches(chunk.standards_scope or [], scope):
            continue


        lexical_score = float(getattr(chunk, "lexical_rank", 0.0))
        if lexical_score <= 0.0:
            # Augment the question with canonical concept terms so the lexical
            # path benefits from the same expanded vocabulary as the embedding.
            expanded_question = (
                question + " " + " ".join(canonical_concept_terms)
                if canonical_concept_terms
                else question
            )
            lexical_score = _token_overlap_score(
                question=expanded_question,
                chunk_text=(
                    f"{chunk.text}\n"
                    f"{chunk.source_path}\n"
                    f"{chunk.label}\n"
                    f"{getattr(chunk, 'heading', '')}"
                ),
            )
        lexical_score = max(0.0, min(1.0, lexical_score))

        vector_similarity = getattr(chunk, "vector_similarity", None)
        if vector_similarity is not None:
            vector_score = max(0.0, min(1.0, float(vector_similarity)))
        else:
            chunk_embedding = chunk.embedding_vector
            if chunk_embedding is None or len(chunk_embedding) == 0:
                chunk_embedding = build_text_embedding(_build_chunk_embedding_input(chunk))
            vector_score = max(0.0, cosine_similarity(query_embedding, chunk_embedding))
        quality_score = max(0.0, min(1.0, chunk.quality_score))
        doc_type = (getattr(chunk, "doc_type", "guide") or "guide").lower()

        hybrid_score = (vector_score * 0.5) + (lexical_score * 0.3) + (quality_score * 0.2)
        # Keep backward-compatible retrieval strength so known covered intents do not regress.
        legacy_score = (quality_score * 0.8) + (lexical_score * 0.2)
        raw_score = (
            max(hybrid_score, legacy_score)
            + _doc_type_score_adjustment(hinted_doc_types=hinted_doc_types, doc_type=doc_type)
            + _path_score_adjustment(question=question, source_path=chunk.source_path)
            + _source_path_intent_adjustment(
                hinted_doc_types=hinted_doc_types,
                source_path=chunk.source_path,
            )
            + _standard_score_adjustment(
                hinted_standards=hinted_standards,
                chunk_scope=chunk.standards_scope or [],
                repository_url=chunk.repository_url,
                source_path=chunk.source_path,
            )
            + _intent_score_adjustment(
                question=question,
                repository_url=chunk.repository_url,
                source_path=chunk.source_path,
                label=chunk.label,
                chunk_text=chunk.text,
            )
        )
        graph_adjustment, graph_hit, matching_concepts = _graph_score_adjustment(
            graph_enabled=graph_rag_enabled,
            question_concepts=question_concepts,
            expanded_concepts=expanded_concepts,
            chunk_text=chunk.text,
            source_path=chunk.source_path,
            label=chunk.label,
            heading=getattr(chunk, "heading", "") or "",
            hinted_doc_types=hinted_doc_types,
        )
        raw_score += graph_adjustment

        # Keyword-trap penalty: high lexical match but semantically divergent from query.
        # When a chunk matches surface terms well (lexical > 0.5) but the query embedding
        # cosine similarity is low (vector < 0.35), we treat it as a false positive and
        # discount its rank.  The published `score` is unchanged (for audit), only the
        # internal rank_score used for selection is reduced.
        # Exception: if graph evidence confirms the chunk is relevant (graph_hit=True),
        # suppress the penalty — the graph provides orthogonal confirmation that the
        # lexical match is genuine rather than spurious.
        keyword_trap = lexical_score > 0.5 and vector_score < 0.35 and not graph_hit

        score = min(1.0, max(0.0, raw_score))
        if score < min_score:
            continue

        # Break ties deterministically; keyword-trap chunks rank below genuine matches.
        rank_score = raw_score + (lexical_score * 0.01) + (vector_score * 0.005)
        if keyword_trap:
            rank_score *= keyword_trap_penalty

        candidates.append(
            {
                "text": chunk.text,
                "score": score,
                "_rankScore": rank_score,
                "_vectorScore": vector_score,
                "repositoryUrl": chunk.repository_url,
                "commitSha": chunk.commit_sha,
                "sourcePath": chunk.source_path,
                "chunkId": chunk.chunk_id,
                "label": chunk.label,
                "standardsScope": chunk.standards_scope or [],
                "chunkType": getattr(chunk, "chunk_type", "") or "",
                "docType": getattr(chunk, "doc_type", "") or "",
                "heading": getattr(chunk, "heading", "") or "",
                "structuredMetadata": getattr(chunk, "structured_metadata", {}) or {},
                "retrievalEventId": f"re-{uuid4().hex[:8]}",
                "_graphContribution": graph_adjustment,
                "_graphHit": graph_hit,
                "_graphProvenanceConceptIds": sorted(matching_concepts),
            }
        )
    _record_stage("candidateScoringMs", stage_start)

    stage_start = time.perf_counter()
    candidates.sort(key=lambda value: (value["_rankScore"], value["score"]), reverse=True)
    candidates = _apply_source_path_cap(candidates=candidates, max_per_source_path=source_path_cap)
    if retrieval_diversity_enabled:
        trimmed = _diversified_top_k(candidates=candidates, top_k=top_k, mmr_lambda=mmr_lambda)
    else:
        trimmed = candidates[:top_k]
    _record_stage("candidateSelectionMs", stage_start)

    stage_start = time.perf_counter()
    graph_hits = 0
    graph_total = 0.0
    provenance_chains: set[str] = set()
    vector_scores_trimmed: list[float] = []
    for candidate in trimmed:
        graph_hits += 1 if candidate.get("_graphHit") else 0
        graph_total += float(candidate.get("_graphContribution") or 0.0)
        for concept_id in candidate.get("_graphProvenanceConceptIds", []):
            provenance_chains.add(concept_id)
        if "_vectorScore" in candidate:
            vector_scores_trimmed.append(float(candidate.pop("_vectorScore")))
        candidate.pop("_rankScore", None)
        candidate.pop("_graphContribution", None)
        candidate.pop("_graphHit", None)
        # Include provenance in final response
        if candidate.get("_graphProvenanceConceptIds"):
            candidate["graphProvenanceConceptIds"] = candidate.pop("_graphProvenanceConceptIds")
        else:
            candidate.pop("_graphProvenanceConceptIds", None)
    _record_stage("trimmedPostprocessMs", stage_start)

    stage_start = time.perf_counter()
    repository_coverage_count = len(
        {
            str(candidate.get("repositoryUrl", "")).strip()
            for candidate in trimmed
            if str(candidate.get("repositoryUrl", "")).strip()
        }
    )
    graph_concepts_in_trimmed: set[str] = set()
    for candidate in trimmed:
        chunk_concepts = extract_graph_concepts(
            "\n".join(
                [
                    str(candidate.get("text", "")),
                    str(candidate.get("sourcePath", "")),
                    str(candidate.get("label", "")),
                ]
            )
        )
        graph_concepts_in_trimmed.update(chunk_concepts)
    _record_stage("coverageMetricsMs", stage_start)

    stage_timing_ms["totalMeasuredMs"] = round((time.perf_counter() - retrieval_start_perf) * 1000, 1)

    trace = {
        "graphRagVariant": "control" if not graph_rag_enabled else "graph-rag",
        "graphExpansionHops": graph_expansion_hops,
        "graphExpansionSource": graph_expansion_source,
        "graphConceptIds": sorted(expanded_concepts) if graph_rag_enabled else [],
        "graphConceptCap": graph_expansion_max_concepts if graph_rag_enabled else 0,
        "graphCandidatesAdded": graph_candidates_added if graph_rag_enabled else 0,
        "graphCandidateCap": graph_expansion_max_candidates if graph_rag_enabled else 0,
        "graphEvidenceCount": graph_hits if graph_rag_enabled else 0,
        "graphScoreContribution": round(graph_total / len(trimmed), 4) if graph_rag_enabled and trimmed else 0.0,
        "graphProvenanceChainCount": len(provenance_chains) if graph_rag_enabled else 0,
        "exampleChunksAdded": example_chunks_added,
        "repositoryCoverageCount": repository_coverage_count,
        "conceptCoverageCount": len(graph_concepts_in_trimmed),
        "semanticAlignmentScore": round(sum(vector_scores_trimmed) / len(vector_scores_trimmed), 4) if vector_scores_trimmed else 0.0,
        "retrievalSourcePathCap": source_path_cap,
        "retrievalScoringCandidateCap": retrieval_scoring_candidate_cap,
        "retrievalGraphPreselectMultiplier": graph_preselect_multiplier,
        "retrievalGraphPreselected": len(selected_graph_ids),
        "retrievalDiversityEnabled": retrieval_diversity_enabled,
        "retrievalMmrLambda": round(mmr_lambda, 4),
        "retrievalLatencyMs": round((time.time() - retrieval_start_time) * 1000, 1),
        "retrievalStageTimingsMs": stage_timing_ms,
    }
    return trimmed, trace
