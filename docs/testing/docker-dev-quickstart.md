# Docker Development Quickstart

Run the development stack with Docker Compose.

Two supported modes:
- Embedded PostgreSQL mode: app + PostgreSQL in one compose stack.
- Shared PostgreSQL mode: one independent PostgreSQL container reused by multiple applications.

## Prerequisites
- Docker Engine with Docker Compose v2
- Ports free on localhost: `5173`, `8000`, `5432`, `6379`
- Also requires port `7200` for GraphDB

## Start stack
From repository root:

```bash
make docker-dev-up
```

This starts:
- Frontend (Vite): `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL (pgvector): `localhost:5432`
- Redis: `localhost:6379`
- GraphDB: `http://localhost:7200`
- Celery worker + beat

GraphDB repository bootstrap and ontology load are executed by the backend startup command.
If you need to run them manually, use:

```bash
make graphdb-init
make graphdb-load
```

## Shared PostgreSQL mode (single independent DB container)
Use this mode when multiple application stacks should share one PostgreSQL instance.

1. Start shared PostgreSQL once:

```bash
make shared-postgres-up
```

2. Bootstrap one application DB/user (run once per app):

```bash
APP_DB=napcore_helpdesk APP_USER=napcore APP_PASSWORD=napcore make shared-postgres-bootstrap-app
```

3. Start application services against external PostgreSQL:

```bash
make docker-dev-up-external-postgres
```

4. Optional explicit host/port overrides:

```bash
POSTGRES_HOST=host.docker.internal POSTGRES_PORT=5432 make docker-dev-up-external-postgres
```

5. Multi-app shared DB naming example (same PostgreSQL instance, separate databases):

```bash
# App A (this project)
APP_DB=napcore_helpdesk APP_USER=napcore APP_PASSWORD=napcore make shared-postgres-bootstrap-app
POSTGRES_HOST=host.docker.internal POSTGRES_PORT=5432 \
POSTGRES_DB=napcore_helpdesk POSTGRES_USER=napcore POSTGRES_PASSWORD=napcore \
make docker-dev-up-external-postgres

# App B (another stack)
APP_DB=other_app_db APP_USER=other_app APP_PASSWORD=change-me make shared-postgres-bootstrap-app
POSTGRES_HOST=host.docker.internal POSTGRES_PORT=5432 \
POSTGRES_DB=other_app_db POSTGRES_USER=other_app POSTGRES_PASSWORD=change-me \
docker compose -f /path/to/other-app/docker-compose.yml up -d
```

Notes:
- In shared mode, the app stack does not start the embedded `db` service.
- Stop local host PostgreSQL services (for example Homebrew) to avoid port conflicts with shared Docker PostgreSQL.
- Create each application database/user once in the shared PostgreSQL instance before first startup.
- Audit existing shared databases/users anytime with `make shared-postgres-audit`.

## Stop stack

```bash
make docker-dev-down
```

To stop shared PostgreSQL:

```bash
make shared-postgres-down
```

## Live logs

```bash
make docker-dev-logs
```

## Configuration notes
- Frontend proxy target is container-aware via `VITE_BACKEND_ORIGIN` and set to `http://backend:8000` in Compose.
- Backend, Celery worker, and Celery beat are configured for:
  - `POSTGRES_HOST=db`
  - `CELERY_BROKER_URL=redis://redis:6379/0`
  - `CELERY_RESULT_BACKEND=redis://redis:6379/1`
- In shared PostgreSQL mode, `POSTGRES_HOST` defaults to `host.docker.internal` via `docker-compose.external-postgres.yml`.
- LLM and embedding environment variables are optional. They can be injected from shell environment before running Compose.

## Quick health checks
- Backend liveness: `http://localhost:8000/api/v1/health/live`
- Backend readiness: `http://localhost:8000/api/v1/health/ready`
- Frontend: `http://localhost:5173/user`
