# Plan: an XML request that names its NeTEx object and gives a duration gets a generated example

Written 2026-11-10 (Fable) against 0.97.172 (main 3748838, same build on prod), for the implementing agent (Opus).
Numbers were measured on the dev stack (Docker, semantic index, Claude Haiku 5.5, netex-validator) unless marked
**prod**. Each claim is labelled **measured** (re-derived here, scripts in §8), **believed** or **assumed**.

## Status (2026-11-10, Opus)

P0–P3 implemented in one PR (branch `fix/example-named-object-durations`). P1–P3 were done together, not in order: four of
the five new benchmark questions do not trigger before P3, so P1 and P2 could not be measured on their own.
P2(b) counts two times inside any object (an element with an id, not a frame) that contains both: in the
generated fragments departure and arrival sit in two `Call`s, each with its own id. P4 stays open.

Dev benchmark, 31 questions × 3 runs (**measured**):

| | Valid | First attempt | Mean time |
|---|---|---|---|
| gen01–26, 0.97.163 (plan of 2026-11-10) | 78/78 | 63–65 | 4.0 s |
| gen01–26, this branch | 78/78 | 70 | 3.3 s |
| gen27 ferry, "create an XML file" | 3/3 | 3 | 6.1 s; TemplateServiceJourney, "3 minutes" → `Time` 3 minutes after the departure, no number in Name/Description |
| gen28 ferry, "give an XML snippet" | 3/3 | 3 | 6.0 s; same |
| gen29 "write the XML for a NeTEx FlexibleLine" | 3/3 | – | 0.2 s; FlexibleLine from the standard (Netex_Uniqueness_01.xml) |
| gen30 TemplateServiceJourney every 10 minutes 06:00–22:00 | 3/3 | 3 | 2.6 s; PT10M in `ScheduledHeadwayInterval` |
| gen31 ServiceJourney, wait time of 30 seconds | 3/3 | 3 | 5.8 s; PT30S in `WaitTime` |

Trigger replay (**measured**): prod log, 432 distinct questions: the new pattern adds 3, all of them the ferry
question (three wordings); dev log, 319: adds 1, the July ferry question. One prod example request names two or more
CamelCase names (a follow-up quoting `<WaitTime>` and `<ForBoarding>`); neither is an object, so P1 does not change it.

## 1. The problem, measured

**Prod** question 1187, `req-mwb6auo0-n3jh83`, 2026-11-10 20:59 UTC, 0.97.172:

> I want to map a ferry service into a NeTEx TemplateServiceJourney. The ferry operates between two sides of the
> river when there is demand, it takes 3 minutes from side to side. Can you create an XML file modelling such
> TemplateServiceJourney?

`generatedExample` null, `exampleMs` null: the generator did not run. The user got text saying the evidence cannot
model the ferry, plus a 30-minute GTFS `HeadwayJourneyGroup` snippet copied from the evidence. Stored as
`mode=abstain`, confidence 0 (**measured**, event read through the prod API).

Three independent faults, each reproduced on dev with the exact question text (**measured**):

| # | Fault | Evidence |
|---|---|---|
| F1 | The request is not recognised. `_EXAMPLE_WORDS` needs example/sample/snippet/fragment/"show me how"/"show the xml"; "create an XML file" has none. | `asks_for_netex_example` → False. The July wording "give an XML snipped" (typo) misses too. |
| F2 | The object named in the question is ignored. `asked_element` only reads "example of/for X"; `TemplateServiceJourney`, written twice, is not looked at. | `asked_element` → `""`, although `concrete_elements("TemplateServiceJourney")` is an object and 8 example files use it. |
| F3 | "3 minutes" is treated as a count of parts and as the bare value "3". | `counted_shapes` → `(3, "3", "minutes")`; `part_holders` → {PassengersPerMinute, MaximumFlowPerMinute}; `asked_from_parts` → **StopPlace**. The value check then wants "3" as the whole content of an element. |

What each fault costs (probe runs, question with "file" → "example" so the trigger fires; app retrieval, scope NeTEx):

| Variant | Result (**measured**) |
|---|---|
| A: code as is | `origin=standard`, askedObject **StopPlace**: the Stockholm "Tekniska högskolan" stop place, shown as the NeTEx example for a ferry journey. Worse than the prod answer. |
| B: asked object forced to TemplateServiceJourney (F2 fixed) | 3 runs: 2 valid after 2 attempts (12–14 s), 1 fell back to the standard example after 3 attempts (24 s). Attempt 1 always fails the value check ("3 is missing"); the model then writes `<Description>3</Description>` or `<Name>3</Name>` to pass it, or an invalid `RunTime`. |
| C: B + PT3M accepted for "3" | no better: 3/3 valid but 2, 2, 3 attempts, still `<Name>3</Name>`. The model does not write PT3M by itself. |
| D: B + no value demanded for the duration | **3/3 valid on the first attempt, 5.8–7.1 s.** A `TimetableFrame` with one `TemplateServiceJourney` and two `Call`s, departure 00:00:00 at side A, arrival 00:03:00 at side B. |

