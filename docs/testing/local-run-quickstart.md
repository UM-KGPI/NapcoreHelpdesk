# Local Run Quickstart

This is the single entry-point guide for running and testing NAPCORE Helpdesk locally.

## Recommended local mode
Use SQLite first for the fastest local functional check.

Why:
- minimal setup
- no PostgreSQL dependency
- enough to verify frontend, backend, auth, editorial workflow, KPIs, and first-user testing scenarios

## Prerequisites
- Python virtual environment already available at `.venv/`
- Node.js and npm installed
- Repository root opened in VS Code

## 1. Backend local environment
The local SQLite environment file is already prepared at:
- `backend/.env`

Important active setting:
- `DJANGO_USE_SQLITE=True`

Current source setup can include multiple allow-listed repositories, for example:
- `https://github.com/NeTEx-CEN/NeTEx`
- `https://github.com/NeTEx-CEN/test-Profile-Documentation`

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
- `http://localhost:5173/operator`

## 5. Get a local JWT token
Preferred local mode:
- open `http://localhost:5173/user` or `http://localhost:5173/operator`
- keep `auto-create dev JWT on page reload` enabled in the shared `Connection` panel
- reload once if needed; frontend will call `POST /api/v1/auth/dev-token`

Manual fallback:

```bash
cd backend
DJANGO_USE_SQLITE=True ../.venv/bin/python manage.py shell -c "import jwt, datetime as dt; from django.conf import settings; now=dt.datetime.now(dt.timezone.utc); print(jwt.encode({'sub':'local-user','roles':['admin'],'iat':int(now.timestamp()),'exp':int((now+dt.timedelta(hours=8)).timestamp())}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))"
```

Use the printed token in the shared frontend field:
- `JWT Bearer Token`

## 6. First functional checks
In the frontend:
- confirm the shared `Connection` panel already contains a JWT or paste one manually
- use default API base URL: `/api/v1`
- run these checks:
  - Open `/user`, send one message, and confirm turn history with citations
  - Open `/operator`, ask a known FAQ question
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
4. Open `/operator`.
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

## 8. Optional LLM-ready mode
To enable provider-backed generation in `Chat Session`:

1. Edit `backend/.env` and set:
  - `LLM_ENABLED=True`
  - `LLM_API_KEY=<your key>`
  - optionally override `LLM_API_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`
2. Restart backend.
3. In frontend `/user`, choose `llm-ready` as `Generation Profile`.

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

## 10. When to switch to PostgreSQL
Switch from SQLite to PostgreSQL when:
- local flow is already working
- you want production-like validation
- you want to verify pgvector path, release workflow, and deployment posture

PostgreSQL runbook:
- `docs/architecture/postgresql-pgvector-runbook.md`

## 11. Related docs
- `backend/README.md`
- `frontend/README.md`
- `docs/architecture/deployment-operations-checklist.md`
