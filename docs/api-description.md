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

## Key response behaviors

- Modes: `faq`, `rag`, `abstain`
- Responses include citations and trace fields
- Policy can block unsupported answers
- Insufficient evidence returns explicit abstention

For schema details and examples, use [api/openapi.yaml](../api/openapi.yaml).
