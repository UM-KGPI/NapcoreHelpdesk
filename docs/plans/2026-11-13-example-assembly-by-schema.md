# Plan: the model decides the content of a generated example, code does the mechanics

Written 2026-11-13 (Fable) against 0.97.204, for the implementing agent (Opus). Continues
`2026-11-12-generated-example-linked-objects.md` (its S2 and R3 are live). Each claim is labelled **measured**
(re-derived for this plan), **believed** or **assumed**.

## 1. The principle

Today the model writes the whole NeTEx frame and code checks it afterwards. Every new kind of question shows a new
way to get the XML wrong, and a rule is added for it. The change of direction:

1. **The model decides what only it can decide**: which objects, which values, which object relates to which.
2. **Code does what the schema already decides**: in which frame and list an object goes, the order of children,
   how a reference is written. No model call is spent on these.
3. **Only checks that hold for every question remain**: the values are in the example, everything is connected to
   the asked object, the asked object is there.

One thing differs from the proposal as first described: the model's description stays **XML, read loosely**, not a
new JSON format. The model's frame is treated as a draft that says which objects, fields and references exist; code
rebuilds the mechanics around it. Reasons, all from this project's own data:
- every step can be measured **offline, without a model call**, by replaying the stored failed attempts (the
  attempt log keeps each fragment since 0.97.197); a JSON format can only be measured by full benchmark runs;
- the evidence the model learns from is XML, and gen01–32 are at 96/96 valid with 4.4 s mean: a new output format
  puts that at risk for no measured gain;
- a JSON description that can hold calls, passing times and properties is XML without its order and wrappers,
  which is what loose reading gives anyway.
A JSON description stays possible later; §6 says when it would be worth trying.

## 2. What was measured (2026-11-13)

Baseline for everything below: `.mylocal/bench/up.json` (gen01–36, 3 runs) and `up-10.json` (gen33–36, 10 runs),
current code, **dev index and validator on upstream NeTEx v2.0 at 5d2e569, the commit prod runs**. Earlier
benchmark files were taken on a branch checkout and are not comparable for gen33/gen34.

- **Failed attempts by kind**, gen33–36 at 10 runs: 65 failed attempts, 42 of them (65%) structural (wrong-parent
  19, missing-required 12, order 6, undeclared 4, keyref 1), 21 about meaning (link 17, value 4), 2 other.
- **What the structural ones are** (`.mylocal/bench/agnostic_probe.py`, 75 diagnostics over both files):

  | Diagnostics | What it is | Who can fix it |
  |---|---|---|
  | 25 | a list or object in the wrong frame (`stopPlaces` in a ServiceFrame 15, `dayTypes` in a TimetableFrame 3, …) | code |
  | 11 | order together with another problem (so S2 did not repair) | code |
  | 16 | `Call` lacks the required stop point reference before `Arrival` | feedback (B1) |
  | 16 | an element inside an object that has no such child (`parkings` in StopPlace, `StartPointRef` in Route) | model, with better feedback |
  | 4 | undeclared element | model |
  | 3 | other missing required children (`PublicCode` in Line) | model |

- **An object has one place.** In the standard's 287 example files, 273 kinds of object sit directly in a frame
  list; 236 kinds have exactly one (frame, list) placement, and 28,110 of 29,009 objects (96.9%) sit in their
  kind's most common one. `Line` → ServiceFrame/lines (289 of 289), `ServiceJourney` →
  TimetableFrame/vehicleJourneys (351 of 351), `StopPlace` → SiteFrame/stopPlaces (2049 of 2055).
- **The excerpt R3 shows is itself invalid.** `_holder_shape` cuts the linking object down to the two reference
  paths and drops required siblings: for StopPlace ↔ Line it shows `Call > Arrival > QuayAssignmentView >
  StopPlaceRef` without the `ScheduledStopPointRef` a Call requires. All 16 `Arrival` failures say exactly that
  ("`Call` needs one of (ScheduledStopPointRef, …) before `Arrival`"); 14 of the 16 come directly after the link
  feedback.
- **S2 works as designed**: 93 of 103 stored order-only failures repaired; but it repairs only when order is the
  only problem, and then the model never sees the sorted frame.
- **Prod is not yet explained.** On identical evidence dev links gen33 in 7 of 12 runs, prod in 0 of 3 since
  0.97.202. Model, link examples and validator verdicts are the same. **Not checked**: the app's answer path
  against the benchmark's call (the English rendering of the question, scope, the number of chunks).
- Seven baseline runs (gen30–32) hit Anthropic API 503 errors and fell back; they are excluded from comparisons.

## 3. Steps

Each step is one PR, measured against `up.json` / `up-10.json`, and stops there: merging and deploying only when
Andrej says "full cycle". Results go into §7 of this file in the same PR.

### P0. The replay corpus and harness (no shipped behaviour)

`backend/helpdesk/management/commands/replay_example_repairs.py` (or a script under `.mylocal/bench` if a command
is too heavy; say which): reads benchmark JSON files and prod event exports, takes every attempt with a fragment
and a structural error class, sends it to the validator, and reports per error class: attempts, valid after
repair, diagnostics before and after. Corpus: every `*.json` in `.mylocal/bench` with fragments (r1 onwards),
`prod-examples*.jsonl`, `prod-failed-fragments.json`. Distinct fragments only.
- Record the starting point (S2 as shipped) in §7.
- Also fix the benchmark's blind spot: a run whose attempts are all `model-error` (API down) is reported
  separately and left out of the valid/first-attempt/time figures, so an outage cannot pass for a regression.

### B1. The link excerpt keeps what the schema requires (small, first, because it is measured and cheap)

In `_holder_shape` (netex_example_generator.py): when cutting the linking object to the reference paths, keep,
at every kept element, the children that fill a **required slot** of its content model (ask the validator: the
structure endpoint, or a new field of it, gives the slots with `min >= 1`). For the Call above that keeps
`ScheduledStopPointRef`. The excerpt must validate as a shape: add a unit test that the excerpt of
`Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml`'s ServiceJourney keeps it.
- When a required child is a reference to a kind the fragment does not define (a ScheduledStopPoint next to
  StopPlaces), the feedback says so in one sentence: "a Call also needs a ScheduledStopPointRef: define a
  ScheduledStopPoint for each stop". Derived from the kept required children, no list of cases.
- Check: benchmark gen33–36, 10 runs. Expect the `Arrival` missing-required class (16 diagnostics) to drop to a
  few and the gen33 linked share to rise from 7 of 12. gen01–32, 3 runs, unchanged within noise (first attempts
  not more than 5 below 71 of 89 clean runs; mean time within 1 s). If linked share does not rise, report the
  attempt logs before going on.

### A. The validator normalizes the draft (the core; three parts, one PR each if large)

All in the validator service, next to `repair_order`; the generator already continues with a repaired frame.

**A1. Order always, not only alone.** Sort every sortable element's children (as S2) even when other problems
remain. Return the sorted frame with the remaining diagnostics (`"repaired": ["order"]`, `"fragment"`, `valid`
false). The generator then continues the conversation with that frame as the model's reply, so the next feedback
is about a frame that is already in order, and the model does not reintroduce or chase order errors.

**A2. Placement by the standard.** At schema load, extend `count_usage` (netex_content_model.py) to record, for
each object kind, its (frame, list) placements in the example files; keep the most common one where the schema
confirms it (the frame's content model has the list, the list's has the kind). Then, for an invalid draft:
- every object that sits in a frame list, in a list the frame does not have, directly in a frame, or directly in
  `dataObjects`/`frames`, and that the content model flags (wrong-parent on it or on its list), is moved into its
  placement; the frame is created when missing (id `hd:<FrameName>_1`, the version of the other frames), and more
  than one frame is wrapped in a `CompositeFrame > frames` when the root is not one already;
