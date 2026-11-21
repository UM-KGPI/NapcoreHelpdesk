# Improving OpRa/SIRI Transmodel alignment coverage

Status (2026-11-21): options A and B are implemented. Option C is not built and not planned.
Context: [issue #85](https://github.com/UM-KGPI/NapcoreHelpdesk/issues/85). I told the NeTEx v3 group
that the alignment is by concept name, works well for NeTEx, and covers far fewer concepts for SIRI
and OpRa.

## 1. How alignment works

`plan_alignment` in `backend/helpdesk/services/transmodel_alignment.py` links a standard class to a
Transmodel class only when the names match exactly, after turning `STOP_PLACE` into `StopPlace`. There
is no fuzzy, label or definition matching in that step. The only other way in is a manual row in
`transmodel-alignment-curation.csv`. Labels cannot serve as match keys: SIRI labels are short
glosses of the definition, not alternative names.

## 2. Why OpRa and SIRI look low

Many unmatched classes are XSD message envelopes or abstract base types: names ending in `Request`,
`Response`, `Delivery`, `Discovery`, `Subscription`, `Error`, or starting with `Abstract`. Transmodel
is a conceptual model and has no counterpart for them. The report now counts them apart.

Regenerated on 2026-11-21 from the committed standards (aligned counts did not change):

| Standard | Classes | Aligned | Unmatched before | Unmatched now | Service-operation types |
|---|---|---|---|---|---|
| NeTEx | 938 | 704 (75%) | 234 | 228 | 6 |
| OpRa | 106 | 33 (31%) | 73 | 11 | 62 |
| SIRI | 310 | 11 (3.5%) | 299 | 186 | 113 |

OpRa's low coverage is mostly a ceiling, not a matching failure. Its realistic upper bound by
better matching is about 44 of 106. SIRI has real headroom: 186 classes that may be genuine Transmodel
concepts under another name.

## 3. What was built

- **Option A.** The report has a separate section "service-operation types, out of scope for
  conceptual alignment". `--dry-run` prints the list. A name match still wins over the filter.
- **Option B.** `suggest_transmodel_candidates` scores every Transmodel class against each unmatched
  class with the existing word-overlap `definition_status`. The top 3 go to
  `docs/ontology/alignments/transmodel-alignment-suggestions.md`, sorted by best score. The file is
  for review only. It is never passed to `render_turtle`, so the three `transmodel-*-align.ttl` files
  do not depend on it. To accept a suggestion, add a row to `transmodel-alignment-curation.csv` and
  regenerate. A full run takes about 30 seconds.
- **Option C (name transforms before the exact match) is not built.** A wrong transform would write a
  false `skos:exactMatch` straight into the TTL. I would only consider it as a feeder for the
  suggestions, and only if the suggestions show a clearly safe recurring pattern.

## 4. Risks

- The envelope pattern was checked by reading the list, not against every class. Some `Abstract*`
  classes in OpRa (`AbstractLogEntry`, `AbstractLoggableObject`, `AbstractCtxIndicator`) are base types
  of real domain concepts. They are debatable as "out of scope".
- Word overlap on short definitions gives confident but wrong suggestions. Identical definitions
  (score 1.00) are reliable leads; lower scores need a person.
- Accepting suggestions into the curation CSV is for the NeTEx v3 group and the maintainers.
