---
title: "NAPCORE Helpdesk: Trusted FAQ + RAG Architecture"
subtitle: "Presentation Draft"
author: "NAPCORE Helpdesk Team"
date: "2026-03-28"
lang: "en"
colorlinks: true
---

# Problem And Goal

- Need a trustworthy helpdesk for multimodal standards implementation.
- Main risk is hallucinated or uncited AI guidance.
- Goal is grounded answers with traceable references.

# System Context (C4 Level 1)

**Five stakeholder groups share one helpdesk interface:**

- PTO (Public Transport Operator) — responsible for daily service delivery
- PTA (Public Transport Authority) — sets policy and compliance standards
- Developer — implements integrations and APIs
- ITS System Integrator — connects helpdesk to broader mobility ecosystem
- Ticketing Agent — manages passenger-facing systems

**External systems:**

- Approved GitHub repositories (NeTEx-CEN/NeTEx) — knowledge source
- LLM provider — grounded generation only; no unconstrained model memory

**Key architectural constraint:**

- All answers sourced from approved repositories only.
- If evidence is insufficient, the system abstains rather than speculating.

![C4 System Context Diagram](docs/architecture/c4-system-context.png)

# Scope

- Standards: Transmodel, NeTEx, SIRI, OJP/OpRa, DATEX II.
- Priority source: NeTEx-CEN/NeTEx and approved companion repositories.
- User channel: GUI-based technical Q and A.

# Core Approach

- FAQ-first with RAG fallback.[^rag-fallback]
- FAQ-first: return approved canonical answers when confidence is high.
- RAG fallback: retrieve source chunks then generate grounded answer.
- If evidence is insufficient, abstain explicitly.

# Trust And Safety

- Repository allowlist enforces knowledge boundary.
- Generation limited to retrieved evidence.
- Citation gate blocks uncited publication.
- Editorial gate enforces draft, review, approve, publish states.

# Functional Requirements Highlights

- FR-001: developer question answering in GUI.
- FR-004: ingestion and indexing of approved GitHub sources.
- FR-005: retrieval and grounded generation.
- FR-006: anti-hallucination and boundary enforcement.
- FR-002 and FR-003: editorial curation and FAQ promotion.

# Data Model Logic

- Source governance: approved_repositories -> source_documents -> source_chunks.
- FAQ lifecycle: faq_entries -> faq_versions -> review_events.
- Runtime telemetry: question_events -> retrieval_events.
- Evidence mapping: answer_evidence_links ties answers to source chunks.

# Why Hallucinations Are Prevented

- Only approved repositories are retrievable.
- Unsupported claims fail citation and support checks.
- Evidence links provide claim-to-source traceability.
- Unknown questions produce abstention, not speculation.

# User Experience Flow

- User submits question in GUI.
- System attempts FAQ match first.
- On miss or low confidence, system executes RAG retrieval plus generation.
- Response includes references and confidence signal.
- Feedback is captured for continuous improvement.

# Operations And Governance

- Reviewer decisions are logged and auditable.
- Editorial operations run through Django Admin.
- Recurring intents are promoted into curated FAQ backlog.
- Re-indexing handles source and standards updates.
- Metrics monitor quality and safety continuously.

# MVP Success Metrics

- Citation coverage for published FAQs: 100%.
- Unsupported-claim publication rate: 0%.
- P95 latency: <= 8 seconds.
- Retrieval success on covered intents: >= 90%.

# Current Artifacts

- Functional requirements document.
- RAG architecture and database logic documents.
- Technology baseline: Django 5 + DRF + Django Admin + Celery/Redis.
- PlantUML database model and SQL migration.
- Diagram render target for reproducible outputs.

# Next Steps

1. Finalize repository allowlist and ingestion profile.
2. Implement Django/DRF orchestration API for FAQ-first plus RAG fallback.
3. Configure Django Admin editorial workflow and publication gates.
4. Run pilot validation against KPI targets.

# Appendix: Example Questions

- How to use NeTEx for exchanging a timetable?
- How to implement IDs for a Stop Place registry?

Expected outputs:
- practical implementation guidance,
- explicit citations,
- abstention where evidence is insufficient.

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks and then generates an answer grounded in that retrieved evidence.
