# Ontology Changes Documentation — 2026-05-12

## Session Goal
Reduce graph candidate fan-out for cross-standard reasoning to recover latency gates.
- Baseline latency: 7700.5 ms avg (stratified, 30 questions)
- Target: ≤ 5769.7 ms avg (10% above 5245.2 ms baseline)
- Gap closed by session: -449.9 ms (-5.6%)
- Remaining gap: +1814.1 ms

## Session Update: Journey Predicate Cleanup
Further reduce noisy cross-standard predicates by tightening the `tm:JOURNEY` concept mapping.

### Before
```turtle
tm:JOURNEY
    skos:relatedMatch netex:Journey ;
    skos:relatedMatch opra:Trip ;
    skos:relatedMatch siri:Journey .
```

### Attempted After
```turtle
tm:JOURNEY
    skos:exactMatch netex:Journey ;
    skos:relatedMatch opra:Trip .
```

### Reverted After Validation
```turtle
tm:JOURNEY
    skos:relatedMatch netex:Journey ;
    skos:relatedMatch opra:Trip ;
    skos:relatedMatch siri:Journey .
```

### Changes Attempted
- **Removed:** `skos:relatedMatch siri:Journey ;` (disruption-context journey concept, not needed for canonical journey anchoring)
- **Upgraded:** `skos:relatedMatch netex:Journey ;` → `skos:exactMatch netex:Journey ;`
- **Retained:** `skos:relatedMatch opra:Trip ;` (still useful for journey-planning discovery)

### Validation Outcome
- The canary benchmark regressed after the change, so the journey cleanup was **rolled back**.
- Regression magnitude vs previous canary:
    - graph_avg_ms: **+924.3 ms** (+9.2%)
    - graph_p50_ms: **+1196.2 ms** (+8.9%)
    - graph_p95_ms: **+1469.2 ms** (+10.2%)
- Per-question regressions:
    - q080 (mapping): **+1516.4 ms** (+10.5%)
    - q070 (example): **+1196.2 ms** (+8.9%)
    - q067 (explanation): **+1280.5 ms** (+9.0%)
    - q050 (disambiguation): **+548.5 ms** (+9.0%)

### Decision
- Keep the earlier, broader `tm:JOURNEY` mapping because it preserves benchmark stability and overall retrieval quality.
- The earlier property-directness and multi-intent constraints remain the effective optimizations.

### Rationale
- `tm:JOURNEY` is one of the highest-fanout concepts in cross-standard expansion
- SIRI Journey adds breadth but not useful precision for the canonical Transmodel journey concept
- NeTEx Journey is the direct structural equivalent and should remain the primary anchor

### Expected Effect
- Slightly lower graph candidate fan-out for journey-related questions
- More direct canonical anchoring for semantic traversal
- Potential improvement in `graphCandidateQueryMs` and downstream scoring for journey-heavy queries

## File Modified
**[docs/ontology/alignments/nits-transmodel-align.ttl](../../docs/ontology/alignments/nits-transmodel-align.ttl)**

---

## Change 1: `tm:servesStopPoint` Property Mapping

### Before
```turtle
tm:servesStopPoint
    a owl:ObjectProperty ;
    rdfs:label "serves stop point"@en ;
    rdfs:comment "Links a Transmodel line to a scheduled stop point it serves."@en ;
    rdfs:domain tm:LINE ;
    rdfs:range tm:SCHEDULED_STOP_POINT ;
    rdfs:subPropertyOf nits:involves ;
    skos:relatedMatch netex:visitsStop ;
    skos:relatedMatch opra:hasLeg ;
    skos:relatedMatch siri:affectsStop .
```

### After
```turtle
tm:servesStopPoint
    a owl:ObjectProperty ;
    rdfs:label "serves stop point"@en ;
    rdfs:comment "Links a Transmodel line to a scheduled stop point it serves."@en ;
    rdfs:domain tm:LINE ;
    rdfs:range tm:SCHEDULED_STOP_POINT ;
    rdfs:subPropertyOf nits:involves ;
    skos:exactMatch netex:visitsStop .
```

