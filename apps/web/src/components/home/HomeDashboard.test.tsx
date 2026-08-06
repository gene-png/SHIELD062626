import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AssessmentResponse } from "@/lib/intake/types";

import { HomeDashboard, phaseFor, SERVICE_PHASE_LEGEND } from "./HomeDashboard";

/**
 * S7. The "Your services" grid shows a client one phase label per engagement and
 * nothing else, so the label carries the whole claim about where their
 * engagement stands. Two things get held here:
 *
 * 1. The legend explains every label `phaseFor` can return. Not a sample: the
 *    full lifecycle status domain is driven through `phaseFor` and every label
 *    it produces must have a legend entry.
 * 2. Nothing in the legend is a phantom. Every entry has to be reachable from
 *    some real status, so the legend never describes a phase the lifecycle
 *    cannot produce.
 *
 * Server-rendered and pure: HomeDashboard fetches nothing.
 */

/** Every value `assessment_status` can carry on the wire, plus one the API does not send. */
const ASSESSMENT_STATUSES: ReadonlyArray<string | null> = [
  null,
  "draft",
  "submitted",
  "approved",
  "released",
  "discarded",
  "quantum_reviewed",
];

/** Every value the enclosing service `status` can carry (apps/api ServiceStatus). */
const SERVICE_STATUSES: readonly string[] = [
  "draft",
  "in_progress",
  "review",
  "released",
  "archived",
];

function engagement(
  serviceId: string,
  assessmentStatus: string | null,
  status: string,
): AssessmentResponse {
  return {
    service_id: serviceId,
    service_type: "nist_csf",
    title: `Engagement ${serviceId}`,
    status,
    assessment_status: assessmentStatus,
    created_at: "2026-08-01T00:00:00Z",
  };
}

describe("HomeDashboard service phase legend", () => {
  it("explains all five phase labels a client can be shown", () => {
    render(
      <HomeDashboard
        greetingName="Rae"
        deliverables={[]}
        engagements={[engagement("svc-1", "draft", "in_progress")]}
        unreadMessages={0}
        valueSummary={null}
      />,
    );

    expect(SERVICE_PHASE_LEGEND).toHaveLength(5);
    expect(SERVICE_PHASE_LEGEND.map((e) => e.label)).toEqual([
      "Getting started",
      "In progress",
      "Under review",
      "Finalizing your report",
      "Report ready",
    ]);
    const legend = screen.getByRole("list", { name: "What each phase means" });
    for (const entry of SERVICE_PHASE_LEGEND) {
      expect(legend.textContent).toContain(entry.label);
      expect(legend.textContent).toContain(entry.meaning);
    }
  });

  it("never shows a phase the legend does not explain", () => {
    const explained = new Set(SERVICE_PHASE_LEGEND.map((e) => e.label));
    for (const assessmentStatus of ASSESSMENT_STATUSES) {
      for (const status of SERVICE_STATUSES) {
        for (const released of [false, true]) {
          const label = phaseFor(
            engagement("svc-1", assessmentStatus, status),
            released,
          ).label;
          expect(explained).toContain(label);
        }
      }
    }
  });

  it("has no legend entry a real status cannot reach", () => {
    const reachable = new Set<string>();
    for (const assessmentStatus of ASSESSMENT_STATUSES) {
      for (const status of SERVICE_STATUSES) {
        for (const released of [false, true]) {
          reachable.add(
            phaseFor(engagement("svc-1", assessmentStatus, status), released)
              .label,
          );
        }
      }
    }
    for (const entry of SERVICE_PHASE_LEGEND) {
      expect(reachable).toContain(entry.label);
    }
  });

  it("labels each engagement card with the phase its status maps to", () => {
    render(
      <HomeDashboard
        greetingName="Rae"
        deliverables={[]}
        engagements={[
          engagement("svc-1", "submitted", "in_progress"),
          engagement("svc-2", "approved", "in_progress"),
        ]}
        unreadMessages={0}
        valueSummary={null}
      />,
    );

    const grid = screen.getByRole("list", { name: "Your services" });
    expect(grid.textContent).toContain("Under review");
    expect(grid.textContent).toContain("Finalizing your report");
  });
});
