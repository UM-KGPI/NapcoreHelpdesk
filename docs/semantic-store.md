# Semantic Store

The semantic store supports GraphRAG retrieval expansion and cross-standard alignment reasoning.

## Purpose

- Store ontology modules and alignment graphs used for concept expansion.
- Resolve related concepts across standards before retrieval ranking.
- Provide explicit graph context for traceable answer generation.

## Runtime role

1. Query parsing identifies candidate concepts.
2. Graph expansion runs against the semantic store.
3. Expanded concepts enrich retrieval signals.
4. Retrieval + graph signals are merged before answer composition.

## Technology

- GraphDB (RDF/OWL + SPARQL) is used as the semantic store.
- PostgreSQL remains the primary relational and vector store.

## Scope boundary

- Semantic expansion is limited to approved ontology assets and alignment graphs.
- Graph results augment retrieval and do not replace citation-based evidence requirements.

## Operational note

When GraphRAG is disabled, the system uses lexical/vector retrieval only.
