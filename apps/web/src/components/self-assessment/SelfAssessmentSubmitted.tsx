import Link from "next/link";

import { Card, CardBody, CardHeader, CardTitle } from "@shield/design-system";

/** Shown after a client submits a CSF/ZT self-assessment for admin review. */
export function SelfAssessmentSubmitted(): JSX.Element {
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
          <CardTitle>Self-assessment submitted</CardTitle>
        </div>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <p className="text-sm text-ink-secondary">
          Thanks — your consultant will review your responses for completeness
          and accuracy, then run the analysis. The report will appear under
          Deliverables once it&apos;s released to you.
        </p>
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
      </CardBody>
    </Card>
  );
}
