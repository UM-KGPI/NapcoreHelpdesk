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
from functools import lru_cache
from uuid import uuid4
from django.db import connection, models
from django.conf import settings

logger = logging.getLogger(__name__)


class ChunkDict:
    """Wrapper for dict-based chunks to provide attribute access."""
    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        return self._data.get(name)

    def get(self, key, default=None):
        return self._data.get(key, default)

try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
except Exception:  # pragma: no cover - unavailable when postgres search extras are missing
    SearchQuery = None
    SearchRank = None
    SearchVector = None

from helpdesk.models import SourceChunk
from helpdesk.db_fields import HAS_NATIVE_PGVECTOR
from helpdesk.services.embeddings import (
    build_text_embedding,
    cosine_similarity,
    normalize_text_tokens,
    passage_text,
    semantic_enabled,
)
from helpdesk.services.concept_extractor import extract_concepts, build_enriched_query
from helpdesk.services.xsd_schema_extractor import retrieve_schema_definitions_for_concepts
from helpdesk.services.example_retrieval import (
    format_examples_as_chunks,
    retrieve_concept_examples_with_fallback,
)
from helpdesk.services.ontology_evidence import (
    format_definitions_as_chunks,
    indexed_commit_shas,
    retrieve_concept_definitions,
)
from helpdesk.services.graphdb_client import (
    build_graph_scope_for_standards,
    query_graphdb_concept_expansion_with_distance,
)
from helpdesk.services.relation_paths import (
    format_relation_paths_as_chunks,
    is_relation_question,
    load_relation_graph,
    relation_paths_for_question,
    supporting_subclass_chunks,
)
from helpdesk.services.schema_overlap import format_overlap_chunk, overlap_for_schemas
from helpdesk.services.service_abbreviations import expand_abbreviations, services_in_question
from helpdesk.services.vocabulary_bridge import bridged_question_concepts
from helpdesk.services.property_terms import question_property_concepts
from helpdesk.services.semantic_graph import (
    CONCEPT_TO_TRANSMODEL,
    GRAPH_CONCEPT_ALIASES,
    TRANSMODEL_TO_CONCEPTS,
    concepts_in_scope,
    expand_graph_concepts_with_distance,
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
    },
]


def _ensure_seed_chunks() -> None:
    if SourceChunk.objects.exists():
        return

    # Embedded here, not at import: with semantic embeddings that calls the embedding service.
    for chunk in DEFAULT_CHUNKS:
        SourceChunk.objects.get_or_create(
            chunk_id=chunk["chunk_id"],
            defaults={**chunk, "embedding_vector": build_text_embedding(chunk["text"])},
        )


def _token_overlap_score(question: str, chunk_text: str) -> float:
    question_tokens = set(normalize_text_tokens(question))
    if not question_tokens:
        return 0.0
    chunk_tokens = set(normalize_text_tokens(chunk_text))
    overlap = question_tokens.intersection(chunk_tokens)
    return len(overlap) / len(question_tokens)


# Sources searched only when the question's scope names them: EU legislation (issue #91), the
# mobilityDCAT-AP metadata profile, NAPCORE's own material (napcore.eu), the INSPIRE Transport Networks
# specification and DATEX II would otherwise compete with the standards in every question that names no
# standard.
OPT_IN_SCOPES = ("EU legislation", "mobilityDCAT-AP", "NAPCORE", "INSPIRE", "DATEX II", "TN-ITS")
# A chunk that also belongs to one of these is never opt-in: SIRI's copy of the DATEX II situation schema
# (scope DATEX II and SIRI) stays in the unscoped search, as it was before DATEX II became a source.
CORE_SCOPES = ("NeTEx", "SIRI", "OpRa", "Transmodel")


def _scope_query_filter(scope: list[str] | None):
    """Build JSON scope filter compatible with PostgreSQL JSON array fields."""

    if not scope:
        core = models.Q()
        for standard in CORE_SCOPES:
            core |= models.Q(standards_scope__contains=[standard])
        unscoped = models.Q()
        for opt_in in OPT_IN_SCOPES:
            unscoped &= ~models.Q(standards_scope__contains=[opt_in]) | core
        return unscoped

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
    # A service named by its abbreviation ("SIRI-CA") points at its schema file.
    for service in services_in_question(question):
        hints.discard(service.abbreviation.lower())
        hints.update(path.lower() for path in service.schema_paths)
    return hints


def _question_service_paths(question: str) -> list[set[str]]:
    """Schema paths of each service the question names, one set per service."""
    return [set(service.schema_paths) for service in services_in_question(question) if service.schema_paths]


