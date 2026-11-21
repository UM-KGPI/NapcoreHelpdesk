# Record: refused questions that look answerable

Written 2026-11-14 against 0.97.219. Prod refused 52 of the 324 questions asked through the web page between
2026-10-18 and 2026-11-14 (16 %). Replayed on 0.97.219, 30 distinct questions were still refused. This record
gives the mechanism that refused each, which of them the indexed sources answer, the fixes for the general
causes and their measurements. Each claim is labelled **measured**, **believed** or **assumed**.

The questions are in `backend/helpdesk/benchmarks/refused-questions.yaml` (23 refused questions the sources
answer, 25 that must stay refused). One refused question is left out of the file: a review request with a pasted
SIRI document (§2.4).

## 1. Where a question is refused

There are four places in the answer views (`api/views.py`, both the JSON and the streamed endpoint):

| | Where | Decides on | Reason |
|---|---|---|---|
| R1 | `semantic_abstention_message`, before retrieval | the keyword rules: no ontology concept matched (`NO_CONCEPT`), or one matched with low confidence, and no standard named or recognised and no CamelCase term | `INSUFFICIENT_EVIDENCE`, 137-character message |
| R2 | after retrieval, when nothing is retrieved or the evidence gate refuses | chunk count, alignment (gate off on prod and dev) | `INSUFFICIENT_EVIDENCE` |
| R3 | `evaluate_policy` on the answer's citations | no citation, or a cited source outside the allow-list | `INSUFFICIENT_EVIDENCE` / `POLICY_BLOCK`, 72-character message |
| R4 | `_non_answer_outcome` | the answer model's own `evidence_answers_question: false` | `INSUFFICIENT_EVIDENCE`, the model's text kept |

Configuration (**measured** on dev with `settings`; prod as stated by the owner, **believed**): answer model and
controller on `claude-haiku-5-5` on both; `RELEVANCE_CHECK_ENABLED`, `VOCABULARY_BRIDGE_ENABLED`,
`EVIDENCE_GATE_ENABLED`, `POLICY_STRICT_CLAIM_GUARD` all off on dev. That prod has the relevance check off is
consistent with the log: every R1 refusal carries the keyword message, none the "This helpdesk answers questions
about …" message the check would give (**measured**, 26 of 26).

## 2. Diagnosis of the 30

Every one of the 30 was asked again on a dev backend serving `origin/main` (0.97.219) and was refused through
the same mechanism and with the same reason as on prod (**measured**, 30 of 30). The keyword decisions were also
reproduced by calling `_parse_question` and `semantic_abstention_message` by hand (17 of 17), the policy block by
running retrieval and `evaluate_policy` on each retrieved chunk (§2.3).

### 2.1 Cause A: keyword rules (R1) — 17 of the 30, 26 of the 52

All 17 have `coreConcept: unknown-concept`, an empty scope and no CamelCase term. The rule matches ontology label
words (literal, plurals only for multi-word labels) and GraphDB anchors of the question's words. Everyday wording
matches nothing: "lift", "elevator", "escalator", "station", "seat capacity", "ticket", "timetable", "delays",
"journeys" (plural of a one-word label), "metadata", "static data" all give no concept (**measured**,
`extract_graph_concepts` and `parse_question_to_semantic_query` on each word). Slovenian questions are translated
first ("What is the timetable?"), and the translation matches nothing either.

Evidence in the index (**measured** by querying `SourceChunk` on dev; prod's index is believed to have the same
NeTEx/SIRI/OpRa/legislation content):

| Question | Answerable? | Evidence |
|---|---|---|
| Which formats count as machine-readable? | yes | MMTIS Art. 2, 4, 5 (`02017R1926-20240304#art_2` …) |
| Make a example file of observed delays. | yes | OpRa `examples/DelayedAndCancelledJourneysWithEvents.xml`, `opra_lateDatedVehicleJourney_version.xsd` |
| How are parkings defined in standards? | yes | Transmodel PARKING, `netex_ifopt_parking_version.xsd`, DATEX II `Parking.*` |
| lift / escalator / elevator in a station (3) | yes | `netex_ifopt_equipmentAccess_version.xsd` (LiftEquipment, EscalatorEquipment), Transmodel LIFT_EQUIPMENT |
| What is seat capacity? | yes | `SeatingCapacity` in `netex_vehicleType_version.xsd`, `siri_journey.xsd` |
| Kaj so to metapodatki? | yes | mobilityDCAT-AP `src/index.html` |
| Kaj je vozni red (avtobusa)? (2) | yes | `netex_timetableFrame_version.xsd`, `examples/functions/timetable/*` |
| How to model number of late journeys? | yes | `opra_lateDatedVehicleJourney_version.xsd` |
| How to describe a bus ticket? | yes | `netex_typeOfTravelDocument_*.xsd`, fare products |
| How are static / dynamical data described? (2) | yes | MMTIS Art. 2 definitions of static and dynamic travel and traffic data |
| hi; what is narcose; ma che cosa e un sapore helpdesk? | no, rightly refused | — |

So 14 of the 17 are wrongly refused.

A general signal for "the question is about the sources" was looked for in two places:

