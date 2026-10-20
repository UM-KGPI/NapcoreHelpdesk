# Phase 0 — Non-NITS Cross-Standard Pivot: Design and Implementation

Status: **implemented, additive, not yet live-GraphDB-verified.**
Executes `docs/ontology/NITS-REMOVAL-PLAN.md` §3 Phase 0 (checks 0.1, 0.2, 0.3). Produced and
implemented in the same session, on branch `chore/remove-nits-plan`, immediately after that
plan's Phase 1 steps landed.

---

## 1. Decision

**Replace NITS as the cross-standard pivot with Transmodel, and source the in-memory pivot
from the already-committed, offline-generated `docs/ontology/alignments/transmodel-
{netex,siri,opra}-align.ttl` files instead of a live GraphDB query.**

Rationale, in order of importance:

1. **Transmodel is the only other cross-standard hub the system has**, and it already has a
   generator (`build_transmodel_alignment.py`) and three populated alignment files that encode
   exactly the data a pivot needs: `{standard}:{Class} skos:exactMatch tm:{TM_CLASS}`.
2. **Sourcing the in-memory snapshot from these static files, instead of a live GraphDB query at
   process startup (as NITS's `_load_nits_ontology_from_graphdb` did), removes a real production
   failure mode.** The NITS in-memory fallback only ever contained real data if GraphDB happened
   to be reachable at the exact moment the Django worker process started; if it wasn't, the
   fallback was permanently empty for that worker's lifetime, with no way to recover short of a
   restart (see the original plan's §1 and §6). The static pivot has no such dependency — it
   loads the same way every time, GraphDB up or down, enabled or disabled.
3. **The live GraphDB pivot (`graphdb_client.query_graphdb_concept_expansion`) already had a
   working Transmodel-namespace branch running alongside the NITS one**, per the pre-existing
   code comment: "SPARQL already has a Transmodel-namespace pivot alternative." Removing the
   NITS half of that OR filter is removing a redundant branch next to an already-proven one, not
   introducing new, unverified live-query logic.

## 2. What was found while implementing this

Before any of this work, with `GRAPHDB_ENABLED=False` (this environment, and CI), the system's
in-memory ontology state is **entirely empty**: `_ONTOLOGY`, `_NITS_ONTOLOGY`,
`GRAPH_CONCEPT_ALIASES`, `CONCEPT_TO_NITS`, and `GRAPH_RELATIONS` are all `{}`, because
`_load_ontology()`/`_load_nits_ontology()` short-circuit to empty dicts whenever GraphDB is
disabled. This was verified directly in this session (`manage.py shell`), not assumed.

One concrete consequence of that emptiness, also verified directly: asking
`parse_question_to_semantic_query("What is a vehicle journey in NeTEx?")` with GraphDB disabled
returned `core_concept == "nits:unknown-concept"` **even though** `extract_graph_concepts`
correctly recognized `netex:VehicleJourney` via the hardcoded fallback alias list. The sentinel
fired not because nothing was recognized, but because `CONCEPT_TO_NITS` had no entry for
anything (it's empty), and the old `_anchor_candidates_to_nits` returned `[]` whenever no NITS
mapping existed for any input concept, with no further fallback. This is a real, pre-existing bug
in any GraphDB-disabled deployment, not something introduced by Phase 1. Fixing it is now part of
0.2 below.

## 3. What was implemented

### 0.1 — In-memory pivot (`backend/helpdesk/services/semantic_graph.py`)

Added, **additively** (the existing NITS pivot is untouched and still runs):

- `_parse_transmodel_alignment_file(path)` — regex parser (no `rdflib` dependency at runtime) for
  the generated `transmodel-<standard>-align.ttl` format.
- `_load_transmodel_pivot_from_static_files()` — reads all three alignment files unconditionally
  at module import time (no `GRAPHDB_ENABLED`/`NAPCORE_SKIP_GRAPHDB_IMPORT` gate) and builds
  `CONCEPT_TO_TRANSMODEL` / `TRANSMODEL_TO_CONCEPTS`.
- `get_concept_transmodel_ids()`, `_expand_transmodel_concepts()` — same shape as the existing
  `get_concept_nits_ids()`/`_expand_nits_concepts()`, but with no internal multi-hop (the
  alignment files only record direct `skos:exactMatch` pairs, not a Transmodel-internal relation
  graph, so a shared-pivot sibling group is already the full expansion in one step).
- `expand_graph_concepts()` now runs **both** the NITS bridging phase and the new Transmodel
  bridging phase, unconditionally, every call.
- `_build_graph_relations_from_ontology()`'s cross-standard bridge now folds in both
  `NITS_TO_CONCEPTS.values()` and `TRANSMODEL_TO_CONCEPTS.values()`.

Verified directly in this session, with `GRAPHDB_ENABLED=False` and no live GraphDB at all:

```
expand_graph_concepts({"netex:DatedVehicleJourney"}, hops=1)
  -> {"netex:DatedVehicleJourney", "siri:DatedVehicleJourney"}
```

This is exactly the plan's own §3 check-0.1 example (a NeTEx vehicle-journey concept surfacing
its SIRI sibling with GraphDB disabled), now passing. A regression test against the real
committed files (`TransmodelPivotTests.test_real_committed_alignment_files_bridge_netex_and_siri_dated_vehicle_journey`
in `test_semantic_graph.py`) pins this.

Today the real alignment files yield 748 concept→Transmodel mappings and 9 cross-standard
sibling groups (concepts shared by 2+ standards) — small, because NeTEx/SIRI/OpRa alignment
coverage to Transmodel is still mostly 1:1 per-standard (SIRI: 11/310 classes aligned; OpRa:
33/106), not because the mechanism is broken. This will grow as alignment coverage improves
(`transmodel-alignment-curation.csv`), with zero code changes needed.

### 0.2 — Core-concept identity and sentinel (`question_parsing.py`, `semantic_abstention.py`,
`faq_publication.py`)

- New sentinel: `question_parsing.UNKNOWN_CONCEPT_SENTINEL = "unknown-concept"` (no namespace
  prefix — it's a literal "nothing was recognized" marker, trivially distinct from any real
  concept ID, which always has a `namespace:local` shape). Replaces `"nits:unknown-concept"` in
  all three files that shared the old string-literal contract (the original plan's risk #2).
- `_anchor_candidates_to_nits` → `_anchor_candidates_to_concepts`: tries the NITS pivot first
  (still real data in any GraphDB-enabled deployment until Phase 2 removes NITS), then the static
  Transmodel pivot, then — new — **falls back to the glossary concept IDs themselves** when
  neither pivot resolves anything. This directly fixes the bug in §2: a recognized concept with
  no cross-standard alignment is no longer indistinguishable from recognizing nothing at all.
- `_anchor_with_graphdb`: previously forced *any* GraphDB-returned alignment IRI into a
  `"nits:localname"` shape regardless of its real namespace (dead code: the `iri.startswith
  ("nits:")` check could never be true for a real URI returned over SPARQL, so every live hit was
  silently mislabeled). Now classifies by namespace and correctly emits `"transmodel:localname"`
  for Transmodel hits.
- `_discover_standards_with_graphdb`: now branches on `core_concept` prefix. For `"transmodel:"`
  IDs it queries GraphDB directly with the exact Transmodel IRI (no slug-matching needed — the
  local name *is* the real class name, unlike NITS's label-derived slugs) and skips
  `discover_standards_for_core_concept_slug` entirely for that branch. The `"nits:"` branch is
  unchanged, kept for live-GraphDB parity until Phase 2.

Verified directly: `parse_question_to_semantic_query("What is a vehicle journey in NeTEx?")` with
`GRAPHDB_ENABLED=False` now returns `core_concept == "transmodel:VEHICLE_JOURNEY"` (previously
the sentinel); a question that recognizes nothing at all still correctly returns the sentinel.

### 0.3 — Live GraphDB pivot (`graphdb_client.py`)

- `query_graphdb_concept_expansion`'s pivot-branch `FILTER` no longer has a NITS half: the
  `(CONTAINS(...,'nits') && NOT IN (abstract roots)) || STRSTARTS(...,transmodel)` OR condition
  is now just the Transmodel `STRSTARTS` check. `_ABSTRACT_NITS_PIVOTS` is deleted (it has no
  other caller after this edit).
- `STANDARD_GRAPH_SCOPE`'s per-standard `alignments/{netex,opra,siri}` entries are removed. Those
  graph names are populated *exclusively* by the `nits-{netex,opra,siri}-align.ttl` files
  (confirmed in the original plan's §2 group A and §4.1) — removing them from scope changes
  nothing for the Transmodel branch, because `TRANSMODEL_REFERENCE_GRAPHS` already adds
  `alignments/transmodel-{netex,siri,opra}` **unconditionally** to every standard-scoped query,
  independent of this change.
- `DEFAULT_NAMESPACES["nits"]` is **kept** — it's still needed by `_to_iri`/`_iri_to_concept_id`
  for any `"nits:"`-prefixed concept ID that still flows through the system via the 0.2 live-
  GraphDB branch, until Phase 2 removes that branch too.

**Not runtime-verified against a live GraphDB instance** — this environment has none. What *was*
verified: the exact SPARQL string the function now builds (captured via a mocked `urlopen`,
bypassing the network call) contains no `nits` reference, contains the Transmodel namespace
check, and is syntactically well-formed. `test_graphdb_client.py`'s three NITS-pivot-specific
tests were rewritten to match (not run — the test class is a DB-backed `TestCase` and this
container has no Postgres); this is the same category of limitation this session already has for
all of `test_graphdb_client.py` and `test_api.py`.

## 4. What is explicitly *not* done here (left for Phase 2/3)

- `CONCEPT_TO_NITS`, `NITS_TO_CONCEPTS`, `NITS_RELATIONS`, `_NITS_ONTOLOGY`, and
  `get_concept_nits_ids` are **untouched** and still load from live GraphDB exactly as before.
  Deleting them is Phase 2 (§3 steps 2.1–2.2), gated on this design being proven against a real
  GraphDB instance first.
- `graphdb_connector.py`'s `discover_standards_for_core_concept_slug` is untouched; it has one
  remaining caller (the `"nits:"` branch in `_discover_standards_with_graphdb`).
- The `nits-{netex,opra,siri}-align.ttl` `graph_specs` entries in `load_default_ontology_graphs`
  still load into GraphDB (Phase 3 deletes the files; this change only stopped *querying* the
  graphs they populate).
- `semantic_abstention.py`/`faq_publication.py` otherwise read `core_concept` generically and
  needed no further change beyond the sentinel constant.

## 5. Before Phase 2 can proceed

Per the original plan's §3 Phase 2 gate, confirm against a real (non-production) GraphDB
instance:

- A known cross-standard question still surfaces the expected sibling-standard evidence with
  `GRAPHDB_ENABLED=True` (exercises the now-Transmodel-only live pivot branch in
  `query_graphdb_concept_expansion`).
- `test_graphdb_client.py`'s three rewritten pivot tests actually pass when run with a real
  Postgres/test-DB available (this session could only verify their SPARQL-construction logic by
  hand, not execute them).
- `test_api.py`'s sentinel-dependent test passes end-to-end (same DB limitation).