So the generator can build this journey today; the checks around it stop it. In all D runs the 3 minutes are a
difference between two `Time` values, never an `xs:duration` element, and "when there is demand" is not modelled
at all (only an invented `DayTypeRef ref="hd:DT_OnDemand"`).

## 2. Constraints

- General mechanisms only: nothing keyed to ferries, TemplateServiceJourney or this wording.
- The 26-question example benchmark (78/78 valid, 63–65 first attempt, mean 4.0 s) must not regress. Compare with
  at least 3 runs per question; run-to-run variance is about ±1 run per question.
- No extra model call on the answer path (latency plan: prod mean 8.4 s). All three fixes are regex, cached
  validator look-ups and index queries.
- All changes stay inside `backend/helpdesk/services/netex_example_generator.py` and its tests; `views.py` calls
  the generator from two copies (stream and non-stream, lines ~1437 and ~2131) and needs no change.
- Tests must not call the live model (`backend/.env` points at a real endpoint): mock `_ask_model` and the
  validator look-ups as `test_netex_example_generator.py` already does.

## 3. Work items, in this order

The order matters: P3 (trigger) goes last. Turning the trigger on first would send more questions into variant A.

### P0. Benchmark and baseline first

Add to `backend/benchmarks/example-generation-questions.yaml` (ids continue the file's numbering):

1. the prod question verbatim ("create an XML file modelling such TemplateServiceJourney");
2. the same with "give an XML snippet";
3. a named object with no example noun and no values: "Can you write the XML for a NeTEx FlexibleLine?";
4. a named object with a headway: "Create NeTEx XML for a TemplateServiceJourney that runs every 10 minutes
   between 06:00 and 22:00." (expected: `ScheduledHeadwayInterval` PT10M — a duration that does have an element);
5. a duration on another object: "Show me a NeTEx example of a ServiceJourney with a wait time of 30 seconds at
   the second stop."

Run `run_example_benchmark --runs 3 --output …` on main and keep the JSON as the baseline. Expected baseline for
1–3: "not triggered". The command prints `asked=` and `present=`; they are the pass criteria below.

### P1. A NeTEx element named in the question is the asked object (F2)

- New `named_elements(question)`: tokens written as element names — CamelCase with at least two humps
  (`[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+`) — that `concrete_elements` knows as an object and `_in_examples` finds.
  An abstract one stands for its concrete members, as in `asked_element` today. Single capitalised words ("Line",
  "Quay") stay with the existing subject path: they are ordinary words at a sentence start.
- In `asked_element`: the subject phrase first, unchanged (so the 26 benchmark questions resolve as today). When
  it resolves nothing, the named elements, without those that are the noun of a counted shape or a wanted part
  ("StopPlace with two Quays" → StopPlace). Several left: the one named most often, then the first.
- `asked_from_parts` only runs when both gave nothing (already the control flow in `_generate`; keep it).
- `_generate`, no-values branch: a named element goes before `concept_elements` in the list given to
  `_plain_standard_example` ("write the XML for a NeTEx FlexibleLine" shows a FlexibleLine, not the nearest concept).

Pass: benchmark questions 1, 2, 4 report `asked=TemplateServiceJourney`; 3 shows a `FlexibleLine`.

### P2. A number with a time unit is a duration, not a count and not a bare number (F3)

- New `durations(question)`: `(\d+(?:\.\d+)?|number word) (second|minute|hour|day)(s)` and the common short forms
  (sec, min, hr) → (text as written, seconds, ISO form "PT3M"). No single-letter units.
- `counted_shapes` skips these, so `part_holders`, `asked_from_parts`, `count_places` and the `counted` sets no
  longer see "3 minutes". This alone removes the StopPlace answer of variant A.
- `requested_values`: the number of a duration is replaced by its ISO form ("PT3M"). `wants_generated_example`
  stays true for such questions. `value_holders(["PT3M"])` then asks the validator which elements accept it: 80
  duration elements, none of which accepts "3" (**measured**: JourneyDuration, RunTime, WaitTime,
  ScheduledHeadwayInterval, …), so the value-aware skeleton can bring one near the asked object (**believed**, not
  run).
- A duration value is met (`holds_value` / `_unmet_values`) when either
  (a) an element or attribute holds an equal `xs:duration` (compare in seconds: PT3M = PT180S), or
  (b) two time-of-day or dateTime values inside one object of the fragment differ by exactly that duration.
  (b) is what the model writes by itself in 3/3 runs (variant D); without it the retry loop of variant B returns.
- `_places` / `value_places`: report where it sits — the duration element for (a), the later of the two times for
  (b) — with the value shown as written ("3 minutes"). Read how the lead text and the frontend use `valuePlaces`
  before choosing the shape of the entry for (b); I did not read that code.
- The model prompt's "Values to use:" line names durations as such: "3 minutes (an xs:duration PT3M where the
  schema has an element for it, or times 3 minutes apart)".

