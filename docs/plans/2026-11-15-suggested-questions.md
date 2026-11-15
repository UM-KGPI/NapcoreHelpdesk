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
4. **The source named in words** (added during S0, measured in runs of its own with the same gate): the controller
   model names the sources that may answer the question, as in C0, and restates the question with the source in it,
   so it goes through the screen as an ordinary unscoped question.

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

### S0 (2026-11-15, dev, 0.97.225): gate failed for every way

**Verdict.** No way meets gate S0, so S1 is not started. The best, way 1 (questions written from passages of every
source), is useful for 5, 6 and 7 of the 12 questions refused today (42–58 %, gate 60 % in 3 of 3 runs), 6–31 % of
its shown suggestions are refused when asked (gate 10 %), and it adds 5.7 s to a refusal after the search at the
median (gate 2 s). Way 2 (earlier answered questions) is fast and almost never dead, but is useful for 3 of 12 and
offers questions that have little to do with what was asked. Way 3 is way 2 by construction. Way 4 (the source
named in words, from the C0 idea) is useful for 2–4 of 12 and two thirds of its suggestions are refused. The cheap
check before showing passed every one of 536 suggestions, so it predicts nothing. All numbers **measured** unless
marked.

**How it was measured.** A host server from this branch on port 8061 (`RELEVANCE_CHECK_ENABLED=True`,
`LLM_MAX_EVIDENCE_CHUNKS=6`, as prod runs; controller model `claude-haiku-5-5`; graph mode on), one request
at a time. `measure_suggested_questions` (this branch): `baseline` asks every question twice through the API;
`suggest` makes the suggestions of each way and runs the check for each; `score` asks every suggestion through the
API as the chat page asks (no scope); `summary` counts. Three runs for ways 1–3 (runs 1–3), three separate runs for
way 4 (runs 11–13), and a timing run at the end. "Useful" = at least one suggestion shown after the check that is
answered and cites a wanted source of the original question (the gold file's patterns; for the 23 through `ref`,
so every one has its wanted source and none was judged by reading). "Dead" = a shown suggestion that is refused.
Suggestion texts are model output: a way-1 or way-4 suggestion is a new text in every run.

**Today's state** (2 runs each, refused in at least one counts as refused today, decided before the runs):

| Group | Asked | Refused today | Of them refused in both | Where |
|---|---|---|---|---|
| wrongly refused (refused-questions.yaml) | 23 | 10 | 7 | all by the answer model's verdict, after the search |
| gold b-questions (answer-source-questions.yaml) | 34 | 2 (b14, b30) | 1 | verdict |
| must-refuse | 25 | 24 (m19 answered in both) | 24 | 14 at the screen (second opinion IRRELEVANT), 10 by the verdict |

So the gate's denominator is 12: k11, k14, e02–e08, p01, b14, b30. None of the 12 is refused at the screen any more
(the second opinion lets all 14 keyword-refused ones through). "Kaj so to metapodatki?" was answered in both runs on
my server (from the GML metadata property types, beside the point, as Q3 found), so it is not in the set.

**Gate S0** (skip: no suggestions when the second opinion said IRRELEVANT; the other skip options below):

| Gate | Needed | Way 1 written | Way 2 earlier | Way 3 both | Way 4 source named |
|---|---|---|---|---|---|
| 1. useful, of 12, per run | ≥ 60 % in 3 of 3 | 5, 6, 7 | 3, 3, 3 | 3, 3, 3 | 2, 4, 2 |
| 2. shown suggestions refused when asked | ≤ 10 % | 11/35, 4/33, 2/33 | 2/66, 1/66, 1/66 | as way 2 | 20/31, 23/30, 20/31 |
| 3a. must-refuse not about the sources get none | none | none (also without skip) | none with skip; 3 each without | as way 2 | none (also without skip) |
| 3b. no suggestion that answers the original | none | none; 1 borderline (m06) | none read as such | as way 2 | 2 restatements answered (m23, m25), text declines |
| 4. added to a refusal after the search, median | ≤ 2 s | 5.7 s (8.6 s with check) | 0.05 s (4.4 s with check) | sum | 2.7 s (4.0 s with check) |
| | | fails 1, 2, 4 | fails 1 | fails 1 | fails 1, 2, 3b |

