/**
 * Static "About the project" page: origin, requirements authorship, and
 * development approach. Content mirrors docs/project-background.md; keep
 * the two in sync when either changes.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-07-02  |  Modified: 2026-11-06
 */

import systemContextDiagramUrl from "../assets/c4-system-context.svg";

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

// The knowledge pool as of 6 November 2026. Keep in sync with the sources in backend/helpdesk/services
// (regulations.ACTS, datex, inspire, napcore_site, source_refresh) and with docs/project-background.md.
const EURLEX = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:";

const CORE_STANDARDS = [
  {
    name: "Transmodel",
    what: "The reference data model for public transport (v6.2): its concepts and definitions, and the class pages of the published model with packages and diagrams.",
    url: "/napcore-helpdesk/transmodel/",
    source: "Transmodel model export",
  },
  { name: "NeTEx", what: "Network and timetable exchange: XSD schemas, examples and documentation.", url: "https://github.com/TransmodelEcosystem/NeTEx", source: "TransmodelEcosystem/NeTEx" },
  { name: "SIRI", what: "Real-time service information: XSD schemas, examples and documentation.", url: "https://github.com/TransmodelEcosystem/SIRI", source: "TransmodelEcosystem/SIRI" },
  { name: "OpRa", what: "Operating raw data exchange: XSD schemas, examples and documentation.", url: "https://github.com/TransmodelEcosystem/OpRa", source: "TransmodelEcosystem/OpRa" },
];

const NAMED_SOURCES = [
  {
    name: "DATEX II v3.7",
    what: "Road traffic and travel information: the data model (classes, enumerations, data types) and the documentation portal.",
    url: "https://docs.datex2.eu/v3.7/",
    source: "docs.datex2.eu",
  },
  {
    name: "TN-ITS",
    what: "Updates of road attributes such as speed limits (DATEX II Part 14): schemas, code lists, ontology and examples.",
    url: "https://github.com/ERTICO-TN-ITS/TN-ITS-Open",
    source: "ERTICO-TN-ITS/TN-ITS-Open",
  },
  {
    name: "INSPIRE Transport Networks",
    what: "The data specification on transport networks (Technical Guidelines D2.8.I.7, v2025.1), which MMTIS requires for the spatial network, and its 35 code lists.",
    url: "https://github.com/INSPIRE-MIF/technical-guidelines/tree/v2025.1/data/tn",
    source: "INSPIRE-MIF, INSPIRE registry",
  },
  {
    name: "mobilityDCAT-AP",
    what: "The metadata profile for describing mobility data in National Access Point catalogues, with its ontology.",
    url: "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP",
    source: "mobilityDCAT-AP/mobilityDCAT-AP",
  },
  {
    name: "NAPCORE",
    what: "NAPCORE's own pages, news and published deliverables, for questions about NAPCORE, National Access Points and National Bodies.",
    url: "https://napcore.eu/",
    source: "napcore.eu",
  },
];

