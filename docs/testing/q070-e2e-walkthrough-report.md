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

## 2026-05-11 Pipeline Benchmark Update (Control vs Graph)
To validate the current pipeline after ontology relationship enrichment (SIRI and NeTEx object properties), we ran an additional q070-style A/B benchmark with the same user question and retrieval parameters (`top_k=6`, `min_score=0.62`, `scope=["NeTEx"]`).

### Benchmark setup
- Control mode: `graph_rag_enabled=false`
- Graph mode: `graph_rag_enabled=true`
- Same PostgreSQL/pgvector index and same ontology dataset in GraphDB
- Retrieval measured in-process via `retrieve_chunks_with_trace` to isolate retrieval semantics from generation variability

### Measured results
- Control mode:
	- retrieval latency: `~2769.4 ms`
	- top results dominated by timetable examples
	- canonical `examples/functions/line/NeTEx_01_simple_line.xml` was not top-ranked
	- semantic alignment score: `0.4015`
- Graph mode:
	- retrieval latency: `~85594.9 ms`
	- canonical `examples/functions/line/NeTEx_01_simple_line.xml` became top-ranked
	- graph concept IDs: `11`
	- graph candidates added: `6`
	- graph evidence count: `6`
	- graph score contribution: `0.34`
	- semantic alignment score: `0.4164`

### Interpretation
- Retrieval relevance improved for q070 intent: the pipeline now surfaces the expected canonical simple-line example when graph expansion is active.
- Operational latency regressed significantly under graph-enabled mode, causing the API-level q070 regression script to time out at the current 30-second client timeout.
- Therefore, current status is a quality/latency tradeoff: better source targeting, but not yet production-ready response time for this benchmark path.

## Runtime Query Trace (SPARQL and SQL)
The following query forms document how q070 flows from semantic expansion to hybrid candidate retrieval.

### SPARQL query used for concept expansion (GraphDB)
This is the runtime pattern used by `query_graphdb_concept_expansion` for graph-enabled retrieval.

```sparql
SELECT DISTINCT ?related WHERE {
	VALUES ?seed { <https://netex.org.uk/netex/2.0#Line> <https://netex.org.uk/netex/2.0#ScheduledStopPoint> }
	VALUES ?g {
		<https://napcore.eu/graph/standards/netex>
		<https://napcore.eu/graph/alignments/netex>
	}
	GRAPH ?g {
		?seed ((<http://www.w3.org/2004/02/skos/core#related>
					| <http://www.w3.org/2004/02/skos/core#relatedMatch>
					| <http://www.w3.org/2004/02/skos/core#exactMatch>
					| <http://www.w3.org/2004/02/skos/core#closeMatch>)
					|^(<http://www.w3.org/2004/02/skos/core#related>
					| <http://www.w3.org/2004/02/skos/core#relatedMatch>
					| <http://www.w3.org/2004/02/skos/core#exactMatch>
					| <http://www.w3.org/2004/02/skos/core#closeMatch>)) ?related .
	}
	FILTER(isIRI(?related))
}
```

Notes:
- Seeds shown above are representative q070 concepts (`Line`, `ScheduledStopPoint`) from the semantic extraction stage.
- Runtime may send a different seed list based on current parsing output and scope.

Observed runtime result (2026-05-11, q070 question, NeTEx scope):

```text
endpoint= http://localhost:7200/repositories/napcore-helpdesk
repository= napcore-helpdesk
seeds= ['netex:Line', 'netex:ScheduledStopPoint']
related_count= 0
```

Interpretation:
- For this specific seed set, GraphDB SKOS-path expansion returned no additional related concept IDs.
- This is expected for a strict SKOS-only expansion query when source concepts have no matching SKOS edges in the selected named graphs.

### SQL query pattern used for hybrid candidate retrieval (PostgreSQL + pgvector)
This is the SQL-equivalent shape produced by `_postgres_hybrid_candidates` for q070 candidate retrieval.