Useful per question, way 1: k11, e03, e06, p01, b14 in 3 of 3 runs; e02 in 2; b30 in 1; never k14, e04, e05, e07, e08.
Way 2: k11, e06, b30 in 3 of 3 (deterministic). Way 4: b14 3, k11 2, e06 2, e03 1. The union of ways 1 and 2 (not a
way that was defined before the runs) would be 6, 7 and 7 of 12, still below 60 %. Way 3 equals way 2 because way 2
always fills the three places and the check never removes one; the order "earlier first" was fixed by the plan.

**Way 2 needed a stand-in.** The dev question log holds 156 distinct questions that were answered, validated and not
disliked; 68 of them are questions of the test sets themselves and the other 88 are questions from earlier
measurements (presence, example and concept benchmarks), some of them paraphrases of the test questions ("How do I
describe a lift in a station in NeTEx? Show me an example in XML."). It is too contaminated to judge way 2, and it is
not users' data. As a stand-in, **clearly not the real thing**, the pool was the 140 answerable benchmark questions
asked once through the API: 126 answered, 123 validated, 2 of them also in the test sets and left out, so 121. The
benchmark covers NeTEx, SIRI and OpRa only, so way 2 could never be useful for the legislation and profile questions;
on prod's log the result may differ in both directions (**believed**).

**The check before showing.** Keyword screen (no second opinion), then the unscoped search with the app's scope
selection, pass when one passage reaches 0.62. It passed all 444 suggestions of ways 1–2 and all 92 of way 4. Of
the passed ones, 23 of 444 and 63 of 92 were refused when asked: every refusal came from the answer model's verdict,
which the check cannot see. It costs 0.8 s (at the screen) to 1.4 s (after the search) per suggestion at the median,
for nothing. The full check is asking the suggestion: 3.9–5.4 s per suggestion at the median through the API, so
about 4–5 s added per refusal if three are asked in parallel, 13 s one after the other, and twice the model cost.

**Skipping questions that are not about the sources.** Three options, fixed before the runs: no skip; skip when
the second opinion said IRRELEVANT; skip every refusal at the screen. On today's state the last two are the same (no
refusal at the screen is the keyword message alone) and cost nothing in usefulness (none of the 12 is refused at the
screen). What they let through: with the skip, the 14 screen-refused must-refuse questions get nothing, and the 10
refused by the verdict get suggestions. Without a skip, way 1 still writes nothing for the nine questions that are not
about the sources (greetings, weather, bread, football, poem, capital, laptop, narcose, the Italian question) in 3 of
3 runs: the model follows "suggest nothing" even with passages above the score; but it does write for the vague
"Explain the data format.", "What are the rules?" and "Is this mandatory?" (DATEX II regulation profiles, the
mobilityDCAT-AP mandatory properties). Way 2 without a skip gives three benchmark questions to every question, "hi"
and the weather in Ljubljana included. The skip costs nothing (the verdict is already known); with it, nothing is
added to a refusal at the screen.

**Must-refuse: every way-1 suggestion shown with the skip, read with its answer** (3 runs; short form):

| Original | Suggestions (answered unless marked) | Reading |
|---|---|---|
| m04 is croatian NAP good? | goal of NAPCORE; how NAPCORE's data insights report assesses NAPs (refused once) | related, does not judge a NAP |
| m05 colour of bus seats | seats of a double-decker bus in the deck plan example; what that example includes | related, about deck plans |
| m06 round ExpectedArrivalTime to whole minutes? | SIRI definition of ExpectedDepartureTime; NeTEx EstimatedTimesAtStopGroup; "What time precision is used … in the SIRI stop monitoring example?" (answer: to the second) | **borderline**: the last does not say whether rounding is allowed, but a reader may take it as an answer |
| m20 OpenStreetMap API | why data consumers use OSM, NAPCORE cycling conclusions | related, says nothing about the API |
| m21 NeTEx vs GTFS real-time quality | NeTEx is for scheduled data; what EN 15531-2 covers | related, no comparison |
| m22 cost of implementing OpRa | what gap OpRa fills (refused in all runs) | — |
| m23 W3C/OGC ontology for NeTEx | NeTEx is an XML representation of Transmodel; Transmodel version | related, no ontology named |
| m24 OpRa with GTFS-RT | OpRa's four data groups; the gap OpRa fills (refused in run 1) | related |
| m13, m25 | none in any run | — |

