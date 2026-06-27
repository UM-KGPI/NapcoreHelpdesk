import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import AnswerMarkdown from "./AnswerMarkdown";

import type {
  AnswerResponse,
  AskedQuestionRow,
  EditorialBoardItem,
  EditorialBoardResponse,
  EditorialQueueResponse,
  EditorialQueueTransitionResponse,
  IndexRepositoryResponse,
} from "../types";
const TRANSITION_ACTIONS = ["submit_for_review", "request_changes", "approve", "reject", "publish", "reopen"] as const;
const BOARD_STATUSES = ["draft", "review", "approved", "rejected", "published"] as const;

type TransitionAction = (typeof TRANSITION_ACTIONS)[number];
type BoardStatus = (typeof BOARD_STATUSES)[number];
type QueueReason = "LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION";
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
  queueReason: QueueReason;
  boardStatus: BoardStatus | "";
  busy: boolean;
  token: string;
  setQuestion: (value: string) => void;
  setQueueReason: (value: QueueReason) => void;
  setSelectedQuestionEventId: (value: string) => void;
  setBoardStatus: (value: BoardStatus | "") => void;
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onLoadAskedQuestions: () => Promise<void>;
  onQueueEditorial: (questionEventIdOverride?: string) => Promise<void>;
  onLoadEditorialBoard: () => Promise<void>;
  onQuickTransition: (item: EditorialBoardItem, action: TransitionAction) => Promise<void>;
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
  const [askedOnlyReviewRequired, setAskedOnlyReviewRequired] = useState(false);
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
    queueReason,
    boardStatus,
    busy,
    token,
    setQuestion,
    setQueueReason,
    setSelectedQuestionEventId,
    setBoardStatus,
    onAskQuestion,
    onLoadAskedQuestions,
    onQueueEditorial,
    onLoadEditorialBoard,
    onQuickTransition,
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

  const groupedAskedQuestions = useMemo(() => {
    type GroupedRow = AskedQuestionRow & { count: number };
    const groups = new Map<string, GroupedRow>();
    for (const item of askedQuestions) {
      if (askedOnlyReviewRequired && !item.reviewRequired) {
        continue;
      }
      const key = item.question.trim().toLowerCase();
      const existing = groups.get(key);
      if (!existing) {
        groups.set(key, { ...item, count: 1 });
      } else {
        // Representative: prefer reviewRequired=true; among ties prefer most recent
        const useNew =
          (item.reviewRequired && !existing.reviewRequired) ||
          (item.reviewRequired === existing.reviewRequired && item.askedAt > existing.askedAt);
        groups.set(key, { ...(useNew ? item : existing), count: existing.count + 1 });
      }
    }
    return Array.from(groups.values());
  }, [askedOnlyReviewRequired, askedQuestions]);

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
  const inReviewBoardItems = boardItems.filter((item) => item.status === "draft" || item.status === "review" || item.status === "rejected");
  const faqBoardItems = boardItems.filter((item) => item.status === "approved" || item.status === "published");

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
            <section className="panel step-4-transition">
              <h2>Questions for Review</h2>
              <p className="muted">Inspect the stored questions and select one to send into the review queue.</p>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={askedOnlyReviewRequired}
                  onChange={(event) => setAskedOnlyReviewRequired(event.target.checked)}
                />
                Only reviewRequired
              </label>

              <div className="button-row">
                <button
                  onClick={() => {
                    void onLoadAskedQuestions();
                  }}
                  disabled={busy || !token}
                >
                  Load questions
                </button>
              </div>
              <p className="muted tiny">Loaded mode counts: rag {askedModeCounts.rag} · faq {askedModeCounts.faq} · abstain {askedModeCounts.abstain}</p>

              <h3>Questions</h3>
              <p className="muted tiny">Identical questions are grouped — count shows how many times each was asked. Select one row, then click Send Selected for Review.</p>
              <div className="table-wrap">
                <table className="board-table">
                  <thead>
                    <tr>
                      <th>Select</th>
                      <th>Question</th>
                      <th>Asked</th>
                      <th>Mode</th>
                      <th>Confidence</th>
                      <th>reviewRequired</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groupedAskedQuestions.length === 0 && (
                      <tr>
                        <td colSpan={6} className="muted">No stored question events found for current filters.</td>
                      </tr>
                    )}
                    {groupedAskedQuestions.map((item) => (
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
                        <td>
                          <div>{item.question}</div>
                          {item.count > 1 && <div className="muted tiny">×{item.count} asked</div>}
                        </td>
                        <td>{item.askedAt}</td>
                        <td>{item.mode}</td>
                        <td>{item.confidence.toFixed(2)}</td>
                        <td>{String(item.reviewRequired)}</td>
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
              <p className="muted">Review questions in the editorial queue and apply workflow transitions.</p>

              <div className="button-row">
                <select aria-label="Status filter" value={boardStatus} onChange={(event) => setBoardStatus(event.target.value as BoardStatus | "")}>
                  <option value="">any status</option>
                  {BOARD_STATUSES.map((value) => (
                    <option key={value} value={value}>{value}</option>
                  ))}
                </select>
                <button onClick={onLoadEditorialBoard} disabled={busy || !token}>Load Queue</button>
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

              {boardResult && (
                <article className="result-card">
                  <h3>Questions In Review</h3>
                  <p className="muted">total {boardResult.total}</p>
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
              <p className="muted">Approved and published questions.</p>

              {!boardResult && <p className="muted">Load Queue first to populate FAQ rows.</p>}
              {boardResult && faqBoardItems.length === 0 && <p className="muted">No approved or published questions found for current filters.</p>}
              {boardResult && faqBoardItems.length > 0 && (
                <div className="table-wrap">
                  <table className="board-table">
                    <thead>
                      <tr>
                        <th>Status</th>
                        <th>Reason</th>
                        <th>Question</th>
                        <th>Updated</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {faqBoardItems.map((item) => (
                        <tr key={item.queueItemId}>
                          <td>{item.status}</td>
                          <td>{item.reason}</td>
                          <td>
                            <div>{item.question}</div>
                            <div className="muted tiny">{item.requestId}</div>
                            <div className="muted tiny">{item.queueItemId}</div>
                          </td>
                          <td>{item.updatedAt}</td>
                          <td>
                            <div className="button-column">
                              {item.allowedActions.length === 0 && <span className="muted tiny">—</span>}
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
