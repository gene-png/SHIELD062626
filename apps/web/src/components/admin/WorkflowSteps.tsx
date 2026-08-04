import { cn } from "@shield/design-system";

import type { JSX } from "react";

/**
 * The ordered step strip every consultant workspace carries (S7).
 *
 * Two pieces, and nothing else: a per-service list of the steps an engagement
 * moves through, and a lookup from the status the workspace already holds to the
 * step that status puts it on. No state, no fetching, no state machine.
 *
 * Each step names the statuses that land on it, so the mapping is data rather
 * than a switch. A status no step claims RAISES: a strip that quietly fell back
 * to step 1 would tell the consultant the engagement had not started, which is
 * exactly the kind of confident-but-wrong claim this batch keeps producing.
 */

export const WORKFLOW_SERVICES = ["tech_debt", "csf", "zt", "attack"] as const;

export type WorkflowService = (typeof WORKFLOW_SERVICES)[number];

export interface WorkflowStep {
  /** Short name for the step, shown in the strip. */
  label: string;
  /** What happens during the step. Static, so it reads the same whether the step is behind, current, or ahead. */
  detail: string;
  /**
   * Statuses that put the engagement on this step. `null` means nothing has
   * been created yet, which is the state the first step describes.
   */
  statuses: readonly (string | null)[];
}

/**
 * Copy for the consultant, per service. `discarded` returns to the first step
 * because a discarded draft leaves the workspace with either no assessment or
 * the previous approved version, and the work starts again either way.
 */
const STEPS: Record<WorkflowService, readonly WorkflowStep[]> = {
  tech_debt: [
    {
      label: "Inventory",
      detail:
        "Upload the client's tool inventory as CSV or XLSX. The redactor strips PII before extraction runs.",
      statuses: [null, "discarded"],
    },
    {
      label: "Capability list",
      detail:
        "Edit the extracted rows, set a disposition on each, and correct whatever the extraction got wrong.",
      statuses: ["draft"],
    },
    {
      label: "Approved",
      detail:
        "The list is locked. The consolidation plan and the deliverable build from it.",
      statuses: ["approved"],
    },
    {
      label: "Released",
      detail: "The report is with the client.",
      statuses: ["released"],
    },
  ],
  csf: [
    {
      label: "Assessment",
      detail: "Create the v1, one row per in-scope subcategory.",
      statuses: [null, "discarded"],
    },
    {
      label: "Scoring",
      detail:
        "Set a maturity tier per outcome, with a note naming the tool, policy, or process behind it.",
      statuses: ["draft"],
    },
    {
      label: "Client answers",
      detail:
        "Where the client self-assessed, read and correct what they submitted before approving it.",
      statuses: ["submitted"],
    },
    {
      label: "Approved",
      detail: "The answers are locked and the deliverable can be built.",
      statuses: ["approved"],
    },
    {
      label: "Released",
      detail: "The report is with the client.",
      statuses: ["released"],
    },
  ],
  zt: [
    {
      label: "Assessment",
      detail: "Create the v1, one row per capability in the framework.",
      statuses: [null, "discarded"],
    },
    {
      label: "Scoring",
      detail:
        "Set a current maturity stage per capability, with a note naming the tool, policy, or process behind it.",
      statuses: ["draft"],
    },
    {
      label: "Client answers",
      detail:
        "Where the client self-assessed, read and correct what they submitted before approving it.",
      statuses: ["submitted"],
    },
    {
      label: "Approved",
      detail: "The answers are locked and the deliverable can be built.",
      statuses: ["approved"],
    },
    {
      label: "Released",
      detail: "The report is with the client.",
      statuses: ["released"],
    },
  ],
  attack: [
    {
      label: "Assessment",
      detail:
        "Pre-seed an unscored coverage row for every technique in the Enterprise matrix.",
      statuses: [null, "discarded"],
    },
    {
      label: "Coverage",
      detail:
        "Set a coverage status per technique and name the detection, prevention, or response tooling behind it.",
      statuses: ["draft"],
    },
    {
      label: "Approved",
      detail: "Coverage is locked and the deliverable can be built.",
      statuses: ["approved"],
    },
    {
      label: "Released",
      detail: "The report is with the client.",
      statuses: ["released"],
    },
  ],
};

/**
 * Orientation copy for the two services a client can self-assess. One string,
 * rendered by both workspaces, so the two cannot drift apart.
 */
export const CLIENT_ANSWER_OWNERSHIP =
  "The client answers what they can. You review and edit those answers here, and you own the quality of what ships. They see the outcome, not this workspace.";

export function workflowSteps(
  service: WorkflowService,
): readonly WorkflowStep[] {
  const steps = STEPS[service];
  if (!steps) {
    throw new Error(
      `[WorkflowSteps] no step strip is defined for service "${service}"`,
    );
  }
  return steps;
}

/**
 * 1-based number of the step the engagement stands on.
 *
 * Raises on a status the service defines no step for, rather than defaulting to
 * the first step and claiming the engagement has not started.
 */
export function currentStepNumber(
  service: WorkflowService,
  status: string | null,
): number {
  const steps = workflowSteps(service);
  const index = steps.findIndex((step) => step.statuses.includes(status));
  if (index === -1) {
    throw new Error(
      `[WorkflowSteps] service "${service}" defines no step for status ${
        status === null ? "null" : `"${status}"`
      }, so the strip cannot say where the engagement stands`,
    );
  }
  return index + 1;
}

export interface WorkflowStepsProps {
  service: WorkflowService;
  /** The assessment or capability-list status the workspace already holds; `null` before one exists. */
  status: string | null;
}

export function WorkflowSteps({
  service,
  status,
}: WorkflowStepsProps): JSX.Element {
  const steps = workflowSteps(service);
  const current = currentStepNumber(service, status);
  console.debug(
    `[WorkflowSteps] ${service} status ${status ?? "null"} is step ${current} of ${steps.length}`,
  );

  return (
    <nav aria-label="Engagement steps" data-workflow-service={service}>
      <ol className="flex flex-col gap-2 sm:flex-row sm:gap-3">
        {steps.map((step, i) => {
          const number = i + 1;
          const state =
            number === current
              ? "current"
              : number < current
                ? "done"
                : "upcoming";
          return (
            <li
              key={step.label}
              data-step-state={state}
              {...(state === "current" ? { "aria-current": "step" } : {})}
              className={cn(
                "flex-1 rounded-md border px-3 py-2",
                state === "current"
                  ? "border-brand-500 bg-brand-50"
                  : "border-border-subtle bg-surface-sunken",
              )}
            >
              <p
                className={cn(
                  "text-xs font-semibold uppercase tracking-wide",
                  state === "upcoming" ? "text-ink-tertiary" : "text-brand-600",
                )}
              >
                Step {number}
              </p>
              <p
                className={cn(
                  "text-sm font-semibold",
                  state === "upcoming"
                    ? "text-ink-secondary"
                    : "text-ink-primary",
                )}
              >
                {step.label}
              </p>
              <p className="mt-0.5 text-xs text-ink-secondary">{step.detail}</p>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
