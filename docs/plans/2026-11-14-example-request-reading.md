# Plan: the model states what the question asks for, the checks compare the example with that statement

Written 2026-11-14 against 0.97.213, for the implementer. Continues `2026-11-13-example-assembly-by-schema.md`:
that plan made the *structure* of a generated example independent of the kind of question (the validator orders,
places and re-references the draft). This plan does the same for *reading the question*. Each claim is labelled
**measured** (re-derived for this plan), **believed** or **assumed**.

## 1. The problem

What the question asks for is read by text patterns in `services/netex_example_generator.py`, one per kind of
thing:

| What is read | Function | How |
|---|---|---|
| values (names, numbers, times, durations) | `requested_values` | quotes, digits, clock and date patterns, capitalised words |
| counts | `counted_words`, `counted_shapes`, `object_counts` | a number word or digit before one to three words |
| parts | `wanted_parts`, `named_object_parts` | "with a/an/one/some …" and the next one or two words |
| the asked object | `example_subject`, `asked_element`, `asked_from_parts` | "example of/for … with/that/in" |
| how the service runs | `service_conditions` | one English pattern, mapped in code to `FlexibleServiceProperties` |

Each pattern was added for a question that failed, and each new phrasing shows a new gap:

- **measured** (65 runs of 13 prod questions, `prod-5.json`): "a line with 2 service journeys" made "2" a value;
  the model wrote `<Description>2</Description>` to pass (fixed by one more pattern, #503).
- **measured** (same run): "a line with a stop place departure" was accepted as a Line alone, 5 of 5 (one more
  pattern, #505).
- **measured** (same run): for 4 of the 9 generated questions no asked object was found at all, and 13 failed
  attempts were `asked-object` rejections of frames whose journeys were right ("a line with two departures").
- **measured** (#503's value table): "3 stop points" is still a value, met with `<Name>3</Name>` or `order="3"`,
  because the words do not match the element name ScheduledStopPoint.
- **measured** (2026-11-13, gen33 and gen34): before the first attempt only the asked object and the values are
  known, not that the frame will hold a vehicle type or stops. So nothing can be said about linking them until an
  attempt has failed (12 of 23 and 9 of 23 first attempts fail on linking alone).
- **believed** (from the patterns, not run): a count in words gets no check; "with departure on Monday" has no
  article and is not seen as a part; the patterns are English, so a Slovenian or Portuguese question is read
  through its translation.
- The condition pattern is the one place where code names a NeTEx element, against the rule of the earlier plan.

## 2. The principle

Reading a question is a language task. The model does it once, in a fixed form; code checks that reading against
the question and the schema, and every later check works from it.

**The reading** is a small JSON object, the reply to one short model call that sees only the question (and a list
of candidate element names, see R0):

```json
{"asked": "Line",
 "objects": [{"kind": "ServiceJourney", "count": 2, "phrase": "2 service journeys"}],
 "values": [{"value": "14:00", "phrase": "at 14:00", "of": "ServiceJourney"}],
 "conditions": [{"phrase": "only on school days"}]}
```

**Code keeps only what it can ground.** This is what makes the reading safe to check against:

1. every `phrase` is a substring of the question (after whitespace folding); an entry whose phrase is not there is
   dropped;
2. every `value` is in its phrase as written, or is the normal form of it that today's code already computes
   (a clock time, a date, a duration);
3. every `kind` and `asked` is an element the schema defines as an object (the validator's `/concrete`, `object`
   true; an abstract one stands for its concrete ones, as in #503); an entry with an unknown kind keeps its phrase
   and loses its kind;
4. `count` is a positive integer and its phrase contains that number as a digit or a number word.

Nothing in the reading can add a fact the question does not contain, so a wrong reading can make a check too
strict or too lax, but cannot put invented content into an example.

**The checks do not change**, only their input: values present, counts met, named objects defined, the asked
object present, everything linked to it. The patterns stay as the fallback when the call fails or returns nothing
usable, and are retired later (§5).

## 3. Steps

Each step is one PR. No step changes an answer before its gate is met.

### R0. Measure the reading offline (no shipped behaviour)

The load-bearing question is whether the model reads questions better than the patterns, and steadily. It can be
answered without generating a single example.

1. A gold file `backend/helpdesk/benchmarks/example-request-readings.yaml`: for gen01–45 and about 30 more
   requests from the prod question log (include the Slovenian and Portuguese ones, and phrasings with counts in
   words), the expected asked object, objects with counts, and values. Written by hand, reviewed by Andrej: about
   75 entries, a few lines each.
2. `read_request(question)` in a new module `services/example_request_reading.py`: the prompt, the call (same
   model and client as the generator, no thinking, small `max_tokens`), the grounding rules of §2.
3. A command `read_example_requests` that runs each question 5 times and reports, per field, against the gold
   file: the reading's score, the patterns' score on the same questions, how often the 5 readings agree, and the
   call's time.
4. Candidate element names for the prompt: **assumed** the model names NeTEx elements well enough alone; measure
   with and without the names from `schema_declarations(question)` and keep the simpler variant if the scores are
   equal.

**Gate R0** (all must hold, else stop and record): on each of asked object, objects-with-counts and values the
reading scores at least as well as the patterns and clearly better on at least one; the 5 readings of a question
agree on at least 95% of questions; median call time under 2 s.

### R1. Counts and named objects come from the reading

The smallest and newest patterns, so the least to lose. `object_counts` and `named_object_parts` take the
reading's `objects` when a reading exists. Gate: gen01–45 x3 — generated and first-attempt counts not below main
beyond run-to-run spread; the count and part cases of §1 pass in words as well as digits; "3 stop points" is three
objects.

### R2. The asked object comes from the reading

`asked_element` and `asked_from_parts` take `asked`. Gate: as R1, plus on the 13 prod questions fewer
`asked-object` failed attempts than the 13 measured, and no question that has an asked object today loses it.

### R3. Values come from the reading

`requested_values` takes `values`; `of` (the object a value belongs to) replaces the guess that two unknown
values need their own objects (`values_rule(own_objects=…)`). This is the largest change: every question has
values. Gate: gen01–45 x5 — generated, first-attempt and linked counts not below main; the value table of #503
re-printed, every difference explained.

### R4. Conditions come from the reading

A condition phrase with no kind is passed to the model as text to express, and checked only by the general
checks. The `_SERVICE_CONDITIONS` pattern and its element name leave the code. Gate: gen27, gen28, gen30, gen32
(the on-demand questions) keep their generated and first-attempt counts over 10 runs each.

### R5 (only if wanted). Linking guidance before the first attempt

With the reading, the kinds are known before attempt 1, which the 2026-11-13 attempt lacked. `link_example` for
each (kind, asked) pair goes into the first prompt. Gate, as set then: 80 runs per side on gen33–36; first-attempt
link failures clearly fall; nothing else worse. B2 showed that a hint can do nothing, so this is measured, not
assumed.

## 4. What is not planned

- **Changing when an example is generated** (`wants_generated_example`, the routing to a standard example). That
  decision runs before retrieval; it is a separate question with its own risks.
- **A new output format for the example.** The frame stays XML, as decided in the earlier plan.
- **Removing the patterns in the same step that replaces them.** See §5.
- **Rules that name NeTEx elements, nouns or questions**, in the prompt or in code. The prompt describes the form
  of the reading; its examples use placeholders.

## 5. Order, cost and retiring the patterns

- Order: R0, then R1–R4 in that order, each behind its gate. R5 is optional and last.
- Cost: one model call per generated example. **Assumed** about 1–2 s (the reply is some 100–200 tokens; a
  generation attempt of 1,700–2,200 tokens takes 8–9 s, measured). R0 measures it. The call needs only the
  question, so it can run while retrieval runs; whether the calling code allows that is **not checked**.
- When the call fails or grounding leaves nothing, the patterns are used, so an outage of the reading degrades to
  today's behaviour. The benchmark counts how often that happens.
- A pattern is removed one release after its step, when the benchmark and the prod log show the fallback unused
  except in outages. Removal is its own PR with its own run.

## 6. Risks

- **A wrong reading makes a wrong check.** A count read where none was meant would force extra objects. Guards:
  the grounding rules, the agreement measure of R0, and that each step replaces one input at a time against a
  gate.
- **The reading varies between calls.** Temperature 0 and the 95% agreement gate; if a question is read two ways,
  the stricter check must not be the one that decides acceptance — R0 lists such questions.
- **The gold file is written by us.** It encodes our reading of each question. Andrej reviews it; the prod
  questions in it are taken as typed.
- **One more dependency on the model.** Covered by the fallback; the outage accounting from P0 applies.

## 7. Working conditions

As §6 of `2026-11-13-example-assembly-by-schema.md`. In addition: R0 needs no validator change and no benchmark
run of the generator; its command writes to `/tmp` in the container. The dev stack must be up before any run
(Docker is started by hand).

## 8. Results

(Each step records its numbers here.)

### R0 (2026-11-14): the reading measured offline. Better than the patterns on every field, not steady: gate failed

Files: `services/example_request_reading.py` (`read_request`: prompt, call, JSON parsing, the four grounding rules
of §2), `benchmarks/example-request-readings.yaml` (78 gold readings: gen01–45 and p01–p33 from the prod log, 21
marked unsure, 10 not in English), `management/commands/read_example_requests.py` (scoring rules in its
docstring), `tests/test_example_request_reading.py` (18 tests, model and validator mocked). Nothing in the
generator calls the reading.

**Setup.** From the host against the dev stack (validator on localhost:8091, database on 5432). Model
`claude-haiku-5-5` through the generator's client (`_request_chat_completion`, Anthropic SDK), thinking disabled,
`max_tokens` 600. Temperature could not be set: the Anthropic path sends no sampling parameter and the installed
SDK rejects `temperature` (checked with one direct call). The patterns' asked object needs the NeTEx example files
on disk: `SOURCE_CHECKOUT_DIR` pointed at a directory whose `NeTEx` is `../NeTEx-upstream`, as the container
mounts it; without it `asked_from_parts` finds nothing and the patterns lose gen01 and gen15. The patterns read
each question as typed (the app gives them its English rendering for the asked object and parts), so the
non-English entries are reported apart as well. Grounding rule 4 knows English number words only. Raw output:
`.mylocal/bench/request-reading-r0-rev0.json` (both variants), `request-reading-r0-rev1.json`; rescored without
calls by `read_example_requests --rescore FILE`.

**Scores** (share of readings right; 5 readings per question and variant, the patterns once). Gated = the 57
entries not marked unsure. **Measured.**

| | asked | objects | values | counts¹ | conditions¹ | readings agree |
|---|---|---|---|---|---|---|
| patterns, gated | 79% | 77% | 91% | 95% | 96% | – |
| reading, question only (rev 0), gated | **88%** | **83%** | **97%** | 97% | 98% | **84%** |
| reading, with candidate names (rev 0), gated | 94% | 90% | 90% | 98% | 96% | 81% |
| reading, question only (rev 1), gated | 90% | 83% | 95% | 93% | 97% | 77% |
| patterns, gated English (47) | 83% | 76% | 91% | 94% | 96% | – |
| reading, question only (rev 0), gated English | 88% | 82% | 97% | 97% | 98% | 83% |
| patterns, unsure (21) | 43% | 67% | 86% | 90% | 95% | – |
| reading, question only (rev 0), unsure | 62% | 77% | 89% | 90% | 95% | 52% |

¹ Reported, not in the gate.

**Variant kept: question only, rev 0.** With the names of `schema_declarations(question)` the asked object and the
objects are better (94%, 90%), but values fall below the patterns (90% vs 91%: the long name list draws values'
`of` and kinds to unrelated elements, `of` stripped 104 times against 26) and agreement is lower; it fails the
gate's first condition, question only does not.

**Prompt revisions.** One, rev 1, motivated by the aggregate (agreement 84%) and by the grounding drops, which were
mostly invented element names, not by single gold entries; it added: name the object also for "how do I describe
/ model / link" requests, use an element name the request writes, list only objects the request mentions, every
element name as the schema spells it or empty. Agreement fell to 77% and values to 95%, so rev 0 stays. No second
revision: the disagreements are between substantive readings drawn at default sampling, and nothing in the prompt
reached them.

**Call time** (question only, rev 0, 390 calls, none failed): median 1.06 s, p90 1.31 s. With candidates: median
1.06 s, p90 1.52 s.

**Grounding** (question only, rev 0): 70 of 390 readings lost something; rule 3 98 times (kind stripped 45, asked
stripped 27, `of` stripped 26), rule 2 9 (value dropped), rule 1 and rule 4 never. The stripped names are words
made into element names (`Lift`, `Elevator`, `Bus`, `Port`, `Timetable`, `DepartureTime`, `SeatingArrangement`,
`WheelchairArea`) and frames: `ServiceCalendarFrame` and `TimetableFrame` are not objects for `/concrete`, so a
question that names a frame (p22) can never keep its asked object, by either side.

**Read more than one way** (question only, rev 0), gated: gen14 (`JourneyPattern` 4, `ServiceJourneyPattern` 1),
gen15 (value 1 left out once), gen23 (asked `Tariff` 2, `FareZone` 3), gen31 (an empty-kind object once), gen36
(`Line` as an object once), gen38 (two departures as `ServiceJourney` 2, as a kind that grounding strips 3), gen45
(`Deck` x2 twice, "two decks" as a value twice, nothing once), p29 (asked `FulfilmentMethod` 1, empty 3,
`ServiceJourneyPattern` 1), p32 (`FareProduct` 2, `PreassignedFareProduct` 3: the same thing). Unsure: gen21,
gen33, gen39, gen44, p02, p13, p14, p23, p25, p31. Per §6, where a question is read two ways the stricter reading
must not decide acceptance; gen23, gen38 and gen45 are such cases (a count present in some readings only).

**Where the patterns still win** (gated, question only): asked on gen01, gen15, p01 (`Vehicle` for a bus with
seats; the gold has `VehicleType`), gen14 (once), gen23 (3 of 5), p33 (Norwegian "how do I link" question: the
model answered that no example was asked for); objects on gen25 (the deck plan never listed, the decks always) and
gen45; values on gen22 ("10 EUR" as one value; the gold splits number and currency), gen15, gen45. The reading wins
asked on gen19, gen41, p03, p06 (a named or unnamed station), gen42, p16, p27, p28 (Slovenian), p29, p32; objects
on gen03, gen20 (the operator), gen14 (3 stop points), gen23, gen36, gen38, p18; values on gen38, gen42, p04 (the
patterns lose "Monday"), gen14 ("3" is a count, not a value) and p01 (a quoted description is no value).

**Gate R0: failed, on agreement.** Asked, objects and values are each at least the patterns' score and clearly
better on all three (+9, +6, +6 points); median call 1.06 s is under 2 s; but the five readings agree on 84% of the
gated questions, against 95%. R1 is not started. What would decide it: a call that can be made deterministic
(temperature 0 is not available on this client), or a gate that accepts a reading only when its runs agree
(majority or unanimity of several calls, at several times the cost), or an agreement measure on the checks a
reading leads to rather than on its exact content (p32's two names are one check). Each is a change of the gate,
for Andrej to decide, not taken here.
