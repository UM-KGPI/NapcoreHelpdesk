# Plan: helping the user clarify a question the helpdesk cannot answer

Written 2026-11-15 against 0.97.225, for the implementer. Related: the record `2026-11-14-refused-questions.md`
(why questions are refused) and the plan `2026-11-14-retrieval-misses.md` (why the answering passage is not
found). This is the one plan for helping the user clarify; it holds the record of the first means tried (a choice
of scope, §8 C0). Each claim is labelled **measured**, **believed** or **assumed**.

## 1. The idea

When the helpdesk refuses, the user gets a text that says so and nothing to do next. Whatever the user types
next is again a new, unrelated question. Two means of giving the user a next step:

1. **A choice of scope** ("Do you mean NeTEx, SIRI or the EU legislation?"), the pick sent with the same question
   as its scope. Tried first (C0, 2026-11-14) and failed: a scope switches off the keyword screen, and vague and
   off-topic questions were then answered (§8 C0).
2. **Suggested questions**: under a refusal, up to three questions that are close to what the user asked and that
   the helpdesk can answer. A click asks that question as an ordinary one. Many assistants and helpdesks offer
   this next step. Steps S0 to S3 below are about this means.

## 2. What is known

- **Measured** (prod log 2026-10-14 to 2026-11-14, about 324 questions from the web page): 52 were refused, 16%.
  23 distinct ones were refused wrongly: the sources answer them.
- **Measured** (prod 0.97.225, 2026-11-15, one run each): after the second opinion on keyword refusals and six
  evidence passages, 14 of those 23 are answered and 9 are still refused. Refusals will stay: some are right (the
  sources do not answer the question), some are wrong and not fixed yet.
- **Measured** (the same log): after a refusal users do try again, and it fails. Follow-ups like "Can you explain
  that better …" were refused, because every question is answered on its own and the follow-up means nothing
  without the turn before.
- **Measured** (prod, 2026-11-15): "Kaj so to metapodatki?" was refused at the keyword screen. The helpdesk holds
  two sources that answer it in the sense a user of a National Access Point means (mobilityDCAT-AP, the MMTIS
  regulation), and the user had no way to know which words would get there.
- **Measured** (C0, §8): offering the user a scope to choose (NeTEx, SIRI, EU
  legislation …) fails. A question sent with a scope skips the keyword screen and the second opinion, and 9 of the
  25 questions that must be refused were then answered.
- **Measured** (code): the page already shows questions of other users ("Inspiring questions": the latest liked
  questions, `TrendingQuestionsView`). They are not related to what the user asked.
- **Measured** (code): a refusal comes from one of four places: the keyword screen with the second opinion
  (before any search, fixed text), nothing retrieved, the policy check, and the answer model's verdict that the
  evidence does not answer the question (after the search, with the passages cited).
- **Believed**: for most wrongly refused questions the index holds passages near the question, so questions that
  those passages answer can be offered. For the refusals by the model's verdict this is visible today (3 to 6
  passages are cited under the refusal). For refusals at the screen no search runs, so it is not known.
- **Not usable as a trigger** (**measured**): the confidence number (0.94 on nearly every answer).

## 3. Principles

- **A suggestion is a whole question.** It can be read and asked alone. A click sends it as a new, ordinary
  question, without a scope and without the earlier turn. So the screen, the search, the answer checks and the
  log work as they do today, and the fault of C0 (a scope that skips the screen) cannot occur.
- **Only what the helpdesk can answer.** A suggestion is shown only when a check before showing it says the
  sources answer it. A suggestion that is refused when clicked is worse than no suggestion.
- **Related, not "did you mean".** The helpdesk does not claim to know what the user meant. The line above the
  suggestions says that these are related questions it can answer.
- **Nothing for a question that is not about the sources.** A question about the weather gets the refusal alone.
- **In the language of the question.**
- **General mechanisms only.** No list of suggestions per topic, no rule that names a standard's element, a noun
  of a question or a benchmark question.

## 4. Steps

One PR per step. Nothing changes for users before S0's gate is met.

### S0. Can good suggestions be made? (no change of behaviour)

A command that, for a refused question, produces up to three suggestions in each of the ways below, and measures
them. Ways to compare, all from what exists:

1. **From the passages near the question.** Search all indexed sources for the question (also the sources an
   unscoped question does not search today), take the best passages, and have the controller model write for
   each of up to three passages one question that this passage answers and that is as close as possible to the
   user's question. One model call. The model gets only the question and the passages.
2. **From questions already answered.** The nearest earlier questions in the log (by the embedding of the
   question) that were answered, validated, and not disliked. No model call. To check first: whether showing
   another user's question is acceptable in general (the page does it already for liked questions), and that
   nothing personal can be in such a question.
3. **Both**, earlier answered questions first, then written ones.

