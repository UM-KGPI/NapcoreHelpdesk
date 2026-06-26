import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import type { AnswerResponse } from "../types";
import AnswerMarkdown from "./AnswerMarkdown";

export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  createdAt: string;
  answer?: AnswerResponse;
  requestId?: string;
}

interface UserChatWorkspaceProps {
  chatPrompt: string;
  chatTurns: ChatTurn[];
  token: string;
  busy: boolean;
  setChatPrompt: (value: string) => void;
  onSendChat: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onResetChatSession: () => void;
  onSetAnswerFeedback: (
    requestId: string,
    payload: {
      userLikes?: boolean;
      userDislikes?: boolean;
      answerSuccess?: boolean | null;
      citationClicksDelta?: number;
    }
  ) => Promise<void>;
}

export default function UserChatWorkspace(props: UserChatWorkspaceProps) {
  const {
    chatPrompt,
    chatTurns,
    token,
    busy,
    setChatPrompt,
    onSendChat,
    onResetChatSession,
    onSetAnswerFeedback,
  } = props;

  const latestUserTurnId = [...chatTurns].reverse().find((turn) => turn.role === "user")?.id;
  const chatLogRef = useRef<HTMLDivElement | null>(null);
  const latestUserTurnRef = useRef<HTMLElement | null>(null);
  const [feedbackPendingByRequestId, setFeedbackPendingByRequestId] = useState<Record<string, boolean>>({});

  const buildAnswerWithEvidenceText = (turn: ChatTurn): string => {
    const answerText = turn.text.trim();
    if (!answerText) {
      return "";
    }

    const lines: string[] = [answerText];
    if (turn.answer && turn.answer.citations.length > 0) {
      lines.push("");
      lines.push("Evidence list:");
      turn.answer.citations.forEach((citation, index) => {
        const label = citation.label ?? citation.sourcePath;
        lines.push(
          `- [E${index + 1}] ${label} | ${citation.sourcePath} | ${citation.repositoryUrl}`
        );
      });
    }

    return lines.join("\n");
  };

  const copyAnswerToClipboard = async (turn: ChatTurn) => {
    const text = buildAnswerWithEvidenceText(turn);
    if (!text) {
      return;
    }

    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const temp = document.createElement("textarea");
    temp.value = text;
    temp.setAttribute("readonly", "true");
    temp.style.position = "absolute";
    temp.style.left = "-9999px";
    document.body.appendChild(temp);
    temp.select();
    document.execCommand("copy");
    document.body.removeChild(temp);
  };

  const exportChatAsTextMarkdown = () => {
    const lines: string[] = [];
    lines.push("# NAPCORE Helpdesk Chat Export");
    lines.push("");
    lines.push(`Generated: ${new Date().toISOString()}`);
    lines.push("");

    for (const turn of chatTurns) {
      lines.push(`## ${turn.role === "assistant" ? "Assistant" : "User"}`);
      lines.push(`Timestamp: ${turn.createdAt}`);
      lines.push("");
      lines.push(turn.text || "");
      if (turn.answer && turn.answer.citations.length > 0) {
        lines.push("");
        lines.push("### Evidence list");
        turn.answer.citations.forEach((citation, index) => {
          const label = citation.label ?? citation.sourcePath;
          lines.push(
            `- [E${index + 1}] ${label} | ${citation.sourcePath} | ${citation.repositoryUrl}`
          );
        });
      }
      if (turn.answer) {
        const feedbackLike = turn.answer.trace.userLikes ?? false;
        const feedbackDislike = turn.answer.trace.userDislikes ?? false;
        lines.push("");
        lines.push(
          `Trace: requestId=${turn.requestId ?? turn.answer.trace.requestId}; mode=${turn.answer.mode}; confidence=${turn.answer.confidence.toFixed(2)}; userLikes=${String(feedbackLike)}; userDislikes=${String(feedbackDislike)}; answerSuccess=${String(turn.answer.trace.answerSuccess ?? null)}; citationClickCount=${String(turn.answer.trace.citationClickCount ?? 0)}`
        );
      }
      lines.push("");
    }

    const fileText = lines.join("\n");
    const blob = new Blob([fileText], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    const exportId = "chat";
    link.href = URL.createObjectURL(blob);
    link.download = `${exportId}-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };

  const setFeedback = async (
    requestId: string,
    payload: {
      userLikes?: boolean;
      userDislikes?: boolean;
      answerSuccess?: boolean | null;
      citationClicksDelta?: number;
    }
  ) => {
    setFeedbackPendingByRequestId((prev) => ({ ...prev, [requestId]: true }));
    try {
      await onSetAnswerFeedback(requestId, payload);
    } finally {
      setFeedbackPendingByRequestId((prev) => {
        const next = { ...prev };
        delete next[requestId];
        return next;
      });
    }
  };

  const alignLatestUserBubbleToTop = () => {
    if (!latestUserTurnRef.current || !chatLogRef.current) {
      return;
    }

    const chatLog = chatLogRef.current;
    const latestUserTurn = latestUserTurnRef.current;
    const containerRect = chatLog.getBoundingClientRect();
    const bubbleRect = latestUserTurn.getBoundingClientRect();
    const delta = bubbleRect.top - containerRect.top;
    chatLog.scrollTop = Math.max(0, chatLog.scrollTop + delta - 8);
  };

  useLayoutEffect(() => {
    if (!busy || !latestUserTurnRef.current || !chatLogRef.current) {
      return;
    }

    alignLatestUserBubbleToTop();
    const frameId = window.requestAnimationFrame(alignLatestUserBubbleToTop);
    return () => window.cancelAnimationFrame(frameId);
  }, [busy, latestUserTurnId, chatTurns.length]);

  useEffect(() => {
    if (!busy) {
      return;
    }

    const intervalId = window.setInterval(() => {
      alignLatestUserBubbleToTop();
    }, 60);

    return () => window.clearInterval(intervalId);
  }, [busy, latestUserTurnId]);

  return (
    <section className="workspace-section user-workspace">
      <section className="panel chat-panel">

        <details className="getting-started-inline collapsible-panel">
          <summary className="collapsible-summary getting-started-summary">
            <span>Getting Started</span>
          </summary>
          <div className="collapsible-body welcome-grid">
            <div>
              <strong>1. Ask plainly</strong>
              <p className="muted">Type the standards question in your own words. The assistant grounds the answer in indexed source material.</p>
            </div>
            <div>
              <strong>2. Review answer</strong>
              <p className="muted">Check the returned answer and references, and inspect the overall quality of the response.</p>
            </div>
            <div>
              <strong>3. Follow up</strong>
              <p className="muted">Ask further questions in the same session. Each question is answered independently — the assistant does not retain prior turns as context.</p>
            </div>
          </div>
        </details>

        <div className="chat-log" aria-live="polite" ref={chatLogRef}>
          {chatTurns.length === 0 && <p className="muted">Start a conversation.</p>}
          {chatTurns.map((turn) => (
            <article
              key={turn.id}
              ref={turn.id === latestUserTurnId ? latestUserTurnRef : undefined}
              className={`chat-bubble ${turn.role === "user" ? "chat-user" : "chat-assistant"}`}
            >
              <p className="chat-role">{turn.role}</p>
              {turn.role === "assistant" ? <AnswerMarkdown text={turn.text} /> : <p>{turn.text}</p>}
              {turn.answer && (
                <>
                  <div className="chat-answer-actions" role="group" aria-label="Answer actions">
                    <button
                      type="button"
                      className="chat-icon-button"
                      onClick={() => {
                        void copyAnswerToClipboard(turn);
                      }}
                      title="Copy answer to clipboard"
                      aria-label="Copy answer to clipboard"
                    >
                      📋
                    </button>
                    <button
                      type="button"
                      className="chat-icon-button"
                      onClick={exportChatAsTextMarkdown}
                      title="Export chat to Markdown text file"
                      aria-label="Export chat to Markdown text file"
                    >
                      💾
                    </button>
                    <button
                      type="button"
                      className={`chat-icon-button ${(turn.answer.trace.userLikes ?? false) ? "chat-icon-button-active" : ""}`}
                      onClick={() => {
                        const requestId = turn.requestId ?? turn.answer?.trace.requestId;
                        if (!requestId) {
                          return;
                        }
                        const currentLike = turn.answer?.trace.userLikes ?? false;
                        void setFeedback(requestId, { userLikes: !currentLike, userDislikes: false, answerSuccess: !currentLike });
                      }}
                      disabled={feedbackPendingByRequestId[turn.requestId ?? turn.answer.trace.requestId] === true}
                      title="Good answer"
                      aria-label="Good answer"
                    >
                      👍
                    </button>
                    <button
                      type="button"
                      className={`chat-icon-button ${(turn.answer.trace.userDislikes ?? false) ? "chat-icon-button-active" : ""}`}
                      onClick={() => {
                        const requestId = turn.requestId ?? turn.answer?.trace.requestId;
                        if (!requestId) {
                          return;
                        }
                        const currentDislike = turn.answer?.trace.userDislikes ?? false;
                        void setFeedback(requestId, { userLikes: false, userDislikes: !currentDislike, answerSuccess: currentDislike });
                      }}
                      disabled={feedbackPendingByRequestId[turn.requestId ?? turn.answer.trace.requestId] === true}
                      title="Answer could be better"
                      aria-label="Answer could be better"
                    >
                      👎
                    </button>
                  </div>
                  {turn.answer.citations.length > 0 && (
                    <>
                      <p className="tiny"><strong>Evidence list</strong></p>
                      <ul>
                        {turn.answer.citations.map((citation, index) => (
                          <li key={`${turn.id}-${citation.chunkId}`}>
                            <strong>{`[E${index + 1}]`}</strong>{" "}
                            <a
                              href={citation.repositoryUrl}
                              target="_blank"
                              rel="noreferrer"
                              onClick={() => {
                                const requestId = turn.requestId ?? turn.answer?.trace.requestId;
                                if (!requestId) {
                                  return;
                                }
                                void onSetAnswerFeedback(requestId, { citationClicksDelta: 1 });
                              }}
                            >
                              {citation.label ?? citation.sourcePath}
                            </a>
                            <span className="muted"> · {citation.sourcePath}</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                  <p className="muted tiny">
                    requestId: {turn.requestId ?? turn.answer.trace.requestId} · mode: {turn.answer.mode} · confidence: {turn.answer.confidence.toFixed(2)}
                    {` · answerSuccess: ${String(turn.answer.trace.answerSuccess ?? null)} · citationClicks: ${String(turn.answer.trace.citationClickCount ?? 0)}`}
                  </p>
                </>
              )}
            </article>
          ))}
        </div>

        <form onSubmit={onSendChat} className="stack">
          <label>
            Message
            <textarea
              value={chatPrompt}
              onChange={(event) => setChatPrompt(event.target.value)}
              rows={3}
              placeholder="Ask a standards question..."
              required
            />
          </label>

          <div className="chat-actions">
            <button type="submit" disabled={busy || !token || !chatPrompt.trim()}>Send</button>
            <button type="button" onClick={onResetChatSession} disabled={busy}>New Session</button>
          </div>

          {busy && (
            <div className="chat-progress" role="status" aria-live="polite" aria-label="Generating answer">
              <div className="chat-progress-bar" />
              <p className="chat-progress-label muted tiny">Generating answer...</p>
            </div>
          )}
        </form>

      </section>
    </section>
  );
}
