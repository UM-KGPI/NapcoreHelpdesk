# C4 Architecture Overview

This file introduces the C4 diagram set for the NAPCORE Helpdesk.

## Included Levels
- Level 1 (System Context): [c4-system-context.md](c4-system-context.md)
- Level 2 (Container): [c4-container.md](c4-container.md)
- Level 3 (Orchestrator Components): [c4-orchestrator-components.md](c4-orchestrator-components.md)

## Actors Included
- NAP Manager (manages a national access point, ensures data publisher compliance)
- Transport Authority (sets policy and oversees multimodal standards adoption)
- Transport Operator (publishes journey, stop, and timetable data using NeTEx, SIRI, or OpRa)
- Road Authority (publishes road network and traffic data using DATEX II)
- Standards Implementer (developer or engineer implementing NeTEx, SIRI, DATEX II, or OpRa integrations)
- ITS System Integrator (integrates across standards and deploys interoperability solutions)

This list is representative of the NAPCORE constituency, not exhaustive.

## Purpose
- Level 1: explain system scope and external dependencies for mixed technical and non-technical audiences.
- Level 2: show internal containers, responsibilities, and interaction flow.

## Planned Next Level
- Level 3 is maintained alongside implementation and updated when orchestration modules or semantic-layer runtime behavior change.

## Notes
- The diagrams align with the FAQ-first + RAG fallback model.
- The LLM path is split into a controller runtime (intent/routing/SPARQL planning) and a narration runtime (grounded answer composition).
- Knowledge boundary remains restricted to approved GitHub repositories.
- Graph-aware retrieval is represented as a first-class path using GraphDB-backed ontology expansion when enabled.
- Abstention behavior is kept explicit for insufficient evidence.
