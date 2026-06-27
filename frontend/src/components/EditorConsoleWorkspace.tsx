import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import AnswerMarkdown from "./AnswerMarkdown";

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
} from "../types";
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
type EditorTab = "assist" | "editorial" | "indexing";

type IndexRepoPresetOption = {
  id: string;
  label: string;
  repoUrl: string;
  repoPath: string;
  profile: string;
};

interface EditorConsoleWorkspaceProps {
  question: string;
  answerResult: AnswerResponse | null;
  askedQuestions: AskedQuestionRow[];
  selectedQuestionEventId: string;
  editorialResult: EditorialQueueResponse | null;
  transitionResult: EditorialQueueTransitionResponse | null;
  boardResult: EditorialBoardResponse | null;
  boardMetrics: EditorialBoardMetricsResponse | null;
  semanticClustersResult: EditorialSemanticClustersResponse | null;
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
  semanticWindowDays: number;
  semanticMinClusterSize: number;
  semanticSimilarityThreshold: number;
  semanticMaxEvents: number;
  busy: boolean;
  token: string;
  setQuestion: (value: string) => void;
  setQueueReason: (value: QueueReason) => void;
  setQueuePriority: (value: QueuePriority) => void;
  setSelectedQuestionEventId: (value: string) => void;
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
  setSemanticWindowDays: (value: number) => void;
  setSemanticMinClusterSize: (value: number) => void;
  setSemanticSimilarityThreshold: (value: number) => void;
  setSemanticMaxEvents: (value: number) => void;
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onLoadAskedQuestions: () => Promise<void>;
  onQueueEditorial: (questionEventIdOverride?: string) => Promise<void>;
  onTransitionEditorial: () => Promise<void>;
  onLoadEditorialBoard: () => Promise<void>;
  onQuickTransition: (item: EditorialBoardItem, action: TransitionAction) => Promise<void>;
  onLoadBoardMetrics: () => Promise<void>;
  onLoadSemanticClusters: () => Promise<void>;
  indexPresetId: string;
  indexRepoPresets: IndexRepoPresetOption[];
  indexRepoUrl: string;
  indexRepoPath: string;
  indexProfile: string;
  indexIncremental: boolean;
  indexPrune: boolean;
  indexIncludeIssues: boolean;
  indexAutoAllowRepository: boolean;
  indexResult: IndexRepositoryResponse | null;
  indexBusy: boolean;
  onSelectIndexPreset: (value: string) => void;
  setIndexRepoUrl: (value: string) => void;
  setIndexRepoPath: (value: string) => void;
  setIndexProfile: (value: string) => void;
  setIndexIncremental: (value: boolean) => void;
  setIndexPrune: (value: boolean) => void;
  setIndexIncludeIssues: (value: boolean) => void;
  setIndexAutoAllowRepository: (value: boolean) => void;
  onIndexRepository: () => Promise<void>;
}

