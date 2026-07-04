/**
 * Collapsible panel showing top 3 most-liked questions to inspire user queries.
 *
 * Displays trending questions with answer snippets. Clicking a question loads
 * the full Q&A via deep link (?questionId=).
 *
 * Preloads data on mount with 24-hour localStorage cache to avoid delays
 * when opening the panel.
 *
 * Crafted by: AI coding agents
 * Created: 2026-07-04  |  Modified: 2026-07-04
 */

import { useEffect, useState } from "react";
import type { TrendingQuestion } from "../types";

interface InspiredByOthersPanelProps {
  token: string;
  apiBaseUrl: string;
  onLoadQuestion: (questionId: string) => void;
}

const CACHE_KEY = "napcore.helpdesk.trending-questions";
const CACHE_TTL_HOURS = 24;

interface CachedData {
  items: TrendingQuestion[];
  timestamp: number;
}

export default function InspiredByOthersPanel(props: InspiredByOthersPanelProps) {
  const { token, apiBaseUrl, onLoadQuestion } = props;
  const [questions, setQuestions] = useState<TrendingQuestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!token) return;

    const fetchTrendingQuestions = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/questions/trending?limit=3`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch trending questions: ${response.status}`);
        }

        const data = await response.json() as { items: TrendingQuestion[] };
        const cachedData: CachedData = {
          items: data.items,
          timestamp: Date.now(),
        };
        localStorage.setItem(CACHE_KEY, JSON.stringify(cachedData));
        setQuestions(data.items);
      } catch (err) {
        console.error("Error fetching trending questions:", err);
      }
    };

    const getCachedQuestions = (): TrendingQuestion[] | null => {
      try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (!cached) return null;

        const data: CachedData = JSON.parse(cached);
        const isExpired = Date.now() - data.timestamp > CACHE_TTL_HOURS * 60 * 60 * 1000;

        if (isExpired) {
          localStorage.removeItem(CACHE_KEY);
          return null;
        }

        return data.items;
      } catch {
        return null;
      }
    };

    // Try to load from cache first
    const cached = getCachedQuestions();
    if (cached && cached.length > 0) {
      setQuestions(cached);
    }

    // Always fetch in background to keep cache fresh
    void fetchTrendingQuestions();
  }, [token, apiBaseUrl]);

  if (!token || questions.length === 0) {
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
        <span>✨ Inspiring questions</span>
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
