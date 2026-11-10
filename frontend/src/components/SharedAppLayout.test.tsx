import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth-context";
import SharedAppLayout from "./SharedAppLayout";

vi.mock("./ServiceStatusBanner", () => ({ default: () => null }));

afterEach(cleanup);

function renderLayout() {
  const auth = {
    apiBaseUrl: "/api",
    setApiBaseUrl: () => undefined,
    token: "",
    setToken: () => undefined,
    autoTokenEnabled: false,
    setAutoTokenEnabled: () => undefined,
  };
  return render(
    <AuthProvider value={auth}>
      <MemoryRouter>
        <Routes>
          <Route element={<SharedAppLayout appVersion="0.97.163" backendBuildRef="" apiBaseUrl="/api" />}>
            <Route path="/" element={<p>page</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("SharedAppLayout branding (#377)", () => {
  it("shows the NAPCORE logo and the EU funding emblem in the header and the footer", () => {
    renderLayout();
    for (const region of [screen.getByRole("banner"), screen.getByRole("contentinfo")]) {
      expect(within(region).getByAltText("NAPCORE")).toBeTruthy();
      expect(within(region).getByAltText("Co-funded by the European Union")).toBeTruthy();
    }
  });

  it("links the footer to the About page, the source code and the licence", () => {
    renderLayout();
    const footer = screen.getByRole("contentinfo");
    expect(within(footer).getByRole("link", { name: "About this project" }).getAttribute("href")).toBe("/about");
    expect(within(footer).getByRole("link", { name: "Source code" }).getAttribute("href")).toBe(
      "https://github.com/UM-KGPI/NapcoreHelpdesk",
    );
    expect(within(footer).getByRole("link", { name: "Licence (AGPL-3.0)" })).toBeTruthy();
  });
});
