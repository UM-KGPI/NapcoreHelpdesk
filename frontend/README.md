# Frontend Web GUI (React + TypeScript + Vite)

This folder contains the C4 Web GUI container for NAPCORE Helpdesk.

## Features in current slice
- Ask questions via `POST /api/v1/questions/answer`.
- Inspect answer mode, confidence, citations, and trace IDs.
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

3. Build for production check:

   `npm run build`

## API expectations
- Backend default base URL is `http://localhost:8000/api/v1`.
- Endpoints require a JWT bearer token.
- `POST /questions/answer` also requires `X-Request-Id` (auto-generated in UI).