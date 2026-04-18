# First User Testing Pack

Context date: 2026-03-28

## Objective
Run a controlled first-user pilot to validate FAQ-first accuracy, RAG fallback safety, editorial workflow usability, and operational readiness.

## Pilot scope
- Product surfaces:
  - Routed Web GUI user chat at `/user`
  - Routed Web GUI editor console at `/editor`
  - API endpoints in `/api/v1/*`
- Standards focus:
  - NeTEx primary
  - SIRI and OpRa secondary
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
- Frontend is split into two independently addressable routes: `/user` and `/editor`.
- Chat-style UX is available on `/user` and preserves turn history inside the active browser session.
- Editorial board, orchestration, routing, and KPI flows are available on `/editor`.
- Backend answer generation supports:
  - `deterministic-grounded` mode
  - `llm-ready` mode with safe deterministic fallback if provider config is missing or fails
- Citations remain grounded in indexed repository chunks with repository URL, commit SHA, source path, and chunk ID.

## Scenario matrix

### S0 Chat session continuity
- Role: viewer
- Action:
  - Open `/user` and ask two related questions using the same `Session ID`.
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
  - Submit an unknown OpRa question.
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
  - Open `/editor` and route a question outcome to editorial queue.
- Expected:
  - queue item created
  - status and reason reflect routing input
- Pass criteria:
  - queue item visible on Editorial Board

### S5 Role-aware board actions
- Role: viewer then reviewer
- Action:
  - Open `/editor` and load Editorial Board as viewer and reviewer.
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

## FAQ curation rubric (editorial review sheet)
Use this rubric for draft -> review -> approved/published decisions.

### Hard gates (must all pass)
- Answer is grounded in approved GitHub sources only.
- At least one usable citation is attached, and citations support the claim text.
- No uncited legal/compliance claims.
- No contradiction between standards in cross-standard answers.
- If evidence is insufficient, answer must abstain or explicitly state limitation.

If any hard gate fails, mark the item `rejected` or return it to `draft`.

### Weighted scoring (0-100)
Score each dimension from 0 to 5, then multiply by weight.

| Dimension | Weight | 0 score | 3 score | 5 score |
|---|---:|---|---|---|
| Grounding and citation quality | 30 | No citation or unusable citation | Citations partly support answer | All key claims are directly supported and traceable |
| Technical correctness | 25 | Materially wrong | Mostly correct with minor inaccuracies | Correct, precise, and terminology-consistent |
| Scope and source-policy compliance | 15 | Out-of-scope or non-allowlisted source use | Minor scope leakage | Fully within approved standards and source boundary |
| Safety and uncertainty handling | 15 | Hallucinated certainty | Some caveats but incomplete | Clear uncertainty/abstention when evidence is weak |
| Clarity and usefulness | 10 | Hard to understand | Understandable but verbose/ambiguous | Clear, concise, directly answers user intent |
| Editorial readiness | 5 | Needs major rewrite | Needs minor edits | Ready to publish with no substantive edits |

Total score formula:
- `total = sum((dimension_score / 5) * weight)`

### Decision thresholds
- `approved/publish-ready`: total >= 85 and all hard gates pass.
- `review-needed`: total 70-84 and all hard gates pass.
- `rework`: total < 70, or any hard gate fails.

### Reviewer worksheet template
Use this per FAQ candidate:

| Field | Value |
|---|---|
| Candidate ID | |
| Canonical question | |
| Proposed answer version | |
| Reviewer | |
| Review date | |
| Grounding and citation quality (0-5) | |
| Technical correctness (0-5) | |
| Scope and source-policy compliance (0-5) | |
| Safety and uncertainty handling (0-5) | |
| Clarity and usefulness (0-5) | |
| Editorial readiness (0-5) | |
| Hard gates pass (yes/no) | |
| Weighted total (0-100) | |
| Decision (`approved` / `review` / `rework`) | |
| Reviewer notes | |

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

## Two-week pilot execution checklist
This checklist operationalizes first-user testing into a 10-business-day pilot window.

### Roles and ownership
- Pilot lead: schedules sessions, tracks blockers, issues go/no-go recommendation.
- Editor lead: owns curation queue throughput and rubric consistency.
- Reviewer lead: owns quality gates, cross-standard checks, and rejection reasons.
- Publisher lead: owns publication controls and release candidate list.
- Ops lead: owns environment health, indexing stability, and incident response.

### Week 1 (stabilization and baseline)
#### Day 1: Environment and baseline smoke
- Confirm entry criteria and test account access.
- Run scenarios S0-S4 and capture results in reporting format.
- Record baseline metrics:
  - median response time (FAQ mode)
  - median response time (RAG mode)
  - citation attachment rate
  - abstention rate for out-of-scope prompts

#### Day 2: Editorial workflow validation
- Run scenarios S5-S7 with all relevant roles.
- Execute at least 5 rubric-based reviews using the reviewer worksheet.
- Verify all transition audits are present and role-accurate.

#### Day 3: Source-grounding stress pass
- Run 15 mixed questions across NeTEx, OpRa, and SIRI.
- Ensure each non-abstained answer includes citations to approved repositories.
- Create defects for any uncited claim, source-policy leak, or contradiction.

#### Day 4: Safety and abstention tuning
- Run at least 10 intentionally unsupported or ambiguous prompts.
- Confirm safe abstention behavior and clear limitation language.
- Re-test any previously failing safety scenarios.

#### Day 5: Week-1 review gate
- Hold 45-minute triage with pilot leads.
- Required week-1 thresholds:
  - >= 85% scenario pass rate on re-run set
  - 0 critical defects open
  - 100% published candidates pass hard gates in rubric
- Decide: proceed to week 2, or hold for remediation.

### Week 2 (scale and readiness)
#### Day 6: Retrieval coverage expansion
- Run 20 benchmark-style prompts with cross-standard focus.
- Confirm evidence breadth across repositories and concept families.
- Flag recurring retrieval misses for ingestion/indexing backlog.

#### Day 7: Curation throughput day
- Process at least 10 draft FAQ candidates end-to-end.
- Target state distribution:
  - >= 4 approved/publish-ready
  - <= 3 rework due to preventable citation defects
- Verify reviewer notes are specific and actionable.

#### Day 8: Regression and traceability audit
- Re-run all failed scenarios from week 1.
- Sample at least 8 approved answers and verify:
  - citation traceability
  - provenance completeness
  - consistency with source-policy boundary

#### Day 9: Dry-run release candidate
- Build a pilot release set of approved FAQs.
- Validate publication workflow and role permissions.
- Produce release notes summary:
  - number approved
  - key known limitations
  - deferred items with owners

#### Day 10: Final go/no-go review
- Recompute pilot KPIs and compare to week-1 baseline.
- Required final thresholds:
  - >= 90% scenario pass rate (overall)
  - 0 critical defects and <= 3 high defects with approved mitigations
  - citation attachment rate >= 98% for non-abstained answers
  - no uncited legal/compliance assertions
- Deliver recommendation: go, conditional-go, or no-go.

### Pilot deliverables by end of week 2
- Completed scenario execution log with request IDs and outcomes.
- Completed rubric worksheets for reviewed FAQ candidates.
- Defect register with severity, owner, target fix date, and status.
- Release candidate FAQ list (approved items only).
- Final pilot summary with KPI trend and recommendation.
