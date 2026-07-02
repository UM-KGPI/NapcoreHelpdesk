# Project Background

> **Status:** This project is actively in development. Core functionality is stable and in pilot testing, but new features, refinements, and integrations are ongoing. The work is part of the NAPCORE WG 4.3, with active contributions from workgroup members.

This page covers where NAPCORE Helpdesk came from, who defined it, and how it was
built. For what the system does and how it's structured today, see
[Architecture overview](architecture-overview.md); for a running log of feature
changes, see [Recent updates](recent-updates.md).

## Purpose

NAPCORE Helpdesk is a multilingual Q&A assistant for implementer questions
about European public transport data standards — Transmodel, NeTEx, SIRI, and
OpRa — grounded only in approved source repositories, with citations and an
abstain path when evidence is insufficient. Questions can be asked in any of
the supported languages and are answered in that same language, so
implementers are not required to work in English. The name reflects NAPCORE,
the EU coordination initiative for National Access Points to transport data,
which these standards serve (www.napcore.eu).

## Requirements & design

The requirements and domain design are credited throughout the codebase (see
the header comment of most backend service modules) to:

- Andrej Tibaut
- Sara Guerra de Oliveira

both affiliated with University of Maribor
Faculty of Civil Engineering,
Transportation Engineering and Architecture,
Chair of Construction and Transportation Informatics (https://kgpi.fgpa.um.si/). They defined the standards scope (NeTEx/SIRI/OpRa/
Transmodel), the FAQ-first/RAG-fallback answer strategy, the citation and
abstention guarantees, and the editorial review workflow. The work is part of the NAPCORE WG 4.3. Members of the workgroup are actively contributing after the app launch.

## Development approach

Implementation was carried out by humans and by AI coding agents working under human
direction — every service module in `backend/helpdesk/services/` and
`backend/helpdesk/management/commands/` states this explicitly in its header
(`Crafted by: AI coding agents`). The development style visible in the commit
history is iterative rather than big-upfront-design:

- Small, scoped, conventionally-named commits (`feat(...)`, `fix(...)`,
  `chore(...)`, `docs(...)`).
- CI quality gates (backend tests, OpenAPI schema, C4 diagram checks, Postgres
  integration) were added early and extended alongside features rather than
  bolted on at the end.
- Fixes and reverts follow closely behind features shipped to real usage
  (e.g. the deep-link, spell-check, and GraphRAG definition-retrieval work),
  reflecting a "ship, observe, correct quickly" loop rather than long
  pre-verification cycles.

## Timeline (from git history)

The project started on 2026-03-28 and has had continuous, active development
since. Broad phases, in order:

1. **Foundations** — initial project import; hybrid lexical+vector retrieval
   on PostgreSQL/pgvector; FAQ and RAG persistence aligned to the C4
   architecture.
2. **Editorial workflow** — RBAC-based draft → review → approved/rejected →
   published queue, KPI widgets, and board UI.
3. **CI/ops hardening** — backend, OpenAPI, and C4 quality gates; health
   probes; security and release automation.
4. **Pilot testing** — first-user testing pack and feedback workflow.
5. **Production deployment & GraphRAG** — Fedora VM + Docker Compose
   deployment; GraphDB-backed concept expansion; XSD-to-ontology extraction
   pipeline providing authoritative concept definitions; multilingual
   question support; deep-linking to individual Q&A exchanges.

See [Recent updates](recent-updates.md) for a detailed log of the latest
phase.

## Where to go next

- [Architecture overview](architecture-overview.md) — system design and runtime flow
- [Recent updates](recent-updates.md) — latest feature and API changes
- [Installation](installation.md) / [Production deployment](production-deployment.md)
- [Contributing](../CONTRIBUTING.md) — development flow and commit conventions
