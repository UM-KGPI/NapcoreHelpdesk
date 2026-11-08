/**
 * A NeTEx fragment generated for an "example with values" question, shown under the answer. Labelled as
 * generated (not an example from the standard) and with the NeTEx version it was validated against.
 * Under the fragment, what each of its elements is in the schema's own words (no model involved).
 * Renders a short note when no valid fragment could be produced, and nothing when none was asked for.
 */
import { useState } from "react";

import type { GeneratedExample } from "../types";

export default function GeneratedExampleBlock({ example }: { example?: GeneratedExample | null }) {
  const [copied, setCopied] = useState(false);
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

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(example.xml ?? "");
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const download = () => {
    const blob = new Blob([example.document ?? example.xml ?? ""], { type: "application/xml" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "netex-generated-example.xml";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="generated-example" aria-label="Generated NeTEx example">
      <h4>Generated example</h4>
      <p className="tiny generated-example-badge">
        Generated for this question, not taken from the standard · valid against {version}
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
      <p className="tiny generated-example-actions">
        <button type="button" onClick={() => void copy()}>
          {copied ? "Copied" : "Copy fragment"}
        </button>{" "}
        <button type="button" onClick={download}>
          Download as PublicationDelivery
        </button>
      </p>
    </section>
  );
}
