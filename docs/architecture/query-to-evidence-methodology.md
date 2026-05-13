# Query-to-Evidence Methodology

## Purpose
This document is the single consolidated methodology for how NAPCORE Helpdesk processes a user question from API input to semantic expansion, hybrid retrieval, grounded answer generation, and persisted audit trail.

It merges and operationalizes the pipeline fragments previously described across:
- `docs/architecture/rag-architecture.md`
- `docs/architecture/semantic-layer-plan.md`
- `docs/architecture/c4-orchestrator-components.md`
- `backend/README.md`
- `docs/testing/q070-e2e-walkthrough-report.md`
- `docs/testing/q080-e2e-walkthrough-report.md`

## Methodology Scope
- Runtime request path: `POST /api/v1/questions/answer`
- Semantic layer path: GraphDB-backed concept anchoring and expansion
- Retrieval path: PostgreSQL full-text + pgvector hybrid retrieval
- Persistence path: question event, retrieval events, evidence links, provenance
- Governance path: policy guardrails and abstention behavior

## Canonical Runtime Sequence

### 1) Request intake and validation
1. API receives request in `QuestionAnswerView`.
2. Required headers and payload contract are validated.
3. Request is normalized into orchestration options (`scope`, `top_k`, `min_score`, generation profile, citation limits).

Output: validated request context and correlation ID.

### 2) Semantic parsing and scope determination
1. Semantic parser classifies intent and normativity.
2. Concepts are extracted from the question text.
3. Candidate standards are resolved from concepts and requested scope.
4. Ambiguity and semantic-confidence signals are emitted for later abstention/policy logic.

Output: semantic query object with:
- core concept(s)
- candidate standards
- ambiguity flag
- confidence fields

### 3) Route selection: FAQ-first, RAG fallback
1. FAQ matcher is checked first.
2. If FAQ confidence is high and policy-safe, FAQ answer is returned.
3. Otherwise, RAG retrieval path is executed.

Output: selected route (`faq`, `rag`, or abstain path).

### 4) Graph-enabled semantic expansion (SPARQL stage)
When graph mode is enabled:
1. Active standards are resolved into named graph scope.
2. SPARQL query expands seed concept IDs over allowed relation paths.
3. Expanded concept IDs are projected back to local concept IDs used by retrieval/ranking.

SPARQL implementation characteristics:
- Endpoint: GraphDB repository endpoint (`GRAPHDB_SPARQL_ENDPOINT` + repository)
- Query transport: HTTP POST with `application/sparql-query`
- Response format: `application/sparql-results+json`
- Graph scoping: named graph restriction based on requested/effective standards

Representative expansion pattern:
- `VALUES ?seed { ... }`
- property-path traversal over SKOS relation set
- optional `GRAPH ?g` scoping

Output: expanded concept set + graph trace fields (source, hop count, concept count).

### 5) Hybrid retrieval (SQL + pgvector stage)
1. Query embedding is built from question text and semantic terms.
2. PostgreSQL candidate retrieval executes with hybrid ranking:
   - lexical ranking via `SearchVector` and `SearchRank`
   - vector distance via pgvector `CosineDistance(embedding_vector, query_embedding)`
3. Additional path-hint and graph-concept candidates are injected.
4. Final score blends vector, lexical, quality, and graph contributions.
5. Diversity and source-path caps are applied before final top-k selection.

Output: ranked evidence chunk set and retrieval trace metrics.

### 6) Grounded generation and policy checks
1. If evidence is insufficient, abstain or request clarification according to policy gates.
2. Otherwise, answer is generated from retrieved evidence only.
3. Policy guard enforces source/citation constraints and unsupported-claim checks.

Output: final answer payload with citations, confidence, and trace metadata.

### 7) Persistence and audit trail (SQL writes)
The following records are persisted in PostgreSQL:
1. `question_events` (request-level orchestration outcome)
2. `retrieval_events` (per-chunk retrieval telemetry)
3. `answer_evidence_links` (answer-to-citation link table)
4. `evidence_provenance` (traceable provenance payloads)

