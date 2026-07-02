/**
 * Static "About the project" page — origin, requirements authorship, and
 * development approach. Content mirrors docs/project-background.md; keep
 * the two in sync when either changes.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

export default function AboutPage() {
  return (
    <section className="workspace-section about-page">
      <section className="panel">
        <div className="panel-title-row">
          <h2>About NAPCORE Helpdesk</h2>
          <p>Where the project came from, who defined it, and how it was built.</p>
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
          The requirements and domain design are credited throughout the codebase to
          Andrej Tibaut and Sara Guerra de Oliveira, both affiliated with the University
          of Maribor, Faculty of Civil Engineering, Transportation Engineering and
          Architecture, Chair of Construction and Transportation Informatics
          (<a href="https://kgpi.fgpa.um.si/" target="_blank" rel="noreferrer">kgpi.fgpa.um.si</a>).
          They defined the standards scope (NeTEx/SIRI/OpRa/Transmodel), the
          FAQ-first/RAG-fallback answer strategy, the citation and abstention
          guarantees, and the editorial review workflow. The work is part of NAPCORE
          WG3; members of the workgroup are actively contributing after the app launch.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Development approach</h2>
        </div>
        <p>
          Implementation was carried out by humans and by AI coding agents working
          under human direction. The development style is iterative rather than
          big-upfront-design: small, scoped, conventionally-named commits; CI quality
          gates added early and extended alongside features; fixes following closely
          behind features shipped to real usage rather than long pre-verification
          cycles.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Timeline</h2>
        </div>
        <ol>
          <li><strong>Foundations</strong> — initial project import; hybrid lexical+vector retrieval on PostgreSQL/pgvector; FAQ and RAG persistence aligned to the C4 architecture.</li>
          <li><strong>Editorial workflow</strong> — RBAC-based draft → review → approved/rejected → published queue, KPI widgets, and board UI.</li>
          <li><strong>CI/ops hardening</strong> — backend, OpenAPI, and C4 quality gates; health probes; security and release automation.</li>
          <li><strong>Pilot testing</strong> — first-user testing pack and feedback workflow.</li>
          <li><strong>Production deployment &amp; GraphRAG</strong> — Fedora VM + Docker Compose deployment; GraphDB-backed concept expansion; XSD-to-ontology extraction pipeline providing authoritative concept definitions; multilingual question support; deep-linking to individual Q&amp;A exchanges.</li>
        </ol>
      </section>
    </section>
  );
}
