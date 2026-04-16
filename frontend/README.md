# Frontend Web GUI (React + TypeScript + Vite)

This folder contains the C4 Web GUI container for NAPCORE Helpdesk.

## Features in current slice
- Route-based split UX: `/user` for chat and `/operator` for editorial/orchestration console.
- Shared connection shell with route switcher and common JWT/API configuration.
- Chat-style session UX with multi-turn history, per-turn evidence, and request IDs.
- `Generation Profile` selector for deterministic grounded mode and LLM-ready backend mode.
- Ask questions via `POST /api/v1/questions/answer`.
- Inspect answer mode, confidence, citations, and trace IDs.
- Inspect semantic trace signals in answers (provisional evidence, conflict flags, and cross-standard evidence partitions).
- Route current answer to editorial queue via `POST /api/v1/editorial/queue`.
- Apply editorial workflow transitions via `POST /api/v1/editorial/queue/transition`.
- List/filter editorial queue board items via `GET /api/v1/editorial/queue`.
- Show role-aware `allowedActions` from API and perform only permitted inline transitions.
- Load board KPI metrics (status distribution, aging, overdue) via `GET /api/v1/editorial/queue/metrics`.
- Load FAQ promotion candidates via `GET /api/v1/faqs/promotion-candidates`.

## Local usage
1. Install dependencies:

   `npm install`

2. Start dev server:

   `npm run dev`

3. Run frontend tests:

   `npm run test`

4. Build for production check:

   `npm run build`

## Demo routes
- `http://localhost:5173/user` for the user-facing chat surface.
- `http://localhost:5173/operator` for the operator console surface.
- `http://localhost:5173/` redirects to `/user`.

## API expectations
- Backend default base URL in local dev is `/api/v1` via Vite proxy to `http://localhost:8000/api/v1`.
- Endpoints require a JWT bearer token.
- `POST /questions/answer` also requires `X-Request-Id` (auto-generated in UI).
- Health probes are available without auth: `GET /health/live`, `GET /health/ready`.

Local auth convenience in the UI:
- JWT token is persisted in browser localStorage.
- `auto-create dev JWT on page reload` is enabled by default.
- When enabled and token is empty, frontend calls `POST /api/v1/auth/dev-token` and auto-fills the bearer token.
- If the dev-token endpoint is disabled, manual token paste still works.
- The shared connection panel applies to both `/user` and `/operator` routes.

`POST /questions/answer` accepts:
- `sessionId`
- `userId`
- `standardsScope`
- `generationProfile` (`deterministic-grounded` or `llm-ready`)

Current backend behavior:
- `deterministic-grounded` is always available.
- `llm-ready` works when backend `LLM_ENABLED=True`; otherwise the backend falls back safely.

## Pilot operations
- Local run quickstart: `../docs/testing/local-run-quickstart.md`
- Console usage steps: `../docs/testing/console-usage-steps.md`
- Scenario matrix and acceptance criteria: `../docs/testing/first-user-testing-pack.md`
- Live session worksheet: `../docs/testing/day-1-execution-sheet.md`
- Feedback issue form: `../.github/ISSUE_TEMPLATE/pilot-feedback.yml`