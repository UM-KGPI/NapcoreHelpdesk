import type {
  AnswerResponse,
  ApiErrorEnvelope,
  EditorialBoardMetricsResponse,
  EditorialBoardResponse,
  EditorialQueueResponse,
  EditorialQueueTransitionResponse,
  HealthResponse,
  IndexRepositoryResponse,
  PromotionCandidatesResponse,
  StandardsScope,
} from "./types";

export interface AnswerRequest {
  question: string;
  sessionId?: string;
  userId?: string;
  standardsScope?: StandardsScope[];
  language?: string;
  generationProfile?: "deterministic-grounded" | "llm-ready";
  controllerProfile?: "deterministic-grounded" | "llm-ready";
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

export interface EditorialQueueTransitionRequest {
  queueItemId: string;
  action: "submit_for_review" | "request_changes" | "approve" | "reject" | "publish" | "reopen";
  comment?: string;
}

export interface EditorialBoardQuery {
  status?: "draft" | "review" | "approved" | "rejected" | "published";
  reason?: "LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION";
  priority?: "low" | "normal" | "high";
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface EditorialBoardMetricsQuery {
  windowDays?: number;
  slaHours?: number;
}

export interface IndexRepositoryRequest {
  repoUrl: string;
  repoPath: string;
  profile?: string;
  incremental?: boolean;
  prune?: boolean;
  includeIssues?: boolean;
  // Local-ops convenience: temporarily adds unknown URL to runtime allow-list.
  autoAllowRepository?: boolean;
}

interface ApiClientConfig {
  baseUrl: string;
  token: string;
}

export interface DevTokenResponse {
  token: string;
  tokenType: "Bearer";
  expiresInSeconds: number;
  subject: string;
  roles: string[];
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

  async answerQuestionStream(
    payload: AnswerRequest,
    requestId: string,
    onToken: (delta: string) => void,
    signal?: AbortSignal,
  ): Promise<AnswerResponse> {
    const response = await fetch(`${this.baseUrl}/questions/answer/stream`, {
      method: "POST",
      signal,
      headers: {
        ...defaultHeaders,
        Authorization: `Bearer ${this.token}`,
        "X-Request-Id": requestId,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const bodyText = await response.text();
      let errorCode = `HTTP_${response.status}`;
      try {
        const parsed = JSON.parse(bodyText) as { error?: { code?: string; message?: string } };
        errorCode = parsed?.error?.code ?? errorCode;
        const msg = parsed?.error?.message ?? response.statusText;
        throw new Error(`${errorCode}: ${msg}`);
      } catch {
        throw new Error(`${errorCode}: ${response.statusText}`);
      }
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("STREAM_UNAVAILABLE: Response body is not readable.");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE lines delimited by double newline.
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const eventText = buffer.slice(0, boundary).trim();
        buffer = buffer.slice(boundary + 2);

        if (!eventText.startsWith("data:")) continue;
        const jsonStr = eventText.slice("data:".length).trim();

        let event: { type: string; delta?: string; answer?: AnswerResponse; code?: string; message?: string };
        try {
          event = JSON.parse(jsonStr) as typeof event;
        } catch {
          continue;
        }

        if (event.type === "token" && event.delta != null) {
          onToken(event.delta);
        } else if (event.type === "done" && event.answer != null) {
          return event.answer;
        } else if (event.type === "error") {
          throw new Error(`${event.code ?? "STREAM_ERROR"}: ${event.message ?? "Unknown stream error"}`);
        } else if (event.type === "llm_fallback") {
          // LLM failed mid-stream; deterministic fallback was used.
          // Continue consuming until "done" event arrives.
        }
      }
    }

    throw new Error("STREAM_ENDED: Stream closed without a done event.");
  }

  async issueDevToken(): Promise<DevTokenResponse> {
    return this.request<DevTokenResponse>("/auth/dev-token", {
      method: "POST",
      body: "{}",
    }, false);
  }

  async getLiveHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health/live", { method: "GET" }, false);
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

  async transitionEditorialQueue(payload: EditorialQueueTransitionRequest): Promise<EditorialQueueTransitionResponse> {
    return this.request<EditorialQueueTransitionResponse>("/editorial/queue/transition", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listEditorialBoard(query: EditorialBoardQuery): Promise<EditorialBoardResponse> {
    const params = new URLSearchParams();
    if (query.status) params.set("status", query.status);
    if (query.reason) params.set("reason", query.reason);
    if (query.priority) params.set("priority", query.priority);
    if (query.search && query.search.trim()) params.set("search", query.search.trim());
    params.set("page", String(query.page ?? 1));
    params.set("pageSize", String(query.pageSize ?? 20));
    return this.request<EditorialBoardResponse>(`/editorial/queue?${params.toString()}`, {
      method: "GET",
    });
  }

  async getEditorialBoardMetrics(query: EditorialBoardMetricsQuery): Promise<EditorialBoardMetricsResponse> {
    const params = new URLSearchParams();
    params.set("windowDays", String(query.windowDays ?? 30));
    params.set("slaHours", String(query.slaHours ?? 72));
    return this.request<EditorialBoardMetricsResponse>(`/editorial/queue/metrics?${params.toString()}`, {
      method: "GET",
    });
  }

  async indexRepository(payload: IndexRepositoryRequest): Promise<IndexRepositoryResponse> {
    return this.request<IndexRepositoryResponse>("/admin/index", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  private async request<T>(path: string, init: RequestInit, withAuth = true): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        ...defaultHeaders,
        ...(withAuth ? { Authorization: `Bearer ${this.token}` } : {}),
        ...(init.headers ?? {}),
      },
    });

    const bodyText = await response.text();
    const contentType = (response.headers.get("content-type") ?? "").toLowerCase();
    const isJsonResponse = contentType.includes("application/json");
    let parsed: unknown = null;

    if (bodyText) {
      if (isJsonResponse) {
        try {
          parsed = JSON.parse(bodyText) as unknown;
        } catch {
          const preview = bodyText.slice(0, 160).replace(/\s+/g, " ").trim();
          throw new Error(
            `INVALID_JSON_RESPONSE: Expected valid JSON but got malformed JSON from ${path} (HTTP ${response.status}). Response preview: ${preview}`
          );
        }
      }
    }

    if (!response.ok) {
      const errorBody = (parsed ?? {}) as ApiErrorEnvelope;
      const errorCode = errorBody.error?.code ?? `HTTP_${response.status}`;
      const fallbackMessage = response.statusText || "Request failed";
      const preview = bodyText.slice(0, 160).replace(/\s+/g, " ").trim();
      const message = errorBody.error?.message ?? (isJsonResponse ? fallbackMessage : `${fallbackMessage} (non-JSON response: ${preview})`);
      const requestId = errorBody.error?.requestId;
      const requestHint = requestId ? ` (requestId: ${requestId})` : "";
      throw new Error(`${errorCode}: ${message}${requestHint}`);
    }

    if (bodyText && !isJsonResponse) {
      const preview = bodyText.slice(0, 160).replace(/\s+/g, " ").trim();
      throw new Error(
        `INVALID_RESPONSE_FORMAT: Expected JSON from ${path} but received '${contentType || "unknown"}'. Response preview: ${preview}`
      );
    }

    return parsed as T;
  }
}
