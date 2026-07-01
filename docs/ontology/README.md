# NAPCORE ITS Ontology Assets

## Purpose
This directory contains ontology assets for the NAPCORE semantic layer.

Policy: GraphDB is the only runtime ontology knowledge base.
The local ontology files in this directory are maintained as a 1:1 mirror of what is loaded into GraphDB.

The current canonical core ontology is intentionally minimal and focused on cross-standard semantic anchoring.
It supports reasoning, evidence grounding, and retrieval behavior in the Helpdesk app.
It also serves as a stable pivot for repository-specific instance ontologies derived from ingested source documents.

## Instance Ontology Lifecycle
1. Ingest repository files from approved sources.
2. Extract concepts, relations, and evidence links from source artifacts.
3. Materialize repository-specific concept inventories aligned to the core/standards/alignment model.
4. Index chunks with ontology-linked metadata for retrieval and citation.
5. Use the standards + alignment ontology set during retrieval-time reasoning and ranking.

The draft is intentionally small:
- reuse SKOS for concept modeling,
- reuse PROV-O for provenance,
- reuse DCTERMS for source metadata,
- reuse schema.org for published FAQ and Q&A artifacts,
- reuse Web Annotation (`oa:`) for citation and evidence span structures,
- add only the minimum NAPCORE-specific classes and properties needed for graph-aware retrieval.

## Current Scope
- Final target scope: NAPCORE-wide ontology coverage.
- Current implemented scope: core `nits:` concepts plus standard modules for NeTEx, OpRa, SIRI, and DATEX II.
- Current implemented scope also includes explicit cross-standard alignment modules, example-artifact modules for retrieval-oriented artifact linking, and optional artifact-derived rule modules for standard-specific normative reasoning.

## Files
- `napcore-its.ttl`: canonical NAPCORE ITS core ontology in Turtle (`nits:` namespace).
- `standards/netex.ttl`: NeTEx standard ontology module.
- `standards/opra.ttl`: OpRa standard ontology module.
- `standards/siri.ttl`: SIRI standard ontology module.
- `standards/datex.ttl`: DATEX II standard ontology module.
- `examples/netex-examples.ttl`: NeTEx example-artifact ontology module linking repository examples to canonical standard concepts.
- `alignments/nits-netex-align.ttl`: NITS-NeTEx alignment axioms.
- `alignments/nits-opra-align.ttl`: NITS-OpRa alignment axioms.
- `alignments/nits-siri-align.ttl`: NITS-SIRI alignment axioms.
- `alignments/nits-datex-align.ttl`: NITS-DATEX II alignment axioms.
- `artifact-rules/netex-artifact-rules-v1.0.ttl`: NeTEx XSD-derived normative rules (versioned, standard-scoped).
- `artifact-rules/opra-artifact-rules-v1.0.ttl`: OpRa XSD-derived normative rules (versioned, standard-scoped).
- `artifact-rules/siri-artifact-rules-v1.0.ttl`: SIRI XSD-derived normative rules (versioned, standard-scoped).
- `artifact-rules/datex-artifact-rules-v1.0.ttl`: DATEX II XSD-derived normative rules (versioned, standard-scoped).

## Generation Workflow
The ontology files are generated from extracted concept inventories:
1. Refresh extracted concepts into `backend/helpdesk/ontologies/standards.json` from local standards repositories.
2. Rebuild standard module ontologies under `docs/ontology/standards/` from the refreshed glossary or XSD-grounded workflows.
3. Rebuild alignment ontologies under `docs/ontology/alignments/` from refreshed mappings.

Recommended commands:
`cd backend && ../.venv/bin/python manage.py extract_xsd_ontology --merge --refresh-auto --skip-example-xml`

Notes:
- Full-tree XSD scanning is now the default for both NeTEx and OpRa.
- Use `--netex-key-files-only` or `--opra-key-files-only` only if you need the earlier focused extraction mode.
- Manual post-regeneration guard (required for current pipeline): after each regeneration of `docs/ontology/standards/netex.ttl`, re-add a standard root concept `netex:NeTEx` with lexical labels (`rdfs:label "NeTEx"@en`, `skos:prefLabel "netex"@en`, optional `skos:altLabel` variants) so semantic parsing can anchor plain-language questions like "What is NeTEx?".
- Keep alignment parity with this guard by ensuring `docs/ontology/alignments/nits-netex-align.ttl` contains a mapping from `netex:NeTEx` to `nits:NeTExSpecification`.
- After local ontology updates, publish them to GraphDB to preserve 1:1 parity using `manage.py load_graphdb_ontologies --apply`.

