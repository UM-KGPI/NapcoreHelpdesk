# Plan: the right piece of a cited file

Written 2026-11-15 against 0.97.225. Each claim is labelled **measured**, **believed** or **assumed**. All
measurements are on dev (host-side runs against the dev database, embedder, validator and GraphDB, relevance check
on, `LLM_MAX_EVIDENCE_CHUNKS=6` as prod runs), while other branches were measured on the same stack: time figures
are upper bounds.

## 1. The problem

Prod 0.97.225 refused "How to model number of late journeys?" with "The evidence does not describe a dedicated
element for counting late journeys …", citing `examples/CancelledAndLateDatedVehicleJourneys.xml` (OpRa). The file
answers the question: its `LateDatedVehicleJourneyCount` counts late journeys per journey pattern in delay
intervals. The model was given another piece of the same file. So the citation links to a file that holds the
answer, and the text says it does not.

The question: how often does retrieval find the right file and give the model the wrong piece of it, and is there
one general mechanism that gives the right piece on the index as it is?

## 2. What is measured

- **The finer measure** (new in `locate_answer_sources`, field `pieces`): for each question whose wanted file is
  among the passages the model gets, whether the piece given is the file's best piece. The best piece is the chunk
  of the file that holds the most *answer terms*: the English stems of the question (its English rendering when
  there is one), with markup removed and CamelCase split, plus the element names the gold note writes. It is a
  proxy for hand labels; its accuracy is checked by hand (§4.2). A file of one chunk, or whose chunks share no
  answer term, is not counted. `piecesAllFiles` gives the same for every file among the passages.
- File level, as before: gold found and benchmark found (`locate_answer_sources`), the CI retrieval benchmark.
- Through the API (host server, one request at a time): the 23 answerable and 25 must-refuse questions of
  `refused-questions.yaml`, and twelve benchmark questions answered well today.

## 3. The step and the gate (fixed before the change)

One commit, one general mechanism working on the index as it is, chosen from the diagnosis. Gate, against step 0
of the same day:

1. Finer measure: the number of questions whose best piece of the wanted file is among the passages rises by at
   least 5 or 25 % of the affected questions, whichever is smaller, beyond the spread; no question loses it.
2. Gold and benchmark found not below step 0; every lost question explained.
3. CI retrieval benchmark: no metric below `ci-baseline.json`, not below step 0 beyond spread.
4. The case through the API, 3 runs: the model gets the piece with the count element; the answer read against
   the file.
5. Answerable (23), 3 runs: answered not lower; must-refuse (25), 3 runs: none answered more often.
6. Twelve benchmark questions, 2 runs: cited sources and substance not worse.
7. Prompt characters, retrieval median not more than 0.3 s above step 0, no added model call.

## 4. Diagnosis (no change of behaviour)

### 4.1 The case

The file (93 lines) is five chunks in the index (**measured**, ids in index order):

| piece | chars | content | vector rank (no scope) | cosine to the question |
|---|---|---|---|---|
| 1 | 38 | `<?xml …?>` alone | 66 | 0.8493 |
| 2 | 1,621 | root element with namespaces, the frame, the first cancelled entry | 11 | 0.8555 |
| 3 | 1,468 | cancelled and late entries | 3,863 | 0.8325 |
| 4 | 1,604 | last late entries, `<indicators>`, `<LateDatedVehicleJourneyCount>` (at character 655) with its first interval | 548 | 0.8427 |
| 5 | 1,498 | the other intervals, `</LateDatedVehicleJourneyCount>` | 24 | 0.8524 |