For each way, measured on the 23 wrongly refused questions, the 25 must-refuse questions
(`refused-questions.yaml`) and the questions of the gold file (`answer-source-questions.yaml`) that are refused
today:

- **Useful**: at least one suggestion that, asked through the API, is answered and cites the source the gold
  file names for the original question. This is the measure that the suggestion leads where the user wanted to
  go, not just somewhere.
- **Dead**: suggestions that are refused when asked.
- **Check before showing**: how well a cheap check (the search finds passages above the score the app needs;
  no model call) predicts that the suggestion is answered, against asking it in full. If the cheap check is not
  good enough, what the full check costs.
- **Must-refuse**: which of the 25 get suggestions, and the suggestions read. The ones that have nothing to do
  with the sources (weather, bread, football, a poem, a capital, a laptop, "hi") must get none. For the ones
  near the sources ("What does NeTEx say about the colour of bus seats?") a related question that the sources
  do answer is acceptable; a suggestion that restates the unanswerable question so that it gets answered is not.
- **Language**: suggestions for the non-English questions are in that language.
- **Stability**: 3 runs; how much the suggestions change, and whether the useful ones stay.
- **Cost**: model calls and seconds added to a refusal, per kind of refusal. A refusal at the screen runs no
  search today, so there the search is added too.

**Gate S0**, for the way that is taken further:

- useful for at least 60% of the wrongly refused questions (23 and the refused gold questions), in 3 of 3 runs;
- at most 10% of the shown suggestions dead;
- none for the must-refuse questions that are not about the sources; no suggestion for the other must-refuse
  questions that leads to an answer of the original, unanswerable question (all read);
- at most 2 s added to a refusal at the median, nothing added to an answered question.

If the gate fails for every way: record it and stop. Do not change the gate after seeing the numbers; a variant
thought of afterwards gets its own run.

### S1. Show them

- The API returns the suggestions with a refusal (a new field of the answer; the OpenAPI contract is updated).
  Both endpoints, JSON and stream.
- The chat page shows them under the refusal as buttons, with one line above them. A click asks the question as
  if the user had typed it. The refusal text itself is unchanged.
- The log records that a question came from a suggestion and from which refusal (a trace field), so S2 can
  measure use. No personal data is added.
- **Gate S1**: S0's numbers hold through the API on the dev stack; must-refuse unchanged (3 runs, none answered
  more often than before); answered questions get no suggestions and no added time; frontend tests for the
  buttons; the page read on a narrow screen.

### S2. Do users take them? (after some weeks on prod)

From the log: of the refusals that showed suggestions, how many were followed by a click; of the clicked ones,
how many were answered, liked, disliked; how many users typed a new question of their own after a refusal, and
how many of those were refused again, compared with the weeks before.

- No gate; the numbers decide whether S3 is worth doing and whether the suggestions stay.

### S3. Beyond refusals (only if S2 shows use)

Suggestions under an answer that is weak: one whose text could not be confirmed against the sources (the page
marks these already). Not under every answer: there is no measure today that says an answer is beside the point.

## 5. Not planned

- A conversation: sending earlier turns to the model. Grounding, the validator and the log rest on one
  self-contained question; that is kept.
- A choice of scope: tried as C0 and failed; the record is §8 C0.
- Suggestions written without passages, from the model's own knowledge of the standards.
- Fixing the refusals themselves; that is the retrieval-misses plan. The two meet: every refusal that plan
  removes is one where no suggestion is needed.

## 6. Risks

- **A suggestion steers the user away from the question they had.** The gold file's wanted source is the
  measure against that in S0; in use, S2's numbers are.
- **Suggestions make refusing look like answering.** For the questions near the sources that must be refused,
  a related question is shown. That is acceptable only when its answer is plainly about the related question.
  S0 reads these one by one.
- **Cost on questions that are not about the sources.** They are refused at the screen in milliseconds today.
  If a search and a model call are added to every one of them, a visitor who types nonsense makes the helpdesk
  work. S0 measures it; a cheap first test (the second opinion already says "not relevant") may be enough to
  skip them.
- **Other users' questions** (way 2) may hold a name or a place. Check what the log holds before using it.
- **57 and 23 questions are few.** A way that passes may be fitted to them. S2 on real use is the proof.

## 7. Order and cost

S0 is a command and a measurement: about a day. S1 is a field in the API, one model call or one query on
refusals, and a few buttons: one to two days. S2 needs only the log and some weeks.

## 8. Results

(Each step records its numbers here, dated.)

### C0 (2026-11-14, against 0.97.221): a choice of scope — gate failed

