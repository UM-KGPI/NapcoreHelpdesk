# NAPCORE Helpdesk Speaker Notes

These notes map to the slide order in the presentation summary.

## Slide 1 - Problem And Goal
- Explain that the main challenge is trust, not only speed.
- Stress that hallucinated standards guidance creates implementation risk.
- Position the project as a reliability-first helpdesk.

## Slide 2 - System Context (C4 Level 1)
- Explain that five stakeholder groups share one helpdesk interface.
- Point out external dependencies: approved GitHub repos and LLM provider.
- Reinforce the hard knowledge boundary and abstention policy.

## Slide 3 - Scope
- Clarify this is multimodal standards support, not a generic chatbot.
- Mention NeTEx-CEN/NeTEx is the anchor source.
- Note that scope is broad enough for interoperability discussions.

## Slide 4 - Core Approach
- Walk through FAQ-first then RAG fallback.[^rag-fallback]
- Explain cost and latency benefit of FAQ-first.
- Emphasize abstention as a feature, not a failure.

## Slide 5 - Trust And Safety Principles
- Describe repository allowlist as hard boundary.
- Explain citation gate and why uncited answers are blocked.
- Mention editorial workflow before publication.

## Slide 6 - Functional Requirements Highlights
- Present FR-001, FR-004, FR-005, FR-006 as delivery backbone.
- Add FR-002 and FR-003 for operational sustainability.
- Keep details short; promise deeper technical appendix if needed.

## Slide 7 - Data Model Logic
- Explain how data model enforces governance by design.
- Highlight answer_evidence_links as anti-hallucination control point.
- Mention that runtime and curated answers both remain auditable.

## Slide 8 - Why This Prevents Hallucinations
- Repeat the three constraints:
  - approved source only,
  - retrieval-grounded generation,
  - citation and support checks.
- Reinforce that unsupported claims are blocked or abstained.

## Slide 9 - User Experience Flow
- Describe user path in plain language.
- Highlight confidence display and references in response.
- Mention feedback loop for continuous quality improvement.

## Slide 10 - Operations And Governance
- Explain reviewer accountability and decision logging.
- Mention editorial operations are handled in Django Admin.
- Describe recurring-question promotion as scale mechanism.
- Mention re-indexing for repository updates and standard drift.

## Slide 11 - MVP Success Metrics
- Explain why each metric exists:
  - citation coverage for trust,
  - unsupported-claim rate for safety,
  - latency for usability,
  - retrieval success for usefulness.

## Slide 12 - Current Artifacts
- Reassure stakeholders that design is implementation-ready.
- Point to requirements, architecture, schema, PlantUML, and Django/DRF baseline.

## Slide 13 - Next Steps
- Present as a short execution plan.
- Call out Django/DRF API build and Django Admin workflow setup.
- Emphasize pilot-first delivery and measurable validation.

## Appendix - Example Questions
- Use timetable and Stop Place ID examples as concrete value proof.
- State expected output qualities: practical, cited, non-speculative.

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks and then generates an answer grounded in that retrieved evidence.
