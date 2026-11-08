/**
 * A NeTEx fragment generated for an "example with values" question, shown first in the answer. Labelled as
 * generated and with the NeTEx version it was validated against. Under the fragment, what each of its
 * elements is in the schema's own words (no model involved). The download button sits on the fragment
 * (it belongs to this block); copying is covered by the answer's "Copy answer". Renders a short note when no valid fragment could be
 * produced, and nothing when none was asked for.
 */
import { downloadExampleDocument } from "./generatedExampleActions";
import type { GeneratedExample } from "../types";

/** "valid against NeTEx 2.0, commit 37ff1e4": the version and commit the fragment was validated against. */
export function validityNote(example: GeneratedExample): string {
  const version = example.schemaVersion ? `NeTEx ${example.schemaVersion}` : "NeTEx";
  return `valid against ${version}${example.schemaCommit ? `, commit ${example.schemaCommit.slice(0, 7)}` : ""}`;
}

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
  return (
    <section className="generated-example" aria-label="Generated NeTEx example">
      <h4>
        Generated example for this question{" "}
        <span className="generated-example-badge">({validityNote(example)})</span>
      </h4>
      {example.valuePlaces && example.valuePlaces.length > 0 ? (
        <ul className="generated-example-lead" aria-label="Where the question's values go">
          {example.valuePlaces.map((place) => (
            <li key={`${place.value}-${place.element}`}>
              <strong>{place.value}</strong> → <code>{place.element}</code>
              {place.path.length > 0 ? (
                <span className="muted"> in {place.path.slice(-3).join(" › ")}</span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="generated-example-code">
        <pre>
          <code>{example.xml}</code>
        </pre>
        <button
          type="button"
          className="chat-icon-button generated-example-download"
          onClick={() => downloadExampleDocument(example)}
          title="Download generated example as XML file"
          aria-label="Download generated example as XML file"
        >
          ⬇️
        </button>
      </div>
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
