# Console Usage Steps

This guide describes the operator flow in the FAQ-first and Evidence-grounded Q&A Console.

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
- API base URL in the UI is `/api/v1`
- a valid JWT token is pasted into `JWT Bearer Token`

## 2-minute smoke test
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

## Step 1. Connect
In the `Connection` panel:
- confirm `API Base URL` is `/api/v1`
- paste JWT token into `JWT Bearer Token`

Expected result:
- buttons become usable (not disabled by missing token)

## Step 2. Run question orchestration
In the `Ask Question` panel:
- keep or edit the sample question
- set `Session ID` and `User ID`
- choose one or more `Standards Scope` values
- click `Run Orchestration`

Expected result:
- `Answer Result` card appears
- confidence and citations are shown
- trace includes a `questionEventId`

## Step 3. Route answer to editorial queue
In `Editorial Routing`:
- choose `Reason` and `Priority`
- click `Queue for Editorial`

Expected result:
- `Editorial Queue Result` appears with a `queueItemId`
- `queueItemId` is copied into the `Editorial Transition` input

## Step 4. Load editorial board
In `Editorial Board`:
- optionally set filters (`Status`, `Reason`, `Priority`, `Search`, `pageSize`)
- click `Load Board`

Expected result:
- board table appears with rows
- each row shows status, priority, reason, question, request id, queue item id
- row action buttons reflect role-based `allowedActions`

## Step 5. Apply transition
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

## Step 6. Load KPI metrics
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

## Step 7. Load promotion candidates
In `Promotion Candidates`:
- set `windowDays`, `minCount`, and `onlyUnresolved`
- click `Load Candidates`

Expected result:
- candidates list appears for FAQ curation decisions

## Recommended operator sequence
For first-user testing, use this order:
1. Connect with token
2. Run Orchestration
3. Queue for Editorial
4. Load Board
5. Apply transition
6. Load Metrics
7. Load Candidates

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
