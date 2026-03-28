# NAPCORE Helpdesk Executive Summary

## Objective
Build a trustworthy helpdesk for multimodal standards questions that provides practical answers with traceable sources and no hallucinated claims.

## System Context
The helpdesk serves five key stakeholder groups:
- **PTO (Public Transport Operator)**: responsible for daily service delivery.
- **PTA (Public Transport Authority)**: sets policy and standards compliance.
- **Developer**: implements integration and APIs.
- **ITS System Integrator**: connects helpdesk to broader mobility ecosystem.
- **Ticketing Agent**: handles passenger-facing systems.

All groups access a single shared helpdesk interface. The system maintains a strict knowledge boundary by only retrieving answers from approved GitHub repositories (especially NeTEx-CEN/NeTEx). If evidence is insufficient, the system abstains rather than speculating.

## Business Need
Standards implementers need fast, reliable guidance for topics such as NeTEx timetable exchange and Stop Place identifier design. Traditional documentation search is slow and inconsistent, while generic AI assistants risk uncited or incorrect answers.

## Proposed Solution
Implement a GUI-based helpdesk using FAQ-first with RAG fallback:[^rag-fallback]
- FAQ-first: return approved canonical answers when confidence is high.
- RAG fallback: retrieve evidence from approved GitHub repositories, then generate grounded answers with citations.
- Abstention: if evidence is insufficient, return transparent insufficiency response instead of speculation.

## Scope
- Standards: Transmodel, NeTEx, SIRI, OJP/OpRa, DATEX II.
- Priority source: NeTEx-CEN/NeTEx plus approved companion repositories.
- Users: developers and implementers asking technical integration questions.

## Trust And Governance
- Knowledge boundary enforced by repository allowlist.
- Publication guardrails: no answer without citations.
- Editorial workflow: draft, review, approve, publish (operated in Django Admin).
- Auditability: answers linked to source chunks through evidence records.

## Data And Architecture Snapshot
- Source pipeline: approved_repositories -> source_documents -> source_chunks.
- FAQ pipeline: faq_entries -> faq_versions -> review_events.
- Runtime telemetry: question_events -> retrieval_events.
- Evidence integrity: answer_evidence_links maps claims to source chunks.
- Implementation baseline: Django 5 + DRF API + Django Admin + Celery/Redis workers.

## MVP Success Criteria
- 100 percent citation coverage for published FAQs.
- 0 percent unsupported-claim publication rate.
- P95 response latency <= 8 seconds.
- Retrieval success >= 90 percent for covered intents.

## Current Readiness
Core artifacts are prepared:
- Functional requirements
- RAG architecture design
- Database model and migration schema
- PlantUML diagram source and render target

## Immediate Next Steps
1. Finalize approved repository allowlist and ingestion profile.
2. Implement Django/DRF FAQ-first orchestration plus RAG fallback API.
3. Configure Django Admin editorial workflow and publication gates.
4. Run pilot scenarios and measure KPI targets.

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks and then generates an answer grounded in that retrieved evidence.
