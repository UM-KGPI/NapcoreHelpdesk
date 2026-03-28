import type {
  AnswerResponse,
  ApiErrorEnvelope,
  EditorialQueueResponse,
  PromotionCandidatesResponse,
  StandardsScope,
} from "./types";

export interface AnswerRequest {
  question: string;
  sessionId?: string;
  userId?: string;
  standardsScope?: StandardsScope[];
  language?: string;
  options?: {
    maxCitations?: number;
    allowAbstain?: boolean;
    faqMinConfidence?: number;
    retrievalTopK?: number;
    retrievalMinScore?: number;
  };
}

export interface EditorialQueueRequest {
  questionEventId: string;
  reason: "LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION";
  priority?: "low" | "normal" | "high";
}

interface ApiClientConfig {
  baseUrl: string;
  token: string;
}

const defaultHeaders = {
  "Content-Type": "application/json",
};

export class HelpdeskApiClient {
  private readonly baseUrl: string;
  private readonly token: string;

  constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.token = config.token;
  }

  async answerQuestion(payload: AnswerRequest, requestId: string): Promise<AnswerResponse> {
    return this.request<AnswerResponse>("/questions/answer", {
      method: "POST",
      headers: {
        "X-Request-Id": requestId,
      },
      body: JSON.stringify(payload),
    });
  }

  async listPromotionCandidates(windowDays: number, minCount: number, onlyUnresolved: boolean): Promise<PromotionCandidatesResponse> {
    const params = new URLSearchParams({
      windowDays: String(windowDays),
      minCount: String(minCount),
      onlyUnresolved: String(onlyUnresolved),
    });
    return this.request<PromotionCandidatesResponse>(`/faqs/promotion-candidates?${params.toString()}`, {
      method: "GET",
    });
  }

  async routeToEditorialQueue(payload: EditorialQueueRequest): Promise<EditorialQueueResponse> {
    return this.request<EditorialQueueResponse>("/editorial/queue", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        ...defaultHeaders,
        Authorization: `Bearer ${this.token}`,
        ...(init.headers ?? {}),
      },
    });

    const bodyText = await response.text();
    const parsed = bodyText ? (JSON.parse(bodyText) as unknown) : null;

    if (!response.ok) {
      const errorBody = (parsed ?? {}) as ApiErrorEnvelope;
      const errorCode = errorBody.error?.code ?? `HTTP_${response.status}`;
      const message = errorBody.error?.message ?? response.statusText;
      const requestId = errorBody.error?.requestId;
      const requestHint = requestId ? ` (requestId: ${requestId})` : "";
      throw new Error(`${errorCode}: ${message}${requestHint}`);
    }

    return parsed as T;
  }
}
