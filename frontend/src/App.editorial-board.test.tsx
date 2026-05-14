import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

async function openConnectionPanel(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  await user.click(screen.getByText("Connection"));
}

async function goToEditorialTab(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  await user.click(screen.getByRole("button", { name: "Editor Review" }));
}

function mockJsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("Editorial Board flows", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch");
    localStorage.setItem("napcore.helpdesk.autoToken", "false");
    localStorage.removeItem("napcore.helpdesk.jwt");
    window.history.pushState({}, "", "/editor");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("loads board using selected filters", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse([])
    );
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

    await openConnectionPanel(user);
    await user.type(screen.getByPlaceholderText("Paste token"), "jwt-token");
    await goToEditorialTab(user);
    await user.selectOptions(screen.getByLabelText("Status"), "review");
    const [, boardReasonSelect] = screen.getAllByLabelText("Reason");
    await user.selectOptions(boardReasonSelect, "POLICY_REVIEW");
    const [, boardPrioritySelect] = screen.getAllByLabelText("Priority");
    await user.selectOptions(boardPrioritySelect, "high");
    await user.type(screen.getByPlaceholderText("search text"), "policy");

    await user.click(screen.getByRole("button", { name: "Load Queue" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    const calledUrl = fetchMock.mock.calls[1][0] as string;
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
      .mockResolvedValueOnce(mockJsonResponse([]))
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

    await openConnectionPanel(user);
    await user.type(screen.getByPlaceholderText("Paste token"), "jwt-token");
    await goToEditorialTab(user);
    await user.click(screen.getByRole("button", { name: "Load Queue" }));

    expect(await screen.findByText("Queue item for approval")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "reject" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "publish" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "approve" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });

    const transitionUrl = fetchMock.mock.calls[2][0] as string;
    const refreshedBoardUrl = fetchMock.mock.calls[3][0] as string;
    expect(transitionUrl).toContain("/editorial/queue/transition");
    expect(refreshedBoardUrl).toContain("/editorial/queue?");

    expect(await screen.findByRole("button", { name: "publish" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "approve" })).not.toBeInTheDocument();
  });

  it("loads KPI metrics and renders key tiles", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse([])
    );
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        windowDays: 14,
        slaHours: 48,
        generatedAt: "2026-03-28T12:00:00Z",
        totalItems: 9,
        unresolvedItems: 6,
        overdueItems: 2,
        byStatus: {
          draft: 2,
          review: 3,
          approved: 1,
          rejected: 1,
          published: 2,
        },
        byPriority: {
          low: 1,
          normal: 5,
          high: 3,
        },
        byReason: {
          LOW_CONFIDENCE: 3,
          CITATION_GAP: 2,
          POLICY_REVIEW: 3,
          USER_ESCALATION: 1,
        },
        agingBuckets: {
          lt24h: 2,
          h24to72: 3,
          gt72h: 1,
        },
      })
    );

    const user = userEvent.setup();
    render(<App />);

    await openConnectionPanel(user);
    await user.type(screen.getByPlaceholderText("Paste token"), "jwt-token");
    await goToEditorialTab(user);
    await user.clear(screen.getByLabelText("metricsWindowDays"));
    await user.type(screen.getByLabelText("metricsWindowDays"), "14");
    await user.clear(screen.getByLabelText("metricsSlaHours"));
    await user.type(screen.getByLabelText("metricsSlaHours"), "48");

    await user.click(screen.getByText("Load Queue Metrics"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    const calledUrl = fetchMock.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/editorial/queue/metrics?");
    expect(calledUrl).toContain("windowDays=14");
    expect(calledUrl).toContain("slaHours=48");

    expect(screen.getByText("generated 2026-03-28T12:00:00Z")).toBeInTheDocument();
    expect(screen.getByText("Overdue")).toBeInTheDocument();
    expect(screen.getByText("gt72h")).toBeInTheDocument();
  });

  it("shows error banner when KPI metrics request fails", async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse([])
    );
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse([])
    );
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse(
        {
          error: {
            code: "HTTP_500",
            message: "Metrics backend unavailable",
            requestId: "req-metrics-fail-1",
          },
        },
        500
      )
    );

    const user = userEvent.setup();
    render(<App />);

    await openConnectionPanel(user);
    await user.type(screen.getByPlaceholderText("Paste token"), "jwt-token");
    await goToEditorialTab(user);
    await user.click(screen.getByText("Load Queue Metrics"));

    expect(await screen.findByText("HTTP_500: Metrics backend unavailable (requestId: req-metrics-fail-1)")).toBeInTheDocument();
  });
});
