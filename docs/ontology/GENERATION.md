# How each ontology file is produced

Inventory made on 2026-10-18 for the scheduled ontology drift check (issue #41, part B). The question
for each file is: can it be regenerated from the source repositories without hand work, and so
compared automatically against the committed copy? The "measured" results come from running the
generators on the CI-pinned repository commits (NeTEx `24040c1`, SIRI `7b1463b`, OpRa `1cf114b`)
in a clean checkout and comparing the output with the committed files. The committed files were
not necessarily produced from those commits.

## Summary

| File | Produced by | Regenerable from the repositories? |
|---|---|---|
| `standards/opra.ttl` | `extract_xsd_ontology` | **Yes.** Same 106 classes and 661 triples; only the provenance comment differs (see below). |
| `standards/siri.ttl` | `extract_xsd_ontology` | **Yes.** Same 310 classes and 1,852 triples; only the provenance comment differs. |
| `standards/netex.ttl` | `build_standard_ontologies`: `extract_xsd_ontology`, `scripts/build_netex_ttl_with_properties.py`, and a class recovery rule (`helpdesk/services/netex_recovery.py`) | **Yes, with the pipeline.** On upstream `dc6f162` it reproduces 919 of the 922 committed classes and 99.5% of the committed non-comment triples (below). The committed file predates the pipeline and has not been replaced yet. |
| `standards/examples.ttl` | `extract_xsd_ontology` without `--skip-example-xml` (scans every example XML) | Not measured. The scan did not finish in 10 minutes. |
| `standards/transmodel.ttl` | Enterprise Architect model export (`TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea`, header of the file), plus a section at the end written by `add_transmodel_parts --model <.qea>` (one `tmalign:transmodelPart` per class, the top-level Transmodel package such as "Part 10 - Alternative Modes (NM)"; a rerun gives the same file) | **No.** The source is a local file, not a public repository. |
| `alignments/transmodel-{netex,opra,siri}-align.ttl` | `build_transmodel_alignment` from the standards files, `transmodel.ttl` and `transmodel-alignment-curation.csv` | **Yes**, deterministic: regenerating changes only the date line. Depends on the files above. |
| `artifact-rules/*.ttl` | No generator found; the opra and siri files say "initial module scaffold" | No source to compare with. |

## Measured results

`extract_xsd_ontology --merge --refresh-auto --skip-example-xml` (the README's command) takes about
2 seconds for the three repositories.

- **OpRa and SIRI:** the class sets are identical, as are the triple counts. Every class differs in one
  triple, its `rdfs:comment "Extracted from: ..."`: the committed files say `opra.xsd`, the current
  extractor writes `xsd/opra.xsd`. The extractor changed after the committed files were made. A drift
  check would flag every class until the files are regenerated once to re-baseline them.
- **NeTEx:** the committed file has 61 classes that regeneration does not produce (`Address`,
  `AirSubmode`, `DayType`, ...) and about 3,700 further triples (properties, definitions,
  `skos:related`). The commit `703f14b` ("netex enrichment round 2") says these were "harvested from XSD
  element declarations" and the suffix table of the enrichment script was extended, but no script in the
  repository does the harvesting. Running the enrichment script on the regenerated file (its hard-coded NeTEx path
  pointed at the pinned clone, nothing else changed) gives 23,034 triples and no recovered classes. The NeTEx
  version is not the cause: the CI-pinned commit (`24040c1`), the upstream default branch (`dc6f162`,
  2026-10-08) and a local work-in-progress branch (`c7f5caa`) all give 861 extracted classes and miss the
  same 61.

### Recovering the missing classes

The 61 classes are elements that object properties point to ("dangling" targets; the enrichment finds 182)
but that the extractor does not emit. The commit that added them marks them `(property-gap recovery)`; the
selection was made by hand: of the 182 targets, documented elements such as `PrivateCode` were taken and
`PublicCode` was not. The generated ontology must not depend on a hand-made list, so the pipeline replaces it
with a fixed rule (`helpdesk/services/netex_recovery.py`). A dangling target becomes a class when it is
declared as an `xsd:element`, its name is PascalCase, and it is not a placeholder (`X_Dummy`) or a derived
view (`XView`, `XInverse`). Its definition is the documentation of the element, else of its type. The
enrichment then runs again, because the new classes bring properties with new targets, until nothing is added
(3 rounds on upstream).

Measured against the committed `netex.ttl`, generated from upstream `dc6f162` with the pinned OpRa and SIRI:

| | committed | generated |
|---|---|---|
| classes | 922 | 938 (919 in common) |
| object / datatype properties | 1,866 / 2,018 | 1,972 / 2,077 |
| triples without `rdfs:comment` in common | 20,813 of 20,910 (99.5%) | |

Only in the committed file: `privateCodes` (a lower-case container element), `SiteStructure` (never a property
target) and `SimplePoint`. Only in the generated file: 19 documented NeTEx concepts that the manual selection
skipped, among them `PublicCode`, `Presentation`, `Frequency`, `Location`, `Arrival` and `Departure`.

## Things that blocked automation (status)

1. ~~Hard-coded developer paths in both generators.~~ Resolved: see "Running the generators" below.
   (Before that change `extract_xsd_ontology` fell back to `/Users/andrejt/Research/repositories/git/<name>`,
   and the enrichment script hard-coded the NeTEx path.)
2. ~~The class recovery had no tool.~~ Resolved by the pipeline above. The README also names a manual step
   (re-add the root concept `netex:NeTEx`), but the committed file has no such concept: that README text is
   stale. If questions such as "What is NeTEx?" need the concept, the pipeline has to produce it.
3. The README's workflow mentions a glossary `backend/helpdesk/ontologies/standards.json`. It does not
   exist in the repository, so `--merge` and `--refresh-auto` have nothing to merge with.
4. ~~The `nits:` layer (`napcore-its.ttl` and the `nits-*-align.ttl` files) had no regenerable source.~~
   Resolved by `docs/ontology/NITS-REMOVAL-PLAN.md`: issue #43's question is settled — NITS was not
   needed, and both files are now deleted. Transmodel (already regenerable, see above) is the
   cross-standard pivot instead.

## What a drift check can do now

- **OpRa and SIRI:** after one re-baseline commit, regenerate on a schedule and compare. Safe to
  automate fully, even to the point of opening a pull request with the regenerated files.
- **NeTEx:** the pipeline regenerates the whole file, so it can be compared and proposed like the other
  two. Nothing is maintained by hand: the OpRa, SIRI and NeTEx ontologies are generated.
- **Transmodel alignments:** rerun `build_transmodel_alignment` after any change to the standards
  files and the curation file; this is already deterministic.
- **Not checkable:** `transmodel.ttl`, `examples.ttl` (not measured), and the artifact rules.

## Running the generators

Both take their inputs from options, so they run on any machine. Repository paths come from an
option, then an environment variable, then a directory next to this repository (`../NeTEx`, `../OpRa`,
`../SIRI`).

```bash
cd backend
python manage.py extract_xsd_ontology --merge --refresh-auto --skip-example-xml \
    --netex-path /path/to/NeTEx --opra-path /path/to/OpRa --siri-path /path/to/SIRI \
    --ttl-output-dir ../docs/ontology/standards    # default: backend/helpdesk/ontologies/standards
cd ..
python scripts/build_netex_ttl_with_properties.py docs/ontology/standards/netex.ttl netex.enriched.ttl \
    --netex-xsd-root /path/to/NeTEx/xsd            # or set NETEX_XSD_ROOT
```

Output is byte-identical to what the generators wrote before the options were added (checked on the
pinned commits).

All three standard ontologies in one command, with the same options for the repository paths:

```bash
cd backend
python manage.py build_standard_ontologies \
    --netex-path /path/to/NeTEx --opra-path /path/to/OpRa --siri-path /path/to/SIRI \
    --output-dir ../docs/ontology/standards    # the default
```

It runs the extractor, copies `opra.ttl` and `siri.ttl`, and builds `netex.ttl` with the enrichment and the
class recovery. Two runs on the same repositories give byte-identical files (tested).

## Steps before the scheduled check can be built

1. ~~Give both generators path and output options.~~ Done.
2. ~~Re-baseline `opra.ttl` and `siri.ttl` with the current extractor.~~ Done (#59).
3. ~~Decide for NeTEx.~~ Decision: nothing is maintained by hand; the pipeline generates it.
4. ~~Replace the committed `netex.ttl` with the generated one~~ Done (#61): loaded into a GraphDB and benchmarked
   with the app's scope selection first (hit@10 0.843 both ways).
5. ~~The weekly workflow~~ Done: `.github/workflows/ontology-drift.yml`, described below.

## The scheduled check

`Ontology Drift Check` runs every Monday at 05:23 UTC and on demand (Actions, "Run workflow"). On a
GitHub-hosted runner it clones the default branch of `TransmodelEcosystem/NeTEx`, `SIRI` and `OpRa`,
runs `build_standard_ontologies`, and compares the three files with the committed ones.

- **No difference:** nothing happens; the run summary lists the three commits it used.
- **Difference:** it also runs `build_transmodel_alignment`, drops any alignment file whose only change
  is its date line, and opens (or updates) the pull request `chore/regenerate-standard-ontologies` with
  the class counts and the three upstream commits.
- **A checkout with fewer than 20 files fails the run** instead of regenerating from a broken clone.

The pull request is opened with the workflow token, so it has no CI checks. Before merging, load the
changed graphs into a GraphDB (`load_graphdb_ontologies --apply --replace`) and run
`run_retrieval_benchmark --app-scope`, as was done for #61; after merging, repeat the load on the server and
restart the backend and the worker, which read the graphs only when they start
(`docs/production-deployment.md`, section 12.2). A file whose triples are unchanged, only reordered (#147), needs
no load: compare old and new with `rdflib.compare.isomorphic` first.

Checked before the first run by executing the workflow's steps locally against the upstream default
branches (NeTEx `dc6f162`, SIRI `b42cdba`, OpRa `3b829b7`, on 2026-10-19): the only difference was one
reworded definition in `opra.ttl`. Not checked locally: Python 3.11 (the runner's version; the local
runs used 3.13) and the pull-request step itself.