- **Similarity to the concept index** (`ConceptVector`, the e5-small vectors `presence_concepts` uses): rejected.
  Top similarity of the 14 answerable questions 0.817–0.891, of 16 must-refuse questions 0.773–0.888 ("hi" 0.848,
  "How does it work?" 0.888) (**measured**). No threshold separates them, as with the retrieval scores earlier.
- **The relevance check** (`RELEVANCE_CHECK_ENABLED`, built 2026-10-19, never switched on in prod): the controller
  model answers RELEVANT or IRRELEVANT. On the 14 answerable it said RELEVANT in 10 of 14 (4 rounds each: 10
  stable, 2 at 3 of 4, 2 never), on 16 must-refuse IRRELEVANT 64 of 64 (**measured**). Two faults:
  - It was asked about every question naming no standard and no artifact, so it also refused questions the
    keyword rules let through. Over the 252 distinct log questions it newly refused 6, among them "Any timetable
    from Slovenia?" and "Any timetable from France?", which prod answered from NeTEx's examples, and "What if my
    dataset is available in several formats?" (**measured**).
  - Its prompt did not list the EU legislation, which has been indexed since #91. The two answerable questions it
    never accepted were about legislation terms ("machine-readable", "metadata").

### 2.2 Cause B: the answer model says the evidence does not answer (R4) — 11 of the 30, 23 of the 52

The model's text is kept; it says what the retrieved blocks contain and that they do not answer. Read against the
index (**measured** unless marked):

| Question | Verdict | Why |
|---|---|---|
| What is OpRa used for? | wrongly refused, retrieval | OpRa `README.md` overview is indexed; retrieval gave four schema fragments |
| Which fare data must be provided … MMTIS … | wrongly refused, retrieval | MMTIS Annex 1.1–1.3 (`#anx_1`) lists fare data; retrieval gave Articles 1, 6, 9 and recital 7 of 2024/490 |
| What if my dataset is available in several formats? | wrongly refused, retrieval | mobilityDCAT-AP distributions (`src/index.html`, `properties-for-distribution.html`); retrieval gave SIRI/NeTEx enumerations |
| How do I describe an elevator in a station in NeTEx? / … in a stop place? | wrongly refused, retrieval | LiftEquipment in `netex_ifopt_equipmentAccess_version.xsd`; retrieval gave passenger entrance and taxi stand |
| How to define a location of a parking bay in DATEX? | believed answerable in part | DATEX II v3.7 model is indexed (`datex-model-v3.7/Parking.*`); the location association was not found by text search, **believed** |
| In which legislation is DATEX. included? | wrongly refused, model verdict | the cited MMTIS Art. 4(2) and 5(2) name DATEX II; the model quoted them and still said "does not state that DATEX II is included" |
| How are DATEX and SIRI connected? | answerable in part, model verdict | cited SIRI SX examples embed DATEX II situation records; answered on some runs, refused on others |
| is croatian NAP good?; What does NeTEx say about the colour of bus seats?; Is it ok to round ExpectedArrivalTime …? | rightly refused | the sources do not say; the kept text says so |

DATEX II is indexed on prod as well (prod citations of `docs.datex2.eu/v3.7/*` and `datex-model-v3.7/*` on
2026-11-06 and 2026-11-09, **measured** from the log), so "DATEX II is not indexed" is out of date.

The verdict is not deterministic: "What is OpRa used for?" and "How are DATEX and SIRI connected?" were answered on
one dev run and refused on another, on the same code (**measured**).

### 2.3 Cause C: policy block on a generated ontology file (R3) — 1 of the 30, 1–3 of the 52

