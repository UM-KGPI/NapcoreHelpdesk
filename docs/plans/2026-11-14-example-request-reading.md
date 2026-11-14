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
