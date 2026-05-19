"use client";

import * as React from "react";

import { Field, inputClasses, textareaClasses } from "../Field";
import {
  SERVICE_LABELS,
  type IntakeStateResponse,
  type ServiceRequestInput,
  type ServiceType,
} from "@/lib/intake/types";

export interface Step5NotesProps {
  state: IntakeStateResponse;
  serviceInputs: Record<ServiceType, ServiceRequestInput>;
  onChange: (next: Record<ServiceType, ServiceRequestInput>) => void;
}

/**
 * Stage-4 baseline: per-service notes + deadline live in the wizard's local
 * state and are bundled into POST /intake/submit. We don't PATCH partial
 * service_request rows on this step — the API only writes them at final
 * submit (see DECISIONS.md context around the spec §11 service_requests
 * lifecycle).
 */
export function Step5Notes({
  state,
  serviceInputs,
  onChange,
}: Step5NotesProps): JSX.Element {
  const picks = (state.client?.service_interests ?? []) as ServiceType[];

  if (picks.length === 0) {
    return (
      <p className="text-sm text-ink-secondary">
        You haven&apos;t picked any services yet. Go back to step 1 to choose at
        least one.
      </p>
    );
  }

  function update(svc: ServiceType, patch: Partial<ServiceRequestInput>): void {
    onChange({
      ...serviceInputs,
      [svc]: {
        ...serviceInputs[svc],
        service_type: svc,
        ...patch,
      },
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-ink-secondary">
        Add any notes or target deadlines for each service you picked. These
        ride along when you submit; you can refine them in the engagement
        workspace afterwards.
      </p>
      {picks.map((svc) => {
        const input = serviceInputs[svc] ?? { service_type: svc };
        return (
          <section
            key={svc}
            aria-labelledby={`svc-${svc}-heading`}
            className="rounded-md border border-border-subtle bg-surface-card p-4"
          >
            <h3
              id={`svc-${svc}-heading`}
              className="text-sm font-semibold text-ink-primary"
            >
              {SERVICE_LABELS[svc]}
            </h3>
            <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field
                id={`svc-${svc}-notes`}
                label="Notes"
                className="sm:col-span-2"
              >
                <textarea
                  id={`svc-${svc}-notes`}
                  defaultValue={input.notes ?? ""}
                  onBlur={(e) =>
                    update(svc, { notes: e.target.value || undefined })
                  }
                  className={textareaClasses}
                  rows={3}
                />
              </Field>
              <Field
                id={`svc-${svc}-deadline`}
                label="Target deadline"
                hint="Optional. ISO date."
              >
                <input
                  id={`svc-${svc}-deadline`}
                  type="date"
                  defaultValue={input.deadline?.slice(0, 10) ?? ""}
                  onBlur={(e) =>
                    update(svc, {
                      deadline: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    })
                  }
                  className={inputClasses}
                />
              </Field>
            </div>
          </section>
        );
      })}
    </div>
  );
}
