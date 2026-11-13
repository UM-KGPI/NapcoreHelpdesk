# Plan: a generated example links the objects it defines to the object the question asks for

Written 2026-11-12 (Fable) against 0.97.196 (main, same build on prod), for the implementing agent (Opus).
Each claim is labelled **measured** (re-derived for this plan), **believed** or **assumed**. Nothing here was run
on the dev stack: the measurements are the prod record of one question, the code as read, and a local copy of
the NeTEx XSD (from the PR #765 review; it may differ from the schema commit prod validates against, 5d2e569).

This replaces P4 of `2026-11-10-example-request-named-object-durations.md` ("should the answer say which
conditions the example leaves out?"). The prod answer below shows the conditions are not left out; they are
written as objects that nothing connects.

## Revision 4 (2026-11-13, Fable), after S1 went live. Read this first

State: S1 is live (0.97.198, PR #471). S2–S4 of Revision 3 are not started. This revision adds one step (T) before
them and folds S3 into it.

### What the live run showed

Prod, the Maribor–Ptuj question again (`req-diag-s1-1794542419`), **measured** from its attempt log:

| Attempt | On the `Line` | Result |
|---|---|---|
| 1 | `Name` "Maribor - Ptuj" | `order` only (`RestrictedLine` before `UserTypes`) |
| 2 | the same, order fixed | `value`: "Maribor … must be the whole content of an element" |
| 3 | `Name` "Maribor", `ShortName` "Ptuj" | accepted, no unlinked objects |

The accepted example says the line is called "Maribor" and its short name is "Ptuj". It is valid, holds both
values and has one object, so no check objects and `valuePlaces` reports it as correct. The value feedback caused
it: it says where a value may not be and not where a place belongs, and the split is the cheapest way to obey.
The same mechanism as the `<Name>3</Name>` case of 2026-11-10 (`req-mwb6auo0-n3jh83`).

On the dev benchmark the split is in 0 of 12 generated gen33 runs after S1 and in 4 of 5 with R1 (**measured**
by counting; the attempt logs of those 4 were not read, so "same mechanism" is **believed** for them). Why prod's
first attempt differs from dev's is **not known** (different retrieved evidence is the guess).

### T0 result (2026-11-13, Opus): 21 flagged, all wrong as written, all after a value failure

Replay of `shared_name_values` (naming children = local name ending in `Name`, plus `Description`; a child whose
words occur in the question is skipped) over every stored valid generated example: prod log (40 + the live run),
dev DB (5), and the benchmark JSONs (`.mylocal/bench/t0.py`, output `t0.out`). **Measured.**

| Source | valid generated | flagged |
|---|---|---|
| prod log to 2026-11-12 | 40 | 0 |
| prod live run `req-diag-s1-1794542419` | 1 | 1 |
| dev DB | 5 | 0 |
| benchmarks base, p1, p2, r1, r1-5 (incl. p1-examples) | 419 | 17 |
| s1 + s1-10 (main) | 123 | 3 |

- Every flag is a `Line` holding two values of a gen33/gen34-style question: Maribor/Ptuj, Koper/Piran, and once
  operator + place (gen20 "a line operated by LPP in Ljubljana" -> `Name` LPP, `Description` Ljubljana, p2). Judged
  by eye: none is right as written. Holder pairs seen: Name+ShortName, Name+Description, ShortName+Description.
  No narrowing of the rule needed.
- In all 21 the example was accepted after a `value` failure ("must be the whole content …"): directly before the
  accepted attempt in 20, at attempt 1 in gen20 (then an order error). This includes the 4 R1 gen33 runs.
  The value feedback causes the split; **measured**, no longer believed.
- Baseline on main (S1, for T4): gen33 0 of 12 generated runs split; **gen34 3 of 12** (s1 1/3, s1-10 2/9);
  gen35, gen36 0 of 3; gen01–32 0. So the fault is live on main for gen34 too, not only the one prod draw.

### S2 result (2026-11-13, Opus): order repaired in the validator, condition met

Replay: of 103 distinct stored fragments that failed on `order`, 93 validate after the repair; the other 10 have
a second problem (a duplicate in a single slot, or an error libxml2 reported only after the order was fixed),
so they are correctly left to the model. Benchmark `s2.json` + `s2-10.json` against T (`t.json` + `t-10.json`),
gen01–32 3 runs, gen33–36 13 runs. **Measured.**

| | T (main) | S2 |
|---|---|---|
| valid | 148/148 | 148/148 |
| first attempt, all questions | 98 | 102 |
| mean time, all runs | 8.3 s | 8.1 s |
| failed `order` attempts (3-run / 10-run) | 10 / 24 | 3 / 7 |
| attempts repaired | 0 | 24 |
| gen33 linked | 1 of 12 | 3 of 13 |
| gen36 first attempt, mean time | 6, 11.4 s | 9, 10.1 s |

gen01–32 first attempts 79 -> 78 (one repair happened there; noise). On gen33 the freed attempt mostly goes to
the link feedback and then a `wrong-parent` on the linking object: the model writes `serviceJourneys` in the
ServiceFrame (7 of 9 linked attempts in T). R3 below targets that.

### T1–T4 result (2026-11-13, Opus): release condition met, PR #474

Benchmark on the PR branch, `t.json` (gen01–36, 3 runs) and `t-10.json` (gen33–36, 10 runs), against S1
(`s1.json`, `s1-10.json`). gen33–36 below are 13 runs (10 + 3). **Measured.**

| | S1 (main) | T |
|---|---|---|
| gen01–32 valid | 96/96 | 96/96 |
| gen01–32 first attempt | 82 | 79 (limit 77) |
| gen01–32 mean time | 4.1 s | 4.4 s (limit 5.1 s) |
| gen33 generated / split / linked | 12 / 0 / 0 | 12 / 0 / 1 |
| gen34 generated / split / linked | 12 / 3 / 8 | 11 / 0 / 5 |
| gen35 generated | 3/3 | 13/13 |
| gen36 generated / first attempt | 3/3 / 0 | 13/13 / 6 |
| gen33, gen34 mean time | 17.9 s, 16.7 s | 21.8 s, 23.8 s |

- No split in any of 153 runs (S1: 3 of 12 gen34 runs).
- gen34 generated is one below S1 (11 vs 12), read as met: S1's 12 hold the 3 split examples, so correct
  generated examples went 9 → 11; the 2 others fell back to the standard's example. S1's "linked" 8 includes
  the 3 splits (one object is trivially linked); without them 5 of 9, now 5 of 11.
- gen33/gen34 take 4–7 s longer: the split no longer passes, so more attempts run.
- S4, the linked share: gen33 1 of 12, gen34 5 of 11, gen35/36 all (one object or already linked). gen33 is
  under half, so R3 of Revision 2 (the linking object's excerpt in the feedback) is the next step for it.

### T. Two of the question's values are not two names of one object

**T0. Replay first (no shipped code).** New function `shared_name_values(fragment, values) -> list[dict]`: for
each object (an element with an `id`, as in `unlinked_objects`), the question's values that are the whole content
of its direct naming children. Start with the children whose local name ends in `Name`, plus `Description`. Two or
more different values in one object is a finding: `{"element", "id", "holders": {"Name": "Maribor", …}}`.
Run it over every stored valid generated example (prod and dev logs, the bench JSONs) and report: how many are
flagged, each one judged by eye, and for the 4 R1 runs above whether a `value` failure preceded the split.
- Not a finding when the question names the field: the holder's words occur in the question ("short name",
  "description"). `PublicCode`, `PrivateCode` and other non-name children do not count, so "line 12 named City
  Express" is clean.
- If the replay flags a case that is right as written, narrow the rule on that evidence and say so; if it cannot
  be narrowed, stop and report.

**T1. The check (hard, class `value`).** After `_unmet_values` finds nothing, `shared_name_values` runs. A finding
is an error like a missing value, because the value is not where the example claims it is:
"Maribor and Ptuj are written as Name and ShortName of the one Line. A Line has one name. Give each value that
names something else (a place, a stop, an operator) its own object with that Name, and link the object to the
Line." Without an asked object: the same without the last clause.
Hard and not soft: the soft rule of Revision 2 keeps an example that is true but incomplete; this one is false.
When no attempt is left, the best earlier attempt or the standard's example is returned as today.

**T2. The value feedback says where the value goes.** In `missing_value_error`, when the missing value occurs
inside a `Name` or `Description` text of the fragment ("Maribor - Ptuj") and another of the question's values
occurs in the same text, add the same advice: "…: if Maribor is a thing of its own (a place, a stop, an operator),
give it its own object with that Name and link it to the Line." One missing value inside a longer name keeps
today's message.

**T3. The first prompt says it too (this is S3).** The value rule of S3 goes into the first prompt for every
question with values; when `skeletonSkipped == "values"` (two or more values without a holder in the skeleton)
it is followed by the T2 advice in general words. Drop the general sentence if first attempts on gen01–32 go
down; keep the `skeletonSkipped` sentence if gen33–36 gain.

**T4. The benchmark counts it.** `run_example_benchmark` reports per question and in total the runs whose
accepted example has a `shared_name_values` finding (0 after T1 by construction for generated examples; the
figure guards the rule and shows it on main first). Run it on main before T1 for the baseline.

**Tests.** The three prod fragments above (joined name: T2 message; split: T1 finding; a `Line` with two
`ScheduledStopPoint`s named Maribor and Ptuj: clean); "stop place 'Celje Bus Station' with short name 'Celje AP'":
clean; a value in `Name` and another in `PublicCode`: clean; two objects each with one value: clean.

**Release condition** (10 runs gen33–36, 3 runs gen01–32):
- gen01–32 stay 96/96 valid; first attempts not more than 5 below S1's 82; mean time within 1 s of 4.1 s;
- gen33 generated in at least 9 of 10 (S1: 9/10), none with the split; gen34–36 not below their S1 counts;
- report the linked share of gen33–36 (this is the S4 measurement; no second run needed).
If gen33 falls below 9 of 10: do not ship T1; ship T2–T4 alone if they pass on their own, and bring the logs back.

### Order of work

1. T0 replay and the T4 baseline on main. Report before building if anything is flagged that looks right.
2. T1–T4, one PR.
3. S2 (order repair, Revision 3), own PR. It matters more now: attempt 1 of the live run was lost to order alone,
   and T1 can use the attempt it frees.
4. The linked share after both; R3 only if it is under half.

Not changed: the whole-content rule itself. Accepting "Maribor - Ptuj" as the line's name was considered and
rejected: it is true data, but it reopens the rule that the 2026-11-10 plan put in on purpose, and it gives a
poorer example than a line with its two stops.

## Revision 3 (2026-11-13, Fable), after R1 and R2 were measured

State: PR #471 (subject fix + link check + R1 soft handling + R2 sentence) is open, CI green, **not merged**.
Release condition of Revision 2 failed: gen33 generated 5 of 8 with R1 (main: 11 of 11). Everything below is
**measured** unless labelled.

### S1 result (2026-11-13, Opus): release condition met

Skeleton skipped (replay): benchmark gen33, gen34 only; prod 2 of 29 example questions with an asked object (both
"from A to B" / "between A and B"); dev 0 of 11. Benchmark, dev (**measured**):

| | result | condition |
|---|---|---|
| gen01–32, 3 runs | 96/96 valid, 82 first attempt, 4.1 s mean | 96/96, ≥ 75, ≤ 4.5 s |
| gen33, 10 runs | 9/10 generated | ≥ 9/10 |
| gen34, 10 runs | 9/10 generated | ≥ 7/10 |
| gen35, gen36, 3 runs | 3/3, 3/3 | 3/3 |

Of the generated gen33 examples (13 runs in all, 12 generated), 0 are fully linked and 12 carry the sentence; gen34:
8 with no unlinked object, 4 with the sentence. Linking the prod question is S2–S4's work.

### What R1 showed

| gen33 | generated | of those fully linked |
|---|---|---|
| main (R0 + baseline) | 11/11 | 0 |
| R1 as in the PR (with skeleton) | 5/8 | 1 linked by a Route; 4 are a Line alone |
| R1 without the skeleton | 5/5 | 1; the other 4 returned with `unlinkedObjects` and the sentence |

- R1 works: nothing valid with the values is discarded any more, and the soft path returns it with the sentence.
- The remaining loss is the skeleton. For gen33 it is `Line_with_facilities.xml`: a Line with an
  `AccessibilityAssessment`, facilities and notices, and no element that can hold a second place name. Its
  instruction says "write the question's object in this shape … put the question's values in the elements that
  hold such values". The model obeys: it models low-floor inside the accessibility block (`LowFloor`: wrong parent)
  and day types inside the Line (`dayTypes`: wrong parent), and runs out of attempts before the values are placed.
  Without the skeleton it goes straight to two stop points (5/5).
- The rule Revision 2 proposed ("no skeleton when `value_holders` is empty") is wrong as written: it also drops
  the skeleton for 11 old questions that pass on the first attempt with it (gen02, 04, 05, 08, 11, 12, 13, 17, 27,
  28, 31): one name fits the asked object's own `Name`.
- Where the attempts go (R1 run, 41 failed attempts): `value` 14, `order` 11, `wrong-parent` 8, `link` 4. For
  gen33 without the skeleton the sequence is `value` → `order` → `link` in 4 of 5 runs: the link feedback arrives
  on the last attempt, when nothing can act on it.

So two different things are needed: stop the skeleton from misleading (to ship), and free attempts so the link
feedback can be acted on (to get linked examples).

### S1. The skeleton only when the question's values fit in it (ships PR #471)

Rule, in `_generate` where the skeleton is chosen: do not give the skeleton when the question has **two or more
values with no known holder** (`value_holders(values)` empty and `len(values) >= 2`, counted values excluded as
today). One such value fits the asked object's own `Name` (gen02 "Ljubljana Bus Station"); two cannot both be the
name of one object, so they belong to other objects and the asked object's shape alone tells the model nothing
about where. Record it in the result: `skeletonSkipped: "values"`.

- In the benchmark this touches gen33 and gen34 only (the list above: every other holderless question has one
  value). Confirm by printing, for all 36 questions, whether the skeleton is given before and after.
- Unit tests: two holderless values → no skeleton, no SKELETON block in the prompt; one → skeleton as today;
  typed values (a time, a number with a holder) → as today.
- Replay over the prod and dev example questions: list those that lose the skeleton. Read them; each should be
  of the "from A to B" / "between A and B" kind. Anything else: stop and report.

Release condition for PR #471 (unchanged in spirit, now with more runs because 3 were too few to tell 5/5 from
5/8):
- gen01–32, 3 runs: 96/96 valid, first attempts ≥ 75, mean ≤ 4.5 s (today 77–78, 4.0–4.4 s);
- gen33 and gen34, **10 runs each**: generated at least 9/10 and 7/10 (main: 11/11 and 6/8);
- gen35, gen36, 3 runs: generated 3/3 as today.
If met: add the numbers as a PR comment, merge, deploy. Report, without promising: how many of the 10 are fully
linked and how many carry the sentence.

### S2. Repair element order without the model (own PR, after S1)

`order` is the second largest class of failed attempts (11 of 41) and costs a whole model call each time,
although nothing has to be decided: the schema fixes the order of an element's children. The validator already
knows it (`netex_content_model.py` reports `order` from the parent's slots).

- New in the validator service: for a fragment whose only errors are `order`, return the fragment with each
  offending parent's children sorted into slot order (stable within a slot), revalidated. Only when every child
  of that parent is in a slot; otherwise no repair.
- Generator: if the repaired fragment validates, continue with it as if the model had written it; log the
  attempt with `repaired: "order"` and do not count a model call.
- Check: unit tests on the order errors in `.mylocal/bench/r1.json` (the stored fragments: `lines` before
  `scheduledStopPoints`, `FlexibleServiceType`, `DepartureTime`, `Description`); replay all stored `order`
  fragments and report how many validate after repair; benchmark: gen01–36 valid count unchanged or better,
  first attempts up, mean time down. **Believed**, not measured: most of the 11 are repairable.

### S3. Say the value rule before the first attempt (own PR, after S2)

As in Revision 2 ("Separate, optional"), now with a reason to do it: `value` is the largest class (14 of 41) and
is the first failure of gen33 in almost every run (the model writes "Maribor–Ptuj" in a Name). Own benchmark;
drop it if first attempts on gen01–32 go down.

### S4. Then measure linking again

After S2 and S3 the usual gen33 sequence should have one or two attempts left when the link feedback arrives.
Run gen33–36 at 10 runs and report the linked share. Only if it is still under half: R3 of Revision 2 (the excerpt
of the linking object in the feedback).

### Order of work

1. S1 on the PR branch, measurements, merge and deploy if the condition holds.
2. S2, S3 as separate PRs, each with its benchmark.
3. S4 measurement and a short report.

Not changed: R1, R2, the link check, P3 (property as a name) still gated on its replay.

## Revision 2 (2026-11-12, Fable), after P0–P2 were measured

Read this first. It replaces §3 and §4 where they differ; the status sections below hold the measurements it
rests on. Labels as before: **measured**, **believed**, **assumed**.

### What the first version got wrong

1. **It treated a missing link as a failed example.** A fragment that is schema-valid and holds the question's
   values was thrown away for not being linked, and the user got the standard's example without their values. On
   main that same fragment is shown, and Andrej judged it acceptable ("it looks ok to me"). So every step made the
   prod question worse: gen33 generated 3/3 on main (6/6 with the re-run), 0/3 with P1, 1/3 with P1+P2
   (**measured**).
2. **It assumed linking was the bottleneck.** In 108 runs the link check fired in 3 attempts. For gen33 the model
   fails earlier, on the value check and on schema order, and the runs that fell back ended on `order`,
   `wrong-parent`, `value` and `asked-object`, not on `link` (**measured**, `p1.json`, `p2.json`).
3. **It did not ask for the evidence that would show why.** The attempt log keeps each attempt's first error but not
   the fragment, so nobody has seen what the model writes for gen33 with P1. Whether the skeleton
   (`Line_with_facilities.xml`, whose Name is "Line 24 Alpha to Charley") or the asked-object check causes the
   regression is **not known**. §2's "F1 is the root cause" was right about the resolver and wrong about what
   resolving it would buy.

What held: the resolver fix finds the right objects and changes nothing else (replay: prod 2 of 452, dev 0 of
320); `unlinked_objects` has no false positive in 113 stored fragments (8 flagged, 8 real); gen01–32 stay 96/96.

### The principle for the rest

Two kinds of problem, handled differently:
- **Hard** (as today): not schema-valid, a value of the question missing, the asked element absent. Retry; after
  the last attempt, the standard's example.
- **Soft** (new): schema-valid, values present, but objects not linked to the asked one. Retry while attempts
  remain, to improve it. **Never discard for it.** Keep the best acceptable fragment seen so far (fewest unlinked
  objects) and return that at the end, with `unlinkedObjects` when not empty.

Consequence, by construction and to be confirmed by measurement: with the resolver fix on, a question can only
lose against main through the model's own variance or through the skeleton, not through a check. R0 measures the
skeleton's part.

### R0. See what the model writes (diagnosis, no shipped behaviour)

1. Store each attempt's fragment in the result (`attemptLog[n].fragment`, benchmark and trace; cut at 4,000
   characters). Small, and needed for every later failure analysis.
2. gen33 and gen34, 5 runs each, three configurations: main; the branch with the skeleton switched off for these
   runs (patch `skeleton_for` to return None in a shell, not in code); the branch as it is. Report per
   configuration: generated n/5, and for each failed attempt what the fragment did with Maribor and Ptuj.
3. Decide from that, not before:
   - if the regression follows the skeleton: the skeleton must not be given when it holds none of the question's
     values and `value_holders` is empty (**believed** to be the gen33 case), or it needs the linked companion;
     write which, with the fragments as evidence;
   - if it follows the asked-object check: R1 removes it as a hard failure, nothing more needed;
   - if neither (pure variance): say so, with the 5-run numbers of all three.

Stop and report after R0 if the cause is none of the three.

### R0 result (2026-11-13, Opus): the asked-object check causes the regression, not the skeleton

gen33/gen34, 5 runs per configuration, each attempt's fragment kept (`.mylocal/bench/r0.json`; "main" = the branch
with main's subject pattern and prompt and no link check). **Measured:**

| | main | branch, no skeleton | branch |
|---|---|---|---|
| gen33 generated | **5/5** | 0/5 | 0/5 |
| gen34 generated | 4/5 | 2/5 | 3/5 |

- In all 5 main runs the accepted fragment holds Maribor and Ptuj as the `Name` of two `ScheduledStopPoint`s that
  nothing links to the Line.
- The branch reaches that same fragment (or one with the values in unlinked `DestinationDisplay`s or `StopPlace`s)
  in 8 of 10 gen33 runs, and the second half of `asked_object_problem` rejects it ("the values … are neither in it
  nor in an object that refers to it"), mostly on the last attempt. Under R1 those 8 runs return a generated
  fragment; the other 2 never placed the values as whole content (value check, as on main).
- Without the skeleton the result is the same (0/5), so the skeleton is not the cause. With it the model tries the
  conditions more often (VehicleType, DayType, DestinationDisplay appear), which costs attempts.

Decision as planned: R1, nothing more.

### R1. Soft handling of links (changes the branch's P2)

In `_generate`:
- `asked_object_problem` keeps only its first half as a hard error (the asked element is absent). Its second half
  (values neither in the asked object nor in a linked one) is dropped: when every object is linked, every value is
  in a linked object, so `unlinked_objects` covers it and gives the better feedback.
- After schema and values pass: `link_problems`. If empty, return. If not, remember the fragment as the best so
  far when it has fewer unlinked objects than the remembered one, and retry with the link feedback if attempts
  remain.
- At the end, or when a later attempt fails hard: return the remembered fragment (valid, `origin: generated`,
  `unlinkedObjects`). Only without a remembered fragment: today's failure path and the standard's example.
- This replaces the branch's last-attempt rule, which keeps the fragment only when the **last** attempt is the
  acceptable one.

Unit tests: acceptable-then-broken (attempt 2 acceptable but unlinked, attempt 3 schema-invalid → attempt 2 is
returned with `unlinkedObjects`); acceptable-then-linked (attempt 3 returned, no field); two acceptable ones (the
one with fewer unlinked objects); the fare product whose price group does not refer to it
(`SkeletonGenerationTests`) still retried, now with the link feedback.

Check, 3 runs, plus 5 runs for gen33/34:
- gen01–32: 96/96 valid; first attempts and mean time within the run-to-run range seen today (77–78, 4.0–4.3 s);
- gen33–36: generated at least as often as main in the R0 runs. This is the release condition for the resolver
  fix. If it fails although no check discards anything, the skeleton finding of R0 applies;
- report, do not promise: in how many runs the returned fragment is fully linked.

### R2. Say it in the answer (was P4)

Needed with R1, because R1 shows unlinked fragments on purpose.
- `GeneratedExample.tsx` already has `missingValuesText` for "the example does not hold these values". Add the same
  kind of line from `unlinkedObjects`, built by code: "The example defines a VehicleType and a ScheduledStopPoint
  but does not link them to the Line." Types in `types.ts`; a Vitest case.
- Pass the same sentence to `generated_example_rule` as a fact the text must not contradict.
- F4 (the text denying what the example shows) stays as in the old P4: replay the lack-sentence filter over the
  new answers and extend it only on that evidence.

### R3. Help the model link (only if R1's numbers show the need)

If after R1 the prod question is linked in fewer than half the runs:
- give the link feedback a short excerpt of the linking object from the example file `link_example` found (as
  `condition_example` does: at most 14 lines, "the shape only, not the values"), so the model does not have to
  invent a journey with calls;
- allow one extra attempt only for soft problems (4 in total) and measure the time it costs; do not raise
  `MAX_ATTEMPTS` for hard errors.
Each measured on gen33–36 and gen01–32 as in R1. Drop either if it does not move the linked count.

### Separate, optional: say the value rule before the first attempt

`value` is the largest class of failed attempts (18 of 43 on main, 11 of 41 with P1; **measured**), and gen14 and
gen20 fail on it first in almost every run: the prompt says "use the values", and the rule "each value is the
whole content of an element, not part of a Name or Description" is told only after the first failure. One
sentence in the `Values to use` line could save an attempt on those questions. Not part of this work: its own PR,
its own benchmark, because text added up front has lowered the benchmark before (declarations: 18 → 12 of 20).

### Shipping order

1. R0 (diagnosis) → report.
2. One PR: resolver fix + R1 + R2. Not the resolver fix alone, not P2 as it is on the branch.
3. R3 and the value-rule sentence only on their own numbers.

P3 of §3 (a property written only as a name) is unchanged and still gated on its replay. §5 and §6 stand.

## Status (2026-11-12, Opus): P0 done, P1 implemented and measured, not shippable alone

Dev, 3 runs per question, Claude Haiku 5.5 (**measured**; logs and JSON in `.mylocal/bench/`):

| | gen01–32 valid | first attempt | mean | gen33 (prod question) | gen34 | gen35 | gen36 |
|---|---|---|---|---|---|---|---|
| main (baseline) | 96/96 | 78 | 4.0 s | 3/3 generated, asked "" | 2/3 generated | 3/3 | 3/3 |
| P1 | 96/96 | 77 | 4.3 s | **0/3 generated**: all fell back to the standard's Line without Maribor/Ptuj | 2/3 | 3/3 | 2/3 |

- P1 resolves the right object: gen33/34 → `Line`, gen35 → `StopPlace`, gen36 → `ServiceJourney`; gen01–29 asked
  objects identical before and after. Subject replay: prod 452 distinct questions → 2 change (both newly resolved,
  correct); dev 320 → 0.
- Why gen33 regresses: with `Line` resolved, `asked_object_problem` demands Maribor and Ptuj in the line or an object
  linked to it. On main the model put them in two unlinked `ScheduledStopPoint`s (the unlinked-object count of P2:
  2 of 3 objects in all 3 runs) and passed. With P1 the skeleton (`Line_with_facilities.xml`) has no element that
  holds a place name (`value_holders` → []), the feedback does not say which object links a stop to a line, and 3
  attempts are not enough.
- gen36 is not changed by P1 (same asked object); its one fallback is run-to-run variance.
- The validator's `/declarations` gives the holders P2 needs: `VehicleTypeRef` and `LineRef` in `ServiceJourney`
  (and others); `DayTypeRef` only in the `dayTypes` wrapper, so P2's feedback must name the wrapper's owner.

Conclusion: ship P1 together with P2 (the link feedback that names the bridging object), not alone.

### P2 implemented and measured (2026-11-12, Opus)

`unlinked_objects`, `link_example` (the linking object from the standard's example files, ranked by the number of
files and shared across the unlinked kinds; the validator's parent lists are cut at 12 names), `link_problems`,
the last-attempt rule (`unlinkedObjects`), one prompt sentence, error class `link`. 7 unit tests.

Replay gate (**measured**): prod, 33 stored valid generated examples with an asked object → 4 flagged (the two
Maribor questions; a Parking without ParentSiteRef, twice); benchmark P1 fragments, 80 → 4 (the same Parking; a
GroupOfLines/LineNetwork "Ljubljana" holding no line). All 8 are real misses; no false positive.

| | gen01–32 valid | first attempt | mean | gen33 | gen34 | gen35 | gen36 |
|---|---|---|---|---|---|---|---|
| P1 + P2 | 96/96 | 77 | 4.3 s | 1/3 generated, 2 fallbacks | 2/3, 1 fallback | 3/3 | 3/3 |

The link check fired once in 108 runs (gen18). gen33 does not get that far: the model cannot place Maribor and
Ptuj ("value" first, then "asked-object"); the one generated run passed by writing `<Name>Maribor</Name>` and
`<Description>Ptuj</Description>` in the Line. The bottleneck is where place names go for a Line (stop points in
a journey or route), before linking.

## 1. The problem, measured

Prod question `req-mwdzf8px-3qfhdl` (2026-11-12, 0.97.196, read through `/questions/events/<id>`):

> Give me a NeTEx example of a bus line from Maribor to Ptuj that runs only on school days and uses low-floor vehicles.

The generated example is schema-valid (3 attempts, 17.7 s of generation) and contains, in a `CompositeFrame`:
a `VehicleType` named "Low-floor bus"; a `FareDayType` "School day" with `HolidayTypes` = `SchoolDay`; a `Line`
with `Description` "School day service with low-floor vehicles"; two `ScheduledStopPoint`s named Maribor and Ptuj.

Four faults, all **measured** on that record:

| # | Fault | Evidence |
|---|---|---|
| F1 | The asked object was not resolved | trace: `askedObject: ""`, `skeletonSourcePath: ""`, `askedObjectPresent: false` |
| F2 | No object refers to another: the line, the stop points, the vehicle type and the day type are five unconnected objects. The conditions are stated only in the `Description` text | the fragment has no `…Ref` element at all |
| F3 | "Low-floor" is only a `Name`; the schema has a boolean `LowFloor` for a vehicle type | local XSD, `netex_vehicleType_version.xsd:402` |
| F4 | The text contradicts the example: "These show how a school bus line is classified, but not that it runs on school days or that its vehicles are low-floor", next to an example that shows both | the `answer` field |

A fifth observation, not planned as a fix (§5): the day type is a `FareDayType` (fares domain), not a `DayType`.

## 2. Causes

**F1, measured.** `_SUBJECT_WIDE` (`netex_example_generator.py:911`) ends the subject only before
`with|having|has|that|containing|including|for|in|named|called|operated|departing|arriving|at|on|of`, the end of
the sentence, or punctuation. "bus line **from** Maribor" has none of these within three words, so the regex does
not match. Run on the regex alone: the prod question → no match; the same question without "from Maribor to Ptuj"
→ `bus line`; "example of a line between Maribor and Ptuj" → no match.

With no asked object, three things are skipped (`_generate`, lines 2146–2165 and 2262): the skeleton from the
standard's examples, `asked_object_problem` (the check that the question's values sit in the asked object or in
one linked to it by a reference), and the fallback to the standard's example.

**F2, measured in the code.** Nothing checks that an object defined in the fragment is connected to anything.
`asked_object_problem` returns "" as soon as **one** value sits in a linked object, and it does not run at all
without an asked object. The prompt's "Define an object in the frame only when the question asks for it" does not
say to link it.

The schema can express the links (**measured**, local XSD): a `ServiceJourney` may hold `LineRef`
(`netex_serviceJourney_version.xsd:194`), `dayTypes` and `VehicleTypeRef` (`:405`, `:415`); `FareDayTypeRef`
is in the substitution group of `DayTypeRef`. So a linked example needs one more object, a journey.

**F3, believed.** No check compares the words of a `Name`/`Description` with the elements the object's own
structure offers. The existing value check does this only for the question's values.

**F4, believed.** `generated_example_rule` (`llm_generator.py:1444`) tells the model "do not say what the evidence
lacks", and the model did it anyway about cited blocks E2 and E4. The removal filter (#425) did not catch "These
show …, but not that …". The narrator is told which elements hold the question's **values**; the two conditions are
not values, so nothing told it the example covers them.

## 3. The plan (first version; Revision 2 at the top replaces it where they differ)

Order by dependency. P1 is the load-bearing piece: without an asked object nothing in P2–P4 has an anchor.
Each step is one PR with its own measurement; stop and report if a step's check fails.

### P0. Measure before changing anything (no shipped code)

1. Add to `backend/benchmarks/example-generation-questions.yaml`: the prod question (gen32) and three questions of
   the same shape with other objects, so the mechanism is tested and not this wording. Suggested: a ferry line
   between two named ports that runs only on Sundays; a stop place with a named quay served by wheelchair-accessible
   vehicles; a service journey on a named line that runs only on public holidays. Check the wording triggers a
   generated example before fixing the list.
2. Baseline on dev, 3 runs each, existing 31 questions and the new ones: valid, first attempt, time, and for the
   new ones `askedObject` and the number of objects not connected to it (count by hand or with the P2 function
   written first as a script).
3. Confirm on the dev validator that `/declarations?q=VehicleTypeRef` returns the elements that may hold a
   `VehicleTypeRef` in `parents` (**believed** from `_declared_parents`; P2's feedback depends on it). If not,
   P2's feedback names no holder and says only "link it by a reference".

### P1. Resolve the asked object when the subject is followed by another preposition

Extend the endings of `_SUBJECT_WIDE` with the words that can follow the subject noun: `from`, `to`, `between`,
`via`, `through`, `by`, `near`, `during`, `which`, `whose`, `where`, `when`, `running`, `serving`, `operating`,
`connecting`, `using`, `and`, `or`. The match is lazy, so a new ending can only shorten a subject that used to
match, or make one match that did not.

Check (the trigger-replay pattern of the 2026-11-10 plan):
- unit tests: the three regex cases of §2, and "example of a point to point fare" (must not become "point");
- replay `asked_element` over the distinct example questions in the dev and prod logs, before and after; list every
  question whose result changes. Accept only if each change is a newly resolved, correct object. A subject that
  gets shorter and resolves to a different object is a regression: drop the word that caused it;
- benchmark: gen01–31 stay 93/93 valid; record gen32+ after P1 alone. With `Line` resolved, the existing
  `asked_object_problem` already demands Maribor and Ptuj in the line or in an object linked to it, so P1 may by
  itself force a journey or route. Measure this before writing P2: it decides how much P2 has to do.

Rejected: trying every prefix of the three words until one resolves. "fare product" would resolve on "fare" first.

### P2. Check that every object in the fragment is connected to the asked object

New function `unlinked_objects(fragment, asked) -> list[node]`, next to `asked_object_problem`, reusing its
`owner` logic:
- objects: elements with an `id` whose name does not end in `Frame`;
- edges: an object nested inside another object; an element with a `ref` equal to an object's `id` joins the
  object that contains the reference with the referred one. References to objects outside the fragment are ignored;
- result: the objects outside the connected component of the asked object(s). Empty when `asked` is "".

Run it in `_generate` after `asked_object_problem` and before `condition_problems`. Each unlinked object gives one
feedback line:

> the frame defines a VehicleType (hd:VT_LowFloor) that nothing links to the Line. Link it by a reference from an
> object that is linked to the Line; a VehicleTypeRef may be written in: ServiceJourney, … . Define that object if
> the frame has none, and give it a LineRef.

The holder list comes from `_declared_parents(<element>Ref)`, first those that can also hold `<asked>Ref`
(the intersection names the bridging object, here the journey), at most six names. Add "or remove it" only when no
word of the object's element name or `Name` text occurs in the question: an object the question asks for must be
linked, not dropped. Add `link` to `_ERROR_CLASSES` so the attempt log shows it.

One sentence in `_PROMPT`: every object defined in the frame is referred to by, or refers to, the object the
question asks for, directly or through another object in the frame.

**Decision built in (assumed; say so in the PR and let Andrej overrule):** on the last attempt, a fragment that is
schema-valid, holds the values and has only link problems is returned as valid, with `unlinkedObjects`
(element, id) in the result and the trace. Failing it would swap it for the standard's example without the
question's values, which is worse. P4 uses the field to say so in plain words.

Check:
- unit tests on hand-written fragments: the prod fragment (four unlinked objects for asked `Line`); the same with
  a `ServiceJourney` carrying `LineRef`, `dayTypes/DayTypeRef`, `VehicleTypeRef` and two calls (none); a StopPlace
  with nested quays (none); no asked object (none);
- offline replay over every stored valid generated example in the dev and prod logs: how many have unlinked
  objects. This is the expected rise in retries. Report the number. If more than about one in five stored examples
  is flagged, do not ship the retry; ship only the `unlinkedObjects` field and bring the numbers back;
- benchmark, 3 runs: gen01–31 stay 93/93 valid, first-attempt count and mean time reported against P0 (expect
  some loss; more than 5 first attempts or 1 s mean is a stop-and-report); gen32+ valid with no unlinked objects in
  at least 2 of 3 runs each.

### P3. A property written only as a name (measure first, ship only if clean)

New check `named_not_set(fragment)`: for each object, take the 1–3-word runs of its `Name` and `Description`
(lower case, hyphens and spaces removed) and compare them with the names of the child elements its structure
allows (`_structure(element)`, all groups) that the object does not have. A match ("Low-floor bus" ↔ `LowFloor`)
gives the feedback: "the VehicleType is named 'Low-floor bus'; it has an element LowFloor for that: set it".

Replay over the stored valid examples first. Ship only if every flagged case is right; candidates for false
positives are placeholder names that equal a child element ("Line 1" under an object with a `Line` child), so
require a match of two or more camel-case parts or a boolean/enumerated child if the replay shows them.
If the replay is not clean after that, drop P3 and record why.

### P4. The text agrees with the example

Only after P2, on the benchmark answers of gen32+:
- add the linked objects whose element-name or `Name` words occur in the question to `valuePlaces`
  (value: the question's words, element, path), as `condition_places` does for service conditions, so the line
  above the fragment and the narrator's brief cover them;
- when `unlinkedObjects` is not empty, the answer gets one sentence built by code, not by the model: "The example
  defines a VehicleType but does not link it to the Line." Look at how `valuePlaces` reaches the frontend before
  choosing where it is shown (not read for this plan);
- then replay the lack-sentence filter over the new answers. If "…, but not that …" sentences without a citation
  remain next to a generated example, extend the filter the way #425 did, measured by replay over all stored
  answers with a schema block (none removed that states a cited fact).

## 4. Expected result (first version; see Revision 2: a linked example is reported, not promised)

The prod question returns a `Line`, a journey that refers to it, to a day type with `SchoolDay` and to a vehicle
type with `LowFloor` true, and stop points referred to from the journey's calls or pattern; the text does not deny
what the example shows. Not promised: first-attempt validity for this question (it took 3 attempts before), and
the choice of `DayType` over `FareDayType`.

## 5. Not planned

- **A list of condition phrases** ("only on school days" → DayType), as `_SERVICE_CONDITIONS` has for on-demand
  services. It fixes named cases and misses the next one; the link check needs no list.
- **`FareDayType` instead of `DayType`.** Valid and linkable (`FareDayTypeRef` substitutes `DayTypeRef`), wrong
  domain. No general rule for "the plainer element" is known. Look again after P1–P2: the skeleton and the journey
  evidence may change what the model picks. Record what gen32 produces.
- **Saying which conditions are missing** (old P4). After P2 an asked-for object cannot be removed on feedback, and
  an unlinked one is reported by code. A condition the model never writes at all stays undetected; the benchmark
  questions of P0 are the only guard. If they show it, bring it back with the data.

## 6. Risks

- P1 changes which questions get a skeleton and the asked-object check; a wrongly resolved object gives a worse
  example than none. The replay diff is the guard.
- P2 makes fragments larger (a journey, calls), so more schema-order errors and time. The stop conditions in P2
  are the guard; the last-attempt rule keeps a usable example.
- The local XSD used for §2 is not the prod schema commit. The validator decides, not this plan.
- One prod answer is the whole evidence for F3 and F4. P3 and P4 are gated on replay for that reason.
