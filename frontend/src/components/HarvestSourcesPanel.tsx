import { useCallback, useEffect, useRef, useState } from "react";
import type { HelpdeskApiClient } from "../api";
import type { HarvestJobResponse, HarvestSource } from "../types";

// A harvest runs in the Celery worker; the panel polls its state until it finishes.
const POLL_INTERVAL_MS = 3000;

type HarvestJobState = {
  source: string;
  jobId: string;
  job: HarvestJobResponse | null;
};

interface HarvestSourcesPanelProps {
  client: HelpdeskApiClient;
  token: string;
}

function shortCommit(commit: string | null | undefined): string {
  return commit ? commit.slice(0, 8) : "—";
}

function formatTime(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "—";
}

function HarvestJobReport({ job }: { job: HarvestJobState }) {
  const response = job.job;
  if (!response || response.state === "queued" || response.state === "running") {
    return (
      <div className="index-progress" aria-live="polite" aria-busy="true">
        <div className="index-progress-bar" role="progressbar" aria-label={`Harvesting ${job.source}`} aria-valuemin={0} aria-valuemax={100}>
          <span className="index-progress-fill" />
        </div>
        <p className="muted">
          {response?.state === "running" ? "Running" : "Queued"}: fetching {job.source}, indexing changed files
          and loading its ontology, if it has one.
        </p>
      </div>
    );
  }
  if (response.state === "error") {
    return <p className="error-text">Harvest of {job.source} failed: {response.error}</p>;
  }
  const report = response.result;
  if (!report) {
    return null;
  }
  if (report.status === "skipped") {
    return <p className="muted">Harvest of {job.source} skipped: {report.reason}.</p>;
  }
  const row = report.results[job.source];
  if (!row) {
    return <p className="error-text">Harvest of {job.source} returned no result.</p>;
  }
  if (row.status !== "ok") {
    return <p className="error-text">Harvest of {job.source} failed: {row.error}</p>;
  }
  return (
    <article className="result-card">
      <h3>Harvest Result: {job.source}</h3>
      <dl className="kv-list">
        <dt>Commit</dt><dd>{shortCommit(row.commit)}</dd>
        <dt>Mode</dt><dd>{row.mode}</dd>
        <dt>Scanned</dt><dd>{row.scanned_files} files</dd>
        <dt>Skipped</dt><dd>{row.skipped_files} files</dd>
        <dt>Created chunks</dt><dd>{row.created_chunks}</dd>
        <dt>Updated chunks</dt><dd>{row.updated_chunks}</dd>
        <dt>Deleted chunks</dt><dd>{row.deleted_chunks}</dd>
        {row.ontology && (
          <>
            <dt>Ontology</dt>
            <dd>
              {row.ontology.key} {row.ontology.version}: {row.ontology.status}
              {row.ontology.reason ? ` (${row.ontology.reason})` : ""}
            </dd>
          </>
        )}
        <dt>Duration</dt><dd>{row.seconds} s</dd>
      </dl>
    </article>
  );
}

export default function HarvestSourcesPanel({ client, token }: HarvestSourcesPanelProps) {
  const [sources, setSources] = useState<HarvestSource[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [fullReindex, setFullReindex] = useState(false);
  const [job, setJob] = useState<HarvestJobState | null>(null);
  const pollTimer = useRef<number | null>(null);

  const loadSources = useCallback(async () => {
    try {
      const response = await client.listSources();
      setSources(response.sources);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    }
  }, [client]);

  useEffect(() => {
    if (token) {
      void loadSources();
    }
  }, [token, loadSources]);

  useEffect(() => () => {
    if (pollTimer.current !== null) {
      window.clearTimeout(pollTimer.current);
    }
  }, []);

  const poll = useCallback(
    async (current: HarvestJobState) => {
      try {
        const response = await client.getHarvestJob(current.jobId);
        const next = { ...current, job: response };
        setJob(next);
        if (response.state === "queued" || response.state === "running") {
          pollTimer.current = window.setTimeout(() => void poll(next), POLL_INTERVAL_MS);
        } else {
          void loadSources();
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setJob({ ...current, job: { requestId: "", jobId: current.jobId, state: "error", result: null, error: message } });
      }
    },
    [client, loadSources],
  );

  async function onHarvest(source: string): Promise<void> {
    try {
      const { jobId } = await client.harvestSource(source, fullReindex);
      const started = { source, jobId, job: null };
      setJob(started);
      void poll(started);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setJob({ source, jobId: "", job: { requestId: "", jobId: "", state: "error", result: null, error: message } });
    }
  }

  const running = job !== null && (job.job === null || job.job.state === "queued" || job.job.state === "running");

  return (
    <section className="panel step-1-index">
      <div className="panel-title-row">
        <h2>Harvest Sources</h2>
        <p className="muted">Fetch a configured source, index what changed, and load its ontology into GraphDB.</p>
      </div>
      {loadError && <p className="error-text">Could not load sources: {loadError}</p>}
      <div className="table-wrap">
        <table className="board-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Profile</th>
              <th>Indexed chunks</th>
              <th>Commit</th>
              <th>Indexed at</th>
              <th>Ontology</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.name}>
                <td>
                  <a href={source.repositoryUrl} target="_blank" rel="noreferrer">{source.name}</a>
                  {!source.checkoutPresent && <span className="muted tiny"> (not harvested yet)</span>}
                </td>
                <td>{source.profile}</td>
                <td>{source.indexedChunks}</td>
                <td>{shortCommit(source.indexedCommit)}</td>
                <td>{formatTime(source.indexedAt)}</td>
                <td>
                  {source.ontology
                    ? `${source.ontology.version ?? "not loaded"}${source.ontology.lastLoadedAt ? `, ${formatTime(source.ontology.lastLoadedAt)}` : ""}`
                    : "—"}
                </td>
                <td>
                  <button onClick={() => void onHarvest(source.name)} disabled={!token || running}>
                    Harvest &amp; index
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <label className="checkbox-label">
        <input type="checkbox" checked={fullReindex} onChange={(e) => setFullReindex(e.target.checked)} />
        Full re-index (all files, and reload the ontology even if unchanged)
      </label>
      {job && <HarvestJobReport job={job} />}
    </section>
  );
}
