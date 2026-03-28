# C4 Orchestrator Components (Level 3 - Planned Next)

Diagram source: [c4-orchestrator-components.puml](docs/architecture/c4-orchestrator-components.puml)

## Status
This is a pre-implementation draft to guide Level 3 work before coding begins.

## Why this diagram matters
It decomposes the Question API / Orchestrator into components so implementation tasks can be assigned clearly.

## Components explained in plain language
1. Request Router: validates incoming request and coordinates the pipeline.
2. FAQ Matcher: attempts high-confidence canonical FAQ answer first.
3. Retrieval Gateway: performs fallback retrieval from allowlisted indexed sources.
4. Grounded Generator: creates answer from retrieved evidence.
5. Policy Guard: blocks unsupported claims and enforces abstention/citation rules.
6. Evidence Mapper: links answer claims to source chunks.
7. Event Logger: stores question and retrieval telemetry.
8. Editorial Router: sends flagged responses to review queue.

## Key messages
1. Safety and governance are handled by dedicated components.
2. Evidence mapping is explicit and auditable.
3. Fallback behavior is structured and testable.
4. Component ownership can be split across implementation teams.

## Recommended pre-implementation checks
1. Confirm confidence and retrieval thresholds.
2. Confirm policy guard fail behavior (abstain vs hard fail).
3. Confirm evidence-link minimum for non-abstain answers.
4. Confirm editorial routing criteria and priority model.

## Relationship to implementation planning
Use this level as the basis for:
- API handler boundaries,
- service/module ownership,
- integration tests for FAQ, RAG, and abstention paths.

## Component to module mapping (v1 baseline)
1. Request Router -> `backend/helpdesk/api/views/questions.py`
2. FAQ Matcher -> `backend/helpdesk/services/faq_matcher.py`
3. Retrieval Gateway -> `backend/helpdesk/services/retrieval_gateway.py`
4. Grounded Generator -> `backend/helpdesk/services/grounded_generator.py`
5. Policy Guard -> `backend/helpdesk/services/policy_guard.py`
6. Evidence Mapper -> `backend/helpdesk/services/evidence_mapper.py`
7. Event Logger -> `backend/helpdesk/services/event_logger.py`
8. Editorial Router -> `backend/helpdesk/services/editorial_router.py`

## Interface contracts per component
1. FAQ Matcher
	- Input: normalized question, standards scope.
	- Output: `mode=faq` candidate with confidence and FAQ version id, or no-match.
2. Retrieval Gateway
	- Input: normalized question, scope filters, top-k, min score.
	- Output: ranked chunk set with repository, path, commit, chunk id.
3. Grounded Generator
	- Input: user question + retrieved chunks.
	- Output: draft answer text + provisional claim-to-chunk references.
4. Policy Guard
	- Input: draft answer + chunk set + citation list.
	- Output: pass/fail, abstention reason, review-required flag.
5. Evidence Mapper
	- Input: final answer id + supporting chunk set.
	- Output: persisted `answer_evidence_links` ids.
6. Event Logger
	- Input: request metadata + routing decisions + timings.
	- Output: `question_events` and `retrieval_events` records.
7. Editorial Router
	- Input: review-required outputs.
	- Output: editorial queue record with reason and priority.