- a list wrapper that no frame has (`serviceJourneys`, `sites`) is dissolved: its objects are placed one by one;
- nothing is moved that the content model accepts where it is; an object nested inside another object (a
  `Quay` in a StopPlace, a `Call` in a journey) is never moved;
- kinds without a confirmed placement, or with two placements within a factor of 3 in the examples
  (`VehicleType`: ResourceFrame 6, InfrastructureFrame 6), are left alone unless one of the candidate frames
  already exists in the draft.
Then A1's sort, then validation.

**A3. References follow their target.** For each `…Ref` element whose `ref` names an id defined in the draft:
- the `version` is set to the target's (the keyref failures);
- when the element name is undeclared or not a child of its parent, and the parent's content model has a
  reference element for the **target's kind** (`ScheduledStopPointRef` for a ScheduledStopPoint) as a child, the
  element is renamed to it. No renaming to a kind the target is not; no moving across objects.
Do A3 only if the P0 replay shows at least 5 distinct fragments it would turn valid; otherwise record the count
and skip it.

- **Gate for A, offline (P0 harness)**: of the distinct stored structural failures, how many validate after A1+A2
  (+A3), by class. Stop and report if a repair turns a fragment valid by **changing what it says**: check 30
  repaired fragments by eye against the originals (same objects, same values, same references).
- **Gate for A, benchmark**: gen01–32 valid 96/96, first attempts not more than 5 below baseline, mean time within
  1 s; gen33–36 at 10 runs: mean attempts and mean time down against `up-10.json` (gen33 3.5 attempts, 28.8 s;
  gen34 3.0, 24.9 s), generated count not below, linked share not below B1's.
- **Believed, not measured**: A1+A2 remove the 25 frame-level and most of the 11 order diagnostics, about half
  of the structural ones, and gen33/gen34 lose about one attempt (6–8 s).

### B2. Feedback for what only the model can fix says what the object has

