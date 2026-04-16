# C4 Container Diagram (Level 2)

Diagram source: [c4-container.puml](docs/architecture/c4-container.puml)

## Why this diagram matters
This view explains how the system is split into deployable/runtime containers.
It helps align architecture decisions across product, engineering, and governance teams.

## Containers explained in plain language
1. Web GUI: where stakeholders run chat sessions, ask questions, and see answers/references.
2. Question API / Orchestrator: decides FAQ-first vs RAG fallback path and accepts session-aware requests.
3. FAQ Service: returns approved canonical answers.
4. Retrieval Service: finds relevant source chunks from hybrid lexical and vector index.
5. Generation and Guardrails: creates grounded answer, optionally calls LLM provider, and enforces policy checks.
6. Editorial Workflow Service: handles review and publication approvals.
7. Ingestion Worker: imports and indexes allowlisted GitHub content, including companion documentation repositories.
8. Application Database: stores FAQs, events, review records, and evidence links.
9. Vector Index: stores embeddings for retrieval.
10. Semantic Graph Database: stores ontology and concept graph relations for graph-aware retrieval expansion.

## Container to technology mapping (v1 baseline)
1. Web GUI -> React + TypeScript + Vite.
2. Question API / Orchestrator -> Django 5 + DRF.
3. FAQ Service -> Django app + DRF viewset/service layer with PostgreSQL repository access.
4. Retrieval Service -> Django app service layer with pgvector + PostgreSQL FTS hybrid retrieval.
5. Generation and Guardrails -> Django app service layer using provider adapter + policy checks.
6. Editorial Workflow Service -> Django app + Django Admin workflow + PostgreSQL state machine.
7. Ingestion Worker -> Celery workers + Redis queue + GitHub API clients.
8. PostgreSQL -> PostgreSQL 15 + Django migrations + pgvector extension.
9. Vector Index -> pgvector tables in PostgreSQL for MVP.
10. Semantic Graph Database -> GraphDB (RDF/OWL-native + SPARQL) for ontology-aware traversal and expansion in graph-aware retrieval mode.

## Current implementation status
- Current runtime uses PostgreSQL + pgvector as the production baseline.
- Graph-aware scoring path is implemented behind feature flags (`GRAPH_RAG_ENABLED`, `GRAPHDB_ENABLED`) with GraphDB as the primary semantic graph backend.
- Neo4j is retained only as an experimental branch (`NEO4J_EXPERIMENTAL_ENABLED`) and is not the production semantic backend.

## Key messages
1. FAQ-first lowers latency and improves consistency for known questions.
2. RAG fallback is isolated behind retrieval and generation/guardrail services.
3. Trust controls are architectural, not optional runtime behavior.
4. Editorial workflow is a first-class container, not an afterthought.

## Discussion prompts for mixed audiences
1. Are service responsibilities clearly separated?
2. Do we agree with where policy checks are enforced?
3. Is any external dependency missing from this level?

## Relationship to requirements
- Maps directly to FR-001 through FR-006 and the RAG trust/safety constraints.
