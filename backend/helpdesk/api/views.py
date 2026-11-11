"""
DRF API views for the NapcoreHelpdesk service.

Implements the full REST surface: answer orchestration (synchronous and
streaming SSE), user feedback, question event listing and detail, editorial
queue management, FAQ promotion candidates, semantic clustering, repository
index ingestion, and health probes.

Answer orchestration follows a tiered path: FAQ match → semantic rule
evaluation → RAG retrieval → LLM generation. Orchestration logic is
delegated to the service layer; views handle HTTP translation and error
mapping only.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-11-01
"""

from collections import defaultdict
import datetime as dt
from datetime import timedelta
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import jwt
from django.conf import settings
from django.db import connection
from django.db import transaction
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from helpdesk.models import EditorialQueueItem, IndexRunMetric, QuestionEvent
from helpdesk.services.editor_accounts import anonymous_roles
from helpdesk.services.editorial_router import route_to_editorial_queue
from helpdesk.services.editorial_workflow import (
    WorkflowTransitionForbidden,
    WorkflowTransitionNotAllowed,
    allowed_actions_for_status,
    apply_transition,
)
from helpdesk.services.controller_llm import ControllerLLMError, decide_route_with_controller_llm
from helpdesk.services.evidence_mapper import map_evidence
from helpdesk.services.event_logger import log_question_event
from helpdesk.services.faq_matcher import match_faq
from helpdesk.services.faq_publication import publish_queue_item_to_faq
from helpdesk.services.grounded_generator import generate_answer
from helpdesk.services.llm_generator import LLMGenerationError, generate_answer_llm, stream_answer_llm
from helpdesk.services.llm_model_recovery import check_gateway_models, get_cached_correction
from helpdesk.services.ontology_registry import current_ontology_version_payload
from helpdesk.services.policy_guard import evaluate_policy
from helpdesk.services.provenance_mapper import persist_evidence_provenance
from helpdesk.services.question_parsing import (
    UNKNOWN_CONCEPT_SENTINEL,
    parse_question_to_semantic_query,
    select_effective_scope,
)
from helpdesk.services.semantic_abstention import semantic_abstention_message
from helpdesk.services.index_builder import index_repository
from helpdesk.services.netex_example_generator import (
    example_element_names,
    example_origin,
    generate_netex_example,
    main_object,
    other_question,
    value_element_names,
)
from helpdesk.services.concept_presence import presence_evidence, question_kind
from helpdesk.services import request_timing
from helpdesk.services.schema_structure import definition_chunk, schema_structure_for
from helpdesk.services.retrieval_gateway import retrieve_chunks_with_trace
from helpdesk.services.retrieval_event_logger import log_retrieval_events
from helpdesk.services.rule_engine import evaluate_semantic_rules
from helpdesk.services.runtime_requirements import ensure_graph_runtime_ready
from helpdesk.services.semantic_clustering import build_semantic_clusters

from .serializers import (
    AnswerFeedbackRequestSerializer,
    AnswerRequestSerializer,
    EditorialQueueListQuerySerializer,
    EditorialQueueMetricsQuerySerializer,
    EditorialQueueRequestSerializer,
    EditorialQueueTransitionRequestSerializer,
    HarvestSourceRequestSerializer,
    IndexRepositoryRequestSerializer,
    PromotionCandidatesQuerySerializer,
    SemanticClustersQuerySerializer,
    QuestionEventsListQuerySerializer,
)


logger = logging.getLogger(__name__)


def _request_id(request):
    # Keep a stable correlation ID for traceability in logs, DB events, and error payloads.
    return request.headers.get("X-Request-Id") or f"req-{uuid4().hex[:12]}"


def _service_version() -> str:
    """The version the service reports: SERVICE_VERSION when set in the environment (production builds),
    else the repo's VERSION file read now, so a running dev stack reports a bump without a restart."""
    if os.environ.get("SERVICE_VERSION"):
        return settings.SERVICE_VERSION
    try:
        return Path(settings.VERSION_FILE).read_text(encoding="utf-8").strip() or settings.SERVICE_VERSION
    except OSError:
        return settings.SERVICE_VERSION


def _service_health_payload(check: str, status_value: str, **extra_fields) -> dict:
    payload = {
        "status": status_value,
        "service": settings.SERVICE_NAME,
        "check": check,
        "version": _service_version(),
        "buildRef": settings.SERVICE_BUILD_REF,
    }
    payload.update(extra_fields)
    return payload


def _citation_title(source_path: str) -> dict:
    """{"title": "MMTIS Art. 4"} for a cited part of an EU act ({"title": "NAPCORE: …"} for a napcore.eu
    document), else nothing: the frontend shows the title instead of the raw source path."""
    from helpdesk.services import datex, inspire, napcore_site
    from helpdesk.services.regulations import citation_title

    title = (
        citation_title(source_path)
        or napcore_site.citation_title(source_path)
        or inspire.citation_title(source_path)
        or datex.citation_title(source_path)
    )
    return {"title": title} if title else {}


def _parse_question(question: str, requested_scope: list[str] | None):
    """(semantic query, English rendering or None, the text the semantic query was parsed from).

    A non-English question is rendered in English once (llm_generator.english_search_query). The concept
    matching, the scope and the refusal rules work with English terms ("national access point",
    "metadata"), so the English rendering is parsed too, and used when it finds more: more scopes than the
    question as asked, or a concept where it finds none. "Welche Metadaten müssen Dateninhaber
    dem nationalen Zugangspunkt bereitstellen?" matched nothing and was refused; "Quelles métadonnées …
    au point d'accès national ?" matched only a concept through the word "point" and was searched without
    the legislation. The rendering is also searched (retrieve_chunks_with_trace); the answer is still
    written for the question as asked.
    """
    from helpdesk.services.llm_generator import english_search_query

    english = english_search_query(question)
    semantic_query = parse_question_to_semantic_query(text=question, requested_scope=requested_scope)
    if english and not requested_scope:
        english_query = parse_question_to_semantic_query(text=english, requested_scope=requested_scope)
        if _parse_strength(english_query) > _parse_strength(semantic_query):
            return english_query, english, english
    return semantic_query, english, question


def _parse_strength(semantic_query) -> tuple[int, bool]:
    """What a parse found, compared scopes first: (how many scopes it names, matches a concept).

    A count, not a yes/no: "nationalen Zugangspunkt" gives the German question the NAPCORE scope, and only
    the English rendering ("national access point", a term the acts define) adds the EU legislation."""
    return len(semantic_query.candidate_standards), semantic_query.core_concept != UNKNOWN_CONCEPT_SENTINEL


def _min_evidence_results() -> int:
    """As many evidence blocks as the answer prompt shows, so a lone chunk above the score threshold
    does not leave the answer with one block (see retrieve_chunks_with_trace)."""
    return max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))


# Words that make a question about law or obligation: only then is the "Legal context" line relevant.
# Before 2026-11-08 every NeTEx answer carried "MMTIS Art. 4 · TEL TSI App. C", schema questions included.
_LEGAL_INTENT = re.compile(
    r"\b(?:mandatory|obligat\w*|oblig\w*|required\s+(?:by|under|to)|requirements?\s+(?:of|in|under)|must\s+(?:I|we|a|an|the)\b"
    r"|compulsory|regulat\w*|directive|delegated|implementing\s+act|legislat\w*|legal\w*|law|laws|lawful|complian\w*|comply"
    r"|national\s+access\s+point|NAPs?\b|MMTIS|RTTI|SRTI|SSTP|TSI|EUR-Lex|article|art\.)",
    re.IGNORECASE,
)


def _asks_about_law(question: str) -> bool:
    return bool(_LEGAL_INTENT.search(question or ""))


# "The evidence does not contain a Ljubljana Bus Station example, so I cannot show one." next to the example
# shown above it: with a block from the schema the text is told not to say what the evidence lacks; a sentence
# that does so anyway contradicts the block and is removed.
_LACK_SENTENCE = re.compile(
    # A sentence about the evidence itself (the evidence, the blocks, the sources) that says it lacks or only
    # partly has something: "does not contain …", "gives only these fragments, not a complete …", "has no …".
    r"(?:(?<=^)|(?<=[.!?]\s)|(?<=\n))[^.!?\n]*\b(?:the\s+)?(?:evidence|blocks?|sources?|provided\s+(?:examples?|material))\b[^.!?\n]*"
    r"\b(?:(?:does|do|did|can)\s*not|cannot|no\s+(?:complete|full|single|example|definition)|only\b[^.!?\n]*\bnot)\b[^.!?\n]*[.!?][ \t]*"
    # The same with the negation first: "A fully valid XML file … cannot be produced from the evidence alone"
    # (prod req-diag-ferry-0974, 2026-11-11, next to an example that validated).
    r"|(?:(?<=^)|(?<=[.!?]\s)|(?<=\n))[^.!?\n\[]*\b(?:cannot|can\s*not|could\s*not|not\s+possible|unable)\b[^.!?\n\[]*"
    r"\b(?:from|in|with|by)\s+(?:the\s+)?(?:evidence|blocks?|sources?|provided\s+(?:examples?|material))\b[^.!?\n\[]*[.!?][ \t]*"
    # Doubt about the example shown above, which the schema has already checked: "should be checked against
    # the schema before use", "may not be fully valid". These two forms only for sentences without a citation:
    # a cited one reports the evidence ("Each example … must be validated by the publisher [E2].").
    r"|(?:(?<=^)|(?<=[.!?]\s)|(?<=\n))[^.!?\n\[]*\b(?:example|fragment|snippet|(?:shown\s+)?above)\b[^.!?\n\[]*"
    r"\b(?:(?:should|must|needs?\s+to)\s+be\s+(?:checked|verified|validated|tested)|(?:may|might)\s+not\s+(?:be\s+(?:fully\s+)?valid|validate)"
    r"|is\s+not\s+(?:fully\s+|necessarily\s+)?valid|cannot\s+be\s+(?:produced|generated|created|built|written))\b[^.!?\n\[]*[.!?][ \t]*",
    re.IGNORECASE,
)


# The contrast left once the lack sentence is gone: "What the blocks do show is that a ServiceJourney …" (prod
# req-diag-ferry-0975, 2026-11-11), "What the evidence does show: …", "The evidence does show how …" read as if
# something were missing next to a block that shows it. The lead-in goes; an emphatic "does show" becomes "shows".
_CONTRAST_SUBJECT = r"(?:the\s+(?:evidence|blocks?|sources?|excerpts?)|it|they)"
_CONTRAST_LEAD = re.compile(
    r"(?:(?<=^)|(?<=[.!?]\s)|(?<=\n))(?:\*\*)?what\s+" + _CONTRAST_SUBJECT + r"\s+(?:does|do)\s+show"
    r"(?:\s*:\s*(?:\*\*)?|(?:\*\*)?\s*:\s*|\s+is\s+that\s+)\s*(?P<next>\S)",
    re.IGNORECASE,
)
_CONTRAST_HOW = re.compile(
    r"(?:(?<=^)|(?<=[.!?]\s)|(?<=\n))what\s+(" + _CONTRAST_SUBJECT + r")\s+(does|do)\s+show\s+is\s+(?=how\b|which\b|where\b)",
    re.IGNORECASE,
)
_EMPHATIC_SHOW = re.compile(r"\b(evidence|blocks?|sources?|excerpts?|it|they|that)\s+(does|do)\s+show\b", re.IGNORECASE)


def _without_contrast(text: str) -> str:
    # The lead-in goes and what followed it starts the sentence with a capital.
    text = _CONTRAST_LEAD.sub(lambda m: m.group("next").upper(), text)
    text = _CONTRAST_HOW.sub(
        lambda m: f"{m.group(1)[:1].upper()}{m.group(1)[1:]} {'shows' if m.group(2).lower() == 'does' else 'show'} ", text
    )
    return _EMPHATIC_SHOW.sub(lambda m: f"{m.group(1)} {'shows' if m.group(2).lower() == 'does' else 'show'}", text)


def _without_lack_sentences(answer_text: str) -> str:
    code = re.findall(r"```.*?```", answer_text, re.S)
    text = re.sub(r"```.*?```", "\x00", answer_text, flags=re.S)
    text = _without_contrast(_LACK_SENTENCE.sub("", text))
    for block in code:
        text = text.replace("\x00", block, 1)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _legal_context(mode: str, scope: list[str] | None, question: str = "") -> list[dict]:
    """Provisions of the EU acts that name the standards an answer is about, for a "Legal context" line.

    Only when the question asks about law or obligation (_LEGAL_INTENT). Empty for refusals, for answers
    that name no standard, and for answers already about legislation (they cite the acts themselves).
    """
    from helpdesk.services.regulations import SCOPE, legal_context

    if mode == QuestionEvent.MODE_ABSTAIN or not scope or SCOPE in scope or not _asks_about_law(question):
        return []
    return legal_context(list(scope))


def _citation_url(chunk: dict) -> str:
    """Link target of a cited chunk.

    A chunk with a sourceUrl (e.g. a Transmodel class page) and a pre-built GitHub tree/blob URL are used
    as they are; otherwise the URL is built from the repository, commit and file path.
    """
    if chunk.get("sourceUrl"):
        return chunk["sourceUrl"]
    repository_url = chunk.get("repositoryUrl", "")
    if "/tree/" in repository_url or "/blob/" in repository_url:
        return repository_url
    return _build_file_url(
        repo_url=repository_url,
        commit_sha=chunk["commitSha"],
        source_path=chunk.get("sourcePath", ""),
    )


