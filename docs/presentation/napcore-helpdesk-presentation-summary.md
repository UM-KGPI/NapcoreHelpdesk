# NAPCORE Helpdesk - Presentation Summary

## Purpose
This summary is intended as the base narrative for a future PPTX or PDF presentation.

## Slide 1 - Problem And Goal
- Need: a trustworthy helpdesk for multimodal standards implementation questions.
- Risk to avoid: hallucinated or uncited AI answers.
- Goal: provide grounded, practical answers with explicit source traceability.

## Slide 2 - System Context (C4 Level 1)
- Stakeholders: PTO (Public Transport Operator), PTA (Public Transport Authority), Developer, ITS System Integrator, Ticketing Agent.
- External systems: Approved GitHub repositories (NeTEx-CEN/NeTEx), LLM provider for grounded generation.
- System boundary: One shared helpdesk interface for all stakeholder groups.
- Knowledge constraint: all answers are sourced from approved repositories only.

## Slide 3 - Scope
- Domain scope: Transmodel, NeTEx, SIRI, OJP/OpRa, DATEX II.
- Priority source: NeTEx-CEN/NeTEx and selected companion repositories.
- Routed demo surfaces: `/user` for chat and `/operator` for governance/orchestration.

## Slide 4 - Evolution Of Helpdesk Implementations
- Stage 1: traditional keyword search across standards documents.
- Stage 2: simple grounded Q and A with FAQ-first orchestration.
- Stage 3: editorial and KPI console for governance and promotion.
- Stage 4: chat session UX with deterministic and LLM-ready generation profiles.
- The trust model stays fixed across all stages: allow-listed repositories and citations only.

## Slide 5 - Why The Evolution Matters
- Search alone is too manual for recurring implementation questions.
- FAQ-first gives fast canonical answers for known intents.
- Editorial workflow turns runtime demand into curated knowledge.
- Chat UX improves usability while keeping evidence grounding.

## Slide 6 - Core Approach
- Architecture: FAQ-first with RAG fallback.[^rag-fallback]
- FAQ-first path: if a high-confidence approved FAQ exists, return canonical answer.
- RAG fallback path: retrieve approved source chunks, then generate grounded answer with citations.
- Generation profile can remain deterministic or switch to LLM-ready mode.
- If evidence is insufficient: abstain with transparent response.

## Slide 7 - Trust And Safety Principles
- Knowledge boundary: only approved GitHub repositories are allowed.
- No unsupported claims: answers must be backed by retrieved evidence.
- Citation gate: publication blocked if citations are missing.
- Editorial gate: draft, review, approve, publish states before FAQ publication.

## Slide 8 - Functional Requirements Highlights
- FR-001: developer question answering through GUI.
- FR-004: ingestion and indexing of approved GitHub sources.
- FR-005: retrieval and grounded generation.
- FR-006: anti-hallucination and knowledge-boundary enforcement.
- FR-002 and FR-003: curation workflow and recurring-question promotion.

## Slide 9 - Data Model Logic
- Source governance: approved_repositories -> source_documents -> source_chunks.
- FAQ lifecycle: faq_entries -> faq_versions -> review_events.
- Runtime telemetry: question_events -> retrieval_events.
- Evidence mapping: answer_evidence_links ties answers to exact source_chunks.

## Slide 10 - Why This Prevents Hallucinations
- Retrieval constrained to approved repositories.
- Generation constrained to retrieved context.
- Evidence links provide auditable claim-to-source mapping.
- Unsupported answers are blocked or abstained.

## Slide 11 - User Experience Flow
- User asks a question in `/user` or performs governed operations in `/operator`.
- System attempts FAQ match.
- If needed, system performs RAG retrieval plus generation.
- Response includes references, confidence signal, and request trace.
- User feedback is captured for quality improvement.

## Slide 12 - Current Product State
- Chat-style multi-turn UX is implemented as a separate `/user` route.
- Backend supports deterministic grounded answers and optional LLM-ready generation.
- Approved companion repositories can be indexed alongside NeTEx-CEN/NeTEx.
- `/operator` contains editorial board, KPI metrics, and promotion candidates under the same shared auth shell.

## Slide 13 - Operations And Governance
- Review workflow records reviewer identity and decisions.
- Internal editorial console is provided via Django Admin.
- Promotion rule identifies recurring intents for curated FAQ backlog.
- Re-indexing handles repository updates and standards drift.
- Audit trail supports quality and compliance reviews.

## Slide 14 - MVP Success Metrics
- 100 percent citation coverage for published FAQs.
- 0 percent unsupported-claim publication rate.
- P95 answer latency target: 8 seconds or less.
- Retrieval success target on covered intents: at least 90 percent.

## Slide 15 - Current Artifacts In Repository
- Functional requirements and first-user testing pack.
- Local run guide and console usage guide.
- Updated C4 architecture and RAG/database documentation.
- Technology baseline: Django 5 + DRF backend, React/Vite frontend.
- PlantUML and exported SVG assets.

## Slide 16 - Next Steps
- Complete pilot scenarios across chat, editorial, and promotion flows.
- Evaluate LLM-ready mode against deterministic fallback.
- Refine companion-repository ingestion profiles.
- Decide production hardening steps from pilot evidence.

## Optional Appendix - Example User Questions
- How to use NeTEx for exchanging a timetable?
- How to implement IDs for a Stop Place registry?

Expected behavior for both:
- grounded answer,
- practical implementation guidance,
- explicit citations,
- abstention when evidence is insufficient.

[^rag-fallback]: In a helpdesk or FAQ system, a RAG fallback (Retrieval‑Augmented Generation) happens when the system cannot find a good direct match (e.g., exact FAQ answer). It then falls back to RAG: retrieves the most relevant documents from approved sources, and generates an answer grounded in that retrieved context. The generation method depends on the profile: (1) **Deterministic mode** (now): uses pattern-matched templates adapted to the question, with confidence based on retrieval scores. (2) **LLM-ready mode** (future): feeds retrieved chunks to an LLM for synthesis. Both approaches prevent hallucination by grounding answers in real retrieved text.
