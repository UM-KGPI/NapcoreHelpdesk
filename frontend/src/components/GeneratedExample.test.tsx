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
    expect(screen.getByText(/not taken from the standard · valid against NeTEx 2\.0/)).toBeTruthy();
    expect(screen.getByText(/commit 37ff1e4/)).toBeTruthy();
    expect(screen.getByText(/<ResourceFrame>/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Download as PublicationDelivery" })).toBeTruthy();
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