For the remaining structural classes (an element the object has no such child for; undeclared; a missing
required child), the diagnostics already name the parent's children in schema order. Two general improvements,
each only if the P0 corpus shows the class still above 10% of failed attempts after A:
- the feedback for a wrong child names, from the content model, **where that element does belong** among the
  objects the draft already has ("`parkings` is not a child of StopPlace; in this frame it belongs in the
  SiteFrame"), which A2's placement table gives;
- a required child that is a reference names the kind to define.
No per-element rules. If a rule would need the name of a NeTEx element in code, it does not belong here.

### C. Make the benchmark take prod's path

The benchmark calls `generate_netex_example(question, chunks, scope)` itself. Add `--via-api` (or reuse the
answer view's function) so a run goes through the same code as `/questions/answer`: the English rendering, scope
selection, the chunks the app passes. Then compare gen33 at 10 runs both ways. If they differ, the difference is
the next thing to explain, before any further generator change; if they agree, run gen33 five times on prod
(`req-diag-*`) after the next deploy and record linked/unlinked in §7.

## 4. What is not planned

- **A JSON description format.** See §1. Entry condition for trying it: after A and B2, structural failures the
  model must fix are still more than a third of failed attempts on gen33–36.
- **Rules that name NeTEx elements** in code (a Call needs…, a Line holds…). The schema and the examples are the
  only sources; that is the point of the plan.
- **Retiring existing checks** (two values as names of one object, the joined-name advice). They stay until a
  replay shows them unused for a release; removing them is a separate, measured step.
- **Raising `MAX_ATTEMPTS`.** A and B1 should lower attempts, not buy more.

## 5. Order of work

1. P0 (harness, benchmark's model-error handling), with this plan in the PR.
2. B1 (excerpt keeps required children).
3. A1, A2, then A3 if its gate passes.
4. C (benchmark through the app's path), then B2 if still needed.

## 6. Working conditions

- Dev stack: `NETEX_CHECKOUT=../NeTEx-upstream` in the root `.env`; before a benchmark check
  `docker exec napcorehelpdesk-backend-1 python -c "import lxml"` and that
  `git -C ../NeTEx-upstream rev-parse HEAD` is the commit prod's examples report (`schemaCommit`). The validator
  must be restarted after a change to `netex_validator_service.py` or `netex_content_model.py` (schema compile
  about 30 s).
- `/app/repo` is read-only in the container: write benchmark output to `/tmp` and `docker cp` it to
  `.mylocal/bench`.
- Tests without Docker: the database-free classes run with `NAPCORE_SKIP_GRAPHDB_IMPORT=1 GRAPHDB_ENABLED=False
  LLM_ENABLED=False` (CI's settings; a local `.env` with `LLM_ENABLED=True` hides a missing
  `@override_settings`).
- Risks: A2 moves objects, so a wrong placement table makes valid-looking but odd frames; the eye check of 30
  repairs and the "only what the content model flags" rule are the guards. A1 changes what the model sees as its
  own reply; if the model starts to copy placeholder frames or ids, the benchmark's first-attempt figure on
  gen01–32 shows it.

## 7. Results

(to be filled per step: date, files, figures against the baseline)

### P0 (2026-11-13, Opus): replay harness and outage handling

Files: `backend/helpdesk/management/commands/replay_example_repairs.py` (a command, not a script: it needs only
the validator and reads any benchmark output, prod event export or list of failed attempts; a directory stands for
its `*.json`/`*.jsonl`), `run_example_benchmark.py` (`is_outage`, `outages` in every summary).

**Outages.** A run is an outage when every attempt in its log is `model-error`; it is counted in `outages` and left
out of runs, valid, first attempt, mean attempts, mean seconds and the failure classes. On the baseline this rule
finds 6 runs, not the 7 of §2: gen32 run 2 had two `model-error` attempts and then a real attempt (`other`), so it
stays in. Either way the gen01–32 baseline is the same: **first attempt 71, mean 5.3 s** (90 runs by the rule,
89 without that run; valid all). **Measured** with `.mylocal/bench/cmp_plan13.py`.

Baseline (`up.json` + `up-10.json`, outages left out), the reference for every step below. **Measured.**

| | runs | first attempt | generated | linked | mean attempts | mean time |
|---|---|---|---|---|---|---|
| gen01–32 (3 runs) | 90 | 71 | 85 | 81 | 1.26 | 5.3 s |
| gen33 (10 runs) | 10 | 0 | 9 | 5 | 3.50 | 28.8 s |
| gen34 (10 runs) | 10 | 0 | 9 | 6 | 3.00 | 24.9 s |
| gen35 (10 runs) | 10 | 10 | 10 | 10 | 1.00 | 5.1 s |
| gen36 (10 runs) | 10 | 7 | 10 | 10 | 1.50 | 10.4 s |

gen33–36, 10 runs, failed attempts: wrong-parent 19, link 17, missing-required 12, order 6, undeclared 4, value 4,
other 2, keyref 1 (65, as in §2). gen33 linked over 13 runs (3 + 10): 7 of 12 generated, as in §2.

**Replay starting point (S2 as shipped, validator at 0.97.204).** Corpus: every `*.json` and `*.jsonl` in
`.mylocal/bench` (all benchmark outputs, `prod-examples*.jsonl`, `prod-failed-fragments.json`), distinct fragments
whose stored attempt failed on a structural class; none cut by the log's 4000-character limit. **Measured**
(`replay-p0.json`).

| Stored class | fragments | valid now | diagnostics stored → now |
|---|---|---|---|
| wrong-parent | 140 | 0 | 135 → 149 (wrong-parent 145, order 4) |
| order | 137 | 94 (all by the order repair) | 154 → 60 (order 47, keyref 8, wrong-parent 5) |
| missing-required | 44 | 0 | 45 → 46 |
| undeclared | 13 | 0 | 25 → 25 |
| keyref | 10 | 0 | 16 → 16 |
| not-expected | 4 | 0 | 4 → 4 |
| min-count | 2 | 0 | 2 → 2 |
| **total** | **350** | **94** | 381 → 302 |

"Stored" diagnostics are what the attempt log kept (older logs keep fewer kinds); "now" is the validator's answer
today, at most six per fragment. The order class is larger than S2's replay (137 vs 103) because the corpus now
holds the up/up-10 runs and r3.

### B1 (2026-11-13, Opus): the excerpt keeps required children. Arrival class gone, linked share not up: stopped here

Files: `netex_validator_service.py` (`/required?path=…`: the required slots, with their minimum, at the end of a
path from a global element), `netex_content_model.py` (`type_at`), `netex_example_generator.py`
(`required_slots`, `_holder_shape` keeps as many children as each required slot of every kept element needs and
returns `requiredRefs`; `link_problems` adds "A Call also needs a ScheduledStopPointRef: define a
ScheduledStopPoint for each Call and refer to it." when the fragment defines no such object;
`MAX_LINK_EXCERPT_LINES` 14 -> 20). The excerpt for StopPlace <-> Line now has the Call's
`ScheduledStopPointRef`, and a second Call (`calls` needs at least two): 17 lines. Checked against the checkout:
every element of that excerpt fits its content model (unit test, skipped without a NeTEx checkout). **Measured.**

Two benchmark rounds. The first (`b1.json` + `b1-10.json`) still had 5 `Arrival` failures: the link feedback
shows the ServiceJourney's shape once, for the first kind it links (the VehicleType), so the StopPlace's line had
no sentence. Fixed in a second commit (the sentence comes for every kind); the second round (`b1b.json` +
`b1b-10.json`) is the one below. The first round's gen35/gen36 lost 9 runs to API 503s (outages, left out).

| | baseline (up) | B1 |
|---|---|---|
| gen01–32 valid / first attempt / mean time | 90/90 / 71 / 5.3 s | 96/96 / 78 / 4.4 s |
| gen33 10 runs: generated / linked / attempts / time | 9 / 5 / 3.50 / 28.8 s | 9 / 5 / 3.40 / 32.0 s |
| gen33 13 runs: generated / linked | 12 / 7 | 11 / 6 |
| gen34 10 runs: generated / linked / attempts / time | 9 / 6 / 3.00 / 24.9 s | 7 / 6 / 1.90 / 22.9 s |
| gen35 10 runs: generated / time | 10 / 5.1 s | 10 / 4.9 s |
| gen36 10 runs: first attempt / time | 7 / 10.4 s | 7 / 8.9 s |
| gen33–36 10 runs, failed attempts | wrong-parent 19, link 17, missing-required 12, order 6, … | wrong-parent 18, order 14, link 13, value 8, asked-object 3, undeclared 1 |

(Mean attempts count a run that fell back to the standard's example as 0, as the benchmark always has: gen34's
1.90 holds 3 such runs.) **Measured.**

- The `Arrival` class is gone: `missing-required` in gen33–36 at 10 runs 12 -> 0 (first round 5, all on the
  second kind's line).
- **The linked share did not rise**: gen33 5 of 9 generated at 10 runs, as the baseline (first round 6 of 9;
  both rounds 11 of 18, 61%, against 56%: noise). gen33 is 3.2 s slower, gen34 generated 2 fewer (its 3 fallbacks
  failed on wrong-parent/value/asked-object before any link feedback, where B1 does not act).
- **Attempt logs, gen33 (second round).** What follows the link feedback: accepted 4, `order` 5, `link` 1; in the
  baseline accepted 3, `missing-required` 6, `order` 3. The model now writes the ScheduledStopPoints and the Call
  right, but the frame comes back with its lists out of order (`lines` after `scheduledStopPoints`) plus a
  keyref, which S2 does not repair because order is not the only problem; it is the last attempt, so the run
  ends unlinked. Before the link feedback, 2–3 attempts go to `wrong-parent`/`order` (stopPlaces in the
  ServiceFrame), so the link feedback comes at attempt 3 in 7 of 10 runs.
- Offline replay of the 16 distinct failed attempts that directly follow link feedback in both B1 rounds: with
  S2 (this PR) 0 validate; with A1 (prepared, not in this PR) 7 do, the 8 order+keyref ones but one (the keyref
  goes with the order). **Measured** with a local validator built from each branch's code.

Stopped here as §3 B1 asks ("if linked share does not rise, report the attempt logs before going on"). A1, A2 and
A3 are written and replayed offline (local branches `feat/example-order-always`, `feat/example-placement`,
`feat/example-reference-repair`, stacked on this one) but not benchmarked or opened as pull requests.

### A1–A3 (2026-11-13, Opus): the validator normalizes the draft. Gate met; linking solved on the benchmark

Benchmark of the whole stack (B1 + A1 + A2 + A3, branch `feat/example-reference-repair`), `a3.json` (gen01–36,
3 runs) and `a3-10.json` (gen33–36, 10 runs), dev on upstream NeTEx 5d2e569, no outages. Against the baseline
(`up`, outages left out) and B1 (`b1b`). Attempts here are attempt-log lengths (a fallback run counts its
attempts). **Measured.**

| | baseline (up) | B1 | A1–A3 |
|---|---|---|---|
| gen01–32 valid / first attempt / mean time | 90/90 / 71 (79%) / 5.3 s | 96/96 / 78 / 4.4 s | 96/96 / 82 (85%) / 4.5 s |
| gen33 generated / linked / attempts / time | 9 / 5 / 3.8 / 28.8 s | 9 / 5 / 3.7 / 32.0 s | 8 / **8** / 2.5 / 23.5 s |
| gen34 generated / linked / attempts / time | 9 / 6 / 3.3 / 24.9 s | 7 / 6 / 2.8 / 22.9 s | **10 / 10** / 2.2 / 17.9 s |
| gen35 generated / time | 10 / 5.1 s | 10 / 4.9 s | 10 / 5.0 s |
| gen36 generated / first attempt / time | 10 / 7 / 10.4 s | 10 / 7 / 8.9 s | 9 / 6 / 10.7 s |
| failed attempts gen33–36 | 65, structural 42 | 57 | 35, structural 11 |
| repairs gen33–36 | order 12 | order 15 | order 26, placement 6, placement+order 2, placement+references 1 |

- **Every generated gen33 and gen34 example is linked** (18 of 18; baseline 11 of 18), with about one attempt
  and 5–7 s less.
- **Structural failures 42 -> 11** on gen33–36 (wrong-parent 19 -> 5, missing-required 12 -> 2, order 6 -> 1).
  What remains is mostly what only the model can decide: `link` 15, `value` 6.
- gen01–32 better on every figure; gate (first attempts not more than 5 below, time within 1 s) met.
- **Gate clause "generated count not below" is one short on gen33 (8 vs 9) and gen36 (9 vs 10)**, read as met:
  the 3 fallbacks failed on classes the repairs do not touch (a value written as a name, `VehicleCategory` inside
  the wrong object with an enumeration value, a missing asked object); at 10 runs one example is within noise
  (B1's gen34 was 2 short for the same reason). gen34 gained one.
- A3's own share is small (1 repair in 40 runs), as its offline gate predicted (5 fragments); kept because it is
  exact (renames and versions only to match the target) and cheap.
- Offline (by the first agent run, `corpus-p0`): A1 102, A2 163, A3 168 of 350 stored structural failures valid;
  all 235 A2 repairs keep the same objects, values and references (script), 30 read by eye.
- The dropped-frames bug of `_frame_text` (7 of 94 S2 repairs) shipped separately in 0.97.205 (#487); A1 carries
  the same change.

Next per §5: C (benchmark through the app's path, then gen33 five times on prod after deploy), B2 only if needed.

### Prod check after A1–A3 (0.97.210, 2026-11-13)

Maribor–Ptuj (gen33) five times on prod (`req-diag-a3-*`): 4 generated, all 4 linked; 1 fell back to the
standard's example (undeclared, order, wrong-parent). Before (0.97.202–204): 3 generated, 0 linked. **Measured.**

### C (2026-11-13, Opus): the benchmark through the app's path agrees with the direct call

`run_example_benchmark --via-api` posts each question to the app's `/questions/answer` (the English rendering,
scope, retrieval settings and evidence order a user's question gets) and reads `generatedExample`. gen33–36 at 10
runs on main (A1–A3), `api-10.json`, against the direct run on the same code (`a3-10.json`). **Measured.**

| | direct | via the app |
|---|---|---|
| gen33 generated / linked / attempts / model time | 8 / 8 / 2.5 / 23.0 s | 10 / 10 / 2.8 / 24.8 s |
| gen34 generated / linked / attempts / model time | 10 / 10 / 2.2 / 17.7 s | 10 / 10 / 2.1 / 18.3 s |
| gen35 generated / first attempt | 10 / 10 | 10 / 10 |
| gen36 generated / first attempt | 9 / 6 | 10 / 8 |
| failed attempts | link 15, value 6, wrong-parent 5, … (35) | link 14, value 5, wrong-parent 4, undeclared 3, … (31) |

The two paths agree within noise, and every generated example is linked on both. The earlier dev/prod gap
(dev 7 of 12 linked, prod 0 of 3) came from the dev index (a branch checkout) and from the missing repairs, not
from the app's path; prod's 4 of 4 after the deploy fits. The direct call stays the default (faster, no answer
text); `--via-api` is for checks against prod behaviour. Through the app a run takes about 10 s more (the answer
text).

### B2 (2026-11-13, Opus): wrong-parent feedback says where the element belongs. Not shipped

After A1–A3, `wrong-parent` was 26% of failed attempts (gen01–36), above §3's 10% bar: mostly lists and objects
written inside the wrong object (`parkings` in a StopPlace, a `Route` where a `RouteRef` fits), which A2 does not
move. B2 (branch `feat/example-wrong-parent-feedback`, kept on GitHub, no PR) adds to the diagnostic the frame and
list the standard's examples keep the element in (`ContentModels.home`), the reference the parent takes instead,
or the elements of the draft that may hold it. On the 17 stored failures the messages read right.

Two 10-run benchmarks of B2 (`b2-10.json`, `b2r-10.json`) against two of main on the same code (`a3-10.json`,
`api-10.json`), gen33–36, 80 runs each, no outages. **Measured.**

| | main (A1–A3) | B2 |
|---|---|---|
| generated / linked | 77 / 77 | 78 / 76 |
| gen33 attempts / model time | 2.65 / 23.9 s | 3.00 / 25.7 s |
| `wrong-parent` failed attempts (attempt 1 / later) | 9 (3 / 6) | 19 (12 / 7) |
| repeated right after its own feedback | 3 of 7 | 3 of 18 |
| all failed attempts | 66 | 77 |

The gate (the class drops, nothing else worse) is not met. The share of repeats after the feedback falls, but the
count is the same (3 and 3); most of B2's extra `wrong-parent` attempts are first attempts, which B2 does not
touch (same prompt; validator logs clean, repair counts equal), so they are the model's spread, not B2. With
outputs level and gen33 slower, B2 is not shipped. What remains is mostly meaning: `link` and `value`, about two
thirds of failed attempts. A JSON description (§4) is not indicated either: structural failures the model must fix
are under a third.

### Count, not value (2026-11-13, Opus): "2 service journeys" is two objects

The prod-question pass (13 prod questions, 5 runs each, `prod-5.json`) showed **zero link failures** in 65 runs,
so link guidance in the first prompt was not built: before attempt 1 the generator knows only the asked object,
and the questions that fail do so before any link check. **Measured.**

What it did show: "Show me a NeTEx example for a line with 2 service journeys." failed the value check on the
first attempt in 5 of 5 runs ("the value 2 from the question is missing"), and the model met it with
`<Description>2</Description>` or `<PublicCode>2</PublicCode>` on the Line in all 4 generated answers. A digit was
a value (`_NUMBER` in `requested_values`), a number word never was (`counted_words`), and the count check
(`count_places`) read only one word after the number ("service" -> no element).

Files: `netex_example_generator.py` (`object_counts`, `_object_kinds`, `counted_out`, `object_count_places`,
`count_problems`, `counts_line`; error class `count`). A number in digits directly before a noun phrase of up to
three words that names an object element by its element name (the validator's `/concrete`, `object` true) is how
many of that object to write: it leaves the values, the prompt gets "Objects to write, each defined with its own
id: 2 ServiceJourney (“2 service journeys”)", and the check wants that many objects in one parent. Before a
property (Departure) or words that name no element, it stays a value. The documentation search of
`resolve_element` is not used: it finds an element for nearly any word ("seats" -> CarModelProfile, "metres" ->
AccessSpace). Number words are unchanged (still no check). Questions gen37–gen45 (prod log) added.

Values extracted, every question with a digit (gen01–45): unchanged except **gen25** "2 decks" (`['2']` -> count
2 Deck) and **gen40** "2 service journeys" (`['2']` -> count 2 ServiceJourney). gen14 "3 stop points" stays a
value (StopPoint is no element name), as on main. **Measured** in the dev container.

| | main | this change |
|---|---|---|
| gen40, first attempt / generated / stray "2" / two ServiceJourneys | 0 of 5 / 4 / 4 of 4 / 4 of 4 (`prod-5`) | 2 of 10 / 10 / 0 / 10 of 10 (`count-10`) |
| gen40 failed attempts | value 5, asked-object 2, … | asked-object 5, keyref 4 (no value, no count) |
| gen25 first attempt / generated / 2 Decks | 3 / 3 / 3 (`a3`, "2" held by a Label in 2 runs) | 3 / 3 / 3, placed as the count |
| gen01–36 (3 runs) first attempt / generated | 88 of 108 / 105 (`a3`) | 88 of 108 / 105 (`count-all`) |
| gen37–45 (3 runs) first attempt / generated | 23 of 45 / 42 of 45 (5 runs, `prod-5`) | 12 of 27 / 25 of 27 |

Only gen25 and gen40 take a different path: for every other question `object_counts` is empty and prompt and
checks are as on main, so their differences (gen06, gen32, gen36, gen37, gen38, gen44 one or two runs lower;
gen20, gen34 higher) are run-to-run spread. In gen40 the remaining first-attempt failures are a frame with the
two ServiceJourneys and a LineRef but no Line.

### Named part present (2026-11-14): "a line with a stop place departure" has its stop place

Prod question gen44 was accepted as a Line alone (0 of 8 answers had a StopPlace). A part the question names by an
object element's name is now listed in the first prompt and must be defined in the frame (error class `part`).
Only element names count: the documentation search resolves "a price" to CellPrice, which correct answers do not
contain (0 of 3), so properties and loose words are not checked. Of gen01–45 four questions have such a part.

| 10 runs each | generated | has the part | unlinked answers | attempts | model s |
|---|---|---|---|---|---|
| gen44 StopPlace (main, 8 runs) | 8 | 0 | 0 | 2.5 | 13.5 |
| gen44 StopPlace | 10 | 10 | 0 | 2.1 | 17.3 |
| gen18 Parking (main, 10 runs) | 10 | 10 | 4 | 3.6 | 17.5 |
| gen18 Parking | 10 | 10 | 6 | 3.8 | 18.0 |
| gen25 DeckPlan | 10 | 10 | 0 | 1.1 | 6.1 |
| gen35 Quay | 10 | 10 | 0 | 1.0 | 5.7 |

gen44 now links the StopPlace to the Line through a journey with calls; all ten first attempts failed on linking
and the feedback fixed them. gen18 is not changed by this step within 10 runs (4 and 6 of 10 unlinked; every first
attempt fails `wrong-parent` on both sides), but it is weak on main itself: a Parking left unlinked to its
StopPlace in 4 of 10 answers. Open.

### Asked object in another frame (2026-11-14): "a line with two departures on Monday at 14:00"

gen38 (a prod question) ended with a generated example in 1 of 10 runs on main (`r1-main-10`), 0 of 3 (`r1-main`)
and 4 of 10 today (`gen38-main-10`); otherwise the standard's example. **Measured.**

Cause: the question's values belong in objects of one kind of frame (two ServiceJourneys with DepartureTime 14:00:00
in a TimetableFrame) and the asked object in another (the Line in a ServiceFrame). The prompt asks for ONE frame,
so the model wrote the TimetableFrame with journeys that refer to `hd:Line_1`; the asked-object check rejected it
("the frame has none"), the model then wrote a ServiceFrame with the Line alone, the value check rejected that
(14:00 missing), and the three attempts ran out. Every rejected attempt in every stored gen38 run is one of these
two frames (or a first attempt with `<DepartureTime>14:00</DepartureTime>`, not an xs:time). An answer came only
when the model wrote a CompositeFrame with both frames on its own, or put the journeys in the ServiceFrame and the
validator's placement repair split them. Checked by hand on stored fragments: the TimetableFrame passes the value
and link checks and fails only `asked_object_problem`; the ServiceFrame fails only the value check; the accepted
CompositeFrame passes all. **Measured.**

Same shape elsewhere: every asked-object rejection in `r1-main`, `prod-5` and `count-all` (gen37, gen38, gen40,
gen44 and their prod copies, 28 attempts) is a TimetableFrame that refers to the asked Line by a LineRef. gen40 and
gen44 recovered on main more often because their retry wrote a CompositeFrame or a ServiceFrame that still held what
their checks want.

Change: only the feedback after an asked-object rejection (`missing_asked_object`). It names the reference that
already points at the asked object ("the frame has none, only a reference to one (hd:Line_1)") and, when one frame
was written, says to keep the objects that hold the values and, if the standard puts the asked object in another
kind of frame, to write a CompositeFrame whose frames hold both. The element and frame names come from the attempt;
no check changed and the first prompt is unchanged.

| | main | this change |
|---|---|---|
| gen38, 10 runs, generated | 1 (`r1-main-10`), 4 (`gen38-main-10`, same day) | 10 (`gen38-frames-10`) |
| gen38, retry after asked-object feedback is a CompositeFrame | 4 of 13 (rest: ServiceFrame alone) | 13 of 13 |
| gen01–45, 3 runs: generated / first attempt | 129 / 98 of 135 (`r1-main`) | 132 / 101 (`gen38-frames-all`) |

Per question only gen38 changed in generated (0 -> 3 of 3); no question generated fewer. First attempts differ by
one run in gen06 (3 -> 2), gen32 (1 -> 0), gen20, gen34, gen37, gen39 (higher): the first prompt is identical on
both sides, so these are run-to-run spread.

What the accepted gen38 answers hold (10 of 10): one Line (placeholder name "Line 1") in a ServiceFrame, two
ServiceJourneys with DepartureTime 14:00:00 that refer to it, in a TimetableFrame. Monday appears only as the id of
a DayTypeRef (`hd:DT_Monday`) to a DayType that is not in the frame; no DaysOfWeek. This was the same in the
answer main accepted: a weekday is not read as a value, so no check asks for it. Open, with two more seen here: a
first attempt that writes 14:00 as written in the question (not an xs:time) costs one attempt in 7 of 10 runs, and
"example of NeTEx in XML for a line …" (gen42) reads "NeTEx" as the subject, so no asked object is checked.

### F1 (2026-11-14): a time is given to the model in its xs:time form. Shipped

Plan `2026-11-14-example-open-faults.md`, F1. A time the question writes without seconds ("14:00") was written as
it stands, and the schema rejects it as an xs:time. `values_line` now gives it with its form, "14:00 (an xs:time is
written with seconds: 14:00:00)", as it already did for a duration. The value check is unchanged and takes both
forms. Measured x10 the same day on both sides (`faults-f1-before-10`, `faults-f1-10`):

| x10 | xs:time rejections (first error of an attempt) | attempts with an `hh:mm` element | first attempt | generated |
|---|---|---|---|---|
| gen32 | 10 -> 0 | 10 -> 0 | 0 -> 10 | 10 -> 10 |
| gen38 | 7 -> 0 | 7 -> 0 | 0 -> 0 | 10 -> 10 |
| gen42 | 2 -> 0 | 2 -> 0 | 5 -> 8 | 10 -> 10 |
| gen06, gen16, gen24, gen30, gen39 | 0 -> 0 | 0 -> 0 | 10 each, unchanged | 10 each |
| gen43 | 0 -> 0 | 0 -> 0 | 0 -> 0 (`min-count`, not a time) | 10 -> 10 |

The accepted answers hold the time in the same element on both sides (DepartureTime, ArrivalTime, Time,
LastDepartureTime), 10 of 10 per question. gen38's first attempt still fails in 10 of 10: that is the asked object in
another frame (§5 of the new plan), not the time. Gate met.

### F3 (2026-11-14): the name of a standard is not the subject. Shipped

"Show me an example of NeTEx in XML for a line …" (gen42, a prod question) had "NeTEx" as its subject, so no asked
object, no skeleton and no asked-object check. `asked_subject` now reads on when the subject is only the name of a
standard (with "XML" at most): the subject is what the next "of" or "for" introduces. The names come from the app's
own list (`question_parsing.is_standard_name`, from the scope patterns), not from a list in the generator.

`asked_subject` and `asked_element` for gen01–45 and the 13 prod questions (`prod-questions.yaml`), before and
after: two differ, gen42 and its prod copy (prod07), both "NeTEx" -> "line" / Line. Over the 665 distinct questions
in the prod and dev logs, three differ: the same one, and "Show me a fragment of NeTEx XMl for a line from
Slovenia." and "… NeTEx XMl for line." ("" -> "line"; "NeTEx XMl" ended as a proper name before). "A NeTEx example
of …" is not touched (the subject pattern starts after "example").

| gen42, x10 | asked object | first attempt | generated | accepted answers with a Line |
|---|---|---|---|---|
| before (`faults-f1-10`) | none | 8 | 10 | 0 (a TimetableFrame with journeys only) |
| after (`faults-f3-10`) | Line, 10 of 10 | 0 | 10 | 10 (CompositeFrame: Line in a ServiceFrame, journeys with a LineRef to it) |

The first attempt now fails the asked-object check in 10 of 10, as gen38's does: the same two-frame fault, expected
by the plan and not a failure of the step. Gate met.

### F2 (2026-11-14): a day of the week as a value. Not shipped (reverted)

Reading: the seven English day names as a closed vocabulary ("on Mondays" -> Monday, the schema's spelling), outside
quotes and not inside a proper name ("Black Friday Express"). A single "Monday" was no value before because it is a
concept label (TN-ITS code list), so `named_values` left it out. Over the 665 distinct questions of the prod and dev
logs, five name a day, all in English, all "Monday"; so English is enough today. The values are read from the
question as written, not from the app's English rendering (checked in `_generate`: `requested_values(question)`).
Values before and after for gen01–45 and the prod questions: only gen38, gen39, gen42 and their prod copies gain
"Monday"; nothing else changes.

Checking: the schema writes the days as a list (DaysOfWeek "Monday Tuesday", type `DaysOfWeekListOfEnumerations`, an
`xsd:list` of `DayOfWeekEnumeration`). The validator's content model read every list as free text. It now keeps a
list's item type, and `/accepting` also answers `inLists`: the elements whose content is a list of an enumerated
item type that has the value as one item ("Monday" -> DaysOfWeek, RequiresNightsAway). A day then counted only in
such an element, as its content or one item of it; an id, a reference, a Name or a Description did not count. No
element was named in code.

Measured x10 on both sides the same day, the after side against a validator run from the branch (port 8092; the
dev container runs main's validator):

| x10 | generated | day in DaysOfWeek in the accepted answers | first attempt |
|---|---|---|---|
| gen38, before (`faults-f1-10`) / after (`faults-f2-10`) | 10 / 9 | 0 / 9 | 0 / 0 |
| gen39 | 10 / 9 | 0 / 9 | 10 / 4 |
| gen42, before (`faults-f3-10`) / after | 10 / 8 | 5 / 8 | 0 / 0 |

Every accepted answer after the step holds Monday in DaysOfWeek of a DayType's PropertyOfDay, and the DayType is
linked (no unlinked answers); none passed by writing the day into a name or description. But generated fell from 30
to 26, so the gate ("generated not below the state before") is not met. The four lost runs ran out of attempts on
the day's object: a DayType written inside a journey's `dayTypes` (the schema wants a DayTypeRef there; 3 of 4),
then a retry that left the day out (3 of 4), a PropertyOfDay given a version and an id (2 of 4), and for gen38 and
gen42 the asked-object attempt (two frames) on top. gen39
also lost first attempts (10 -> 4): before, it passed with Monday only as the id of a DayTypeRef. Reverted
(commit "revert: a day of the week as a value (F2), gate not met"); the change stays in the branch history.

Open: the day's object needs its shape before the first attempt (where DaysOfWeek sits: a DayType, its properties,
a PropertyOfDay without an id), the same way the skeleton gives the asked object's. Whether to take the 26 correct
answers at the cost of 4 standard examples is a decision for later.

### F4 (2026-11-14): the parking that stays unlinked. Diagnosis, then shipped

1. How the standard links the two. In the schema both directions validate (checked against the validator): a Parking
   is a Site and has `ParentSiteRef` (the parking names the place it belongs to), and a StopPlace has `adjacentSites`
   that may hold a ParkingRef. Neither a `parkings` list nor a bare ParkingRef is allowed inside a StopPlace, and a
   Parking has no StopPlaceRef. In the standard's examples (every file with both objects) a Parking is linked to a
   StopPlace once, by `ParentSiteRef` (`examples/standards/epiap/Chur_Equipment_Pathlink_V1.0.xml`); elsewhere it is
   reached only through path links (PlaceRef in From/To) or not at all. The skeleton's companion comes from
   `StopPlace-with-equipment-and-parking_example.xml`, where the parkings are not linked to the stop place. **Measured.**
2. `link_example("Parking", "StopPlace")` returned None: it looked only for references named after the two kinds
   (ParkingRef, StopPlaceRef), and no example has one between these two. So the feedback was the bare "Link it to the
   StopPlace by a reference, directly or through another object in the frame": it said neither which object carries
   the reference nor which element. The model then wrote a ParkingRef or a `parkings` list inside the StopPlace, or a
   StopPlaceRef inside the Parking (`wrong-parent`), and the attempts ran out. Over all stored runs, a `link` attempt
   followed by `wrong-parent` is gen18 in 45 of 66 cases (ParkingRef 33, StopPlaceRef 8, parkings 4). The plan's
   belief was half right: not a wrong direction in the feedback, but no direction at all, because the examples'
   reference has a general name. **Measured.**
3. Other pairs with the bare feedback in the stored runs: WheelchairVehicleEquipment to VehicleType (7 attempts,
   gen15), FareDayType to Line (4), TopographicPlace to Line (1). These are not the same shape: in the examples
   those objects sit in their frames' lists and no reference of any name links them to the asked kind, so the
   change below does not find a link for them either. **Measured.**

Change: when no reference named after the kinds is found, `link_example` searches the same files again and counts
any `...Ref` element whose `ref` is the id of an object of either kind in that file, under its own name (an object's
reference to itself does not count). The name-based search runs first and is unchanged, so every pair it already
resolved resolves as before (checked for 21 pairs: only Parking/StopPlace changed, None -> "Parking >
ParentSiteRef"). The feedback is the existing one for that case: "Give the Parking a reference to the StopPlace, as
the standard's examples do: Parking > ParentSiteRef". Nothing names an element.

| x10, same day | generated | first attempt | unlinked answers | mean attempts |
|---|---|---|---|---|
| gen18 before (`faults-f4-before-10`) / after (`faults-f4-10`) | 10 / 10 | 0 / 0 | 7 / 0 | 3.8 / 2.9 |
| gen33 | 8 / 9 | 1 / 1 | 0 / 0 | 2.7 / 2.5 |
| gen34 | 9 / 10 | 2 / 2 | 0 / 0 | 2.2 / 1.9 |
| gen35 | 10 / 10 | 10 / 10 | 0 / 0 | 1.0 / 1.0 |
| gen36 | 10 / 10 | 5 / 7 | 0 / 0 | 1.6 / 1.3 |

All 10 gen18 answers after the change hold the Parking with TotalCapacity 40 and a `ParentSiteRef` to the
StopPlace's id, in one SiteFrame: the way the standard's example links it. Every link feedback was followed in one
retry. The first attempt still fails in 10 of 10, on a `parkings` list inside the StopPlace (9) before any link
feedback: that comes from the skeleton's companion, whose file does not link the parking. Open. gen33–gen36 get no
other link feedback than before (their pairs resolve by name), so their differences are run-to-run spread.

### F1–F4 together (2026-11-14): all 45 questions x3 on the final state (F1, F3, F4; F2 reverted)

| gen01–45, 3 runs | main (`gen38-frames-all`) | F3 state (`faults-f3-all`) | final (`faults-final-all`) |
|---|---|---|---|
| generated | 132 | 132 | 132 |
| first attempt | 101 | 101 | 98 |
| answers with an unlinked object | 3 (gen18 x3) | 3 (gen15, gen18, gen37) | 0 |
| asked object present | 117 | 120 | 120 |
| xs:time rejections | 4 | 0 | 0 |

No question generated fewer than on main. First attempts against main: gen32 0 -> 3 (F1), gen42 3 -> 0 (F3: it now
has an asked object and the two-frame fault of gen38), gen06 and gen14 +1, gen20, gen34, gen36 -1, gen37 -2. The
last six have no time and no standard name in the question and their first prompt is the same on all three sides,
so these are run-to-run spread (gen34 and gen36 x10 above: 2 and 2, 5 and 7). gen18 now takes 3 attempts in each
run, not 4, and links its parking in all three.

### Slovenian timetable request (2026-11-14): "from Slovenia", the empty frame, the empty answer

On prod (0.97.217) "Prikaži primer voznega reda v NeTEx XML iz Slovenije?" gave twice an empty TimetableFrame named
"Slovenije" and no answer text or citations; the English wording gave text, but wrote "Slovenia" into the frame's
Description. Three faults, each looked at on its own. Both wordings are now gen46 and gen47 in the benchmark, and
the direct benchmark reads a non-English question through the app's English rendering (as `_generate` does), so
gen46 is triggered as in the app. Outputs are in `.mylocal/bench/sl-*`.

**A. The place the example comes from was a value. Fixed.**

1. Why it was a value. `named_values` takes every capitalised run that does not start a sentence, so "Slovenia" in
   the English rendering and "Slovenije" in the question as typed were values. The Slovenian question has no English
   example word, so `_generate` triggers it on the English rendering (there "Slovenia" was the only value, so it
   asked for generation), and then reads the values from the question as typed ("Slovenije"). The model wrote the
   value into a Name or Description to pass the value check. **Measured** (calling the functions by hand; on dev, x10
   on main: the place in a Name or Description in 20 of 20 runs of both wordings, `sl-before-10`).
2. What tells it apart from "a bus line from Maribor to Ptuj". Where "from" attaches: after an example word or after
   the format or the name of a standard ("Any NeTEx example from Slovenia?", "… in NeTEx XML from Slovenia") it says
   where the example comes from; after an object's noun ("a bus line from Maribor") it says where the object goes.
   That is a rule about word order, with no place or element named; the names of the standards come from
   `question_parsing.is_standard_name`, as in F3.
3. What it does not cover. "a fragment of NeTEx XMl for a line from Slovenia" (p15) has the same shape as "a line
   from Maribor": nothing general tells them apart, so "Slovenia" stays a value there (the gold reading marks it
   unsure). And the rule reads English "from": a non-English question that is triggered by other values and also
   names where it comes from ("… iz Slovenije" next to a time) would still give the place as a value, because the
   values are read from the question as typed. I did not build a mapping between the two wordings for this.

Value table before and after (`requested_values` for the 45 benchmark questions, the 13 of `prod-questions.yaml` and
the 78 gold readings): no difference. The English wording is in none of them; p14 is read on the question as typed
and keeps "Slovenije" (in the app the English rendering decides, see 1). Over the 665 distinct questions of the prod
and dev logs one changes: "Any NeTEx example from Slovenia?" ['Slovenia'] -> []. No real name value is lost
(Maribor, Ptuj, Ljubljana, Koper, Piran, LPP, Ljubljana Bus Station all stay). **Measured.**

| x10 | main (`sl-before-10`) | A (`sl-a-10`) |
|---|---|---|
| gen46 (Slovenian): the place in a name or description | 10 | 0 |
| gen47 (English): the place in a name or description | 10 | 0 |
| gen46 / gen47 answer | generated, 2 of the gen46 ones an empty frame | the standard's own example, `Netex_09.2_Bus_SimpleTimetable_Slovenia.xml`, 10 + 10 |
| gen39 generated / first attempt | 10 / 10 | 10 / 10 |

Gate met. Generated falls from 30 to 10 because both wordings now have nothing to generate: no values, so the
standard's example is shown, and it is the Slovenian file (its name has both "timetable" and "slovenia"). But with A
alone that example was an empty TimetableFrame excerpt (Name, VehicleModes, "…"): fault B on the standard's route.

**B. An empty frame was accepted, and shown. Fixed.**

1. Why nothing required content. "timetable" resolves to TimetableFrame (`candidate_element_names`), and the
   validator's `/concrete` answers `object: false` for it, as for every frame (CompositeFrame too), so
   `asked_element` gives "" and no asked-object check runs. With "Slovenije" as the only requirement, a TimetableFrame
   with only `<Name>Slovenije</Name>` passed every check: 2 of 10 gen46 runs on main. **Measured.**
2. What the standard's examples do. Of the 128 TimetableFrames in the NeTEx examples, 110 fill `vehicleJourneys`,
   and 3 hold no object at all. Over 3,451 accepted answers in all stored benchmark runs, none was a frame without an
   object, so a check for one can only fire on this kind of question. **Measured** (scan of the example files and of
   `.mylocal/bench/*.json`).
3. The same fault on the standard's route. An excerpt keeps an object's simple children and drops every branch the
   question does not ask for; for a frame that is all its content. "Show me a timetable example in NeTEx." (a prod
   question) was shown a TimetableFrame with only a "…" inside; after A the Slovenian file's frame was shown the
   same way. **Measured.**

Change, no element named: (a) a generated fragment must hold at least one object, an element the validator's
`/concrete` calls an object (`holds_object`; it passes when the validator cannot tell); else the attempt is retried
with "the frame holds no object …" (error class `empty-frame`). (b) When the standard's example of a container (not
an object for `/concrete`) is cut to an excerpt, it keeps the first object of the list the standard's examples
most often fill in that container (`usual_list`, counted over up to 40 example files that use it, cached), cut to
its simple children and without its references: the objects they point to are left out and the schema's keyrefs
fail (the Slovenian file's journey with its ServicePatternRef failed validation, and the next file was shown).

| x10 | A only (`sl-a-10`) | A+B (`sl-b-10`) | B without A (`sl-b-only-10`, against `sl-before-10`) |
|---|---|---|---|
| gen46 empty frame accepted | 10 (standard, empty excerpt) | 0 | 0 (before: 2) |
| gen47 empty frame accepted | 10 (standard, empty excerpt) | 0 | 0 (before: 0) |
| gen39 empty / generated / first attempt | 0 / 10 / 10 | 0 / 10 / 10 | not run |
| generated, all three or both | 10 | 10 | 20 (before: 20) |

With A and B, both wordings show `Netex_09.2_Bus_SimpleTimetable_Slovenia.xml`: its TimetableFrame (Name "Winter
timetable for route 66 outbound", VehicleModes bus) with its first ServiceJourney (DepartureTime 14:20), validated, in
20 of 20. Without A the generator check fired twice (both on an attempt that was only a named TimetableFrame) and the
retry gave a frame with a journey both times. gen39's accepted answers are unchanged: a TimetableFrame with two
ServiceJourneys at 14:00 and a DayTypeRef. Gate met.

Not done: making "timetable" mean the container's usual content as the asked object (ServiceJourney), which would
also give a skeleton and the link checks. It changes more than the fault needs; measured nowhere yet.

**C. No answer text and no citations for the Slovenian wording. One cause fixed; the cause seen on prod is a
diagnosis only.**

Where the text goes. When an example is shown and the answer failed the answer validator on both attempts
(`answer_validated` false), the answer view drops the text and the citations (`views.py`, "With a block from the
schema … text that failed validation is noise"). Confidence 0.80 on prod is the cap for an unvalidated answer.
The prod response's trace confirms it: `llmAnswerValidated` false, both attempts rejected. The English rendering and
retrieval were right (the Slovenian example's description block was cited). Dev runs the same model as prod
(`claude-haiku-5-5`, provider anthropic, host and container).

Two different validator false positives make a Slovenian answer fail, both because the checks compare the answer's
words with English evidence:

1. A cited sentence with only plain words. "Dokazi prikazujejo slovenski primer enostavnega avtobusnega voznega
   reda v NeTEx XML, ki je poravnan s profilom NeTEx EU [E3]." has no term the validator counts (NeTEx and XML are
   ubiquitous), is not read as a statement about the evidence (`_is_evidence_scope_statement` knows English words
   only), and `_plain_sentence_grounded` needs a run of the block's own words, which a Slovenian sentence about an
   English block never has. This is prod's cause, on both attempts: the two rejected texts from the prod trace,
   replayed offline against the Slovenian file's blocks, are rejected by main's validator and by the branch's.
   **Measured.** On dev it is also the most common rejection of Slovenian answers: 6 of the 11 rejections left in
   the capture below, over four Slovenian questions.
2. An inflected name. "… iz Slovenije …, primer za Slovenijo [E1]" is checked for "Slovenije" and "Slovenijo"; the
   English block has "Slovenia", so the sentence "does not ground the claim". **Measured**: on the branch with A and
   B (where the Slovenian file is now the cited example), 2 of 11 runs of the Slovenian wording came back empty,
   one rejected for this on both attempts, the other first for this and then for 1.

Main on dev did not show the empty answer: 0 of 6 through the API and 0 of 5 with prod's empty frame put in by hand
(`sl-c-main-api-*`, `sl-c-replay-prodexample-5`). So on prod it depends on which sentences the model writes;
believed, as the two prod tries are the only sample.

Change for 2 (general, no word or language named): in an answer whose question is not in English, a capitalised
word without inner capitals (a name, not an identifier) is found in the cited block by its first letters, all but
the last three and at least six ("Slovenijo" by "sloven"). Identifiers and English answers are compared as before.
Offline replay of 39 validator calls captured over 30 questions (8 of the two wordings, 12 Slovenian and German,
10 English; `sl-c-capture`, `sl-c-replay`): rejections 13 -> 11; the two that pass are both case 2 and both were
the sentences that emptied a run; no other verdict changes. English answers cannot change (the function returns the
old comparison when the language is English).

| Slovenian wording, whole answer path on the branch | text and citations | first attempt rejected |
|---|---|---|
| A+B, before this change (`sl-c-branch-path-5`, `sl-c-capture`) | 9 of 11 | 3 of 11 (2 case 2, 1 an English answer) |
| A+B+C (`sl-c-after-10`) | 10 of 10 | 1 of 10 (case 1; the retry passed) |

Gate (5 of 5) met on dev, but it does not cover prod's cause: case 1 is untouched and can still empty the answer
when both attempts write such a sentence. I did not build a fix for it: grounding a Slovenian plain sentence in an
English block needs a translation (a model call) or a loose word-stem heuristic that would also let filler through.
Options for later: check plain sentences of a non-English answer against an English rendering of that sentence; or,
when an example is shown, keep text that failed validation and mark it unvalidated instead of dropping it (a change
of the rule in the view, not of the validator).

**Why the standard's Slovenian example was not shown before.** The app shows an example from the standard's files
on three routes: (1) a request with counts or parts and no other value ("a stop place with two quays",
`standard_example` through `_from_standard`); (2) a request with no values, counts or parts at all: the elements the
question names or the nearest concepts (`concept_elements`), the file whose name has most of the question's words
first, the first excerpt that validates (`_plain_standard_example`); (3) after generation fails, an object of the
asked element (`standard_fallback`). Any value that is not a count rules out routes 1 and 2. With "Slovenia" as a
value, the request went to generation, so `Netex_09.2_Bus_SimpleTimetable_Slovenia.xml` was never looked at. Once
the place is no value (A), route 2 ranks that file first (its name has "timetable" and "slovenia") and shows it in
20 of 20 runs (with B, with a journey). **Measured.**

**All questions x3 on the final state** (`sl-final-all`, against `faults-final-all`, the same generator code as
main):

| gen01–45, 3 runs | main (`faults-final-all`) | final (`sl-final-all`) |
|---|---|---|
| generated | 132 | 132 |
| first attempt | 98 | 100 |
| asked object present | 120 | 120 |
| answers with an unlinked object | 0 | 0 |
| accepted answers without an object | 0 | 0 |

No question generated fewer. First attempts: gen20, gen34, gen45 +1, gen36 -1. None of the 45 questions reads a
different value (the value table is the same), and the empty-frame check fired in none of the 135 runs, so their
prompts and checks are those of main: run-to-run spread. gen46 and gen47 show the Slovenian file's TimetableFrame with
a ServiceJourney, validated, in 3 of 3 each, with no "Slovenia" written anywhere.

### Unvalidated text next to an example (2026-11-14): kept and marked, not dropped

Decision: when an example (or an element's structure) is shown and the answer text fails the answer validator on
both attempts, I keep the text and mark it, instead of leaving the example alone. This answers case 1 of C above
(a plain Slovenian sentence can never be grounded in an English block) without touching the validator and without a
new model call.

**What the old rule did and why.** Since #305 (2026-11-08) the view emptied such a text and its
citations and kept it only in `trace.llmDroppedAnswer`: "text that fails validation is left out instead of being
shown marked for review next to a valid example". At that time the text often narrated a different file than the
one shown (DeckPlans and other alphabetical neighbours, fixed by P7 in 0.97.151) and attributed meanings to elements
that no evidence defines. The drop was a blunt guard: it did not detect either fault, it only hid the texts the
validator happened to reject.

**What I found in the dev log** (all question events since 2026-11-08, **measured**): 415 answers with a valid
example, 14 of them unvalidated, all 14 dropped. 12 of the 14 are English; their reasons are mostly "attributes a
purpose to an element no evidence defines" and "does not ground the claim". Two narrate other files than the shown
one (both before P7). 9 of the 14 hold a code block, and all 9 blocks are lines of the evidence or of the shown
example (checked against the stored retrieval chunks; the prompt's chunks are not stored, so this is close, not
exact). So the change is not about Slovenian only: it brings back English text that the validator found ungrounded,
now with a marker.

**The new rule** (both endpoints, one function, `_keeps_unvalidated_text` in `views.py`). The text stays, with
`trace.llmAnswerValidated` false (already in the API, confidence capped at 0.80 as before), unless:

- it holds a code block that is neither in the evidence nor in the shown example (a second, unchecked fragment next
  to the checked one: a marker on the text does not make a copied XML block safe), or
- its citations are refused by the policy (keeping it would turn the whole answer into an abstention and hide the
  example).

Then it is dropped as before (`trace.llmDroppedAnswer`). The code-block check is the one the generator already used
for verbatim example questions (`has_ungrounded_code_block`), now without the question-shape gate. Answers without
an example are unchanged: there the rule never applied, unvalidated text was already served (marked only in the
trace).

**For a reader**: under the example, above the text, a note: "Not confirmed against the sources: the automatic check
could not match this text to the cited evidence." It shows only next to an example or a structure and only when
`trace.llmAnswerValidated` is false. The UI has no translation mechanism (every label is English; only the answer
follows the question's language), so the note is English like the rest of the page.

**Measured on dev** (host backend from the branch on port 8011, the dev database, model `claude-haiku-5-5`):

| question | path | runs | text and citations | rejected twice -> kept and marked | validated, no note |
|---|---|---|---|---|---|
| Slovenian wording (gen46) | answer | 10 | 10 of 10 | 1 | 9 |
| Slovenian wording (gen46) | stream | 3 | 3 of 3 | 2 | 1 |
| English wording (gen47) | answer | 5 | 5 of 5 | 0 | 5 |
| gen01, gen02, gen06, gen19, gen39 | answer | 1 each | 5 of 5 | 0 | 5 |

The three kept Slovenian texts are accurate about the shown file (Name, VehicleModes, validity Sept to April). All
three were rejected for "does not ground the claim" on a sentence about `DepartureTime`, which is in the shown
example but not in the cited block: a third false-positive class, next to the two in C. One of them also says in
Slovenian that the block does not show `DepartureTime`; the lack-sentence filter reads English only (**observed**, not
changed). Rejected twice on dev is 3 of 13 Slovenian runs here against 0 of 6 on main in C, which is spread on a
small sample (**believed**).

**Forced case**: a view test feeds the prod Slovenian sentence to both endpoints twice with the model mocked; the
real validator rejects both attempts ("Citation [E1] without specific technical content", as on prod) and the
answer keeps the text, its citation and `llmAnswerValidated` false. Further tests: the text with an invented XML
block is dropped, text citing an unapproved source is dropped (no abstention), validated text carries no mark; each
condition was removed once to see its test fail.

Not done: the copy-answer and export texts do not carry the note; the editor's stored-answer view (`AnswerDetail`)
has no trace and shows no note.
