# Benchmark Regression Testing Strategy and Gates

## Purpose
This document defines the three-tier regression testing approach (canary, stratified, full) that operationalizes the capability-matrix governance model referenced in [Query-to-Evidence Methodology](../architecture/query-to-evidence-methodology.md).

Each tier serves a different phase of the development lifecycle:
- **Canary**: Fast feedback during active development (single-question validation)
- **Stratified**: Medium-cost pre-integration verification (representative subset by capability/intent)
- **Full**: Release-gate validation (all 100 benchmark questions)

## Baseline: All-100 Control-vs-Graph (2026-05-11)

Before defining gates, establish the empirical baseline from the full 100-question A/B run:

**Reference artifacts:**
- Machine-readable: [benchmark-graphrag-ab-2026-05-11.json](benchmark-graphrag-ab-2026-05-11.json)
- Human-readable: [benchmark-graphrag-ab-2026-05-11.md](benchmark-graphrag-ab-2026-05-11.md)

**Global baseline under documented settings:**
- Control average: 1507.3 ms
- Graph average: 5241.3 ms
- Graph/control ratio: 5.229
- Graph p95: 9851.3 ms
- Graph slower on: 100/100 questions

**Intent-level baselines:**
| Intent | Control Avg (ms) | Graph Avg (ms) | Delta Avg (ms) |
|--------|------------------|----------------|----------------|
| abstention | 1677.9 | 5077.3 | 3399.5 |
| disambiguation | 1719.5 | 5816.6 | 4097.1 |
| example | 863.5 | 4477.6 | 3614.0 |
| explanation | 1406.3 | 5077.8 | 3671.5 |
| mapping | 2337.2 | 6570.1 | 4233.0 |

## Tier 1: Canary Tests

### Purpose
Provide immediate feedback during code iteration on a single reference question per capability slice. Used after commit-level changes to retrieval, scoring, or query expansion logic.

### Scope
- **Regression type**: targeted capability (e.g., "graph candidate query latency spike")
- **Questions**: one representative per intent (5 total)
- **Runtime**: < 60 seconds per change validation

### Representative Questions
| Intent | Question ID | Rationale |
|--------|------------|-----------|
| example | q070 | reference for answer example queries (known slow: 13432.4 ms baseline) |
| mapping | q080 | reference for ontology mapping intents (known slowest: 14811.9 ms baseline) |
| explanation | q067 | reference for explanatory queries (known slow: 14038.8 ms baseline) |
| abstention | q098 | reference for graceful edge-case handling |
| disambiguation | q050 | reference for ambiguous standard references |

### Pass/Fail Gates
For each question run in **graph mode** (graph-rag-enabled=true):

| Gate Name | Metric | Pass Condition | Fail Condition | Action on Fail |
|-----------|--------|-----------------|-----------------|----------------|
| **execution** | error count | 0 errors | any error | rollback change |
| **latency_p50** | query time (ms) | ≤ baseline * 1.15 | > baseline * 1.15 | investigate hotspot |
| **latency_p95** | max query time (ms) | ≤ baseline * 1.20 | > baseline * 1.20 | profile and optimize |
| **stage_concentration** | top-3 stages % of total | < 85% | ≥ 85% | check for new bottleneck |

### Example Invocation
```bash
# Run canary subset
cd backend
../.venv/bin/python manage.py benchmark_canary \
  --questions q070,q080,q067,q098,q050 \
  --baseline-file ../docs/testing/benchmark-graphrag-ab-2026-05-11.json \
  --fail-fast
```

## Tier 2: Stratified Tests

### Purpose
Provide medium-cost pre-integration regression detection for semantic, graph, or retrieval changes. Executed before merging feature branches into main.

### Scope
- **Regression type**: cross-capability impact (e.g., graph settings change)
- **Questions**: representative subset stratified by intent (25–30 total)
- **Runtime**: < 5–7 minutes per validation

### Question Selection Strategy
Sample 5–6 questions per intent group, preferring:
1. Known high-latency outliers (top quartile by baseline)
2. Diverse standards (NeTEx, SIRI, OpRa, DATEX II)
3. Mix of fast and slow within each intent

**Suggested stratified set (25 questions):**
- Abstention: q098, q097, q096, q095, q094, q093
- Disambiguation: q050, q051, q052, q053, q054, q055
- Example: q070, q059, q058, q057, q056, q055
- Explanation: q067, q066, q065, q064, q063, q062
- Mapping: q080, q089, q083, q081, q082, q079

