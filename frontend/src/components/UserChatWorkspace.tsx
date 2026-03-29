import type { FormEvent } from "react";

import type { AnswerResponse, StandardsScope } from "../types";

export type ChatProfile = "deterministic-grounded" | "llm-ready";

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
  chatApplyScope: boolean;
  standardsScope: StandardsScope[];
  chatPrompt: string;
  chatTurns: ChatTurn[];
  token: string;
  busy: boolean;
  setSessionId: (value: string) => void;
  setUserId: (value: string) => void;
  setChatProfile: (value: ChatProfile) => void;
  setChatApplyScope: (value: boolean) => void;
  setChatPrompt: (value: string) => void;
  onSendChat: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onResetChatSession: () => void;
}

export default function UserChatWorkspace(props: UserChatWorkspaceProps) {
  const {
    sessionId,
    userId,
    chatProfile,
    chatApplyScope,
    standardsScope,
    chatPrompt,
    chatTurns,
    token,
    busy,
    setSessionId,
    setUserId,
    setChatProfile,
    setChatApplyScope,
    setChatPrompt,
    onSendChat,
    onResetChatSession,
  } = props;

  return (
    <section className="workspace-section user-workspace">
      <header className="workspace-header">
        <p className="kicker">User Workspace</p>
        <h2>User Chat Interface</h2>
        <p className="muted">Independent user-facing conversation area (planned standalone surface).</p>
      </header>

      <section className="panel chat-panel">
        <p className="kicker">NAPCORE HELPDESK</p>
        <h2>Q&amp;A about NAPCORE related multimodal standardisation</h2>
        <p className="muted">Web GUI chat for users</p>

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
              <option value="deterministic-grounded">deterministic-grounded (active)</option>
              <option value="llm-ready">llm-ready (wiring pending backend)</option>
            </select>
          </label>
        </div>

        <div className="chat-log" aria-live="polite">
          {chatTurns.length === 0 && <p className="muted">Start a conversation. The client remembers turn history in this session.</p>}
          {chatTurns.map((turn) => (
            <article key={turn.id} className={`chat-bubble ${turn.role === "user" ? "chat-user" : "chat-assistant"}`}>
              <p className="chat-role">{turn.role}</p>
              <p>{turn.text}</p>
              {turn.answer && (
                <>
                  <p className="muted tiny">
                    mode: {turn.answer.mode} · confidence: {turn.answer.confidence.toFixed(2)} · reviewRequired: {String(turn.answer.reviewRequired)}
                  </p>
                  {turn.answer.citations.length > 0 && (
                    <ul>
                      {turn.answer.citations.map((citation) => (
                        <li key={`${turn.id}-${citation.chunkId}`}>
                          <a href={citation.repositoryUrl} target="_blank" rel="noreferrer">{citation.label ?? citation.sourcePath}</a>
                          <span className="muted"> · {citation.sourcePath} · {citation.commitSha.slice(0, 7)}</span>
                        </li>
                      ))}
                    </ul>
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
            <label className="checkbox-label">
              <input type="checkbox" checked={chatApplyScope} onChange={(event) => setChatApplyScope(event.target.checked)} />
              apply selected standards scope ({standardsScope.join(", ") || "none"})
            </label>
            <button type="submit" disabled={busy || !token || !chatPrompt.trim()}>Send</button>
            <button type="button" onClick={onResetChatSession} disabled={busy}>New Session</button>
          </div>
        </form>
      </section>
    </section>
  );
}