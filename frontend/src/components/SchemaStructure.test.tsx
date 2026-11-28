import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AnswerBody from "./AnswerBody";
import SchemaStructureBlock from "./SchemaStructure";
import { answerBodyText, schemaStructureText } from "./answerText";

afterEach(cleanup);

const structure = {
  element: "StopPlace",
  documentation: "Version of a named place where public transport may be accessed.",
  source: "xsd/netex_part_1/part1_ifopt/netex_ifopt_stopPlace_version.xsd",
  groups: [
    { owner: "StopPlace", inherited: false, children: [{ name: "quays", documentation: "QUAYs within the STOP PLACE." }] },
    { owner: "Site", inherited: true, children: [{ name: "entrances", documentation: "ENTRANCEs to and within SITE." }] },
  ],
  attributes: [{ name: "id", documentation: "Identifier of STOP PLACE.", owner: "StopPlace" }],
};

describe("SchemaStructureBlock", () => {
  it("shows the element's own children open and the inherited ones collapsed", () => {
    render(<SchemaStructureBlock structure={structure} />);
    expect(screen.getByText(/From the NeTEx schema/)).toBeTruthy();
    expect(screen.getByText("quays")).toBeTruthy();
    expect(screen.getByText(/Inherited as/)).toBeTruthy();
    expect(screen.getByText(/Attributes \(1\)/)).toBeTruthy();
  });

  it("renders nothing without a structure", () => {
    const { container } = render(<SchemaStructureBlock structure={null} />);
    expect(container.textContent).toBe("");
  });

  it("comes first in the answer body, with the text after it and no heading over the text", () => {
    render(<AnswerBody text="Examples fill `quays` [E1]." structure={structure} />);
    expect(screen.queryByText("In the standard")).toBeNull();
    expect(screen.getByText(/Examples fill/)).toBeTruthy();
    expect(screen.getByText(/What/)).toBeTruthy();
  });

  it("is included in the copied text", () => {
    const text = answerBodyText("Plain.", null, structure);
    expect(text.startsWith("What StopPlace contains, from the NeTEx schema")).toBe(true);
    expect(text).toContain("- quays: QUAYs within the STOP PLACE.");
    expect(text).toContain("Inherited as Site:");
    expect(text.endsWith("\n\nPlain.")).toBe(true);
    expect(schemaStructureText(null)).toBe("");
  });
});
