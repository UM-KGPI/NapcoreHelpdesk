# Functional Requirements

## FR-001: Developer FAQ question answering

### User story
As a developer, I want to ask standards-implementation questions through the helpdesk GUI so that I receive relevant, practical, and source-grounded answers.

### Acceptance criteria
1. The app accepts free-text developer questions from the GUI helpdesk.
2. The system answers from approved FAQ entries first, then uses RAG retrieval plus generation as fallback.[^rag-fallback]
3. Answers include practical guidance and references to source materials.
4. For implementation questions, answers include examples when available (for example XML snippets).
5. If confidence is low or references are incomplete, the answer is routed to editorial review before publication as FAQ.

## FR-004: RAG ingestion and indexing

### User story
As a platform engineer, I want GitHub standards sources to be chunked and indexed for semantic retrieval so that user questions can be grounded on authoritative content.

### Acceptance criteria
1. The ingestion job reads configured repositories, with NeTEx-CEN/NeTEx prioritized.
2. The job applies include and exclude path rules and records source metadata.
3. Source content is chunked and stored in a retrieval index with citation fields.
4. Re-indexing can be triggered on source updates.

## FR-005: RAG retrieval and grounded generation

### User story
As a developer user, I want generated answers to be based on retrieved context so that responses are relevant and traceable.

### Acceptance criteria
1. For non-FAQ intents, the system retrieves top-k relevant passages before answer generation.
2. The generator uses only retrieved context and system policy to produce the final answer.
3. The final answer includes references to retrieved source documents.
4. If retrieval quality is below threshold, the system returns a safe fallback response and logs a retrieval miss.

## FR-006: Knowledge-boundary and anti-hallucination enforcement

### User story
As a platform owner, I want answers restricted to approved GitHub repositories so that users receive traceable, non-hallucinated responses.

### Acceptance criteria
1. The system enforces an allowlist of approved GitHub repositories as the only retrievable knowledge sources.
2. Responses are generated only from retrieved evidence linked to allowlisted sources.
3. If supporting evidence is missing, the system returns an abstention response stating insufficient evidence.
4. Responses without citations are blocked from publication and flagged for review.
5. Each answer event stores evidence references used in generation for auditability.

## FR-002: FAQ curation and publication workflow

### User story
As an editor, I want draft answers to move through review and approval so that only validated FAQ entries are published.

### Acceptance criteria
1. Draft answers are tracked through draft, review, approve, and publish states.
2. Published answers must include at least one traceable citation.
3. Regulatory or compliance statements without citation are blocked from publication.
4. Reviewer identity, decision, and notes are stored for auditability.

## FR-003: Frequent-question capture and FAQ promotion

### User story
As a product owner, I want recurring user questions to be detected automatically so that high-value topics are promoted into curated FAQs.

### Acceptance criteria
1. Every user question is stored as an event in history.
2. The system normalizes similar questions into shared intents.
3. Promotion candidates are generated using the rolling-window threshold rule.
4. Promotion candidates are routed to the editorial queue before publish.

## Example FAQ scenarios from users
These are examples of questions that should be handled by FR-001 and can become curated FAQ entries.

### Example 1
Question: "How to use NeTEx for exchanging a timetable?"

Expected answer characteristics:
1. Identifies a practical NeTEx starting point for timetable exchange.
2. Includes at least one structurally consistent XML example.
3. Includes references to the relevant NeTEx source documentation.

### Example 2
Question: "How to implement IDs for a Stop Place registry?"

Expected answer characteristics:
1. Explains identifier format, uniqueness, lifecycle, and governance concerns.
2. Aligns guidance with NeTEx and related standards context when relevant.
3. Includes traceable references to source materials.

## Notes
- These functional requirements align with the FAQ-first with AI fallback mode.
- The fallback mode is implemented using RAG architecture.
- Published FAQ answers must pass editorial review and citation checks.
- Knowledge base scope is restricted to approved GitHub repositories.
- Unsupported questions must produce abstention responses, not speculative content.

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks and then generates an answer grounded in that retrieved evidence.
