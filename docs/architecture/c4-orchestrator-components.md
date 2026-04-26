# C4 Orchestrator Components (Level 3)

Diagram source: [c4-orchestrator-components.puml](docs/architecture/c4-orchestrator-components.puml)

## Why this diagram matters
It decomposes the Question API / Orchestrator into components so implementation tasks can be assigned clearly.

## Components explained in plain language
1. Request Router: validates incoming request and coordinates the pipeline.
2. Semantic Query Parser: normalizes scope and concept intent before retrieval.
3. FAQ Matcher: attempts high-confidence canonical FAQ answer first.
4. Retrieval Gateway: performs fallback retrieval from allowlisted indexed sources.
5. Semantic Graph Adapter: runs ontology and alignment expansion against GraphDB when enabled.
6. Generation Adapter: creates answer from retrieved evidence using deterministic grounded logic or optional provider-backed LLM mode.
7. Policy Guard: blocks unsupported claims and enforces abstention/citation rules.
8. Semantic Rule Engine: evaluates rule conclusions against retrieved evidence.
9. Ontology Registry: publishes ontology version trace metadata.
10. Evidence Mapper: links answer claims to source chunks and provenance records.
11. Event Logger: stores question and retrieval telemetry.
12. Editorial Router: sends flagged responses to review queue.

## Key messages
1. Safety and governance are handled by dedicated components.
2. Evidence mapping is explicit and auditable.
3. Fallback behavior is structured and testable.
4. Component ownership can be split across implementation teams.

## Relationship to implementation planning
Use this level as the basis for:
- API handler boundaries,
- service/module ownership,
- integration tests for FAQ, RAG, and abstention paths.

## Component to module mapping (v1 baseline)
1. Request Router -> `backend/helpdesk/api/views.py` (`QuestionAnswerView`)
2. FAQ Matcher -> `backend/helpdesk/services/faq_matcher.py`
3. Semantic Query Parser -> `backend/helpdesk/services/question_parsing.py`
4. Retrieval Gateway -> `backend/helpdesk/services/retrieval_gateway.py`
5. Semantic Graph Adapter -> `backend/helpdesk/services/semantic_graph.py` + `backend/helpdesk/services/graphdb_client.py`
6. Generation Adapter -> `backend/helpdesk/services/grounded_generator.py` + `backend/helpdesk/services/llm_generator.py`
7. Policy Guard -> `backend/helpdesk/services/policy_guard.py`
8. Semantic Rule Engine -> `backend/helpdesk/services/rule_engine.py`
9. Ontology Registry -> `backend/helpdesk/services/ontology_registry.py`
10. Evidence Mapper -> `backend/helpdesk/services/evidence_mapper.py` + `backend/helpdesk/services/provenance_mapper.py`
11. Event Logger -> `backend/helpdesk/services/event_logger.py` + `backend/helpdesk/services/retrieval_event_logger.py`
12. Editorial Router -> `backend/helpdesk/services/editorial_router.py`

## Interface contracts per component
1. FAQ Matcher
	- Input: normalized question, standards scope.
	- Output: `mode=faq` candidate with confidence and FAQ version id, or no-match.
2. Semantic Query Parser
	- Input: raw question text, requested standards scope.
	- Output: semantic query object with candidate standards, concept confidence, and ambiguity flags.
3. Retrieval Gateway
	- Input: normalized question, scope filters, top-k, min score.
	- Output: ranked chunk set with repository, path, commit, chunk id, plus graph trace metadata.
4. Semantic Graph Adapter
	- Input: extracted concept IDs, active standards, graph feature flags.
	- Output: expanded concept set and provenance-ready graph trace fields.
5. Generation Adapter
	- Input: user question + retrieved chunks.
	- Output: draft answer text via deterministic grounded generation or LLM-ready provider call.
6. Policy Guard
	- Input: draft answer + chunk set + citation list.
	- Output: pass/fail, abstention reason, review-required flag.
7. Semantic Rule Engine
	- Input: semantic query + retrieved chunks + effective scope.
	- Output: matched rules, conclusions, and traceable rule-hit count.
8. Ontology Registry
	- Input: runtime ontology state.
	- Output: ontology version payload included in trace metadata.
9. Evidence Mapper
	- Input: final answer id + supporting chunk set + graph/rule trace context.
	- Output: persisted `answer_evidence_links` ids and evidence provenance ids.
10. Event Logger
	- Input: request metadata + routing decisions + timings.
	- Output: `question_events` and `retrieval_events` records.
11. Editorial Router
	- Input: review-required outputs.
	- Output: editorial queue record with reason and priority.
