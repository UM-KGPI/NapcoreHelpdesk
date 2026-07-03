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
  // GFM fenced code blocks must start and end at the beginning of a line.
  // The LLM sometimes places fences mid-sentence, e.g.:
  //   "For example: ```xml\n<...>\n``` [E2] 2. Next section"
  // We normalize by:
  // 1. Inserting newline before opening ``` that is not line-initial
  // 2. Inserting newline after closing ``` when followed by non-whitespace
  let normalised = text.replace(/([^\n])(```)/g, "$1\n$2");  // opening fence
  normalised = normalised.replace(/(```[A-Za-z0-9_-]*)([ \t]*[^\n\s])/g, "$1\n$2");  // closing fence

  return (
    <div className="answer-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalised}</ReactMarkdown>
    </div>
  );
}
