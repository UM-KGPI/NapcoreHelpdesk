# Semantic Layer Plan (Graph + RAG)

Related document:
- `docs/architecture/semantic-layer-findings.md`
- `docs/ontology/napcore-core.ttl`

## Purpose
Define a practical semantic layer that improves:
- reasoning and multi-hop inference over standards concepts,
- retrieval precision and citation quality,
- end-to-end latency for repeated and structurally similar questions.

The plan keeps current PostgreSQL + pgvector retrieval as baseline and adds a graph layer for concept-level expansion and constraint traversal.

## Scope And Baseline
- Existing baseline remains authoritative for chunk storage and vector retrieval.
- Semantic layer is additive, behind a feature flag, with deterministic fallback always available.
- All answers must stay source-grounded to approved repositories and include citations.

## Implementation Status (2026-04-15)
- Added `options.graphRagEnabled` to `POST /api/v1/questions/answer` (defaults to `false`).
- Added backend feature flag `GRAPH_RAG_ENABLED` for safe rollout gating.
- Implemented a first graph-aware retrieval slice:
  - concept extraction from query/chunk text,
  - 1-hop concept expansion,
  - graph contribution scoring integrated into ranking when enabled.
- Added response trace fields:
  - `graphExpansionHops`
  - `graphConceptIds`
  - `graphEvidenceCount`
  - `graphScoreContribution`

## Overall Implementation Plan
1. Build semantic extraction during indexing.
2. Materialize concept graph in a graph database.
3. Link chunks to graph concepts for graph-aware retrieval.
4. Add hybrid retrieval path (vector + lexical + graph expansion).
5. Add graph-aware reranking and evidence bundling.
6. Roll out via feature flag and compare against baseline.
7. Promote to default only if quality and latency targets are met.

## Target Technology Choice
Recommended primary option: Neo4j (property graph) for initial delivery speed and traversal performance.

Alternative options:
- Memgraph for similar property-graph model.
- PostgreSQL + Apache AGE for fewer moving parts.
- RDF store (for example GraphDB or Fuseki) if formal ontology inference becomes first priority.

## Target Graph Schema

### Node Labels
- `Repository`
- `Document`
- `Section`
- `Chunk`
- `Concept`
- `Requirement`
- `Profile`
- `CodeList`
- `Example`
- `Standard`

### Core Node Properties
- `Repository`: `url`, `name`, `branch`, `allowlisted`.
- `Document`: `path`, `docType`, `commitSha`, `versionTag`, `lastIndexedAt`.
- `Section`: `sectionId`, `heading`, `order`.
- `Chunk`: `chunkId`, `textHash`, `qualityScore`, `standardsScope`, `embeddingRef`.
- `Concept`: `conceptId`, `name`, `canonicalName`, `aliases`, `namespace`, `confidence`.
- `Requirement`: `reqId`, `statement`, `normativeLevel`.
- `Profile`: `profileId`, `name`, `version`.
- `CodeList`: `codeListId`, `name`.
- `Example`: `exampleId`, `title`.
- `Standard`: `standardId`, `name`, `family`.

### Relationship Types
- `(Repository)-[:CONTAINS_DOCUMENT]->(Document)`
- `(Document)-[:HAS_SECTION]->(Section)`
- `(Section)-[:HAS_CHUNK]->(Chunk)`
- `(Chunk)-[:MENTIONS_CONCEPT {score}]->(Concept)`
- `(Concept)-[:ALIAS_OF]->(Concept)`
- `(Concept)-[:DEFINED_IN]->(Section)`
- `(Concept)-[:RELATED_TO {relationType, confidence}]->(Concept)`
- `(Requirement)-[:CONSTRAINS]->(Concept)`
- `(Profile)-[:SPECIALIZES]->(Standard)`
- `(Profile)-[:CONSTRAINS]->(Requirement)`
- `(CodeList)-[:USED_BY]->(Concept)`
- `(Example)-[:ILLUSTRATES]->(Concept)`
- `(Section)-[:PART_OF_STANDARD]->(Standard)`

### Provenance Properties On Edges
- `sourceUrl`
- `sourcePath`
- `commitSha`
- `extractorVersion`
- `createdAt`

