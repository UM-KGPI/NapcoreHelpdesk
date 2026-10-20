# Ontology Enrichment

Ontology enrichment is the process of adding example registrations to keep the semantic store
accurate as transport standard repositories grow.

> **2026-10-19 update:** the `ontology_alignment_gap` management command and its `make
> ontology-alignment-gap` target were removed as part of Phase 1 of the NITS-upper-ontology
> removal (see `docs/ontology/NITS-REMOVAL-PLAN.md`). That command was the only tool that
> automated alignment-gap detection and NITS-category assignment described further below — those
> capabilities no longer exist and the figures in "Coverage baseline" below can no longer be
> regenerated or re-verified. The example-scanning workflow (`make ontology-scan-examples`) is
> unaffected and still works as documented.

## Why enrichment matters

GraphRAG retrieval uses two ontology layers to expand and rank evidence:

| Layer | File | Role |
|-------|------|------|
| Example artifacts | `examples/<standard>-examples.ttl` | Maps each XML example to the NeTEx/SIRI concepts it illustrates |
| Normative rules | `artifact-rules/netex-artifact-rules-v1.0.ttl` | XSD-derived containment and attribute rules for validation |

(A third layer, alignment axioms mapping standard classes to NITS categories, existed until the
NITS removal referenced above; see that plan document for current status.)

A concept not covered by these layers is invisible to GraphRAG. Retrieval falls back to lexical/vector matching only, which can miss structurally correct examples that use domain vocabulary.

## Coverage baseline (NeTEx, 2026-09) — historical, frozen

These figures were last measured before the `ontology_alignment_gap` command was removed and can
no longer be regenerated:

- Per the (now-removed) `make ontology-alignment-gap` report: 824 of 2939 NeTEx terms aligned (~28%) in
  `nits-netex-align.ttl` (`owl:versionInfo "0.3-realignment-pass"`) — up from 62/872 (~7%) before a
  September 2026 realignment pass that combined hand-curated entries with a heuristic
  NITS-category pass over the remaining unaligned classes; see
  [Recent updates](recent-updates.md).
  Note: despite the report's "classes" label, that 2939 figure counts every `netex:`-prefixed
  term the extraction regex matches at line-start — both `owl:Class` declarations (922 of them)
  and lowercase-first `netex:` *properties* (~2017). Of the true `owl:Class` subset, 829/922
  (~90%) are aligned. The two percentages measure different things.
- ~287 XML examples in the NeTEx repository
- ~19 registered in `netex-examples.ttl` before the first enrichment session (example-artifact coverage was not re-scanned as part of the September realignment pass, so this figure is not re-verified)

## Scan commands

### `make ontology-scan-examples`

Scans XML example directories, extracts the top-N substantive element names per file, and writes draft `example:ExampleArtifact` TTL stanzas.

```
make ontology-scan-examples
# or with options:
cd backend && ../.venv/bin/python manage.py scan_example_artifacts \
    --standard netex \
    --dirs functions/fares functions/stopPlace \
    --top 8
```

Output: `docs/ontology/examples/netex-examples.proposed.ttl`

The command skips:
- Sources already registered in the live TTL (`dct:source` match)
- Frame containers and XML envelope elements (`PublicationDelivery`, `dataObjects`, etc.)
- Property-like elements (`Name`, `Date`, `BookingUrl`, `DaysOfWeek`, etc.)
- Abstract base classes and reference structures (`TypeOf*`, `*Ref`, `*RefStructure`, etc.)
- Cross-cutting real-world directories that mix many concepts and need manual review (`standards/norway/`, `standards/tap_tsi/`, `standards/vdv452/`, `ws_siri_request/`)

By default the scan covers all `functions/` subdirectories. The `standards/` tree and multi-standard request examples are flagged for manual review. This command only ever supported `--standard netex`; it is unaffected by the NITS removal.

## Enrichment workflow

### Trigger conditions

Run an enrichment session when:
- A new NeTEx (or SIRI/OpRa/DATEX II) release adds example files.
- A weak-answer investigation identifies a coverage gap (concept retrieved by vector search but not by graph expansion).

### Steps

**1. Scan**

```bash
make ontology-scan-examples
```

Review the output file:
- `docs/ontology/examples/netex-examples.proposed.ttl` — draft example stanzas

**2. Review and edit**

For each proposed example stanza:
- Verify the `illustratesConcept` links match what the XML actually demonstrates.
- Remove or replace concepts added by heuristic that are structural artefacts, not domain concepts.
- Adjust the label if the derived name is unclear.

**3. Publish**

Copy approved stanzas into the live TTL file:
- Example stanzas → `docs/ontology/examples/netex-examples.ttl`

Bump `owl:versionInfo` in the modified file, then load into GraphDB:

```bash
make graphdb-load
```

Re-run the scan command to confirm coverage improved.

## Automated vs manual

| Concern | Automated | Manual |
|---------|-----------|--------|
| Discovering unregistered example files | Yes — `scan_example_artifacts` scans `functions/` tree | — |
| Concept extraction per XML | Yes — top-N element frequency | Verify links are semantically correct |
| `standards/` real-world examples | No — flagged for manual review | Inspect structure before generating stanzas |
| Publishing to GraphDB | No — deliberate human gate | `make graphdb-load` after review |

Detecting unaligned classes and assigning a heuristic alignment category were automated by the
now-removed `ontology_alignment_gap` command; there is currently no tooling for either.

The deliberate human gate between scan and publish mirrors the editorial review pattern used elsewhere in the system: automation surfaces candidates, a human approves, the system publishes.
