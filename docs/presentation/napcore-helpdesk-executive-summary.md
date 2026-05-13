# NAPCORE Helpdesk Executive Summary

## Objective
Build a trustworthy helpdesk for multimodal standards questions that provides practical answers with traceable sources and no hallucinated claims.

## System Context
The helpdesk serves a representative range of NAPCORE stakeholders:
- **NAP Manager**: manages a national access point and ensures data publisher compliance.
- **Transport Authority**: sets policy and oversees multimodal standards adoption.
- **Transport Operator**: publishes journey, stop, and timetable data using NeTEx, SIRI, or OpRa.
- **Road Authority**: publishes road network and traffic data using DATEX II.
- **Standards Implementer**: developer or engineer implementing NeTEx, SIRI, DATEX II, or OpRa integrations.
- **ITS System Integrator**: integrates across standards and deploys interoperability solutions.

All groups access a single shared helpdesk interface. The system maintains a strict knowledge boundary by only retrieving answers from approved GitHub repositories (especially NeTEx-CEN/NeTEx). If evidence is insufficient, the system abstains rather than speculating.

## Business Need
Standards implementers need fast, reliable guidance for topics such as NeTEx timetable exchange and Stop Place identifier design. Traditional documentation search is slow and inconsistent, while generic AI assistants risk uncited or incorrect answers.

## Proposed Solution
Implement a grounded helpdesk that can evolve from search to chat while preserving provenance:[^rag-fallback]
- Traditional keyword search remains useful for direct document lookup.
- FAQ-first grounded Q and A handles recurring questions with canonical answers.
- Editorial workflow and KPI views support governance and backlog promotion.
- Separate routed user and operator surfaces improve demonstration clarity and future product separation.
- Optional LLM-ready generation can be introduced without relaxing evidence controls.

## Evolution Path
- Stage 1: keyword search over approved repositories.
- Stage 2: simple FAQ-first and grounded Q and A interface.
- Stage 3: editorial, metrics, and promotion workflows for operating the helpdesk.
- Stage 4: chat session UX with deterministic and optional LLM-backed grounded generation.
- FAQ-first: return approved canonical answers when confidence is high.
- RAG fallback: retrieve evidence from approved GitHub repositories, then generate grounded answers with citations using deterministic templates (now) or LLM synthesis (when enabled).
- Abstention: if evidence is insufficient, return transparent insufficiency response instead of speculation.

## Scope
- Standards: Transmodel, NeTEx, SIRI, OpRa, DATEX II.
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
- Local run and testing guides
- RAG architecture design
- Updated C4 architecture diagrams
- Database model and migration schema
- PlantUML diagram source and render target
- Route-based frontend split (`/user`, `/operator`) and LLM-ready backend wiring

## Immediate Next Steps
1. Complete pilot testing across chat, editorial, and promotion workflows.
2. Evaluate grounded LLM mode against deterministic fallback behavior.
3. Refine companion repository ingestion profiles.
4. Use pilot evidence to decide production hardening priorities.

[^rag-fallback]: In a helpdesk or FAQ system, a RAG fallback (Retrieval‑Augmented Generation) happens when the system cannot find a good direct match (e.g., exact FAQ answer). It then falls back to RAG: retrieves the most relevant documents from approved sources, and generates an answer grounded in that retrieved context. The generation method depends on the profile: (1) **Deterministic mode** (now): uses pattern-matched templates adapted to the question, with confidence based on retrieval scores. (2) **LLM-ready mode** (future): feeds retrieved chunks to an LLM for synthesis. Both approaches prevent hallucination by grounding answers in real retrieved text.
