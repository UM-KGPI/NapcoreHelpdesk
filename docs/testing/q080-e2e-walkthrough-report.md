# Q080 End-to-End Walkthrough Report (Chapter 19 Format)

## Scope
This report documents an end-to-end test for benchmark question q080:

- Question: "How does OpRa service intensity relate to NeTEx line and network concepts?"
- Date: 2026-04-19
- Walkthrough template source: chapter 19 in [../Rules.pdf](../Rules.pdf)

Raw execution artifacts:

- Tuned unscoped run artifact: [q080-e2e-artifact-rerun-tuned.json](q080-e2e-artifact-rerun-tuned.json)
- Tuned scoped run artifact: [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)
- Ontology-only tuned unscoped run artifact: [q080-e2e-artifact-rerun-tuned-ontology-only.json](q080-e2e-artifact-rerun-tuned-ontology-only.json)
- Ontology-only tuned scoped run artifact: [q080-e2e-artifact-scoped-rerun-tuned-ontology-only.json](q080-e2e-artifact-scoped-rerun-tuned-ontology-only.json)
- Previous scoped GraphDB rerun artifact (comparison baseline): [q080-e2e-artifact-scoped-rerun-graphdb.json](q080-e2e-artifact-scoped-rerun-graphdb.json)

## Tuning Actions Applied Before This Rerun
- Added `netex:Network` + `netex:inNetwork` in the NeTEx conceptual ontology module.
- Added `opra:ServiceIntensity` + `opra:hasServiceIntensity` in the OpRa conceptual ontology module.
- Added corresponding alignment triples in `nits-netex-align.ttl` and `nits-opra-align.ttl`.
- Reloaded GraphDB (`make graphdb-load`) and validated ontology graph state (`make graphdb-verify`) before execution.

## Ontology-Only Optimization Iteration (No Retrieval/Prompt Tweaks)
- Added `nits:Network`, `nits:ServiceMetric`, and `nits:ServiceIntensity` to the core ontology.
- Added `nits:characterisesService` and `nits:appliesToNetwork` as core ontology object properties.
- Strengthened NeTEx conceptual relation: `netex:Line rdfs:subClassOf netex:Service`.
- Strengthened NeTEx alignment: `netex:Network owl:equivalentClass nits:Network`, and explicit `netex:Line rdfs:subClassOf nits:Service`.
- Strengthened OpRa alignment: `opra:ServiceIntensity owl:equivalentClass nits:ServiceIntensity` and `opra:hasServiceIntensity rdfs:subPropertyOf nits:characterisesService`.

## Purpose of This Walkthrough
Following chapter 19, this walkthrough validates that runtime orchestration proceeds from user question through semantic parsing, standard activation, retrieval, generation, policy checks, and explainability/provenance.

## Example User Question
"How does OpRa service intensity relate to NeTEx line and network concepts?"

## 2026-05-11 Stage-Profiled Benchmark Update (Control vs Graph)
To validate whether q070 optimizations generalize, we ran an in-process control-vs-graph benchmark for q080 using the same retrieval settings (`top_k=6`, `min_score=0.62`, `scope=["OpRa", "NeTEx"]`) with active bounded preselection.

Applied runtime settings:
- `GRAPHDB_TIMEOUT_SECONDS=3`
- `GRAPH_EXPANSION_MAX_CONCEPTS=8`
- `GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=12`
- `RETRIEVAL_SCORING_CANDIDATE_CAP=32`
- `RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER=2`

### Measured results
- Control mode (`graph_rag_enabled=false`):
	- retrieval latency: `~2500.0 ms`
	- top-1: `docs/opra_qm_query_model_section.md`
- Graph mode (`graph_rag_enabled=true`):
	- retrieval latency: `~15429.7 ms`
	- graph concept IDs: `8`
	- graph candidates added: `12`
	- graph evidence count: `6`
	- `retrievalGraphPreselected`: `12`
	- top evidence includes mixed OpRa + NeTEx artifacts (`opra_service_serviceIntensity.xsd`, `NeTEx_01_simple_line.xml`)

### Stage timing trace (graph-rag, q080)

```text
retrievalStageTimingsMs={
	"seedChunkEnsureMs": 1.6,
	"conceptExtractMs": 22.1,
	"graphExpandMs": 8.1,
	"conceptMetadataMs": 0.0,
	"queryEmbeddingMs": 0.3,
	"postgresCandidateQueryMs": 1.2,
	"pathHintMergeMs": 2127.0,
	"graphCandidateQueryMs": 10129.4,
	"candidatePreselectMs": 0.0,
	"candidateScoringMs": 2762.4,
	"candidateSelectionMs": 0.4,
	"trimmedPostprocessMs": 0.0,
	"coverageMetricsMs": 376.7,
	"totalMeasuredMs": 15429.4
}
```

### Interpretation
- q070 optimizations generalized to q080 behaviorally (stable mixed-standard evidence and active preselection) but not to near-control latency.
- For q080, the dominant bottleneck is `graphCandidateQueryMs` rather than scoring.
- Next performance work should focus on reducing graph candidate query fan-out/cost in cross-standard graph mode.

