# Local Run Quickstart

This is the single entry-point guide for running and testing NAPCORE Helpdesk locally.

## Recommended local mode
The local runtime uses PostgreSQL with pgvector. SQLite is no longer the default.

Prerequisites for PostgreSQL mode:
- PostgreSQL running locally with the `vector` extension available
- Database `napcore_helpdesk` created with user `napcore` (see `backend/.env`)
- pgvector enabled (superuser or pre-installed extension — see `docs/architecture/postgresql-pgvector-runbook.md`)

## Prerequisites
- Python virtual environment already available at `.venv/`
- Node.js and npm installed
- Repository root opened in VS Code

## 1. Backend local environment
The environment file is at:
- `backend/.env`

Active settings:
- `DJANGO_USE_SQLITE=False` — PostgreSQL mode
- `LLM_ENABLED=True` — grounded generation via LLM provider
- `POSTGRES_DB=napcore_helpdesk`, `POSTGRES_USER=napcore`, `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432`

Allow-listed source repositories:
- `https://github.com/NeTEx-CEN/NeTEx`
- `https://github.com/NeTEx-CEN/test-Profile-Documentation`
- `https://github.com/OpRa-CEN/OpRa`
- `https://github.com/hfjelstad/Profile_Documentation_v2`

## 2. Apply backend migrations
From repository root:

```bash
make backend-migrate
```

## 3. Start backend
From repository root:

```bash
make backend-run
```

If startup fails with `Error: That port is already in use.`, clear stale local runserver processes and retry:

```bash
# show who is listening on 8000
lsof -nP -iTCP:8000 -sTCP:LISTEN

# stop any stale Django runserver chain
pkill -f "manage.py runserver" || true

# confirm port is free
lsof -nP -iTCP:8000 -sTCP:LISTEN || true

# start backend again
make backend-run
```

If a specific PID still appears, stop it directly and retry:

```bash
kill <PID>
```

Backend URL:
- `http://localhost:8000`

Health checks:
- `http://localhost:8000/api/v1/health/live`
- `http://localhost:8000/api/v1/health/ready`

## 4. Start frontend
Open a second terminal from repository root:

```bash
make frontend-install
make frontend-dev
```

Frontend URL:
- `http://localhost:5173`
- `http://localhost:5173/user`
- `http://localhost:5173/editor`

## 5. Get a local JWT token
Preferred local mode:
- open `http://localhost:5173/user` or `http://localhost:5173/editor`
- keep `auto-create dev JWT on page reload` enabled in the shared `Connection` panel
- reload once if needed; frontend will call `POST /api/v1/auth/dev-token`

Manual fallback:

```bash
cd backend
../.venv/bin/python manage.py shell -c "import jwt, datetime as dt; from django.conf import settings; now=dt.datetime.now(dt.timezone.utc); print(jwt.encode({'sub':'local-user','roles':['admin'],'iat':int(now.timestamp()),'exp':int((now+dt.timedelta(hours=8)).timestamp())}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))"
```

Use the printed token in the shared frontend field:
- `JWT Bearer Token`

## 6. First functional checks
In the frontend:
- confirm the shared `Connection` panel already contains a JWT or paste one manually
- use default API base URL: `/api/v1`
- run these checks:
  - Open `/user`, send one message, and confirm turn history with citations
  - Open `/editor`, ask a known FAQ question
  - Load Editorial Board
  - Load KPI metrics
  - Route an item to editorial queue
  - Apply a transition

Note:
- In local Vite dev mode, `/api/v1` is proxied to `http://localhost:8000/api/v1` to avoid browser CORS preflight failures.

### 2-minute smoke test
Use this for a fast go/no-go check.

1. Open `http://localhost:5173`.
2. Confirm `API Base URL` is `/api/v1`.
3. Confirm `JWT Bearer Token` is present or wait for auto-create to fill it.
4. Open `/editor`.
5. Click `Load Metrics` in `Editorial Board`.
6. Click `Load Board` in `Editorial Board`.
7. In `Ask Question`, click `Run Orchestration` with default values.

Pass criteria:
- no `Load failed` banner appears
- KPI tiles render values
- board response renders rows or a valid empty-state message
- answer response renders with trace and citations section

