# Database Layout

Database artifacts live under this folder.

## Current files
- `migrations/001_initial_schema.sql`: initial PostgreSQL schema for the FAQ helpdesk RAG system.
- `database-class-diagram.svg`: UML class diagram of the current database schema.
- `database-class-diagram-simple.svg`: simplified presentation view of the core database entities.
- `database-er-diagram.mmd`: Mermaid ER diagram source for maintainable auto-layout.
- `database-er-diagram.puml`: PlantUML source for maintainable ER/class-style diagramming.

## Why here
- The repository is still architecture-first and does not yet have an application runtime.
- A dedicated `db/` folder keeps schema evolution separate from docs and future app code.
- This structure works whether the eventual backend is local, containerized, or deployed to managed PostgreSQL.

## Do We Need Docker?
No, not to define the schema.

Use Docker only if you want a reproducible local PostgreSQL instance for development and testing. If you already have PostgreSQL available locally or in a managed environment, Docker is optional.

## Recommended next step
When backend implementation starts, add either:
- a `docker-compose.yml` with PostgreSQL for local development, or
- environment-specific connection instructions for an existing PostgreSQL service.

## Diagram Recommendation
For ongoing maintenance, prefer the PlantUML source in `database-er-diagram.puml`.

- It is easier to edit than hand-positioned SVG.
- Orthogonal routing improves readability as relationships grow.
- It keeps cardinality and constraints explicit while staying source-controlled.

Mermaid source (`database-er-diagram.mmd`) is kept as an optional alternative.

## Generate SVG From PlantUML
Use the project target:

- `make diagrams-db`

This renders:

- `db/database-er-diagram.puml` -> `db/database-er-diagram.svg`

Manual command (single file):

- `bash scripts/render-plantuml.sh db/database-er-diagram.puml`