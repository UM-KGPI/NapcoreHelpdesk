# NAPCORE Helpdesk Speaker Notes

These notes map to the current slide order in the presentation deck.

## Slide 1 - Problem And Goal
- Explain that the main challenge is trust, not only speed.
- Stress that uncited guidance creates delivery and compliance risk.
- Position the project as a reliability-first helpdesk.

## Slide 2 - System Context (C4 Level 1)
- Explain that five stakeholder groups share one helpdesk interface.
- Point out external dependencies: approved GitHub repos and LLM provider.
- Reinforce the hard knowledge boundary and abstention policy.

## Slide 3 - Scope
- Clarify this is multimodal standards support, not a generic chatbot.
- Mention NeTEx-CEN/NeTEx is the anchor source.
- Note that the current product now combines operator and chat-style access patterns.

## Slide 4 - Evolution Of Helpdesk Implementations
- Walk the audience through the maturity curve.
- Start with keyword search as the lowest-friction but lowest-assistance option.
- Show how FAQ-first and editorial workflow add operational value before full chat UX.
- Position the current build as the point where traceable chat becomes feasible.

## Slide 5 - Why The Evolution Matters
- Explain that each stage solves a real limitation of the previous one.
- Stress that the project did not jump straight to LLM usage.
- Emphasize that governance and provenance were kept as the invariant.

## Slide 6 - Core Approach
- Walk through FAQ-first then RAG fallback.[^rag-fallback]
- Explain cost and latency benefit of FAQ-first.
- Mention that generation can stay deterministic or switch to LLM-ready mode.
- Emphasize abstention as a feature, not a failure.

## Slide 7 - Trust And Safety Principles
- Describe repository allowlist as hard boundary.
- Explain citation gate and why uncited answers are blocked.
- Mention editorial workflow before publication.

## Slide 8 - Functional Requirements Highlights
- Present FR-001, FR-004, FR-005, FR-006 as delivery backbone.
- Add FR-002 and FR-003 for operational sustainability.
- Keep details short; promise deeper technical appendix if needed.

## Slide 9 - Data Model Logic
- Explain how data model enforces governance by design.
- Highlight answer_evidence_links as anti-hallucination control point.
- Mention that runtime and curated answers both remain auditable.

## Slide 10 - Why This Prevents Hallucinations
- Repeat the three constraints:
  - approved source only,
  - retrieval-grounded generation,
  - citation and support checks.
- Reinforce that unsupported claims are blocked or abstained.

## Slide 11 - User Experience Flow
- Describe the chat session as the new primary demo surface.
- Mention that the operator console still exists for governance and board work.
- Highlight session trace, references, and confidence in each answer.
- Mention feedback loop and editorial routing for continuous quality improvement.

## Slide 12 - Current Product State
- Make clear that the deck now reflects implemented work, not only a target design.
- Call out chat UX, deterministic grounded generation, and optional LLM-ready mode.
- Mention companion repository support as a controlled extension of coverage.

## Slide 13 - Current Chat UX
- Use the screenshot to anchor the discussion in a real interface, not just architecture.
- Point out the evidence-bearing assistant turn, confidence score, and request trace.
- Emphasize that the chat surface remains grounded and auditable.

## Slide 14 - Operations And Governance
- Explain reviewer accountability and decision logging.
- Mention editorial operations are handled in Django Admin.
- Describe recurring-question promotion as scale mechanism.
- Mention re-indexing for repository updates and standard drift.

## Slide 15 - MVP Success Metrics
- Explain why each metric exists:
  - citation coverage for trust,
  - unsupported-claim rate for safety,
  - latency for usability,
  - retrieval success for usefulness.

## Slide 16 - Current Artifacts
- Point to requirements, testing, architecture, and C4 documentation.
- Mention that architecture exports and presentation outputs are reproducible.

## Slide 17 - Next Steps
- Present as a short pilot-hardening plan, not greenfield implementation work.
- Emphasize evaluation of LLM-ready mode against deterministic fallback.
- Close on production-readiness decisions being evidence-led.

## Appendix - Example Questions
- Use timetable and Stop Place ID examples as concrete value proof.
- State expected output qualities: practical, cited, non-speculative.

[^rag-fallback]: RAG fallback means that when no high-confidence FAQ answer is available, the system retrieves relevant source chunks and then generates an answer grounded in that retrieved evidence.