def _build_file_url(repo_url: str, commit_sha: str, source_path: str) -> str:
    """Construct a direct GitHub file URL pointing to the exact blob at a commit."""
    # Remove trailing .git if present, normalize the repo URL.
    repo_url = repo_url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    # Prevent double /blob/ construction if source_path is malformed
    if "/blob/" in source_path:
        # sourcePath should not contain /blob/; extract actual relative file path
        # If path is like "examples/file.xml/blob/main/examples/file.xml", take the first part
        parts = source_path.split("/blob/")
        source_path = parts[0] if parts[0] and not parts[0].startswith("/") else parts[-1]

    if source_path.startswith("issues/") and source_path.endswith(".md"):
        issue_number = Path(source_path).stem
        if issue_number.isdigit():
            return f"{repo_url}/issues/{issue_number}"

    # Encode unsafe characters (e.g. spaces) in path segments while keeping / separators.
    # A "#anchor" suffix (e.g. transmodel.ttl#STOP_PLACE) stays a URL fragment; encoded as %23 it
    # would become part of the file name and GitHub would answer 404.
    file_path, hash_mark, fragment = source_path.partition("#")
    encoded_path = quote(file_path, safe="/") + (f"#{quote(fragment, safe='')}" if hash_mark else "")

    resolved_commit_sha = _resolve_commit_sha(repo_url=repo_url, commit_sha=commit_sha)
    # When commit SHA is unavailable, prefer a stable repository ref instead of a broken blob URL.
    normalized_ref = (resolved_commit_sha or "").strip()
    unresolved_refs = {"", "unknown", "placeholder"}
    if normalized_ref.lower() in unresolved_refs:
        resolved_repo_ref = _resolve_repository_ref(repo_url=repo_url)
        if resolved_repo_ref:
            return f"{repo_url}/blob/{resolved_repo_ref}/{encoded_path}"

        default_ref_by_repo = {
            "https://github.com/transmodelecosystem/netex": (
                "https://github.com/TransmodelEcosystem/NeTEx",
                "v2.0",
            ),
            "https://github.com/netex-cen/netex": (
                "https://github.com/TransmodelEcosystem/NeTEx",
                "v2.0",
            ),
            "https://github.com/transmodelecosystem/siri": (
                "https://github.com/TransmodelEcosystem/SIRI",
                "v2.2",
            ),
            "https://github.com/siri-cen/siri": (
                "https://github.com/TransmodelEcosystem/SIRI",
                "v2.2",
            ),
            "https://github.com/transmodelecosystem/opra": (
                "https://github.com/TransmodelEcosystem/OpRa",
                "1.0rc",
            ),
            "https://github.com/opra-cen/opra": (
                "https://github.com/TransmodelEcosystem/OpRa",
                "1.0rc",
            ),
        }
        repo_key = repo_url.lower()
        fallback = default_ref_by_repo.get(repo_key)
        if fallback:
            canonical_repo_url, fallback_ref = fallback
            return f"{canonical_repo_url}/blob/{fallback_ref}/{encoded_path}"

        # Last-resort fallback: default to main to avoid emitting broken blob/unknown links.
        return f"{repo_url}/blob/main/{encoded_path}"

    # Build the GitHub blob URL: https://github.com/OWNER/REPO/blob/COMMIT/PATH
    return f"{repo_url}/blob/{normalized_ref}/{encoded_path}"


def _resolve_commit_sha(repo_url: str, commit_sha: str) -> str:
    """Expand short commit SHAs using the most recent indexed local repository path when available."""

    normalized = (commit_sha or "").strip()
    if len(normalized) >= 40 or not normalized or normalized == "placeholder":
        return normalized

    latest_run = IndexRunMetric.objects.filter(repository_url=repo_url).order_by("-created_at").first()
    if not latest_run:
        return normalized

    repository_path = Path(latest_run.repository_path).expanduser()
    if not repository_path.exists():
        return normalized

    try:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "rev-parse", normalized],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return normalized

    resolved = result.stdout.strip()
    return resolved or normalized


def _resolve_repository_ref(repo_url: str) -> str:
    """Resolve a stable branch/tag ref from the latest indexed local repository when available."""

    latest_run = IndexRunMetric.objects.filter(repository_url=repo_url).order_by("-created_at").first()
    if not latest_run:
        return ""

    repository_path = Path(latest_run.repository_path).expanduser()
    if not repository_path.exists():
        return ""

    # Prefer remote default branch if available (for example, origin/main).
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        origin_head = result.stdout.strip()
        if origin_head.startswith("origin/") and len(origin_head) > len("origin/"):
            return origin_head[len("origin/") :]
    except Exception:
        pass

    # Then prefer current branch if repository is not in detached HEAD state.
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        branch_name = result.stdout.strip()
        if branch_name and branch_name != "HEAD":
            return branch_name
    except Exception:
        pass

    # Finally, if detached, use exact tag name when available.
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "describe", "--tags", "--exact-match", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        tag_name = result.stdout.strip()
        if tag_name:
            return tag_name
    except Exception:
        pass

    return ""


def _dominant_repository_url(chunks: list[dict]) -> str | None:
    if not chunks:
        return None

    repository_weights: dict[str, float] = defaultdict(float)
    for index, chunk in enumerate(chunks):
        repository_url = chunk.get("repositoryUrl")
        if not repository_url:
            continue
        repository_weights[repository_url] += float(chunk.get("score", 0.0)) * max(0.5, 1.0 - (index * 0.08))

    if not repository_weights:
        return None
    return max(repository_weights.items(), key=lambda item: item[1])[0]


def _select_citations(chunks: list[dict], max_citations: int) -> list[dict]:
    def citation_sort_key(chunk: dict) -> tuple:
        source_path = str(chunk.get("sourcePath", "")).lower()
        basename = source_path.rsplit("/", 1)[-1]
        is_docs_or_model = (
            source_path.startswith("docs/")
            or "/docs/" in source_path
            or "model-summary" in source_path
            or source_path.startswith("models/")
            or "/models/" in source_path
        )
        is_readme = basename.startswith("readme.")
        return (
            0 if is_docs_or_model else 1,
            0 if not is_readme else 1,
            -float(chunk.get("score", 0.0)),
            source_path,
        )

    selected: list[dict] = []
    selected_repositories: set[str] = set()
    seen_sources: set[tuple[str, str]] = set()
    sorted_chunks = sorted(chunks, key=citation_sort_key)

    # Pass 1: maximize repository coverage while keeping best-ranked sources per repo.
    for chunk in sorted_chunks:
        repository_url = chunk.get("repositoryUrl", "")
        source_path = chunk.get("sourcePath", "")
        source_key = (repository_url, source_path)
        if source_key in seen_sources:
            continue
        if repository_url in selected_repositories:
            continue

        seen_sources.add(source_key)
        selected_repositories.add(repository_url)
        final_url = _citation_url(chunk)
        selected.append(
            {
                "repositoryUrl": final_url,
                "commitSha": chunk["commitSha"],
                "sourcePath": source_path,
                "chunkId": chunk["chunkId"],
                "label": chunk.get("label"),
                **_citation_title(source_path),
            }
        )
        if len(selected) >= max_citations:
            return selected

    # Pass 2: fill remaining slots by global ranking regardless of repository.
    for chunk in sorted_chunks:
        repository_url = chunk.get("repositoryUrl", "")
        source_path = chunk.get("sourcePath", "")
        source_key = (repository_url, source_path)
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        final_url = _citation_url(chunk)
        selected.append(
            {
                "repositoryUrl": final_url,
                "commitSha": chunk["commitSha"],
                "sourcePath": source_path,
                "chunkId": chunk["chunkId"],
                "label": chunk.get("label"),
                **_citation_title(source_path),
            }
        )
        if len(selected) >= max_citations:
            break

    return selected


def _citations_from_prompt_order(chunks: list[dict], answer_text: str) -> list[dict]:
    """Build the citation list mirroring the LLM prompt's [E#] numbering.

    generate_answer_llm labels evidence blocks [E1]..[EN] as the first
    LLM_MAX_EVIDENCE_CHUNKS chunks in retrieval order, so the citation list
    must preserve exactly that order and length for the answer's [E#] markers
    to point at the right sources. Uncited trailing entries are trimmed so the
    list does not advertise references the answer never uses; interior entries
    are kept so positions still match labels for position-based consumers.
    """
    max_chunks = max(1, int(getattr(settings, "LLM_MAX_EVIDENCE_CHUNKS", 4)))
    prompt_chunks = chunks[:max_chunks]
    cited = {
        int(num)
        for num in re.findall(r"\[E(\d+)\]", answer_text or "")
        if 1 <= int(num) <= len(prompt_chunks)
    }
    keep_until = max(cited) if cited else len(prompt_chunks)

    citations: list[dict] = []
    for index, chunk in enumerate(prompt_chunks[:keep_until], start=1):
        final_url = _citation_url(chunk)
        citations.append(
            {
                "repositoryUrl": final_url,
                "commitSha": chunk["commitSha"],
                "sourcePath": chunk.get("sourcePath", ""),
                "chunkId": chunk["chunkId"],
                "label": f"E{index}",
                **_citation_title(chunk.get("sourcePath", "")),
            }
        )
    return citations


_SENTENCE_END_PATTERN = re.compile(r"[.!?](?:\s|$)|\n")


def _rewrite_source_paths_as_evidence_markers(answer_text: str, citations: list[dict]) -> str:
    """Replace cited sourcePath strings in answer prose with the file name and its [E#] marker.

    A path is often part of the sentence ("defined in the file xsd/NeTEx_siri.xsd"), so it
    becomes the file name rather than a bare marker, which would read "in the file [E2]".
    The marker follows the name unless the rest of the sentence already cites that source.
    """

    if not answer_text or not citations:
        return answer_text

    rewritten = answer_text
    for index, citation in enumerate(citations, start=1):
        source_path = str(citation.get("sourcePath", "")).strip()
        if not source_path:
            continue

        marker = f"[E{index}]"
        file_name = source_path.rsplit("/", 1)[-1]

        def _name_and_marker(match: re.Match, marker: str = marker, file_name: str = file_name) -> str:
            rest = match.string[match.end():]
            sentence_end = _SENTENCE_END_PATTERN.search(rest)
            rest_of_sentence = rest[: sentence_end.start() if sentence_end else len(rest)]
            if marker in rest_of_sentence:
                return f"`{file_name}`"
            return f"`{file_name}` {marker}"

        rewritten = re.sub(rf"`?{re.escape(source_path)}`?", _name_and_marker, rewritten)

    return rewritten


def _drop_markers_without_citation(answer_text: str, citations: list[dict]) -> str:
    """Remove [E#] markers that point past the citation list.

    [E#] is the #-th citation. A model sometimes cites a block that was never in its
    prompt ([E20] when only E1-E6 exist); when the retry does the same, its answer is
    still used, and the marker would link to nothing.
    """

    if not answer_text:
        return answer_text

    def _keep_if_cited(match: re.Match) -> str:
        return match.group(0) if 1 <= int(match.group(1)) <= len(citations) else ""

    return re.sub(r"[ \t]*\[E(\d+)\]", _keep_if_cited, answer_text)


def _merge_citations_of_same_source(answer_text: str, citations: list[dict]) -> tuple[str, list[dict]]:
    """Give each source file one citation and renumber the answer's [E#] markers to match.

    Two evidence blocks are often passages of the same file; the prompt numbers them [E1]
    and [E2], but the reader needs one reference per file. The merged citation keeps the
    first passage's entry, and a marker repeated in a row afterwards is kept once.
    """

    if not citations:
        return answer_text, citations

    merged: list[dict] = []
    first_index_of_source: dict[str, int] = {}
    new_index: dict[int, int] = {}
    for old_index, citation in enumerate(citations, start=1):
        source = str(citation.get("sourcePath", "")).strip() or f"#{old_index}"
        if source not in first_index_of_source:
            merged.append({**citation, "label": f"E{len(merged) + 1}"})
            first_index_of_source[source] = len(merged)
        new_index[old_index] = first_index_of_source[source]
    if len(merged) == len(citations):
        return answer_text, citations

    def _renumber(match: re.Match) -> str:
        old = int(match.group(1))
        return f"[E{new_index[old]}]" if old in new_index else match.group(0)

    text = re.sub(r"\[E(\d+)\]", _renumber, answer_text or "")
    text = re.sub(r"\[E(\d+)\](?:[ \t]*\[E\1\])+", r"[E\1]", text)
    return text, merged


def _inject_evidence_markers_if_missing(answer_text: str, citations: list[dict]) -> str:
    """
    Fallback: if answer_text lacks [E#] markers but citations exist,
    inject them at sentence boundaries to indicate evidence-grounded statements.
    This handles cases where LLM was prompted for citations but token budget prevented them.
    """
    import re

    if not answer_text or not citations or len(citations) < 1:
        return answer_text

    # Check if answer already has any evidence markers
    if re.search(r'\[E\d+\]', answer_text):
        return answer_text  # Already has markers, skip injection

    # If answer lacks markers despite having citations, inject top citation after first sentence
    first_sentence_match = re.search(r'([.!?]+)', answer_text)
    if first_sentence_match and len(citations) > 0:
        insertion_point = first_sentence_match.end()
        marker = " [E1]"
        answer_text = answer_text[:insertion_point] + marker + answer_text[insertion_point:]

    return answer_text


def _error_response(code, message, request_id, http_status=status.HTTP_400_BAD_REQUEST):
    # Central helper to preserve the OpenAPI ErrorResponse contract shape.
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
            }
        },
        status=http_status,
    )


def _request_roles(request):
    """Extract normalized role set from JWT claims plus local admin fallback."""

    roles = set()
    token = request.auth if isinstance(request.auth, dict) else {}

    role = token.get("role")
    if isinstance(role, str) and role.strip():
        roles.add(role.strip().lower())

    token_roles = token.get("roles", [])
    if isinstance(token_roles, str):
        token_roles = [token_roles]
    if isinstance(token_roles, list):
        for item in token_roles:
            if isinstance(item, str) and item.strip():
                roles.add(item.strip().lower())

    user = getattr(request, "user", None)
    if user and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
        roles.add("admin")

    return roles


EDITORIAL_ROLES = frozenset({"editor", "reviewer", "publisher", "admin"})


def _forbid_without_editorial_role(request):
    """403 for a token without an editorial role (the anonymous reader), else None."""

    if _request_roles(request) & EDITORIAL_ROLES:
        return None
    return _error_response(
        code="FORBIDDEN",
        message="This needs a signed-in editor account.",
        request_id=_request_id(request),
        http_status=status.HTTP_403_FORBIDDEN,
    )


def _resolve_graph_rag_enabled(_options: dict) -> bool:
    """Graph retrieval runs unconditionally whenever GRAPH_RAG_ENABLED is true.

    Variant flags and per-request opt-out are not honoured: knowledge graph
    expansion should always apply so that reasoning is repo-independent.
    """
    if settings.GRAPH_RAG_ENABLED:
        ensure_graph_runtime_ready()
        return True
    return False


