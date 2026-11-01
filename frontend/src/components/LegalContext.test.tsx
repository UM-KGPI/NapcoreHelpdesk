import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LegalContext from "./LegalContext";

describe("LegalContext", () => {
  it("links each provision to EUR-Lex", () => {
    render(
      <LegalContext
        items={[
          { label: "MMTIS Art. 4", url: "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02017R1926-20240304#art_4" },
          { label: "TEL TSI App. C", url: "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32026R0253#app_C" },
        ]}
      />,
    );
    expect(screen.getByText("Legal context:")).toBeTruthy();
    expect(screen.getByRole("link", { name: "MMTIS Art. 4" }).getAttribute("href")).toContain("#art_4");
    expect(screen.getByRole("link", { name: "TEL TSI App. C" }).getAttribute("href")).toContain("#app_C");
  });

  it("renders nothing without provisions", () => {
    const { container } = render(<LegalContext items={[]} />);
    expect(container.textContent).toBe("");
  });
});