## Step 1: Core Concept Identification
Observed in tuned rerun trace semantic query payload:

- intent: `cross_standard_relation`
- normativity: `unspecified`
- core concept: `nits:service`
- candidate standards: `OpRa`, `NeTEx`
- ambiguity flag: `ambiguousCoreConcept: false`

Evidence:

- [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## Step 2: Standard Discovery via Alignments
### Unscoped run outcome
The unscoped run still resolved to a cross-standard RAG path in this run:

- `semanticDisambiguationRequired: false`
- `semanticFallback: PARTIAL_EVIDENCE`
- `mode: rag`
- `abstained: false`

Evidence:

- [q080-e2e-artifact-rerun-tuned.json](q080-e2e-artifact-rerun-tuned.json)

### Scoped run outcome
The question was re-run with explicit scope `["OpRa", "NeTEx"]` to execute intended cross-standard path:

- `semanticDisambiguationRequired: false`
- `standardsScope` persisted as `["OpRa", "NeTEx"]`
- final mode: `rag`
- confidence: `0.94`

Evidence:

- [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## Step 3: Competency Question Matching
In scoped run trace, rule conclusions include competency question matching:

- matched IDs: `CQ-OPRA-ROLE-01`, `CQ-OPRA-ROLE-02`
- `requiresRuleCount: 0`

This indicates the engine recognized competency-question context, but not a mandatory artifact-rule path for this query.

Evidence:

- [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## Step 4: Conditional Loading of Artifact-Derived Rules
Chapter 19 expects selective rule loading only when justified. Observed behavior in scoped run:

- trace returns ontology versions for core, standards, alignments, and artifact-rules (13 ontology/version entries)
- not strictly minimal loading in the chapter-19 sense

Note: this report records current runtime behavior, not the target ideal from chapter 19.

Evidence:

- `ontologyVersions` block in [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## Step 5: Reasoning and Evaluation
Scoped run retrieval + graph trace:

- mode: `rag`
- confidence: `0.94`
- retrieval events persisted: `6`
- evidence links persisted: `5`
- provenance records persisted: `5`
- graph expansion hops: `1`
- graph concept IDs: `netex:Line`, `netex:Service`, `opra:PublicTransportService`
- graph evidence count: `6`
- graph score contribution: `0.2`
- semantic alignment score: `0.2651`
- repository coverage count: `2`
- concept coverage count: `16`

Top retrieval paths include both OpRa and NeTEx materials, including:

- `xsd/opra_service/opra_service_serviceIntensity.xsd`
- `xsd/netex_framework/netex_reusableComponents/netex_mode_support.xsd`
- `xsd/netex_part_1/part1_tacticalPlanning/netex_commonSection_version.xsd`

Evidence:

- [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## Step 6: Explanation Assembly
Scoped run produced a policy-allowed answer with citations and provenance IDs.

Returned answer text:

The OpRa service intensity is defined through elements such as ActualServiceIntensityRequest and PlannedServiceIntensityRequest, which are structured to request actual and planned service intensities, respectively [E1], [E2]. These elements are based on the ServiceIntensityRequestStructure, indicating a standardized approach to managing service intensity data within the OpRa framework.

In relation to NeTEx, the concepts of service intensity can be linked to the broader network and line concepts, such as the CommonSection, which describes areas where multiple routes may operate in parallel and where service journeys can be synchronized [E3]. However, the specific relationship between OpRa's service intensity and NeTEx's line and network concepts is not explicitly detailed in the provided evidence. Further information would be needed to clarify how these two frameworks interact regarding service intensity.

Evidence list (IDs used in answer text):

- [E1] `xsd/netex_framework/netex_reusableComponents/netex_mode_support.xsd`
	Source: <https://github.com/TransmodelEcosystem/NeTEx/blob/de021e83a02522cff4ed936408bf927f798aae0d/xsd/netex_framework/netex_reusableComponents/netex_mode_support.xsd>
- [E2] `xsd/opra_service/opra_service_serviceIntensity.xsd`
	Source: <https://github.com/OpRa-CEN/OpRa/blob/86eaeba401ddc853d34796a383a5c92ae3ccd1c8/xsd/opra_service/opra_service_serviceIntensity.xsd>
- [E3] `xsd/netex_part_1/part1_tacticalPlanning/netex_commonSection_version.xsd`
	Source: <https://github.com/TransmodelEcosystem/NeTEx/blob/de021e83a02522cff4ed936408bf927f798aae0d/xsd/netex_part_1/part1_tacticalPlanning/netex_commonSection_version.xsd>

Citations were attached and persisted as evidence links.

Evidence:

- `response.answer`, `response.citations`, and `trace.provenanceIds` in [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## Step 7: Negative Reasoning Validation
### What was not inferred in tuned rerun
The tuned rerun did not over-assert an unsupported hard mapping:

- explicit limitation retained in answer text for unsupported direct mapping
- `semanticProvisional: true`
- `semanticProvisionalReason: LOW_RETRIEVAL_CONFIDENCE`

### Cross-standard guardrails in scoped run
Trace indicates cross-standard caution:

- `crossStandardConflict: false`
- `CROSS_STANDARD_REVIEW_RECOMMENDED` appears in `ruleConclusions`

This signals that cross-standard review remains recommended even without a detected hard conflict in this run.

Evidence:

- [q080-e2e-artifact-rerun-tuned.json](q080-e2e-artifact-rerun-tuned.json)
- [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

## End-to-End Success Criteria Check (Chapter 19)
### 1) Activates only relevant standards
- Unscoped run: yes (candidate standards and evidence came from OpRa/NeTEx path)
- Scoped run: yes (OpRa + NeTEx)

### 2) Loads rules only when justified
- Partially. Runtime traces show broad ontology/rules version payloads rather than strict minimal selective load semantics.

### 3) Answers competency questions correctly
- Partially. The run completed with RAG answer and CQ matching, and now includes an explicit evidence-bound limitation for the missing direct mapping.

### 4) Provides traceable explanations
- Yes. Retrieval IDs, evidence links, provenance records, semantic query, ontology versions, and rule conclusions are persisted.

### 5) Avoids accidental inference
- Yes. The answer avoids unsupported definitive claims and includes explicit uncertainty/limitation language.

## Improvement Delta vs Previous GraphDB Scoped Rerun
Comparison baseline: [q080-e2e-artifact-scoped-rerun-graphdb.json](q080-e2e-artifact-scoped-rerun-graphdb.json)

- Mode: unchanged (`rag` -> `rag`)
- Confidence: improved (`0.90` -> `0.94`)
- Citations count: improved (`1` -> `5`)
- Evidence links persisted: improved (`1` -> `5`)
- Provenance records persisted: improved (`1` -> `5`)
- Repository coverage count: improved (`1` -> `2`)
- Concept coverage count: improved (`2` -> `16`)
- Rule hits count: improved (`3` -> `4`)
- Cross-standard conflict: improved (`false` remains `false`, with stronger review signal preserved)
- Semantic alignment score: lower (`0.5091` -> `0.2651`)

## Tuning Iteration Delta vs Previous Local Scoped Run
Comparison baseline: [q080-e2e-artifact-scoped.json](q080-e2e-artifact-scoped.json)

- Mode: unchanged (`rag` -> `rag`)
- Confidence: unchanged (`0.94` -> `0.94`)
- Citations count: unchanged (`5` -> `5`)
- Evidence links persisted: unchanged (`5` -> `5`)
- Provenance records persisted: unchanged (`5` -> `5`)
- Semantic alignment score: unchanged (`0.2651` -> `0.2651`)
- Answer relevance wording: improved (tuned scoped answer now explicitly references NeTEx line/network context before stating evidence limits)

## Ontology-Only Iteration Delta vs Prior Tuned Scoped Run
Comparison baseline: [q080-e2e-artifact-scoped-rerun-tuned.json](q080-e2e-artifact-scoped-rerun-tuned.json)

- Mode: unchanged (`rag` -> `rag`)
- Confidence: unchanged (`0.94` -> `0.94`)
- Semantic alignment score: unchanged (`0.2651` -> `0.2651`)
- Concept coverage count: unchanged (`16` -> `16`)
- Rule hits count: unchanged (`4` -> `4`)
- Graph concept IDs: unchanged (`netex:Line`, `netex:Service`, `opra:PublicTransportService`)
- Answer text: changed (wording variation only; no measurable trace metric gain)

Interpretation:

- This iteration respected the ontology-only constraint and confirmed stable behavior.
- Additional ontology enrichment alone did not improve q080 retrieval trace metrics in the current pipeline configuration.

Interpretation:

- Pipeline robustness and traceability improved materially (more citations, links, provenance, and coverage breadth).
- The answer quality is more evidence-disciplined (explicit limitation), aligning with semantic engineering guardrails.
- Remaining quality gap is the lowered semantic alignment score, which should be monitored in follow-up tuning.

## Final Takeaway
The full API semantic pipeline was executed end-to-end for q080, including parsing, scope handling, retrieval/graph expansion, generation, policy gating, and provenance persistence.

Current operational findings:

- The scoped run successfully executes the intended OpRa+NeTEx path and produces full traceability with stronger evidence volume than the previous GraphDB rerun.
- The unscoped run no longer falls back to abstention for this specific query instance.
- Quality gap remains: direct OpRa-to-NeTEx line/network relation is still not fully grounded in retrieved evidence.
- Ontology tuning in this iteration improved wording focus, but not retrieval trace metrics; the remaining gap is primarily evidence coverage/ranking for explicit cross-standard relation passages.

## Recommended Follow-Up
1. Improve intent-specific generation prompts for cross-standard relation questions (especially service-intensity mapping).
2. Enforce stricter alignment between retrieved evidence and generated answer content before returning high-confidence responses.
3. Align runtime graph/rules activation behavior more closely with chapter 19 selective-loading expectations.
