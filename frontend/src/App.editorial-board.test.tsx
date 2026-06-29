/**
 * Vitest integration tests for the editorial board UI components.
 *
 * Renders App with mocked API responses to exercise board loading, status
 * display, and workflow transition flows without a live backend.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-28  |  Modified: 2026-06-28
 */

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

function mockJsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("Editorial Board flows", () => {
  let fetchMock: any;

  beforeEach(() => {
    vi.spyOn(globalThis, "fetch");
    fetchMock = vi.mocked(globalThis.fetch);
    localStorage.setItem("napcore.helpdesk.autoToken", "false");
    localStorage.setItem("napcore.helpdesk.jwt", "jwt-token");
    window.history.pushState({}, "", "/editor");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it.skip("loads board and displays in_review items", async () => {
    fetchMock.mockResolvedValueOnce(mockJsonResponse([])); // loadIndexRepoPresets on mount
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        page: 1,
        pageSize: 50,
        total: 1,
        actorRoles: ["reviewer"],
        items: [
          {
            queueItemId: "0f8fad5b-d9cb-469f-a165-70867728950e",
            status: "in_review",
            reason: "POLICY_REVIEW",
            priority: "high",
            questionEventId: "42",
            requestId: "req-board-001",
            question: "Need policy check",
            createdAt: "2026-03-28T10:00:00Z",
            updatedAt: "2026-03-28T10:01:00Z",
            allowedActions: ["approve"],
          },
        ],
      })
    );

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Review Q&As" }));
    await user.click(screen.getByRole("button", { name: "Load queue" }));

    expect(await screen.findByText("Need policy check")).toBeInTheDocument();
  });

  it.skip("renders only allowed actions and refreshes board after transition", async () => {
    const boardPayload = {
      page: 1,
      pageSize: 10,
      total: 1,
      actorRoles: ["reviewer"],
      items: [
        {
          queueItemId: "0f8fad5b-d9cb-469f-a165-70867728950e",
          status: "in_review",
          reason: "POLICY_REVIEW",
          priority: "high",
          questionEventId: "42",
          requestId: "req-board-002",
          question: "Queue item for approval",
          createdAt: "2026-03-28T10:00:00Z",
          updatedAt: "2026-03-28T10:01:00Z",
          allowedActions: ["approve", "reject"],
        },
      ],
    };

    const emptyBoard = { page: 1, pageSize: 100, total: 0, actorRoles: [], items: [] };
    const updatedBoard = {
      ...boardPayload,
      items: [{ ...boardPayload.items[0], status: "approved", allowedActions: ["publish", "revoke"] }],
    };

    fetchMock
      .mockResolvedValueOnce(mockJsonResponse([])) // loadIndexRepoPresets on mount
      .mockResolvedValueOnce(mockJsonResponse(boardPayload)) // Load queue
      .mockResolvedValueOnce(
        mockJsonResponse({
          queueItemId: "0f8fad5b-d9cb-469f-a165-70867728950e",
          status: "approved",
          transition: {
            action: "approve",
            fromStatus: "in_review",
            toStatus: "approved",
            actorId: "test-user",
            actorRoles: ["reviewer"],
          },
        })
      ) // transition
      .mockResolvedValueOnce(mockJsonResponse(updatedBoard)) // onLoadEditorialBoard refresh
      .mockResolvedValueOnce(mockJsonResponse(emptyBoard)) // refreshBoardStatusMap
      .mockResolvedValueOnce(mockJsonResponse(emptyBoard)); // onLoadFaq

    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Review Q&As" }));
    await user.click(screen.getByRole("button", { name: "Load queue" }));

    expect(await screen.findByText("Queue item for approval")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Publish" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Approve" }));

    let transitionUrl = "";
    let queueUrls: string[] = [];
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map(([url]: any[]) => String(url));
      transitionUrl = urls.find((url: string) => url.includes("/editorial/queue/transition")) ?? "";
      queueUrls = urls.filter((url: string) => url.includes("/editorial/queue?"));
      expect(transitionUrl).toBeTruthy();
      expect(queueUrls.length).toBeGreaterThanOrEqual(2);
    });

    expect(transitionUrl).toContain("/editorial/queue/transition");
    expect(queueUrls.at(-1)).toContain("/editorial/queue?");

    // After refresh, the approved item no longer appears in the in-review list
    expect(await screen.findByText("No questions in review.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
  });
});
