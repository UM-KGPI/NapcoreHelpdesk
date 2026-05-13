# Benchmark Commands Quick Reference

This guide explains how to use the three operationalized benchmark tiers to validate the GraphRAG retrieval pipeline.

## Commands Summary

| Tier | Command | Runtime | Purpose | Exit Code |
|------|---------|---------|---------|-----------|
| **Canary** | `benchmark_canary` | ~60s | Commit-level feedback (5 reference questions) | 1 on gate fail |
| **Stratified** | `benchmark_stratified` | ~7 min | Pre-merge validation (30 representative questions) | 1 on gate fail |
| **Full** | `benchmark_full` | ~15 min | Release-gate validation (all 100 questions) | 0 or 1 (with `--exit-code-on-fail`) |

## Getting Started

### Prerequisites
```bash
cd /Users/andrejt/Research/repositories/git/NapcoreHelpdesk
source .venv/bin/activate
cd backend
```

### Environment
- Baseline report: `docs/testing/benchmark-graphrag-ab-2026-05-11.json` (generated 2026-05-11)
- Capability matrix: `docs/testing/capability-matrix.yaml`
- Question set: `docs/testing/benchmark-questions.yaml`

---

## Tier 1: Canary (5 Reference Questions)

Fast feedback during active development or after code changes affecting retrieval.

### Usage
```bash
python manage.py benchmark_canary [--fail-fast] [--output <path>]
```

### Example
```bash
# Run with immediate failure on errors
python manage.py benchmark_canary --fail-fast

# Custom output path
python manage.py benchmark_canary --output /tmp/my-canary-run.json
```

### Questions Included
- **q070** (example, NeTEx) — baseline slow: 13432.4 ms
- **q080** (mapping, NeTEx) — baseline slowest: 14811.9 ms
- **q067** (explanation, NeTEx) — baseline slow: 14038.8 ms
- **q098** (abstention, SIRI) — edge-case handling
- **q050** (disambiguation, OpRa) — ambiguous references

### Pass Gates
- **execution**: 0 errors
- **latency_p50**: ≤ baseline × 1.15
- **latency_p95**: ≤ baseline × 1.20
- **stage_concentration**: top-3 stages < 85% of total

### Output
```
Wrote: docs/testing/benchmark-canary-2026-05-11-200133.json
Summary: {
  "tier": "canary",
  "question_ok": 5,
  "graph_avg_ms": 9716.3,
  "gates_passed": ["execution"],
  "gates_failed": ["latency_p50: ...", "latency_p95: ..."]
}
```

---

## Tier 2: Stratified (30 Representative Questions)

Pre-merge regression detection before integrating feature branches. Balanced by intent.

### Usage
```bash
python manage.py benchmark_stratified [--fail-on-regression <pct>] [--output <path>]
```

### Example
```bash
# Default 10% regression tolerance
python manage.py benchmark_stratified

# Stricter 8% tolerance
python manage.py benchmark_stratified --fail-on-regression 8

# Custom output
python manage.py benchmark_stratified --fail-on-regression 10 --output ./my-stratified.json
```

### Questions Included (6 per intent)
- **Abstention** (6): q098, q097, q096, q095, q094, q093
- **Disambiguation** (6): q050, q051, q052, q053, q054, q055
- **Example** (6): q070, q059, q058, q057, q056, q055
- **Explanation** (9): q067, q066, q065, q064, q063, q062, q061, q058, q057
- **Mapping** (6): q080, q089, q083, q081, q082, q079

### Pass Gates
- **execution**: error rate ≤ 2% (≤1 error in 30 questions)
- **latency_avg_change**: ≤ +`<fail_on_regression>%` (default 10%)
- **latency_p95_change**: ≤ +15%
- **intent_balance**: no intent exceeds +12% avg regression

### Output
```json
{
  "summary": {
    "tier": "stratified",
    "question_count": 30,
    "question_ok": 30,
    "graph_avg_ms": 7520.9,
    "intent_summary": {
      "abstention": {"count": 6, "avg_ms": 4467.3},
      "explanation": {"count": 15, "avg_ms": 8032.0},
      ...
    },
    "gates_passed": ["execution"],
    "gates_failed": ["latency_avg_change: +43.5% vs baseline..."]
  }
}
```

---

## Tier 3: Full (100 Questions)

Release-gate validation. Typically run before tagged releases or quarterly for baseline resets.

