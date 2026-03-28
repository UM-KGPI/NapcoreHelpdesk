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
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("loads board using selected filters", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        page: 1,
        pageSize: 10,
        total: 1,
        actorRoles: ["reviewer"],
        items: [
          {
            queueItemId: "0f8fad5b-d9cb-469f-a165-70867728950e",
            status: "review",
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

    await user.type(screen.getByPlaceholderText("Paste token"), "jwt-token");
    await user.selectOptions(screen.getByLabelText("Status"), "review");
    const [boardReasonSelect] = screen.getAllByLabelText("Reason");
    await user.selectOptions(boardReasonSelect, "POLICY_REVIEW");
    const [boardPrioritySelect] = screen.getAllByLabelText("Priority");
    await user.selectOptions(boardPrioritySelect, "high");
    await user.type(screen.getByPlaceholderText("search text"), "policy");

    await user.click(screen.getByRole("button", { name: "Load Board" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/editorial/queue?");
    expect(calledUrl).toContain("status=review");
    expect(calledUrl).toContain("reason=POLICY_REVIEW");
    expect(calledUrl).toContain("priority=high");
    expect(calledUrl).toContain("search=policy");
    expect(calledUrl).toContain("page=1");
    expect(calledUrl).toContain("pageSize=10");

    expect(await screen.findByText("Need policy check")).toBeInTheDocument();
    expect(screen.getByText("roles: reviewer")).toBeInTheDocument();
  });

  it("renders only allowed actions and refreshes board after transition", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);

    const boardPayload = {
      page: 1,
      pageSize: 10,
      total: 1,
      actorRoles: ["reviewer"],
      items: [
        {
          queueItemId: "0f8fad5b-d9cb-469f-a165-70867728950e",
          status: "review",
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

    fetchMock
      .mockResolvedValueOnce(mockJsonResponse(boardPayload))
      .mockResolvedValueOnce(
        mockJsonResponse({
          queueItemId: "0f8fad5b-d9cb-469f-a165-70867728950e",
          status: "approved",
          transition: {
            action: "approve",
            fromStatus: "review",
            toStatus: "approved",
            actorId: "test-user",
            actorRoles: ["reviewer"],
          },
        })
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          ...boardPayload,
          items: [
            {
              ...boardPayload.items[0],
              status: "approved",
              allowedActions: ["publish", "reopen"],
            },
          ],
        })
      );

    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByPlaceholderText("Paste token"), "jwt-token");
    await user.click(screen.getByRole("button", { name: "Load Board" }));

    expect(await screen.findByText("Queue item for approval")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "reject" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "publish" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "approve" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    const transitionUrl = fetchMock.mock.calls[1][0] as string;
    const refreshedBoardUrl = fetchMock.mock.calls[2][0] as string;
    expect(transitionUrl).toContain("/editorial/queue/transition");
    expect(refreshedBoardUrl).toContain("/editorial/queue?");

    expect(await screen.findByRole("button", { name: "publish" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "approve" })).not.toBeInTheDocument();
  });
});