def _request_actor_id(request):
    """Resolve actor identifier used in transition audit entries."""

    token = request.auth if isinstance(request.auth, dict) else {}
    subject = token.get("sub")
    if isinstance(subject, str) and subject.strip():
        return subject.strip()
    user = getattr(request, "user", None)
    username = getattr(user, "username", "") if user else ""
    return username or "unknown"


def _evidence_coverage_level(chunks: list[dict], avg_score: float) -> str:
    """Classify evidence coverage for traceability and provisional-answer signaling."""

    if len(chunks) >= 4 and avg_score >= 0.75:
        return "high"
    if len(chunks) >= 2 and avg_score >= 0.62:
        return "medium"
    return "low"


def _non_answer_outcome(*, allow_abstain: bool) -> tuple[str, float, bool, bool, str | None]:
    """(mode, confidence, review_required, abstained, abstention_reason) for an LLM answer that says the
    evidence does not answer the question. Its text stays (it is in the user's language and says what the
    evidence does cover), but it is not an answer: confidence 0 rather than the retrieval score, and an
    abstention, so the editorial queue and the FAQ candidates treat the question as unresolved."""
    if not allow_abstain:
        return QuestionEvent.MODE_RAG, 0.0, True, False, None
    return QuestionEvent.MODE_ABSTAIN, 0.0, True, True, QuestionEvent.REASON_INSUFFICIENT_EVIDENCE


def _classify_partial_evidence(
    *,
    mode: str,
    abstained: bool,
    confidence: float,
    chunks: list[dict],
    graph_trace: dict,
    effective_scope: list[str],
) -> dict:
    """Return provisional-answer metadata for partial-evidence fallback behavior."""

    if mode != QuestionEvent.MODE_RAG or abstained:
        return {
            "semanticProvisional": False,
            "semanticProvisionalReason": None,
            "evidenceCoverageLevel": "high",
        }

    if not chunks:
        return {
            "semanticProvisional": True,
            "semanticProvisionalReason": "LIMITED_EVIDENCE_COVERAGE",
            "evidenceCoverageLevel": "low",
        }

    avg_score = sum(float(chunk.get("score", 0.0)) for chunk in chunks) / max(1, len(chunks))
    coverage_level = _evidence_coverage_level(chunks, avg_score)
    semantic_alignment = float(graph_trace.get("semanticAlignmentScore", 0.0))
    repository_coverage = int(graph_trace.get("repositoryCoverageCount", 0))

    reason = None
    if confidence < 0.72 or semantic_alignment < 0.40:
        reason = "LOW_RETRIEVAL_CONFIDENCE"
    elif len(chunks) < 2 or coverage_level == "low":
        reason = "LIMITED_EVIDENCE_COVERAGE"
    elif len(effective_scope) > 1 and repository_coverage < min(2, len(effective_scope)):
        reason = "CROSS_STANDARD_GAP"

    return {
        "semanticProvisional": reason is not None,
        "semanticProvisionalReason": reason,
        "evidenceCoverageLevel": coverage_level,
    }


def _evaluate_evidence_gate(*, chunks: list[dict], graph_trace: dict, effective_scope: list[str]) -> dict:
    """Apply generic grounding checks before generation.

    This guard is intentionally benchmark-agnostic and uses only retrieval/trace
    quality signals.
    """

    min_chunks = max(1, int(getattr(settings, "EVIDENCE_GATE_MIN_CHUNKS", 1)))
    min_alignment = float(getattr(settings, "EVIDENCE_GATE_MIN_ALIGNMENT", 0.30))
    min_multi_scope_repositories = max(
        1,
        int(getattr(settings, "EVIDENCE_GATE_MIN_REPOSITORIES_MULTI_SCOPE", 2)),
    )

    if len(chunks) < min_chunks:
        return {
            "allowed": False,
            "reason": "INSUFFICIENT_EVIDENCE",
            "review_required": False,
        }

    alignment = float(graph_trace.get("semanticAlignmentScore", 0.0))
    if alignment < min_alignment:
        return {
            "allowed": False,
            "reason": "LOW_RETRIEVAL_CONFIDENCE",
            "review_required": True,
        }

    if len(effective_scope) > 1:
        repository_coverage = int(graph_trace.get("repositoryCoverageCount", 0))
        expected_repositories = min(len(effective_scope), min_multi_scope_repositories)
        if repository_coverage < expected_repositories:
            return {
                "allowed": False,
                "reason": "CROSS_STANDARD_GAP",
                "review_required": True,
            }

    return {
        "allowed": True,
        "reason": None,
        "review_required": True,
    }


def _infer_standard_from_chunk(chunk: dict, effective_scope: list[str]) -> str | None:
    chunk_scope = chunk.get("standardsScope") or chunk.get("standards_scope") or []
    if isinstance(chunk_scope, list):
        for standard in effective_scope:
            if standard in chunk_scope:
                return standard

    blob = "\n".join(
        [
            str(chunk.get("repositoryUrl", "")),
            str(chunk.get("sourcePath", "")),
            str(chunk.get("label", "")),
            str(chunk.get("text", "")),
        ]
    ).lower()
    aliases = {
        "NeTEx": ["netex"],
        "OpRa": ["opra"],
        "SIRI": ["siri"],
        "Transmodel": ["transmodel"],
        "mobilityDCAT-AP": ["mobilitydcat", "dcat"],
        "INSPIRE": ["inspire"],
        "DATEX II": ["datex"],
        "TN-ITS": ["tn-its", "tnits"],
    }
    for standard in effective_scope:
        for alias in aliases.get(standard, []):
            if alias in blob:
                return standard
    return None


def _build_cross_standard_analysis(
    *,
    mode: str,
    effective_scope: list[str],
    chunks: list[dict],
) -> dict:
    """Build per-standard evidence partitions and detect contradiction signals."""

    if mode != QuestionEvent.MODE_RAG or len(effective_scope) < 2:
        return {
            "crossStandardConflict": False,
            "crossStandardConflictType": None,
            "crossStandardEvidencePartitions": [],
        }

    partitions: dict[str, list[dict]] = {standard: [] for standard in effective_scope}
    for chunk in chunks:
        standard = _infer_standard_from_chunk(chunk, effective_scope)
        if standard:
            partitions.setdefault(standard, []).append(chunk)

    partition_payload: list[dict] = []
    mandatory_standards: set[str] = set()
    optional_standards: set[str] = set()
    conflict_subject_detected = False

    for standard in effective_scope:
        standard_chunks = partitions.get(standard, [])
        if not standard_chunks:
            continue

        merged_text = "\n".join(str(chunk.get("text", "")).lower() for chunk in standard_chunks)
        signals = []
        if any(token in merged_text for token in ["shall", "must", "required"]):
            signals.append("mandatory")
            mandatory_standards.add(standard)
        if any(token in merged_text for token in ["may", "optional"]):
            signals.append("optional")
            optional_standards.add(standard)
        if any(token in merged_text for token in ["journey", "delay", "pattern", "timetable", "exchange"]):
            conflict_subject_detected = True

        top_paths = []
        for chunk in sorted(standard_chunks, key=lambda item: float(item.get("score", 0.0)), reverse=True)[:3]:
            source_path = str(chunk.get("sourcePath", "")).strip()
            if source_path and source_path not in top_paths:
                top_paths.append(source_path)

        avg_score = sum(float(chunk.get("score", 0.0)) for chunk in standard_chunks) / len(standard_chunks)
        partition_payload.append(
            {
                "standard": standard,
                "evidenceCount": len(standard_chunks),
                "avgScore": round(avg_score, 4),
                "topSourcePaths": top_paths,
                "normativitySignals": signals,
            }
        )

    conflict_type = None
    conflict_detected = False
    if mandatory_standards and optional_standards and conflict_subject_detected:
        conflict_detected = True
        conflict_type = "NORMATIVE_STRENGTH_MISMATCH"
    elif len(partition_payload) >= 2 and any(partition["evidenceCount"] == 0 for partition in partition_payload):
        conflict_detected = True
        conflict_type = "EVIDENCE_COVERAGE_ASYMMETRY"

    return {
        "crossStandardConflict": conflict_detected,
        "crossStandardConflictType": conflict_type,
        "crossStandardEvidencePartitions": partition_payload,
    }


class HealthLiveView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Liveness reflects process availability without dependency checks.
        return Response(_service_health_payload(check="live", status_value="ok"), status=status.HTTP_200_OK)


class ServiceStatusView(APIView):
    """Whether answers are slower than usual right now (an index run, a saturated host). Public, like the
    health checks: the frontend polls it to show a banner, and nothing in it is secret."""

    permission_classes = [AllowAny]

    def get(self, request):
        from helpdesk.services.service_status import current_status

        response = Response(current_status(), status=status.HTTP_200_OK)
        response["Cache-Control"] = "no-store"
        return response


BROKER_CHECK_TIMEOUT_SECONDS = 3


def _broker_status() -> str:
    """"ok" if this process can open a connection to the Celery broker, else "unavailable".

    It catches more than an unreachable Redis: a client library mismatch (kombu.VersionMismatch, the
    2026-11-03 outage) also fails here, in the same way that it fails the worker and every .delay().
    """
    from config.celery import app as celery_app

    try:
        with celery_app.connection_for_write() as conn:
            conn.ensure_connection(max_retries=1, interval_start=0, interval_step=0, timeout=BROKER_CHECK_TIMEOUT_SECONDS)
    except Exception:
        logger.warning("Celery broker check failed", exc_info=True)
        return "unavailable"
    return "ok"


class HealthReadyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Readiness requires successful DB connectivity before accepting traffic.
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response(
                _service_health_payload(check="ready", status_value="degraded", database="unavailable"),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # The broker only carries background work (harvests, the nightly refresh); questions are answered
        # without it. So a broker failure marks the service degraded but keeps it ready (200): deploy.sh
        # waits on this endpoint with the maintenance page up, and checks the broker field separately.
        broker = _broker_status()
        from helpdesk.services.concept_vectors import index_status

        # The concept index (classes found by meaning) is informational: without it answers use label words.
        return Response(
            _service_health_payload(
                check="ready", status_value="ok" if broker == "ok" else "degraded", database="ok", broker=broker,
                **index_status(),
            ),
            status=status.HTTP_200_OK,
        )


def _describe_llm_provider(
    *,
    label: str,
    enabled: bool,
    base_url: str,
    configured_model: str,
    api_key: str,
    verify_ssl: bool,
    ca_bundle: str,
    live: bool,
    backend: str = "openai-compatible",
) -> dict:
    """Build one provider's status block: config, cached self-heal state, and an optional live gateway probe."""
    if not enabled:
        return {"provider": label, "enabled": False, "status": "disabled"}

    from helpdesk.services import anthropic_chat

    if backend == anthropic_chat.PROVIDER:
        # Claude via the Anthropic API: no gateway alias drift to self-heal, so no cached correction.
        base_url = "https://api.anthropic.com"

    cached_correction = get_cached_correction(base_url, configured_model)
    block = {
        "provider": label,
        "enabled": True,
        "apiBaseUrl": base_url,
        "configuredModel": configured_model,
        "activeModel": cached_correction or configured_model,
        "autoCorrected": cached_correction is not None,
    }

    if not live:
        block["status"] = "unknown" if cached_correction is None else "degraded"
        return block

    if backend == anthropic_chat.PROVIDER:
        probe = anthropic_chat.check_models(api_key=settings.ANTHROPIC_API_KEY)
    else:
        probe = check_gateway_models(api_base_url=base_url, api_key=api_key, verify_ssl=verify_ssl, ca_bundle=ca_bundle)
    block["backend"] = backend
    block["gatewayReachable"] = probe["reachable"]
    if probe["error"]:
        block["probeError"] = probe["error"]

    if not probe["reachable"]:
        block["status"] = "degraded"
    elif probe["modelIds"] is None:
        # Gateway responded but the /models body couldn't be parsed for IDs -- can't confirm authorization.
        block["status"] = "degraded" if cached_correction else "unknown"
    else:
        block["authorizedModels"] = probe["modelIds"]
        configured_authorized = configured_model in probe["modelIds"]
        block["configuredModelAuthorized"] = configured_authorized
        if configured_authorized:
            block["status"] = "ok"
        elif cached_correction and cached_correction in probe["modelIds"]:
            # Configured model is drifted but the self-heal has already found and is using a valid one.
            block["status"] = "degraded"
        else:
            block["status"] = "error"

    return block


class HealthLLMView(APIView):
    # AllowAny to match HealthLiveView/HealthReadyView: health checks are meant
    # to be viewable directly in a browser (or by infra probes) without a
    # bearer token, same as the other /health/* endpoints. No secret ever
    # appears in the payload -- base URL, model names, and reachability only.
    permission_classes = [AllowAny]

    def get(self, request):
        # Diagnostic status for the answer-generation and controller-routing LLM providers:
        # configured vs. actually-authorized model, and whether the self-heal in
        # llm_model_recovery has already had to correct a drifted gateway alias.
        # Pass ?live=false to skip the network probe and report cached state only.
        live = request.query_params.get("live", "true").strip().lower() not in ("false", "0", "no")

        llm_block = _describe_llm_provider(
            label="answer_generation",
            enabled=settings.LLM_ENABLED,
            base_url=settings.LLM_API_BASE_URL,
            configured_model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            verify_ssl=settings.LLM_VERIFY_SSL,
            ca_bundle=settings.LLM_CA_BUNDLE,
            live=live,
            backend=settings.LLM_PROVIDER,
        )
        controller_block = _describe_llm_provider(
            label="controller_routing",
            enabled=settings.CONTROLLER_LLM_ENABLED and settings.CONTROLLER_LLM_PROVIDER in {"openai-compatible", "anthropic"},
            base_url=settings.CONTROLLER_LLM_API_BASE_URL,
            configured_model=settings.CONTROLLER_LLM_API_MODEL,
            api_key=settings.CONTROLLER_LLM_API_KEY,
            verify_ssl=settings.CONTROLLER_LLM_VERIFY_SSL,
            ca_bundle=settings.CONTROLLER_LLM_CA_BUNDLE,
            live=live,
            backend=settings.CONTROLLER_LLM_PROVIDER,
        )

        statuses = {llm_block["status"], controller_block["status"]}
        if statuses <= {"disabled"}:
            overall = "disabled"
        elif "error" in statuses:
            overall = "error"
        elif "degraded" in statuses:
            overall = "degraded"
        elif "unknown" in statuses:
            overall = "unknown"
        else:
            overall = "ok"

        # Unlike /health/ready, this endpoint isn't a traffic-gating readiness
        # probe -- it's a diagnostic dashboard for humans/tooling to read.
        # Always return 200 so the body's own `status` field (ok/degraded/
        # error/disabled/unknown) is the single source of truth, and callers
        # (including the frontend status page) don't need special-case
        # handling for a non-2xx response that still carries useful data.
        return Response(
            _service_health_payload(
                check="llm",
                status_value=overall,
                llm=llm_block,
                controllerLlm=controller_block,
            ),
            status=status.HTTP_200_OK,
        )


class DevTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Dev convenience endpoint to avoid manual token copy/paste after page reload.
        # Gated on DEV_JWT_AUTO_ISSUE alone (not DEBUG): this must stay togglable
        # independent of Django's general debug setting -- see
        # test_dev_token_endpoint_issues_token_when_auto_issue_enabled.
        if not settings.DEV_JWT_AUTO_ISSUE:
            return Response(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Dev token endpoint is disabled.",
                        "requestId": _request_id(request),
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "sub": settings.DEV_JWT_DEFAULT_SUBJECT,
            # Reader only once editor accounts exist (services/editor_accounts.py).
            "roles": anonymous_roles(),
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(minutes=settings.DEV_JWT_TTL_MINUTES)).timestamp()),
        }
        if settings.JWT_ISSUER:
            payload["iss"] = settings.JWT_ISSUER
        if settings.JWT_AUDIENCE:
            payload["aud"] = settings.JWT_AUDIENCE

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return Response(
            {
                "token": token,
                "tokenType": "Bearer",
                "expiresInSeconds": settings.DEV_JWT_TTL_MINUTES * 60,
                "subject": payload["sub"],
                "roles": payload["roles"],
            },
            status=status.HTTP_200_OK,
        )


class QuestionAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # This endpoint enforces explicit request IDs for end-to-end traceability.
        request_id = _request_id(request)
        if "X-Request-Id" not in request.headers:
            return _error_response(
                code="MISSING_HEADER",
                message="X-Request-Id header is required.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        options = data.get("options", {})
        question = data["question"].strip()
        language = data.get("language", "en")
        scope = data.get("standardsScope", [])
        request_timing.start()
        with request_timing.timed("parseMs"):
            semantic_query, english_question, parsed_question = _parse_question(question, scope)
        semantic_query_dict = semantic_query.as_dict() if hasattr(semantic_query, "as_dict") else {}
        effective_scope, needs_clarification = select_effective_scope(semantic_query, scope)
        semantic_disambiguation_required = False
        semantic_disambiguation_prompt = None
        semantic_fallback = None
        generation_profile = data.get("generationProfile", "llm-ready")
        controller_profile = data.get("controllerProfile", generation_profile)
        allow_abstain = options.get("allowAbstain", True)
        faq_min_confidence = options.get("faqMinConfidence", 0.85)
        max_citations = options.get("maxCitations", 5)
        retrieval_top_k = options.get("retrievalTopK", 6)
        retrieval_min_score = options.get("retrievalMinScore", 0.62)

        mode = QuestionEvent.MODE_RAG
        confidence = 0.0
        abstained = False
        abstention_reason = None
        generated_example = None
        dropped_answer = None
        presence = []
        schema_structure = None
        review_required = True
        matched_faq_entry_id = None
        retrieval_event_ids = []
        evidence_link_ids = []
        citations = []
        retrieved_chunks = []
        provenance_ids = []
        rule_result = {"rulesEvaluated": [], "conclusions": [], "matchedRuleCount": 0}
        ontology_versions = []
        graph_trace = {
            "graphRagVariant": "control",
            "graphExpansionHops": 0,
            "graphExpansionSource": "none",
            "graphConceptIds": [],
            "graphCandidatesAdded": 0,
            "graphEvidenceCount": 0,
            "graphScoreContribution": 0.0,
            "graphProvenanceChainCount": 0,
            "repositoryCoverageCount": 0,
            "conceptCoverageCount": 0,
            "semanticAlignmentScore": 0.0,
            "retrievalLatencyMs": 0.0,
        }
        faq_match = None
        controller_route = None

        # 1) FAQ-first: fast, deterministic, and usually high confidence.
        if needs_clarification:
            # Several named standards and an ambiguous core concept: search all of them, and ask for clarification.
            semantic_disambiguation_required = True
            semantic_disambiguation_prompt = (
                "Your question maps to multiple core concepts. "
                "Please clarify the intended standard or artifact type for a more precise answer."
            )
            semantic_fallback = "AMBIGUOUS_CORE_CONCEPT"

        faq_match = match_faq(question=question, scope=effective_scope)
        qualifying_faq_match = bool(
            faq_match
            and faq_match["confidence"] >= faq_min_confidence
            and faq_match.get("scope_match", True)
        )

        # Optional controller model can veto the FAQ route in favour of RAG. Its
        # decision only matters when a qualifying FAQ match exists, so the
        # controller LLM call is skipped entirely otherwise. Any failure falls
        # back to the current deterministic flow.
        if qualifying_faq_match and controller_profile == "llm-ready":
            try:
                controller_decision = decide_route_with_controller_llm(
                    question=question,
                    requested_scope=effective_scope,
                    semantic_query=semantic_query_dict,
                )
                controller_route = controller_decision.route if controller_decision else None
            except ControllerLLMError:
                controller_route = None

        if qualifying_faq_match and controller_route != "rag":
            # FAQ match identifies the intent and scope. Run retrieval + LLM to
            # produce a grounded answer enriched from actual source evidence.
            # The stored FAQ answer is passed as a directional hint to the LLM.
            # Fall back to the stored answer when retrieval or LLM is unavailable.
            mode = QuestionEvent.MODE_FAQ
            matched_faq_entry_id = faq_match["faq_entry_id"]

            graph_rag_enabled = _resolve_graph_rag_enabled(options)
            chunks, graph_trace = retrieve_chunks_with_trace(
                question=question,
                top_k=retrieval_top_k,
                min_score=retrieval_min_score,
                scope=effective_scope,
                graph_rag_enabled=graph_rag_enabled,
                min_results=_min_evidence_results(),
                english_question=english_question,
            )
            retrieved_chunks = chunks
            retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]
            all_candidates = graph_trace.get("allCandidates", [])

            use_llm = generation_profile == "llm-ready" and settings.LLM_ENABLED
            if chunks and use_llm:
                try:
                    generated = generate_answer_llm(
                        question=question,
                        chunks=chunks,
                        scope=effective_scope,
                        faq_hint=faq_match["answer"],
                        language=language,
                        all_candidates=all_candidates,
                    )
                    answer_text = generated["answer"]
                    confidence = generated["confidence"]
                    review_required = generated["review_required"]
                    citations = _select_citations(chunks=chunks, max_citations=max_citations)
                except LLMGenerationError:
                    logger.warning(
                        "LLM generation failed on FAQ-enriched path; using stored FAQ answer",
                        extra={
                            "requestId": request_id,
                            "faqEntryId": matched_faq_entry_id,
                        },
                        exc_info=True,
                    )
                    answer_text = faq_match["answer"]
                    confidence = faq_match["confidence"]
                    review_required = faq_match["review_required"]
                    citations = faq_match["citations"][:max_citations]
            elif chunks:
                generated = generate_answer(question=question, chunks=chunks)
                answer_text = generated["answer"]
                confidence = generated["confidence"]
                review_required = generated["review_required"]
                citations = _select_citations(chunks=chunks, max_citations=max_citations)
            else:
                answer_text = faq_match["answer"]
                confidence = faq_match["confidence"]
                review_required = faq_match["review_required"]
                citations = faq_match["citations"][:max_citations]
        elif (
            abstention_message := semantic_abstention_message(
                semantic_query=semantic_query,
                effective_scope=effective_scope,
                requested_scope=scope,
                allow_abstain=allow_abstain,
                question=parsed_question,
            )
        ) is not None:
            mode = QuestionEvent.MODE_ABSTAIN
            confidence = 0.0
            abstained = True
            abstention_reason = QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
            review_required = True
            semantic_fallback = "NO_CONCEPT_MATCH"
            answer_text = abstention_message
            citations = []
        else:
            # 2) RAG fallback: retrieve evidence, generate, then run policy gate.
            graph_rag_enabled = _resolve_graph_rag_enabled(options)
            chunks, graph_trace = retrieve_chunks_with_trace(
                question=question,
                top_k=retrieval_top_k,
                min_score=retrieval_min_score,
                scope=effective_scope,
                graph_rag_enabled=graph_rag_enabled,
                min_results=_min_evidence_results(),
                english_question=english_question,
            )

            # Retry with a relaxed threshold to avoid abstaining on terse asks that still
            # have relevant evidence in indexed sources.
            relaxed_min_score = min(retrieval_min_score, 0.45)
            if not chunks and relaxed_min_score < retrieval_min_score:
                chunks, graph_trace = retrieve_chunks_with_trace(
                    question=question,
                    top_k=retrieval_top_k,
                    min_score=relaxed_min_score,
                    scope=effective_scope,
                    graph_rag_enabled=graph_rag_enabled,
                    min_results=_min_evidence_results(),
                    english_question=english_question,
                )

            # "Does NeTEx have X?": the model's definition of X (with which standards implement it) and the
            # schema elements named after X go first; text retrieval alone found unrelated examples.
            presence = presence_evidence(question, effective_scope, english_question)
            if presence:
                presence_ids = {c["chunkId"] for c in presence}
                chunks = (presence + [c for c in chunks if c.get("chunkId") not in presence_ids])[: max(retrieval_top_k, len(presence))]
            retrieved_chunks = chunks
            retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]
            all_candidates = graph_trace.get("allCandidates", [])

            if getattr(settings, "EVIDENCE_GATE_ENABLED", False):
                evidence_gate = _evaluate_evidence_gate(
                    chunks=chunks,
                    graph_trace=graph_trace,
                    effective_scope=effective_scope,
                )
            else:
                evidence_gate = {"allowed": True, "reason": None, "review_required": True}

            if (not chunks or not evidence_gate["allowed"]) and allow_abstain:
                # Abstain if we cannot provide grounded evidence safely.
                mode = QuestionEvent.MODE_ABSTAIN
                confidence = 0.0
                abstained = True
                abstention_reason = QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
                review_required = evidence_gate.get("review_required", False)
                if semantic_fallback is None and not evidence_gate.get("allowed", True):
                    semantic_fallback = "PARTIAL_EVIDENCE"
                answer_text = "I do not have sufficient approved-source evidence to answer this safely."
            else:
                # What the element contains, from the schema, for "what does X contain" questions (no model).
                schema_structure = schema_structure_for(question, effective_scope, english_question)
                structure_shown = bool(schema_structure)
                # The example first, so the text can explain it instead of saying none exists.
                generated_example = generate_netex_example(question, chunks, effective_scope, english_question)
                example_ready = bool(generated_example and generated_example.get("valid"))
                example_elements = example_element_names(generated_example)
                if example_elements:
                    # The text is about the example's elements: search for them, not for the question's words
                    # ("bus with 50 seats" finds deck plans; "PassengerCapacity SeatingCapacity" finds its definition).
                    element_chunks, element_trace = _example_element_evidence(
                        generated_example,
                        example_elements,
                        chunks,
                        graph_trace,
                        lambda: retrieve_chunks_with_trace(
                            question=question,
                            top_k=retrieval_top_k,
                            min_score=relaxed_min_score,
                            scope=effective_scope,
                            graph_rag_enabled=graph_rag_enabled,
                            min_results=_min_evidence_results(),
                            english_question=f"{english_question or question} {' '.join(example_elements)}",
                        ),
                        search_question=english_question or question,
                    )
                    element_chunks = _compose_example_evidence(
                        question, english_question, generated_example, element_chunks, chunks, retrieval_top_k
                    )
                    if element_chunks:
                        chunks, graph_trace = element_chunks, element_trace
                        retrieved_chunks = chunks
                        retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]
                        all_candidates = graph_trace.get("allCandidates", [])
                use_llm = generation_profile == "llm-ready" and settings.LLM_ENABLED
                llm_generated = False
                if use_llm:
                    try:
                        generated = generate_answer_llm(
                            question=question,
                            chunks=chunks,
                            scope=effective_scope,
                            language=language,
                            all_candidates=all_candidates,
                            example_elements=example_elements or None,
                            structure_element=schema_structure["element"] if structure_shown else None,
                            example_fragment=(generated_example or {}).get("xml", "") if example_ready else "",
                            also_asks=other_question(english_question or question) if example_ready else "",
                            example_origin=example_origin(generated_example),
                            existence=(question_kind(english_question or question) or True) if presence else False,
                        )
                        llm_generated = True
                    except LLMGenerationError:
                        logger.warning(
                            "LLM generation failed; falling back to deterministic answer",
                            extra={
                                "requestId": request_id,
                                "questionEventId": None,
                                "generationProfile": generation_profile,
                                "controllerProfile": controller_profile,
                                "standardsScope": effective_scope,
                            },
                            exc_info=True,
                        )
                        generated = generate_answer(question=question, chunks=chunks)
                else:
                    generated = generate_answer(question=question, chunks=chunks)
                answer_text = generated["answer"]
                confidence = generated["confidence"]
                review_required = generated["review_required"]
                if llm_generated:
                    # LLM answers cite [E#] by prompt order; the citation list
                    # must mirror that numbering exactly (see _citations_from_prompt_order).
                    citations = _citations_from_prompt_order(chunks=chunks, answer_text=answer_text)
                else:
                    citations = _select_citations(chunks=chunks, max_citations=max_citations)
                if example_ready or structure_shown:
                    answer_text = _without_lack_sentences(answer_text)
                if (example_ready or structure_shown) and generated.get("answer_validated") is False:
                    # With a block from the schema (example or structure), text that failed validation is noise.
                    dropped_answer, answer_text = answer_text, ""
                if (example_ready or structure_shown) and not answer_text.strip():
                    # The block from the schema is the answer; the text had nothing to add.
                    policy = {"allowed": True, "reason": None, "review_required": False}
                    citations = []
                else:
                    policy = evaluate_policy(answer_text=answer_text, citations=citations)
                if not policy["allowed"]:
                    if allow_abstain:
                        # Policy block -> abstain rather than returning potentially unsafe claims.
                        mode = QuestionEvent.MODE_ABSTAIN
                        confidence = 0.0
                        abstained = True
                        abstention_reason = policy["reason"]
                        review_required = policy["review_required"]
                        citations = []
                        answer_text = "I do not have sufficient approved-source evidence to answer this safely."
                    else:
                        return _error_response(
                            code="POLICY_BLOCK",
                            message="Request cannot be answered within policy constraints.",
                            request_id=request_id,
                            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        )
                else:
                    # Policy-approved RAG response.
                    mode = QuestionEvent.MODE_RAG
                    review_required = policy["review_required"] or review_required
                    # A valid generated example answers an example request the evidence alone cannot.
                    if llm_generated and generated.get("evidence_answers_question") is False and not (example_ready or structure_shown):
                        mode, confidence, review_required, abstained, abstention_reason = _non_answer_outcome(
                            allow_abstain=allow_abstain
                        )

            if mode == QuestionEvent.MODE_RAG and retrieved_chunks:
                rule_result = evaluate_semantic_rules(
                    semantic_query=semantic_query,
                    retrieved_chunks=retrieved_chunks,
                    effective_scope=effective_scope,
                )
                ontology_versions = current_ontology_version_payload()

        # Fallback: inject evidence markers if LLM output lacks them
        answer_text = _inject_evidence_markers_if_missing(answer_text=answer_text, citations=citations)

        # Rewrite any source path references to [E#] markers
        answer_text = _rewrite_source_paths_as_evidence_markers(answer_text=answer_text, citations=citations)
        answer_text = _drop_markers_without_citation(answer_text=answer_text, citations=citations)
        answer_text, citations = _merge_citations_of_same_source(answer_text=answer_text, citations=citations)

        # A NeTEx fragment for "example with values" questions, validated against the XSD (None otherwise).
        # Also when the answer abstained for lack of a direct answer: no example in the standard has the
        # question's values, which is exactly when a generated one helps. Never after a policy block.
        # Usually generated before the answer text (above); here only for evidence-gate abstentions.
        if not retrieved_chunks or not (
            mode == QuestionEvent.MODE_RAG or abstention_reason == QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
        ):
            generated_example = None
        elif generated_example is None:
            generated_example = generate_netex_example(question, retrieved_chunks, effective_scope)
        answer_id = f"ans-{uuid4().hex[:12]}"
        # Persist the orchestration outcome as a question event before child trace records.
        event = log_question_event(
            {
                "request_id": request_id,
                "question": question,
                "session_id": data.get("sessionId", ""),
                "user_id": data.get("userId", ""),
                "standards_scope": effective_scope,
                "language": data.get("language", "en"),
                "mode": mode,
                "confidence": confidence,
                "answer": answer_text,
                "abstained": abstained,
                "abstention_reason": abstention_reason,
                "review_required": review_required,
                "matched_faq_entry_id": matched_faq_entry_id,
                "retrieval_event_ids": retrieval_event_ids,
                "evidence_link_ids": evidence_link_ids,
            }
        )

        # Persist retrieval/evidence rows and mirror their IDs into event trace arrays.
        persisted_retrieval_ids = log_retrieval_events(question_event=event, chunks=retrieved_chunks)
        evidence_link_ids = map_evidence(question_event=event, answer_id=answer_id, chunks=citations)
        citation_chunks = []
        if citations and retrieved_chunks:
            chunks_by_id = {chunk.get("chunkId"): chunk for chunk in retrieved_chunks if chunk.get("chunkId")}
            for citation in citations:
                chunk = chunks_by_id.get(citation.get("chunkId"))
                if chunk:
                    citation_chunks.append(chunk)
        provenance_ids = persist_evidence_provenance(
            question_event=event,
            answer_id=answer_id,
            chunks=citation_chunks,
            semantic_query=semantic_query,
            graph_trace=graph_trace,
            rule_result=rule_result,
        )
        event.retrieval_event_ids = persisted_retrieval_ids
        event.evidence_link_ids = evidence_link_ids
        event.save(update_fields=["retrieval_event_ids", "evidence_link_ids", "updated_at"])

        partial_evidence = _classify_partial_evidence(
            mode=mode,
            abstained=abstained,
            confidence=confidence,
            chunks=retrieved_chunks,
            graph_trace=graph_trace,
            effective_scope=effective_scope,
        )
        cross_standard_analysis = _build_cross_standard_analysis(
            mode=mode,
            effective_scope=effective_scope,
            chunks=retrieved_chunks,
        )
        if partial_evidence["semanticProvisional"] and semantic_fallback is None:
            semantic_fallback = "PARTIAL_EVIDENCE"

        trace_response = {
            "requestId": request_id,
            "questionEventId": str(event.id),
            "matchedFaqEntryId": matched_faq_entry_id,
            "retrievalEventIds": persisted_retrieval_ids,
            "searchTranslation": english_question,
            "evidenceLinkIds": evidence_link_ids,
            "graphExpansionHops": graph_trace["graphExpansionHops"],
            "graphConceptIds": graph_trace["graphConceptIds"],
            "graphEvidenceCount": graph_trace["graphEvidenceCount"],
            "graphScoreContribution": graph_trace["graphScoreContribution"],
            "exampleChunksAdded": graph_trace.get("exampleChunksAdded", 0),
            "ontologyDefinitionsAdded": graph_trace.get("ontologyDefinitionsAdded", 0),
            "repositoryCoverageCount": graph_trace.get("repositoryCoverageCount", 0),
            "conceptCoverageCount": graph_trace.get("conceptCoverageCount", 0),
            "semanticAlignmentScore": graph_trace.get("semanticAlignmentScore", 0.0),
            "provenanceIds": provenance_ids,
            "ruleHitsCount": rule_result["matchedRuleCount"],
            "ruleConclusions": rule_result["conclusions"],
            "ontologyVersions": ontology_versions,
            "semanticQuery": semantic_query_dict,
            "semanticDisambiguationRequired": semantic_disambiguation_required,
            "semanticDisambiguationPrompt": semantic_disambiguation_prompt,
            "semanticFallback": semantic_fallback,
            "semanticProvisional": partial_evidence["semanticProvisional"],
            "semanticProvisionalReason": partial_evidence["semanticProvisionalReason"],
            "evidenceCoverageLevel": partial_evidence["evidenceCoverageLevel"],
            "crossStandardConflict": cross_standard_analysis["crossStandardConflict"],
            "crossStandardConflictType": cross_standard_analysis["crossStandardConflictType"],
            "crossStandardEvidencePartitions": cross_standard_analysis[
                "crossStandardEvidencePartitions"
            ],
            "userLikes": event.user_likes,
            "userDislikes": event.user_dislikes,
            "answerSuccess": event.answer_success,
            "citationClickCount": event.citation_click_count,
            "llmRejectedAnswer": (generated.get("rejected_answer") if isinstance(locals().get("generated"), dict) else None),
            "llmRejectionReason": (generated.get("rejection_reason") if isinstance(locals().get("generated"), dict) else None),
            "llmDroppedAnswer": dropped_answer,
            "presenceEvidence": [c.get("sourcePath") for c in presence],
            # False when the answer was served although its retry failed validation too (it is then marked
            # for review); None when no LLM answer was generated.
            "llmAnswerValidated": (generated.get("answer_validated") if isinstance(locals().get("generated"), dict) else None),
            "generatedExample": generated_example,
            "schemaStructure": schema_structure,
            # Where the time went (services/request_timing.py): parse, all retrieval calls and model calls,
            # the last retrieval's stages, and the example's own lookup or generation time.
            "timingsMs": {
                **request_timing.snapshot(),
                "exampleMs": (generated_example or {}).get("generationMs"),
            },
            "retrievalLatencyMs": graph_trace.get("retrievalLatencyMs", 0.0),
            "retrievalStageTimingsMs": graph_trace.get("retrievalStageTimingsMs") or {},
        }

        # Persist trace to event for later retrieval
        event.trace = trace_response
        event.save(update_fields=["trace", "updated_at"])

        return Response(
            {
                "answerId": answer_id,
                "mode": mode,
                "confidence": confidence,
                "answer": answer_text,
                "citations": citations,
                "legalContext": _legal_context(mode, effective_scope, question),
                "abstained": abstained,
                "abstentionReason": abstention_reason,
                "reviewRequired": review_required,
                "generatedExample": generated_example,
                "schemaStructure": schema_structure,
                "trace": trace_response,
            },
            status=status.HTTP_200_OK,
        )


