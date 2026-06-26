import { FormEvent, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { HelpdeskApiClient } from "./api";
import { AuthProvider } from "./auth-context";
import EditorConsoleWorkspace from "./components/EditorConsoleWorkspace";
import SharedAppLayout from "./components/SharedAppLayout";
import UserChatWorkspace, { type ChatTurn } from "./components/UserChatWorkspace";
import type {
  AnswerResponse,
  AskedQuestionRow,
  EditorialBoardMetricsResponse,
  EditorialBoardItem,
  EditorialBoardResponse,
  EditorialQueueResponse,
  EditorialQueueTransitionResponse,
  EditorialSemanticClustersResponse,
  IndexRepositoryResponse,
  StandardsScope,
} from "./types";

const TRANSITION_ACTIONS = [
  "submit_for_review",
  "request_changes",
  "approve",
  "reject",
  "publish",
  "reopen",
] as const;
const BOARD_STATUSES = ["draft", "review", "approved", "rejected", "published"] as const;
const BOARD_REASONS = ["LOW_CONFIDENCE", "CITATION_GAP", "POLICY_REVIEW", "USER_ESCALATION"] as const;
const BOARD_PRIORITIES = ["low", "normal", "high"] as const;
const TOKEN_STORAGE_KEY = "napcore.helpdesk.jwt";
const AUTO_TOKEN_STORAGE_KEY = "napcore.helpdesk.autoToken";

type TransitionAction = (typeof TRANSITION_ACTIONS)[number];
type BoardStatus = (typeof BOARD_STATUSES)[number];
type BoardReason = (typeof BOARD_REASONS)[number];
type BoardPriority = (typeof BOARD_PRIORITIES)[number];

type IndexRepoPreset = {
  id: string;
  label: string;
  repoUrl: string;
  repoPath: string;
  profile: string;
};

const DEFAULT_INDEX_REPO_PRESETS: IndexRepoPreset[] = [
  {
    id: "netex",
    label: "NeTEx",
    repoUrl: "https://github.com/TransmodelEcosystem/NeTEx",
    repoPath: "/app/repos/NeTEx",
    profile: "netex",
  },
  {
    id: "opra",
    label: "OpRa",
    repoUrl: "https://github.com/OpRa-CEN/OpRa",
    repoPath: "/app/repos/OpRa",
    profile: "opra",
  },
  {
    id: "siri",
    label: "SIRI",
    repoUrl: "https://github.com/TransmodelEcosystem/SIRI",
    repoPath: "/app/repos/SIRI",
    profile: "siri",
  },
];

const INDEX_REPO_PRESETS_CONFIG_PATH = "/index-repo-presets.json";

function isIndexRepoPreset(value: unknown): value is IndexRepoPreset {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.label === "string" &&
    typeof candidate.repoUrl === "string" &&
    typeof candidate.repoPath === "string" &&
    typeof candidate.profile === "string"
  );
}

