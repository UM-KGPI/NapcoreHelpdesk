# Contributing

Thanks for contributing to NAPCORE Helpdesk.

## Development flow

1. Create a feature branch from `main`.
2. Keep changes focused (small, targeted commits).
3. Run relevant checks locally.
4. Open a PR with a clear summary and testing notes.

## Commit style

Use concise, scoped commit messages. Examples:

- `feat(api): add stable citation links`
- `fix(retrieval): guard graph fallback path`
- `docs: consolidate top-level documentation`

## Local checks

Run from repository root:

```bash
make backend-check
make frontend-test
make frontend-build
```

For API contract changes:

```bash
make openapi-validate
```

For indexing or retrieval-sensitive changes, run focused backend tests:

```bash
cd backend
../.venv/bin/python manage.py test helpdesk.tests.test_api helpdesk.tests.test_index_builder helpdesk.tests.test_policy_guard
```

## Version automation

This repository now supports both build-based and commit-based version automation.

- Build-based versioning (recommended):
	- Keep `VERSION` as release SemVer.
	- Build metadata is generated from git history.
	- Use `make version-print` to inspect computed values.
	- `make frontend-build` now injects a computed app version automatically.
	- `make backend-run` now sets `SERVICE_BUILD_REF` automatically.

- Commit-based bumping (optional):
	- Install repository hooks once: `make hooks-install`
	- After that, each commit bumps `VERSION` patch unless `VERSION` is already staged.
	- Bypass for one commit with `SKIP_AUTO_VERSION=1 git commit ...`.

- Merge-based bumping (GitHub Actions):
	- On merge to `main`, `.github/workflows/version-bump-on-merge.yml` updates `VERSION` automatically.
	- Label PR with one of: `version:major`, `version:minor`, `version:patch`.
	- If no version label is present, it defaults to a `patch` bump.

Manual bump helpers:

- `make version-bump-patch`
- `make version-bump-minor`
- `make version-bump-major`

## Documentation requirements

When changing behavior, update docs in the same PR:

- Public overview or usage: `README.md`
- Developer workflow: `CONTRIBUTING.md`
- Detailed documentation map: `docs/README.md`
- Architecture changes: `docs/architecture/*`
- Operations/testing changes: `docs/testing/*`

## API and frontend contract alignment

If backend API shape changes:

- Update `api/openapi.yaml`
- Keep frontend contracts aligned (`frontend/src/types.ts`, `frontend/src/api.ts`)

## Secrets policy

- Never commit real secrets.
- Keep local tokens in ignored `.env` files.
- Use repository or CI secret stores for shared environments.
- Rotate exposed tokens immediately.

## Useful references

- [Documentation index](docs/README.md)
- [Make targets reference](docs/testing/make-targets-reference.md)
- [Local run quickstart](docs/testing/local-run-quickstart.md)
