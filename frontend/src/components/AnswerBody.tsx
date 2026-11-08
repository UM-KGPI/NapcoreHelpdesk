/**
 * The body of an assistant turn. With a valid generated example the example comes first (it is the
 * answer to an "example with values" question) and the text follows under "In the standard", only when
 * there is any: the text then adds what the evidence says about the example's elements, and is left out
 * when it had nothing to add or failed validation. Without one, the text alone, as before.
 */
import AnswerMarkdown from "./AnswerMarkdown";
import GeneratedExampleBlock from "./GeneratedExample";
import type { GeneratedExample } from "../types";

export default function AnswerBody({ text, example }: { text: string; example?: GeneratedExample | null }) {
  if (!example?.valid) {
    return <AnswerMarkdown text={text} />;
  }
  return (
    <>
      <GeneratedExampleBlock example={example} />
      {text.trim() ? (
        <div className="answer-in-standard">
          <p className="tiny">
            <strong>In the standard</strong>
          </p>
          <AnswerMarkdown text={text} />
        </div>
      ) : null}
    </>
  );
}
