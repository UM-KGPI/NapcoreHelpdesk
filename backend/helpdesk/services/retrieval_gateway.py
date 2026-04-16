from __future__ import annotations

import re
import time
from uuid import uuid4
from django.db import connection, models
from django.conf import settings

try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
except Exception:  # pragma: no cover - only unavailable in non-postgres-only environments
    SearchQuery = None
    SearchRank = None
    SearchVector = None

from helpdesk.models import SourceChunk
from helpdesk.db_fields import HAS_NATIVE_PGVECTOR
from helpdesk.services.embeddings import build_text_embedding, cosine_similarity, normalize_text_tokens
from helpdesk.services.graphdb_client import query_graphdb_concept_expansion
from helpdesk.services.neo4j_importer import query_neo4j_concept_expansion
from helpdesk.services.semantic_graph import (
    GRAPH_CONCEPT_ALIASES,
    expand_graph_concepts,
    extract_graph_concepts,
    get_concept_canonical_terms,
    get_concept_example_paths,
)

try:
    from pgvector.django import CosineDistance  # type: ignore
except Exception:  # pragma: no cover - optional dependency in SQLite-only environments
    CosineDistance = None


DEFAULT_CHUNKS = [
    {
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
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
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
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
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-003",
        "label": "OJP context",
        "text": "OJP provides profile-based operational and planning data exchange flows.",
        "standards_scope": ["OJP"],
        "quality_score": 0.78,
        "doc_type": "readme",
        "embedding_vector": build_text_embedding(
            "OJP provides profile-based operational and planning data exchange flows."
        ),
    },
    {
        "repository_url": "https://github.com/NeTEx-CEN/NeTEx",
        "commit_sha": "placeholder",
        "source_path": "README.md",
        "chunk_id": "rag-c-004",
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
            or any(ch.isupper() for ch in token[1:])
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
            adjustment -= 0.08

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


def _diversified_top_k(candidates: list[dict], top_k: int) -> list[dict]:
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
    mmr_lambda = 0.92

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


def _question_doc_type_hints(question: str) -> set[str]:
    lower_question = question.lower()
    hinted: set[str] = set()
    for doc_type, markers in DOC_TYPE_HINTS.items():
        if any(marker in lower_question for marker in markers):
            hinted.add(doc_type)
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
    "OJP": {"ojp"},
    "OpRa": {"opra"},
    "DATEX II": {"datex", "datexii", "datex2"},
}


def _graph_score_adjustment(
    graph_enabled: bool,
    question_concepts: set[str],
    expanded_concepts: set[str],
    concept_example_paths: set[str],
    chunk_text: str,
    source_path: str,
    label: str,
    heading: str,
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
    has_example_path_match = bool(
        lowered_path
        and any(lowered_path.endswith(path.lower()) for path in concept_example_paths)
    )

    direct_overlap = chunk_concepts.intersection(question_concepts)
    if direct_overlap:
        return 0.20, True, direct_overlap

    expanded_overlap = chunk_concepts.intersection(expanded_concepts)
    if expanded_overlap:
        bonus = 0.0
        if lowered_path.startswith("examples/"):
            # Generic preference for concept-relevant example artifacts.
            bonus += 0.08
        if has_example_path_match:
            bonus += 0.05
        return 0.10 + bonus, True, expanded_overlap

    return 0.0, False, set()


def _graph_concept_candidates(
    expanded_concepts: set[str],
    top_k: int,
    scope: list[str] | None = None,
):
    """Return DB chunks whose text mentions any alias of the expanded concept set.

    Builds an OR filter across all aliases for each concept ID present in
    *expanded_concepts*, capped at ``max(10, top_k * 2)`` results.
    Restricts candidates to schema/example chunks to avoid broad markdown
    keyword hits dominating graph-mode reranking.
    Returns an empty queryset when *expanded_concepts* is empty.
    """

    if not expanded_concepts:
        return SourceChunk.objects.none()

    alias_filter = models.Q()
    for concept_id in expanded_concepts:
        for alias in GRAPH_CONCEPT_ALIASES.get(concept_id, set()):
            alias_filter |= models.Q(text__icontains=alias)
            alias_filter |= models.Q(source_path__icontains=alias)
            alias_filter |= models.Q(label__icontains=alias)
            alias_filter |= models.Q(heading__icontains=alias)

    if not alias_filter:
        return SourceChunk.objects.none()

    return (
        SourceChunk.objects.filter(_scope_query_filter(scope))
        .filter(doc_type__in=["schema", "example"])
        .filter(alias_filter)[: max(10, top_k * 2)]
    )


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

    _ensure_seed_chunks()

    hinted_standards = _question_standard_hints(question)
    hinted_doc_types = _question_doc_type_hints(question)

    # Concept extraction happens BEFORE embedding so canonical domain terms
    # are present in the query vector and align with indexed document vocabulary.
    question_concepts = extract_graph_concepts(question) if graph_rag_enabled else set()
    graph_expansion_source = "none"
    if graph_rag_enabled and question_concepts:
        graphdb_enabled = getattr(settings, "GRAPHDB_ENABLED", False)
        neo4j_experimental_enabled = getattr(settings, "NEO4J_EXPERIMENTAL_ENABLED", False)

        if graphdb_enabled:
            try:
                expanded_concepts = query_graphdb_concept_expansion(
                    concept_ids=question_concepts,
                    hops=1,
                    endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
                    repository=settings.GRAPHDB_REPOSITORY,
                    username=getattr(settings, "GRAPHDB_USER", ""),
                    password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                    timeout_seconds=settings.GRAPHDB_TIMEOUT_SECONDS,
                )
                graph_expansion_source = "graphdb"
            except Exception:
                expanded_concepts = expand_graph_concepts(question_concepts, hops=1)
                graph_expansion_source = "memory_fallback"
        elif neo4j_experimental_enabled and getattr(settings, "NEO4J_ENABLED", False):
            try:
                expanded_concepts = query_neo4j_concept_expansion(
                    concept_ids=question_concepts,
                    hops=1,
                    uri=settings.NEO4J_URI,
                    username=settings.NEO4J_USER,
                    password=settings.NEO4J_PASSWORD,
                    database=settings.NEO4J_DATABASE,
                )
                graph_expansion_source = "neo4j_experimental"
            except Exception:
                expanded_concepts = expand_graph_concepts(question_concepts, hops=1)
                graph_expansion_source = "memory_fallback"
        else:
            expanded_concepts = expand_graph_concepts(question_concepts, hops=1)
            graph_expansion_source = "memory"
        graph_expansion_hops = 1
    else:
        expanded_concepts = set()
        graph_expansion_hops = 0

    concept_example_paths = get_concept_example_paths(expanded_concepts) if expanded_concepts else set()

    canonical_concept_terms = get_concept_canonical_terms(expanded_concepts) if expanded_concepts else []
    query_embedding = build_text_embedding(
        _build_query_embedding_input(
            question=question,
            hinted_standards=hinted_standards,
            hinted_doc_types=hinted_doc_types,
            expanded_concept_terms=canonical_concept_terms if canonical_concept_terms else None,
        )
    )

    postgres_candidates = _postgres_hybrid_candidates(
        question=question,
        query_embedding=query_embedding,
        top_k=top_k,
        scope=scope,
    )
    if postgres_candidates is None:
        postgres_candidates = _postgres_fts_candidates(question=question, top_k=top_k, scope=scope)

    if postgres_candidates is not None:
        chunk_iterable = list(postgres_candidates)
        existing_ids = {chunk.id for chunk in chunk_iterable}
        for hinted_chunk in _path_hint_candidates(question=question, top_k=top_k, scope=scope):
            if hinted_chunk.id not in existing_ids:
                chunk_iterable.append(hinted_chunk)
    else:
        chunk_iterable = list(SourceChunk.objects.all())
        existing_ids = {chunk.id for chunk in chunk_iterable}

    graph_candidates_added = 0
    if graph_rag_enabled and expanded_concepts:
        if not isinstance(chunk_iterable, list):
            chunk_iterable = list(chunk_iterable)
            existing_ids = {chunk.id for chunk in chunk_iterable}
        for graph_chunk in _graph_concept_candidates(
            expanded_concepts=expanded_concepts, top_k=top_k, scope=scope
        ):
            if graph_chunk.id not in existing_ids:
                chunk_iterable.append(graph_chunk)
                existing_ids.add(graph_chunk.id)
                graph_candidates_added += 1

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
            concept_example_paths=concept_example_paths,
            chunk_text=chunk.text,
            source_path=chunk.source_path,
            label=chunk.label,
            heading=getattr(chunk, "heading", "") or "",
        )
        raw_score += graph_adjustment

        # Keyword-trap penalty: high lexical match but semantically divergent from query.
        # When a chunk matches surface terms well (lexical > 0.5) but the query embedding
        # cosine similarity is low (vector < 0.35), we treat it as a false positive and
        # discount its rank.  The published `score` is unchanged (for audit), only the
        # internal rank_score used for selection is reduced.
        keyword_trap = lexical_score > 0.5 and vector_score < 0.35

        score = min(1.0, max(0.0, raw_score))
        if score < min_score:
            continue

        # Break ties deterministically; keyword-trap chunks rank below genuine matches.
        rank_score = raw_score + (lexical_score * 0.01) + (vector_score * 0.005)
        if keyword_trap:
            rank_score *= 0.6

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
                "retrievalEventId": f"re-{uuid4().hex[:8]}",
                "_graphContribution": graph_adjustment,
                "_graphHit": graph_hit,
                "_graphProvenanceConceptIds": sorted(matching_concepts),
            }
        )

    candidates.sort(key=lambda value: (value["_rankScore"], value["score"]), reverse=True)
    trimmed = _diversified_top_k(candidates=candidates, top_k=top_k)
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

    trace = {
        "graphRagVariant": "control" if not graph_rag_enabled else "graph-rag",
        "graphExpansionHops": graph_expansion_hops,
        "graphExpansionSource": graph_expansion_source,
        "graphConceptIds": sorted(expanded_concepts) if graph_rag_enabled else [],
        "graphCandidatesAdded": graph_candidates_added if graph_rag_enabled else 0,
        "graphEvidenceCount": graph_hits if graph_rag_enabled else 0,
        "graphScoreContribution": round(graph_total / len(trimmed), 4) if graph_rag_enabled and trimmed else 0.0,
        "graphProvenanceChainCount": len(provenance_chains) if graph_rag_enabled else 0,
        "repositoryCoverageCount": repository_coverage_count,
        "conceptCoverageCount": len(graph_concepts_in_trimmed),
        "semanticAlignmentScore": round(sum(vector_scores_trimmed) / len(vector_scores_trimmed), 4) if vector_scores_trimmed else 0.0,
        "retrievalLatencyMs": round((time.time() - retrieval_start_time) * 1000, 1),
    }
    return trimmed, trace
