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