Through the stages of the app's retrieval (the probe, the question without scope as the chat page sends it):
pieces 2 and 5 are in the vector pool (11th and 24th of 30); after scoring piece 2 is 3rd (rank score 0.890) and
piece 5 is 9th (0.873); sorted, they are 1st and 2nd; the per-file cap (`RETRIEVAL_MAX_SAME_SOURCE_PATH`, 1 on dev)
keeps piece 2 only. The view then puts four presence definitions (JOURNEY LAYOVER, JOURNEY PATTERN and two
schema files) in front, and the model reads piece 2 as E5. The prompt cut (1,200 characters, a block up to 1,500
is kept whole) removed the end of piece 2 and its semantic summary, nothing that answers the question; piece 5
(1,498) would be shown whole, and the count element in piece 4 would be inside the cut. With the per-file cap at 2
(the default; `.env.prod.example` does not set it, prod's own file I did not read), piece 5 survives retrieval as
5th of 6, and the presence definitions push it below the six places of the prompt (**measured** with the cap
overridden). Through the API on step 0 the model got piece 2 in both runs and refused both times, as on prod.

**The cause, as a checkable claim** (**measured**, by calling the functions by hand: the pool and stages through
`retrieval_probe`, the pieces' scores by injecting all five into the scoring, and their parts with
`_token_overlap_score` and the query embedding): the five pieces of the file have nearly the same vector (cosine
0.833 to 0.856), because what they share (the file path, the standard, the XML form) dominates the passage vector.
Which piece represents the file is therefore decided by small differences: piece 2 wins over piece 5 by 0.003 of
cosine (lexical overlap 0.4 against 0.6 does not make up for it), takes the file's one place, and piece 4, which
opens the count element, is 548th by vector and never a candidate. Not the cause: the prompt's character cut.
Injected into the scoring, the app's own score ranks the pieces 2 (0.890), 5 (0.873), 4 (0.682): applying the
existing score within the file would still choose piece 2.

### 4.2 How often

Step 0, two runs each (gold 57, benchmark 141):

| | gold run 1 | gold run 2 | bench run 1 | bench run 2 |
|---|---|---|---|---|
| found (file level) | 33 | 32 | 124 | 124 |
| wanted file among the passages | 31 | 30 | 92 | 92 |
| of these with a multi-chunk file and a term signal | 29 | 28 | 90 | 90 |
| best piece given (proxy) | 26 | 26 | 83 | 83 |
| not given (proxy) | 5 | 4 | 9 | 9 |

Not given by the proxy (**measured**): gold a05, a09, a15 (run 1 only), b14, b25; benchmark q057, q059, q072, q107,
q109, q117, q141, q142, q149. The piece choice itself is stable between runs: 1 changed piece in gold, 0 in the
benchmark.

**How good the proxy is** (**measured**, read by me):

- A random sample of 20 file passages from gold run 1, all files (12 where the proxy says the piece given is not
  the best, 8 where it agrees): where it agrees, it is right 8 of 8; where it disagrees, it is right 1 of 12. Most
  of those 12 are everyday fare and timetable questions on files that do not answer them, where the "best" piece is
  just the one with more question words; in 3 of them the piece given was the right one (the `StopPlace`
  declaration, a `DistributionAssignment` "onBoard" piece for "where can a passenger buy tickets", the bus fare
  table) and the proxy preferred the file's header comment.
- The 19 file passages of the 14 affected questions above: the proxy's best piece is the better one in 8, not in
  11. Better given elsewhere in the file: a09 (the example's header describing the bus timetable, not a stop list),
  a15 (README overview), b14 (both MMTIS annexes: the data categories), q057 (weakly), q059 (one of three files),
  q072 (`LinePropertiesGroup` with `OperatorRef`), q149 (`WheelchairVehicleEquipmentGroup`). Wrong: a05 and b25
  (the piece given is the asked element), q059's frequency-group piece, q107, q109, q117, q141, q142.

So, read by hand, **7 of the 119 questions** with the wanted file among the passages have a clearly better piece of
it left out (6 %): three schema declarations (q057, q072, q149), two examples (a09, q059), one regulation annex
(b14), one README (a15). Three of them are in the API sets (a09 = k09, a15 = e01, a05 = k05) and all three are
answered in 2 of 2 runs today; the others are not asked through the API. The case question is not among them: the
gold file names only the late-journey schema for it (a11), not the example. **Believed**: the pattern is real but
not frequent on these question sets, and the proxy over-counts it about twofold.

### 4.3 How files are chunked

**Measured** on the dev index:

| kind | chunks | files | median chars | chunks per file (median / p90 / max) | overlap between neighbours | piece starts inside the document |
|---|---|---|---|---|---|---|
| XML examples (`example`, no heading) | 43,193 | 405 | 1,471 | 8 / 172 / 9,855 | none (1 of 1,946 pairs in a 40-file sample) | 88 % start at depth 3 or more |
| XSD (`schema`, one declaration each, with heading) | 10,579 | 608 | 244 | 13 / 35 / 250 | none (units) | – |
| NAPCORE, DATEX II, regulation, INSPIRE (prose, with heading) | 6,784 | 2,134 | 683–1,535 | 1–5 | none | – |
| guide, README (sections and prose) | 1,169 | 109 | 229–1,189 | 3–4 | 200 characters in about 7 % of pairs | – |

`split_xml` starts a new segment only at a line indented by at most two spaces, so the body of an example is one
segment, which is then cut by lines at 1,200 characters, mid-element, without overlap and without any trace of
where the piece sits. Each piece gets a semantic summary of up to 18 element names and comments.

How often the piece given is the file's opening (the first piece of 100 characters or more): among XML passages,
23 of 77 in gold and 137 of 309 in the benchmark, against 6.6 and 63 if the piece were drawn at random; among XSD
passages 15 of 91 and 40 of 278 (7.1 and 27 by chance). An opening is not wrong as such (its header comment often
says what the example is about, which is what an example question needs), but it wins more often than its content
explains, which agrees with §4.1: within a file the vectors hardly differ.

**Is it chunking?** For examples, partly (**believed**): the cut by size without context is why the pieces of a
file cannot be told apart by vector and why the count element is split over pieces 4 and 5. For schema files, no:
declarations are units, and the three affected schema questions are a choice between declarations. A re-chunking
is outside this step (it needs the index rebuilt); what it would need is in §6.

### 4.4 Mechanism chosen for step 2

Of the candidates: neighbouring pieces as one passage does not fit the budget (pieces are 1,400–1,600 characters;
the prompt keeps 1,200); the per-chunk budget around matched terms exists already (`_trim_chunk_text` with focus
terms) and is not the cause here; a lower weight for declaration-heavy pieces does not touch the case (piece 2 is
mostly content); the app's own score within the file chooses piece 2 (§4.1). Left: **among the pieces of a file
that has no headings (a size cut, which in this index means the XML examples), give the one that holds strictly
more of the question's terms**, found with the existing English text-search index; on a tie the retrieved piece
stays; the file and its rank do not change. It applies to every source kind cut by size and not to pieces with a
heading (schema declarations, sections, articles, classes), which are units chosen for what they declare. Expected
(**believed**, from §4.2): at most the two example questions plus the case; the proxy's accuracy suggests it will
also change pieces that were right.

## 5. Results