const EU_ACTS = [
  { name: "MMTIS", act: "Delegated Regulation (EU) 2017/1926", version: "consolidated text of 4 March 2024", celex: "02017R1926-20240304" },
  { name: "MMTIS amendment", act: "Delegated Regulation (EU) 2024/490", version: "as adopted", celex: "32024R0490" },
  { name: "ITS Directive", act: "Directive 2010/40/EU", version: "consolidated text of 20 December 2023", celex: "02010L0040-20231220" },
  { name: "ITS Directive amendment", act: "Directive (EU) 2023/2661", version: "as adopted", celex: "32023L2661" },
  { name: "TEL TSI", act: "Implementing Regulation (EU) 2026/253", version: "as adopted", celex: "32026R0253" },
  { name: "INSPIRE Directive", act: "Directive 2007/2/EC", version: "consolidated text of 26 November 2024", celex: "02007L0002-20241126" },
  {
    name: "INSPIRE interoperability rules",
    act: "Regulation (EU) No 1089/2010",
    version: "consolidated text of 19 November 2023; articles and Annex II section 7 (Transport Networks) only",
    celex: "02010R1089-20231119",
  },
];

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
          European public transport data standards Transmodel, NeTEx, SIRI, and OpRa, and about the EU
          legislation that governs their data: the MMTIS Delegated Regulation (EU) 2017/1926, the ITS
          Directive 2010/40/EU and the TEL TSI (EU) 2026/253. Questions that name them are also answered
          from the road traffic standard DATEX II and TN-ITS (its Part 14 for road attribute updates), and
          from the INSPIRE Transport Networks specification that MMTIS requires for the spatial network.
          The full list is under <a href="#knowledge-pool">Knowledge pool</a> below.
        </p>
        <ul>
          <li><strong>Grounded answers:</strong> responses are based only on approved source repositories and the official EU legal texts, and cite the evidence they use. A Transmodel definition links to its class page in the Transmodel model (with its package and diagrams), and a legal answer links to the article on EUR-Lex.</li>
          <li><strong>Semantic technologies:</strong> the standards are modelled as linked data and stored in a GraphDB knowledge graph, with Transmodel as the shared reference model, helping the assistant find related concepts across standards. The terms the EU acts define form a vocabulary generated from the acts, linked to the standards the acts name.</li>
          <li><strong>Structure-aware answers:</strong> how two concepts are related (for example a LINE, its ROUTEs and the JOURNEY PATTERNs on them) and what two schemas have in common are computed from the standards' own structure, refreshed with every update of the source repositories, and cited as evidence.</li>
          <li><strong>Legal context:</strong> answers about NeTEx, SIRI or Transmodel list the provisions of the EU acts that name the standard, and questions about a standard's legal status (for example whether it is mandatory) are answered from those provisions.</li>
          <li><strong>AI as controller and narrator:</strong> a controller model checks whether a matched FAQ fits or the sources should be searched, and a narration model writes the answer from the retrieved evidence. Both are large language models used through an API.</li>
          <li><strong>Honest about gaps:</strong> when the evidence is insufficient, the assistant says so instead of guessing.</li>
          <li><strong>Curated knowledge:</strong> editorially reviewed FAQ answers are used first, with search across the source repositories as a fallback.</li>
          <li><strong>Your language:</strong> ask in any supported language and get the answer in the same language, so working in English is not required. Sources are found by meaning, with a multilingual embedding model, not only by shared words.</li>
        </ul>
        <p>
          The name refers to NAPCORE, the EU coordination initiative for National Access Points to
          transport data, which these standards serve (<a href="https://www.napcore.eu" target="_blank" rel="noreferrer">www.napcore.eu</a>).
        </p>
      </section>

      <section className="panel" id="knowledge-pool">
        <div className="panel-title-row">
          <h2>Knowledge pool</h2>
        </div>
        <p>
          The Helpdesk answers only from the sources below. Anything outside them, for example the GTFS
          specification itself or DATEX II versions before 3.7, is not in the pool: the Helpdesk then says it cannot answer rather than
          answering from general knowledge. Every answer cites the documents it used.
        </p>

        <h3>Public transport standards: searched for every question</h3>
        <p>The NeTEx, SIRI and OpRa repositories are refreshed every night from their GitHub repositories.</p>
        <div className="table-wrap">
          <table className="board-table">
            <thead>
              <tr><th>Standard</th><th>What is included</th><th>Source</th></tr>
            </thead>
            <tbody>
              {CORE_STANDARDS.map((item) => (
                <tr key={item.name}>
                  <td><strong>{item.name}</strong></td>
                  <td>{item.what}</td>
                  <td><a href={item.url} target="_blank" rel="noreferrer">{item.source}</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>Further standards and sources: searched when a question names them</h3>
        <p>
          These are searched only when the question mentions them (for example "In DATEX II, what is a
          SituationRecord?"), so they do not crowd out the public transport standards in other answers.
        </p>
        <div className="table-wrap">
          <table className="board-table">
            <thead>
              <tr><th>Name</th><th>What is included</th><th>Source</th></tr>
            </thead>
            <tbody>
              {NAMED_SOURCES.map((item) => (
                <tr key={item.name}>
                  <td><strong>{item.name}</strong></td>
                  <td>{item.what}</td>
                  <td><a href={item.url} target="_blank" rel="noreferrer">{item.source}</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>EU legislation</h3>
        <p>
          The official texts from the EU Publications Office, quoted by article and linked to EUR-Lex. They
          are searched when a question is about the law: when it names an act, asks about regulations or
          directives, or uses a term the acts define (for example "static travel data"). Answers about
          NeTEx, SIRI and Transmodel also show a Legal context line with the provisions that name the standard.
        </p>
        <div className="table-wrap">
          <table className="board-table">
            <thead>
              <tr><th>Short name</th><th>Act</th><th>Version indexed</th></tr>
            </thead>
            <tbody>
              {EU_ACTS.map((item) => (
                <tr key={item.celex}>
                  <td><strong>{item.name}</strong></td>
                  <td><a href={`${EURLEX}${item.celex}`} target="_blank" rel="noreferrer">{item.act}</a></td>
                  <td>{item.version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted tiny">
          Pool as of 6 November 2026. Missing a standard or act you need? Tell us with the feedback buttons
          under an answer, or contact the team (see Contributing below).
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>System context</h2>
        </div>
        <p>
          Who uses the helpdesk and which external systems it relies on (C4 model, level 1). Select the diagram to open it at full size.
        </p>
        <a className="about-diagram" href={systemContextDiagramUrl} target="_blank" rel="noreferrer">
          <img
            src={systemContextDiagramUrl}
            alt="C4 system context: NAP operators, transport authorities, transport operators, standards implementers and ITS system integrators ask questions, and editors review answers. The helpdesk indexes the NeTEx, SIRI and OpRa repositories on GitHub and publishes the Transmodel model from its own repository there, indexes the EU legislation from the EU Publications Office and links answers to EUR-Lex, queries the GraphDB ontology store, uses a large language model through an API, and downloads its multilingual embedding model once from Hugging Face."
          />
        </a>
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
          Chair of Construction and Transportation Informatics (<a href="https://kgpi.fgpa.um.si/" target="_blank" rel="noreferrer">kgpi.fgpa.um.si</a>). They defined the scope (the standards NeTEx/SIRI/OpRa/Transmodel and, since November 2026, the EU legislation that governs their data: MMTIS, the ITS Directive and the TEL TSI), the FAQ-first/RAG-fallback answer strategy, the citation and
          abstention rules, and the editorial review workflow. The work is part of NAPCORE Task 4.3 Multimodal standards, led by Jorge Gonzalez, Multimodal and Digital Policy Officer at the French Ministry of Transport (DGITM). Active task partners are contributing during the pilot phase.
        </p>
        <p>
          Collaborators who joined recently make important contributions to the requirements and to testing:
        </p>
        <ul>
          <li>David Ariño-Montoya</li>
          <li>Thibaut Barrère</li>
          <li>Valentina Carriero</li>
          <li>Nenad Čuš Babič</li>
          <li>Christophe Duquesne</li>
          <li>Brewenn Métayer</li>
          <li>Mario Scrocca</li>
          <li>Tu-Tho Thai</li>
        </ul>
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
          <li>CI quality gates (backend tests, OpenAPI schema, C4 diagram checks, Postgres integration, a retrieval benchmark that fails when answer evidence gets worse, and an nginx configuration check) were added early and extended alongside features rather than bolted on at the end.</li>
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
             single largest push, about 40% of all commits to date): citation-grounding
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
             102 OpRa concepts now correctly mapped to a shared core ontology, since replaced by Transmodel); fixed the
             GraphDB query structure that had silently prevented cross-standard concept
             expansion from ever working; corrected a production LLM model-alias regression and
             built a self-healing recovery mechanism, plus a public, browser-viewable LLM
             status endpoint, to make gateway drift visible instead of silently breaking answers; closed
             drift between the API and its documentation (OpenAPI spec, endpoint reference);
             dependency upgrades (React Router v7, Vitest v4).</li>
          <li><strong>Transmodel pivot &amp; structure-aware answers</strong> (Oct 2026, ongoing):
             replaced the separate core ontology with Transmodel as the single cross-standard
             reference and dropped DATEX II from scope; relation paths between concepts, with
             longer chains chosen where Transmodel's own definitions document each step; service
             abbreviations (e.g. SIRI-CA, SIRI-VM) read from the standards' READMEs and shared schema
             structure computed for comparison questions; matching everyday wording to model terms
             (e.g. "charging station" for RECHARGING STATION); stricter checks that claims about an
             element's purpose are grounded in a definition; a daily refresh of all indexed
             repositories at their real commits, and the standard ontologies regenerated from
             upstream with a weekly drift check; a maintenance page during deploys; faster and
             sturdier answers, with retrieval in about half the time and a stream that reports
             progress from the start, so long answers no longer time out; since 27 October, sources
             are found by meaning with a multilingual embedding model (multilingual-e5-small) running
             in the helpdesk's own embedding service. Collaborators recently joined and contribute to
             the requirements and testing.</li>
          <li><strong>EU legislation &amp; linked source models</strong> (Nov 2026, ongoing): the
             Transmodel model published as an Enterprise Architect HTML export, with each Transmodel
             definition in an answer linking to its class page (package and diagrams) by the class's
             EA GUID; the EU legislation added as a source: MMTIS, the ITS Directive and the TEL TSI
             from the EU Publications Office, as consolidated texts together with the amending acts,
             quoted by article and linked to EUR-Lex; a vocabulary of the 97 terms the acts define,
             generated from their definitions articles, so questions such as "What is static travel
             data?" reach the legislation; questions about a standard's legal status answered from the
             provisions that name it, and a Legal context line under answers about NeTEx, SIRI and
             Transmodel; sources searched only when a question names them: the INSPIRE Directive and the
             Transport Networks rules with their data specification and code lists, DATEX II v3.7 (its data
             model and documentation) and TN-ITS.</li>
        </ol>
        <p>
          Development is ongoing, and this timeline will grow as the project evolves.
        </p>
      </section>

      <section className="panel">
        <div className="panel-title-row">
          <h2>Contributing</h2>
        </div>
        <p>
          NAPCORE Helpdesk is developed collaboratively, and feedback from the community is very welcome. Because the project is a work in progress, reports of incorrect, incomplete, or missing answers are especially valuable: use the thumbs up and thumbs down buttons under each answer.
        </p>
        <p>
          The <a href="https://github.com/UM-KGPI/NapcoreHelpdesk" target="_blank" rel="noreferrer">GitHub repository</a> is currently private. NAPCORE task members can ask Andrej Tibaut or Sara Guerra de Oliveira for access, and collaborators can there:
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
          <h2>License</h2>
        </div>
        <p>
          Originally developed by the University of Maribor, Chair of Construction and Transportation Informatics (KGPI) (<a href="https://kgpi.fgpa.um.si/" target="_blank" rel="noreferrer">kgpi.fgpa.um.si</a>).
          The source code is licensed under the <a href="https://www.gnu.org/licenses/agpl-3.0.html" target="_blank" rel="noreferrer">GNU Affero General Public License v3.0</a> (AGPL-3.0-only), with additional attribution terms under its section 7.
          Content taken from the standards, EU legislation and napcore.eu keeps its original terms.
        </p>
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
