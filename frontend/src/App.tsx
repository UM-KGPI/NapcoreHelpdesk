/**
 * Root application: routing, global auth state, and editorial workflow handlers.
 *
 * All server state (asked questions, board items, FAQs) is owned here and
 * passed down as props to keep child components pure and testable.
 *
 * Key design decisions:
 *   boardStatusMap is kept separate from boardResult so the Status column in
 *   Questions Asked can refresh independently of which queue filter or page
 *   is active. It is populated with a dedicated unfiltered fetch (pageSize 100,
 *   the backend cap) rather than derived from boardResult.
 *
 *   onQuickTransition triggers onLoadAskedQuestions only for the 'revoke' action
 *   because revoke moves an approved item back into the asked-questions view.
 *   Other transitions change only the queue status, already reflected by the
 *   boardStatusMap refresh that always runs.
 *
 *   onDeleteQuestionEvent also removes matching items from boardResult
 *   client-side to keep Questions in Review in sync without a round-trip;
 *   the backend ON DELETE CASCADE handles DB consistency.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-28  |  Modified: 2026-06-28
 */

import { FormEvent, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useSearchParams } from "react-router-dom";

import { HelpdeskApiClient } from "./api";
import { AuthProvider } from "./auth-context";
import EditorConsoleWorkspace from "./components/EditorConsoleWorkspace";
import SharedAppLayout from "./components/SharedAppLayout";
import UserChatWorkspace, { type ChatTurn } from "./components/UserChatWorkspace";
import type {
  AnswerResponse,
  AskedQuestionRow,
  EditorialBoardItem,
  EditorialBoardResponse,
  IndexRepositoryResponse,
  QuestionEventDetail,
  StandardsScope,
} from "./types";

const TRANSITION_ACTIONS = [
  "request_changes",
  "approve",
  "reject",
  "publish",
  "revoke",
  "reopen",
] as const;
const TOKEN_STORAGE_KEY = "napcore.helpdesk.jwt";
const AUTO_TOKEN_STORAGE_KEY = "napcore.helpdesk.autoToken";

type TransitionAction = (typeof TRANSITION_ACTIONS)[number];

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

const INDEX_REPO_PRESETS_CONFIG_PATH = `${import.meta.env.BASE_URL}index-repo-presets.json`;

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

const BROWSER_LANGUAGE_NAMES: Record<string, string> = {
  en: "English", nb: "Norwegian", no: "Norwegian", nn: "Norwegian Nynorsk",
  sl: "Slovenian", de: "German", fr: "French", es: "Spanish", it: "Italian",
  nl: "Dutch", pl: "Polish", pt: "Portuguese", sv: "Swedish", da: "Danish",
  fi: "Finnish", cs: "Czech", sk: "Slovak", hu: "Hungarian", ro: "Romanian",
  hr: "Croatian", bg: "Bulgarian", el: "Greek", lt: "Lithuanian", lv: "Latvian",
  et: "Estonian", mt: "Maltese", ga: "Irish",
};

function detectBrowserLanguage(): string {
  const tag = (navigator.languages?.[0] ?? navigator.language ?? "en").split("-")[0].toLowerCase();
  return BROWSER_LANGUAGE_NAMES[tag] ?? "English";
}

function isJwtExpired(token: string): boolean {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return false;
    const payload = JSON.parse(atob(parts[1])) as Record<string, unknown>;
    const exp = typeof payload.exp === "number" ? payload.exp : null;
    if (exp === null) return false;
    return Date.now() / 1000 > exp;
  } catch {
    return false;
  }
}

