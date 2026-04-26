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
- additional core concepts: `nits:line`
- ambiguity flag: `ambiguousCoreConcept: true`

Run-specific candidate standards:

- unscoped run: `NeTEx`, `OpRa`, `SIRI`
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
Unscoped execution still flagged semantic ambiguity, but now completed retrieval and answer generation:

- `semanticDisambiguationRequired: true`
- `semanticFallback: AMBIGUOUS_CORE_CONCEPT`
- `mode: rag`
- `abstained: false`
- `confidence: 0.94`

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
Competency question matching is now recorded in both refreshed rerun artifacts:

- unscoped `ruleHitsCount: 2`
- scoped `ruleHitsCount: 2`
- rule conclusion types include `COMPETENCY_QUESTION_MATCH` and `ONTOLOGY_ANCHOR_PRESENT`

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 4: Conditional Loading of Artifact-Derived Rules
Observed behavior:

- unscoped run returned ontology version payload across core, standards, alignments, and artifact-rules modules
- scoped run returned the same ontology version payload family

This indicates that after the q070 parser/retrieval adjustments, both runs now proceed far enough into evidence-backed retrieval to emit ontology version provenance.

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 5: Reasoning and Evaluation
### Unscoped run
- mode: `rag`
- confidence: `0.94`
- retrieval events persisted: `6`
- evidence links persisted: `5`
- provenance records persisted: `5`
- graph concept IDs: `netex:Line`, `netex:ScheduledStopPoint`, `opra:StopPoint`, `siri:Stop`
- graph expansion hops: `1`
- graph evidence count: `6`
- graph score contribution: `0.2`
- repository coverage count: `1`
- concept coverage count: `23`
- semantic alignment score: `0.6437`

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
- semantic alignment score: `0.6437`

Top scoped citations include NeTEx example sources such as:

- `examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml`
- `examples/functions/timetable/Netex_08.1_BusTram_Timetable_AmbiguousLinks.xml`
- `examples/standards/gtfs/Netex_gtfs_exm1_Stops_1.xml`

Important remaining gap:

- expected `examples/functions/line/NeTEx_01_simple_line.xml` is still not present in top citations
- retrieval quality improved for example-shaped output, but source selection is still not the best available simple-line artifact

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 6: Explanation Assembly
### Unscoped run answer
- Unscoped run now returns a grounded answer even though semantic disambiguation remains flagged in trace metadata.

### Scoped run answer
Scoped run produced a citation-backed RAG answer with 5 citations and persisted provenance IDs.

Returned answer text:

Here is a simple NeTEx XML example for a line with stop points, based on the provided evidence:

```xml
<Network>
	<StopPlace id="stopPlace_001">
		<Name>Stop Place A</Name>
		<Quay>
			<Name>Quay A</Name>
		</Quay>
	</StopPlace>
	<StopPlace id="stopPlace_002">
		<Name>Stop Place B</Name>
		<Quay>
			<Name>Quay B</Name>
		</Quay>
	</StopPlace>
	<ScheduledStopPoint id="SSP_001">
		<Name>Scheduled Stop Point A</Name>
		<Location>
			<Latitude>36.905697</Latitude>
			<Longitude>-116.76218</Longitude>
		</Location>
	</ScheduledStopPoint>
	<ScheduledStopPoint id="SSP_002">
		<Name>Scheduled Stop Point B</Name>
		<Location>
			<Latitude>36.641496</Latitude>
			<Longitude>-116.40094</Longitude>
		</Location>
	</ScheduledStopPoint>
	<StopAssignment>
		<StopPlaceRef ref="stopPlace_001"/>
		<ScheduledStopPointRef ref="SSP_001"/>
	</StopAssignment>
	<StopAssignment>
		<StopPlaceRef ref="stopPlace_002"/>
		<ScheduledStopPointRef ref="SSP_002"/>
	</StopAssignment>
</Network>
```

This example illustrates the relationship between stop places and scheduled stop points, as well as the use of stop assignments to link them, which is consistent with the NeTEx structure described in the evidence [E1], [E6]. However, specific details such as service patterns or journey patterns are not included in the evidence provided, so they cannot be safely added to this example.

Evidence list (IDs used in answer text):

- [E1] `examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml`
	Source: <https://github.com/NeTEx-CEN/NeTEx/blob/de021e83a02522cff4ed936408bf927f798aae0d/examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml>
