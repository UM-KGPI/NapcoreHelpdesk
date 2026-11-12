# NITS Upper-Ontology Removal — Plan

Status: **NITS is fully removed from both the codebase and the live GraphDB this was run against.**
Phases 0-3 are complete: `napcore-its.ttl` and the 3 `nits-{netex,opra,siri}-align.ttl` files are deleted
from the repository; their graphs were deleted from GraphDB by a `--replace` reload (confirmed via the
load command's own output); a direct SPARQL `ASK` across every named graph (not just the default graph)
for any triple under `https://napcore.eu/ontology/nits#` returns `false`. The full test suite (269 tests)
shows only two pre-existing, unrelated failure categories that were confirmed present identically on the
pre-removal code (§7 risk 1 below is resolved; the commit_sha/None bug and the live-GraphDB-vs-mock test
sensitivity are both independent, older issues). Phase 0's design document (`NITS-REMOVAL-PHASE0-DESIGN.md`)
was produced by a cloud session that exceeded its brief (asked for options only, it implemented instead)
but checked out correctly on independent re-verification.

**Follow-up 2026-11-11:** prod GraphDB is now checked on every deploy: `manage.py retire_graphdb_graphs`
(run by `scripts/deploy.sh`) deletes the retired graphs and fails the deploy if any statement in the NITS
namespace remains. On prod (0.97.188–0.97.190, 2026-11-12) it found NITS data in five legacy graphs loaded under the
older names (`urn:graph:napcore-its`, `urn:graph:nits-{netex,opra,siri,transmodel}-align`); they were added to
`RETIRED_GRAPH_URIS` and deleted, and the 0.97.190 deploy reported no NITS statements. With that in place, the eight protective NITS-exclusion `FILTER`s in `semantic_graph.py`
and `graphdb_connector.py` were removed. The documentation (`docs/ontology/README.md`, `GENERATION.md`, `backend/README.md`) already describes
Transmodel as the cross-standard pivot; the last NITS-era wording (the README title and "core concepts") was
fixed on 2026-11-12. The removal is complete.
Scope: namespace `https://napcore.eu/ontology/nits#`, file `docs/ontology/napcore-its.ttl`, and every
reference to it (`nits:` prefix, `NITS_*`/`_NITS_*`/`*_nits_*` symbols, the `nits-{netex,opra,siri}-align.ttl`
alignment files, and the `nits:unknown-concept` sentinel string).

Produced from main @ `4d9da5a` (v0.97.13), on branch `chore/remove-nits-plan`.

**Phase 1 execution log** (commits `e655df1`, `f5fc28b`, `ad6546f`, `1c84d6d`, `024ac25` on this branch,
done in a cloud session, independently re-verified afterward — `manage.py check` and 103 relevant tests
pass against live GraphDB/Postgres):
- Steps 1.1–1.5 (§3) done and verified: `llm_generator.py` no longer imports `_NITS_ONTOLOGY`; the
  `nits:transmodelDefinitionStatus`/`nits:alignmentMethod` properties were renamed and the 3
  `transmodel-*-align.ttl` files regenerated; the vestigial `@prefix nits:` line is gone from
  `netex.ttl`/`opra.ttl`/`siri.ttl`/`examples.ttl` (checked for the literal token, not just a case-insensitive
  grep, since those files legitimately contain "unit(s)" text); `ontology_alignment_gap.py`, its Makefile
  target, and the 3 generated `*-alignment-gap.md` reports are deleted; the Makefile smoke-test placeholder
  was swapped.
- Step 1.6 was only half-done by the cloud session (Makefile fixed, `.claude/settings.local.json` missed) —
  fixed directly afterward by deleting the 2 stale `nits:` SPARQL-debug permission lines plus a 3rd stale
  entry found while fixing it (`Bash(make ontology-alignment-gap *)`, dead since that target no longer
  exists).

**Two corrections to this document, found while verifying Phase 1 (neither blocks anything above),
both now addressed:**
- §2 group E previously stated `docs/ontology/ontology-enrichment.md` does not exist. That was checking the
  wrong path — **`docs/ontology-enrichment.md`** (one level up, at repo-root `docs/`) does exist, and it
  documented the `ontology_alignment_gap` workflow in detail (heuristic NITS-category table, example output,
  "Alignment axioms → `docs/ontology/alignments/nits-netex-align.ttl`"). Since step 1.5 deleted that command,
  this doc was stale — it has been rewritten to drop every reference to the removed command/workflow while
  keeping the unrelated, still-working `make ontology-scan-examples` documentation intact.
- A previously unnoticed `backend/docs/ontology/standards/` directory existed with its own stale copies
  of `netex.ttl`/`opra.ttl`, still carrying the old unused `@prefix nits:` line. Confirmed by grep: no code,
  script, or Makefile target anywhere references this path — the live app resolves its ontology directory to
  repo-root `docs/ontology/` only (`graphdb_client.py`, `parents[3] / "docs" / "ontology"`). Further
  correction: this directory was not actually part of the repository at all — it is named in
  `.git/info/exclude` (a local-only, personal exclude list, never committed or shared with other developers
  or CI), meaning it was local build/checkout residue on this one machine, not shared project content. It
  has since been removed from the local checkout; nothing to commit for this item.

---

## 1. Answer first

**Is NITS safely removable?** Not as a drop-it-and-done change. NITS is not dead alignment scaffolding —
it is the system's only cross-standard concept-bridging mechanism today, and it is wired into the live
question-answering path in several places, not just into offline ontology-generation tooling. Removing it
requires replacing that bridging mechanism first, then deleting the NITS code/data in a specific order (§3),
not simply `git rm`-ing `napcore-its.ttl` and its alignment files.

**Single riskiest dependency:** `backend/helpdesk/services/semantic_graph.py`'s NITS-mediated in-memory
concept expansion — `CONCEPT_TO_NITS`, `NITS_TO_CONCEPTS`, `NITS_RELATIONS`, and the `expand_graph_concepts()`
function built from them. This is:
- called **unconditionally, for every parsed question**, from `question_parsing.py:114`
  (`expanded_concepts = expand_graph_concepts(direct_concepts, hops=1)`), independent of whether GraphDB
  or graph-RAG is even enabled, and
- the **only** cross-standard bridging mechanism used by `retrieval_gateway.py` whenever `GRAPHDB_ENABLED`
  is `False` (verified: `retrieval_gateway.py:1124`) or whenever the live GraphDB SPARQL call raises
  (verified: `retrieval_gateway.py:1121`, inside an `except Exception:` block) — and it has **no
  Transmodel-based equivalent today**.

This makes it the riskiest dependency for two independent reasons: (a) it is structurally the most
deeply threaded through the answer path of everything inventoried, and (b) its failure mode on removal
is **silent degradation**, not a crash — cross-standard concept expansion would quietly stop working
specifically in the GraphDB-disabled/erroring case (a documented recurring condition in this project —
GraphDB reloads take ~17 minutes and the configured SPARQL timeout has been too short for bulk loads, per
prior incidents), while CI (which runs with `GRAPHDB_ENABLED=False`, see §5) would not surface the
regression unless `test_semantic_graph.py` is rewritten to assert the replacement behavior.

A secondary, more immediately user-visible risk is the `"nits:unknown-concept"` sentinel string
(`question_parsing.py:121`) that gates whether the system **refuses to answer at all**
(`semantic_abstention.py:63`) — this is a plain string-literal contract across three files
(`question_parsing.py`, `semantic_abstention.py`, `faq_publication.py`), not a shared constant, so it is
easy to miss one caller while renaming/removing it and either start over-refusing or under-refusing
questions.

---

## 2. Dependency inventory

Every reference found by a repo-wide `grep -rliE 'nits'` scan (code, TTL, docs, tests, Makefile, CI,
benchmark, frontend, `.claude/settings.local.json`), classified by kind and recommended action.
Line numbers were read directly from the files (either by me or by the research agents I dispatched;
every claim used to justify the "answer-time" classifications in group A was independently re-verified
by me by reading the cited lines myself — see §8).

### A. Core cross-standard pivot — answer-time, structural (requires replacement before deletion)

| File:Line | What | Action |
|---|---|---|
| `backend/helpdesk/services/semantic_graph.py:302-381,414-445` | `_load_nits_ontology_from_graphdb()` / `_load_nits_ontology()` — loads the NITS ontology from GraphDB at module-import time into `_NITS_ONTOLOGY` | Rewrite |
| `backend/helpdesk/services/semantic_graph.py:493-803` | `_build_concept_nits_mapping()` builds `CONCEPT_TO_NITS` / `NITS_TO_CONCEPTS` (aliased `CONCEPT_TO_NCH`/`NCH_TO_CONCEPTS`) | Rewrite |
| `backend/helpdesk/services/semantic_graph.py:660-722,806-807` | `_build_nits_relations()` builds `NITS_RELATIONS` (aliased `NCH_RELATIONS`); `_expand_nits_concepts()` hop-expansion helper | Rewrite |
| `backend/helpdesk/services/semantic_graph.py:785-793` | "Cross-standard bridge" in `_build_graph_relations_from_ontology()` — merges `NITS_TO_CONCEPTS` edges directly into `GRAPH_RELATIONS` | Rewrite |
| `backend/helpdesk/services/semantic_graph.py:838-851` | `get_concept_nits_ids()` / `get_concept_nch_ids()` — public API consumed by `question_parsing.py` | Rewrite |
| `backend/helpdesk/services/semantic_graph.py:854-882` | `expand_graph_concepts()` — called unconditionally from every `question_parsing.py.parse()` call (line 114) and as retrieval_gateway's GraphDB-off/error fallback (lines 1121, 1124) | Rewrite — **riskiest item, see §1** |
| `backend/helpdesk/services/semantic_graph.py:250-256` | `_ABSTRACT_NITS_IDS` — duplicated (not shared) with `graphdb_client._ABSTRACT_NITS_PIVOTS`, kept in sync only by a comment | Rewrite |
| `backend/helpdesk/services/graphdb_client.py:40` | `DEFAULT_NAMESPACES["nits"]` | Delete |
| `backend/helpdesk/services/graphdb_client.py:130-133` | `_ABSTRACT_NITS_PIVOTS` | Rewrite |
| `backend/helpdesk/services/graphdb_client.py:286-287,297-298,315,323` | NITS pivot UNION branch inside `query_graphdb_concept_expansion()`'s SPARQL — called live every question via `retrieval_gateway.py:1109` | Rewrite — SPARQL already has a Transmodel-namespace pivot alternative (same function, lines ~298/316), so this is the easier half of the pivot to migrate |
| `backend/helpdesk/services/graphdb_client.py:447-490` | `graph_specs` entries `nits-netex-align` / `nits-opra-align` / `nits-siri-align` loading `docs/ontology/alignments/nits-{netex,opra,siri}-align.ttl` into graphs `https://napcore.eu/graph/alignments/{netex,opra,siri}` | Delete (after step 2.3/3.1, see §3) |
| `backend/helpdesk/services/graphdb_client.py:91-107` | `STANDARD_GRAPH_SCOPE["{netex,opra,siri}"]` lists include the `alignments/{netex,opra,siri}` graphs above — **verified**: these graph names are populated *exclusively* by the `nits-*-align.ttl` files (no other `graph_specs` entry writes to them); the Transmodel alignment graphs use the distinct name `alignments/transmodel-{standard}` | Rewrite — remove the NITS-alignment graph from scope once the GraphDB pivot (above) no longer needs it |
| `backend/helpdesk/services/graphdb_connector.py:91,125,142` | `discover_standards_for_core_concept[_slug]()` — filters/resolves by the `napcore.eu/ontology/nits` namespace string; called live from `question_parsing.py`'s `_discover_standards_with_graphdb` | Rewrite |
| `backend/helpdesk/services/question_parsing.py:25,119,121,241-245,292,313,315` | `_anchor_candidates_to_nits()`, `_anchor_with_graphdb()`'s nits-normalization, `_discover_standards_with_graphdb()`'s nits-namespace gate, the `"nits:unknown-concept"` sentinel | Rewrite — entry point for every question; its sentinel string is a cross-file contract (see below) |
| `backend/helpdesk/services/semantic_abstention.py:63` | Gates whether the system **refuses to answer** on `core_concept == "nits:unknown-concept"` | Rewrite in lockstep with the sentinel change above |

### B. Answer-time but low-risk to decouple (fallback already exists, or unreachable in practice)

| File:Line | What | Action |
|---|---|---|
| `backend/helpdesk/services/llm_generator.py:181,186,187,203` | Imports `semantic_graph._NITS_ONTOLOGY` to build `_UBIQUITOUS_TERMS` (citation-grounding term set); already has a non-NITS hardcoded fallback list at line 203 | Rewrite (trivial — switch to the existing fallback list, extended with a one-time copy of NITS's current terms) |
| `backend/helpdesk/services/example_retrieval.py:160,412` | `PREFIX nits:` + `_ensure_uri` prefix-map entry in a fallback SPARQL branch | Delete, **after** confirming (e.g. temporary logging over a traffic sample) that no live concept ID ever reaches this function with a `nits:` prefix — static trace says it doesn't, but this was not runtime-verified |
| `backend/helpdesk/services/ontology_evidence.py:29-34,464` | `DEFINITION_GRAPHS` includes `https://napcore.eu/graph/core/napcore-its`; `_ensure_uri` prefix-map `nits` entry | Delete, same runtime-verification caveat as above |
| `backend/helpdesk/services/ontology_evidence.py:82,106` | `PREFIX nits:` + `nits:transmodelDefinitionStatus` in `retrieve_concept_definitions()` SPARQL | Rename (not a NITS-class dependency — see next row) |
| `backend/helpdesk/services/transmodel_alignment.py:218,231,239,250-251` | Emits `nits:transmodelDefinitionStatus` / `nits:alignmentMethod` annotation-property triples into the generated `transmodel-{netex,siri,opra}-align.ttl` files | Rename — these are new Transmodel-era properties that merely reuse the `nits:` URI prefix as a naming convenience; they do **not** reference `napcore-its.ttl`'s class hierarchy and can move to a new prefix (e.g. `tmalign:`) independently of the Phase-0/2 pivot rewrite |
| `backend/helpdesk/services/faq_publication.py:115` | Checks `"unknown nits:unknown-concept"` sentinel; offline editorial-publish path only (not live-answer) | Rewrite in lockstep with the sentinel change |
| `backend/helpdesk/services/ontology_registry.py:59-81` | `ONTOLOGY_SPECS` entries for `nits-{netex,opra,siri}-align` — version/hash tracking for the admin reload-detection UI only, no SPARQL | Delete, after the corresponding TTL files are deleted |

### C. Generation / offline tooling (not on the answer path)

| File:Line | What | Action |
|---|---|---|
| `backend/helpdesk/management/commands/extract_xsd_ontology.py:~744` | `"nits"` entry in a hardcoded default `namespaces` dict | Delete — removes an unused `@prefix nits:` line currently emitted into `netex.ttl:12`, `opra.ttl:12`, `siri.ttl:12`, `examples.ttl:11`; **zero `nits:` triples exist in any of these files today** (verified: only "unit(s)" substring false positives otherwise) |
| `backend/helpdesk/management/commands/ontology_alignment_gap.py` (whole file; `_HEURISTIC_RULES` 26-77, `_classify_heuristic()` 82/86, reads of `nits-{standard}-align.ttl` ~145, report text ~187/190/210/257) | Entire purpose is reporting NITS-alignment gaps; writes markdown only, never TTL/GraphDB (per its own `help` text) | Delete whole command |
| `Makefile:158-159` | `ontology-alignment-gap` target invoking the command above | Delete |
| `docs/ontology/alignments/{netex,opra,siri}-alignment-gap.md` | Generated reports from the command above | Delete |
| `backend/helpdesk/management/commands/build_transmodel_alignment.py` | Writes the `nits:transmodelDefinitionStatus`/`nits:alignmentMethod` properties (paired with group B) and `transmodel-alignment-report.md` | Rename property namespace only — this command is the **live** Transmodel-alignment generator and stays |
| `Makefile:114` | Smoke-test one-liner embeds literal `'coreConcept':'nits:test'` as a sample payload | Rewrite — swap for any non-NITS placeholder string; purely cosmetic |
| `.claude/settings.local.json:77,217` | Stale Bash-permission allowlist entries for ad hoc `PREFIX nits:` SPARQL debug queries from earlier interactive sessions | Delete — session tooling residue, zero functional/build impact |

### D. Static/manually-maintained artifacts (no in-repo generator today)

| File | What | Size | Action |
|---|---|---|---|
| `docs/ontology/napcore-its.ttl` | The NITS upper ontology itself. Per `docs/ontology/GENERATION.md`: maintained **by hand**, no regenerable source | 450 lines | Delete — **last** code-adjacent step, after group A/B stop depending on its graph/content |
| `docs/ontology/alignments/nits-netex-align.ttl` | NITS↔NeTEx alignment axioms | 2,676 lines | Delete — after `graphdb_client.py`'s `graph_specs` entry is removed |
| `docs/ontology/alignments/nits-opra-align.ttl` | NITS↔OpRa alignment axioms | 370 lines | Delete, same ordering |
| `docs/ontology/alignments/nits-siri-align.ttl` | NITS↔SIRI alignment axioms | 974 lines | Delete, same ordering |
| `docs/ontology/alignments/transmodel-alignment-report.md` | Generated by `build_transmodel_alignment.py`; genuinely NITS-independent today (its 4 "nits" grep hits are all "unit(s)" false positives) | — | Keep; regenerate after the group-B/C rename to confirm no residual `nits:` text |

### E. Documentation (describes the architecture — must be rewritten, not a functional dependency)

| File:Line | What | Action |
|---|---|---|
| `docs/ontology/GENERATION.md:20,77,88` | Documents NITS's (lack of) generation pipeline; explicitly flags "whether it is needed at all is issue #43" | Rewrite after removal |
| `docs/ontology/README.md:30,34,40-43,64,73,76,94,103` | Describes NITS as the architectural core / 4-layer cross-standard anchor | Rewrite — the largest doc change; the architecture narrative moves from "NITS as anchor" to "Transmodel as anchor". Also: line 43 references `alignments/nits-datex-align.ttl`, which **I confirmed does not exist in the repo** (`ls docs/ontology/alignments/ | grep -i datex` → no match) — drop that stale line regardless of the NITS removal timeline |
| `backend/README.md:103-111` | Documents "GraphDB-backed NITS core concept graph for cross-standard expansion" as a current feature, plus the legacy `maps_to_nch` backward-compat note | Rewrite |
| `docs/ontology/inheritance-chains-reference.md:303` | `numbersOfUnitsInDistance` — "unit(s)" false positive | None |
| `docs/ontology/ontology-enrichment.md` | **Does not exist in the repo** — the original task brief's reference to it was stale | None |

### F. Tests (must change in lockstep with the code they test)

| File | NITS coupling | Action |
|---|---|---|
| `backend/helpdesk/tests/test_semantic_graph.py` | Majority of the file (lines 18, 46, 59, 106, 131, 154, 179 and surrounding) — directly tests `CONCEPT_TO_NITS`/`NITS_TO_CONCEPTS`/`NITS_RELATIONS`/`expand_graph_concepts`/`_build_concept_nits_mapping`/`_build_nits_relations` | Rewrite — largest test-rewrite surface, paired 1:1 with group A's riskiest item |
| `backend/helpdesk/tests/test_graphdb_client.py` | 3 tests (~94, 137, 199) assert the NITS SPARQL pivot/UNION branch and the abstract-NITS exclusion | Rewrite |
| `backend/helpdesk/tests/test_question_parsing.py` | Lines 23, 50, 68, 92, 111, 144, 171 patch `get_concept_nits_ids` and test the anchoring mechanism directly (structural); lines 203, 237 use `nits:`-shaped IDs only as arbitrary mock fixture data (literal-only) | Rewrite the structural ones; relabel the literal-only ones |
| `backend/helpdesk/tests/test_semantic_abstention.py` | Line 16 default fixture is the `"nits:unknown-concept"` sentinel itself; other tests use `"nits:Stop"` only as an arbitrary "known concept" stand-in | Rewrite the sentinel-dependent default; relabel the rest |
| `backend/helpdesk/tests/test_api.py` | Lines 364, 431, 468, 532, 603, 690 — mocked `core_concept` values; only line 431 (`test_answer_returns_clarification_abstain_when_no_concept_match`) is directly coupled to the sentinel | Rewrite line 431's test; relabel the rest |
| `backend/helpdesk/tests/test_ontology_evidence.py` | Line 56 asserts the `nits:transmodelDefinitionStatus` predicate | Rewrite paired with group B's rename |
| `backend/helpdesk/tests/test_transmodel_alignment.py` | Line 139 asserts the same predicate in rendered Turtle | Rewrite paired with group B's rename |

### G. Confirmed non-dependencies (verified — no action needed)

- **CI workflows** (`.github/workflows/*.yml`): zero `nits` references. The retrieval-benchmark workflows run with GraphDB and the LLM fully disabled and do not exercise any NITS code path — see the benchmark blind spot in §5.
- **Frontend** (`frontend/src`): zero `nits` references in source; the only repo-wide frontend hits are inside a minified `frontend/dist` build artifact and `node_modules` (byte-level substring matches, not ontology references).
- **The retrieval benchmark itself** (`run_retrieval_benchmark.py`, `benchmark-questions.yaml`): zero `nits` references — it measures source-chunk retrieval by file path (NeTEx/SIRI/OpRa standards repos), not ontology concepts.
- **`docker-compose*.yml`, `backend/.env.example`, `backend/.env.prod.example`**: zero `nits` references.
- **`docs/ontology/standards/{netex,opra,siri,transmodel,examples}.ttl`**: no real dependency beyond the vestigial `@prefix nits:` line covered in group C; zero `nits:` triples. `transmodel.ttl` has zero NITS references of any kind (its 4 grep hits are "unit(s)" false positives).
- **`docs/ontology/alignments/transmodel-alignment-report.md`**, **`docs/ontology/inheritance-chains-reference.md`**: "unit(s)" false positives only.

---

## 3. Ordered removal steps

Each step is phrased as a claim you can check independently — run the check before moving to the next step.

### Phase 0 — Prerequisite design work (not started; blocks Phase 2)

- **0.1** *A Transmodel-based (or otherwise non-NITS) replacement for cross-standard concept expansion exists and is wired into `question_parsing.py` and `retrieval_gateway.py`'s GraphDB-off/error fallback.*
  Check: with `GRAPHDB_ENABLED=False`, a known cross-standard question (e.g. a NeTEx "VehicleJourney" question) still surfaces SIRI "DatedVehicleJourney" evidence in the retrieval trace.
- **0.2** *A replacement core-concept-identity scheme (replacing `nits:` IDs and the `nits:unknown-concept` sentinel) is implemented in `question_parsing.py`, with `semantic_abstention.py` and `faq_publication.py` updated to the new sentinel.*
  Check: `test_semantic_abstention.py` and `test_api.py::test_answer_returns_clarification_abstain_when_no_concept_match` pass against the new sentinel.
- **0.3** *`graphdb_client.py`'s `query_graphdb_concept_expansion` SPARQL pivots through Transmodel (or another non-NITS hub) instead of the `nits:` namespace, and `STANDARD_GRAPH_SCOPE` no longer depends on the `nits-*-align.ttl` graphs.*
  Check: `test_graphdb_client.py`'s 3 pivot tests pass against the new pivot mechanism.

### Phase 1 — Decouple the low-risk pieces (independent of Phase 0; can start now)

- **1.1** Remove `llm_generator.py`'s `_NITS_ONTOLOGY` import; extend its existing line-203 fallback list to cover the same terms. Check: citation-validation tests show no behavior change.
- **1.2** After confirming via temporary logging that no live concept ID reaching `example_retrieval.py`/`ontology_evidence.py` ever carries a `nits:` prefix, delete those dead-in-practice lines. Check: the added assertion never fires over a representative traffic sample.
- **1.3** Rename `nits:transmodelDefinitionStatus`/`nits:alignmentMethod` to a new prefix in `transmodel_alignment.py` and `ontology_evidence.py`; regenerate the 3 `transmodel-*-align.ttl` files. Check: `grep -i nits` on the regenerated files returns zero hits.
- **1.4** Remove the `"nits"` entry from `extract_xsd_ontology.py`'s default `namespaces` dict; regenerate `netex.ttl`/`opra.ttl`/`siri.ttl`/`examples.ttl`. Check: `grep -i nits` on the 4 files returns zero hits.
- **1.5** Delete `ontology_alignment_gap.py`, its Makefile target, and the 3 generated `*-alignment-gap.md` reports. Check: `make ontology-alignment-gap` no longer exists; the 3 files are gone from git.
- **1.6** Remove `Makefile:114`'s placeholder string and the stale `.claude/settings.local.json` SPARQL-debug permission entries. Check: `grep -i nits` on both files returns zero hits.

### Phase 2 — Remove the structural pivot (only after Phase 0 is verified)

- **2.1 — DONE.** `question_parsing.py` no longer imports `get_concept_nits_ids`/calls any NITS-anchoring method; `core_concept` comes entirely from the Transmodel pivot (falling back to the glossary concept ID itself when Transmodel has no alignment). Verified: rewritten `test_question_parsing.py` passes with `GRAPHDB_ENABLED=False`; `grep -i nits` on the file returns zero hits; a live manual check shows "vehicle journey in NeTEx" now resolves to `transmodel:VEHICLE` (previously `nits:Vehicle`).
- **2.2 — DONE.** `CONCEPT_TO_NITS`, `NITS_TO_CONCEPTS`, `NITS_RELATIONS`, `_NITS_ONTOLOGY`, `get_concept_nits_ids`/`get_concept_nch_ids`, and their builder functions (`_build_concept_nits_mapping`, `_build_nits_relations`, `_expand_nits_concepts`, `_default_nits_concept_id`, `_normalize_nits_target`, `_build_nits_label_index`, `_infer_nits_mapping_from_labels`, `_validate_ontology_payload`) are deleted from `semantic_graph.py`; `expand_graph_concepts` uses only the Transmodel pivot. Verified: rewritten `test_semantic_graph.py` passes; `grep -i nits` on the file returns zero hits (only protective SPARQL `FILTER`s excluding NITS concepts from the main standards load remain, correctly, until Phase 3 deletes the source file they guard against).
- **2.3 — PARTIALLY done** (by the Phase 0 cloud session, before this step was reached deliberately): `_ABSTRACT_NITS_PIVOTS` and the NITS half of the live SPARQL UNION branch in `query_graphdb_concept_expansion` are deleted. **Not yet done, by design:** the `nits-*-align` `graph_specs` entries and `DEFAULT_NAMESPACES["nits"]` remain in `graphdb_client.py` — removing the load spec while the TTL files it points at still exist would stop using them without deleting them, which is exactly Phase 3's job, not this step's.
- **2.4 — DONE.** `discover_standards_for_core_concept_slug` (the method that resolved NITS concept slugs) is deleted from `graphdb_connector.py` along with its one caller; its sibling method `discover_standards_for_core_concept` is untouched (generic, still used by the Transmodel branch) and keeps its protective NITS-exclusion filter. No dedicated `test_graphdb_connector.py` existed or was needed — the method had no direct test coverage to begin with.
- **2.5 — not started.** `semantic_abstention.py`/`faq_publication.py` still check the Phase-0 sentinel (`UNKNOWN_CONCEPT_SENTINEL = "unknown-concept"`, already namespace-free) — nothing further to do here; this step is effectively subsumed by Phase 0's sentinel change.
- **2.6 — not started.** `ontology_registry.py`'s `nits-{netex,opra,siri}-align` `ONTOLOGY_SPECS` entries are untouched, deliberately — same reasoning as 2.3, these track files that still exist until Phase 3.

### Phase 3 — Delete the static artifacts and reload GraphDB (see §4 for exact commands)

- **3.1** Delete `docs/ontology/napcore-its.ttl` and the 3 `nits-{netex,opra,siri}-align.ttl` files. Check: a full-repo `grep -ri nits` (excluding this plan document and git history) returns zero hits.
- **3.2** Add the retired graph URIs to `RETIRED_GRAPH_URIS` (§4) and run a replace-load against a **non-production** GraphDB instance. Check: a `SPARQL ASK` for any triple under `https://napcore.eu/ontology/nits#` returns `false`.
- **3.3** Run `make graphdb-verify` (or the equivalent `scripts/verify-graphdb-ontology-state.sh`). Check: the script's own exit code / output.

---

## 4. GraphDB reload steps

1. Confirm, before touching `RETIRED_GRAPH_URIS`, that `https://napcore.eu/graph/alignments/{netex,opra,siri}` carry **only** NITS-alignment content — verified in §2 group A: these three graph names are populated exclusively by `graph_specs` entries pointing at `nits-{netex,opra,siri}-align.ttl` (`graphdb_client.py:466-480`); the parallel Transmodel-alignment graphs use the distinct name `alignments/transmodel-{standard}` (lines 482-489). No other `graph_specs` entry writes into `alignments/{netex,opra,siri}`.
2. Add to `graphdb_client.py`'s `RETIRED_GRAPH_URIS` (next to the existing `alignments/transmodel` entry, which already documents the precedent for retiring a graph whose source TTL was deleted):
   - `https://napcore.eu/graph/core/napcore-its`
   - `https://napcore.eu/graph/alignments/netex`
   - `https://napcore.eu/graph/alignments/opra`
   - `https://napcore.eu/graph/alignments/siri`
3. Delete the corresponding `graph_specs` entries (step 2.3/3.1 above) so a future reload doesn't recreate them.
4. Run, against a **non-production** GraphDB instance only:
   ```
   make graphdb-load      # python manage.py load_graphdb_ontologies --apply --replace --include-artifact-rules
   make graphdb-verify    # scripts/verify-graphdb-ontology-state.sh
   ```
5. Confirm removal with a direct SPARQL check:
   ```sparql
   ASK { ?s ?p ?o . FILTER(CONTAINS(STR(?s), "napcore.eu/ontology/nits") || CONTAINS(STR(?p), "napcore.eu/ontology/nits") || CONTAINS(STR(?o), "napcore.eu/ontology/nits")) }
   ```
   Expected: `false`, across all graphs (default + named).
6. This plan does **not** touch production, any server, or any credentials — step 4/5 must run against a local or staging GraphDB only, per standing project policy.

---

## 5. Benchmark protocol

### 5.1 What I attempted

I looked for a way to get a baseline before/after numbers, per the task brief. I did **not** run the benchmark. Two independent blockers, both confirmed directly:

- **Docker is not running** on this machine (`docker ps` → `failed to connect to the docker API ... no such file or directory`), so the local GraphDB container is not up. The project's own standing workflow is to start Docker manually and then `make dev-up` — I did not start it myself.
- **`backend/.env` is configured for a live LLM endpoint** (`LLM_API_BASE_URL`, `LLM_API_KEY` etc. are set to real values, confirmed by listing variable names only). Running the benchmark locally with this `.env` would make real network calls to a live LLM, which I will not do without explicit confirmation.

**No numbers are given anywhere in this plan.** The task brief's prior figures (hit@10 ≈ 0.90, MRR ≈ 0.479 on 100 questions) are **not re-measured and not to be trusted** — treat them as stale until a real run produces fresh numbers.

### 5.2 A more important finding: the existing CI benchmark cannot validate this removal

Reading `.github/workflows/benchmark-regression.yml` and `benchmark-release-gate.yml` (the only places `run_retrieval_benchmark` is actually invoked — it is **not** wired into the Makefile at all) shows both set:
```
GRAPHDB_ENABLED: "False"
NAPCORE_SKIP_GRAPHDB_IMPORT: "1"
GRAPH_RAG_ENABLED: "False"
LLM_ENABLED: "False"
CONTROLLER_LLM_ENABLED: "False"
```
Per the workflow's own header comments, this means CI's gated retrieval benchmark measures hash-embedding-based source-chunk retrieval only, and explicitly does **not** cover "GraphDB-backed retrieval (ontology definitions, example lookup, graph scope)" — i.e. it never exercises any NITS-dependent code path (the GraphDB pivot in `graphdb_client.py`, or even the in-memory `expand_graph_concepts` fallback, since `GRAPH_RAG_ENABLED=False` skips concept expansion entirely per `retrieval_gateway.py:1095`'s `if graph_rag_enabled and question_concepts:` guard).

**Implication:** running the standard CI benchmark before and after NITS removal, and seeing identical (or even improved) hit@10/MRR numbers, would prove nothing about whether the removal broke cross-standard answering — the benchmark's gated metrics structurally cannot see that code path. A before/after comparison that matters would need to run with `GRAPHDB_ENABLED=True` and `GRAPH_RAG_ENABLED=True` against a real GraphDB instance, and ideally also once with `GRAPHDB_ENABLED=False` (to exercise the in-memory fallback specifically, since that's the riskiest path per §1).

### 5.3 Recommended protocol, once infrastructure is available

1. Start Docker and GraphDB manually (`make dev-up`, or just `docker compose -f docker-compose.dev.yml --profile local-db up -d graphdb` + `make graphdb-bootstrap`) — do not let an agent start this unattended.
2. Baseline run A — GraphDB on: `GRAPHDB_ENABLED=True GRAPH_RAG_ENABLED=True python manage.py run_retrieval_benchmark --output baseline-graphdb.json` (before any code change).
3. Baseline run B — GraphDB off: `GRAPHDB_ENABLED=False GRAPH_RAG_ENABLED=True python manage.py run_retrieval_benchmark --output baseline-memory-fallback.json` (exercises the `expand_graph_concepts` fallback specifically).
4. After each removal phase (§3), re-run both A and B and diff against the phase-0 baseline, not just the CI-default (GraphDB-off, graph-RAG-off) numbers.
5. Add a small, explicit set of cross-standard questions (e.g. NeTEx↔SIRI vehicle-journey pairs) to `benchmark-questions.yaml` if one doesn't already exist, tagged so they can be filtered with `--tags`, specifically to detect cross-standard-bridging regressions that the existing question set (benchmarked by file path, not by ontology concept) may not catch.
6. Do not treat a passing CI run (`benchmark-regression.yml`) as sufficient evidence that NITS removal is safe, per §5.2.

---

## 6. Rollback notes

- Every deletion in Phases 1–3 is a `git revert` away as long as it lands in discrete, reviewable commits per phase/step (recommended: one PR per phase, not one PR for the whole removal).
- GraphDB-side changes (§4) are the only non-trivial-to-revert step: once `RETIRED_GRAPH_URIS` causes a graph to be dropped on a `--replace` load, restoring it requires re-adding the `graph_specs` entry **and** re-running `load_graphdb_ontologies --apply --replace` with the TTL file restored from git history (`git show <commit>:docs/ontology/napcore-its.ttl` etc.) — the files should not be deleted from git history (a normal `git rm` + commit preserves them in history; do not squash/rebase them away).
- Because `expand_graph_concepts()` is evaluated once at module-import time (`_ONTOLOGY`/`_NITS_ONTOLOGY` module globals), a rollback also requires a process restart (Django dev server / gunicorn workers), not just a code revert — the old NITS data won't reload into a running process.
- Recommended safety net: keep Phase 0's replacement cross-standard-bridging mechanism behind a feature flag (e.g. reuse the existing `GRAPH_RAG_ENABLED`-style settings pattern) through Phase 2, so a regression can be mitigated by a config flip before a full code revert is needed.

---

## 7. Risks and unknowns

**Risks (ranked):**
1. Removing the semantic_graph.py in-memory fallback (§1, group A) without Phase 0's replacement silently breaks cross-standard concept expansion specifically when GraphDB is disabled or erroring — a documented recurring operational condition in this project, and not covered by the standard CI benchmark (§5.2).
2. The `"nits:unknown-concept"` sentinel is a plain string-literal contract across 3 files (`question_parsing.py`, `semantic_abstention.py`, `faq_publication.py`) with no shared constant — a missed caller during the rename changes abstention behavior (over- or under-refusal) without raising an error.
3. `STANDARD_GRAPH_SCOPE`'s `alignments/{netex,opra,siri}` graphs are confirmed to be exclusively NITS-alignment content today (§2, §4.1), but that is a snapshot fact about the current codebase, not an invariant — if someone adds unrelated content to those graph names before this removal lands, retiring the whole graph would silently drop it too. Re-verify immediately before executing Phase 3.
4. Groups B's "dead-in-practice" classifications (`example_retrieval.py`, `ontology_evidence.py`'s `DEFINITION_GRAPHS`/`_ensure_uri` entries) rest on a static trace that no `nits:`-prefixed concept ID reaches those functions today — this was not runtime-verified (no test suite run, no live traffic sampled). Confirm with logging before deleting (Phase 1 step 1.2).
5. `docs/ontology/README.md` references `alignments/nits-datex-align.ttl`, a file that does not exist in the repo — a pre-existing documentation bug, unrelated to NITS removal per se, but worth fixing in the same pass (§2 group E).
6. No dedicated test file for `graphdb_connector.py` was found during this inventory — its NITS-dependent methods are only exercised indirectly (if at all) through `test_graphdb_client.py` or callers. Confirm coverage before Phase 2 step 2.4.

**Unknowns (not verified by reading code or running anything):**
- Whether `query_graphdb_concept_expansion()`'s NITS-pivot UNION branch actually returns non-empty results against the live production GraphDB data today (static SPARQL reading only — no live query was run).
- Whether any HTTP API consumer-facing surface (views/serializers) ever exposes a raw `nits:`-prefixed concept ID to an external caller — this inventory covered the service layer named in the brief plus the files their symbols led into, not the full views/serializers layer.
- Actual benchmark numbers before or after removal — none were measured (§5.1); none should be trusted until measured.
- Whether `transmodel-alignment-report.md`'s generation path inside `build_transmodel_alignment.py` has any other NITS coupling beyond the `nits:transmodelDefinitionStatus`/`nits:alignmentMethod` properties already identified — the file was located but not read in full.

---

## 8. Verified facts vs. assumptions

### Verified (by directly reading the cited file/line, either by me or a dispatched research agent whose specific line citations I independently re-read and confirmed)
- The exact call chain `retrieval_gateway.py:1091-1130` showing `expand_graph_concepts` as the unconditional GraphDB-off path (line 1124) and the GraphDB-exception fallback (line 1121).
- `question_parsing.py:114-121` calling `expand_graph_concepts` unconditionally (independent of `graph_rag_enabled`) and setting the `"nits:unknown-concept"` sentinel.
- `semantic_abstention.py:62-65` gating the refusal message on that exact sentinel string.
- `semantic_graph.py:838-882` — `get_concept_nits_ids`/`expand_graph_concepts` implementation, confirming the cross-standard "glossary → NITS → neighboring NITS → glossary" bridging logic.
- `graphdb_client.py:447-490` — the full `graph_specs` list, confirming `alignments/{netex,opra,siri}` are populated only by `nits-*-align.ttl` and that Transmodel alignment graphs use a separate name.
- CI workflow GraphDB/LLM-disabled flags in `benchmark-regression.yml` (lines 41-45).
- `nits-datex-align.ttl` does not exist in `docs/ontology/alignments/`.
- `build_transmodel_alignment.py` is the source of `transmodel-alignment-report.md` (resolves a gap the research agent flagged as unverified).
- Line counts of the 4 files slated for deletion in group D.
- Docker is not running on this machine; `backend/.env` is configured with live LLM endpoint variable names (values not read).

### Believed, not independently re-verified by me (taken from the research agents' reports on trust, because the specific line citations were consistent across multiple independent agents and internally consistent with the parts I did re-verify)
- The precise line numbers for every entry in groups B, C, E, F above that I did not personally open and re-read.
- The claim that zero `nits:` triples exist in `netex.ttl`/`opra.ttl`/`siri.ttl`/`examples.ttl` beyond the vestigial `@prefix` line (based on the agents' grep sampling, not an exhaustive triple-by-triple check by me).
- The claim that `frontend/src` has zero NITS references (based on the agent's grep, not re-run by me).

### Assumed
- That the maintainer's intended replacement for NITS's cross-standard bridging role is Transmodel-based, since Transmodel is described as "now the reference/entry point" in the task brief and the SPARQL already supports an alternative Transmodel pivot — but no design for the in-memory (`expand_graph_concepts`) replacement exists yet, and this plan does not design one.
- That retiring the `alignments/{netex,opra,siri}` graph names in Phase 3 is safe given today's `graph_specs` wiring — flagged as a re-check-immediately-before-executing item in §7, not a standing guarantee.
