/**
 * Read-only display of a stored question and answer.
 * Used on the /question page for deep-linked Q&A exchanges.
 * Shows only the question, answer, and citations — no input field, no buttons.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

import AnswerMarkdown from "./AnswerMarkdown";
import type { ChatTurn } from "./UserChatWorkspace";

interface ReadOnlyQuestionDisplayProps {
  chatTurns: ChatTurn[];
  onSetAnswerFeedback?: (
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
    <section className="workspace-section user-workspace">
      <section className="panel chat-panel">
        <div className="chat-log" aria-live="polite">
          {chatTurns.length === 0 && <p className="muted">No question found.</p>}
          {chatTurns.map((turn) => (
            <article key={turn.id} className={`chat-bubble ${turn.role === "user" ? "chat-user" : "chat-assistant"}`}>
              <p className="chat-role">{turn.role}</p>
              {turn.role === "assistant" ? <AnswerMarkdown text={turn.text} /> : <p>{turn.text}</p>}
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
                  </div>
                  <details className="collapsible-panel citations-collapsible">
                    <summary className="collapsible-summary">
                      <span>
                        {turn.answer.citations.length} citation{turn.answer.citations.length !== 1 ? "s" : ""}
                      </span>
                    </summary>
                    <div className="collapsible-body citations-list">
                      {turn.answer.citations.map((citation, i) => (
                        <div key={i} className="citation-item">
                          <a
                            href={citation.repositoryUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="citation-link"
                            onClick={() => {
                              if (onSetAnswerFeedback && turn.requestId) {
                                void onSetAnswerFeedback(turn.requestId, { citationClicksDelta: 1 });
                              }
                            }}
                          >
                            {citation.label || citation.sourcePath}
                          </a>
                        </div>
                      ))}
                    </div>
                  </details>
                  {turn.answer.confidence && (
                    <div className="confidence-indicator">
                      <span className="confidence-label">Confidence:</span>
                      <span className="confidence-value">{(turn.answer.confidence * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </>
              )}
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