"when describing the calendar of a service journey, how to choose between UIC bit field and explicit Operational
Days?" retrieves a relation path (`docs/ontology/standards/netex.ttl#ServiceJourney`) whose `repositoryUrl` is this
project's `netex.ttl`. Relation paths without a schema-backed step cite their standard's ontology file
(`relation_paths.format_relation_paths_as_chunks`, since #96), but the allow-list in `policy_guard` knew only
`transmodel.ttl`; when the answer cites the path, the whole answer is blocked (**measured**: `evaluate_policy` on
that chunk returns `POLICY_BLOCK`, on the five XSD chunks none). Of the 252 distinct log questions, 2 retrieve such a
chunk (**measured**, without translation). The other two `POLICY_BLOCK`-shaped refusals in the log (2026-10-19,
2026-11-04) are answered on 0.97.219; their cause is not known.

### 2.4 Not a refusal mechanism: a review request

"Du you have any comments to this SIRI example: <pasted SIRI document>": the pasted XML dominates retrieval, which
returns other SIRI and TN-ITS examples, and the model says they do not describe the user's document. Reviewing a
user's document is a capability the helpdesk does not have; not counted as wrongly refused.

### 2.5 Summary

Of the 30: 23 wrongly refused (14 by cause A, 8 by cause B, 1 by cause C), 6 rightly refused, 1 review request.

## 3. Fixes

Rule for both: general mechanisms only; nothing names a question, a noun from one, or an element.

### F1 (cause C): the generated standard ontologies are approved citation sources

`ontology_evidence.GENERATED_ONTOLOGY_URLS` holds the four generated files (transmodel, netex, siri, opra);
`policy_guard` matches citations against it by exact URL, and `relation_paths` builds its URL from the same base.
The three standard ontologies are generated from the approved repositories by `build_standard_ontologies` and
never edited by hand, the same status as `transmodel.ttl`. Other files of this repository stay blocked (test).

### F2 (cause A): the relevance check as a second opinion on keyword refusals, prompt brought up to date

`semantic_abstention_message` runs the keyword rules first. Only when they refuse, and the check is enabled, the
controller model is asked: RELEVANT answers the question, IRRELEVANT refuses it with the message that says what the
helpdesk covers, a failed call keeps the keyword refusal. A question the keyword rules let through is never put
to the model, so the check cannot refuse anything prod answers today. The prompt now lists the EU legislation.

F2 does nothing on prod until `RELEVANCE_CHECK_ENABLED=True` is set in `.env.prod` (owner's decision, §6). The
default stays off: tests would otherwise reach the model wherever it is not mocked.

### Not fixed

- **Cause B, retrieval** (6 of the 30): each is a different ranking fault (an overview file under schema
  fragments, an annex under articles, a profile under schema enumerations, a synonym). The three questions
  F2 lets through but the answer model still refuses ("elevator in a station", "number of late journeys",
  "dynamical data") are the same fault. What would be needed: a way to rank definition and overview sources for
  "what is X for / what must be provided" questions, and a vocabulary step for synonyms. The vocabulary bridge
  (`VOCABULARY_BRIDGE_ENABLED`) is the existing candidate for the second; it is off on prod and was not measured
  here.
- **Cause B, the model's verdict** (2 of the 30): the prompt already says to set the flag false only when the
  evidence does not answer at all. Changing that is a prompt change to every answer and needs its own gate on
  the must-refuse set over several runs, because the verdict varies between runs.

## 4. Gates

Measured on the dev stack (index as of 2026-11-14), each question asked once through HTTP to two backends started
from the worktree: `origin/main` on port 8011 (relevance check off, as prod) and the branch on port 8012 with
`RELEVANCE_CHECK_ENABLED=True`. Rule-level decisions with `probe_abstention` and by hand.

- Must-refuse set (25 questions in `refused-questions.yaml`): 0 answered on the branch that were refused on main.
  14 of the 15 off-topic and vague ones get the "not relevant" message, and "How does it work?" (let through by the keyword rules on both) is refused by the model's verdict; 1 question is answered on both ("What does GTFS
  say about stop times?": grounded in NeTEx's GTFS mapping examples, so not a leak of model knowledge).
- Relevance check with the new prompt, 4 rounds: 16 must-refuse 64 of 64 IRRELEVANT; the 14 answerable 55 of 56 RELEVANT (one Slovenian
  question 3 of 4).
- Benchmark questions under `probe_abstention` (147): with the old full-mode check 2 more answered and 0 more
  refused; in the second-opinion mode no question the keyword rules answer can be refused (by construction, test
  `test_a_question_the_keyword_rules_answer_is_not_put_to_the_model`). Retrieval is unchanged by both fixes; the
  CI retrieval benchmark gate runs on the PR.

## 5. Results

| | main | branch |
|---|---|---|
| Cause-A questions answered (14 answerable) | 0 | 10 |
| Cause-B questions answered (8) | 2 | 1 (verdict varies between runs, unchanged code) |
| Cause-C question | POLICY_BLOCK | no block; refused by the model's verdict (R4) |
| Must-refuse answered (25) | 1 | 1 (same question) |

Reading of the 10 newly answered (all cite evidence, 3–4 blocks each; read against the cited blocks):

- Good: parkings (Transmodel and NeTEx definitions), lift in a station (LiftEquipment, LiftCallEquipment),
  escalator (EscalatorEquipment, EscalatorFreeAccess), seat capacity (SeatingCapacity in SIRI and NeTEx, example
  values), "kaj je vozni red?" (TimetableFrame, example in Slovenian).
- Partial: observed delays (points to the OpRa DelayedAndCancelled example, says it cannot write a whole file), "Kaj je
  vozni red avtobusa?" (describes the Slovenian and other timetable examples, no definition).
- Grounded but off the question's intent: machine-readable formats (answers NeTEx's travel-document
  `MachineReadable`, not the legislation), bus ticket (ticketing equipment, not fare products), static data
  (DataManagedObject, not the MMTIS definition). These say what the evidence does not cover. They are the
  retrieval fault of §3 (Not fixed), now visible instead of hidden behind a refusal.

No newly given answer was found to state anything its cited blocks do not support (**believed**: read by hand, not
checked by the validator separately).

## 6. Decisions for the owner

1. Set `RELEVANCE_CHECK_ENABLED=True` in `.env.prod` after merging (deployment guide §12.4 has the check). It adds
   one controller call to questions the keyword rules refuse, 26 of the 324 web questions in the log (8 %).
2. Accept the generated NeTEx, SIRI and OpRa ontology files as citation sources (F1), as `transmodel.ttl` is.
3. Whether to take on the retrieval faults of cause B (§3) as their own plan.

## 7. Questions sent with a scope (2026-11-15, against 0.97.221): gate not met, code reverted

**Verdict: the gate is not met, so the change is reverted on the branch** (commit kept in its history). The fix does
what it was meant to: the five vague must-refuse questions that a scope let through are refused under every
scope. It fails the gate on two counts: one must-refuse question was answered under a scope in 1 of 30 runs
(a question the screen never sees, answered on main at the same rate), and one answerable Slovenian question
was refused under its fitting scopes in all runs.

### 7.1 Diagnosis

Verified in the code and by calling `_parse_question` and `semantic_abstention_message` by hand (check enabled,
model mocked to IRRELEVANT): "Is this mandatory?", "Explain the data format.", "What are the rules?", "Can you
help me?", "What is the weather?" and "How do I describe a lift in a station?" are refused without a scope and
answered with NeTEx or EU legislation as scope, and the check is not called (**measured**). The cause is as
stated in the clarifying-choice record (§8): `has_scope_hint` is true for any non-empty scope, so neither keyword
rule fires, and the check is only asked after a keyword refusal.

It explains only part of the leaks C0 counted. Of the 25 must-refuse questions, 14 are refused by the keyword
rules without a scope (**measured**); the scope bypass concerns those. Five of them were answered under a scope
in C0 ("Can you help me?", "What should I do first?", "Explain the data format.", "What are the rules?", "Is this
mandatory?", 67 runs). The other questions C0 saw answered under a scope ("How does it work?", the two GTFS
comparisons, "is croatian NAP good?", "What is the formal W3C or OGC ontology for NeTEx concepts?") pass the
keyword rules without a scope too, because they name a standard or a CamelCase term or match a concept; the
screen never sees them with or without a scope, and their answers come from the answer model's verdict (R4)
varying between runs.

### 7.2 Design

- Check on: a scoped question is judged by the parse of the question as if asked without the scope (the same
  parse, English rendering included, an unscoped question gets). When the keyword rules would refuse that, the
  check is asked; IRRELEVANT refuses with the "This helpdesk answers questions about …" message, RELEVANT and a
  failed call answer within the scope. When the keyword rules let it through, nothing is asked.
- Check off: unchanged, a scoped question is never refused by the keyword rules. Refusing it would refuse
  "How do I describe a lift in a station?" with NeTEx, which is answered from LiftEquipment today; nothing
  general separates it from "Is this mandatory?" without the model.
- What the check is told: the question only, not the scope. Measured with the controller model as configured on
  dev, 3 calls each, on the questions the keyword rules refuse:

| Prompt | 14 must-refuse × 10 scopes: IRRELEVANT | 14 answerable × fitting scopes: RELEVANT |
|---|---|---|
| unchanged (scope not told) | 42 of 42 (the verdict does not depend on the scope) | 42 of 42 |
| told "The user asked the question within this source: X." | 403 of 420 ("Explain the data format." accepted under DATEX II, NeTEx, OpRa, SIRI, TN-ITS 3 of 3, NAPCORE 1; "Is this mandatory?" under TN-ITS 1) | 54 of 54 |
| the same plus "Naming a source does not make a vague question specific …" | 420 of 420 | 42 of 54 (rejects "Kaj so to metapodatki?", "How to model number of late journeys?", the static/dynamic data questions under the legislation) |

  The model does see a vague question as specific when a source is named next to it; telling it the scope
  lets "Explain the data format." through, and warning it against that rejects answerable questions. Not told.

### 7.3 Gate results (dev, branch on a host server with `RELEVANCE_CHECK_ENABLED=True`, 3 runs each)

| # | Criterion | Result | |
|---|---|---|---|
| 1 | Must-refuse, every scope: 0 answered that are refused without a scope | 1 question: "Is it ok to round ExpectedArrivalTime …" under EU legislation, 1 of 3 runs | not met |
| 2 | 23 wrongly refused, fitting scope: not fewer than C0's 43 of 69 beyond spread | 41 of 69 (C0 43, main the same day 45); "Kaj so to metapodatki?" refused at the screen in all 9 scoped runs | not met |
| 3 | Unscoped screen decisions unchanged | identical on all 235 questions (refused-questions, benchmark, probe set) for each model verdict | met |
| 4 | Check off: scoped behaviour as designed | tests: answered, no parse and no call | met |
| 5 | CI retrieval benchmark not below baseline; benchmark questions not newly refused | passed on the fix commit (baseline hit@10 0.483, MRR@10 0.266; graph-RAG 0.497, 0.281; gate passed against `ci-baseline.json`); the 149 benchmark entries have identical screen decisions (row 3) | met |
| 6 | Cost | below | stated |

**1. Must-refuse set** (825 requests, 25 questions × (10 scopes + none) × 3). The 14 questions the keyword rules
refuse were refused at the screen in all 420 scoped runs; C0 answered 67 runs of five of them. Answered under a
scope on the branch:

| Question | C0 (main) | Branch | Judged against |
|---|---|---|---|
| How does it work? | none 1, Transmodel 1, EU legislation 3, mobilityDCAT-AP 2, NAPCORE 1, DATEX II 2 | none 1, NeTEx 2, SIRI 1, EU legislation 3, mobilityDCAT-AP 3, DATEX II 3 | unscoped (answered 1 of 3 without a scope) |
| What does GTFS say about stop times? | none 3 | none 3, NeTEx 1 | unscoped (answered 3 of 3) |
| What does NeTEx say about the colour of bus seats? | none 1 | NeTEx 1 | unscoped (names NeTEx: the NeTEx scope is its unscoped search) |
| Is it ok to round ExpectedArrivalTime and ExpectedDepartureTime …? | — | EU legislation 1 | refused without a scope: fails criterion 1 |
| Two GTFS comparisons, croatian NAP, W3C ontology | NeTEx 1, OpRa 1, Transmodel 1, Transmodel 2 | — | variance (none of these is seen by the screen) |

The rounding question names two CamelCase elements, so the keyword rules let it through with and without a
scope; the change does not touch its path. Asked 24 more times with the EU legislation scope: main answered 2 of
24, the branch 2 of 24 (**measured**). Its answer says the evidence has no rounding rule, then describes the TEL
TSI forecast message: a grounded non-answer from the answer model, as C0 read for the others.

**2. The 23 wrongly refused questions.** With the first fitting scope: C0 43, main the same day 45, branch 41 of
69. Spread: C0 and main the same day differ by 2; the per-pair binomial spread of the total is about 1.2 runs. The
branch's deficit against the same-day main is 4: "Kaj so to metapodatki?" refused at the screen in 3 of 3 runs
under mobilityDCAT-AP (and under EU legislation and NAPCORE), 1 run of variance. With the controller's first
option: C0 37, main the same day 39, branch 35, the same question. Reading: the check judges "Kaj so to
metapodatki?" RELEVANT in 13 of 20 calls, its English rendering "What is metadata?" in 0 of 20 (**measured**).
`_ask` is cached per process, so one IRRELEVANT verdict refuses the question until the backend restarts
(**believed**: all 9 scoped runs refused after the first calls, consistent with the cache; not traced). Without a
scope the same verdict refuses it today with the check on; with a scope it newly refuses an answer main gives
from mobilityDCAT-AP. The other answers that changed: "Kaj je vozni red avtobusa?" with NeTEx went from 2 to 3 of
3, as on main the same day.

**3. Unscoped behaviour.** `_parse_question` and `semantic_abstention_message` called as the answer view calls
them, on main and the branch, for the 48 refused questions, the 149 benchmark entries and the 38 probe questions,
with the model mocked to RELEVANT, IRRELEVANT and failing: same decisions and same questions put to the model,
byte-identical output (**measured**).

**6. Cost**, with the check on: every scoped question gets a second parse without the scope (0.37 s mean, 1.8 s
max on dev, no model call); a scoped question the keyword rules would refuse also gets one controller call (1.1 s
mean, 3.8 s max, cached per question). The chat page sends no scope, so today only API clients pay it. With
the check off: nothing.

### 7.4 What would be needed

- The rounding question: an under-scope leak of the answer model's verdict (R4), present on main. No screen
  reaches it; it belongs with the "the model's verdict" fault of §3.
- "Kaj so to metapodatki?" + mobilityDCAT-AP: the check sees "what is metadata" as too vague, which it is
  without the scope. The two prompt variants measured either let vague questions through under a scope or reject
  this one.
- The relevance check's cache keeps a wrong verdict for the life of the process; the same holds without a scope.

## 8. Scope check from the index, no kept verdict, every source searched (2026-11-21): gate not met, code reverted

Short questions the sources answer were refused by the scope check before retrieval. A diagnosis the same day
(own measuring set: 66 questions that reach the check, 32 answerable, 34 that must stay refused) found three causes:
the check's list of what is covered does not name the general data subjects the sources hold (metadata, licences,
data quality and validation, mandatory data), its vagueness rule refuses short questions, and a question that names no
standard is never searched in the opt-in sources, where 13 of the 32 have their answer. I built the remedy as one step
and measured it against a gate fixed before the run. **It fails three lines. The code is reverted on the branch; this
record stays.**

