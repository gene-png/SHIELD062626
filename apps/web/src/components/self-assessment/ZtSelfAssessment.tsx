"use client";

import * as React from "react";

import { Card, CardBody, CardHeader, CardTitle, cn } from "@shield/design-system";

import { SelfAssessmentSubmitted } from "@/components/self-assessment/SelfAssessmentSubmitted";
import { ZtQuestionnaire } from "@/components/admin/zt/ZtQuestionnaire";
import {
  fetchCatalog,
  fetchSelfAssessment,
  patchSelfAssessmentAnswer,
  submitSelfAssessment,
} from "@/lib/zt/client";
import type {
  ZtAnswer,
  ZtAnswerPatch,
  ZtAssessment,
  ZtCatalog,
  ZtFramework,
} from "@/lib/zt/types";

export function ZtSelfAssessment({
  serviceId,
  framework,
}: {
  serviceId: string;
  framework: ZtFramework;
}): JSX.Element {
  const [catalog, setCatalog] = React.useState<ZtCatalog | null>(null);
  const [assessment, setAssessment] = React.useState<ZtAssessment | null>(null);
  const [target, setTarget] = React.useState<number>(3);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const [submitted, setSubmitted] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    Promise.all([fetchCatalog(framework), fetchSelfAssessment(serviceId)])
      .then(([cat, a]) => {
        if (cancelled) return;
        setCatalog(cat);
        setAssessment(a);
        if (a?.client_target_stage) setTarget(a.client_target_stage);
        if (a && a.status !== "draft") setSubmitted(true);
      })
      .catch((err) => {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : "Failed to load.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [serviceId, framework]);

  const answersByCode = React.useMemo(() => {
    const map: Record<string, ZtAnswer> = {};
    for (const a of assessment?.answers ?? []) map[a.capability_code] = a;
    return map;
  }, [assessment]);

  async function onAnswerUpdate(
    answerId: string,
    patch: ZtAnswerPatch,
  ): Promise<void> {
    setAssessment((curr) =>
      curr
        ? {
            ...curr,
            answers: curr.answers.map((a) =>
              a.id === answerId ? ({ ...a, ...patch } as ZtAnswer) : a,
            ),
          }
        : curr,
    );
    try {
      const updated = await patchSelfAssessmentAnswer(answerId, patch);
      setAssessment((curr) =>
        curr
          ? {
              ...curr,
              answers: curr.answers.map((a) =>
                a.id === answerId ? updated : a,
              ),
            }
          : curr,
      );
    } catch {
      // Best-effort optimistic save; a reload reconciles if it failed.
    }
  }

  async function onSubmit(): Promise<void> {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const next = await submitSelfAssessment(serviceId, {
        target_stage: target,
      });
      setAssessment(next);
      setSubmitted(true);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submit failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Couldn&apos;t load your self-assessment</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-status-danger-fg">{loadError}</p>
        </CardBody>
      </Card>
    );
  }
  if (!catalog || !assessment) {
    return (
      <p className="text-sm text-ink-tertiary">Loading your self-assessment…</p>
    );
  }
  if (submitted) {
    return <SelfAssessmentSubmitted />;
  }

  const answeredCount = assessment.answers.filter(
    (a) => a.maturity_stage !== null,
  ).length;
  const total = assessment.answers.length;
  const targetStages = catalog.stages.filter((s) => s.stage >= 2);

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>1. Your maturity target</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-3">
          <p className="text-sm text-ink-secondary">
            Pick the maturity stage you want to reach. We measure the gap
            between your answers below and this goal to recommend what to
            prioritize.
          </p>
          <div className="flex flex-wrap gap-2">
            {targetStages.map((s) => (
              <button
                key={s.stage}
                type="button"
                onClick={() => setTarget(s.stage)}
                aria-pressed={target === s.stage}
                className={cn(
                  "max-w-xs rounded-md border px-4 py-2 text-left text-sm transition-colors",
                  target === s.stage
                    ? "border-brand-500 bg-brand-50 text-ink-primary"
                    : "border-border bg-surface-card text-ink-secondary hover:border-border-strong",
                )}
              >
                <span className="block font-semibold">
                  Stage {s.stage} · {s.label}
                </span>
                <span className="block text-xs text-ink-tertiary">
                  {s.description}
                </span>
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle>2. Self-assessment</CardTitle>
            <span className="text-sm text-ink-tertiary">
              {answeredCount} of {total} answered
            </span>
          </div>
        </CardHeader>
        <CardBody>
          <p className="mb-4 text-sm text-ink-secondary">
            For each capability, choose the stage that best reflects your
            organization today. Answer what you can — your consultant reviews
            everything before anything is processed.
          </p>
          <ZtQuestionnaire
            catalog={catalog}
            answersByCode={answersByCode}
            onAnswerUpdate={onAnswerUpdate}
          />
        </CardBody>
      </Card>

      {submitError ? (
        <div
          role="alert"
          className="rounded-md border border-status-danger-border bg-status-danger-bg px-4 py-3 text-sm text-status-danger-fg"
        >
          {submitError}
        </div>
      ) : null}

      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-ink-tertiary">
          You can submit now and your consultant will follow up if anything
          needs more detail.
        </p>
        <button
          type="button"
          onClick={() => void onSubmit()}
          disabled={submitting}
          className="rounded-md bg-brand-500 px-5 py-2.5 text-sm font-semibold text-ink-on-accent hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Submitting…" : "Submit for review"}
        </button>
      </div>
    </div>
  );
}