function createRequestId(): string {
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function App() {
  const frontendVersion = import.meta.env.VITE_APP_VERSION ?? __APP_VERSION__;
  const [apiBaseUrl, setApiBaseUrl] = useState("/api/v1");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) ?? "");
  const [autoTokenEnabled, setAutoTokenEnabled] = useState(() => {
    const saved = localStorage.getItem(AUTO_TOKEN_STORAGE_KEY);
    return saved ? saved === "true" : true;
  });

  const [question, setQuestion] = useState("How to use NeTEx for exchanging a timetable?");
  const [sessionId, setSessionId] = useState("sess-local");
  const [userId, setUserId] = useState("user-local");
  const [standardsScope, setStandardsScope] = useState<StandardsScope[]>([]);

  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null);
  const [askedQuestions, setAskedQuestions] = useState<AskedQuestionRow[]>([]);
  const [selectedQuestionEventId, setSelectedQuestionEventId] = useState("");
  const [editorialResult, setEditorialResult] = useState<EditorialQueueResponse | null>(null);
  const [transitionResult, setTransitionResult] = useState<EditorialQueueTransitionResponse | null>(null);
  const [boardResult, setBoardResult] = useState<EditorialBoardResponse | null>(null);
  const [boardMetrics, setBoardMetrics] = useState<EditorialBoardMetricsResponse | null>(null);
  const [semanticClustersResult, setSemanticClustersResult] = useState<EditorialSemanticClustersResponse | null>(null);

  const [indexRepoPresets, setIndexRepoPresets] = useState<IndexRepoPreset[]>(DEFAULT_INDEX_REPO_PRESETS);
  const [indexPresetId, setIndexPresetId] = useState(DEFAULT_INDEX_REPO_PRESETS[0].id);
  const [indexRepoUrl, setIndexRepoUrl] = useState(DEFAULT_INDEX_REPO_PRESETS[0].repoUrl);
  const [indexRepoPath, setIndexRepoPath] = useState(DEFAULT_INDEX_REPO_PRESETS[0].repoPath);
  const [indexProfile, setIndexProfile] = useState(DEFAULT_INDEX_REPO_PRESETS[0].profile);
  const [indexIncremental, setIndexIncremental] = useState(true);
  const [indexPrune, setIndexPrune] = useState(true);
  const [indexIncludeIssues, setIndexIncludeIssues] = useState(false);
  const [indexAutoAllowRepository, setIndexAutoAllowRepository] = useState(true);
  const [indexResult, setIndexResult] = useState<IndexRepositoryResponse | null>(null);
  const [indexBusy, setIndexBusy] = useState(false);

  const [queueReason, setQueueReason] = useState<"LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION">("LOW_CONFIDENCE");
  const [queuePriority, setQueuePriority] = useState<"low" | "normal" | "high">("normal");
  const [transitionQueueItemId, setTransitionQueueItemId] = useState("");
  const [transitionAction, setTransitionAction] = useState<TransitionAction>("submit_for_review");
  const [transitionComment, setTransitionComment] = useState("");
  const [boardStatus, setBoardStatus] = useState<BoardStatus | "">("");
  const [boardReason, setBoardReason] = useState<BoardReason | "">("");
  const [boardPriority, setBoardPriority] = useState<BoardPriority | "">("");
  const [boardSearch, setBoardSearch] = useState("");
  const [boardPage, setBoardPage] = useState(1);
  const [boardPageSize, setBoardPageSize] = useState(10);
  const [metricsWindowDays, setMetricsWindowDays] = useState(30);
  const [metricsSlaHours, setMetricsSlaHours] = useState(72);
  const [semanticWindowDays, setSemanticWindowDays] = useState(30);
  const [semanticMinClusterSize, setSemanticMinClusterSize] = useState(2);
  const [semanticSimilarityThreshold, setSemanticSimilarityThreshold] = useState(0.82);
  const [semanticMaxEvents, setSemanticMaxEvents] = useState(500);
  const [chatPrompt, setChatPrompt] = useState("How is a journey departure time represented in NeTEx XML?");
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const client = useMemo(() => new HelpdeskApiClient({ baseUrl: apiBaseUrl, token }), [apiBaseUrl, token]);
  const authValue = useMemo(
    () => ({
      apiBaseUrl,
      setApiBaseUrl,
      token,
      setToken,
      autoTokenEnabled,
      setAutoTokenEnabled,
    }),
    [apiBaseUrl, token, autoTokenEnabled]
  );

  useEffect(() => {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }, [token]);

  useEffect(() => {
    localStorage.setItem(AUTO_TOKEN_STORAGE_KEY, String(autoTokenEnabled));
  }, [autoTokenEnabled]);

  useEffect(() => {
    let cancelled = false;

    async function loadIndexRepoPresets(): Promise<void> {
      try {
        const response = await fetch(INDEX_REPO_PRESETS_CONFIG_PATH, { cache: "no-store" });
        if (!response.ok) {
          return;
        }

        const payload: unknown = await response.json();
        if (!Array.isArray(payload)) {
          return;
        }

        const presets = payload.filter(isIndexRepoPreset);
        if (!presets.length || cancelled) {
          return;
        }

        setIndexRepoPresets(presets);
        setIndexPresetId(presets[0].id);
        setIndexRepoUrl(presets[0].repoUrl);
        setIndexRepoPath(presets[0].repoPath);
        setIndexProfile(presets[0].profile);
      } catch {
        // Keep bundled defaults when external config is unavailable.
      }
    }

    void loadIndexRepoPresets();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function ensureDevToken(): Promise<void> {
      if (!autoTokenEnabled) {
        return;
      }
      try {
        const devClient = new HelpdeskApiClient({ baseUrl: apiBaseUrl, token: "" });
        const issued = await devClient.issueDevToken();
        if (!cancelled) {
          setToken(issued.token);
        }
      } catch {
        // Keep manual token mode if the dev endpoint is disabled.
      }
    }

    void ensureDevToken();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, autoTokenEnabled]);

  async function onLoadAskedQuestions(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const result = await client.listQuestionEvents({ page: 1, pageSize: 100 });
      setAskedQuestions(result.items);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  function toggleScope(scope: StandardsScope): void {
    setStandardsScope((prev) => {
      if (prev.includes(scope)) {
        return prev.filter((item) => item !== scope);
      }
      return [...prev, scope];
    });
  }

  function createSessionId(): string {
    return `sess-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  }

  async function refreshDevTokenAfterUnauthorized(caught: unknown): Promise<string | null> {
    const message = caught instanceof Error ? caught.message : String(caught);
    if (!autoTokenEnabled || !message.startsWith("UNAUTHORIZED:")) {
      return null;
    }

    try {
      const devClient = new HelpdeskApiClient({ baseUrl: apiBaseUrl, token: "" });
      const issued = await devClient.issueDevToken();
      setToken(issued.token);
      return issued.token;
    } catch {
      return null;
    }
  }

  function onSelectIndexPreset(presetId: string): void {
    setIndexPresetId(presetId);
    const preset = indexRepoPresets.find((item) => item.id === presetId);
    if (!preset) {
      return;
    }

    setIndexRepoUrl(preset.repoUrl);
    setIndexRepoPath(preset.repoPath);
    setIndexProfile(preset.profile);
  }

  async function onSendChat(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const prompt = chatPrompt.trim();
    if (!prompt) {
      return;
    }

    const requestId = createRequestId();
    const assistantTurnId = `a-${requestId}`;
    setChatTurns((prev) => [
      ...prev,
      {
        id: `u-${requestId}`,
        role: "user",
        text: prompt,
        createdAt: new Date().toISOString(),
      },
    ]);

    setBusy(true);
    setError(null);

    const answerPayload = {
      question: prompt,
      sessionId,
      userId,
      standardsScope: standardsScope.length > 0 ? standardsScope : undefined,
      language: "en",
      generationProfile: "llm-ready" as const,
      controllerProfile: "llm-ready" as const,
      options: {
        maxCitations: 5,
        allowAbstain: true,
        faqMinConfidence: 0.85,
        retrievalTopK: 6,
        retrievalMinScore: 0.62,
      },
    };

    const useStreaming = true;

    const handleStreamToken = (delta: string) => {
      setChatTurns((prev) =>
        prev.map((t) =>
          t.id === assistantTurnId ? { ...t, text: t.text + delta } : t
        )
      );
    };

    try {
      if (useStreaming) {
        // Insert a placeholder assistant turn immediately so the user sees typing start.
        setChatTurns((prev) => [
          ...prev,
          {
            id: assistantTurnId,
            role: "assistant",
            text: "",
            createdAt: new Date().toISOString(),
          },
        ]);

        let result: import("./types").AnswerResponse;
        try {
          result = await client.answerQuestionStream(answerPayload, requestId, handleStreamToken);
        } catch (streamErr) {
          // Streaming endpoint unavailable or failed — retry with the regular endpoint.
          // Remove the placeholder turn first, then fall through to the non-streaming path.
          setChatTurns((prev) => prev.filter((t) => t.id !== assistantTurnId));
          result = await client.answerQuestion(answerPayload, requestId);
          setChatTurns((prev) => [
            ...prev,
            {
              id: assistantTurnId,
              role: "assistant",
              text: result.answer,
              createdAt: new Date().toISOString(),
              answer: result,
              requestId: result.trace.requestId,
            },
          ]);
          setAnswerResult(result);
          setQuestion(prompt);
          setEditorialResult(null);
          setChatPrompt("");
          return;
        }

        // Streaming completed: update the placeholder turn with full metadata.
        setChatTurns((prev) =>
          prev.map((t) =>
            t.id === assistantTurnId
              ? { ...t, text: result.answer, answer: result, requestId: result.trace.requestId }
              : t
          )
        );
        setAnswerResult(result);
        setQuestion(prompt);
        setEditorialResult(null);
        setChatPrompt("");
        return;
      }

      const result = await client.answerQuestion(answerPayload, requestId);

      setAnswerResult(result);
      setQuestion(prompt);
      setEditorialResult(null);
      setChatTurns((prev) => [
        ...prev,
        {
          id: assistantTurnId,
          role: "assistant",
          text: result.answer,
          createdAt: new Date().toISOString(),
          answer: result,
          requestId: result.trace.requestId,
        },
      ]);
      setChatPrompt("");
    } catch (caught) {
      // Remove any streaming placeholder turn on error.
      setChatTurns((prev) => prev.filter((t) => t.id !== assistantTurnId || t.text !== ""));
      const refreshedToken = await refreshDevTokenAfterUnauthorized(caught);
      if (refreshedToken) {
        try {
          const retryClient = new HelpdeskApiClient({ baseUrl: apiBaseUrl, token: refreshedToken });
          const result = await retryClient.answerQuestion(answerPayload, requestId);

          setAnswerResult(result);
          setQuestion(prompt);
          setEditorialResult(null);
          setChatTurns((prev) => [
            ...prev,
            {
              id: assistantTurnId,
              role: "assistant",
              text: result.answer,
              createdAt: new Date().toISOString(),
              answer: result,
              requestId: result.trace.requestId,
            },
          ]);
          setChatPrompt("");
          return;
        } catch (retryCaught) {
          setError(retryCaught instanceof Error ? retryCaught.message : String(retryCaught));
          return;
        }
      }
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  function onResetChatSession(): void {
    setChatTurns([]);
    setSessionId(createSessionId());
  }

  async function onAskQuestion(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError(null);

    try {
      const requestId = createRequestId();
      const answerPayload = {
        question,
        sessionId,
        userId,
        standardsScope,
        language: "en",
        generationProfile: "llm-ready" as const,
        controllerProfile: "llm-ready" as const,
        options: {
          maxCitations: 5,
          allowAbstain: true,
          faqMinConfidence: 0.85,
          retrievalTopK: 6,
          retrievalMinScore: 0.62,
        },
      };

      const useStreaming = true;
      if (useStreaming) {
        setAnswerResult({
          answerId: `streaming-${requestId}`,
          mode: "rag",
          confidence: 0,
          answer: "",
          citations: [],
          abstained: false,
          abstentionReason: null,
          reviewRequired: true,
          trace: {
            requestId,
            questionEventId: `streaming-${requestId}`,
            matchedFaqEntryId: null,
            retrievalEventIds: [],
          },
        });

        const result = await client.answerQuestionStream(
          answerPayload,
          requestId,
          (delta) => {
            setAnswerResult((prev) =>
              prev
                ? {
                    ...prev,
                    answer: prev.answer + delta,
                  }
                : prev
            );
          }
        );
        setAnswerResult(result);
        setAskedQuestions((prev) => {
          const row: AskedQuestionRow = {
            question,
            askedAt: new Date().toISOString(),
            requestId: result.trace.requestId,
            questionEventId: result.trace.questionEventId,
            mode: result.mode,
            confidence: result.confidence,
            reviewRequired: result.reviewRequired,
          };
          const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
          return next.slice(0, 200);
        });
        setEditorialResult(null);
        return;
      }

      const result = await client.answerQuestion(answerPayload, requestId);
      setAnswerResult(result);
      setAskedQuestions((prev) => {
        const row: AskedQuestionRow = {
          question,
          askedAt: new Date().toISOString(),
          requestId: result.trace.requestId,
          questionEventId: result.trace.questionEventId,
          mode: result.mode,
          confidence: result.confidence,
          reviewRequired: result.reviewRequired,
        };
        const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
        return next.slice(0, 200);
      });
      setEditorialResult(null);
    } catch (caught) {
      const refreshedToken = await refreshDevTokenAfterUnauthorized(caught);
      if (refreshedToken) {
        try {
          const retryClient = new HelpdeskApiClient({ baseUrl: apiBaseUrl, token: refreshedToken });
          const requestId = createRequestId();
          const answerPayload = {
            question,
            sessionId,
            userId,
            standardsScope,
            language: "en",
            generationProfile: "llm-ready" as const,
            controllerProfile: "llm-ready" as const,
            options: {
              maxCitations: 5,
              allowAbstain: true,
              faqMinConfidence: 0.85,
              retrievalTopK: 6,
              retrievalMinScore: 0.62,
            },
          };

          const useStreaming = true;
          if (useStreaming) {
            setAnswerResult({
              answerId: `streaming-${requestId}`,
              mode: "rag",
              confidence: 0,
              answer: "",
              citations: [],
              abstained: false,
              abstentionReason: null,
              reviewRequired: true,
              trace: {
                requestId,
                questionEventId: `streaming-${requestId}`,
                matchedFaqEntryId: null,
                retrievalEventIds: [],
              },
            });

            const result = await retryClient.answerQuestionStream(
              answerPayload,
              requestId,
              (delta) => {
                setAnswerResult((prev) =>
                  prev
                    ? {
                        ...prev,
                        answer: prev.answer + delta,
                      }
                    : prev
                );
              }
            );
            setAnswerResult(result);
            setAskedQuestions((prev) => {
              const row: AskedQuestionRow = {
                question,
                askedAt: new Date().toISOString(),
                requestId: result.trace.requestId,
                questionEventId: result.trace.questionEventId,
                mode: result.mode,
                confidence: result.confidence,
                reviewRequired: result.reviewRequired,
              };
              const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
              return next.slice(0, 200);
            });
            setEditorialResult(null);
            return;
          }

          const result = await retryClient.answerQuestion(answerPayload, requestId);
          setAnswerResult(result);
          setAskedQuestions((prev) => {
            const row: AskedQuestionRow = {
              question,
              askedAt: new Date().toISOString(),
              requestId: result.trace.requestId,
              questionEventId: result.trace.questionEventId,
              mode: result.mode,
              confidence: result.confidence,
              reviewRequired: result.reviewRequired,
            };
            const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
            return next.slice(0, 200);
          });
          setEditorialResult(null);
          return;
        } catch (retryCaught) {
          setError(retryCaught instanceof Error ? retryCaught.message : String(retryCaught));
          return;
        }
      }
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onSetAnswerFeedback(
    requestId: string,
    payload: {
      userLikes?: boolean;
      userDislikes?: boolean;
      answerSuccess?: boolean | null;
      citationClicksDelta?: number;
    }
  ): Promise<void> {
    setError(null);
    try {
      const result = await client.submitAnswerFeedback({
        requestId,
        ...payload,
      });

      setChatTurns((prev) =>
        prev.map((turn) => {
          if (!turn.answer) {
            return turn;
          }
          const turnRequestId = turn.requestId ?? turn.answer.trace.requestId;
          if (turnRequestId !== result.requestId) {
            return turn;
          }
          return {
            ...turn,
            answer: {
              ...turn.answer,
              trace: {
                ...turn.answer.trace,
                userLikes: result.userLikes,
                userDislikes: result.userDislikes,
                answerSuccess: result.answerSuccess,
                citationClickCount: result.citationClickCount,
              },
            },
          };
        })
      );

      setAnswerResult((prev) => {
        if (!prev || prev.trace.requestId !== result.requestId) {
          return prev;
        }
        return {
          ...prev,
          trace: {
            ...prev.trace,
            userLikes: result.userLikes,
            userDislikes: result.userDislikes,
            answerSuccess: result.answerSuccess,
            citationClickCount: result.citationClickCount,
          },
        };
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  async function onQueueEditorial(questionEventIdOverride?: string): Promise<void> {
    const questionEventId = questionEventIdOverride || selectedQuestionEventId || answerResult?.trace.questionEventId;
    if (!questionEventId) {
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const result = await client.routeToEditorialQueue({
        questionEventId,
        reason: queueReason,
        priority: queuePriority,
      });
      setEditorialResult(result);
      setTransitionQueueItemId(result.queueItemId);
      setTransitionResult(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onTransitionEditorial(): Promise<void> {
    if (!transitionQueueItemId.trim()) {
      setError("queueItemId is required for transition.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const result = await client.transitionEditorialQueue({
        queueItemId: transitionQueueItemId.trim(),
        action: transitionAction,
        comment: transitionComment,
      });
      setTransitionResult(result);
      await onLoadEditorialBoard();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadEditorialBoard(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const result = await client.listEditorialBoard({
        status: boardStatus || undefined,
        reason: boardReason || undefined,
        priority: boardPriority || undefined,
        search: boardSearch,
        page: boardPage,
        pageSize: boardPageSize,
      });
      setBoardResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onQuickTransition(item: EditorialBoardItem, action: TransitionAction): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const result = await client.transitionEditorialQueue({
        queueItemId: item.queueItemId,
        action,
        comment: `board action: ${action}`,
      });
      setTransitionQueueItemId(item.queueItemId);
      setTransitionResult(result);
      await onLoadEditorialBoard();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadBoardMetrics(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const result = await client.getEditorialBoardMetrics({
        windowDays: metricsWindowDays,
        slaHours: metricsSlaHours,
      });
      setBoardMetrics(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadSemanticClusters(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const result = await client.runEditorialSemanticClusters({
        windowDays: semanticWindowDays,
        minClusterSize: semanticMinClusterSize,
        similarityThreshold: semanticSimilarityThreshold,
        maxEvents: semanticMaxEvents,
      });
      setSemanticClustersResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onIndexRepository(): Promise<void> {
    setBusy(true);
    setIndexBusy(true);
    setError(null);
    setIndexResult(null);
    try {
      const result = await client.indexRepository({
        repoUrl: indexRepoUrl,
        repoPath: indexRepoPath,
        profile: indexProfile,
        incremental: indexIncremental,
        prune: indexPrune,
        includeIssues: indexIncludeIssues,
        autoAllowRepository: indexAutoAllowRepository,
      });
      setIndexResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setIndexBusy(false);
      setBusy(false);
    }
  }

  return (
    <AuthProvider value={authValue}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <SharedAppLayout
                appVersion={frontendVersion}
              />
            }
          >
            <Route index element={<Navigate to="/user" replace />} />
            <Route
              path="user"
              element={
                <UserChatWorkspace
                  chatPrompt={chatPrompt}
                  chatTurns={chatTurns}
                  token={token}
                  busy={busy}
                  setChatPrompt={setChatPrompt}
                  onSendChat={onSendChat}
                  onResetChatSession={onResetChatSession}
                  onSetAnswerFeedback={onSetAnswerFeedback}
                />
              }
            />
            <Route
              path="editor"
              element={
                <EditorConsoleWorkspace
                  question={question}
                  sessionId={sessionId}
                  userId={userId}
                  standardsScope={standardsScope}
                  answerResult={answerResult}
                  askedQuestions={askedQuestions}
                  selectedQuestionEventId={selectedQuestionEventId}
                  editorialResult={editorialResult}
                  transitionResult={transitionResult}
                  boardResult={boardResult}
                  boardMetrics={boardMetrics}
                  semanticClustersResult={semanticClustersResult}
                  queueReason={queueReason}
                  queuePriority={queuePriority}
                  transitionQueueItemId={transitionQueueItemId}
                  transitionAction={transitionAction}
                  transitionComment={transitionComment}
                  boardStatus={boardStatus}
                  boardReason={boardReason}
                  boardPriority={boardPriority}
                  boardSearch={boardSearch}
                  boardPage={boardPage}
                  boardPageSize={boardPageSize}
                  metricsWindowDays={metricsWindowDays}
                  metricsSlaHours={metricsSlaHours}
                  semanticWindowDays={semanticWindowDays}
                  semanticMinClusterSize={semanticMinClusterSize}
                  semanticSimilarityThreshold={semanticSimilarityThreshold}
                  semanticMaxEvents={semanticMaxEvents}
                  busy={busy}
                  token={token}
                  setQuestion={setQuestion}
                  setSessionId={setSessionId}
                  setUserId={setUserId}
                  toggleScope={toggleScope}
                  setQueueReason={setQueueReason}
                  setQueuePriority={setQueuePriority}
                  setSelectedQuestionEventId={setSelectedQuestionEventId}
                  setTransitionQueueItemId={setTransitionQueueItemId}
                  setTransitionAction={setTransitionAction}
                  setTransitionComment={setTransitionComment}
                  setBoardStatus={setBoardStatus}
                  setBoardReason={setBoardReason}
                  setBoardPriority={setBoardPriority}
                  setBoardSearch={setBoardSearch}
                  setBoardPage={setBoardPage}
                  setBoardPageSize={setBoardPageSize}
                  setMetricsWindowDays={setMetricsWindowDays}
                  setMetricsSlaHours={setMetricsSlaHours}
                  setSemanticWindowDays={setSemanticWindowDays}
                  setSemanticMinClusterSize={setSemanticMinClusterSize}
                  setSemanticSimilarityThreshold={setSemanticSimilarityThreshold}
                  setSemanticMaxEvents={setSemanticMaxEvents}
                  onAskQuestion={onAskQuestion}
                  onLoadAskedQuestions={onLoadAskedQuestions}
                  onQueueEditorial={onQueueEditorial}
                  onTransitionEditorial={onTransitionEditorial}
                  onLoadEditorialBoard={onLoadEditorialBoard}
                  onQuickTransition={onQuickTransition}
                  onLoadBoardMetrics={onLoadBoardMetrics}
                  onLoadSemanticClusters={onLoadSemanticClusters}
                  indexRepoUrl={indexRepoUrl}
                  indexRepoPath={indexRepoPath}
                  indexProfile={indexProfile}
                  indexPresetId={indexPresetId}
                  indexRepoPresets={indexRepoPresets}
                  indexIncremental={indexIncremental}
                  indexPrune={indexPrune}
                  indexIncludeIssues={indexIncludeIssues}
                  indexAutoAllowRepository={indexAutoAllowRepository}
                  indexResult={indexResult}
                  indexBusy={indexBusy}
                  setIndexRepoUrl={setIndexRepoUrl}
                  setIndexRepoPath={setIndexRepoPath}
                  setIndexProfile={setIndexProfile}
                  onSelectIndexPreset={onSelectIndexPreset}
                  setIndexIncremental={setIndexIncremental}
                  setIndexPrune={setIndexPrune}
                  setIndexIncludeIssues={setIndexIncludeIssues}
                  setIndexAutoAllowRepository={setIndexAutoAllowRepository}
                  onIndexRepository={onIndexRepository}
                />
              }
            />
          </Route>
        </Routes>

        {error && <div className="error-banner">{error}</div>}
      </BrowserRouter>
    </AuthProvider>
  );
}