### 8.1 Diagnosis (by hand, main at 0.97.248)

- The coverage text lives only in `relevance_check._PROMPT`. The refusal the check gives
  (`semantic_abstention.NOT_RELEVANT_MESSAGE`) names the same sources in short. `measure_scope_options` keeps its own
  one-line descriptions (a measuring command, not the app's path).
- A question that names no standard gets an empty effective scope (`select_effective_scope`). Retrieval with an empty
  scope leaves out every chunk of an opt-in source that is not also a core standard (`_scope_query_filter`, again in
  `_scope_matches`). The logic that gives each opt-in source its own share of candidates runs only when the scope
  holds more than one source.
- `_ask` was `lru_cache(512)`: one verdict per process per question text, failures not kept. Nothing else uses it; tests
  and the capture scripts clear it.
- What the index holds (dev index, read only): files and chunks per source, the acts in the EU legislation source
  (MMTIS 2017/1926 consolidated and 2024/490, ITS Directive consolidated and 2023/2661, TEL TSI 2026/253, INSPIRE
  Directive 2007/2/EC and Regulation 1089/2010), the NAPCORE files, the schema file topics of NeTEx, SIRI and OpRa, the
  terms the acts define, the headings of the document sources. Found on the way: the RTTI, SRTI and truck parking
  regulations are not in the EU legislation source; NAPCORE's site holds copies of them (2015/962, 2022/670,
  886/2013, 885/2013).

