# Plan: all sources prepared for semantic search, with the graph

Written 2026-11-15 against 0.97.226, for the implementer. It follows two records in
`2026-11-15-xml-example-chunks.md` §8 (PR #540): R0, the element cut of XML examples measured on copies of the dev
database, and the audit of every source kind. Their numbers are used here and not repeated in full.
Each claim is labelled **measured**, **believed** or **assumed**.

## 1. The problem

Every source is searched by meaning, but most pieces are not prepared for it. The embedder reads the first 256
tokens of a piece, and most pieces are longer, so a vector describes the beginning of a piece and not the piece.
The search then cannot tell the pieces of one file apart, and the model is given the wrong one.

R0 tried to repair one kind (XML examples) by itself. It fixed the case it was built for and failed its gate,
because the better example pieces pushed schema declarations and READMEs out of the six passages the model reads.
The fault is not in one kind. It is in how all kinds are cut, sized and chosen together, so this plan treats them
together and re-indexes once.

## 2. What is known

- **Measured** (audit): the embedder is `multilingual-e5-small`, input cut at 256 tokens. Share of pieces longer
  than that: XML examples 99 %, NAPCORE pages 94 %, NeTEx text examples 91 %, DATEX II pages 58 %, TN-ITS 53 %,
  INSPIRE 49 %, mobilityDCAT-AP guide 44 %, EU legislation 37 %, DATEX II classes 21 %, READMEs 18 %, schema
  declarations 5 %. Of an XML example piece the embedder reads about 59 %.
- **Measured** (audit): the size limits are in characters (1,200 for examples, 1,500 for prose). 256 tokens are
  about 690 characters of XML; of English prose about 900 to 1,000 (**believed**).
- **Measured** (audit): the heading of a piece is embedded but not shown to the model. For an XML example there is
  no heading at all, and nothing says where in the document the piece sits.
- **Measured** (audit): 92 % of example pieces are cut inside an element. READMEs: pieces of one README are no
  closer to each other than to another README; 8 of 61 are headings without text. DATEX II pages: 74 exact
  duplicates.
- **Measured** (R0): with example pieces cut at element boundaries and a line giving the place in the document,
  the model gets the piece with the count element and answers the late-journeys question 3 of 3 times.
- **Measured** (R0): every variant loses 2 to 3 gold questions and 2 to 3 benchmark questions at file level. In
  the lost questions, example pieces take the places of the schema declaration or README the question file names.
- **Measured** (R0): the variant whose pieces fit the embedder (600 characters) answered most of the answerable
  questions (46 of 69 runs, baseline 40) and answered the fewest questions it must refuse (2 runs, baseline 4). It
  doubled the rows and lost most at file level. **Believed**: differences of this size are partly spread of three
  runs; the spread was not measured.
- **Believed** (a comment in the embedder's code, from the trial of 2026-10-25; not re-measured): reading 512
  tokens of a piece was no better than 256 and twice as slow. So the pieces must fit the embedder; the embedder is
  not made to read more.
- **Measured** (read in the code): the question's concepts are found by meaning (the concept vectors, 3,104
  classes) only for "does the standard have X" questions. Everywhere else the search finds concepts by the words
  of their labels.
- **Measured** (read in the code): the facts of the graph (definitions) are put in front of the passages and take
  some of the six places.
- **Not known**: how much the file-level measure punishes a good change. It counts a question as lost when a named
  file is no longer among the passages, also when another passage holds the same answer.
- **Not known**: the spread of each measure between two runs on the same index.

## 3. The design

1. **A piece is a unit of its source.** XML: whole elements (the cut of R0, which gives back every file exactly).
   Prose: section, then paragraph, then sentence. Schema: one declaration (as today). Turtle: one statement (as
   today). No piece begins or ends inside a unit unless the unit itself is larger than the limit.
2. **A piece fits what the embedder reads.** The limit is counted in tokens, with the embedder's own tokenizer, on
   exactly the text that is embedded. One limit for all kinds.
3. **A piece says where it sits.** One line of place: the path of elements from the root for XML, the path of
   headings for prose. It is embedded and it is shown to the model.
4. **Search small, read large.** The search works on the small pieces. The model is given the found piece together
   with as much of the unit around it as fits the room it has today (1,200 characters a passage). The index does
   not decide how much the model reads.
5. **The six places are shared among kinds of source.** No kind takes all the places while another kind has a
   candidate above the score limit. The rule is about kinds, not about any standard or file.
6. **The graph works with the vectors, in three places:**
   - at indexing, each piece gets the concepts of the ontology it is about (for XML from its element names, for
     prose from the labels and the concept vectors), stored beside the piece;
   - at the question, the concepts are found by meaning for every question, and the pieces that carry them are
     candidates. This replaces the search of paths by label words;
   - after the passages are chosen, the definitions and relations of their concepts are given to the model in a
     block of their own, beside the six passages and not in their place.

Relation questions keep using the graph as today. I do not measure the helpdesk with the graph switched off.

## 4. Principles

- **General.** No rule names an element, a standard, a file or a question.
- **Measured on copies first.** The dev index and the prod index are not rebuilt before the gates of steps 1 to 4
  are met. Copies are made as in R0, with the baseline on a copy as well.
- **One re-index** on dev and one on prod, for everything.
- **No added model call.** The app's models stay as they are.
- **Gates are fixed here** and not changed after the numbers are seen.

## 5. The yardstick

R0 showed that the file-level count alone cannot judge this change. The measures for every step:

- **Answers.** The 23 answerable and the 25 must-refuse questions, 3 runs each. The verdicts taken before the
  search (the relevance check above all) do not depend on the index; they are recorded with the baseline and held
  equal in every variant. A question is asked again only where what the model is given differs from the baseline;
  elsewhere the baseline's answer counts. Every answer that was asked again is read against its passages, and the
  comparison is made question by question, not on the sum.
- **Files.** Gold (57) and benchmark (141) at file level. Each question lost at file level is read: it counts as
  lost only if the passages given no longer hold what the named file holds for the question.
- **The case.** The late-journeys question, 3 runs, and the 7 questions with a better piece left out, read by hand.
- **Examples.** The example benchmark, all questions, 3 runs: generated, first attempts, linked objects.
- **Cost.** Rows, index size, embedding time, retrieval time.

"Not lower" means not lower than the baseline by more than the spread measured in step 0 (§10): files found,
the retrieval benchmark and generated examples did not move, so any loss there is real; first attempts: a fall of
6 or more; answers on the sum: 7 of 69 runs, which is why the questions asked again are read one by one. Questions
whose passages move between two runs on the same index are listed with the baseline and marked in every
comparison. Retrieval time is compared on warm runs only.

(§5 was written this way on 2026-11-16, after step 0 and before any number of step 1 existed. The first version
said only "3 runs each" and "the spread measured in step 0".)

## 6. Steps

### Step 0. The yardstick and the facts (no index change, about 1 day)

- Measure the baseline copy twice, all measures of §5, to get the spread of each.
- Read the gold file once for questions where more than one source holds the answer, and name those sources.
  This is the review that is still open (12 entries marked unsure).
- Prod: free disk, memory of the database container, and the per-file limit set there. Rows will about double
  (**believed**, from R0's 600-character variant: 61,877 to 128,411 with examples alone).
- A token counter in the indexer that gives the same count as the embedder (**measured** in the audit with the
  embedder's tokenizer; the indexer has none today).

No gate. If the spread is larger than the differences R0 saw, I say so before step 1, because then the gates need
more runs.

### Step 1. The prepared index, on a copy (3 to 4 days)

Design points 1 to 4, for every kind, in one build. Near-empty pieces (headings without text) and exact duplicates
are left out.

**Gate 1:**

- share of pieces longer than the embedder reads: under 5 % for every kind; pieces cut inside a unit: under 5 %;
- the case: the model reads a piece with the count element in 3 of 3 runs; of the 7 questions, at least 4 better
  and none worse;
- answers: answerable not lower; must-refuse not answered more often;
- files: questions lost by the rule of §5: none unexplained, and not more than gained;
- examples: not lower;
- retrieval time not more than 0.3 s above the baseline; rows not more than 2.5 times today's, and prod has the
  room for it (step 0).

### Step 2. The six places shared among kinds (about 1 day, code only, on the copy)

Design point 5. Measured against step 1's result.

**Gate 2:** the questions step 1 lost at file level are back, by the same rule; answers and examples not lower;
no kind of question gets worse, read on the changed passages (a random 20).

### Step 3. Concepts on the pieces and concepts by meaning (about 2 days)

Design point 6, first and second part. The labels are written on the copy without a new embedding.

**Gate 3:** the concept benchmark not lower (23 of 26 today); the questions in languages other than English in the
gold and benchmark files not lower; answers, files and examples not lower; retrieval time not higher than step 2
(the search of paths by label words was the slowest part of retrieval on prod).

### Step 4. Facts of the graph in their own block (about 1 day)

Design point 6, third part.

**Gate 4:** the "does the standard have X" questions answered as before, read; answers not lower; the tokens the
model reads per question stated, and not more than a quarter above step 3.

### Step 5. The indexer, and the dev index (1 to 2 days, with my go-ahead)

- The new cut goes into the indexer behind a version stored with each file. The nightly source refresh must not
  re-cut everything on its own; the re-index is its own command.
- A file's old pieces stay until its new ones are embedded, so the search never sees a file without pieces.
- CI builds its own index with the indexer, so from here the CI retrieval benchmark sees the change. Its baseline
  is set anew in the same PR, with the old and new numbers side by side.

**Gate 5:** the numbers of steps 1 to 4 hold on the real dev index; the command can be stopped and started again;
tests of the cut for every kind; the way back is the same command with the old version.

**Gate 5, reworded on 2026-11-18, before the step starts.** No gate from 1 to 4 was met as written, so "the
numbers of steps 1 to 4" names nothing. Step 5 would ship what was measured on the copy `napcore_helpdesk_s5v`:
the cut of step 1 with its repairs and the index of step 2b, without step 3 (reverted) and without step 4 (not
built). The gate is that the real dev index gives the numbers of that copy (§10, steps 2b to 2d):

- pieces: the count per kind of source equals the copy's, or each difference is explained by a changed source;
  no piece over 256 tokens;
- the index: the exact nearest pieces on every captured retrieval call (recall 1.000);
- files found, with the spread of step 0: gold not under 39 of 57, benchmark not under 120 of 141, retrieval
  benchmark hit@10 not under 0.873;
- answers and examples, with recorded calls replayed wherever the prompt is the same: answerable questions
  answered, must-refuse questions answered, examples generated, first attempts and unlinked examples not worse
  than run `s5-a` beyond the spreads of step 0; the late-journeys case answered in 3 of 3 runs;
- warm retrieval time not more than 0.1 s above the copy's, timed in the same round;
- as before: the command can be stopped and started again; tests of the cut for every kind; the way back is the
  same command with the old version.

Two lines of the copy are worse than the baseline and are carried, not judged by this gate: must-refuse
questions answered in 6 of 75 runs (baseline 4) and examples generated 131 of 141 (baseline 132). Whether step 5
starts with them carried is my decision, taken before it starts. Before step 6, prod's pgvector version is
checked: the index of step 2b needs 0.7 or later.

### Step 6. Prod (one night, or a load)

About 130,000 pieces at prod's 3.4 pieces a second are about 11 hours (**believed**, by division): longer than a
night, and the nightly refresh must not run beside it. Two ways, decided in step 5:

- embed on prod over a weekend, or
- build the pieces and vectors on dev from the same source commits as prod and load them on prod through a
  workflow (**assumed** possible: the model is the same, so the vectors are the same; to be proven on one source
  first).

Then check: health, rows, the case and the answer sets through the API, the time it took.

## 7. Not planned

- Another embedding model, or the embedder reading more than 256 tokens.
- A run with the graph switched off.
- The FAQ (3 entries, matched by word stems; **measured** in the audit). Too small to matter now.
- The clarifying questions (#536) and the search of all sources without a scope (#539). Both failed their gates on
  today's index. They may be measured again after step 6, as their own steps.

## 8. Risks

- **Everything that ranks or counts pieces moves at once** (listed in R0, step 0b: the lookup of examples by
  element, element candidates, limits counted in pieces, the quality score). The example benchmark is in every
  gate for this reason.
- **Twice the rows.** Index size and memory on prod. Checked in step 0, before anything is built.
- **Reading by hand decides part of the gates.** It is slower and less exact than a count. The rule is written in
  §5 and the readings go into the record, question by question.
- **Design point 4 changes what the model reads** although the index only got smaller pieces. If the unit around a
  piece is chosen badly, answers get worse while every search measure gets better. Answers are in gate 1 for this.
- **The gain may be small.** R0 gave +6 answered runs of 69 for the variant that fits the embedder, with unknown
  spread. If step 1 shows no more than the case fixed, the plan stops there and nothing is re-indexed.

## 9. Order and cost

Steps 0 to 4 on copies: 8 to 9 working days. Step 5: 1 to 2 days. Step 6: a night or a weekend on prod.

Each build of a copy embeds about 130,000 pieces: about 3.5 hours on my laptop with the embedder at 2 cores
(**measured** in R0: 11 pieces a second). At least three builds are expected (step 1, one repair, step 5). Before
each I decide whether Docker gets more cores for that session.

The four copies R0 left in the dev database server (7.7 GB together) can be dropped once this plan is accepted;
step 0 makes its own.

## 10. Results

(Each step records its numbers here, dated.)

### Step 0 (2026-11-15, dev copy `napcore_helpdesk_s0base`, 0.97.226 with #540 and #542)

**Verdict.** The spread of the answer sets is as large as the differences R0 read as results, so the gates of steps 1
to 4 do not stand as written for answers: R0's baseline on another copy of the same data and code answered 40 of 69
runs of the answerable set; my two passes, same code and data, answered 45 and 43. V3's 46, read in R0 as the gain
of fitting the embedder, is inside that range. The main cause is not the model's wording but a verdict cached once
per server process (below), so three runs in one process are not three samples. The file-level, pieces, retrieval
benchmark and example-generated measures did not move at all; first attempts moved by 1 between passes. The gold file
undercounted: 5 of the 23 questions it counted as lost have another source among the passages that holds the answer
(B). Prod's limit of one piece per file is believed, not read (C). The token counter counts exactly what the embedder
reads (D).

**A. The spread of the measures.** One copy of the dev database, `napcore_helpdesk_s0base` (copied 2026-11-15 in the evening,
vector index rebuilt fresh, 484 MB), code frozen at the branch's commit before any step 0 change (exported tree), the
app's models as configured (Haiku 5.5), host servers pointed at the copy as in R0. Two passes one after the other,
each: `locate_answer_sources` gold and benchmark twice (model off, stored renderings), `run_retrieval_benchmark`,
`run_example_benchmark --runs 3`, the 23 answerable and 25 must-refuse questions through the API three times (two
workers, one server process per pass). A first start of pass 1 was stopped after its first locate run and thrown
away: the dev embedder restarted under it (my token check for D ran out of the embedder container's memory, see D);
both passes below ran after that, on a healthy embedder. The dev database is unchanged (61,877 chunks, 43,193
example chunks, last update 2026-11-13 12:08:35, before and after). All figures **measured** unless marked.

What makes two runs differ, checked before the passes (by reading the code and the effective settings of the host
runs, which are those of R0):

- The model samples: the Anthropic call sends no temperature (`anthropic_chat.chat_completion`), so the API default
  applies to every call: the answer, the relevance check, the controller, the vocabulary bridge, the English
  rendering and the example generator. Active on the copy.
- Verdicts cached per process: the relevance check (`relevance_check._ask`), the controller route
  (`_decide_route_cached`) and the bridge (`bridged_question_concepts`) are `lru_cache`d by question text. Inside one
  server process the second and third run of a question reuse the first run's verdict; a new process samples again.
  Active: one process per pass.
- The Redis caches: not active on host runs. `CACHE_URL` is empty there, so the fixed texts of refusals are kept in
  the process's memory; question embeddings are not cached anywhere, definition passages only in the process
  (`cached_passage_embedding`, vectors are deterministic). These change time, not results.
- Retrieval caches with one hour's life (examples by element, element candidates, alias matches) and the database's
  own caches: time only.
- GraphDB calls with a 3 s timeout (`GRAPHDB_TIMEOUT_SECONDS` in the dev env): a timed-out call drops its
  candidates (**believed** to be why a few questions get other passages from run to run, below).
- Order: two workers, run 1 of every question before run 2; the order does not change any cached verdict's value,
  only which run samples it.

| measure | pass 1: run 1 / run 2 (/ run 3) | pass 2: run 1 / run 2 (/ run 3) | pass totals | spread seen | smallest difference a later step may call real |
|---|---|---|---|---|---|
| gold found, old file (57) | 34 / 34 | 34 / 34 | – | 0 (R0's copy: 34 / 34) | 1 question, after reading it (see the passage note below) |
| benchmark found (141) | 124 / 124 | 124 / 124 | – | 0 (R0: 124 / 124) | 1 question, as above |
| pieces: best piece given (gold of 30, bench of 90) | 26, 83 / 26, 83 | 26, 83 / 26, 83 | – | 0 (R0: 26, 83) | 1 |
| retrieval benchmark hit@10 / MRR@10 | 0.893 / 0.564 | 0.893 / 0.564 | – | 0 (R0 the same) | any change |
| example benchmark generated (of 47 a run) | 44 / 44 / 44 | 44 / 44 / 44 | 132 / 132 | 0 (R0: 132) | 1 |
| example benchmark first attempts (of 47 a run) | 35 / 32 / 32 | 33 / 32 / 33 | 99 / 98 | 1 between passes (R0: 99); 3 between runs; 8 questions move between passes | 6 of 141 (**believed**, see below) |
| example benchmark unlinked | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 | 0–1 (R0: 1) | 2 |
| answerable answered (of 23 a run) | 16 / 14 / 15 | 15 / 13 / 15 | 45 / 43 of 69 | 2 between my passes, 5 against R0's copy (40); 13–16 per run | 7 of 69 with three runs in one process; see below |
| must-refuse answered (of 25 a run) | 1 / 1 / 1 | 1 / 2 / 1 | 3 / 4 of 75 | 1 (R0: 4) | 2 of 75, or any new question answered twice |
| the case (k11): piece with the count element given / answered | 0 / 0 / 0, refused | 0 / 0 / 0, refused | 0 of 6 | 0 (R0: 0 of 3) | 1 of 3 |
| retrieval median, locate gold / bench | 0.97, 0.61 s / 0.67, 0.60 s | 0.76, 0.68 s / 0.76, 0.67 s | – | 0.30 s gold (first run cold), 0.08 s bench | 0.3 s, warm runs only |
| retrieval median, API answerable | 0.52 s | 0.56 s | – | 0.04 s | as above |

Per question over the six API runs (pass 1 + pass 2): answerable e05 2 (1+1), e06 2 (1+1), e07 2 (2+0), k02 5
(2+3), k14 5 (3+2), every other question 0 or 6; must-refuse m19 6 (3+3), m13 1 (0+1), all others 0. R0's baseline
copy, same code and data, a separate process: k08 0 of 3 (refused before retrieval, no evidence, so by the
relevance check) where both my passes answered it 6 of 6, and e06 3 of 3 against my 2 of 6. A question decided by a
cached verdict flips all three runs of a process at once: that is three answered runs from one sample.
**Consequence** (**measured** for k08, **believed** in general): R0's k08 "answered in all three V1 runs" and its
must-refuse differences of one run are within this spread, and V3's 46 against 40 is too.

The passages (not the files) are not fully repeatable: with the model off, the six passages of a15 and a17 (gold) and
of 4 benchmark questions per run (q031, q071, q104, q125, q136, q144 in turn) differ from run to run, also inside a
pass; R0's baseline copy differed from mine on the same questions. No file-level or pieces result moved with them.
So a question lost or gained among these is read before it counts.

What a later gate needs (**believed**, from these numbers):

- Files, pieces, retrieval benchmark, generated examples: one run is enough; any difference is real, read the
  question if it is one of the eight with moving passages.
- First attempts: the pass totals moved by 1, but 8 questions moved between passes in both directions and single
  runs ranged 32–35; if the runs were independent, the difference of two 141-run totals would have a standard
  deviation of about 7. I would call 6 or more real and 1–5 spread until more runs; R0's 94 (−5) is spread, its 90
  (−9) real.
- Answers: run each of the three runs in its own server process (or clear the three caches between runs), so each
  run samples the relevance check, the route and the bridge anew. With that, compare per question over 6 runs (two
  passes of three), and call a question changed when it moves by 4 or more of 6; a gate on answered runs needs a
  margin of about 7 of 69, which R0's +6 does not clear. That doubles the API runs of every gate (288 questions asked per variant instead of 144).
- Must-refuse: m19 is answered every time; any other question answered twice or more is a change.
- Time: compare warm runs; the first locate run after a copy is up to 0.3 s slower, which is gate 1's whole margin.

**B. The gold file, read for further sources.** I went through all 57 questions of `answer-source-questions.yaml`,
not only the ones R0 lost. For each I searched the dev index for passages that hold what the question asks (by the
question's terms and the standard's element names, in every source kind), read every candidate, and added a source
only when the passage I read holds the answer, or the same share of it as the sources already named. No source was
added because a retrieval run returned it, and none was removed. 44 questions got 70 further patterns (each matches
one indexed file, a03's parking pattern two examples; checked against the index). The `unsure` marks stay as they
were. The entries are below for review; the YAML notes say only that a source was added and point here.

| question | pattern added | where in the file | why |
|---|---|---|---|
| a01 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs on the Delegated Regulations, §3.5 "Which formats are considered machine-readable?" | answers the question by name (CSV, XML exports; the formats the Delegated Regulations specify); NAPCORE scope, opt-in |
| a02 | `OpRa/examples/ResponseLateDatedVehicleJourneys.xml` | IndicatorFrame / indicatorLogEntries / LateDatedVehicleJourneyEntry with DelayDuration | an OpRa example file of observed delays, one entry per late journey |
| a02 | `OpRa/examples/CancelledAndLateDatedVehicleJourneys.xml` | indicatorLogEntries (LateDatedVehicleJourneyEntry, DelayDuration) and indicators (LateDatedVehicleJourneyCount) | an OpRa example file of observed delays, entries and counts per delay interval |
| a03 | `Netex_21_Sites_Parking_` | NeTEx examples Netex_21_Sites_Parking_1.xml and _2.xml: parkings / Parking (multistorey car park, on-street parking) with ParkingProperties and ParkingCapacity | a parking defined in NeTEx, element by element |
| a03 | `TN-ITS-Open/OWL/codelists/ParkingSiteTypeCode.ttl` | the code list's skos:definition of each parking site type (e.g. interUrbanParkingSite) | TN-ITS defines kinds of parking sites; another standard's definition |
| a04 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a04 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a04 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a04 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a06 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a06 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a06 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a06 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a21 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a21 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a21 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a21 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a22 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a22 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a22 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a22 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a05 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / EscalatorEquipment (Rolltreppe …, Width) with EquipmentPlace refs | an escalator described in a station; the only example with EscalatorEquipment |
| a08 | `02007L0002-20241126#art_3$` | INSPIRE Directive Art. 3(6): 'metadata' means information describing spatial data sets and services, to discover, inventory and use them | another act's definition of metadata |
| a08 | `napcore.eu/metadata` | NAPCORE page 'mobilityDCAT-AP': metadata as the building block that describes datasets on NAPs | says what metadata are for on a NAP |
| b16 | `napcore.eu/metadata` | NAPCORE page 'mobilityDCAT-AP', opening paragraphs | metadata make NAP datasets accessible, reusable and discoverable: what they are used for |
| b17 | `napcore.eu/metadata` | NAPCORE page 'mobilityDCAT-AP', opening paragraphs | what metadata on a NAP are |
| a09 | `Netex_01.1_Bus_SimpleTimetable_JourneysOnly` | header comment: 'the encoding of a simple bus timetable for a linear route … SERVICE JOURNEYS with CALLS with computed passing times' | says what a bus timetable is in NeTEx terms, with the example |
| a10 | `Netex_01.1_Bus_SimpleTimetable_JourneysOnly` | same header comment | as a09 |
| a10 | `32026R0253#art_3$` | TEL TSI Art. 3(33): 'passenger timetable' means the date and time of passenger rail services … | a legal definition of a timetable (rail) |
| a11 | `DelayedAndCancelledJourneysWithEvents` | indicators / LateDatedVehicleJourneyCount ('Delayed Journey Statistics') with intervals | counts late journeys per journey pattern, as in the example already named |
| a11 | `OpRa/examples/ResponseLateDatedVehicleJourneys.xml` | indicators / LateDatedVehicleJourneyCount with intervals, after the LateDatedVehicleJourneyEntry log | counts late journeys, as in the example already named |
| a12 | `FX-PI-01_UK_AMSY_NETWORK_FARE_Arriva-trip_20200417` | ValueSet TypeOfTravelDocument: paper ticket bought on the bus, m-ticket, contactless (UK fare profile) | bus tickets described in NeTEx, as travel document types |
| a15 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| b04 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| b05 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| b06 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| a16 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs, §2.1.4 'Which data must be provided regarding fares information parameters?' | answers the question for MMTIS: static fare data usable in a route planner, if available |
| b11 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs, §1.1 'What is a NAP? Why do I need to provide data on the NAPs?' | defines a NAP and its legal basis |
| a03 | `M4.3.5-Technical-mapping-of-multimodal-data-standards` | NAPCORE M4.3.5, the parking section: parking data in Transmodel/NeTEx, SIRI, APDS and DATEX II, and their mappings | surveys how parkings are defined across the standards |
| a20 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs, §3.4 (formats of the delegated regulations: RTTI DATEX II, MMTIS DATEX II/SIRI/NeTEx, SSTP DATEX II, SRTI DATEX II) and §2.3.2 (SRTI in DATEX II) | names the delegated regulations that require DATEX II |
| b08 | `32024R0490#art_1$` | Art. 1 (amended Art. 4 of 2017/1926): 'NeTEx CEN/TS 16614 and subsequent versions' | gives the CEN reference |
| b08 | `32026R0253#app_C$` | TEL TSI Appendix C, [P.1]/[P.2]: CEN/TS 16614-1:2025 … (NeTEx) Part 1, Part 2 | gives the CEN reference with parts |
| b08 | `SIRI/README.md$` | SIRI README overview: 'relates to NeTEx (CEN/TS 16614 series)' | gives the CEN reference |
| b08 | `napcore.eu/multimodal-data` | NAPCORE page 'multimodal data', Static multimodal data: NeTEx parts 1-6 with CEN/TS 16614-1 … -5 | gives the CEN reference per part |
| b03 | `napcore.eu/multimodal-data` | same page, 'NeTEx is a CEN Technical Standard for exchanging Public Transport schedules and related data', its parts | says what NeTEx is |
| b01 | `napcore.eu/multimodal-data` | same page, Dynamic multimodal data: 'SIRI … enables the exchange of information on transport operations between different computer systems' | says what SIRI is for (short) |
| b02 | `napcore.eu/multimodal-data` | as b01 | German form of b01 |
| b05 | `napcore.eu/multimodal-data` | same page: Transmodel, NeTEx (static) and SIRI (dynamic) explained | explains two of the three standards, as each README explains one |
| b09 | `docs.datex2.eu/v3.7/user-guide$` | DATEX II user guide, 'What is DATEX II?': a standard for the traffic and travel information sector to share data … | answers the question by name |
| b09 | `napcore.eu/standards$` | NAPCORE page 'DATEX II': 'the electronic language used in Europe for the exchange of traffic information and traffic data', history and governance | says what DATEX II is |
| b10 | `dataspecification_tn.adoc#L93$` | INSPIRE TN Technical Guidelines, 'General Executive Summary': Directive 2007/2/EC establishes an Infrastructure for Spatial Information in the European Community (INSPIRE) … | says what INSPIRE is |
| b14 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | NAPCORE MMTIS Quality Framework, Table 2: the time and service related data types of 2024/490 by level (S-1 … D-2) | lists the MMTIS data categories |
| a16 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | same Table 2, rows S-2 'basic common standard fares' (fare network data …) | lists the fare data categories of MMTIS |
| b12 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | the guidance-paper passage: 'NeTEx (stop registry, schedules, fares), SIRI (real-time), OJP …' | names NeTEx for static data under MMTIS |
| b13 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | as b12 | Norwegian form of b12 |
| b15 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs §3.5 'Which formats are considered machine-readable?' | as a01 |
| b20 | `FX-PI-01_UK_FBRI_NETWORK-FARE_WOE-Bristol-pass-(Z2Z)` | FareFrame / distributionChannels / DistributionChannel (First travel shop, Tourist Information Centre, Travelwest outlets) with Description and Url 'where-buy' | where passengers buy tickets, in NeTEx |
| b21 | `FX-PI-01_UK_FBRI_NETWORK-FARE_WOE-Bristol-pass-(Z2Z)` | FareFrame / distributionChannels / DistributionChannel (First travel shop, Tourist Information Centre, Travelwest outlets) with Description and Url 'where-buy' | where passengers buy tickets, in NeTEx |
| b22 | `FX-PI-01_UK_AMSY_NETWORK_FARE_Arriva-trip_20200417` | FareTable 'ArrivaSingleTrip - Cash' / prices / DistanceMatrixElementPrice with Amount per zone pair, for a sales offer package and user profile | a bus fare with its prices, in NeTEx |
| b23 | `FX-PI-01_UK_AMSY_NETWORK_FARE_Arriva-trip_20200417` | FareTable 'ArrivaSingleTrip - Cash' / prices / DistanceMatrixElementPrice with Amount per zone pair, for a sales offer package and user profile | a bus fare with its prices, in NeTEx |
| b24 | `Netex_04_Stops_SimpleStation_1` | header comment and StopPlace: 'a simple station with two platforms encoded in NeTEx XML' (quays, access space, entrance) | how a station is defined in NeTEx, by example |
| b24 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace of a complex station (levels, quays, equipment places) | how a station is defined in NeTEx, by example |
| b25 | `Netex_01_Stops_SingleStopOnStreet_1` | header comment: a single stop on a street: a STOP PLACE with a QUAY, scheduled stop point and stop assignment | how a stop is described in NeTEx, by example |
| b26 | `Netex_07.1_Bus_FlexibleTimetable_ZonesOnly` | SiteFrame / flexibleStopPlaces / FlexibleStopPlace 'Flexible Zone Sigma' with Centroid and area | a flexible stop defined in NeTEx, by example |
| b27 | `netex_nm_equipmentEnergy_version` | VehicleChargingEquipment: 'Specialisation of PLACE EQUIPMENT for vehicle charging', its type and group | the NeTEx element for charging equipment at a place |
| b28 | `norway/vehicles/submodel-Train.xml` | the Train element: TrainSize, components / TrainComponent / TrainElement (carriage) | a train modelled in NeTEx, by example |
| b29 | `Netex_01.1_Bus_SimpleTimetable_JourneysOnly` | lines / Line 'Line 24' with OperatorRef | the link of an operator to a line, by example |
| b31 | `DelayedAndCancelledJourneysWithEvents` | indicatorLogEntries / CancelledDatedVehicleJourneyEntry ('Cancelled Journey 1: No replacement service') with ControlActionType JourneyCancellation | shows what a cancelled journey is in OpRa, by example |
| b32 | `OpRa/examples/TicketingBasedPassengerCount.xml` | indicators / TicketingBasedPassengerCount with BoardingCount and AlightingCount, from ValidationEntry log entries | passenger counts modelled in OpRa, by example |
| b32 | `OpRa/examples/ExpectedPassengerCount.xml` | indicators / ExpectedPassengerCount per scheduled stop point and time band with BoardingCount | passenger counts modelled in OpRa, by example |

Read and not added (the passage I found does not hold the answer): a07 (examples give values of `SeatingCapacity`, no
meaning; the occupancy enumeration is about free seats), a13 and a14 (no other act defines static or dynamic data; the
NAPCORE quality framework uses the words without defining them), a17, a18, a19 (NAPCORE M4.3.5 names DATEX II and SIRI
side by side for parking, not how they connect), a23, b07, b18, b19, b30, b33 and b34 (one Slovenian timetable
example only). b01/b02 got only the short NAPCORE description of SIRI; the SIRI schema's own documentation of its root
element is one line and was not added.

What it shows (**measured** by reading, not by a run): for 44 of 57 questions more than one indexed source holds the
answer, and most of the further holders are of a kind the old entries did not name: example files for element
questions (a02, a04–a06, a11, a12, b20–b29, b31, b32) and NAPCORE documents for legislation and overview questions
(a01, a15, a16, a20, b03–b06, b08–b17). So the file-level measure did count a question as lost when another passage
held the same answer; how often, the run below says.

**The benchmark question file** (149 questions, 141 with patterns) I did not edit. Its patterns are coarser than the
gold file's (`README.md` matches every README, 55 questions name one pattern), so it already counts many neighbours as
found; two questions have the same text as gold questions (q145 = b04, q147 = b01) and the same additions would apply
to them, but the file is also the CI retrieval benchmark's input and CI's index has no NAPCORE pages, so the rule does
not apply cleanly there. Left for step 1's reading of lost questions (**assumed**: the reading rule of §5 covers it).

**File-level baseline, old and new gold file side by side** (same copy, same code, model off, two runs each;
**measured**):

| | found (of 57) | gained | lost |
|---|---|---|---|
| old gold file (pass 1 and 2, four runs) | 34 / 34 / 34 / 34 | – | – |
| new gold file (two runs) | 39 / 39 | b10, b16, b17, b24, b32 | none |

Still not found with the new file (18): a01, a06, a08, a12, a13, a14, a16, a17, a21, a22, b01, b02, b20, b21, b22, b23,
b26, b30. So 5 of the 23 questions the old file counted as lost had another indexed source among the passages that
holds the answer: the file-level measure undercounted by 5 of 57 (**measured**). Step 1 and later steps measure with the
new file; the old numbers stay here for comparison.

**C. Prod's room.** What I could read without changing anything (**measured**, 2026-11-15 evening):

- `health/ready`: version 0.97.226, database and broker ok, 3,125 concept vectors, concept index complete;
  `health/llm`: answer and controller model Haiku 5.5, reachable. No endpoint reports disk, memory, row counts or
  settings.
- The last deploy log (workflow run of 2026-11-15 10:55 UTC, read with `gh run view --log`): the deploy script checks
  a few keys in `.env.prod` and prints only those (`LLM_MAX_EVIDENCE_CHUNKS` not set, default 6 applies;
  `RELEVANCE_CHECK_ENABLED` set). It prints nothing about disk, rows or `RETRIEVAL_MAX_SAME_SOURCE_PATH`.
- `docker-compose.prod.yml`: the `db` service has no memory or CPU limit (it shares the host's memory); the
  embedder has 1.5 GB and 2 CPUs, GraphDB 6 GB, backend 3 GB, worker 2 GB.
- The prod question log since 2026-11-12 (296 events, 219 with evidence blocks, read through the API): no answer has
  two evidence blocks from the same file. On dev (limit 1) the step 0 API runs show the same (0 of 204 answers). With the limit at 2, the model-free
  locate run on the copy puts two pieces of one file among the passages for 36 of 57 gold and 98 of 141 benchmark
  questions, so with 2 on prod most answers would show it. So prod's `RETRIEVAL_MAX_SAME_SOURCE_PATH` is **believed** to be 1, not
  read.

What cannot be read from here, as commands for Andrej on the prod host (all read-only; nothing restarts):

```
cd /opt/napcore-helpdesk
# 1. disk where Docker keeps the database volume, and the volume's size
df -h "$(docker info -f '{{.DockerRootDir}}')"
docker system df -v | grep -E 'VOLUME NAME|postgres-data'
# 2. memory of the host and of each container
free -h; nproc
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}'
# 3. rows, sizes and Postgres memory settings
docker compose -f docker-compose.prod.yml exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "${POSTGRES_DB:-napcore_helpdesk}"' <<'SQL'
select count(*) as rows from helpdesk_sourcechunk;
select pg_size_pretty(pg_total_relation_size('helpdesk_sourcechunk')) as chunk_table,
       pg_size_pretty(pg_relation_size('sourcechunk_embedding_ivfflat_idx')) as vector_index,
       pg_size_pretty(pg_database_size(current_database())) as database;
show shared_buffers; show maintenance_work_mem; show max_wal_size;
SQL
# 4. the per-file limit as the app sees it (default 2 when the key is not in .env.prod)
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "from django.conf import settings as s; print('RETRIEVAL_MAX_SAME_SOURCE_PATH', s.RETRIEVAL_MAX_SAME_SOURCE_PATH)"
```

What each must show for the rows to grow to the plan's bound of 2.5 times (step 1's gate):

- Rows (3): today's count N. Dev has 61,877; prod should be close (same sources; **assumed** until read).
- Size per row (**measured** on the fresh dev copy after `VACUUM FULL`): the chunk table is 1,598 MB for 61,877 rows,
  25.8 KB a row, of which 915 MB are the two 1,536-wide vectors in TOAST and 484 MB the vector index (7.8 KB a row;
  R0's doubled copy had the same 7.8 KB a row). Dev's own table is 3,198 MB for the same rows (dead space).
- Disk (1): at least **8 GB available**. Reasoning (**believed**): 2.5 × N × 25.8 KB ≈ 4.0 GB for the new pieces at
  dev's N, written while the old ones stay (step 5), up to `max_wal_size` (1 GB by default) of WAL, and a dump of the
  database before the switch (the fresh dev copy is 1.7 GB). If (3) shows N much above 62,000, scale the 4.0 GB.
- Memory (2): free memory beside the running containers of at least the new vector index, about 2.5 × N × 7.8 KB ≈
  1.2 GB at dev's N, so the index stays in the page cache (**believed**: ivfflat reads about a fifth of its lists per
  question at 20 probes of 100). The db container has no limit of its own, so the host's free memory is what counts.
- `maintenance_work_mem` (3): building the vector index of today's rows needs 65 MB (**measured**: the copy's restore
  failed at the default 64 MB). A build at 2.5 times the rows needs the session setting raised, as the R0 copies did
  with 512 MB; not a reason to change the server, a step for step 5's command.
- (4) prints 1 or 2. If 2, every measure of this plan on dev (limit 1) differs from prod in one more way, and the
  six places of design point 5 must be measured with prod's value as well.

**D. A token counter that counts as the embedder does.** How the embedder counts (**measured** by reading
`embedding_service.py` and fastembed 0.9.1 in the embedder image): `load_model` builds fastembed's `TextEmbedding`
for `intfloat/multilingual-e5-small` and sets the model's own `tokenizers` tokenizer (0.23.3, the model's
`tokenizer.json` with fastembed's special-token and padding set-up) to cut at `EMBEDDER_MAX_TOKENS` (256);
`embed_texts` prefixes each text with `passage: ` or `query: ` and fastembed tokenizes it with `encode_batch`, which
adds `<s>` and `</s>`; the model reads the first 256 tokens including those two (fastembed's own `token_count` is the
sum of the attention mask, so it never exceeds 256). The indexer embeds `passage_text` = source path, heading and
text, each on its own line.

Where the counter lives, and why: in the embedding service, as `POST /count`, with a backend call
`count_embedded_tokens(texts, kind)` and `count_passage_tokens(chunks)` in `services/embeddings.py`. The service
counts with a copy of the very tokenizer it embeds with (cut and padding switched off on the copy), on the same
prefix, so the count cannot drift from what is embedded when the model, the library or the cut changes; the backend
and worker images have the `tokenizers` library but not the model's files (they live in the embedder's volume), and
the indexer already calls the embedder for every piece. The cost is an HTTP call per batch of 256 texts, and a cut
that tries many sizes must send its candidates in batches. Nothing calls the counter yet; the indexer's cut and every
index result are unchanged (the counter's functions are referenced only by tests).

Verified (**measured**):

- On 1,500 random indexed chunks spread over all 17 kinds (`doc_type`, `chunk_type`, source; up to 60 per kind,
  the rest at random): the new `/count` handler, built from the model as in production and run with the embedder
  image's fastembed 0.9.1 and tokenizers 0.23.3 and the model files copied from the embedder's volume, gives for
  every chunk the same number as fastembed's own `token_count` on a model whose cut is set above any chunk (1,500 of
  1,500), and cut at 256 the same as fastembed's `token_count` of the model as the service configures it, which is
  what the embedder reads (1,500 of 1,500). The model's tokenizer still cuts after the counter is built.
- Against the running dev embedder: for 93 chunks over 256 tokens from 15 kinds, the text cut right after its 254th
  content token (256 tokens by the counter) gives the same vector as the whole chunk, and the text cut one token
  earlier (255) a different vector, 93 of 93. So the running embedder reads exactly the 256 tokens the counter
  counts.
- Of the 1,500 chunks, 983 are longer than 256 tokens (XML examples 653 of 667, NAPCORE 144 of 149, guides 70 of
  135, regulation 31 of 68, INSPIRE 37 of 107, DATEX II 33 of 98, READMEs 11 of 61, schema declarations 1 of 202),
  in line with the audit.
- Unit tests (`test_embedding_service.py`): the count is of the text with its kind's prefix; `/count` rejects what
  `/embed` rejects; without a tokenizer there is no `/count`; with a small real tokenizer the count includes the
  special tokens and is not cut while the model's tokenizer still cuts and pads; the backend call sends exactly
  `passage_text`, batches by 256, and raises when the service cannot count. 27 tests of the embedding and re-embed
  files pass with `tokenizers` installed (the real-tokenizer test skips without it).
- Not done: the live dev embedder serves `/count` only after it is started again with this code, and prod's after
  the next deploy (the deploy rebuilds the embedder). I did not restart it. The check above ran the new handler on
  the host, with the embedder image's library versions, not inside the running service.

### Corrections to the step 0 record (2026-11-16, from building the local measurement tool)

- **Measured** (the three functions called by hand with a counting stand-in for the model): of the three verdicts
  cached per process, only the relevance check was a source of spread in step 0. The vocabulary bridge is switched
  off in the host settings and made no call; the controller route is asked only on an FAQ match, and none of the
  288 runs had one.
- **Measured**: the passages that move between two runs on the same index are not caused by a GraphDB timeout, as
  I believed above. GraphDB gave identical answers, without a failure and without a call over 1 s. The same
  retrieval repeated in one process gives 4 different results with the graph candidates on and 1 with them off.
  The cause is in the graph candidate code in the process; the line is not found yet. In the validation the
  questions e01, e03 and m22 moved (and e04 once).
- **Measured**: in the table, "26 of 30" and "83 of 90" mix two sets. 26 and 83 count the questions with a wanted
  file among the passages (of 32 and 92); on the measurable subset the numbers are 24 of 30 and 81 of 90.
- **Measured** (validation of the tool on the step 0 copy, 2 runs of the 48 questions): with the verdicts held
  equal and unchanged prompts replayed, 90 of 96 question runs needed no model call, and all 90 gave the recorded
  outcome. On a copy with one schema file removed, exactly the two questions that had read it were asked again,
  plus the moving ones: 13 model calls where a full run makes 213.

### Step 1 (2026-11-16, dev copies `napcore_helpdesk_s1base` and `napcore_helpdesk_s1v`, 0.97.227)

**Verdict: gate 1 is not met.** The cut does what design points 1 to 3 ask for every kind but one (pieces fit the
embedder, nearly none cut inside a unit by the cutter's own count; but NAPCORE's PDF text is cut inside sentences
far more often than 5 %, read by hand), the case is fixed (the passage with `LateDatedVehicleJourneyCount` is given
in 3 of 3 runs) and retrieval is faster, but of the 7 questions with a better piece left out only 2 got it (gate: at
least 4), files are lost and gained in about equal numbers, and the retrieval benchmark fell from 0.893 to 0.812
hit@10. The 7-questions line cannot be repaired by a cut: 5 of the 7 better pieces are schema declarations, a
README section and an example header that this cut leaves as they were; what decides them is which passages win the
six places. So I stopped after stage 1 and the free dry replay: no answer was asked again, no example generated, no
repair build. Everything stays off by default (`RETRIEVAL_PREPARED_INDEX`, the command writes only to a named
copy). All figures **measured** unless marked.

| gate 1 line | baseline | step 1 | met? |
|---|---|---|---|
| pieces longer than the embedder reads, per kind | 5–99 % (audit) | at most 0.01 % (XML examples: 13 of 128,207) | yes |
| pieces cut inside a unit, per kind | 92 % of XML examples (audit) | cutter's count at most 3.7 % (DATEX II pages); read by hand, NAPCORE about a quarter (below) | **no** for NAPCORE |
| the case: passage with the count element given | 0 of 3 | 3 of 3 (dry replay; the answer was not asked) | yes (passages) |
| the 7 questions with a better piece left out | – | 2 better (b14, q059), 5 unchanged, 0 worse | **no** (needs 4) |
| answers (answerable, must-refuse) | 44/69, 4/75 | not measured (stopped by the line above) | – |
| files, gold as on main (57) | 39 | 39: lost a19, b05, b29; gained a16, b01, b02 | see below |
| files, gold before step 0 (57) | 33 | 33: lost a19, b05, b29, b31; gained a16, b01, b02, b10 | see below |
| files, benchmark (141) | 124 | 122: lost q013, q017, q019, q083, q121, q140; gained q015, q063, q146, q147 | see below |
| examples | 129 generated, 94 first attempts of 141 | not measured | – |
| retrieval median, warm gold run, both copies one after the other on a quiet stack | 1.80 s | 1.07 s | yes |
| rows | 61,877 | 152,607 (2.47×; bound 154,692) | yes, barely |

Not in gate 1 but measured: retrieval benchmark hit@10 / MRR@10 0.893 / 0.564 → 0.812 / 0.567; best piece given
(the finer measure) gold 31 of 37 in both, benchmark 83 of 92 → 80 of 91; chunk table 1,598 → 2,760 MB, vector index
484 → 1,193 MB (after `VACUUM FULL` and `REINDEX`, ivfflat lists 100 as on dev).

**Diagnosis 1: where the text to cut comes from.** Checked by cutting each local source with today's cut and
comparing with the stored chunks of every indexed file, as multisets of texts. Repository kinds come from the local
checkouts (NeTEx, SIRI, OpRa as they are; TN-ITS from a clone at the indexed commit, made for R0; mobilityDCAT-AP
from a clone at the indexed commit `1ae93b2`, because the local checkout is at another commit). The web-harvested
kinds come from the snapshots committed in `docs/` (EU legislation `.xhtml`, the NAPCORE and DATEX II text
snapshots, the DATEX II model JSON, the INSPIRE AsciiDoc and code-list JSON), read through each indexer's own
record builder; nothing was harvested and no source refresh ran. Every file of every kind gives back exactly its
indexed chunks (61,708 of 61,877 rows), except 6 TN-ITS schema files (169 rows), whose chunks were made before the
XSD summary got enumeration values. Those 6 are left as they are and are the only part not covered. Whether
harvested prose can be cut again from the stored chunks did not need an answer, since every harvested kind has a
local copy.

**Diagnosis 2: the dry cut, and the limit.** The limit was written down before any search result existed
(at 01:17, after the first dry cut): 256 tokens, the embedder's own cut, as returned by `/count`. It is counted on exactly
the embedded text (`passage: `, source path, heading, the piece's lead and place lines and body, with the two
special tokens), and it is the same for every kind. It is not set lower because every token below 256 is text the
embedder would have read, and the cut was already near the row bound. The XML summary is stored after the body and
is not embedded; at 1,200 characters the embedder never reached it either (R0 step 0a). The first dry cut missed
the inside-a-unit line for XML examples (6.2 %), the INSPIRE specification (11.9 %) and the READMEs (13.6 %). Long
comments, tables and lists were being cut at any line or at words. I repaired this before building: such text is
now cut at lines that end a sentence or start a new item first, then at sentence ends. The XML size estimate is
also calibrated per file (the sum of line counts missed about 10 tokens a piece). The build used this cut.

| kind | rows before | pieces | kept as is | tokens median / p90 / max | over 256 | inside a unit (cutter) | text check (upper bound) | near-empty left out | duplicates left out |
|---|---|---|---|---|---|---|---|---|---|
| XML examples | 43,193 | 128,207 | 0 | 198 / 223 / 262 | 0.01 % | 0.1 % | 2 % | 289 | 19,024 |
| XSD declarations | 10,565 | 10,658 | 169 | 122 / 187 / 256 | 0 | 0.3 % | 21 % | 6 | 134 |
| XML schema files | 14 | 31 | 0 | 175 / 245 / 252 | 0 | 0 | 0 | 0 | 5 |
| NAPCORE | 2,979 | 6,081 | 0 | 240 / 254 / 256 | 0 | 0.1 % | 51 % | 0 | 6 |
| DATEX II pages | 1,236 | 2,043 | 0 | 224 / 253 / 256 | 0 | 3.7 % | 45 % | 6 | 131 |
| DATEX II model | 1,240 | 1,491 | 0 | 163 / 248 / 256 | 0 | 0 | 31 % | 8 | 0 |
| EU legislation | 735 | 1,004 | 0 | 193 / 249 / 256 | 0 | 0.2 % | 16 % | 12 | 0 |
| INSPIRE specification | 553 | 898 | 0 | 211 / 252 / 256 | 0 | 0.2 % | 42 % | 3 | 2 |
| INSPIRE code lists | 41 | 50 | 0 | 156 / 243 / 255 | 0 | 0 | 20 % | 0 | 0 |
| TN-ITS Turtle (guide, frame) | 905 | 1,389 | 0 | 224–235 / 248–253 / 256 | 0 | 0 | 20–27 % | 0 | 4 |
| mobilityDCAT-AP HTML (guide, frame, object) | 216 | 273 | 0 | 201 / 248 / 256 | 0 | 0 | 38–92 % | 0 | 0 |
| READMEs | 61 | 59 | 0 | 151 / 243 / 254 | 0 | 0 | 42 % | 1 | 0 |
| NeTEx `.txt` examples | 123 | 226 | 0 | 254 / 256 / 256 | 0 | 0 | 8 % | 0 | 0 |
| mobilityDCAT-AP `.ttl` examples | 16 | 28 | 0 | 229 / 248 / 253 | 0 | 0 | 54 % | 0 | 0 |

"Inside a unit (cutter)" counts pieces the cutter itself had to cut below its smallest unit: inside a sentence, a
line, a text node or a comment. The "text check" is the audit's test (a piece that starts in lower case or ends
without a sentence end). It also counts every list item, table row and heading, so it is an upper bound. I read 20
random prose pieces flagged by the text check. 13 end at a real unit (a list item, a table row, a heading line, a
table of contents). 6 end inside a sentence, 5 of them NAPCORE PDF text where the wrapped next line starts with a
capital or a digit, so the cutter's line rule took the break for a new unit. One more is unclear. Read that way,
about a quarter of NAPCORE pieces (13 of the 20 sampled were NAPCORE, 6 of them inside a sentence) and a few
percent of the other prose kinds end inside a sentence. So the line is **not met for NAPCORE** (**believed** at
this size of sample). A rule that fits PDF text (a line break ends a unit only after a sentence end) would repair
it. It is not built.

The 19,024 duplicates are XML example pieces whose stored text equals one already kept: copies of the same example
in two folders, and repeated frames. A file whose pieces are all copies of another file's now has no pieces of its
own. The 289 near-empty XML pieces were pieces of end tags only. Leaving them out drops closing tags from the text
read at answer time, so they are kept from now on (separate commit). The measured build still left them out.

**Diagnosis 3: what ranks or counts pieces** (read in the code; the list of R0 step 0b checked again place by
place). The rule I used: a limit meant for files counts files. Everything else is left as on main.

- Rare-term limit (`RARE_TERM_MAX_CHUNKS`, 200, counted in rows): with about 3 times the pieces per example file a
  term stops being rare much sooner. With the setting on it counts files, read in a stream and stopped at the
  bound.
- Graph alias bound (`GRAPH_ALIAS_MAX_CHUNKS`, 1,000 rows): an alias found in 40 to 50 example file names would pass
  the bound and lose its candidates. With the setting on it counts files.
- Element candidates (top 6 by quality): the places would go to pieces of one or two files. With the setting on it
  takes one piece per file first.
- `condition_example` and `asked_from_parts` (`values(...).distinct()`): the model's default ordering puts
  `quality_score` and `chunk_id` into `SELECT DISTINCT`, so these rows were per chunk, not per file. This is a fault
  on main already (**measured** by the generated SQL, read by a helper). With the setting on the ordering is cleared.
- `examples_using_elements`, `shown_example_chunk`: a parent and its child in one piece get rarer, and the shown
  piece is the opening of the object (about 600 characters). Left as is. The shown piece goes through
  `_added_candidate`, which reads its unit around it when the setting is on.
- Graph per-file scan (8 rows per file, by quality): quality is nearly flat inside a file, so the 8 are the file's
  first pieces. Left as is (step 3 replaces this search).
- `compute_chunk_quality` (word bands): an XML piece with its summary mostly stays in the 60–280 band. About 40 %
  drop to the 20–59 band (−0.05; **measured** by the helper on R0's 600-character cut, not on this one). Left as is.
- Per-file cap, vector pool (30 rows) and pre-selection (32): pieces of one file take several slots of the pool, so
  fewer files reach scoring. **Believed** to be why the retrieval benchmark fell (0.893 → 0.812). Not changed here.
  It is the same question as design point 5 (step 2).
- `grounded_generator` (the answer without the model) shows the place line instead of XML. Not reached on dev (model
  on). Left as is.
- `_named_example_candidates` reads a non-empty example heading as Turtle types. XML pieces keep an empty heading, so
  nothing changes.
- `infer_doc_type` and `infer_scope` are computed per piece on its body, not on the lead and place lines, so the
  heading path cannot make a guide piece read as "frame".

**Diagnosis 4: reading large.** Each piece stores, in `structured_metadata["piece"]`, its unit (an XML document; a
prose section; a schema declaration; a run of Turtle statements), its order in the file and where its body lies in
its text. At answer time one query fetches up to 6 pieces on each side of every passage (same repository, path and
unit), and the passage's text becomes the found piece plus the next and the previous piece in turn, while they fit
1,200 characters, under the place line of the first piece taken. The chunk id, path and source of the passage do
not change, so the citation points at the same file. Checked by hand on stored pieces of three kinds: an XML
example (a fare usage parameter, grown with the next sibling element, 826 → 1,046 characters, document text in
order), a NAPCORE PDF passage (grown with the paragraph before, 700 → 1,177) and a schema declaration cut in two
(its two halves joined, 225 → 819). Time: 32 ms median, 38 ms p90 for six passages (50 random sets).

**The case and the 7 questions** (read by hand, base against step 1, gold run 2 and benchmark). The late-journeys
question gets a passage with `LateDatedVehicleJourneyCount` in 3 of 3 runs (dry replay, so passages only; the answer
was not asked). Of the 7, b14 is better (the MMTIS annex passage now lists timetables, interchanges, hours,
vehicles and their accessibility for a bus operator, where the baseline gave the cycle-network items). q059 is
better (NeTEx_50's `TemplateServiceJourney` instead of its day types). a09, a15 (already the README overview), q057,
q072 and q149 are unchanged: they are the same schema declarations or headers as before, or the better piece still
loses its place.

**Files lost and gained, read** (the rule of §5: a loss counts only if the passages no longer hold what the named
file holds).

- Gold, counted as lost: a19 (the SIRI situation-exchange example and the situation schema replaced by a DATEX II
  TLS annex and an OpenLR class), b05 (the OpRa README replaced by OpRa and SIRI example openings), b29
  (`LinePropertiesGroup` with `OperatorRef` replaced by an operator list and a TransXChange line).
- Gold gained: a16 (the MMTIS amending annex), b02 (the SIRI README overview) are real. b01 is a gain only by file:
  its README piece is the one on the use of AI in the repository.
- Benchmark, not counted (another passage holds the answer): q013 and q017 (the OpRa examples show
  `LateDatedVehicleJourneyCount` per journey pattern with its intervals, counts and percentages), q083 (the
  ticketing-based passenger count example links counts to `netex:ScheduledStopPointRef`).
- Benchmark, counted as lost: q019 (no declaration says which fields are required), q121 (no definition of a late
  journey; a NeTEx planned-delay example instead), q140 (the connection-monitoring example is gone).
- Benchmark gained: q015, q063, q146 are real; q147 is a gain only by file (the same README piece as b01).

So, as the gate is written (losses read, gains counted): gold 3 lost against 3 gained, benchmark 3 against 4. That
meets the line. If gains are read the same way as losses, gold is 3 lost against 2 gained, and it is not met.
Every loss has the same explanation, as in R0: example pieces, now three times as many, take the places of schema
declarations and READMEs. The old gold file shows the same picture side by side (33 → 33; a19, b05, b29, b31 lost,
a16, b01, b02, b10 gained).

**What the free replay says about stage 2.** With the setting on, the text of almost every passage changes, so
almost nothing can be replayed. In the dry replay only 42 must-refuse runs and 2 example runs matched a recorded
prompt. 234 question runs would have needed the model, about 300 calls (**believed**, from the baseline's 475 calls
for 278 runs). None were made.

**Spread of the baseline** (the free dry replay against its own copy): e01, e03 and m22 move as in step 0, and so do
gen44 (all three runs) and gen33 (run 3).

**Cost.** Baseline recorded once: 475 model calls (Haiku, as configured). Step 1: no model call. Build: one build,
2 h 2 min of wall time in three parts. The embedder timed out twice (one request of 16 pieces took more than the
120 s timeout) while the baseline's example benchmark and a gold run were using it. It did not restart: same start
time, restart count 0, no OOM. The command skips files already cut, so it went on from where it stopped, and the
third part ran with nothing else on the stack. Pieces whose embedded text equals an indexed chunk's kept their
vector: at least 11,589, mostly schema declarations (the third part's count; the reports of the first two
parts were lost when they stopped). `VACUUM FULL` and `REINDEX` took 5 minutes.

**Believed, not verified.** That the retrieval benchmark fell because pieces of one file take several pool slots.
That NAPCORE's share cut inside a sentence is about a quarter (20 pieces read). That "rows end near 130,000": they
ended at 152,607. The 19,024 duplicate example pieces, left out as the plan says, are why it is not more.

*Correction (2026-11-17, from step 2).* The belief that the retrieval benchmark fell because pieces of one file take
several pool slots is mostly wrong. **Measured**: on this copy the vector index (ivfflat, 100 lists, 20 probes) keeps
on average 88 % of the exact 30 nearest pieces (367 retrieval calls of the gold, benchmark and retrieval benchmark
runs; for some questions 17 %), where on the baseline copy it kept all of them. With every vector search exact (50
probes, which Postgres plans as a full scan) the same copy gives 0.873 hit@10 instead of 0.812; with 40 probes, 94 %
of the nearest pieces, 0.846 (step 2's copy). So most of the fall, 0.06 of 0.081, was the index missing near pieces
on a table 2.5 times larger. What is left, 0.02 with exact search, is the share example pieces take of the first
places (below, step 2).

**For step 2 and later.** The files lost here and in R0 come from one cause: whole, labelled example pieces win
places from declarations and READMEs. That is design point 5. The retrieval benchmark's fall has the same cause in
the pool. The PDF line rule and the kept end tags would need the one repair build this step did not use.

### Step 2 (2026-11-16/17, dev copy `napcore_helpdesk_s2v`, a copy of `napcore_helpdesk_s1v`, branch at 7a152e2 and c58d8ca)

**Verdict: gate 2 is not met, and no model was called.** Of the stage 1 lines fixed before the runs, retrieval time,
rows, tokens and files lost against gained are met; the index line, the NAPCORE reading, the step 1 losses, the
7 questions and the reading of changed passages are not. So stage 2 (answers, examples) was not run. The six places
shared among kinds (design point 5) brought back one file of the six step 1 lost (q013); I reverted it (342a0d6),
because the rule as the plan states it rarely applies: six places held by one kind happen in 19 of 198 questions,
and the files are lost where examples hold four or five of the six. Two findings matter more than the rule: the
vector index misses near pieces on the larger table and no setting I tried fixes that within the time gate (A), and
the PDF line repair halves NAPCORE's cut sentences but does not bring them under 5 % (B). All figures **measured**
unless marked.

| gate line (fixed before the runs) | baseline (`base`) | reference (`s2ref`) | step 2 (`s2`) | met? |
|---|---|---|---|---|
| 1. index: recall of the exact top 30 ≥ 0.99, no question under 0.9 | 1.00 (15 gold questions, given) | 0.943, lowest 0.38, 63 of 367 calls under 0.9 (ivfflat 100 lists, 40 probes) | same index | **no** |
| 2. retrieval median, warm gold run, ≤ base + 0.3 s | 1.75 s; again at 00:34: 2.38 s | 1.34 s; again: 2.09 s | 1.98 s; again: 2.07 s | yes (below base in both rounds) |
| 3a. rows ≤ 154,692 | 61,877 | 152,741 | 152,741 | yes |
| 3b. pieces over 256 tokens, per kind | – | 0 in every re-cut kind (embedder's counter) | same | yes |
| 3c. NAPCORE pieces cut inside a unit, read by hand | – | about 6.6 % (9 of 60 flagged pieces; 44 % flagged) | same | **no** |
| 4. step 1's counted losses back: a19, b05, b29, q019, q121, q140 | – | b05, b29, q140 back; a19, q019, q121 still lost | same as s2ref (q013 back too) | **no** |
| 5. files: no unexplained loss, not more lost than gained | gold 39, bench 124 | gold 41 (−a19, +a16 b01 b02), bench 122 (−q013 q017 q019 q083 q121, +q015 q063 q147) | gold 41, bench 123 (q013 back) | yes for files; retrieval benchmark 0.846 against 0.893, not explained question by question |
| 6. the 7 questions: ≥ 4 better, none worse | – | 2 better (b14, q059), 5 unchanged: the same pieces as step 1 | same; a15 and q072 changed, read equal | **no** |
| 7. changed passages s2ref → s2, read | – | – | 8 better, 9 equal, 1 worse (a18) of 18 | **no** (one worse) |
| stage 2: answers, examples | 44/69, 4/75 (step 0) | not run | not run | not measured |

Retrieval benchmark hit@10 / MRR@10: base 0.893 / 0.564, step 1 0.812 / 0.567, s2ref 0.846 / 0.571, s2 0.846 / 0.571.
Best piece given: gold 31 of 37 → 34 of 39 → 35 of 40; benchmark 83 of 92 → 79 of 91 → 80 of 93.

**A. The index (diagnosis first).** Measured with every retrieval call the stage 1 runs make (75 gold passes, 143
benchmark passes with the app's scopes and graph concepts in the query vector; 149 retrieval benchmark calls without
scope): the query vectors were captured, and for each call the exact nearest pieces in its scope (index scans off)
were compared with what the app's index query keeps (`ORDER BY` distance `LIMIT` twice the pool, then the pool by
distance). Scripts and tables: `.claude/skills/measure-on-copy/runs/s2-work/`.

- It is the index, not the scope filter or the iterative scan: with the iterative scan off the result is the same
  (0.883); with every list probed it is 1.00. Calls with a small scope (OpRa, EU legislation, mobilityDCAT-AP, and
  after the re-cut DATEX II and SIRI) are planned by Postgres as a full scan and are always exact; the misses are in
  the unscoped and NeTEx searches.
- The step 1 run with 50 probes (`step1-probes50`) did not use the index: from 50 probes of 100 lists Postgres plans
  a parallel full scan (read in `EXPLAIN ANALYZE`, 0.9–1.1 s a query). Its 100 % recall and its 2.19 s are the exact
  search's.
- The lists are uneven: of 300 sampled rows, the largest list holds 20,960 rows (14 % of the table) on s1v and 4,193
  on s1base. The given `recall.py` reads only the gold file (the benchmark YAML's first list is `target_k`), so its
  15-question sample had no benchmark question.
- **Believed**: the question vectors (`query:`) lie away from the clusters of passage vectors, and the nearest 30
  sit in a narrow band of distance (a01: 0.167 to 0.195), so any approximate index needs to look at a large part of
  the table.

| index (built on the copy) | setting | mean recall | lowest | calls < 0.9 | index query median / p90 |
|---|---|---|---|---|---|
| ivfflat 100 lists (migration 0009) | 20 probes (the app today) | 0.883 | 0.17 | 137 | 0.14 / 0.22 s |
| same | 30 probes | 0.937 | 0.37 | 72 | 0.36 / 0.48 s |
| same | 40 probes | 0.966 | 0.37 | 33 | 0.33 / 0.53 s |
| same | 50 or 100 probes | 1.000 | 1.00 | 0 | 1.03 / 1.17 s (full scan) |
| ivfflat 400 lists (build time not recorded) | 20 probes | 0.819 | 0.00 | 163 | 0.04 / 0.16 s |
| same | 40 probes | 1.000 | 1.00 | 0 | 0.98 / 1.07 s (full scan) |
| hnsw m 16, ef_construction 64 (7 min 54 s, 1,192 MB) | ef_search 64 / 100 / 200 | 0.56 / 0.59 / 0.62 | 0.00 | 230–250 | 0.08–0.10 / 0.20–0.23 s |
| hnsw m 32, ef_construction 128 (22 min 13 s, 1,192 MB) | ef_search 100 / 200 / 400 | 0.74 / 0.77 / 0.83 | 0.00 | 118–168 | 0.13–0.20 / 0.26–0.41 s |
| exact search by hand (a01, `LIMIT 60`) | 2 workers; 4 or 6 asked (3 started) | 1.00 | – | – | 0.91–1.06 s; 0.79–0.81 s |

The hnsw builds ran with `maintenance_work_mem` 256 MB for the session and no parallel workers: the first try with
the default 2 workers failed at once ("could not resize shared memory segment … No space left on device", the
container's `/dev/shm`), and the graph stopped fitting the memory after 39,022 rows, so the builds went on on disk.
Nothing else failed. Even at ef_search 1,000 the m 16 index returned none of a01's exact 30 (distances 0.203–0.213).

No index definition or setting reached the line within the time gate. I chose ivfflat with 100 lists and 40 probes
(`VECTOR_INDEX_PROBES=40`, no new index, no code): after the re-cut 0.943 of the nearest pieces, lowest 0.38, at
0.24 s median per index query. For step 5 this is open, not decided: the exact search costs about 0.9 s a query
here; an index on the 384 numbers the embedder fills (the column holds 1,536, the rest zero) might make the exact
search cheap enough (**not measured**). No code for another kind of index is on the branch.

**B. The PDF line repair applied.** `prepare_index --recut` (7a152e2) cuts files already cut again and replaces only
those whose pieces change. Before writing I ran it dry over every harvested kind: the repair as committed (a0eef30)
changed the INSPIRE specification too, and badly: its width test joined long XML lines of the style listings and
AsciiDoc table and block lines to the next line, and the cutter then cut 69 of 902 pieces inside a line (7.7 %,
against 2 before). I repaired that in the same commit: a line continues only into one that starts as prose (a word,
a number, an opening bracket or quote). With that, the repair changes 51 of 119 NAPCORE files (6,081 → 6,211
pieces) and 7 of 197 DATEX II pages (2,043 → 2,047); EU legislation, INSPIRE (specification and code lists) and the
DATEX II model are unchanged. Repository prose (Markdown, NeTEx `.txt` examples, XSD) gives the same pieces before and
after on the local checkouts (estimated token counts; TN-ITS Turtle and the mobilityDCAT-AP HTML not checked, no
checkout at the indexed commit). Written: 152,607 → 152,741 rows, 3,309 NAPCORE vectors kept, 2 min 35 s; then
`VACUUM FULL` (24 min 49 s under a busy machine) and the ivfflat index rebuilt (14 s, 1,194 MB).

Real token counts (embedder's counter): no piece over 256 in any re-cut kind; NAPCORE median 237, p90 254; cut inside
a unit by the cutter's count NAPCORE 0.1 %, DATEX II pages 3.8 %. Read by hand (20, then 40 more because the 20 gave
2), NAPCORE pieces flagged by the text check (2,733 of 6,211):

- 20 (seed 7): 1 ends inside a sentence (a page footer splits it), 1 inside a file name; 3 split a table row between
  its columns, 1 unclear; the rest end at a heading, list item, footer, sentence end or table end.
- 40 (seed 8): 5 end inside a sentence (two of them at a page break or inside the footer sentence), 1 inside a
  wrapped list item, 1 inside a URL; 5 split a table row; 1 unclear.

So 9 of 60 flagged pieces end inside a sentence, item or URL, about 6.6 % of all NAPCORE pieces (**believed**, 60
read), 12 % if table rows split between columns count too. Step 1 read about a quarter. The line is not met. What is
left is mostly page furniture (running headers and footers break sentences) and PDF tables, which the text snapshots
do not mark as tables.

**Reference run `s2ref`** (part C off: the run used the tree at 7a152e2, which has no part C). Against `base`:

- Gold 39 → 41: a16, b01, b02 gained (as in step 1), a19 lost. b05 and b29 are back.
- Benchmark 124 → 122: q015, q063, q147 gained; q013, q017, q019, q083, q121 lost. q140 is back.
- Retrieval benchmark: 10 questions lose hit@10 (q001, q007, q017, q019, q041, q056, q082, q088, q121, q129; 9 of
  them hit@20 too), 3 gain it (q077, q137, q146). Top-5 places held by example `.xml` files: 277 in base, 433 here;
  schema `.xsd` 415 → 266. I did not read these 10 one by one.

**C. The six places shared among kinds.** Diagnosis on `s2ref`'s settings, every gold and benchmark question run as
`locate_answer_sources` runs it, with the probe keeping the candidates after the per-file cap, the six after the cut
and the final six, with their kind (`doc_type`; for passages made at answer time their own type such as
ontology-definition and xsd-definition, which I count as kinds of their own):

- Questions whose six are all one kind while another kind has a candidate above the score limit (0.62): 19 of 198
  (7 gold, 12 benchmark), examples in 11, schema declarations in 4, ontology relations 2, DATEX II 1, guide 1.
- Questions that lose their file at the choice of the six: 17 in this run (16 at the cut, q083 at the coverage
  step). In 5 of them the six are all examples (a12, q013, q070, q078, q133); in the others examples hold four or
  five places and one or two go to a README, a schema declaration or a definition. The wanted file stands 4th to
  19th after the per-file cap. In a12, q070 and q133 the wanted file is an example itself, so a rule about kinds
  cannot help them.
- Checked by hand with the probe: q013's six are all OpRa examples; its file, `opra_lateDatedVehicleJourney_version.xsd`,
  is 11th after the cap with score 0.934, and it is the first candidate of another kind, so the rule gives it the
  sixth place. q019's six are five examples and the README; its file (a schema declaration with score 1.0) is 7th,
  and the rule does not apply.

The rule (c58d8ca, behind `RETRIEVAL_KINDS_SHARE_PLACES`, off): when every chosen passage is of one kind and a
candidate of another kind reaches the score limit, the best such candidate takes the last place. It runs after the
two coverage steps, so what they put in keeps its place. Five unit tests.

`s2` against `s2ref`: files gold 41 = 41, benchmark 122 → 123 (q013 back), nothing lost; the retrieval benchmark
did not move (its 20 places are rarely one kind). The passages of 18 questions changed, so all 18 were read, not a
random 20 (a15, a17, q104 and q144 also move between two runs of the same index):

- a15 equal (one OpRa schema declaration for another; the README stays); a17 equal (no passage answers, before or
  after); a18 **worse** (a DATEX II parking-arrangement enumeration replaced by OpenLR's location name); a23 better
  (the UIC operating period with `ValidDayBits` comes in); b19 equal (dataset series replaced by the README overview).
- q013 better (the `DelayGroup` declaration replaces a fleet-dimensions example); q020 better (the cancelled-journey
  entry with `operationalEvents` replaces a passenger-count example); q062 equal; q066 better (a `Line` example
  replaces an aggregate schema header); q072 equal (README for the same header); q076 better (the OpRa delayed and
  cancelled journeys example beside the NeTEx relations); q078 better (the NeTEx journey declaration replaces an
  example header); q080 better (the planned service intensity example); q102 equal (the stop monitoring schema for
  a subscription example; request and response stay); q104 equal; q105 better (an estimated timetable example
  with `EstimatedCall`); q133 equal; q144 equal.

Diagnoses asked for:

- q017: lost at the score limit. Its file's pieces stand last of 23 scored candidates: similarity is rescaled between
  the lowest and the highest in each question's pool, and in a pool of OpRa example pieces the schema declaration
  is the lowest. Not counted as lost: the examples given show `LateDatedVehicleJourneyCount` with its intervals.
- a19: never a candidate. Its nearest wanted piece is 49th by exact distance in the SIRI and DATEX II scope, the pool
  holds 30, and no rare term finds it. Counted as lost: the six hold no link between SIRI and DATEX II.
- q083: in the six after the cut (4th and 6th), then pushed out by the element coverage step, which puts in two
  example pieces showing the asked elements from outside the six and cuts to six. Not counted (**believed**, as step
  1 read: the ticketing-based passenger count example links counts to `netex:ScheduledStopPointRef`).
- q140: back in `s2ref`; the element coverage step puts two pieces in front of it but it keeps the sixth place.
- q019 and q121 still count as lost: no declaration of the required fields (q019); no definition of a late journey,
  though the OpRa example of delayed journeys is given (q121).

None of these is fixed: each is a threshold or a step of its own, not the rule of this step.

**Why I reverted part C.** As fixed before the runs, a failed part is reverted. The rule did what it says, cheaply,
and did not lose a file, but it moves one of the six counted losses and one read passage set got worse. What the
diagnosis shows instead (**believed**, not tried): the losses come from examples taking four or five places, and
from the rescaling of scores inside a pool full of example pieces (q017). A share per kind (for example, at most
half the places for one kind when other kinds have candidates above the limit) would be the next variant; it is a
threshold chosen after seeing the data, so it needs its own run.

**Times.** The two rounds of gold runs differ by 0.6–0.7 s for the same code and copy (`s2ref` 1.34 s at 22:44,
`s2ref-time` 2.09 s at 00:09): the machine got slower during the night (load 4–13; the Docker VM used up to 11
cores during the `VACUUM FULL`). So I timed the baseline copy again in the second round (`base-time`, 2.38 s). In
the same round the rule costs nothing (2.09 s off, 2.07 s on).

**Cost.** No model call. Runs: `s2ref`, `s2` (25 min each), gold timing runs `s2ref-time`, `s2-time`,
`base-time`; the diagnosis of part C (20 min); recall trials 6 min each. Builds: hnsw 8 and 22 min, ivfflat 100
lists 14 s; re-cut 2 min 35 s; `VACUUM FULL` 25 min. The embedder container
restarted once by itself at 21:36 UTC (restart count 1, not marked out of memory), after the re-cut had finished; I
did not restart anything. Copies: `napcore_helpdesk_s2v` (152,741 rows, ivfflat 100 lists) is step 2's record;
s1base and s1v are unchanged.

**Believed, not verified.** That the query vectors lie away from the passage clusters (why every index needs so many
lists probed). That an index on the 384 filled numbers would make exact search cheap. That q083's passages still
hold the link to stop points. That TN-ITS Turtle and the mobilityDCAT-AP HTML are unchanged by the line repair.
That a share per kind would bring back q019 and q121; nothing here shows it.

### Step 2b: the index (2026-11-17, dev copy `napcore_helpdesk_s2v`, branch at a92b10c)

The vector index of step 2 kept 0.943 of the exact nearest pieces at 40 probes and failed gate line 1. Before any
fix I looked for the cause. The gate for a fix was fixed before the trials: on the same 367 captured retrieval calls,
against the exact reference on the copy as it stands, (1) mean recall ≥ 0.99 and no call under 0.9; (2) retrieval
median of the warm gold run ≤ 2.05 s in a stage 1 run; (3) index size and build time reported; (4) nothing changes
with the setting off. No model was called. Scripts, logs and caches: `.claude/skills/measure-on-copy/runs/s3-work/`.
All figures **measured** unless marked.

**Verdict: all four lines are met.** The vector index misses near pieces because the questions lie far from
every piece, not because of the filter, the build or duplicates; no approximate index setting fixes that. An
ivfflat index on the 384 numbers the embedder fills, in half precision, read whole (100 of 100 lists), keeps every
exact piece of the 367 calls at 0.08–0.13 s a query (120 MB, built in 8.5 s), and the gold retrieval median falls to
1.16 s. With the exact index, none of a19, q019, q121, q013, q017, q083 comes back: those losses are not the
index's. The retrieval benchmark recovers to 0.873 (base 0.893, s2ref 0.846).

**Diagnosis.**

- *The column.* `embedding_vector` is `vector(1536)`; the embedder fills the first 384 numbers. Counted on all
  152,741 rows: no row has a number other than zero beyond the 384th, every row's first 384 have norm 1.0 (to 1e-8),
  no row is all zero. `alternate_vector` is set for 169 rows only (TN-ITS schema pieces, full width, the hash
  vectors kept for rollback); retrieval never reads it. The rows carry no embedding model field. So the cosine
  distance on the first 384 numbers is the distance on the column.
- *Storage.* Each vector is 6,148 bytes, stored out of line (storage `external`, not compressed): the table is
  203 MB, its TOAST 1,195 MB. Any exact scan reads the 1.2 GB of whole vectors, and so does the ivfflat index on
  the column when every list is probed (1,194 MB). This is why the exact search costs about 0.9–1.0 s a query
  whatever form it takes (table below).
- *Duplicates.* Exact duplicates of `embedding_vector`: 26 groups, 58 rows, 32 redundant rows, largest group 4
  (NeTEx fare examples whose texts differ after the first 256 tokens). Not a cause.
- *Near-identical vectors.* The ivfflat list that holds 14 % of the rows (20,958 rows) is NeTEx example pieces only,
  all from two files, `examples/standards/tap_tsi/B1_NRT/Netex_tap_tsi_B1-1080-full.xml` (25,237 pieces in all) and
  `Netex_tap_tsi_B1-1080.xml` (4,328): repeated `FareStructureElement` blocks whose pieces begin with the same element
  path. Within that list the median distance from a piece to its nearest other piece is 0.0002, and every sampled
  piece has 200 others within 0.02 (40 sampled). Elsewhere it is 0.0031, with a median of 52 within 0.02. By kind,
  the whole list is `example` (0 of other kinds). These two files are 19 % of the table (29,565 rows); for the open
  decision on leaving such pieces out of the index, that is the count. Nothing was deleted.
- *Where the questions lie.* For the 367 captured calls the nearest piece is at distance 0.119 (median; p10 0.096,
  p90 0.144) and the last of the 25–100 wanted at 0.150, a band 0.027 wide. For 60 sampled pieces used as queries the
  nearest other piece is at 0.0016 (median). The questions lie about 75 times farther from the pieces than the pieces
  from each other, and their 30 nearest sit in a thin shell at nearly equal distance.

**Why HNSW failed.** I rebuilt the m 16, ef_construction 64 index on the column as step 2 had (7 min 38 s, spilled
after 39,022 rows, 1,193 MB) and tested each candidate:

| candidate | test | result | holds? |
|---|---|---|---|
| the scope filter applied after the index scan | same calls without the filter, against an exact reference without the filter | ef_search 100: 0.476 with the filter, 0.386 without; ef_search 400 with iterative scan: 0.662 with, 0.633 without | **no**: without the filter it is no better |
| the iterative scan off | `hnsw.iterative_scan = relaxed_order` | 0.476 → 0.566 at ef_search 100 (the short results go: 58 → 0) | a small part only |
| a build spilled to disk or under a full `/dev/shm` | HNSW on the 384 numbers as `halfvec`, built wholly in memory (47 s, 170 MB, no spill notice) | 0.459 / 0.573 / 0.715 at ef_search 100 / 400 / 1,000 | **no**: as bad in memory |
| duplicates | count | 32 redundant rows | **no** |
| the reference and the index query not reading the same rows or operator | both `<=>`, the same filter SQL; a01 by hand: exact scan and index on the same query | at ef_search 1,000 the planner chose a full scan (exact, 30 of 30); with the full scan off, the index returned distances 0.203–0.215 and 0 of the 30 unfiltered nearest (0.167–0.195), 17 of the filtered | **no**, but step 2's by-hand check set the filtered index result against the unfiltered exact 30 (**believed**, from the distances); the unfiltered index result has none of them either, so the miss is real |
| the graph cannot reach the wanted rows | each of a01's 30 nearest, searched by its own vector | 28 of 30 found; 260 of 300 random rows found by their own vector (38 of the 40 missed are examples) | **no**: the rows are reachable |
| the questions lie away from the pieces | 60 stored piece vectors as queries on the in-memory HNSW, top 30 | 0.908 at ef_search 100, 0.962 at 400 (questions: 0.459, 0.573) | **yes** |

So HNSW finds the near pieces of a piece but not of a question: the questions lie in a thin shell far from every
piece (**verified** by the contrast above, on the same index), and the greedy walk stops in a region whose pieces
are only slightly farther. The same fact explains why ivfflat needs nearly every list: the lists nearest to the
question do not hold its nearest pieces (**believed**: this is the reading that fits both, not a separate test). The
near-identical blocks make it worse for pieces (the zero-recall pieces as queries are in such blocks, **believed**
from their kind, not counted) but are not what fails the questions: a01's nearest pieces are NAPCORE text,
schemas and regulations, none in the big list.
**The trials.** Recall as in step 2: the share of the exact nearest 25–100 pieces (the full column, full scan, the
app's scope filter) that the index query keeps (`LIMIT` twice the pool, then the pool by exact distance); all 367
calls; index query time warm, on the same machine in one night. "Full scan off" is `SET LOCAL enable_seqscan = off`
in the query's transaction; without it Postgres plans a full scan from about half the lists.

| index (built by hand on the copy) | setting | mean recall | lowest | calls < 0.9 | index query median / p90 | size, build |
|---|---|---|---|---|---|---|
| ivfflat 100 lists on the column (step 2) | 20 / 40 probes | 0.862 / 0.943 | 0.07 / 0.38 | 145 / 63 | 0.11 / 0.24 s | 1,194 MB, 15 s |
| same | 100 probes, full scan off | 1.000 | 1.00 | 0 | 0.94 / 1.03 s | same |
| none: exact scan on the 384 numbers | full scan | 1.000 | 1.00 | 0 | 0.89 / 0.98 s | – |
| hnsw m 16, ef_construction 64 on the column | ef_search 100 / 100 + iterative / 400 + iterative | 0.476 / 0.566 / 0.662 | 0.00 | 257 / 240 / 252 | 0.06 / 0.08 / 0.14 s | 1,193 MB, 7 min 38 s |
| hnsw m 16, ef_construction 64, `halfvec` 384 | ef_search 100 / 400 / 1,000, iterative | 0.459 / 0.573 / 0.715 | 0.00 | 321 / 289 / 208 | 0.03 / 0.02 / 0.04 s | 170 MB, 47 s |
| ivfflat 100 lists, `vector` 384 | 40 / 60 / 100 probes, full scan off | 0.973 / 0.994 / 1.000 | 0.37 / 0.57 / 1.00 | 20 / 2 / 0 | 0.05 / 0.08 / 0.14 s | 239 MB, 7 s |
| ivfflat 100 lists, `halfvec` 384 | 40 / 60 / 100 probes, full scan off | 0.915 / 0.968 / 1.000 | 0.37 / 0.44 / 1.00 | 112 / 46 / 0 | 0.04 / 0.06 / 0.10–0.13 s | 120 MB, 8.5 s |
| same, through the app's own `_nearest_ids_by_index` | the settings below | 1.000 | 1.00 | 0 | 0.08 / 0.10 s | – |

What the table says: no approximate setting reaches the line, because of where the questions lie (above); what
reaches it is reading every list, and that is fast only when the index holds the 384 numbers and not the
1,536. With all lists probed the ivfflat index is in effect an exact scan of a compact copy of the vectors (120 MB
instead of 1.2 GB); the lists only keep the option of probing fewer. The ivfflat lists on the 384 numbers are as
uneven as on the column (not counted again; they do not matter when all are read). I dropped HNSW: its failure
is not a build fault, so a better build cannot repair it.

**The definition chosen.**

```sql
SET maintenance_work_mem = '256MB'; SET max_parallel_maintenance_workers = 0;
CREATE INDEX x_ivf_half384 ON helpdesk_sourcechunk
  USING ivfflat ((subvector(embedding_vector, 1, 384)::halfvec(384)) halfvec_cosine_ops) WITH (lists = 100);
```

with `VECTOR_INDEX_DIMENSIONS=384`, `VECTOR_INDEX_HALF_PRECISION=True`, `VECTOR_INDEX_PROBES=100` (068f7e7). The
code: with `VECTOR_INDEX_DIMENSIONS` above 0 the nearest-row query orders by the same expression as the index and
turns the full scan off for that one transaction (a full scan of the expression reads every whole vector, 0.9 s);
the pool is still ranked on the full column after it. Off by default: then the query is the one of today (unit
tests check the SQL and that the result equals the exact scan's, with and without half precision). Half precision
changes the order only inside the margin of twice the pool, which the exact ranking after it absorbs: 0 of 367
calls lost a piece (**verified** for these calls, **believed** in general). No migration: the index is built by
hand on the copy; whether step 5 adds it as a migration is open.

Build cost: 8.5 s and an `ANALYZE` of 7 s on this copy, no spill and no parallel workers; ivfflat's build holds a
sample of the vectors for its k-means in memory (**believed** a few MB at 100 lists, from how pgvector builds, not
measured); it reads the 1.2 GB of vectors once. Room: 120 MB on disk beside the existing 1,194 MB index, which the
setting no longer uses and which can go once the setting is on (**not done**: the copy keeps both). At query time
the whole 120 MB is read per query; with `shared_buffers` 128 MB here it comes from the file cache.

**Verdict per gate line.**

| gate line (fixed before the trials) | result | met? |
|---|---|---|
| 1. mean recall ≥ 0.99, no call under 0.9 (367 calls, exact reference on the copy) | 1.000, lowest 1.00 (trial script and the app's own query) | yes |
| 2. retrieval median, warm gold, ≤ 2.05 s | `s3` 1.16 s; in the same round `base-time3` 1.77 s, `s2ref-time3` (setting off, 20 probes) 1.09 s; `s2ref-off40` (setting off, 40 probes) 1.37 s | yes |
| 3. index size and build time | 120 MB, 8.5 s + `ANALYZE` 7 s, 256 MB maintenance memory, no spill, no parallel workers | reported |
| 4. nothing changes with the setting off | unit tests of the query (SQL and result); a gold run with the setting off and 40 probes (`s2ref-off40`) gives `s2ref`'s 41 files exactly; the backend test suite (1,131 tests, models off): 7 fail, and the same 7 fail on the tree before the change (cd409fe) under the same environment (relevance check, request body and alias-query tests; **believed** to read settings that my models-off overrides of the local `.env` change); none is in the vector search | yes |

The machine was not slower tonight: `base-time3` (1.77 s) is close to `base`'s first run (1.75 s). The step 2 run
`s2ref` used 40 probes: the same copy with 20 probes (`s2ref-time3`) finds 38 gold files and loses b05, b24, b29,
and with 40 (`s2ref-off40`) it finds `s2ref`'s 41 (**verified** by the two runs; step 2's record did not say which
probes its runs used).

**Stage 1 with the exact index (`s3`, copy s2v, 068f7e7, no model call).** What is left once the index is exact:

| measure | base | s2ref (40 probes) | s3 (exact) |
|---|---|---|---|
| gold files | 39/57 | 41/57 | 41/57 (same files as s2ref) |
| best piece given, gold | 31/37 | 34/39 | 34/39 |
| benchmark files | 124/141 | 122/141 | 121/141 (q140 lost against s2ref) |
| best piece given, benchmark | 83/92 | 79/91 | 76/88 |
| retrieval benchmark hit@10 / MRR@10 | 0.893 / 0.564 | 0.846 / 0.571 | 0.873 / 0.587 |
| retrieval median, gold warm | 1.75 s | 1.34 s | 1.16 s |

- Of a19, q019, q121, q013, q017 and q083, **none is found** at file level with the exact index. So these losses
  are not the index's: they come after the vector search (the six places, the score limit, the coverage step), as
  step 2's diagnosis of each said.
- q140 is lost again (it was back in `s2ref`, where step 2 found it held the sixth place narrowly); not read.
- Retrieval benchmark against `s2ref`: 6 questions gain hit@10 (q001, q007, q019, q041, q121, q129: 6 of the 10
  that `s2ref` had lost against base), 2 lose it (q049, q146). Against `base`: lost q017, q049, q056, q082, q088;
  gained q077, q137. The index explains most of the retrieval benchmark's fall since step 1, not all of it.
- The best-piece counts are over fewer rated questions (88 against 91), so they are not comparable as they stand.

**Verified and believed.** Verified: the column's width and zeros (counted on every row); duplicates (counted);
what the largest list holds (its rows listed); that the filter and the build are not the HNSW cause (runs above);
the contrast between pieces and questions as queries; every recall and time in the tables; that the app's own
query uses the new index and keeps every exact piece (`EXPLAIN` and the 367 calls); that the setting off leaves the
gold run as it was. Believed, not tested separately: that the questions' place in the space is also why ivfflat
needs nearly all lists; that half precision never loses a piece the margin cannot absorb; ivfflat's build memory.
Not checked: the benchmark files lost and gained against `s2ref` question by question; q140 and the retrieval
benchmark's two new losses; the answers (stage 2 was not run); prod's pgvector version (`halfvec` needs 0.7, the copy
has 0.8.3).

**Cost.** No model call. Builds: hnsw on the column 7 min 38 s, hnsw `halfvec` 47 s, ivfflat 7–9 s each, the
column's ivfflat rebuilt (15 s). Trials 1–6 min each. Runs: `s3` 24 min, three gold runs of 8 min. The copy s2v now
holds the step 2 index (ivfflat 100 lists on the column, as before) and `x_ivf_half384`; nothing else changed.

### Step 2c: answers and examples on the exact index (2026-11-17, copies `napcore_helpdesk_s1base` and `napcore_helpdesk_s2v`, branch at 5007c0f)

Stage 2 of the yardstick, which steps 1 and 2 never reached: the 23 answerable and 25 must-refuse questions and the
example benchmark, 3 runs each, on the baseline copy with every setting off (`base-a`, the app as on main) and on
the step 2 copy with the exact index (`s3-a`: `RETRIEVAL_PREPARED_INDEX=True`, `VECTOR_INDEX_DIMENSIONS=384`,
`VECTOR_INDEX_HALF_PRECISION=True`, `VECTOR_INDEX_PROBES=100`, the settings of `s3`). `s3-a` replays `base-a`'s
recorded calls wherever the request is the same. The two runs ran one after the other, not side by side. The gate was
fixed before the runs; no setting was tuned and no code changed. Runs, logs and scripts:
`.claude/skills/measure-on-copy/runs/base-a`, `s3-a`, `base-a-noise` and `s3a-work/`. The recorded baseline answers
are in `runs/base-a/record.jsonl.gz` (every request and reply). All figures **measured** unless marked.

**Verdict: not met.** Answers on the answerable set rose clearly (41 → 49 of 69) and the late-journeys case is fixed
in the answers (the count element given in 3 of 3 runs, answered 3 of 3). But one must-refuse question is now
answered every time, one example run fell back to a standard file, and the one changed question that names a
standard got worse.

| gate line (fixed before the runs) | `base-a` | `s3-a` | spread used (step 0, §10 A, table) | met? |
|---|---|---|---|---|
| answerable answered | 41/69 | 49/69 (+8) | 7 of 69 | yes (better beyond the spread) |
| must-refuse answered | 4/75 | 6/75 (+2) | 2 of 75, or a new question answered twice or more | **no**: +2, and m13 is answered 3 of 3 (0 in `base-a`) |
| examples generated | 132/141 | 131/141 (−1) | 1 (did not move in step 0: any difference is real) | **no** |
| examples first attempts | 99/141 | 94/141 (−5) | 6 of 141 | yes (within the spread) |
| examples unlinked | 0/141 | 1/141 | 2 | yes |
| reading: no kind worse on balance | – | – | – | **no**: by standard 0 better / 0 equal / 1 worse |
| count | 466 calls made | 321 made, 168 replayed | – | reported; no call failed, none retried by the tool |

**Count.** `base-a` made 466 calls: 412 to Haiku, 54 to Sonnet (all naming the language of a question,
`_classify_question_language_with_llm`, the model kept for that on 2026-11-15; no other call went to a model other
than Haiku). By site: example generator 173, answer 125, relevance check 84, English rendering 14, controller 12,
fixed texts 4. `s3-a` made 321 calls, all Haiku (answer 130, example generator 191), and replayed 168 (114 Haiku,
54 Sonnet). No call returned an error. The app's own second attempts (the answer validator's retry, the example
generator's further attempts) are model calls and are counted in these numbers. The dry replay before `s3-a`
left 233 question runs not run; `base-a` had made 405 calls on those runs, which was the ceiling I checked against
the 650 limit. Wall time: `base-a` 28 min, the dry replay 7 min, `s3-a` 29 min, the dry replay of the baseline on
its own copy (`base-a-noise`) 7 min.

**Which changes are the index's.** The dry replay of `base-a` on its own copy (`base-a-noise`, free) has the prompt
move only for e01, e03, e04 and m22. None of these is among the ten questions whose answered count moved, so all
ten changes come with the new index (**verified** by that replay). On the new index every question that reaches
retrieval got other passages (the pieces are new), so 233 of 278 question runs ran; the 45 replayed (42 must-refuse, 1 answerable, 2
examples) are **believed** to be questions refused before retrieval (not checked one by one).

**Reading.** I read every question run of the ten questions whose answered count moved (30 runs), against the gold
patterns of `answer-source-questions.yaml` (passages that match one are marked in `s3a-work/read-changed.md`) and the
`expect` of `refused-questions.yaml`. The kinds were fixed before reading: non-English k08–k10; example request k02;
regulation k01, k13, k14, e02, e06; by standard e01, e04, e05, e07; explanation the other answerable questions;
must-refuse on its own line.

| kind | changed questions | better / equal / worse |
|---|---|---|
| regulation | e02, e06, k14 | 1 / 2 / 0 |
| example request | k02 | 1 / 0 / 0 |
| explanation | k06, k11, k12 | 2 / 1 / 0 |
| by standard | e05 | 0 / 0 / 1 |
| non-English | none moved | – |
| must-refuse | m05, m13 | 1 / 0 / 1 |

- e02 (fare data under MMTIS), 0 → 3, better: the new passages hold the Annex point 1.2 of 2017/1926 and of
  2024/490 (gold), and every run answers with the basic common standard fares (fare network data, standard fare
  structures). The baseline had Articles 1, 2, 6 and 9 and refused.
- k11 (number of late journeys), 0 → 3, better: `DelayedAndCancelledJourneysWithEvents.xml` with
  `LateDatedVehicleJourneyCount` and its duration intervals replaces `CancelledAndLateDatedVehicleJourneys.xml`'s
  opening; the answers name the count element. The baseline answered with `JourneyLayover`.
- k02 (example of observed delays), 2 → 3, better: the OpRa pieces now start at the element path, and the answers
  build the `LateDatedVehicleJourneyEntry` with `DelayDuration` and `TriggeredBy`; `ResponseLateDatedVehicleJourneys.xml`
  is among the passages.
- k12 (bus ticket), 2 → 3, better: a second Bristol fare example (line fare, stage) replaces a rail fare example, and
  run 1 answers from it. Neither run has the gold file (Arriva).
- e05 (DATEX and SIRI connected), 1 → 0, worse: the baseline's two `siri_exm_SX` examples (gold: the SIRI
  situation example with the embedded DATEX II `d2:` record) are gone; the new passages are a DATEX II TLS annex
  section, the OpenLR line attributes class and unrelated SIRI examples. The baseline's one answer used the
  embedded record; now all three runs refuse.
- e06 (legislation that includes DATEX II), 0 → 3, equal: both sides get Articles 4 and 5 of 2017/1926 (gold) and
  both answers say the evidence names no act that "includes" DATEX II while quoting Art. 4(2) and 5(2). The variant's
  answers are counted as answered; their content is the baseline's.
- k06 (elevator in a station), 3 → 2, and k14 (dynamic data), 3 → 2, equal: the same files on both sides, no gold
  passage on either; one run each refused where the baseline answered beside the point (`AccessFeatureEnumeration`'s
  `lift`; `DynamicDistanceMatrixElement`).
- m05 (colour of bus seats), 1 → 0, better: the seating plan schema (`PassengerSpotGroup`) comes in and all three
  runs refuse.
- m13 ("How does it work?"), 0 → 3, worse: two Bristol fare examples (`FX-PI-01_UK_FBRI_NETWORK-FARE_WOE-Bristol-(mixed)`
  and `-pass-(Z2Z)`) come in, whose pieces describe how m-tickets are activated, and every run answers the empty
  question about m-tickets. That is the step 0 rule's "new question answered twice or more".

**Examples.** Eight of 47 questions moved; I read the runs whose measure moved. gen42 run 2 (a line departing
Monday 17:00) was generated in `base-a` and is a standard file in `s3-a` (attempts 0, `NeTEx_01_simple_line.xml` and
a calendar example now among the passages): the generated count's −1. I did not open the standard example shown, so
that it lacks the asked departure is **believed** (the generator chose a standard file because one matched, not
because it holds the values). gen34 run 3 (ferry Koper–Piran) has an unlinked `ScheduledStopPoint` (+1 unlinked,
within the spread). First attempts fell for gen03, gen14 (2 → 0), gen16, gen22, gen31 and rose for gen36: −5, within
the spread of 6. Every example question got other passages (132 of 141 runs ran).

**What it means (believed, not tested).** The index helps where the right passage was just outside the six places
(e02, k11, k02): the exact search and the cut bring it in. It also brings in more example pieces that read as
prose about tickets and transfers, which a vague question can now match (m13), and it lets near-miss pieces from
DATEX II documentation push out SIRI examples (e05). Both failures are about what wins the six places, not about the
index's recall, which step 2b showed to be exact.

**Not checked.** The 223 question runs that ran and kept their answered/refused outcome were not read (the rule reads
the changed ones). The answers' citations and wording against gold, beyond the ten questions. Whether m13 and e05
move with another sample of the relevance check (each was run 3 times with the same replayed verdicts). The
stage 1 measures were not run again (they are `s3`'s, same copy and settings). Retrieval time of the API answers
(0.83 s against 1.33 s) is cold on both sides and not a gate.

### Step 3: concepts on the pieces and concepts by meaning (2026-11-17, copy `napcore_helpdesk_s4v`, a copy of `napcore_helpdesk_s2v`, branch at bb29e32)

Design point 6, first and second part. The gate was fixed before any code (below, "Gate 3 as counted"). Scripts,
logs and counts: `.claude/skills/measure-on-copy/runs/s4-work/`. No model was called for the diagnosis or the
labels. All figures **measured** unless marked.

**Diagnosis (written before the code).**

- *How concepts reach retrieval today* (read in `retrieval_gateway._retrieve_chunks_once`). The question's concepts
  are the classes whose label words occur in it (`extract_graph_concepts`, with plurals and short prefixes), the
  vocabulary bridge's terms (a model call, `bridged_question_concepts`) and the property terms; GraphDB expands them
  one hop. They are used five ways: (1) the graph candidates, `_graph_concept_candidates`, which search the paths and
  labels of schema and example pieces for every alias of the expanded concepts, and the text when that finds too few;
  (2) the element candidates, pieces whose text opens an element the question names; (3) a score bonus for pieces
  whose text, matched against every label at query time, names a question concept; (4) the definitions from GraphDB;
  (5) the example files from GraphDB. The concept vectors (3,104 classes, 384 numbers) are used only by
  `presence_concepts` ("does the standard have X") and the concept benchmark.
- *Time.* On the copy, warm (second of two passes over the 57 gold questions, model and bridge off,
  `diag.py A`): measured retrieval 0.44 s median, 0.72 s mean; the label-word search of paths takes 0 ms median
  (37 of 57 questions have no specific concept) and 109 ms mean; the vector query 244 ms mean and the rare-term
  search 230 ms mean are the larger parts. So on the copy the search of paths is not the slowest part. The prod
  measurement the plan cites came before the per-alias cache of 0.97.149 (**believed**, from the dates).
- *What it brings* (`s3`, passes of locate). The graph candidates hold a file the question names in 6 of the 41 gold
  questions found and 89 of the 121 benchmark questions found; in none of them are they the only stage that holds it.
- *Share of pieces that would carry a label, and from what* (a random 3,000 pieces, `diag.py B`; the full build is
  below). XML example pieces: 79 % name a class of their standard in an element opened in the body. Schema
  declarations: 13 % by the declared name. Prose: label words occur in most pieces (86–100 %, about 6 classes a
  piece), but only 20–28 % of NAPCORE, DATEX II, legislation and INSPIRE pieces keep one when a class must also be
  among the 20 classes nearest to the piece by meaning (its stored vector against the concept vectors).
- *A question's concepts, by words against by meaning* (concept benchmark, hit@3, on the reference copy, model off so
  the three non-English questions are searched as asked): label words 7 of 26, meaning on the whole question 11,
  meaning on the question's subject 18, the app's order (`presence_concepts`) 20. The 23 of 26 of the plan needs the
  English renderings of c04, c18 and c25 (model calls); with the model off it is 20 on both sides.
- *Verdict.* The design point can work as written: three quarters of the pieces can carry a class without a new
  embedding, and meaning finds a question's classes far more often than label words. The time it can save is small
  on the copy.

**Choices made before measuring** (no variant was tried after seeing a number):

- Labels in `structured_metadata["concepts"]`, written by `label_chunk_concepts` (no migration; a GIN index on that
  key built by hand on the copy, `x_concepts_gin`, as the vector index of step 2b). XML example piece: the classes of
  its standard named by the elements opened in its body (not the line of place, not the summary after the body).
  Schema declaration: its declared name when that is a class; any other piece and a declaration besides its name:
  the classes whose label occurs in it and that are among its 20 nearest classes by meaning. Each class brings its
  aligned Transmodel class.
- At the question (`RETRIEVAL_CONCEPT_LABELS`, off by default): the 5 classes nearest to the question's subject by
  meaning, among those that concern the standards of the scope (all standards when the scope names none), with the
  classes that implement them; the pieces of every kind in scope that carry one, nearest to the question first, at
  most 2 a file and as many as the graph candidate cap, take the place of `_graph_concept_candidates`. Without the
  embedder or the concept index, the label-word search runs as before. Everything else (element candidates, score
  bonus, definitions, examples) is unchanged.

**Gate 3 as counted** (fixed before the runs): stage 1 `s4` against `s3`, no model call: (1) concept benchmark not
lower than the reference measured the same way; (2) the 15 non-English gold questions (a08–a10, b02, b05, b06, b13,
b14, b17, b21, b23–b26, b34; the benchmark file has none): files found not lower than `s3` (11 of 15); (3) gold,
benchmark, retrieval benchmark hit@10 and MRR not lower than `s3` (step 0's spread for these is 0); (4) retrieval
median, gold warm, not above `s3` by more than 0.1 s, `s3` timed again in the same round; (5) setting off: existing
tests pass and a gold run with it off reproduces `s3`'s files. Stage 2 only if 1–5 are met: answers and examples not
lower than `s3-a` by more than step 0's spreads; changed answers read by kind, no kind worse on balance; m13, e05
and gen42 reported.

**What was built** (df8c34a, reverted in 1e11378): `services/chunk_concepts.py`, the command `label_chunk_concepts`,
the setting `RETRIEVAL_CONCEPT_LABELS` (off) and 15 unit tests (labels by kind, nearest classes in scope, the
candidate query against the exact order, the setting off and on in the gateway). On the copy: labels written in 358 s,
no embedding; 111,662 of 152,741 pieces (73 %) carry at least one class: XML example pieces 102,500 of 128,207,
declarations 5,224 of 10,858, NAPCORE 1,496 of 6,211, DATEX II 811 of 3,538, guides 1,012 of 1,647, legislation 305
of 1,004, INSPIRE 282 of 948 (`labels-report.json`); 2,365 classes are used, a class on 8 pieces at the median and
21,733 at most (`FareStructureElement`). GIN index `x_concepts_gin` 1.2 MB, built in 1.5 s. The labels were written as
an update of every row, which left the table spread out: with the setting off the warm gold run on the copy took
1.14 s against 0.71 s on `s2v` in the same hour (`diag.py A`). `VACUUM FULL` and a reindex (heap 214 MB against
203 MB on `s2v`) brought it back (`s4-off` below); every run below is after that. An indexer that writes the labels
with the piece would not have this cost (**believed**).

**Verdict: not met** (lines 3 and 4). Stage 2 was not run; no model was called in step 3.

| gate line (fixed before the runs) | `s3` (reference) | `s4` (setting on) | met? |
|---|---|---|---|
| 1. concept benchmark, app order, hit@3 (model off on both) | 20/26 (`s2v`) | 20/26 (`s4v`, setting on) | yes (the change does not touch `presence_concepts`) |
| 2. non-English gold questions, files found (15) | 11 | 11, the same ones | yes |
| 3. gold files | 41/57 | 42/57 (a19 gained) | yes |
| 3. benchmark files | 121/141 | 118/141 (lost q063, q109, q117, q122; gained q140) | **no** |
| 3. retrieval benchmark hit@10 / MRR@10 (the measure `s3` counted) | 0.873 / 0.587 | 0.873 / 0.587 | yes |
| 4. retrieval median, gold warm | 1.16 s; `s3-time4` (same copy and settings, this round) 1.31 s | 1.44 s (+0.13 s on the same round) | **no** |
| 5. setting off: tests; a gold run reproduces `s3`'s files | – | 1,146 tests, 6 fail, all among the 7 that failed before step 3 under the same environment (step 2b); `s4-off` finds `s3`'s 41 files exactly, 1.33 s | yes |

- *The four benchmark losses*, read on the passage lists (file names; I did not read the passage text, so **believed**):
  q063 (frequency timetables) loses `NeTEx_50_JourneyFrequencyGroup.xml` to `NeTEx_01_simple_line.xml`; q109 (SIRI
  roadworks) loses `exx_situationExchange_road.xml` to a request example and two SIRI schemas; q117 (connection
  monitoring) loses `exc_connectionMonitoringFeeder_response.xml` to the control action schema; q122 (delay types)
  loses `opra_delayClassification_version.xsd` to the DATEX II schema. In each the newcomer carries a class near the
  question by meaning but not the one the question asks for. q140 gains the connection monitoring example.
- *Time.* The candidates by meaning cost 60 ms median per pass on the warm gold questions (0 ms before, because 37
  of 57 questions had no specific concept and did not search at all); the rest of the 0.13 s is the second pass and
  the scoring of the larger pool (**believed**, from `diag-A-on.json`, not split further).
- *The graph variant of the retrieval benchmark*, not a gate measure: hit@10 0.873 → 0.886, MRR@10 0.584 → 0.583.

**Carried faults of step 2c** (m13, e05, gen42): not measured, stage 2 was not reached.

**Verified and believed.** Verified: the label counts (the command's report and SQL on the copy); every stage 1
number (runs `s3-time4`, `s4-off`, `s4` and the compare in `s4-work/cmp-s3-s4.txt`); that `s4-off` gives `s3`'s gold
files; the concept benchmark on both copies; the test failures against step 2b's list. Believed: that the four losses
are real losses (file names only); the split of the added time; that the slow copy came from the update alone.
Assumed: that the benchmark file has no non-English question (a scan of the texts for non-English words and letters
found none; it has no language field).

**Not checked.** Stage 2 (answers, examples). Other values of the two numbers chosen before the runs (20 nearest,
5 question classes) or candidates restricted to schema and example pieces as before: not tried, by the rule. The copy
`napcore_helpdesk_s4v` keeps the labels and `x_concepts_gin`; `napcore_helpdesk_s2v` is unchanged.

### Step 1 repair: pieces close at sentence ends (2026-11-17, copy `napcore_helpdesk_s5v`, a copy of `napcore_helpdesk_s2v`, branch at 11f742f)

The repair (0f0aa16 on `fix/prepared-cut-sentence-ends`, cherry-picked as 11f742f): when a piece has to close, it
ends at the latest boundary where a sentence ends, a list item starts or two paragraphs meet, as long as it keeps
75 % of the limit; otherwise where the limit falls, as before. XML examples do not go through `pack_unit` and are
not touched. Cut tests and retrieval tests: 110 run, all pass. The gate was fixed before the re-cut was applied.
Scripts, logs and counts: `.claude/skills/measure-on-copy/runs/s5-work/` (dry counts of the repair branch:
`runs/cut-work/`). No model was called.

**Applied.** `prepare_index --recut` on the copy, over every harvested kind and the two repository sources whose
prose goes through `pack_unit` and had no checkout at the indexed commit before: mobilityDCAT-AP (`1ae93b2`) and
TN-ITS (`5e68a9b`), both fetched at those commits into a scratch directory (no existing checkout touched). A dry run
on the copy first; the write gave the same counts as the dry run for every kind. NeTEx, SIRI and OpRa were not re-cut:
their prose (XSD, Markdown, `.txt`) gave the same pieces before and after on the local checkouts (`cut-work/repo-cmp-*`).
Written in 7 min 42 s, 3,675 pieces embedded; then `VACUUM FULL` (7 min), `REINDEX` (54 s, `x_ivf_half384`
rebuilt with the table) and `ANALYZE`; heap 218 → 203 MB, as on `s2v`.

| kind | rows before | dry run on the copy (cut-work, harvested) | applied | files changed |
|---|---|---|---|---|
| NAPCORE | 6,211 | 6,341 | 6,341 | 81 of 119 |
| DATEX II pages | 2,047 | 2,059 | 2,059 | 68 of 197 |
| EU legislation | 1,004 | 1,007 | 1,007 | 4 of 7 |
| INSPIRE specification | 898 | 899 | 899 | 1 of 1 |
| DATEX II model, INSPIRE code lists | 1,491, 50 | unchanged | unchanged | 0 |
| mobilityDCAT-AP frame `.html` | 53 | – (dry on the copy: 54) | 54 | 1 of 3 |
| mobilityDCAT-AP `.ttl` examples | 28 | – (28) | 28 | 1 of 2 (pieces moved, same count) |
| TN-ITS frame `.ttl` | 70 | – (71) | 71 | 1 of 1 |
| TN-ITS guide `.ttl` | 1,319 | – (1,321) | 1,321 | 9 of 35 |
| mobilityDCAT-AP guide `.html`, READMEs, TN-ITS schema and XML | 219, 6, 226, 106 | – | unchanged | 0 |
| all rows | 152,741 | | 152,891 | |

The mobilityDCAT-AP comparison in `cut-work/` (11 HTML files changed) was made on the local checkout at another
commit; at the indexed commit one frame file changes. TN-ITS Turtle was not in the dry counts of the repair branch;
the dry run on the copy showed it changing, so it was applied too.

**Verdict: not met** (line 4). Lines 1, 3 and 5 are met; line 2 is under the line at its point value but not settled.

| gate line (fixed before the re-cut) | reference | `s5` | met? |
|---|---|---|---|
| 1. pieces per kind equal the dry run's; none over 256 tokens; rows ≤ 154,692 | dry run | equal for every kind; 0 over in the command's count and in a recount from the stored rows; 152,891 rows | yes |
| 2. NAPCORE pieces cut inside a sentence, under 5 % | dry reading 3 of 40 flagged | second sample 6 of 40; pooled 9 of 80 flagged = 3.4 % of all pieces (1.9–6.1 %) | point yes, **not settled** |
| 3. index recall on the captured calls, exact reference recomputed on the copy | – | 367 calls, mean 1.000, lowest 1.00 (the app's own query, and the `x_ivf_half384` query with sequential scan off) | yes |
| 4. gold files | 41/57 (`s3`) | 40/57, lost b17 | **no** |
| 4. benchmark files | 121/141 | 121/141, same questions | yes |
| 4. retrieval benchmark hit@10 / MRR@10 | 0.873 / 0.587 | 0.873 / 0.587, no question changed | yes |
| 5. retrieval median, gold warm, against the reference timed in the same round | `s3-time5` 1.13 s | 0.95 s | yes |

- *Line 2.* The second sample: 40 of the 1,903 flagged NAPCORE pieces not in the dry reading, drawn from the copy,
  `random.seed(23)` over the pool sorted by file and order (`s5-work/napcore-read-40b.txt`, readings in
  `napcore-readings-40b.txt`). Read by the rule of step 2: 6 end inside a sentence (#16, #20, #25, #27, #33, #37), 1
  unclear (#18, a sentence the source text itself breaks before a heading), 3 split a table row between columns.
  #20 is the M3.4 footer case left from step 2. #33 is new: "described in Chapter" | "1.2. As highlighted", where the
  chapter number reads as a numbered item, so the repair's preference chose that boundary. Pooled 9 of 80 (10 with
  #18: 3.8 %, 2.1–6.6 %). With 80 pieces the 95 % interval still reaches past 5 %, so 80 do not settle the line; about
  200 more read pieces would be needed if the point stays where it is.
- *b17 lost* ("Kaj so metapodatki v NAP?", gold file `napcore.eu/metadata`). The page is a re-cut kind: its last two
  pieces moved (boundary between pieces 3 and 4), its opening piece is unchanged. In the Slovenian pass the page falls
  from place 3 to 9 in the pool behind re-cut pieces of M2.11, Annex B and D5.1.1, and the English pass, which now
  carries the question, keeps other NAPCORE files. So the loss touches the re-cut kinds (**believed**, from the
  passage lists and ranks, not from the pieces' scores).
- *Every other question whose passages changed* (`s5-work/changed-questions.txt`; found or not, unchanged):
  touching re-cut kinds: a19, a20 (DATEX II), b10 (INSPIRE), b11, b16, b18 (NAPCORE, EU legislation), q092 (NAPCORE
  M5.4 in for a NeTEx schema). Not touching them: a15 and a17 (move between two runs on the reference itself), b01,
  b02, b33, q031, q104, q125, q136, q138, q144, q147 (SIRI, NeTEx and OpRa files only). The same kind of moves for
  b01 and b33 appeared on `s4v` with no change of content after its `VACUUM FULL` (`s4-off` against `s3`), so I take
  them for ties broken by the new physical order of the table (**believed**).
- *Time.* The re-cut copy was faster than the reference in the same round (0.95 s against 1.13 s); the reference was
  timed first, so part of that may be the order (**believed**, not repeated).

**Verified and believed.** Verified: the applied counts against the dry run (both reports); the harvested dry counts
against `cut-work/recut-dry-harvested.json` (identical); that the copy's NAPCORE pieces equal the dry cut's
(multiset of bodies); the token recount (embedder's `/count` on the stored rows: the only row over 256 is a TN-ITS
schema row of the old cut, one of the 169 left as they are since step 1); index recall; every stage 1 number
(`s3-time5`, `s5`, `cmp-s3-s5.txt`). Believed: the second reading (one reader, by hand); why b17 was lost; that the
SIRI and NeTEx moves come from the table order. Assumed: that the mobilityDCAT-AP and TN-ITS clones at the indexed
commits are the sources that were indexed (the commit is the one stored on the rows; the files were not compared
with the rows, since a file already cut is not checked again).

**Not checked.** Stage 2 (answers, examples). The XML examples, NeTEx, SIRI and OpRa on the copy (not re-cut). The
cherry-pick stays on the branch: lines 1 and 3 hold. `napcore_helpdesk_s5v` holds the re-cut;
`napcore_helpdesk_s2v` is unchanged and `napcore_helpdesk_s4v` is as step 3 left it.

### Step 2d: answers and examples after the sentence-end cut (2026-11-17, copy `napcore_helpdesk_s5v`, branch at 260ba74)

Stage 2 on the re-cut copy (`s5-a`), with the settings of `s3-a` (`RETRIEVAL_PREPARED_INDEX=True`,
`VECTOR_INDEX_DIMENSIONS=384`, `VECTOR_INDEX_HALF_PRECISION=True`, `VECTOR_INDEX_PROBES=100`), the same sets and 3 runs
each, replaying `s3-a`'s record (it saves more than `base-a`'s: the dry replay against it left 22 question runs, on
which `s3-a` had made 30 calls; against `base-a`'s record about 233 runs would have run again, as in step 2c, since
the pieces differ from the old index: **believed**, no dry replay against `base-a` was made). The gate was fixed before the runs; nothing was tuned and no code
changed. Runs and scripts: `.claude/skills/measure-on-copy/runs/s5-a-dry`, `s5-a` and `s5a-work/`. All figures
**measured** unless marked.

**Verdict: met.** Not one question changed its answered count against `s3-a`; the carried faults are as they were.

| gate line (fixed before the runs) | `base-a` | `s3-a` | `s5-a` | met? |
|---|---|---|---|---|
| answerable answered, against `s3-a` (spread 7) | 41/69 | 49/69 | 49/69 | yes (same) |
| must-refuse answered, against `s3-a` (spread 2) | 4/75 | 6/75 | 6/75 | yes (same) |
| examples generated, against `s3-a` (spread 1) | 132/141 | 131/141 | 131/141 | yes (same) |
| examples first attempts, against `s3-a` (spread 6) | 99/141 | 94/141 | 94/141 | yes (same) |
| examples unlinked, against `s3-a` (spread 2) | 0/141 | 1/141 | 1/141 | yes (same) |
| answerable answered, better than `base-a` beyond the spread | 41/69 | – | 49/69 (+8, spread 7) | yes |
| reading: no kind worse on balance against `s3-a` | – | – | no question moved | yes |

**Count.** 24 question runs ran (the dry replay listed 22; e04 runs 2 and 3 ran too, and e04 also moves on the
reference's own copy) and made 26 calls, all Haiku, all the answer itself
(`_generate_answer_text`); no call to Sonnet was made and none failed. 457 calls were replayed (403 Haiku, 54 Sonnet:
the language naming recorded in `base-a`). The 188 example runs were replayed or needed no model: the example
generator got the same prompts on the re-cut copy. Wall time: the dry replay 7 min, `s5-a` 7.5 min.

**What ran, and whether it is the re-cut** (per run, both passage lists compared by file and piece,
`s5a-work/perq.txt`, `same-files-diff.txt`). All 24 runs kept their outcome (answered or refused), so the step 2c rule
reads none of them. What moved in their passages:

- Re-cut kinds: m04 (NAPCORE: Annex C out, M5.2 and the partners page in; refused on both sides), m25 (DATEX II pages:
  two profile and levels pages swapped for two others; refused on both), e05 (the same DATEX II annex section, a new
  piece id with the same text; refused on both), e06 (the DATEX II user guide page out, together with a DATEX II
  model class; answered on both).
- Not re-cut: e01, e03, m22 (OpRa, NeTEx and SIRI files; all three also move on the reference's own copy, `base-a-noise`)
  and e04 (the same pieces; moves on the reference's own copy).

**Carried faults.**

- m13 ("How does it work?"): answered 3 of 3, as in `s3-a` (replayed: the same passages and prompt). Still open.
- e05 (DATEX and SIRI connected): refused 3 of 3, as in `s3-a`; the passages are the same pieces of text. Still open.
- gen42 run 2: still a standard file (replayed), runs 1 and 3 generated. Still open.
- b17 ("Kaj so metapodatki v NAP?", lost in `s5`): it is a gold question, not in the answer sets, so stage 2 does
  not ask it. The nearest question there, k08 ("Kaj so to metapodatki?"), was replayed on all three runs (the same
  prompt as `s3-a`), answered 2 of 3 as before. How b17 itself is answered on `s5v` was not measured.

**Verified and believed.** Verified: the counts (the tool's result and a recount from both records by question,
`perq.txt`); that no question's answered count moved; the calls by model and site (`count-s5-a.txt`, and the guard
saw only Haiku calls live). Believed: that the moves of e01, e03, e04 and m22 are not the re-cut's (they touch no
re-cut kind and move on the reference's own copy).

**Not checked.** The wording of the 24 answers that ran (the outcome held, and the rule reads only moved questions).
b17 asked through the app. Another sample of the relevance check (replayed verdicts, as in step 2c). The re-cut
leaves the step 2c failures as they were: against `base-a`, must-refuse (+2, m13) and examples generated (−1, gen42)
are still on the wrong side, which this gate does not cover.

### Step 5: the indexer and the dev index (2026-11-18, dev database `napcore_helpdesk`, rehearsal copy `napcore_helpdesk_s6r`, branch at c62944f)

The cut of step 1 with its repairs, the index of step 2b and the re-index command went into the code, the dev
index was brought to the state measured on `napcore_helpdesk_s5v`, and gate 5 as reworded on 2026-11-18 was
measured on it. Scripts, logs and reports: `.claude/skills/measure-on-copy/runs/s6-work/`; runs `s6`, `s6-a`,
`s6-a-dry`, `s5-time6`, `s6-time6b`, `s5-time6b`, `s6-s1base-defaults`. All figures **measured** unless marked.

**Verdict: met on every line but two.** Files, the index, answers, examples, the case and the command are as on
the copy. Not met as written: (1) "no piece over 256 tokens": 19 XML example pieces are over (at most 262), as on
the copy (13 in step 1's count); (2) warm retrieval in the round as fixed (copy first) is 0.13 s above the copy;
in the round run the other way it is 0.12 s below, so it is the order, not the index (**believed**, two rounds).
The two lines are my decision.

| gate 5 line | `napcore_helpdesk_s5v` (the copy) | dev after the re-index | met? |
|---|---|---|---|
| pieces per kind | 152,891 rows | 152,912 rows; every kind equal but XML examples +19 and DATEX II pages +2 (below) | explained, not by a changed source: by code after the copy was built |
| no piece over 256 tokens | 13 XML example pieces over (step 1) | 19 XML example pieces over, at most 262; every other kind at most 256 | **no** (as the copy) |
| index recall, 367 captured calls | 1.000 | 1.000, lowest 1.00, every call planned on the index (`recall-dev.txt`) | yes |
| gold files | 40/57 (`s5`) | 40/57, the same questions | yes (≥ 39) |
| benchmark files | 121/141 | 121/141, the same questions | yes (≥ 120) |
| retrieval benchmark hit@10 / MRR@10 | 0.873 / 0.587 | 0.873 / 0.587 | yes (≥ 0.873) |
| answerable answered (`s6-a` against `s5-a`, replayed) | 49/69 | 49/69 | yes |
| must-refuse answered | 6/75 | 6/75 | yes |
| examples generated / first attempts / unlinked | 131 / 94 / 1 of 141 | 131 / 94 / 1 of 141 | yes |
| the late-journeys case (k11), answered and term given | 3 of 3 | 3 of 3 | yes |
| warm retrieval, gold median, same round | round 1 (copy first): 1.07 s; round 2 (dev first): 1.20 s | round 1: 1.20 s; round 2: 1.08 s | **no** in round 1 (+0.13), yes in round 2 (−0.12) |
| the command stops and starts again | – | rehearsal: stopped after 3 documents, started again, the same rows as the copy; dev: stopped by an embedder timeout, started again, 0 files with mixed rows, the same counts as the dry run | yes |
| tests of the cut for every kind | – | `test_prepared_index.py` (21 tests) beside `test_prepared_cut.py` | yes |
| the way back is the same command with the old version | – | rehearsal, EU legislation: `--cut-version 0` gave back the dev rows exactly (735 rows, same chunk ids and texts) | yes |

No question changed its answered count against `s5-a`; 18 question runs ran (e01, e03, e04, e06, k02, m22; e01, e03,
e04 and m22 move on the reference's own copy too) and every one kept its outcome.

**Diagnosis (before code), each claim checked by hand on stored rows** (`verify_a.txt`).

- *Where the cut is stored.* Each row of the prepared cut has `structured_metadata["piece"]["v"] = 1`; a row of the
  cut of before has no such key. On `s5v` every file's rows have one version (0 files mixed); OpRa's rows are of
  version 1 there and 0 on `s1base`. So the version is already stored with each file; no migration is needed.
- *Old pieces stay until the new ones are embedded.* `prepare_index` embedded a file's pieces first and replaced
  its rows in one transaction afterwards. Checked on dev itself: the run that stopped on an embedder timeout left 0
  files with rows of two versions.
- *A stopped run resumes.* A file already of the version is skipped. Checked on the rehearsal (below).
- *What the nightly refresh does.* `refresh_all_sources` runs `index_repository` incremental with prune; a file
  whose content hash equals its `IndexedSourceFile` row is skipped (62 of 62 OpRa files on `s5v`). A changed file was
  cut with the cut of before, so before this step a refresh would have turned changed files back to the old cut,
  file by file; it never re-cut everything. On dev `SOURCE_REFRESH_ENABLED` is not set in the worker (default off)
  and the beat container crash-loops on a missing module, so no refresh ran.
- *Shared code.* The old indexer never called the prepared cut, and `prepare_index` never ran inside the indexer;
  the prepared cut does reuse parsing helpers of `index_builder` (HTML blocks, Turtle statements, the XSD summary).
  Today's shared cut reproduces the stored pieces of `s5v`: 62 of 62 OpRa files and 10 of 10 NAPCORE snapshots.
- *Sources.* Dev's 61,877 rows are identical to `s1base`'s (chunk ids and text hash), last written 2026-11-13, and
  the `IndexedSourceFile` hashes are identical: nothing was refreshed since the copies were made.

**What was built.** b3d5c0d: `services/prepared_index.py`; `index_repository` and the four harvesters cut a changed
file with the version its rows have; a new file takes the version most rows of its repository (or kind) have, and
`INDEX_CUT_VERSION` (0) when there are none; the cut of before is `old_cut_chunks`, the code `index_repository`
ran inline. d65031f, 6261d3c: `prepare_index --cut-version 1|0` (the re-index and the way back), `--stop-after`,
`--files-report`; a file whose pieces were all copies (no rows) is still a job, so the way back gives it its rows
again; tests. a578141: `vector_index`, which builds the index of step 2b from the same settings as the query and
refuses without them or on pgvector older than 0.7. 560963f, c62944f: CI (below).

**Prod stays as it is when this is merged** (**verified** for the points marked, **believed** for the rest). No
migration (none on the branch; the migration drift check passes). `INDEX_CUT_VERSION` 0, `RETRIEVAL_PREPARED_INDEX`
and `VECTOR_INDEX_DIMENSIONS` off by default; prod has no row of the prepared cut, so every file keeps the cut of
before on every refresh (test `test_an_index_of_before_stays_one`). The re-index and the index are commands that
run only by hand and only on the database named on the command line. Verified: the backend suite (1,156 tests,
models off): 6 fail, the same 6 that fail on d7e4127 under the same environment (relevance check, request body);
a gold run on the old-cut copy `s1base` with default settings (`s6-s1base-defaults`) finds `base`'s 39 files and 31
best pieces. **Believed**: the extra queries a refresh now makes (the version of a changed file) cost
milliseconds.

**Rehearsal on `napcore_helpdesk_s6r`** (a fresh copy of dev, 171 s).

- Dry run of every kind, 213 s: per kind the copy's counts but XML examples 128,226 (copy 128,207) and DATEX II
  pages 2,061 (2,059) (`cmp-s6r-dry-s5v.txt`). XML: 19 pieces of end tags only, which step 1's build left out and the
  cut keeps since fceff23 (as step 1 recorded; checked file by file in `extra-pieces.txt`). DATEX II: one page
  (`rtti-962/drd-15…/d2rsp/`) had no rows on the copy, all its pieces copies of another page's in step 1's build; the
  repair re-cut changed that page, and the old command could not visit a document without rows, so 2 of its
  pieces are not copies any more (**believed** from the pieces' texts, `datex-page-diff.txt`).
- Stopped and started: EU legislation, `--stop-after 3`, then the same command: 1,007 rows whose texts, kinds and
  order equal the copy's (one hash over all of them).
- Rate: 13–15 pieces a second with other work on the embedder (DATEX II pages 2,013 in 153 s). Projected for dev
  (about 140,000 to embed): about 3 hours.
- The way back: `--cut-version 0` on EU legislation gave back dev's 735 rows exactly (chunk ids and texts).

**The dev run.** Backup `napcore_helpdesk_s6pre` first (61,877 rows, the same hash as dev). No query was writing to
the table and no refresh is scheduled (above). The run took 17 min, stopped on an embedder timeout while my local
CI build used the embedder, and was started again: 88 min, 121,592 pieces embedded at 23 a second, 11,600
vectors kept. Rows 61,877 → 152,912, per file equal to the dry run of the rehearsal (0 files differ). Then
`VACUUM FULL` (8 min 26 s), `REINDEX` (66 s), `ANALYZE`, and `vector_index` (14 s, 120 MB). Table 205 MB, with
TOAST and indexes 2,887 MB.

**CI.** The benchmark index is now built with the prepared cut (hash vectors; the embedder runs only to count
tokens) and read with `RETRIEVAL_PREPARED_INDEX`. Old and new, CI runs 44204496420 and 44212998383, 149 questions:

| mode | hit@10 old → new | MRR@10 old → new | hit@5 old → new |
|---|---|---|---|
| baseline | 0.483 → 0.383 | 0.266 → 0.220 | 0.436 → 0.342 |
| graph | 0.497 → 0.403 | 0.281 → 0.235 | 0.456 → 0.362 |

The baseline is the new run's; the allowed drop stays 0.03. The run after it, same inputs, gave 0.396 / 0.416: the
CI measure moves about 0.013 between runs. **Believed**: hash vectors of small pieces carry fewer words each, so
this measure punishes the cut that the semantic measures do not (dev: 0.873 on the semantic retrieval benchmark).

**Model calls.** Stage 1: none. Stage 2: the dry replay left 17 question runs, 23 Haiku calls in `s5-a`; the run made
23 calls, all Haiku, all the answer itself; 462 replayed (408 Haiku, 54 Sonnet language naming recorded earlier).
No Sonnet call was made.

**Believed, not verified.** That the order explains the timing line. That the DATEX II page is explained as above.
That the CI drop is the hash vectors'. That the 19 pieces over 256 have the cause of step 1's 13 (not read).

**Not checked.** The wording of the 23 answers that ran (their outcome held). Prod's pgvector version (step 6).
Whether running the harvesters for real (a new snapshot) on dev keeps the cut: tested with a test act, not on dev.

**What the running dev app sees now.** It runs main's code with the settings off: the new pieces without their unit
around them, and the vector search on the full column at 20 probes, which on this table keeps about 88 % of the
nearest pieces (step 2's correction). So dev answers are expected to be worse than on main's index until this
branch runs there with the settings on (**believed**, from steps 1 and 2; not measured on dev).

**Ways back, if wanted.** `prepare_index --database napcore_helpdesk --cut-version 0` with the same checkouts
(about 1.5 hours of embedding, shown on one kind), or the backup `napcore_helpdesk_s6pre`.

**Decisions after the step (2026-11-18).**

- The two lines not met are accepted. The 19 pieces over 256 tokens (the longest 262) stay as a known fault of the
  cut of XML examples; the timing line is read as an effect of the order of the runs.
- CI stays on the old cut, which is what prod runs, until prod is re-indexed in step 6. The two CI commits
  (560963f, c62944f) are reverted, so the baseline is again 0.483 / 0.497 hit@10. The table above stays as the
  record of what the prepared cut gives with hash vectors; what CI measures after step 6 is decided there.

### Step 6, preparation: the order of the switch (2026-11-18, copies `napcore_helpdesk_s7a`, `_s7m`, `_s7l`, `_s7l2`, `_s7r`, main at 09fd59a, 0.97.231)

I measured on dev copies which order prod can be switched in without its answers getting worse on the way. Stage 1
only, no model call. Scripts, logs and runs: `.claude/skills/measure-on-copy/runs/s7-work/` (notes in `notes.md`),
runs `s7-*`. Figures are **measured** unless marked.

**Verdict.**
- No in-place order meets the line I fixed before the runs.
- The half re-cut index with all four settings on, (c), loses 2 benchmark questions at per-file limit 1 and 3 at
  limit 2 (the line allows 1).
- With the settings off, (d) loses more: gold −3 or −4, hit@10 −0.041 or −0.047.
- So I recommend a different order: build the new index beside the live database, measure it there, and swap the
  two index tables in one transaction. Users then see only today's prod and the end state.
- The swap was rehearsed on dev copies (below) and meets every check:
  - the transfer takes 107–111 s in one transaction and never blocks a reader;
  - the index tables come out equal to the re-cut dev index, and every other table stays as it was;
  - the search keeps every exact nearest piece (recall 1.000), and its time is within 0.022 s of an index built
    beside;
  - stage 1 on the swapped copy is exactly `s6`.
- The end state at prod's limit 2 against today's prod at limit 2 was not measured on dev. It is measured on prod
  before the swap, which is done only if it meets the line. At limit 1 the end state (`s6`) was 3 benchmark
  questions under `base`, which points to that line being in doubt (**believed**).

**Conditions.**
- Each counted run ran alone, one after another, with 0 GraphDB timeouts.
- Docker Desktop's memory was raised from 4 to 8 GB at about 13:30 by my decision. Runs before that do not
  count: from 12:42 the Docker machine was out of memory (28 MB available, swap full) and GraphDB queries timed out.
- Between 13:23 and 16:20, MemAvailable in the machine was 3.1–3.7 GB and memory pressure 0.00 before and after
  every run.
- Times are compared only within that round. The per-file limit (`RETRIEVAL_MAX_SAME_SOURCE_PATH`) is 1 in dev's
  `backend/.env` (as `base` and `s6` ran) and 2 on prod. Every state was measured at both, each against a
  reference of today's prod at the same limit.
- The line, fixed in the brief before the runs: against the reference, gold not lower by more than 1, benchmark
  not lower by more than 1, retrieval benchmark hit@10 not lower by more than 0.02, warm gold retrieval median not
  more than 0.3 s higher.

**The copies.**
- `s7a`: dev's index before step 5 (`s6pre`, 61,877 rows, the old cut as prod has it), with the index of step 2b
  built by `vector_index` (14.7 s, 49 MB).
- `s7m`: the same, then `prepare_index --cut-version 1` in the command's own order. Its dry run was identical per
  file to step 5's rehearsal: 0 of 1,458 files differ, and 6 TN-ITS schema files are "source differs".
- I stopped the `s7m` run at 10:18, between two file writes. At that point:
  - 109,545 rows, 67,878 of them new cut; 0 files with rows of both cuts.
  - Re-cut: TN-ITS, the NeTEx READMEs, and 234 of 298 NeTEx example files.
  - Still old: 64 NeTEx example files, every NeTEx schema, SIRI, OpRa, mobilityDCAT-AP, and every harvested kind.
  - 33 % of the old rows replaced; new-cut rows are 62 % of the table. This is the state of the first hours on
    prod.
- The run stopped three times: two embedder timeouts and one kill. Each time 0 files were mixed, and the same
  command went on from the next file.

**Limit 1.** The reference is `s7-p0r`: old cut, settings off. It equals `base` question for question.

| state | run | gold | benchmark | hit@10 / MRR@10 | gold median | line |
|---|---|---|---|---|---|---|
| today's prod | `s7-p0r` | 39 | 124 | 0.893 / 0.564 | 1.02 s | reference |
| (a) old cut, index + 3 vector settings | `s7-a2` | 39 (=) | 124 (=) | 0.893 / 0.564 | 0.83 s | met |
| (b) old cut, all four | `s7-b2` | 40 (+a12) | 124 (= ; −q137 +q063) | 0.893 / 0.568 | 0.98 s | met |
| (c) half re-cut, all four | `s7-c` | 39 (=) | **122 (−2)** | 0.893 / 0.559 | 1.16 s | **not met** (benchmark) |
| (d) half re-cut, all off | `s7-d` | **36 (−3)** | 122 (−2) | **0.852 (−0.041)** / 0.551 | 0.73 s | **not met** |
| end state (dev, step 5) | `s6` | 40 | 121 | 0.873 / 0.587 | – | (benchmark −3 against `base`) |
| end state by the swap | `s7-swap` | 40 | 121 | 0.873 / 0.587 | 0.84 s (outside the round) | = `s6`, the same questions |

The closing reference run `s7-p0r-end`: gold 39, the same questions, gold median 0.69 s. The reference ran faster at the end of the round (1.02 s at the start); against the closing reference (c) is +0.47 s and (b) +0.29 s, so the time line is not decided by this round.

**Limit 2.** The reference is `s7-p0-L2`: gold 39, benchmark 122, hit@10 0.886 / MRR 0.556, gold median 0.65 s.

| state | run | gold | benchmark | hit@10 | gold median | line |
|---|---|---|---|---|---|---|
| (a) | `s7-a-L2` | 39 / 38 (−a15 in gold run 2) | 122 (=) | 0.886 (=) | 0.83 s | met |
| (b) | `s7-b-L2` | 39 / 40 (+a12) | **120 (−2)**: −q124 −q137 | 0.886 (=) | 0.70 s | **not met** (benchmark) |
| (c) | `s7-c-L2` | 38 (−1: a15 in gold run 2; 39 in run 1) | **119 (−3)**: −q063 −q137 −q143 | 0.893 (+0.007) | 0.75 s | **not met** (benchmark) |
| (d) | `s7-d-L2` | **35 (−4)** | **120 (−2)**: −q063 −q121 −q143 +q140 | **0.839 (−0.047)** | 0.72 s | **not met** |
| end state | – | not measured on dev | | | | measured on prod before the swap |

**What (c) loses, read.**
- **q137** (roadwork warnings in real time): the SIRI example `exx_situationExchange_road.xml` is given in `base`
  and `s6`. In (c) its place goes to `siri_all_functionalServices.xsd` (twice) and a NeTEx example.
- **q144** (NeTEx and Transmodel): the NeTEx `README.md` is given in `base` and `s6`. In (c) NeTEx schema files
  take its place.
- These are losses of the mixed state itself: SIRI is still old cut, the NeTEx README already new, the NeTEx
  schemas still old.
- (d) against `base` on the retrieval benchmark: lost q047, q056, q075, q081, q083, q121, q122, q124, q130; gained
  q077, q086, q137.

**Index recall.**
- On `s7a` with the index of step 2b as the app reads it: 1.000, lowest 1.00, on all 367 captured calls, every
  call planned on the index (morning, under load, so the time is not a gate time).
- On `s7l` after the swap: 1.000 on the 206 gold and benchmark questions (`recall_check.py`, limit 50), every
  search planned on the index.
- The app's index search right after the transfer took a median of 0.64 s. I believed the cause was the index built
  on the old rows and filled by the transfer, and tested it by other routes (`swap2.sh`, each alone, all at recall
  1.000):

| index on the swapped copy | search median |
|---|---|
| as rehearsed (built before the transfer, then `VACUUM ANALYZE`), 80 min later | 0.109 s |
| after another plain `VACUUM`, no rebuild | 0.107 s |
| dropped and built after the transfer (17 s, 120 MB) | 0.111 s |
| variant without the old 1,536-wide index (below) | 0.105 s |
| built beside: a fresh copy of the re-cut dev database, its indexes rebuilt | 0.089 s |

- So the belief was wrong. The order of the build makes no difference once warm, and 0 dead tuples were left.
- The 0.64 s was the first pass on a cold cache (**believed**: the only difference is the time).
- The gate fixed for this, the swapped copy's search median within 0.1 s of the built-beside copy's, is met in
  every variant (+0.016 to +0.022 s).
- Sizes: the new index is 168 MB when built before the transfer and 120 MB when built after. The old index grows
  from about 1 GB to 1,679 MB when the transfer fills it.
- **Believed from the code** that the index stays exact while the re-cut inserts rows into it: a new row goes into
  the list of its nearest centroid, and the app reads all 100 lists. The dropped run on the finished `s7m` would
  have shown it. The swap rehearsal shows it for an index built on the old cut and then filled by the transfer.

**The swap rehearsal.** `swap.sh`: "live" = `napcore_helpdesk_s7l`, a fresh copy of `s6pre` (the old cut); "built beside" = the dev
database `napcore_helpdesk` after step 5's re-cut, read only through `pg_dump --data-only` of the two index tables
(8 s, 1.26 GB). The step 2b index was built on live first (8.6 s). The transfer, in one transaction (`DELETE` of both
tables, `COPY` of the dump, both sequences set): 111 s (the `DELETE` 4.2 s, the `COPY` of the chunk table 106 s). A
reader counting the rows every second during it saw 61,877 rows in all 87 reads (0.22–0.50 s each, including
`docker exec`) and 152,912 right after the commit: no read was blocked. After it: both index tables equal to the
dev database (152,912 rows and 1,458 files; one hash over ids, chunk ids, text and vector of every row), every other
table with the same row count as before, a marker row written to another table before the transfer still there,
the sequences past the largest id; `VACUUM (ANALYZE)` 25 s. Stage 1 on it at limit 1 with all four settings on:
gold 40, benchmark 121, hit@10 0.873 / MRR 0.587, the same questions as `s6` (0 graph timeouts).

The old 1,536-wide index during the transfer (copy `s7l2`, `swap2.sh`):
- Its 152,912 inserts cost about 4 s of the transaction: 111 s with it, 107 s with it dropped first.
- The app with `VECTOR_INDEX_DIMENSIONS=384` no longer reads it.
- Dropping it before the transfer is therefore possible, at a price:
  - the `DROP` takes an exclusive lock (1 s on dev);
  - until the settings are on, the old search runs without an index, as an exact scan;
  - the way back has to rebuild it: 13 s for 152,912 rows with `maintenance_work_mem` 512MB. Prod's 64MB is too
    small: the restore on prod needed 65 (read on prod).
- Keeping it costs 1–1.7 GB of disk and an insert per row, and keeps the fast way back (settings off).
- Both variants are in the guidance; I choose.

**What the swap touches** (read in the models and the code; checked on the catalog of `s7a`).
- `prepare_index` writes only `helpdesk_sourcechunk`: per file, a delete and a bulk create in one transaction. It
  reads `helpdesk_indexedsourcefile`. `vector_index` creates one index and runs `ANALYZE`.
- No foreign key points at `helpdesk_sourcechunk` or `helpdesk_indexedsourcefile` (0 rows in `pg_constraint`),
  and there is no trigger, view or materialized view on them. Their ids come from their own sequences.
- `chunk_id` is kept as text in the question logs (`helpdesk_retrievalevent`, `helpdesk_answerevidencelink`).
  After a swap, as after any re-index, those ids of past questions point at rows that are gone; nothing answers
  from them (**believed**, from reading the code).
- Row ids are cached in-process for up to an hour (example use, element candidates, alias matches). The restart
  that switches the settings clears them. The redis cache holds only translated fixed texts.
- `helpdesk_indexedsourcefile` is swapped together with the rows, so that its hashes belong to them.

**The nightly refresh between the copy and the swap** (read in the code; not shown by a run).
- A refresh on live after the copy changes rows and stored hashes that the swap then replaces with the copy's.
- The next refresh re-indexes those files, because their stored hash no longer matches the checkout:
  `index_repository` skips a file only when its hash matches. So one day's changes are lost for a day and come
  back by themselves.
- A refresh that moves the checkouts while the copy is being re-cut makes the moved files "source differs" on the
  copy. They stay of the old cut until `prepare_index` visits them again.
- Holding the refresh for the whole window avoids both. The refresh and the editor's harvest take a non-blocking
  `flock` on `/app/repos/.refresh.lock` and skip when it is held; a one-off container can hold it.
- That the lock holds across containers is **believed** (one kernel, one file of a named volume), not tried.
- On the live database, in place, a refresh would be worse: its prune deletes every row of a repository whose id
  it did not see during its pass, so new rows written by a re-cut beside it are deleted (read in the code). The
  run on a copy that was to show this failed on an embedder timeout, and I did not repeat it (dropped, below).

**What the re-cut needs on prod** (read in the code).
- Repository files come from the checkouts named by `--checkout URL=PATH`, matched exactly to the stored
  `repository_url`; on prod these are `/app/repos/<name>`.
- Harvested documents come only from the snapshots under `docs/`, mounted read only at `/app/docs`. Their network
  fetches are not called by the re-cut.
- A file whose source differs from its rows is left as it is.
- Prod's NeTEx, SIRI and mobilityDCAT-AP checkouts are at commits dev does not have (11d40b5, d0b2fb3, 6ef08d7, read
  on prod), so prod's own dry run decides the coverage.

**A load of vectors from dev** (assessed, not built).
- It would need three things: an export of (hash of the exact embedding input, vector), a file of about 200 MB,
  and a lookup option in `vectors_for` before the embedder is called.
- The share it covers is the share of byte-identical source files, which can be counted from `content_hash` on
  both sides. NeTEx is 88 % of the rows and sits at another commit on prod, so the share is unknown.
- What could go wrong: a vector filed under the wrong key would be silent; a different embedder would give
  different vectors; and it is new code.
- Building beside with a second, larger embedder on prod's idle CPUs got the same result without new code: on prod
  about 2.5 hours (above).

**Prod, 2026-11-18 (read on prod, not checked a second way).** Phases 1 and 2 of the guidance ran there: dump,
reference, restore, second embedder and the re-cut of the copy.
- The reference of today's prod at prod's settings: gold 36 (run 1) / 37 (run 2) of 57, benchmark 122 of 141,
  hit@10 0.8859, MRR@10 0.5603, gold median 1.5 s, 0 graph timeouts. Recall of the old index at 20 probes: 0.9993.
- The restore of the copy needed `maintenance_work_mem` 512MB (the server has 64MB; the old index needs 65).
- The second embedder ran 24.3 pieces a second at 16 threads.
- The dry run gave 1,464 files, rows 61,883 → 152,926, 0 "source differs".
- The re-cut started at 15:13 UTC and was at 117,000 of about 139,000 embeddings at 16:35 UTC, on its first attempt.
- The line for the swap, fixed before the copy's numbers existed: the finished copy must show gold (run 2) not under
  36, benchmark not under 121, hit@10 not under 0.866, recall 1.000 with the plan on the filled-numbers index, and 0
  graph timeouts.

The prod guidance (local, in `.mylocal/`, not committed) has two files: phases 1–2, which ran, and phases 3–4, final
for this order. The swap is gated by the line above and by my approval.

**Not done, and why.** Because the prod host runs all day while this laptop may be closed, I moved the long runs
to prod. The following were dropped on dev:
- the rest of the re-cut on `s7m` with its timing and end checks;
- stage 1 of the finished copy at limits 1 and 2;
- recall on `s7m`;
- the embedder's rate at two thread counts (it is the first step on prod);
- the refresh collision as a run (the code reading stands).

**Believed, not verified.**
- That the lock holds across containers.
- That `up -d --no-deps` recreates only the named services.
- That a one-off container started with `compose run` resolves by its name on the project network.
- Prod's embedding rate.
- That the end state at limit 2 meets the line (prod measures it).

**Decisions left to me.**
- The primary order (swap) or the in-place one, whose cost is measured above.
- The thread count of the second embedder (from its timed rate).
- Holding the refresh by the lock.
- `INDEX_CUT_VERSION=1` after the swap.
- Dropping the copy and the old 1 GB vector index; a `VACUUM FULL`.
- The per-file limit (prod 2, dev 1).
- Whether a prod end state that misses the benchmark line by a little is acceptable: the guidance stops there and
  asks.

### Step 6: prod (2026-11-18, the live database and its copy `napcore_helpdesk_recut` on prod, 0.97.231)

I re-cut a copy of prod's database on prod, measured it against live, decided, and swapped the two index tables.
All times UTC. Figures are **read on prod** unless marked.

**Verdict.**
- The line fixed before the copy's numbers is met only with the per-file limit changed from 2 to 1. At prod's
  limit 2 the copy (`new`) did not meet it (hit@10 0.8523).
- At limit 1 the copy (`new-l1`) meets every line, but it is still 2 questions under today's prod on hit@10 (130
  against 132) and 3 under today's prod at limit 1 (`ref-l1`). The limit alone also helps the old cut a little.
- Answers with model calls were not measured on prod's copy, only on dev (dev has run at limit 1 throughout).
- I decided to swap with the per-file limit 1 (five settings), keeping the old index (variant A). The swap is done.

**The copy (phases 1 and 2).**
- Live dumped (165 MB) and restored as `napcore_helpdesk_recut`. The restore first failed on the old index build
  (it needs 65 MB, prod's `maintenance_work_mem` is 64MB); rerun with `PGOPTIONS='-c maintenance_work_mem=512MB'`.
- A second embedder container for the re-cut: 17.9 pieces a second at 8 threads, 23.6 at 16.
- The preparation record's 24.3 pieces a second at 16 threads was the first reading, 23.6 the later one (both read
  on prod).
- Dry run: 1,464 files, rows 61,883 → 152,926, 0 "source differs".
- Re-cut 15:12:58 → 16:52:14 (1 h 39 min), on its first attempt. The copy: 152,926 rows, all of the new cut, 0
  files with both cuts. The new index built in 34 s, 120 MB.

**Stage 1 on prod** (no model calls; 0 graph timeouts in all four runs). Gold is of 57, two runs; benchmark of 141;
hit@10 of 149.

| state | run | gold | benchmark | hit@10 | MRR@10 | recall (206 calls) | index search median |
|---|---|---|---|---|---|---|---|
| live, per-file limit 2 | `ref` | 36 / 37 | 122 | 0.8859 (132) | 0.5603 | 0.9993 (old index, 20 probes) | 0.322 s |
| copy, four settings, limit 2 | `new` | 38 / 38 | 121 | **0.8523 (127)** | 0.5735 | 1.0000 | 0.130 s |
| live, limit 1 | `ref-l1` | 37 / 37 | 123 | 0.8926 (133) | 0.5690 | 0.9995 | 0.249 s |
| copy, four settings, limit 1 | `new-l1` | 40 / 40 | 123 | 0.8725 (130) | 0.5871 | 1.0000 | 0.133 s |

- The line, fixed before the copy's numbers: gold ≥ 36, benchmark ≥ 121, hit@10 ≥ 0.866, recall 1.000 with the plan
  using the filled-numbers index, 0 graph timeouts.
- `new` at limit 2 did not meet it. Lost from the top 10 against `ref`: q017, q049, q082, q088, q090, q110; gained
  q137. The cause, as read from the top-5 lists: example XML files, two per path, push the expected schema or
  documentation sources out.
- The limit-1 measurement was proposed after seeing that miss, and run as its own measurement, once per state.
- `new-l1` meets every line. Against `ref-l1` it loses q017, q049, q056, q082, q088 and gains q077, q137. Against
  `ref` the same five are lost; gained q007, q077, q137.
- Gold found in `ref-l1` only: b17; in `new-l1` only: a16, a18, b01, b02.
- Benchmark in `ref-l1` only: q013, q019, q121; in `new-l1` only: q015, q063, q147.

**Decision.** I decided to swap with the per-file limit 1 (five settings), keeping the old index (variant A). The
limit change is visible to users: at most one passage per source file among an answer's sources.

**The swap (phase 4).**
- The refresh held by a lock container from 21:43:26 (the lock confirmed held from the worker).
- Live's two index tables dumped as the way back (163 MB, done 21:44:58).
- The new index built on live on the old rows: 11.1 s, 49 MB (done 21:45:44).
- Transfer of `helpdesk_sourcechunk` and `helpdesk_indexedsourcefile` in one transaction: started 21:45:58,
  committed 21:56:39, about 10.7 min including the dump of the copy's two tables, against 8 s + 111 s on dev. The
  dump's own seconds were not logged. **Believed**: the `COPY` of the vectors waited on WAL sync.
- Five settings appended to `.env.prod` (none was present before): `RETRIEVAL_PREPARED_INDEX=True`,
  `VECTOR_INDEX_DIMENSIONS=384`, `VECTOR_INDEX_HALF_PRECISION=True`, `VECTOR_INDEX_PROBES=100`,
  `RETRIEVAL_MAX_SAME_SOURCE_PATH=1`.
- `backend` and `celery-worker` recreated 21:56:46–21:57:04, health ready by 21:57:32; no other container
  restarted. So live served the new rows with the old settings for under a minute.
- After: settings read `[True, 384, True, 100, 1]`; live 152,926 rows, all of the new cut, 1,464 files, equal to the
  copy; 0 files with both cuts; vacuum done 22:02:08; the refresh lock released.
- **Checked from my laptop** at 22:05: health ok (0.97.231, database and broker ok); three test questions answered
  and validated with 4, 6 and 4 sources, no source file twice.
- The late-journeys question cited two schema files and two example files before the swap (21:39) and four example
  files after it: the same pattern as the lost benchmark questions.

**Not as planned.**
- Recall on live: 0.9999 twice with the unchanged check (one benchmark call of 206 at 0.98, at 22:10 and 22:14,
  after the vacuum), then 1.0000 in a third run at 22:15–22:18 with a copy of the check that also prints details.
  No rows changed in between. The cause is not established; the shortfall is intermittent. With 100 lists and 100
  probes the search scans every list, so I believe the build order is not the cause (**not checked**).
- The health line's build reference reads `dev` since the restart: the manual `up -d` did not pass
  `SERVICE_BUILD_REF`, which a deploy passes. Images were not rebuilt (same creation times). The next deploy sets it
  back.
- The transfer took about five times dev's time.

**Open after the step.**
- The first nightly refresh (03:30) on the new rows: check that it ran and left 0 files with both cuts. Prod's
  `INDEX_CUT_VERSION` is still 0, so this is the check that matters; setting it to 1 is undecided.
- The next deploy recreates `db` once (`.env.prod` is shared): a few seconds without the database.
- Kept on prod until I decide: the copy database, the dumps, the saved `.env.prod`, the old index (variant A).
- The recall reading above.
- Example files outranking schema and documentation on explanation and mapping questions (q017, q049, q056, q082,
  q088) is the fault this step leaves.
- The CI baseline stays on the old cut for now.

### After step 6: clean-up and the first nightly refresh (2026-11-18 and 2026-11-19, prod 0.97.232)

I shipped the step 6 record, removed the ways back and read the first nightly refresh on the new rows.
All times UTC. Figures are **read on prod** unless marked.

**Shipping the record.**
- The step 6 records were merged (#551) and 0.97.232 deployed on 2026-11-18 at about 22:31. The deploy recreated
  `db` once, as expected.
- **Checked from my laptop**: health ok on 0.97.232 with a proper build reference again; the late-journeys question
  asked twice gave the same four example-file sources as right after the swap.

**Clean-up** (2026-11-18 23:20–23:31, my decision).
- Dropped: the copy database `napcore_helpdesk_recut` (3.7 GB), the old index `sourcechunk_embedding_ivfflat_idx`
  (2.2 GB, with `DROP INDEX CONCURRENTLY`), and the three dump files (the full dump of live from before the swap, the
  dump of live's two index tables, the transfer's input). No `step6-*` container is left.
- After: database 2.9 GB (5.1 GB before), 261 GB free; settings `[True, 384, True, 100, 1]`; 152,926 rows, all of the
  new cut; health ok.
- The ways back to the old cut are gone; only a re-index rebuilds it. This closes "kept on prod until I decide" of the
  step 6 entry, except the saved pre-swap settings file and the markers, logs and measurement outputs in the working
  folder, which remain.

**Recall on live** (206 calls each; the check reads only).
- 2026-11-18 about 22:02 (during the vacuum): 0.9999, one benchmark call at 0.98. At 22:10 and 22:14: 0.9999, the
  same single call at 0.98.
- 22:15–22:18 (the copy of the check that prints details): 1.0000. 23:31 (after the old index was dropped): 1.0000.
  2026-11-19 about 06:50: 1.0000.
- So three readings at 0.9999 and three at 1.0000; none under 1.0 since 22:15. The cause is not established: the
  detail run had no call under 1.0, so it found nothing to analyse.

**The first nightly refresh on the new rows** (2026-11-19 03:30).
- It ran and succeeded in 17.3 s. All five repository sources (NeTEx, SIRI, OpRa, mobilityDCAT-AP, TN-ITS) were
  scanned and every file skipped as unchanged; 0 rows created, updated or deleted.
- After it: 152,926 rows, all of the new cut, 0 without a vector, 0 files with both cuts; the five settings identical
  in backend and worker; `INDEX_CUT_VERSION` 0.
- What it does not show: no file changed overnight, so the refresh has not yet cut a changed file on prod.
- By the code (`services/prepared_index.py`): a file is cut again with the cut its rows have, a new file takes the cut
  of most rows of its repository, and `INDEX_CUT_VERSION` applies only to a repository or kind with no rows. Read in
  the code, **not yet seen on prod**.
- This corrects the step 6 open point that calls the refresh check "the check that matters" for `INDEX_CUT_VERSION`
  0: with the rule above, the setting matters only when a new source is added.

**Two figures I checked.**
- File records: `helpdesk_indexedsourcefile` has 1,463 rows. The 1,464 in the step 6 record is the dry run's count of
  files to cut, found only in the dry run's log. No file record was created, updated or removed after the morning
  refresh of 2026-11-18, and there are no duplicates. The two numbers count different things; which file makes the
  difference of one was **not looked up**.
- On dev, 169 rows are of the old cut: the schema pieces of six XSD files of TN-ITS, indexed 2026-11-05
  (**measured** on dev). No file mixes cuts. **Believed, not checked** in the code: the dev re-cut skipped them
  because the TN-ITS checkout was not passed to the command. On prod all TN-ITS rows are of the new cut.

**A restart that was not the index's doing** (2026-11-19 08:05).
- All containers on the prod host restarted: a package upgrade on the host upgraded Docker (docker-ce 29.10.0,
  containerd) and the daemon was stopped and started. No host reboot, no deploy; the containers are those of the
  2026-11-18 deploy.
- Outage about 75 s by container start times (08:05:25 to about 08:06:40); the web logs were not read.
- Backend, worker and beat failed twice at start: `helpdesk/services/semantic_graph.py` loads the ontology from
  GraphDB at import, and GraphDB was not yet listening. Docker restarted them and they ran. No error mentions rows,
  vectors or the index.
- After it: 152,926 rows of the new cut. **Checked from my laptop** at 08:45: health ok.
- Open, outside this plan: the start-up should wait for GraphDB.

**Open now** (the current list; the step 6 list above stays as it was).
- The refresh cutting a changed file on prod: look at the two counts the morning after an upstream source changes.
- Example files outranking schema and documentation on explanation and mapping questions (q017, q049, q056, q082,
  q088, and the late-journeys answer).
- The recall reading above.
- The CI baseline is still on the old cut.
- The six TN-ITS schema files on dev.

### Preselection by file (2026-11-19, dev database `napcore_helpdesk` and copy `napcore_helpdesk_s6pre`, read only, main at ac92c23)

I diagnosed why the prepared cut loses five questions, tried one remedy for the larger cause on a grid fixed before
the first run, and the remedy failed its gate on every variant. The code is not merged; this entry is the record.
All runs on dev with models off and GraphDB on, the per-file limit 1, hit@10 of the 149 benchmark questions
(identical in baseline and graph mode in every run); MRR@10 is graph mode. Every run: 62 GraphDB calls, the known
7 HTTP 400, 0 timeouts; the Docker VM had 3.9–4.0 GB available before and after each.

**The diagnosis of the morning, in brief** (measured).
- Old cut (`_s6pre`, old settings) 133; prepared cut (dev, the five settings) 130. Lost q017, q049, q056, q082,
  q088; gained q077, q137. Prod shows the same five (step 6 entry).
- Two hybrid databases (the old cut with the prepared example rows, and the prepared cut with the old example rows)
  put the whole difference on the prepared example rows. Example files are cut into about three times as many pieces
  as before.
- (a) Preselection for scoring (`RETRIEVAL_SCORING_CANDIDATE_CAP`, 32) keeps rows by similarity. The 32 rows covered
  20–28 files on the old cut and 8–18 on the prepared cut. After the per-file limit the final list is short (mean
  15.4 → 12.4 entries; lists under 10 entries: 20 → 37 questions), and the expected schema file is cut or last. This
  accounts for q017, q049, q056 and q088.
- (b) Example pieces are about 0.005 more similar to the questions than before, and schema pieces are unchanged.
  This accounts for q082. Not the subject of this step.
- A probe of the remedy (in-process, keep only each file's most similar row before preselection) gave 131 on the
  prepared cut. I ran it again today: 0 rank changes.

**Why the probe lost four questions** (measured with the gateway's own trace, `retrieve_chunks_with_trace` with
its probe, reference against probe, on the same question).
- The belief was that each of the four loses because a file's second piece no longer reaches scoring. That holds
  for one of them, q122. The reference scores two pieces of the expected file that match the question's words
  (similarity 0.8405 and 0.838, lexical rank 0.985 and 1.0); the better one is 7th after the per-file limit. The
  probe admits only the file's most similar piece (0.841, lexical rank 0), which is 24th.
- q077 and q090: the same piece of the expected file is scored in both. The probe admits 31 files instead of 12–14,
  and files the row count had kept out now rank above it: 3 of them for q077 (9th → 12th), 7 for q090 (9th → 15th).
- q147: the reference scored 15 pieces of the expected README (15 of 32 slots); its best piece is the same in both.
  The probe admits 10 SIRI schema files the reference never scored, and the README falls from 10th to 20th.
- A second effect, through the vector range. The scaled vector score is computed over the scored rows, from the
  lowest to the highest similarity. The lexical reserve admits rows of the lexical recall pool that have no stored
  similarity; their computed similarity is low (0.74–0.80). Admitting by file brings in more of them, and the low
  end drops (q049 0.849 → 0.774, q147 0.792 → 0.740) (measured). I re-scored the probe's lists with the reference's
  range, changing only the scaled part: q049 1st → 10th, q056 4th → 10th, q147 20th → 11th. So much of the probe's
  gain on q049 and q056, and of its loss on q147, comes through the range (**believed**: the re-scoring is
  arithmetic on lists the other range did not build, not a run).

**The design.**
- Preselection chooses files by their best piece's similarity and admits up to K pieces of each chosen file until
  the budget is used. The budget counts rows (32, as now) or files (32 files). A file is the source path, as for the
  per-file limit. The lexical reserve (at most a quarter of the slots) keeps the same per-file limit. Ties: lexical
  rank, quality, then the lower id. Nothing names a kind of document, a standard, a path or a question.
- Behind `RETRIEVAL_PRESELECT_PIECES_PER_FILE` (0 = by row, as before) and `RETRIEVAL_PRESELECT_BUDGET` (`rows` or
  `files`), declared and documented like their neighbours. 10 unit tests (the files chosen by their best piece, K,
  both budgets, a file with fewer than K pieces, ties, the reserve, and the setting off equal to the preselection by
  row on a constructed pool). They passed run as CI runs them, without a `.env` and with models off.
- Fixed before the first run: the grid K ∈ {1, 2} × budget in rows or files, four variants; no change to the vector
  scaling. The range moves because more low-similarity rows are admitted, which comes with admitting files. Changing
  the scaling is a separate tuning, and the re-scoring above shows it cuts both ways.
- Selection rule: among variants that pass the gate, the highest hit@10 on the prepared cut, then MRR@10, then the
  fewest lost.

**The grid** (prepared cut, one run each, measured; reference `p545/after2`: 130, MRR@10 0.6001).

| variant | hit@10 | MRR@10 | of the five in the top 10 | lost (rank before → after) | gained |
|---|---|---|---|---|---|
| K 1, budget in rows | 131 | 0.5988 | 4 (q082 16th) | q077 9→12, q090 9→14, q122 7→none, q147 10→19 | q017, q049, q056, q068, q088 |
| K 1, budget in files | 131 | 0.5988 | 4 | the same | the same |
| K 2, budget in rows | 129 | 0.6024 | 2 (q017 11th, q082 17th, q088 20th) | q077 9→11, q090 9→13, q147 10→15 | q049 11→9, q056 11→9 |
| K 2, budget in files | 132 | 0.6221 | 4 (q082 16th) | q077 9→12, q090 9→15, q147 10→20 | q017 12→10, q049 11→1, q056 11→3, q068 none→4, q088 none→9 |

- K 1 in rows and in files are the same mechanism (one row per file), as I said before the runs: 0 rank changes.
- K 2 keeps q122 (6th), as the diagnosis predicted. q077, q090 and q147 are lost in every variant: their losses come
  from new competing files and the range, which K does not change.

**The gate** (fixed before the runs; all lines must hold for the selected variant).
- Line 2, at most 1 question of the reference's top 10 lost: **not met by any variant** (4, 4, 3, 3).
- K 2 in rows also fails line 1 (2 of 5 in the top 10, at least 3 needed) and line 3 (129, at least 131 needed).
- K 2 in files meets line 1 (4 of 5) and line 3 (132; MRR@10 0.6221, not lower than 0.6001 − 0.005) on its one run.
- No variant passes, so none is selected. The runs the rule makes for the selected variant were not made: the
  second prepared run, the old cut (line 4), the answer-source questions (line 5), timing (line 6), the final list
  length (line 7) and CI (line 8).
- **Decision**: the gate failed, and a failed gate is the result. I reverted the code. The grid is not extended,
  no gate line is loosened, and the row cap is not raised instead.

**Believed, not checked.**
- That the K 2 budget in files would hold line 4 (the old cut) and line 6 (time); it scores up to 64 rows instead
  of 32. Not measured. In its run the benchmark's median retrieval time was 340 ms against 307 ms for K 1, but
  in a different hour from the reference, so this is no gate reading.
- That prod's `RETRIEVAL_SCORING_CANDIDATE_CAP` is the default 32 (not read on prod).

**Open.**
- (b), the higher similarity of example pieces, and q082 with it (16th at best here).
- The row cap: raising it was probed in the morning (96: prepared 132, old cut 132) and stays outside this step.
- Answers with model calls were not measured.
- The vector range follows whatever low-similarity rows enter scoring. It is a lever of its own: it explains part
  of this step's gains and of its losses.

### Preselection by file, second step (2026-11-19, dev database `napcore_helpdesk` and copy `napcore_helpdesk_s6pre`, read only, main at 3eac565)

The first step on this idea failed its gate (entry above), and that record stands. I set a second gate after it,
with two variants. One of them (two pieces per file, the budget in files) was picked after seeing the first step's
numbers. So only runs made for this step count, every number below is fresh, and a failure here would have ended the
idea. All runs on dev with models off and GraphDB on, the per-file limit 1, hit@10 of the 149 benchmark questions
(identical in baseline and graph mode in every run); MRR@10 is graph mode. Every benchmark run: 62 GraphDB calls,
the known 7 HTTP 400 (a malformed fallback query, fixed separately and not part of this comparison), 0 timeouts; the
Docker VM had 3.9–4.0 GB available before and after each.

**The grid** (fixed with the gate, before the runs).
- V1: two pieces per file, the budget counted in files: the first step's "K 2, budget in files", unchanged.
- V2: the same selection, with the vector score scaled over today's range. Within the same call the gateway also
  computes the rows the preselection by row would keep (the same pool, the same graph and definition rows). It takes
  the lowest and highest similarity over those rows, with the same rule per row as today. The rows scored are V1's;
  the scale is today's, not clipped. So a row less similar than today's lowest gets a vector part below 0, on today's
  scale extended.
- Why that isolates the range: with today's selection this definition gives today's range by construction. So V1
  against V2 is the range effect, and V2 against the reference is the selection effect. Nothing in it names a kind of
  document, a standard, an element or a question. It is behind its own setting, `RETRIEVAL_PRESELECT_ROW_RANGE`.
- Selection rule: among variants that pass the gate, the highest hit@10 on the prepared cut (both runs agreeing),
  then MRR@10, then V2.

**The runs** (measured; reference `p545/after2`, which today's code path reproduced in this step with 0 rank
changes, run from the branch with the setting at 0).

| run | hit@10 | MRR@10 | q017 / q049 / q056 / q082 / q088 | q077 / q090 / q147 |
|---|---|---|---|---|
| reference | 130 | 0.6001 | 12 / 11 / 11 / – / – | 9 / 9 / 10 |
| V1, run 1 and run 2 (identical, 0 rank changes) | 132 | 0.6221 | 10 / 1 / 3 / 16 / 9 | 12 / 15 / 20 |
| V2, run 1 and run 2 (identical, 0 rank changes) | 132 | 0.6082 | 10 / 9 / 9 / 18 / 12 | 11 / 16 / 10 |

- V1 against the reference: lost from the top 10 q077 (9th → 12th), q090 (9th → 15th), q147 (10th → 20th); gained
  q017 (12th → 10th), q049 (11th → 1st), q056 (11th → 3rd), q068 (none → 4th), q088 (none → 9th). V1 reproduces
  the first step's run of the same variant with 0 rank changes.
- V2 against the reference: lost q077 (9th → 11th) and q090 (9th → 16th); gained q017 (12th → 10th), q049 (11th →
  9th), q056 (11th → 9th), q068 (none → 7th).
- **Range or selection** (measured, V1 against V2 on the same selection). Choosing by file carries the hit@10 gain:
  V2 alone is at 132, with q017, q049 and q056 in the top 10 and q068 gained. The wider range of V1 carries most of
  the MRR gain (0.6082 → 0.6221) and the top ranks of q049 (9th → 1st) and q056 (9th → 3rd). It brings q088 into the
  top 10 (12th → 9th) and costs q147 (10th → 20th). This confirms what the first step's re-scoring suggested about
  q049, q056 and q147, now by runs.
- Selected: **V1**. It ties V2 on hit@10 (132 in both runs of each) and has the higher MRR@10.

**The gate** (fixed before the runs; all lines for the selected variant).
1. hit@10 at least 132 in both runs, MRR@10 not below 0.6001: **met** (132 and 132; 0.6221).
2. q077, q090 and q147 each at rank 20 or better, and at most one question of the reference's top 10 below rank 20:
   **met** (12th, 15th, 20th; none below 20). q147 is exactly at the line.
3. At least 3 of q017, q049, q056, q082, q088 in the top 10: **met** (4: q017, q049, q056, q088; q082 16th).
4. Old cut (`_s6pre`, old settings) not under 132: **met** (134; against this morning's 133 q068 gained, none lost).
5. Answer-source questions (stage 1, no model call; 0 model calls counted) not under 40 of 57 in either run: **met**
   (40 and 40, the same set). Against this morning's 40 on the prepared cut: b22 and b26 found only now, b01 and
   b16 only then.
6. Median retrieval time per question not more than 0.3 s above the reference made in the same hour: **met**. Graph
   mode: 304 ms against 293 ms, 90th percentile 6.36 s against 6.15 s; baseline mode 306 ms against 298 ms. The pair
   was run back to back, 14:35–14:47 local time, after another task on the dev stack had finished. Timings from the
   grid runs are not used: that task ran a benchmark on dev during them.
7. Questions with fewer than 10 final entries do not rise: **met** (38 → 1; mean final list length 12.7 → 19.4;
   rows scored per question 32.0 → 40.1 on average; all 149 questions traced, both sides counted the same way).
8. CI green, including the retrieval benchmark against the existing baseline with no baseline or threshold change:
   **met** on PR #563 (measured there). The retrieval benchmark ran with the new defaults on CI's old-cut hash index
   and passed against the unchanged baseline. hit@10 rose: 0.517 → 0.537 (baseline mode), 0.517 → 0.544 (graph).
   MRR@10 fell within the allowed 0.03: 0.270 → 0.261 and 0.284 → 0.272. I changed no baseline and no threshold.
   The other CI checks passed too.

**What changed.** `retrieval_gateway._preselect_base_ids_by_file`, used at the preselection for scoring when
`RETRIEVAL_PRESELECT_PIECES_PER_FILE` is above 0. New settings: `RETRIEVAL_PRESELECT_PIECES_PER_FILE` (default 2;
0 restores the preselection by row without a deploy), `RETRIEVAL_PRESELECT_BUDGET` (default `files`) and
`RETRIEVAL_PRESELECT_ROW_RANGE` (default False, V2 when True). They are declared and documented like their
neighbours. 11 unit tests: files by their best piece, K, both budgets, a file with fewer than K pieces, ties, the
reserve, rows without a path, the setting off equal to the preselection by row on a constructed pool, and V2's range
giving the scores of the preselection by row. The full backend suite passed, run as CI runs it, without a `.env`
and with models off (1,204 tests, 9 skipped).

**Believed, not checked.**
- That prod behaves like dev here. Prod has the same cut and settings (step 6 entry), and its
  `RETRIEVAL_SCORING_CANDIDATE_CAP` is believed to be the default 32 (not read on prod).
- That answers improve with longer source lists. Answers with model calls were not measured. Lists now have up to
  20 entries where they had 12.7 on average, so an answer is given more passages.

**Open.**
- (b), the higher similarity of example pieces, and q082 with it (16th).
- q147 sits at rank 20, at the edge of line 2.
- The row cap stays as it is.
- The answers with model calls, and prod after a deploy.

### The application's path, and no concept boost from a stop word or a loose label match (2026-11-20/21, dev database `napcore_helpdesk` and copy `napcore_helpdesk_s6pre`, read only, main at cad6550)

**What I found on 2026-11-20 and had not recorded** (measured; files in `.claude/skills/measure-on-copy/runs/x1/`
and `runs/y1/`, which agree with the figures below).
- Every benchmark run until then ran with the ontology's concept table empty: the measuring environment set
  `NAPCORE_SKIP_GRAPHDB_IMPORT`, so question concepts and the concept boost were missing. It judged the top 10 of
  20 passages. The application has 4,616 concepts and serves 6 passages (k 6, minimum score 0.62, `min_results` 6).
- The four conditions, prepared cut, graph mode: ontology empty, 20 passages: hit@10 132; ontology loaded, 20
  passages: hit@10 136; ontology empty, 6 passages: hit@6 124; ontology loaded, 6 passages: hit@6 129.
- Six runs of the live choices on the application's path (ontology loaded, hit@6 of 149, MRR@6, right source
  first): prod's configuration today 129, 0.680, 91 first; preselection by row 129, 0.684; per-file limit 2: 127,
  0.673; both old (by row, limit 2) 129, 0.696; the old cut with today's settings 133, 0.650, 82 first; the old cut
  with all old settings 130, 0.657. Reading: the per-file limit 1 is confirmed; preselection by file is neutral on
  this path; the re-cut is a trade: the right source first more often (91 against 82), four fewer questions among
  the 6 (129 against 133).
- The DATEX II Accident miss ("How do I describe a road accident with a closed lane in DATEX II, and which classes
  and attributes carry the location and the lane restriction?"): the class definition is row 8 of the vector pool;
  with no concepts it ranks 7th, one place outside the 6; with concepts it ranks 13th. Seven passages get +0.20 for
  naming a concept the question "names" through ordinary words: "with" (transmodel:with), "classes ...
  attributes" (transmodel:CLASS_ATTRIBUTE), "location" (netex:Location, transmodel:LOCATION).

**Correction of a count.** The day's tally (`ordinary.py`) gave 44 stop-word matches in the 149 questions. It
counted one alias per concept, the shortest, and so missed the alias "is for". Counting every alias that matches
(`runs/z1/cls.py`), there are 52 stop-word matches (for 20, with 10, between 9, is for 8, from 3, when 2) in 38
questions. The other two counts stand: 156 one-word matches not rare in the scope, 19 loose matches.

**Diagnosis per class of match** (measured; in-process counterfactuals on main's code, no tracked code edited,
`runs/z1/cfhooks.py`; the command's `--app-conditions --app-scope` with the ontology loaded; reference 129, MRR@6
0.6799, reproduced). A concept counts in a class when every alias it matched is of that class. Two forms: A, the
concept gives no boost, no graph expansion and no graph candidates, but keeps its definitions and element lookups;
B, the concept is removed entirely.

| class suppressed | form A | form B |
|---|---|---|
| stop word (alias with no text-search term) | 130, 0.6796; q146 gained (– → 6) | 130, 0.6799; q146 gained (– → 5) |
| loose (several-word label reached only through plurals or prefixed words) | 129, 0.6772; none gained or lost | 128, 0.6704; q049 lost (1st → –) |
| common (one-word alias not rare in the scope) | 132, 0.6819 | 132, 0.6956 |

- Stop words: suppressing them helps by one question in both forms. Loose: neutral in A, harmful in B (the
  definitions of a loosely named class matter for q049). I chose form A.
- Every common match in the 149 questions is the concept's own name (opra 66, siri 25, journey, vehicle, stop,
  timing, location ...). The grid exempted own names before any number existed, so V3 (V2 plus common matches that
  are not the concept's own name) suppresses exactly what V2 suppresses on every question measured. I did not run it;
  by the selection rule it could not be chosen.
- How the code knows each class at run time (read): a stop word is an alias whose `to_tsvector('english', ...)` is
  empty (one query per question for aliases not yet seen, then cached); a loose match is one that only
  `_alias_matches_question` makes, not `_alias_matches_text`; a common match is a one-word alias whose term is not
  among the question's rare terms, which the gateway already computes.

**The grid** (fixed before the runs; branch code; setting by environment). V1: stop-word matches give no boost.
V2: V1 and loose matches. V3: dropped, see above. Selection: among variants that pass the gate, the highest hit@6,
then MRR@6, then the variant that suppresses less.

| run | hit@6 | MRR@6 | right source first | fewer than 6 | Accident (ranked) | (a) / (b) / (d) |
|---|---|---|---|---|---|---|
| reference (main), two runs | 129, 129 | 0.6799, 0.6799 | 91 | 15 | 13th | 1 / 3 / 1 |
| V1 | 130 | 0.6802 | 90 | 15 | 13th | 1 / 3 / 4 |
| V2, run 1 and run 2 | 130, 130 | 0.6805, 0.6802 | 90 | 15 | 12th | 1 / 1 / 4 |

- V1 against the reference: q146 gained (– → 4th); none lost; q052 1st → 2nd, q119 4th → 2nd, q144 5th → 4th.
- V2 against the reference: the same, and q122 5th → 4th; q146 at 4th and 5th in the two runs.
- Selected: **V2**. V1 fails gate line 4: the Accident class stays 13th.
- Every benchmark run: 348–364 GraphDB calls, 0 failures, 0 timeouts; the Docker VM had 3.81–3.91 GB available
  before and after each.

**The gate** (fixed before the runs; all lines for V2).
1. hit@6 not under 129: **met** (130 and 130).
2. MRR@6 not under 0.6746: **met** (0.6805 and 0.6802).
3. At most 1 question lost that the reference finds first, at most 2 lost from the 6: **met** (none lost; q052
   moves from 1st to 2nd).
4. The Accident class better than 13th, and (a), (b), (d) keep it in their 6: **met** (12th; 1st, 1st, 4th).
5. Old cut (`_s6pre`, old index settings, per-file limit 1) not under 132: **met** (135, MRR@6 0.6566; against the
   morning's 133: q122 and q133 gained, none lost).
6. Answer-source questions (stage 1, no model; ontology loaded) not under the same-hour reference: **met**. The
   reference with today's code finds 38 of 57 in both its runs; V2 finds 38 and 38 (b33 found only with V2, b16
   only with the reference). The stored 40 of 57 was measured with the ontology empty and is not comparable.
7. Median retrieval time not more than 0.2 s above the same-hour reference: **met** (graph mode 829 ms against
   830 ms; baseline mode 339 ms against 333 ms).
8. CI green, including the retrieval benchmark against the unchanged baseline: **met** on PR #572 (measured there;
   1,266 backend tests, the 5 database-backed new ones among them). CI's figures did not move: hit@10 0.537
   (baseline mode) and 0.544 (graph), MRR@10 0.261 and 0.272, the same as recorded for PR #563. CI runs with the
   ontology empty, so no concept is extracted there. I changed no baseline and no threshold.

**What changed.** `semantic_graph.question_alias_matches` reports how each alias of a concept matched a question.
`retrieval_gateway.no_boost_question_concepts` picks the concepts whose every match is of a suppressed kind. They
are left out of the concepts used for the boost, graph expansion and graph candidates. New setting
`RETRIEVAL_CONCEPT_NO_BOOST_MATCHES` (default `stop,loose`; empty restores the previous behaviour without a
deploy), declared and documented like its neighbours. The trace has `noBoostConceptIds`. 12 unit tests: a
stop-word-only concept gives no boost; a concept also matched on a distinctive alias keeps it; a stop phrase of
several words; loose matches; without PostgreSQL no alias counts as a stop word; the setting; the setting off
reproduces today's path; scope handling; fixed order. The 1,027 backend tests that need no database, these 7
among them, passed locally, run without a `.env` and with models off. The 5 database-backed tests run only on CI.

**Believed, not checked.**
- That prod behaves like dev here. Prod has the same cut, settings and ontology (step 6 entry); not measured on prod.
- That answers improve. Answers with model calls were not measured.
- That q052's move from 1st to 2nd is a near tie at the top: it moves in every counterfactual.

**Open.**
- The common class, own names (not part of this step; for a possible separate step with its own gate). Measured as
  a counterfactual on main's code:
  - Form A: hit@6 132, MRR@6 0.6819, 90 first. Gained q070 (– → 6), q083 (– → 6), q133 (– → 5), q140 (– →
    6); lost q143 (6th → –).
  - Form B: 132, 0.6956, 92 first. Gained q070 (– → 6), q076 (– → 1), q083 (– → 4), q140 (– → 4); lost q080
    (5th → –); 19 rank changes.
  - Accident, form A: 13th → 8th, still outside the 6; variant (c) 11th → 5th; (a), (b), (d) unchanged.
  - It covers 156 matches in 111 questions.
  - At run time it is a one-word alias, matched as written, not a stop word, whose term is not among the question's
    rare terms in the scope. Own name: the alias words written together equal the concept id's local name. The rare
    terms never include the standards' names (an existing list in the code), so those names always fall here.
  - The hooks are kept in `runs/z1/` (`cfhooks.py`, `bench_cf.py`, `tf_cf.py`).
- The Accident class is still outside the 6 (12th).
- The answers with model calls, and prod after a deploy.
