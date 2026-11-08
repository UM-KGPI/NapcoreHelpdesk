/**
 * Plain-text rendering of a generated NeTEx example, for "Copy answer" and "Export chat": the same
 * content the page shows (badge, fragment, what each element is), so those two actions cover the
 * example too and no separate "copy fragment" is needed.
 */
import type { GeneratedExample } from "../types";

export function generatedExampleText(example?: GeneratedExample | null): string {
  if (!example?.valid || !example.xml) {
    return "";
  }
  const version = example.schemaVersion ? `NeTEx ${example.schemaVersion}` : "NeTEx";
  const commit = example.schemaCommit ? ` (commit ${example.schemaCommit.slice(0, 7)})` : "";
  const lines = [
    `Generated example (generated for this question · valid against ${version}${commit} · built from the cited evidence):`,
    "```xml",
    example.xml,
    "```",
  ];
  if (example.elementNotes && example.elementNotes.length > 0) {
    lines.push("", "What each element is, in the words of the NeTEx schema:");
    for (const note of example.elementNotes) {
      lines.push(`- ${note.name}: ${note.documentation}`);
    }
  }
  return lines.join("\n");
}

/** The example first, then the text under "In the standard" when both exist; whichever exists otherwise. */
export function answerBodyText(text: string, example?: GeneratedExample | null, heading = "In the standard:"): string {
  const exampleText = generatedExampleText(example);
  const answerText = text.trim();
  if (exampleText && answerText) {
    return `${exampleText}\n\n${heading}\n${answerText}`;
  }
  return exampleText || answerText;
}
