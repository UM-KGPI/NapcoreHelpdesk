# Plan: questions whose answer is in the index but is not retrieved

Written 2026-11-14 against 0.97.220, for the implementer. Continues the record
`2026-11-14-refused-questions.md` (#523): its causes A and C are fixed there, cause B is this plan. Each claim is
labelled **measured**, **believed** or **assumed**.

## 1. The problem

After #523, a question can still end without a useful answer in two ways:

- **Refused by the answer model** (`evidence_answers_question: false`): 11 of the 30 questions prod still
  refused, 8 of them wrongly. 6 of the 8 because the passage that answers them was not among the evidence, 2
  because the model judged the evidence too strictly (**measured**, the record §2.2).
- **Answered beside the point**: of the 10 questions #523's second opinion lets through, 3 are answered from
  evidence that is real but about something else ("Which formats count as machine-readable?" from a NeTEx element
  of that name, not from the regulation) (**measured**, the record §5). These were hidden behind a refusal before.

Both are the same fault seen from two sides: the passage that answers the question does not reach the model.
The model sees 4 passages (`LLM_MAX_EVIDENCE_CHUNKS`); retrieval is asked for 6. (Checked in Q0: the web page sends
`retrievalTopK: 6`, the prompt takes `chunks[:4]` with their text and lists the paths of up to 20 more candidates
without text.)

### What a first look shows

I asked retrieval on dev for up to 60 candidates for 10 of these questions and looked for the source that answers
each (**measured**, 2026-11-14, the bare `retrieve_chunks_with_trace` with graph expansion on; the app adds
passages on top, so this is a lower bound, not the app's exact evidence):

| Question | Wanted source | Rank among candidates |
|---|---|---|
| What is OpRa used for? | OpRa `README.md` | 5 of 19 (four schema files above it) |
| How to model number of late journeys? | `opra_lateDatedVehicleJourney` | 1, 3, 8 |
| How do I describe an elevator in a stop place? | `netex_ifopt_equipmentAccess` (LiftEquipment) | 20 of 20 |
| How do I describe an elevator in a station in NeTEx? | same | not among 23 |
| Which fare data must be provided … MMTIS …? | regulation Annex 1 | not among 18 |
| What if my dataset is available in several formats? | mobilityDCAT-AP | not among 27 |
| Which formats count as machine-readable? | regulation Art. 2, 4, 5 | not among 18 |
| How are static data described? | regulation Art. 2 | not among 19 |
| In which legislation is DATEX included? | regulation Art. 4, 5 | not among 12 |
| How to describe a bus ticket? | fare product schema | not among 18 |

So for 7 of the 10 the wanted source is not a candidate at all: this is mostly a fault of finding, not of
ordering. Two patterns stand out, both **believed** until Q0 measures them:

- **A question in everyday words against a source in the standard's words** ("elevator" / LiftEquipment, "ticket" /
  fare product, "several formats" / distribution).
- **A question the legislation or a profile answers, with no standard named**, where every candidate comes from
  schemas and examples. The candidate list holds no passage of the regulation at all.

Limits of this look: one run per question, 10 questions, my own choice of "wanted source", and the pool never
returned more than 27 candidates although 60 were asked for. (Q0 found why: the candidate list in the trace is taken
after the preselection cap, `RETRIEVAL_SCORING_CANDIDATE_CAP` = 32, and after the per-file cap,
`RETRIEVAL_MAX_SAME_SOURCE_PATH`, which is 1 in the dev `.env` and 2 by default. top_k only sets the size of the
vector pool before them. On the app's path it is still 7 of 10, but not the same 7: "In which legislation is DATEX
included?" is answered, from the legal-status provisions added after ranking, and the MMTIS Annex is a candidate (at
23 of 29), while "number of late journeys" and "elevator in a stop place" are not candidates.)

## 2. Principle

Before any change, find out for a fixed set of questions **at which step the answering passage is lost**. Every
later step is chosen by that table and measured against it. No step is taken because a mechanism looks plausible:
the earlier attempts of that kind (plural matching, coverage ranking, related-match expansion) each made the
benchmark worse.

## 3. Steps

Each step is one commit on one branch, measured against the state before it, reverted if its gate fails.

### Q0. Where the passage is lost (no change of behaviour)

1. **A gold file** `backend/helpdesk/benchmarks/answer-source-questions.yaml`: questions with the source that
   answers them, in the format of `benchmark-questions.yaml` (`expected_source_patterns`). Content: the 23 wrongly
   refused questions of the record, the 3 answered beside the point, and about 30 more from the prod log of the
   same kinds (everyday wording; legislation, profile and overview questions; non-English). The wanted source of
   each is checked in the index, and reviewed by Andrej.
