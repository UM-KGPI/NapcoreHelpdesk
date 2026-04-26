import type { FormEvent } from "react";

import type { AnswerResponse, StandardsScope } from "../types";
import AnswerMarkdown from "./AnswerMarkdown";

export type ChatProfile = "deterministic-grounded" | "llm-ready";

const STANDARDS: StandardsScope[] = ["Transmodel", "NeTEx", "SIRI", "OpRa", "DATEX II", "Profile Documentation"];

export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  createdAt: string;
  answer?: AnswerResponse;
  requestId?: string;
}

interface UserChatWorkspaceProps {
  sessionId: string;
  userId: string;
  chatProfile: ChatProfile;
  standardsScope: StandardsScope[];
  chatPrompt: string;
  chatTurns: ChatTurn[];
  token: string;
  busy: boolean;
  setSessionId: (value: string) => void;
  setUserId: (value: string) => void;
  setChatProfile: (value: ChatProfile) => void;
  toggleScope: (scope: StandardsScope) => void;
  setChatPrompt: (value: string) => void;
  onSendChat: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onResetChatSession: () => void;
}

export default function UserChatWorkspace(props: UserChatWorkspaceProps) {
  const {
    sessionId,
    userId,
    chatProfile,
    standardsScope,
    chatPrompt,
    chatTurns,
    token,
    busy,
    setSessionId,
    setUserId,
    setChatProfile,
    toggleScope,
    setChatPrompt,
    onSendChat,
    onResetChatSession,
  } = props;

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
              <strong>2. Review citations</strong>
              <p className="muted">Check the returned references to inspect the exact source text or repository path.</p>
            </div>
            <div>
              <strong>3. Tune only if needed</strong>
              <p className="muted">Open Advanced Settings only when you want to change session identity, scope, or generation profile.</p>
            </div>
          </div>
        </details>

        <div className="chat-log" aria-live="polite">
          {chatTurns.length === 0 && <p className="muted">Start a conversation. The client remembers turn history in this session.</p>}
          {chatTurns.map((turn) => (
            <article key={turn.id} className={`chat-bubble ${turn.role === "user" ? "chat-user" : "chat-assistant"}`}>
              <p className="chat-role">{turn.role}</p>
              {turn.role === "assistant" ? <AnswerMarkdown text={turn.text} /> : <p>{turn.text}</p>}
              {turn.answer && (
                <>
                  <p className="muted tiny">
                    mode: {turn.answer.mode} · confidence: {turn.answer.confidence.toFixed(2)} · reviewRequired: {String(turn.answer.reviewRequired)}
                  </p>
                  {(turn.answer.trace.semanticProvisional || turn.answer.trace.crossStandardConflict) && (
                    <div className="semantic-trace-chip-row">
                      {turn.answer.trace.semanticProvisional && (
                        <span className="semantic-chip semantic-chip-provisional">
                          provisional evidence
                          {turn.answer.trace.semanticProvisionalReason
                            ? `: ${turn.answer.trace.semanticProvisionalReason}`
                            : ""}
                        </span>
                      )}
                      {turn.answer.trace.evidenceCoverageLevel && (
                        <span className="semantic-chip semantic-chip-coverage">
                          coverage: {turn.answer.trace.evidenceCoverageLevel}
                        </span>
                      )}
                      {turn.answer.trace.crossStandardConflict && (
                        <span className="semantic-chip semantic-chip-conflict">
                          cross-standard conflict
                          {turn.answer.trace.crossStandardConflictType
                            ? `: ${turn.answer.trace.crossStandardConflictType}`
                            : ""}
                        </span>
                      )}
                    </div>
                  )}
                  {(turn.answer.trace.semanticDisambiguationRequired || turn.answer.trace.semanticFallback) && (
                    <div className="semantic-trace-note tiny muted">
                      {turn.answer.trace.semanticDisambiguationRequired && turn.answer.trace.semanticDisambiguationPrompt
                        ? turn.answer.trace.semanticDisambiguationPrompt
                        : null}
                      {turn.answer.trace.semanticFallback
                        ? `${turn.answer.trace.semanticDisambiguationRequired ? " · " : ""}fallback: ${turn.answer.trace.semanticFallback}`
                        : null}
                    </div>
                  )}
                  {turn.answer.trace.crossStandardEvidencePartitions &&
                    turn.answer.trace.crossStandardEvidencePartitions.length > 0 && (
                      <details className="semantic-partitions">
                        <summary className="tiny">Cross-standard evidence partitions</summary>
                        <ul className="semantic-partitions-list">
                          {turn.answer.trace.crossStandardEvidencePartitions.map((partition) => (
                            <li key={`${turn.id}-${partition.standard}`}>
                              <strong>{partition.standard}</strong>
                              <span className="muted tiny">
                                {` · evidence: ${partition.evidenceCount} · avg score: ${partition.avgScore.toFixed(2)}`}
                              </span>
                              {partition.normativitySignals.length > 0 && (
                                <div className="tiny muted">
                                  normativity: {partition.normativitySignals.join(", ")}
                                </div>
                              )}
                              {partition.topSourcePaths.length > 0 && (
                                <div className="tiny muted">
                                  top sources: {partition.topSourcePaths.join(" | ")}
                                </div>
                              )}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                  {turn.answer.citations.length > 0 && (
                    <>
                      <p className="tiny"><strong>Evidence list</strong></p>
                      <ul>
                        {turn.answer.citations.map((citation, index) => (
                          <li key={`${turn.id}-${citation.chunkId}`}>
                            <strong>{`[E${index + 1}]`}</strong>{" "}
                            <a href={citation.repositoryUrl} target="_blank" rel="noreferrer">{citation.label ?? citation.sourcePath}</a>
                            <span className="muted"> · {citation.sourcePath} · {citation.commitSha.slice(0, 7)}</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                  <p className="muted tiny">requestId: {turn.requestId ?? turn.answer.trace.requestId}</p>
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
        </form>

        <details className="advanced-controls collapsible-panel">
          <summary className="collapsible-summary advanced-controls-header">
            <div>
              <h3>Advanced Settings</h3>
              <p className="muted">Open this only when you want to adjust session identity, retrieval scope, or generation profile.</p>
            </div>
          </summary>

          <div className="collapsible-body">
            <div className="grid-three">
              <label>
                Session ID
                <input value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
              </label>
              <label>
                User ID
                <input value={userId} onChange={(event) => setUserId(event.target.value)} />
              </label>
              <label>
                Generation Profile
                <select value={chatProfile} onChange={(event) => setChatProfile(event.target.value as ChatProfile)}>
                  <option value="llm-ready">llm-ready (default)</option>
                  <option value="deterministic-grounded">deterministic-grounded</option>
                </select>
              </label>
            </div>

            <fieldset className="panel-subsection advanced-scope">
              <legend>Standards Scope</legend>
              <p className="muted">Selecting one or more standards restricts retrieval to those standards. Leave all unchecked to search across all indexed sources.</p>
              <div className="checkbox-grid">
                {STANDARDS.map((scope) => (
                  <label key={scope} className="checkbox-label">
                    <input type="checkbox" checked={standardsScope.includes(scope)} onChange={() => toggleScope(scope)} />
                    {scope}
                  </label>
                ))}
              </div>
            </fieldset>
          </div>
        </details>

      </section>
    </section>
  );
}