// Wrapper for user chat to handle ?questionId= query parameter
function UserChatWithQueryParams(props: React.ComponentProps<typeof UserChatWorkspace>) {
  const [searchParams] = useSearchParams();
  const [enhancedTurns, setEnhancedTurns] = useState<typeof props.chatTurns>(props.chatTurns);

  // Sync with parent chatTurns when no query parameter
  useEffect(() => {
    const questionId = searchParams.get("questionId");
    if (!questionId) {
      setEnhancedTurns(props.chatTurns);
    }
  }, [props.chatTurns, searchParams]);

  // Load historical question when query parameter present
  useEffect(() => {
    const questionId = searchParams.get("questionId");
    if (!questionId || !props.token) return;

    // Clear the input field when showing historical Q&A
    props.setChatPrompt("");

    // Fetch and display the historical question
    const baseUrl = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
      ? "http://localhost:8000/api/v1"
      : `${window.location.origin}${import.meta.env.BASE_URL}api/v1`;

    fetch(`${baseUrl}/questions/events/${questionId}`, {
      headers: { Authorization: `Bearer ${props.token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then((detail) => {
        // Create two turns: one for the question, one for the answer
        const questionTurn: ChatTurn = {
          id: `${detail.requestId}-q`,
          role: "user",
          text: detail.question,
          createdAt: detail.createdAt,
        };

        const answerTurn: ChatTurn = {
          id: `${detail.requestId}-a`,
          role: "assistant",
          text: detail.answer, // Show answer as text
          createdAt: detail.createdAt,
          answer: {
            answerId: detail.questionEventId,
            mode: "rag" as const,
            confidence: detail.confidence,
            answer: detail.answer,
            citations: (detail.citations || []).map((c: any) => ({
              repositoryUrl: c.repositoryUrl,
              commitSha: "", // Will be populated from detail if available
              sourcePath: c.sourcePath,
              chunkId: c.chunkId,
              label: c.label,
            })),
            abstained: false,
            abstentionReason: null,
            reviewRequired: false,
            trace: {
              requestId: detail.requestId,
              questionEventId: detail.questionEventId,
              matchedFaqEntryId: null,
              retrievalEventIds: [],
              userLikes: false,
              userDislikes: false,
            } as any,
          },
          requestId: detail.requestId,
        };

        setEnhancedTurns([questionTurn, answerTurn]);
      })
      .catch((error) => {
        console.error(`Failed to load question ${questionId}:`, error);
      });
  }, [searchParams, props.token]);

  return <UserChatWorkspace {...props} chatTurns={enhancedTurns} />;
}

// Wrapper component to handle ?questionId= query parameter in editor
function EditorWithQueryParams(props: React.ComponentProps<typeof EditorConsoleWorkspace>) {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const questionId = searchParams.get("questionId");
    if (questionId) {
      props.setSelectedQuestionEventId(questionId);
    }
  }, [searchParams, props.setSelectedQuestionEventId]);

  return <EditorConsoleWorkspace {...props} />;
}

export default function App() {
  const frontendVersion = import.meta.env.VITE_APP_VERSION ?? '0.6.1';
  const [apiBaseUrl, setApiBaseUrl] = useState(() => {
    const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    return isDev ? 'http://localhost:8000/api/v1' : `${window.location.origin}${import.meta.env.BASE_URL}api/v1`;
  });
  const [token, setToken] = useState(() => {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY) ?? "";
    if (stored && isJwtExpired(stored)) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      return "";
    }
    return stored;
  });
  const [autoTokenEnabled, setAutoTokenEnabled] = useState(() => {
    const saved = localStorage.getItem(AUTO_TOKEN_STORAGE_KEY);
    return saved ? saved === "true" : true;
  });

  const [question, setQuestion] = useState("How to use NeTEx for exchanging a timetable?");
  const [sessionId, setSessionId] = useState("sess-local");
  const userId = "user-local";
  const [standardsScope] = useState<StandardsScope[]>([]);

  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null);
  const [askedQuestions, setAskedQuestions] = useState<AskedQuestionRow[]>([]);
  const [selectedQuestionEventId, setSelectedQuestionEventId] = useState("");
  const [boardResult, setBoardResult] = useState<EditorialBoardResponse | null>(null);
  const [faqItems, setFaqItems] = useState<EditorialBoardItem[]>([]);
  const [boardStatusMap, setBoardStatusMap] = useState<Map<string, string>>(new Map());

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

  const [chatPrompt, setChatPrompt] = useState("How is a journey departure time represented in NeTEx XML?");
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendBuildRef, setBackendBuildRef] = useState("");
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
    async function fetchBuildRef(): Promise<void> {
      try {
        const response = await fetch(`${apiBaseUrl}/health/live`, { cache: "no-store" });
        if (!response.ok) return;
        const data: unknown = await response.json();
        if (typeof data === "object" && data !== null && "buildRef" in data) {
          const buildRef = (data as Record<string, unknown>).buildRef;
          if (typeof buildRef === "string") {
            setBackendBuildRef(buildRef);
          }
        }
      } catch {
        // Health endpoint unavailable; continue without build ref
      }
    }

    void fetchBuildRef();
  }, [apiBaseUrl]);

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

  async function refreshBoardStatusMap(): Promise<void> {
    try {
      const result = await client.listEditorialBoard({ page: 1, pageSize: 100 });
      const map = new Map<string, string>();
      for (const item of result.items) map.set(item.requestId, item.status);
      setBoardStatusMap(map);
    } catch {
      // best-effort: status column may be stale but should not block question loading
    }
  }

  async function onDeleteQuestionEvent(questionEventIds: string[]): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await Promise.all(questionEventIds.map((id) => client.deleteQuestionEvent(id)));
      const deletedSet = new Set(questionEventIds);
      setAskedQuestions((prev) => prev.filter((q) => !deletedSet.has(q.questionEventId)));
      setBoardResult((prev) => prev ? { ...prev, items: prev.items.filter((b) => !deletedSet.has(b.questionEventId)) } : prev);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadAskedQuestions(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const [result] = await Promise.all([
        client.listQuestionEvents({ page: 1, pageSize: 100 }),
        refreshBoardStatusMap(),
      ]);
      setAskedQuestions(result.items);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
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
      language: detectBrowserLanguage(),
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
        setChatPrompt("");
        return;
      }

      const result = await client.answerQuestion(answerPayload, requestId);

      setAnswerResult(result);
      setQuestion(prompt);
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
        language: detectBrowserLanguage(),
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
            userLikes: false,
            userDislikes: false,
            answerSuccess: null,
          };
          const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
          return next.slice(0, 200);
        });
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
          userLikes: false,
          userDislikes: false,
          answerSuccess: null,
        };
        const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
        return next.slice(0, 200);
      });
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
            language: detectBrowserLanguage(),
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
                userLikes: false,
                userDislikes: false,
                answerSuccess: null,
              };
              const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
              return next.slice(0, 200);
            });
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
              userLikes: false,
              userDislikes: false,
              answerSuccess: null,
            };
            const next = [row, ...prev.filter((item) => item.requestId !== row.requestId)];
            return next.slice(0, 200);
          });
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
      await client.routeToEditorialQueue({ questionEventId });
      await Promise.all([onLoadEditorialBoard(), refreshBoardStatusMap()]);
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
      const result = await client.listEditorialBoard({ page: 1, pageSize: 50 });
      setBoardResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadFaq(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const approved = await client.listEditorialBoard({ status: "approved", page: 1, pageSize: 100 });
      setFaqItems(approved.items);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  async function onLoadQuestionEventDetail(questionEventId: string): Promise<QuestionEventDetail> {
    try {
      return await client.getQuestionEventDetail(questionEventId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      throw caught;
    }
  }

  async function onQuickTransition(item: EditorialBoardItem, action: TransitionAction): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await client.transitionEditorialQueue({
        queueItemId: item.queueItemId,
        action,
        comment: `board action: ${action}`,
      });
      const refreshes: Promise<void>[] = [onLoadEditorialBoard(), refreshBoardStatusMap(), onLoadFaq()];
      if (action === "revoke") refreshes.push(onLoadAskedQuestions());
      await Promise.all(refreshes);
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
      <BrowserRouter basename="/napcore-helpdesk">
        <Routes>
          <Route
            path="/"
            element={
              <SharedAppLayout
                appVersion={frontendVersion}
                backendBuildRef={backendBuildRef}
              />
            }
          >
            <Route index element={<Navigate to="user" replace />} />
            <Route
              path="user"
              element={
                <UserChatWithQueryParams
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
                <EditorWithQueryParams
                  question={question}
                  answerResult={answerResult}
                  askedQuestions={askedQuestions}
                  selectedQuestionEventId={selectedQuestionEventId}
                  boardResult={boardResult}
                  faqItems={faqItems}
                  boardStatusMap={boardStatusMap}
                  busy={busy}
                  token={token}
                  setQuestion={setQuestion}
                  setSelectedQuestionEventId={setSelectedQuestionEventId}
                  onAskQuestion={onAskQuestion}
                  onLoadAskedQuestions={onLoadAskedQuestions}
                  onQueueEditorial={onQueueEditorial}
                  onDeleteQuestionEvent={onDeleteQuestionEvent}
                  onLoadEditorialBoard={onLoadEditorialBoard}
                  onLoadFaq={onLoadFaq}
                  onLoadQuestionEventDetail={onLoadQuestionEventDetail}
                  onQuickTransition={onQuickTransition}
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