KEEPALIVE_EVENT = ": keep-alive\n\n"  # an SSE comment: clients ignore it, networks see traffic


class _StreamFailure:
    def __init__(self, error: BaseException):
        self.error = error


MAX_EXAMPLE_DEFINITIONS = 3
MAX_EXAMPLE_BLOCKS = 2


def _example_element_evidence(generated_example, example_elements, chunks, graph_trace, search, search_question=""):
    """Evidence about the example's elements, for the text next to it. A generated example needs a search
    for its elements ("bus with 50 seats": PassengerCapacity, SeatingCapacity). One taken verbatim from the
    standard's examples gets the schema's definitions of its elements and the question's own search
    instead: a second full search took ~10 s of ~22 s (local 2026-11-08), over 20 s on prod."""
    if (generated_example or {}).get("origin") != "standard":
        return search()
    # The elements holding the question's values first, then the example's objects; not its frame or the
    # frame's list wrappers (SiteFrame, stopPlaces).
    wanted = value_element_names(generated_example) + [e for e in example_elements if e[:1].isupper() and not e.endswith("Frame")]
    definitions = []
    for element in dict.fromkeys(wanted):
        chunk = definition_chunk(element)
        if chunk and chunk["chunkId"] not in {c["chunkId"] for c in definitions}:
            definitions.append(chunk)
        if len(definitions) >= MAX_EXAMPLE_DEFINITIONS:
            break
    # And the standard's example blocks with the example's object, so the text can say how the standard's
    # examples fill it (without them: "the VehicleType definition is not in the evidence", local 2026-11-09).
    from helpdesk.services.retrieval_gateway import examples_using_elements

    main = main_object(generated_example)
    using = (
        examples_using_elements(
            [main], limit=MAX_EXAMPLE_BLOCKS, prefer_path=generated_example.get("sourcePath"), question=search_question
        )
        if main
        else []
    )
    added = definitions + [c for c in using if c["chunkId"] not in {d["chunkId"] for d in definitions}]
    ids = {c["chunkId"] for c in added}
    return added + [c for c in chunks if c.get("chunkId") not in ids], graph_trace


def _compose_example_evidence(question, english_question, generated_example, element_chunks, chunks, top_k):
    """The evidence for the text next to an example, cut to top_k.

    The chunk of the shown standard example's own file first, so the text can describe the example the user
    sees (without it, the text next to a two-quays example described a deck plan's quays: 6 of 8 example
    questions, 2026-11-09). Then, when the question also asks something else, the definition of what the
    example is an example of and the question's best blocks; then the standard's examples that use the
    elements holding the question's values (SeatingCapacity, WheelchairPlaceCapacity); then the rest.
    """
    from helpdesk.services.retrieval_gateway import examples_using_elements, shown_example_chunk

    search_question = english_question or question
    using = examples_using_elements(
        value_element_names(generated_example),
        # A generated example was shaped on a standard example file's object (its skeleton): that file first.
        prefer_path=(generated_example or {}).get("sourcePath") or (generated_example or {}).get("skeletonSourcePath"),
        question=search_question,
    )
    using_ids = {chunk["chunkId"] for chunk in using}
    # A question that also asks something else ("How do you describe a stop place?") keeps the
    # best blocks of its own search first, so that part can be answered from them.
    asked_too = other_question(search_question)
    first = chunks[:3] if asked_too else []
    if asked_too and (definition := definition_chunk(main_object(generated_example))):
        # The schema's definition of what the example is an example of, so "how do you describe
        # a stop place" is answered from the standard's own words.
        first = [definition] + [c for c in first if c["chunkId"] != definition["chunkId"]][:2]
    seen_ids = {c["chunkId"] for c in first} | using_ids
    composed = (
        first
        + [c for c in using if c["chunkId"] not in {f["chunkId"] for f in first}]
        + [c for c in element_chunks if c["chunkId"] not in seen_ids]
    )
    own = shown_example_chunk(generated_example)
    if own is not None:
        composed = [own] + [c for c in composed if c["chunkId"] != own["chunkId"]]
    return composed[:top_k]


def with_keepalive(events, interval: float):
    """The events of a stream, with an SSE comment whenever none comes for `interval` seconds.

    The stream is produced in a worker thread, so every step that blocks (question parsing, retrieval, schema
    lookups, example generation, the model call) is covered without a status call before each. An error in
    the stream is raised here. interval 0 yields the events inline (tests).
    """
    if not interval or interval <= 0:
        yield from events
        return
    import queue
    import threading

    from django.db import connection

    pending: "queue.Queue" = queue.Queue()
    finished = object()

    def produce():
        try:
            for event in events:
                pending.put(event)
        except BaseException as error:  # handed to the response's generator
            pending.put(_StreamFailure(error))
        finally:
            pending.put(finished)
            connection.close()  # this thread's own database connection

    threading.Thread(target=produce, name="answer-stream", daemon=True).start()
    while True:
        try:
            event = pending.get(timeout=interval)
        except queue.Empty:
            yield KEEPALIVE_EVENT
            continue
        if event is finished:
            return
        if isinstance(event, _StreamFailure):
            raise event.error
        yield event


