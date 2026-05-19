"use client";

import * as React from "react";

import {
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  StatusPill,
} from "@shield/design-system";

import {
  approveAssessment,
  createAssessment,
  CsfProxyError,
  fetchCatalog,
  fetchGapAnalysis,
  fetchLatestAssessment,
  fetchLatestDeliverable,
  fetchScore,
  patchAnswer,
} from "@/lib/csf/client";
import type {
  CsfAnswer,
  CsfAnswerPatch,
  CsfAssessment,
  CsfCatalog,
  CsfDeliverable,
  CsfScoreSummary,
  GapAnalysis,
} from "@/lib/csf/types";

import { CsfDeliverableCard } from "./CsfDeliverableCard";
import { CsfGapList } from "./CsfGapList";
import { CsfQuestionnaire } from "./CsfQuestionnaire";
import { CsfScoreCard } from "./CsfScoreCard";

export interface CsfWorkspaceProps {
  serviceId: string;
  serviceTitle: string;
}

function describeError(err: unknown): string {
  if (err instanceof CsfProxyError) {
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

export function CsfWorkspace({
  serviceId,
  serviceTitle,
}: CsfWorkspaceProps): JSX.Element {
  const [catalog, setCatalog] = React.useState<CsfCatalog | null>(null);
  const [assessment, setAssessment] = React.useState<CsfAssessment | null>(
    null,
  );
  const [score, setScore] = React.useState<CsfScoreSummary | null>(null);
  const [gap, setGap] = React.useState<GapAnalysis | null>(null);
  const [deliverable, setDeliverable] = React.useState<CsfDeliverable | null>(
    null,
  );
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState<"create" | "approve" | null>(null);
  const [targetTier, setTargetTier] = React.useState(3);

  const answersByCode = React.useMemo(() => {
    const out: Record<string, CsfAnswer> = {};
    if (assessment) {
      for (const a of assessment.answers) {
        out[a.subcategory_code] = a;
      }
    }
    return out;
  }, [assessment]);

  const refreshScoreAndGap = React.useCallback(
    async (currentTarget: number) => {
      try {
        const [s, g] = await Promise.all([
          fetchScore(serviceId),
          fetchGapAnalysis(serviceId, { targetTier: currentTarget }),
        ]);
        setScore(s);
        setGap(g);
      } catch {
        // Non-blocking; the score/gap panels show their own loading state.
      }
    },
    [serviceId],
  );

  const initialLoad = React.useCallback(async () => {
    try {
      const cat = await fetchCatalog();
      setCatalog(cat);
    } catch (err) {
      setLoadError(describeError(err));
      return;
    }
    try {
      const a = await fetchLatestAssessment(serviceId);
      setAssessment(a);
      if (a) {
        await refreshScoreAndGap(targetTier);
        try {
          const d = await fetchLatestDeliverable(serviceId);
          setDeliverable(d);
        } catch {
          // non-blocking; deliverable card shows "not finalized yet".
        }
      }
    } catch (err) {
      setLoadError(describeError(err));
    }
  }, [serviceId, refreshScoreAndGap, targetTier]);

  React.useEffect(() => {
    void initialLoad();
  }, [initialLoad]);

  async function onCreateAssessment(): Promise<void> {
    setBusy("create");
    try {
      const next = await createAssessment(serviceId);
      setAssessment(next);
      await refreshScoreAndGap(targetTier);
    } catch (err) {
      setLoadError(describeError(err));
    } finally {
      setBusy(null);
    }
  }

  async function onAnswerUpdate(
    answerId: string,
    patch: CsfAnswerPatch,
  ): Promise<void> {
    // Optimistic update.
    setAssessment((curr) => {
      if (!curr) return curr;
      return {
        ...curr,
        answers: curr.answers.map((a) =>
          a.id === answerId ? { ...a, ...patch } : a,
        ),
      };
    });
    try {
      const next = await patchAnswer(answerId, patch);
      setAssessment((curr) => {
        if (!curr) return curr;
        return {
          ...curr,
          answers: curr.answers.map((a) => (a.id === answerId ? next : a)),
        };
      });
      // Re-fetch derived data; cheap.
      await refreshScoreAndGap(targetTier);
    } catch (err) {
      setLoadError(describeError(err));
      // Roll back by re-fetching authoritative answers.
      const a = await fetchLatestAssessment(serviceId);
      setAssessment(a);
    }
  }

  async function onApprove(): Promise<void> {
    if (!assessment) return;
    setBusy("approve");
    try {
      const next = await approveAssessment(assessment.id);
      setAssessment(next);
    } catch (err) {
      setLoadError(describeError(err));
    } finally {
      setBusy(null);
    }
  }

  async function onChangeTargetTier(next: number): Promise<void> {
    setTargetTier(next);
    if (assessment) {
      const g = await fetchGapAnalysis(serviceId, { targetTier: next });
      setGap(g);
    }
  }

  const readOnly =
    assessment?.status === "approved" || assessment?.status === "released";

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-500">
            NIST CSF 2.0 service
          </p>
          <h1 className="text-3xl font-semibold text-ink-primary">
            {serviceTitle}
          </h1>
          <p className="max-w-prose text-sm text-ink-secondary">
            Score each of the 106 subcategories against the 4-tier maturity
            model. Coverage + per-function rollup update on every edit;
            prioritized remediation gaps surface alongside the score.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {assessment ? (
            <StatusPill
              tone={
                assessment.status === "approved" ||
                assessment.status === "released"
                  ? "success"
                  : "info"
              }
              withDot
            >
              {assessment.status === "draft"
                ? `Draft v${assessment.version}`
                : assessment.status === "approved"
                  ? `Approved v${assessment.version}`
                  : `Released v${assessment.version}`}
            </StatusPill>
          ) : (
            <StatusPill tone="neutral" withDot>
              No assessment yet
            </StatusPill>
          )}
          {assessment ? (
            <button
              type="button"
              onClick={() => void onApprove()}
              disabled={busy !== null || assessment.status !== "draft"}
              className="rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-ink-on-accent hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {assessment.status === "approved"
                ? "Approved"
                : assessment.status === "released"
                  ? "Released"
                  : busy === "approve"
                    ? "Approving…"
                    : "Approve"}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => void onCreateAssessment()}
              disabled={busy !== null || !catalog}
              className="rounded-md bg-brand-500 px-4 py-2 text-sm font-semibold text-ink-on-accent hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy === "create" ? "Creating…" : "Start assessment"}
            </button>
          )}
        </div>
      </header>

      {loadError ? (
        <Card>
          <CardHeader>
            <CardTitle>Couldn&apos;t load the assessment</CardTitle>
          </CardHeader>
          <CardBody>
            <p className="text-sm text-status-danger-fg" role="alert">
              {loadError}
            </p>
          </CardBody>
        </Card>
      ) : null}

      {!catalog ? (
        <p className="text-sm text-ink-tertiary" aria-live="polite">
          Loading CSF 2.0 catalog…
        </p>
      ) : !assessment ? (
        <EmptyState
          title="No CSF assessment yet"
          description="Click 'Start assessment' to create a fresh v1 with 106 empty subcategory rows."
        />
      ) : (
        <>
          <CsfScoreCard score={score} />
          <CsfGapList
            analysis={gap}
            targetTier={targetTier}
            onChangeTargetTier={(t) => void onChangeTargetTier(t)}
          />
          <CsfDeliverableCard
            serviceId={serviceId}
            assessmentStatus={assessment.status}
            deliverable={deliverable}
            onChange={setDeliverable}
          />
          <CsfQuestionnaire
            catalog={catalog}
            answersByCode={answersByCode}
            readOnly={readOnly}
            onAnswerUpdate={onAnswerUpdate}
          />
        </>
      )}
    </div>
  );
}
