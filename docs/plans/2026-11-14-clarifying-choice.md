# Plan: a clarifying choice when a question cannot be answered well

Written 2026-11-14 against 0.97.221, for the implementer. Related: the record `2026-11-14-refused-questions.md`
(why questions are refused) and the plan `2026-11-14-retrieval-misses.md` (why the answering passage is not
found). Each claim is labelled **measured**, **believed** or **assumed**.

## 1. The idea

Today every question is answered on its own, and the page says so. When a question cannot be answered well, the
helpdesk refuses or answers beside the point, and whatever the user types next is again a new, unrelated question.

The idea: in those cases the helpdesk offers the user a short choice ("Do you mean NeTEx, SIRI or the EU
legislation?"), and the choice is used to answer the same question again, better.

## 2. What is known

- **Measured** (prod log, 324 web questions since 2026-10-18): 52 refused; 15 more carry the existing flag "maps
  to multiple core concepts", which only appends a fixed sentence asking the user to clarify. There is nothing to
  choose, and a reply would be a new question.
- **Measured** (the same log): users do follow up, and it fails. "Kannst du das besser in Textform erklären …" and
  "A mi lahko objasniš …" were refused, because without the turn before they mean nothing.
- **Measured** (code): the API takes a scope with the question (`standardsScope`: Transmodel, NeTEx, SIRI, OpRa,
  EU legislation, mobilityDCAT-AP, NAPCORE, …). The chat page never sends one: its scope is a constant empty
  list. So a user cannot say which standard is meant except in the words of the question.
- **Measured** (prod 0.97.221, 2026-11-14, 14 wrongly refused questions of the record, each asked once with the
  standard that fits it given as scope): **11 of 14 are answered**, against 0 of 14 without a scope.

  | | Without scope | With the fitting scope |
  |---|---|---|
  | Refused by the keyword rules (9 asked) | 9 refused | 9 answered |
  | Refused by the model's verdict (5 asked) | 5 refused | 2 answered, 3 still refused |

  The answers now cite the right kind of source: the questions about machine-readable formats, static data and
  DATEX in legislation cite the regulation's articles and annexes, where without a scope not one passage of the
  regulation was among the candidates. Still refused: "an elevator in a stop place" (the wording gap),
  "Which fare data must be provided …" (the annex is still not found), "What is OpRa used for?" (the overview
  file is still under the schema files). One answer is still beside the point ("bus ticket" from ticketing
  equipment).
- Limits of that measurement: I chose the scope myself, so it is the best case; one run per question; the
  answers were judged from their citations and first lines, not read in full.
- **Not usable as a trigger** (**measured**): the confidence number. It is 0.94 on nearly every answer and 0.80
  on an unvalidated one; it does not say whether the answer is good.

So the best case is large: a scope alone recovers most of the wrongly refused questions. What is not known is
whether the helpdesk can offer the right choice, and whether users will take it.

## 3. Principles

- **A choice, not a conversation.** The helpdesk offers options it derived from the index; the user picks one.
  The model is not asked to invent a question to the user.
- **One self-contained question again.** The pick is sent with the original question as its scope. No earlier
  turn goes to the model, so grounding, the validator, the checks and the log work as they do today.
- **Never only a question back.** Where a best-effort answer exists it is shown, with the choice beneath it. A
  helpdesk that answers a question with a question is worse than one that refuses.
- **Refusing stays safe.** A choice must not make an off-topic question answerable.

## 4. Steps

One PR per step. No step changes what users see before its gate is met.

### C0. Can the right options be offered? (no change of behaviour)

The best case above assumed the right scope. Measure how often the helpdesk itself would offer it.

1. Candidate ways to derive up to three options for a question, all from what exists: the standards of the
   candidates retrieval finds over all sources; the standards the semantic parse already lists
   (`candidateStandards`); the answer of the controller model asked which of the scopes the question may be
   about (one call, the same call the relevance check makes).
2. On the gold file of the retrieval plan (its Q0) and the 23 wrongly refused questions: is the fitting scope
   among the options, per way of deriving them?
3. With each offered option as scope, through the API, 3 runs: answered, refused, and the answer read against
   the wanted source.
4. The must-refuse set (`refused-questions.yaml`, 25 questions) with every scope: how many become answered.

**Gate C0**: for at least 80% of the wrongly refused questions the fitting scope is among at most three options;
with it, at least two thirds are answered from the wanted source; no must-refuse question is answered under any
scope that it is not answered under today. If the gate fails, the plan stops here and the result is recorded.

### C1. The choice in the API

- The answer carries a `clarification` when a trigger fires: why (refused by the rules, several concepts, the
  model says the evidence does not answer) and the options (label, scope).
- A request may name the question it clarifies and the chosen scope; the server answers the original question
  with that scope and links the two events in the log.
- Triggers are events the system already has: the keyword rules refuse (and, when the relevance check of #523 is
  on, it says the question is on topic); the existing ambiguity flag; the model's "does not answer" verdict.
- Both endpoints (JSON and stream), the OpenAPI description, tests with the model mocked.

Gate: the questions of C0 through the API, the pick taken from the offered options by rule (the fitting one),
give C0's numbers; without a pick nothing changes for any question (the 140 benchmark questions and the
must-refuse set answer as before).

### C2. The choice on the page

Buttons under the refusal or the answer; choosing one asks again and shows the new answer in the same turn. The
sentence on the page about questions being answered independently is rewritten to say what now happens. The
labels are the standards' names, so they need no translation; the lead-in is English like the rest of the page.

Gate: tried by Andrej on the staging of the change; frontend tests; no change for answers without a trigger.

### C3. Does anyone use it? (after release)

From the prod log, after three weeks: how often a choice was offered, how often taken, how often the second
answer was not a refusal, likes and dislikes on both. This decides whether C4 is worth doing.

### C4. Real follow-ups (separate, later, only on C3's numbers)

"Explain that in plain text", "and for trams?": a follow-up is rewritten into a self-contained question from the
turn before, with one model call, and then answered as any question. More useful than the choice and riskier: a
wrong rewrite answers the wrong question without anyone noticing. It needs its own plan and gate (the rewritten
question shown to the user; a set of follow-ups with the rewrite expected).

## 5. How this fits the other work

- **The relevance check of #523** lets a keyword-refused question through without a scope, and three of ten such
  answers were beside the point. With a choice, the same question gets a scope and, in the measurement above,
  the right kind of source. When both exist: answer best effort and offer the choice.
- **The retrieval plan** remains needed: three of the 14 stay refused with the right scope, for the reasons that
  plan looks into. Its gold file is reused here.
- If the retrieval plan's Q2 finds why sources of the legislation never become candidates without a scope and
  fixes it, part of this plan's gain disappears. C0 is therefore measured after Q0's table is in.

## 6. Not planned

- Sending the conversation to the model.
- Free-text clarifying questions written by the model.
- Blocking an answer until the user has chosen.
- A scope selector as a permanent control above the input: it asks every user every time, where the choice asks
  only when it helps. (It is the fallback if C0 fails on deriving options but the best case holds.)

## 7. Risks

- **Users do not pick.** Then the gain stays on paper; C3 measures it, and the answer shown without a pick is no
  worse than today.
- **The wrong options are offered.** C0's gate.
- **A scope makes an off-topic question answerable.** C0's fourth measurement.
- **Two answers cost twice.** Only when a choice is taken.

## 8. Results

(Each step records its numbers here.)
