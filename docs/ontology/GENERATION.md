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
| `standards/netex.ttl` | `extract_xsd_ontology`, then `scripts/build_netex_ttl_with_properties.py`, then work with no tool in the repository | **No.** Regeneration gives 861 classes and 23,034 triples; the committed file has 922 and 25,718. |
| `standards/examples.ttl` | `extract_xsd_ontology` without `--skip-example-xml` (scans every example XML) | Not measured. The scan did not finish in 10 minutes. |
| `standards/transmodel.ttl` | Enterprise Architect model export (`TransmodelEcoSystem2024-EAv16-nk84_OpRa-v13.qea`, header of the file) | **No.** The source is a local file, not a public repository. |
| `alignments/transmodel-{netex,opra,siri}-align.ttl` | `build_transmodel_alignment` from the standards files, `transmodel.ttl` and `transmodel-alignment-curation.csv` | **Yes**, deterministic: regenerating changes only the date line. Depends on the files above. |
| `alignments/nits-{netex,opra,siri}-align.ttl` | Heuristic rules in `ontology_alignment_gap` (`_HEURISTIC_RULES`), as stated in the header of the SIRI file and the commit messages for the other two | **No tool writes them.** That command only writes a gap report; the step that wrote the Turtle is not in the repository. |
| `napcore-its.ttl` | By hand | No source to compare with. |
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
  pointed at the pinned clone, nothing else changed) gives 23,034 triples and no recovered classes.

## Things that block automation today

1. ~~Hard-coded developer paths in both generators.~~ Resolved: see "Running the generators" below.
   (Before that change `extract_xsd_ontology` fell back to `/Users/andrejt/Research/repositories/git/<name>`,
   and the enrichment script hard-coded the NeTEx path.)
2. A manual step after every NeTEx regeneration (README, "Generation Workflow"): re-add the root concept
   `netex:NeTEx` with its labels, and keep a mapping from it to `nits:NeTExSpecification` in
   `nits-netex-align.ttl`. Nothing checks that it was done.
3. The README's workflow mentions a glossary `backend/helpdesk/ontologies/standards.json`. It does not
   exist in the repository, so `--merge` and `--refresh-auto` have nothing to merge with.
4. The `nits:` layer (`napcore-its.ttl` and the `nits-*-align.ttl` files) has no regenerable source. Whether
   it is needed at all is issue #43.

## What a drift check can do now

- **OpRa and SIRI:** after one re-baseline commit, regenerate on a schedule and compare. Safe to
  automate fully, even to the point of opening a pull request with the regenerated files.
- **NeTEx:** compare only the class set (classes added or removed upstream), and report it; do not
  overwrite the file, because regeneration would delete the 61 recovered classes and the properties.
- **Transmodel alignments:** rerun `build_transmodel_alignment` after any change to the standards
  files and the curation file; this is already deterministic.
- **Not checkable:** `transmodel.ttl`, `examples.ttl` (not measured), the `nits:` files and the rules.

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

## Steps before the scheduled check can be built

1. ~~Give both generators path and output options.~~ Done.
2. Re-baseline `opra.ttl` and `siri.ttl` with the current extractor (one commit; the diff is the
   `xsd/` prefix in the provenance comments).
3. Decide for NeTEx: either put the "recovered classes" step into code, or declare `netex.ttl` a
   maintained file and compare class sets only.
4. Turn the manual `netex:NeTEx` root concept into a check or into code.
5. Then the weekly workflow on GitHub-hosted runners: clone the three repositories at their default
   branch, run the extractor, compare, and open a pull request or an issue with the differences.