Pass: question 1 valid on the first attempt in ≥ 2 of 3 runs with no `<Name>3</Name>`/`<Description>3</Description>`;
question 4 holds PT10M in `ScheduledHeadwayInterval`; question 5 holds PT30S in a `WaitTime`.

If (b) proves hard to do cleanly, the fallback is variant D as measured: durations are not must-hold values at all
(dropped from `requested_values`, kept in the prompt line). It loses the check, not the result.

### P3. Recognise a request to produce XML (F1)

- Extend the request test (keep `_EXAMPLE_WORDS` for its other users, add a second pattern used by
  `asks_for_netex_example`, `other_question`, `_SUBJECT`, `_SUBJECT_WIDE`): a producing verb followed, in the same
  sentence, by "XML"/"NeTEx" + file/document/code/snippet/fragment/instance/representation, or by "an/the XML";
  and "snipped" as a spelling of snippet. The candidate regex is in §8 (`trigger_replay.py`).
- False-positive check, dev log (**measured**): 319 distinct logged questions, 30 trigger today, the candidate adds
  exactly 1 — the July ferry question. Repeat on the **prod** log before merging (`GET /questions/events` with a
  dev token; the detail endpoint worked that way today) and read every newly matched question.
- Unit tests with negatives that must stay untriggered: "How do I validate a NeTEx XML file?", "What does the
  header of a NeTEx XML file contain?", "Which XML schema does NeTEx use?".
- **Assumed** acceptable: "How do I create a NeTEx XML file for my timetable?" now triggers and, having no values,
  shows a standard example of the nearest concept next to the text answer. If Andrej disagrees, require an object
  (P1 or subject) for the new pattern to count.

Pass: question 1–3 trigger; the prod replay adds no question that does not ask for XML.

### P4 (decide with Andrej, not part of the fix). Conditions the example does not model

"When there is demand" is silently dropped: the valid fragment is a fixed-time journey. Two separate questions:
- Wording: should the answer say which stated conditions the example leaves out? The narration rule is
  `generated_example_rule` in `llm_generator.py` (not read for this plan).
- Modelling: what is the right NeTEx for an on-demand shuttle — `FlexibleServiceProperties` (in the examples,
  **measured**), a frequency group, or neither? This is a domain call, not a code fix.

## 4. Expected result

The prod question, unchanged, returns a schema-valid `TimetableFrame` with a `TemplateServiceJourney` whose two
calls are 3 minutes apart, on the first attempt in most runs, about 6–7 s for the example step (variant D). Not
promised: the on-demand behaviour (P4). The 26 existing questions stay at 78/78.

## 5. Verification (every PR)

1. Unit tests for the new functions and for the three faults (mocked model and validator).
2. `run_example_benchmark --runs 3`: the 26 old questions against the 0.97.163 numbers, the 5 new ones against P0.
3. After deploy (only if Andrej asks for the full cycle; otherwise stop at the PR): ask the prod question once and
   read `generatedExample` in the stored event.

## 6. Risks

- P1 can pick an element the user only mentions ("How does a ServiceJourney differ from a TemplateServiceJourney?
  Show an example."). Mitigation in the rule: subject phrase first, then most-named, then first; measure on the
  prod log how many example questions name two or more elements.
- P2(b) accepts any two times 3 minutes apart in one object, also unrelated ones. Accepted: the alternative is the
  junk `<Name>3</Name>` the strict check produces today.
- P2 changes `requested_values` for every question with a duration; the benchmark has none today, so the 26
  questions cannot show a regression there — the 3 new duration questions are the only cover.
- P3 widens the trigger on prod, where the example step adds 2–7 s. The prod-log replay bounds how many.
- All dev runs used Haiku 5.5; prod may return to Qwen, where attempts and timings differ (**assumed** similar
  ranking of the variants).

## 7. Seen on the way, not in scope

- The event is stored as `mode=abstain`, confidence 0, although a four-sentence answer with citations was shown
  (`evidence_answers_question` false → `_non_answer_outcome`). Probably intended; it skews abstention counts.
- Two more example detectors exist with their own word lists: `_is_example_driven_question`
  (`retrieval_gateway.py`, fired here: 8 example chunks added) and `_question_requests_verbatim_example`
  (`llm_generator.py`). Not unified by this plan.
- The fallback result reports `attempts=0` after three failed attempts (the attempt log has them).

## 8. Reproduction

Scratchpad `/private/tmp/claude-502/-Users-andrejt-Research-repositories-git-NapcoreHelpdesk/cf39e0ee-2c5e-48d8-94b1-f572373e0140/scratchpad/`,
each run as `docker exec -i napcorehelpdesk-backend-1 python manage.py shell < file`:

- `ferry_probe.py` — variants A, B, C (3 runs each, per-attempt errors, the XML);
- `ferry_probe2.py` — validator `/accepting` for PT3M and variant D;
- `trigger_replay.py` — the candidate trigger regex replayed over the logged questions;
- `ev.json` — the prod event of `req-mwb6auo0-n3jh83`.

The scratchpad is session storage: copy the three scripts next to the benchmark before relying on them.
