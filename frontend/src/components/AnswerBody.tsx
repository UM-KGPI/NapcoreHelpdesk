/**
 * The body of an assistant turn. A block taken from the schema comes first when there is one: a valid
 * generated example (an "example with values" question) or what an element contains (a "what does X
 * contain" question). The text follows it, without a heading (every answer is source-grounded), only when there is any: it then adds
 * what the evidence says, and is left out when it had nothing to add or failed validation. Without a
 * block, the text alone, as before.
 */
import AnswerMarkdown from "./AnswerMarkdown";
import GeneratedExampleBlock from "./GeneratedExample";
import SchemaStructureBlock from "./SchemaStructure";
import type { GeneratedExample, SchemaStructure } from "../types";

export default function AnswerBody({
  text,
  example,
  structure,
}: {
  text: string;
  example?: GeneratedExample | null;
  structure?: SchemaStructure | null;
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
          <AnswerMarkdown text={text} />
        </div>
      ) : null}
    </>
  );
}
