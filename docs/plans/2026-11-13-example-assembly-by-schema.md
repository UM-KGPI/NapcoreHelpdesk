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
