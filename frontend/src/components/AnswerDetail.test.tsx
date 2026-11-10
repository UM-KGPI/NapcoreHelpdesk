import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AnswerDetail from "./AnswerDetail";

afterEach(cleanup);

const path = "examples/functions/patterns/Netex_KBIC_ParisNetwork_with_bookingArrangements.xml";

describe("AnswerDetail (editor console)", () => {
  it("shows the generated example and one evidence row per source, without the E# label repeated", () => {
    render(
      <AnswerDetail
        detail={{
          answer: "The booking arrangement is shown above [E1] [E2].",
          citations: [
            { label: "E1", sourcePath: path, repositoryUrl: "https://example.org/a", chunkId: "c1" },
            { label: "E2", sourcePath: path, repositoryUrl: "https://example.org/a", chunkId: "c2" },
          ],
          generatedExample: { valid: true, attempts: 1, xml: "<ServiceFrame/>", schemaVersion: "2.0" },
          legalContext: [{ label: "MMTIS Art. 4", url: "https://eur-lex.europa.eu/x" }],
        }}
      />,
    );
    expect(screen.getByText(/<ServiceFrame\/>/)).toBeTruthy();
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(1);
    expect(rows[0].textContent).toBe(`[E1] [E2] Netex_KBIC_ParisNetwork_with_bookingArrangements.xml · ${path}`);
    expect(screen.getByRole("link", { name: "MMTIS Art. 4" })).toBeTruthy();
  });

  it("says so when no valid example could be generated", () => {
    render(<AnswerDetail detail={{ answer: "Text.", citations: [], generatedExample: { valid: false, attempts: 3 } }} />);
    expect(screen.getByText(/No NeTEx example valid against the schema could be generated/)).toBeTruthy();
  });
});