### Minimal Constraints And Indexes (Neo4j)
```cypher
CREATE CONSTRAINT repository_url IF NOT EXISTS
FOR (r:Repository) REQUIRE r.url IS UNIQUE;

CREATE CONSTRAINT chunk_id IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.chunkId IS UNIQUE;

CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (c:Concept) REQUIRE c.conceptId IS UNIQUE;

CREATE INDEX concept_name IF NOT EXISTS
FOR (c:Concept) ON (c.name);

CREATE INDEX document_path IF NOT EXISTS
FOR (d:Document) ON (d.path);
```

## Integration With Current Pipeline

### Ingestion Additions
1. After chunk creation, run concept and relation extraction.
2. Upsert graph nodes and edges with provenance.
3. Store `chunkId <-> conceptId[]` mapping in graph and optionally in PostgreSQL metadata.

### Retrieval Flow (Graph-Aware)
1. Run existing FAQ-first check.
2. For fallback, run existing hybrid retrieval (vector + lexical).
3. Resolve top chunks to concepts.
4. Expand graph by 1 to 2 hops with allowed relation types.
5. Retrieve additional chunks connected to expanded concepts.
6. Rerank by combined score:

$$
S = w_v S_v + w_l S_l + w_q S_q + w_g S_g
$$

Where:
- $S_v$ = vector score,
- $S_l$ = lexical score,
- $S_q$ = quality score,
- $S_g$ = graph proximity and relation confidence.

Initial weights:
- $w_v = 0.40$
- $w_l = 0.20$
- $w_q = 0.15$
- $w_g = 0.25$

### Guardrails
- Only expand through allowlisted repository provenance.
- Reject graph facts lacking source provenance.
- Keep citation gate unchanged: no citation, no publish.

## PoC Plan (Concrete)

### Phase P0: Design Freeze (2-3 days)
Deliverables:
- Final schema v1.
- Allowed relation types list.
- Extraction confidence thresholds.
- Feature flag contract (`GRAPH_RAG_ENABLED`).

Exit criteria:
- Team approval of schema and retrieval scoring contract.

### Phase P1: Graph Bootstrap (1 week)
Deliverables:
- Neo4j local/dev deployment.
- Migration/index script for nodes/edges from existing indexed content.
- Initial graph populated for:
  - `NeTEx-CEN/NeTEx`
  - `OpRa-CEN/OpRa`
  - `Profile_Documentation_v2`

Exit criteria:
- >95% of chunks linked to at least one concept.
- Graph constraints/indexes applied successfully.

### Phase P2: Extraction Pipeline (1 week)
Deliverables:
- Extractor module in ingestion worker.
- Upsert logic with idempotency by `(conceptId, relationship, provenance)`.
- Unit tests for extractor and graph writer.

Exit criteria:
- Re-index produces stable graph cardinality on repeated runs.

### Phase P3: Retrieval Integration (1 week)
Deliverables:
- New graph-aware retriever service component.
- Combined scoring and reranking.
- API option for graph mode under feature flag.

Exit criteria:
- End-to-end answer flow works with graph mode and deterministic fallback.

### Phase P4: Evaluation And Tuning (1 week)
Deliverables:
- Benchmark set (minimum 100 representative questions).
- Metrics dashboard and runbook updates.
- Weight tuning report.

Success targets (vs baseline):
- Citation precision: +10% relative improvement.
- Unsupported claim rate: no regression.
- P95 latency: <= current baseline + 15% during PoC; then optimize to parity or better.
- Top-5 evidence relevance judged by reviewers: +15% relative improvement.

### Phase P5: Rollout Decision (2-3 days)
Deliverables:
- Go/no-go report.
- Rollout steps and rollback procedure.

Decision rule:
- Promote graph mode only if quality gains are clear and guardrail compliance is unchanged or better.

## Minimal API Surface Additions
- `POST /answer` option: `options.graphRagEnabled` (boolean, default false during PoC).
- Trace additions:
  - `graphExpansionHops`
  - `graphConceptIds`
  - `graphEvidenceCount`
  - `graphScoreContribution`

## Operational Notes
- Keep Neo4j as read-optimized query store; source of truth for text chunks remains PostgreSQL.
- Rebuild graph from indexed content if extractor logic changes.
- Version extractor output (`extractorVersion`) to keep runs auditable.

## Open Questions
1. Which relation types are allowed in production inference path?
2. How aggressive should alias merging be across standards families?
3. Should graph expansion be bounded differently by question type?
4. What is the maximum acceptable latency overhead for graph traversal?