def _path_hint_candidates(question: str, top_k: int, scope: list[str] | None = None):
    """Return path-matching candidates for explicit filename/example-name queries."""

    hints = _question_path_hints(question)
    if not hints:
        return SourceChunk.objects.none()

    # Each hint gets its own share, so a file with many chunks cannot crowd out
    # the other file a comparison question names.
    per_hint = max(5, max(15, top_k * 3) // len(hints))
    candidates: list = []
    seen: set[int] = set()
    for hint in sorted(hints):
        for chunk in SourceChunk.objects.filter(_scope_query_filter(scope)).filter(source_path__icontains=hint)[:per_hint]:
            if chunk.pk not in seen:
                seen.add(chunk.pk)
                candidates.append(chunk)
    return candidates


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


# The text-search expression of migration 0022_sourcechunk_text_search_index: a filter written exactly like
# the index expression lets PostgreSQL use the GIN index instead of building every chunk's tsvector
# (~3 s per pass over NeTEx).
TEXT_SEARCH_MATCH = "to_tsvector('english'::regconfig, text) @@ to_tsquery('simple'::regconfig, %s)"
# A question term found in at most this many chunks of the scope is rare: it names the topic ("roadwork"),
# where common ones ("siri", "defin") name the standard or the question form. Counting stops one past it.
RARE_TERM_MAX_CHUNKS = 200


def _question_lexemes(question: str) -> list[str]:
    """The question's terms as the English text-search configuration stems them ("roadworks" -> "roadwork")."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT tsvector_to_array(to_tsvector('english'::regconfig, %s))", [question])
        row = cursor.fetchone()
    return [lexeme for lexeme in (row[0] if row else []) if re.fullmatch(r"[a-z0-9]{3,}", lexeme)]


# Standard names are never a question's topic, though a small standard's name is rare in a shared scope
# ("opra" among NeTEx and OpRa chunks).
STANDARD_NAME_LEXEMES = frozenset({"netex", "siri", "opra", "transmodel", "datex", "gtfs", "napcor", "mobilitydcat", "inspir", "tnit"})


def _rare_lexemes(lexemes: list[str], scope: list[str] | None) -> list[str]:
    filtered = SourceChunk.objects.filter(_scope_query_filter(scope))
    rare = []
    for lexeme in lexemes:
        if lexeme in STANDARD_NAME_LEXEMES:
            continue
        matches = filtered.extra(where=[TEXT_SEARCH_MATCH], params=[lexeme])
        if 0 < len(matches.values_list("id", flat=True)[: RARE_TERM_MAX_CHUNKS + 1]) <= RARE_TERM_MAX_CHUNKS:
            rare.append(lexeme)
    return rare


def _is_standard_identity_concept(concept_id: str) -> bool:
    """A concept that stands for a whole standard: "siri:Siri", "opra:Opra"."""
    prefix, _, local = concept_id.partition(":")
    return bool(local) and local.lower() == prefix.lower()


def question_rare_lexemes(question: str, scope: list[str] | None) -> list[str]:
    """The question's rare terms in the scope (see RARE_TERM_MAX_CHUNKS); empty without PostgreSQL."""
    if connection.vendor != "postgresql":
        return []
    return _rare_lexemes(_question_lexemes(question), scope)


def _lexical_recall_candidates(question: str, limit: int, scope: list[str] | None = None, rare: list[str] | None = None) -> list:
    """Chunks that contain the question's rare terms, for the candidate pool when vectors are semantic.

    The hybrid pool is the top rows by vector similarity; the lexical rank only orders them. Semantic
    vectors miss a rare exact term: for "Does SIRI define roadworks?" the DATEX II RoadWorks definitions
    bundled with SIRI never reached the pool, which held only general SIRI chunks (prod 2026-11-05).
    Matching all terms would not help (those chunks do not say "SIRI"), so any rare term counts.
    """
    if limit <= 0 or connection.vendor != "postgresql" or not all([SearchQuery, SearchRank, SearchVector]):
        return []
    if rare is None:
        rare = question_rare_lexemes(question, scope)
    if not rare:
        return []
    query = " | ".join(rare)
    return list(
        SourceChunk.objects.filter(_scope_query_filter(scope))
        .extra(where=[TEXT_SEARCH_MATCH], params=[query])
        .annotate(lexical_rank=SearchRank(_search_vector(), SearchQuery(query, search_type="raw", config="simple")))
        .order_by("-lexical_rank", "id")[:limit]
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
    limit = max(25, top_k * 5)
    filtered = SourceChunk.objects.filter(_scope_query_filter(scope))

    # Rows are ordered by vector similarity first; the lexical rank only breaks ties.
    # Building the text search vector for every chunk took seconds per pass, so first
    # find the similarity of the limit-th row (cheap: no text processing), then rank
    # only rows at or above it. Every row of the full ordering's top `limit` passes
    # that filter, ties included, so the result is the same. Rows without an
    # embedding sort first (NULLs lead a descending order) and are always kept.
    cutoff = list(
        filtered.annotate(vector_distance=CosineDistance("embedding_vector", query_embedding))
        .annotate(vector_similarity=1.0 - models.F("vector_distance"))
        .order_by("-vector_similarity")
        .values_list("vector_similarity", flat=True)[limit - 1 : limit]
    )

    # Cosine distance is lower-is-better; convert to similarity with (1 - distance).
    ranked = filtered.annotate(
        lexical_rank=SearchRank(_search_vector(), search_query),
        vector_distance=CosineDistance("embedding_vector", query_embedding),
    ).annotate(vector_similarity=1.0 - models.F("vector_distance"))
    if cutoff and cutoff[0] is not None:
        ranked = ranked.filter(
            models.Q(vector_similarity__gte=cutoff[0]) | models.Q(embedding_vector__isnull=True)
        )
    return (
        ranked.only(
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
        # id last: rows tied on both scores come back in a stable order, not in storage order
        .order_by("-vector_similarity", "-lexical_rank", "id")[:limit]
    )


MAX_LINKED_PROVISIONS = 2
# Further chunks of a linked provision's section, when it is split (see _linked_provision_candidates).
MAX_PROVISION_SIBLINGS = 1


def _linked_provision_candidates(standards: list[str], score: float, acts: list[str] | None = None) -> list[dict]:
    """Chunks of the provisions that name the standards (from the legislation vocabulary), as candidates.

    One provision per standard before any standard gets a second, so "NeTEx and SIRI" gets both MMTIS
    Art. 4 and Art. 5 under the cap; only provisions of `acts` (CELEX numbers) when given. For each
    provision, the first chunk that names the standard: a long appendix has several chunks, and a table
    split across two (TEL TSI Appendix C: NeTEx in one, EN 12896 and EN 15531 in the next) gives each
    standard its own chunk.
    """
    from itertools import zip_longest

    from helpdesk.services.regulations import STANDARD_IDENTIFIERS, provisions_naming

    per_standard = [
        [(standard, path) for path in provisions_naming(standard) if not acts or path.split("#", 1)[0] in acts]
        for standard in standards
    ]
    found: list[dict] = []
    seen: set[str] = set()
    for standard, source_path in (pair for row in zip_longest(*per_standard) for pair in row if pair):
        pattern = re.compile(STANDARD_IDENTIFIERS[standard])
        if len(found) >= MAX_LINKED_PROVISIONS:
            break
        chunk = next(
            (c for c in SourceChunk.objects.filter(source_path=source_path).order_by("chunk_id") if pattern.search(c.text)),
            None,
        )
        if chunk is None or chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        found.append(_added_candidate(chunk, score))
    # The rest of a list split across chunks (TEL TSI Appendix C: EN 12896 in one chunk, the NeTEx parts in
    # the one before): the other chunks of the same section that name any standard.
    any_standard = re.compile("|".join(STANDARD_IDENTIFIERS.values()))
    siblings: list[dict] = []
    for provision in list(found):
        for chunk in SourceChunk.objects.filter(
            source_path=provision["sourcePath"], heading=provision["heading"]
        ).order_by("chunk_id"):
            if len(siblings) >= MAX_PROVISION_SIBLINGS:
                break
            if chunk.chunk_id not in seen and any_standard.search(chunk.text):
                seen.add(chunk.chunk_id)
                siblings.append(_added_candidate(chunk, score))
    return found + siblings


def _added_candidate(chunk: SourceChunk, score: float) -> dict:
    """A chunk added next to the ranked evidence, in the shape retrieval returns."""
    return {
        "text": chunk.text,
        "score": score,
        "repositoryUrl": chunk.repository_url,
        "sourceUrl": chunk.source_url,
        "commitSha": chunk.commit_sha,
        "sourcePath": chunk.source_path,
        "chunkId": chunk.chunk_id,
        "label": chunk.label,
        "standardsScope": chunk.standards_scope or [],
        "chunkType": chunk.chunk_type or "",
        "docType": chunk.doc_type or "",
        "heading": chunk.heading or "",
        "structuredMetadata": chunk.structured_metadata or {},
        "retrievalEventId": f"re-{uuid4().hex[:8]}",
    }


def examples_using_elements(elements: list[str], limit: int = 3, repository: str = "netex") -> list[dict]:
    """The standard's own example chunks that use the given elements, most of them first, one per file.

    For a generated example, the text is about how the standard fills the elements that hold the
    question's values; similarity search found a rail example without WheelchairPlaceCapacity for "a
    coach with 49 seats and 1 wheelchair area" while nine example files use it. A text lookup on the
    element tags (about 80 ms) finds them directly.
    """
    from helpdesk.services.netex_example_generator import has_tag

    tags = [name for name in elements if re.fullmatch(r"[A-Za-z][\w.-]*", name)][:4]
    if not tags:
        return []
    base = SourceChunk.objects.filter(repository_url__icontains=repository, source_path__startswith="examples/")
    found: list[dict] = []
    files: set[str] = set()
    # All tags first, then fewer: a chunk using every value element shows them together.
    for size in range(len(tags), 0, -1):
        query = base
        for tag in tags[:size]:
            query = query.filter(has_tag(tag))
        for chunk in query.order_by("source_path", "chunk_id")[:40]:
            if chunk.source_path in files or chunk.source_path.startswith(".mylocal"):
                continue
            files.add(chunk.source_path)
            found.append(_added_candidate(chunk, 1.0))
            if len(found) >= limit:
                return found
    return found


MAX_NAMED_EXAMPLES = 2
# Example chunks read per question: the chunks with a heading, which only Turtle examples have.
_NAMED_EXAMPLE_SCAN_LIMIT = 2000


def _name_words(type_name: str) -> list[str]:
    """The words of a type name: "dcat:CatalogRecord" -> ["catalog", "record"]."""
    local = type_name.rsplit(":", 1)[-1].rsplit("#", 1)[-1]
    return [w.lower() for w in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", local)]


def _word_matches(asked: str, named: str) -> bool:
    """Same word, or one starts with the other and the shorter has five letters or more.

    This covers spelling variants and plurals ("catalogue" / "Catalog", "records" / "Record") without a
    word list.
    """
    if asked == named:
        return True
    shorter, longer = sorted((asked, named), key=len)
    return len(shorter) >= 5 and longer.startswith(shorter)


def _named_example_candidates(question: str, scope: list[str] | None, score: float) -> list[dict]:
    """Example chunks of the scope whose heading names the type the question asks an example of.

    A Turtle example is chunked by resource, and the chunk heading lists the resource types
    ("dcat:CatalogRecord"). The text says "dcat:CatalogRecord" where the question says "catalogue record",
    so by similarity the chunk ranked 93rd of 236 mobilityDCAT-AP chunks and never reached the candidate
    pool (prod 2026-11-07); the spec tables about the class took its place. The type whose words the
    question names with the most words wins ("catalogue record": CatalogRecord, not Catalog), and at most
    one chunk per file, the one that describes fewest types.
    """
    if not scope:
        return []
    question_words = set(re.findall(r"[a-z0-9]+", question.lower()))
    best_words = 0
    matches: list[tuple[int, SourceChunk]] = []
    chunks = (
        SourceChunk.objects.filter(_scope_query_filter(scope), doc_type="example")
        .exclude(heading="")
        .order_by("source_path", "chunk_id")[:_NAMED_EXAMPLE_SCAN_LIMIT]
    )
    for chunk in chunks:
        types = [t.strip() for t in chunk.heading.split(",") if t.strip()]
        named = 0
        for type_name in types:
            words = [w for w in _name_words(type_name) if len(w) >= 3]
            if words and all(any(_word_matches(q, w) for q in question_words) for w in words):
                named = max(named, len(words))
        if not named or named < best_words:
            continue
        if named > best_words:
            best_words, matches = named, []
        matches.append((len(types), chunk))
    found: list[dict] = []
    seen_paths: set[str] = set()
    for _, chunk in sorted(matches, key=lambda pair: (pair[0], pair[1].source_path, pair[1].chunk_id)):
        if chunk.source_path in seen_paths or len(found) >= MAX_NAMED_EXAMPLES:
            continue
        seen_paths.add(chunk.source_path)
        found.append(_added_candidate(chunk, score))
    return found


MAX_STANDARD_IDENTITY_CHUNKS = 1


def _standard_identity_candidates(provisions: list[dict], score: float) -> list[dict]:
    """For standards a provision names only by number ("EN 12896-1:2016 … Reference data model"), the
    standards chunk that gives the name and the number together ("Transmodel V6.2 (EN 12896 series)").

    Without it the answer cannot tell that the act names the standard the question asks about. The
    chunk naming the most of the needed standards comes first; standards sources only, never an act.
    """
    from helpdesk.services.regulations import SCOPE as LEGISLATION_SCOPE, STANDARD_NAMES, STANDARD_NUMBERS

    needed: list[str] = []
    for provision in provisions:
        text = str(provision.get("text", ""))
        for standard, number in STANDARD_NUMBERS.items():
            if re.search(number, text) and not re.search(STANDARD_NAMES[standard], text) and standard not in needed:
                needed.append(standard)
    found: list[dict] = []
    while needed and len(found) < MAX_STANDARD_IDENTITY_CHUNKS:
        digits = re.search(r"\d+", STANDARD_NUMBERS[needed[0]]).group(0)
        candidates = (
            SourceChunk.objects.filter(text__contains=digits)
            .exclude(standards_scope__contains=[LEGISLATION_SCOPE])
            .exclude(chunk_id__in=[c["chunkId"] for c in found])
            .order_by("-quality_score", "chunk_id")[:50]
        )

        def covered(chunk: SourceChunk) -> list[str]:
            return [
                s for s in needed if re.search(STANDARD_NAMES[s], chunk.text) and re.search(STANDARD_NUMBERS[s], chunk.text)
            ]

        best = max(
            (c for c in candidates if needed[0] in covered(c)), key=lambda c: len(covered(c)), default=None
        )
        if best is None:
            needed.pop(0)
            continue
        found.append(_added_candidate(best, score))
        needed = [s for s in needed if s not in covered(best)]
    return found


def _scope_matches(chunk_scope: list[str], requested_scope: list[str] | None) -> bool:
    if not requested_scope:
        return bool(set(chunk_scope).intersection(CORE_SCOPES)) or not set(chunk_scope).intersection(OPT_IN_SCOPES)
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


def _relation_path_candidates(question_concepts: set[str]) -> list[dict]:
    """Relation-path evidence for a relationship question, ranked above scored chunks.

    Paths are the answer to "how is X related to Y" and would otherwise never reach
    the generator: they are graph edges, not text. Each path comes with the indexed
    XSD chunk that shows its subclass step, when there is one.
    """
    if not getattr(settings, "GRAPHDB_ENABLED", False):
        return []
    graph = load_relation_graph(
        endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
        repository=settings.GRAPHDB_REPOSITORY,
        username=getattr(settings, "GRAPHDB_USER", ""),
        password=getattr(settings, "GRAPHDB_PASSWORD", ""),
        timeout_seconds=max(5, int(settings.GRAPHDB_TIMEOUT_SECONDS)),
        transmodel_of=CONCEPT_TO_TRANSMODEL,
    )
    if graph is None:
        return []
    paths = relation_paths_for_question(graph, question_concepts, CONCEPT_TO_TRANSMODEL, TRANSMODEL_TO_CONCEPTS)
    if not paths:
        return []

    candidates: list[dict] = []
    for index, chunk in enumerate(format_relation_paths_as_chunks(paths, commit_shas=indexed_commit_shas())):
        candidates.append(
            {
                **chunk,
                "score": 1.0,
                "_rankScore": 3.0 - index * 0.01,
                "_vectorScore": 1.0,
                "chunkType": "relation-path",
                "structuredMetadata": {},
                "retrievalEventId": f"re-{uuid4().hex[:8]}",
                "_graphContribution": 0.0,
                "_graphHit": True,
                "_graphProvenanceConceptIds": sorted(question_concepts),
            }
        )
    for index, chunk in enumerate(supporting_subclass_chunks(paths)):
        candidates.append(
            {
                "text": chunk.text,
                "score": 0.95,
                "_rankScore": 2.5 - index * 0.01,
                "_vectorScore": 0.9,
                "repositoryUrl": chunk.repository_url,
                "commitSha": chunk.commit_sha,
                "sourcePath": chunk.source_path,
                "chunkId": chunk.chunk_id,
                "label": chunk.label,
                "standardsScope": chunk.standards_scope or [],
                "chunkType": chunk.chunk_type or "",
                "docType": chunk.doc_type or "",
                "heading": chunk.heading or "",
                "structuredMetadata": chunk.structured_metadata or {},
                "retrievalEventId": f"re-{uuid4().hex[:8]}",
                "_graphContribution": 0.0,
                "_graphHit": True,
                "_graphProvenanceConceptIds": sorted(question_concepts),
            }
        )
    return candidates


def _cap_expanded_concepts(
    *,
    question_concepts: set[str],
    expanded_concepts: set[str],
    max_concepts: int,
    concept_distances: dict[str, int] | None = None,
) -> set[str]:
    """Cap expanded graph concepts to reduce query drift and noisy fan-out.

    Takes concepts round-robin across hop-distance levels (nearest first),
    alphabetically within each level, rather than a single alphabetical sort
    over the whole set. A sort keyed on distance alone still lets one hop
    level's fan-out consume the entire cap before a farther level is ever
    considered (e.g. a seed with 30 hop-1 neighbors leaves no room for a
    hop-2 concept, however relevant) -- round-robin guarantees every hop
    level present gets a share of the budget as long as the cap is at least
    as large as the number of distinct hop levels.

    This does not fully solve every case: within one hop level, a relevant
    concept can still be crowded out by same-level siblings that merely sort
    earlier (this is a tiebreak, not a relevance score) -- that needs ranking
    by relation type (e.g. a direct property reference vs. an
    rdfs:subClassOf sibling), which this function does not have the
    information to do.
    """

    if max_concepts <= 0:
        return set()
    if len(expanded_concepts) <= max_concepts:
        return expanded_concepts

    distances = concept_distances or {}
    seeds = sorted(c for c in expanded_concepts if c in question_concepts)
    non_seeds = [c for c in expanded_concepts if c not in question_concepts]

    buckets: dict[int, list[str]] = {}
    for concept_id in non_seeds:
        buckets.setdefault(distances.get(concept_id, 1), []).append(concept_id)
    for bucket in buckets.values():
        bucket.sort()

    selected = list(seeds)
    remaining_budget = max_concepts - len(selected)
    hop_levels = sorted(buckets)
    cursors = {hop: 0 for hop in hop_levels}
    while remaining_budget > 0 and any(cursors[hop] < len(buckets[hop]) for hop in hop_levels):
        for hop in hop_levels:
            if remaining_budget <= 0:
                break
            if cursors[hop] < len(buckets[hop]):
                selected.append(buckets[hop][cursors[hop]])
                cursors[hop] += 1
                remaining_budget -= 1

    return set(selected[:max_concepts])


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


def _example_chunk_boost(doc_type: str, query_concepts: set[str]) -> float:
    """Boost example chunks so they rank high enough to be included in context.

    Examples provide concrete evidence for understanding schema concepts.
    This boost ensures example chunks aren't crowded out by other documents
    when the retrieval context window fills up.

    Args:
        doc_type: The document type (e.g., "xml-example")
        query_concepts: Set of ontology concepts in the question

    Returns:
        Score boost to add to ranking (0.0 if not an example)
    """
    if doc_type == "xml-example":
        # Strong boost for examples when concepts are identified
        boost = 0.15 if query_concepts else 0.10
        return boost
    return 0.0


_ELEMENT_STANDARD_PREFIXES = ("netex:", "siri:", "opra:")
_ELEMENT_BOOST_DOC_TYPES = frozenset({"example", "xml-example", "schema", "xsd-definition"})


def concept_element_names(concept_ids: set[str]) -> list[str]:
    """XML element names for the standard-namespace concepts a question names
    (netex:TemplateServiceJourney -> TemplateServiceJourney)."""
    return sorted(
        concept_id.split(":", 1)[1]
        for concept_id in concept_ids
        if concept_id.startswith(_ELEMENT_STANDARD_PREFIXES) and concept_id.split(":", 1)[1][:1].isupper()
    )


def _element_candidates(element_names: list[str], per_element: int = 6) -> list:
    """Indexed example and schema chunks whose text contains <Element followed by
    a space, > or />, a few per element, highest quality first."""
    from django.db.models import Q

    found: list = []
    seen: set[int] = set()
    for name in element_names[:4]:
        tag_match = Q(text__contains=f"<{name} ") | Q(text__contains=f"<{name}>") | Q(text__contains=f"<{name}/")
        for chunk in (
            SourceChunk.objects.filter(tag_match, doc_type__in=("example", "schema"))
            .order_by("-quality_score", "id")[:per_element]
        ):
            if chunk.id not in seen:
                seen.add(chunk.id)
                found.append(chunk)
    return found


def _ensure_element_coverage(
    selected: list[dict], candidates: list[dict], element_names: list[str], top_k: int
) -> list[dict]:
    """Put the best chunk for each asked element right after the definitions.

    The answer model only sees the first few chunks. When a question names two
    elements (TemplateServiceJourney, FlexibleServiceProperties), plain ranking
    can fill those slots with examples of one element only; the model then
    improvises the other (it presented TimeDemandTypeRef as "on demand").
    """
    if len(element_names) < 2:
        return selected

    def shows(candidate: dict, name: str) -> bool:
        return bool(re.search(rf"<{re.escape(name)}[\s>/]", candidate.get("text", "") or ""))

    covering: list[dict] = []
    for name in element_names:
        best = next((c for c in selected if shows(c, name)), None) or next(
            (c for c in candidates if shows(c, name)), None
        )
        if best is not None and all(best is not chosen for chosen in covering):
            covering.append(best)
    if not covering:
        return selected

    leading = [c for c in selected if c.get("docType") in {"ontology-definition", "ontology-relation"}]
    rest = [c for c in selected if all(c is not x for x in leading + covering)]
    return (leading + covering + rest)[:top_k]


def _ensure_source_coverage(
    selected: list[dict], candidates: list[dict], path_groups: list[set[str]], top_k: int
) -> list[dict]:
    """Put the best chunk from each named service's schema right after the definitions.

    A comparison question ("overlaps between SIRI-CA and SIRI-VM") needs evidence
    for both sides; plain ranking filled every slot with Vehicle Monitoring.
    """
    if len(path_groups) < 2:
        return selected

    leading_types = {"ontology-definition", "ontology-relation"}

    def from_schema(candidate: dict, paths: set[str]) -> bool:
        # Computed chunks (shared structure) cite a schema path but are not the schema.
        return candidate.get("sourcePath") in paths and candidate.get("docType") not in leading_types

    covering: list[dict] = []
    for paths in path_groups:
        best = next((c for c in selected if from_schema(c, paths)), None) or next(
            (c for c in candidates if from_schema(c, paths)), None
        )
        if best is not None and all(best is not chosen for chosen in covering):
            covering.append(best)
    if not covering:
        return selected

    leading = [c for c in selected if c.get("docType") in leading_types]
    rest = [c for c in selected if all(c is not x for x in leading + covering)]
    return (leading + covering + rest)[:top_k]


def _concept_element_boost(doc_type: str, chunk_text: str, element_names: list[str]) -> float:
    """Prefer the chunk of a file that actually contains the asked element.

    An example file is split into ~10 chunks and only one per file survives the
    same-source-path cap. Without this, the winner is usually the file's first
    chunk, whose header comment describes the example in words close to the
    question, while the chunk with <TemplateServiceJourney ...> loses.
    """
    if doc_type not in _ELEMENT_BOOST_DOC_TYPES or not element_names or not chunk_text:
        return 0.0
    for name in element_names:
        if re.search(rf"<{re.escape(name)}[\s>/]", chunk_text):
            return 0.2
    return 0.0


def _semantic_definition_boost(doc_type: str, query_concepts: set[str]) -> float:
    """Boost semantic definitions from ontology so they rank high in context.

    Semantic definitions provide authoritative definitions directly from the
    ontology, and should be prioritized over other sources for definition-seeking
    queries. This boost ensures definitions appear in the final context window.

    Args:
        doc_type: The document type (e.g., "ontology-definition")
        query_concepts: Set of ontology concepts in the question

    Returns:
        Score boost to add to ranking (0.0 if not a definition)
    """
    if doc_type == "ontology-definition":
        # Highest priority: definitions are authoritative
        # Stronger boost than examples since definitions directly answer "what is X?" queries
        boost = 0.25 if query_concepts else 0.20
        return boost
    return 0.0


def _build_query_embedding_input(
    question: str,
    hinted_standards: set[str],
    hinted_doc_types: set[str],
    expanded_concept_terms: list[str] | None = None,
) -> str:
    # A semantic model compares meaning, so it gets the question itself; the metadata lines
    # below steer only the hash vectors.
    if semantic_enabled():
        return question
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
    if semantic_enabled():
        return passage_text(chunk.source_path, getattr(chunk, "heading", "") or "", chunk.text)
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
    "mobilityDCAT-AP": {"mobilitydcat", "dcat"},
    "INSPIRE": {"inspire"},
    "DATEX II": {"datex"},
    "TN-ITS": {"tnits", "tn-its"},
}

_STANDARD_SCOPE_ALIASES = {
    "netex": "netex",
    "siri": "siri",
    "opra": "opra",
    "tn-its": "tn-its",
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
    scope: list[str] | None = None,
) -> tuple[float, bool, set[str]]:
    """Score adjustment for graph reasoning with provenance tracking.

    Returns:
        (adjustment_score, is_graph_hit, matching_concept_ids)
    """
    if not graph_enabled:
        return 0.0, False, set()

    chunk_concepts = extract_graph_concepts(
        "\n".join([chunk_text, source_path, label, heading]), scope=scope
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


@lru_cache(maxsize=1024)
def _token_set(value: str) -> frozenset[str]:
    # Graph candidate ranking checks every alias against the same few chunk
    # fields, so each field is tokenized once rather than once per alias.
    return frozenset(_normalize_tokens(value))


def _alias_token_subset_match(alias: str, value: str) -> bool:
    alias_tokens = _token_set(alias)
    if not alias_tokens:
        return False
    return alias_tokens.issubset(_token_set(value or ""))


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


def _preselect_base_ids(vector_ranked: list, base_limit: int, lexical_reserve: int) -> set[int]:
    """Pick `base_limit` candidates from a vector-ranked list for full scoring.

    The last slots (at most a quarter) go to the strongest lexical matches the
    vector order would cut, e.g. a schema named in the question that sits
    mid-pool by vector similarity.
    """
    reserve = min(base_limit // 4, lexical_reserve)
    selected = {int(chunk.id) for chunk in vector_ranked[: base_limit - reserve]}
    lexical_leaders = sorted(
        (chunk for chunk in vector_ranked if int(chunk.id) not in selected),
        key=lambda chunk: float(getattr(chunk, "lexical_rank", 0.0) or 0.0),
        reverse=True,
    )
    selected.update(int(chunk.id) for chunk in lexical_leaders[:reserve])
    return selected


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


# Default of retrieve_chunks_with_trace(english_question=...): compute the English rendering there.
_TRANSLATE = object()


def retrieve_chunks_with_trace(
    question: str,
    top_k: int,
    min_score: float,
    scope: list[str] | None = None,
    graph_rag_enabled: bool = False,
    min_results: int = 0,
    english_question: str | None | object = _TRANSLATE,
) -> tuple[list[dict], dict]:
    """Retrieve chunks for a question; a non-English question is also searched in English.

    english_question: the English rendering when the caller already has it (None: search the question
    only); by default it is computed here.

    The sources are English, and an English rendering finds them more reliably than the question as asked
    (40 benchmark questions in Slovenian and German: hit@4 0.57 as asked, 0.75 searched both ways). Both
    searches use the same scope; their results are merged by rank, the English one first on a tie.
    """
    from helpdesk.services.llm_generator import english_search_query

    arguments = dict(top_k=top_k, min_score=min_score, scope=scope, graph_rag_enabled=graph_rag_enabled, min_results=min_results)
    english = english_search_query(question) if english_question is _TRANSLATE else english_question
    chunks, trace = _retrieve_chunks_once(question=question, **arguments)
    if english:
        english_chunks, english_trace = _retrieve_chunks_once(question=english, **arguments)
        chunks = _merge_by_rank(english_chunks, chunks)[:top_k]
        trace = {
            **trace,
            "searchTranslation": english,
            "allCandidates": _merge_by_rank(english_trace.get("allCandidates", []), trace.get("allCandidates", [])),
            "legalStatusStandards": english_trace.get("legalStatusStandards") or trace.get("legalStatusStandards"),
        }
    return _with_scope_coverage(english or question, chunks, trace, arguments)


# Chunks a scope missing from the result gets: its two best, since the best match by similarity is not
# always the one that answers ("What is INSPIRE?": Directive Art. 2 first, the defining Art. 1 second).
SCOPE_COVERAGE_CHUNKS = 2


def _standards_of(chunk: dict, scope: list[str]) -> set[str]:
    return {standard for standard in chunk.get("standardsScope") or [] if standard in scope}


def _with_scope_coverage(question: str, chunks: list[dict], trace: dict, arguments: dict) -> tuple[list[dict], dict]:
    """Every standard a question is searched in gets a place in the evidence when it has a match.

    Searched together, one scope can crowd out another entirely: for "What is INSPIRE?" in INSPIRE and EU
    legislation, the INSPIRE repository's chunks (with "INSPIRE" everywhere) scored 1.0 and the Directive
    that defines INSPIRE was not among 25 candidates, though searched alone it is found at once (Art. 2 at
    0.77, Art. 1 at 0.58). A scope missing from the result is searched alone and its best chunk replaces the
    last chunk of the most represented scope, and goes right after the top chunk (the model reads the first
    few). Only when a scope is missing, so most questions pay nothing.
    """
    scope = list(arguments.get("scope") or [])
    top_k = int(arguments.get("top_k") or 0)
    if len(scope) < 2 or not chunks or top_k < len(scope):
        return chunks, trace
    present = set().union(*(_standards_of(chunk, scope) for chunk in chunks))
    missing = [standard for standard in scope if standard not in present]
    if not missing:
        return chunks, trace
    started = time.perf_counter()
    result = list(chunks)
    added = []
    for standard in missing:
        alone, _ = _retrieve_chunks_once(
            question=question,
            top_k=SCOPE_COVERAGE_CHUNKS,
            min_score=arguments.get("min_score", 0.0),
            scope=[standard],
            graph_rag_enabled=arguments.get("graph_rag_enabled", False),
            min_results=0,
        )
        for best in [c for c in alone if c.get("chunkId") not in {r.get("chunkId") for r in result}][:SCOPE_COVERAGE_CHUNKS]:
            counts: dict[str, int] = {}
            for chunk in result:
                for name in _standards_of(chunk, scope):
                    counts[name] = counts.get(name, 0) + 1
            crowded = max(counts, key=counts.get) if counts else None
            if len(result) >= top_k:
                drop = next(
                    (i for i in range(len(result) - 1, 0, -1) if crowded in _standards_of(result[i], scope)),
                    len(result) - 1,
                )
                result.pop(drop)
            # Right after the top chunk: the model reads only the first few (LLM_MAX_EVIDENCE_CHUNKS, 4).
            result.insert(min(1 + len(added), len(result)), best)
            added.append({"standard": standard, "sourcePath": best.get("sourcePath")})
    trace = {
        **trace,
        "scopeCoverageAdded": added,
        "scopeCoverageMs": round((time.perf_counter() - started) * 1000),
    }
    return result, trace


def _merge_by_rank(first: list[dict], second: list[dict]) -> list[dict]:
    """Interleave two ranked lists (first[0], second[0], first[1], ...), each chunk once."""
    merged: list[dict] = []
    seen: set[str] = set()
    for index in range(max(len(first), len(second))):
        for ranked in (first, second):
            if index < len(ranked):
                chunk = ranked[index]
                key = str(chunk.get("chunkId") or id(chunk))
                if key not in seen:
                    seen.add(key)
                    merged.append(chunk)
    return merged


def _retrieve_chunks_once(
    question: str,
    top_k: int,
    min_score: float,
    scope: list[str] | None = None,
    graph_rag_enabled: bool = False,
    min_results: int = 0,
) -> tuple[list[dict], dict]:
    """Retrieve chunks using hybrid vector and lexical ranking.

    min_results: when at least one candidate reaches min_score but fewer than min_results do, the
    next-best candidates fill up to min_results. Scores are rescaled within each question's candidates,
    so in a pool of very similar passages (one act's articles) only the best one may reach an absolute
    threshold, and an answer built on it alone misses what the others say.

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

    # "SIRI-CA" becomes "SIRI-CA (Control Actions)", so concept matching, lexical
    # search and the query vector see the service name the README gives.
    question = expand_abbreviations(question, services_in_question(question))

    graph_expansion_max_concepts = max(1, int(getattr(settings, "GRAPH_EXPANSION_MAX_CONCEPTS", 64)))
    graph_expansion_max_candidates = max(1, int(getattr(settings, "GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS", 40)))
    retrieval_scoring_candidate_cap = max(12, int(getattr(settings, "RETRIEVAL_SCORING_CANDIDATE_CAP", 40)))
    graph_preselect_multiplier = max(1, int(getattr(settings, "RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER", 2)))
    lexical_preselect_reserve = max(0, int(getattr(settings, "RETRIEVAL_LEXICAL_PRESELECT_RESERVE", 8)))
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
    question_concepts = (
        extract_graph_concepts(question, word_variants=True, scope=scope) if graph_rag_enabled else set()
    )
    _record_stage("conceptExtractMs", stage_start)
    bridged_concepts: set[str] = set()
    if graph_rag_enabled:
        stage_start = time.perf_counter()
        bridged_concepts = concepts_in_scope(bridged_question_concepts(question), scope) - question_concepts
        question_concepts |= bridged_concepts
        _record_stage("vocabularyBridgeMs", stage_start)
    property_concepts: set[str] = set()
    if graph_rag_enabled and getattr(settings, "PROPERTY_TERMS_ENABLED", True):
        stage_start = time.perf_counter()
        property_concepts = question_property_concepts(question, question_concepts, scope)
        question_concepts |= property_concepts
        _record_stage("propertyTermsMs", stage_start)
    rare_lexemes: list[str] = []
    if semantic_enabled():
        stage_start = time.perf_counter()
        rare_lexemes = question_rare_lexemes(question, scope)
        # "Does SIRI define roadworks?" parses to the concept siri:Siri. In a search scoped to SIRI alone it
        # names nothing more specific (with NeTEx and OpRa in scope it does tell them apart), yet its graph neighbours (ServiceDelivery, VehicleMonitoringDelivery) were
        # boosted over the RoadWorks definitions. It is dropped when the question has a topic of its own (a
        # rare term); for "What is SIRI?" it is the topic and stays.
        identity_concepts = {
            concept
            for concept in question_concepts
            if _is_standard_identity_concept(concept) and scope and len(scope) == 1
            and concept.partition(":")[0].lower() == scope[0].lower()
        }
        if identity_concepts and rare_lexemes:
            question_concepts -= identity_concepts
        _record_stage("rareTermMs", stage_start)

    # Concepts of opt-in sources (TN-ITS) add their cited definitions and element lookups only. Through graph
    # expansion and the graph score they reordered the source's own passages: for "How is a road feature
    # update encoded in a TN-ITS dataset?" the examples overtook the schemas the question is about.
    graph_question_concepts = concepts_in_scope(question_concepts, None)

    graph_expansion_source = "none"
    if graph_rag_enabled and graph_question_concepts:
        stage_start = time.perf_counter()
        graph_expansion_hops = 1
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
                # The per-concept distance is what _cap_expanded_concepts below
                # uses to keep the closest concepts when truncating.
                concept_distances = query_graphdb_concept_expansion_with_distance(
                    concept_ids=graph_question_concepts,
                    hops=graph_expansion_hops,
                    endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
                    repository=settings.GRAPHDB_REPOSITORY,
                    username=getattr(settings, "GRAPHDB_USER", ""),
                    password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                    timeout_seconds=settings.GRAPHDB_TIMEOUT_SECONDS,
                    graph_uris=graph_scope or None,
                )
                graph_expansion_source = "graphdb"
            except Exception:
                concept_distances = expand_graph_concepts_with_distance(graph_question_concepts, hops=graph_expansion_hops)
                graph_expansion_source = "memory_fallback"
        else:
            concept_distances = expand_graph_concepts_with_distance(graph_question_concepts, hops=graph_expansion_hops)
            graph_expansion_source = "memory"
        expanded_concepts = _cap_expanded_concepts(
            question_concepts=graph_question_concepts,
            expanded_concepts=concepts_in_scope(concept_distances, scope),
            max_concepts=graph_expansion_max_concepts,
            concept_distances=concept_distances,
        )
        _record_stage("graphExpandMs", stage_start)
    else:
        expanded_concepts = set()
        graph_expansion_hops = 0
        stage_timing_ms["graphExpandMs"] = 0.0

    # Placeholder for example retrieval (moved after chunk_iterable initialization)
    example_chunks_added = 0
    ontology_definitions_added = 0

    stage_start = time.perf_counter()
    canonical_concept_terms = get_concept_canonical_terms(expanded_concepts) if expanded_concepts else []
    _record_stage("conceptMetadataMs", stage_start)

    # Extract domain-specific concepts (XML elements, properties, classes) from question
    # These are combined with ontology concepts for richer semantic search
    stage_start = time.perf_counter()
    domain_concepts = extract_concepts(question)
    domain_concept_terms = []
    xsd_schema_chunks = []

    if domain_concepts.get("properties"):
        domain_concept_terms.extend(domain_concepts["properties"])
        # Try to retrieve XSD schema definitions for properties
        for prop in domain_concepts["properties"]:
            # Convert "departure time" to "DepartureTime" for XSD lookup
            prop_camel = ''.join(word.capitalize() for word in prop.split())
            try:
                schema_chunks = retrieve_schema_definitions_for_concepts([prop_camel], standard="NeTEx")
                xsd_schema_chunks.extend(schema_chunks)
            except Exception as e:
                logger.debug(f"Could not retrieve XSD definition for {prop}: {e}")

    if domain_concepts.get("classes"):
        domain_concept_terms.extend(domain_concepts["classes"])
        # Try to retrieve XSD schema definitions for classes
        for cls in domain_concepts["classes"]:
            cls_camel = ''.join(word.capitalize() for word in cls.split())
            try:
                schema_chunks = retrieve_schema_definitions_for_concepts([cls_camel], standard="NeTEx")
                xsd_schema_chunks.extend(schema_chunks)
            except Exception as e:
                logger.debug(f"Could not retrieve XSD definition for {cls}: {e}")

    if domain_concepts.get("standards"):
        domain_concept_terms.extend(domain_concepts["standards"])

    # Combine ontology concepts with domain concepts for richer embedding
    all_concept_terms = canonical_concept_terms + domain_concept_terms if canonical_concept_terms else domain_concept_terms
    _record_stage("domainConceptExtractMs", stage_start)

    stage_start = time.perf_counter()
    query_embedding = build_text_embedding(
        _build_query_embedding_input(
            question=question,
            hinted_standards=hinted_standards,
            hinted_doc_types=hinted_doc_types,
            expanded_concept_terms=all_concept_terms if all_concept_terms else None,
        ),
        kind="query",
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
    elif scope and len(scope) > 1:
        # A small opt-in source (EU legislation) asked for together with a standard gets its own share
        # of candidates; in one shared pool the standard's tens of thousands of chunks crowd it out.
        for opt_in in (s for s in scope if s in OPT_IN_SCOPES):
            opt_in_candidates = _postgres_hybrid_candidates(
                question=question, query_embedding=query_embedding, top_k=top_k, scope=[opt_in]
            )
            pooled = list(postgres_candidates)
            pooled_ids = {chunk.id for chunk in pooled}
            postgres_candidates = pooled + [c for c in opt_in_candidates if c.id not in pooled_ids]
    if postgres_candidates is not None and semantic_enabled():
        pooled = list(postgres_candidates)
        pooled_ids = {chunk.id for chunk in pooled}
        lexical_pool_size = max(0, int(getattr(settings, "RETRIEVAL_LEXICAL_POOL_SIZE", 8)))
        postgres_candidates = pooled + [
            chunk
            for chunk in _lexical_recall_candidates(
                question=question, limit=lexical_pool_size, scope=scope, rare=rare_lexemes
            )
            if chunk.id not in pooled_ids
        ]
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
    if graph_rag_enabled and _is_example_driven_question(question) and graph_question_concepts:
        try:
            graphdb_enabled = getattr(settings, "GRAPHDB_ENABLED", False)
            if graphdb_enabled:
                example_files = retrieve_concept_examples_with_fallback(
                    concept_ids=graph_question_concepts,
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
                        chunk_iterable.append(ChunkDict(example_chunk))
        except Exception as e:
            logger.debug(f"Failed to retrieve examples: {e}")
    _record_stage("exampleRetrievalMs", stage_start)

    # Retrieve ontology definitions for identified concepts
    # Provides authoritative semantic definitions from ontology
    stage_start = time.perf_counter()
    ontology_definitions_added = 0
    if graph_rag_enabled and question_concepts:
        try:
            graphdb_enabled = getattr(settings, "GRAPHDB_ENABLED", False)
            if graphdb_enabled:
                definitions = retrieve_concept_definitions(
                    concept_ids=question_concepts,
                    endpoint=settings.GRAPHDB_SPARQL_ENDPOINT,
                    repository=settings.GRAPHDB_REPOSITORY,
                    timeout_seconds=max(1, settings.GRAPHDB_TIMEOUT_SECONDS - 1),
                    username=getattr(settings, "GRAPHDB_USER", ""),
                    password=getattr(settings, "GRAPHDB_PASSWORD", ""),
                )
                if definitions:
                    definition_chunks = format_definitions_as_chunks(definitions, commit_shas=indexed_commit_shas())
                    ontology_definitions_added = len(definition_chunks)
                    logger.info(f"Retrieved {ontology_definitions_added} ontology definitions for {len(question_concepts)} concepts")
                    # Add definitions to the retrieval results (highest quality evidence)
                    if not isinstance(chunk_iterable, list):
                        chunk_iterable = list(chunk_iterable)
                    for def_chunk in definition_chunks:
                        chunk_iterable.append(ChunkDict(def_chunk))
        except Exception as e:
            logger.debug(f"Failed to retrieve ontology definitions: {e}")
    _record_stage("ontologyDefinitionRetrievalMs", stage_start)

    # Chunks that contain an element the question names (<TemplateServiceJourney ...>).
    # They may not reach the pool on embedding similarity alone, and a ranking boost
    # can only reorder chunks that are already in it.
    stage_start = time.perf_counter()
    question_element_names = concept_element_names(question_concepts) if graph_rag_enabled else []
    element_chunk_ids: set[int] = set()
    if question_element_names:
        if not isinstance(chunk_iterable, list):
            chunk_iterable = list(chunk_iterable)
        present_ids = {int(chunk.id) for chunk in chunk_iterable}
        for element_chunk in _element_candidates(question_element_names):
            element_chunk_ids.add(int(element_chunk.id))
            if int(element_chunk.id) not in present_ids:
                chunk_iterable.append(element_chunk)
                present_ids.add(int(element_chunk.id))
    # A few chunks of each named service's schema survive preselection like the
    # element chunks, so the coverage step below has both sides of a comparison.
    service_path_groups = _question_service_paths(question)
    if len(service_path_groups) >= 2:
        if not isinstance(chunk_iterable, list):
            chunk_iterable = list(chunk_iterable)
        for paths in service_path_groups:
            for chunk in [c for c in chunk_iterable if c.source_path in paths][:3]:
                element_chunk_ids.add(int(chunk.id))
    _record_stage("elementCandidateMs", stage_start)

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

        # Separate definition chunks - always include them as they're authoritative
        definition_ids: set[int] = set()
        base_candidates = []
        for chunk in chunk_iterable:
            if int(chunk.id) in selected_graph_ids:
                continue
            doc_type = (getattr(chunk, "doc_type", "guide") or "guide").lower()
            if doc_type == "ontology-definition" or int(chunk.id) in element_chunk_ids:
                definition_ids.add(int(chunk.id))
            else:
                base_candidates.append(chunk)

        base_candidates.sort(
            key=lambda chunk: (
                float(getattr(chunk, "vector_similarity", 0.0) or 0.0),
                float(getattr(chunk, "lexical_rank", 0.0) or 0.0),
                float(getattr(chunk, "quality_score", 0.0) or 0.0),
            ),
            reverse=True,
        )

        base_limit = max(0, retrieval_scoring_candidate_cap - len(selected_graph_ids) - len(definition_ids))
        selected_base_ids = _preselect_base_ids(base_candidates, base_limit, lexical_preselect_reserve)

        chunk_iterable = [
            chunk
            for chunk in chunk_iterable
            if int(chunk.id) in selected_base_ids or int(chunk.id) in selected_graph_ids or int(chunk.id) in definition_ids
        ]
    _record_stage("candidatePreselectMs", stage_start)

    stage_start = time.perf_counter()
    candidates = []
    below_threshold_candidates: list[dict] = []
    # With semantic vectors, similarity decides the ranking: it is rescaled to 0-1 over this
    # question's candidates (the model's similarities fall in a narrow band), and the legacy
    # floor and README penalty below, tuned for hash vectors, no longer override it. Both
    # parts were needed in the trial; either alone found no README answers.
    vector_range = None
    if semantic_enabled():
        raw_vectors = []
        for chunk in chunk_iterable:
            similarity = getattr(chunk, "vector_similarity", None)
            if similarity is None and chunk.embedding_vector is not None and len(chunk.embedding_vector):
                similarity = cosine_similarity(query_embedding, chunk.embedding_vector)
            if similarity is not None:
                raw_vectors.append(max(0.0, min(1.0, float(similarity))))
        if raw_vectors:
            vector_range = (min(raw_vectors), max(raw_vectors))
    for chunk in chunk_iterable:
        if not _scope_matches(chunk.standards_scope or [], scope):
            continue


        lexical_rank = getattr(chunk, "lexical_rank", None)
        lexical_score = float(lexical_rank) if lexical_rank is not None else 0.0
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

        if vector_range is not None:
            low, high = vector_range
            scaled_vector = (vector_score - low) / (high - low) if high > low else 1.0
            base_score = (scaled_vector * 0.5) + (lexical_score * 0.3) + (quality_score * 0.2)
            doc_type_adjustment = _doc_type_score_adjustment(hinted_doc_types=hinted_doc_types, doc_type=doc_type)
            if doc_type == "readme":
                doc_type_adjustment -= DOC_TYPE_BASE_ADJUSTMENTS.get("readme", 0.0)
        else:
            hybrid_score = (vector_score * 0.5) + (lexical_score * 0.3) + (quality_score * 0.2)
            # Keep backward-compatible retrieval strength so known covered intents do not regress.
            legacy_score = (quality_score * 0.8) + (lexical_score * 0.2)
            base_score = max(hybrid_score, legacy_score)
            doc_type_adjustment = _doc_type_score_adjustment(hinted_doc_types=hinted_doc_types, doc_type=doc_type)
        raw_score = (
            base_score
            + doc_type_adjustment
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
            + _semantic_definition_boost(doc_type=doc_type, query_concepts=question_concepts)
            + _example_chunk_boost(doc_type=doc_type, query_concepts=question_concepts)
            + _concept_element_boost(doc_type=doc_type, chunk_text=chunk.text, element_names=question_element_names)
        )
        graph_adjustment, graph_hit, matching_concepts = _graph_score_adjustment(
            graph_enabled=graph_rag_enabled,
            question_concepts=graph_question_concepts,
            expanded_concepts=expanded_concepts,
            chunk_text=chunk.text,
            source_path=chunk.source_path,
            label=chunk.label,
            heading=getattr(chunk, "heading", "") or "",
            hinted_doc_types=hinted_doc_types,
            scope=scope,
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
        below_threshold = score < min_score
        if below_threshold and not min_results:
            continue

        # Break ties deterministically; keyword-trap chunks rank below genuine matches.
        rank_score = raw_score + (lexical_score * 0.01) + (vector_score * 0.005)
        if keyword_trap:
            rank_score *= keyword_trap_penalty

        (below_threshold_candidates if below_threshold else candidates).append(
            {
                "text": chunk.text,
                "score": score,
                "_rankScore": rank_score,
                "_vectorScore": vector_score,
                "repositoryUrl": chunk.repository_url,
                # Final link of a source outside a repository file, e.g. a Transmodel class page
                "sourceUrl": getattr(chunk, "source_url", "") or "",
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
    if candidates and len(candidates) < min_results:
        below_threshold_candidates.sort(key=lambda value: value["_rankScore"], reverse=True)
        candidates.extend(below_threshold_candidates[: min_results - len(candidates)])
    _record_stage("candidateScoringMs", stage_start)

    # Add XSD schema definitions if they were retrieved for domain concepts
    # These chunks have high quality scores and provide structural information
    if xsd_schema_chunks:
        for xsd_chunk in xsd_schema_chunks:
            candidates.append(
                {
                    "text": xsd_chunk["text"],
                    "score": 0.95,  # High quality score for schema definitions
                    "_rankScore": 0.95,
                    "_vectorScore": 0.90,
                    "repositoryUrl": xsd_chunk.get("repositoryUrl", ""),
                    "commitSha": xsd_chunk.get("commitSha", "v2.0"),
                    "sourcePath": xsd_chunk.get("sourcePath", "xsd/netex_framework/netex_frame.xsd"),
                    "chunkId": xsd_chunk.get("chunkId", ""),
                    "label": xsd_chunk.get("label", ""),
                    "standardsScope": xsd_chunk.get("standards_scope", ["NeTEx"]),
                    "chunkType": "xsd-definition",
                    "docType": xsd_chunk.get("doc_type", "xsd-definition"),
                    "heading": xsd_chunk.get("heading", ""),
                    "retrievalEventId": f"re-{uuid4().hex[:8]}",
                    "_graphContribution": 0.0,
                    "_graphHit": False,
                    "_graphProvenanceConceptIds": [],
                }
            )
        logger.info(f"Added {len(xsd_schema_chunks)} XSD schema definition chunks to candidates")

    stage_start = time.perf_counter()
    relation_paths_added = 0
    if graph_rag_enabled and question_concepts and is_relation_question(question):
        try:
            relation_candidates = _relation_path_candidates(question_concepts)
            candidates.extend(relation_candidates)
            relation_paths_added = sum(1 for c in relation_candidates if c["docType"] == "ontology-relation")
        except Exception:
            logger.warning("Relation-path evidence failed", exc_info=True)
    _record_stage("relationPathMs", stage_start)

    # A comparison of named services gets their shared structure, computed from
    # the schema references stored at index time (schema_overlap).
    stage_start = time.perf_counter()
    schema_overlap_added = 0
    named_services = [service for service in services_in_question(question) if service.schema_paths]
    if len(named_services) >= 2:
        try:
            overlap = overlap_for_schemas(
                [service.schema_paths[0] for service in named_services],
                [service.name for service in named_services],
            )
            if overlap is not None:
                candidates.append(
                    {
                        **format_overlap_chunk(overlap),
                        "score": 1.0,
                        "_rankScore": 3.0,
                        "_vectorScore": 1.0,
                        "chunkType": "schema-overlap",
                        "structuredMetadata": {},
                        "retrievalEventId": f"re-{uuid4().hex[:8]}",
                        "_graphContribution": 0.0,
                        "_graphHit": False,
                        "_graphProvenanceConceptIds": [],
                    }
                )
                schema_overlap_added = 1
        except Exception:
            logger.warning("Schema overlap evidence failed", exc_info=True)
    _record_stage("schemaOverlapMs", stage_start)

    stage_start = time.perf_counter()
    candidates.sort(key=lambda value: (value["_rankScore"], value["score"]), reverse=True)
    candidates = _apply_source_path_cap(candidates=candidates, max_per_source_path=source_path_cap)
    if retrieval_diversity_enabled:
        trimmed = _diversified_top_k(candidates=candidates, top_k=top_k, mmr_lambda=mmr_lambda)
    else:
        trimmed = candidates[:top_k]
    trimmed = _ensure_element_coverage(trimmed, candidates, question_element_names, top_k)
    trimmed = _ensure_source_coverage(trimmed, candidates, _question_service_paths(question), top_k)
    # A question about a standard's legal status ("Is NeTEx mandatory in the EU?") gets the provisions that
    # name that standard, next to the best standards evidence. They are added, not ranked: by similarity
    # legal text would compete with the standards evidence in every question.
    from helpdesk.services.question_parsing import (
        asks_for_named_standards,
        legal_status_standards,
        named_acts,
        standards_named_in_legislation_question,
    )
    from helpdesk.services.regulations import STANDARD_IDENTIFIERS

    legal_standards = legal_status_standards(question, question_concepts, scope)
    legal_acts = None
    if not legal_standards and asks_for_named_standards(question, scope):
        # "Which standards does MMTIS name?": the provisions that name any standard, in the act it names.
        legal_standards, legal_acts = list(STANDARD_IDENTIFIERS), named_acts(question)
    if not legal_standards:
        # "Does the TEL TSI reference Transmodel?": the provisions that name that standard, in the act it names.
        legal_standards = [s for s in standards_named_in_legislation_question(question, scope) if s in STANDARD_IDENTIFIERS]
        legal_acts = named_acts(question) or None
    if legal_standards and trimmed:
        top_score = float(trimmed[0].get("score") or 0.0)
        provisions = _linked_provision_candidates(legal_standards, score=top_score, acts=legal_acts)
        added = provisions + _standard_identity_candidates(provisions, score=top_score)
        added_ids = {c["chunkId"] for c in added}
        trimmed = (trimmed[:1] + [c for c in added if c["chunkId"] != trimmed[0].get("chunkId")]
                   + [c for c in trimmed[1:] if c["chunkId"] not in added_ids])[:top_k]
    # "Show an example of a catalogue record": the example of that type, added after the best evidence.
    # By similarity a Turtle example rarely reaches the pool (_named_example_candidates).
    named_examples_added = 0
    if "example" in hinted_doc_types and trimmed:
        examples = _named_example_candidates(question, scope, score=float(trimmed[0].get("score") or 0.0))
        example_ids = {c["chunkId"] for c in examples}
        trimmed_ids = {c.get("chunkId") for c in trimmed}
        named_examples_added = sum(1 for c in examples if c["chunkId"] not in trimmed_ids)
        if examples:
            trimmed = (trimmed[:1] + [c for c in examples if c["chunkId"] != trimmed[0].get("chunkId")]
                       + [c for c in trimmed[1:] if c["chunkId"] not in example_ids])[:top_k]
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
            ),
            scope=scope,
        )
        graph_concepts_in_trimmed.update(chunk_concepts)
    _record_stage("coverageMetricsMs", stage_start)

    stage_timing_ms["totalMeasuredMs"] = round((time.perf_counter() - retrieval_start_perf) * 1000, 1)

    trace = {
        "graphRagVariant": "control" if not graph_rag_enabled else "graph-rag",
        "graphExpansionHops": graph_expansion_hops,
        "graphExpansionSource": graph_expansion_source,
        "graphConceptIds": sorted(expanded_concepts) if graph_rag_enabled else [],
        "bridgedConceptIds": sorted(bridged_concepts),
        "propertyConceptIds": sorted(property_concepts),
        "schemaOverlapAdded": schema_overlap_added,
        "graphConceptCap": graph_expansion_max_concepts if graph_rag_enabled else 0,
        "graphCandidatesAdded": graph_candidates_added if graph_rag_enabled else 0,
        "graphCandidateCap": graph_expansion_max_candidates if graph_rag_enabled else 0,
        "graphEvidenceCount": graph_hits if graph_rag_enabled else 0,
        "graphScoreContribution": round(graph_total / len(trimmed), 4) if graph_rag_enabled and trimmed else 0.0,
        "graphProvenanceChainCount": len(provenance_chains) if graph_rag_enabled else 0,
        "exampleChunksAdded": example_chunks_added + named_examples_added,
        "ontologyDefinitionsAdded": ontology_definitions_added,
        "relationPathsAdded": relation_paths_added,
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
        "allCandidates": candidates,  # Include all candidate chunks for LLM awareness
        "legalStatusStandards": legal_standards,
    }
    return trimmed, trace
