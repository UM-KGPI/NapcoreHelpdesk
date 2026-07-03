/**
 * Markdown renderer for grounded answer text.
 *
 * Uses react-markdown with remark-gfm to handle GitHub-flavored markdown
 * including tables and footnotes that appear in standards-domain answers.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-04-26  |  Modified: 2026-06-28
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface AnswerMarkdownProps {
  text: string;
}

export default function AnswerMarkdown({ text }: AnswerMarkdownProps) {
  // Debug logging to verify Markdown is being rendered
  console.log("[AnswerMarkdown] Rendering text length:", text.length);
  console.log("[AnswerMarkdown] Has code blocks:", text.includes("```"));
  console.log("[AnswerMarkdown] Has bold:", text.includes("**"));
  console.log("[AnswerMarkdown] First 200 chars:", text.substring(0, 200));

  return (
    <div className="answer-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}