Way 4 restates the must-refuse question with a source in it ("Is it ok to round … to whole minutes in SIRI?", "What is
the estimated cost of implementing OpRa …, according to NAPCORE's material …?"). Most were refused; m23 ("… as
described in the Transmodel reference data model?") and m25 ("What is the Transmodel equivalent of an OpRa capacity
indicator?") were answered once each (run 11), with texts that say the evidence does not name one; in run 13 m25 got
two related questions that were answered ("What is an OpRa capacity indicator?"). That is the risk
expected when the way was proposed: naming a source in the words is the same move as a scope, and the restatement is the original
question. None of the nine not about the sources got a way-4 suggestion (the model named no source).

**Suggestions to read** (original → suggestion; way 1 unless marked):

- "How to model number of late journeys?" → "How is the late dated vehicle journey count reported in an OpRa
  ServiceDelivery response?" (answered from `opra_lateDatedVehicleJourney`: useful)
- "What if my dataset is available in several formats?" → "In mobilityDCAT-AP, can one dataset have multiple
  distributions, with the same dataset provided in different ways such as a zip file or XML?" (useful)
- "In which legislation is DATEX. included?" → "Which formats must data holders use for dynamic road travel and traffic
  data under Article 5 of Delegated Regulation (EU) 2017/1926 (MMTIS)?" (useful)
- "Como operador de uma rede nacional de autocarros, que categorias de datasets tenho de ter em conta, do regulamento
  MMTIS?" → "Em que secção do anexo do Regulamento Delegado (UE) 2017/1926 (MMTIS) se tratam os tipos de dados
  dinâmicos de viagem e tráfego?" (useful, in Portuguese)
- "when describing the calendar of a service journey, how to choose between UIC bit field and explicit Operational
  Days?" → "In NeTEx, how is a service journey linked to day types through the ServiceCalendar?" (useful by the gold
  patterns, but it does not answer the choice the user asked about)
- "How do I describe an elevator in a station in NeTEx?" → "What are the allowed values of the AccessFeatureEnumeration
  in the NeTEx netex_environment_support.xsd schema?" (refused)
- "How to define a location of a parking bay in DATEX?" → "How is the location of a ParkingBay expressed in NeTEx,
  using a Centroid and a gml:Polygon?" (refused; and it moved to another standard)
- "How are dynamical data described?" → "How is dynamic road status data on the availability of charging points for
  electric vehicles defined in DD 2015 962?" (refused; drifted to a NAPCORE data dictionary)
- "What does NeTEx say about the colour of bus seats?" → "How does NeTEx represent the seats of a double decker bus in a
  deck plan?" (answered; acceptable)
- "Is this mandatory?" → "Which properties are mandatory in the mobilityDCAT-AP quick reference of classes and
  properties?" (only without the skip; a guess at what the user meant)
- Way 2: "How to define a location of a parking bay in DATEX?" → "What is a NeTEx Route and how is it different from a
  Line?" (similarity 0.85; unrelated)
- Way 2 without skip: "What is the weather in Ljubljana tomorrow?" → "What does a ResponseLateDatedVehicleJourneys OpRa
  message look like?"
- One trial, not in the set (answered on my server): "Kaj so to metapodatki?" → "Kaj je metapodatkovni zapis v
  mobilityDCAT-AP?" and "Kako so metapodatki opredeljeni v MMTIS DR in Aktu EU o podatkih (EU) 2023/2854?"; asked
  once, both answered, from mobilityDCAT-AP and MMTIS Art. 2, the sources the user meant.

**Without a gate.**

- Language: the only non-English question in the set with suggestions is the Portuguese b14; 5 of 5 way-1
  suggestions were in Portuguese (detector). Way 2 suggests in the pool's language (English here).
- Stability: way 1 wrote 1–3 suggestions per question; no suggestion text recurs in all three runs for any question
  (2–9 distinct per question). The useful ones stay useful by content: 5 questions useful in 3 of 3.
- Difference from the original: no way-1 suggestion repeats the original (0 of 120). For the 12 wrongly refused
  questions (62 suggestions) the cosine similarity to the original is 0.78–0.97, median 0.88 (way 2: 0.85); word
  overlap median 0.11. They are new questions, often longer and in the
  source's terms ("late dated vehicle journey", "AccessFeatureEnumeration").
