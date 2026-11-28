import { describe, expect, it } from "vitest";

import { answerFromEvent, isNetworkFailure, recoverAnswer } from "./answerRecovery";

const saved = {
  questionEventId: "qe-1",
  requestId: "req-1",
  question: "Is there an element for a stop place entrance in NeTEx?",
  answer: "Yes. NeTEx defines `StopPlaceEntrance` [E1].",
  mode: "rag" as const,
  confidence: 0.94,
  citations: [{ label: null, sourcePath: "xsd/a.xsd", repositoryUrl: "https://github.com/x/NeTEx", chunkId: "c1" }],
  legalContext: [],
  createdAt: "2026-11-08T16:43:00Z",
};

describe("answerRecovery", () => {
  it("tells network failures from server errors", () => {
    expect(isNetworkFailure(new TypeError("Load failed"))).toBe(true);
    expect(isNetworkFailure(new Error("STREAM_ENDED: Stream closed without a done event."))).toBe(true);
    expect(isNetworkFailure(new Error("HTTP_500: Internal Server Error"))).toBe(false);
    const aborted = new Error("aborted");
    aborted.name = "AbortError";
    expect(isNetworkFailure(aborted)).toBe(false);
  });

  it("shows a saved event as an answer", () => {
    const answer = answerFromEvent(saved);
    expect(answer.answer).toBe(saved.answer);
    expect(answer.trace.requestId).toBe("req-1");
    expect(answer.citations[0].sourcePath).toBe("xsd/a.xsd");
  });

  it("polls until the server has saved the answer", async () => {
    let calls = 0;
    const client = {
      getQuestionEventDetail: async () => {
        calls += 1;
        if (calls < 3) throw new Error("HTTP_404");
        return saved;
      },
    };
    const answer = await recoverAnswer(client as never, "req-1", 10_000, 1, async () => undefined);
    expect(calls).toBe(3);
    expect(answer?.answer).toBe(saved.answer);
  });

  it("gives up after the timeout", async () => {
    const client = { getQuestionEventDetail: async () => { throw new Error("HTTP_404"); } };
    expect(await recoverAnswer(client as never, "req-1", 5, 1, async () => new Promise((r) => setTimeout(r, 2)))).toBeNull();
  });
});
