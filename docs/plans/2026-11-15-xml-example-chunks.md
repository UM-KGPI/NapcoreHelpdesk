# Plan: cutting the XML examples into pieces that can be told apart

Written 2026-11-15 against 0.97.226, for the implementer. It continues
`2026-11-15-right-piece-of-cited-file.md` (the diagnosis and the failed step; its §4 holds the numbers used here).
Each claim is labelled **measured**, **believed** or **assumed**.

## 1. The problem

The helpdesk cites the right example file and gives the model the wrong piece of it. The case: "How to model
number of late journeys?" was refused, citing an OpRa example whose fourth and fifth piece hold
`LateDatedVehicleJourneyCount`; the model had read the second piece, the file's opening.

## 2. What is known

- **Measured**: the index holds 43,193 pieces of 405 XML example files (median 1,471 characters, median 8 pieces
  per file, one file has 9,855). `split_xml` starts a new segment only at a line indented by at most two spaces,
  so the body of an example is cut by lines at 1,200 characters: in the middle of elements, without overlap, and
  without any trace of where in the document the piece sits. 88% of the pieces start three or more levels deep.
- **Measured**: within one file the pieces can hardly be told apart by the search. In the case the five pieces
  have a similarity of 0.833 to 0.856 to the question; the piece that opens the count element ranks 548th and is
  never a candidate.
- **Measured**: the opening piece of a file is the one given to the model far more often than chance: 23 of 77
  XML passages on the gold questions (6.6 expected), 137 of 309 on the benchmark (63 expected).
- **Measured**: read by hand, 7 of 119 questions have a clearly better piece of the wanted file left out; 2 of
  them are examples. The case itself is not among them, because the gold file does not name the example as a
  wanted source for it.
- **Measured**: choosing among a file's pieces by the question's words, on the index as it is, fails (5 better,
  10 worse, 14 neutral): the text search drops XML tags and sees only comments and descriptions.
- **Believed**: the cut by size without context is the reason. A piece that begins inside an element and does
  not say which element it is in gives the embedding little that differs from its neighbours.
- **Not known**: how much of a piece the embedding model reads. It has a limit on input length, and XML uses many
  tokens per character. If a piece of 1,471 characters is cut by the embedder, its vector describes only its
  beginning. R0 measures this first; it decides the size of a piece.
- **Not known**: how many answers get worse today because the model reads a file's opening where a later piece
  would serve it better. The 7 of 119 count only the cases a reader could be sure of.

## 3. Principles

- **General.** The cut follows the structure of the document, for every XML example of every standard. No rule
  names an element, a file or a question.
- **Measured on a separate index first.** The dev index and the prod index are not rebuilt before the gate is met.
- **Examples only.** Schema files are cut one declaration per piece and are not the problem (measured). Prose
  sources are not touched.
- **No added model call**, and the app's model stays as it is.

## 4. Steps

### R0. A separate index with the new pieces, measured (no change of behaviour)

1. **The cut.** Split an example at element boundaries at any depth: take the largest whole elements that fit the
   size limit; an element larger than the limit is split into its children, and so on down. Each piece begins
   with a line that gives its place in the document, the names of its ancestors from the root (for the case:
   `Opra / ServiceDelivery / … / IndicatorFrame / indicators`). A list of many equal siblings (hundreds of stop
   points) is cut into runs of whole siblings.
2. **Variants to compare**, each its own index and its own run:
   - the path as a line inside the piece's text, or kept beside the text and used only for the embedding and the
     text search;
   - the size limit as today, and one that fits what the embedder reads (from the measurement in §2);
   - with and without the small summary of element names each piece gets today.
3. **Where.** A copy of the dev database under another name in the same database server, with only the example
   pieces rebuilt and embedded there (about 43,000 pieces; **measured** earlier: about 15 pieces a second on the
   laptop, so under an hour per variant). The dev index stays as it is. This needs my go-ahead when it is time,
   because it copies the database and loads the embedder for hours.
4. **What is measured**, against the index as it is, same day:
   - the finer measure of the earlier plan (`pieces` in `locate_answer_sources`) and the same reading by hand:
     the 7 questions, and a random 20 of the pieces that changed;
   - the case, through the API, 3 runs: which piece the model reads, and the answer read against the file. For
     this the example is added to the wanted sources of the late-journeys question in the gold file;
   - how often the given piece is the file's opening, against chance;
   - the gold questions and the benchmark at file level, the CI retrieval benchmark;
   - the example benchmark (`run_example_benchmark`, all questions, 3 runs): the example generator and the example
     answers read these pieces as evidence, so generated answers, first attempts and linked objects must not fall;
   - the 23 answerable and the 25 must-refuse questions, 3 runs;
   - the number of pieces, the size of the index, the time to embed, retrieval time.
