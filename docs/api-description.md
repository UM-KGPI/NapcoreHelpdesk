# API Description

Authoritative contract: [api/openapi.yaml](../api/openapi.yaml)

## Base path

- Local: `http://localhost:8000/api/v1`

## Main endpoint groups

### Operations

- `GET /health/live`
- `GET /health/ready`
- `POST /admin/index`

### QnA

- `POST /questions/answer`
- `POST /questions/answer/stream`
- `POST /questions/feedback`
- `GET /questions/events`

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

## Frontend Deep-Linking

Editor deep-links to specific questions:

```
/napcore-helpdesk/editor?questionId=req-mr0tatgt-bmw50d
```

Auto-loads question and all details.

For schema details and examples, use [api/openapi.yaml](../api/openapi.yaml).
