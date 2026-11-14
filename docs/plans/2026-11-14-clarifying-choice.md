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

### C0 (2026-11-14, against 0.97.221): gate failed

**Gate C0 is not met.** The options can be derived, but a scope makes off-topic and vague questions answerable,
and the share answered from the wanted source is at the limit. The plan stops here.

| Gate criterion | Needed | Measured | |
|---|---|---|---|
| Fitting scope among at most three options (23 wrongly refused) | ≥ 80 % | 21 of 23 (91 %), controller model | met |
| With the fitting scope, answered from the wanted source (≥ 2 of 3 runs) | ≥ 2/3 | 16 of 23 (70 %) on dev; on prod believed 15 of 23 (65 %) | met on dev only |
| Must-refuse questions answered under a scope that are refused today | 0 | 9 of 25 (any scope); 4 of 25 under the scopes the controller would offer | not met |

How it was measured (**measured** unless marked). Dev stack serving main (0.97.221, relevance check, vocabulary
bridge and evidence gate off, as on prod). `measure_scope_options derive` lists the options each way gives;
`measure_scope_options ask` sends each question to the answer endpoint with `standardsScope` set to each offered
scope and to each fitting scope, and without one, 3 runs each (399 requests for the 23, 825 for the must-refuse
set with all ten scope values). The fitting scopes are my judgement from the dev index, one or more per question,
in `benchmarks/refused-questions-scopes.yaml`; they agree with the `fitting_scope` of the retrieval plan's gold
file, which names one scope where I list two for four questions (parkings, seat capacity, metadata, DATEX and
SIRI); with its single scopes the option counts below do not change. An answer counts as "from the wanted
source" when a passage it cites is one of the passages that answer (path patterns in the same file); the 46
answered runs under a fitting scope were read (first lines and citations), the others were not.

#### Ways of deriving the options

On the 23 wrongly refused questions; the fitting scope is among the first 1, 2 or 3 options.

| Way | @1 | @2 | @3 | Cost per question |
|---|---|---|---|---|
| `candidateStandards` of the semantic parse | 5 | 6 | 6 (17 questions get no option) | none (already computed) |
| the same plus the standards the ontology recognised | 7 | 8 | 8 | none |
| standards of the unscoped search (as the app searches) | 11 | 15 | 15 | one search, 2.1 s mean |
| standards of a search over every source | 15 | 18 | 20 | one search per wording, 5.0 s mean, 11.9 s max |
| controller model asked which scopes fit (one call) | 20 | 21 | 21 | 1 model call, 1.7 s mean, 4.4 s max |
| controller, then search over every source | 20 | 21 | 21 | both |

- The controller's options were asked three times: @3 was 21 of 23 each time, @1 20, 20 and 21; the order and
  the third option change between calls for about a third of the questions.
- The controller misses the two "static / dynamical data" questions (it offers NeTEx, SIRI, Transmodel, not the
  legislation that defines the terms). The unscoped search cannot offer the opt-in sources (legislation,
  mobilityDCAT-AP, NAPCORE, DATEX II …) at all, which is why it does worst on the questions that need them.
