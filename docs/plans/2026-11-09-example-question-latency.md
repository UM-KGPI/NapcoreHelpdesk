# Plan: faster example questions, same semantic retrieval

Written 2026-11-09 against 0.97.139. For the implementing agent/engineer. Every number below was measured on the
dev stack (Docker, 4 CPUs, 62,029 chunks, semantic embeddings, Claude Haiku 5.5) unless marked **prod**.

## 1. Where the time goes now

Prod (0.97.139, single runs, non-stream endpoint): stop place with two quays 26 s, fare zone 28 s, lift 17 s,
vehicle type 21 s; a plain question ("What is a StopPlace in NeTEx?") 15 s.

Local, same example question (14.5 s total), by stage:

| Stage | Local | Note |
|---|---|---|
| `_parse_question` | 1.0 s | GraphDB anchor 0.43 s + language detection (`question_language` runs twice, 0.48 s) |
| `retrieve_chunks_with_trace` (one pass) | 4.9–5.4 s | plain question: 3.3–3.6 s |
| ├ `postgresCandidateQueryMs` | **2.0–2.2 s** | two full-table scans of the vector column, every question |
| ├ `graphCandidateQueryMs` | 0.65–0.93 s | alias OR-query (113 ms, uses trgm indexes) + Python ranking |
| ├ `candidateSelectionMs` | 0.38 s (plain: 0.9 ms) | `_named_example_candidates`: a query that returns **0 rows** for NeTEx |
| ├ `candidateScoringMs` | 0.4 s | |
| ├ `elementCandidateMs` | 0.24 s | |
| `generate_netex_example` (standard-example lookup) | 0.2–0.3 s | |
| `_example_element_evidence` | 0.05–0.13 s | |
| `generate_answer_llm` | **6–8 s, usually one Haiku call** | **Corrected after P0 (2026-11-09):** the time follows output tokens, which include adaptive thinking: 1,450–1,860 tokens took 6.0–8.3 s, 350–450 tokens took 2.1–2.4 s, for visible answers of similar length. A validator retry happened in 1 of 9 answers, not "nearly every" one as first written. |

Not a lever: Anthropic effort. The prompt is 8.6k input tokens; replaying the same call: `low` 2.3–2.8 s (530–610
output tokens), `medium` 7.1–8.6 s (1.7–2.0k tokens), `high` 8.3–8.7 s (2.0–2.2k tokens). Settings already use `low`;
at `low`, Haiku 5.5 still thinks adaptively and sometimes at length.

