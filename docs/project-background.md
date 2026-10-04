# Project Background

> **Work in progress:** NAPCORE Helpdesk is under active development and currently in pilot testing. Answers may be incomplete or occasionally inaccurate. Always check them against the cited sources and the official standard documentation. Coverage, features, and behaviour may change between releases, and your feedback directly shapes what comes next. The work is part of the NAPCORE Task 4.3 Multimodal standards, with active contributions from task members.

This page covers where NAPCORE Helpdesk idea came from, who defined it, and how it was
built. For what the system does and how it's structured today, see
[Architecture overview](architecture-overview.md); for a running log of feature
changes, see [Recent updates](recent-updates.md).

## Purpose

NAPCORE Helpdesk helps implementers get reliable answers to their questions
about the European public transport data standards Transmodel, NeTEx, SIRI,
and OpRa.

- **Grounded answers:** responses are based only on approved source
  repositories and cite the evidence they use.
- **Semantic technologies:** the standards are modelled as linked data and
  stored in a GraphDB knowledge graph, helping the assistant find related
  concepts across standards.
- **AI as controller and narrator:** a controller model checks whether a
  matched FAQ fits or the sources should be searched, and a narration model
  writes the answer from the retrieved evidence. Both use the open-weight model
  `nvidia/Qwen3.6-35B-A3B-NVFP4`, hosted at the University of Maribor, Faculty
  of Electrical Engineering and Computer Science.
- **Honest about gaps:** when the evidence is insufficient, the assistant says
  so instead of guessing.
- **Curated knowledge:** editorially reviewed FAQ answers are used
  first, with search across the source repositories as a fallback.
- **Your language:** ask in any supported language and get the answer in the
  same language, so working in English is not required.

The name refers to NAPCORE, the EU coordination initiative for National Access
Points to transport data, which these standards serve (www.napcore.eu).

## Requirements & design

The requirements and domain design are by:

- Andrej Tibaut
- Sara Guerra de Oliveira

both affiliated with University of Maribor
Faculty of Civil Engineering,
Transportation Engineering and Architecture,
Chair of Construction and Transportation Informatics (https://kgpi.fgpa.um.si/). They defined the standards scope (NeTEx/SIRI/OpRa/
Transmodel), the FAQ-first/RAG-fallback answer strategy, the citation and
abstention rules, and the editorial review workflow. The work is part of NAPCORE Task 4.3 Multimodal standards, led by Jorge Gonzalez, Multimodal and Digital Policy Officer at the French Ministry of Transport (DGITM). Active task partners are contributing during the pilot phase.

## Development approach

Development is led by Andrej Tibaut, who orchestrates the implementation and also
contributes directly to the code. AI-assisted coding tools support the
day-to-day work. As the commit history shows, development has been iterative
rather than planned in full up front:

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

1. **Foundations** (Mar 2026): initial project import; hybrid lexical+vector
   retrieval on PostgreSQL/pgvector; FAQ and RAG persistence and editorial
   RBAC scaffolding aligned to the C4 architecture.
2. **Ontology, GraphRAG & editorial maturation** (Apr to Jun 2026):
   XSD-to-ontology extraction pipeline and GraphDB-backed concept expansion;
   FAQ-first/RAG-fallback answer strategy; the editorial draft → review →
   approved/rejected → published workflow, KPI widgets, and board UI; Fedora
   VM + Docker Compose deployment automation.
3. **Answer-quality & reasoning-model hardening** (Jul 2026, the single
   largest push, over half of all commits to date): citation-grounding
   correctness (stop false rejections, prevent hallucinated [E#] references,
   lenient handling for code blocks); Qwen reasoning-model controller
   tuning; prompt-constraint and markdown-formatting fixes; multilingual
   abstain/insufficient-evidence phrasing.
4. **UI/UX refinement & release cadence** (Jul 2026, ongoing): user
   discovery features (Inspiring questions panel with smart caching);
   streamlined version display and deep-linking to individual Q&A
   exchanges; frequent patch releases; C4 diagram maintenance;
   Dependabot/security fixes; community contribution pathway via GitHub.
5. **Cross-standard ontology alignment & robustness** (Sep 2026, ongoing):
   migrated NeTEx/OpRa/SIRI source repositories to their current
   canonical GitHub orgs and reindexed; rewrote stale ontology alignments
   (825 NeTEx, 297 SIRI, 102 OpRa concepts now correctly mapped to the
   shared core ontology); fixed the GraphDB query structure that had
   silently prevented cross-standard concept expansion from ever working;
   corrected a production LLM model-alias regression and built a
   self-healing recovery mechanism, plus a public, browser-viewable LLM
   status endpoint, to make gateway drift visible instead of silently
   breaking answers; closed drift between the API and its documentation (OpenAPI
   spec, endpoint reference); dependency upgrades (React Router v7,
   Vitest v4).

See [Recent updates](recent-updates.md) for a detailed log of the latest
phase. Development is ongoing, and this timeline will grow as the project
evolves.

## Contributing

NAPCORE Helpdesk is open-source and developed collaboratively. We welcome
contributions, feedback, and ideas from the community. Because the project is
a work in progress, reports of incorrect, incomplete, or missing answers are
especially valuable. Visit the
[GitHub repository](https://github.com/UM-KGPI/NapcoreHelpdesk) to report
issues, propose features, submit pull requests, or review the codebase and
architecture. See [Contributing](../CONTRIBUTING.md) for development flow and
commit conventions.

## Where to go next

- [Architecture overview](architecture-overview.md): system design and runtime flow
- [Recent updates](recent-updates.md): latest feature and API changes
- [Installation](installation.md) / [Production deployment](production-deployment.md)
- [Contributing](../CONTRIBUTING.md): development flow and commit conventions
- [GitHub repository](https://github.com/UM-KGPI/NapcoreHelpdesk): source code and issue tracking