5. **What else reads example pieces.** Before building: list every place in the code that reads them (example
   retrieval, excerpts of frames, the elements-to-examples lookup, citations stored with earlier answers, the
   rare-term search, the summary) and say for each whether the new pieces change its result. A stored answer
   that cites a piece which no longer exists must still open.

**Gate R0**, for the variant taken further:

- of the questions with a better piece left out (the 7, and the case), at least 4 now get the better piece, and
  none of the others gets a worse one, read by hand; of the 20 changed pieces read, clearly more better than worse;
- the case: the model reads the piece with the count element in 3 of 3 runs;
- gold and benchmark at file level not lower; every lost question named and explained; the CI retrieval
  benchmark not below its baseline;
- the example benchmark: generated answers, first attempts and linked objects not lower;
- must-refuse: none answered more often; answerable: not fewer answered, new answers read;
- retrieval time not more than 0.3 s above today; the index not more than half again as large.

If no variant meets it: record it and stop. The gate is not changed after the numbers are seen.

### R1. The indexer cuts examples the new way, switched on deliberately

- The new cut goes into the indexer behind a version of the cut that is stored with each file. The nightly
  source refresh on prod must NOT re-cut 405 files on its own the night after a deploy: on prod embedding runs
  at about 3.4 pieces a second (**measured**, 2026-10-27), so 43,000 pieces take three to four hours. The re-cut
  runs as its own command, started by hand through a workflow.
- While it runs, the old pieces of a file stay until its new pieces are embedded, then they are replaced file by
  file, so the search never sees a file without pieces.
- The way back: the same command with the old version.
- **Gate R1**: on dev (the real dev index now, with my go-ahead) the R0 numbers hold; the command can be stopped
  and started again without leaving a file half done; tests for the cut on small documents (nesting, long lists
  of siblings, comments, namespaces, an element larger than the limit).

### R2. Prod

Run the re-cut on prod at a quiet hour, then check: health, the number of pieces, the case and the questions of
the earlier plan through the API, the refused and must-refuse sets. Record the time it took.

## 5. Not planned

- Schema files and prose sources.
- More than one piece of a file for the model, or the neighbours of a piece. The limit of pieces per file and the
  definitions put in front of the passages decide that; they are measured in the retrieval-misses plan.
- Another embedding model.

## 6. Risks

- **Everything that reads example pieces moves at once.** The example generator's evidence is the largest reader.
  That is why the example benchmark is in the gate.
- **More, smaller pieces.** Whole elements are often shorter than 1,200 characters; the index may grow and the
  search may slow. Both are in the gate.
- **The path line costs room.** The model reads at most 1,200 characters of a piece; a long path takes some of
  them. One of the variants keeps the path out of the text for this reason.
- **Gains may be small on the test questions.** 7 of 119 are affected for certain. The over-use of opening pieces
  (twice to three times chance) says the effect is wider, but that is an inference. If R0 shows no more than the
  case fixed, the three to four hours of prod embedding are not worth it, and the plan stops there.
- **Prod time.** A re-cut during the day would slow answers; it runs at night, and the nightly source refresh
  must not overlap with it.

## 7. Order and cost

R0: two to three days, most of it building the separate index and reading by hand. R1: one to two days. R2: one
night on prod.

## 8. Results

(Each step records its numbers here, dated.)

### R0 (2026-11-15, dev copies, 0.97.226): gate not met by any variant, the cut stays unused

**Verdict.** No variant meets the gate. The element cut does what it was meant to do for the case (the model gets a
piece with `LateDatedVehicleJourneyCount` and answers 3 of 3 times with V1 and V3), but every variant loses
questions at file level, and gate 1 cannot be met by an example-only cut at all (below). The cut code and its tests
stay in the repository, unused by default (`recut_examples` only writes to a database named on the command line);
nothing in the app changed. All figures **measured** unless marked.