This persistence model ensures end-to-end traceability from answer claims back to indexed source chunks and source repositories.

## Data Stores and Their Roles

### GraphDB (SPARQL)
Used for:
- ontology and alignment storage
- concept anchoring/expansion
- standards-scoped semantic traversal

Not used for:
- chunk embedding retrieval ranking

### PostgreSQL + pgvector (SQL)
Used for:
- source chunk store (`SourceChunk`)
- vector similarity retrieval (pgvector)
- lexical full-text ranking
- event and evidence persistence tables

## Quality and Governance Controls
- FAQ-first for low latency where canonical answers exist.
- Evidence-gate thresholds for minimum support quality.
- Citation required for publishable confidence.
- Abstention behavior when evidence quality is below thresholds.
- Runtime trace fields exposed for diagnostics, A/B comparisons, and benchmark reporting.

## Benchmark Interpretation Rule
For methodology acceptance, evaluate both:
1. Retrieval quality (citation relevance, canonical-source hit rate).
2. Latency budget (API and retrieval timing under production-like configuration).

A retrieval improvement is not considered production-ready if it violates latency and timeout constraints.

## Methodological Basis
The capability-matrix approach used for GraphRAG optimization is based on three complementary references:

1. Repository empirical evidence:
   - q070 and q080 benchmark walkthroughs show that different question families stress different retrieval stages.
   - Stage timing traces (for example, graph candidate query vs candidate scoring) demonstrate that optimization targets are capability-dependent rather than question-specific.

2. Software quality engineering practice:
   - risk-based testing for selective execution on high-impact changes,
   - contract testing to protect stable interfaces (core ontology + alignments) while allowing volatile regenerated standards modules,
   - tiered regression suites (canary, stratified, full) for cost-effective coverage.

3. Retrieval evaluation practice:
   - grouped evaluation by capability slice,
   - representative subset execution for fast feedback,
   - periodic full-benchmark runs for portfolio-level regression detection.

In this project, the matrix is therefore not an additional architectural layer. It is an execution and validation control plane that links ontology contracts, retrieval-stage metrics, and benchmark slices so that latency tuning remains scalable across the benchmark portfolio.

## Empirical Confirmation (Full 100-Question A/B, 2026-05-11)
A full control-vs-GraphRAG benchmark run across all 100 benchmark questions confirms the methodological need for capability-sliced governance and matrix-driven regression routing.

Primary evidence artifacts:
- [GraphRAG A/B machine-readable results](../testing/benchmark-graphrag-ab-2026-05-11.json)
- [GraphRAG A/B human-readable summary](../testing/benchmark-graphrag-ab-2026-05-11.md)

Observed outcomes under the documented runtime settings:
- Successful runs: 100/100 (no execution errors)
- Global latency: control average 1507.3 ms vs graph average 5241.3 ms
- Relative impact: graph/control average ratio 5.229
- Portfolio result: GraphRAG slower on 100/100 questions in this run
- Tail behavior: graph p95 9851.3 ms vs control p95 2925.7 ms

Stage-profile evidence identifies concentrated latency pressure in a small number of retrieval stages, primarily candidate scoring, path-hint merge, and graph candidate query. This confirms that optimization and guardrails must be defined and monitored by capability slice and stage budget, not by isolated question anecdotes.

Methodological implication:
- The capability matrix is required as an operational control artifact (not optional documentation) to map change types to benchmark slices, expected stage budgets, and promotion gates.
- Full 100-question execution remains mandatory for release-level validation, while canary and stratified slices provide fast iteration feedback between full runs.

For detailed operational gates and test-tier definitions, see [Benchmark Regression Testing Strategy and Gates](../testing/benchmark-regression-gates.md).

## Methodology Status
This methodology is active and implemented in the current architecture baseline. It should be treated as the authoritative query-to-evidence runtime process unless superseded by an approved architecture update.
