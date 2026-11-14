import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AnswerBody from "./AnswerBody";

afterEach(cleanup);

const example = { valid: true, attempts: 1, xml: "<SiteFrame/>", schemaVersion: "2.0" };

describe("AnswerBody", () => {
  it("puts a valid generated example before the text, with no heading over the text", () => {
    const { container } = render(<AnswerBody text="A `Quay` sits inside `quays` [E1]." example={example} />);
    const headings = Array.from(container.querySelectorAll("h4, strong")).map((node) => node.textContent);
    expect(headings.findIndex((h) => (h ?? "").startsWith("Generated example"))).toBeGreaterThanOrEqual(0);
    expect(screen.queryByText("In the standard")).toBeNull();
    const html = container.innerHTML;
    expect(html.indexOf("Generated example")).toBeLessThan(html.indexOf("sits inside"));
    expect(screen.getByText(/sits inside/)).toBeTruthy();
  });

  it("shows only the example when the text is empty", () => {
    render(<AnswerBody text="" example={example} />);
    expect(screen.getByText(/^Generated example for this question/)).toBeTruthy();
    expect(screen.queryByText("In the standard")).toBeNull();
  });

  it("shows the text alone without a valid example", () => {
    render(<AnswerBody text="Plain answer." example={{ valid: false, attempts: 3 }} />);
    expect(screen.getByText("Plain answer.")).toBeTruthy();
    expect(screen.queryByText(/^Generated example/)).toBeNull();
    expect(screen.queryByText("In the standard")).toBeNull();
  });

  it("marks text that failed validation next to a block as not confirmed against the sources", () => {
    const { container } = render(<AnswerBody text="Primer kaže sedeže [E1]." example={example} unvalidated />);
    const note = screen.getByRole("note");
    expect(note.textContent).toMatch(/^Not confirmed against the sources/);
    const html = container.innerHTML;
    expect(html.indexOf("Generated example")).toBeLessThan(html.indexOf("Not confirmed"));
    expect(html.indexOf("Not confirmed")).toBeLessThan(html.indexOf("Primer kaže"));
  });

  it("does not mark validated text", () => {
    render(<AnswerBody text="A `Quay` sits inside `quays` [E1]." example={example} />);
    expect(screen.queryByRole("note")).toBeNull();
    expect(screen.queryByText(/Not confirmed against the sources/)).toBeNull();
  });
});
