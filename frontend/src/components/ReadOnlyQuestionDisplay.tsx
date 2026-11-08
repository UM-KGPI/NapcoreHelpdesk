/**
 * Read-only display of a stored question and answer.
 * Used on the /question page for deep-linked Q&A exchanges.
 * Shows only the question, answer, and citations — no input field, no send/reset buttons.
 * Includes interactive buttons: copy deep link, copy answer, like/dislike, and citations.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

import React from "react";
import { citationDisplayName, groupCitationsBySource } from "../citationLabels";
import GeneratedExampleBlock from "./GeneratedExample";
import AnswerBody from "./AnswerBody";
import LegalContext from "./LegalContext";
import type { ChatTurn } from "./UserChatWorkspace";

interface ReadOnlyQuestionDisplayProps {
  chatTurns: ChatTurn[];
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

export default function ReadOnlyQuestionDisplay({
  chatTurns,
  onSetAnswerFeedback,
}: ReadOnlyQuestionDisplayProps) {
  const [feedbackPendingByRequestId, setFeedbackPendingByRequestId] = React.useState<Record<string, boolean>>({});

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
      setFeedbackPendingByRequestId((prev) => ({ ...prev, [requestId]: false }));
    }
  };
  const copyDeepLinkToClipboard = async (turn: ChatTurn) => {
    const questionId = turn.requestId ?? turn.answer?.trace.requestId;
    if (!questionId) {
      return;
    }

    const baseUrl = window.location.origin;
    const deepLink = `${baseUrl}/napcore-helpdesk/question?questionId=${questionId}`;

    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(deepLink);
      return;
    }

    const temp = document.createElement("textarea");
    temp.value = deepLink;
    temp.setAttribute("readonly", "true");
    temp.style.position = "absolute";
    temp.style.left = "-9999px";
    document.body.appendChild(temp);
    temp.select();
    document.execCommand("copy");
    document.body.removeChild(temp);
  };

  const copyAnswerToClipboard = async (turn: ChatTurn) => {
    if (!turn.text) return;
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(turn.text);
      return;
    }

    const temp = document.createElement("textarea");
    temp.value = turn.text;
    temp.setAttribute("readonly", "true");
    temp.style.position = "absolute";
    temp.style.left = "-9999px";
    document.body.appendChild(temp);
    temp.select();
    document.execCommand("copy");
    document.body.removeChild(temp);
  };

  return (
    <section className="panel chat-panel user-workspace">
        <div className="chat-log" aria-live="polite">
          {chatTurns.length === 0 && <p className="muted">No question found.</p>}
          {chatTurns.map((turn) => (
            <article key={turn.id} className={`chat-bubble ${turn.role === "user" ? "chat-user" : "chat-assistant"}`}>
              <p className="chat-role">{turn.role}</p>
              {turn.role === "assistant" ? (
                <AnswerBody text={turn.text} example={turn.answer?.generatedExample} />
              ) : (
                <p>{turn.text}</p>
              )}
              {turn.answer && (
                <>
                  <div className="chat-answer-actions" role="group" aria-label="Answer actions">
                    <button
                      type="button"
                      className="chat-icon-button"
                      onClick={() => {
                        void copyDeepLinkToClipboard(turn);
                      }}
                      title="Copy deep link to share this Q&A"
                      aria-label="Copy deep link to share this Q&A"
                    >
                      🔗
                    </button>
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
                      className={`chat-icon-button ${(turn.answer.trace.userLikes ?? false) ? "chat-icon-button-active" : ""}`}
                      onClick={() => {
                        const requestId = turn.requestId ?? turn.answer?.trace.requestId;
                        if (!requestId) {
                          return;
                        }
                        const currentLike = turn.answer?.trace.userLikes ?? false;
                        void setFeedback(requestId, { userLikes: !currentLike, userDislikes: false, answerSuccess: currentLike ? null : true });
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
                        void setFeedback(requestId, { userLikes: false, userDislikes: !currentDislike, answerSuccess: currentDislike ? null : false });
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
                        {groupCitationsBySource(turn.answer.citations).map((group) => (
                          <li key={`${turn.id}-${group.primary.chunkId}`}>
                            <strong>{group.markers.join(" ")}</strong>{" "}
                            <a
                              href={group.primary.repositoryUrl}
                              target="_blank"
                              rel="noreferrer"
                              onClick={() => {
                                const requestId = turn.requestId ?? turn.answer?.trace.requestId;
                                if (!requestId) {
                                  return;
                                }
                                void setFeedback(requestId, { citationClicksDelta: 1 });
                              }}
                            >
                              {citationDisplayName(group.primary)}
                            </a>
                            {!group.primary.title && citationDisplayName(group.primary) !== group.primary.sourcePath && (
                              <span className="muted"> · {group.primary.sourcePath}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                  {!turn.answer.generatedExample?.valid && <GeneratedExampleBlock example={turn.answer.generatedExample} />}
                  <LegalContext items={turn.answer.legalContext} />
                </>
              )}
            </article>
          ))}
        </div>
    </section>
  );
}
