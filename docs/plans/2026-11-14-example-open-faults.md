# Plan: four open faults of generated examples

Written 2026-11-14 against 0.97.216, for the implementer. Continues
`2026-11-13-example-assembly-by-schema.md` (§7 records #503, #505 and #512). The request-reading plan
(`2026-11-14-example-request-reading.md`) is closed: three variants failed their gates, so the question is still
read by the patterns, and these faults are fixed there. Each claim is labelled **measured** (from the stored runs
in `.mylocal/bench/`), **believed** or **assumed**.

## 1. The faults

| | Fault | Evidence |
|---|---|---|
| F1 | A time the question writes without seconds ("14:00") is written as it stands, and the schema rejects it | **measured**: `'14:00' is not a valid value of the atomic type 'xs:time'` on 8 failed attempts in 10 gen38 runs (`gen38-frames-10.json`) and on 2 and 3 failed attempts in 3 gen32 runs (`r1-main.json`, `gen38-frames-all.json`); each costs the run one of its attempts |
| F2 | A weekday in the question is not a value and nothing checks it | **measured**: gen38's values are `['14:00']`; all 10 accepted answers (and 3 of 3 on prod) carry "Monday" only as the id of a `DayTypeRef` to an object the frame does not define |
| F3 | "example of NeTEx in XML for a line …" makes the standard's name the subject | **measured** (#512's diagnosis): `asked_subject` returns "NeTEx" for gen42, so there is no asked object, no skeleton for it and no asked-object check; gen42 is accepted 3 of 3 on the first attempt without one |
| F4 | A stop place with a parking: the parking is left unlinked | **measured**: gen18 never passes the first attempt (0 of 16 runs across `gen18-main.json`, `r1-main.json`, `gen38-frames-all.json`) and the accepted answer has an unlinked Parking in 8 of 16; the failed attempts are `parkings` or `ParkingRef` written inside the StopPlace (`wrong-parent`) and "nothing links the Parking to the StopPlace" |

