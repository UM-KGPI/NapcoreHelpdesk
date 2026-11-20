# Retrieval benchmark

`python manage.py run_retrieval_benchmark` asks the retrieval step each question of
`backend/helpdesk/benchmarks/benchmark-questions.yaml` (149 questions) and checks whether the expected source files
are among the passages it returns. It runs every question twice, as baseline and with graph retrieval, and writes a
JSON report. It never calls a language model.

## Two ways to run it

**The benchmark's own conditions (the default).** For each question k is the larger of `--top-k` (20) and the
question's own `top_k_threshold` (10 or 20), the minimum score is 0, and the report has hit@5, hit@10, hit@20,
MRR@10 and MRR@20. This is what CI runs against `backend/helpdesk/benchmarks/ci-baseline.json`. It is a guard
against regressions in the retrieval code. It is not the number users get.

**The application's path (`--app-conditions`).** The answer endpoint asks retrieval for a fixed k of 6, a minimum
score of 0.62 and `min_results` equal to `LLM_MAX_EVIDENCE_CHUNKS` (6 by default), and gives the answer the first 6
passages. This mode uses exactly those values, read from the same place the endpoint reads
(`backend/helpdesk/services/answer_retrieval_defaults.py` and the setting). Per mode it reports hit@5, hit@6 and
MRR@6 over the first 6 passages only, the number of questions that end with fewer than 6 passages, and the number
that end with none. Add `--app-scope` to search with the scope the endpoint chooses for each question, as the
application does. `--top-k` and `--gate-against` are refused with it: the baseline file has no figure at that k.

The endpoint also does things the benchmark does not: it matches stored FAQ answers first, retries with a lower
score when nothing is found, and adds evidence for concepts named in the question. The mode measures the retrieval
call, not the whole answer.

## What the report says about its conditions

At start the command prints a `BENCH-CONDITIONS:` line (mode, k, minimum score, `min_results`, scope mode and the
number of ontology concepts loaded), and the JSON report carries the same under `conditions`. If graph mode is
requested and the ontology holds no concepts, it prints a `BENCH-WARNING:` line saying so and why, at the start and
again under the summary, and marks it in the report (`ontology_empty`, `warnings`). With `--app-conditions` it
refuses to run in that case. `--acknowledge-empty-ontology-is-not-the-app` lets it run anyway; the report then says
the ontology was empty and that this was acknowledged.

## Measuring the application's path on a machine with GraphDB

You need the same stack the application runs on:

- GraphDB running and reachable, with the ontology loaded: `GRAPHDB_ENABLED=True`,
  `GRAPHDB_SPARQL_ENDPOINT` set, `GRAPH_RAG_ENABLED=True`.
- `NAPCORE_SKIP_GRAPHDB_IMPORT` not set. It makes the ontology load return an empty table, and nothing fills the
  table afterwards.
- The embedding service reachable, and the language models off: `LLM_ENABLED=False`,
  `CONTROLLER_LLM_ENABLED=False`.
- The database and the index settings the application serves with (for the prepared cut: `RETRIEVAL_PREPARED_INDEX`,
  `VECTOR_INDEX_DIMENSIONS`, `VECTOR_INDEX_HALF_PRECISION`, `VECTOR_INDEX_PROBES`, `RETRIEVAL_MAX_SAME_SOURCE_PATH`).
  Read the database, never write to it.
- `LLM_MAX_EVIDENCE_CHUNKS` as in the environment you want to describe; a developer `.env` can set a lower value
  than the default 6, which lowers `min_results`.

Then, from `backend/`:

```
python manage.py run_retrieval_benchmark --app-conditions --app-scope --quiet --output app-conditions.json
```

Check the first lines of the output: `ontology_concepts=` should be in the thousands, and there must be no
`BENCH-WARNING:` line.

## What CI can and cannot measure

CI (`benchmark-regression.yml`, `benchmark-release-gate.yml`) has no GraphDB and no semantic embedder. It sets
`NAPCORE_SKIP_GRAPHDB_IMPORT=1` and `GRAPHDB_ENABLED=False`, indexes the old cut with deterministic hash vectors,
and runs the default mode with an empty ontology. Its log now shows the `BENCH-WARNING:` line, which is correct:
the graph figures there come without ontology concepts. CI can tell me that a change made retrieval worse at the
benchmark's own k on that index. It cannot tell me what the application serves: not the ontology's concept
extraction and passage boost, not semantic vectors, not the prepared cut, not k 6 with minimum score 0.62.
`--app-conditions` refuses to run in CI's environment unless acknowledged, so CI does not report an application
number by accident.

The reference figures for the application's path on the developer stack, with their conditions, are in the
`not_the_applications_number` note of `backend/helpdesk/benchmarks/ci-baseline.json`.
