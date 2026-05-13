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

![C4 System Context](docs/architecture/c4-system-context.svg)

_Figure: C4 Level 1 system context._

Core architecture docs:

- [C4 overview](docs/architecture/c4-overview.md)
- [Container diagram](docs/architecture/c4-container.md)
- [Orchestrator components](docs/architecture/c4-orchestrator-components.md)
- [RAG architecture](docs/architecture/rag-architecture.md)

## Quickstart (local)

Prerequisites:

- Python virtual environment at `.venv`
- Node.js + npm
- PostgreSQL (default local mode)

Run from repository root:

```bash
make backend-migrate
make backend-run
```

In a second terminal:

```bash
make frontend-install
make frontend-dev
```

Main URLs:

- Backend API: `http://localhost:8000/api/v1`
- Frontend user UI: `http://localhost:5173/user`
- Frontend operator UI: `http://localhost:5173/editor`

Full local run guide:

- [Local run quickstart](docs/testing/local-run-quickstart.md)

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

Complete target reference:

- [Make targets reference](docs/testing/make-targets-reference.md)

## Documentation

Use this order:

1. [Documentation index](docs/README.md)
2. [Architecture](docs/architecture/c4-overview.md)
3. [Testing and operations](docs/testing/local-run-quickstart.md)
4. [Functional requirements](docs/requirements/functional-requirements.md)

## Contributing

Contribution workflow and checks are documented in:

- [CONTRIBUTING.md](CONTRIBUTING.md)

## Security and secrets

- Do not commit real credentials or API tokens.
- Keep local secrets only in ignored files like `backend/.env`.
- Use environment variables in CI/CD secret stores.
- If a token is exposed, rotate it immediately.
