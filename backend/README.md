# Backend Scaffold (Django + DRF)

This folder contains the initial backend scaffold for NAPCORE Helpdesk.

## What is included
- Django project config in `config/`.
- Helpdesk app in `helpdesk/`.
- Canonical FAQ persistence with versioning (`FAQEntry`, `FAQVersion`).
- Retrieval and evidence audit persistence (`RetrievalEvent`, `AnswerEvidenceLink`).
- Chat-session compatible answer orchestration keyed by `sessionId` / `userId`.
- Deterministic grounded generation plus optional LLM-ready provider adapter with safe fallback.
- Full REST API surface: [api/openapi.yaml](../api/openapi.yaml).
- FAQ-first plus RAG-fallback orchestration in service modules aligned with C4 Level 3 mapping.
- JWT bearer authentication (`Authorization: Bearer <jwt>`) validated with `JWT_SECRET_KEY` and `JWT_ALGORITHM`.

## Database baseline
- Architecture baseline is PostgreSQL with pgvector-ready schema.
- On PostgreSQL, migration `0006_pgvector_native_alignment` enables the `vector` extension and creates an IVF Flat index on `SourceChunk.embedding_vector`.

## API request headers
- `Authorization: Bearer <jwt-token>`
- `X-Request-Id: <non-empty-id>` for `POST /api/v1/questions/answer`
