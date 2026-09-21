/**
 * Static "About the project" page — origin, requirements authorship, and
 * development approach. Content mirrors docs/project-background.md; keep
 * the two in sync when either changes.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-07-02  |  Modified: 2026-09-21
 */

interface AboutPageProps {
  appVersion: string;
  backendBuildRef?: string;
}

function extractBaseVersion(appVersion: string): string {
  const [baseVersion] = appVersion.split("+", 2);
  return baseVersion;
}

function extractBuildInfo(appVersion: string): string {
  const [, buildMetadata] = appVersion.split("+", 2);
  return buildMetadata || "dev";
}

export default function AboutPage({ appVersion }: AboutPageProps) {
  return (
    <section className="about-page">
      <section className="panel status-banner">
        <p>
          <strong>Status:</strong> This project is actively in development. The core functionality is stable and in pilot testing, but new features, refinements, and integrations are ongoing. The work is part of the NAPCORE Task 4.3 Multimodal Standards, with active contributions from task members.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Purpose</h2>
        </div>
        <p>
          NAPCORE Helpdesk is a multilingual Q&amp;A assistant for implementer questions
          about European public transport data standards — Transmodel, NeTEx, SIRI, and
          OpRa — grounded only in approved source repositories, with citations and an
          abstain path when evidence is insufficient. Questions can be asked in any of
          the supported languages and are answered in that same language, so
          implementers are not required to work in English. The name reflects NAPCORE,
          the EU coordination initiative for National Access Points to transport data,
          which these standards serve (<a href="https://www.napcore.eu" target="_blank" rel="noreferrer">www.napcore.eu</a>).
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Requirements &amp; design</h2>
        </div>
        <p>
          The requirements and domain design are credited throughout the codebase (see
          the header comment of most backend service modules) to:
        </p>
        <ul>
          <li>Andrej Tibaut</li>
          <li>Sara Guerra de Oliveira</li>
        </ul>
        <p>
          both affiliated with University of Maribor,
          Faculty of Civil Engineering,
          Transportation Engineering and Architecture,
          Chair of Construction and Transportation Informatics (<a href="https://kgpi.fgpa.um.si/" target="_blank" rel="noreferrer">kgpi.fgpa.um.si</a>). They defined the standards scope (NeTEx/SIRI/OpRa/Transmodel), the FAQ-first/RAG-fallback answer strategy, the citation and
          abstention guarantees, and the editorial review workflow. The work is part of the NAPCORE Task 4.3. Active task partners are contributing after the app launch.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Development approach</h2>
        </div>
        <p>
          Implementation was carried out by humans and by AI coding agents working under human
          direction — every service module in <code>backend/helpdesk/services/</code> and
          <code>backend/helpdesk/management/commands/</code> states this explicitly in its header
          (<code>Crafted by: AI coding agents</code>). The development style visible in the commit
          history is iterative rather than big-upfront-design:
        </p>
        <ul>
          <li>Small, scoped, conventionally-named commits (<code>feat(...)</code>, <code>fix(...)</code>, <code>chore(...)</code>, <code>docs(...)</code>).</li>
          <li>CI quality gates (backend tests, OpenAPI schema, C4 diagram checks, Postgres integration) were added early and extended alongside features rather than bolted on at the end.</li>
          <li>Fixes and reverts follow closely behind features shipped to real usage (e.g. the deep-link, spell-check, and GraphRAG definition-retrieval work), reflecting a "ship, observe, correct quickly" loop rather than long pre-verification cycles.</li>
        </ul>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Timeline (from git history)</h2>
        </div>
        <p>
          The project started on 2026-03-28 and has had continuous, active development
          since. Broad phases, in order:
        </p>
        <ol>
          <li><strong>Foundations</strong> (Mar 2026) — initial project import; hybrid
             lexical+vector retrieval on PostgreSQL/pgvector; FAQ and RAG persistence and
             editorial RBAC scaffolding aligned to the C4 architecture.</li>
          <li><strong>Ontology, GraphRAG &amp; editorial maturation</strong> (Apr–Jun 2026) —
             XSD-to-ontology extraction pipeline and GraphDB-backed concept expansion;
             FAQ-first/RAG-fallback answer strategy; the editorial draft → review →
             approved/rejected → published workflow, KPI widgets, and board UI; Fedora VM +
             Docker Compose deployment automation.</li>
          <li><strong>Answer-quality &amp; reasoning-model hardening</strong> (Jul 2026 — the
             single largest push, over half of all commits to date) — citation-grounding
             correctness (stop false rejections, prevent hallucinated [E#] references, lenient
             handling for code blocks); Qwen reasoning-model controller tuning; prompt-constraint
             and markdown-formatting fixes; multilingual abstain/insufficient-evidence
             phrasing.</li>
          <li><strong>UI/UX refinement &amp; release cadence</strong> (Jul 2026, ongoing) — user
             discovery features (Inspiring questions panel with smart caching); streamlined
             version display and deep-linking to individual Q&amp;A exchanges; frequent patch
             releases; C4 diagram maintenance; Dependabot/security fixes; community contribution
             pathway via GitHub.</li>
          <li><strong>Cross-standard ontology alignment &amp; production readiness</strong> (Sep
             2026) — migrated NeTEx/OpRa/SIRI source repositories to their current canonical
             GitHub orgs and reindexed; rewrote stale ontology alignments (825 NeTEx, 297 SIRI,
             102 OpRa concepts now correctly mapped to the shared core ontology); fixed the
             GraphDB query structure that had silently prevented cross-standard concept
             expansion from ever working; corrected a production LLM model-alias regression and
             built a self-healing recovery mechanism, plus a live LLM status endpoint and
             browser page, so future gateway drift no longer breaks answers silently; closed
             drift between the API and its documentation (OpenAPI spec, endpoint reference);
             dependency upgrades (React Router v7, Vitest v4).</li>
        </ol>
        <p>
          See{" "}
          <a
            href="https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/recent-updates.md"
            target="_blank"
            rel="noreferrer"
          >
            Recent updates
          </a>{" "}
          for a detailed log of the latest phase.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Contributing</h2>
        </div>
        <p>
          NAPCORE Helpdesk is open-source and developed collaboratively. We welcome contributions, feedback, and ideas from the community.
        </p>
        <p>
          Visit the <a href="https://github.com/UM-KGPI/NapcoreHelpdesk" target="_blank" rel="noreferrer">GitHub repository</a> to:
        </p>
        <ul>
          <li>Report issues and bugs</li>
          <li>Propose new features and improvements</li>
          <li>Submit pull requests</li>
          <li>Review the codebase and architecture</li>
          <li>Follow development progress</li>
        </ul>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Version information</h2>
        </div>
        <dl className="version-info">
          <dt>Application version:</dt>
          <dd>v{extractBaseVersion(appVersion)}</dd>
          <dt>Build:</dt>
          <dd>{extractBuildInfo(appVersion)}</dd>
        </dl>
      </section>
    </section>
  );
}
