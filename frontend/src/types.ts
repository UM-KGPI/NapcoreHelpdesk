export type StandardsScope = "Transmodel" | "NeTEx" | "SIRI" | "OJP/OpRa" | "DATEX II";

export type AnswerMode = "faq" | "rag" | "abstain";

export interface Citation {
  repositoryUrl: string;
  commitSha: string;
  sourcePath: string;
  chunkId: string;
  label?: string;
}

export interface AnswerTrace {
  requestId: string;
  questionEventId: string;
  matchedFaqEntryId: string | null;
  retrievalEventIds: string[];
  evidenceLinkIds?: string[];
}

export interface AnswerResponse {
  answerId: string;
  mode: AnswerMode;
  confidence: number;
  answer: string;
  citations: Citation[];
  abstained: boolean;
  abstentionReason: string | null;
  reviewRequired: boolean;
  trace: AnswerTrace;
}

export interface PromotionCandidate {
  normalizedIntent: string;
  questionCount: number;
  notHelpfulRate: number;
  lastAskedAt: string;
  recommendedAction: "CREATE_FAQ_DRAFT" | "REVIEW_EXISTING_FAQ" | "MONITOR";
}

export interface PromotionCandidatesResponse {
  windowDays: number;
  minCount: number;
  items: PromotionCandidate[];
}

export interface EditorialQueueResponse {
  queued: boolean;
  queueItemId: string;
  status: string;
}

export interface EditorialTransition {
  action: "submit_for_review" | "request_changes" | "approve" | "reject" | "publish" | "reopen";
  fromStatus: string;
  toStatus: string;
  actorId: string;
  actorRoles: string[];
}

export interface EditorialQueueTransitionResponse {
  queueItemId: string;
  status: string;
  transition: EditorialTransition;
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    requestId?: string;
  };
}
