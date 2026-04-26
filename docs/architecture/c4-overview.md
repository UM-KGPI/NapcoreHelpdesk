# C4 Architecture Overview

This file introduces the C4 diagram set for the NAPCORE Helpdesk.

## Included Levels
- Level 1 (System Context): [c4-system-context.md](docs/architecture/c4-system-context.md)
- Level 2 (Container): [c4-container.md](docs/architecture/c4-container.md)
- Level 3 (Orchestrator Components): [c4-orchestrator-components.md](docs/architecture/c4-orchestrator-components.md)

## Actors Included
- PTO (Public Transport Operator)
- PTA (Public Transport Authority)
- Developer
- ITS System Integrator
- Ticketing Agent

## Purpose
- Level 1: explain system scope and external dependencies for mixed technical and non-technical audiences.
- Level 2: show internal containers, responsibilities, and interaction flow.

## Planned Next Level
- Level 3 is maintained alongside implementation and updated when orchestration modules or semantic-layer runtime behavior change.

## Notes
- The diagrams align with the FAQ-first + RAG fallback model.
- Knowledge boundary remains restricted to approved GitHub repositories.
- Graph-aware retrieval is represented as a first-class path using GraphDB-backed ontology expansion when enabled.
- Abstention behavior is kept explicit for insufficient evidence.
