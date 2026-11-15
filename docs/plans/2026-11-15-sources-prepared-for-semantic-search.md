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

- **Answers.** The 23 answerable and the 25 must-refuse questions, 3 runs each. Every answer that is new or
  changed is read against its passages.
- **Files.** Gold (57) and benchmark (141) at file level. Each question lost at file level is read: it counts as
  lost only if the passages given no longer hold what the named file holds for the question.
- **The case.** The late-journeys question, 3 runs, and the 7 questions with a better piece left out, read by hand.
- **Examples.** The example benchmark, all questions, 3 runs: generated, first attempts, linked objects.
- **Cost.** Rows, index size, embedding time, retrieval time.

"Not lower" means not lower than the baseline by more than the spread measured in step 0.

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