Not in this plan: gen38's first attempt still fails in 10 of 10 runs, because the first prompt does not know that
the asked object and the values need two frames (#512 changed only the feedback). It is noted in §5.

## 2. Rule for every step

General mechanisms only. No rule in code or prompt names a NeTEx element, a noun of a question, or a benchmark
question. What a step may use: the schema (through the validator), the standard's own examples, the attempt
itself, and closed vocabularies of the language of the question (number words are one already; weekday names are
another). Names of standards are already known to the app and may be read from there.

## 3. Steps

One branch, one commit per step, in this order. Each step is measured on its own, against the state before it,
and taken out again (a revert commit) if its gate fails. The order is by risk: F1 and F3 are small and certain,
F2 changes what counts as a value, F4 starts with a diagnosis and may end without code.

### F1. A time is given to the model in the schema's form

`values_line` already tells the model how the schema writes a duration ("3 minutes (an xs:duration PT3M …)"). Do
the same for a clock time: the prompt gives "14:00" with its schema form "14:00:00". The value check already
accepts the written form (`holds_value`, `_clock_seconds`); it must keep accepting both.

- **Assumed**: the missing seconds are the whole cause. The rejections are all on elements of type `xs:time`; a
  time inside an `xs:dateTime` is not in the stored runs.
- Gate: the `xs:time` rejections on gen32 and gen38 (x10 each) fall clearly from 2–3 in 3 runs and 8 in 10 runs; first
  attempts on the questions with a time (gen06, gen16, gen24, gen32, gen38, gen39, gen42 and any other the value
  table shows) not below main.

### F3. The name of a standard is not the subject

Where the subject pattern stops on the name of a standard ("example of NeTEx in XML for a line"), read on: the
subject is what follows the next "of/for". The names come from the app's list of standards, not from a list in
the generator. "A NeTEx example of …" already works and must not change.

- Gate: gen42 gets an asked object (a line), in the benchmark output `askedObject`; a table of `asked_subject`
  and `asked_element` for all 45 questions and the prod questions (`.mylocal/bench/prod-questions.yaml`) before
  and after, every difference explained; gen42 x10 generated not below main (it gains a check, so a lower first
  attempt count is expected and is reported, not a failure, when the accepted answers hold a Line).

### F2. A weekday is a value

A weekday name in the question joins the values, so the value check asks for it in the example. Two parts:

1. Reading: weekday names as a closed vocabulary, like the number words. English at least; say which other
   languages the questions in the prod log need, and whether the app's English rendering of the question is
   what the generator reads (**believed**, not checked).
2. Checking: the schema writes days of the week as a list in one element ("Monday Tuesday"), so "the whole
   content of an element" is too strict here: a value that is one item of a whitespace list must count. Find out
   from the schema (the validator) whether a field is a list type and do not guess from the element name. If that
   cannot be had from the validator without naming elements, accept a value as one whole token of an element's
   content only for values of this vocabulary, and say so.

- **Believed**: once the day must be in the example, the model writes the object that holds it and the reference
  to it resolves. If it instead writes the day into a name or description to pass the check, that is the same
  fault as #503's `<Description>2</Description>` and the step fails.
- Gate: gen38, gen39 and gen42 x10 — the day is in every accepted answer in a field the schema has for days, not
  in an id, a name or a description; generated not below the state before the step; first attempts reported. All
  45 x3: no question loses generated answers; the values of every question before and after, every difference
  explained (a weekday that is part of a quoted or proper name must not become a second value).

### F4. The parking that stays unlinked (diagnosis first)

No fix is planned before the cause is known. What must be answered, from the stored attempts and by running the
functions by hand:

1. How does the standard link the two: which object refers to which, and through which element? Take it from the
   schema and from the standard's examples, not from memory.
2. What does `link_example(element, asked)` return for this pair, and is it right? The link feedback is built
   from it. **Believed**: the feedback ("link it to the StopPlace by a reference") sends the model to write a
   reference inside the StopPlace, which the schema does not allow there, where the standard links from the other
   side (the parking names the place it belongs to). If so the fault is the direction of the link in the
   feedback, and it would hit every pair the standard links from the part to the whole.
3. Which other pairs in the benchmark and the prod questions show the same shape (`wrong-parent` on a reference
   to the part, then `link`)?

Fix only what the diagnosis shows to be a mechanism: for example a `link_example` that looks for the link in both
directions and says which object carries the reference. If the cause is particular to this pair, record it and
stop.

- Gate: gen18 x10 — unlinked answers clearly below 4–6 of 10, and the Parking is linked the way the standard
  links it; gen33–gen36 (the linked-object questions) x10 not worse in linked or first-attempt counts; all 45 x3
  no loss.

## 4. Measuring

- Baseline for all 45 x3: `r1-main.json` and `gen38-frames-all.json` (the generator's first prompt has not
  changed between them). Where a question's difference could be noise, run it x10 on both sides the same day.
- Every gate reads the accepted answers, not only the counts: an answer accepted because a check became laxer,
  without the asked content, is a failure.
- After the last step: all 45 x3 once more on the final state, and the result of each step in §7 of
  `2026-11-13-example-assembly-by-schema.md`.

## 5. Not planned

- The first attempt of a question whose asked object and values need two frames (gen38, 0 of 10 first attempts).
  It needs to be known before the first attempt which frame holds what; the skeleton may already have it. A step
  of its own, after these.
- Reading the question with a model call (closed, see above).
- Counts in words for kinds the patterns do not name ("3 stop points"): the reading fixed it, the patterns do
  not; open.

## 6. Risks

- **F2 makes a check stricter for every question with a weekday.** If the model cannot place the day, questions
  that are answered today fall back to the standard's example. The gate reads generated counts for that reason.
- **F3 gives gen42-like questions a check they did not have.** Same risk, same gate.
- **F4's believed cause may be wrong.** That is why it is a diagnosis first.
- **Four steps on one branch.** A later step is measured on top of the earlier ones; a failed step is reverted
  before the next starts, so each gate compares two states that differ by one step.

## 7. Results

(Each step records its numbers in §7 of `2026-11-13-example-assembly-by-schema.md`; this section links them.)
