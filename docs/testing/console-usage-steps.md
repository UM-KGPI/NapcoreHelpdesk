# Console Usage Steps

This guide describes the routed editor flow in the FAQ-first and Evidence-grounded Q&A Console.

## Goal
Use the console to:
- run a grounded answer
- route low-confidence outcomes to editorial queue
- process queue transitions
- monitor queue KPIs
- identify FAQ promotion candidates

## Preconditions
Before running these steps:
- backend is running on `http://localhost:8000`
- frontend is running on `http://localhost:5173`
- editor route is `http://localhost:5173/editor`
- user chat route is `http://localhost:5173/user`
- API base URL in the UI is `/api/v1`
- a valid JWT token is available in the shared `Connection` panel

## Editor Tasks (Ordered UI)
Use the numbered order shown in the editor interface.

1. `1. Ask Question`
2. `2. Editorial Routing`
3. `3. Editorial Board`
4. `4. Editorial Transition`
5. `5. Queue KPIs`
6. `6. Promotion Candidates`
7. `7. Index Repository` (optional operations)

Recommended editorial flow for routine triage:
1. Ask Question
2. Editorial Routing
3. Editorial Board
4. Editorial Transition
5. Queue KPIs

## 2-minute smoke test
Use this for a fast go/no-go check.

1. Open `http://localhost:5173/editor`.
2. Confirm `API Base URL` is `/api/v1`.
3. Confirm a valid JWT token is present.
4. Click `Load Metrics` in `Editorial Board`.
5. Click `Load Board` in `Editorial Board`.
6. In `Ask Question`, click `Run Orchestration` with default values.

Pass criteria:
- no `Load failed` banner appears
- KPI tiles render values
- board response renders rows or a valid empty-state message
- answer response renders with trace and citations section

## Step 1. Connect
In the `Connection` panel:
- confirm `API Base URL` is `/api/v1`
- paste JWT token into `JWT Bearer Token`

Expected result:
- buttons become usable (not disabled by missing token)

## Step 2. Use the separate user chat route
In `http://localhost:5173/user`:
- keep or edit `Session ID` and `User ID`
- select `Generation Profile`:
  - `deterministic-grounded` for current default backend mode
  - `llm-ready` when backend `LLM_ENABLED=True`
- type a message and click `Send`

Expected result:
- conversation history appears with user and assistant turns
- assistant turns include mode, confidence, citations, and request id
- `New Session` resets chat history and rotates session id

Note:
- If `llm-ready` is selected but backend LLM configuration is unavailable or fails, the backend falls back to deterministic grounded generation.

## Step 3. Run question orchestration on the editor route
In `http://localhost:5173/editor`, in the `Ask Question` panel:
- keep or edit the sample question
- set `Session ID` and `User ID`
- choose one or more `Standards Scope` values
- click `Run Orchestration`

Expected result:
- `Answer Result` card appears
- confidence and citations are shown
- trace includes a `questionEventId`

## Step 4. Route answer to editorial queue
In `Editorial Routing`:
- choose `Reason` and `Priority`
- click `Queue for Editorial`

Expected result:
- `Editorial Queue Result` appears with a `queueItemId`
- `queueItemId` is copied into the `Editorial Transition` input

## Step 5. Load editorial board
In `Editorial Board`:
- optionally set filters (`Status`, `Reason`, `Priority`, `Search`, `pageSize`)
- click `Load Board`

Expected result:
- board table appears with rows
- each row shows status, priority, reason, question, request id, queue item id
- row action buttons reflect role-based `allowedActions`

## Step 6. Apply transition
Use one of two methods.

Method A: Inline board actions
- click an action button in the row `Actions` column

Method B: Manual transition form
- paste `queueItemId`
- choose `Action`
- optionally add `Comment`
- click `Apply Transition`

Expected result:
- transition result panel updates
- board reloads with new status

## Step 7. Load KPI metrics
In `Editorial Board` KPI section:
- set `metricsWindowDays` and `metricsSlaHours`
- click `Load Metrics`

Expected result:
- KPI tiles appear:
  - Total
  - Unresolved
  - Overdue
  - By status
  - Aging buckets (`lt24h`, `24to72h`, `gt72h`)

## Step 8. Load promotion candidates
In `Promotion Candidates`:
- set `windowDays`, `minCount`, and `onlyUnresolved`
- click `Load Candidates`

Expected result:
- candidates list appears for FAQ curation decisions

## Recommended editor sequence
For first-user testing, use this order:
1. Connect with token
2. Open `/editor`
3. Use `1. Ask Question`
4. Use `2. Editorial Routing`
5. Use `3. Editorial Board`
6. Use `4. Editorial Transition`
7. Use `5. Queue KPIs`
8. Use `6. Promotion Candidates`

## Troubleshooting
If you see `Load failed`:
- verify backend health endpoint: `http://localhost:8000/api/v1/health/live`
- verify frontend API base URL is `/api/v1` (not direct cross-origin URL)
- regenerate and re-paste JWT token
- retry `Load Board` and `Load Metrics`

If transition buttons are missing:
- your actor role may not allow actions for current status
- inspect `roles` shown above board rows

## Evidence logging for pilot
For each scenario, record:
- request id from answer trace
- queue item id
- transition action taken
- KPI snapshot values after transition

Use the execution worksheet:
- `docs/testing/day-1-execution-sheet.md`