**Where.** Copies of the dev database on the same server: `napcore_helpdesk_r0base` (unchanged, the baseline) and one
per variant (`…_r0v1`, `…_r0v2`, `…_r0v3`), each with only the 405 XML example files cut again, embedded through the
dev embedder, then `VACUUM FULL` and the vector index rebuilt (the copy's index is built fresh, so the baseline is
measured on a copy as well, not on dev). Before the cut, `recut_examples` checks that today's line cut of each file
in the checkout gives exactly the indexed chunks: 405 of 405 do (TN-ITS from a clone at the indexed commit), so only
the cut changes, not the content. The dev database ended as it began (chunks 61,877, examples 43,193, last update
2026-11-13 12:08:35, checked before, during and after).

**Step 0a: what the embedder reads.** `multilingual-e5-small` with input cut at 256 tokens (the embedder's default,
not overridden on dev). On 1,000 random example chunks: median 495 tokens (p90 548); 99 % are longer than 256; the
embedder reads about 59 % of a piece's XML (median 694 of 1,181 characters, 3.1 characters per token) and reaches the
semantic summary in 10 of 983 chunks. So today's vector of an example piece describes its first half only, and the
summary serves the text search and the model, not the vector.

**Step 0b: what reads example pieces** (read in the code; details in the PR):

- Not changed: the "show me an example" path (whole files from disk and GraphDB links), the example generator's
  excerpts and frames (from files on disk; chunks only tell which files hold an element), the validator, the GraphDB
  examples graph, the concept vectors, the FAQ, the benchmarks (no chunk ids).
- Changed: everything that ranks or counts chunks. More, smaller pieces per file change the elements-to-examples
  lookup (`examples_using_elements` wants all asked tags in one chunk), `shown_example_chunk`, element candidates
  (top 6 by quality), queries that take the first N rows per element (`standard_example`, `condition_example`,
  `asked_from_parts` count chunks per file), the rare-term limit (counted in chunks), the per-file scan of graph
  candidates (8 rows per file), and `compute_chunk_quality` (word-count bands; the summary counts).
- Could break: only the non-model fallback answer (`grounded_generator`, treats a chunk that does not start with `<`
  as prose); with the path line it would show the path line. Not reached on dev (model on).
- Stored answers: citations keep repository, commit, path and chunk id; the question page builds the link from
  repository, commit and path and never loads the chunk. An answer citing a piece that no longer exists still opens
  with a working link (**measured** by reading `QuestionEventDetailView` and the frontend; not clicked).
- The path in `heading` instead of the text: the heading is embedded and ranked, but not shown to the model, the
  text-search filter is on the text only, and `_named_example_candidates` reads a non-empty example heading as a list
  of Turtle types. So "the path beside the text" is not a cut-only variant; I did not build it.

**Step 0c: baseline** (`napcore_helpdesk_r0base`, same day): table below. **Step 0d**: the OpRa example is now a
wanted source of the late-journeys question (a11) in `answer-source-questions.yaml` (own commit); with it a11 is found
at file level on the baseline (prompt place 5), and the piece given is the file's opening.

**Step 1: the cut** (`services/xml_example_cut.py`): the largest whole elements that fit the limit; a larger element
is cut into its children, recursively; runs of siblings are cut into runs of whole siblings; comments and text go
with the element after them; closing tags stay with the piece they close; each piece gets
`Element path: Opra / ServiceDelivery / … / indicators` as its first line (local names, from the root; none for the
opening piece). Put together, the pieces give back every file exactly: tested on all 405 indexed files and on every
`.xml` under the four checkouts' example folders, at 600 and 1,200 characters. At 1,200: 57,165 pieces (today
43,193), median 951 characters; 1.4 % of pieces start inside text or a comment (long comments and descriptions,
which are cut at lines), against 92 % of today's pieces cut inside an element. Unit tests: nesting, long sibling
lists, comments, markup inside comments, CDATA and attributes, namespaces and prefixes, an element larger than the
limit, mixed content, closing tags, a file smaller than a piece, a document that is not well formed (keeps the line
cut).

**Step 2: variants**, chosen and written down before any variant result:

- V1: path line in the text, limit 1,200, summary kept (the plan's proposal);
- V2: as V1 without the summary (the embedder never reaches it at 1,200; it matters only for the text search, the
  quality score and the model);
- V3: as V1 with a limit of 600 characters, which fits what the embedder reads. Known before building: 109,727
  pieces, twice the rows, so it fails gate 6 by construction; built to learn whether fitting the embedder helps.
- Not built: the path beside the text (above); the other combinations.

**Gate 1 cannot be met by this plan's cut.** Of the 7 questions with a better piece left out plus the case, only
three are about an example (a09, q059, the case); the others are schema declarations (q057, q072, q149), a regulation
annex (b14) and a README (a15), which this cut does not touch. "At least 4 of 8" is out of reach by construction. I
noticed this after the baseline, before reading any variant; I kept the gate as written.

**Results** (2 runs for the locate measures, 3 for the API and the example benchmark; "a / b" = run 1 / run 2):

| Gate | base | V1 (1,200, summary) | V2 (1,200, no summary) | V3 (600, summary) |
|---|---|---|---|---|
| 1. better piece, of 8 (read by hand) | – | 2 better (case, a09), 1 worse (q059), 5 untouched | not read (fails 2, 3) | not read (fails 3, 6) |
| 1. 20 changed pieces (gold run 1, random) | – | 6 better, 1 worse, 13 neutral | – | – |
| 2. case, piece with the count element / answered | 0 of 3 / 0 of 3 | 3 of 3 / 3 of 3 (from two other OpRa examples) | 0 of 3 / 1 of 3 | 3 of 3 / 3 of 3 (another OpRa example) |
| 3. gold found (57) | 34 / 34 | 32 / 32 | 32 / 32 | 31 / 31 |
| 3. benchmark found (141) | 124 / 124 | 122 / 122 | 121 / 122 | 121 / 121 |
| 3. finer measure: best piece given | gold 26 of 30, bench 83 of 90 | 26 of 28, 80 of 88 | 24 of 28, 80 of 90 | 25 of 27, 78 of 88 |
| 3. retrieval benchmark, hit@10 / MRR@10 (app index, no GraphDB) | 0.893 / 0.564 | 0.893 / 0.604 | 0.873 / 0.562 | 0.839 / 0.583 |
| 4. example benchmark: generated / first attempt / unlinked (141 runs) | 132 / 99 / 1 | 132 / 94 / 1 | 132 / 100 / 1 | 131 / 90 / 0 |
| 5. answerable (23 × 3): answered runs | 40 | 40 | 39 | 46 |
| 5. must-refuse (25 × 3): answered runs | 4 (m19 3, m24 1) | 5 (m19 3, m24 2) | 4 (m13 1, m19 2, m24 1) | 2 (m19 2) |
| 6. retrieval median, quiet pass (gold / bench) | 1.37 / 1.05 s | 1.37 / 0.63 s | 0.73 / 0.66 s | 0.78 / 0.69 s |
| 6. rows / vector index / row data without the hash vector | 61,877 / 484 MB / 457 MB | 75,849 (1.23×) / 593 MB / 553 MB (1.21×) | 75,849 / 593 MB / 540 MB | 128,411 (2.08×) / 1,004 MB / 898 MB (1.97×) |
| embedding time on the laptop | – | 5,301 s (10.8 pieces/s, measurements running beside it) | 5,507 s | 9,701 s (11.3/s) |
| opening piece given (multi-chunk files among passages, gold / bench) | 62 of 232 / 190 of 626 | 61 of 230 / 115 of 632 | 53 of 220 / 115 of 615 | 56 of 230 / 80 of 635 |

The quiet pass ran one copy after the other with nothing else on the stack, the baseline first; the baseline may be slower because it ran on cold caches (**believed**). No variant is slower than the baseline, so gate 6's time part holds for all; its size part fails for V3.

Gate per variant: V1 fails 1, 3, 4 (first attempts 99 → 94) and 5 (m24 one run more); V2 fails 1, 2, 3 and 5 (m13);
V3 fails 1, 3, 4 (90 first attempts, one generated answer fewer) and 6. The API and example-benchmark differences of
one run are within the spread three runs can show (**believed**); the file-level losses are stable over both runs.

**Lost questions at file level** (V1, the same in both runs; V2 and V3 share a19, q013 and q109 and lose others of the same kind: V2 a10, b31, q124, q137, q140, q144; V3 a11, b29, q016, q017, q019):

- a11 (the case): the two other OpRa examples with `LateDatedVehicleJourneyCount` now take the example places; the
  wanted file drops out at the view. The model still gets the count element (above), so the loss is of the file, not
  of the answer.
- a19 (DATEX and SIRI): the wanted SIRI situation example drops below other SIRI example pieces and a DATEX II page.
- q013 (OpRa reliability indicators): six OpRa example pieces push both indicator schemas out of the six places.
- q109, q137 (roadwork warnings): the road situation example is replaced by pieces of the other situation examples;
  in q137 its piece falls out of the vector pool (rank 6 → 70).
- q143 (how SIRI uses NeTEx): the README is pushed out by SIRI example pieces.
- Gained: q015 (the RequestLateDatedVehicleJourneys example now among the passages), q063 (the frequency timetable
  example is first by vector).

The pattern: whole, labelled example pieces are better matches for many questions, so more of them win the six
places and push out the schema declarations and READMEs the gold and benchmark files name. That is a change of what
the model reads, not only of which piece of a file.

**The case through the API** (V1, run 1, quoted in short): "Late journeys are counted in the
`LateDatedVehicleJourneyCount` element, which sits inside `indicators` in an `IndicatorFrame` … Each count is broken
down into `intervals`, where each `DurationInterval` gives a delay range using `StartOfInterval`, `EndOfInterval`,
`StartIncluded` and `EndIncluded` (for example delays of PT10M up to PT20M), together with `NumberOfOccurrences` and
`PercentageOfOccurrences` [E5] [E6]." Read against the two pieces (`DelayedAndCancelledJourneysWithEvents.xml`,
`ResponseLateDatedVehicleJourneys.xml`): every element and value named is in them; the path line gave the answer the
element's place. It still opens with "the evidence does not give a direct data model … as a single concept".

