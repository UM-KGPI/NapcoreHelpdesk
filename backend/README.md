# Backend Scaffold (Django + DRF)

This folder contains the initial backend scaffold for NAPCORE Helpdesk.

## What is included
- Django project config in `config/`.
- Helpdesk app in `helpdesk/`.
- Canonical FAQ persistence with versioning (`FAQEntry`, `FAQVersion`).
- Retrieval and evidence audit persistence (`RetrievalEvent`, `AnswerEvidenceLink`).
- DRF endpoints for:
  - `GET /api/v1/health/live`
  - `GET /api/v1/health/ready`
  - `POST /api/v1/questions/answer`
  - `GET /api/v1/faqs/promotion-candidates`
  - `POST /api/v1/editorial/queue`
  - `GET /api/v1/editorial/queue`
  - `GET /api/v1/editorial/queue/metrics`
  - `POST /api/v1/editorial/queue/transition`
- FAQ-first plus RAG-fallback orchestration in service modules aligned with C4 Level 3 mapping.
- JWT bearer authentication (`Authorization: Bearer <jwt>`) validated with `JWT_SECRET_KEY` and `JWT_ALGORITHM`.

## Local setup
1. Install Python dependencies from `requirements.txt`.
2. Copy `.env.example` to `.env` and adjust values.
3. Run migrations.
4. Start the server.

## Database baseline
- Architecture baseline is PostgreSQL-first (`DJANGO_USE_SQLITE=False`) with pgvector-ready schema.
- SQLite remains supported for local tests and lightweight development by setting `DJANGO_USE_SQLITE=True`.
- On PostgreSQL, migration `0006_pgvector_native_alignment` enables the `vector` extension and creates an IVF Flat index on `SourceChunk.embedding_vector`.
- On SQLite, embeddings transparently fall back to JSON storage while keeping the same service interfaces.
- Operational rollout checklist: [docs/architecture/postgresql-pgvector-runbook.md](../docs/architecture/postgresql-pgvector-runbook.md)

## API request headers
- `Authorization: Bearer <jwt-token>`
- `X-Request-Id: <non-empty-id>` for `POST /api/v1/questions/answer`

## Build retrieval index from repository sources
Run from `backend/`:

`../.venv/bin/python manage.py build_source_index --repo-url https://github.com/NeTEx-CEN/NeTEx --repo-path /absolute/path/to/NeTEx --profile netex --incremental --prune`

This ingests supported text files (`.md`, `.txt`, `.yaml`, `.yml`, `.xml`, `.json`) into `SourceChunk`.
Use `--include-ext` repeatedly to narrow file types.
Use `--include-path` / `--exclude-path` to refine path filtering.

Profile rules are data-driven from YAML files in `helpdesk/index_profiles/`:
- `default.yaml`
- `netex.yaml`

Add new profiles by creating additional `<profile>.yaml` files with:
- `include: [ ... ]`
- `exclude: [ ... ]`

Repository allow-list is enforced via `ALLOWED_SOURCE_REPOSITORIES`.

Each run records telemetry in `IndexRunMetric` and incremental state in `IndexedSourceFile`.

## Scheduled incremental indexing
Celery Beat runs `helpdesk.reindex_default_repository` daily. Configure:
- `INDEX_SCHEDULE_REPO_URL`
- `INDEX_SCHEDULE_REPO_PATH`
- `INDEX_SCHEDULE_PROFILE` (default `netex`)

## Top-level Make targets
From repository root:
- `make backend-check`
- `make backend-migrate`
- `make backend-run`
- `make backend-index REPO_URL=https://github.com/NeTEx-CEN/NeTEx REPO_PATH=/absolute/path/to/NeTEx PROFILE=netex INCREMENTAL=1`
- `make frontend-install`
- `make frontend-dev`
- `make frontend-build`

Frontend Web GUI container docs: `../frontend/README.md`

## Operations automation
- CI workflow: `../.github/workflows/ci.yml`
- Security workflow: `../.github/workflows/security.yml`
- Release workflow: `../.github/workflows/release.yml`
- Deployment checklist: `../docs/architecture/deployment-operations-checklist.md`
- First user testing pack: `../docs/testing/first-user-testing-pack.md`
- Day 1 execution sheet: `../docs/testing/day-1-execution-sheet.md`
- Pilot feedback template: `../.github/ISSUE_TEMPLATE/pilot-feedback.yml`
