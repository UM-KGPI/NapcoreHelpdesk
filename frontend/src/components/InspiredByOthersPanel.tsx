/**
 * Collapsible panel showing top 3 most-liked questions to inspire user queries.
 *
 * Displays trending questions with answer snippets. Clicking a question loads
 * the full Q&A via deep link (?questionId=).
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-04
 */

import { useEffect, useState } from "react";
import type { TrendingQuestion } from "../types";

interface InspiredByOthersPanelProps {
  token: string;
  apiBaseUrl: string;
  onLoadQuestion: (questionId: string) => void;
}

export default function InspiredByOthersPanel(props: InspiredByOthersPanelProps) {
  const { token, apiBaseUrl, onLoadQuestion } = props;
  const [questions, setQuestions] = useState<TrendingQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const fetchTrendingQuestions = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${apiBaseUrl}/questions/trending?limit=3`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch trending questions: ${response.status}`);
        }

        const data = await response.json() as { items: TrendingQuestion[] };
        setQuestions(data.items);
      } catch (err) {
        console.error("Error fetching trending questions:", err);
        setError(err instanceof Error ? err.message : "Failed to load trending questions");
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      void fetchTrendingQuestions();
    }
  }, [token, apiBaseUrl]);

  if (!token || loading) {
    return null;
  }

  if (error || questions.length === 0) {
    return null;
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  return (
    <details className="inspired-by-others-panel collapsible-panel" open={isOpen}>
      <summary
        className="collapsible-summary inspired-by-others-summary"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>✨ Inspired by Others</span>
      </summary>
      <div className="collapsible-body inspired-by-others-grid">
        {questions.map((question) => (
          <article
            key={question.questionEventId}
            className="inspired-card"
            onClick={() => onLoadQuestion(question.requestId)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onLoadQuestion(question.requestId);
              }
            }}
          >
            <h4 className="inspired-card-title">{truncateText(question.question, 80)}</h4>
            <p className="inspired-card-answer muted">
              {truncateText(question.answer, 150)}
            </p>
            <div className="inspired-card-meta">
              <span className="inspired-badge">
                {question.mode === "faq" ? "📋 FAQ" : "🔍 RAG"}
              </span>
              <span className="inspired-confidence">
                Confidence: {(question.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </article>
        ))}
      </div>
    </details>
  );
}
