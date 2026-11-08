/**
 * A NeTEx fragment generated for an "example with values" question, shown first in the answer. Labelled as
 * generated and with the NeTEx version it was validated against. Under the fragment, what each of its
 * elements is in the schema's own words (no model involved). Copy and download live in the answer's
 * action group (generatedExampleActions.ts). Renders a short note when no valid fragment could be
 * produced, and nothing when none was asked for.
 */
import type { GeneratedExample } from "../types";

export default function GeneratedExampleBlock({ example }: { example?: GeneratedExample | null }) {
  if (!example) {
    return null;
  }
  if (!example.valid || !example.xml) {
    return (
      <p className="tiny muted generated-example-note">
        No NeTEx example valid against the schema could be generated for these values; see the cited examples.
      </p>
    );
  }
  const version = example.schemaVersion ? `NeTEx ${example.schemaVersion}` : "NeTEx";
  const commit = example.schemaCommit ? ` (commit ${example.schemaCommit.slice(0, 7)})` : "";

  return (
    <section className="generated-example" aria-label="Generated NeTEx example">
      <h4>Generated example</h4>
      <p className="tiny generated-example-badge">
        Generated for this question · valid against {version}
        {commit} · built from the cited evidence
      </p>
      <pre>
        <code>{example.xml}</code>
      </pre>
      {example.elementNotes && example.elementNotes.length > 0 ? (
        <div className="generated-example-notes">
          <p className="tiny muted">What each element is, in the words of the NeTEx schema:</p>
          <dl>
            {example.elementNotes.map((note) => (
              <div key={note.name}>
                <dt>
                  <code>{note.name}</code>
                </dt>
                <dd>{note.documentation}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}
    </section>
  );
}
