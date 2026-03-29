import { FormEvent, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { HelpdeskApiClient } from "./api";
import { AuthProvider } from "./auth-context";
import OperatorConsoleWorkspace from "./components/OperatorConsoleWorkspace";
import SharedAppLayout from "./components/SharedAppLayout";
import UserChatWorkspace, { type ChatTurn } from "./components/UserChatWorkspace";
import type {
  AnswerResponse,
  EditorialBoardMetricsResponse,
  EditorialBoardItem,
  EditorialBoardResponse,
  EditorialQueueResponse,
  EditorialQueueTransitionResponse,
  PromotionCandidatesResponse,
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

function createRequestId(): string {
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState("/api/v1");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) ?? "");
  const [autoTokenEnabled, setAutoTokenEnabled] = useState(() => {
    const saved = localStorage.getItem(AUTO_TOKEN_STORAGE_KEY);
    return saved ? saved === "true" : true;
  });

  const [question, setQuestion] = useState("How to use NeTEx for exchanging a timetable?");
  const [sessionId, setSessionId] = useState("sess-local");
  const [userId, setUserId] = useState("user-local");
  const [standardsScope, setStandardsScope] = useState<StandardsScope[]>(["NeTEx"]);

  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null);
  const [promotionResult, setPromotionResult] = useState<PromotionCandidatesResponse | null>(null);
  const [editorialResult, setEditorialResult] = useState<EditorialQueueResponse | null>(null);
  const [transitionResult, setTransitionResult] = useState<EditorialQueueTransitionResponse | null>(null);
  const [boardResult, setBoardResult] = useState<EditorialBoardResponse | null>(null);
  const [boardMetrics, setBoardMetrics] = useState<EditorialBoardMetricsResponse | null>(null);

  const [windowDays, setWindowDays] = useState(14);
  const [minCount, setMinCount] = useState(3);
  const [onlyUnresolved, setOnlyUnresolved] = useState(true);

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
  const [chatPrompt, setChatPrompt] = useState("How can I validate a NeTEx timetable profile before publishing?");
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [chatProfile, setChatProfile] = useState<"deterministic-grounded" | "llm-ready">("deterministic-grounded");
  const [chatApplyScope, setChatApplyScope] = useState(true);

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
    async function ensureDevToken(): Promise<void> {
      if (!autoTokenEnabled || token.trim()) {
        return;
      }
      try {
        const devClient = new HelpdeskApiClient({ baseUrl: apiBaseUrl, token: "" });
        const issued = await devClient.issueDevToken();
        setToken(issued.token);
      } catch {
        // Keep manual token mode if the dev endpoint is disabled.
      }
    }

    void ensureDevToken();
  }, [apiBaseUrl, autoTokenEnabled, token]);

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

  async function onSendChat(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const prompt = chatPrompt.trim();
    if (!prompt) {
      return;
    }

    const requestId = createRequestId();
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

    try {
      const result = await client.answerQuestion(
        {
          question: prompt,
          sessionId,
          userId,
          standardsScope: chatApplyScope ? standardsScope : undefined,
          language: "en",
          generationProfile: chatProfile,
          options: {
            maxCitations: 5,
            allowAbstain: true,
            faqMinConfidence: 0.85,
            retrievalTopK: 6,
            retrievalMinScore: 0.62,
          },
        },
        requestId
      );

      setAnswerResult(result);
      setQuestion(prompt);
      setEditorialResult(null);
      setChatTurns((prev) => [
        ...prev,
        {
          id: `a-${requestId}`,
          role: "assistant",
          text: result.answer,
          createdAt: new Date().toISOString(),
          answer: result,
          requestId: result.trace.requestId,
        },
      ]);
      setChatPrompt("");
    } catch (caught) {
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
      const result = await client.answerQuestion(
        {
          question,
          sessionId,
          userId,
          standardsScope,
          language: "en",
          options: {
            maxCitations: 5,
            allowAbstain: true,
            faqMinConfidence: 0.85,
            retrievalTopK: 6,
            retrievalMinScore: 0.62,
          },
        },
        requestId
      );
      setAnswerResult(result);
      setEditorialResult(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadPromotionCandidates(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const result = await client.listPromotionCandidates(windowDays, minCount, onlyUnresolved);
      setPromotionResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onQueueEditorial(): Promise<void> {
    if (!answerResult?.trace.questionEventId) {
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const result = await client.routeToEditorialQueue({
        questionEventId: answerResult.trace.questionEventId,
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

  return (
    <AuthProvider value={authValue}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<SharedAppLayout />}>
            <Route index element={<Navigate to="/user" replace />} />
            <Route
              path="user"
              element={
                <UserChatWorkspace
                  sessionId={sessionId}
                  userId={userId}
                  chatProfile={chatProfile}
                  chatApplyScope={chatApplyScope}
                  standardsScope={standardsScope}
                  chatPrompt={chatPrompt}
                  chatTurns={chatTurns}
                  token={token}
                  busy={busy}
                  setSessionId={setSessionId}
                  setUserId={setUserId}
                  setChatProfile={setChatProfile}
                  setChatApplyScope={setChatApplyScope}
                  setChatPrompt={setChatPrompt}
                  onSendChat={onSendChat}
                  onResetChatSession={onResetChatSession}
                />
              }
            />
            <Route
              path="operator"
              element={
                <OperatorConsoleWorkspace
                  question={question}
                  sessionId={sessionId}
                  userId={userId}
                  standardsScope={standardsScope}
                  answerResult={answerResult}
                  promotionResult={promotionResult}
                  editorialResult={editorialResult}
                  transitionResult={transitionResult}
                  boardResult={boardResult}
                  boardMetrics={boardMetrics}
                  windowDays={windowDays}
                  minCount={minCount}
                  onlyUnresolved={onlyUnresolved}
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
                  busy={busy}
                  token={token}
                  setQuestion={setQuestion}
                  setSessionId={setSessionId}
                  setUserId={setUserId}
                  toggleScope={toggleScope}
                  setWindowDays={setWindowDays}
                  setMinCount={setMinCount}
                  setOnlyUnresolved={setOnlyUnresolved}
                  setQueueReason={setQueueReason}
                  setQueuePriority={setQueuePriority}
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
                  onAskQuestion={onAskQuestion}
                  onLoadPromotionCandidates={onLoadPromotionCandidates}
                  onQueueEditorial={onQueueEditorial}
                  onTransitionEditorial={onTransitionEditorial}
                  onLoadEditorialBoard={onLoadEditorialBoard}
                  onQuickTransition={onQuickTransition}
                  onLoadBoardMetrics={onLoadBoardMetrics}
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
