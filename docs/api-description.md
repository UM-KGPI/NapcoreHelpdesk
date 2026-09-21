# API Description

Authoritative contract: [api/openapi.yaml](../api/openapi.yaml)

## Base path

- Local: `http://localhost:8000/api/v1`

## Main endpoint groups

### Operations

- `GET /health/live`
- `GET /health/ready`
- `GET /health/llm` — configured vs. gateway-authorized model status for answer generation and controller routing (see [LLM status page](#llm-status-page) below)
- `POST /admin/index`

### Auth

- `POST /auth/dev-token` — local-development-only short-lived JWT issuance (disabled unless `DEV_JWT_AUTO_ISSUE` is set)

### QnA

- `POST /questions/answer`
- `POST /questions/answer/stream`
- `GET /questions/trending`
- `POST /questions/feedback`
- `GET /questions/events`
- `GET /questions/events/{questionEventId}` — full detail by numeric ID or request ID
- `DELETE /questions/events/{questionEventId}`

### FAQOps

- `GET /faqs/promotion-candidates`

### Editorial

- `GET /editorial/queue`
- `POST /editorial/queue`
- `POST /editorial/queue/transition`
- `GET /editorial/queue/metrics`
- `GET /editorial/semantic-clusters`

## Key request parameters

### Questions API (`POST /questions/answer`)

- `question` (required): Natural language question
- `language` (optional): Response language (auto-detected if not provided)
  - Supported: English, Norwegian, Slovenian, German, French, Spanish, Italian, Dutch, Polish, Portuguese, Swedish, Danish, Finnish, Czech, Slovak, Hungarian, Romanian, Croatian, Bulgarian, Greek, Lithuanian, Latvian, Estonian, Maltese, Irish
  - Default: Auto-detect from question
- `standardsScope` (optional): Filter to specific standards (NeTEx, SIRI, OpRa)
- `generationProfile` (optional): "llm-ready" or "grounded"
- `controllerProfile` (optional): "llm-ready" or "deterministic"

### Example Multilingual Request

```json
POST /questions/answer
{
  "question": "Kaj je STOP PLACE v NeTEx?",
  "language": "Slovenian",
  "standardsScope": ["NeTEx"]
}
```

Response will be in Slovenian, with technical terms in English.

## Key response behaviors

- Modes: `faq`, `rag`, `abstain`
- Responses include citations and trace fields
- Policy can block unsupported answers
- Insufficient evidence returns explicit abstention
- Evidence display improved: no duplicate file paths

## LLM status page

`GET /health/llm` is a diagnostic endpoint (not a readiness probe — always
returns 200, with health conveyed via the body's `status` field). It reports,
for both answer generation and controller routing: configured vs. active
model, live gateway reachability, the gateway's current authorized-model
list, and whether the model-drift self-heal has already corrected anything
this process. Pass `?live=false` to skip the live gateway probe and read
cached state only.

Viewable in the browser at `/napcore-helpdesk/llm-status` (nav link "LLM
status"), which renders this endpoint's result instead of requiring a manual
authenticated `curl` call.

## Frontend Deep-Linking

Editor deep-links to specific questions:

```
/napcore-helpdesk/editor?questionId=req-mr0tatgt-bmw50d
```

Auto-loads question and all details.

For schema details and examples, use [api/openapi.yaml](../api/openapi.yaml).
