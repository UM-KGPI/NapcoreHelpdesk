# Semantic Layer Plan (Graph + RAG)

Related document:
- `docs/architecture/semantic-layer-findings.md`
- `docs/ontology/napcore-its.ttl`
- `docs/ontology/standards/netex.ttl`
- `docs/ontology/standards/opra.ttl`
- `docs/ontology/standards/siri.ttl`
- `docs/ontology/standards/datex.ttl`
- `docs/ontology/alignments/nits-netex-align.ttl`
- `docs/ontology/alignments/nits-opra-align.ttl`
- `docs/ontology/alignments/nits-siri-align.ttl`
- `docs/ontology/alignments/nits-datex-align.ttl`

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

## Architecture Conformance Note (2026-04-16)
- The implementation guide defines GraphDB (RDF/OWL-native) as the ontology database.
- Neo4j is not the target production ontology platform for the initial architecture.
- Existing Neo4j utilities remain useful for exploratory graph traversal and diagnostics, but production ontology reasoning must use GraphDB + SPARQL + built-in reasoning profiles.

## Implementation Status (2026-04-15)
- ✅ **Step 1: Graph snapshot bootstrap** (commit f653185)
  - `python manage.py export_semantic_graph` exports Repository/Document/Concept/Chunk nodes + topology edges
  - Filters: `--repo-url`, `--min-quality`; reports node/edge counts
- ✅ **Step 2: Neo4j import adapter** (commit 9aea073)
  - `python manage.py import_semantic_graph_neo4j --input <file.json>` with dry-run by default
  - Idempotent schema bootstrap: 6 constraints + 2 indexes (CREATE ... IF NOT EXISTS)
  - Optional `--no-ensure-schema` to skip bootstrap on pre-prepared databases
- ✅ **Step 3: Live concept expansion adapter (GraphDB-first)** (commit c490188 + 2026-04-16 alignment)
  - Production expansion path uses GraphDB SPARQL traversal over alignment relations.
  - Neo4j traversal remains available only as experimental fallback path when explicitly enabled.
  - Trace includes `graphExpansionSource`: "graphdb" | "neo4j_experimental" | "memory" | "memory_fallback" | "none"
- ✅ **Step 4: Graph concept alias candidate injection** (commit 8fd8fc8)
  - `_graph_concept_candidates()` retrieves chunks whose text matches expanded concept aliases
  - Injected into retrieval pool after path-hint candidates
  - Trace tracks `graphCandidatesAdded` count
- ✅ **Step 5: Graph-aware reranking with provenance** (commit ac39aab)
  - Enhanced scoring: direct concept overlap 0.22 (was 0.18), expanded overlap 0.15 (was 0.10)
  - Each chunk includes `graphProvenanceConceptIds`: which expanded concepts led to selection
  - Trace includes `graphProvenanceChainCount`: total unique concept IDs in top-k
- ✅ **Step 6: Feature flag rollout with variant tracking** (commit 1359140)
  - Added `GRAPH_RAG_VARIANT` setting (default "baseline"; can be "graph-rag", "control", "baseline")
  - Trace includes `graphRagVariant`: "control" (graph disabled) | "graph-rag" (graph enabled)
  - Latency measurement: `retrievalLatencyMs` added to trace
  - Ready for A/B testing: requests can opt in via `graphRagEnabled=true` in options

## Overall Implementation Plan
1. ✅ Build semantic extraction during indexing.
2. ✅ Materialize concept graph in a graph database.
3. ✅ Link chunks to graph concepts for graph-aware retrieval.
4. ✅ Add hybrid retrieval path (vector + lexical + graph expansion).
5. ✅ Add graph-aware reranking and evidence bundling.
6. ✅ Roll out via feature flag and compare against baseline.
7. ⏳ Promote to default only if quality and latency targets are met.

