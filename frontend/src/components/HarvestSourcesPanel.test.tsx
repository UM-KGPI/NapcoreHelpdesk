import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { HelpdeskApiClient } from "../api";
import type { HarvestJobResponse, SourcesResponse } from "../types";
import HarvestSourcesPanel from "./HarvestSourcesPanel";

const SOURCES: SourcesResponse = {
  requestId: "r1",
  sources: [
    {
      name: "mobilityDCAT-AP",
      repositoryUrl: "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP",
      profile: "mobilitydcat-ap",
      checkoutPresent: false,
      indexedChunks: 0,
      indexedCommit: null,
      indexedAt: null,
      ontology: { key: "mobilitydcat-ap", graphUri: "https://napcore.eu/graph/standards/mobilitydcat-ap", version: null, lastLoadedAt: null },
    },
  ],
};

const FINISHED: HarvestJobResponse = {
  requestId: "r3",
  jobId: "job-1",
  state: "finished",
  error: null,
  result: {
    status: "ok",
    results: {
      "mobilityDCAT-AP": {
        status: "ok",
        repository: "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP",
        commit: "1ae93b2c0ffee",
        mode: "incremental",
        scanned_files: 64,
        skipped_files: 0,
        created_chunks: 192,
        updated_chunks: 0,
        deleted_chunks: 0,
        ontology: { key: "mobilitydcat-ap", graph: "https://napcore.eu/graph/standards/mobilitydcat-ap", version: "3.0.0", status: "loaded" },
        seconds: 12.5,
      },
    },
  },
};

describe("HarvestSourcesPanel", () => {
  // Vitest runs without globals, so Testing Library does not unmount between tests by itself.
  afterEach(cleanup);

  it("lists the sources, queues a harvest and shows its result", async () => {
    const client = {
      listSources: vi.fn().mockResolvedValue(SOURCES),
      harvestSource: vi.fn().mockResolvedValue({ jobId: "job-1", source: "mobilityDCAT-AP" }),
      getHarvestJob: vi.fn().mockResolvedValue(FINISHED),
    } as unknown as HelpdeskApiClient;

    render(<HarvestSourcesPanel client={client} token="t" />);

    expect(await screen.findByRole("link", { name: "mobilityDCAT-AP" })).toBeTruthy();
    expect(screen.getByText("(not harvested yet)")).toBeTruthy();

    fireEvent.click(screen.getByLabelText(/Full re-index/));
    fireEvent.click(screen.getByRole("button", { name: "Harvest & index" }));

    expect(await screen.findByText("Harvest Result: mobilityDCAT-AP")).toBeTruthy();
    expect(client.harvestSource).toHaveBeenCalledWith("mobilityDCAT-AP", true);
    expect(client.getHarvestJob).toHaveBeenCalledWith("job-1");
    expect(screen.getByText("192")).toBeTruthy();
    expect(screen.getByText("mobilitydcat-ap 3.0.0: loaded")).toBeTruthy();
    // The list is reloaded after the harvest to show the new index state.
    await waitFor(() => expect(client.listSources).toHaveBeenCalledTimes(2));
  });

  it("reports a skipped harvest when another one holds the lock", async () => {
    const client = {
      listSources: vi.fn().mockResolvedValue(SOURCES),
      harvestSource: vi.fn().mockResolvedValue({ jobId: "job-2", source: "mobilityDCAT-AP" }),
      getHarvestJob: vi.fn().mockResolvedValue({
        ...FINISHED,
        result: { status: "skipped", reason: "another refresh is running", results: {} },
      }),
    } as unknown as HelpdeskApiClient;

    render(<HarvestSourcesPanel client={client} token="t" />);
    fireEvent.click(await screen.findByRole("button", { name: "Harvest & index" }));

    expect(await screen.findByText("Harvest of mobilityDCAT-AP skipped: another refresh is running.")).toBeTruthy();
  });
});
