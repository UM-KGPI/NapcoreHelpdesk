# Cross-Standard User Test Script (10 Questions)

## Scope
- Validate cross-standard reasoning using the implemented glossary -> federated ontology -> expanded retrieval flow.
- Verify source-grounding quality, citation behavior, and abstention on weak evidence.

## Pass/Fail Legend
- `PASS`: all required checks for the question are met.
- `FAIL`: one or more required checks are missing or incorrect.

## Global checks for every question
- Answer includes at least one citation.
- Citations point to approved repositories only.
- No unsupported factual claim appears without evidence.

---

## Q1
Question:
- How does OpRa delay statistics relate to NeTEx vehicle journey concepts?

Pass criteria:
- Mentions OpRa delay concept and NeTEx vehicle journey concept in one coherent mapping.
- Provides at least 2 citations with at least 1 from OpRa and 1 from NeTEx.

Expected evidence pattern:
- OpRa source mentioning delay statistics or delay classification.
- NeTEx source mentioning vehicle journey semantics.

---

## Q2
Question:
- If a journey is cancelled in OpRa, what is the closest NeTEx concept and why?

Pass criteria:
- Identifies the closest NeTEx concept and gives a short reason based on cited text.
- Includes at least 1 OpRa citation and 1 NeTEx citation.

Expected evidence pattern:
- OpRa cancellation-related type or example payload.
- NeTEx vehicle journey definition or related model section.

---

## Q3
Question:
- Map OpRa planned and actual capacity indicators to related NeTEx concepts.

Pass criteria:
- Distinguishes planned vs actual capacity context.
- Provides concept-level mapping, not only keyword overlap.

Expected evidence pattern:
- OpRa capacity specification/indicator artifacts.
- NeTEx concepts tied to vehicle/journey/line or capacity-relevant structures.

---

## Q4
Question:
- How are service intensity indicators in OpRa semantically connected to network or line concepts in NeTEx?

Pass criteria:
- Explains the semantic bridge (service intensity -> network/line context).
- Includes citations from both standards.

Expected evidence pattern:
- OpRa service intensity metrics.
- NeTEx line/network/grouping concepts.

---

## Q5
Question:
- Explain the relation between journey pattern, line, and network across NeTEx and OpRa terminology.

Pass criteria:
- Gives a structured relation chain (pattern -> line -> network or equivalent).
- Uses cross-standard language alignment.

Expected evidence pattern:
- NeTEx journey pattern/line/network docs or schema fragments.
- OpRa indicators/examples that contextualize operational measurements over journeys/routes/networks.

---

## Q6
Question:
- Which OpRa passenger count and vehicle load concepts correspond to capacity-related reasoning in NeTEx?

Pass criteria:
- Identifies passenger/load concepts and maps to a capacity-oriented interpretation.
- Includes at least 2 citations with cross-repo coverage.

Expected evidence pattern:
- OpRa expected/external passenger count or vehicle load entries.
- NeTEx journey/vehicle-related concepts used for capacity context.

---

## Q7
Question:
- For delay-type analysis, which concepts should be compared between OpRa and NeTEx first?

Pass criteria:
- Returns a prioritized short list (2-5 concepts) with rationale.
- Rationale is grounded in cited passages.

Expected evidence pattern:
- OpRa type-of-delay or delay statistics structures.
- NeTEx journey/time/passing-time or related operational timing concepts.

---

## Q8
Question:
- I only know the term "late journey". What equivalent concepts exist across OpRa and NeTEx?

Pass criteria:
- Correctly resolves lexical variant to canonical concepts.
- Shows cross-standard equivalents in answer text.

Expected evidence pattern:
- Alias/label evidence for delayed/late journey language.
- Concept evidence from both standards.

---

## Q9
Question:
- Provide a minimal concept map (bullet list) linking OpRa delay indicators to NeTEx operational journey concepts.

Pass criteria:
- Produces a clear bullet list of mappings.
- Each mapping is traceable to at least one citation.

Expected evidence pattern:
- OpRa delay indicator concepts.
- NeTEx journey-oriented concepts with model semantics.

---

## Q10
Question:
- What can you NOT conclude reliably about OpRa-to-NeTEx mapping from available evidence?

Pass criteria:
- Explicitly states uncertainty or abstains where evidence is weak.
- Avoids fabricated mappings.

Expected evidence pattern:
- Limited, ambiguous, or absent evidence is acknowledged.
- Response includes cautious language and/or abstention behavior.

---

## Execution sheet (quick)
- For each question, record:
  - `Result`: PASS/FAIL
  - `Cross-standard coverage`: Yes/No
  - `Citation count`: integer
  - `Evidence quality`: High/Medium/Low
  - `Notes`: short issue summary

## Exit criteria
- Minimum 8/10 questions PASS.
- At least 7/10 answers show cross-repository citation coverage.
- 0 hallucinated unsupported claims in reviewed answers.