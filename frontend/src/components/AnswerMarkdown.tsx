/**
 * Markdown renderer for grounded answer text.
 *
 * Uses react-markdown with remark-gfm (GitHub-flavored markdown).
 * No custom component overrides — the library renders code blocks,
 * inline code, tables and footnotes correctly out of the box.
 * Styling comes from the global pre/code rules in styles.css.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-04-26  |  Modified: 2026-07-03
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface AnswerMarkdownProps {
  text: string;
}

export default function AnswerMarkdown({ text }: AnswerMarkdownProps) {
  return (
    <div className="answer-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}