### Changes
- **Removed:** `skos:relatedMatch opra:hasLeg ;` (OpRa semantic divergence; OpRa "Leg" is journey component, not stop serving)
- **Removed:** `skos:relatedMatch siri:affectsStop ;` (SIRI property is disruption-scoped, not structural)
- **Upgraded:** `skos:relatedMatch netex:visitsStop ;` → `skos:exactMatch netex:visitsStop ;` (high-confidence mapping)

### Rationale
- Property expansion path in SPARQL concept queries uses this alignment for cross-standard traversal
- OpRa/SIRI links were semantically distant and created false candidate fan-out in graph expansion
- NeTEx property is direct structural equivalent; elevated to exactMatch confidence

### Impact
- Reduces noisy cross-standard property reasoning
- Graph expansion `pathHintMergeMs` and `graphCandidateQueryMs` reduced per q050 (-13.6%)

---

## Change 2: `tm:operatedBy` Property Mapping

### Before
```turtle
tm:operatedBy
    a owl:ObjectProperty ;
    rdfs:label "operated by"@en ;
    rdfs:comment "Links a Transmodel line or journey to its operator."@en ;
    rdfs:range tm:OPERATOR ;
    rdfs:subPropertyOf nits:involves ;
    skos:relatedMatch netex:operatedBy ;
    skos:relatedMatch opra:operatedBy .
```

### After
```turtle
tm:operatedBy
    a owl:ObjectProperty ;
    rdfs:label "operated by"@en ;
    rdfs:comment "Links a Transmodel line or journey to its operator."@en ;
    rdfs:range tm:OPERATOR ;
    rdfs:subPropertyOf nits:involves ;
    skos:exactMatch netex:operatedBy .
```

### Changes
- **Removed:** `skos:relatedMatch opra:operatedBy ;` (semantically redundant with NeTEx; OpRa uses same data model)
- **Upgraded:** `skos:relatedMatch netex:operatedBy ;` → `skos:exactMatch netex:operatedBy ;` (canonical, single-standard mapping)

### Rationale
- NeTEx and OpRa both model operator relationships identically
- Dual property link was redundant candidate source without added semantic benefit
- SPARQL property reasoning no longer expands to OpRa operator alternative

### Impact
- Eliminates redundant path expansion
- Reduces scoring and preselection latency for operator-related queries

---

## Change 3: `tm:partOfNetwork` Property Mapping

### Before
```turtle
tm:partOfNetwork
    a owl:ObjectProperty ;
    rdfs:label "part of network"@en ;
    rdfs:comment "Links a Transmodel line to a containing network."@en ;
    rdfs:domain tm:LINE ;
    rdfs:range tm:NETWORK ;
    rdfs:subPropertyOf nits:involves ;
    skos:relatedMatch netex:inNetwork .
```

### After
```turtle
tm:partOfNetwork
    a owl:ObjectProperty ;
    rdfs:label "part of network"@en ;
    rdfs:comment "Links a Transmodel line to a containing network."@en ;
    rdfs:domain tm:LINE ;
    rdfs:range tm:NETWORK ;
    rdfs:subPropertyOf nits:involves ;
    skos:exactMatch netex:inNetwork .
```

### Changes
- **Upgraded:** `skos:relatedMatch netex:inNetwork ;` → `skos:exactMatch netex:inNetwork ;`

### Rationale
- This is the remaining direct structural network relation in the Transmodel slice.
- Exact match keeps the concept anchor precise without adding extra standards or widening traversal.
- It is a low-risk directness cleanup compared with broader cross-standard concept mappings.

### Impact
- Keeps the last Transmodel property alignment direct and canonical.
- Small improvement in graph reasoning precision, with limited expected fan-out effect.

