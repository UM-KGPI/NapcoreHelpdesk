# Backend Scaffold (Django + DRF)

This folder contains the initial backend scaffold for NAPCORE Helpdesk.

## What is included
- Django project config in `config/`.
- Helpdesk app in `helpdesk/`.
- Canonical FAQ persistence with versioning (`FAQEntry`, `FAQVersion`).
- Retrieval and evidence audit persistence (`RetrievalEvent`, `AnswerEvidenceLink`).
- Chat-session compatible answer orchestration keyed by `sessionId` / `userId`.
- Deterministic grounded generation plus optional LLM-ready provider adapter with safe fallback.
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

## Answer generation modes
- `generationProfile=deterministic-grounded` uses the built-in grounded generator.
- `generationProfile=llm-ready` attempts provider-backed generation when `LLM_ENABLED=True`.
- If LLM generation fails, the service falls back to deterministic grounded generation.

LLM settings are configured through:
- `LLM_ENABLED`
- `LLM_PROVIDER`
- `LLM_API_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_TOKENS`
- `LLM_TEMPERATURE`

## Versioning
- Single source of truth: repository-root `VERSION` file.
- Frontend display uses `VITE_APP_VERSION` when provided, otherwise uses the root `VERSION` file at build time.
- Backend health endpoints use `SERVICE_VERSION`; when unset, backend defaults to the root `VERSION` file.
- Build traceability remains separate via `SERVICE_BUILD_REF` (for example git short SHA or release tag).

Version bump workflow:
1. Update the root `VERSION` file.
2. Set `SERVICE_BUILD_REF` for the deployment/build.
3. Rebuild frontend and restart backend containers/services.

### Latest narration improvements (2026-05-13)
- For XML/JSON/YAML example requests, the narration prompt now asks for one short verbatim fenced snippet from a single retrieved evidence block when available.
- Fabricated example protection is enforced: generated structured code blocks are validated against retrieved evidence lines and rejected when unsupported.
- If no safe verbatim snippet exists in evidence, narration must explicitly state that an embedded example cannot be provided safely.
- Evidence citation links now avoid `blob/unknown` by resolving stable repository refs first and using repository-specific fallback refs when needed.
- Single-token default wiring is supported for GitHub Models: `GITHUB_API_TOKEN` feeds `LLM_API_KEY` and `CONTROLLER_LLM_API_KEY` when dedicated keys are not set.

## Build retrieval index from repository sources
Run from `backend/`:

`../.venv/bin/python manage.py build_source_index --repo-url https://github.com/TransmodelEcosystem/NeTEx --repo-path /absolute/path/to/NeTEx --profile netex --incremental --prune`

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

Multiple approved repositories can be ingested side-by-side, for example:
- `https://github.com/TransmodelEcosystem/NeTEx`
- `https://github.com/NeTEx-CEN/test-Profile-Documentation`

Store them as a comma-separated list in `ALLOWED_SOURCE_REPOSITORIES`.

Each run records telemetry in `IndexRunMetric` and incremental state in `IndexedSourceFile`.

Note for local SQLite:
- `--prune` may hit SQLite parameter limits on very large repositories.
- If that happens, run without `--prune` or use PostgreSQL for production-scale indexing.

## Semantic reasoning model (implemented)
- The backend retrieval path uses an explicit two-layer semantic setup:
  - GraphDB-backed standards glossary concepts loaded from ontology modules and alignments.
  - GraphDB-backed NITS core concept graph for cross-standard expansion.
- Runtime uses `nits:` as the canonical core namespace and still supports legacy `maps_to_nch` fields for backward compatibility.
- Canonical RDF/Turtle artifact for the same core graph: `../docs/ontology/napcore-its.ttl`.
- Runtime implementation is in `helpdesk/services/semantic_graph.py`.
- Canonical end-to-end runtime methodology: `../docs/architecture/query-to-evidence-methodology.md`.
- Query reasoning flow:
  1. Lexical concept extraction from glossary labels and aliases.
  2. Mapping from glossary concepts to `nits:` concepts (`maps_to_nits`, legacy `maps_to_nch`, or synonym-derived mapping).
  3. NITS relation expansion (`related_to`) for cross-standard semantic neighbors.
  4. Projection back to glossary concepts for candidate retrieval and ranking adjustments.
- This keeps term normalization and user-language matching in the glossary while semantic interoperability is handled by the ontology graph.

