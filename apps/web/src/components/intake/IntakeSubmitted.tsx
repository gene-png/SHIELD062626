"use client";

import Link from "next/link";

import { Card, CardBody, CardHeader, CardTitle, StatusPill } from "@shield/design-system";

import {
  SERVICE_LABELS,
  type IntakeStateResponse,
  type ServiceType,
} from "@/lib/intake/types";

export interface IntakeSubmittedProps {
  state: IntakeStateResponse;
}

/**
 * Shown after a successful intake submission instead of leaving the client
 * sitting on the review step. Summarizes what was sent and what happens next.
 */
export function IntakeSubmitted({ state }: IntakeSubmittedProps): JSX.Element {
  const legalName =
    state.client?.legal_name && state.client.legal_name !== "(pending intake)"
      ? state.client.legal_name
      : "your organization";

  // Authoritative list of what was actually created, de-duplicated.
  const services = Array.from(
    new Set(state.service_requests.map((r) => r.service_type)),
  ) as ServiceType[];

  const submittedAt = state.intake_completed_at
    ? new Date(state.intake_completed_at).toLocaleString()
    : null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className="flex h-9 w-9 items-center justify-center rounded-full bg-status-success-bg text-base font-semibold text-status-success-fg"
          >
            ✓
          </span>
          <CardTitle>Intake received</CardTitle>
        </div>
      </CardHeader>
      <CardBody>
        <div className="flex flex-col gap-6">
          <p className="text-sm text-ink-secondary">
            Thanks — we&apos;ve received the engagement intake for{" "}
            <span className="font-medium text-ink-primary">{legalName}</span>
            {submittedAt ? ` on ${submittedAt}` : ""}. A consultant will review
            your submission and reach out with next steps.
          </p>

          {services.length > 0 ? (
            <div className="flex flex-col gap-2">
              <p className="text-sm font-semibold uppercase tracking-wider text-ink-tertiary">
                Services requested
              </p>
              <div className="flex flex-wrap gap-2">
                {services.map((svc) => (
                  <StatusPill key={svc} tone="info" withDot>
                    {SERVICE_LABELS[svc]}
                  </StatusPill>
                ))}
              </div>
            </div>
          ) : null}

          <div className="rounded-md border border-border-subtle bg-surface-sunken px-4 py-3 text-sm text-ink-secondary">
            <p className="font-medium text-ink-primary">What happens next</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>
                Our team reviews your intake and any documents you uploaded.
              </li>
              <li>We confirm scope and schedule the assessment kickoff.</li>
              <li>Completed reports will appear under Deliverables.</li>
            </ul>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/deliverables"
              className="rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-ink-on-accent hover:bg-brand-600"
            >
              Go to deliverables
            </Link>
            <Link
              href="/"
              className="rounded-md border border-border bg-surface-card px-4 py-2 text-sm font-semibold text-ink-primary hover:bg-surface-sunken"
            >
              Back to home
            </Link>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
