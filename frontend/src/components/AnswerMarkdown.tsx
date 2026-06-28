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
  return (
    <div className="answer-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}
