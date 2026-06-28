"""
Semantic parsing of natural-language questions into structured query objects.

Extracts intent, core concepts, normativity signals, and candidate standards
from a question string. The resulting SemanticQuery drives SPARQL rule
evaluation and retrieval scope filtering in downstream services.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-16  |  Modified: 2026-06-28
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from django.conf import settings

from helpdesk.services.graphdb_connector import GraphDBConnector
from helpdesk.services.semantic_graph import (
    expand_graph_concepts,
    extract_graph_concepts,
    get_concept_nits_ids,
)

_IDENTIFIER_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9]{2,}\b")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_MAX_CORE_CONCEPT_CANDIDATES = 6

_LOW_VALUE_TOKENS = {
    "show",
    "give",
    "tell",
    "what",
    "where",
    "when",
    "which",
    "with",
    "from",
    "into",
    "this",
    "that",
    "please",
}

_STANDARD_BY_NAMESPACE = {
    "netex": "NeTEx",
    "opra": "OpRa",
    "siri": "SIRI",
    "transmodel": "Transmodel",
}

_INTENT_PATTERNS = {
    "normative_status": [r"\bshall\b", r"\bmust\b", r"\bshould\b", r"\bmay\b"],
    "definition": [r"\bwhat is\b", r"\bdefine\b", r"\bmeaning of\b"],
    "location": [r"\bwhere\b", r"\bin which\b", r"\bwhich file\b"],
    "cross_standard_relation": [r"\brelate\b", r"\bcross[- ]standard\b", r"\bbetween\b"],
    "comparison": [r"\bcompare\b", r"\bdifference\b", r"\bvs\b", r"\bversus\b"],
}


@dataclass(frozen=True)
class SemanticQuery:
    intent: str
    normativity: str
    core_concept: str
    core_concepts: list[str]
    ambiguous_core_concept: bool
    candidate_standards: list[str]
    original_terms: list[str]
    confidence: dict[str, float]

    def as_dict(self) -> dict:
        return {
            "intent": self.intent,
            "normativity": self.normativity,
            "coreConcept": self.core_concept,
            "coreConcepts": self.core_concepts,
            "ambiguousCoreConcept": self.ambiguous_core_concept,
            "candidateStandards": self.candidate_standards,
            "originalTerms": self.original_terms,
            "confidence": self.confidence,
        }


class QuestionParsingService:
    """Deterministic semantic preprocessing before retrieval and generation.

    This service intentionally avoids statistical NLP steps and instead uses
    controlled normalization, rule-first intent detection, and ontology-driven
    concept extraction.
    """

    def parse(self, text: str, requested_scope: list[str] | None = None) -> SemanticQuery:
        normalized = self._normalize_text(text)
        intent = self._detect_intent(normalized)
        normativity = self._detect_normativity(normalized)

        direct_concepts = extract_graph_concepts(normalized)
        expanded_concepts = expand_graph_concepts(direct_concepts, hops=1)
        all_concepts = direct_concepts | expanded_concepts

        original_terms = self._extract_original_terms(normalized)
        graphdb_core_concepts = self._anchor_with_graphdb(original_terms)
        raw_core_concepts = graphdb_core_concepts or self._anchor_candidates_to_nits(all_concepts)
        core_concepts = self._rank_and_cap_core_concepts(raw_core_concepts, normalized)
        core_concept = core_concepts[0] if core_concepts else "nits:unknown-concept"
        ambiguous_core_concept = len(core_concepts) > 1
        candidate_standards = self._discover_standards(
            concept_ids=all_concepts,
            requested_scope=requested_scope,
            core_concepts=core_concepts,
        )

        concept_confidence = self._concept_confidence(core_concepts)
        intent_confidence = self._intent_confidence(intent=intent, requested_scope=requested_scope)
        confidence = {
            "intent": intent_confidence,
            "concept": concept_confidence,
        }

        return SemanticQuery(
            intent=intent,
            normativity=normativity,
            core_concept=core_concept,
            core_concepts=core_concepts,
            ambiguous_core_concept=ambiguous_core_concept,
            candidate_standards=candidate_standards,
            original_terms=original_terms,
            confidence=confidence,
        )

    def _normalize_text(self, text: str) -> str:
        canonical = unicodedata.normalize("NFKC", text or "")
        canonical = canonical.replace("\u00a0", " ")
        return _WHITESPACE_PATTERN.sub(" ", canonical).strip()

    def _detect_intent(self, text: str) -> str:
        lowered = text.lower()
        for intent, patterns in _INTENT_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns):
                return intent
        return "unknown"

    def _detect_normativity(self, text: str) -> str:
        lowered = text.lower()
        if re.search(r"\b(shall|must|required)\b", lowered):
            return "mandatory"
        if re.search(r"\bshould\b", lowered):
            return "recommended"
        if re.search(r"\bmay\b", lowered):
            return "optional"
        return "unspecified"

    def _extract_original_terms(self, text: str) -> list[str]:
        # Keep important identifier-like terms (e.g., NeTEx, ServiceJourneyPattern)
        # but also include meaningful lowercase intent tokens such as line/stop/example.
        ordered_terms: list[str] = []
        seen: set[str] = set()

        for token in _IDENTIFIER_PATTERN.findall(text):
            normalized = token.strip()
            key = normalized.lower()
            if key in _LOW_VALUE_TOKENS:
                continue
            if normalized and key not in seen:
                ordered_terms.append(normalized)
                seen.add(key)

        for token in re.split(r"[^A-Za-z0-9]+", text):
            normalized = token.strip()
            if len(normalized) < 4:
                continue
            key = normalized.lower()
            if key in _LOW_VALUE_TOKENS:
                continue
            if key not in seen:
                ordered_terms.append(normalized)
                seen.add(key)

        return ordered_terms[:12]

    def _rank_and_cap_core_concepts(self, core_concepts: list[str], text: str) -> list[str]:
        if not core_concepts:
            return []

        question_tokens = set(_TOKEN_PATTERN.findall(text.lower()))

        def score(candidate: str) -> tuple[int, int, int]:
            local = candidate.split(":", 1)[-1].lower()
            local_tokens = set(_TOKEN_PATTERN.findall(local.replace("-", " ").replace("_", " ")))
            overlap = len(question_tokens.intersection(local_tokens))
            substring_hit = 1 if local and local in text.lower() else 0
            # Prefer shorter canonical IDs when all else is equal.
            return (overlap, substring_hit, -len(local))

        ranked = sorted(set(core_concepts), key=score, reverse=True)
        return ranked[:_MAX_CORE_CONCEPT_CANDIDATES]

    def _concept_confidence(self, core_concepts: list[str]) -> float:
        if not core_concepts:
            return 0.45
        if len(core_concepts) == 1:
            return 0.95
        if len(core_concepts) <= 3:
            return 0.78
        return 0.62

    def _intent_confidence(self, intent: str, requested_scope: list[str] | None) -> float:
        if intent == "unknown":
            return 0.6
        if not requested_scope and intent in {"cross_standard_relation", "comparison"}:
            return 0.85
        return 0.9

    def _anchor_candidates_to_nits(self, concept_ids: set[str]) -> list[str]:
        nits_ids = sorted(get_concept_nits_ids(concept_ids))
        if not nits_ids:
            return []
        return [f"nits:{nits_id.split(':', 1)[-1]}" for nits_id in nits_ids]

    def _discover_standards(
        self,
        concept_ids: set[str],
        requested_scope: list[str] | None,
        core_concepts: list[str],
    ) -> list[str]:
        if requested_scope:
            return list(dict.fromkeys(requested_scope))

        graphdb_standards = self._discover_standards_with_graphdb(core_concepts)
        if graphdb_standards:
            return graphdb_standards

        discovered: list[str] = []
        for concept_id in sorted(concept_ids):
            namespace = concept_id.split(":", 1)[0].lower() if ":" in concept_id else ""
            standard = _STANDARD_BY_NAMESPACE.get(namespace)
            if standard and standard not in discovered:
                discovered.append(standard)
        return discovered

    def _graphdb_connector(self) -> GraphDBConnector | None:
        if not getattr(settings, "GRAPHDB_ENABLED", False):
            return None
        endpoint = getattr(settings, "GRAPHDB_SPARQL_ENDPOINT", "").strip()
        if not endpoint:
            return None
        return GraphDBConnector(
            endpoint_url=endpoint,
            repository=getattr(settings, "GRAPHDB_REPOSITORY", ""),
            timeout_seconds=getattr(settings, "GRAPHDB_TIMEOUT_SECONDS", 5),
        )

    def _anchor_with_graphdb(self, original_terms: list[str]) -> list[str]:
        connector = self._graphdb_connector()
        if connector is None:
            return []

        discovered: list[str] = []
        for term in original_terms:
            for iri in connector.anchor_term_to_core_concepts(term):
                if not iri:
                    continue
                # Present GraphDB anchors in the app core namespace expected by runtime trace.
                local = iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                candidate = iri if iri.startswith("nits:") else f"nits:{local}"
                if candidate not in discovered:
                    discovered.append(candidate)
                if len(discovered) >= _MAX_CORE_CONCEPT_CANDIDATES:
                    return discovered
        return discovered

    def _discover_standards_with_graphdb(self, core_concepts: list[str]) -> list[str]:
        connector = self._graphdb_connector()
        if connector is None:
            return []

        discovered: list[str] = []
        namespace_base = "https://napcore.eu/ontology/nits#"
        for core_concept in core_concepts:
            if not core_concept.startswith("nits:"):
                continue
            local = core_concept.split(":", 1)[1]
            iri = f"{namespace_base}{local}"
            standards = connector.discover_standards_for_core_concept(iri)
            if not standards:
                standards = connector.discover_standards_for_core_concept_slug(local)

            for standard in standards:
                normalized = standard.strip()
                if normalized and normalized not in discovered:
                    discovered.append(normalized)
        return discovered


def parse_question_to_semantic_query(text: str, requested_scope: list[str] | None = None) -> SemanticQuery:
    return QuestionParsingService().parse(text=text, requested_scope=requested_scope)