- [E6] Trace-level graph evidence item counted in `trace.graphEvidenceCount = 6` for this answer.
	Note: `response.citations` persists 5 items, so this additional evidence reference is trace-level rather than a separate emitted citation row.

Rerun quality note: output is materially better aligned with the user's requested format (example XML) and remains policy-safe by limiting details to what is supported by retrieved evidence.
Post-fix quality note: parser and retrieval changes improved term extraction (`line`, `stop`, `example`) and reduced schema-heavy drift for example-XML queries, but they did not yet lift the canonical `functions/line` example into top citations.

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## Step 7: Negative Reasoning Validation
### What was not inferred
- The system still avoided unsupported service-pattern/journey-pattern details that were not present in retrieved evidence.
- No unsupported hard cross-standard mapping claims were introduced.

### Cross-standard guardrails
- `crossStandardConflict: false` in both runs.
- Unscoped run still records `semanticDisambiguationRequired: true`, which is an important caution signal even though it produced a grounded answer.
- Scoped run remained within NeTEx scope and repository coverage count stayed at 1 repository.

Evidence:

- [q070-e2e-artifact-rerun.json](q070-e2e-artifact-rerun.json)
- [q070-e2e-artifact-scoped-rerun.json](q070-e2e-artifact-scoped-rerun.json)

## End-to-End Success Criteria Check (Chapter 19)
### 1) Activates only relevant standards
- Unscoped run: partially (candidate standards still span `NeTEx`, `OpRa`, `SIRI`, although the returned evidence stayed inside NeTEx repository material).
- Scoped run: yes (NeTEx-only scope).

### 2) Loads rules only when justified
- Partially. Both refreshed runs now carry ontology version payloads, so runtime behavior is broader than the strict selective-loading ideal.

### 3) Answers competency questions correctly
- Partially. The refreshed run returns grounded XML-shaped answers with stronger term extraction and competency-question matching, but answer specificity for the canonical simple-line source remains incomplete because `functions/line/NeTEx_01_simple_line.xml` is still not retrieved.

### 4) Provides traceable explanations
- Yes (scoped run). Retrieval IDs, evidence links, provenance IDs, semantic query, and ontology versions were persisted.

### 5) Avoids accidental inference
- Yes. Both runs remain evidence-backed and avoid unsupported service/journey structure details.

## Improvement Delta (Scoped vs Unscoped in rerun)
- Mode: unchanged (`rag` -> `rag`)
- Confidence: unchanged (`0.94` -> `0.94`)
- Citations count: unchanged (`5` -> `5`)
- Retrieval events persisted: unchanged (`6` -> `6`)
- Evidence links persisted: unchanged (`5` -> `5`)
- Provenance records persisted: unchanged (`5` -> `5`)
- Semantic alignment score: unchanged (`0.6437` -> `0.6437`)

Interpretation:

- Scope is no longer required to get a grounded answer, but it still removes standards ambiguity from the trace.
- The remaining problem is no longer abstention; it is source quality and source selection.

## Rerun Delta vs Previous Scoped Run
- Mode: unchanged (`rag` -> `rag`)
- Confidence: improved (`0.9` -> `0.94`)
- Traceability: unchanged high (`5` citations, `5` evidence links, `5` provenance records)
- Answer relevance: improved (direct XML example returned, with better line/stop/example term capture)
- Best-source retrieval: unchanged gap (`functions/line/NeTEx_01_simple_line.xml` still absent)

## Final Takeaway
The q070 pipeline executed end-to-end with both unscoped and NeTEx-scoped runs. After the parser and retrieval adjustments, both runs now return grounded XML-style answers with strong traceability and competency-question matches. However, the key retrieval defect remains unresolved: the best canonical simple-line artifact is still not selected.

Current operational finding:

- Explicit scope still improves trace clarity by removing cross-standard ambiguity, but it does not yet fix the missing `functions/line` citation family.

## Recommended Follow-Up
1. Add prompt shaping for `intent=example` to prioritize concise, directly requested XML example output format.
2. Continue retrieval tuning without hard-coded path boosts so `line`-family example evidence outranks timetable/stop examples on semantic merit.
3. Add a targeted regression check for q070 to ensure scoped run keeps >=1 expected `functions/line`-family citation near top results.