export default function EditorConsoleWorkspace(props: EditorConsoleWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<EditorTab>("indexing");
  const [askedSearch, setAskedSearch] = useState("");
  const [askedOnlyReviewRequired, setAskedOnlyReviewRequired] = useState(false);
  const [askedMode, setAskedMode] = useState<"" | "faq" | "rag" | "abstain">("");
  const [askedShowAdvancedIds, setAskedShowAdvancedIds] = useState(false);
  const answerResultRef = useRef<HTMLElement | null>(null);
  const lastAnswerRequestIdRef = useRef<string | null>(null);
  const {
    question,
    answerResult,
    askedQuestions,
    selectedQuestionEventId,
    editorialResult,
    transitionResult,
    boardResult,
    boardMetrics,
    semanticClustersResult,
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
    semanticWindowDays,
    semanticMinClusterSize,
    semanticSimilarityThreshold,
    semanticMaxEvents,
    busy,
    token,
    setQuestion,
    setQueueReason,
    setQueuePriority,
    setSelectedQuestionEventId,
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
    setSemanticWindowDays,
    setSemanticMinClusterSize,
    setSemanticSimilarityThreshold,
    setSemanticMaxEvents,
    onAskQuestion,
    onLoadAskedQuestions,
    onQueueEditorial,
    onTransitionEditorial,
    onLoadEditorialBoard,
    onQuickTransition,
    onLoadBoardMetrics,
    onLoadSemanticClusters,
    indexPresetId,
    indexRepoPresets,
    indexRepoUrl,
    indexRepoPath,
    indexProfile,
    indexIncremental,
    indexPrune,
    indexIncludeIssues,
    indexAutoAllowRepository,
    indexResult,
    indexBusy,
    onSelectIndexPreset,
    setIndexRepoUrl,
    setIndexRepoPath,
    setIndexProfile,
    setIndexIncremental,
    setIndexPrune,
    setIndexIncludeIssues,
    setIndexAutoAllowRepository,
    onIndexRepository,
  } = props;

  useEffect(() => {
    const requestId = answerResult?.trace.requestId;
    if (!requestId || requestId === lastAnswerRequestIdRef.current) {
      return;
    }

    lastAnswerRequestIdRef.current = requestId;
    answerResultRef.current?.scrollIntoView({ block: "start", behavior: "auto" });
  }, [answerResult?.trace.requestId]);

  const filteredAskedQuestions = useMemo(() => {
    const needle = askedSearch.trim().toLowerCase();
    return askedQuestions.filter((item) => {
      if (askedOnlyReviewRequired && !item.reviewRequired) {
        return false;
      }
      if (askedMode && item.mode !== askedMode) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return (
        item.question.toLowerCase().includes(needle) ||
        item.requestId.toLowerCase().includes(needle) ||
        item.questionEventId.toLowerCase().includes(needle)
      );
    });
  }, [askedMode, askedOnlyReviewRequired, askedQuestions, askedSearch]);

  const askedModeCounts = useMemo(() => {
    return askedQuestions.reduce(
      (acc, item) => {
        acc[item.mode] += 1;
        return acc;
      },
      { faq: 0, rag: 0, abstain: 0 }
    );
  }, [askedQuestions]);

  const canQueueSelectedQuestion = Boolean(selectedQuestionEventId);
  const boardItems = boardResult?.items ?? [];
  const inReviewBoardItems = boardItems.filter((item) => item.status !== "published");
  const faqBoardItems = boardItems.filter((item) => item.status === "published");

  return (
    <section className="workspace-section editor-workspace">
      <header className="workspace-header">
        <p className="kicker">Editor Workspace</p>
        <h2>Editor Console</h2>
        <p className="muted">Operational controls for harvesting and indexing trusted knowledge sources, Q&amp;A validation, editorial review.</p>
      </header>

      <section className="panel tab-strip-panel" aria-label="Editor sections">
        <div className="tab-strip">
          <button type="button" className={activeTab === "indexing" ? "tab-button tab-button-active" : "tab-button"} onClick={() => setActiveTab("indexing")}>
            Harvest &amp; Index
          </button>
          <button type="button" className={activeTab === "assist" ? "tab-button tab-button-active" : "tab-button"} onClick={() => setActiveTab("assist")}>
            Dry run Q&amp;A
          </button>
          <button type="button" className={activeTab === "editorial" ? "tab-button tab-button-active" : "tab-button"} onClick={() => setActiveTab("editorial")}>
            Editor Review
          </button>
        </div>
        <p className="muted tab-strip-copy">
          {activeTab === "assist" && "Run a question, inspect the answer, and adjust request context only when needed."}
          {activeTab === "editorial" && "Triage answers, move queue items through workflow states, and review promotion signals."}
          {activeTab === "indexing" && "Refresh approved repositories and monitor indexing output."}
        </p>
      </section>

      <div className="dashboard">
        {activeTab === "assist" && (
          <>
            <section className="panel step-2-ask">
              <h2>Run Helpdesk Query</h2>
              <p className="muted">Use this to simulate a user question and inspect the grounded response before routing anything into review.</p>
              <form onSubmit={onAskQuestion} className="stack">
                <label>
                  Question
                  <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} required />
                </label>
                <button type="submit" disabled={busy || !token}>Run Query</button>
              </form>

              {answerResult && (
                <article className="result-card" ref={answerResultRef}>
                  <h3>Answer Result</h3>
                  <div className="answer-stream-question">
                    <p className="muted tiny">Question</p>
                    <p>{question}</p>
                  </div>
                  <p className="mode-pill">mode: {answerResult.mode}</p>
                  <AnswerMarkdown text={answerResult.answer} />
                  <p>
                    confidence: <strong>{answerResult.confidence.toFixed(2)}</strong>
                  </p>
                  <p>
                    reviewRequired: <strong>{String(answerResult.reviewRequired)}</strong>
                  </p>

                  <h4>Evidence List</h4>
                  {answerResult.citations.length === 0 && <p className="muted">No citations returned.</p>}
                  {answerResult.citations.length > 0 && (
                    <ul>
                      {answerResult.citations.map((citation, index) => (
                        <li key={`${citation.chunkId}-${citation.sourcePath}`}>
                          <strong>{`[E${index + 1}]`}</strong>{" "}
                          <a href={citation.repositoryUrl} target="_blank" rel="noreferrer">{citation.label ?? citation.sourcePath}</a>
                          <span className="muted"> · {citation.sourcePath}</span>
                        </li>
                      ))}
                    </ul>
                  )}

                  <h4>Trace</h4>
                  <pre>{JSON.stringify(answerResult.trace, null, 2)}</pre>
                </article>
              )}
            </section>

          </>
        )}

        {activeTab === "editorial" && (
          <>
            <section className="panel step-3-clustering">
              <h2>Semantic Clusters</h2>
              <p className="muted">Group related QuestionEvent rows by semantic similarity, then use keyword aggregation labels and validation signals for triage.</p>

              <div className="grid-three">
                <label>
                  windowDays
                  <input type="number" min={1} value={semanticWindowDays} onChange={(event) => setSemanticWindowDays(Number(event.target.value))} />
                </label>
                <label>
                  minClusterSize
                  <input type="number" min={2} value={semanticMinClusterSize} onChange={(event) => setSemanticMinClusterSize(Number(event.target.value))} />
                </label>
                <label>
                  similarityThreshold
                  <input type="number" min={0} max={1} step={0.01} value={semanticSimilarityThreshold} onChange={(event) => setSemanticSimilarityThreshold(Number(event.target.value))} />
                </label>
              </div>
              <div className="grid-two">
                <label>
                  maxEvents
                  <input type="number" min={1} max={2000} value={semanticMaxEvents} onChange={(event) => setSemanticMaxEvents(Number(event.target.value))} />
                </label>
                <label>
                  Semantic Batch
                  <button onClick={onLoadSemanticClusters} disabled={busy || !token}>Run Semantic Clustering</button>
                </label>
              </div>

              {semanticClustersResult && (
                <article className="result-card">
                  <h3>Cluster Results</h3>
                  <p className="muted">generated {semanticClustersResult.generatedAt}</p>
                  <p className="muted tiny">totalEvents {semanticClustersResult.totalEvents} · clusteredEvents {semanticClustersResult.clusteredEvents} · singletonEvents {semanticClustersResult.singletonEvents}</p>
                  {semanticClustersResult.clusters.length === 0 && <p className="muted">No clusters met the minimum cluster size for current filters.</p>}
                  {semanticClustersResult.clusters.length > 0 && (
                    <div className="table-wrap">
                      <table className="board-table">
                        <thead>
                          <tr>
                            <th>Label</th>
                            <th>Signal</th>
                            <th>Members</th>
                            <th>Keywords</th>
                            <th>Top Bigrams</th>
                          </tr>
                        </thead>
                        <tbody>
                          {semanticClustersResult.clusters.map((cluster) => (
                            <tr key={cluster.clusterId}>
                              <td>
                                <div>{cluster.labelHint}</div>
                                <div className="muted tiny">{cluster.clusterId}</div>
                              </td>
                              <td>
                                <div>{cluster.validationSignal}</div>
                                <div className="muted tiny">sim {cluster.averageSimilarity.toFixed(2)} · cohesion {cluster.keywordAggregation.lexicalCohesion.toFixed(2)}</div>
                              </td>
                              <td>
                                <div>{cluster.memberCount}</div>
                                <div className="muted tiny">{cluster.questionEventIds.slice(0, 2).join(", ")}{cluster.questionEventIds.length > 2 ? " ..." : ""}</div>
                              </td>
                              <td>{cluster.keywordAggregation.topKeywords.slice(0, 3).map((item) => item.token).join(", ") || "none"}</td>
                              <td>{cluster.keywordAggregation.topBigrams.slice(0, 2).map((item) => item.ngram).join(", ") || "none"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </article>
              )}
            </section>

            <section className="panel step-4-transition">
              <h2>Questions for Review</h2>
              <p className="muted">Inspect the stored questions, filter the list, and select one to send into the review queue.</p>

              <div className="grid-three">
                <label>
                  Search
                  <input
                    value={askedSearch}
                    onChange={(event) => setAskedSearch(event.target.value)}
                    placeholder="question, requestId, questionEventId"
                  />
                </label>
                <label>
                  Mode
                  <select value={askedMode} onChange={(event) => setAskedMode(event.target.value as "" | "faq" | "rag" | "abstain") }>
                    <option value="">any</option>
                    <option value="faq">faq</option>
                    <option value="rag">rag</option>
                    <option value="abstain">abstain</option>
                  </select>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={askedOnlyReviewRequired}
                    onChange={(event) => setAskedOnlyReviewRequired(event.target.checked)}
                  />
                  Only reviewRequired
                </label>
              </div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={askedShowAdvancedIds}
                  onChange={(event) => setAskedShowAdvancedIds(event.target.checked)}
                />
                Advanced: show questionEventId column
              </label>

              <div className="button-row">
                <button
                  onClick={() => {
                    setAskedSearch("");
                    setAskedOnlyReviewRequired(false);
                    setAskedMode("");
                    void onLoadAskedQuestions();
                  }}
                  disabled={busy || !token}
                >
                  Load questions
                </button>
              </div>
              <p className="muted tiny">Loaded mode counts: rag {askedModeCounts.rag} · faq {askedModeCounts.faq} · abstain {askedModeCounts.abstain}</p>

              <h3>Questions</h3>
              <p className="muted tiny">Select one row, then click Send Selected for Review.</p>
              <div className="table-wrap">
                <table className="board-table">
                  <thead>
                    <tr>
                      <th>Select</th>
                      <th>Question</th>
                      <th>Mode</th>
                      <th>Confidence</th>
                      <th>reviewRequired</th>
                      <th>Asked</th>
                      <th>requestId</th>
                      {askedShowAdvancedIds && <th>questionEventId</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAskedQuestions.length === 0 && (
                      <tr>
                        <td colSpan={askedShowAdvancedIds ? 8 : 7} className="muted">No stored question events found for current filters.</td>
                      </tr>
                    )}
                    {filteredAskedQuestions.map((item) => (
                      <tr key={item.requestId}>
                        <td>
                          <input
                            type="radio"
                            name="selectedQuestionForReview"
                            checked={selectedQuestionEventId === item.questionEventId}
                            onChange={() => setSelectedQuestionEventId(item.questionEventId)}
                            aria-label={`Select question ${item.questionEventId}`}
                          />
                        </td>
                        <td>{item.question}</td>
                        <td>{item.mode}</td>
                        <td>{item.confidence.toFixed(2)}</td>
                        <td>{String(item.reviewRequired)}</td>
                        <td>{item.askedAt}</td>
                        <td>{item.requestId}</td>
                        {askedShowAdvancedIds && <td>{item.questionEventId}</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

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
                <button onClick={() => onQueueEditorial(selectedQuestionEventId)} disabled={busy || !token || !canQueueSelectedQuestion}>Send Selected for Review</button>
              </div>

              {editorialResult && (
                <article className="result-card">
                  <h3>Queue Result</h3>
                  <p>queued: <strong>{String(editorialResult.queued)}</strong></p>
                  <p>queueItemId: <code>{editorialResult.queueItemId}</code></p>
                  <p>status: <strong>{editorialResult.status}</strong></p>
                </article>
              )}
            </section>

            <section className="panel step-5-board">
              <h2>Review Queue</h2>
              <p className="muted">Apply workflow transitions to questions already routed into editorial review.</p>
              <div className="stack">
                <label>
                  Queue Item ID
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
                  Apply Status Update
                </button>
              </div>

              {transitionResult && (
                <article className="result-card">
                  <h3>Status Update Result</h3>
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
              <h3>Queue Metrics</h3>
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
                  Metrics
                  <button onClick={onLoadBoardMetrics} disabled={busy || !token}>Load Queue Metrics</button>
                </label>
              </div>

              {boardMetrics && (
                <article className="result-card">
                  <h3>Queue Metrics</h3>
                  <p className="muted">generated {boardMetrics.generatedAt}</p>
                  <div className="kpi-grid">
                    <div className="kpi-tile"><span>Total</span><strong>{boardMetrics.totalItems}</strong></div>
                    <div className="kpi-tile"><span>Unresolved</span><strong>{boardMetrics.unresolvedItems}</strong></div>
                    <div className="kpi-tile"><span>Overdue</span><strong>{boardMetrics.overdueItems}</strong></div>
                    <div className="kpi-tile"><span>Likes 24h</span><strong>{boardMetrics.feedbackToday.likes}</strong></div>
                    <div className="kpi-tile"><span>Dislikes 24h</span><strong>{boardMetrics.feedbackToday.dislikes}</strong></div>
                    <div className="kpi-tile"><span>Success 24h</span><strong>{boardMetrics.feedbackToday.answerSuccess}</strong></div>
                    <div className="kpi-tile"><span>Citation Clicks 24h</span><strong>{boardMetrics.feedbackToday.citationClicks}</strong></div>
                    <div className="kpi-tile"><span>{`Likes ${boardMetrics.windowDays}d`}</span><strong>{boardMetrics.feedbackWindow.likes}</strong></div>
                    <div className="kpi-tile"><span>{`Dislikes ${boardMetrics.windowDays}d`}</span><strong>{boardMetrics.feedbackWindow.dislikes}</strong></div>
                    <div className="kpi-tile"><span>{`Success ${boardMetrics.windowDays}d`}</span><strong>{boardMetrics.feedbackWindow.answerSuccess}</strong></div>
                    <div className="kpi-tile"><span>{`Citation Clicks ${boardMetrics.windowDays}d`}</span><strong>{boardMetrics.feedbackWindow.citationClicks}</strong></div>
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
                <button onClick={onLoadEditorialBoard} disabled={busy || !token}>Load Queue</button>
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
                  <h3>Questions In Review</h3>
                  <p className="muted">page {boardResult.page} · size {boardResult.pageSize} · total {boardResult.total}</p>
                  <p className="muted">roles: {(boardResult.actorRoles ?? []).join(", ") || "none"}</p>
                  {inReviewBoardItems.length === 0 && <p className="muted">No in-review items found for current filters.</p>}
                  {inReviewBoardItems.length > 0 && (
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
                          {inReviewBoardItems.map((item) => (
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

            <section className="panel step-6-promotion">
              <h2>FAQ</h2>
              <p className="muted">Final list of approved questions.</p>

              {!boardResult && <p className="muted">Load Queue first to populate promoted FAQ rows.</p>}
              {boardResult && faqBoardItems.length === 0 && <p className="muted">No published FAQ questions found for current filters.</p>}
              {boardResult && faqBoardItems.length > 0 && (
                <div className="table-wrap">
                  <table className="board-table">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Reason</th>
                        <th>Priority</th>
                        <th>Question</th>
                        <th>Updated</th>
                      </tr>
                    </thead>
                    <tbody>
                      {faqBoardItems.map((item) => (
                        <tr key={item.queueItemId}>
                          <td>{item.status}</td>
                          <td>{item.reason}</td>
                          <td>{item.priority}</td>
                          <td>
                            <div>{item.question}</div>
                            <div className="muted tiny">{item.requestId}</div>
                            <div className="muted tiny">{item.queueItemId}</div>
                          </td>
                          <td>{item.updatedAt}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

            </section>
          </>
        )}

        {activeTab === "indexing" && (
          <section className="panel step-1-index">
            <h2>Refresh Source Index</h2>
            <p className="muted">Trigger ingestion on a locally-cloned approved repository.</p>
            <p className="muted">Incremental mode uses per-file content hashing, so unchanged files are skipped even when repository HEAD changes.</p>
            <div className="stack">
              <label>
                Repository Preset
                <select value={indexPresetId} onChange={(e) => onSelectIndexPreset(e.target.value)}>
                  {indexRepoPresets.map((preset) => (
                    <option key={preset.id} value={preset.id}>
                      {preset.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Repository URL
                <input
                  type="text"
                  value={indexRepoUrl}
                  onChange={(e) => setIndexRepoUrl(e.target.value)}
                  placeholder="https://github.com/TransmodelEcosystem/NeTEx"
                />
              </label>
              <label>
                Local Repository Path
                <input
                  type="text"
                  value={indexRepoPath}
                  onChange={(e) => setIndexRepoPath(e.target.value)}
                  placeholder="/data/repos/NeTEx"
                />
              </label>
              <label>
                Profile
                <input
                  type="text"
                  value={indexProfile}
                  onChange={(e) => setIndexProfile(e.target.value)}
                  placeholder="netex"
                />
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={indexIncremental}
                  onChange={(e) => setIndexIncremental(e.target.checked)}
                />
                Incremental (skip unchanged files)
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={indexPrune}
                  onChange={(e) => setIndexPrune(e.target.checked)}
                />
                Prune removed files (delete stale chunks)
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={indexIncludeIssues}
                  onChange={(e) => setIndexIncludeIssues(e.target.checked)}
                />
                Include GitHub issues and comments
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={indexAutoAllowRepository}
                  onChange={(e) => setIndexAutoAllowRepository(e.target.checked)}
                />
                Auto-add repository to allow-list
              </label>
            </div>
            <button onClick={onIndexRepository} disabled={busy || !token || !indexRepoUrl || !indexRepoPath}>
              Run Index Refresh
            </button>

            {indexBusy && (
              <div className="index-progress" aria-live="polite" aria-busy="true">
                <div className="index-progress-bar" role="progressbar" aria-label="Indexing repository" aria-valuemin={0} aria-valuemax={100}>
                  <span className="index-progress-fill" />
                </div>
                <p className="muted">Working: harvesting repository content, fetching issues, chunking text, and writing the retrieval index.</p>
              </div>
            )}

            {indexResult && (
              <article className="result-card">
                <h3>Index Result</h3>
                <dl className="kv-list">
                  <dt>Repository</dt><dd>{indexResult.repositoryUrl}</dd>
                  <dt>Profile</dt><dd>{indexResult.profile}</dd>
                  <dt>Mode</dt><dd>{indexResult.incremental ? "incremental" : "full"}</dd>
                  <dt>Auto-allowed</dt><dd>{indexResult.autoAllowedRepository ? "yes" : "no"}</dd>
                  <dt>Scanned</dt><dd>{indexResult.scannedFiles} files</dd>
                  <dt>Skipped</dt><dd>{indexResult.skippedFiles} files</dd>
                  <dt>Created chunks</dt><dd>{indexResult.createdChunks}</dd>
                  <dt>Updated chunks</dt><dd>{indexResult.updatedChunks}</dd>
                  <dt>Deleted chunks</dt><dd>{indexResult.deletedChunks}</dd>
                </dl>
              </article>
            )}
          </section>
        )}

      </div>
    </section>
  );
}