### 8.2 Design (as measured)

1. The coverage list rewritten from that inventory, per source: what kind of files and which subjects. The rule:
   "irrelevant" only for another subject (general knowledge, travel information itself, other software, other
   standards) or no subject at all (greets, thanks, asks for help without saying with what). The refusal text was left
   as it is (same sources named; a test ties the two).
2. No cached verdict. On Claude the call runs without thinking (Haiku takes no temperature; "disabled" only up to
   effort high, so above that thinking stays on). The other gateways already ask at temperature 0.
3. A question the check let through is searched in every source (core and opt-in), so each opt-in source gets its own
   share. The answer keeps the question's own scope. Every other question is searched as before.
4. `FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS` default 3 → 4 (deploy moves an old 3 to 4).

The prompt was frozen at commit 5f25ec0 (15:04) before the held-out set was opened; it was not changed after.

### 8.3 Gate

Held-out set: 30 short "in" and 25 "out" questions written by someone who had not seen the prompt or the code. All 30
"in" questions have an answering passage in the dev index (found and read by hand). The check was called directly, 3
runs each, on the 66 and the 55. Full answers ran in process on the dev stack, once each, inside rolled-back
transactions. Main for the full answers is 0.97.248; the yardstick compares the branch rebased on 0.97.249 with
0.97.249.

