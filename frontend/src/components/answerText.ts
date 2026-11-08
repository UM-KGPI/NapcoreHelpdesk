/**
 * Plain-text rendering of the blocks taken from the schema (a generated example, or what an element
 * contains), for "Copy answer" and "Export chat": the same content the page shows, so those two actions
 * cover the blocks too.
 */
import { citationDisplayName, citationMarker } from "../citationLabels";
import { validityNote } from "./GeneratedExample";
import type { AnswerResponse, GeneratedExample, SchemaStructure } from "../types";

export function generatedExampleText(example?: GeneratedExample | null): string {
  if (!example?.valid || !example.xml) {
    return "";
  }
  const lines = [
    `Generated example for this question (${validityNote(example)}):`,
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

/** The block first, then the text when both exist; whichever exists otherwise. */
export function answerBodyText(
  text: string,
  example?: GeneratedExample | null,
  structure?: SchemaStructure | null,
): string {
  const block = blockText(example, structure);
  const answerText = text.trim();
  if (block && answerText) {
    return `${block}\n\n${answerText}`;
  }
  return block || answerText;
}

/**
 * What "Copy answer" puts on the clipboard: everything the answer shows, in page order. The block from
 * the schema and the text (answerBodyText), the evidence list, and the "Legal context" line.
 */
export function copiedAnswerText(text: string, answer?: AnswerResponse | null): string {
  const lines: string[] = [];
  const body = answerBodyText(text, answer?.generatedExample, answer?.schemaStructure);
  if (body) {
    lines.push(body);
  }
  const citations = answer?.citations ?? [];
  if (citations.length > 0) {
    lines.push("", "Evidence list:");
    citations.forEach((citation, index) => {
      lines.push(`- ${citationMarker(citation, index)} ${citationDisplayName(citation)} | ${citation.sourcePath} | ${citation.repositoryUrl}`);
    });
  }
  const legal = answer?.legalContext ?? [];
  if (legal.length > 0) {
    lines.push("", "Legal context:");
    for (const item of legal) {
      lines.push(`- ${item.label} | ${item.url}`);
    }
  }
  return lines.join("\n").trim();
}
