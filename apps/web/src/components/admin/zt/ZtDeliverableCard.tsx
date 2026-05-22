"use client";

import * as React from "react";

import {
  Card,
  CardBody,
  CardDescription,
  CardHeader,
  CardTitle,
  StatusPill,
} from "@shield/design-system";

import {
  finalizeZtDeliverable,
  releaseZtDeliverable,
  ZtProxyError,
} from "@/lib/zt/client";
import type { ZtAssessmentStatus, ZtDeliverable } from "@/lib/zt/types";

export interface ZtDeliverableCardProps {
  serviceId: string;
  assessmentStatus: ZtAssessmentStatus | null;
  deliverable: ZtDeliverable | null;
  onChange: (next: ZtDeliverable) => void;
}

function fmtTime(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function describeError(err: unknown): string {
  if (err instanceof ZtProxyError) {
    const payload = err.payload as
      | { error?: { message?: string }; detail?: string }
      | undefined;
    return (
      payload?.error?.message ??
      payload?.detail ??
      `Request failed (${err.status}).`
    );
  }
  return err instanceof Error ? err.message : "Request failed.";
}

export function ZtDeliverableCard({
  serviceId,
  assessmentStatus,
  deliverable,
  onChange,
}: ZtDeliverableCardProps): JSX.Element {
  const [busy, setBusy] = React.useState<"finalize" | "release" | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const canFinalize =
    assessmentStatus === "approved" || assessmentStatus === "released";
  const isReleased = Boolean(deliverable?.released_to_client_at);
  const isFinalized = Boolean(deliverable?.finalized_at);
  const canRelease = isFinalized && !isReleased;

  async function onFinalize(): Promise<void> {
    setBusy("finalize");
    setError(null);
    try {
      const next = await finalizeZtDeliverable(serviceId);
      onChange(next);
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(null);
    }
  }

  async function onRelease(): Promise<void> {
    if (!deliverable) return;
    setBusy("release");
    setError(null);
    try {
      const next = await releaseZtDeliverable(deliverable.id);
      onChange(next);
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evaluation &amp; report</CardTitle>
        <CardDescription>
          Once you&apos;ve reviewed and approved the inputs, send for evaluation
          to run the gap analysis and produce the PDF + XLSX report, then
          release it to the client. Re-running on the same day appends{" "}
          <code>_v2</code> and supersedes the prior version.
        </CardDescription>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {deliverable ? (
            <>
              <StatusPill tone={isReleased ? "success" : "info"} withDot>
                {isReleased
                  ? `Released v${deliverable.version}`
                  : `Finalized v${deliverable.version}`}
              </StatusPill>
              <span className="text-xs text-ink-tertiary">
                Finalized {fmtTime(deliverable.finalized_at)}
              </span>
              {isReleased ? (
                <span className="text-xs text-ink-tertiary">
                  · Released {fmtTime(deliverable.released_to_client_at)}
                </span>
              ) : null}
            </>
          ) : (
            <StatusPill tone="neutral" withDot>
              Not finalized yet
            </StatusPill>
          )}
        </div>

        {deliverable ? (
          <ul className="space-y-1 text-sm">
            {deliverable.pdf_artifact_id ? (
              <li>
                <a
                  href={`/api/proxy/artifacts/${deliverable.pdf_artifact_id}/download`}
                  className="text-brand-500 underline hover:text-brand-600"
                >
                  {deliverable.pdf_filename ?? "Download PDF"}
                </a>
              </li>
            ) : null}
            {deliverable.xlsx_artifact_id ? (
              <li>
                <a
                  href={`/api/proxy/artifacts/${deliverable.xlsx_artifact_id}/download`}
                  className="text-brand-500 underline hover:text-brand-600"
                >
                  {deliverable.xlsx_filename ?? "Download XLSX"}
                </a>
              </li>
            ) : null}
          </ul>
        ) : null}

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void onFinalize()}
            disabled={!canFinalize || busy !== null}
            className="rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-ink-on-accent hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy === "finalize"
              ? "Sending…"
              : deliverable
                ? "Re-run evaluation"
                : "Send for evaluation"}
          </button>
          <button
            type="button"
            onClick={() => void onRelease()}
            disabled={!canRelease || busy !== null}
            className="rounded-md border border-border bg-surface-card px-4 py-2 text-sm font-semibold text-ink-primary hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy === "release"
              ? "Releasing…"
              : isReleased
                ? "Released"
                : "Release to client"}
          </button>
          {!canFinalize && !deliverable ? (
            <span className="text-xs text-ink-tertiary">
              Approve the client inputs to enable evaluation.
            </span>
          ) : null}
        </div>

        {error ? (
          <p className="text-sm text-status-danger-fg" role="alert">
            {error}
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}
