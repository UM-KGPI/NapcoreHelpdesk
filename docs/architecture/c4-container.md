# C4 Container Diagram (Level 2)

Diagram source: [c4-container.puml](docs/architecture/c4-container.puml)

## Why this diagram matters
This view explains how the system is split into deployable/runtime containers.
It helps align architecture decisions across product, engineering, and governance teams.

## Containers explained in plain language
1. Web GUI: where stakeholders run chat sessions, ask questions, and see answers/references.
2. Question API / Orchestrator: coordinates FAQ-first vs RAG fallback and accepts session-aware requests.
3. Controller LLM Service: performs intent detection, route selection, and constrained SPARQL/query planning.
4. FAQ Service: returns approved canonical answers.
5. Retrieval Service: finds relevant source chunks from hybrid lexical and vector index.
6. Narration LLM Service: composes final grounded answer from an evidence pack.
7. Policy Guardrails Service: enforces SPARQL allowlists, source-policy constraints, citation checks, and abstention.
8. Editorial Workflow Service: handles review and publication approvals.
9. Ingestion Worker: imports and indexes allowlisted GitHub content, including companion documentation repositories.
10. Application Database: stores FAQs, events, review records, policy outcomes, and evidence links.
11. Vector Index: stores embeddings for retrieval.
12. Semantic Graph Database: stores ontology, alignments, and concept graph relations for graph-aware retrieval expansion.

## Container to technology mapping (v1 baseline)
1. Web GUI -> React + TypeScript + Vite.
2. Question API / Orchestrator -> Django 5 + DRF.
3. Controller LLM Service -> Django service layer + local/runtime model adapter with strict JSON output contract.
4. FAQ Service -> Django app + DRF viewset/service layer with PostgreSQL repository access.
5. Retrieval Service -> Django app service layer with pgvector + PostgreSQL FTS hybrid retrieval.
6. Narration LLM Service -> Django service layer + local/runtime model adapter constrained to evidence pack input.
7. Policy Guardrails Service -> Deterministic Python policy validators + citation/source checks + SPARQL query validators.
8. Editorial Workflow Service -> Django app + Django Admin workflow + PostgreSQL state machine.
9. Ingestion Worker -> Celery workers + Redis queue + GitHub API clients.
10. PostgreSQL -> PostgreSQL 15 + Django migrations + pgvector extension.
11. Vector Index -> pgvector tables in PostgreSQL for MVP.
12. Semantic Graph Database -> GraphDB (RDF/OWL + SPARQL endpoint) for ontology-aware traversal and expansion in graph-aware retrieval mode.

## Current implementation status
- Current runtime uses PostgreSQL + pgvector as the production baseline.
- Graph-aware scoring path is implemented behind feature flags (`GRAPH_RAG_ENABLED`, `GRAPHDB_ENABLED`) with GraphDB as the semantic graph backend.
- Ontology loading for runtime semantic expansion is GraphDB-driven in graph-enabled deployments.
- Controller/Narration split is the target container architecture for local-model operation and deterministic routing.
- No Neo4j runtime path is modeled in the current baseline.

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
