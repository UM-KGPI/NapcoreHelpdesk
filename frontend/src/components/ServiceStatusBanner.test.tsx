import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ServiceStatusBanner, { bannerMessage, interpretStatusResponse } from "./ServiceStatusBanner";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

describe("interpretStatusResponse", () => {
  it("is ok when the backend is idle", () => {
    expect(interpretStatusResponse(200, { state: "ok", reasons: [] })).toEqual({ kind: "ok" });
  });

  it("names the sources being indexed", () => {
    const condition = interpretStatusResponse(200, {
      state: "busy",
      reasons: [{ code: "indexing", sources: ["DATEX II", "INSPIRE"] }, { code: "high_load" }],
    });
    expect(condition).toEqual({ kind: "busy", indexingSources: ["DATEX II", "INSPIRE"], highLoad: true });
    expect(bannerMessage(condition, 0)).toContain("(DATEX II, INSPIRE)");
  });

  it("reports a busy host without naming a source", () => {
    const condition = interpretStatusResponse(200, { state: "busy", reasons: [{ code: "high_load" }] });
    expect(bannerMessage(condition, 0)).toBe("The Helpdesk server is busy. Answers may take longer than usual.");
  });

  it("recognises the maintenance 503 from nginx", () => {
    const condition = interpretStatusResponse(503, { error: { code: "SERVICE_UNAVAILABLE", message: "…" } });
    expect(bannerMessage(condition, 0)).toContain("being updated");
  });

  it("shows the outer proxy's unavailable reply at once, worded for a deploy or an outage", () => {
    const condition = interpretStatusResponse(502, { error: { code: "UPSTREAM_UNAVAILABLE", message: "…" } });
    expect(condition).toEqual({ kind: "restarting" });
    expect(bannerMessage(condition, 0)).toBe("The Helpdesk is being updated or restarting. Please try again in a few minutes.");
    expect(interpretStatusResponse(504, { error: { code: "UPSTREAM_UNAVAILABLE" } })).toEqual({ kind: "restarting" });
  });

  it("treats a missing endpoint (older backend) as ok", () => {
    expect(interpretStatusResponse(404, null)).toEqual({ kind: "ok" });
  });

  it("warns about an unreachable server only after two failures in a row", () => {
    const failed = interpretStatusResponse(502, null);
    expect(failed).toEqual({ kind: "failed" });
    expect(bannerMessage(failed, 1)).toBeNull();
    expect(bannerMessage(failed, 2)).toContain("not responding");
    expect(interpretStatusResponse(null, null)).toEqual({ kind: "failed" });
  });
});

describe("ServiceStatusBanner", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows nothing while the service is ok", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { state: "ok", reasons: [] }));
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<ServiceStatusBanner apiBaseUrl="/api/v1" />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/v1/status", expect.anything()));
    expect(container.textContent).toBe("");
  });

  it("shows the indexing banner", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { state: "busy", reasons: [{ code: "indexing", sources: ["DATEX II"] }] })),
    );
    render(<ServiceStatusBanner apiBaseUrl="/api/v1" />);
    expect((await screen.findByRole("status")).textContent).toContain("DATEX II");
  });
});
