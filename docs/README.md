# Documentation Index

This index reduces discovery overhead by grouping the most important documents first.

## Start here

- [Repository overview](../README.md)
- [Contributing guide](../CONTRIBUTING.md)
- [Local run quickstart](testing/local-run-quickstart.md)
- [Make targets reference](testing/make-targets-reference.md)

## Architecture

- [C4 overview](architecture/c4-overview.md)
- [System context](architecture/c4-system-context.md)
- [Container view](architecture/c4-container.md)
- [Orchestrator components](architecture/c4-orchestrator-components.md)
- [RAG architecture](architecture/rag-architecture.md)
- [Database logic](architecture/database-logic.md)
- [PostgreSQL + pgvector runbook](architecture/postgresql-pgvector-runbook.md)
- [Deployment and operations checklist](architecture/deployment-operations-checklist.md)

## Testing and operations

- [Local run quickstart](testing/local-run-quickstart.md)
- [Console usage steps](testing/console-usage-steps.md)
- [First user testing pack](testing/first-user-testing-pack.md)
- [Backup and restore workflow](testing/backup-restore-workflow.md)
- [Docker dev quickstart](testing/docker-dev-quickstart.md)

## Requirements

- [Functional requirements](requirements/functional-requirements.md)

## Ontology and standards assets

- [Ontology README](ontology/README.md)
- [TRANSMODEL ontology notes](ontology/TRANSMODEL-ONTOLOGY.md)
- [Transmodel glossary](transmodel-glossary.md)

## Presentations

- [Executive summary](presentation/napcore-helpdesk-executive-summary.md)

## Notes on document strategy

- Root-level documents (`README.md`, `CONTRIBUTING.md`) are the primary public entrypoints.
- Detailed implementation and operational material remains under `docs/`.
- New docs should be added only when existing pages cannot be extended cleanly.
- Ontology pipeline known limitation: after regenerating `docs/ontology/standards/netex.ttl`, a manual `netex:NeTEx` root concept + label patch is currently required to preserve plain-language NeTEx semantic anchoring; see `docs/ontology/README.md` for the authoritative regeneration checklist.
