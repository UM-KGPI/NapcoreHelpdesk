# NAPCORE Ontology Draft

## Purpose
This directory contains the initial ontology draft for the NAPCORE semantic layer.

This is currently an experimental helpdesk application ontology.
It is not yet a consensus NAPCORE domain ontology.

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
- `napcore-core.ttl`: initial ontology draft in Turtle.

## Maintainers
- Author: TODO: Author Name
- Organization: TODO: Organization Name

## Modeling Conventions
- Use `nch:` for project-specific terms.
- Prefer `skos:Concept` and `skos:ConceptScheme` over custom class hierarchies unless there is a strong implementation need.
- Keep domain assertions source-grounded through `prov:wasDerivedFrom` and DCTERMS metadata.
- Treat example XML files and normative XSD files as artifacts that can be linked to concepts and chunks.

## Initial Design Choices
- Standards are modeled as `nch:Standard` resources.
- Source files are modeled as `nch:StandardArtifact` resources.
- Example files use `nch:ExampleArtifact`, a subclass of `nch:StandardArtifact`.
- Retrieval chunks are modeled as `nch:Chunk` resources.
- Domain concepts remain `skos:Concept` resources grouped into a `skos:ConceptScheme`.
- Published FAQ resources are aligned through `nch:PublishedFAQPage`, `nch:FAQQuestion`, and `nch:FAQAnswer` as subclasses of schema.org classes.
- Evidence links are modeled through `nch:EvidenceAnnotation` as a subclass of `oa:Annotation`.
- Extraction, generation, and review workflow traces are modeled as PROV-O activities.

## Alignment Patterns
1. FAQ publishing pattern:
	- `nch:PublishedFAQPage` with `schema:mainEntity` to `nch:FAQQuestion`.
	- `nch:FAQQuestion` with `schema:acceptedAnswer` to `nch:FAQAnswer`.
2. Evidence pattern:
	- `nch:FAQAnswer` links to `nch:EvidenceAnnotation` via `nch:hasEvidenceAnnotation`.
	- `oa:hasTarget` points to source artifact URLs.
3. Provenance pattern:
	- Extraction, answer generation, and editorial review are represented with PROV-O-aligned activities.
	- Answers and evidence annotations link to the generating activity and used chunks.

## Near-Term Extension Path
1. Add more Transmodel-family concepts from NeTEx, SIRI, OJP, and OpRa materials.
2. Add extracted artifact and chunk instances during indexing.
3. Add relation extraction confidence and retrieval-oriented weighting metadata.
4. Add DATEX II concept mappings after the Transmodel-family slice is stable.