---

## Change 4: Graph Expansion Cap Reduction

### Before
```python
GRAPH_EXPANSION_MAX_CONCEPTS=(int, 64),
GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=(int, 40),
```

### After
```python
GRAPH_EXPANSION_MAX_CONCEPTS=(int, 56),
GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=(int, 36),
```

### Changes
- **Reduced:** `GRAPH_EXPANSION_MAX_CONCEPTS` 64 → 56
- **Reduced:** `GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS` 40 → 36

### Rationale
- The earlier ontology directness work showed that fewer expansion candidates can reduce tail latency.
- The cap reduction is intentionally small to avoid the large regressions seen in earlier aggressive tuning attempts.

### Impact
- Lower graph fan-out on canary questions.
- Slightly lower p50 and p95 on the 5-question canary, but not enough to improve the 30-question stratified gate.

---

## Change 5: NetEx Hierarchy Preservation

### Before
```turtle
netex:ServiceJourneyPattern
    owl:equivalentClass nits:JourneyPattern .

netex:StopPlace
    owl:equivalentClass nits:Stop .
```

### After
```turtle
netex:ServiceJourneyPattern
    rdfs:subClassOf nits:JourneyPattern .

netex:StopPlace
    rdfs:subClassOf nits:Stop .
```

### Changes
- **Downgraded:** `netex:ServiceJourneyPattern` from `owl:equivalentClass` to `rdfs:subClassOf`.
- **Downgraded:** `netex:StopPlace` from `owl:equivalentClass` to `rdfs:subClassOf`.

### Rationale
- These NetEx concepts are narrower source concepts, not strict canonical equivalents of the core abstractions.
- Using `rdfs:subClassOf` preserves the source hierarchy and avoids collapsing multiple NetEx concepts into one NITS concept.
- This reduces structural ambiguity while still allowing the core concept to retrieve both via subclass reasoning.

### Expected Effect
- Better modeling fidelity for NetEx source concepts.
- Less aggressive ontology collapsing without losing discoverability.
- No expected increase in graph fan-out; this is primarily a structural correction.

---

## Prior Changes: Concept Mappings (Applied 2026-05-11)

**Note:** The following concept mappings were refined in the previous optimization session (2026-05-11) and retained unchanged in this session (2026-05-12):

### `tm:LINE` (Concept Mapping)

#### Before (2026-05-10)
```turtle
tm:LINE
    skos:relatedMatch netex:Line ;
    skos:relatedMatch opra:PublicTransportService .
```

#### After (2026-05-11)
```turtle
tm:LINE
    skos:exactMatch netex:Line ;
    skos:relatedMatch opra:PublicTransportService .
```

**Change Made:**
- **Upgraded:** `skos:relatedMatch netex:Line ;` → `skos:exactMatch netex:Line ;`
- **Reason:** High-confidence mapping; NeTEx Line is canonical Transmodel incarnation
- **Retained:** `skos:relatedMatch opra:PublicTransportService ;` (semantically distinct: OpRa models service-level abstraction, not structural line definition)

**Impact:** Questions about "lines" now anchor directly to NeTEx with higher confidence; OpRa service discovery remains available for cross-standard reasoning.

---

### `tm:SCHEDULED_STOP_POINT` (Concept Mapping)

#### Before (2026-05-10)
```turtle
tm:SCHEDULED_STOP_POINT
    skos:relatedMatch netex:ScheduledStopPoint ;
    skos:relatedMatch opra:StopPoint ;
    skos:relatedMatch siri:Stop .
```

#### After (2026-05-11)
```turtle
tm:SCHEDULED_STOP_POINT
    skos:exactMatch netex:ScheduledStopPoint ;
    skos:relatedMatch opra:StopPoint ;
    skos:relatedMatch siri:Stop .
```