### Ontology validation controls
- Ontology payloads are schema-validated at load time in `helpdesk/services/semantic_graph.py`.
- Malformed ontology fields are sanitized where possible.
- GraphDB is the only runtime ontology knowledge base. If required ontology payloads cannot be loaded from GraphDB, initialization fails.
- Optional strict mode: set `NAPCORE_ONTOLOGY_STRICT_VALIDATION=true` to fail fast on schema validation errors (recommended for CI and controlled deployments).

## GraphDB anchoring interface (implemented)
- Semantic parsing now supports optional GraphDB SPARQL anchoring/discovery through a connector abstraction in `helpdesk/services/graphdb_connector.py`.
- Configuration flags:
  - `GRAPHDB_ENABLED`
  - `GRAPHDB_SPARQL_ENDPOINT`
  - `GRAPHDB_REPOSITORY`
  - `GRAPHDB_TIMEOUT_SECONDS`
- When GraphDB is enabled and reachable, parsing can:
  - anchor terms to core concepts via SPARQL;
  - discover relevant standards from aligned concepts.
- If GraphDB anchoring/discovery returns no anchors for a query, parsing uses already-loaded in-memory indexes derived from GraphDB ontology payloads.

## Staging rollout controls
Use feature flags in `backend/.env` for progressive rollout:

- Wave 1 evidence and policy controls:
  - `SEMANTIC_LOW_CONFIDENCE_THRESHOLD`
  - `EVIDENCE_GATE_ENABLED`
  - `EVIDENCE_GATE_MIN_ALIGNMENT`
  - `EVIDENCE_GATE_MIN_CHUNKS`
  - `EVIDENCE_GATE_MIN_REPOSITORIES_MULTI_SCOPE`
  - `POLICY_STRICT_CLAIM_GUARD`
- Wave 2 retrieval governance controls:
  - `GRAPH_EXPANSION_MAX_CONCEPTS`
  - `GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS`
  - `RETRIEVAL_DIVERSITY_ENABLED`
  - `RETRIEVAL_MAX_SAME_SOURCE_PATH`
  - `RETRIEVAL_MMR_LAMBDA`
  - `RETRIEVAL_KEYWORD_TRAP_PENALTY`

Recommended staging start (conservative):
- Keep `POLICY_STRICT_CLAIM_GUARD=False` initially.
- Set `EVIDENCE_GATE_ENABLED=True` with defaults from `.env.example`.
- Keep retrieval governance defaults, then tune only by aggregate telemetry deltas.

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
- `make backend-index REPO_URL=https://github.com/TransmodelEcosystem/NeTEx REPO_PATH=/absolute/path/to/NeTEx PROFILE=netex INCREMENTAL=1`
- `make frontend-install`
- `make frontend-dev`
- `make frontend-build`

Frontend Web GUI container docs: `../frontend/README.md`

## JWT for local development
Manual token generation (from `backend/`):

`../.venv/bin/python manage.py shell -c "import datetime as dt, jwt; from django.conf import settings; now=dt.datetime.now(dt.timezone.utc); payload={'sub':'user-local','roles':['editor','reviewer','publisher'],'iat':int(now.timestamp()),'exp':int((now+dt.timedelta(hours=8)).timestamp())}; print(jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))"`

Automatic token generation for the UI is available via dev-only endpoint:
- `POST /api/v1/auth/dev-token`
- Enabled only when `DEBUG=True` and `DEV_JWT_AUTO_ISSUE=True`

Related settings in `.env`:
- `DEV_JWT_AUTO_ISSUE=true`
- `DEV_JWT_DEFAULT_SUBJECT=user-local`
- `DEV_JWT_DEFAULT_ROLES=editor,reviewer,publisher`
- `DEV_JWT_TTL_MINUTES=480`

## Operations automation
- Local run quickstart: `../docs/testing/local-run-quickstart.md`
- Console usage steps: `../docs/testing/console-usage-steps.md`
- CI workflow: `../.github/workflows/ci.yml`
- Security workflow: `../.github/workflows/security.yml`
- Release workflow: `../.github/workflows/release.yml`
- Deployment checklist: `../docs/architecture/deployment-operations-checklist.md`
- First user testing pack: `../docs/testing/first-user-testing-pack.md`
- Day 1 execution sheet: `../docs/testing/day-1-execution-sheet.md`
- Pilot feedback template: `../.github/ISSUE_TEMPLATE/pilot-feedback.yml`
