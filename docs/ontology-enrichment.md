# Ontology Enrichment

Ontology enrichment is the process of adding example registrations and cross-standard alignment axioms to keep the semantic store accurate as transport standard repositories grow.

## Why enrichment matters

GraphRAG retrieval uses three ontology layers to expand and rank evidence:

| Layer | File | Role |
|-------|------|------|
| Example artifacts | `examples/<standard>-examples.ttl` | Maps each XML example to the NeTEx/SIRI concepts it illustrates |
| Alignment axioms | `alignments/nits-<standard>-align.ttl` | Maps standard classes to NITS categories for cross-standard reasoning |
| Normative rules | `artifact-rules/netex-artifact-rules-v1.0.ttl` | XSD-derived containment and attribute rules for validation |

A concept not covered by these layers is invisible to GraphRAG. Retrieval falls back to lexical/vector matching only, which can miss structurally correct examples that use domain vocabulary.

## Coverage baseline (NeTEx, 2026-06)

- 872 NeTEx classes defined in `netex.ttl`
- 62 aligned in `nits-netex-align.ttl` (~7%)
- ~287 XML examples in the NeTEx repository
- ~19 registered in `netex-examples.ttl` before the first enrichment session

## Scan commands

Two management commands surface gaps without touching live files or GraphDB.

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

By default the scan covers all `functions/` subdirectories. The `standards/` tree and multi-standard request examples are flagged for manual review.

### `make ontology-alignment-gap`

Diffs all classes in `netex.ttl` against `nits-netex-align.ttl`, groups unaligned classes by heuristic NITS category, and writes a markdown report with a ready-to-paste TTL block per category.

```
make ontology-alignment-gap
# or:
cd backend && ../.venv/bin/python manage.py ontology_alignment_gap --standard netex
```

Output: `docs/ontology/alignments/netex-alignment-gap.md`

Heuristic category assignment (first match wins):

| Pattern | Assigned category |
|---------|-------------------|
| `TypeOf*`, `*List`, `*Ref`, `*RefStructure`, `Abstract*` | `skip` (enumeration/helper types) |
| Contains `Zone`, `Area`, `Place`, `Link`, `Point`, `Path`, `Entrance`, `Section` | `nits:SpatialEntity` |
| Contains `Journey`, `Route`, `Pattern`, `Run` | `nits:Journey` |
| Contains `Operator`, `Authority`, `Organisation`, `Provider` | `nits:Organisation` |
| Contains `Timetable`, `DayType`, `Calendar`, `Period`, `Schedule` | `nits:TemporalEntity` |
| Starts with `Stop` or ends with `Quay` | `nits:Stop` |
| Contains `Network` or ends with `Group` | `nits:Network` |
| Starts with `Line` | `nits:Line` |
| Starts with `Service` | `nits:Service` |
| Everything else | `nits:DataArtifact` (catch-all) |

The report lists skip candidates separately so they can be ignored without scrolling past them.

## Enrichment workflow

### Trigger conditions

Run an enrichment session when:
- A new NeTEx (or SIRI/OpRa/DATEX II) release adds example files or classes.
- A weak-answer investigation identifies a coverage gap (concept retrieved by vector search but not by graph expansion).
- Alignment coverage falls below an acceptable threshold on the gap report.

### Steps

**1. Scan**

```bash
make ontology-scan-examples
make ontology-alignment-gap
```

Review the two output files:
- `docs/ontology/examples/netex-examples.proposed.ttl` — draft example stanzas
- `docs/ontology/alignments/netex-alignment-gap.md` — alignment gap report with TTL blocks

**2. Review and edit**

For each proposed example stanza:
- Verify the `illustratesConcept` links match what the XML actually demonstrates.
- Remove or replace concepts added by heuristic that are structural artefacts, not domain concepts.
- Adjust the label if the derived name is unclear.

For alignment entries:
- Remove skip-category entries you do not want aligned.
- Promote any `nits:DataArtifact` defaults to a more precise NITS class if one exists.
- Flag classes that require a new NITS class (those need a core ontology extension — see below).

**3. Publish**

Copy approved stanzas into the live TTL files:
- Example stanzas → `docs/ontology/examples/netex-examples.ttl`
- Alignment axioms → `docs/ontology/alignments/nits-netex-align.ttl`

Bump `owl:versionInfo` in each modified file, then load into GraphDB:

```bash
make graphdb-load
```

Re-run the scan and gap commands to confirm coverage improved.

## Automated vs manual

| Concern | Automated | Manual |
|---------|-----------|--------|
| Discovering unregistered example files | Yes — `scan_example_artifacts` scans `functions/` tree | — |
| Concept extraction per XML | Yes — top-N element frequency | Verify links are semantically correct |
| Detecting unaligned classes | Yes — set diff of TTL class names | — |
| NITS category assignment | Yes — heuristic (first-match regex) | Override when heuristic is wrong |
| `standards/` real-world examples | No — flagged for manual review | Inspect structure before generating stanzas |
| New NITS classes (none exists yet) | No | Add class to core NITS ontology, reload, then re-align |
| Publishing to GraphDB | No — deliberate human gate | `make graphdb-load` after review |

The deliberate human gate between scan and publish mirrors the editorial review pattern used elsewhere in the system: automation surfaces candidates, a human approves, the system publishes.

## Scope: beyond NeTEx

The commands support additional standards via `--standard`:

```bash
python manage.py ontology_alignment_gap --standard opra
python manage.py ontology_alignment_gap --standard siri
python manage.py ontology_alignment_gap --standard datex
```

Each standard requires its own `standards/<standard>.ttl` and `alignments/nits-<standard>-align.ttl` to be present in `docs/ontology/`. The scan command currently supports `--standard netex` only; extend `scan_example_artifacts.py` when example repositories for other standards are available locally.
