# RAG Architecture For NAPCORE Helpdesk

## Goal
Implement the helpdesk as a retrieval-augmented generation (RAG) system that produces source-grounded answers for standards questions and supports FAQ curation.

## UML Reference Diagram
- Primary activity diagram: [rag-activity-diagram.svg](docs/architecture/rag-activity-diagram.svg)

## C4 Diagrams
- Overview: [c4-overview.md](docs/architecture/c4-overview.md)
- Level 1: [c4-system-context.md](docs/architecture/c4-system-context.md)
- Level 2: [c4-container.md](docs/architecture/c4-container.md)
- Level 3 draft: [c4-orchestrator-components.md](docs/architecture/c4-orchestrator-components.md)

## API Contract
- Implementation contract: [rag-fallback-api-contract.md](docs/architecture/rag-fallback-api-contract.md)

## Semantic Layer Extension
- Graph-based semantic layer plan: [semantic-layer-plan.md](docs/architecture/semantic-layer-plan.md)
- Semantic layer findings and ontology baseline: [semantic-layer-findings.md](docs/architecture/semantic-layer-findings.md)
- Initial ontology draft: [../ontology/napcore-core.ttl](docs/ontology/napcore-core.ttl)

## Ontology Namespace Policy
- Baseline policy: reuse common core vocabularies before adding project-specific terms.
- Target scope: final ontology must cover NAPCORE-related concepts, not only Transmodel.
- Delivery sequencing:
  - Start with concepts from Transmodel family standards and materials.
  - Extend with DATEX II concepts in a later phase.
- Reused core namespaces:
  - SKOS for concept schemes, preferred and alternative labels, broader and narrower semantics.
  - PROV-O for provenance of extracted concepts, links, and retrieval evidence lineage.
  - DCTERMS for document and artifact metadata fields.
- Project extension namespace:
  - Working namespace: `https://napcore.eu/ontology/helpdesk#`
  - Working prefix: `nch`
  - Scope: experimental helpdesk application ontology (not yet a full NAPCORE domain ontology).
  - Usage: only for transport relations not already covered by SKOS, PROV-O, or DCTERMS.
- Governance rules:
  - All new project terms must include definition, scope note, and source provenance.
  - Ontology term additions follow editorial lifecycle: draft -> review -> approved.
  - Retrieval runs must record ontology version used for traceability.

## Technology Baseline (Decision Set 1)

These decisions establish the first implementation baseline so backend and frontend work can start without blocking on stack selection.

### Runtime and services
- Backend API and orchestration: Python 3.11 + Django 5 + Django REST Framework.
- Data validation: DRF serializers and model validation aligned with [openapi.yaml](api/openapi.yaml).
- Async jobs (ingestion/re-indexing): Celery + Redis.
- Frontend: React + TypeScript + Vite.

### Persistence and retrieval
- Relational store: PostgreSQL 15.
- Vector retrieval: pgvector extension in the same PostgreSQL instance for MVP.
- Lexical retrieval: PostgreSQL full-text search for hybrid ranking.
- Migration tooling: Django migrations.

### LLM and embeddings
- LLM provider adapter: provider-agnostic interface with OpenAI-compatible default.
- Default generation model (pilot): GPT-4.1-mini class model.
- Default embedding model (pilot): text-embedding-3-large class model.

### API and generation workflow
- Contract-first implementation from [openapi.yaml](api/openapi.yaml).
- Question pipeline: FAQ match -> hybrid retrieval -> grounded generation -> policy guard -> evidence mapping.
- Fail-safe policy: abstain when evidence support is below threshold or citations are missing.

### Why this baseline
- Minimizes moving parts for MVP by keeping vectors in PostgreSQL.
- Preserves portability with provider adapters and OpenAPI contract-first design.
- Keeps strict guardrail logic in application code, not model prompt only.

### Deferred choices (post-MVP)
- Move from pgvector to dedicated vector DB if scale or latency requires it.
- Add second LLM provider for resilience and benchmark comparison.
- Introduce workflow orchestration (for example Temporal) if job complexity grows.

