/**
 * Human-readable view of GET /api/v1/health/llm — configured vs.
 * gateway-authorized model for answer generation and controller routing,
 * so an operator can check LLM health in the browser instead of curling
 * the API with a bearer token by hand.
 *
 * Crafted by: AI coding agents
 * Created: 2026-09-21
 */

import { useCallback, useEffect, useState } from "react";

import type { HelpdeskApiClient } from "../api";
import type { LlmProviderStatus, LlmStatusResponse } from "../types";

interface LlmStatusPageProps {
  client: HelpdeskApiClient;
}

function StatusPill({ status: statusValue }: { status: string }) {
  return <span className={`llm-status-pill llm-status-pill--${statusValue}`}>{statusValue}</span>;
}

function ProviderPanel({ title, info }: { title: string; info: LlmProviderStatus }) {
  return (
    <section className="panel">
      <div className="panel-title-row">
        <h2>{title}</h2>
        <StatusPill status={info.status} />
      </div>
      {!info.enabled ? (
        <p>Disabled in configuration.</p>
      ) : (
        <dl className="llm-status-meta">
          <dt>API base URL</dt>
          <dd>{info.apiBaseUrl}</dd>
          <dt>Configured model</dt>
          <dd>{info.configuredModel}</dd>
          <dt>Active model</dt>
          <dd>{info.activeModel}</dd>
          <dt>Auto-corrected this process</dt>
          <dd>{info.autoCorrected ? "Yes — see server logs for when/why" : "No"}</dd>
          {info.gatewayReachable !== undefined && (
            <>
              <dt>Gateway reachable</dt>
              <dd>{info.gatewayReachable ? "Yes" : "No"}</dd>
            </>
          )}
          {info.authorizedModels && (
            <>
              <dt>Gateway-authorized models</dt>
              <dd>{info.authorizedModels.join(", ") || "(none returned)"}</dd>
            </>
          )}
          {info.configuredModelAuthorized !== undefined && (
            <>
              <dt>Configured model authorized</dt>
              <dd>{info.configuredModelAuthorized ? "Yes" : "No"}</dd>
            </>
          )}
          {info.probeError && (
            <>
              <dt>Probe error</dt>
              <dd>{info.probeError}</dd>
            </>
          )}
        </dl>
      )}
    </section>
  );
}

export default function LlmStatusPage({ client }: LlmStatusPageProps) {
  const [data, setData] = useState<LlmStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkedAt, setCheckedAt] = useState<Date | null>(null);

  const load = useCallback(async (live: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const result = await client.getLlmStatus(live);
      setData(result);
      setCheckedAt(new Date());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setLoading(false);
    }
  }, [client]);

  useEffect(() => {
    load(true);
  }, [load]);

  return (
    <section className="llm-status-page">
      <div className="panel-title-row">
        <h2>LLM Status</h2>
        {data && <StatusPill status={data.status} />}
      </div>
      <div className="button-row">
        <button type="button" onClick={() => load(true)} disabled={loading}>
          {loading ? "Checking…" : "Re-check now"}
        </button>
        <button type="button" onClick={() => load(false)} disabled={loading}>
          Cached only (no gateway call)
        </button>
      </div>
      {checkedAt && (
        <p className="llm-status-refreshed">Last checked {checkedAt.toLocaleTimeString()}</p>
      )}
      {error && <div className="error-banner">{error}</div>}
      {data && (
        <>
          <ProviderPanel title="Answer generation" info={data.llm} />
          <ProviderPanel title="Controller routing" info={data.controllerLlm} />
        </>
      )}
    </section>
  );
}
