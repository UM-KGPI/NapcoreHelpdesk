"""
Persists provenance chains linking answer evidence to ontology versions and rule conclusions.

Records which ontology assets and rule derivations contributed to each
AnswerEvidenceLink, enabling full auditability of how an answer was constructed.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-04-26  |  Modified: 2026-06-28
"""

from __future__ import annotations

from helpdesk.models import AnswerEvidenceLink, EvidenceProvenance, QuestionEvent
from helpdesk.services.ontology_registry import current_ontology_version_payload


def persist_evidence_provenance(
    *,
    question_event: QuestionEvent,
    answer_id: str,
    chunks: list[dict],
    semantic_query,
    graph_trace: dict,
    rule_result: dict,
) -> list[str]:
    ontology_versions = current_ontology_version_payload()
    provenance_ids: list[str] = []

    core_concepts = []
    if hasattr(semantic_query, "core_concepts"):
        core_concepts = list(getattr(semantic_query, "core_concepts") or [])
    elif isinstance(semantic_query, dict):
        core_concepts = list(semantic_query.get("core_concepts") or semantic_query.get("coreConcepts") or [])

    for index, chunk in enumerate(chunks):
        evidence_link_id = f"el-{answer_id}-{index + 1}"
        try:
            evidence_link = AnswerEvidenceLink.objects.get(
                evidence_link_id=evidence_link_id,
                question_event=question_event,
            )
        except AnswerEvidenceLink.DoesNotExist:
            continue

        provenance_id = f"prov-{answer_id}-{index + 1}"
        payload = {
            "repositoryUrl": chunk.get("repositoryUrl", ""),
            "sourcePath": chunk.get("sourcePath", ""),
            "chunkId": chunk.get("chunkId", ""),
            "graphProvenanceConceptIds": chunk.get("graphProvenanceConceptIds", []),
            "competencyQuestionIds": rule_result.get("competencyQuestionIds", []),
            "structuredMetadata": chunk.get("structuredMetadata", {}),
            "graphTrace": {
                "graphConceptIds": graph_trace.get("graphConceptIds", []),
                "graphExpansionSource": graph_trace.get("graphExpansionSource", "none"),
                "graphExpansionHops": graph_trace.get("graphExpansionHops", 0),
            },
        }
        EvidenceProvenance.objects.update_or_create(
            provenance_id=provenance_id,
            defaults={
                "question_event": question_event,
                "evidence_link": evidence_link,
                "core_concepts": core_concepts,
                "ontology_versions": ontology_versions,
                "rule_conclusions": rule_result.get("conclusions", []),
                "provenance_payload": payload,
            },
        )
        provenance_ids.append(provenance_id)

    return provenance_ids