```sql
SELECT
	sc.*,
	ts_rank(
		setweight(to_tsvector('english', coalesce(sc.text, '')), 'A') ||
		setweight(to_tsvector('english', coalesce(sc.source_path, '')), 'A') ||
		setweight(to_tsvector('english', coalesce(sc.label, '')), 'B') ||
		setweight(to_tsvector('english', coalesce(sc.heading, '')), 'B'),
		plainto_tsquery('english', :question)
	) AS lexical_rank,
	(sc.embedding_vector <=> :query_embedding) AS vector_distance,
	(1 - (sc.embedding_vector <=> :query_embedding)) AS vector_similarity
FROM helpdesk_sourcechunk sc
WHERE sc.standards_scope @> :scope_jsonb
ORDER BY vector_similarity DESC, lexical_rank DESC
LIMIT :candidate_limit;
```

Representative q070 parameters:
- `:question` = `Show me a NeTEx XML example for a simple line with stop points.`
- `:scope_jsonb` = `["NeTEx"]`
- `:candidate_limit` = `max(25, top_k * 5)`

Notes:
- This SQL is the operational equivalent of the Django ORM path used in runtime.
- Final top-k scoring then adds quality, intent/path, and graph-based adjustments before citations are selected.

Observed runtime result (2026-05-11, q070 question, NeTEx scope):

```text
row_count= 8
1. examples/functions/timetable/Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml | lexical_rank=1.000000 | vector_similarity=0.466360
2. examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml | lexical_rank=1.000000 | vector_similarity=0.450050
3. examples/functions/timetable/Netex_51.1_Occupancy.xml | lexical_rank=1.000000 | vector_similarity=0.447306
4. examples/functions/timetable/Netex_01.2_Bus_SimpleTimetable_WithTimings.xml | lexical_rank=1.000000 | vector_similarity=0.444554
5. examples/functions/timetable/Netex_01.4_Bus_SimpleTimetable_WithConnection.xml | lexical_rank=1.000000 | vector_similarity=0.439642
6. examples/functions/timetable/Netex_09.2_Bus_SimpleTimetable_Slovenia.xml | lexical_rank=1.000000 | vector_similarity=0.410146
7. examples/functions/timetable/Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml | lexical_rank=1.000000 | vector_similarity=0.405840
8. examples/functions/simpleNetwork/Netex_SimpleNetwork_1.xml | lexical_rank=1.000000 | vector_similarity=0.396596
```

Interpretation:
- The hybrid SQL candidate stage favors timetable/example artifacts for q070 lexical tokens.
- In the current pipeline, canonical simple-line evidence (`examples/functions/line/NeTEx_01_simple_line.xml`) is surfaced later by graph-aware candidate expansion and reranking, not by this SQL candidate query alone.

### Final reranked top-k comparison (control vs graph-rag)
The block below shows the final retrieval output after full reranking (`retrieve_chunks_with_trace`), not only the initial SQL candidate set.

Observed runtime result (2026-05-11, q070 question, NeTEx scope):

```text
CONTROL (graph_rag_enabled=false)
time_ms=2797.6
graphConceptIds=0
graphCandidatesAdded=0
graphEvidenceCount=0
graphScoreContribution=0.0
1. examples/functions/timetable/Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml | score=1.000000
2. examples/functions/timetable/Netex_21_Rail_NetworkTimetable_eurostar.xml | score=1.000000
3. examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml | score=1.000000
4. examples/functions/timetable/Netex_51.1_Occupancy.xml | score=1.000000
5. examples/functions/timetable/Netex_09.2_Bus_SimpleTimetable_Slovenia.xml | score=1.000000
6. examples/functions/timetable/Netex_01.4_Bus_SimpleTimetable_WithConnection.xml | score=1.000000

GRAPH-RAG (graph_rag_enabled=true)
time_ms=82942.1
graphConceptIds=11
graphCandidatesAdded=6
graphEvidenceCount=6
graphScoreContribution=0.34
1. examples/functions/line/NeTEx_01_simple_line.xml | score=1.000000
2. examples/functions/line/NeTEx_01_simple_line.xml | score=1.000000
3. examples/standards/fxc/FX-PI-01_UK_MB_LINE_FARE_MB-Line-1-trip-(Z2Z-basic)_20170101.xml | score=1.000000
4. examples/standards/txc/uk_nap_extract1_minimal.xml | score=1.000000
5. examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml | score=1.000000
6. examples/functions/fares/Netex_101.21_TfL_GeographicFares_UnitZone_MultipleProduct.xml | score=1.000000
```