- Model calls: way 1 one controller call per refusal, 0 failed of 108; way 4 one call, 0 failed of 108. Way 2 none.
- Privacy, way 2: a logged question is free text and holds whatever the user typed. In the dev log I found place and
  operator names in example requests ("Ljubljana Bus Station", "Arriva Slovenija", "LPP"), and the record knows of a
  question with a pasted SIRI document. Nothing filters these before a question would be shown to another user; a
  filter would be needed and is not in the plan.

**Time** (the timing run at the end, the dev stack otherwise idle: the other two measurements had finished; the runs
before were under their load and slower). Seconds added to a refusal, median (90th percentile):

| | at the screen (14) | after the search (22) |
|---|---|---|
| way 1: search over every source | 2.1 (2.3) | 2.6 (3.1) |
| way 1: model call | 1.1 (3.2) | 3.1 (4.1) |
| way 1 total, without the check | 3.2 (5.4) | 5.7 (7.9) |
| way 1 total, with the check | 3.2 (10.1) | 8.6 (10.8) |
| way 2: embedding and nearest, without the check | 0.04 | 0.05 |
| way 2 with the check | 3.0 (4.2) | 4.4 (5.9) |
| way 4: model call, without / with the check | 1.2 (2.1) / 1.2 (2.1) | 2.7 (4.3) / 4.0 (10.1) |

With the skip, a refusal at the screen gets nothing and pays nothing. A refusal today takes 0.8 s at the screen and
5.4 s after the search (median of the baseline). Nothing runs for an answered question: in S0 by construction (the
suggestions are made only for refused questions); the English rendering and the language are known to the app
before the screen and are not counted.

**What is believed, not verified.**

- That prod behaves like dev here: prod's index and settings file were not read; the 12 refused today are dev's.
- That way 2 on prod's real log would do better than on the benchmark stand-in: not measured, and the log is not
  filtered for personal data.
- That the gold patterns judge "useful" fairly: p01 counts as useful from relation paths that do not answer the
  user's choice; the gold file's patterns were used as they are.
- That m06's borderline suggestion is acceptable: my reading; it is Andrej's call.

**What was not tried.**

- Showing way 1's suggestions only after asking them in full (the full check): it would remove the dead ones, at
  about 4–5 s more per refusal in parallel and three more answer-model calls; usefulness would stay at 5–7 of 12.
- Way 1 from the passages the answer model already read (no second search), which would save 2.6 s after the search;
  those passages come from the unscoped search, so the legislation and profile questions would lose their sources.
- A faster model call (no thinking), or fewer passages in the prompt.
- Way 2 on prod's log.
- Any variant thought of after seeing these numbers needs its own run, by the plan's rule.

**Next.** The plan stops here by its own rule. What S0 shows: the passages near a wrongly refused question do exist
for most of them (way 1 found an answering source for 7 of 12 at best), but a question written from them is refused
by the same verdict in about one case in six (19 of 120), and the cheap check cannot tell. The two numbers that fail most
clearly, dead suggestions and time, both come from the answer model's verdict and the search over every source.

### A case for a later step: an answer to the other reading (2026-11-15, prod 0.97.225)

Not a refusal, so nothing above covers it. "Which formats count as machine-readable?" was answered, confidence
0.94, text confirmed against its citations, about how a ticket can be read by a machine (`TypeOfMachineReadability`
in the NeTEx fare schema: OCR, magnetic stripe, bar code). The reading a user of a National Access Point has in
mind is the regulation's: machine-readable formats of data, and the standards it requires.

- **Measured** (Q2 of the retrieval-misses plan): the regulation's passage for this question ranks 65th by vector
  among all sources and 5th within the legislation alone. An unscoped question does not search the legislation,
  and adding the opt-in sources to the unscoped search does not bring this passage in (Q2's step, gate failed).
- **Measured** (S0, one trial): for "Kaj so to metapodatki?", which has the same shape (answered from a GML type,
  meant as metadata of datasets), the written suggestions named mobilityDCAT-AP and the MMTIS regulation, and
  both were answered from the sources the user meant.
- **Believed**: a question like this has two readings in two kinds of source, and that can be seen without a
  model call: the best passages of the default search and the best passages of a search over the other sources
  are both strong and of different kinds. Where that holds, the helpdesk could answer the first reading and offer
  the second beneath the answer as a question to click.
- Not measured: how often this holds on answered questions, how often the offered reading would be the wanted
  one, and what the second search costs on every answer (Q2 measured about 0.5 s for a similar search).

It would be its own step with its own gate, and only after a way of making suggestions has passed S0's gate.