## Diagram Alignment Notes
- Keep FAQ-first routing before embedding generation when there is a high-confidence canonical FAQ match.
- Use embedding plus vector retrieval only when FAQ lookup misses or confidence is below threshold.
- Keep the LLM stage as fallback generation grounded in retrieved passages.
- Always return source citations with generated answers and route low-confidence outputs to editorial review.

## Trust And Safety Guardrails
- Knowledge scope: only approved GitHub repositories are allowed in retrieval.
- Retrieval filter: enforce repository allowlist at query time.
- Generation policy: answer strictly from retrieved passages; do not use latent model knowledge for factual claims.
- Abstention policy: if evidence is insufficient, return an explicit insufficient-evidence response.
- Publish policy: block any answer lacking citations or containing unsupported claims.

## Architecture Overview
1. Source ingestion layer
2. Processing and chunking layer
3. Retrieval index layer
4. Answer orchestration layer (FAQ-first, RAG fallback[^rag-fallback])
5. Editorial curation layer
6. Persistence and analytics layer
7. GUI interaction layer

## Core Components

### 1) Source ingestion
- Inputs: GitHub repositories (priority: NeTEx-CEN/NeTEx), docs, and approved references.
- Responsibilities:
  - Enforce repository allowlist and approved branch/tag policy.
  - Pull content by configured branch/tag.
  - Apply include and exclude filters.
  - Record source metadata: repo, path, commit, standard tag, version.

### 2) Processing and chunking
- Responsibilities:
  - Normalize markdown, XML, and text content.
  - Split into semantic chunks with chunk IDs.
  - Attach citation payload: source path, commit hash, section heading.

### 3) Retrieval index
- Responsibilities:
  - Store chunk embeddings and metadata.
  - Store repository identity fields for allowlist filtering.
  - Support top-k semantic retrieval with metadata filtering.
  - Support re-indexing and stale-index cleanup.

### 4) Answer orchestration
- Request flow:
  1. Receive GUI question.
  2. Try FAQ lookup for canonical answer.
  3. If FAQ match confidence is high, return canonical answer.
  4. If no FAQ match or low confidence, run RAG retrieval.
  5. If retrieval evidence is insufficient, return abstention response.
  6. Otherwise generate answer from retrieved context only.
  7. Run citation and support checks; block unsupported claims.
  8. Return answer with citations and confidence score.
  9. Log event for analytics and FAQ promotion.

### 5) Editorial curation
- States: draft, review, approve, publish.
- Rules:
  - No publish without citations.
  - Regulatory statements require explicit editorial validation.
  - Low-confidence answers stay in draft queue.

### 6) Persistence
- PostgreSQL tables:
  - faq_entries
  - faq_versions
  - question_events
  - review_events
  - retrieval_events
  - answer_evidence_links
- Notes:
  - Keep immutable revision history for approved content.
  - Track feedback and frequency for promotion logic.

### 7) GUI
- Features:
  - Question input and answer rendering.
  - Display references and confidence.
  - Capture feedback: helpful, not helpful, escalate.

## Non-Functional Targets (MVP)
- P95 answer latency: <= 8 seconds.
- Citation coverage for published FAQ answers: 100%.
- Retrieval success on covered intents: >= 90%.
- Full audit trail for publish actions: 100%.
- Unsupported-claim publication rate: 0%.

## Failure Handling
- Retrieval miss:
  - Return explicit insufficient-evidence response with transparency.
  - Log miss and route to curation backlog.
- Citation gap:
  - Block publish and request reviewer action.
- Unsupported claim detected:
  - Block response from publish path and regenerate or abstain.
- Source update drift:
  - Trigger re-indexing and mark impacted FAQs for revalidation.

## Implementation Phasing
1. Phase 1: Ingestion, index, and FAQ-first routing.
2. Phase 2: RAG fallback with citations and confidence.
3. Phase 3: Editorial workflow and promotion automation.
4. Phase 4: Quality metrics dashboard and revalidation jobs.

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks and then generates an answer grounded in that retrieved evidence.
