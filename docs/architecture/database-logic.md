# Database Diagram Logic

This document explains the logic represented in the PlantUML diagram.

For the current model-level ERD with explicit cardinalities, see [ERD schema with cardinalities](erd-schema.md).

## Source Of Truth
- Schema is managed by Django migrations in `backend/helpdesk/migrations/`.
- Use `make backend-migrate` to apply migrations.

## 1) Knowledge Boundary And Ingestion
1. `approved_repositories` is the allowlist of GitHub repositories that are allowed as knowledge sources.
2. `source_documents` stores files pulled from those repositories, including commit and path metadata.
3. `source_chunks` splits documents into retrievable units used by RAG.

Logical effect:
- The system can only retrieve from repositories that are explicitly approved.

## 2) FAQ Content Lifecycle
1. `faq_entries` stores the canonical question and status.
2. `faq_versions` stores immutable answer revisions for each FAQ entry.
3. `review_events` records editorial decisions over FAQ versions.
4. `faq_entries.current_version_id` points to the currently active version (optional pointer).

Logical effect:
- FAQ content is versioned, reviewable, and auditable.

## 3) Runtime Question Handling
1. `question_events` records each user question and outcome (faq, rag, or abstain).
2. `question_events.matched_faq_entry_id` is optional and set when an existing FAQ is matched.
3. `retrieval_events` records retrieval attempts for RAG responses.
4. `retrieval_events.repository_id` ties retrieval to an approved repository context.

Logical effect:
- Every question is tracked and RAG operations are observable.

## 4) Evidence Mapping And Anti-Hallucination
1. `answer_evidence_links` links answer claims to `source_chunks` evidence.
2. Evidence links can be attached to:
   - `faq_versions` for curated answers, or
   - `question_events` for runtime answers.
3. Constraint: at least one of `faq_version_id` or `question_event_id` must be present.

Logical effect:
- Published or runtime answers can be traced back to exact source chunks.
- Unsupported claims can be blocked because evidence is explicit.

## 5) Cardinality Meaning
1. One approved repository can have many source documents.
2. One source document can have many source chunks.
3. One FAQ entry can have many versions.
4. One FAQ version can have many review events.
5. One question event can have many retrieval events.
6. One source chunk can support many answer evidence links.
7. FAQ matching and current-version pointers are optional relationships.

## 6) End-To-End Logic In One Line
Approved GitHub content is ingested and chunked, answers are created or retrieved via FAQ/RAG, and every answer is tied to source evidence so the system can avoid hallucinated output.
