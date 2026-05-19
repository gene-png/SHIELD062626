"use client";

import * as React from "react";

import {
  Card,
  CardBody,
  CardDescription,
  CardHeader,
  CardTitle,
  EmptyState,
  StatusPill,
} from "@shield/design-system";

import { fetchIntakeQueue } from "@/lib/admin/client";
import type { AdminIntakeQueueResponse } from "@/lib/admin/types";
import { SERVICE_LABELS, type ServiceType } from "@/lib/intake/types";

function row(label: string, value: string | null | undefined): JSX.Element {
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-border-subtle py-2 last:border-b-0 sm:grid-cols-3">
      <dt className="text-sm font-medium text-ink-secondary">{label}</dt>
      <dd className="text-sm text-ink-primary sm:col-span-2">
        {value ? (
          value
        ) : (
          <span className="italic text-ink-tertiary">Not provided</span>
        )}
      </dd>
    </div>
  );
}

function serviceTone(
  s: AdminIntakeQueueResponse["service_requests"][number],
): "info" | "success" | "warning" | "neutral" {
  if (s.fulfilled_service_id) return "success";
  if (s.declined_at) return "warning";
  if (s.service_type === "consultation") return "neutral";
  return "info";
}

function serviceState(
  s: AdminIntakeQueueResponse["service_requests"][number],
): string {
  if (s.fulfilled_service_id) return "Fulfilled";
  if (s.declined_at) return "Declined";
  return "Open";
}

export function IntakeQueue(): JSX.Element {
  const [state, setState] = React.useState<AdminIntakeQueueResponse | null>(
    null,
  );
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    fetchIntakeQueue()
      .then((s) => {
        if (!cancelled) setState(s);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Couldn&apos;t load the queue</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-status-danger-fg">{error}</p>
        </CardBody>
      </Card>
    );
  }

  if (!state) {
    return <p className="text-sm text-ink-tertiary">Loading…</p>;
  }

  const c = state.client;
  const submittedAt = state.intake_completed_at
    ? new Date(state.intake_completed_at).toLocaleString()
    : null;
  const hasIntake = c !== null && c.legal_name !== "(pending intake)";

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-500">
            Admin
          </p>
          <h1 className="text-3xl font-semibold text-ink-primary">
            Intake queue
          </h1>
          <p className="max-w-prose text-sm text-ink-secondary">
            Single-tenant deployment: one client, one intake. The queue reflects
            exactly what the client entered. Phase 3 adds the workflow surfaces
            (attach reviewer, mark final, release deliverable).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {submittedAt ? (
            <StatusPill tone="success" withDot>
              Submitted {submittedAt}
            </StatusPill>
          ) : hasIntake ? (
            <StatusPill tone="warning" withDot>
              In progress — not yet submitted
            </StatusPill>
          ) : (
            <StatusPill tone="neutral" withDot>
              No intake started
            </StatusPill>
          )}
          <StatusPill tone="info">
            {state.total_users} user{state.total_users === 1 ? "" : "s"}
          </StatusPill>
        </div>
      </header>

      {hasIntake ? (
        <Card>
          <CardHeader>
            <CardTitle>Organization</CardTitle>
            <CardDescription>
              From the client&apos;s intake submission.
            </CardDescription>
          </CardHeader>
          <CardBody>
            <dl>
              {row("Legal name", c.legal_name)}
              {row("DBA / Trade name", c.dba_name)}
              {row("Website", c.website)}
              {row("Headcount band", c.size_band)}
              {row("Industry", c.industry)}
              {row(
                "Address",
                [
                  c.address_line1,
                  c.address_line2,
                  c.city,
                  c.state,
                  c.postal_code,
                  c.country,
                ]
                  .filter(Boolean)
                  .join(", ") || null,
              )}
              {row("Systems and context", c.prompting_context)}
            </dl>
          </CardBody>
        </Card>
      ) : (
        <EmptyState
          title="No client intake yet"
          description="When the deployment's primary POC submits intake, it will appear here."
        />
      )}

      <section
        aria-labelledby="service-requests"
        className="flex flex-col gap-3"
      >
        <h2
          id="service-requests"
          className="text-lg font-semibold text-ink-primary"
        >
          Service requests ({state.service_requests.length})
        </h2>
        {state.service_requests.length === 0 ? (
          <EmptyState
            title="No service requests yet"
            description="Each service the client picks at intake becomes a request here."
          />
        ) : (
          <ul className="flex flex-col gap-3">
            {state.service_requests.map((s) => (
              <li key={s.id}>
                <Card>
                  <CardHeader>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <CardTitle>
                        {SERVICE_LABELS[s.service_type as ServiceType]}
                      </CardTitle>
                      <StatusPill tone={serviceTone(s)} withDot>
                        {serviceState(s)}
                      </StatusPill>
                    </div>
                    <CardDescription>
                      Requested {new Date(s.requested_at).toLocaleString()} by{" "}
                      <span className="font-medium text-ink-primary">
                        {s.requested_by.display_name ?? s.requested_by.email}
                      </span>
                      {s.requested_by.title ? ` · ${s.requested_by.title}` : ""}
                    </CardDescription>
                  </CardHeader>
                  <CardBody>
                    <dl>
                      {row("Email", s.requested_by.email)}
                      {row(
                        "Target deadline",
                        s.deadline
                          ? new Date(s.deadline).toLocaleDateString()
                          : null,
                      )}
                      {row("Notes", s.notes)}
                      {s.declined_at
                        ? row("Decline reason", s.declined_reason)
                        : null}
                    </dl>
                  </CardBody>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="artifacts" className="flex flex-col gap-3">
        <h2 id="artifacts" className="text-lg font-semibold text-ink-primary">
          Uploaded documents ({state.artifacts.length})
        </h2>
        {state.artifacts.length === 0 ? (
          <EmptyState
            title="No documents uploaded yet"
            description="Files the client attaches during intake will appear here."
          />
        ) : (
          <ul className="flex flex-col gap-1">
            {state.artifacts.map((a) => (
              <li
                key={a.id}
                className="flex items-center justify-between gap-3 rounded-md border border-border-subtle bg-surface-card px-3 py-2 text-sm"
              >
                <span
                  className="truncate font-medium text-ink-primary"
                  title={a.title}
                >
                  {a.title}
                </span>
                <span className="shrink-0 text-xs text-ink-tertiary">
                  {(a.size_bytes / 1024).toFixed(1)} KB ·{" "}
                  {new Date(a.uploaded_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
