/**
 * Plain-text rendering of the blocks taken from the schema (a generated example, or what an element
 * contains), for "Copy answer" and "Export chat": the same content the page shows, so those two actions
 * cover the blocks too.
 */
import type { GeneratedExample, SchemaStructure } from "../types";

export function generatedExampleText(example?: GeneratedExample | null): string {
  if (!example?.valid || !example.xml) {
    return "";
  }
  const version = example.schemaVersion ? `NeTEx ${example.schemaVersion}` : "NeTEx";
  const commit = example.schemaCommit ? ` (commit ${example.schemaCommit.slice(0, 7)})` : "";
  const lines = [
    `Generated example (generated for this question · valid against ${version}${commit} · built from the cited evidence):`,
    ...(example.valuePlaces ?? []).map(
      (place) => `- ${place.value} → ${place.element}${place.path.length ? ` in ${place.path.slice(-3).join(" › ")}` : ""}`,
    ),
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

export function schemaStructureText(structure?: SchemaStructure | null): string {
  if (!structure) {
    return "";
  }
  const lines = [`What ${structure.element} contains, from the NeTEx schema${structure.source ? ` (${structure.source})` : ""}:`];
  if (structure.documentation) {
    lines.push(structure.documentation);
  }
  for (const group of structure.groups) {
    lines.push("", group.inherited ? `Inherited as ${group.owner}:` : "Its own elements:");
    for (const child of group.children) {
      lines.push(`- ${child.name}: ${child.documentation}`);
    }
  }
  if (structure.attributes.length > 0) {
    lines.push("", "Attributes:");
    for (const attribute of structure.attributes) {
      lines.push(`- ${attribute.name}: ${attribute.documentation}`);
    }
  }
  return lines.join("\n");
}

/** The block shown first, as text: the valid example when there is one, else the structure, else nothing. */
export function blockText(example?: GeneratedExample | null, structure?: SchemaStructure | null): string {
  return generatedExampleText(example) || schemaStructureText(structure);
}

/** The block first, then the text under "In the standard" when both exist; whichever exists otherwise. */
export function answerBodyText(
  text: string,
  example?: GeneratedExample | null,
  structure?: SchemaStructure | null,
  heading = "In the standard:",
): string {
  const block = blockText(example, structure);
  const answerText = text.trim();
  if (block && answerText) {
    return `${block}\n\n${heading}\n${answerText}`;
  }
  return block || answerText;
}
