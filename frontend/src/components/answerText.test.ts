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
    expect(text).toContain("generated for this question · valid against NeTEx 2.0 (commit 37ff1e4)");
    expect(text).toContain("```xml\n<ResourceFrame/>\n```");
    expect(text).toContain("- ResourceFrame: A coherent set of reference values.");
  });

  it("renders nothing for a missing or invalid example", () => {
    expect(generatedExampleText(null)).toBe("");
    expect(generatedExampleText({ valid: false, attempts: 3 })).toBe("");
  });

  it("puts the example before the text, under a heading, and copes with either missing", () => {
    expect(answerBodyText("Plain answer.", example)).toMatch(/^Generated example[\s\S]*\n\nIn the standard:\nPlain answer\.$/);
    expect(answerBodyText("", example)).toBe(generatedExampleText(example));
    expect(answerBodyText("Plain answer.", null)).toBe("Plain answer.");
  });
});

describe("copiedAnswerText", () => {
  it("copies the text, the evidence list and the legal context, in page order", async () => {
    const { copiedAnswerText } = await import("./answerText");
    const answer = {
      citations: [{ repositoryUrl: "https://github.com/TransmodelEcosystem/NeTEx", commitSha: "abc", sourcePath: "xsd/a.xsd", chunkId: "c1" }],
      legalContext: [
        { label: "MMTIS Art. 4", url: "https://eur-lex.europa.eu/x#art_4" },
        { label: "TEL TSI App. C", url: "https://eur-lex.europa.eu/y#app_C" },
      ],
    } as never;
    const text = copiedAnswerText("A StopPlace is a place [E1].", answer);
    expect(text.startsWith("A StopPlace is a place [E1].\n\nEvidence list:\n- ")).toBe(true);
    expect(text).toContain("| xsd/a.xsd | https://github.com/TransmodelEcosystem/NeTEx");
    expect(text.endsWith("Legal context:\n- MMTIS Art. 4 | https://eur-lex.europa.eu/x#art_4\n- TEL TSI App. C | https://eur-lex.europa.eu/y#app_C")).toBe(true);
    expect(text.indexOf("Evidence list:")).toBeLessThan(text.indexOf("Legal context:"));
  });

  it("leaves out empty sections", async () => {
    const { copiedAnswerText } = await import("./answerText");
    expect(copiedAnswerText("Only text.", { citations: [], legalContext: [] } as never)).toBe("Only text.");
  });
});