Thinking off (`thinking: {"type": "disabled"}`, accepted on Haiku 5.5 at effort `high` or below), measured end to end
on the 9 questions of §5, one run each: mean model time 5.9 s → 3.6 s; first-answer rejections 1 → 2; and two answers
followed the rules less well (one pasted the whole shown StopPlace fragment into the text, against the "do not repeat
the fragment" rule; the lift question fell back to a bare list of evidence blocks). This is a speed-for-quality trade:
a decision for the product owner, not part of this plan unless approved; if approved, add a setting
(`LLM_ANTHROPIC_THINKING`, default `adaptive`) rather than changing the default silently.

## 2. Constraints

- Keep semantic retrieval (e5 embeddings, pgvector) and concept matching by meaning; nothing falls back to label words.
- Results must stay: the CI retrieval benchmark gate (`run_retrieval_benchmark --gate-against helpdesk/benchmarks/ci-baseline.json --max-drop 0.03`, 140 questions, hash backend) must pass, and the semantic index must be benchmarked locally (see §5).
- General solutions only; no question-specific tuning. No Claude/AI attribution in commits or PRs. Stop at the PR unless told "full cycle".

## 3. Work items, in order

### P0 — Make prod measurable (small, first)

`backend/helpdesk/api/views.py` hard-codes `"retrievalLatencyMs": 0.0` in the stored trace (lines ~1257 and ~1903) and never
copies `retrievalStageTimingsMs`, although `_retrieve_chunks_once` computes both (`retrieval_gateway.py` ~2497).
Add to the stored trace: `retrievalLatencyMs`, `retrievalStageTimingsMs` (from `graph_trace`), `llmMs` (around the
`generate_answer_llm` / `stream_answer_llm` calls), `exampleMs` (from `generated_example["generationMs"]`) and `parseMs`.
Then every prod question event can be profiled from `/questions/events/<id>` without a server session.
Verification: ask one question locally, read the event, see non-zero values. Measure the 5 prod questions of §5 before P1.

### P1 — Vector search through an index (largest win, all questions)

**Finding.** `_postgres_hybrid_candidates` (`retrieval_gateway.py` ~381–440) orders by `(1.0 - (embedding_vector <=> q)) DESC`.
pgvector can only use an index for `ORDER BY embedding_vector <=> q` (ascending, raw operator), so the ivfflat index from
migration 0009 (`sourcechunk_embedding_ivfflat_idx`, lists=100) has **never been used** (`pg_stat_user_indexes.idx_scan = 0`).
Each pass runs two parallel seq scans (cutoff query 1.07 s + ranked query 1.1 s), each reading ~2.3 GB of buffers: the
1536-dim vectors live in TOAST (heap 298 MB, index 970 MB, total 3.1 GB). On prod (Xeon 4210, 2.2 GHz, default
`shared_buffers`) this is most of the ~8 s per retrieval pass noted in memory.

Measured on 8 queries (NeTEx / SIRI / OpRa / EU legislation / unscoped), top-30 overlap with the exact scan:

| Query form | ms per query | overlap /240 | top-10 /80 |
|---|---|---|---|
| exact (current) | 200–1,340 | 240 | 80 |
| ivfflat, `probes=10`, `iterative_scan=relaxed_order` | 100–270 | **240** | **80** |
| ivfflat, `probes=5`, iterative | 60–145 | 196 | 66 |
| HNSW 384-dim, `ef_search=40`, no iterative scan | 11–36 | 141 (0/30 on SIRI, OpRa, EU) | 49 |
| HNSW 384-dim, `ef_search=40`, iterative | 1–96 | 227 | 78 |
| HNSW 384-dim, `ef_search=100`, iterative | **2–18** | **234** | **78** |

The scope filter (`standards_scope @> '["SIRI"]'`) is why the iterative scan is mandatory: without it a small scope
gets 0 rows. pgvector here is 0.8.3 (iterative scans exist since 0.8.0).

**Tier 1 — no schema change (do first, ships alone).** Rewrite `_postgres_hybrid_candidates` as one query:
nearest `limit` rows by `ORDER BY embedding_vector <=> %s LIMIT n` (a subquery/CTE), then `ts_rank` and the final
`ORDER BY -similarity, -lexical_rank, id` on those n rows only (today's "cutoff then rank" trick exists only because the
text-search vector was built for every row; ranking n rows makes it unnecessary). Inside `transaction.atomic()` run
`SET LOCAL ivfflat.probes = 10` and `SET LOCAL ivfflat.iterative_scan = 'relaxed_order'` (settings, with defaults).
Keep rows with a NULL vector (today they sort first); today every row has a vector, so a cheap union is enough.
Expected: 2 × ~1.1 s → ~0.2 s per pass locally; more on prod. Results: identical on the 8-query sample.

**Tier 2 — HNSW on the real 384 dimensions.** Semantic vectors are 384-dim padded with zeros to 1536
(`embeddings.py` line 114); `vector_norm(subvector(embedding_vector, 385, 1152)) = 0` for all 62,029 rows, so
`subvector(embedding_vector, 1, 384)::vector(384)` is lossless and 4× smaller (trial index 121 MB vs 970 MB).
- Index: `CREATE INDEX CONCURRENTLY sourcechunk_embedding_hnsw384_idx ON helpdesk_sourcechunk USING hnsw ((subvector(embedding_vector,1,384)::vector(384)) vector_cosine_ops) WITH (m=16, ef_construction=64)`.
  Build it from a management command (`build_vector_index`), not inside a migration: `CONCURRENTLY` cannot run in a
  transaction, and prod's compose runs `migrate` before gunicorn starts, so a slow migration is downtime. The worker can
  run the command at startup like `build_concept_vectors` (idempotent: `IF NOT EXISTS`, check `pg_index.indisvalid`).
- Build settings: a parallel build with `maintenance_work_mem='256MB'` **failed** in Docker ("could not resize shared
  memory segment … No space left on device": the container's `/dev/shm` is 64 MB). Either `SET max_parallel_maintenance_workers = 0`
  for the build, or add `shm_size` to the db service. The default-memory build worked. Build time: see §6.
- Query form, used only when `EMBEDDING_BACKEND == "semantic"` **and** the index exists and is valid (cache the
  `pg_indexes` check per process, re-check on failure): `ORDER BY subvector(embedding_vector,1,384)::vector(384) <=> %s::vector(384)`
  with `SET LOCAL hnsw.ef_search = 100; SET LOCAL hnsw.iterative_scan = 'relaxed_order'`. Otherwise Tier 1.
  Hash vectors fill all 1536 dimensions, so the 384-dim form would be wrong under the hash backend (CI).
- `reembed_chunks --swap` reindexes `VECTOR_INDEX` after swapping columns (`reembed_chunks.py` ~38, ~117): include the new index.
- The query embedding is built once per pass already (`queryEmbeddingMs` 12 ms); pass its first 384 values.

Risk: approximate neighbours. Gate with the benchmarks in §5; keep Tier 1 as the fallback switch (a setting).

### P2 — Stop the zero-row example query

`_named_example_candidates` (`retrieval_gateway.py` ~563) queries `doc_type='example' AND heading <> ''` ordered by
`source_path` with `LIMIT 2000`; the planner walks the `source_path` index and filters all 62k rows, 0.44–0.77 s per
pass, and for NeTEx/SIRI/OpRa it returns **0 rows** (only Turtle examples carry type headings; the feature is for
mobilityDCAT-AP). Fix: compute once per process (refresh with the index's chunk count or a TTL) the set of standards
whose example chunks have headings (`SELECT DISTINCT standards_scope … WHERE doc_type='example' AND heading<>''`), and
return `[]` without a query when the scope has none. Alternative: a partial index `(doc_type, source_path) WHERE heading <> ''`.
Expected: 0.4–0.8 s per pass locally for NeTEx questions. Results unchanged (the query returned nothing).

### P3 — Fix the validator false positives (fewer retries, no empty lift text)

**Corrected after P0:** retries are less frequent than first written (1 of 9 answers with thinking on), so the
time saved is smaller (~2.5–3 s on the answers that retry). The quality reason stands. When a retry happens, and the retry fails too,
the lift question ends with an empty text beside its example (`_nothing_to_add`, `llm_generator.py` ~1465) or a
"review required" flag. Three defects, all in `backend/helpdesk/services/llm_generator.py`:

1. `_ELEMENT_PURPOSE_CLAIM_PATTERN` (~670) matches nouns: "`AlightingUse` **flags**", "the **means** of calling a lift",
   "**marks**". Require the element mention to be the subject right before the verb (mention, optional "element/attribute",
   then the purpose verb), or require a verb form ("is used to", "indicates that") rather than bare "flags|means|marks".
2. `_XML_ELEMENT_MENTION_PATTERN` (~661) treats any backticked word as an element: "`indoors`" (a value) was flagged.
   Match element names only (CapitalCase/camelCase, as in `[A-Z][A-Za-z0-9]*`).
3. Reporting the shown fragment's values ("sets `Covered` to `indoors`", "carries `Name`, `Width` …") is description,
   not a purpose claim; a sentence whose elements all occur in the shown example fragment and that states values should
   pass. The example path already tells the model the fragment is shown.
Plus, in evidence building: `format_definitions_as_chunks` (`retrieval_gateway.py`) emits Transmodel definition chunks
without `docType` (the presence chunks for LIFT CALL EQUIPMENT have `docType None`), so `_element_has_definition_in_evidence`
(~684, set `_DEFINITIONAL_DOC_TYPES` ~681) does not count them; set `"docType": "ontology-definition"`. And
`_example_element_evidence` (`views.py` ~1731) should place the presence/concept definition chunks before the generic
element definitions so they are within the first `LLM_MAX_EVIDENCE_CHUNKS` (4) blocks the model and validator see.
Rejected sentences to turn into unit tests (verbatim from the logs):
- "Each `Quay` has a `Name`, a `Covered` value (both are `indoors`), and `BoardingUse` and `AlightingUse` flags. … [E3]"
- "The means of calling a lift, such as button height, is a separate concept, `LiftCallEquipment` [E2]."
- "It is also described as a specialisation of access equipment, with the same kind of lift characteristics [E3]." (rejected as "citation without specific technical content"; check that rule's false-positive rate on the 8 questions too)
Expected: no empty lift text, fewer "review required" answers, ~2.5–3 s saved on the answers that retry. Verification: retry rate over the 8 questions of §5 (before: 2 of 2 sampled retried) and
the validator's true positives must stay (existing tests in `test_llm_generator.py`).

### P4 — Overlap the independent work (smaller)

Run concurrently with retrieval in a `ThreadPoolExecutor` (each thread closes its DB connection): the standard-example
lookup (`generate_netex_example` for a standard example needs no chunks; 0.2–0.3 s), `presence_evidence`, and the
GraphDB anchor in `_parse_question` (0.43 s). Cache `question_language` per question (called twice, 0.48 s).
Expected: 0.5–1 s locally, more on prod. Do this last; it adds threading to the request path.

### Not planned

Changing the embedding model (trial 2026-11-08: none beat e5-small), raising Anthropic effort (slower, no gain),
dropping concept matching, or trimming evidence below 4 blocks.

## 4. Expected result

Local example question: 14.5 s → about 10–11 s from P1, P2 and P4 (retrieval 4.9 → ~2.3 s); the model's thinking
(2–8 s, varies per call) stays unless thinking-off is approved (§1). Plain question: 5.9 → ~4 s.
Prod (estimate, prod retrieval is CPU-bound and the vector scans weigh more there): example questions 26–28 s → ~15 s,
plain ~15 s → ~9 s. Treat as estimates until P0 numbers from prod are in.

**P0 status (2026-11-09):** implemented. Every stored trace now has `timingsMs` (parseMs, retrievalMs/retrievalCalls,
llmMs/llmCalls/llmOutputTokens, exampleMs, totalMs) plus `retrievalLatencyMs` and `retrievalStageTimingsMs`.

## 5. Verification protocol (every PR)

1. Unit tests: the changed modules plus `python manage.py test` (16 known environment failures locally; none new).
2. CI gate: `run_retrieval_benchmark --quiet --gate-against helpdesk/benchmarks/ci-baseline.json --max-drop 0.03` (runs in CI with the hash backend, so it exercises Tier 1, not HNSW).
3. Semantic benchmark locally (the semantic index, app scope): `run_retrieval_benchmark --app-scope`; reference 2026-11-08: hit@10 0.919, MRR@10 0.654 (149 questions). Also `run_concept_benchmark --method app` (23/26) and `run_example_benchmark`.
4. Timing set, local and prod, single runs each, before and after:
   - Show me a NeTEx example of a stop place with two quays.
   - Show me a NeTEx example of a fare zone.
   - How do I describe a lift in a station in NeTEx? Show me an example in XML.
   - Show me a NeTEx example of a stop place with an elevator.
   - Give me an example of a quay in NeTEx.
   - Show me a NeTEx example of a day type.
   - How do you describe a stop place in NeTEx? Show me an example with two quays.
   - Show a NeTEx example of a vehicle type.
   - What is a StopPlace in NeTEx? (control, no example)
   Record total seconds, example origin/validated, answer length, review flag and LLM call count. Read the answers before/after side by side.
5. Prod: deploy, then the same questions through `/questions/answer` with `X-Request-Id: req-diag-…`, and the stage timings from P0.

## 6. Measurements and commands used (for reproduction)

- Stage timings: `retrieve_chunks_with_trace(..., english_question=None)` and read `trace["retrievalStageTimingsMs"]`.
- SQL profile: `django.test.utils.CaptureQueriesContext` around one retrieval, `EXPLAIN (ANALYZE, BUFFERS)` of the slow ones.
- Index trial: `CREATE INDEX CONCURRENTLY trial_hnsw_384_idx … hnsw ((subvector(embedding_vector,1,384)::vector(384)) vector_cosine_ops)`; recall measured as top-30/top-10 overlap with the exact ordering on 8 queries; trial index dropped afterwards.
- HNSW build time, 62,029 rows, `CONCURRENTLY`, `max_parallel_maintenance_workers=0`, `maintenance_work_mem='256MB'`: **25 s** locally (index 121 MB). Expect about a minute on prod's slower cores; the default-memory build also completes, more slowly.
- LLM replay: capture `anthropic_chat.chat_completion` kwargs during one question, replay at efforts low/medium/high.
