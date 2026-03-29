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

## 5. Generate a local JWT token
Open a third terminal:

```bash
cd backend
DJANGO_USE_SQLITE=True ../.venv/bin/python manage.py shell -c "import jwt, datetime as dt; from django.conf import settings; now=dt.datetime.now(dt.timezone.utc); print(jwt.encode({'sub':'local-user','roles':['admin'],'iat':int(now.timestamp()),'exp':int((now+dt.timedelta(hours=8)).timestamp())}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))"
```

Use the printed token in the frontend field:
- `JWT Bearer Token`

## 6. First functional checks
In the frontend:
- paste JWT token
- use default API base URL: `/api/v1`
- run these checks:
  - Ask a known FAQ question
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
3. Paste a valid JWT token.
4. Click `Load Metrics` in `Editorial Board`.
5. Click `Load Board` in `Editorial Board`.
6. In `Ask Question`, click `Run Orchestration` with default values.

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

## 8. First-user testing pack
Console usage steps:
- `docs/testing/console-usage-steps.md`

Scenario guide:
- `docs/testing/first-user-testing-pack.md`

Live worksheet:
- `docs/testing/day-1-execution-sheet.md`

Feedback template:
- `.github/ISSUE_TEMPLATE/pilot-feedback.yml`

## 9. When to switch to PostgreSQL
Switch from SQLite to PostgreSQL when:
- local flow is already working
- you want production-like validation
- you want to verify pgvector path, release workflow, and deployment posture

PostgreSQL runbook:
- `docs/architecture/postgresql-pgvector-runbook.md`

## 10. Related docs
- `backend/README.md`
- `frontend/README.md`
- `docs/architecture/deployment-operations-checklist.md`
