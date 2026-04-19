# Q070 End-to-End Walkthrough Report (Chapter 19 Format)

## Scope
This report documents an end-to-end test for benchmark question q070:

- Question: "Show me a NeTEx XML example for a simple line with stop points."
- Date: 2026-04-19
- Walkthrough template source: chapter 19 in [../Rules.pdf](../Rules.pdf)

Raw execution artifacts:

- Previous unscoped run artifact: [q070-e2e-artifact.json](q070-e2e-artifact.json)
- Previous scoped run artifact: [q070-e2e-artifact-scoped.json](q070-e2e-artifact-scoped.json)
- Rerun unscoped artifact: [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- Rerun scoped artifact: [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Purpose of This Walkthrough
Following chapter 19, this walkthrough validates runtime orchestration from user question through semantic parsing, standard activation, retrieval, generation, policy checks, and explainability/provenance.

## Example User Question
"Show me a NeTEx XML example for a simple line with stop points."

## Step 1: Core Concept Identification
Observed semantic payload in the rerun artifacts:

- intent: `unknown`
- normativity: `unspecified`
- core concept: `nits:stop`
- additional core concepts: `nits:service`, `nits:spatialentity`
- ambiguity flag: `ambiguousCoreConcept: true`

Run-specific candidate standards:

- unscoped run: `DATEX II`, `NeTEx`, `OpRa`, `SIRI`
- scoped run: `NeTEx`

Direct concept matches (from rerun trace plus live GraphDB-backed mapping resolution):

| Direct concept ID | Current NITS mapping | Notes |
| --- | --- | --- |
| `netex:Line` | `nits:line` | Updated from broad service mapping to explicit line concept |
| `netex:ScheduledStopPoint` | `nits:stop` | Explicit stop alignment retained |
| `opra:StopPoint` | `nits:stop` | Cross-standard stop concept |
| `siri:Stop` | `nits:stop` | Cross-standard stop concept |

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 2: Standard Discovery via Alignments
### Unscoped run outcome
Unscoped execution required semantic disambiguation and resulted in safe abstention:

- `semanticDisambiguationRequired: true`
- `semanticFallback: AMBIGUOUS_CORE_CONCEPT`
- `mode: abstain`
- `abstained: true`
- `abstentionReason: INSUFFICIENT_EVIDENCE`

### Scoped run outcome
Scoped execution with `standardsScope=["NeTEx"]` completed retrieval and answer generation:

- `semanticDisambiguationRequired: false`
- final `mode: rag`
- `confidence: 0.94`
- `abstained: false`

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 3: Competency Question Matching
No competency question matching was recorded in this run:

- unscoped `ruleHitsCount: 0`
- scoped `ruleHitsCount: 1`
- scoped rule conclusion type: `ONTOLOGY_ANCHOR_PRESENT`

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 4: Conditional Loading of Artifact-Derived Rules
Observed behavior:

- unscoped run returned no ontology version payload (`ontologyVersions: []`)
- scoped run returned ontology version payload across core, standards, alignments, and artifact-rules modules

This indicates selective behavior in practice for this question path: broad ontology version payload appears after scope-constrained, evidence-backed retrieval, while ambiguous unscoped execution remained minimal.

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 5: Reasoning and Evaluation
### Unscoped run
- mode: `abstain`
- confidence: `0.0`
- retrieval events persisted: `0`
- evidence links persisted: `0`
- provenance records persisted: `0`
- graph concept IDs: `netex:Line`, `netex:ScheduledStopPoint`, `opra:StopPoint`, `siri:Stop`
- semantic alignment score: `0.0`

### Scoped run
- mode: `rag`
- confidence: `0.94`
- retrieval events persisted: `6`
- evidence links persisted: `5`
- provenance records persisted: `5`
- graph expansion hops: `1`
- graph evidence count: `6`
- graph score contribution: `0.2`
- repository coverage count: `1`
- concept coverage count: `23`
- semantic alignment score: `0.6438`

Top scoped citations include NeTEx example sources such as:

- `examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml`
- `examples/functions/timetable/Netex_08.1_BusTram_Timetable_AmbiguousLinks.xml`
- `examples/standards/gtfs/Netex_gtfs_exm1_Stops_1.xml`

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 6: Explanation Assembly
### Unscoped run answer
- "I do not have sufficient approved-source evidence to answer this safely."

### Scoped run answer
Scoped run produced a citation-backed RAG answer with 5 citations and persisted provenance IDs.

Returned answer text:

- The rerun now returns a direct XML example response containing `StopPlace`, `ScheduledStopPoint`, and `StopAssignment`, instead of only generic implementation guidance.

Rerun quality note: output is materially better aligned with the user's requested format (example XML). It still states that a complete full-line multi-stop structure is not fully evidenced, which keeps the response policy-safe.

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 7: Negative Reasoning Validation
### What was not inferred
- Unscoped run abstained instead of hallucinating across multiple candidate standards.
- No unsupported hard cross-standard mapping claims were introduced.

### Cross-standard guardrails
- `crossStandardConflict: false` in both runs.
- Scoped run remained within NeTEx scope and repository coverage count stayed at 1 repository.

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## End-to-End Success Criteria Check (Chapter 19)
### 1) Activates only relevant standards
- Unscoped run: partially (multiple candidate standards triggered due ambiguous core concept).
- Scoped run: yes (NeTEx-only scope).

### 2) Loads rules only when justified
- Mostly yes for this scenario. Unscoped ambiguous path stayed minimal; scoped retrieval path carried ontology version payload.

### 3) Answers competency questions correctly
- Partially. The scoped run returned a grounded answer with strong traceability, but answer specificity for "simple line with stop points" can be improved.

### 4) Provides traceable explanations
- Yes (scoped run). Retrieval IDs, evidence links, provenance IDs, semantic query, and ontology versions were persisted.

### 5) Avoids accidental inference
- Yes. Unscoped path abstained safely; scoped path remained evidence-backed.

## Improvement Delta (Scoped vs Unscoped in rerun)
- Mode: improved (`abstain` -> `rag`)
- Confidence: improved (`0.0` -> `0.94`)
- Citations count: improved (`0` -> `5`)
- Retrieval events persisted: improved (`0` -> `6`)
- Evidence links persisted: improved (`0` -> `5`)
- Provenance records persisted: improved (`0` -> `5`)
- Semantic alignment score: improved (`0.0` -> `0.6438`)

Interpretation:

- Scope-constraining to NeTEx resolves ambiguity and activates successful retrieval/generation.
- Rerun answer targeting improved: the scoped response now returns a direct XML-style example instead of generic timetable guidance.

## Rerun Delta vs Previous Scoped Run
- Mode: unchanged (`rag` -> `rag`)
- Confidence: improved (`0.9` -> `0.94`)
- Traceability: unchanged high (`5` citations, `5` evidence links, `5` provenance records)
- Answer relevance: improved (direct XML example now provided in scoped answer)

## Final Takeaway
The q070 pipeline executed end-to-end with both unscoped and NeTEx-scoped runs. The unscoped run behaved safely with abstention under ambiguity, and the scoped run produced a traceable citation-backed answer with strong retrieval signals.

Current operational finding:

- For this benchmark query, explicit scope materially improves quality and should be preferred when user intent can be safely narrowed.

## Recommended Follow-Up
1. Add prompt shaping for `intent=example` to prioritize concise, directly requested XML example output format.
2. Rank "simple line" example artifacts higher when the query includes "simple line" and "stop points" terms.
3. Add a targeted regression check for q070 to ensure scoped run keeps >=1 expected `functions/line`-family citation near top results.