Interpretation:
- Control mode keeps lower latency but does not prioritize the canonical simple-line artifact.
- Graph-rag mode promotes `examples/functions/line/NeTEx_01_simple_line.xml` to top rank, confirming semantic reranking impact.
- The same run also confirms current latency regression in graph-rag mode, so optimization remains required before default rollout.

### Compact metrics summary

| Metric | Control (`graph_rag_enabled=false`) | Graph-rag (`graph_rag_enabled=true`) |
| --- | --- | --- |
| Retrieval latency (ms) | 2797.6 | 82942.1 |
| Graph concept IDs | 0 | 11 |
| Graph candidates added | 0 | 6 |
| Graph evidence count | 0 | 6 |
| Graph score contribution | 0.0 | 0.34 |
| Canonical simple-line source in top-1 | No | Yes |

### Post-tuning trial (2026-05-11, recommended path follow-up)
After applying conservative graph tuning in [backend/.env](../../backend/.env) and reducing graph alias fan-out in [backend/helpdesk/services/retrieval_gateway.py](../../backend/helpdesk/services/retrieval_gateway.py), we reran the same in-process benchmark (`top_k=6`, `min_score=0.62`, `scope=["NeTEx"]`).

Applied tuning values:
- `GRAPHDB_TIMEOUT_SECONDS=3`
- `GRAPH_EXPANSION_MAX_CONCEPTS=8`
- `GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=12`
- `RETRIEVAL_MAX_SAME_SOURCE_PATH=1`

Observed runtime result (post-tuning):

```text
CONTROL (graph_rag_enabled=false)
time_ms=2806.6
graphConceptIds=0
graphCandidatesAdded=0
graphEvidenceCount=0
graphScoreContribution=0.0
1. examples/functions/timetable/Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml | score=1.000000
2. examples/functions/timetable/Netex_21_Rail_NetworkTimetable_eurostar.xml | score=1.000000
3. examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml | score=1.000000
4. examples/functions/timetable/Netex_51.1_Occupancy.xml | score=1.000000
5. examples/functions/timetable/Netex_09.2_Bus_SimpleTimetable_Slovenia.xml | score=1.000000
6. examples/functions/timetable/Netex_01.4_Bus_SimpleTimetable_WithConnection.xml | score=1.000000

GRAPH-RAG (graph_rag_enabled=true)
time_ms=32223.6
graphConceptIds=8
graphCandidatesAdded=8
graphEvidenceCount=6
graphScoreContribution=0.3
1. examples/functions/line/NeTEx_01_simple_line.xml | score=1.000000
2. examples/standards/fxc/FX-PI-01_UK_MB_LINE_FARE_MB-Line-1-trip-(Z2Z-basic)_20170101.xml | score=1.000000
3. examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml | score=1.000000
4. examples/functions/fares/Netex_101.21_TfL_GeographicFares_UnitZone_MultipleProduct.xml | score=1.000000
5. examples/functions/timetable/Netex_03.2_Bus_BranchedRouteTimetable_SharedPatterns.xml | score=1.000000
6. examples/functions/timetable/Netex_21_Rail_NetworkTimetable_eurostar.xml | score=1.000000
```

Post-tuning interpretation:
- Graph-rag latency improved from `~82.9s` to `~32.2s` (about `61%` faster) for the same q070 retrieval path.
- Canonical top-1 evidence is preserved (`examples/functions/line/NeTEx_01_simple_line.xml`).
- Control path remains stable around `~2.8s`.
- Further optimization is still required to reach near-control latency in graph mode.

