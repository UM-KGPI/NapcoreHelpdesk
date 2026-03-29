import type { FormEvent } from "react";

import type {
  AnswerResponse,
  EditorialBoardMetricsResponse,
  EditorialBoardItem,
  EditorialBoardResponse,
  EditorialQueueResponse,
  EditorialQueueTransitionResponse,
  PromotionCandidatesResponse,
  StandardsScope,
} from "../types";

const STANDARDS: StandardsScope[] = ["Transmodel", "NeTEx", "SIRI", "OJP/OpRa", "DATEX II"];
const TRANSITION_ACTIONS = ["submit_for_review", "request_changes", "approve", "reject", "publish", "reopen"] as const;
const BOARD_STATUSES = ["draft", "review", "approved", "rejected", "published"] as const;
const BOARD_REASONS = ["LOW_CONFIDENCE", "CITATION_GAP", "POLICY_REVIEW", "USER_ESCALATION"] as const;
const BOARD_PRIORITIES = ["low", "normal", "high"] as const;

type TransitionAction = (typeof TRANSITION_ACTIONS)[number];
type BoardStatus = (typeof BOARD_STATUSES)[number];
type BoardReason = (typeof BOARD_REASONS)[number];
type BoardPriority = (typeof BOARD_PRIORITIES)[number];
type QueueReason = "LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION";
type QueuePriority = "low" | "normal" | "high";

interface OperatorConsoleWorkspaceProps {
  question: string;
  sessionId: string;
  userId: string;
  standardsScope: StandardsScope[];
  answerResult: AnswerResponse | null;
  promotionResult: PromotionCandidatesResponse | null;
  editorialResult: EditorialQueueResponse | null;
  transitionResult: EditorialQueueTransitionResponse | null;
  boardResult: EditorialBoardResponse | null;
  boardMetrics: EditorialBoardMetricsResponse | null;
  windowDays: number;
  minCount: number;
  onlyUnresolved: boolean;
  queueReason: QueueReason;
  queuePriority: QueuePriority;
  transitionQueueItemId: string;
  transitionAction: TransitionAction;
  transitionComment: string;
  boardStatus: BoardStatus | "";
  boardReason: BoardReason | "";
  boardPriority: BoardPriority | "";
  boardSearch: string;
  boardPage: number;
  boardPageSize: number;
  metricsWindowDays: number;
  metricsSlaHours: number;
  busy: boolean;
  token: string;
  setQuestion: (value: string) => void;
  setSessionId: (value: string) => void;
  setUserId: (value: string) => void;
  toggleScope: (scope: StandardsScope) => void;
  setWindowDays: (value: number) => void;
  setMinCount: (value: number) => void;
  setOnlyUnresolved: (value: boolean) => void;
  setQueueReason: (value: QueueReason) => void;
  setQueuePriority: (value: QueuePriority) => void;
  setTransitionQueueItemId: (value: string) => void;
  setTransitionAction: (value: TransitionAction) => void;
  setTransitionComment: (value: string) => void;
  setBoardStatus: (value: BoardStatus | "") => void;
  setBoardReason: (value: BoardReason | "") => void;
  setBoardPriority: (value: BoardPriority | "") => void;
  setBoardSearch: (value: string) => void;
  setBoardPage: (value: number) => void;
  setBoardPageSize: (value: number) => void;
  setMetricsWindowDays: (value: number) => void;
  setMetricsSlaHours: (value: number) => void;
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onLoadPromotionCandidates: () => Promise<void>;
  onQueueEditorial: () => Promise<void>;
  onTransitionEditorial: () => Promise<void>;
  onLoadEditorialBoard: () => Promise<void>;
  onQuickTransition: (item: EditorialBoardItem, action: TransitionAction) => Promise<void>;
  onLoadBoardMetrics: () => Promise<void>;
}

