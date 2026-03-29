---
title: "NAPCORE Helpdesk: requirements and development"
subtitle: "Presentation Draft"
author: "NAPCORE Helpdesk Team"
date: "2026-03-29"
lang: "en"
colorlinks: true
---

# Problem And Goal

- Need a trusted answer layer for multimodal standards implementation.
- Main risk is fast but uncited guidance that creates delivery risk.
- Goal is practical answers with traceable references and controlled escalation.

# Stakeholders And System Context (C4 Level 1)

**Five stakeholder groups share one helpdesk interface:**

- PTO (Public Transport Operator) — responsible for daily service delivery.
- PTA (Public Transport Authority) — sets policy and compliance standards.
- Developer — implements integrations and APIs.
- ITS System Integrator — connects helpdesk to broader mobility ecosystem.
- Ticketing Agent — manages passenger-facing systems.

**External systems:**

- Approved GitHub repositories (NeTEx-CEN/NeTEx) — knowledge source.
- LLM provider — optional grounded generation path.

![](docs/architecture/c4-system-context.png){ width=92% }

# Documentation Scope

- Standards: Transmodel, NeTEx, SIRI, OJP/OpRa, DATEX II.
- Priority source: NeTEx-CEN/NeTEx and approved companion repositories.
- Surfaces: separate user route (`/user`) and operator route (`/operator`) over one shared backend shell.

# Core Approach

- FAQ-first with RAG fallback.[^rag-fallback]
- FAQ-first: return approved answers when confidence is high.
- RAG fallback: retrieve source chunks, then generate a grounded answer.
- Generation profiles:
  - `deterministic-grounded` (active): question-adaptive deterministic templates with retrieval-score confidence.
  - `llm-ready` (optional): retrieved chunks passed to LLM synthesis when enabled.
- If evidence is weak, abstain explicitly.

# Functional Requirements Highlights

- FR-001: question answering through the helpdesk UI.
- FR-004: ingestion and indexing of approved GitHub sources.
- FR-005: retrieval and grounded generation.
- FR-006: anti-hallucination and boundary enforcement.
- FR-002 and FR-003: editorial curation and FAQ promotion.

# Current Product State

- Frontend now exposes separate routed surfaces for user chat and operator console.
- Backend supports deterministic grounded generation and an optional LLM-ready mode.
- Knowledge index is built from approved repositories and selected companion repositories.
- Shared connection state keeps auth and backend targeting consistent across both routes.

# Current Chat UX

- User route and operator route are shown in full-size screenshots.
- Connection fields are intentionally blank for presentation clarity.

![](docs/presentation/assets/user-chat-empty-full.png){ width=96% }

![](docs/presentation/assets/operator-console-empty-full.png){ width=96% }

# Documentation And Delivery Artifacts

- Functional requirements, testing pack, and local run guide.
- RAG architecture and updated C4 architecture documents.
- Technology baseline: Django 5 + DRF backend, React/Vite frontend.
- Separate routed user/operator UX and deterministic grounded answering.
- PlantUML and exported SVG architecture assets for reproducible documentation.

# Next Steps

1. Complete pilot testing across user chat, operator flow, and promotion workflow.
2. Evaluate deterministic mode outcomes against grounded LLM mode on the same question set.
3. Finalize repository ingestion profiles and production hardening backlog.

# Appendix: Example Questions

**Question 1:** How to use NeTEx for exchanging a timetable?

![](docs/presentation/assets/question-timetable.png){ width=96% }

**Question 2:** How to implement IDs for a Stop Place registry?

![](docs/presentation/assets/question-stop-place-ids.png){ width=96% }

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks from approved repositories and generates an answer grounded in that retrieved evidence. In deterministic mode this is template-driven and score-based; in LLM-ready mode retrieved chunks are synthesized by the LLM while remaining evidence-bound.