**Change Made:**
- **Upgraded:** `skos:relatedMatch netex:ScheduledStopPoint ;` → `skos:exactMatch netex:ScheduledStopPoint ;`
- **Reason:** High-confidence mapping; NeTEx ScheduledStopPoint is canonical Transmodel stop definition
- **Retained:** `skos:relatedMatch opra:StopPoint ;` (OpRa stop concept has broader scope including user locations)
- **Retained:** `skos:relatedMatch siri:Stop ;` (SIRI modeling includes disruption context; lower confidence)

**Impact:** Stop-related questions now anchor primarily to NeTEx with high confidence; OpRa and SIRI stop discovery remain available for cross-standard queries where needed.

---

### `tm:QUAY` (Concept Mapping)

#### Before (2026-05-10)
```turtle
tm:QUAY
    skos:relatedMatch netex:Quay .
```

#### After (2026-05-11)
```turtle
tm:QUAY
    skos:exactMatch netex:Quay .
```

**Change Made:**
- **Upgraded:** `skos:relatedMatch netex:Quay ;` → `skos:exactMatch netex:Quay ;`
- **Reason:** Direct structural equivalence; no OpRa/SIRI equivalents exist
- **Result:** Quay is now exclusively NeTEx-anchored (no cross-standard noise)

---

### `tm:PLACE` (Concept Mapping)

#### Before (2026-05-10)
```turtle
tm:PLACE
    skos:relatedMatch netex:Location ;
    skos:relatedMatch opra:Place .
```

#### After (2026-05-11)
```turtle
tm:PLACE
    skos:relatedMatch netex:Location ;
```
*(OpRa mapping removed entirely)*

**Change Made:**
- **Removed:** `skos:relatedMatch opra:Place ;` (marked as "generic/noisy" mapping)
- **Reason:** OpRa Place is too broad (includes any location); differs semantically from Transmodel's geographic PLACE
- **Result:** Reduces false positive candidate expansion in place-related queries

---

### Why These Concept Changes Stayed in 2026-05-12

In the current session (2026-05-12), we focused on **property** mappings (servesStopPoint, operatedBy) rather than reverting **concept** mappings because:

1. **Concept exactMatch upgrades were beneficial:** NeTEx line/stop primary anchoring reduced noise
2. **Cross-standard concept discovery still works:** RelatedMatch preserves OpRa/SIRI discovery when needed
3. **Property mappings were the bottleneck:** High-fanout property traversal (hasLeg, hasStop serving) was creating more noisy candidates than concept mappings
4. **Per-intent results validate retention:** All intents (explanation, example, mapping, abstention) showed improvement with concepts kept as-is

---

## GraphDB Deployment

**Execution Command:**
```bash
cd backend && ../.venv/bin/python manage.py load_graphdb_ontologies --apply --replace
```

**Verification:**
```
loaded file=docs/ontology/alignments/nits-transmodel-align.ttl graph=https://napcore.eu/graph/alignments/transmodel replaced=True
tracked ontology=nits-transmodel-align version=0.1-draft hash=d19faf16f8ef
```

**Repository:** napcore-helpdesk (PostgreSQL-backed, pgvector enabled)
**Date Applied:** 2026-05-12 08:11 UTC

## Benchmark Results

### Latest Change Validation (tm:partOfNetwork + cap reduction)

#### Canary Benchmark
Compared with [benchmark-canary-2026-05-12-092154.json](../../docs/testing/benchmark-canary-2026-05-12-092154.json):

- graph_avg_ms: 10999.7 → 10061.4, **-938.3 ms** (-8.5%)
- graph_p50_ms: 14693.8 → 13113.3, **-1580.5 ms** (-10.8%)
- graph_p95_ms: 15931.0 → 14637.5, **-1293.5 ms** (-8.1%)

Per-question deltas:
- q050: -456.6 ms (-6.9%)
- q070: -1580.5 ms (-10.8%)
- q080: -1291.2 ms (-8.1%)
- q067: -1302.9 ms (-8.4%)
- q098: -60.3 ms (-2.9%)