Rebuild alignment ontologies using the per-standard alignment artifacts in `docs/ontology/alignments/` and the XSD-grounded workflow.

Most recent refresh used local repositories for NeTEx and OpRa and linked concepts to available XML example artifacts.

## Ontology Topology
The ontology topology is core + standards + examples + alignments (+ optional artifact-derived rules):
1. Core ontology (`napcore-its.ttl`) provides canonical `nits:` concepts.
2. Standard modules (`standards/netex.ttl`, `standards/opra.ttl`, `standards/siri.ttl`, `standards/datex.ttl`) provide standard-local concepts.
3. Example modules (`examples/*.ttl`) describe repository artifacts and map them to canonical standard concepts without polluting the conceptual standard ontologies.
4. Alignment modules (`alignments/nits-netex-align.ttl`, `alignments/nits-opra-align.ttl`, `alignments/nits-siri-align.ttl`, `alignments/nits-datex-align.ttl`) declare explicit cross-standard mappings and equivalences.
5. Artifact-derived rules (`artifact-rules/*-artifact-rules-v*.ttl`) capture XSD-derived normativity (mandatory/optional/cardinality/required attributes), one standard per file and one version per file.

This structure keeps runtime anchoring stable while allowing each standard ontology to evolve independently.

## Artifact-Rules Loading Scope
- Artifact-derived rules are not part of default ontology graph loading.
- Load them only for standard-specific normative question answering.
- Use `manage.py load_graphdb_ontologies --apply --include-artifact-rules` to include all artifact-rules modules.
- Use `--artifact-rule-standards netex,opra` to limit scope to selected standards.

## Maintainers
- Author: TODO: Author Name
- Organization: TODO: Organization Name

## Modeling Conventions
- Use `nits:` for canonical project-specific core terms.
- Use standard-local module prefixes such as `netex:`, `opra:`, `siri:`, and `datex:` for standard-specific concepts.
- Model core and standard concepts primarily as `owl:Class` and `owl:ObjectProperty`, and use SKOS annotations for lexical labels, aliases, and related-term hints.
- Keep domain assertions source-grounded through `prov:wasDerivedFrom` and DCTERMS metadata.
- Treat example XML files and normative XSD files as artifacts that can be linked to concepts and chunks.

## Initial Design Choices
- Standard modules model transport entities as OWL classes with source-grounded annotations and hierarchy axioms.
- Example modules model repository artifacts separately and attach retrieval-relevant example labels and source paths to canonical concepts through explicit illustration links.
- Cross-standard anchoring is handled through canonical `nits:` concepts and explicit alignment assertions.
- Artifact-derived rules remain in separate standard-scoped modules so normative constraints can be loaded only when a query requires them.
- Source artifacts and retrieval chunks stay source-grounded through PROV-O and DCTERMS metadata rather than a separate application ontology.
- Published FAQ resources can still align to schema.org and Web Annotation where needed, but those shapes are not part of the core ontology set.

## Alignment Patterns
1. FAQ publishing pattern:
	- Use `schema:FAQPage`, `schema:Question`, and `schema:Answer` directly when publishing FAQ artifacts.
2. Evidence pattern:
	- Use `oa:Annotation` for answer-to-evidence linking when span-level evidence records are required.
	- `oa:hasTarget` points to source artifact URLs.
3. Provenance pattern:
	- Extraction, answer generation, and editorial review are represented with PROV-O-aligned activities.
	- Answers and evidence annotations link to the generating activity and used chunks.

## Near-Term Extension Path
1. Add more Transmodel-family concepts from NeTEx, SIRI, and OpRa materials.
2. Add extracted artifact and chunk instances during indexing.
3. Add relation extraction confidence and retrieval-oriented weighting metadata.
4. Add DATEX II concept mappings after the Transmodel-family slice is stable.
