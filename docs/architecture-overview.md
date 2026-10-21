# Architecture Overview

NAPCORE Helpdesk is a FAQ-first, RAG-fallback system for transport standards.

## C4 views

- System context: [docs/diagrams/c4-system-context.svg](diagrams/c4-system-context.svg)
- Container view: [docs/diagrams/c4-container.svg](diagrams/c4-container.svg)
- Orchestrator components: [docs/diagrams/c4-orchestrator-components.svg](diagrams/c4-orchestrator-components.svg)

## Runtime flow

1. User asks a question.
2. System tries FAQ match first.
3. If FAQ confidence is low, the system runs RAG retrieval from approved repositories.
4. If GraphRAG is enabled, GraphDB expands concepts and alignments for retrieval ranking.
5. Answer generation is grounded only in retrieved evidence.
6. Policy checks enforce citation and support constraints.
7. If evidence is weak, system abstains.
8. Events and evidence links are persisted for traceability and editorial review.

## RAG architecture

- Main design: FAQ-first + RAG fallback
- Knowledge boundary: approved repositories only
- Guardrails: citation-required output and abstention on insufficient evidence
- Editorial workflow: draft -> review -> approved/rejected -> published

## RAG activity diagram (updated with GraphDB)

- PlantUML source: [.mylocal/docs/architecture/rag-activity-graphdb.puml](../../.mylocal/docs/architecture/rag-activity-graphdb.puml)
- SVG render: [docs/diagrams/rag-activity-graphdb.svg](diagrams/rag-activity-graphdb.svg)

![RAG Activity Diagram](diagrams/rag-activity-graphdb.svg)

## NeTEx Line–Journey class relations

How `netex:Line` and `netex:Journey` connect once `rdfs:subClassOf` is followed downward only
(PR #95) and relation-path evidence cites the resulting `owl:ObjectProperty` edges (PR #96):
`Journey` has no direct link to `Line`, but its subclasses `ServiceJourney` and `DeadRun` each
reference `Line` through `lineRef`.

- Interactive (mermaid.js): [docs/diagrams/netex-line-journey-relations.html](diagrams/netex-line-journey-relations.html)
- SVG render: [docs/diagrams/netex-line-journey-relations.svg](diagrams/netex-line-journey-relations.svg)

![NeTEx Line-Journey relations](diagrams/netex-line-journey-relations.svg)
