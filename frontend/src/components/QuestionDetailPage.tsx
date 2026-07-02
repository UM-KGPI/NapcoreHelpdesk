/**
 * Dedicated page for displaying a stored question with its answer.
 * Used when following deep links to specific Q&A exchanges.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-02
 */

import { useEffect, useState } from "react";
import type { ChatTurn } from "./UserChatWorkspace";
import UserChatWorkspace from "./UserChatWorkspace";

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
      <div className="workspace-section">
        <div className="panel">
          <p>Loading question...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workspace-section">
        <div className="panel">
          <p className="error-text">{error}</p>
        </div>
      </div>
    );
  }

  if (!chatTurns.length) {
    return (
      <div className="workspace-section">
        <div className="panel">
          <p>Question not found.</p>
        </div>
      </div>
    );
  }

  return (
    <UserChatWorkspace
      chatTurns={chatTurns}
      chatPrompt=""
      setChatPrompt={() => {}}
      onSendChat={() => Promise.resolve()}
      onResetChatSession={() => {}}
      onSetAnswerFeedback={onSetAnswerFeedback}
      token={token}
      busy={false}
    />
  );
}