### Post-tuning trial 2 (2026-05-11, stage-profiled optimization)
We then added retrieval stage timing trace fields and optimized graph candidate lookup to run path/label matching first, with text fallback only when needed.

Observed runtime result (post-tuning trial 2):

```text
CONTROL (graph_rag_enabled=false)
time_ms=2837.7
graphConceptIds=0
graphCandidatesAdded=0
graphEvidenceCount=0
1. examples/functions/timetable/Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml | score=1.000000
2. examples/functions/timetable/Netex_21_Rail_NetworkTimetable_eurostar.xml | score=1.000000
3. examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml | score=1.000000
4. examples/functions/timetable/Netex_51.1_Occupancy.xml | score=1.000000
5. examples/functions/timetable/Netex_09.2_Bus_SimpleTimetable_Slovenia.xml | score=1.000000
6. examples/functions/timetable/Netex_01.4_Bus_SimpleTimetable_WithConnection.xml | score=1.000000

GRAPH-RAG (graph_rag_enabled=true)
time_ms=14866.7
graphConceptIds=8
graphCandidatesAdded=8
graphEvidenceCount=6
1. examples/functions/line/NeTEx_01_simple_line.xml | score=1.000000
2. examples/standards/fxc/FX-PI-01_UK_MB_LINE_FARE_MB-Line-1-trip-(Z2Z-basic)_20170101.xml | score=1.000000
3. examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml | score=1.000000
4. examples/functions/fares/Netex_101.21_TfL_GeographicFares_UnitZone_MultipleProduct.xml | score=1.000000
5. examples/functions/timetable/Netex_03.2_Bus_BranchedRouteTimetable_SharedPatterns.xml | score=1.000000
6. examples/functions/timetable/Netex_21_Rail_NetworkTimetable_eurostar.xml | score=1.000000
```

Stage timing trace (graph-rag, trial 2):

```text
retrievalStageTimingsMs={
	"seedChunkEnsureMs": 2.7,
	"conceptExtractMs": 26.0,
	"graphExpandMs": 10.2,
	"conceptMetadataMs": 0.0,
	"queryEmbeddingMs": 0.3,
	"postgresCandidateQueryMs": 1.2,
	"pathHintMergeMs": 2144.7,
	"graphCandidateQueryMs": 6608.9,
	"candidateScoringMs": 5255.3,
	"candidateSelectionMs": 0.9,
	"trimmedPostprocessMs": 0.0,
	"coverageMetricsMs": 815.6,
	"totalMeasuredMs": 14865.8
}
```

Interpretation (trial 2):
- Graph-rag latency improved from `~32.2s` to `~14.9s` (about `54%` faster than trial 1).
- Relative to the original baseline (`~82.9s`), graph-rag is now about `82%` faster.
- Canonical top-1 evidence remains preserved.
- Remaining dominant costs are `graphCandidateQueryMs` and `candidateScoringMs`.

### Post-tuning trial 3 (2026-05-11, stability check)
We applied an additional low-risk optimization pass and revalidated the same q070 retrieval benchmark.

Changes kept in final state:
- Reuse PostgreSQL-provided `vector_similarity` during scoring when available, avoiding Python-side cosine recomputation for SQL candidates.
- Tightened filename/path hint extraction to prefer concrete path-like tokens (`.xml`, `.xsd`, `_`, `-`, `/`, digits).
- Limited PostgreSQL hybrid candidate payload to required fields only.

Observed runtime result (trial 3, graph-rag):

```text
time_ms=14976.0
retrievalStageTimingsMs={
	"seedChunkEnsureMs": 22.5,
	"conceptExtractMs": 21.8,
	"graphExpandMs": 7.2,
	"conceptMetadataMs": 0.0,
	"queryEmbeddingMs": 0.3,
	"postgresCandidateQueryMs": 7.0,
	"pathHintMergeMs": 2307.3,
	"graphCandidateQueryMs": 6507.5,
	"candidateScoringMs": 5276.4,
	"candidateSelectionMs": 0.9,
	"trimmedPostprocessMs": 0.0,
	"coverageMetricsMs": 824.5,
	"totalMeasuredMs": 14975.6
}
top-1=examples/functions/line/NeTEx_01_simple_line.xml
```

