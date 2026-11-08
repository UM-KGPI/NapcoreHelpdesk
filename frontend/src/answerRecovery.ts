/**
 * Recovering an answer whose stream was cut off by the network.
 *
 * On a phone, a long answer's connection can drop ("Load failed" in Safari) while the server keeps working:
 * the answer stream runs in its own thread on the server and the finished answer is saved under the
 * request id. So instead of asking again (which would repeat the whole pipeline and double the wait), the
 * app fetches the saved answer by its request id until it is there.
 */
import type { HelpdeskApiClient } from "./api";
import type { AnswerResponse, QuestionEventDetail } from "./types";

/** A failure of the network itself (no HTTP response), not an error the server answered with. */
export function isNetworkFailure(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }
  if (error.name === "AbortError") {
    return false;
  }
  return (
    error instanceof TypeError ||
    /load failed|failed to fetch|networkerror|network connection|the network connection was lost|STREAM_ENDED/i.test(error.message)
  );
}

/** A saved question event shown as an answer (what the stream's "done" event would have carried). */
export function answerFromEvent(detail: QuestionEventDetail & { trace?: Record<string, unknown> }): AnswerResponse {
  const trace = (detail.trace ?? {}) as Record<string, unknown>;
  return {
    answerId: detail.questionEventId,
    mode: detail.mode || "rag",
    confidence: detail.confidence,
    answer: detail.answer,
    citations: (detail.citations || []).map((c) => ({
      repositoryUrl: c.repositoryUrl,
      commitSha: "",
      sourcePath: c.sourcePath,
      chunkId: c.chunkId,
      label: c.label ?? undefined,
      title: c.title,
    })),
    legalContext: detail.legalContext ?? [],
    abstained: detail.mode === "abstain",
    abstentionReason: null,
    reviewRequired: false,
    generatedExample: detail.generatedExample ?? null,
    schemaStructure: detail.schemaStructure ?? null,
    trace: {
      ...(trace as object),
      requestId: detail.requestId,
      questionEventId: detail.questionEventId,
      matchedFaqEntryId: (trace.matchedFaqEntryId as string | null) ?? null,
      retrievalEventIds: (trace.retrievalEventIds as string[]) ?? [],
    } as AnswerResponse["trace"],
  };
}

/**
 * The saved answer for a request id, polled every `intervalMs` until it is there or `timeoutMs` has passed
 * (null then). A 404 means the server is still working on it.
 */
export async function recoverAnswer(
  client: Pick<HelpdeskApiClient, "getQuestionEventDetail">,
  requestId: string,
  timeoutMs = 120_000,
  intervalMs = 3_000,
  sleep: (ms: number) => Promise<void> = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms)),
): Promise<AnswerResponse | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const detail = await client.getQuestionEventDetail(requestId);
      if (detail && detail.answer !== undefined) {
        return answerFromEvent(detail as QuestionEventDetail & { trace?: Record<string, unknown> });
      }
    } catch {
      // Not saved yet (404) or the network is still away: try again.
    }
    await sleep(intervalMs);
  }
  return null;
}
