# NAPCORE ITS Ontology Assets

## Purpose
This directory contains ontology assets for the NAPCORE semantic layer.

The current canonical core ontology is intentionally minimal and focused on cross-standard semantic anchoring.
It supports reasoning, evidence grounding, and retrieval behavior in the Helpdesk app.
It also serves as a stable pivot for repository-specific instance ontologies derived from ingested source documents.

## Instance Ontology Lifecycle
1. Ingest repository files from approved sources.
2. Extract concepts, relations, and evidence links from source artifacts.
3. Materialize repository-specific concept inventories aligned to the federated core/module/alignment model.
4. Index chunks with ontology-linked metadata for retrieval and citation.
5. Use the federated ontology set during retrieval-time reasoning and ranking.

The draft is intentionally small:
- reuse SKOS for concept modeling,
- reuse PROV-O for provenance,
- reuse DCTERMS for source metadata,
- reuse schema.org for published FAQ and Q&A artifacts,
- reuse Web Annotation (`oa:`) for citation and evidence span structures,
- add only the minimum NAPCORE-specific classes and properties needed for graph-aware retrieval.

## Current Scope
- Final target scope: NAPCORE-wide ontology coverage.
- Initial seeded scope: concepts from the Transmodel family of standards and materials.
- Planned later extension: DATEX II concepts and mappings.

## Files
- `napcore-its.ttl`: canonical minimal federated NAPCORE ITS core ontology in Turtle (`nits:` namespace).
- `netex-federated.ttl`: NeTEx federated ontology module linked to core concepts.
- `opra-federated.ttl`: OpRa federated ontology module linked to core concepts.
- `siri-federated.ttl`: SIRI federated ontology module linked to core concepts.
- `datex-federated.ttl`: DATEX II federated ontology module linked to core concepts.
- `standards-alignment.ttl`: alignment ontology declaring cross-standard mappings.

## Generation Workflow
The federated module files are generated from extracted concept inventories:
1. Refresh extracted concepts into `backend/helpdesk/ontologies/standards.yaml` from local standards repositories.
2. Rebuild standard module ontologies (`netex-federated.ttl`, `opra-federated.ttl`, `siri-federated.ttl`, `datex-federated.ttl`) from the refreshed glossary.
3. Rebuild `standards-alignment.ttl` from the refreshed glossary.

Recommended commands:
`cd backend && ../.venv/bin/python manage.py extract_xsd_ontology --merge --refresh-auto --skip-example-xml`

`cd backend && ../.venv/bin/python manage.py build_federated_ontologies`

`cd backend && ../.venv/bin/python manage.py build_standards_alignment`

Notes:
- Full-tree XSD scanning is now the default for both NeTEx and OpRa.
- Use `--netex-key-files-only` or `--opra-key-files-only` only if you need the earlier focused extraction mode.

Rebuild alignment ontology using the reproducible backend command:
`cd backend && ../.venv/bin/python manage.py build_standards_alignment`

Useful options:
- `--input <path>` to use a custom glossary YAML.
- `--output <path>` to write a custom TTL path.
- `--no-related` to generate only exact/close mappings.
- `--ontology-version <value>` and `--created-date YYYY-MM-DD` to control ontology metadata.

Most recent refresh used local repositories for NeTEx and OpRa and linked concepts to available XML example artifacts.

## Federated Topology
The planned ontology topology is federated and hub-and-spoke:
1. Core ontology (`napcore-its.ttl`) provides canonical `nits:` concepts.
2. Standard modules (`netex-federated.ttl`, `opra-federated.ttl`, `siri-federated.ttl`, `datex-federated.ttl`) provide standard-local concepts.
3. Alignment module (`standards-alignment.ttl`) declares explicit cross-standard mappings and equivalences.

This structure keeps runtime anchoring stable while allowing each standard ontology to evolve independently.

## Maintainers
- Author: TODO: Author Name
- Organization: TODO: Organization Name

## Modeling Conventions
- Use `nits:` for canonical project-specific core terms.
- Use standard-local module prefixes such as `netex:` and `opra:` for standard-specific concepts.
- Prefer `skos:Concept` and `skos:ConceptScheme` over custom class hierarchies unless there is a strong implementation need.
- Keep domain assertions source-grounded through `prov:wasDerivedFrom` and DCTERMS metadata.
- Treat example XML files and normative XSD files as artifacts that can be linked to concepts and chunks.

## Initial Design Choices
- Domain concepts remain `skos:Concept` resources grouped into canonical and standard-local `skos:ConceptScheme` resources.
- Cross-standard anchoring is handled through canonical `nits:` concepts and explicit alignment assertions.
- Source artifacts and retrieval chunks stay source-grounded through PROV-O and DCTERMS metadata rather than a separate application ontology.
- Published FAQ resources can still align to schema.org and Web Annotation where needed, but those shapes are not part of the core federated ontology set.

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
1. Add more Transmodel-family concepts from NeTEx, SIRI, OJP, and OpRa materials.
2. Add extracted artifact and chunk instances during indexing.
3. Add relation extraction confidence and retrieval-oriented weighting metadata.
4. Add DATEX II concept mappings after the Transmodel-family slice is stable.