class QuestionAnswerStreamView(APIView):
    """
    Streaming variant of QuestionAnswerView. Returns an SSE stream so the
    browser can render narration tokens as they arrive from the LLM.

    SSE event shapes:
      data: {"type":"status","stage":"received|retrieving|generating|retrying"}
      data: {"type":"token","delta":"..."}
      data: {"type":"done","answer":{...full AnswerResponse payload...}}
      data: {"type":"error","code":"...","message":"..."}

    Note: true per-token streaming at the WSGI layer requires an async or
    green-thread worker (e.g. gunicorn with gevent).  Django's dev server
    (runserver) streams correctly.  Nginx must be configured with
    proxy_buffering off or X-Accel-Buffering: no (set below).
    """

    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        # Pass StreamingHttpResponse through without DRF wrapping.
        if isinstance(response, StreamingHttpResponse):
            return response
        return super().finalize_response(request, response, *args, **kwargs)

    def post(self, request):
        request_id = _request_id(request)
        if "X-Request-Id" not in request.headers:
            return _error_response(
                code="MISSING_HEADER",
                message="X-Request-Id header is required.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AnswerRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        streaming_response = StreamingHttpResponse(
            with_keepalive(self._event_stream(request, data, request_id), getattr(settings, "STREAM_KEEPALIVE_SECONDS", 0)),
            content_type="text/event-stream",
        )
        streaming_response["Cache-Control"] = "no-cache"
        streaming_response["X-Accel-Buffering"] = "no"
        return streaming_response

    def _sse(self, payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def _status(self, stage: str) -> str:
        return self._sse({"type": "status", "stage": stage})

    def _event_stream(self, request, data, request_id):  # noqa: C901
        # Status events go out before the main steps; with_keepalive (STREAM_KEEPALIVE_SECONDS) adds a
        # comment whenever the stream is silent, so no step leaves the connection idle: proxies close
        # upstreams that send nothing for 60 s, and mobile Safari drops silent requests ("Load failed").
        yield self._status("received")
        options = data.get("options", {})
        question = data["question"].strip()
        language = data.get("language", "en")
        scope = data.get("standardsScope", [])
        request_timing.start()
        with request_timing.timed("parseMs"):
            semantic_query, english_question, parsed_question = _parse_question(question, scope)
        semantic_query_dict = semantic_query.as_dict() if hasattr(semantic_query, "as_dict") else {}
        effective_scope, needs_clarification = select_effective_scope(semantic_query, scope)
        semantic_disambiguation_required = False
        semantic_disambiguation_prompt = None
        semantic_fallback = None
        generation_profile = data.get("generationProfile", "llm-ready")
        controller_profile = data.get("controllerProfile", generation_profile)
        allow_abstain = options.get("allowAbstain", True)
        faq_min_confidence = options.get("faqMinConfidence", 0.85)
        max_citations = options.get("maxCitations", 5)
        retrieval_top_k = options.get("retrievalTopK", 6)
        retrieval_min_score = options.get("retrievalMinScore", 0.62)

        mode = QuestionEvent.MODE_RAG
        confidence = 0.0
        abstained = False
        abstention_reason = None
        generated_example = None
        dropped_answer = None
        presence = []
        schema_structure = None
        review_required = True
        matched_faq_entry_id = None
        retrieval_event_ids = []
        evidence_link_ids = []
        citations = []
        retrieved_chunks = []
        rule_result = {"rulesEvaluated": [], "conclusions": [], "matchedRuleCount": 0}
        ontology_versions = []
        graph_trace = {
            "graphRagVariant": "control",
            "graphExpansionHops": 0,
            "graphExpansionSource": "none",
            "graphConceptIds": [],
            "graphCandidatesAdded": 0,
            "graphEvidenceCount": 0,
            "graphScoreContribution": 0.0,
            "graphProvenanceChainCount": 0,
            "repositoryCoverageCount": 0,
            "conceptCoverageCount": 0,
            "semanticAlignmentScore": 0.0,
            "retrievalLatencyMs": 0.0,
        }
        controller_route = None

        if needs_clarification:
            semantic_disambiguation_required = True
            semantic_disambiguation_prompt = (
                "Your question maps to multiple core concepts. "
                "Please clarify the intended standard or artifact type for a more precise answer."
            )
            semantic_fallback = "AMBIGUOUS_CORE_CONCEPT"

        faq_match = match_faq(question=question, scope=effective_scope)
        answer_text = ""

        qualifying_faq_match = bool(
            faq_match
            and faq_match["confidence"] >= faq_min_confidence
            and faq_match.get("scope_match", True)
        )

        # Optional controller model can veto the FAQ route in favour of RAG. Its
        # decision only matters when a qualifying FAQ match exists, so the
        # controller LLM call is skipped entirely otherwise. Any failure falls
        # back to the current deterministic flow.
        if qualifying_faq_match and controller_profile == "llm-ready":
            try:
                controller_decision = decide_route_with_controller_llm(
                    question=question,
                    requested_scope=effective_scope,
                    semantic_query=semantic_query_dict,
                )
                controller_route = controller_decision.route if controller_decision else None
            except ControllerLLMError:
                controller_route = None

        if qualifying_faq_match and controller_route != "rag":
            # FAQ match identifies the intent and scope. Run retrieval + LLM to
            # produce a grounded answer enriched from actual source evidence.
            # The stored FAQ answer is passed as a directional hint to the LLM.
            # Fall back to the stored answer when retrieval or LLM is unavailable.
            mode = QuestionEvent.MODE_FAQ
            matched_faq_entry_id = faq_match["faq_entry_id"]

            graph_rag_enabled = _resolve_graph_rag_enabled(options)
            yield self._status("retrieving")
            chunks, graph_trace = retrieve_chunks_with_trace(
                question=question,
                top_k=retrieval_top_k,
                min_score=retrieval_min_score,
                scope=effective_scope,
                graph_rag_enabled=graph_rag_enabled,
                min_results=_min_evidence_results(),
                english_question=english_question,
            )
            retrieved_chunks = chunks
            retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]
            all_candidates = graph_trace.get("allCandidates", [])

            use_llm = generation_profile == "llm-ready" and settings.LLM_ENABLED
            if chunks and use_llm:
                generated = None
                try:
                    yield self._status("generating")
                    for event_type, payload in stream_answer_llm(
                        question=question,
                        chunks=chunks,
                        scope=effective_scope,
                        faq_hint=faq_match["answer"],
                        language=language,
                        all_candidates=all_candidates,
                    ):
                        if event_type == "token":
                            yield self._sse({"type": "token", "delta": payload})
                        elif event_type == "status":
                            yield self._status(payload)
                        elif event_type == "done":
                            generated = payload
                except LLMGenerationError as exc:
                    logger.warning(
                        "LLM stream failed on FAQ-enriched path; using stored FAQ answer",
                        extra={"requestId": request_id, "faqEntryId": matched_faq_entry_id},
                        exc_info=True,
                    )
                    yield self._sse({"type": "llm_fallback", "message": str(exc)})

                if generated:
                    answer_text = generated["answer"]
                    confidence = generated["confidence"]
                    review_required = generated["review_required"]
                    citations = _select_citations(chunks=chunks, max_citations=max_citations)
                else:
                    answer_text = faq_match["answer"]
                    confidence = faq_match["confidence"]
                    review_required = faq_match["review_required"]
                    citations = faq_match["citations"][:max_citations]
            elif chunks:
                generated = generate_answer(question=question, chunks=chunks)
                answer_text = generated["answer"]
                confidence = generated["confidence"]
                review_required = generated["review_required"]
                citations = _select_citations(chunks=chunks, max_citations=max_citations)
            else:
                answer_text = faq_match["answer"]
                confidence = faq_match["confidence"]
                review_required = faq_match["review_required"]
                citations = faq_match["citations"][:max_citations]
        elif (
            abstention_message := semantic_abstention_message(
                semantic_query=semantic_query,
                effective_scope=effective_scope,
                requested_scope=scope,
                allow_abstain=allow_abstain,
                question=parsed_question,
            )
        ) is not None:
            mode = QuestionEvent.MODE_ABSTAIN
            confidence = 0.0
            abstained = True
            abstention_reason = QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
            review_required = True
            semantic_fallback = "NO_CONCEPT_MATCH"
            answer_text = abstention_message
            citations = []
        else:
            graph_rag_enabled = _resolve_graph_rag_enabled(options)
            yield self._status("retrieving")
            chunks, graph_trace = retrieve_chunks_with_trace(
                question=question,
                top_k=retrieval_top_k,
                min_score=retrieval_min_score,
                scope=effective_scope,
                graph_rag_enabled=graph_rag_enabled,
                min_results=_min_evidence_results(),
                english_question=english_question,
            )
            relaxed_min_score = min(retrieval_min_score, 0.45)
            if not chunks and relaxed_min_score < retrieval_min_score:
                yield self._status("retrieving")
                chunks, graph_trace = retrieve_chunks_with_trace(
                    question=question,
                    top_k=retrieval_top_k,
                    min_score=relaxed_min_score,
                    scope=effective_scope,
                    graph_rag_enabled=graph_rag_enabled,
                    min_results=_min_evidence_results(),
                    english_question=english_question,
                )

            # "Does NeTEx have X?": the model's definition of X (with which standards implement it) and the
            # schema elements named after X go first; text retrieval alone found unrelated examples.
            presence = presence_evidence(question, effective_scope, english_question)
            if presence:
                presence_ids = {c["chunkId"] for c in presence}
                chunks = (presence + [c for c in chunks if c.get("chunkId") not in presence_ids])[: max(retrieval_top_k, len(presence))]
            retrieved_chunks = chunks
            retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]
            all_candidates = graph_trace.get("allCandidates", [])

            if getattr(settings, "EVIDENCE_GATE_ENABLED", False):
                evidence_gate = _evaluate_evidence_gate(
                    chunks=chunks,
                    graph_trace=graph_trace,
                    effective_scope=effective_scope,
                )
            else:
                evidence_gate = {"allowed": True, "reason": None, "review_required": True}

            if (not chunks or not evidence_gate["allowed"]) and allow_abstain:
                mode = QuestionEvent.MODE_ABSTAIN
                confidence = 0.0
                abstained = True
                abstention_reason = QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
                review_required = evidence_gate.get("review_required", False)
                if semantic_fallback is None and not evidence_gate.get("allowed", True):
                    semantic_fallback = "PARTIAL_EVIDENCE"
                answer_text = "I do not have sufficient approved-source evidence to answer this safely."
            else:
                use_llm = generation_profile == "llm-ready" and settings.LLM_ENABLED
                if use_llm:
                    yield self._status("generating")
                # What the element contains, from the schema, for "what does X contain" questions (no model).
                schema_structure = schema_structure_for(question, effective_scope, english_question)
                structure_shown = bool(schema_structure)
                # The example first, so the text can explain it instead of saying none exists.
                generated_example = generate_netex_example(question, chunks, effective_scope, english_question)
                example_ready = bool(generated_example and generated_example.get("valid"))
                example_elements = example_element_names(generated_example)
                if example_elements:
                    # The text is about the example's elements: search for them, not for the question's words
                    # ("bus with 50 seats" finds deck plans; "PassengerCapacity SeatingCapacity" finds its definition).
                    element_chunks, element_trace = _example_element_evidence(
                        generated_example,
                        example_elements,
                        chunks,
                        graph_trace,
                        lambda: retrieve_chunks_with_trace(
                            question=question,
                            top_k=retrieval_top_k,
                            min_score=relaxed_min_score,
                            scope=effective_scope,
                            graph_rag_enabled=graph_rag_enabled,
                            min_results=_min_evidence_results(),
                            english_question=f"{english_question or question} {' '.join(example_elements)}",
                        ),
                        search_question=english_question or question,
                    )
                    element_chunks = _compose_example_evidence(
                        question, english_question, generated_example, element_chunks, chunks, retrieval_top_k
                    )
                    if element_chunks:
                        chunks, graph_trace = element_chunks, element_trace
                        retrieved_chunks = chunks
                        retrieval_event_ids = [chunk["retrievalEventId"] for chunk in chunks]
                        all_candidates = graph_trace.get("allCandidates", [])
                llm_generated = False
                if use_llm:
                    # Stream tokens to the client; accumulate for post-stream processing.
                    generated = None
                    try:
                        for event_type, payload in stream_answer_llm(
                            question=question,
                            chunks=chunks,
                            scope=effective_scope,
                            language=language,
                            all_candidates=all_candidates,
                            example_elements=example_elements or None,
                            structure_element=schema_structure["element"] if structure_shown else None,
                            example_fragment=(generated_example or {}).get("xml", "") if example_ready else "",
                            also_asks=other_question(english_question or question) if example_ready else "",
                            example_origin=example_origin(generated_example),
                            existence=(question_kind(english_question or question) or True) if presence else False,
                        ):
                            if event_type == "token":
                                yield self._sse({"type": "token", "delta": payload})
                            elif event_type == "status":
                                yield self._status(payload)
                            elif event_type == "done":
                                generated = payload
                                llm_generated = True
                    except LLMGenerationError as exc:
                        logger.warning(
                            "LLM stream generation failed; falling back to deterministic answer",
                            extra={"requestId": request_id},
                            exc_info=True,
                        )
                        # Tokens may have been partially emitted; signal client to discard them.
                        yield self._sse({"type": "llm_fallback", "message": str(exc)})
                        generated = generate_answer(question=question, chunks=chunks)
                        llm_generated = False

                    answer_text = generated["answer"]
                    confidence = generated["confidence"]
                    review_required = generated["review_required"]
                else:
                    generated = generate_answer(question=question, chunks=chunks)
                    answer_text = generated["answer"]
                    confidence = generated["confidence"]
                    review_required = generated["review_required"]

                if llm_generated:
                    # LLM answers cite [E#] by prompt order; the citation list
                    # must mirror that numbering exactly (see _citations_from_prompt_order).
                    citations = _citations_from_prompt_order(chunks=chunks, answer_text=answer_text)
                else:
                    citations = _select_citations(chunks=chunks, max_citations=max_citations)
                if example_ready or structure_shown:
                    answer_text = _without_lack_sentences(answer_text)
                if (example_ready or structure_shown) and generated.get("answer_validated") is False:
                    # With a block from the schema (example or structure), text that failed validation is noise.
                    dropped_answer, answer_text = answer_text, ""
                if (example_ready or structure_shown) and not answer_text.strip():
                    # The block from the schema is the answer; the text had nothing to add.
                    policy = {"allowed": True, "reason": None, "review_required": False}
                    citations = []
                else:
                    policy = evaluate_policy(answer_text=answer_text, citations=citations)
                if not policy["allowed"]:
                    if allow_abstain:
                        mode = QuestionEvent.MODE_ABSTAIN
                        confidence = 0.0
                        abstained = True
                        abstention_reason = policy["reason"]
                        review_required = policy["review_required"]
                        citations = []
                        answer_text = "I do not have sufficient approved-source evidence to answer this safely."
                    else:
                        yield self._sse({
                            "type": "error",
                            "code": "POLICY_BLOCK",
                            "message": "Request cannot be answered within policy constraints.",
                        })
                        return
                else:
                    mode = QuestionEvent.MODE_RAG
                    review_required = policy["review_required"] or review_required
                    # A valid generated example answers an example request the evidence alone cannot.
                    if llm_generated and generated.get("evidence_answers_question") is False and not (example_ready or structure_shown):
                        mode, confidence, review_required, abstained, abstention_reason = _non_answer_outcome(
                            allow_abstain=allow_abstain
                        )

            if mode == QuestionEvent.MODE_RAG and retrieved_chunks:
                rule_result = evaluate_semantic_rules(
                    semantic_query=semantic_query,
                    retrieved_chunks=retrieved_chunks,
                    effective_scope=effective_scope,
                )
                ontology_versions = current_ontology_version_payload()

        answer_text = _inject_evidence_markers_if_missing(answer_text=answer_text, citations=citations)
        answer_text = _rewrite_source_paths_as_evidence_markers(answer_text=answer_text, citations=citations)
        answer_text = _drop_markers_without_citation(answer_text=answer_text, citations=citations)
        answer_text, citations = _merge_citations_of_same_source(answer_text=answer_text, citations=citations)

        # A NeTEx fragment for "example with values" questions, validated against the XSD (None otherwise).
        # Also when the answer abstained for lack of a direct answer: no example in the standard has the
        # question's values, which is exactly when a generated one helps. Never after a policy block.
        # Usually generated before the answer text (above); here only for evidence-gate abstentions.
        if not retrieved_chunks or not (
            mode == QuestionEvent.MODE_RAG or abstention_reason == QuestionEvent.REASON_INSUFFICIENT_EVIDENCE
        ):
            generated_example = None
        elif generated_example is None:
            generated_example = generate_netex_example(question, retrieved_chunks, effective_scope)
        answer_id = f"ans-{uuid4().hex[:12]}"

        event = log_question_event(
            {
                "request_id": request_id,
                "question": question,
                "session_id": data.get("sessionId", ""),
                "user_id": data.get("userId", ""),
                "standards_scope": effective_scope,
                "language": data.get("language", "en"),
                "mode": mode,
                "confidence": confidence,
                "answer": answer_text,
                "abstained": abstained,
                "abstention_reason": abstention_reason,
                "review_required": review_required,
                "matched_faq_entry_id": matched_faq_entry_id,
                "retrieval_event_ids": retrieval_event_ids,
                "evidence_link_ids": evidence_link_ids,
            }
        )

        persisted_retrieval_ids = log_retrieval_events(question_event=event, chunks=retrieved_chunks)
        evidence_link_ids = map_evidence(question_event=event, answer_id=answer_id, chunks=citations)
        citation_chunks = []
        if citations and retrieved_chunks:
            chunks_by_id = {chunk.get("chunkId"): chunk for chunk in retrieved_chunks if chunk.get("chunkId")}
            for citation in citations:
                chunk = chunks_by_id.get(citation.get("chunkId"))
                if chunk:
                    citation_chunks.append(chunk)
        provenance_ids = persist_evidence_provenance(
            question_event=event,
            answer_id=answer_id,
            chunks=citation_chunks,
            semantic_query=semantic_query,
            graph_trace=graph_trace,
            rule_result=rule_result,
        )
        event.retrieval_event_ids = persisted_retrieval_ids
        event.evidence_link_ids = evidence_link_ids
        event.save(update_fields=["retrieval_event_ids", "evidence_link_ids", "updated_at"])

        partial_evidence = _classify_partial_evidence(
            mode=mode,
            abstained=abstained,
            confidence=confidence,
            chunks=retrieved_chunks,
            graph_trace=graph_trace,
            effective_scope=effective_scope,
        )
        cross_standard_analysis = _build_cross_standard_analysis(
            mode=mode,
            effective_scope=effective_scope,
            chunks=retrieved_chunks,
        )
        if partial_evidence["semanticProvisional"] and semantic_fallback is None:
            semantic_fallback = "PARTIAL_EVIDENCE"

        trace_response = {
            "requestId": request_id,
            "questionEventId": str(event.id),
            "matchedFaqEntryId": matched_faq_entry_id,
            "retrievalEventIds": persisted_retrieval_ids,
            "searchTranslation": english_question,
            "evidenceLinkIds": evidence_link_ids,
            "graphExpansionHops": graph_trace["graphExpansionHops"],
            "graphConceptIds": graph_trace["graphConceptIds"],
            "graphEvidenceCount": graph_trace["graphEvidenceCount"],
            "graphScoreContribution": graph_trace["graphScoreContribution"],
            "exampleChunksAdded": graph_trace.get("exampleChunksAdded", 0),
            "ontologyDefinitionsAdded": graph_trace.get("ontologyDefinitionsAdded", 0),
            "repositoryCoverageCount": graph_trace.get("repositoryCoverageCount", 0),
            "conceptCoverageCount": graph_trace.get("conceptCoverageCount", 0),
            "semanticAlignmentScore": graph_trace.get("semanticAlignmentScore", 0.0),
            "provenanceIds": provenance_ids,
            "ruleHitsCount": rule_result["matchedRuleCount"],
            "ruleConclusions": rule_result["conclusions"],
            "ontologyVersions": ontology_versions,
            "semanticQuery": semantic_query_dict,
            "semanticDisambiguationRequired": semantic_disambiguation_required,
            "semanticDisambiguationPrompt": semantic_disambiguation_prompt,
            "semanticFallback": semantic_fallback,
            "semanticProvisional": partial_evidence["semanticProvisional"],
            "semanticProvisionalReason": partial_evidence["semanticProvisionalReason"],
            "evidenceCoverageLevel": partial_evidence["evidenceCoverageLevel"],
            "crossStandardConflict": cross_standard_analysis["crossStandardConflict"],
            "crossStandardConflictType": cross_standard_analysis["crossStandardConflictType"],
            "crossStandardEvidencePartitions": cross_standard_analysis["crossStandardEvidencePartitions"],
            "userLikes": event.user_likes,
            "userDislikes": event.user_dislikes,
            "answerSuccess": event.answer_success,
            "citationClickCount": event.citation_click_count,
            "llmRejectedAnswer": (generated.get("rejected_answer") if isinstance(locals().get("generated"), dict) else None),
            "llmRejectionReason": (generated.get("rejection_reason") if isinstance(locals().get("generated"), dict) else None),
            "llmDroppedAnswer": dropped_answer,
            "presenceEvidence": [c.get("sourcePath") for c in presence],
            # False when the answer was served although its retry failed validation too (it is then marked
            # for review); None when no LLM answer was generated.
            "llmAnswerValidated": (generated.get("answer_validated") if isinstance(locals().get("generated"), dict) else None),
            "generatedExample": generated_example,
            "schemaStructure": schema_structure,
            # Where the time went (services/request_timing.py): parse, all retrieval calls and model calls,
            # the last retrieval's stages, and the example's own lookup or generation time.
            "timingsMs": {
                **request_timing.snapshot(),
                "exampleMs": (generated_example or {}).get("generationMs"),
            },
            "retrievalLatencyMs": graph_trace.get("retrievalLatencyMs", 0.0),
            "retrievalStageTimingsMs": graph_trace.get("retrievalStageTimingsMs") or {},
        }

        # Persist trace to event
        event.trace = trace_response
        event.save(update_fields=["trace", "updated_at"])

        yield self._sse({
            "type": "done",
            "answer": {
                "answerId": answer_id,
                "mode": mode,
                "confidence": confidence,
                "answer": answer_text,
                "citations": citations,
                "legalContext": _legal_context(mode, effective_scope, question),
                "abstained": abstained,
                "abstentionReason": abstention_reason,
                "reviewRequired": review_required,
                "generatedExample": generated_example,
                "schemaStructure": schema_structure,
                "trace": trace_response,
            },
        })


class QuestionFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_id = _request_id(request)
        serializer = AnswerFeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        event = QuestionEvent.objects.filter(request_id=data["requestId"]).order_by("-created_at").first()
        if event is None:
            return _error_response(
                code="REQUEST_NOT_FOUND",
                message="requestId does not reference an existing question event.",
                request_id=request_id,
                http_status=status.HTTP_404_NOT_FOUND,
            )

        if "userLikes" in data:
            event.user_likes = bool(data.get("userLikes"))
        if "userDislikes" in data:
            event.user_dislikes = bool(data.get("userDislikes"))
        if "answerSuccess" in data:
            event.answer_success = data.get("answerSuccess")

        citation_clicks_delta = int(data.get("citationClicksDelta", 0))
        if citation_clicks_delta > 0:
            event.citation_click_count += citation_clicks_delta

        event.save(
            update_fields=[
                "user_likes",
                "user_dislikes",
                "answer_success",
                "citation_click_count",
                "updated_at",
            ]
        )

        return Response(
            {
                "requestId": event.request_id,
                "questionEventId": str(event.id),
                "userLikes": event.user_likes,
                "userDislikes": event.user_dislikes,
                "answerSuccess": event.answer_success,
                "citationClickCount": event.citation_click_count,
            },
            status=status.HTTP_200_OK,
        )


class QuestionEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        # Return persisted question events so editorial intake does not depend on the current tab session.
        serializer = QuestionEventsListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        queryset = QuestionEvent.objects.all()

        mode_value = data.get("mode")
        if mode_value:
            queryset = queryset.filter(mode=mode_value)

        review_required = data.get("reviewRequired", None)
        if review_required is not None:
            queryset = queryset.filter(review_required=review_required)

        user_likes = data.get("userLikes", None)
        if user_likes is not None:
            queryset = queryset.filter(user_likes=user_likes)

        user_dislikes = data.get("userDislikes", None)
        if user_dislikes is not None:
            queryset = queryset.filter(user_dislikes=user_dislikes)

        answer_success = data.get("answerSuccess", None)
        if answer_success is not None:
            queryset = queryset.filter(answer_success=answer_success)

        search = data.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(question__icontains=search)
                | Q(request_id__icontains=search)
                | Q(id__icontains=search)
            )

        page = data["page"]
        page_size = data["pageSize"]
        total = queryset.count()
        offset = (page - 1) * page_size
        items = list(queryset[offset: offset + page_size])

        return Response(
            {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "items": [
                    {
                        "question": item.question,
                        "askedAt": item.created_at.isoformat().replace("+00:00", "Z"),
                        "requestId": item.request_id,
                        "questionEventId": str(item.id),
                        "mode": item.mode,
                        "confidence": float(item.confidence),
                        "reviewRequired": bool(item.review_required),
                        "userLikes": bool(item.user_likes),
                        "userDislikes": bool(item.user_dislikes),
                        "answerSuccess": item.answer_success,
                    }
                    for item in items
                ],
            },
            status=status.HTTP_200_OK,
        )


class QuestionEventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_event_id):
        event = None
        # Try numeric ID first if it looks numeric
        if question_event_id.isdigit():
            try:
                event = QuestionEvent.objects.get(id=question_event_id)
            except QuestionEvent.DoesNotExist:
                pass

        # Try by request_id (req-...) if not found
        if not event:
            try:
                event = QuestionEvent.objects.get(request_id=question_event_id)
            except QuestionEvent.DoesNotExist:
                return Response(
                    {"error": {"code": "NOT_FOUND", "message": "Question event not found."}},
                    status=status.HTTP_404_NOT_FOUND,
                )

        citations = []
        for link in event.answer_evidence_links.all().order_by("created_at"):
            citations.append({
                "label": link.label or None,
                "sourcePath": link.source_path,
                # A stored link outside GitHub is already the final URL (a Transmodel class page)
                "repositoryUrl": (
                    link.repository_url
                    if link.repository_url.startswith("https://") and "github.com/" not in link.repository_url
                    else _build_file_url(link.repository_url, link.commit_sha, link.source_path)
                ),
                "chunkId": link.chunk_id,
                **_citation_title(link.source_path),
            })

        return Response(
            {
                "questionEventId": str(event.id),
                "requestId": event.request_id,
                "question": event.question,
                "answer": event.answer,
                "mode": event.mode,
                "confidence": float(event.confidence),
                "citations": citations,
                "legalContext": _legal_context(event.mode, event.standards_scope, event.question),
                "generatedExample": (event.trace or {}).get("generatedExample"),
                "schemaStructure": (event.trace or {}).get("schemaStructure"),
                "trace": event.trace or {},
                "createdAt": event.created_at.isoformat().replace("+00:00", "Z"),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, question_event_id):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        try:
            event = QuestionEvent.objects.get(id=question_event_id)
        except QuestionEvent.DoesNotExist:
            return Response(
                {"error": {"code": "NOT_FOUND", "message": "Question event not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrendingQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return top N questions by user likes, ordered by created_at descending
        limit = int(request.query_params.get("limit", 3))
        limit = min(limit, 10)  # Cap at 10 to prevent abuse

        items = QuestionEvent.objects.filter(user_likes=True).order_by("-created_at")[:limit]

        return Response(
            {
                "items": [
                    {
                        "question": item.question,
                        "answer": item.answer,
                        "askedAt": item.created_at.isoformat().replace("+00:00", "Z"),
                        "requestId": item.request_id,
                        "questionEventId": str(item.id),
                        "mode": item.mode,
                        "confidence": float(item.confidence),
                    }
                    for item in items
                ],
            },
            status=status.HTTP_200_OK,
        )


class PromotionCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        # Aggregate historical question events into candidate FAQ intents.
        serializer = PromotionCandidatesQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        window_days = data["windowDays"]
        min_count = data["minCount"]
        only_unresolved = data["onlyUnresolved"]
        since = timezone.now() - timedelta(days=window_days)

        events = QuestionEvent.objects.filter(created_at__gte=since)
        buckets = defaultdict(
            lambda: {
                "questionCount": 0,
                "lastAskedAt": None,
                "lastQuestionEventId": None,
                "unresolved": False,
            }
        )

        for event in events:
            # Lightweight intent normalization by whitespace + lowercase collapsing.
            intent = " ".join(event.question.lower().strip().split())
            bucket = buckets[intent]
            bucket["questionCount"] += 1
            if bucket["lastAskedAt"] is None or event.created_at >= bucket["lastAskedAt"]:
                bucket["lastAskedAt"] = event.created_at
                bucket["lastQuestionEventId"] = str(event.id)
            bucket["unresolved"] = bucket["unresolved"] or event.review_required or event.abstained

        items = []
        for intent, bucket in buckets.items():
            if only_unresolved and not bucket["unresolved"]:
                continue

            count = bucket["questionCount"]
            if count >= min_count:
                action = "CREATE_FAQ_DRAFT"
            elif count >= max(2, min_count // 2):
                action = "REVIEW_EXISTING_FAQ"
            else:
                action = "MONITOR"

            items.append(
                {
                    "questionEventId": bucket["lastQuestionEventId"],
                    "normalizedIntent": intent,
                    "questionCount": count,
                    "notHelpfulRate": 0.0,
                    "lastAskedAt": bucket["lastAskedAt"].isoformat().replace("+00:00", "Z"),
                    "recommendedAction": action,
                }
            )

        items.sort(key=lambda i: i["questionCount"], reverse=True)

        return Response(
            {
                "windowDays": window_days,
                "minCount": min_count,
                "items": items,
            },
            status=status.HTTP_200_OK,
        )


class EditorialSemanticClustersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        # Manual trigger endpoint for semantic clustering over recent question events.
        serializer = SemanticClustersQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = build_semantic_clusters(
            window_days=data["windowDays"],
            min_cluster_size=data["minClusterSize"],
            similarity_threshold=float(data["similarityThreshold"]),
            max_events=data["maxEvents"],
        )
        return Response(result, status=status.HTTP_200_OK)


class EditorialQueueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        # Return paginated board rows for editorial triage and state transitions.
        serializer = EditorialQueueListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        actor_roles = _request_roles(request)

        queryset = EditorialQueueItem.objects.select_related("question_event").all()

        status_value = data.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        reason = data.get("reason")
        if reason:
            queryset = queryset.filter(reason=reason)

        priority = data.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        search = data.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(question_event__question__icontains=search)
                | Q(question_event__request_id__icontains=search)
            )

        page = data["page"]
        page_size = data["pageSize"]
        total = queryset.count()
        offset = (page - 1) * page_size
        items = list(queryset[offset: offset + page_size])

        return Response(
            {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "actorRoles": sorted(actor_roles),
                "items": [
                    {
                        "queueItemId": str(item.queue_item_id),
                        "status": item.status,
                        "reason": item.reason,
                        "priority": item.priority,
                        "questionEventId": str(item.question_event_id),
                        "requestId": item.question_event.request_id,
                        "question": item.question_event.question,
                        "createdAt": item.created_at.isoformat().replace("+00:00", "Z"),
                        "updatedAt": item.updated_at.isoformat().replace("+00:00", "Z"),
                        "allowedActions": allowed_actions_for_status(
                            status=item.status,
                            actor_roles=actor_roles,
                        ),
                    }
                    for item in items
                ],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        # Route already-generated answers to editorial review queues.
        request_id = _request_id(request)
        serializer = EditorialQueueRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            question_event = QuestionEvent.objects.get(pk=data["questionEventId"])
        except QuestionEvent.DoesNotExist:
            return _error_response(
                code="QUESTION_EVENT_NOT_FOUND",
                message="questionEventId does not reference an existing event.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        item = route_to_editorial_queue({
            "question_event": question_event,
            "reason": data["reason"],
            "priority": data.get("priority", EditorialQueueItem.PRIORITY_NORMAL),
        })

        return Response(
            {
                "queued": True,
                "queueItemId": str(item.queue_item_id),
                "status": item.status,
            },
            status=status.HTTP_200_OK,
        )


class EditorialQueueTransitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Enforce workflow transitions with explicit role checks and audit trail creation.
        request_id = _request_id(request)
        serializer = EditorialQueueTransitionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            item = EditorialQueueItem.objects.get(queue_item_id=data["queueItemId"])
        except EditorialQueueItem.DoesNotExist:
            return _error_response(
                code="QUEUE_ITEM_NOT_FOUND",
                message="queueItemId does not reference an existing queue item.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        actor_roles = _request_roles(request)
        actor_id = _request_actor_id(request)

        try:
            with transaction.atomic():
                transition = apply_transition(
                    queue_item=item,
                    action=data["action"],
                    actor_id=actor_id,
                    actor_roles=actor_roles,
                    comment=data.get("comment", ""),
                )
                if item.status == EditorialQueueItem.STATUS_PUBLISHED:
                    publish_queue_item_to_faq(queue_item=item)
        except WorkflowTransitionNotAllowed as exc:
            return _error_response(
                code="INVALID_STATE_TRANSITION",
                message=str(exc),
                request_id=request_id,
                http_status=status.HTTP_409_CONFLICT,
            )
        except WorkflowTransitionForbidden as exc:
            return _error_response(
                code="TRANSITION_FORBIDDEN",
                message=str(exc),
                request_id=request_id,
                http_status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "queueItemId": str(item.queue_item_id),
                "status": item.status,
                "transition": {
                    "action": transition.action,
                    "fromStatus": transition.from_status,
                    "toStatus": transition.to_status,
                    "actorId": transition.actor_id,
                    "actorRoles": transition.actor_roles,
                },
            },
            status=status.HTTP_200_OK,
        )


class EditorialQueueMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        forbidden = _forbid_without_editorial_role(request)
        if forbidden:
            return forbidden
        # Compute queue health KPIs for board-level monitoring widgets.
        serializer = EditorialQueueMetricsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        window_days = data["windowDays"]
        sla_hours = data["slaHours"]
        now = timezone.now()
        since = now - timedelta(days=window_days)
        queryset = EditorialQueueItem.objects.filter(created_at__gte=since)

        by_status = {
            status_value: queryset.filter(status=status_value).count()
            for status_value, _ in EditorialQueueItem.STATUS_CHOICES
        }
        by_priority = {
            priority_value: queryset.filter(priority=priority_value).count()
            for priority_value, _ in EditorialQueueItem.PRIORITY_CHOICES
        }
        by_reason = {
            reason_value: queryset.filter(reason=reason_value).count()
            for reason_value, _ in EditorialQueueItem.REASON_CHOICES
        }

        unresolved = queryset.exclude(status=EditorialQueueItem.STATUS_PUBLISHED)
        overdue_threshold = now - timedelta(hours=sla_hours)
        overdue_count = unresolved.filter(created_at__lt=overdue_threshold).count()

        age_0_24 = unresolved.filter(created_at__gte=now - timedelta(hours=24)).count()
        age_24_72 = unresolved.filter(
            created_at__lt=now - timedelta(hours=24),
            created_at__gte=now - timedelta(hours=72),
        ).count()
        age_over_72 = unresolved.filter(created_at__lt=now - timedelta(hours=72)).count()
        # Feedback counters are computed from question events in the same window.
        feedback_window_events = QuestionEvent.objects.filter(created_at__gte=since)
        feedback_today_events = feedback_window_events.filter(created_at__gte=now - timedelta(hours=24))

        return Response(
            {
                "windowDays": window_days,
                "slaHours": sla_hours,
                "generatedAt": now.isoformat().replace("+00:00", "Z"),
                "totalItems": queryset.count(),
                "unresolvedItems": unresolved.count(),
                "overdueItems": overdue_count,
                "byStatus": by_status,
                "byPriority": by_priority,
                "byReason": by_reason,
                "agingBuckets": {
                    "lt24h": age_0_24,
                    "h24to72": age_24_72,
                    "gt72h": age_over_72,
                },
                "feedbackToday": {
                    "likes": feedback_today_events.filter(user_likes=True).count(),
                    "dislikes": feedback_today_events.filter(user_dislikes=True).count(),
                    "answerSuccess": feedback_today_events.filter(answer_success=True).count(),
                    "citationClicks": sum(item.citation_click_count for item in feedback_today_events),
                },
                "feedbackWindow": {
                    "likes": feedback_window_events.filter(user_likes=True).count(),
                    "dislikes": feedback_window_events.filter(user_dislikes=True).count(),
                    "answerSuccess": feedback_window_events.filter(answer_success=True).count(),
                    "citationClicks": sum(item.citation_click_count for item in feedback_window_events),
                },
            },
            status=status.HTTP_200_OK,
        )


def _forbid_without_index_role(request, request_id):
    """The error response for a caller who may not harvest or index, else None."""

    if _request_roles(request) & {"admin", "publisher"}:
        return None
    return _error_response(
        code="FORBIDDEN",
        message="Indexing requires admin or publisher role.",
        request_id=request_id,
        http_status=status.HTTP_403_FORBIDDEN,
    )


def _source_payload(source) -> dict:
    """A configured source as the editor's Harvest & Index tab lists it, with what is indexed now."""

    from helpdesk.models import OntologyAssetVersion, SourceChunk
    from helpdesk.services.repository_urls import canonical_repository_url

    chunks = SourceChunk.objects.filter(repository_url=canonical_repository_url(source.url))
    latest = chunks.order_by("-updated_at").values("commit_sha", "updated_at").first()
    ontology = None
    if source.ontology:
        record = OntologyAssetVersion.objects.filter(ontology_key=source.ontology.key).first()
        ontology = {
            "key": source.ontology.key,
            "graphUri": source.ontology.graph_uri,
            "version": record.version if record else None,
            "lastLoadedAt": record.last_loaded_at.isoformat() if record and record.last_loaded_at else None,
        }
    return {
        "name": source.name,
        "repositoryUrl": source.url,
        "profile": source.profile,
        "checkoutPresent": (Path(settings.SOURCE_CHECKOUT_DIR) / source.name / ".git").is_dir(),
        "indexedChunks": chunks.count(),
        "indexedCommit": latest["commit_sha"] if latest else None,
        "indexedAt": latest["updated_at"].isoformat() if latest else None,
        "ontology": ontology,
    }


class SourcesView(APIView):
    """The sources the knowledge base is harvested from (services/source_refresh.configured_sources)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from helpdesk.services.source_refresh import configured_sources

        request_id = _request_id(request)
        forbidden = _forbid_without_index_role(request, request_id)
        if forbidden:
            return forbidden
        return Response(
            {"requestId": request_id, "sources": [_source_payload(source) for source in configured_sources()]},
            status=status.HTTP_200_OK,
        )


class HarvestSourceView(APIView):
    """Queue a harvest of one configured source: fetch, index, and load its ontology (tasks.harvest_source).

    It runs in the Celery worker: a full index takes minutes, longer than the proxy in front of the API waits.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from helpdesk.services.source_refresh import find_source
        from helpdesk.tasks import harvest_source

        request_id = _request_id(request)
        forbidden = _forbid_without_index_role(request, request_id)
        if forbidden:
            return forbidden
        serializer = HarvestSourceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = find_source(serializer.validated_data["source"])
        if source is None:
            return _error_response(
                code="UNKNOWN_SOURCE",
                message=f"No configured source named {serializer.validated_data['source']!r}.",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        job = harvest_source.delay(source.name, full=serializer.validated_data["full"])
        return Response(
            {"requestId": request_id, "jobId": job.id, "source": source.name, "state": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )


_HARVEST_STATES = {"PENDING": "queued", "RECEIVED": "queued", "STARTED": "running", "RETRY": "running"}


class HarvestJobView(APIView):
    """State of a queued harvest; the result is the refresh report (one row per source)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, job_id: str):
        from celery.result import AsyncResult

        request_id = _request_id(request)
        forbidden = _forbid_without_index_role(request, request_id)
        if forbidden:
            return forbidden
        job = AsyncResult(job_id)
        payload = {"requestId": request_id, "jobId": job_id, "result": None, "error": None}
        if job.state == "SUCCESS":
            payload.update(state="finished", result=job.result)
        elif job.state in {"FAILURE", "REVOKED"}:
            payload.update(state="error", error=str(job.result))
        else:
            payload["state"] = _HARVEST_STATES.get(job.state, "running")
        return Response(payload, status=status.HTTP_200_OK)


class IndexRepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Trigger a source repository ingestion run against an already-cloned local path."""
        from pathlib import Path

        request_id = _request_id(request)

        # Restrict to admin or publisher roles to prevent accidental re-indexing.
        actor_roles = _request_roles(request)
        if not (actor_roles & {"admin", "publisher"}):
            return _error_response(
                code="FORBIDDEN",
                message="Indexing requires admin or publisher role.",
                request_id=request_id,
                http_status=status.HTTP_403_FORBIDDEN,
            )

        serializer = IndexRepositoryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        repo_url = data["repoUrl"].strip()
        repo_path = Path(data["repoPath"]).expanduser().resolve()
        auto_allow_repository = bool(data.get("autoAllowRepository", True))

        if not repo_path.exists() or not repo_path.is_dir():
            return _error_response(
                code="INVALID_REPO_PATH",
                message=f"repoPath does not exist or is not a directory: {repo_path}",
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional convenience for operators: add repository URL to in-process allow-list.
        allowed_repositories = set(settings.ALLOWED_SOURCE_REPOSITORIES)
        auto_allowed = False
        if auto_allow_repository and repo_url not in allowed_repositories:
            allowed_repositories.add(repo_url)
            settings.ALLOWED_SOURCE_REPOSITORIES = allowed_repositories
            auto_allowed = True

        try:
            stats = index_repository(
                repo_url=repo_url,
                repo_path=repo_path,
                allowed_repositories=allowed_repositories,
                profile=data["profile"],
                incremental=data["incremental"],
                prune=data["prune"],
                include_issues=bool(data.get("includeIssues", False)),
                github_token=settings.GITHUB_API_TOKEN or None,
                github_verify_ssl=settings.GITHUB_API_VERIFY_SSL,
                github_ca_bundle=settings.GITHUB_CA_BUNDLE,
            )
        except ValueError as exc:
            return _error_response(
                code="INDEX_ERROR",
                message=str(exc),
                request_id=request_id,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "ok",
                "requestId": request_id,
                "repositoryUrl": repo_url,
                "repositoryPath": str(repo_path),
                "profile": data["profile"],
                "incremental": data["incremental"],
                "prune": data["prune"],
                "autoAllowedRepository": auto_allowed,
                "scannedFiles": stats.scanned_files,
                "skippedFiles": stats.skipped_files,
                "createdChunks": stats.created_chunks,
                "updatedChunks": stats.updated_chunks,
                "deletedChunks": stats.deleted_chunks,
            },
            status=status.HTTP_200_OK,
        )
