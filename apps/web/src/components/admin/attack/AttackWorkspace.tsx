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
  AttackProxyError,
  createAssessment,
  fetchCatalog,
  fetchHeatmap,
  fetchLatestAssessment,
  fetchLatestDeliverable,
  patchCoverage,
} from "@/lib/attack/client";
import type {
  AttackAssessment,
  AttackCatalog,
  AttackCoveragePatch,
  AttackCoverageRow,
  AttackDeliverable,
  AttackHeatmap,
  CatalogTechnique,
  TacticHeatmapEntry,
} from "@/lib/attack/types";

import { AttackDeliverableCard } from "./AttackDeliverableCard";
import { AttackHeatmapCard } from "./AttackHeatmapCard";
import { AttackMatrix } from "./AttackMatrix";
import { AttackTechniquePanel } from "./AttackTechniquePanel";

export interface AttackWorkspaceProps {
  serviceId: string;
  serviceTitle: string;
}

function describeError(err: unknown): string {
  if (err instanceof AttackProxyError) {
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

export function AttackWorkspace({
  serviceId,
  serviceTitle,
}: AttackWorkspaceProps): JSX.Element {
  const [catalog, setCatalog] = React.useState<AttackCatalog | null>(null);
  const [assessment, setAssessment] = React.useState<AttackAssessment | null>(
    null,
  );
  const [heatmap, setHeatmap] = React.useState<AttackHeatmap | null>(null);
  const [deliverable, setDeliverable] =
    React.useState<AttackDeliverable | null>(null);
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState<"create" | "approve" | null>(null);
  const [selectedCode, setSelectedCode] = React.useState<string | null>(null);
  const [showSubs, setShowSubs] = React.useState(false);

  const coverageByCode = React.useMemo(() => {
    const out: Record<string, AttackCoverageRow> = {};
    if (assessment) {
      for (const row of assessment.coverage) {
        out[row.technique_code] = row;
      }
    }
    return out;
  }, [assessment]);

  const techniqueByCode = React.useMemo(() => {
    const out: Record<string, CatalogTechnique> = {};
    if (catalog) {
      for (const t of catalog.techniques) {
        out[t.id] = t;
      }
    }
    return out;
  }, [catalog]);

  const heatmapByTactic = React.useMemo(() => {
    const out: Record<string, TacticHeatmapEntry> = {};
    if (heatmap) {
      for (const t of heatmap.by_tactic) {
        out[t.tactic_id] = t;
      }
    }
    return out;
  }, [heatmap]);

  const refreshHeatmap = React.useCallback(async () => {
    try {
      const next = await fetchHeatmap(serviceId);
      setHeatmap(next);
    } catch {
      // non-blocking
    }
  }, [serviceId]);

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
        await refreshHeatmap();
        try {
          const d = await fetchLatestDeliverable(serviceId);
          setDeliverable(d);
        } catch {
          // non-blocking
        }
      }
    } catch (err) {
      setLoadError(describeError(err));
    }
  }, [serviceId, refreshHeatmap]);

  React.useEffect(() => {
    void initialLoad();
  }, [initialLoad]);

  async function onCreateAssessment(): Promise<void> {
    setBusy("create");
    try {
      const next = await createAssessment(serviceId);
      setAssessment(next);
      await refreshHeatmap();
    } catch (err) {
      setLoadError(describeError(err));
    } finally {
      setBusy(null);
    }
  }

  async function onPatch(
    coverageId: string,
    patch: AttackCoveragePatch,
  ): Promise<void> {
    // Optimistic.
    setAssessment((curr) => {
      if (!curr) return curr;
      return {
        ...curr,
        coverage: curr.coverage.map((c) =>
          c.id === coverageId ? { ...c, ...patch } : c,
        ),
      };
    });
    try {
      const next = await patchCoverage(coverageId, patch);
      setAssessment((curr) => {
        if (!curr) return curr;
        return {
          ...curr,
          coverage: curr.coverage.map((c) => (c.id === coverageId ? next : c)),
        };
      });
      await refreshHeatmap();
    } catch (err) {
      setLoadError(describeError(err));
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

  const readOnly =
    assessment?.status === "approved" || assessment?.status === "released";

  const selectedTechnique = selectedCode
    ? (techniqueByCode[selectedCode] ?? null)
    : null;
  const selectedCoverage = selectedCode
    ? (coverageByCode[selectedCode] ?? null)
    : null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-500">
            MITRE ATT&amp;CK Coverage
          </p>
          <h1 className="text-3xl font-semibold text-ink-primary">
            {serviceTitle}
          </h1>
          <p className="max-w-prose text-sm text-ink-secondary">
            Walk the Enterprise matrix and set defensive coverage status per
            technique. The heatmap updates live; cells that show as Gap drive
            the deliverable&apos;s remediation priorities.
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
          Loading ATT&amp;CK matrix…
        </p>
      ) : !assessment ? (
        <EmptyState
          title="No coverage assessment yet"
          description="Click 'Start assessment' to pre-seed an unscored coverage row for every technique in the Enterprise matrix."
        />
      ) : (
        <>
          <AttackHeatmapCard heatmap={heatmap} />
          <AttackDeliverableCard
            serviceId={serviceId}
            assessmentStatus={assessment.status}
            deliverable={deliverable}
            onChange={setDeliverable}
          />
          <AttackTechniquePanel
            technique={selectedTechnique}
            coverage={selectedCoverage}
            coverageDefinitions={catalog.coverage_definitions}
            readOnly={readOnly}
            onPatch={(patch) => {
              if (!selectedCoverage) return;
              return onPatch(selectedCoverage.id, patch);
            }}
          />
          <AttackMatrix
            catalog={catalog}
            coverageByCode={coverageByCode}
            heatmapByTactic={heatmapByTactic}
            onSelectTechnique={(code) => setSelectedCode(code)}
            selectedCode={selectedCode}
            showSubTechniques={showSubs}
            onToggleSubTechniques={setShowSubs}
          />
        </>
      )}
    </div>
  );
}
