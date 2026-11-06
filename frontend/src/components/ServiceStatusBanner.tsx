/**
 * Banner telling users that answers are slower than usual, or that the server is not answering at all.
 *
 * Polls GET /status (backend: helpdesk/services/service_status.py). The backend reports an index run or a
 * saturated host; this component adds what only the browser can see: the server returning the maintenance
 * 503, the outer proxy's own 502/504 error page (shown at once), or not answering at all (network error,
 * timeout, any other 5xx). "Not answering" needs two failed polls in a row, so one dropped request never
 * flashes a warning.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-11-06  |  Modified: 2026-11-06
 */

import { useEffect, useState } from "react";

export const STATUS_POLL_MS = 60_000;
// While something is wrong, look again sooner so the banner clears soon after the server recovers.
export const STATUS_RETRY_MS = 20_000;
const STATUS_TIMEOUT_MS = 15_000;
const FAILURES_BEFORE_UNREACHABLE = 2;

export type ServiceCondition =
  | { kind: "ok" }
  | { kind: "busy"; indexingSources: string[]; highLoad: boolean }
  | { kind: "maintenance" }
  | { kind: "restarting" }
  | { kind: "failed" };

interface StatusReason {
  code?: unknown;
  sources?: unknown;
}

function errorCode(body: unknown): unknown {
  return (body as { error?: { code?: unknown } } | null)?.error?.code;
}

/** Turns one poll's outcome into a condition. `status` is the HTTP status, or null when the request failed. */
export function interpretStatusResponse(status: number | null, body: unknown): ServiceCondition {
  if (status === null) return { kind: "failed" };
  // A backend without the endpoint (an older version mid-deploy) is answering, so nothing to report.
  if (status === 404) return { kind: "ok" };
  if (status === 503) {
    return errorCode(body) === "SERVICE_UNAVAILABLE" ? { kind: "maintenance" } : { kind: "failed" };
  }
  // The kgpi.fgpa.um.si proxy answers 502/504 with this code when the Helpdesk cannot be reached
  // (docs/outer-proxy). That is a deploy's container restart or a real outage, which the browser cannot tell
  // apart, so it gets wording that fits both, at once: unlike a dropped request, it is a definite answer.
  if ((status === 502 || status === 504) && errorCode(body) === "UPSTREAM_UNAVAILABLE") return { kind: "restarting" };
  if (status < 200 || status >= 300) return { kind: "failed" };
  if (typeof body !== "object" || body === null) return { kind: "failed" };

  const reasons = Array.isArray((body as { reasons?: unknown }).reasons)
    ? ((body as { reasons: StatusReason[] }).reasons)
    : [];
  const indexingSources = reasons
    .filter((reason) => reason?.code === "indexing")
    .flatMap((reason) => (Array.isArray(reason.sources) ? reason.sources : []))
    .filter((source): source is string => typeof source === "string");
  const highLoad = reasons.some((reason) => reason?.code === "high_load");
  if ((body as { state?: unknown }).state !== "busy" || (indexingSources.length === 0 && !highLoad)) {
    return { kind: "ok" };
  }
  return { kind: "busy", indexingSources, highLoad };
}

export function bannerMessage(condition: ServiceCondition, consecutiveFailures: number): string | null {
  switch (condition.kind) {
    case "ok":
      return null;
    case "maintenance":
      return "The Helpdesk is being updated. Please try again in a few minutes.";
    case "restarting":
      return "The Helpdesk is being updated or restarting. Please try again in a few minutes.";
    case "failed":
      return consecutiveFailures >= FAILURES_BEFORE_UNREACHABLE
        ? "The Helpdesk server is not responding. It may be restarting or overloaded; please try again in a few minutes."
        : null;
    case "busy": {
      if (condition.indexingSources.length > 0) {
        return `The Helpdesk is adding material to its search index (${condition.indexingSources.join(", ")}). Answers may take longer than usual.`;
      }
      return "The Helpdesk server is busy. Answers may take longer than usual.";
    }
  }
}

async function pollStatus(apiBaseUrl: string): Promise<ServiceCondition> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), STATUS_TIMEOUT_MS);
  try {
    const response = await fetch(`${apiBaseUrl}/status`, { cache: "no-store", signal: controller.signal });
    let body: unknown = null;
    if ((response.headers.get("content-type") ?? "").includes("application/json")) {
      try {
        body = await response.json();
      } catch {
        body = null;
      }
    }
    return interpretStatusResponse(response.status, body);
  } catch {
    return interpretStatusResponse(null, null);
  } finally {
    clearTimeout(timer);
  }
}

export default function ServiceStatusBanner({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let failures = 0;

    async function check(): Promise<void> {
      const condition = await pollStatus(apiBaseUrl);
      if (cancelled) return;
      failures = condition.kind === "failed" ? failures + 1 : 0;
      setMessage(bannerMessage(condition, failures));
      timer = setTimeout(() => void check(), condition.kind === "ok" ? STATUS_POLL_MS : STATUS_RETRY_MS);
    }

    // A tab left in the background shows a stale banner when it comes back; check right away instead.
    function onVisible(): void {
      if (document.visibilityState !== "visible") return;
      clearTimeout(timer);
      void check();
    }

    void check();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [apiBaseUrl]);

  if (!message) return null;
  return (
    <div className="service-status-banner" role="status" aria-live="polite">
      {message}
    </div>
  );
}