2. **A command** that, for each question, reports the rank of the wanted source in each candidate source
   separately (full-text, vector, rare terms, graph and alias candidates, path hints, the added element, example
   and provision candidates), then after scoring, after the per-source cap and the diversification, and finally
   whether it is among the 4 passages the model gets. It runs the question as the app does (English rendering,
   scope, the app's added passages).
3. **The table**: for each question the first step where the passage is absent or falls below the cut, and the
   counts per step. Run on the existing 140 benchmark questions as well, to see whether these questions lose
   passages somewhere the benchmark does not look.

No gate; the output decides which of Q1 to Q3 are done and in what order. If the losses are spread evenly over
many steps with no dominant one, that is the finding, and the plan stops for a rethink.

### Q1. The wording gap (only if Q0 shows candidates are missing because of wording)

The existing vocabulary bridge (`VOCABULARY_BRIDGE_ENABLED`, off on prod, never measured on these questions) maps
the question's words to the standards' terms with one controller call. Measure it as it is, off against on.

- Gate: on the gold file, clearly more questions with the wanted source among the 4 passages; the CI retrieval
  benchmark not below `ci-baseline.json`; the must-refuse set of `refused-questions.yaml` unchanged; added time
  per question stated (retrieval time is what decides prod's 504s).
- If it does not pass as it is, the finding is what it gets wrong; a change to it is then its own step.

### Q2. Sources that never become candidates (only if Q0 shows whole kinds of source are absent)

For a question with no standard named, find out why no passage of the legislation, a profile or an overview file
enters the candidate list: scope cut to the first standard, a filter, the candidate count, or scores that never
compete with schema text. The fix follows the cause and is general: for example a share of the candidate list
kept for each kind of source the index holds, so that the scoring can choose among them.

- Gate: as Q1, plus: on the 140 benchmark questions no question loses its expected source from the top 10.

### Q3. Ordering (only if Q0 shows passages that are candidates but fall below the cut)

"What is OpRa used for?" is the pattern: an overview file under four schema files. The code already has hints
for explanation questions and document types; measure what they do for these questions before adding anything.

- Gate: as Q1.

### Q4. The model's verdict (last, and only if Q1 to Q3 leave wrongly refused questions)

Two questions were refused although the cited passages answer them, and the verdict changes between runs on the
same evidence. First measure: 20 questions of the gold file and 20 of the must-refuse set, 5 runs each, with the
evidence fixed, how often the verdict changes. Only then decide between a prompt change and leaving it.

- Gate for any change: over 5 runs each, no must-refuse question answered more often than before; wrongly refused
  answered clearly more often; the answers read against their citations.

## 4. What is measured in every step

- **Found**: the wanted source is among the 4 passages the model gets.
- **Refused wrongly** and **answered beside the point** (an answer none of whose citations is a wanted source),
  on the gold file, through the API.
- **Must-refuse**: the 25 questions of `refused-questions.yaml`; none newly answered.
- **The CI retrieval benchmark** against `ci-baseline.json`.
- **Time**: retrieval and total, per question, median and 90th percentile.
- Where a count rests on the model (a verdict, an answer), 3 runs at least, and the spread stated.

## 5. Not planned

- More keyword rules or word lists for single questions.
- A new embedding model (the trial of 2026-11-08 found none better on concept matching).
- A larger number of passages for the model as the first move: it costs time and money on every answer and hides
  the cause. It is a fallback if Q0 shows passages just below the cut everywhere.
- Changes to refusing itself (#523 covers that).

## 6. Order and cost

Q0 first, about a day, and useful on its own: it is a measuring tool the retrieval work has lacked. Q1 to Q3
only as Q0's table says, each about a day with its runs. Q4 last. Each of Q1 to Q3 can make prod slower or change
many answers, so none ships without its gate and Andrej's word.

## 7. Risks

- **The gold file is written by us**, and "the source that answers" is a judgement. Andrej reviews it; where two
  sources answer, both are listed.
- **Dev and prod indexes differ** (the record found DATEX II indexed on prod; the content was not compared).
  Q0's table is for dev; before a step ships, the questions it should fix are asked on prod. (Q0: DATEX II is
  indexed on dev as well, 1,240 model chunks and the v3.7 documentation; every wanted source of the gold file is
  in the dev index.)
- **A fix for these questions makes others worse.** That is what happened with plural matching and coverage
  ranking. Hence the 140-question gate on every step.
- **The first look may mislead**: it used the bare retrieval call. Q0 measures the app's real path.

## 8. Results

### Q0 (2026-11-14, dev, 0.97.221)

**Finding.** The passages are lost at two places, not spread over many. 57 gold questions asked as the chat page
asks them (no scope): 29 reach the model's 4 passages, 17 never become candidates, 11 are candidates but end
below a cut. Of the 17, 6 are not even searched: their source (EU legislation, mobilityDCAT-AP) is an opt-in scope
that a question without a named source never searches. The other 11 are searched, but their wanted passage is
74th to 12,142nd by vector similarity, where the pool takes the nearest 30; all 11 are in everyday words. With the
fitting scope sent as `standardsScope`, 33–34 of 57 are found, 10 are still never candidates (the same everyday
questions), and 13–14 are candidates below a cut. The 140 benchmark questions are lost elsewhere: 114 of 139 found,
22 of the 25 losses are candidates ranked below a cut, 2 are not candidates. So the gold questions lose their
passages where the benchmark does not look (finding), and both lose them by ordering.

All numbers **measured** with `locate_answer_sources`, unless marked.

**How retrieval works on the app's path** (read from `api/views.py` and `retrieval_gateway.py`, and confirmed by
the probe on every question):

1. The view renders a non-English question in English (one model call) and searches both: the question as asked and
   the rendering, each through the whole pass below; the two results are interleaved, the rendering first, and cut
   to 6. Scope: the request's `standardsScope`, else the standards the parser finds in the question. With no scope,
   the opt-in sources (EU legislation, mobilityDCAT-AP, NAPCORE, INSPIRE, DATEX II, TN-ITS) are not searched at all
   (`_scope_query_filter`).
2. Candidates: the 30 nearest chunks by vector (`max(25, 5 × top_k)`; the text rank only breaks ties at the 30th),
   a separate 30 for each opt-in source when the scope names several, up to 8 chunks with the question's rare
   terms, path hints, GraphDB examples and Transmodel definitions, element chunks and graph alias candidates (cap 12
   on dev). There is no separate full-text candidate list while vectors are semantic; full text is only the
   fallback without pgvector.
3. Preselection to 32 (`RETRIEVAL_SCORING_CANDIDATE_CAP`), scoring, `min_score` 0.62 (topped up to 4 with the best
   below it), schema definitions and relation paths added, sorted, per-file cap (1 on dev, 2 by default), MMR
   diversification to top_k = 6, coverage of named elements and services, legal-status provisions and named
   examples inserted after the first passage.
4. Scope coverage: a searched standard missing from the 6 is searched alone and its best 2 inserted (these passes
   run with `min_results` 0, so nothing below 0.62 survives them).
5. The view puts "does X exist / how is X defined" definitions first (`presence_evidence`), and for example questions
   replaces the evidence with the example's element evidence. The model gets the first 4 with text.

**Counts per step.** "Lost at" is the first step after the last one the passage is in. Three runs each, with
fresh English renderings and different hash seeds; the unscoped runs gave the same step for all 57 in all three,
the scoped runs differ in one question (a15).

| Lost at | gold, no scope | gold, fitting scope | benchmark (139), no scope |
|---|---|---|---|
| found (among the 4 passages) | 29 | 33–34 | 114 |
| not a candidate: source not searched (opt-in scope) | 6 | 0 | 0 |
| not a candidate: searched, vector rank beyond the pool | 11 | 10 | 2 |
| preselection cap (32) | 1 | 0 | 2 |
| min_score | 1 | 1 | 1 |
| top_k cut (6, after diversification) | 3 | 5 | 10 |
| merge of the two searches | 1 | 1 | 0 |
| view additions (presence definitions first) | 1 | 1 | 1 |
| prompt cut (4) | 4 | 5–6 | 9 |

Never the loss step: the per-file cap, the scope filter in scoring, the coverage step, scope coverage. Two benchmark
questions (q025, q032) are left out: their pattern `VehicleLoadEntry` matches nothing in the index.

By kind (gold, found of all, no scope → fitting scope): everyday 13/27 → 13/27, legislation 7/13 → 9/13,
overview 7/12 → 7/12, profile 1/3 → 3/3, element 1/2 → 1/2.

Keyword rules: 14 of the 57 (a01–a14) are refused before retrieval on prod as it is (relevance check off); the table
measures them as if let through.

**What it supports.**

- **Q1 (wording gap): supported, 10 questions** (11 without scope): a06, a11 (no scope only), a12, a21, a22, b20–b24,
  b30. Their wanted passage is 74th to 11,918th by vector similarity in the right scope; rare-term recall adds
  nothing (the question's words are not in the sources). No reordering can reach them; they need other search
  terms. The existing vocabulary bridge is the candidate, as planned.
- **Q2 (sources never candidates): supported, 6 questions, and the cause is the scope, not the scores.** a01, a13,
  a14 (legislation), a08, a17 (profile) and b16 (parsed to NAPCORE, the regulation not searched). With the fitting
  scope all 6 become candidates and 3 are found (a01, a08, a17); a13, a14, b16 are then lost by ordering. Two more
  show the same in a mixed scope: b10 ("What is INSPIRE?", searched in INSPIRE and EU legislation, Directive Art. 1
  below min_score) and b17 (NAPCORE and EU legislation, MMTIS cut at preselection) are found when only EU
  legislation is searched. This agrees with the prod check the coordinator ran today (11 of 14 answered with a
  scope; **reported to me, not re-measured**). The fix is a scope decision for questions that name no source, not a
  share of candidates by kind.
- **Q3 (ordering): supported, 10 gold questions (13–14 with the scope) and 22 of the 139 benchmark questions.**
  Patterns: an overview README under schema files (a15 9th of 32, b01 21st, b02, b05), the Annex under articles of
  the same act (a16, 23rd of 29 even in EU legislation alone), and presence definitions put before the retrieved
  passage (b26, b27, benchmark q053, q063: the passage was 1st to 3rd, the definitions moved it out of the first 4).
  Passages just below the cut (5th or 6th of 6, lost at the prompt cut): 4 gold (5–6 with scope), 9 benchmark.
- **Not supported:** that the pool size is the cause. The pool being smaller than top_k=60 in the first look is the
  preselection and per-file caps (§1); in the app's path the preselection cap is the loss step for 1 gold and 2
  benchmark questions. Nothing here points at plural forms, coverage ranking or related-match expansion.

**Determinism.** Everything up to the graph alias candidates is deterministic for a fixed question, scope and
rendering. `_graph_concept_candidates` returns different chunks between calls, in one process too (measured on
"What fields are included in PlannedServiceDimensions?": vector pool, rare terms, definitions identical, graph
candidates and everything after different); that makes 7 of the 149 benchmark questions differ between runs in
graph mode (0 without graph). In the gold runs it changes one question (a15: found in 1 of 3 scoped runs). The
English rendering is the only model call; three fresh renderings differed in wording for 5 of the 15 non-English
questions and changed no step. Not model-dependent otherwise: the example generator ran with the model off; one gold
and three benchmark questions used a standard example, none needed a generated one.

**Behaviour unchanged.** The probe is a `ContextVar` that is `None` in the app; the gateway's results with it off were
compared on the 149 benchmark questions (top_k 20, both modes, full chunk lists and scores) against three runs of
unchanged main: without graph identical in all 149; with graph identical in 142, and the other 7 differ between
the runs of main themselves (3 different results in 3 runs for 6 of them). A test checks that the same retrieval
gives the same chunks and scores with the probe on and off. The added cost when off is one context lookup and about
20 `is None` checks per pass (**believed** negligible; not timed separately).

**Dev settings that differ from the defaults** (and possibly from prod, whose `.env.prod` I did not read):
`RETRIEVAL_MAX_SAME_SOURCE_PATH` 1 (default 2), `GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS` 12 (default 36,
`.env.prod.example` 12). The per-file cap was never the loss step here.

**Not checked.** Whether the 4 passages would make the model answer (that is the "found" of §4 through the API, for
the step that changes something). The FAQ route: 3 gold and 23 benchmark questions match an FAQ entry well enough
that the controller model decides the route; I measured the RAG route (the prod log shows the RAG route's presence
definitions for a21).

Raw outputs are outside the repository. To repeat: `manage.py locate_answer_sources [--fitting-scope]
--translations <file>`, and `--input helpdesk/benchmarks/benchmark-questions.yaml` for the benchmark.

**Next.** Q2 and Q1 both have a clear cause and a measurable gate. I would do Q1 first, because it costs no code:
the vocabulary bridge off against on, on the 57 with and without scope; gate as in §3 plus at least 5 of the 11
wording questions found. Then Q2 as a scope decision for questions that name no source (gate: the 6 found or
candidates, and no benchmark question loses its source from the 4 passages). Q3 last, starting with the presence
definitions that push a retrieved passage out of the first 4, since that one is a single mechanism.

Per question (step in each of the three runs when they differ; rank after scoring = the passage's place in the
sorted candidates of the better of the two searches; "–" = not among them, or added after scoring, as the presence
definitions of a04 and a05; vector rank = exact rank by similarity among the searched chunks):

| id | question | kind | no scope: lost at | rank after scoring | vector rank | fitting scope | with it: lost at | rank after scoring | vector rank |
|---|---|---|---|---|---|---|---|---|---|
| a01 | Which formats count as machine-readable? | legislation | not a candidate | – | not searched | EU legislation | **found** | 6/11 | 5 |
| a02 | Make a example file of observed delays. | everyday | **found** | 1/17 | 1 | OpRa | **found** | 1/20 | 1 |
| a03 | How are parkings defined in standards? | everyday | **found** | 1/4 | 1 | NeTEx | **found** | 1/4 | 1 |
| a04 | How do I describe a lift in a station? | everyday | **found** | – | 68 | NeTEx | **found** | – | 65 |
| a05 | How do I describe an escalator in a station? | everyday | **found** | – | 278 | NeTEx | **found** | – | 275 |
| a06 | How do I describe an elevator in a station? | everyday | not a candidate | – | 4369 | NeTEx | not a candidate | – | 4293 |
| a07 | What is seat capacity? | everyday | **found** | 1/6 | 1 | NeTEx | **found** | 1/5 | 1 |
| a08 | Kaj so to metapodatki? | profile (sl) | not a candidate | – | not searched | mobilityDCAT-AP | **found** | 3/4 | 1 |
| a09 | Kaj je vozni red avtobusa? | everyday (sl) | **found** | 1/4 | 78 | NeTEx | **found** | 1/4 | 78 |
| a10 | kaj je vozni red? | everyday (sl) | **found** | 1/11 | 1 | NeTEx | **found** | 1/8 | 1 |
| a11 | How to model number of late journeys? | everyday | not a candidate | – | 630 | OpRa | prompt cut | 10/19 | 15 |
| a12 | How to describe a bus ticket? | everyday | not a candidate | – | 1017 | NeTEx | not a candidate | – | 980 |
| a13 | How are static data described? | legislation | not a candidate | – | not searched | EU legislation | top_k cut | 7/9 | 13 |
| a14 | How are dynamical data described? | legislation | not a candidate | – | not searched | EU legislation | min_score | – | 17 |
| a15 | What is OpRa used for? | overview | prompt cut | 9/32 | 1 | OpRa | **found** / prompt cut / prompt cut | 8/32 | 1 |
| a16 | Which fare data must be provided to be in accordance with… | legislation | top_k cut | 23/29 | 7 | EU legislation | top_k cut | 23/29 | 7 |
| a17 | What if my dataset is available in several formats? | profile | not a candidate | – | not searched | mobilityDCAT-AP | **found** | 2/8 | 4 |
| a18 | How to define a location of a parking bay in DATEX? | element | **found** | 1/6 | 1 | DATEX II | **found** | 1/7 | 1 |
| a19 | How are DATEX and SIRI connected? | overview | **found** | 24/32 | 75 | SIRI | top_k cut | 7/28 | 3 |
| a20 | In which legislation is DATEX. included? | legislation | **found** | – | 1843 | EU legislation | **found** | 3/17 | 1 |
| a21 | How do I describe an elevator in a station in NeTEx? | everyday | not a candidate | – | 636 | NeTEx | not a candidate | – | 636 |
| a22 | How do I describe an elevator in a stop place? | everyday | not a candidate | – | 12142 | NeTEx | not a candidate | – | 11918 |
| a23 | when describing the calendar of a service journey, how to… | element | prompt cut | 7/39 | 1 | NeTEx | prompt cut | 7/35 | 1 |
| b01 | What is SIRI used for? | overview | top_k cut | 21/32 | 1 | SIRI | top_k cut | 21/32 | 1 |
| b02 | Wofür wird SIRI verwendet? | overview (de) | merge of the two searches | 6/30 | 1 | SIRI | merge of the two searches | 6/30 | 1 |
| b03 | what is NETEX? | overview | **found** | 2/20 | 1 | NeTEx | **found** | 2/20 | 1 |
| b04 | What kind of data does OpRa exchange? | overview | **found** | 1/10 | 1 | OpRa | **found** | 1/10 | 1 |
| b05 | Kannst du mir einfach erklären, was NeTEx, SIRI und OpRa … | overview (de) | prompt cut | 1/32 | 1 | NeTEx, SIRI, OpRa | prompt cut | 1/32 | 1 |
| b06 | Kako je Opra povezana z NeTEx? | overview (sl) | **found** | 1/32 | 1 | OpRa | **found** | 1/32 | 1 |
| b07 | What are parts of SIRI? | overview | **found** | 5/31 | 1 | SIRI | **found** | 5/31 | 1 |
| b08 | what is the cen reference of netex ? | overview | **found** | 1/31 | 1 | NeTEx | **found** | 1/31 | 1 |
| b09 | What is DATEX? | overview | **found** | 2/22 | 1 | DATEX II | **found** | 2/22 | 1 |
| b10 | What is INSPIRE? | overview | min_score | – | 105 | EU legislation | **found** | 4/4 | 5 |
| b11 | What is a national access point? | legislation | **found** | 1/16 | 1 | EU legislation | **found** | 1/14 | 1 |
| b12 | Which standard must be used for static travel data under … | legislation | **found** | 1/24 | 1 | EU legislation | **found** | 1/24 | 1 |
| b13 | Hvilke standarder krever MMTIS-forordningen for statiske … | legislation (no) | **found** | 2/19 | 3 | EU legislation | **found** | 2/19 | 3 |
| b14 | Como operador de uma rede nacional de autocarros, que cat… | legislation (pt) | **found** | 1/4 | 1 | EU legislation | **found** | 1/4 | 1 |
| b15 | Which formats machine-readable as specified in the MMTIS … | legislation | **found** | 2/18 | 2 | EU legislation | **found** | 2/18 | 2 |
| b16 | What are metadata in NAP used for? | legislation | not a candidate | – | not searched | EU legislation | prompt cut | 6/6 | 4 |
| b17 | Kaj so metapodatki v NAP? | legislation (sl) | preselection cap | – | 1886 | EU legislation | **found** | 2/7 | 6 |
| b18 | What is TEL-TSI and how is it connected to Transmodel rel… | legislation | **found** | 1/26 | 1 | EU legislation | **found** | 1/19 | 1 |
| b19 | What is a Dataset in mobilityDCAT-AP? | profile | **found** | 3/32 | 3 | mobilityDCAT-AP | **found** | 3/32 | 3 |
| b20 | Where can a passenger buy tickets in NeTEx? | everyday | not a candidate | – | 1873 | NeTEx | not a candidate | – | 1873 |
| b21 | Kje lahko potnik kupi vozovnico v NeTEx? | everyday (sl) | not a candidate | – | 1709 | NeTEx | not a candidate | – | 1709 |
| b22 | How to describe a bus fare? | everyday | not a candidate | – | 210 | NeTEx | not a candidate | – | 210 |
| b23 | Kako NeTEx opisuje cene vozovnic? | everyday (sl) | not a candidate | – | 74 | NeTEx | not a candidate | – | 74 |
| b24 | Kako je postaja definirana v NeTEx? | everyday (sl) | not a candidate | – | 2342 | NeTEx | not a candidate | – | 2342 |
| b25 | Wie beschreibt man eine Haltestelle in NetEx? | everyday (de) | **found** | 3/29 | 122 | NeTEx | **found** | 3/29 | 122 |
| b26 | comment sont définis les arrêts flexibles en NeTEx ? | everyday (fr) | view additions | 2/30 | 1 | NeTEx | view additions | 2/30 | 1 |
| b27 | How are e charging stations represented in NeTex ? | everyday | prompt cut | 1/32 | 66 | NeTEx | prompt cut | 1/32 | 66 |
| b28 | How to model a train? | everyday | **found** | 1/23 | 58 | NeTEx | **found** | 5/21 | 45 |
| b29 | How are operators linked to lines? | everyday | **found** | 1/12 | 14 | NeTEx | **found** | 1/10 | 12 |
| b30 | How is NeTEx exchanging data about public transport lines? | everyday | not a candidate | – | 235 | NeTEx | not a candidate | – | 235 |
| b31 | What is canceled journey? | everyday | **found** | 2/27 | 6 | OpRa | **found** | 1/24 | 3 |
| b32 | How to model number of passengers driven in OpRa? | everyday | top_k cut | 12/31 | 14 | OpRa | top_k cut | 12/31 | 14 |
| b33 | Any timetable from Slovenia? | everyday | **found** | 1/28 | 1 | NeTEx | **found** | 1/26 | 1 |
| b34 | Prikaži primer voznega reda v NeTEx XML iz Slovenije? | everyday (sl) | **found** | 1/4 | 1 | NeTEx | **found** | 1/4 | 1 |

### Q1 (2026-11-14, dev, 0.97.221): the vocabulary bridge as it is

**Verdict: the gate fails, on every count but the must-refuse set.** With the bridge on, 2 of the 11 wording
questions reach the 4 passages in at least 2 of 3 runs (gate: 5); 9 gold questions found today are lost in at
least 2 of 3 runs (gate: 0); the 140 benchmark questions found go from 114–115 to 109–111; the retrieval benchmark
on the dev index drops from hit@10 0.886 to 0.785. No must-refuse question is newly answered. Retrieval takes about
5 s more per question. I do not recommend switching it on in prod. All numbers **measured**, unless marked.

**What the bridge does** (read from `vocabulary_bridge.py` and `retrieval_gateway.py`):

- Called once per retrieval pass with graph mode on, after concept extraction, with the pass's question text: the
  question as asked and, for a non-English question, its English rendering separately (two calls, one after the
  other). The scope-coverage passes reuse the reply (`lru_cache` on the question text, per process; in a running
  server a repeated question costs nothing).
- It asks the controller model (dev: Claude Haiku 5.5, effort low) for at most 6 Transmodel/NeTEx concept names
  "in the models' own wording" that the question refers to. The quoted strings of the reply are matched to class
  labels (`concepts_named_by_terms`, the longest matching label wins); a concept whose label the question already
  mostly spells out is dropped (`_described_in_other_words`).
- The concepts are added to the question's concepts. They do **not** reach the vector query: with semantic vectors
  the query text is the question alone (`_build_query_embedding_input`), and the 30 nearest chunks are the same as
  with the bridge off. They do not reach the rare terms or the keyword refusal either (the parser and
  `semantic_abstention` never call the bridge). They enter: property concepts, graph expansion and so the graph alias
  candidates (cap 12 on dev), the GraphDB definitions (`ontology-definition` chunks), the element candidates (up to
  4 elements × 6 chunks), GraphDB examples for example questions, the graph and definition boosts in scoring, the
  element coverage step and relation paths. Definitions and element chunks are exempt from the preselection cap.
- Timeout `VOCABULARY_BRIDGE_TIMEOUT_SECONDS` = 3 per attempt, with one retry in the Anthropic client, so a failed
  call takes up to about 6.5 s. Any failure is logged and the bridge adds nothing. On the Anthropic provider it is
  enabled only when `CONTROLLER_LLM_API_BASE_URL` is also set (not used by that provider). CI runs with
  `CONTROLLER_LLM_ENABLED=False`, so the CI retrieval benchmark never calls it.
- Cost: one controller call (at most 200 tokens plus the reasoning allowance, 1000 on dev) per English question, two per non-English one.
  Measured call time over 3 × 71 gold and 3 × 141 benchmark calls: median 2.8–2.9 s, 90th percentile 6.5 s;
  **20–27 % of the gold calls and 31–38 % of the benchmark calls failed with a timeout**, so on a fair share of
  questions the bridge silently did nothing (the dev stack had other load at the time; prod's rate is not known).

**How it was measured.** `locate_answer_sources --bridge on|off --bridge-terms <file>` (this branch): the bridge's
replies are stored per question text with their time or error, a stored error is raised again. Unscoped runs asked
the model afresh (3 samples of terms, `terms-1..3`); the scoped runs reused the same 3 files, so scoped and unscoped
run k compare later stages on the same terms. English renderings fixed to one file for all runs. Off: 3 runs each.

**Found among the 4 passages** (3 runs each):

| | off | on | found off ≥ 2/3, on < 2/3 | found on ≥ 2/3, off < 2/3 |
|---|---|---|---|---|
| gold, no scope | 29, 30, 30 | 25, 26, 22 | 9: a09, a10, a15, a18, b08, b11, b12, b29, b33 | 3: a23, b20, b21 |
| gold, fitting scope | 33, 33, 34 | 30, 30, 25 | 9: a09, a10, a18, b08, b11, b12, b17, b29, b33 | 3: a23, b20, b21 |
| benchmark (141, no scope) | 115, 114, 114 | 111, 109, 110 | 6: q060, q061, q062, q072, q121, q131 | 4: q013, q016, q083, q144 |

Retrieval benchmark, graph mode, on the dev index (semantic vectors, GraphDB; not comparable with `ci-baseline.json`,
which is the CI index with hash vectors), one run each: off hit@5 0.772, hit@10 0.886, MRR@10 0.569; on 0.685,
0.785, 0.524.

**The 11 wording questions** (no scope; scoped the same, except a11 which with OpRa as scope is a candidate cut at
the prompt in all runs, on and off). Pool = rank among the candidates, scored = rank after scoring.

| id | terms returned (3 runs, abridged) | wanted passage, on | in short |
|---|---|---|---|
| a06 elevator in a station | ACCESS SPACE, STOP PLACE, PATH LINK, LEVEL, ACCESSIBILITY … | never a candidate | terms beside the point: no equipment term |
| a11 number of late journeys | SERVICE / DATED VEHICLE JOURNEY, RECORDED CALL; 1 timeout | not a candidate 2×, top_k cut 1× (scored 21) | wrong model: the prompt names Transmodel and NeTEx, the answer is in OpRa |
| a12 bus ticket | TRAVEL DOCUMENT, FARE PRODUCT, USAGE PARAMETER …; 1 timeout | candidate (pool 60), scored 2nd and 14th, lost at the prompt cut and the view's presence definitions; 1× no candidate | right terms; lost by ordering after the pool |
| a21 elevator in a station in NeTEx | STOP PLACE, ACCESS SPACE, ACCESSIBILITY ASSESSMENT … | candidate 1× (graph, scored 20), else none | terms beside the point |
| a22 elevator in a stop place | same kind | never a candidate | terms beside the point |
| b20 where to buy tickets | DISTRIBUTION OUTLET / CHANNEL, SALES OFFER PACKAGE, RETAILER; 1 timeout | **found 2 of 3** (graph candidates, scored 7–8) | works; the miss is the timeout |
| b21 same, Slovenian | DISTRIBUTION CHANNEL, SALES OFFER PACKAGE … (2 calls) | **found 3 of 3** (scored 10–13) | works |
| b22 bus fare | FARE PRODUCT, FARE TABLE, FARE STRUCTURE ELEMENT | never a candidate | right terms, but the 2–4 concepts' graph candidates and definitions do not include the fare product / price schema files |
| b23 fare prices, Slovenian | FARE PRODUCT, PRICE GROUP, FARE TABLE …; 1 timeout | candidate 2× (scored 11, 18), top_k cut | right terms; lost by ordering |
| b24 station, Slovenian | STOP PLACE, STOP PLACE COMPONENT | scored 1st in all 3, lost at the prompt cut | right term; ordering after retrieval |
| b30 lines | LINE, NETWORK, ROUTE, PUBLICATION DELIVERY; 1 timeout | found 1 of 3 (scored 2) | timeout in one run, not a candidate in the third |

**What it gets wrong**, in general terms:

1. **It is applied to every question, and its concepts are treated as if the question named them.** For questions
   that were found without it (a timetable from Slovenia, what a national access point is, which standard MMTIS
   requires) the model returns broad model terms (LINE, SERVICE JOURNEY, STOP PLACE, DATA SOURCE, PUBLICATION
   DELIVERY). Their element chunks (up to 24) and definitions (up to 12) are exempt from the preselection cap of 32,
   so the room left for the vector pool falls to 0–12, and the passage that was nearest by vector (b11, b12, b33:
   vector rank 1) is cut before scoring. 7 of the 9 gold losses are lost at the preselection cap in at least one run;
   the others (a10, b08) and the remaining runs are lost behind the added chunks at the coverage step, the top_k cut
   or the prompt cut.
2. **Where the terms are right, the wanted passage enters only through the graph candidates and definitions**, never
   the vector pool (the query text is unchanged), and then has to win against the passages the vector pool brought.
   It does for the sales-distribution questions (b20, b21); for a12, b23, b24 it becomes a candidate but is cut by
   ordering (Q3's subject), and for b22 the concepts' graph candidates do not contain the wanted file.
3. **The terms are beside the point for equipment** (the 3 elevator questions: always spaces and accessibility, never
   the equipment) and for a question whose answer is in OpRa (the prompt asks for Transmodel and NeTEx names).
4. **A quarter to a third of the calls time out**: at a 3 s timeout the call's median of 2.9 s is a coin toss, and a
   failure costs 6.5 s for nothing.

**The one change I measured**, from finding 1: element candidates only for the concepts the question names, not for
the bridged ones (`question_element_names = concept_element_names(question_concepts - bridged_concepts)`, which also
takes them out of the element boost and the coverage step; definitions, graph candidates and scoring unchanged).
Measured on the same stored terms, gold without scope, 3 runs: found 30, 30, 29 (off 29, 30, 30); losses down from 9
to 2 (a09, a10, the Slovenian timetable); wording questions found 2 of 11 (b20, b21, now 2 of 3 each). Retrieval
benchmark (fresh calls, one run): hit@5 0.711, hit@10 0.879, MRR@10 0.545. It removes most of the damage but finds no
more wording questions, so it cannot reach the gate. Not committed.

**Through the API** (two host servers from this branch, bridge off on 8011 and on on 8012, relevance check off as on
prod, 3 runs each; the server's cache means runs 2 and 3 reuse run 1's terms, as prod would):

- Must-refuse set (25): off, "What does GTFS say about stop times?" answered 3 of 3 and "How does it work?" 1 of 3;
  on, none answered. No question newly answered.
- Newly found: b20 ("Where can a passenger buy tickets in NeTEx?") answered 3 of 3 from the sales-distribution and
  sales-offer-package schemas with two fare examples, on the question; off it cited neither. b21 (the
  same in Slovenian) answered 2 of 3 from the wanted sources, refused once on the same evidence. b30 refused 3 of 3
  on and off.
- Made worse: "Any timetable from Slovenia?" (b33) refused 2 of 3 on ("the blocks do not mention Slovenia"; off: answered
  from the Slovenian example 3 of 3); "Hvilke standarder krever MMTIS …" (b13) refused 3 of 3 for insufficient evidence
  (off: answered from the regulation 3 of 3); "How are operators linked to lines?" (b29) answered from organisation
  definitions instead of the line schema, and refused once.
- a06, a09–a12 are refused by the keyword rules before retrieval on both (relevance check off), so the bridge cannot
  help them in the app as prod is configured; that needs the relevance check on as well.

**Time** (the dev stack had other load during all runs; off and on ran at the same time, so the difference is
**believed** fair, the absolute values high):

| | off median / p90 | on median / p90 |
|---|---|---|
| retrieval, gold, locate (fresh calls) | 2.5 / 5.2 s | 8.2 / 12.5 s |
| retrieval, benchmark, locate (fresh calls) | 1.8 / 3.0 s | 6.9 / 8.6 s |
| API, 16 retrieved gold questions, first run: retrieval | 2.7 / 7.4 s | 7.7 / 12.1 s |
| API, same: total | 8.9 / 19.1 s | 15.9 / 25.5 s |

Of the added time, the bridge call is about 2.9 s (median of the stage); the rest is the extra graph, element and
scoring work for the added concepts and, for non-English questions, the second call. For prod's 504s (proxy 120 s,
retrieval CPU) this is a large step in the wrong direction.

**Options not built** (each would be its own step with this gate):

- **The bridge's terms in the vector query**: embed the question together with the bridged labels (or search a second
  time with them), so the wanted passage can enter the nearest 30. This is the stage the wording gap is at; it needs
  a second vector search per pass (about 2 s on dev) and its own measure of what generic terms do to the pool.
- **The bridge only when the question names no concept of its own**, so answered questions are not touched. Measured
  here not to separate the cases: 3 of the 9 losses (a09, a10, b08) also have no concept of their own.
- **A longer timeout or no retry**: removes the coin toss but makes the added time worse; only worth it with the call
  moved off the critical path (in parallel with the English rendering, for example).
- **OpRa and SIRI names in the prompt**, and equipment as a kind of concept: would address a11 and the elevator
  questions; a prompt change measured on the same gate.
- **Query expansion of our own, a synonym list, HyDE**: not built, as instructed; HyDE would need one answer-model
  call per question and a second vector search.

**Recommendation.** Leave `VOCABULARY_BRIDGE_ENABLED` off in prod. Q1 as planned ("the existing bridge, no code")
does not close the wording gap; the measurements point at the vector query as the stage that must see other words,
which is a new mechanism and needs Andrej's decision before it is built. Q2 (scope for questions that name no source)
does not depend on it and can go first.

Raw outputs are outside the repository. To repeat: `manage.py locate_answer_sources --bridge on --bridge-terms <file>
[--fitting-scope] --translations <file>`; with `--no-model` a stored reply is used and a missing one adds nothing.
