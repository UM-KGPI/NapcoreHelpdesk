# ERD Schema With Cardinalities

This page provides an entity-relationship diagram for the current Django data model.

## Diagramming tool choice

PlantUML is the authoritative source for the ERD in this repository.

## Source and output

- PlantUML source: [docs/architecture/erd-schema.puml](erd-schema.puml)
- Generated SVG: [docs/architecture/erd-schema.svg](erd-schema.svg)

## Render pipeline

Run from repository root:

```bash
make diagrams-erd
```

This target uses [scripts/render-plantuml.sh](../../scripts/render-plantuml.sh) and writes [docs/architecture/erd-schema.svg](erd-schema.svg).

## ERD SVG

![ERD Schema](erd-schema.svg)

## Cardinality notes

- One QuestionEvent can produce zero or many RetrievalEvent rows.
- One QuestionEvent can produce zero or many AnswerEvidenceLink rows.
- One AnswerEvidenceLink can have zero or many EvidenceProvenance rows.
- One QuestionEvent can have zero or many EditorialQueueItem rows.
- One EditorialQueueItem can have zero or many EditorialQueueTransition rows.
- One FAQEntry can have one or many FAQVersion rows.
- SourceChunk to RetrievalEvent and AnswerEvidenceLink is a logical relationship via chunk_id value, not a database foreign key.
- IndexedSourceFile, IndexRunMetric, and OntologyAssetVersion are currently standalone entities in relational terms.

## Source of truth

- Model definitions: [backend/helpdesk/models.py](../../backend/helpdesk/models.py)
- Narrative data logic: [docs/architecture/database-logic.md](database-logic.md)