## 7. Optional quality checks
From repository root:

```bash
make frontend-test
make frontend-build
cd backend && ../.venv/bin/python manage.py test -v 1
```

## 8. LLM-ready mode
LLM-backed generation is enabled by default (`LLM_ENABLED=True` in `backend/.env`).

Active configuration:
- `LLM_PROVIDER=openai-compatible`
- `LLM_API_BASE_URL=https://models.inference.ai.azure.com`
- `LLM_MODEL=gpt-4o-mini`
- `LLM_TIMEOUT_SECONDS=20`, `LLM_MAX_TOKENS=500`, `LLM_TEMPERATURE=0.2`

To use a different provider, update `LLM_API_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` in `backend/.env` and restart backend.

In frontend `/user`, select `llm-ready` as `Generation Profile` to use the LLM path.

If provider configuration is missing or the request fails, backend falls back to deterministic grounded generation.

## 9. First-user testing pack
Console usage steps:
- `docs/testing/console-usage-steps.md`

Scenario guide:
- `docs/testing/first-user-testing-pack.md`

Live worksheet:
- `docs/testing/day-1-execution-sheet.md`

Feedback template:
- `.github/ISSUE_TEMPLATE/pilot-feedback.yml`

## 10. PostgreSQL and pgvector
The local runtime runs on PostgreSQL with pgvector. For setup, troubleshooting, and production deployment guidance:
- `docs/architecture/postgresql-pgvector-runbook.md`

Migration chain that must be present:
- `0006_pgvector_native_alignment`
- `0007_alter_sourcechunk_embedding_vector`
- `0008_sourcechunk_embedding_dimension_1536`
- `0009_create_sourcechunk_vector_index`

Verify with:
```bash
cd backend && ../.venv/bin/python manage.py showmigrations helpdesk | grep '0006\|0007\|0008\|0009'
```

## 11. GraphDB semantic layer (optional, required for GraphDB-backed graph expansion)
Graph-aware retrieval can run with in-memory fallback, but GraphDB-backed ontology expansion requires explicit configuration.

Prerequisites for the reproducible local path:
- Docker Engine and `docker-compose` available on your PATH
- Port `7200` free on localhost

Set in `backend/.env`:
- `GRAPHDB_ENABLED=True`
- `GRAPHDB_SPARQL_ENDPOINT=http://localhost:7200`
- `GRAPHDB_REPOSITORY=napcore-helpdesk`
- `GRAPHDB_USER=` and `GRAPHDB_PASSWORD=` if your GraphDB requires auth
- Keep `GRAPH_RAG_ENABLED=True` for graph-aware retrieval mode
- Keep `NEO4J_EXPERIMENTAL_ENABLED=False` unless you are intentionally testing the experimental Neo4j branch

Start local GraphDB from repository root:

```bash
make graphdb-up
make graphdb-init
```

This uses:
- `docker-compose.graphdb.yml` to run GraphDB Workbench on `http://localhost:7200`
- `scripts/init-graphdb-repo.sh` to create repository `napcore-helpdesk` through the GraphDB REST API using the checked-in repository template

Once the repository exists, load ontology files (dry-run first, then apply):

```bash
cd backend
../.venv/bin/python manage.py load_graphdb_ontologies
../.venv/bin/python manage.py load_graphdb_ontologies --apply
```

If you need to replace named graphs during reload:

```bash
cd backend
../.venv/bin/python manage.py load_graphdb_ontologies --apply --replace
```

One-command bootstrap from repository root:

```bash
make graphdb-bootstrap
```

That target starts GraphDB, creates the `napcore-helpdesk` repository if missing, and then reloads all ontology modules including artifact rules with `--replace`.

To verify the live repository matches the current modular ontology registry:

```bash
make graphdb-verify
```

That check asserts the exact expected 13 named graphs are present and will fail if stale legacy graphs remain in the repository.

If Docker is not installed, Graph-aware retrieval still falls back to in-memory ontology mappings, but `load_graphdb_ontologies --apply` will continue to fail until a GraphDB server is reachable at the configured endpoint.

## 12. Related docs
- `backend/README.md`
- `frontend/README.md`
- `docs/architecture/deployment-operations-checklist.md`
- `docs/testing/docker-dev-quickstart.md`