**Hand reading** (V1):

- The 8: a11 better (above); a09 better (the simple bus timetable example's header comment now among the passages,
  "This example shows the encoding of a simple bus timetable"); q059 worse (the `RhythmicalJourneyGroup` piece of
  `Netex_06.2` is gone; `TemplateServiceJourney` and frequency pieces of other files instead); q057, q072, q149, b14,
  a15 unchanged by construction (q057's example pieces now begin at `<CoupledJourney>`, cleaner, but the better piece
  was the schema declaration).
- 20 random changed example passages (gold run 1): better 6 (two `<?xml?>`-only openings no longer given, the GBFS
  `Parking` piece for "How are parkings defined", the TfL `SalesOfferPackage` with its purchase description for
  "Where can a passenger buy tickets", the SIRI-VM header comment for "What is SIRI used for", an irrelevant stop
  list no longer given for "Kaj so to metapodatki?"); worse 1 (b29 loses the `Line` with `OperatorRef` pieces of the
  UK rail example); neutral 13 (the same opening on both sides, or one irrelevant piece for another). Two of the new
  pieces start in the middle of a comment or description (the line fallback of the cut).

**Answers that changed** (read): k11 (the case, above); k08 "Kaj so to metapodatki?" answered in all three V1 runs
from GML metadata schema pieces, grounded in them but beside the question's NAP metadata sense; e06 refused in V1
with the same four citations it answered from on the baseline (the model's verdict, not retrieval); m24 (OpRa and
GTFS-RT) answered in 2 of 3 V1 runs, 1 of 3 on the baseline, both times saying GTFS-RT is not in the evidence.

**What the CI benchmark can see.** Nothing: CI builds its own index with `build_source_index`, which keeps the line
cut, so the CI retrieval benchmark cannot see this change. The row "retrieval benchmark" above is the same command on
the dev copies (semantic vectors, no GraphDB), compared with the baseline copy, not with `ci-baseline.json`.

**Cost at prod's speed.** 57,165 pieces (V1) at 3.4 pieces a second (prod, 2026-10-27) is about 4.7 hours; V3's
109,727 about 9 hours (**believed**, by division).

**Not tried.** The path beside the text; a limit between 600 and 1,200; a cut whose limit is counted in tokens; a cap
on example pieces among the six places, which is what the losses point to. Any of these is a new variant and needs its
own full run.

**Believed, not verified.** That the file-level losses come from example pieces crowding schemas and READMEs (read on
the lost questions, not counted over all); that the one-run differences in the API sets are spread; that V2 differs
from V1 only by the summary (66 one-piece files kept their old chunk with the summary in V2, because the skip test of
`recut_examples` compared chunk ids; fixed in the command afterwards).

Raw outputs are outside the repository. To repeat: copy the dev database, `recut_examples --database <copy>
--checkout <repo>=<path> … [--max-chars N] [--no-summary]`, rebuild the vector index, then `locate_answer_sources`,
`run_retrieval_benchmark`, `run_example_benchmark --runs 3` and the API sets against the copy (`POSTGRES_DB`).

