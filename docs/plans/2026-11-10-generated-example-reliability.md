# Plan: reliable generated NeTEx examples (validity, right object, fewer attempts)

Written 2026-11-10 (Fable) against 0.97.155, for the implementing agent/engineer. Every number was measured on the dev
stack (Docker, semantic index, Claude Haiku 5.5 through the Anthropic SDK, netex-validator at NeTEx 2.0 commit
98365bd) unless marked **prod**. Each claim is labelled **measured** (re-derived here, scripts in §7), **believed**
(strong basis, not independently checked) or **assumed**.

## 1. The problem, measured

**Prod** (req-mw9vh973-zgtk0t, 0.97.155, "Create a NeTEx XML example for a fare product for adult for 5 EUR."):
generatedExample valid=False after 3 attempts, 28.2 s of generation, 6 model calls, 7,786 output tokens, 39.9 s in
all; final errors were the value check ("5"/"EUR" not the whole content of an element). The user saw "No NeTEx
example valid against the schema could be generated" and a text saying the evidence has no complete example.

**Dev, the benchmark as it stands** (`run_example_benchmark`, 20 questions, one run, **measured**):
18/20 valid, 13 on the first attempt, median model time 4.7 s, maximum 26.0 s; failures gen16 (timetabled passing
time, 3 attempts, "ArrivalTime not expected") and gen19 (malformed XML on attempt 3, see §2.4). The two runs of
2026-11-08 were also 18/20 with different failures (gen15/gen16; gen12/gen16): the set is mostly single-object,
single-value questions and hides the failing class.

**Dev, structure-heavy questions, 3 runs each, app retrieval** (`multirun.py`, **measured**):

| Question | Valid | Attempts | Seconds | Asked object in the valid XML |
|---|---|---|---|---|
| fare product for adult for 5 EUR | 3/3 | 3, 3, 2 | 20.8, 19.0, 9.4 | 1/3 (`PreassignedFareProduct`; the other two are a `PriceGroup` / `FareTable` holding 5 EUR, no fare product) |
| timetabled passing time arriving at 08:30 | 0/3 | 3, 3, 3 | 20.6, 16.7, 25.2 | – |
| coach with 49 seats and 1 wheelchair area | 2/3 | 3, 3, 2 | 21.2, 16.8, 12.9 | 2/2 (`VehicleType`) |
| route named "Route 1 outbound" | 3/3 | 2, 2, 1 | 10.4, 7.5, 3.0 | 3/3 |
| journey pattern with 3 stop points | 3/3 | 1, 1, 1 | 6.9, 4.6, 5.2 | 3/3 |

15 runs: 11 valid, 2.2 attempts and 13.3 s per run on average; a run that passes on the first attempt takes 3–7 s.
The fare question passed 3/3 here and 2/5 the night before (same code): run-to-run variance is large, so every
comparison below uses at least 3 runs per question.

"Valid" overstates success: for the fare question two of the three valid fragments are not fare products. The
lead text then tells the user "5 → Amount in FareFrame › priceGroups › PriceGroup › members › UsageParameterPrice",
which is XSD-valid and not what was asked.

## 2. Where the failures come from (33 model calls, 22 failed attempts, **measured**; sub-classes hand-read)

