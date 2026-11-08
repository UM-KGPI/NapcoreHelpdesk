import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AnswerBody from "./AnswerBody";

afterEach(cleanup);

const example = { valid: true, attempts: 1, xml: "<SiteFrame/>", schemaVersion: "2.0" };

describe("AnswerBody", () => {
  it("puts a valid generated example before the text, under 'In the standard'", () => {
    const { container } = render(<AnswerBody text="A `Quay` sits inside `quays` [E1]." example={example} />);
    const headings = Array.from(container.querySelectorAll("h4, strong")).map((node) => node.textContent);
    expect(headings.indexOf("Generated example")).toBeLessThan(headings.indexOf("In the standard"));
    expect(screen.getByText(/sits inside/)).toBeTruthy();
  });

  it("shows only the example when the text is empty", () => {
    render(<AnswerBody text="" example={example} />);
    expect(screen.getByText("Generated example")).toBeTruthy();
    expect(screen.queryByText("In the standard")).toBeNull();
  });

  it("shows the text alone without a valid example", () => {
    render(<AnswerBody text="Plain answer." example={{ valid: false, attempts: 3 }} />);
    expect(screen.getByText("Plain answer.")).toBeTruthy();
    expect(screen.queryByText("Generated example")).toBeNull();
    expect(screen.queryByText("In the standard")).toBeNull();
  });
});