| | Must hold | Result | |
|---|---|---|---|
| Answerable wrongly refused, the 32 | at most 1 in any run | 0, 0, 0 (today 6) | met |
| Held-out answerable (30 with a passage) wrongly refused | at most 10 % in any run | 0 %, 0 %, 0 % | met |
| Must-refuse let through, the 34 | none, except "Is my data good?" | 3 in every run: "Is my data good?", "Explain the data format.", "What are the rules?" (3 of 3 each) | **not met** |
| Held-out out-of-scope let through | none | "explain this" 3 of 3; nothing in the index answers it (no subject) | **not met** |
| Unstable verdicts (66 + 55) | at most 1 | 0 of 121 (today 3 of 66) | met |
| Full answers: the 13 opt-in answerable cite their source | at least 9 | 8 of 13 | **not met** |
| Full answers to questions let through: statements not from a retrieved passage | none | none found in the 9 answers read one by one; 21 not read that way | not decided |
| The 25 must-stay-refused benchmark questions answered | not more than main | branch 3, main 3 | met by count |
| App-path retrieval yardstick (149) | identical to main question by question | 132 of 149 on both, 124 in base mode on both; 6 questions differ in the order of their top 6 (graph mode), and main differs from itself on 6 of the same questions in a second run | not met to the letter; within main's own variance |
| Time | check not slower than today's median by more than 0.3 s | median 0.800 s vs 0.775 s | met |
| CI | green, Retrieval Benchmark present and green on the code commit | green on the rebased code commit | met |

Details:

- **Let through.** "Explain the data format." and "What are the rules?" now have a subject for the check (a data
  format, rules), so the narrowed rule lets them pass. Today's prompt refused both 3 of 3, and so did the diagnosis' variant (a) 2 of 2:
  my wording of the "relevant" rule ("another subject of transport data ... that such documents describe") is wider
  than its wording. In the full answers
  "Explain the data format." was refused by the answer model; "What are the rules?" was answered from NAPCORE, DATEX II
  and the RTTI text (quality "rules", the list of delegated regulations, the DATEX II rules of procedure, traffic
  regulations). Every statement I read is in its evidence blocks, but it answers a question nobody asked. "explain
  this" and "Is my data good?" were refused by the answer model.
- **Cite their source** counts an answer whose evidence (the cited blocks) holds a passage of the source that has the
  answering passage. The five that miss: "Kaj so to metapodatki?" and "What is metadata?" were answered from NAPCORE's
  metadata page and mobilityDCAT-AP (the definition in MMTIS Art. 2 did not come up; by reading, the answer is right);
  "How are static data described?" had MMTIS Art. 2(4) in block 6 but cited only NAPCORE and DATEX II and said the
  evidence has no definition; "How are dynamical data described?" got no act; "Speed limit updates?" got no TN-ITS
  passage and was refused by the answer model. The 17 held-out "in" questions whose answer is only in opt-in sources:
  8 of 17 by the same count; three of them (dataset metadata, open licence, who is responsible for quality) do not
  reach the check, so they are searched as today.
- **Must-stay-refused.** Branch: "How does it work?", "What does GTFS say about stop times?" (both as on main) and
  "What are the rules?" (new, from the widened search). Main: the same two and "What is the DATEX II equivalent of an
  OpRa capacity indicator?", which the branch refused: that question names standards, so its path did not change
  (variance).