| Class | Failed attempts | Example (verbatim validator error) |
|---|---|---|
| Element not expected here, of which: | 17 | |
| – an **abstract element** used as if concrete | 4 | `Element 'FarePrice': This element is not expected. Expected is one of ( FarePriceRef, FareProductPriceRef, …)` — `FarePrice` is abstract; the concrete members are `UsageParameterPrice`, `FareProductPrice`, … |
| – a **mandatory sibling missing** before the written one | 4 | `Element 'ArrivalTime': This element is not expected. Expected is one of ( validityConditions, …, DatedVehicleJourneyRef ).` — the list is cut at 10 by libxml2; the required `PointInJourneyPatternRef` (no `minOccurs="0"` in `PassingTimeGroup`) is not in it |
| – **wrong parent/level** | 4 | `SeatingCapacity` directly under `VehicleType` (belongs in `capacities › PassengerCapacity`), 3×; `SalesOfferPackagePrice` in a `PriceGroup` |
| – **sibling order** | 4 | `lines` before `routes` in a ServiceFrame, 2×; `equipments` before `capacities` in a VehicleType, 2× |
| – **undeclared element** | 1 | `PassengerCapacities` (not in the XSD; `WheelchairPlaces` also appeared) |
| Keyref: a `…Ref` to an object not in the document | 2 | `No match found for key-sequence ['hd:spijp_1', 'any'] of keyref 'StopPointInJourneyPattern_KeyRef'` |
| Missing child element(s) with a minimum count | 2 | `pointsInSequence: Missing child element(s)` — the fragment had one point; the XSD says `<xsd:choice minOccurs="2">`, the message does not |
| Malformed XML | 1 | The reply put a sentence before the JSON; `json.loads` failed and the regex fallback took the XML with its `\"` escapes (§2.4) |
| Value check after XSD validity | 0 here; prod's final state; 1 run in the skeleton experiment | |

Four causes carry these classes:

**2.1 No structural evidence for the asked object (measured).** For the fare question the six evidence chunks hold
`PreassignedFareProduct` in one chunk and `Amount`/`Currency` in two, but `prices`/`FareProductPrice` in none; the
model copied the only price pattern it saw (`PriceGroup › members › …Price`) and used the abstract `FarePrice`. For
the coach question 0 of 5 chunks hold `VehicleType` (deck plans and a Eurostar timetable were retrieved). For the
passing time, `TimetabledPassingTime` occurs in one chunk but without `passingTimes`/`ArrivalTime`. The semantic
retrieval finds the right *files* (fares, timetables) but not the chunk with the object's skeleton; the generator
sees 6 × 1,800 characters.

**2.2 The feedback is lxml's text, which is not actionable in four of the classes (measured on the error log).**
Abstract elements are reported as "not expected" with no hint that they are abstract (the model used `FarePrice`
again on the next attempt in 1 of 3 runs, and in all 3 runs of the thinking-off experiment); the expected-list is
cut at 10 entries, so the mandatory `PointInJourneyPatternRef` never appears (one run repeated the identical
`ArrivalTime` error 3 times); "Missing child element(s)" does not say "at least 2"; the keyref message does not say
that a reference without a `version` attribute is not checked (§2.3). The schema declarations added after the first
failure (`schema_declarations`) search by the question's words ≥ 4 letters, so for "fare product … 5 EUR" they
return `fareZones`, `FareClasses`, `fareContracts`, … and nothing about prices (`EUR` is 3 letters, `5` a number).

**2.3 The "define every referenced object" rule makes small examples large (measured).** `_PROMPT` says every
`…Ref` must point to an object defined in the same frame. For a passing time that means a CompositeFrame with a
ServiceFrame (two ScheduledStopPoints, a JourneyPattern with ≥ 2 points) and a TimetableFrame: a hand-written one
validates (`fg.py`), none of 9 model attempts got there. The XSD keyrefs use the fields `@ref` and `@version`; a
reference **without a `version` attribute has no key-sequence and is not checked**: `<StopPointInJourneyPatternRef
ref="hd:SPIJP_1"/>` inside a lone TimetableFrame validates, `version="any"` on the same reference fails (`kr.py`).
The XSD documents a reference as "may include a version" (`netex_relationship_support.xsd` line 85). **Believed**:
a version-less reference to an object outside the frame is legitimate NeTEx for an example; some profiles (Nordic)
require versions on references, so the frontend note should say the referenced objects are outside the fragment.

