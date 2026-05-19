"use client";

import * as React from "react";

import {
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
} from "@shield/design-system";

import { fetchIntake } from "@/lib/intake/client";
import {
  WIZARD_STEPS,
  type IntakeStateResponse,
  type WizardStepKey,
} from "@/lib/intake/types";

import { IntakeProgress } from "./IntakeProgress";
import { SaveStatus, type SaveState } from "./SaveStatus";

const STEP_INDEX: Record<WizardStepKey, number> = WIZARD_STEPS.reduce(
  (acc, step, i) => {
    acc[step.key] = i;
    return acc;
  },
  {} as Record<WizardStepKey, number>,
);

interface PlaceholderProps {
  stepKey: WizardStepKey;
}

function StepPlaceholder({ stepKey }: PlaceholderProps): JSX.Element {
  const step = WIZARD_STEPS.find((s) => s.key === stepKey);
  return (
    <EmptyState
      title={`Step ${(STEP_INDEX[stepKey] ?? 0) + 1}: ${step?.label ?? stepKey}`}
      description="The form for this step lands in Phase 2 stage 4. The wizard frame, navigation, progress indicator, and auto-save plumbing are wired and live; only the per-step fields are still placeholders."
    />
  );
}

export function IntakeWizard(): JSX.Element {
  const [state, setState] = React.useState<IntakeStateResponse | null>(null);
  const [step, setStep] = React.useState<WizardStepKey>("services");
  const [completed, setCompleted] = React.useState<Set<WizardStepKey>>(
    new Set(),
  );
  const [loadError, setLoadError] = React.useState<string | null>(null);
  // Stage-3 baseline: the wizard frame is wired; per-step forms in
  // stage 4 will flip this through `setSaveState` once `patchIntake`
  // returns / fails.
  const saveState: SaveState = { kind: "idle" };

  React.useEffect(() => {
    let cancelled = false;
    fetchIntake()
      .then((s) => {
        if (cancelled) return;
        setState(s);
        // When intake is already submitted, jump to review so the user can
        // verify what's on file instead of starting over.
        if (s.intake_completed_at) setStep("review");
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(
          err instanceof Error ? err.message : "Failed to load intake.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function goPrev(): void {
    const idx = STEP_INDEX[step] ?? 0;
    if (idx <= 0) return;
    setStep(WIZARD_STEPS[idx - 1].key);
  }

  function goNext(): void {
    const idx = STEP_INDEX[step] ?? 0;
    setCompleted((prev) => {
      const next = new Set(prev);
      next.add(step);
      return next;
    });
    if (idx >= WIZARD_STEPS.length - 1) return;
    setStep(WIZARD_STEPS[idx + 1].key);
  }

  const isFirst = STEP_INDEX[step] === 0;
  const isLast = STEP_INDEX[step] === WIZARD_STEPS.length - 1;

  if (loadError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Couldn&apos;t load your intake</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-status-danger-fg">{loadError}</p>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <IntakeProgress currentStep={step} completed={completed} />
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>
              {WIZARD_STEPS.find((s) => s.key === step)?.label}
            </CardTitle>
            <SaveStatus state={saveState} />
          </div>
        </CardHeader>
        <CardBody>
          {state ? (
            <StepPlaceholder stepKey={step} />
          ) : (
            <p className="text-sm text-ink-tertiary">Loading your intake…</p>
          )}
        </CardBody>
      </Card>
      <footer className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={goPrev}
          disabled={isFirst}
          className="rounded-md border border-border bg-surface-card px-4 py-2 text-sm font-semibold text-ink-primary hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-60"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={goNext}
          disabled={isLast}
          className="rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-ink-on-accent hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Next →
        </button>
      </footer>
    </div>
  );
}
