# Semantic Layer Findings

## Status
- Date: 2026-04-14
- Scope: ontology and semantic-layer baseline for FAQ-first, RAG-fallback helpdesk
- Final target scope: NAPCORE-wide ontology coverage
- Goal: improve concept recall, disambiguation, and evidence quality for standards-grounded answers

## Retrieval Findings (Observed)
- Concept-relevant OpRa evidence can be present in indexed chunks but still lose ranking to schema-heavy sources.
- Query phrasing strongly affects retrieval when standards are not named explicitly.
- Example artifacts are under-prioritized for "how represented" and "how exchanged" questions.

## Ontology Reuse Assessment
### MobiVoc
- Assessment: not adopted as primary base for this project baseline.
- Reason: considered outdated for current target needs and governance expectations.

### Linked Connections
- Assessment: not selected for baseline reuse.
- Reason: accessibility and practical reuse constraints for this project workflow.

### GTFS-focused vocabularies
- Assessment: not selected as core ontology basis.
- Reason: too ecosystem-specific for multimodal standards-first scope in this helpdesk.

### MobilityDCAT-AP
- Assessment: useful in adjacent contexts, not core for this semantic layer.
- Reason: mainly catalog and NAP metadata; insufficient for operational concept relations required in answer retrieval.

## Adopted Baseline Recommendation
Reuse common core vocabularies and gradually build a project ontology for NAPCORE concepts.

### Core Reuse Set
- SKOS for concept schemes, preferred labels, alternative labels, and broader/narrower relations.
- PROV-O for provenance and extraction traceability.
- Dublin Core Terms (DCTERMS) for document and artifact metadata.

### Project Extension
- Introduce a project namespace for transport-specific relations not covered by the reused cores.
- Working namespace placeholder: `https://napcore.eu/ontology/napcore#`
- Candidate prefix: `tmx:`

## Minimum Modeling Profile (Phase 1)
- `tmx:Concept` mapped with SKOS semantics.
- `tmx:StandardArtifact` for source files and normative assets.
- `tmx:ExampleArtifact` for executable/illustrative examples.
- `tmx:conceptInStandard` linking concepts to standard families.
- `tmx:evidencedByArtifact` linking concepts to citable sources.
- `tmx:artifactHasChunk` linking assets to retrievable chunks.

## Governance And Change Control
- Keep ontology changes under editorial workflow: draft -> review -> approved.
- Require provenance for extracted links and concept assertions.
- Version ontology snapshots and align each retrieval run with ontology version metadata.

## Incremental Roadmap
1. Phase A: establish SKOS + PROV-O + DCTERMS baseline and seed concepts from Transmodel family standards and materials.
2. Phase B: connect concept aliases and evidence links to existing indexed chunks and retrieval traces.
3. Phase C: expand project ontology for NAPCORE overlap (Transmodel, NeTEx, SIRI, OJP/OpRa) and relation typing.
4. Phase D: extend ontology coverage with DATEX II concepts and mappings.
5. Phase E: evaluate graph-aware retrieval impact on evidence relevance and citation precision.

## Immediate Next Step
- Pilot with a narrow concept slice around delayed and cancelled journeys and verify that example artifacts (including DelayedAndCancelledJourneysWithEvents.xml) are selected as top evidence when intent is explanatory.