### Audit: is every source kind prepared for semantic search (2026-11-15, dev index, no change)

Read on a copy of the dev database made the same day (same chunk count, example count and last update time as dev,
checked before and after). Kinds are taken from the data (`doc_type`, `chunk_type`, file type, source), not from a
list. Samples: tokens and the cut checks on 300 random chunks per kind (all chunks where a kind has fewer); language
on 100 of them; similarity on 15 random files of 3 or more chunks per kind, 8 chunks each, against random pairs of
chunks of different files of the same kind. Tokens are counted with the embedder's own tokenizer on exactly the text
the indexer sends (`passage: ` + source path + heading + text).

**What the embedder reads (measured):** `intfloat/multilingual-e5-small`, 384 dimensions, input cut at 256 tokens
(`EMBEDDER_MAX_TOKENS`, default 256, not set on dev). Every indexed chunk is embedded as `passage: ` + source path +
heading + text (`passage_text`, used by every indexer: repositories, EU legislation, NAPCORE, DATEX II, INSPIRE);
questions as `query: ` + question. That is the convention the model expects; the code follows it everywhere I found
(one exception without consequence: the seed chunks of an empty index are embedded without source path). The model
is shown the text and the source path, **not the heading**: what is embedded and what the model reads differ for
every kind with a heading.

| kind | chunks / files | 1. vector | 2. tokens median / p90 / max; share over 256 | 3. cut; chunks cut inside a unit | 4. context in the embedded text | 5. similarity within a file vs across files (gap) | 6. text embedded; language | 7. near-empty / licence-only / exact duplicates |
|---|---|---|---|---|---|---|---|---|
| XML examples | 43,193 / 405 | semantic, all | 497 / 550 / 955; **99 %** | by size (1,200 characters, lines); **92 %** cut inside an element (tags not balanced, 276 of 300) | source path only; no heading, no place in the document | 0.945 vs 0.897 (0.048) | text + semantic summary (the summary is never reached: 10 of 983); English comments 58 %, German 7 %, 30 % too little prose to tell | 101 / 85 / 148 |
| XSD schema declarations | 10,579 / 608 | semantic, all | 116 / 187 / 1,050; 5 % | one declaration per chunk (by construction) | declaration name as heading (embedded, not shown) | 0.945 vs 0.886 (0.059) | summary text of the declaration; English | 9 / 8 / 130 |
| EU legislation (EUR-Lex) | 735 / 191 | semantic, all | 197 / 382 / 665; 37 % | articles, annexes and recitals, paragraphs grouped up to 1,500 characters, long ones at sentence ends; 18 % end mid-sentence (heuristic) | heading (e.g. "Annex", "Article 4"), embedded, not shown | 0.939 vs 0.871 (0.068) | text; English | 0 / 0 / 0 |
| NAPCORE site pages | 2,979 / 119 | semantic, all | 402 / 443 / 546; **94 %** | by page section, up to 1,500 characters (believed, from `napcore_site.py`); 72 % end mid-sentence (heuristic) | page title as heading | 0.940 vs 0.883 (0.057) | text; English | 0 / 1 / 0; menu-like lines in 8 of 300 |
| DATEX II docs pages | 1,236 / 197 | semantic, all | 272 / 424 / 597; 58 % | by section, up to 1,500 characters; 49 % end mid-sentence (heuristic) | section heading | 0.933 vs 0.890 (0.043) | text; English | 0 / 0 / **74** |
| DATEX II model classes | 1,240 / 1,159 | semantic, all | 163 / 346 / 543; 21 % | one class per chunk (a few split) | "DATEX II class X (namespace Y)" as heading | 0.947 vs 0.893 (0.054) | text; English | 0 / 4 / 0 |
| INSPIRE (regulation and technical guidelines) | 594 / 468 | semantic, all | 252 / 445 / 651; 49 % | by section, up to 1,500 characters; 31 % end mid-sentence (heuristic) | section path as heading ("Data content › Basic notions › …") | 0.934 vs 0.890 (0.044) | text; English | 0 / 1 / 0; menu-like 37 of 300 |
| mobilityDCAT-AP guide (sections) | 216 / 61 | semantic, all | 243 / 339 / 468; 44 % | by heading, up to 1,200; 46 % end mid-sentence (heuristic) | section heading | 0.934 vs 0.890 (0.044) | text; English | 0 / 9 / 0 |
| TN-ITS guide/frame/object (mostly Turtle codelists and ontology) | 905 / 36 | semantic, all | 266 / 449 / 591; 53 % | one Turtle statement per chunk (by construction; the sentence heuristic does not apply) | subject (e.g. `tnits:VehicleType`) as heading | 0.959 vs 0.917 (0.042) | Turtle text; English labels | 5 / 1 / 1 |
| README | 61 / 7 | semantic, all | 115 / 348 / 437; 18 % | by heading; 61 % start or end mid-sentence | section heading | 0.854 vs 0.849 (**0.005**) | text; English | **8** / 3 / 3 |
| examples, not XML: NeTEx `.txt` | 123 / 13 | semantic, all | 542 / 561 / 593; **91 %** | by size, 1,200 with 200 overlap; 81 % start or end mid-sentence | none | 0.947 (one file only) | text; English | 0 / 0 / 0 |
| examples, not XML: mobilityDCAT-AP `.ttl` | 16 / 2 | semantic, all | 263 / 499 / 512; 50 % | one Turtle statement per chunk | subject as heading | 0.932 vs 0.934 (none) | Turtle | 1 / 1 / 0 |
| Ontology classes (concept vectors, not chunks) | 3,104 classes | semantic, all | 36 / 69 / 137; 0 % | one class per vector | name, other names, definition | – | label + definition; English | 14 without definition |

