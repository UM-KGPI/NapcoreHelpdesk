# Improving OpRa/SIRI Transmodel Alignment Coverage — Plan

Status: **planning only — no code changed. For a cloud session to implement.**
Produced from `main` (post-NITS-removal, Transmodel is the live cross-standard pivot).
Context: [issue #85](https://github.com/UM-KGPI/NapcoreHelpdesk/issues/85), promised to the NeTEx v3
group (Tu-Tho, Thibaut) — "the alignment is by concept name, works well for NeTEx and covers far fewer
concepts for SIRI and OpRa, which will improve with next upgrades."

---

## 1. How alignment works today (verified by reading the code)

`backend/helpdesk/services/transmodel_alignment.py` (`plan_alignment`) links a standard class to a
Transmodel class **only when their names match exactly** after converting Transmodel's `STOP_PLACE`
style to the standard's `StopPlace` style (`transmodel_to_camel`, case-insensitive). There is no fuzzy
matching, no label matching, no definition-similarity matching in the automated path at all — a single
`by_camel.get(standard_class.lower(), [])` dict lookup. The only way to add a match the name-check misses
is a manual row in `transmodel-alignment-curation.csv` (currently 1 real row — the file is nearly empty
today, so essentially everything in production came from the exact-name match alone).

Current coverage (`docs/ontology/alignments/transmodel-alignment-report.md`, regenerate to confirm
current numbers before implementing): NeTEx 704/938 (75%), OpRa 33/106 (31%), SIRI 11/310 (3.5%).

## 2. Why coverage is low for OpRa and SIRI — verified, not assumed

I classified every unmatched class in the current report by whether its name matches the pattern of a
message/API-operation wrapper (`Request`, `Response`, `Delivery`, `Discovery`, `Subscription`, `Error`,
or starts with `Abstract`) — these are SOAP/XSD service-operation envelopes, not domain concepts, and
Transmodel (a conceptual reference model) was never going to have an equivalent for them regardless of
how good the matcher is:

| Standard | Unmatched | Message/API-envelope pattern | Remaining real candidates |
|---|---|---|---|
| OpRa | 73 | 62 (85%) | **11** |
| SIRI | 299 | 113 (38%) | **186** |

This is the single most important finding: **OpRa's low coverage is mostly a ceiling, not a matching
failure** — most of its XSD is request/response operation types that have no conceptual counterpart in
Transmodel at all. OpRa's realistic upper bound from better matching alone is roughly 33+11=44/106 (42%),
not something close to NeTEx's 75%. **SIRI has real headroom** — 186 classes that might be genuine
Transmodel concepts under a different name, which is where the improvement effort should concentrate.

I also checked whether `rdfs:label`/`skos:prefLabel` on SIRI classes could be used as better match
keys instead of the local class name (spot-checked 15+ examples). They cannot: SIRI's labels are short
*definition-like glosses* ("Destination" → "description of a destination"), not alternate names, so
label-equality matching would not find more matches than name-equality already does.

## 3. Options (for the cloud session to choose from, not pre-decided here)

### Option A — Stop treating message-envelope classes as "unmatched" (do this regardless of B/C)
Exclude classes matching `Request$|Response$|Delivery$|Discovery$|Subscription$|Error$|^Abstract` (or a
more precise list reviewed against the actual OpRa/SIRI class lists) from the unmatched count and from
the report's "classes without a match" list, with a clearly labeled separate section ("N
service-operation types, out of scope for conceptual alignment") instead of silently dropping them.
- **Effort:** small — a filter in `plan_alignment`/`render_report`, plus a short section in the report.
- **Risk:** the regex might misclassify a genuine domain concept. Mitigation: print the excluded list in
  a dry run and have a human (not the cloud session) spot-check it once before this ships, same review
  discipline as any curation change.
- **Does not improve real coverage** — it only stops the report (and issue #85's framing) from
  overstating the gap. Worth doing either way since it's what makes the next two options' numbers
  meaningful.

### Option B — Definition-similarity candidate suggestions (semi-automated, human-reviewed)
For each of SIRI's 186 (and OpRa's 11) remaining real candidates, compute the same word-overlap
`definition_status` scoring already used for comparing matched pairs, but against **every** Transmodel
class, not just the name-identical one. Surface the top 1-3 scoring Transmodel classes per unmatched
standard class as a new "suggested" report section (e.g.
`transmodel-alignment-suggestions.md`), explicitly **not** auto-written into the `.ttl` alignment files
— a human still decides via the existing `add`/`exclude` curation CSV mechanism.
- **Effort:** medium — reuses `definition_status`, needs an O(unmatched × all TM classes) comparison
  (SIRI 186 × ~1,648 Transmodel classes ≈ 300K comparisons of small word sets; cheap, no new dependency).
- **Risk:** word-overlap similarity on short definitions can produce confident-looking but wrong
  suggestions (the same heuristic already has the caveat "not a semantic judgement" in the existing
  report). Framing this as *suggestions for review*, never as auto-accepted links, keeps the risk at
  "wastes reviewer time on a bad suggestion," not "silently ships a wrong alignment."
- **Likely biggest real improvement** of the three options, bounded by how much reviewer time the
  NeTEx v3 group / project maintainers want to spend afterward — this produces a shortlist, not a fix.

### Option C — Compound-name / synonym normalization before exact match
Before the exact-name lookup, try a short list of mechanical transforms (strip common prefixes/suffixes
seen in real unmatched names — e.g. `Aimed`/`Actual`/`Estimated` time-qualifier prefixes, `OfFeeder`/
`OfDistributor` suffixes — and re-check against the camelCase index), and/or a small hand-built synonym
table for terms that recur across many unmatched classes (spot-check first: do words like `Aimed`,
`Actual`, `Estimated`, `Expected` recur often enough in the 186 SIRI candidates to be worth a rule?).
- **Effort:** medium, and higher-maintenance than A/B — every new transform rule is a thing someone has
  to justify and keep correct as the standards evolve.
- **Risk:** higher than B. A mechanical transform that happens to produce a false exact-name match
  would, unlike B, go straight into the generated `.ttl` alignment file as a real `skos:exactMatch`,
  not just a suggestion — any such rule needs the same curation-CSV-style human review step added
  before it's trusted, or it should only ever feed Option B's suggestion list instead of the match step.

## 4. Recommendation

Do **A** (cheap, reduces noise, makes the other numbers honest) and **B** (reuses existing code, keeps
a human in the loop, addresses the actual headroom which is in SIRI). Treat **C** as a possible later
refinement only if B's suggestion list shows a recurring, clearly-safe naming pattern worth encoding —
don't build it speculatively now. This matches the existing project's own stated caution (the alignment
report already says its classification is "a word-overlap heuristic, not a semantic judgement") and
keeps every actual `skos:exactMatch` link either name-identical or explicitly human-curated, same
guarantee the system has today.

## 5. Implementation steps (checkable claims, for whoever implements this)

1. Regenerate `transmodel-alignment-report.md` first (`manage.py build_transmodel_alignment`) and
   confirm the NeTEx/OpRa/SIRI coverage numbers in §2 above still match within a few classes — the
   standards' TTLs may have changed since this plan was written. If they differ substantially, redo the
   unmatched-classification count in §2 before proceeding.
2. Implement Option A: add the message-envelope filter, with the excluded list printed to stdout in
   `--dry-run` mode so it can be eyeballed before being trusted. Check: regenerated report's "classes
   without a match" section for OpRa/SIRI only lists genuine candidate concepts, with the excluded count
   shown separately.
3. Implement Option B: add a `suggest_transmodel_candidates` (or similarly named) pure function in
   `transmodel_alignment.py`, parallel to `plan_alignment`, taking the unmatched standard classes and all
   `tm_classes`, returning top-N scored candidates per class using the existing `definition_status`/
   `_words` machinery (do not duplicate the word-overlap logic — reuse it). Render as a new, clearly
   labeled report file; do not touch `render_turtle` or the `.ttl` output — suggestions never become
   alignment links automatically. Check: the new report exists, cites a concrete score per candidate, and
   the existing `transmodel-{netex,siri,opra}-align.ttl` files are byte-identical to before (prove
   suggestions didn't leak into the real alignment output).
4. Run the full backend test suite and add unit tests for both new behaviors (filter correctness on a
   few known message-envelope and known real-candidate class names; suggestion ranking on a small
   synthetic example with a known best match) — follow the existing test style in
   `backend/helpdesk/tests/test_transmodel_alignment.py`.
5. Do **not** edit `transmodel-alignment-curation.csv` based on the suggestions yourself — that step is
   explicitly for the NeTEx v3 group / project maintainers to review (see issue #85), not something to
   automate in this change.
6. Commit with conventional-commit messages, no Claude attribution, no version bump (separate automation
   handles that), push to a branch, no PR — same constraints as the NITS removal work.

## 6. Risks and unknowns

- The message-envelope regex in §3 Option A was derived from eyeballing the current unmatched lists; it
  has not been validated against every single class name, only spot-checked. Flag anything it excludes
  that doesn't look like a service-operation wrapper.
- Option B's suggestion quality is unverified — I did not run the word-overlap scoring against the full
  Transmodel class set for any real SIRI/OpRa class in this planning pass, only confirmed the underlying
  `definition_status` function exists and is reusable. The first real run's output needs a human
  sanity-check before anyone treats it as more than a rough shortlist.
- I did not check whether OpRa's or SIRI's upstream repositories have had schema changes since the
  TTLs here were generated — the coverage numbers in §2 are a snapshot, not a guarantee, re-verify per
  step 1 above.
- "Next upgrades" (per the email quote) may independently improve name alignment if the standards
  themselves adopt Transmodel-aligned naming — this plan doesn't assume or depend on that, it only
  improves what's extractable from the data as it exists today.
