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
