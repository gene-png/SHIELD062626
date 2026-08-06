"use client";
import * as React from "react";

import type { JSX } from "react";

interface AiStatus {
  mode: string;
  provider: string;
  model: string;
  ready: boolean;
  detail: string;
}

const INFO_CLASSES =
  "border-status-info-border bg-status-info-bg text-status-info-fg";
const WARNING_CLASSES =
  "border-status-warning-border bg-status-warning-bg text-status-warning-fg";

/**
 * Tells the consultant when no live model call will be made, and distinguishes
 * the two reasons (D-037). Fixture mode is a normal configuration and reads as
 * information; a live mode that cannot reach its provider is a misconfiguration
 * and reads as a warning. Renders nothing when a live call will be made, or
 * while the status is still loading.
 *
 * The sentence explaining the mode is served by GET /admin/ai-status and
 * rendered verbatim. This component keeps no copy of it: a second copy would
 * drift from the API's, and one of the two would then be lying.
 */
export function AiStatusBanner(): JSX.Element | null {
  const [status, setStatus] = React.useState<AiStatus | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    fetch("/api/proxy/admin/ai-status", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: AiStatus | null) => {
        if (!cancelled) setStatus(d);
      })
      .catch(() => {
        /* non-blocking */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status || status.ready) return null;

  // Live-but-not-ready is the only misconfiguration of the two: someone asked
  // for live calls and they will not happen. Fixture mode is a deliberate
  // setting, so it gets the information tone.
  const misconfigured = status.mode === "live";

  return (
    <div
      role="status"
      className={`rounded-md border px-4 py-3 text-sm ${
        misconfigured ? WARNING_CLASSES : INFO_CLASSES
      }`}
    >
      {misconfigured ? (
        <>
          <span className="font-semibold">AI is not live.</span> {status.detail}{" "}
          Run AI will not reach the provider until this is fixed.
        </>
      ) : (
        <>
          <span className="font-semibold">AI mode: {status.mode}.</span>{" "}
          {status.detail}
        </>
      )}
    </div>
  );
}