**2.4 The reply is parsed as JSON only when it is pure JSON (measured).** `_extract_fragment` tries `json.loads`
on the whole reply, then a regex for the first XML block. When the model prefixes a sentence ("The frame drops the
… {"xml": "<TimetableFrame version=\"any\" …"), the regex takes the JSON-escaped XML and the validator says
`AttValue: " or ' expected`. 1 of 33 attempts with thinking on; 5 of 26 with thinking off; gen19 lost its third
attempt to it in the benchmark; the earlier bench runs show it too (gen16 on 2026-11-08).

**Not a cause: thinking or effort.** Generator calls run at effort `low`, adaptive thinking (default of
`_request_chat_completion`). 90 % of the 44,581 output tokens over 33 attempts are thinking (visible JSON ≈ 4,550
tokens); a call takes 4.4 ms per output token, median 5.9 s (2.6–11.5 s), so three attempts are 17–25 s. Thinking
off (same 3 hard questions, 3 runs each): 1/9 valid against 5/9, 5.2 s against 18.1 s per run, 323 against 1,463
tokens per attempt, 5 malformed replies against 1. **Keep thinking on for the generator**; the time comes from the
number of attempts, which the items below reduce.

**Subject resolution today (measured, `subjprobe.py`, `fg.py`).** `example_subject` finds no subject in 11 of 24
example questions (its regex needs "with/having/for/in" right after the noun; "named", "called", "departing",
"arriving", sentence end are not accepted). `resolve_element` maps "fare product" to `RestrictedServiceFacilitySet`,
"coach" to `Deck`, "tram vehicle type" to `Parking`; `concept_elements` maps the fare question to `FareClasses`,
"bus with 50 seats" to `TaxiStand`. A regex with the extra terminators plus `candidate_element_names` plus "the
element occurs in the standard's example files" resolves 21 of 24 by name (`fg.py`); the misses are "fare product"
(`FareProduct` is abstract), "coach"/"bus" (not elements) and a proper name. The XSD substitution groups resolve the
abstract case: `FareProduct` → head `FareProduct_Dummy` → concrete members by example-file count
`PreassignedFareProduct` 73, `SaleDiscountRight` 19, `AmountOfPriceUnitProduct` 16 (`n2n3.py`).

## 3. Experiments that inform the items (measured, 3 hard questions × 3 runs each, same retrieval)

| Variant | Valid | Attempts (mean) | Seconds per run (mean) | Asked object present (valid runs) |
|---|---|---|---|---|
| Baseline (as shipped) | 5/9 | 2.78 | 18.1 | fare 1/3, coach 2/2 |
| **Skeleton of the asked object up front** (`skelrun.py`, element given by hand: PreassignedFareProduct, TimetabledPassingTime, VehicleType) | 5/9 | 2.33 | 14.7 | fare 2/2, coach 3/3 |
| Thinking off | 1/9 | 2.89 | 5.2 | – |

Per question, skeleton vs baseline: coach 3/3 vs 2/3 valid, attempts 2, 1, 2 vs 3, 3, 2, 9.6/5.5/9.3 s vs
21.2/16.8/12.9 s; fare 2/3 vs 3/3 valid (noise-level), both valid fragments are `PreassignedFareProduct`s (but the
price sits in a sibling `PriceGroup` in one), and the model still wrote the abstract `FarePrice` in 2 of 3 first
attempts because the skeleton file (`Netex_61.2_…AdultChildProduct.xml`) has no `prices`; passing time 0/3 vs 0/3:
my skeleton note said references may "be left out", the model dropped the mandatory `StopPointInJourneyPatternRef`,
and where it kept it, the keyref failed (§2.3). Conclusion: the skeleton fixes shape and wrong-object errors
(coach, fare), not abstract elements, mandatory siblings or references; those need the feedback items. Skeleton
lookup costs 59–214 ms (`skeleton.py`).

Two skeleton design facts from the experiment: a "distinct path" skeleton that collapses repeated siblings to one
breaks `minOccurs="2"` content (the JourneyPattern skeleton failed validation for that reason: keep two of a
repeated sibling); shells of ancestors must drop `…Ref` attributes (as `standard_example` already does).

## 4. Constraints

General solutions only: nothing keyed to fare products, passing times or any question; every rule below is driven
by the XSD, the standard's example files or the model's own fragment. Keep semantic retrieval. XSD validation stays
the gate: nothing unvalidated is ever labelled valid. A standard example shown instead of a generated one must say
it does not hold the asked values. No Claude/AI attribution in commits or PRs. Stop at the PR unless told "full cycle".

## 5. Work items, in order

### P0 — Make the benchmark see the failing class (small, first)

- Add structure-heavy questions to `backend/helpdesk/benchmarks/example-generation-questions.yaml` (gen21–gen26):
  the fare product for adult for 5 EUR; a sales offer package with a price of 10 EUR; a tariff with two fare zones;
  a dated service journey on 2026-12-01; a vehicle type with a deck plan of 2 decks; a stop place with a lift and
  two quays. (Only the first is the reported case; the rest are different object types of the same shape class:
  object + nested child holding the value.)
- `run_example_benchmark --runs N` (default 1), per-attempt rows in the JSON output: error class (as in §2, derived
  from the message prefix), `completion_tokens`, ms, whether the reply parsed as JSON, and `askedObjectPresent`
  (P2's resolver; empty when unresolved). Summary: valid rate, first-attempt rate, asked-object rate, mean attempts,
  mean seconds, failures by class.
- Tests: the class derivation on the verbatim messages of §2.
- This is the measurement every later item reports against.

### P1 — Structured, actionable validator feedback (option b; addresses 12 of the 22 failed attempts)

`backend/helpdesk/netex_validator_service.py` returns, next to today's `errors` strings, `diagnostics`: one per
error with `{"line", "element", "parent", "kind", "detail"}`, built from the XSD index (`ElementDocs`) and the
submitted document (the offending node is found by `sourceline`). Kinds and the text the generator renders:

1. **abstract** — the element is declared `abstract="true"` (227 in the XSD; record the flag in `ElementDocs.add_schema`,
   plus `substitutionGroup` heads → members): "`FarePrice` is abstract and cannot appear in a document; concrete
   elements in its place: UsageParameterPrice, FareProductPrice, SalesOfferPackagePrice, … (those used in the
   standard's examples first)". Check the whole fragment for abstract elements, not only the reported line.
2. **not-expected** — give the complete ordered child list of the parent as the schema has it, not libxml2's 10:
   "`TimetabledPassingTime` children in schema order: …, JourneyRef?, AlightAndReboard?, **PointInJourneyPatternRef
   (required; concrete: StopPointInJourneyPatternRef, TimingPointInJourneyPatternRef)**, ArrivalTime?, …; `ArrivalTime`
   is allowed only after the required ones". Order comes from the XSD: record `links` as ordered lists and walk the
   base type before the extension (XSD extension puts base content first); mark `minOccurs` ≥ 1 as required and
   expand substitution-group heads. **Test the order on data**: for every object in the standard's example files
   (parse `examples/**/*.xml`, 40 files is enough), the children's order must be a subsequence of the computed list;
   report the pass rate in the PR and fix the walker until it is ~100 % (choice groups may permute; accept any order
   inside one `xsd:choice`). When the offending element is not a child of the parent at all, say so and name its
   declared parents (the `parents` already computed for `/declarations`).
3. **min-count** — "`pointsInSequence` needs at least 2 of (PointInJourneyPattern, StopPointInJourneyPattern,
   TimingPointInJourneyPattern); the fragment has 1". Read `minOccurs` of the choice/sequence.
4. **keyref** — "`StopPointInJourneyPatternRef` points to `hd:spijp_1`, which is not defined in the fragment. Either
   define a `StopPointInJourneyPattern` with that id, or reference an object outside the fragment by leaving out the
   `version` attribute (`<StopPointInJourneyPatternRef ref="hd:spijp_1"/>`)". (§2.3; the second clause depends on P3.)
5. **undeclared** — "`PassengerCapacities` is not an element of the NeTEx schema" (name not in `ElementDocs.element_type`).

In `netex_example_generator.py`: render `diagnostics` into the retry message (fall back to the strings when absent,
so an old validator still works); keep `schema_declarations` but **after** the diagnostics and only the declarations
whose names are not already covered. The declarations query searches by the question's words ≥ 4 letters, which
for "fare product … 5 EUR" yields nothing about prices (§2.2); add a second query by the *element names the model
used* (`Amount`, `Currency`, from the failed fragment) so their declared parents (`FareProductPrice`, …) reach the
model. Replace `_PROMPT`'s "Every reference element must point to an object
defined in the same frame" with: "Reference an object the question does not ask for with a `…Ref` that has `ref`
and **no** `version` attribute (it lies outside the fragment); define an object in the frame only when the question
asks for it or the schema requires it." Keep "no PublicationDelivery" and the id/version rules for defined objects.

Tests (unit, no model): the five diagnostics on the verbatim fragments of this diagnosis (fare attempt 1 with
`FarePrice`; passing time with `ArrivalTime` alone; journey pattern with one point; `version="any"` reference to an
undefined object; `PassengerCapacities`), the rendered retry message contains the concrete members / the required
sibling / "at least 2" / the version-less form; the order test over the example files (a management command or a
test marked slow). Frontend: the lead and the element notes need no change; the download document is unchanged.

Expected (**believed**, from the failure records): the 4 abstract, 4 mandatory-sibling, 2 min-count and 2 keyref
failures become fixable on the next attempt, and the passing-time class becomes a one-frame fragment. On the §1
table: passing time 0/3 → ≥ 2/3, fare attempts 3 → ~2, coach unchanged until P2. Measure with P0 (3 runs each).

### P2 — Skeleton of the asked object up front and the asked-object check (option a)

1. **Resolver** (`netex_example_generator.py`): `asked_element(question) -> str`: subject from a widened `_SUBJECT`
   (terminators `named|called|operated|departing|arriving|at|on|of`, sentence end, punctuation; the `_SUBJ2` regex in
   `fg.py`), tried as the whole phrase then its suffixes ("tram vehicle type" → "vehicle type"); each candidate from
   `candidate_element_names`, accepted when it (a) is an object (`object: true` from `/declarations`, or `is_object`
   exposed by `/structure`) and (b) occurs in the standard's example files (`has_tag`); when the name is an abstract
   element, take its substitution group's concrete members ordered by example-file count (new validator field
   `substitutes` on `/structure`, or a `/concrete?element=` route) and accept the first that passes (b). No concept
   matching here (it gave `FareClasses` and `TaxiStand`); fall back to `concept_elements` only when it returns an
   element that passes (a) and (b). Unresolved ("coach", "bus", a proper name) → no skeleton, no asked-object check.
   Resolution must be ≥ 21/24 on the benchmark questions (`fg.py` numbers), 0 wrong among the resolved; the test
   lists the 24 questions and their expected element or "".
2. **Skeleton** (`skeleton_for(element, question)`, the prototype is `skeleton_lib.py`): from the example files that
   use the element, best name-overlap first (as `standard_example` ranks them), take the first object of that
   element with its frame chain; keep the first **two** of repeated siblings (minOccurs ≥ 2), drop comments and
   foreign-namespace attributes, strip `…Ref` attributes from the ancestor shells, cap at 40 elements by cutting the
   deepest subtrees first; indent with `indented_fragment`. Prefer a skeleton that validates (try up to 3 files; a
   skeleton with dangling references does not, that is fine, it is a shape, not the answer). Cache per element for
   an hour (the files change at the 03:30 UTC refresh).
3. **Prompt**: a `SKELETON` block before the evidence: "an object of the kind the question asks for, from the
   standard's example file X (with its frame and list wrapper). Keep its nesting and element order; put the
   question's values in the elements that hold such values; drop optional elements the question does not need;
   **keep every element the schema requires** and the references, as version-less references when their target is
   not in the frame." Do not write "may be left out" (the experiment's wording lost the mandatory reference).
   Add the skeleton's file chunk (`shown_example_chunk`-style lookup by `source_path` + `has_tag`) to the evidence
   so the citations and the narration can name it.
4. **Asked-object check**, beside `_unmet_values`: when the element is resolved and the valid fragment has no such
   element, the attempt fails with "the question asks for a `PreassignedFareProduct`; the frame has none", and when
   the values are not inside that object's subtree, "the value 5 sits outside the `PreassignedFareProduct`"
   (`value_places` gives the path). Both are general and only run when the resolver is confident.
5. Tests: resolver table; skeleton of a known file keeps two points of a journey pattern and no `Ref` attributes
   on shells; the check fails a `PriceGroup` fragment for a fare-product question and passes a `PreassignedFareProduct`
   one; `generate_netex_example` with a stubbed model and validator shows the skeleton in the first message.

Expected: coach-type questions 2/3 → 3/3 with one fewer attempt (**measured** in §3); fare: asked object 1/3 →
3/3 (**measured** 2/2 of the valid runs, the third run's price-outside-product case is what item 4 catches);
first-attempt rate on the benchmark 13/20 → ≥ 16/20 (**assumed**). Cost: ~0.1–0.2 s per question, no model call.

### P3 — Robust reply parsing (tiny; 1 of 33 attempts with thinking, 5 of 26 without; lost gen19)

`_extract_fragment`: find the JSON object that holds `"xml"` anywhere in the reply (first `{` whose `json.loads`
succeeds, scanning `{` positions; or a `json.JSONDecoder().raw_decode` from each `{`), then the fenced-JSON case,
and only then the raw XML regex; when the regex path is taken, unescape `\"` and `\n` if the text has them.
Also add to `_PROMPT`: "The reply is the JSON object only, no text before or after it." Tests: the verbatim reply
of passing-time run 1 attempt 3 ("The frame drops the … {"xml": …") parses to a well-formed frame; a bare XML
reply still works. Expected: the "malformed" class disappears; one attempt saved whenever it would have happened.

### P4 — Thinking for the generator calls: keep adaptive (decision, no code)

Measured in §2 ("Not a cause"): thinking off is 3.5× faster per run and 1/9 valid instead of 5/9. Do not add a
setting for it. Revisit only after P1–P3 with the same 3-run protocol, since fewer attempts may change the trade.

### P5 — Clearly labelled fallback to the closest standard example (option c; residual failures)

When all attempts fail and P2's resolver found an element, return the (unpruned, up to `MAX_STANDARD_EXAMPLE_ELEMENTS`)
object from `_plain_standard_example(question, scope, [element])`, with `origin: "standard"`, `valid` as today for
standard examples, `validated` as the validator says, **`holdsValues: false`** and `missingValues: ["5", "EUR"]`,
plus `generationErrors` (the last attempt's diagnostics, for the trace). Frontend (`GeneratedExample.tsx`): title
"Example from the standard: file (does not contain the asked values 5, EUR)"; the lead lists the missing values
instead of value places; the badge stays "as published". The answer text's example rule (`generated_example_rule`,
`llm_generator.py` ~1444) gets an `origin="standard-without-values"` variant: "the example shown is the standard's;
say in one sentence which element would hold each value, from the evidence, and do not claim the example holds them".
Never let `valuePlaces` claim a place for a value the fragment does not hold (today `_from_standard` only reports
counts and parts, so this is already true; keep a test). Expected: the residual "no example" outcome (gen16 class
today; prod's fare case) becomes a labelled standard example; no change to validity numbers.

### P6 — Later, if P1–P2 leave first-attempt failures: structural evidence in retrieval

The evidence lacked the object's skeleton in all three hard cases (§2.1). With P2 the skeleton is in the prompt
regardless of retrieval, so this is optional: when the resolver finds an element, replace the lowest-ranked
evidence chunk with `examples_using_elements([element], limit=1, question=…)` so the model also sees a real,
longer instance. Measure with P0 before and after; drop it if P2 already gives ≥ 90 % first-attempt validity.

### Not planned

A second model call to choose the object (a cheap classifier call): the resolver is deterministic and 21/24; add
the call only if P2's unresolved cases (vehicle kinds such as "coach") matter in prod logs. Raising `MAX_ATTEMPTS`
(each attempt is ~6 s). Changing the model or effort. Relaxing XSD validation.

## 6. Expected result

Three hard questions (§3 protocol, 9 runs): valid 5/9 → ≥ 8/9, attempts 2.8 → ~1.5, seconds 18 → ~9 (**estimate**;
the time follows attempts at ~6 s each). Benchmark (20 + 6 questions, 3 runs): valid 18/20 → 20/20 and ≥ 5/6 on
the new ones, first attempt 13/20 → ≥ 16/20, asked-object rate ≥ 90 % where resolved, malformed 0. Prod fare case:
a valid `PreassignedFareProduct` with `prices › FareProductPrice › Amount 5 / Currency EUR` in ≤ 2 attempts, or,
failing that, a labelled standard example instead of "no example".

## 7. Verification protocol (every PR of this plan)

1. Unit tests of the changed modules (`test_netex_example_generator.py`, the validator service tests) and
   `python manage.py test` (known environment failures only).
2. `run_example_benchmark --runs 3 --output …` on the extended set (26 questions; ~80 runs, ~150 model calls,
   15–20 min): report valid, first-attempt, asked-object, attempts, seconds and the failure classes **per question**,
   against the baseline of this document (`gen-bench-2026-11-10.json` and `multirun.json` in the scratchpad). A PR
   must not lower any question's valid count over 3 runs by more than 1 without an explanation. For a cheap check
   during development, the three hard questions × 3 runs (`skel_questions.json`) are enough.
3. Retrieval and concept benchmarks are unaffected (no retrieval change) unless P6 is done; then
   `run_retrieval_benchmark --app-scope` as in the latency plan.
4. Read the fragments, not only the flags: for each valid fragment of the hard set, is the asked object there and
   do the values sit inside it? (P2 item 4 automates this where the resolver is confident.)
5. Prod after deploy: the fare question and gen16 through `/questions/answer` with `X-Request-Id: req-diag-…`,
   3 times each; read `generatedExample.attempts`, `valid`, `origin`, `holdsValues`, `timingsMs.exampleMs`.

## 8. Risks

- **P1 order walker**: the XSD content model has choices and nested groups; a wrong order in the feedback would
  mislead the model. The example-file subsequence test is the guard; ship the diagnostics without the order list if
  the pass rate is below ~98 %.
- **P2 resolver false positives**: a wrong element gives a wrong skeleton and a wrong asked-object check ("Bus"
  passes `has_tag` because some example has a `<Bus>` element; the object test must reject it). Measure with the
  24-question table; when in doubt, resolve to "".
- **P1 version-less references**: valid XSD and documented as optional (**measured**, **believed** legitimate), but a
  reader copying the fragment into a profile that requires versions will have to add them; the element notes should
  say "reference to an object outside this fragment".
- **Variance**: the fare question went 2/5 and 3/3 on consecutive nights with identical code. Never decide on one
  run; the protocol uses three.
- **Cost**: a 3-run benchmark on 26 questions is ~150 model calls per PR; the three-question set is the loop for
  development.

## 9. Reproduction (scratchpad `/private/tmp/claude-502/-Users-andrejt-Research-repositories-git-NapcoreHelpdesk/fb70c80b-ec77-4f7d-9db6-11974054bdd2/scratchpad/`)

Run a script with `docker cp X.py napcorehelpdesk-backend-1:/tmp/x.py` and
`docker exec napcorehelpdesk-backend-1 sh -c 'cd /app/backend && python manage.py shell -c "exec(open(\"/tmp/x.py\").read())"'`.

- `bench-2026-11-10.log`, `gen-bench-2026-11-10.json` — `run_example_benchmark` baseline.
- `multirun.py` + `mr_questions.json` → `multirun.json`, `multirun.log` — 5 questions × 3 runs with per-attempt
  fragments, validator errors, tokens, prompt sizes (patches `_ask_model`/`validate_fragment`).
- `skeleton.py` (demo over 7 elements) / `skeleton_lib.py` (library) — distinct-path skeleton prototype.
- `skelrun.py` + `skel_questions.json` → `skelrun.json` (mode `skeleton`), `nothink.json` (mode `nothink`).
- `vprobe.py` — validator messages for misordered/wrong-frame fragments and the declarations for the fare question.
- `evtags.py` — which structural elements the evidence chunks hold. `subjprobe.py`, `presprobe.py`, `fg.py` —
  subject/concept resolution; `fg.py` also validates the two-point passing-time CompositeFrame. `n2n3.py` —
  keyref tests, substitution groups from the XSD with example-file counts, content-model sizes. `abstr.py` —
  abstract/undeclared elements in the failed attempts. `kr.py` — version-less references pass the keyref check.
