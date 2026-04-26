# C4 System Context (Level 1)

Diagram source: [c4-system-context.puml](docs/architecture/c4-system-context.puml)

## Why this diagram matters
This view explains the system boundary for non-technical and technical stakeholders.
It shows who uses the helpdesk and which external systems it depends on.

## Stakeholders covered
- PTO (Public Transport Operator)
- PTA (Public Transport Authority)
- Developer
- ITS System Integrator
- Ticketing Agent

## Key messages
1. All stakeholder groups use one shared chat-style helpdesk interface.
2. The helpdesk uses approved GitHub repositories, including allowlisted companion repositories, as knowledge sources.
3. The helpdesk can use GraphDB as a semantic graph backend for ontology-aligned retrieval expansion.
4. LLM generation is the default generation path, constrained by retrieved evidence, not open-ended model memory.
5. If evidence is insufficient, the system abstains rather than speculating.

## Discussion prompts for non-IT stakeholders
1. Are the included user groups complete?
2. Is the knowledge boundary clear enough for governance?
3. Does abstention behavior match operational expectations?

## Relationship to requirements
- Supports FR-001 (question answering), FR-004 and FR-005 (RAG retrieval/generation), and FR-006 (knowledge boundary and anti-hallucination).
