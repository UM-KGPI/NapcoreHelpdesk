/**
 * A NeTEx fragment generated for an "example with values" question, shown first in the answer. Labelled as
 * generated and with the NeTEx version it was validated against. Under the fragment, what each of its
 * elements is in the schema's own words (no model involved). The download button sits on the fragment
 * (it belongs to this block); copying is covered by the answer's "Copy answer". Renders a short note when no valid fragment could be
 * produced, and nothing when none was asked for.
 */
import { downloadExampleDocument } from "./generatedExampleActions";
import type { GeneratedExample } from "../types";

/** "valid against NeTEx 2.0, commit 37ff1e4"; for an excerpt that did not validate on its own, "as published, commit …". */
export function validityNote(example: GeneratedExample): string {
  const version = example.schemaVersion ? `NeTEx ${example.schemaVersion}` : "NeTEx";
  const commit = example.schemaCommit ? `, commit ${example.schemaCommit.slice(0, 7)}` : "";
  if (example.origin === "standard" && example.excerpt) {
    return `excerpt as published${commit}`;
  }
  if (example.origin === "standard" && example.validated === false) {
    return `as published${commit}`;
  }
  return `valid against ${version}${commit}`;
}

/** " (does not contain the asked values 5, EUR)" */
export function withoutValuesSuffix(example: GeneratedExample): string {
  const values = example.missingValues ?? [];
  return values.length ? ` (does not contain the asked values ${values.join(", ")})` : " (does not contain the asked values)";
}

/** The example's title line: generated for the question, or taken from a named file of the standard. */
export function exampleTitle(example: GeneratedExample): string {
  if (example.origin === "standard") {
    const file = (example.sourcePath ?? "").split("/").pop() || "the standard's examples";
    return `Example from the standard: ${file}${example.holdsValues === false ? withoutValuesSuffix(example) : ""}`;
  }
  return "Generated example for this question";
}

/** For a standard example shown because no generated one validated: it does not hold the asked values. */
export function missingValuesText(example: GeneratedExample): string {
  const values = example.missingValues ?? [];
  const asked = values.length ? `the asked values ${values.join(", ")}` : "the asked values";
  return `No example with ${asked} validated against the schema; this example from the standard shows the same kind of object and does not contain them.`;
}

/** "In this example nothing links the VehicleType and 2 ScheduledStopPoints to the Line."; "" when all are linked.
 * Same wording as the backend's unlinked_text (netex_example_generator.py), which the answer text is told not to contradict. */
export function unlinkedObjectsText(example: GeneratedExample): string {
  const unlinked = example.unlinkedObjects ?? [];
  if (!unlinked.length || !example.askedObject) {
    return "";
  }
  const counts = new Map<string, number>();
  unlinked.forEach((item) => counts.set(item.element, (counts.get(item.element) ?? 0) + 1));
  const parts = [...counts].map(([name, n]) => (n > 1 ? `${n} ${name}s` : `the ${name}`));
  const listed = parts.length === 1 ? parts[0] : `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`;
  return `In this example nothing links ${listed} to the ${example.askedObject}.`;
}

/** "two → 2 × Quay in StopPlace › quays", "49 → SeatingCapacity in … › PassengerCapacity". */
export function placeText(place: { value: string; element: string; path: string[]; count?: number }): string {
  const where = place.path.length ? ` in ${place.path.slice(-3).join(" › ")}` : "";
  return place.count ? `${place.value} → ${place.count} × ${place.element}${where}` : `${place.value} → ${place.element}${where}`;
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
    <section className="generated-example" aria-label={example.origin === "standard" ? "NeTEx example from the standard" : "Generated NeTEx example"}>
      <h4>
        {example.origin === "standard" && example.sourceUrl ? (
          <>
            Example from the standard:{" "}
            <a href={example.sourceUrl} target="_blank" rel="noreferrer">
              {(example.sourcePath ?? "").split("/").pop()}
            </a>
            {example.holdsValues === false ? withoutValuesSuffix(example) : ""}
          </>
        ) : (
          exampleTitle(example)
        )}{" "}
        <span className="generated-example-badge">({validityNote(example)})</span>
      </h4>
      {example.holdsValues === false ? (
        <p className="generated-example-lead">
          {missingValuesText(example)}
        </p>
      ) : null}
      {unlinkedObjectsText(example) ? <p className="generated-example-lead">{unlinkedObjectsText(example)}</p> : null}
      {example.valuePlaces && example.valuePlaces.length > 0 ? (
        <ul className="generated-example-lead" aria-label="Where the question's values go">
          {example.valuePlaces.map((place) => (
            <li key={`${place.value}-${place.element}`}>
              <strong>{place.value}</strong> → {place.count ? `${place.count} × ` : ""}
              <code>{place.element}</code>
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
