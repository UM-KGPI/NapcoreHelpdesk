# RAG Fallback API Contract

## Purpose
Define implementation-ready API contracts for FAQ-first orchestration with RAG fallback, including trust guardrails, response semantics, and persistence mapping.

## OpenAPI Specification
- Canonical spec file: [api/openapi.yaml](api/openapi.yaml)

## Scope
- Primary orchestration endpoint for question answering.
- Supporting endpoint for FAQ promotion candidates.
- Supporting endpoint for editorial routing trigger.
- Shared schema for citations, evidence, and abstention.

## Design Principles
1. FAQ-first, then RAG fallback.
2. Approved GitHub repositories only.
3. No unsupported claims.
4. Mandatory citation payload for non-abstain answers.
5. Full event logging for auditability.

## Authentication And Headers
- Recommended auth: Bearer token.
- Required headers:
  - `Content-Type: application/json`
  - `X-Request-Id: <uuid>`
- Optional headers:
  - `X-User-Id: <id>`
  - `X-Session-Id: <id>`

## Endpoint 1: Ask Question (FAQ-first + RAG fallback)

### Method And Path
- `POST /api/v1/questions/answer`

### Request Body
```json
{
  "question": "How to use NeTEx for exchanging a timetable?",
  "sessionId": "sess-123",
  "userId": "user-42",
  "standardsScope": ["NeTEx", "SIRI"],
  "language": "en",
  "options": {
    "maxCitations": 5,
    "allowAbstain": true,
    "faqMinConfidence": 0.85,
    "retrievalTopK": 6,
    "retrievalMinScore": 0.62
  }
}
```

### Request Validation Rules
1. `question` is required and must be non-empty.
2. `standardsScope` values must be from configured standards set.
3. `faqMinConfidence` must be in `[0,1]`.
4. `retrievalTopK` must be in `[1,20]`.
5. If `allowAbstain=false`, service still may return abstain on policy violations.

### Success Response (FAQ)
```json
{
  "answerId": "ans-001",
  "mode": "faq",
  "confidence": 0.93,
  "answer": "Start with the relevant timetable frame...",
  "citations": [
    {
      "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
      "commitSha": "abc1234",
      "sourcePath": ".../timetable-guide.md",
      "chunkId": "3f2d...",
      "label": "Timetable overview"
    }
  ],
  "abstained": false,
  "abstentionReason": null,
  "reviewRequired": false,
  "trace": {
    "requestId": "req-...",
    "questionEventId": "qe-...",
    "matchedFaqEntryId": "faq-...",
    "retrievalEventIds": []
  }
}
```

### Success Response (RAG)
```json
{
  "answerId": "ans-002",
  "mode": "rag",
  "confidence": 0.77,
  "answer": "For timetable exchange, start by...",
  "citations": [
    {
      "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx",
      "commitSha": "abc1234",
      "sourcePath": ".../part-2.xml",
      "chunkId": "8de1...",
      "label": "Service frame example"
    }
  ],
  "abstained": false,
  "abstentionReason": null,
  "reviewRequired": true,
  "trace": {
    "requestId": "req-...",
    "questionEventId": "qe-...",
    "matchedFaqEntryId": null,
    "retrievalEventIds": ["re-..."],
    "evidenceLinkIds": ["el-..."]
  }
}
```

### Success Response (Abstain)
```json
{
  "answerId": "ans-003",
  "mode": "abstain",
  "confidence": 0.0,
  "answer": "I do not have sufficient approved-source evidence to answer this safely.",
  "citations": [],
  "abstained": true,
  "abstentionReason": "INSUFFICIENT_EVIDENCE",
  "reviewRequired": false,
  "trace": {
    "requestId": "req-...",
    "questionEventId": "qe-...",
    "matchedFaqEntryId": null,
    "retrievalEventIds": ["re-..."]
  }
}
```

### Error Responses
- `400 Bad Request`: invalid schema or parameters.
- `401 Unauthorized`: missing or invalid token.
- `403 Forbidden`: scope violation.
- `409 Conflict`: policy conflict (for example unsupported claims found and cannot regenerate).
- `422 Unprocessable Entity`: request valid but cannot be answered under constraints.
- `500 Internal Server Error`: unexpected server failure.

### Error Body
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "retrievalTopK must be between 1 and 20",
    "requestId": "req-..."
  }
}
```

## Endpoint 2: List FAQ Promotion Candidates

### Method And Path
- `GET /api/v1/faqs/promotion-candidates`

### Query Params
- `windowDays` (default `14`)
- `minCount` (default `5`)
- `onlyUnresolved` (default `false`)

### Response
```json
{
  "windowDays": 14,
  "minCount": 5,
  "items": [
    {
      "normalizedIntent": "netex timetable exchange",
      "questionCount": 8,
      "notHelpfulRate": 0.25,
      "lastAskedAt": "2026-03-28T10:00:00Z",
      "recommendedAction": "CREATE_FAQ_DRAFT"
    }
  ]
}
```

## Endpoint 3: Route Answer To Editorial Queue

### Method And Path
- `POST /api/v1/editorial/queue`

### Request Body
```json
{
  "questionEventId": "qe-...",
  "reason": "LOW_CONFIDENCE",
  "priority": "normal"
}
```

### Response
```json
{
  "queued": true,
  "queueItemId": "eq-...",
  "status": "draft"
}
```

## Guardrail Enforcement Contract

### Required checks before non-abstain answer is returned
1. Retrieval source allowlist check passes.
2. Evidence sufficiency check passes.
3. Citation presence check passes.
4. Unsupported-claim check passes.

### Mandatory behavior
- If any check fails, return `mode=abstain` or `409` when policy requires hard-fail.
- Never return uncited factual claims in `mode=faq` or `mode=rag`.

## Persistence Mapping

### On every `POST /questions/answer`
1. Insert into `question_events`.
2. If retrieval executed, insert one or more `retrieval_events`.
3. If answer is faq or rag, insert `answer_evidence_links` for each cited chunk.
4. If FAQ match exists, set `matched_faq_entry_id`.
5. Persist `abstention_reason` when `mode=abstain`.

### Table mapping
- `question_events.answer_mode` <- response `mode`
- `question_events.confidence_score` <- response `confidence`
- `retrieval_events.evidence_sufficient` <- guardrail result
- `answer_evidence_links.source_chunk_id` <- citations[*].chunkId

## Non-Functional Contract
1. P95 latency target: `<= 8s` for covered intents.
2. Citation coverage for published FAQ answers: `100%`.
3. Unsupported claim publication rate: `0%`.
4. Audit traceability: each non-abstain answer must include at least one evidence link.

## Versioning
- API version prefix: `/api/v1`.
- Backward-incompatible changes require `/api/v2`.

## OpenAPI Seed (Minimal)
```yaml
openapi: 3.1.0
info:
  title: NAPCORE Helpdesk API
  version: 1.0.0
paths:
  /api/v1/questions/answer:
    post:
      summary: Answer question with FAQ-first and RAG fallback
      responses:
        '200':
          description: Answer produced (faq, rag, or abstain)
        '400':
          description: Invalid request
        '409':
          description: Policy conflict
```