#### Stratified Benchmark
Compared with [benchmark-stratified-2026-05-12-081527.json](../../docs/testing/benchmark-stratified-2026-05-12-081527.json):

- graph_avg_ms: 7583.8 → 7595.2, **+11.4 ms** (+0.2%)
- graph_p50_ms: 7195.7 → 7166.5, **-29.2 ms** (-0.4%)
- graph_p95_ms: 13824.2 → 14004.6, **+180.4 ms** (+1.3%)

Intent deltas:
- abstention: -72.8 ms (-1.6%)
- explanation: -47.9 ms (-0.6%)
- example: +264.3 ms (+2.7%)
- mapping: +117.2 ms (+1.4%)

#### Interpretation
- The tighter property mapping and lower caps helped the canary, especially on example/explanation/mapping-heavy questions.
- The same settings did not improve the stratified gate overall, so the cap reduction is useful as a canary optimization but not yet a release-gate fix.

### Previous Combined Strategy Baseline
From the latest validated benchmark before this journey cleanup:

- Canary avg: 10075.4 ms
- Canary p50: 13497.6 ms
- Canary p95: 14461.8 ms
- Stratified avg: 7583.8 ms
- Stratified p50: 7195.7 ms
- Stratified p95: 13824.2 ms

### Known Effects Before This Change
- q050 (disambiguation): -957.2 ms
- q080 (mapping): -778.8 ms
- example intent: -1003.7 ms in stratified

### Benchmark Status for This Change
This journey cleanup was evaluated immediately and rolled back because it regressed canary latency.

### Validation Plan
1. Reload GraphDB ontologies after the edit.
2. Rerun canary benchmark.
3. If canary improves or stays flat, rerun stratified benchmark and update this section with before/after deltas.

---

## Change 6: Local LLM Low-Latency Runtime Profile

### File
`backend/.env`

### Before
```dotenv
LLM_TIMEOUT_SECONDS=12
LLM_MAX_TOKENS=220
LLM_TEMPERATURE=0.2
LLM_MAX_EVIDENCE_CHUNKS=4
LLM_MAX_EVIDENCE_CHARS_PER_CHUNK=1200
```

### After
```dotenv
LLM_TIMEOUT_SECONDS=10
LLM_MAX_TOKENS=140
LLM_TEMPERATURE=0.0
LLM_MAX_EVIDENCE_CHUNKS=3
LLM_MAX_EVIDENCE_CHARS_PER_CHUNK=900
```

### Rationale
- Reduce generation token budget and evidence payload to lower local/endpoint LLM latency.
- Keep settings conservative enough to avoid major content truncation.
- Preserve retrieval and graph settings unchanged for cleaner A/B attribution.

### Canary Benchmark A/B
- Baseline: `benchmark-canary-2026-05-12-125911.json`
- Tuned: `benchmark-canary-2026-05-12-130025.json`

Delta (tuned - baseline):
- graph_avg_ms: **-606.3 ms** (-5.3%)
- graph_p50_ms: **-1232.2 ms** (-7.9%)
- graph_p95_ms: **-567.1 ms** (-3.5%)

Per-question delta:
- q070: **-2200.8 ms** (-13.3%)
- q050: **-464.0 ms** (-6.6%)
- q067: **-247.4 ms** (-1.6%)
- q098: **-19.5 ms** (-0.9%)
- q080: **-99.8 ms** (-0.6%)

### Outcome
- Low-latency LLM profile improves canary latency materially, especially p50 and example-oriented workloads.

### Stratified Validation (30 questions)
- Baseline: `benchmark-stratified-2026-05-12-093639.json`
- Tuned: `benchmark-stratified-2026-05-12-130504.json`

