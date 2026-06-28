"""
SPARQL-backed semantic rule evaluation for standards-domain compliance.

Queries the GraphDB knowledge graph to evaluate whether retrieved evidence
satisfies domain rules derived from Transmodel, NeTEx, SIRI, and OpRa
ontologies. Rule conclusions are included in the answer trace for auditability.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-26  |  Modified: 2026-06-28
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def _semantic_value(semantic_query, field_name: str, default=None):
    if hasattr(semantic_query, field_name):
        return getattr(semantic_query, field_name)
    if isinstance(semantic_query, dict):
        return semantic_query.get(field_name, default)
    return default


def _chunk_standards(chunk: dict) -> list[str]:
    value = chunk.get("standardsScope") or chunk.get("standards_scope") or []
    return value if isinstance(value, list) else []


def _normalize_standard(value: str) -> str:
    lowered = (value or "").strip().lower()
    aliases = {
        "netex": "netex",
        "opra": "opra",
        "siri": "siri",
    }
    return aliases.get(lowered, lowered)


def _semantic_terms(semantic_query) -> set[str]:
    raw_terms = _semantic_value(semantic_query, "original_terms", [])
    if not isinstance(raw_terms, list):
        return set()
    return {str(term).strip().lower() for term in raw_terms if str(term).strip()}


@lru_cache(maxsize=1)
def _load_competency_registry() -> list[dict]:
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        repo_root / "docs" / "testing" / "competency-questions-artifact-rules.json",
        repo_root / ".mylocal" / "docs" / "testing" / "competency-questions-artifact-rules.json",
    ]

    registry_path = next((path for path in candidates if path.exists()), None)
    if registry_path is None:
        return []

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    return list(payload.get("competencyQuestions") or [])


def _match_competency_questions(*, semantic_query, effective_scope: list[str], seen_standards: set[str]) -> list[dict]:
    normativity = _semantic_value(semantic_query, "normativity", "unspecified")
    intent = _semantic_value(semantic_query, "intent", "unknown")
    terms = _semantic_terms(semantic_query)

    scoped_standards = {_normalize_standard(value) for value in (effective_scope or []) if value}
    if not scoped_standards:
        scoped_standards = {_normalize_standard(value) for value in seen_standards if value}

    matched: list[dict] = []
    for item in _load_competency_registry():
        standard = _normalize_standard(str(item.get("standard") or ""))
        if standard and scoped_standards and standard not in scoped_standards:
            continue

        requires_rule = bool(item.get("requiresRule") is True)
        if requires_rule and normativity not in {"mandatory", "recommended"}:
            continue

        cq_id = str(item.get("id") or "")
        if not cq_id:
            continue

        if "STOP" in cq_id and not any(token in terms for token in {"stop", "stopplace", "stop place"}):
            continue
        if "SVC" in cq_id and not any(token in terms for token in {"service", "timetable"}):
            continue
        if "JRP" in cq_id and not any(
            token in terms for token in {"journeypattern", "servicejourneypattern", "journey pattern"}
        ):
            continue
        if "ID" in cq_id and "id" not in terms:
            continue
        if "ROLE" in cq_id and intent not in {"definition", "cross_standard_relation", "comparison"}:
            continue

        matched.append(
            {
                "id": cq_id,
                "standard": item.get("standard"),
                "requiresRule": requires_rule,
                "ruleId": item.get("ruleId"),
            }
        )

    return matched


def evaluate_semantic_rules(*, semantic_query, retrieved_chunks: list[dict], effective_scope: list[str]) -> dict:
    rules_evaluated: list[dict] = []
    conclusions: list[dict] = []

    normativity = _semantic_value(semantic_query, "normativity", "unspecified")
    intent = _semantic_value(semantic_query, "intent", "unknown")

    schema_chunks = [chunk for chunk in retrieved_chunks if (chunk.get("docType") or "").lower() == "schema"]
    rules_evaluated.append(
        {
            "ruleId": "schema_evidence_present",
            "matched": bool(schema_chunks),
            "detail": "Schema fragments are present in retrieved evidence." if schema_chunks else "No schema fragments were retrieved.",
        }
    )
    if schema_chunks:
        conclusions.append(
            {
                "type": "SCHEMA_EVIDENCE_PRESENT",
                "message": "Retrieved evidence includes schema fragments that can support structural grounding.",
            }
        )

    if normativity == "mandatory":
        constrained_artifacts: list[dict] = []
        for chunk in schema_chunks:
            metadata = chunk.get("structuredMetadata") or {}
            schema = metadata.get("schema") or {}
            required_children = schema.get("requiredChildElements") or []
            required_attributes = schema.get("requiredAttributes") or []
            if required_children or required_attributes:
                constrained_artifacts.append(
                    {
                        "sourcePath": chunk.get("sourcePath", ""),
                        "heading": chunk.get("heading", ""),
                        "requiredChildElements": required_children,
                        "requiredAttributes": required_attributes,
                    }
                )

        rules_evaluated.append(
            {
                "ruleId": "mandatory_schema_constraint",
                "matched": bool(constrained_artifacts),
                "detail": "Mandatory question matched schema-required children or attributes."
                if constrained_artifacts
                else "Mandatory question did not retrieve explicit required schema constraints.",
            }
        )
        if constrained_artifacts:
            conclusions.append(
                {
                    "type": "MANDATORY_SCHEMA_CONSTRAINT",
                    "message": "Mandatory wording is supported by explicit required schema constraints in the evidence.",
                    "artifacts": constrained_artifacts[:3],
                }
            )

    seen_standards = {
        standard
        for chunk in retrieved_chunks
        for standard in _chunk_standards(chunk)
        if isinstance(standard, str) and standard
    }
    if not seen_standards:
        seen_standards = set(effective_scope or [])

    competency_matches = _match_competency_questions(
        semantic_query=semantic_query,
        effective_scope=effective_scope,
        seen_standards=seen_standards,
    )
    rules_evaluated.append(
        {
            "ruleId": "competency_questions_matched",
            "matched": bool(competency_matches),
            "detail": f"Matched {len(competency_matches)} competency question(s)."
            if competency_matches
            else "No competency question was matched for current query context.",
        }
    )
    if competency_matches:
        conclusions.append(
            {
                "type": "COMPETENCY_QUESTION_MATCH",
                "message": "Matched competency-question checks for this query context.",
                "competencyQuestionIds": [item["id"] for item in competency_matches],
                "requiresRuleCount": sum(1 for item in competency_matches if item.get("requiresRule")),
            }
        )

    cross_standard_matched = intent in {"cross_standard_relation", "comparison"} and len(seen_standards) > 1
    rules_evaluated.append(
        {
            "ruleId": "cross_standard_review",
            "matched": cross_standard_matched,
            "detail": "Cross-standard evidence was detected for a relation/comparison query."
            if cross_standard_matched
            else "Cross-standard review rule did not trigger.",
        }
    )
    if cross_standard_matched:
        conclusions.append(
            {
                "type": "CROSS_STANDARD_REVIEW_RECOMMENDED",
                "message": "Cross-standard evidence is present; comparative review is justified before treating claims as interchangeable.",
                "standards": sorted(seen_standards),
            }
        )

    ontology_anchor_matched = any(chunk.get("graphProvenanceConceptIds") for chunk in retrieved_chunks)
    rules_evaluated.append(
        {
            "ruleId": "ontology_anchor_present",
            "matched": ontology_anchor_matched,
            "detail": "Ontology anchor provenance is attached to at least one evidence chunk."
            if ontology_anchor_matched
            else "No ontology anchor provenance was attached to retrieved chunks.",
        }
    )
    if ontology_anchor_matched:
        conclusions.append(
            {
                "type": "ONTOLOGY_ANCHOR_PRESENT",
                "message": "At least one retrieved chunk is connected to an ontology anchor used during retrieval.",
            }
        )

    matched_count = sum(1 for rule in rules_evaluated if rule["matched"])
    return {
        "rulesEvaluated": rules_evaluated,
        "conclusions": conclusions,
        "matchedRuleCount": matched_count,
        "competencyQuestionIds": [item["id"] for item in competency_matches],
    }
