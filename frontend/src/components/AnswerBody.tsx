/**
 * The body of an assistant turn. A block taken from the schema comes first when there is one: a valid
 * generated example (an "example with values" question) or what an element contains (a "what does X
 * contain" question). The text follows it, without a heading (every answer is source-grounded), only when there is any: it then adds
 * what the evidence says, and is left out when it had nothing to add. Text that failed the answer check on
 * both attempts is kept next to the block with a notice that it was not confirmed against the sources
 * (trace.llmAnswerValidated false). Without a block, the text alone, as before.
 */
import AnswerMarkdown from "./AnswerMarkdown";
import GeneratedExampleBlock from "./GeneratedExample";
import SchemaStructureBlock from "./SchemaStructure";
import type { GeneratedExample, SchemaStructure } from "../types";

export default function AnswerBody({
  text,
  example,
  structure,
  unvalidated = false,
}: {
  text: string;
  example?: GeneratedExample | null;
  structure?: SchemaStructure | null;
  /** The text failed the answer check on both attempts (trace.llmAnswerValidated === false). */
  unvalidated?: boolean;
}) {
  const block = example?.valid ? (
    <GeneratedExampleBlock example={example} />
  ) : structure ? (
    <SchemaStructureBlock structure={structure} />
  ) : null;
  if (!block) {
    return <AnswerMarkdown text={text} />;
  }
  return (
    <>
      {block}
      {text.trim() ? (
        <div className="answer-in-standard">
          {unvalidated ? (
            <p className="tiny answer-unvalidated" role="note">
              Not confirmed against the sources: the automatic check could not match this text to the cited
              evidence.
            </p>
          ) : null}
          <AnswerMarkdown text={text} />
        </div>
      ) : null}
    </>
  );
}
