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

## Operational runbook cadence
- Weekly: review security workflow results and unresolved advisories.
- Per release: run release workflow and verify artifact integrity.
- Per incident: export editorial queue metrics and correlate with health probe status.
