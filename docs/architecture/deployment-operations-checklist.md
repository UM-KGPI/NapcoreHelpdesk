# Deployment and Operations Checklist

This checklist closes the operations hardening loop for production readiness.

## Health checks
- Liveness endpoint: `GET /api/v1/health/live`
- Readiness endpoint: `GET /api/v1/health/ready`
- Configure load balancer and orchestrator probes against these endpoints.

## Release process
- Tag-based release automation is in `.github/workflows/release.yml`.
- Manual release is supported via `workflow_dispatch`.
- Release outputs include:
  - frontend production build,
  - generated docs and presentation artifacts,
  - packaged source bundle.

## Security gates
- Scheduled and PR security checks are in `.github/workflows/security.yml`.
- Backend dependencies are audited via `pip-audit`.
- Frontend dependencies are audited via `npm audit --audit-level=high`.

## Database readiness
- Follow [postgresql-pgvector-runbook.md](postgresql-pgvector-runbook.md).
- Verify pgvector extension and index health after migrations.

## Deployment environment configuration
- Do not commit a production `.env` file.
- Keep [backend/.env.example](../../backend/.env.example) as the template for required keys and fill real values only on the deployment server or in the secret manager.
- At minimum, provide `DJANGO_SECRET_KEY`, `JWT_SECRET_KEY`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`.
- Set `DJANGO_DEBUG=False` and a production `DJANGO_ALLOWED_HOSTS` list before exposing the service.
- Add optional values such as `GITHUB_API_TOKEN`, `LLM_*`, `GRAPHDB_*`, and `INDEX_SCHEDULE_*` only when the deployment uses those integrations.
- Prefer environment injection from Compose, systemd, Kubernetes, or a managed secret store over copying developer-local `.env` files.

### Concrete server patterns
- Docker Compose: keep a server-local env file outside the repo and pass it with `--env-file` or the Compose `env_file` setting; mount only the values needed for that deployment.
- systemd: store secrets in an `EnvironmentFile=` path owned by the service user, or define them in a drop-in under `/etc/systemd/system/<service>.service.d/`.
- Kubernetes: map non-secret values with a ConfigMap and secret values with a Secret, then expose them to the backend container as environment variables.
- In every case, rotate any key that was ever present in a local developer `.env` before using the same deployment identity in production.

## Retrieval quality benchmark
Run after any change to indexing, scoring weights, ontology expansion, or graph-RAG settings.

**Full benchmark (baseline vs graph-RAG comparison):**
```bash
cd backend && ../.venv/bin/python manage.py run_retrieval_benchmark \
  --top-k 20 \
  --output docs/testing/benchmark-report.json
```

**Cross-standard subset only (faster smoke check, ~15 questions):**
```bash
cd backend && ../.venv/bin/python manage.py run_retrieval_benchmark \
  --tags cross-standard \
  --top-k 20 \
  --output docs/testing/benchmark-report.json
```

**Reading the report:**
- `aggregate.baseline.hit_at_10`: fraction of questions where the right source appeared in top-10 (baseline mode).
- `aggregate.graph.hit_at_10`: same metric in graph-RAG mode.
- `aggregate.delta.hit_at_10_delta`: improvement (positive = graph-RAG better).
- `aggregate.delta.latency_overhead_ms`: mean extra latency added by graph expansion.

**P4 success targets:**
- `hit_at_10` delta ≥ +0.10 relative to baseline.
- `mrr_at_10` delta ≥ 0.00 (no regression).
- Latency overhead ≤ +15% of baseline latency.

**Question set location:** `docs/testing/benchmark-questions.yaml` (100 questions, 7 groups: OpRa delay, OpRa capacity, OpRa service intensity, NeTEx timetable, NeTEx network, cross-standard, abstention).

## Operational runbook cadence
- Weekly: review security workflow results and unresolved advisories.
- Per release: run release workflow and verify artifact integrity.
- Per incident: export editorial queue metrics and correlate with health probe status.
- After graph/ontology changes: run full retrieval benchmark and compare report against P4 targets.
