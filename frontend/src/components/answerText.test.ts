import { describe, expect, it } from "vitest";

import { answerBodyText, generatedExampleText } from "./answerText";

const example = {
  valid: true,
  attempts: 1,
  xml: "<ResourceFrame/>",
  schemaVersion: "2.0",
  schemaCommit: "37ff1e453596",
  elementNotes: [{ name: "ResourceFrame", documentation: "A coherent set of reference values." }],
};

describe("answerText", () => {
  it("renders a valid example as badge, xml block and element notes", () => {
    const text = generatedExampleText(example);
    expect(text).toContain("Generated example for this question (valid against NeTEx 2.0, commit 37ff1e4):");
    expect(text).toContain("```xml\n<ResourceFrame/>\n```");
    expect(text).toContain("- ResourceFrame: A coherent set of reference values.");
  });

  it("renders nothing for a missing or invalid example", () => {
    expect(generatedExampleText(null)).toBe("");
    expect(generatedExampleText({ valid: false, attempts: 3 })).toBe("");
  });

  it("puts the example before the text, under a heading, and copes with either missing", () => {
    expect(answerBodyText("Plain answer.", example)).toMatch(/^Generated example[\s\S]*```\n[\s\S]*\n\nPlain answer\.$/);
    expect(answerBodyText("", example)).toBe(generatedExampleText(example));
    expect(answerBodyText("Plain answer.", null)).toBe("Plain answer.");
  });
});