export default function OperatorConsoleWorkspace(props: OperatorConsoleWorkspaceProps) {
  const {
    question,
    sessionId,
    userId,
    standardsScope,
    answerResult,
    promotionResult,
    editorialResult,
    transitionResult,
    boardResult,
    boardMetrics,
    windowDays,
    minCount,
    onlyUnresolved,
    queueReason,
    queuePriority,
    transitionQueueItemId,
    transitionAction,
    transitionComment,
    boardStatus,
    boardReason,
    boardPriority,
    boardSearch,
    boardPage,
    boardPageSize,
    metricsWindowDays,
    metricsSlaHours,
    busy,
    token,
    setQuestion,
    setSessionId,
    setUserId,
    toggleScope,
    setWindowDays,
    setMinCount,
    setOnlyUnresolved,
    setQueueReason,
    setQueuePriority,
    setTransitionQueueItemId,
    setTransitionAction,
    setTransitionComment,
    setBoardStatus,
    setBoardReason,
    setBoardPriority,
    setBoardSearch,
    setBoardPage,
    setBoardPageSize,
    setMetricsWindowDays,
    setMetricsSlaHours,
    onAskQuestion,
    onLoadPromotionCandidates,
    onQueueEditorial,
    onTransitionEditorial,
    onLoadEditorialBoard,
    onQuickTransition,
    onLoadBoardMetrics,
  } = props;

  const canQueueCurrentAnswer = Boolean(answerResult?.trace.questionEventId);

  return (
    <section className="workspace-section operator-workspace">
      <header className="workspace-header">
        <p className="kicker">Operator Workspace</p>
        <h2>Operator Console</h2>
        <p className="muted">Operational controls for orchestration, editorial review, and queue governance.</p>
      </header>

      <div className="dashboard">
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
          <h2>Editorial Board</h2>
          <p className="muted">Filter queue items and apply inline workflow actions.</p>
          <div className="grid-three">
            <label>
              metricsWindowDays
              <input type="number" min={1} value={metricsWindowDays} onChange={(event) => setMetricsWindowDays(Number(event.target.value))} />
            </label>
            <label>
              metricsSlaHours
              <input type="number" min={1} value={metricsSlaHours} onChange={(event) => setMetricsSlaHours(Number(event.target.value))} />
            </label>
            <label>
              KPIs
              <button onClick={onLoadBoardMetrics} disabled={busy || !token}>Load Metrics</button>
            </label>
          </div>

          {boardMetrics && (
            <article className="result-card">
              <h3>Queue KPIs</h3>
              <p className="muted">generated {boardMetrics.generatedAt}</p>
              <div className="kpi-grid">
                <div className="kpi-tile"><span>Total</span><strong>{boardMetrics.totalItems}</strong></div>
                <div className="kpi-tile"><span>Unresolved</span><strong>{boardMetrics.unresolvedItems}</strong></div>
                <div className="kpi-tile"><span>Overdue</span><strong>{boardMetrics.overdueItems}</strong></div>
                <div className="kpi-tile"><span>Draft</span><strong>{boardMetrics.byStatus.draft}</strong></div>
                <div className="kpi-tile"><span>Review</span><strong>{boardMetrics.byStatus.review}</strong></div>
                <div className="kpi-tile"><span>Approved</span><strong>{boardMetrics.byStatus.approved}</strong></div>
                <div className="kpi-tile"><span>lt24h</span><strong>{boardMetrics.agingBuckets.lt24h}</strong></div>
                <div className="kpi-tile"><span>24to72h</span><strong>{boardMetrics.agingBuckets.h24to72}</strong></div>
                <div className="kpi-tile"><span>gt72h</span><strong>{boardMetrics.agingBuckets.gt72h}</strong></div>
              </div>
            </article>
          )}

          <div className="grid-three">
            <label>
              Status
              <select value={boardStatus} onChange={(event) => setBoardStatus(event.target.value as BoardStatus | "") }>
                <option value="">any</option>
                {BOARD_STATUSES.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
            <label>
              Reason
              <select value={boardReason} onChange={(event) => setBoardReason(event.target.value as BoardReason | "") }>
                <option value="">any</option>
                {BOARD_REASONS.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
            <label>
              Priority
              <select value={boardPriority} onChange={(event) => setBoardPriority(event.target.value as BoardPriority | "") }>
                <option value="">any</option>
                {BOARD_PRIORITIES.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="grid-two">
            <label>
              Search question/requestId
              <input value={boardSearch} onChange={(event) => setBoardSearch(event.target.value)} placeholder="search text" />
            </label>
            <label>
              pageSize
              <input type="number" min={1} max={100} value={boardPageSize} onChange={(event) => setBoardPageSize(Number(event.target.value))} />
            </label>
          </div>
          <div className="button-row">
            <button onClick={onLoadEditorialBoard} disabled={busy || !token}>Load Board</button>
            <button
              onClick={() => {
                setBoardPage(Math.max(1, boardPage - 1));
              }}
              disabled={busy || boardPage <= 1}
            >
              Prev
            </button>
            <button
              onClick={() => {
                setBoardPage(boardPage + 1);
              }}
              disabled={busy}
            >
              Next
            </button>
          </div>

          {boardResult && (
            <article className="result-card">
              <h3>Board Rows</h3>
              <p className="muted">page {boardResult.page} · size {boardResult.pageSize} · total {boardResult.total}</p>
              <p className="muted">roles: {boardResult.actorRoles.join(", ") || "none"}</p>
              {boardResult.items.length === 0 && <p className="muted">No queue items found.</p>}
              {boardResult.items.length > 0 && (
                <div className="table-wrap">
                  <table className="board-table">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Reason</th>
                        <th>Question</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {boardResult.items.map((item) => (
                        <tr key={item.queueItemId}>
                          <td>{item.status}</td>
                          <td>{item.priority}</td>
                          <td>{item.reason}</td>
                          <td>
                            <div>{item.question}</div>
                            <div className="muted tiny">{item.requestId}</div>
                            <div className="muted tiny">{item.queueItemId}</div>
                          </td>
                          <td>
                            <div className="button-column">
                              {item.allowedActions.length === 0 && <span className="muted tiny">No allowed actions</span>}
                              {item.allowedActions.map((action) => (
                                <button key={`${item.queueItemId}-${action}`} onClick={() => onQuickTransition(item, action)} disabled={busy || !token}>
                                  {action}
                                </button>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          )}
        </section>

        <section className="panel">
          <h2>Editorial Routing</h2>
          <p className="muted">Route current answer outcome into queue.</p>
          <div className="stack">
            <label>
              Reason
              <select value={queueReason} onChange={(event) => setQueueReason(event.target.value as QueueReason)}>
                <option value="LOW_CONFIDENCE">LOW_CONFIDENCE</option>
                <option value="CITATION_GAP">CITATION_GAP</option>
                <option value="POLICY_REVIEW">POLICY_REVIEW</option>
                <option value="USER_ESCALATION">USER_ESCALATION</option>
              </select>
            </label>
            <label>
              Priority
              <select value={queuePriority} onChange={(event) => setQueuePriority(event.target.value as QueuePriority)}>
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
      </div>
    </section>
  );
}