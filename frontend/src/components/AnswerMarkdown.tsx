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
  // Comprehensive debug logging
  const hasCodeBlocks = text.includes("```");
  const hasBold = text.includes("**");
  const lines = text.split("\n").length;

  console.log("[AnswerMarkdown] Props received:", {
    length: text.length,
    lines: lines,
    hasCodeBlocks: hasCodeBlocks,
    hasBold: hasBold,
    hasBackticks: text.includes("`"),
    first200: text.substring(0, 200),
  });

  // Check for literal \n escape sequences
  const hasEscapedNewlines = text.includes("\\n");
  if (hasEscapedNewlines) {
    console.warn("[AnswerMarkdown] WARNING: Text contains literal \\n escape sequences!");
  }

  return (
    <div className="answer-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}
