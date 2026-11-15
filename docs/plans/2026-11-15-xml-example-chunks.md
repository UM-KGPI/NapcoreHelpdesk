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