The first means. The idea: when a question cannot be answered well, offer a short choice of scope ("Do you mean
NeTEx, SIRI or the EU legislation?") and answer the same question again with the pick as its `standardsScope`.
Principles were a choice and not a conversation, one self-contained question again, never only a question back,
and refusing stays safe. The tools are `measure_scope_options` (derive, ask) and the fitting scopes in
`benchmarks/refused-questions-scopes.yaml`, both on this branch.

**Why it looked worth it** (**measured**, prod 0.97.221, the 14 wrongly refused questions of the record, each asked
once with the fitting scope I chose): 11 of 14 answered with the scope, 0 of 14 without. The 9 refused by the
keyword rules were all answered; of the 5 refused by the model's verdict, 2. The answers cited the right kind of
source (the regulation's articles and annexes for machine-readable formats, static data and DATEX in
legislation). That was the best case: my own choice of scope, one run each, answers read from citations and first
lines.

**Gate C0** (fixed before the run): the fitting scope among at most three options for at least 80 % of the wrongly
refused questions; with it, at least two thirds answered from the wanted source; no must-refuse question answered
under any scope that it is not answered under today.

| Gate criterion | Needed | Measured | |
|---|---|---|---|
| Fitting scope among at most three options (23 wrongly refused) | ≥ 80 % | 21 of 23 (91 %), controller model | met |
| With the fitting scope, answered from the wanted source (≥ 2 of 3 runs) | ≥ 2/3 | 16 of 23 (70 %) on dev; on prod believed 15 of 23 (65 %) | met on dev only |
| Must-refuse questions answered under a scope that are refused today | 0 | 9 of 25 (any scope); 4 of 25 under the scopes the controller would offer | not met |

How it was measured (**measured** unless marked): dev stack serving main 0.97.221 (relevance check, vocabulary
bridge and evidence gate off, as prod was then); each question sent with each offered scope, each fitting scope
and none, 3 runs each (399 requests for the 23, 825 for the must-refuse set with all ten scope values). The
fitting scopes are my judgement from the dev index; they agree with the gold file's `fitting_scope`.

Ways of deriving the options, on the 23 (fitting scope among the first 1 / 2 / 3 options):

| Way | @1 | @2 | @3 | Cost per question |
|---|---|---|---|---|
| `candidateStandards` of the semantic parse | 5 | 6 | 6 (17 get no option) | none |
| the same plus the standards the ontology recognised | 7 | 8 | 8 | none |
| standards of the unscoped search | 11 | 15 | 15 | one search, 2.1 s mean |
| standards of a search over every source | 15 | 18 | 20 | 5.0 s mean, 11.9 s max |
| controller model asked which scopes fit (one call) | 20 | 21 | 21 | 1.7 s mean, 4.4 s max |

The controller's @3 was 21 of 23 in three calls; it missed the two static / dynamic data questions (it offered
NeTEx, SIRI, Transmodel, not the legislation that defines the terms) and often spent an option on Transmodel, which
has only 58 passages of its own scope, all shared with NeTEx, SIRI or OpRa.

Answers with the fitting scope: 16 of 23 answered from the wanted source in 2 or 3 of 3 runs, the other 7 refused
in all 3 (three elevator questions, bus ticket, MMTIS fare data, DATEX parking bay, UIC bit field: each a retrieval
fault that a scope does not reach). Two of the 16 were partial (static / dynamic data from the Annex headings
only). On prod the 10 questions that decide this criterion agreed with dev except "What is OpRa used for?"
(refused 3 of 3 on prod), so 15 of 23 on prod, **believed** for the 13 not asked there. On the 34 b-questions of the
gold file the controller named the fitting scope @3 for 33; answered from the wanted source 18 of 34 without a
scope, 21 of 34 with it.

**Why it failed.** A scoped question skips the keyword screen: `has_scope_hint` is true for any non-empty scope,
so neither keyword rule fires and the relevance check is never asked. Vague and off-topic questions then reach
retrieval and the answer model. Under some scope, 9 of the 25 must-refuse questions were answered: "Explain the
data format." (8 scopes), "Is this mandatory?" (8), "What are the rules?" (6), "How does it work?" (5), "What
should I do first?", "Can you help me?", the W3C/OGC ontology question, the NeTEx–GTFS comparison, "is croatian NAP
good?". The answers did not state anything their passages do not support (**believed**, not read in full), but
they are not answers either: "Can you help me?" under Transmodel explains how to open a GitHub issue. Under the
controller's own options, 4 were answered. A plain scope selector, the fallback, has the same fault for all 9.

**What I learned.**

- The controller model can name the fitting source (21 of 23); naming it is not the problem.
- A scope must not switch off the screen. Any API client that sends `standardsScope` gets these answers today.
- Seven of the 23 stay refused with the right scope: those are retrieval faults (the retrieval-misses plan).
- So the second means keeps the scope out of the request: a suggestion is a whole question sent unscoped, through
  the screen, the search and the checks as any question.