## Ontology Topology (Planned)
- Core ontology: `napcore-its.ttl` (`nits:` namespace) is the canonical semantic anchor layer.
- Standard modules: one ontology per standards family/domain module (for example `standards/netex.ttl`, `standards/opra.ttl`, `standards/siri.ttl`, `standards/datex.ttl`).
- Alignment modules: `alignments/nits-netex-align.ttl`, `alignments/nits-opra-align.ttl`, `alignments/nits-siri-align.ttl`, `alignments/nits-datex-align.ttl` provide explicit cross-standard mapping assertions.
- Runtime contract: retrieval/anchoring resolves first to core `nits:` IDs, while standard-local IDs and mappings remain traceable for provenance and editorial review.

## Target Technology Choice
Recommended primary option: GraphDB (RDF/OWL-native) for ontology storage, alignment reasoning, and standards-compliant querying.

Rationale:
- Native OWL/RDFS semantics.
- Standard SPARQL support for transparent and portable queries.
- Built-in reasoning profiles suitable for aligned standards ontologies.
- Named graph model for per-standard scope and provenance boundaries.

Non-primary / optional components:
- Neo4j or Memgraph only for optional analytics or traversal experimentation outside the core ontology reasoning path.
- PostgreSQL + pgvector remains the primary retrieval store for chunks and embeddings.

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

### Minimal GraphDB Repository Setup
- Separate named graphs for each ontology/module:
  - core: `napcore-its.ttl`
  - standards: `standards/netex.ttl`, `standards/opra.ttl`, `standards/siri.ttl`, `standards/datex.ttl`
  - alignments: `alignments/nits-netex-align.ttl`, `alignments/nits-opra-align.ttl`, `alignments/nits-siri-align.ttl`, `alignments/nits-datex-align.ttl`
- Enable OWL/RDFS reasoning profile in repository config.
- Preserve provenance triples (`sourceUrl`, `sourcePath`, `commitSha`, `extractorVersion`) for traceability.
- Keep SHACL validation available for ontology quality gates during ingestion.

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
- GraphDB local/dev deployment.
- Migration/index script for nodes/edges from existing indexed content.
- Federated ontology load order defined and reproducible:
  1. `napcore-its.ttl`
  2. standards modules (`standards/netex.ttl`, `standards/opra.ttl`, `standards/siri.ttl`, `standards/datex.ttl`)
  3. alignment modules (`alignments/nits-netex-align.ttl`, `alignments/nits-opra-align.ttl`, `alignments/nits-siri-align.ttl`, `alignments/nits-datex-align.ttl`)
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
- ✅ **Benchmark set (2026-04-16)**
  - 100 questions in `docs/testing/benchmark-questions.yaml`.
  - Intent coverage: explanation (42), example (20), mapping (15), disambiguation (4), abstention (9 questions from groups F/G).
  - Standards coverage: OpRa-only, NeTEx-only, and cross-standard (NeTEx+OpRa) groups.
  - Expected source patterns grounded in actual PostgreSQL-indexed paths.
- ✅ **Benchmark runner command (2026-04-16)**
  - `python manage.py run_retrieval_benchmark`
  - Computes hit@5, hit@10, hit@20, MRR@10, MRR@20, latency, graph vs baseline delta.
  - Supports `--tags`, `--ids`, `--baseline-only`, `--graph-only`, `--scope` filters.
  - Writes JSON report to `docs/testing/benchmark-report.json`.
  - 13 unit tests passing.
- ✅ **Weight tuning report (2026-04-16, live DB)**
  - Full run: 100 questions (`docs/testing/benchmark-report.json`).
  - Baseline: hit@10=0.71, mrr@10=0.4657, mean latency=3022.4ms.
  - Graph-RAG: hit@10=0.67, mrr@10=0.2965, mean latency=4186.0ms.
  - Delta: hit@10=-0.04, mrr@10=-0.1692, latency overhead=+1163.6ms (+38%).
  - Improved questions: 9; regressed questions: 13.
  - Observed behavior: graph candidate injection is too broad (mean added candidates=60.38, max=80), causing precision and latency regressions.
  - First tuning pass rerun (`docs/testing/benchmark-report-tuned.json`):
    - Baseline: hit@10=0.71, mrr@10=0.466, mean latency=3042.1ms.
    - Graph-RAG: hit@10=0.61, mrr@10=0.344, mean latency=4185.9ms.
    - Delta: hit@10=-0.10, mrr@10=-0.121, latency overhead=+1144ms.
    - Result: no-go remains; tuning pass reduced worst MRR loss but worsened hit@10 coverage.
  - Revised tuning direction:
    - keep tighter graph candidate cap (`max(10, top_k * 2)`), but remove hard doc_type gating;
    - score graph candidates by alias quality (exact token/phrase match > loose substring);
    - add intent-aware graph gating (apply expansion boosts only for mapping/disambiguation intents).

