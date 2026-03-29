# First User Testing Pack

Context date: 2026-03-28

## Objective
Run a controlled first-user pilot to validate FAQ-first accuracy, RAG fallback safety, editorial workflow usability, and operational readiness.

## Pilot scope
- Product surfaces:
  - Web GUI Chat Session, Editorial Board, and QnA flow
  - API endpoints in `/api/v1/*`
- Standards focus:
  - NeTEx primary
  - SIRI and OJP/OpRa secondary
- User roles to test:
  - viewer
  - editor
  - reviewer
  - publisher
  - admin (ops observer)

## Entry criteria (must be complete before Day 1)
- Shared pilot environment is reachable over HTTPS.
- Backend health probes return OK:
  - `GET /api/v1/health/live`
  - `GET /api/v1/health/ready`
- Content index is prebuilt from the approved repository snapshot.
- Any supplementary explanatory repositories are allow-listed and indexed if used in pilot scope.
- Role accounts are provisioned and credentials distributed.
- Feedback channel is available via GitHub Issues template.

## Required test accounts
- `pilot-viewer-01` role: viewer
- `pilot-editor-01` role: editor
- `pilot-reviewer-01` role: reviewer
- `pilot-publisher-01` role: publisher
- `pilot-admin-01` role: admin

## Seed data checklist
- At least 20 indexed source chunks from NeTEx.
- If supplementary documentation is enabled, at least one companion repository is indexed with traceable provenance.
- At least 5 questions known to map to FAQ mode.
- At least 5 unknown questions that should trigger RAG mode.
- At least 3 low-confidence/policy-review outcomes queued for editorial board.

## Current implementation notes
- Chat-style UX is available in the frontend and preserves turn history inside the active browser session.
- Backend answer generation supports:
  - `deterministic-grounded` mode
  - `llm-ready` mode with safe deterministic fallback if provider config is missing or fails
- Citations remain grounded in indexed repository chunks with repository URL, commit SHA, source path, and chunk ID.

## Scenario matrix

### S0 Chat session continuity
- Role: viewer
- Action:
  - Ask two related questions in the `Chat Session` panel using the same `Session ID`.
- Expected:
  - both turns remain visible in session history
  - each assistant turn includes citations and request id
- Pass criteria:
  - chat history remains readable and traceable across multiple turns

### S1 FAQ hit path
- Role: viewer
- Action:
  - Submit a known NeTEx FAQ-style question.
- Expected:
  - `mode=faq`
  - `abstained=false`
  - citations present
  - trace includes `questionEventId`
- Pass criteria:
  - response in <= 5 seconds
  - answer and citations are coherent and relevant

### S2 RAG fallback path
- Role: viewer
- Action:
  - Submit an unknown OJP/OpRa question.
- Expected:
  - `mode=rag`
  - citations present
  - retrieval trace IDs present
- Pass criteria:
  - grounded answer references approved source

### S2b LLM-ready fallback safety
- Role: viewer or admin
- Action:
  - Select `llm-ready` generation profile without valid provider configuration, or simulate provider failure.
- Expected:
  - response still succeeds using deterministic fallback
  - citations and trace remain present
- Pass criteria:
  - no unhandled error is shown to the user
  - grounded answer still respects evidence boundary

### S3 Safe abstention path
- Role: viewer
- Action:
  - Submit a question outside indexed evidence scope.
- Expected:
  - `mode=abstain`
  - `abstained=true`
  - abstention reason populated
- Pass criteria:
  - no fabricated claims

### S4 Editorial queue routing
- Role: editor
- Action:
  - Route a question outcome to editorial queue.
- Expected:
  - queue item created
  - status and reason reflect routing input
- Pass criteria:
  - queue item visible on Editorial Board

### S5 Role-aware board actions
- Role: viewer then reviewer
- Action:
  - Load Editorial Board as viewer and reviewer.
- Expected:
  - viewer sees no allowed actions
  - reviewer sees only valid review actions for item status
- Pass criteria:
  - allowed actions match role policy

### S6 Transition workflow path
- Role: editor, reviewer, publisher
- Action:
  - draft -> review -> approved -> published
- Expected:
  - each transition succeeds only for allowed role
  - transition audit entries are created
- Pass criteria:
  - invalid role/status transitions return errors

### S7 KPI metrics sanity
- Role: admin or reviewer
- Action:
  - Load KPI metrics with custom `windowDays` and `slaHours`.
- Expected:
  - totals and bucket counts render
  - values are internally consistent
- Pass criteria:
  - KPI widgets load in <= 3 seconds

### S8 Operational readiness
- Role: admin
- Action:
  - Check liveness/readiness before and during test window.
- Expected:
  - live stays `ok`
  - ready stays `ok`
- Pass criteria:
  - no sustained readiness failures during pilot

## Exit criteria for first-user testing
- >= 90% scenarios pass on first run.
- No critical-severity defects open.
- No trust/safety regressions observed.
- Editorial workflow role behavior validated by at least one user per role.

## Defect severity model
- Critical: trust/safety break, security break, data corruption, complete blocker.
- High: core path broken for one or more roles, no workaround.
- Medium: degraded UX or intermittent failures with workaround.
- Low: cosmetic, copy, non-blocking usability issue.

## Reporting format
For every scenario execution, capture:
- Scenario ID
- User role
- Request ID(s)
- Observed mode/status
- Pass or fail
- Notes and screenshots

## Day 1 recommendation
- Run S0-S4 in first 60 minutes.
- Run S5-S7 and S2b in second 60 minutes.
- Use final 30 minutes for triage and go/no-go recommendation.
