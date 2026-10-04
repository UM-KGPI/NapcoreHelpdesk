/**
 * Static "About the project" page: origin, requirements authorship, and
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
          <strong>Work in progress:</strong> NAPCORE Helpdesk is under active development and currently in pilot testing. Answers may be incomplete or occasionally inaccurate. Always check them against the cited sources and the official standard documentation. Coverage, features, and behaviour may change between releases, and your feedback directly shapes what comes next. The work is part of the NAPCORE Task 4.3 Multimodal standards, with active contributions from task members.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Purpose</h2>
        </div>
        <p>
          NAPCORE Helpdesk helps implementers get reliable answers to their questions about the
          European public transport data standards Transmodel, NeTEx, SIRI, and OpRa.
        </p>
        <ul>
          <li><strong>Grounded answers:</strong> responses are based only on approved source repositories and cite the evidence they use.</li>
          <li><strong>Honest about gaps:</strong> when the evidence is insufficient, the assistant says so instead of guessing.</li>
          <li><strong>Curated knowledge:</strong> editorially reviewed FAQ answers are used first, with search across the source repositories as a fallback.</li>
          <li><strong>Your language:</strong> ask in any supported language and get the answer in the same language, so working in English is not required.</li>
        </ul>
        <p>
          The name refers to NAPCORE, the EU coordination initiative for National Access Points to
          transport data, which these standards serve (<a href="https://www.napcore.eu" target="_blank" rel="noreferrer">www.napcore.eu</a>).
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Requirements &amp; design</h2>
        </div>
        <p>
          The requirements and domain design are by:
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
          abstention rules, and the editorial review workflow. The work is part of the NAPCORE Task 4.3 Multimodal standards. Active task partners are contributing during the pilot phase.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Development approach</h2>
        </div>
        <p>
          Development is led by Andrej Tibaut, who orchestrates the implementation and also
          contributes directly to the code. AI-assisted coding tools support the day-to-day
          work. As the commit history shows, development has been iterative rather than
          planned in full up front:
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
          <li><strong>Foundations</strong> (Mar 2026): initial project import; hybrid
             lexical+vector retrieval on PostgreSQL/pgvector; FAQ and RAG persistence and
             editorial RBAC scaffolding aligned to the C4 architecture.</li>
          <li><strong>Ontology, GraphRAG &amp; editorial maturation</strong> (Apr to Jun 2026):
             XSD-to-ontology extraction pipeline and GraphDB-backed concept expansion;
             FAQ-first/RAG-fallback answer strategy; the editorial draft → review →
             approved/rejected → published workflow, KPI widgets, and board UI; Fedora VM +
             Docker Compose deployment automation.</li>
          <li><strong>Answer-quality &amp; reasoning-model hardening</strong> (Jul 2026, the
             single largest push, over half of all commits to date): citation-grounding
             correctness (stop false rejections, prevent hallucinated [E#] references, lenient
             handling for code blocks); Qwen reasoning-model controller tuning; prompt-constraint
             and markdown-formatting fixes; multilingual abstain/insufficient-evidence
             phrasing.</li>
          <li><strong>UI/UX refinement &amp; release cadence</strong> (Jul 2026, ongoing): user
             discovery features (Inspiring questions panel with smart caching); streamlined
             version display and deep-linking to individual Q&amp;A exchanges; frequent patch
             releases; C4 diagram maintenance; Dependabot/security fixes; community contribution
             pathway via GitHub.</li>
          <li><strong>Cross-standard ontology alignment &amp; robustness</strong> (Sep
             2026, ongoing): migrated NeTEx/OpRa/SIRI source repositories to their current canonical
             GitHub orgs and reindexed; rewrote stale ontology alignments (825 NeTEx, 297 SIRI,
             102 OpRa concepts now correctly mapped to the shared core ontology); fixed the
             GraphDB query structure that had silently prevented cross-standard concept
             expansion from ever working; corrected a production LLM model-alias regression and
             built a self-healing recovery mechanism, plus a public, browser-viewable LLM
             status endpoint, to make gateway drift visible instead of silently breaking answers; closed
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
          for a detailed log of the latest phase. Development is ongoing, and this timeline will
          grow as the project evolves.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Contributing</h2>
        </div>
        <p>
          NAPCORE Helpdesk is open-source and developed collaboratively. We welcome contributions, feedback, and ideas from the community. Because the project is a work in progress, reports of incorrect, incomplete, or missing answers are especially valuable.
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
        {extractBaseVersion(appVersion).startsWith("0.") && (
          <p>Pre-1.0 release: features and behaviour may still change.</p>
        )}
      </section>
    </section>
  );
}