Success targets (vs baseline):
- Citation precision: +10% relative improvement.
- Unsupported claim rate: no regression.
- P95 latency: <= current baseline + 15% during PoC; then optimize to parity or better.
- Top-5 evidence relevance judged by reviewers: +15% relative improvement.

To run a quick cross-standard check:
```
cd backend && ../.venv/bin/python manage.py run_retrieval_benchmark \
  --tags cross-standard --top-k 20 \
  --output docs/testing/benchmark-report.json
```

To run the full benchmark:
```
cd backend && ../.venv/bin/python manage.py run_retrieval_benchmark \
  --top-k 20 --output docs/testing/benchmark-report.json
```

### Phase P5: Rollout Decision (2-3 days)
Deliverables:
- Go/no-go report written to `docs/testing/p5-rollout-decision.md`.
- Rollout steps and rollback procedure (see below).

#### Decision table
| Metric | Pass threshold | Action if below threshold |
|---|---|---|
| `hit_at_10_delta` | ≥ +0.10 | Investigate expansion vocabulary; re-check ontology aliases |
| `mrr_at_10_delta` | ≥ 0.00 | Check reranking weights; ensure direct-overlap boost is not over-penalising ranked items |
| `latency_overhead_ms` | ≤ baseline × 0.15 | Reduce graph expansion hops to 0; cache expanded concept sets |
| Guardrail compliance | same or better | Do not promote; investigate any regression before next iteration |

All four criteria must pass for a **go** decision. Partial pass = **conditional go** with explicit trade-off note.
No-criteria pass = **no-go**; keep `GRAPH_RAG_VARIANT=baseline`.

#### Rollout steps (go decision)
1. Set `GRAPH_RAG_VARIANT=graph-rag` in `backend/.env` (or platform environment).
2. Re-run the backend smoke tests: `make backend-check`.
3. Run the cross-standard benchmark subset to confirm no regression after env change:
   ```
   cd backend && ../.venv/bin/python manage.py run_retrieval_benchmark \
     --tags cross-standard --top-k 20 --output docs/testing/benchmark-smoke.json
   ```
4. Monitor `retrievalLatencyMs` and `graphExpansionSource` in trace output for the first 50 live requests.
5. Record decision and metrics in `docs/testing/p5-rollout-decision.md`.

#### Rollback procedure
1. Set `GRAPH_RAG_VARIANT=baseline` in environment.
2. Restart the backend workers.
3. No DB changes or migrations required — rollback is config-only.
4. Re-run baseline-only benchmark to confirm restored to pre-rollout state:
   ```
   cd backend && ../.venv/bin/python manage.py run_retrieval_benchmark \
     --baseline-only --top-k 20 --output docs/testing/benchmark-rollback.json
   ```

#### Status
❌ **No-go (2026-04-16)**
- Current graph-RAG settings do not meet P4 thresholds.
- Keep `GRAPH_RAG_VARIANT=baseline` as default.
- Re-enter P4 tuning cycle and rerun benchmark after candidate-cap and scoring adjustments.

## Minimal API Surface Additions
- `POST /answer` option: `options.graphRagEnabled` (boolean, default false during PoC).
- Trace additions:
  - `graphExpansionHops`
  - `graphConceptIds`
  - `graphEvidenceCount`
  - `graphScoreContribution`

## Operational Notes
- Keep GraphDB as the ontology reasoning store; source of truth for text chunks remains PostgreSQL.
- Rebuild graph from indexed content if extractor logic changes.
- Version extractor output (`extractorVersion`) to keep runs auditable.

## Open Questions
1. Which relation types are allowed in production inference path?
2. How aggressive should alias merging be across standards families?
3. Should graph expansion be bounded differently by question type?
4. What is the maximum acceptable latency overhead for graph traversal?