Interpretation (trial 3):
- Runtime remains in the same optimized envelope as trial 2 (`~14.9s` to `~15.0s`) with canonical top-1 source preserved.
- The dominant bottlenecks remain `graphCandidateQueryMs` and `candidateScoringMs`.
- No additional major latency reduction was observed in this pass; the pipeline is currently stable but still above target.

### Post-tuning trial 4 (2026-05-11, active bounded preselection)
We then activated explicit scoring-cap settings and reran q070 to validate bounded preselection behavior.

Applied runtime settings:
- `RETRIEVAL_SCORING_CANDIDATE_CAP=32`
- `RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER=2`

Observed runtime result (trial 4):

```text
CONTROL (graph_rag_enabled=false)
time_ms=2716.8
graphConceptIds=0
graphCandidatesAdded=0
graphEvidenceCount=0

GRAPH-RAG (graph_rag_enabled=true)
time_ms=13328.7
graphConceptIds=8
graphCandidatesAdded=8
graphEvidenceCount=6
retrievalScoringCandidateCap=32
retrievalGraphPreselected=8
1. examples/functions/line/NeTEx_01_simple_line.xml | score=1.000000
2. examples/standards/fxc/FX-PI-01_UK_MB_LINE_FARE_MB-Line-1-trip-(Z2Z-basic)_20170101.xml | score=1.000000
3. examples/functions/fares/Netex_51.3_Bus_SimpleFares_ZoneToZone_AdultChildProduct.xml | score=1.000000
4. examples/functions/timetable/Netex_09.1_Bus_InterchangeRule.xml | score=1.000000
5. examples/functions/patterns/Netex_KBIC_ParisNetwork_with_bookingArrangements.xml | score=1.000000
6. examples/functions/timetable/Netex_21_Rail_NetworkTimetable_eurostar.xml | score=1.000000
```

Stage timing trace (graph-rag, trial 4):

```text
retrievalStageTimingsMs={
	"seedChunkEnsureMs": 1.4,
	"conceptExtractMs": 22.6,
	"graphExpandMs": 7.3,
	"conceptMetadataMs": 0.0,
	"queryEmbeddingMs": 0.3,
	"postgresCandidateQueryMs": 1.2,
	"pathHintMergeMs": 1965.5,
	"graphCandidateQueryMs": 6186.6,
	"candidatePreselectMs": 0.0,
	"candidateScoringMs": 4340.8,
	"candidateSelectionMs": 0.7,
	"trimmedPostprocessMs": 0.0,
	"coverageMetricsMs": 801.9,
	"totalMeasuredMs": 13328.5
}
```

Interpretation (trial 4):
- Graph-rag improved from `~14.9s` to `~13.3s` for q070 with bounded preselection active.
- Canonical top-1 evidence remains preserved.
- Dominant residual costs remain graph candidate query and candidate scoring stages.

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
	Source: <https://github.com/TransmodelEcosystem/NeTEx/blob/de021e83a02522cff4ed936408bf927f798aae0d/examples/functions/timetable/Netex_07.2_Bus_FlexibleTimetable_WithPattern.xml>
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
The q070 pipeline executed end-to-end with both unscoped and NeTEx-scoped runs, and historical rerun artifacts still show a citation-quality gap (canonical simple-line source missing in top evidence). The 2026-05-11 benchmark update demonstrates that graph-enabled retrieval can now surface the canonical `functions/line` source, but with a major latency increase.

Current operational finding:

- Evidence quality can be improved with graph-aware expansion and object-property relations.
- Latency must be reduced before this path can be treated as default for q070-class requests.

## Recommended Follow-Up
1. Add prompt shaping for `intent=example` to prioritize concise, directly requested XML example output format.
2. Continue retrieval tuning without hard-coded path boosts so `line`-family example evidence outranks timetable/stop examples on semantic merit.
3. Add a targeted regression check for q070 to ensure scoped run keeps >=1 expected `functions/line`-family citation near top results.
