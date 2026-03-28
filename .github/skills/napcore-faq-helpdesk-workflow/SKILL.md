---
name: napcore-faq-helpdesk-workflow
description: "Build and operate a NAPCORE FAQ helpdesk workflow from GitHub standards sources (especially NeTEx-CEN/NeTEx), generate traceable answers, support GUI-based user questions, and store high-frequency FAQs in a database with human editorial review. Use for FAQ ingestion pipelines, answer quality controls, curation operations, and release-readiness checks."
argument-hint: "Describe your target standards, source repositories, GUI channel, and storage backend; include whether you need setup, curation, or operations mode."
user-invocable: true
---

# NAPCORE FAQ Helpdesk Workflow

## Outcome
Create and run a repeatable process that:
1. Ingests and normalizes source content from GitHub repositories, prioritizing NeTEx-CEN/NeTEx.
2. Produces relevant helpdesk answers with traceable source grounding.
3. Lets users ask questions through a GUI.
4. Captures and promotes frequently asked questions into a curated FAQ database.

## When to Use
- You need to bootstrap an AI-assisted FAQ helpdesk for multimodal standards.
- You need a curation workflow that combines AI draft generation with manual review.
- You need regulatory-safe responses with source traceability.
- You need an operational loop that identifies recurring user questions and persists approved FAQs.

## Inputs
- Standards scope: Transmodel, NeTEx, SIRI, OJP/OpRa, DATEX II.
- Source repositories and docs URLs.
- GUI context: web chat, portal widget, or internal support interface.
- Data backend constraints: SQL or NoSQL, retention policy, and audit requirements.
- Governance constraints: reviewer roles, approval policy, and publication rules.

## Default Operating Profile
- Architecture: RAG (retrieval-augmented generation) with citation-grounded answering.
- Knowledge boundary: approved GitHub repositories only.
- Storage backend: PostgreSQL.
- Answer mode: FAQ-first with AI fallback for novel or low-confidence intents.
- FAQ promotion rule: rolling-window frequency threshold.
- Regulatory publication gate: editorial team review only.

## Procedure
1. Define mission and boundaries.
   - Confirm audience, languages, standards scope, and update frequency.
   - Decide whether this run is setup mode or daily operations mode.

2. Build source inventory.
   - Start from NeTEx-CEN/NeTEx, then add required companion repositories.
   - For each source, register URL, branch/tag policy, and document type.
   - Maintain an allowlist of approved GitHub repositories; block all non-allowlisted sources.
   - Reject sources with unclear provenance.

3. Configure ingestion profile.
   - Define include and exclude paths.
   - Define chunking strategy and metadata schema.
   - Add source citation fields that can be attached to every answer.

4. Build RAG pipeline.
   - Parse and chunk source material.
   - Index chunks in a vector index with standard, concept, and version metadata.
   - Retrieve top-k grounded passages per query intent.
   - Generate answers only from retrieved context and return citations.
   - If retrieval evidence is insufficient, return an explicit "insufficient evidence" response and do not speculate.
   - Generate candidate FAQ pairs with confidence and citation coverage.

5. Add editorial curation gate.
   - Route generated FAQs through draft, review, approve, publish states.
   - Track reviewer identity, review notes, and change history.
   - Block publication when citations are missing or weak.

6. Implement GUI question flow.
   - Accept user questions from GUI.
   - Retrieve grounded context from the RAG index.
   - Return answer with references and confidence indicator.
   - Offer user feedback actions: helpful, not helpful, needs escalation.

7. Capture recurring questions and promote FAQs.
   - Log each question, normalized intent, answer outcome, and feedback.
   - Aggregate by frequency and unresolved rate.
   - Promote high-frequency, high-value intents into the curated FAQ backlog.
   - Default threshold: promote when the same normalized intent appears at least 5 times in 14 days.

8. Persist FAQs in database.
   - Store canonical question, approved answer, source citations, standards tags, validity period, and status.
   - Store operational telemetry: frequency, last asked, and satisfaction trend.
   - Keep immutable audit records for approvals and edits.
   - Use PostgreSQL tables for faq_entries, faq_versions, question_events, and review_events.

9. Run quality and readiness checks.
   - Validate grounding, consistency across standards, and review completion.
   - Validate GUI flow latency and fallback behavior.
   - Validate database integrity and deduplication rules.

10. Publish and operate.
   - Publish approved FAQs to the helpdesk experience.
   - Schedule periodic revalidation on repository updates or standards changes.

## Decision Points And Branching
- Source reliability:
  - If source provenance is weak, exclude from ingestion.
  - If source is authoritative but noisy, keep it with stricter include filters.
- Citation sufficiency:
  - If answer has no traceable reference, keep as draft only.
  - If answer has partial references, require reviewer escalation.
- Retrieval quality:
   - If retrieval returns weak or irrelevant passages, use fallback handling and open re-indexing ticket.
   - If repeated retrieval misses occur for a topic, add ingestion coverage task.
- Knowledge boundary enforcement:
   - If no approved GitHub source supports the answer, abstain and request clarification or source expansion.
   - If model output contains claims not present in retrieved evidence, block response and regenerate in strict mode.
- User intent type:
  - If intent matches existing approved FAQ, serve canonical answer first.
  - If intent is novel, use retrieval plus generation and open curation ticket.
- Feedback outcome:
  - If repeated not helpful feedback appears, demote answer and trigger re-review.
  - If sustained helpful feedback appears, mark as stable FAQ candidate.
- Regulatory sensitivity:
  - If legal claim is present without citation, block publication.
   - If legal claim is cited but ambiguous, require editorial clarification note before publish.

## Completion Criteria
- Ingestion profile is documented and reproducible.
- Every published FAQ answer has at least one traceable source citation.
- Editorial workflow is active with draft, review, approve, publish states.
- GUI can accept questions, return answers, and capture feedback.
- RAG retrieval layer returns relevant context for covered intents.
- Database stores approved FAQ content and operational metrics.
- Recurring-question promotion logic is operational and measurable.
- Answers are restricted to approved GitHub knowledge sources.
- Unsupported questions produce abstention responses rather than speculative content.

## Quality Bar
- No uncited legal or compliance assertions.
- Clear separation between standards-specific concepts.
- Reproducible ingestion and curation runs.
- Auditability for every published FAQ and subsequent revision.
- No hallucinated claims: each factual statement in published content is backed by retrieved evidence.

## Suggested Output Structure For Runs
1. Objective
2. Inputs and Assumptions
3. Source Inventory
4. Pipeline Design
5. GUI Integration Notes
6. FAQ Storage Model
7. Curation and Governance Plan
8. Validation Results
9. Risks and Follow-up Actions
