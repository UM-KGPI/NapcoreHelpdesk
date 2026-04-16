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

_STANDARD_BY_NAMESPACE = {
    "netex": "NeTEx",
    "opra": "OpRa",
    "siri": "SIRI",
    "ojp": "OJP",
    "datex": "DATEX II",
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
        core_concepts = graphdb_core_concepts or self._anchor_candidates_to_nits(all_concepts)
        core_concept = core_concepts[0] if core_concepts else "nits:unknown-concept"
        ambiguous_core_concept = len(core_concepts) > 1
        candidate_standards = self._discover_standards(
            concept_ids=all_concepts,
            requested_scope=requested_scope,
            core_concepts=core_concepts,
        )

        confidence = {
            "intent": 0.9 if intent != "unknown" else 0.6,
            "concept": 0.95 if all_concepts else 0.45,
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
        terms = sorted(set(_IDENTIFIER_PATTERN.findall(text)))
        if terms:
            return terms[:12]
        tokens = [token for token in re.split(r"[^A-Za-z0-9]+", text) if len(token) > 3]
        return sorted(set(tokens[:12]))

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
            iri = f"{namespace_base}{core_concept.split(':', 1)[1]}"
            for standard in connector.discover_standards_for_core_concept(iri):
                normalized = standard.strip()
                if normalized and normalized not in discovered:
                    discovered.append(normalized)
        return discovered


def parse_question_to_semantic_query(text: str, requested_scope: list[str] | None = None) -> SemanticQuery:
    return QuestionParsingService().parse(text=text, requested_scope=requested_scope)
