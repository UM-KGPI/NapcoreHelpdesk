# PostgreSQL + pgvector Deployment Runbook

## Purpose
This runbook describes how to deploy and verify the PostgreSQL + pgvector backend baseline for NAPCORE Helpdesk.

## Scope
- Backend database setup
- Migration execution order
- pgvector extension verification
- Retrieval index and query-path validation

## Prerequisites
1. PostgreSQL 16+ instance reachable from backend runtime.
2. pgvector extension package available on the database host.
3. Application environment values configured in `backend/.env`:
- `DJANGO_USE_SQLITE=False`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## Deployment Steps
1. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate --noinput
```

3. Confirm migration `0006_pgvector_native_alignment` was applied:
```bash
python manage.py showmigrations helpdesk | grep 0006
```
Expected: `[X] 0006_pgvector_native_alignment`

## Database Verification
1. Confirm pgvector extension exists:
```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```
Expected: one row with `vector`.

2. Confirm IVF Flat vector index exists:
```sql
SELECT indexname
FROM pg_indexes
WHERE tablename = 'helpdesk_sourcechunk'
  AND indexname = 'sourcechunk_embedding_ivfflat_idx';
```
Expected: one row with `sourcechunk_embedding_ivfflat_idx`.

3. Confirm `embedding_vector` column exists:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'helpdesk_sourcechunk'
  AND column_name = 'embedding_vector';
```

## Application Verification
1. Build retrieval index from an allowlisted repository:
```bash
python manage.py build_source_index \
  --repo-url https://github.com/TransmodelEcosystem/NeTEx \
  --repo-path /absolute/path/to/NeTEx \
  --profile netex \
  --incremental \
  --prune
```

2. Run backend tests against PostgreSQL:
```bash
python manage.py test -v 1
```

3. Smoke test answer endpoint with auth + request ID and verify:
- non-empty `trace.retrievalEventIds` on RAG path
- non-empty `trace.evidenceLinkIds` when citations exist

## Rollback
1. Roll back one migration step if required:
```bash
python manage.py migrate helpdesk 0005
```
2. Drop vector index manually if needed:
```sql
DROP INDEX IF EXISTS sourcechunk_embedding_ivfflat_idx;
```

## Operational Notes
- SQLite remains supported for local development and tests when `DJANGO_USE_SQLITE=True`.
- PostgreSQL path is the production baseline and should be used in staging/prod CI gates.
- If retrieval latency grows, tune IVF list count and PostgreSQL planner settings per workload.
- Index artifact cleanup rules are enforced globally in the index builder (not only per-profile), so current and future repository profiles automatically exclude temporary/generated paths.

## Next-Session Quickstart (Local Baseline)
1. Verify backend is in PostgreSQL mode:
```bash
cd backend
grep '^DJANGO_USE_SQLITE=' .env
```
Expected: `DJANGO_USE_SQLITE=False`

2. Verify helpdesk migration chain:
```bash
../.venv/bin/python manage.py showmigrations helpdesk | grep '0006\|0007\|0008\|0009'
```
Expected: all listed migrations are marked `[X]`.

3. Ensure least-privilege local test posture:
- Role `napcore` should have `CREATEDB`.
- Role `napcore` should **not** require `SUPERUSER`.
- Test DB creation should inherit pgvector from template1 via `DATABASES["default"]["TEST"]["TEMPLATE"] = "template1"` in settings.

4. Re-index allowlisted repositories:
```bash
cd ..
make backend-index REPO_URL=https://github.com/TransmodelEcosystem/NeTEx REPO_PATH=/absolute/path/to/NeTEx PROFILE=netex INCREMENTAL=1
make backend-index REPO_URL=https://github.com/OpRa-CEN/OpRa REPO_PATH=/absolute/path/to/OpRa PROFILE=opra INCREMENTAL=1
```

5. Run focused backend verification:
```bash
cd backend
../.venv/bin/python manage.py test helpdesk.tests.test_api helpdesk.tests.test_index_builder helpdesk.tests.test_policy_guard
```
