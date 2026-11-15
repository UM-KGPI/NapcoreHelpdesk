# Plan: suggested questions when the helpdesk cannot answer

Written 2026-11-15 against 0.97.225, for the implementer. Related: the record `2026-11-14-refused-questions.md`
(why questions are refused), the plan `2026-11-14-retrieval-misses.md` (why the answering passage is not found),
and the clarifying-choice plan (PR #526, not merged), whose first step failed. Each claim is labelled
**measured**, **believed** or **assumed**.

## 1. The idea

When the helpdesk refuses, the user gets a text that says so and nothing to do next. Many assistants and
helpdesks offer a next step there: two or three better questions the user can click.

The idea: under a refusal, show up to three questions that are close to what the user asked and that the helpdesk
can answer. A click asks that question.

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
- **Measured** (C0 of the clarifying-choice plan): offering the user a scope to choose (NeTEx, SIRI, EU
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
- A choice of scope (C0 failed, see §2). PR #526 holds that plan and its record; this plan replaces its idea.
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
