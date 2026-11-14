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
The model sees 4 passages (`LLM_MAX_EVIDENCE_CHUNKS`); retrieval is asked for 6.

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
returned more than 27 candidates although 60 were asked for.

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
  Q0's table is for dev; before a step ships, the questions it should fix are asked on prod.
- **A fix for these questions makes others worse.** That is what happened with plural matching and coverage
  ranking. Hence the 140-question gate on every step.
- **The first look may mislead**: it used the bare retrieval call. Q0 measures the app's real path.

## 8. Results

(Each step records its numbers here.)