### Pass/Fail Gates
For stratified subset in **graph mode**:

| Gate Name | Metric | Pass Condition | Fail Condition | Action on Fail |
|-----------|--------|-----------------|-----------------|----------------|
| **execution** | error rate | ≤ 2% (≤1 error in 25 q's) | > 2% | rollback, debug errors |
| **latency_avg_change** | avg ms vs baseline | ≤ +10% | > +10% | investigate retrieval path |
| **latency_p95_change** | p95 ms vs baseline | ≤ +15% | > +15% | profile stages, check settings |
| **intent_balance** | max intent regression | any intent ≤ +12% avg | any intent > +12% avg | check intent-specific hotspot |

### Example Invocation
```bash
# Run stratified pre-merge validation
cd backend
../.venv/bin/python manage.py benchmark_stratified \
  --baseline-file ../docs/testing/benchmark-graphrag-ab-2026-05-11.json \
  --fail-on-regression 10 \
  --output ../docs/testing/benchmark-stratified-check-$(date +%Y-%m-%d).json
```

## Tier 3: Full Benchmark Run

### Purpose
Release-gate validation across the entire 100-question portfolio. Executed before tagged releases and periodically for regression baseline updates.

### Scope
- **Regression type**: portfolio-level impact
- **Questions**: all 100 benchmark questions
- **Runtime**: ~12 minutes (current baseline: 674.9 s)
- **Frequency**: before every release; quarterly baseline resets

### Pass/Fail Gates
For all 100 questions in **graph mode**:

| Gate Name | Metric | Pass Condition | Fail Condition | Action on Fail |
|-----------|--------|-----------------|-----------------|----------------|
| **execution** | error rate | 0 errors | any error | debug, do not release |
| **latency_avg_change** | avg ms vs baseline | ≤ +8% | > +8% | assess business impact |
| **latency_p50_change** | p50 ms vs baseline | ≤ +12% | > +12% | profile and optimize |
| **latency_p95_change** | p95 ms vs baseline | ≤ +15% | > +15% | mandatory optimization pass |
| **tail_performance** | slowest 10 avg vs baseline | ≤ +10% | > +10% | check outlier causes |
| **intent_coverage** | all intents have results | 5/5 intents present | < 5 intents | update test data |

### Output Artifacts
Generate two files after full run:

1. **JSON payload** (`benchmark-graphrag-ab-{date}.json`): Machine-readable results for scripted gates and historical tracking
2. **Markdown summary** (`benchmark-graphrag-ab-{date}.md`): Human-readable report for review and decision records

### Release Decision Logic
```
IF (latency_p95_change > 15% OR any latency_avg_change > 8%) THEN
  require_explicit_release_approval = true
  attach_profiling_report = true
  document_business_justification = true
ELSE
  release_approved = true
END
```

## Example Invocation
```bash
# Run full 100-question release validation
cd backend
../.venv/bin/python manage.py benchmark_full \
  --baseline-file ../docs/testing/benchmark-graphrag-ab-2026-05-11.json \
  --generate-report \
  --exit-code-on-fail
```

## Guidance for New Development

### Adding a new retrieval stage or gate

1. Profile the canary set to confirm the stage appears
2. Add stage name to `stage_keys` tracking in benchmark runner
3. If stage is consistently > 100 ms, document target budget in YAML alongside stage definition
4. Update intent-level baselines if stage affects particular intents

### Changing a GraphDB or semantic setting

1. Run canary on affected intent (e.g., GRAPH_EXPANSION_MAX_CONCEPTS → example intent)
2. If canary passes, run stratified before merge
3. If stratified passes, merge and schedule full run before release

### Investigating a regression

1. Extract the specific question from the JSON artifact
2. Run with `--verbose-trace` to extract stage timings
3. Compare stage timings to baseline JSON for the same question
4. Focus on largest time delta vs baseline

## Related Docs
- [Query-to-Evidence Methodology](../architecture/query-to-evidence-methodology.md) — capability-matrix governance and empirical basis
- [q070 E2E Walkthrough](q070-e2e-walkthrough-report.md) — single-question profiling methodology
- [q080 E2E Walkthrough](q080-e2e-walkthrough-report.md) — comparison example
- [Local Run Quickstart](local-run-quickstart.md) — environment setup for benchmark execution
