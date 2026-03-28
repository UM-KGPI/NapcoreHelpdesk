import { FormEvent, useMemo, useState } from "react";

import { HelpdeskApiClient } from "./api";
import type {
  AnswerResponse,
  EditorialQueueResponse,
  EditorialQueueTransitionResponse,
  PromotionCandidatesResponse,
  StandardsScope,
} from "./types";

const STANDARDS: StandardsScope[] = ["Transmodel", "NeTEx", "SIRI", "OJP/OpRa", "DATEX II"];
const TRANSITION_ACTIONS = [
  "submit_for_review",
  "request_changes",
  "approve",
  "reject",
  "publish",
  "reopen",
] as const;

type TransitionAction = (typeof TRANSITION_ACTIONS)[number];

function createRequestId(): string {
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState("http://localhost:8000/api/v1");
  const [token, setToken] = useState("");

  const [question, setQuestion] = useState("How to use NeTEx for exchanging a timetable?");
  const [sessionId, setSessionId] = useState("sess-local");
  const [userId, setUserId] = useState("user-local");
  const [standardsScope, setStandardsScope] = useState<StandardsScope[]>(["NeTEx"]);

  const [answerResult, setAnswerResult] = useState<AnswerResponse | null>(null);
  const [promotionResult, setPromotionResult] = useState<PromotionCandidatesResponse | null>(null);
  const [editorialResult, setEditorialResult] = useState<EditorialQueueResponse | null>(null);
  const [transitionResult, setTransitionResult] = useState<EditorialQueueTransitionResponse | null>(null);

  const [windowDays, setWindowDays] = useState(14);
  const [minCount, setMinCount] = useState(3);
  const [onlyUnresolved, setOnlyUnresolved] = useState(true);

  const [queueReason, setQueueReason] = useState<"LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION">("LOW_CONFIDENCE");
  const [queuePriority, setQueuePriority] = useState<"low" | "normal" | "high">("normal");
  const [transitionQueueItemId, setTransitionQueueItemId] = useState("");
  const [transitionAction, setTransitionAction] = useState<TransitionAction>("submit_for_review");
  const [transitionComment, setTransitionComment] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const client = useMemo(() => new HelpdeskApiClient({ baseUrl: apiBaseUrl, token }), [apiBaseUrl, token]);

  const canQueueCurrentAnswer = Boolean(answerResult?.trace.questionEventId);

  function toggleScope(scope: StandardsScope): void {
    setStandardsScope((prev) => {
      if (prev.includes(scope)) {
        return prev.filter((item) => item !== scope);
      }
      return [...prev, scope];
    });
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
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <p className="kicker">NAPCORE Helpdesk</p>
        <h1>FAQ-first and Evidence-grounded Q&A Console</h1>
        <p className="subhead">Web GUI container for operators to run answers, inspect traces, and trigger editorial workflow.</p>
      </header>

      <section className="panel credentials-panel">
        <h2>Connection</h2>
        <div className="grid-two">
          <label>
            API Base URL
            <input value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} placeholder="http://localhost:8000/api/v1" />
          </label>
          <label>
            JWT Bearer Token
            <input value={token} onChange={(event) => setToken(event.target.value)} placeholder="Paste token" />
          </label>
        </div>
      </section>

      <main className="dashboard">
        <section className="panel">
          <h2>Ask Question</h2>
          <form onSubmit={onAskQuestion} className="stack">
            <label>
              Question
              <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} required />
            </label>
            <div className="grid-two">
              <label>
                Session ID
                <input value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
              </label>
              <label>
                User ID
                <input value={userId} onChange={(event) => setUserId(event.target.value)} />
              </label>
            </div>
            <fieldset className="scope-grid">
              <legend>Standards Scope</legend>
              {STANDARDS.map((scope) => (
                <label key={scope} className="scope-item">
                  <input type="checkbox" checked={standardsScope.includes(scope)} onChange={() => toggleScope(scope)} />
                  {scope}
                </label>
              ))}
            </fieldset>
            <button type="submit" disabled={busy || !token}>Run Orchestration</button>
          </form>

          {answerResult && (
            <article className="result-card">
              <h3>Answer Result</h3>
              <p className="mode-pill">mode: {answerResult.mode}</p>
              <p>{answerResult.answer}</p>
              <p>
                confidence: <strong>{answerResult.confidence.toFixed(2)}</strong>
              </p>
              <p>
                reviewRequired: <strong>{String(answerResult.reviewRequired)}</strong>
              </p>

              <h4>Citations</h4>
              {answerResult.citations.length === 0 && <p className="muted">No citations returned.</p>}
              {answerResult.citations.length > 0 && (
                <ul>
                  {answerResult.citations.map((citation) => (
                    <li key={`${citation.chunkId}-${citation.sourcePath}`}>
                      <a href={citation.repositoryUrl} target="_blank" rel="noreferrer">{citation.label ?? citation.sourcePath}</a>
                      <span className="muted"> · {citation.sourcePath} · {citation.commitSha.slice(0, 7)}</span>
                    </li>
                  ))}
                </ul>
              )}

              <h4>Trace</h4>
              <pre>{JSON.stringify(answerResult.trace, null, 2)}</pre>
            </article>
          )}
        </section>

        <section className="panel">
          <h2>Editorial Routing</h2>
          <p className="muted">Route current answer outcome into queue.</p>
          <div className="stack">
            <label>
              Reason
              <select value={queueReason} onChange={(event) => setQueueReason(event.target.value as typeof queueReason)}>
                <option value="LOW_CONFIDENCE">LOW_CONFIDENCE</option>
                <option value="CITATION_GAP">CITATION_GAP</option>
                <option value="POLICY_REVIEW">POLICY_REVIEW</option>
                <option value="USER_ESCALATION">USER_ESCALATION</option>
              </select>
            </label>
            <label>
              Priority
              <select value={queuePriority} onChange={(event) => setQueuePriority(event.target.value as typeof queuePriority)}>
                <option value="low">low</option>
                <option value="normal">normal</option>
                <option value="high">high</option>
              </select>
            </label>
            <button onClick={onQueueEditorial} disabled={busy || !token || !canQueueCurrentAnswer}>Queue for Editorial</button>
          </div>

          {editorialResult && (
            <article className="result-card">
              <h3>Editorial Queue Result</h3>
              <p>queued: <strong>{String(editorialResult.queued)}</strong></p>
              <p>queueItemId: <code>{editorialResult.queueItemId}</code></p>
              <p>status: <strong>{editorialResult.status}</strong></p>
            </article>
          )}

          <h3>Editorial Transition</h3>
          <p className="muted">Apply workflow actions to a queue item.</p>
          <div className="stack">
            <label>
              queueItemId
              <input
                value={transitionQueueItemId}
                onChange={(event) => setTransitionQueueItemId(event.target.value)}
                placeholder="Paste queueItemId"
              />
            </label>
            <label>
              Action
              <select value={transitionAction} onChange={(event) => setTransitionAction(event.target.value as TransitionAction)}>
                {TRANSITION_ACTIONS.map((action) => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
            </label>
            <label>
              Comment
              <textarea
                value={transitionComment}
                onChange={(event) => setTransitionComment(event.target.value)}
                rows={2}
                placeholder="Optional transition comment"
              />
            </label>
            <button onClick={onTransitionEditorial} disabled={busy || !token || !transitionQueueItemId.trim()}>
              Apply Transition
            </button>
          </div>

          {transitionResult && (
            <article className="result-card">
              <h3>Transition Result</h3>
              <p>queueItemId: <code>{transitionResult.queueItemId}</code></p>
              <p>status: <strong>{transitionResult.status}</strong></p>
              <p>
                action: <strong>{transitionResult.transition.action}</strong>
                <span className="muted"> · {transitionResult.transition.fromStatus} to {transitionResult.transition.toStatus}</span>
              </p>
              <p>
                actor: <strong>{transitionResult.transition.actorId}</strong>
                <span className="muted"> · roles: {transitionResult.transition.actorRoles.join(", ") || "none"}</span>
              </p>
            </article>
          )}
        </section>

        <section className="panel">
          <h2>Promotion Candidates</h2>
          <div className="grid-three">
            <label>
              windowDays
              <input type="number" min={1} value={windowDays} onChange={(event) => setWindowDays(Number(event.target.value))} />
            </label>
            <label>
              minCount
              <input type="number" min={1} value={minCount} onChange={(event) => setMinCount(Number(event.target.value))} />
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={onlyUnresolved} onChange={(event) => setOnlyUnresolved(event.target.checked)} />
              onlyUnresolved
            </label>
          </div>
          <button onClick={onLoadPromotionCandidates} disabled={busy || !token}>Load Candidates</button>

          {promotionResult && (
            <article className="result-card">
              <h3>Top Candidate Intents</h3>
              {promotionResult.items.length === 0 && <p className="muted">No candidates found for these filters.</p>}
              {promotionResult.items.length > 0 && (
                <ul>
                  {promotionResult.items.map((item) => (
                    <li key={`${item.normalizedIntent}-${item.lastAskedAt}`}>
                      <strong>{item.normalizedIntent}</strong>
                      <span className="muted"> · count {item.questionCount} · {item.recommendedAction}</span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          )}
        </section>
      </main>

      {error && <div className="error-banner">{error}</div>}
    </div>
  );
}