- The controller often spends an option on Transmodel. Only 58 indexed passages carry the Transmodel scope, all
  shared with NeTEx, SIRI or OpRa (Transmodel's definitions come from the graph), so Transmodel as a scope was
  refused or beside the point in most runs. Combining ways adds nothing over the controller alone.

#### Answers with each scope (dev, 3 runs per question and scope)

| Scope sent | Runs | From the wanted source | Beside the point | Refused |
|---|---|---|---|---|
| none (today) | 69 | 5 | 0 | 64 |
| the fitting scope (first listed) | 69 | 43 | 0 | 26 |
| the best fitting scope per question | 69 | 46 | 0 | 23 |
| the controller's first option | 69 | 37 | 7 | 25 |
| the first option of the search over every source | 69 | 25 | 15 | 29 |
| any offered scope that does not fit (82 pairs) | 246 | 16 | 94 | 136 |

"Beside the point" outside the fitting scopes is classified from the citations only, not read.

- With the fitting scope, 16 of 23 are answered from the wanted source in 2 or 3 of 3 runs, the other 7 are
  refused in all 3. Spread: 18 of the 133 question–scope pairs had different outcomes between runs.
- Two of the 16 are partial: "How are static / dynamical data described?" are answered from the MMTIS Annex
  headings, and the answers say the blocks give only the heading; the definitions in Art. 2(3)–(4) are not
  retrieved.
- Still refused with the fitting scope: the three elevator questions (NeTEx; retrieval gives PassengerEntrance
  and TaxiStand, while "lift" finds LiftEquipment), "How to describe a bus ticket?" (ticketing equipment), the
  MMTIS fare-data question (Articles 1, 6, 9 instead of the Annex), the DATEX parking-bay question (OpenLR
  location passages) and the UIC bit field question (ontology relation paths, no bit field). Each is a retrieval
  fault of the retrieval plan; a scope does not reach them.
- "What is OpRa used for?" was answered without a scope in 3 of 3 runs on dev (refused in the record), with the
  OpRa scope in 2 of 3.

#### The must-refuse set with every scope (dev, 25 questions × 10 scopes × 3 runs, and 3 runs without)

Without a scope: 2 answered sometimes ("What does GTFS say about stop times?" 3 of 3, from NeTEx's GTFS mapping
examples, as in the record; "colour of bus seats" 1 of 3). With a scope:

| Question | Answered under (runs of 3) |
|---|---|
| Explain the data format. | Transmodel 3, SIRI 3, OpRa 3, mobilityDCAT-AP 3, NAPCORE 3, TN-ITS 3, DATEX II 2, INSPIRE 1 |
| Is this mandatory? | Transmodel, NeTEx, SIRI, mobilityDCAT-AP, NAPCORE, INSPIRE 3 each; EU legislation 2; DATEX II 1 |
| What are the rules? | NeTEx, EU legislation, mobilityDCAT-AP, NAPCORE, INSPIRE, DATEX II 3 each |
| How does it work? (answered without scope 1 of 3) | EU legislation 3, mobilityDCAT-AP 2, DATEX II 2, Transmodel 1, NAPCORE 1 |
| What should I do first? | Transmodel 3, EU legislation 1, INSPIRE 1 |
| Can you help me? | Transmodel 1, INSPIRE 1 |
| What is the formal W3C or OGC ontology for NeTEx concepts? | Transmodel 2 |
| How does NeTEx compare to GTFS in terms of real-time data quality? | NeTEx 1 |
| How does OpRa integrate with GTFS-RT …? | OpRa 1 |
| is croatian NAP good? | Transmodel 1 |

The other 15 (greetings, weather, bread, poem, football, capital, laptop, OpenStreetMap, narcose, the Italian
question, "What does NeTEx say about the colour of bus seats?", rounding ExpectedArrivalTime, OpRa cost, DATEX
equivalent of an OpRa indicator, and the GTFS stop-times question, which is answered only without a scope) are
refused under every scope.

Reading of these answers (first 400 characters and citations of each question–scope pair): none states anything
its cited passages do not support, so they are not leaks of model knowledge (**believed**: not read in full, not
checked by the validator). But they are not answers either: a vague question gets "the evidence does not …; what
it does cover is …" from whatever the scope holds ("How does it work?" under the legislation describes the ITS
Directive's working programme; "Can you help me?" under Transmodel explains how to open a GitHub issue). The two
GTFS / GTFS-RT questions name the standard, so their scope is already NeTEx or OpRa without a choice; their
answers under a scope are run-to-run variance of the same pipeline.

Under the scopes the controller would offer (its three options), 4 questions are answered: "Explain the data
format.", "Is this mandatory?", "What are the rules?" and the NeTEx–GTFS comparison. For most off-topic questions
the controller names no scope at all (16, 17 and 16 of 25 in three calls).

#### How a scope changes the pipeline (read in the code)

- `_parse_question` takes the requested scope as `candidateStandards` and does not parse the English rendering;
  `select_effective_scope` returns the requested scope unchanged (an explicit scope wins; no ambiguity flag).
- The keyword rules (R1) never refuse a scoped question: `has_scope_hint` is true for any non-empty scope, so
  neither the no-concept nor the low-confidence rule fires, and the relevance check is never asked. This is why
  the 9 keyword-refused questions are answered with a scope, and why vague and off-topic questions reach
  retrieval and the answer model. Only R2 (nothing retrieved), R3 (policy) and R4 (the model's verdict) remain.
- Retrieval keeps only passages whose `standards_scope` contains a requested value. Without a scope the opt-in
  sources (EU legislation, mobilityDCAT-AP, NAPCORE, INSPIRE, DATEX II, TN-ITS) are left out unless a passage is
  also NeTEx, SIRI, OpRa or Transmodel, so a scope is the only way such a question reaches them. With one scope
  the per-scope coverage step does not run (it needs two or more).
- The scope also goes to the FAQ match, the presence evidence, the schema structure, the example generator, the
  answer prompt (`query_scope`) and the legal-context line.
- "Cut to the first standard" no longer exists: since #43 a question naming no standard is searched in all core
  standards, and a named set is kept whole.

#### Dev against prod

Prod 0.97.221 (relevance check off: "How do I describe a lift in a station?" without scope got the keyword
message), the 10 questions that decide criterion 2 asked with their fitting scope, 3 runs each (30 requests): 9
agree with dev at the 2-of-3 level (elevator ×3, bus ticket, fare data, parking bay, UIC bit field refused;
static and dynamical data answered from the Annex headings). "What is OpRa used for?" differs: refused 3 of 3 on
prod (schema fragments, no README), answered 2 of 3 on dev. Taking the other 13 as on dev (**believed**, not
asked on prod), criterion 2 is 15 of 23 on prod, below two thirds. The bus-ticket answer that the planner's probe
saw beside the point was refused in all 3 runs here. Four must-refuse pairs on prod: "What are the rules?" (EU
legislation), "Is this mandatory?" (NAPCORE) and "How does it work?" (EU legislation) were answered as on dev,
"Explain the data format." (SIRI) was refused in its one run (on dev answered 3 of 3).

#### The fallback (a plain scope selector)

Best case, the user always picks a fitting scope, best of 3 runs: 16 of 23 answered from the wanted source (14
fully, 2 from the Annex headings only). It has the same problem as the choice: the must-refuse questions are
answered because a scope switches off the keyword rules, whoever picks the scope. A selector offers every scope
to every question, so all 9 apply, not only the 4 of the controller's options.

#### What would be needed before trying again (not part of this plan)

- A scoped question still needs a screen for questions about nothing in particular: today any API client that
  sends `standardsScope` gets these answers already. One way is to keep the keyword rules' verdict and let the
  relevance check decide also for scoped questions; it needs its own gate on the must-refuse set.
- The seven questions refused with the right scope are retrieval faults (the retrieval plan).
- Transmodel as an option is of little use while its definitions are not source passages; it should not be
  offered on its own.

#### Gold file of the retrieval plan

`answer-source-questions.yaml` (branch `docs/plan-retrieval-misses`, commit fd5527f) became available during
the run; its 34 b-questions (from the prod log, mostly answered today, some beside the point) were measured the
same way, with its `fitting_scope` and source patterns. Classified from the citations only, not read.

- Fitting scope among the options @1/@2/@3: controller 30/30/33 of 34 (misses "What is INSPIRE?", where it
  offers INSPIRE and the file wants the Directive, marked unsure there); search over every source 21/28/31;
  unscoped search 19/24/24; `candidateStandards` 23/28/28 (these questions mostly name their standard).
  Controller 1.6 s mean.
- Answered from the wanted source in ≥ 2 of 3 runs: 18 of 34 without a scope, 21 of 34 with the fitting scope.
  Gained: "What is INSPIRE?" (refused → Directive), "Kaj so metapodatki v NAP?", "Kako NeTEx opisuje cene
  vozovnic?" and the NeTEx/SIRI/OpRa explanation (through the SIRI scope); lost: the Portuguese MMTIS dataset
  question (answered 2 of 3 without scope, refused 3 of 3 with the legislation). The ones beside the point
  without a scope ("What is SIRI used for?", "What are parts of SIRI?", buying tickets) stay beside it with the
  scope: the fault there is ranking inside the right standard, which a scope does not touch.
