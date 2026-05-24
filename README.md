# NAPCORE Helpdesk

NAPCORE Helpdesk is a FAQ-first, RAG-fallback helpdesk for transport standards.
It answers user questions from approved standards repositories, provides evidence and citations, and supports a human editorial workflow before publication.

## What this repository contains

- Backend API and orchestration: Django + DRF
- Frontend web GUI: React + TypeScript + Vite
- Retrieval stack: lexical + vector retrieval (pgvector in PostgreSQL)
- Optional graph expansion: GraphDB (RDF/OWL + SPARQL)
- Editorial workflow: draft -> review -> approved/rejected -> published

## Architecture at a glance

The runtime uses a split LLM path:

- Controller path: intent detection, route selection, and constrained query planning
- Narration path: grounded answer composition from evidence and citations

![C4 System Context](docs/diagrams/c4-system-context.svg)

_Figure: C4 Level 1 system context._

Essential architecture doc:

- [Architecture overview](docs/architecture-overview.md)

## Quickstart (local)

Install guides:

- [Installation (local and Docker)](docs/installation.md)

## Most used Make targets

- `make backend-check`
- `make backend-migrate`
- `make backend-run`
- `make backend-index REPO_URL=<url> REPO_PATH=<absolute-path> PROFILE=netex INCREMENTAL=1`
- `make frontend-install`
- `make frontend-dev`
- `make frontend-build`
- `make frontend-test`
- `make health`

API contract:

- [API description](docs/api-description.md)
- [OpenAPI source](api/openapi.yaml)

Additional essentials:

- [Semantic store](docs/semantic-store.md)
- [LLM usage](docs/llm-usage.md)

## Documentation

Public docs index:

- [Documentation index](docs/README.md)

## Contributing

Contribution workflow and checks are documented in:

- [CONTRIBUTING.md](CONTRIBUTING.md)

## Security and secrets

- Do not commit real credentials or API tokens.
- Keep local secrets only in ignored files like `backend/.env`.
- Use environment variables in CI/CD secret stores.
- If a token is exposed, rotate it immediately.
