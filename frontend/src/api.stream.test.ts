import { afterEach, describe, expect, it, vi } from "vitest";

import { HelpdeskApiClient, StreamUnavailableError } from "./api";
import type { AnswerRequest } from "./api";

const payload: AnswerRequest = { question: "Show me an example of a stop place with quays." };

function client(): HelpdeskApiClient {
  return new HelpdeskApiClient({ baseUrl: "http://helpdesk.test/api/v1", token: "t" });
}

function sseResponse(events: object[]): Response {
  const body = events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("");
  return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("answerQuestionStream", () => {
  it("skips status events and returns the done answer", async () => {
    const answer = { answer: "A StopPlace contains quays [E1].", trace: { requestId: "req-1" } };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([
      { type: "status", stage: "received" },
      { type: "status", stage: "retrieving" },
      { type: "status", stage: "generating" },
      { type: "token", delta: "A StopPlace contains quays [E1]." },
      { type: "done", answer },
    ])));
    const tokens: string[] = [];

    const result = await client().answerQuestionStream(payload, "req-1", (delta) => tokens.push(delta));

    expect(result).toEqual(answer);
    expect(tokens).toEqual(["A StopPlace contains quays [E1]."]);
  });

  it("reports a missing streaming endpoint as StreamUnavailableError", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("Not Found", { status: 404, statusText: "Not Found" })));

    await expect(client().answerQuestionStream(payload, "req-2", () => {})).rejects.toBeInstanceOf(StreamUnavailableError);
  });

  it("reports a proxy timeout as an ordinary error, so the caller does not ask again", async () => {
    const html = "<html><head><title>504 Gateway Time-out</title></head></html>";
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(html, { status: 504, statusText: "Gateway Time-out" })));

    const error = await client().answerQuestionStream(payload, "req-3", () => {}).catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(Error);
    expect(error).not.toBeInstanceOf(StreamUnavailableError);
    expect((error as Error).message).toBe("HTTP_504: Gateway Time-out");
  });

  it("keeps the server's error code and message for JSON errors", async () => {
    const body = JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Token expired." } });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, { status: 401, statusText: "Unauthorized" })));

    await expect(client().answerQuestionStream(payload, "req-4", () => {})).rejects.toThrow("UNAUTHORIZED: Token expired.");
  });
});
