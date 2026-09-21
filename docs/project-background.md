# Project Background

> **Status:** This project is actively in development. The core functionality is stable and in pilot testing, but new features, refinements, and integrations are ongoing. The work is part of the NAPCORE Task 4.3 Multimodal Standards, with active contributions from task members.

This page covers where NAPCORE Helpdesk idea came from, who defined it, and how it was
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
abstention guarantees, and the editorial review workflow. The work is part of the NAPCORE Task 4.3. Active task partners are contributing after the app launch.

## Development approach

Implementation was carried out by humans and by AI coding agents working under human
direction. The development style visible in the commit
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

1. **Foundations** (Mar 2026) — initial project import; hybrid lexical+vector
   retrieval on PostgreSQL/pgvector; FAQ and RAG persistence and editorial
   RBAC scaffolding aligned to the C4 architecture.
2. **Ontology, GraphRAG & editorial maturation** (Apr–Jun 2026) —
   XSD-to-ontology extraction pipeline and GraphDB-backed concept expansion;
   FAQ-first/RAG-fallback answer strategy; the editorial draft → review →
   approved/rejected → published workflow, KPI widgets, and board UI; Fedora
   VM + Docker Compose deployment automation.
3. **Answer-quality & reasoning-model hardening** (Jul 2026 — the single
   largest push, over half of all commits to date) — citation-grounding
   correctness (stop false rejections, prevent hallucinated [E#] references,
   lenient handling for code blocks); Qwen reasoning-model controller
   tuning; prompt-constraint and markdown-formatting fixes; multilingual
   abstain/insufficient-evidence phrasing.
4. **UI/UX refinement & release cadence** (Jul 2026, ongoing) — user
   discovery features (Inspiring questions panel with smart caching);
   streamlined version display and deep-linking to individual Q&A
   exchanges; frequent patch releases; C4 diagram maintenance;
   Dependabot/security fixes; community contribution pathway via GitHub.
5. **Cross-standard ontology alignment & production readiness** (Sep 2026)
   — migrated NeTEx/OpRa/SIRI source repositories to their current
   canonical GitHub orgs and reindexed; rewrote stale ontology alignments
   (825 NeTEx, 297 SIRI, 102 OpRa concepts now correctly mapped to the
   shared core ontology); fixed the GraphDB query structure that had
   silently prevented cross-standard concept expansion from ever working;
   corrected a production LLM model-alias regression; dependency upgrades
   (React Router v7, Vitest v4).

See [Recent updates](recent-updates.md) for a detailed log of the latest
phase.

## Contributing

NAPCORE Helpdesk is open-source and developed collaboratively. We welcome
contributions, feedback, and ideas from the community. Visit the
[GitHub repository](https://github.com/UM-KGPI/NapcoreHelpdesk) to report
issues, propose features, submit pull requests, or review the codebase and
architecture. See [Contributing](../CONTRIBUTING.md) for development flow and
commit conventions.

## Where to go next

- [Architecture overview](architecture-overview.md) — system design and runtime flow
- [Recent updates](recent-updates.md) — latest feature and API changes
- [Installation](installation.md) / [Production deployment](production-deployment.md)
- [Contributing](../CONTRIBUTING.md) — development flow and commit conventions
- [GitHub repository](https://github.com/UM-KGPI/NapcoreHelpdesk) — source code and issue tracking
