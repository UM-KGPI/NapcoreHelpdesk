import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import GeneratedExampleBlock from "./GeneratedExample";

afterEach(cleanup);

describe("GeneratedExampleBlock", () => {
  it("shows a valid fragment labelled as generated, with the schema version", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 1,
          xml: "<ResourceFrame>\n  <vehicleTypes/>\n</ResourceFrame>",
          document: "<PublicationDelivery/>",
          schemaVersion: "2.0",
          schemaCommit: "37ff1e453596",
        }}
      />,
    );
    expect(screen.getByText("Generated example")).toBeTruthy();
    expect(screen.getByText(/Generated for this question · valid against NeTEx 2\.0/)).toBeTruthy();
    expect(screen.getByText(/commit 37ff1e4/)).toBeTruthy();
    expect(screen.getByText(/<ResourceFrame>/)).toBeTruthy();
    // The block's one button is the download, next to the fragment; copying is the answer's Copy answer.
    expect(screen.getAllByRole("button").map((b) => b.getAttribute("aria-label"))).toEqual([
      "Download generated example as XML file",
    ]);
  });

  it("explains each element in the schema's words", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 1,
          xml: "<ResourceFrame/>",
          elementNotes: [
            { name: "SeatingCapacity", documentation: "The seating capacity of vehicles of the type." },
            { name: "StandingCapacity", documentation: "The standing capacity of vehicles of the type." },
          ],
        }}
      />,
    );
    expect(screen.getByText(/in the words of the NeTEx schema/)).toBeTruthy();
    expect(screen.getByText("SeatingCapacity")).toBeTruthy();
    expect(screen.getByText("The standing capacity of vehicles of the type.")).toBeTruthy();
  });

  it("shows no notes block without notes", () => {
    render(<GeneratedExampleBlock example={{ valid: true, attempts: 1, xml: "<ResourceFrame/>", elementNotes: [] }} />);
    expect(screen.queryByText(/in the words of the NeTEx schema/)).toBeNull();
  });

  it("never shows XML that did not validate", () => {
    render(<GeneratedExampleBlock example={{ valid: false, attempts: 3, errors: ["line 1: ..."] }} />);
    expect(screen.getByText(/No NeTEx example valid against the schema/)).toBeTruthy();
    expect(screen.queryByText("Generated example")).toBeNull();
  });

  it("renders nothing when no example was asked for", () => {
    const { container } = render(<GeneratedExampleBlock example={null} />);
    expect(container.textContent).toBe("");
  });
});
