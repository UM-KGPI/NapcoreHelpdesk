/**
 * Dedicated page for displaying a stored question with its answer.
 * Used when following deep links to specific Q&A exchanges.
 * Shows only the question and answer — no input field, buttons, or chat controls.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ChatTurn } from "./UserChatWorkspace";
import ReadOnlyQuestionDisplay from "./ReadOnlyQuestionDisplay";

interface QuestionDetailPageProps {
  token: string;
  questionId: string;
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

export default function QuestionDetailPage({
  token,
  questionId,
  onSetAnswerFeedback,
}: QuestionDetailPageProps) {
  const navigate = useNavigate();
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!questionId || !token) {
      setLoading(false);
      return;
    }

    const baseUrl = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
      ? "http://localhost:8000/api/v1"
      : `${window.location.origin}${import.meta.env.BASE_URL}api/v1`;

    fetch(`${baseUrl}/questions/events/${questionId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then((detail) => {
        const questionTurn: ChatTurn = {
          id: `${detail.requestId}-q`,
          role: "user",
          text: detail.question,
          createdAt: detail.createdAt,
        };

        const answerTurn: ChatTurn = {
          id: `${detail.requestId}-a`,
          role: "assistant",
          text: detail.answer,
          createdAt: detail.createdAt,
          answer: {
            answerId: detail.questionEventId,
            mode: detail.mode || "rag",
            confidence: detail.confidence,
            answer: detail.answer,
            citations: (detail.citations || []).map((c: any) => ({
              repositoryUrl: c.repositoryUrl,
              commitSha: "",
              sourcePath: c.sourcePath,
              chunkId: c.chunkId,
              label: c.label,
            })),
            abstained: false,
            abstentionReason: null,
            reviewRequired: false,
            trace: (detail.trace && Object.keys(detail.trace).length > 2) ? detail.trace : {
              requestId: detail.requestId,
              questionEventId: detail.questionEventId,
              matchedFaqEntryId: null,
              retrievalEventIds: [],
              userLikes: false,
              userDislikes: false,
            },
          },
          requestId: detail.requestId,
        };

        setChatTurns([questionTurn, answerTurn]);
        setError(null);
      })
      .catch((err) => {
        console.error(`Failed to load question ${questionId}:`, err);
        setError(`Failed to load question: ${err.message}`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [questionId, token]);

  if (loading) {
    return (
      <div className="panel" style={{ marginTop: "1.1rem" }}>
        <p>Loading question...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel" style={{ marginTop: "1.1rem" }}>
        <p className="error-text">{error}</p>
      </div>
    );
  }

  if (!chatTurns.length) {
    return (
      <div className="panel" style={{ marginTop: "1.1rem" }}>
        <p>Question not found.</p>
      </div>
    );
  }

  return (
    <>
      <div style={{ padding: "1rem", textAlign: "center", borderBottom: "1px solid #e0e0e0" }}>
        <button
          type="button"
          onClick={() => navigate("/user")}
          style={{
            padding: "0.5rem 1rem",
            backgroundColor: "#5a9080",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "0.95rem",
          }}
        >
          Have a question?
        </button>
      </div>
      <ReadOnlyQuestionDisplay chatTurns={chatTurns} onSetAnswerFeedback={onSetAnswerFeedback} />
    </>
  );
}