Not in the index (**measured**: no chunk rows): the Transmodel HTML export (linked from definitions, not searched);
ontology definitions are given to the model from GraphDB, found by label words and by the concept vectors above.
FAQ entries (3) are matched by word stems, not by vectors (**measured** by reading `faq_matcher.py`; its docstring
says "embedding similarity", the code does not use one). Hash vectors: every kind also keeps a hash vector in
`alternate_vector` for rollback (5,073 example and 3,032 XSD chunks have none since their last re-index); retrieval
does not use it. No source is searched by words only: every chunk has a semantic vector (**measured**).

How to read the columns: 1–2, 4 and 6–7 are **measured** on the full kind or the sample named. "Cut inside a unit" for
prose is a heuristic (first letter lower case, last character not a sentence end); it over-counts chunks that end in a
list or a table, so read it as an upper bound (**believed**). Column 5 is **measured** on the sample; the gap is the
only meaningful part: this model puts any two passages of one kind at 0.87–0.93, so 0.83–0.86 within a file in the
case was not unusual.

Per kind:

- **XML examples: not fit.** 99 % are longer than the embedder reads (it sees about 690 of 1,180 characters of the
  piece), 92 % are cut inside an element, and nothing says where a piece sits. This is the R0 subject.
- **XSD schema declarations: fit.** One declaration per chunk, 5 % over the limit (the longest enumerations).
- **EU legislation: fit, with a caveat.** Units by article and annex; 37 % are longer than the embedder reads, so
  the end of a long article is not in its vector.
- **NAPCORE site: not fit as it is.** 94 % of the chunks are longer than the embedder reads: the vector describes the
  first half of each 1,500-character section.
- **DATEX II docs pages: fit with caveats.** 58 % too long; 74 exact duplicates (the same section on several pages).
- **DATEX II model classes: fit.** One class per chunk; 21 % too long.
- **INSPIRE: fit with caveats.** 49 % too long; some navigation text.
- **mobilityDCAT-AP guide: fit with caveats.** 44 % too long.
- **TN-ITS Turtle: fit.** One statement per chunk; long codelist statements are cut by the embedder (53 %), which
  matters little for codelists.
- **README: not fit as it is.** Chunks of one README are no closer to each other than to other READMEs (gap 0.005),
  8 of 61 are near-empty headings; the kind is small (61 chunks) but it is what overview questions need.
- **NeTEx `.txt` examples: not fit.** Cut by size with overlap, 91 % too long, 81 % start or end mid-sentence.
- **mobilityDCAT-AP `.ttl` examples: fit** (small).
- **Ontology classes: fit.** Short texts, well within the limit.

Common to all kinds (**measured**): the 1,500-character prose cut and the 1,200-character example cut are both longer
than the 256 tokens the embedder reads (about 690 characters of XML, measured; about 900–1,000 of English prose, believed from 3.8 characters per token in the legislation sample); the heading is
embedded but not shown to the model. **Believed**: a size limit per kind in tokens, not characters, would fix most of
column 2 without touching the units; that is a plan of its own, measured as R0 is.
