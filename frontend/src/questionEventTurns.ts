/**
 * The question and answer turns for a stored question event (GET /questions/events/{id}), shared by the
 * question page and the chat when a question is opened from "Inspiring questions" or a ?questionId= link.
 * The answer keeps everything the event stores: the generated example, the schema structure, the legal
 * context and the citations' titles.
 */
import type { ChatTurn } from "./components/UserChatWorkspace";
import type { AnswerResponse, QuestionEventDetail } from "./types";

type StoredQuestionEvent = QuestionEventDetail & { trace?: AnswerResponse["trace"] };

export function chatTurnsFromQuestionEvent(detail: StoredQuestionEvent): ChatTurn[] {
  const answer: AnswerResponse = {
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
    generatedExample: detail.generatedExample ?? null,
    schemaStructure: detail.schemaStructure ?? null,
    abstained: false,
    abstentionReason: null,
    reviewRequired: false,
    trace:
      detail.trace && Object.keys(detail.trace).length > 2
        ? detail.trace
        : {
            requestId: detail.requestId,
            questionEventId: detail.questionEventId,
            matchedFaqEntryId: null,
            retrievalEventIds: [],
            userLikes: false,
            userDislikes: false,
          },
  };
  return [
    { id: `${detail.requestId}-q`, role: "user", text: detail.question, createdAt: detail.createdAt },
    {
      id: `${detail.requestId}-a`,
      role: "assistant",
      text: detail.answer,
      createdAt: detail.createdAt,
      answer,
      requestId: detail.requestId,
    },
  ];
}