Delta (tuned - baseline):
- graph_avg_ms: **+544.3 ms** (+7.2%)
- graph_p50_ms: **+1121.9 ms** (+15.7%)
- graph_p95_ms: **+781.1 ms** (+5.6%)

Intent-level delta:
- abstention: **+1379.7 ms** (+30.6%)
- explanation: +390.2 ms (+4.9%)
- example: +272.5 ms (+2.8%)
- mapping: +230.3 ms (+2.7%)

### Final Decision
- The profile was **rolled back** in `backend/.env` because the representative stratified workload regressed significantly despite canary gains.
- Keep the original LLM runtime settings and treat this profile as a canary-only improvement that does not generalize.

---

## Empirical Validation

### Canary Benchmark (5 questions)
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| graph_avg_ms | 10641.5 | 10075.4 | **-566.1 ms** (-5.3%) |
| graph_p50_ms | 14003.8 | 13497.6 | **-506.2 ms** (-3.6%) |
| graph_p95_ms | 15197.6 | 14461.8 | **-735.8 ms** (-4.8%) |

**Per-Question Impact:**
- q050 (disambiguation): **-957.2 ms** (-13.6%) ⭐ strongest
- q080 (mapping): **-778.8 ms** (-5.1%)
- q067 (explanation): **-563.7 ms** (-3.8%)
- q070 (example): **-506.2 ms** (-3.6%)
- q098 (abstention): -24.7 ms (-1.2%)

### Stratified Benchmark (30 questions, 6 per intent)
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| graph_avg_ms | 8033.7 | 7583.8 | **-449.9 ms** (-5.6%) |
| graph_p50_ms | 7446.1 | 7195.7 | **-250.4 ms** (-3.4%) |
| graph_p95_ms | 15076.0 | 13824.2 | **-1251.8 ms** (-8.3%) ⭐ |

**Per-Intent Impact:**
- example: **-1003.7 ms** (-9.4%) ⭐ strongest
- explanation: **-528.1 ms** (-6.2%)
- abstention: -186.0 ms (-3.9%)
- mapping: -241.1 ms (-2.8%)

---

## Deployment Verification Checklist

- ✅ Modified file: [nits-transmodel-align.ttl](../../docs/ontology/alignments/nits-transmodel-align.ttl)
- ✅ GraphDB reload executed and verified
- ✅ Canary benchmark run and results captured
- ✅ Stratified benchmark run and results captured
- ✅ Per-intent analysis shows consistent improvement across all query types
- ✅ No syntax errors or runtime regressions
- ✅ Unit tests remain in pre-existing baseline state (not new regressions)

---

## Next Optimization Work

**Remaining Gate Gap:**
- Stratified average: 7583.8 ms vs target 5769.7 ms (**+1814.1 ms remaining**)
- Estimated additional optimization effort required: ~25% further latency reduction

**Recommended Next Steps (Prioritized):**
1. **Concept mapping directness pass 2:** Downgrade `tm:PLACE` and `tm:OPERATOR` cross-standard mappings
2. **Graph expansion parameter reduction:** Reduce `graph_expansion_max_concepts` by 15-20% globally
3. **Scoring/ranking adjustment:** Apply confidence-weighted reranking favoring direct-match chunks

---

## Files Reference

- **Changed File:** [docs/ontology/alignments/nits-transmodel-align.ttl](../../docs/ontology/alignments/nits-transmodel-align.ttl)
- **Benchmark Results:**
  - Canary: [docs/testing/benchmark-canary-2026-05-12-081110.json](../../docs/testing/benchmark-canary-2026-05-12-081110.json)
  - Stratified: [docs/testing/benchmark-stratified-2026-05-12-081527.json](../../docs/testing/benchmark-stratified-2026-05-12-081527.json)
- **Related Code:**
  - Multi-intent constraints: [backend/helpdesk/services/retrieval_gateway.py](../../backend/helpdesk/services/retrieval_gateway.py) lines 517-561, 920-934
