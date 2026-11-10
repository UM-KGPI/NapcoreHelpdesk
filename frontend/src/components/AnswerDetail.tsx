/**
 * A stored answer as the editor console shows it (Review Q&As, the review board, FAQs): the same body as
 * the question page (generated example or schema structure, then the text), the evidence list with one
 * row per source and its [E#] markers, the note when no valid example could be generated, and the
 * legal context.
 */
import { citationDisplayName, groupCitationsBySource } from "../citationLabels";
import type { QuestionEventDetail } from "../types";
import AnswerBody from "./AnswerBody";
import GeneratedExampleBlock from "./GeneratedExample";
import LegalContext from "./LegalContext";

type StoredAnswer = Pick<
  QuestionEventDetail,
  "answer" | "citations" | "generatedExample" | "schemaStructure" | "legalContext"
>;

export default function AnswerDetail({ detail }: { detail: StoredAnswer }) {
  return (
    <>
      <AnswerBody text={detail.answer} example={detail.generatedExample} structure={detail.schemaStructure} />
      {detail.citations.length > 0 && (
        <>
          <p className="tiny"><strong>Evidence</strong></p>
          <ul>
            {groupCitationsBySource(detail.citations).map((group) => (
              <li key={`${group.primary.chunkId}-${group.primary.sourcePath}`}>
                <strong>{group.markers.join(" ")}</strong>{" "}
                <a href={group.primary.repositoryUrl} target="_blank" rel="noreferrer">
                  {citationDisplayName(group.primary)}
                </a>
                {!group.primary.title && citationDisplayName(group.primary) !== group.primary.sourcePath && (
                  <span className="muted"> · {group.primary.sourcePath}</span>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      {!detail.generatedExample?.valid && <GeneratedExampleBlock example={detail.generatedExample} />}
      <LegalContext items={detail.legalContext} />
    </>
  );
}
