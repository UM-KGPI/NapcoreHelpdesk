import { describe, expect, it } from "vitest";

import { chatTurnsFromQuestionEvent } from "./questionEventTurns";

describe("chatTurnsFromQuestionEvent", () => {
  it("keeps the generated example, structure, legal context and citation titles of a stored answer", () => {
    const [question, answer] = chatTurnsFromQuestionEvent({
      questionEventId: "qe1",
      requestId: "req1",
      question: "Give a NeTEx example of a stop place with a parking of 40 spaces",
      answer: "See the example [E1].",
      mode: "rag",
      confidence: 0.8,
      citations: [{ label: "E1", sourcePath: "a/b.xml", repositoryUrl: "https://x/a", chunkId: "c1", title: "T" }],
      legalContext: [{ label: "MMTIS Art. 4", url: "https://eur-lex.europa.eu/x" }],
      generatedExample: { valid: true, attempts: 1, xml: "<StopPlace/>" },
      schemaStructure: null,
      createdAt: "2026-11-10T10:00:00Z",
    });
    expect(question.text).toContain("stop place");
    expect(answer.answer?.generatedExample?.xml).toBe("<StopPlace/>");
    expect(answer.answer?.legalContext).toHaveLength(1);
    expect(answer.answer?.citations[0]).toMatchObject({ label: "E1", title: "T" });
    expect(answer.requestId).toBe("req1");
  });
});
