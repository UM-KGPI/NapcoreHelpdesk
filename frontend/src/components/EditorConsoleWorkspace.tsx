import React, { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import AnswerMarkdown from "./AnswerMarkdown";

import type {
  AnswerResponse,
  AskedQuestionRow,
  EditorialBoardItem,
  EditorialBoardResponse,
  IndexRepositoryResponse,
  QuestionEventDetail,
} from "../types";
const TRANSITION_ACTIONS = ["approve", "reject", "revoke", "reopen"] as const;
const BOARD_STATUSES = ["in_review", "approved", "rejected", "revoked"] as const;

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function formatAction(action: string): string {
  const label = action.replace(/_/g, " ");
  return label.charAt(0).toUpperCase() + label.slice(1);
}

type TransitionAction = (typeof TRANSITION_ACTIONS)[number];
type BoardStatus = (typeof BOARD_STATUSES)[number];
type AskedStatusFilter = "" | BoardStatus;
type EditorTab = "assist" | "editorial" | "faq" | "indexing";
type SortDir = "asc" | "desc";
type SortState = { col: string; dir: SortDir } | null;

function toggleSortState(current: SortState, col: string): SortState {
  if (!current || current.col !== col) return { col, dir: "asc" };
  if (current.dir === "asc") return { col, dir: "desc" };
  return null;
}

function SortTh({ col, sort, onSort, children }: { col: string; sort: SortState; onSort: (col: string) => void; children: React.ReactNode }) {
  const active = sort?.col === col;
  const indicator = active ? (sort.dir === "asc" ? "▲" : "▼") : "⇅";
  return (
    <th>
      <button type="button" className={`sort-btn${active ? " sort-active" : ""}`} onClick={() => onSort(col)}>
        {children} <span className="sort-indicator">{indicator}</span>
      </button>
    </th>
  );
}

const FAQ_PAGE_SIZE = 10;

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
  boardResult: EditorialBoardResponse | null;
  faqItems: EditorialBoardItem[];
  boardStatusMap: Map<string, string>;
  busy: boolean;
  token: string;
  setQuestion: (value: string) => void;
  setSelectedQuestionEventId: (value: string) => void;
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onLoadAskedQuestions: () => Promise<void>;
  onQueueEditorial: (questionEventIdOverride?: string) => Promise<void>;
  onDeleteQuestionEvent: (questionEventIds: string[]) => Promise<void>;
  onLoadEditorialBoard: () => Promise<void>;
  onLoadFaq: () => Promise<void>;
  onLoadQuestionEventDetail: (questionEventId: string) => Promise<QuestionEventDetail>;
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
  const [askedStatusFilter, setAskedStatusFilter] = useState<AskedStatusFilter>("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [faqPage, setFaqPage] = useState(1);
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const [questionsOpenId, setQuestionsOpenId] = useState<string | null>(null);
  const [reviewOpenId, setReviewOpenId] = useState<string | null>(null);
  const [detailCache, setDetailCache] = useState<Record<string, QuestionEventDetail>>({});
  const [detailLoading, setDetailLoading] = useState<Set<string>>(new Set());
  const [detailErrors, setDetailErrors] = useState<Record<string, string>>({});
  const [askedSort, setAskedSort] = useState<SortState>(null);
  const [reviewSort, setReviewSort] = useState<SortState>(null);
  const answerResultRef = useRef<HTMLElement | null>(null);
  const lastAnswerRequestIdRef = useRef<string | null>(null);
  const {
    question,
    answerResult,
    askedQuestions,
    boardResult,
    faqItems,
    boardStatusMap,
    busy,
    token,
    setQuestion,
    onAskQuestion,
    onLoadAskedQuestions,
    onQueueEditorial,
    onDeleteQuestionEvent,
    onLoadEditorialBoard,
    onLoadFaq,
    onLoadQuestionEventDetail,
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
    type GroupedRow = AskedQuestionRow & { count: number; likesCount: number; dislikesCount: number; allEventIds: string[] };
    const groups = new Map<string, GroupedRow>();
    for (const item of askedQuestions) {
      const key = item.question.trim().toLowerCase();
      const existing = groups.get(key);
      if (!existing) {
        groups.set(key, { ...item, count: 1, likesCount: item.userLikes ? 1 : 0, dislikesCount: item.userDislikes ? 1 : 0, allEventIds: [item.questionEventId] });
      } else {
        const useNew =
          (item.reviewRequired && !existing.reviewRequired) ||
          (item.reviewRequired === existing.reviewRequired && item.askedAt > existing.askedAt);
        groups.set(key, {
          ...(useNew ? item : existing),
          count: existing.count + 1,
          likesCount: existing.likesCount + (item.userLikes ? 1 : 0),
          dislikesCount: existing.dislikesCount + (item.userDislikes ? 1 : 0),
          allEventIds: [...existing.allEventIds, item.questionEventId],
        });
      }
    }
    return Array.from(groups.values());
  }, [askedQuestions]);

  useEffect(() => {
    setFaqPage(1);
    setOpenCardId(null);
  }, [faqItems]);

  const filteredAskedQuestions = useMemo(() => {
    if (!askedStatusFilter) return groupedAskedQuestions;
    return groupedAskedQuestions.filter((item) => {
      const s = boardStatusMap.get(item.requestId);
      return s === askedStatusFilter;
    });
  }, [groupedAskedQuestions, askedStatusFilter, boardStatusMap]);

  const sortedAskedQuestions = useMemo(() => {
    if (!askedSort) return filteredAskedQuestions;
    const { col, dir } = askedSort;
    return [...filteredAskedQuestions].sort((a, b) => {
      let cmp = 0;
      if (col === "askedAt") cmp = a.askedAt.localeCompare(b.askedAt);
      else if (col === "confidence") cmp = a.confidence - b.confidence;
      else if (col === "likes") cmp = (a.likesCount - a.dislikesCount) - (b.likesCount - b.dislikesCount);
      else if (col === "status") {
        const sa = boardStatusMap.get(a.requestId) ?? "";
        const sb = boardStatusMap.get(b.requestId) ?? "";
        cmp = sa.localeCompare(sb);
      }
      return dir === "asc" ? cmp : -cmp;
    });
  }, [filteredAskedQuestions, askedSort, boardStatusMap]);

  const boardItems = boardResult?.items ?? [];
  const inReviewBoardItems = boardItems.filter((item) => item.status === "in_review");

  const sortedReviewItems = useMemo(() => {
    if (!reviewSort) return inReviewBoardItems;
    const { col, dir } = reviewSort;
    return [...inReviewBoardItems].sort((a, b) => {
      const cmp = col === "status" ? a.status.localeCompare(b.status) : 0;
      return dir === "asc" ? cmp : -cmp;
    });
  }, [inReviewBoardItems, reviewSort]);

  const faqTotalPages = Math.max(1, Math.ceil(faqItems.length / FAQ_PAGE_SIZE));
  const faqPageItems = faqItems.slice((faqPage - 1) * FAQ_PAGE_SIZE, faqPage * FAQ_PAGE_SIZE);

  return (
    <section className="workspace-section editor-workspace">
      <header className="workspace-header">
<h2>Editorial Console</h2>
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
            Review Q&amp;As
          </button>
          <button type="button" className={activeTab === "faq" ? "tab-button tab-button-active" : "tab-button"} onClick={() => setActiveTab("faq")}>
            FAQs
          </button>
        </div>
        <p className="muted tab-strip-copy">
          {activeTab === "assist" && "Run a question, inspect the answer, and adjust request context only when needed."}
          {activeTab === "editorial" && "Triage answers and move queue items through workflow states."}
          {activeTab === "faq" && "Browse approved answers with full answer text and evidence links."}
          {activeTab === "indexing" && "Refresh approved repositories and monitor indexing output."}
        </p>
      </section>

      <div className="dashboard">
        {activeTab === "assist" && (
          <>
            <section className="panel step-2-ask">
              <div className="panel-title-row">
                <h2>Run Helpdesk Query</h2>
                <p className="muted">Simulate a user question and inspect the grounded response before routing anything into review.</p>
              </div>
              <form onSubmit={onAskQuestion} className="stack">
                <label>
                  Question
                  <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} required />
                </label>
                <button type="submit" disabled={busy || !token}>Run Query</button>
                {busy && (
                  <div className="chat-progress" role="status" aria-live="polite" aria-label="Generating answer">
                    <div className="chat-progress-bar" />
                    <p className="chat-progress-label muted tiny">Generating answer…</p>
                  </div>
                )}
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
              <div className="panel-title-row">
                <h2>
                  Questions Asked
                  {groupedAskedQuestions.length > 0 && (
                    <span className="heading-count">
                      {askedStatusFilter
                        ? `${filteredAskedQuestions.length} / ${groupedAskedQuestions.length}`
                        : groupedAskedQuestions.length}
                    </span>
                  )}
                </h2>
                <p className="muted">Inspect the stored questions and select one to send into the review queue.</p>
              </div>

              <div className="button-row">
                <select aria-label="Status filter" value={askedStatusFilter} onChange={(event) => setAskedStatusFilter(event.target.value as AskedStatusFilter)}>
                  <option value="">All</option>
                  {BOARD_STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <button onClick={() => void onLoadAskedQuestions()} disabled={busy || !token}>Load questions</button>
              </div>

              <div className="table-wrap">
                <table className="board-table">
                  <thead>
                    <tr>
                      <th>Question</th>
                      <SortTh col="askedAt" sort={askedSort} onSort={(c) => setAskedSort((prev) => toggleSortState(prev, c))}>Asked</SortTh>
                      <SortTh col="confidence" sort={askedSort} onSort={(c) => setAskedSort((prev) => toggleSortState(prev, c))}>Confidence</SortTh>
                      <SortTh col="likes" sort={askedSort} onSort={(c) => setAskedSort((prev) => toggleSortState(prev, c))}>Likes</SortTh>
                      <SortTh col="status" sort={askedSort} onSort={(c) => setAskedSort((prev) => toggleSortState(prev, c))}>Status</SortTh>
                      <th className="col-actions">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedAskedQuestions.length === 0 && (
                      <tr>
                        <td colSpan={6} className="muted">No stored question events found.</td>
                      </tr>
                    )}
                    {sortedAskedQuestions.map((item) => {
                      const isOpen = questionsOpenId === item.questionEventId;
                      const detail = detailCache[item.questionEventId];
                      const loading = detailLoading.has(item.questionEventId);
                      return (
                        <React.Fragment key={item.requestId}>
                          <tr>
                            <td>
                              <div>{item.question}</div>
                              {item.count > 1 && <span className="heading-count">×{item.count}</span>}
                            </td>
                            <td>{formatDate(item.askedAt)}</td>
                            <td>{item.confidence.toFixed(2)}</td>
                            <td className="likes-cell">
                              {(() => {
                                const net = item.likesCount - item.dislikesCount;
                                if (item.likesCount === 0 && item.dislikesCount === 0) return null;
                                return <span className={net > 0 ? "likes-positive" : net < 0 ? "likes-negative" : "likes-zero"}>{net > 0 ? `+${net}` : net}</span>;
                              })()}
                            </td>
                            <td>
                              {(() => {
                                const s = boardStatusMap.get(item.requestId);
                                return s ? <span className={`faq-status-pill status-${s}`}>{s}</span> : null;
                              })()}
                            </td>
                            <td>
                              <div className="button-column">
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (isOpen && detail) {
                                      setQuestionsOpenId(null);
                                    } else {
                                      setQuestionsOpenId(item.questionEventId);
                                      if (!detail && !loading) {
                                        setDetailErrors((prev) => { const n = { ...prev }; delete n[item.questionEventId]; return n; });
                                        setDetailLoading((prev) => { const s = new Set(prev); s.add(item.questionEventId); return s; });
                                        void onLoadQuestionEventDetail(item.questionEventId)
                                          .then((d) => setDetailCache((prev) => ({ ...prev, [item.questionEventId]: d })))
                                          .catch((err: unknown) => setDetailErrors((prev) => ({ ...prev, [item.questionEventId]: err instanceof Error ? err.message : String(err) })))
                                          .finally(() => setDetailLoading((prev) => { const s = new Set(prev); s.delete(item.questionEventId); return s; }));
                                      }
                                    }
                                  }}
                                  disabled={loading}
                                >
                                  {loading ? "Loading…" : isOpen && detail ? "Hide" : "Show"}
                                </button>
                                {isOpen && detail && !boardStatusMap.has(item.requestId) && (
                                  <button
                                    onClick={() => onQueueEditorial(item.questionEventId)}
                                    disabled={busy || !token}
                                  >
                                    Send for review
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                          {isOpen && (
                            <tr>
                              <td colSpan={6} className="detail-row">
                                {loading && <p className="muted tiny">Loading answer…</p>}
                                {!loading && !detail && detailErrors[item.questionEventId] && (
                                  <p className="muted tiny">Failed to load: {detailErrors[item.questionEventId]}</p>
                                )}
                                {detail && (
                                  <>
                                    <div className="faq-card-body">
                                      <AnswerMarkdown text={detail.answer} />
                                      {detail.citations.length > 0 && (
                                        <>
                                          <p className="tiny"><strong>Evidence</strong></p>
                                          <ul>
                                            {detail.citations.map((c, i) => (
                                              <li key={`${item.requestId}-c${i}`}>
                                                <strong>[E{i + 1}]</strong>{" "}
                                                <a href={c.repositoryUrl} target="_blank" rel="noreferrer">{c.label ?? c.sourcePath}</a>
                                                <span className="muted"> · {c.sourcePath}</span>
                                              </li>
                                            ))}
                                          </ul>
                                        </>
                                      )}
                                    </div>
                                    <p className="muted tiny">{item.requestId}</p>
                                    <div className="detail-row-actions">
                                      {deleteConfirmId === item.questionEventId ? (
                                        <>
                                          <span className="muted tiny">Delete this question and its answer permanently?</span>
                                          <button
                                            className="btn-danger"
                                            onClick={() => {
                                              setDeleteConfirmId(null);
                                              setQuestionsOpenId(null);
                                              void onDeleteQuestionEvent(item.allEventIds);
                                            }}
                                            disabled={busy}
                                          >
                                            Confirm delete
                                          </button>
                                          <button onClick={() => setDeleteConfirmId(null)} disabled={busy}>
                                            Cancel
                                          </button>
                                        </>
                                      ) : (
                                        <button
                                          className="btn-danger-outline"
                                          onClick={() => setDeleteConfirmId(item.questionEventId)}
                                          disabled={busy}
                                        >
                                          Delete
                                        </button>
                                      )}
                                    </div>
                                  </>
                                )}
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>

            </section>

            <section className="panel step-5-board">
              <div className="panel-title-row">
                <h2>
                  Questions in Review
                  {boardResult && inReviewBoardItems.length > 0 && (
                    <span className="heading-count">{inReviewBoardItems.length}</span>
                  )}
                </h2>
                <p className="muted">Review questions in the editorial queue and apply workflow transitions.</p>
              </div>

              <div className="button-row">
                <button onClick={onLoadEditorialBoard} disabled={busy || !token}>Load queue</button>
              </div>

              {boardResult && inReviewBoardItems.length === 0 && <p className="muted">No questions in review.</p>}
              {boardResult && inReviewBoardItems.length > 0 && (
                <div className="table-wrap">
                  <table className="board-table">
                    <thead>
                      <tr>
                        <th>Question</th>
                        <SortTh col="status" sort={reviewSort} onSort={(c) => setReviewSort((prev) => toggleSortState(prev, c))}>Status</SortTh>
                        <th className="col-actions">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedReviewItems.map((item) => {
                        const isOpen = reviewOpenId === item.queueItemId;
                        const detail = detailCache[item.questionEventId];
                        const loading = detailLoading.has(item.questionEventId);
                        return (
                          <React.Fragment key={item.queueItemId}>
                            <tr>
                              <td>
                                <div>{item.question}</div>
                              </td>
                              <td><span className={`faq-status-pill status-${item.status}`}>{item.status}</span></td>
                              <td>
                                <div className="button-column">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (isOpen && detail) {
                                        setReviewOpenId(null);
                                      } else {
                                        setReviewOpenId(item.queueItemId);
                                        if (!detail && !loading) {
                                          setDetailErrors((prev) => { const n = { ...prev }; delete n[item.questionEventId]; return n; });
                                          setDetailLoading((prev) => { const s = new Set(prev); s.add(item.questionEventId); return s; });
                                          void onLoadQuestionEventDetail(item.questionEventId)
                                            .then((d) => setDetailCache((prev) => ({ ...prev, [item.questionEventId]: d })))
                                            .catch((err: unknown) => setDetailErrors((prev) => ({ ...prev, [item.questionEventId]: err instanceof Error ? err.message : String(err) })))
                                            .finally(() => setDetailLoading((prev) => { const s = new Set(prev); s.delete(item.questionEventId); return s; }));
                                        }
                                      }
                                    }}
                                    disabled={loading}
                                  >
                                    {loading ? "Loading…" : isOpen && detail ? "Hide" : "Show"}
                                  </button>
                                  {item.allowedActions.length === 0 && <span className="muted tiny">No actions</span>}
                                  {item.allowedActions.map((action) => (
                                    <button key={`${item.queueItemId}-${action}`} onClick={() => onQuickTransition(item, action)} disabled={busy || !token}>
                                      {formatAction(action)}
                                    </button>
                                  ))}
                                </div>
                              </td>
                            </tr>
                            {isOpen && (
                              <tr>
                                <td colSpan={3} className="detail-row">
                                  {loading && <p className="muted tiny">Loading answer…</p>}
                                  {!loading && !detail && detailErrors[item.questionEventId] && (
                                    <p className="muted tiny">Failed to load: {detailErrors[item.questionEventId]}</p>
                                  )}
                                  {detail && (
                                    <>
                                      <div className="faq-card-body">
                                        <AnswerMarkdown text={detail.answer} />
                                        {detail.citations.length > 0 && (
                                          <>
                                            <p className="tiny"><strong>Evidence</strong></p>
                                            <ul>
                                              {detail.citations.map((c, i) => (
                                                <li key={`${item.queueItemId}-c${i}`}>
                                                  <strong>[E{i + 1}]</strong>{" "}
                                                  <a href={c.repositoryUrl} target="_blank" rel="noreferrer">{c.label ?? c.sourcePath}</a>
                                                  <span className="muted"> · {c.sourcePath}</span>
                                                </li>
                                              ))}
                                            </ul>
                                          </>
                                        )}
                                      </div>
                                      <p className="muted tiny">{item.requestId}</p>
                                    </>
                                  )}
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}

        {activeTab === "faq" && (
          <section className="panel step-6-faq">
            <div className="panel-title-row">
              <h2>
                FAQs
                {faqItems.length > 0 && (
                  <span className="heading-count">
                    {faqTotalPages > 1
                      ? `${faqPageItems.length} / ${faqItems.length}`
                      : faqItems.length}
                  </span>
                )}
              </h2>
              <p className="muted">Approved answers ready for reference.</p>
            </div>
            <div className="button-row">
              <button onClick={onLoadFaq} disabled={busy || !token}>Load FAQs</button>
            </div>
            {faqItems.length === 0 && <p className="muted">No approved questions found.</p>}
            {faqItems.length > 0 && (
              <>
                <div className="faq-card-list">
                  {faqPageItems.map((item) => {
                    const isOpen = openCardId === item.queueItemId;
                    const detail = detailCache[item.questionEventId];
                    const loading = detailLoading.has(item.questionEventId);
                    return (
                      <article key={item.queueItemId} className="faq-card">
                        <div className="faq-card-question">
                          <span>{item.question}</span>
                          <span className="faq-status-pill">{item.status}</span>
                        </div>
                        <div className="button-row">
                          <button
                            type="button"
                            onClick={() => {
                              if (isOpen && detail) {
                                setOpenCardId(null);
                              } else {
                                setOpenCardId(item.queueItemId);
                                if (!detail && !loading) {
                                  setDetailErrors((prev) => { const n = { ...prev }; delete n[item.questionEventId]; return n; });
                                  setDetailLoading((prev) => { const s = new Set(prev); s.add(item.questionEventId); return s; });
                                  void onLoadQuestionEventDetail(item.questionEventId)
                                    .then((d) => setDetailCache((prev) => ({ ...prev, [item.questionEventId]: d })))
                                    .catch((err: unknown) => setDetailErrors((prev) => ({ ...prev, [item.questionEventId]: err instanceof Error ? err.message : String(err) })))
                                    .finally(() => setDetailLoading((prev) => { const s = new Set(prev); s.delete(item.questionEventId); return s; }));
                                }
                              }
                            }}
                            disabled={loading}
                          >
                            {loading ? "Loading…" : isOpen && detail ? "Hide" : "Show"}
                          </button>
                          {item.allowedActions.map((action) => (
                            <button key={`${item.queueItemId}-${action}`} onClick={() => onQuickTransition(item, action as TransitionAction)} disabled={busy || !token}>
                              {formatAction(action)}
                            </button>
                          ))}
                        </div>
                        {isOpen && loading && <p className="muted tiny">Loading answer…</p>}
                        {isOpen && !loading && !detail && detailErrors[item.questionEventId] && (
                          <p className="muted tiny">Failed to load: {detailErrors[item.questionEventId]}</p>
                        )}
                        {isOpen && detail && (
                          <div className="faq-card-body">
                            <AnswerMarkdown text={detail.answer} />
                            {detail.citations.length > 0 && (
                              <>
                                <p className="tiny"><strong>Evidence</strong></p>
                                <ul>
                                  {detail.citations.map((c, i) => (
                                    <li key={`${item.queueItemId}-c${i}`}>
                                      <strong>[E{i + 1}]</strong>{" "}
                                      <a href={c.repositoryUrl} target="_blank" rel="noreferrer">{c.label ?? c.sourcePath}</a>
                                      <span className="muted"> · {c.sourcePath}</span>
                                    </li>
                                  ))}
                                </ul>
                              </>
                            )}
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
                {faqTotalPages > 1 && (
                  <div className="button-row">
                    <button onClick={() => setFaqPage((p) => Math.max(1, p - 1))} disabled={faqPage === 1}>Prev</button>
                    <span className="muted tiny">{faqPage} / {faqTotalPages}</span>
                    <button onClick={() => setFaqPage((p) => Math.min(faqTotalPages, p + 1))} disabled={faqPage === faqTotalPages}>Next</button>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {activeTab === "indexing" && (
          <section className="panel step-1-index">
            <div className="panel-title-row">
              <h2>Refresh Source Index</h2>
              <p className="muted">Trigger ingestion on a locally-cloned approved repository.</p>
            </div>
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