### Usage
```bash
python manage.py benchmark_full \
  [--exit-code-on-fail] \
  [--output <path>] \
  [--baseline-file <path>]
```

### Example
```bash
# Default (no exit code)
python manage.py benchmark_full

# For CI/CD integration (exit 1 on failure)
python manage.py benchmark_full --exit-code-on-fail

# Custom baseline
python manage.py benchmark_full --baseline-file ./my-baseline.json

# All options
python manage.py benchmark_full \
  --exit-code-on-fail \
  --output ./release-validation-2026-05-11.json \
  --baseline-file ./benchmark-graphrag-ab-2026-05-11.json
```

### Pass Gates (Strict)
- **execution**: 0 errors
- **latency_avg_change**: ≤ +8%
- **latency_p50_change**: ≤ +12%
- **latency_p95_change**: ≤ +15%
- **tail_performance**: top-10 slowest avg ≤ +10%
- **intent_coverage**: all 5 intents present

### Output
```json
{
  "summary": {
    "question_count_total": 100,
    "question_count_ok": 100,
    "global_stats": {
      "control_avg_ms": 1507.3,
      "graph_avg_ms": 5241.3,
      "graph_p95_ms": 9851.3
    },
    "gates_passed": [...],
    "gates_failed": [...]
  },
  "results": [...]
}
```

---

## Workflow: Development → Pre-Merge → Release

### During Development (After Code Changes)
```bash
# Test a commit-level change quickly
python manage.py benchmark_canary --fail-fast

# If gates pass, continue; if fail, profile the hotspots
```

### Before Merge to Main
```bash
# Stratified pre-merge check
python manage.py benchmark_stratified --fail-on-regression 10

# If gates pass, safe to merge; if fail, request performance review
```

### Before Release Tag
```bash
# Full benchmark for release approval
python manage.py benchmark_full --exit-code-on-fail --output ./release-check.json

# If gates pass (exit 0), release is approved
# If gates fail (exit 1), attach performance report and request exception
```

---

## Investigating Failures

### Step 1: Identify which stage is regressing
Look at the JSON output's `retrievalStageTimingsMs` in the failing question:
```json
"trace": {
  "retrievalStageTimingsMs": {
    "graphCandidateQueryMs": 2500,
    "candidateScoringMs": 3000,
    "pathHintMergeMs": 1500
  }
}
```

### Step 2: Compare to baseline
Extract the same question from the baseline report and compare stage times.

### Step 3: Profile the code
- If `graphCandidateQueryMs` spiked: check GraphDB query or concept expansion
- If `candidateScoringMs` spiked: check ranking logic or candidate set size
- If `pathHintMergeMs` spiked: check path hint generation or merge logic

### Step 4: Run diagnostics
```bash
# Run canary on the specific slow question only
python manage.py benchmark_canary --fail-fast

# Extract trace from output JSON
cat benchmark-canary-*.json | jq '.results[] | select(.id == "q080").graph.trace'
```

---

## Settings to Tune

Reference: `backend/.env` and `backend/config/settings.py`

| Setting | Default | Impact | Range |
|---------|---------|--------|-------|
| `GRAPHDB_TIMEOUT_SECONDS` | 3 | GraphDB SPARQL timeout | 1–10 s |
| `GRAPH_EXPANSION_MAX_CONCEPTS` | 8 | Max expanded concepts | 4–16 |
| `GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS` | 12 | Max candidate chunks per concept | 6–24 |
| `RETRIEVAL_SCORING_CANDIDATE_CAP` | 32 | Max candidates to score | 16–64 |
| `RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER` | 2 | Preselect multiplier before scoring | 1–4 |
| `RETRIEVAL_MAX_SAME_SOURCE_PATH` | 1 | Max results from same source file | 0–3 |

**Tuning guidance:**
- Decrease multiplier/caps → faster, less accurate
- Increase multiplier/caps → slower, more accurate
- Always run stratified or full after changing these settings

---

## Related Documentation
- Architecture: [Query-to-Evidence Methodology](../architecture/query-to-evidence-methodology.md)
- Gates definitions: [Benchmark Regression Testing Strategy and Gates](benchmark-regression-gates.md)
- Capability matrix: [capability-matrix.yaml](capability-matrix.yaml)
- Baseline results: [benchmark-graphrag-ab-2026-05-11.md](benchmark-graphrag-ab-2026-05-11.md)