- **Yardstick.** `run_retrieval_benchmark --app-conditions --app-scope`, ontology loaded, no model calls, 337 GraphDB
  calls and 0 failures per run; branch (rebased) and 0.97.249 twice, 15:23–15:46. Branch against main: q048, q050,
  q071, q073, q134, q146 differ; main against main: q048, q050, q071, q073, q134, q135. Every difference is the order
  or choice of example files among equally hit questions. None of these questions goes through the changed code (they
  never reach the scope check).
- **Time.** The check: 396 calls, mean 0.807 s, median 0.800 s, p90 0.89 s, max 1.45 s; today (diagnosis, 198 calls)
  mean 0.912 s, median 0.775 s, p90 1.41 s, max 2.85 s. Searching every source: retrieval 1.05–2.78 s per search
  against 0.29–0.88 s unscoped for the same questions; a full answer mean 6.7 s (13 questions), 7.4 s (17), max 13.6 s.
- **Model calls.** Scope check 449 (Haiku; 396 direct, 51 inside the answer runs, 2 smoke). Other Haiku 87 (answer
  model, its checks, refusal renderings). The app's language naming on Sonnet 27 (existing use). One call to the
  default model was stopped by my guard before it was sent.

### 8.4 Claims

- Measured: every number in 8.3.
- Believed: that thinking off is what made the verdict stable (0 of 121 unstable); the prompt changed at the same time.
  That the widened search would not change core-standard answers for questions the check lets through: not measured
  (in the diagnosis' retrieval, a parking question got one NeTEx passage and five opt-in ones).
- Assumed: that "cite their source" means the source of the answering passage found by hand, not any source that
  answers.

### 8.5 Open (thought of after the numbers, not tried)

- A rule that a subject must be a thing the sources hold (a data object, an act, a process), not a bare kind of word
  ("rules", "format", "this").
- Parts 2 and 4 do not depend on the prompt: the verdict without a cache and without thinking, and the 4 s wait. They
  could be measured alone.
- Part 3 brings opt-in passages to these questions (8 of 13 with the source of the answering passage; 12 of 13
  answered, each with opt-in passages in its evidence), but also lets a question with no real subject be answered
  from them, and costs about 1 s of retrieval.

## 9. The verdict not kept and asked without thinking, prompt unchanged (2026-11-21, step S1): gate met

The two parts of §8 that do not depend on the wording, measured alone with today's prompt: the check's verdict is no
longer cached per process, the check runs without thinking on Claude (Haiku takes no temperature; "disabled" only up
to effort high, so above that thinking stays on; the other gateways already ask at temperature 0), and
`FIXED_TEXT_TRANSLATION_TIMEOUT_SECONDS` defaults to 4 instead of 3 (deploy moves an old 3 to 4). The check called
directly on the 66 questions of the diagnosis set, 3 runs, 0.97.249 plus this change.

| | Must hold | Result | |
|---|---|---|---|
| Answerable wrongly refused, the 32 | not more than 5 in any run | 3, 3, 4 (today: 6 questions refused at least once, 13 of 96 calls) | met |
| Must-refuse let through, the 34 | none in any run | 0, 0, 0 | met |
| Questions with an unstable verdict | at most 1 | 1 ("Dataset licence?", refused 1 of 3) | met |
| A repeat of the same question is asked again | unit test and one direct check | test with the model mocked; direct: two calls for two asks, both without thinking | met |
| The check's median time | at most 0.3 s above today's 0.775 s | 0.841 s (mean 0.857, max 1.40) | met |
| CI | green, Retrieval Benchmark present and green on the code commit | green on 3a6e352 | met |

Refused in every run: "What is metadata?", "Which data are mandatory?" and a prod question on validating data, the
same three that today's prompt refuses every run (§8 diagnosis). "Kaj so to metapodatki?" and "Delayed journeys
example?", refused in some runs today, were accepted 3 of 3. So the change takes away the variance; the refusals that
are left come from the wording (**measured**). 200 Haiku calls (198 + 2 for the direct check).

Believed, not measured: that thinking off, not chance, made "Kaj so to metapodatki?" stable (3 runs). This branch
also carries the record of §8 (PR #588).

## 10. Scope check wording, second attempt, every source searched (2026-11-21, step S2): gate not met, code reverted

Built on step S1 (§9). The list of what is covered is written from the index as in §8. The rule for "irrelevant" now
asks for a subject the question itself names, so that the sources could be searched for it: a general word the
question only points at ("the procedure", "this file") is not a subject until the question says what it belongs to.
A question the check lets through and that names no standard is searched in every source, as in §8. **The gate fails
on three lines (questions with no subject let through in one run of the second held-out set, one of them answered
with content; 8 of 13 opt-in answers from an answering source; one statement not in any passage). The code is
reverted on the branch; this record stays.**

I tried the wording once before freezing it: 54 calls on 28 of the 66, 13 of the first held-out set and 13 questions
of my own (6 with a named subject, 7 that only point at something). All came out as intended. The prompt was frozen at
commit 77e0c0c (16:04:49) before the second held-out set was opened; it was not changed after. The second held-out
set: 35 "out" (15 of them with no real subject) and 20 "in", written without sight of any prompt; 19 of the 20 "in"
have an answering passage in the dev index (found by hand); "Is DATEX II free to use?" has none and is left out.

| | Must hold | Result | |
|---|---|---|---|
| Answerable wrongly refused, the 32 | at most 1 in any run | 0, 0, 0 | met |
| First held-out "in" (30) wrongly refused | at most 10 % | 0 %, 0 %, 0 % | met |
| Second held-out "in" (19 with a passage) wrongly refused | at most 10 % | 0 %, 0 %, 0 % | met |
| Must-refuse let through, the 34 | none, except "Is my data good?" | 0, 0, 0 ("Is my data good?" refused too) | met |
| First held-out "out" let through | none | 0, 0, 0 | met |
| Second held-out "out" let through | at most 1 of 35 in any run, none then answered with content | 1, 1, 3: "Price of a bus ticket?" 3 of 3, "Show an example" and "What is the difference?" 1 of 3 each; the bus ticket question was answered with content | **not met** |
| Unstable verdicts, all sets (176) | at most 2 | 2 ("Show an example", "What is the difference?") | met |
| The 13 opt-in answerable: answered from a source whose cited passage answers | at least 9 | 8 | **not met** |
| Full answers read one by one | no statement that is not in a retrieved passage | one found | **not met** |
| The 25 must-stay-refused benchmark questions answered | not more than main | 2 and 2 (the same two) | met |
| App-path yardstick | hit@6 not under main's; no question differs branch–main that does not differ main–main | hit@6 132 of 149 in all four runs (base 124); main against main differs on q048, q050, q071, q073, q134, q135, q146 (order of example files); every branch–main difference is among those | met |
| Time | reported | check median 0.782 s (mean 0.809, max 1.58); widened retrieval 1.05–2.53 s; full answer mean 6.8 s, max 12.4 s | |
| CI | green, Retrieval Benchmark present and green on the code commit | green on 77e0c0c, Retrieval Benchmark included | met |

The 13 opt-in answerable questions, read against the passages the answer cited:

| Question | Answering source cited | Reading |
|---|---|---|
| Which formats count as machine-readable? | NAPCORE (FAQs on the delegated regulations) | yes |
| Kaj so to metapodatki? | mobilityDCAT-AP (metadata entry), NAPCORE | yes |
| How are static data described? | no: MMTIS Art. 2(4) was retrieved but not used; the answer says there is no definition | no |
| How are dynamical data described? | NAPCORE (RTTI/SRTI data dictionaries, DD 2015/962) | yes |
| A prod question on validating data | NAPCORE (M3.9, data insights), INSPIRE | yes |
| Speed limit updates? | INSPIRE and NAPCORE describe speed limits, not their updates; no TN-ITS passage | no |
| What is metadata? | mobilityDCAT-AP, NAPCORE | yes |
| How to describe a dataset? | mobilityDCAT-AP (properties for dataset) | yes |
| Dataset licence? | mobilityDCAT-AP (CMC mapping), NAPCORE FAQ | yes |
| What is static data? | MMTIS Art. 2(4) | yes |
| What is dynamic data? | no: MMTIS Art. 2(3) not retrieved; the answer assembles examples | no |
| Who must publish data? | no: the publisher role of mobilityDCAT-AP, not who is obliged (MMTIS not retrieved) | no |
| Which data are mandatory? | no: the MMTIS Annex not retrieved; INSPIRE and TEL TSI items | no |

The statement not in a passage: the answer to "What is dynamic data?" opens with "Dynamic data is defined in the
NAPCORE M3.1a document as data that changes over time"; the M3.1a passage says no such thing. The other twelve read
sentence by sentence against their passages: the claims are in them; "Speed limit updates?" adds a gloss
("continuous updates") to a code value. The three let-through "out" questions: two refused by the check in the full
run; "Price of a bus ticket?" never reaches the check in the app (a standards concept matches, so it is searched as
today) and was answered from NeTEx fare examples. The must-stay-refused answers ("How does it work?", "What does GTFS
say about stop times?") are on the keyword path, the same on both.

Model calls for S1 and S2 together: scope check 825 (Haiku), other Haiku 45, the app's language naming on Sonnet 13.

Claims: every number above is **measured**. **Believed**: that "Price of a bus ticket?" is answered on main too (it
does not reach the check; not run on main). That the answer numbering ([E1]…) matches the blocks the model saw: my
capture records the retrieval, and for some answers the model's blocks include ontology definitions the capture does
not list, so the reading was done by content.

Open, not tried (thought of after the numbers): the remaining misses are retrieval, not the check: for four of the five
the act that answers (MMTIS Art. 2, 3, Annex) is not among the six passages when every source competes. A share of
the evidence for each source that has a match (as `_with_scope_coverage` does for two to six scopes) might bring it in.
"Show an example" and "What is the difference?" are minority RELEVANT verdicts on questions with no subject.

Yardstick runs, 16:17–16:48, in the order main, branch, main, branch; no model calls, 337 GraphDB calls and 0
failures each. This branch carries S1's commits (§9) and the record of §8 (PR #588) until those are merged.
