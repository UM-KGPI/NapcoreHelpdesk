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
import type { Components } from "react-markdown";

interface AnswerMarkdownProps {
  text: string;
}

export default function AnswerMarkdown({ text }: AnswerMarkdownProps) {
  // Debug logging
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

  // Custom component overrides to ensure code blocks render
  const components: Components = {
    pre: ({ children }) => (
      <pre className="answer-code-block">
        {children}
      </pre>
    ),
    code: ({ className, children, ...props }) => {
      // Fenced code blocks are wrapped in <pre> by react-markdown; inline code is not.
      const isInline = !className;
      return isInline ? (
        <code className="answer-inline-code" {...props}>
          {children}
        </code>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
  };

  return (
    <div className="answer-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
