"use client";

import * as React from "react";

import {
  Card,
  CardBody,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@shield/design-system";

import type {
  AttackCoverageRow,
  AttackCoveragePatch,
  CatalogCoverageDefinition,
  CatalogTechnique,
  CoverageStatus,
} from "@/lib/attack/types";

import { StatusBadge } from "./StatusBadge";

const ALL_STATUSES: CoverageStatus[] = [
  "covered",
  "partial",
  "gap",
  "not_applicable",
];

export interface AttackTechniquePanelProps {
  technique: CatalogTechnique | null;
  coverage: AttackCoverageRow | null;
  coverageDefinitions: CatalogCoverageDefinition[];
  readOnly?: boolean;
  onPatch: (patch: AttackCoveragePatch) => void | Promise<void>;
}

export function AttackTechniquePanel({
  technique,
  coverage,
  coverageDefinitions,
  readOnly = false,
  onPatch,
}: AttackTechniquePanelProps): JSX.Element {
  if (!technique) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Technique details</CardTitle>
          <CardDescription>
            Select a technique in the matrix to set coverage.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle>
            <span className="font-mono text-sm text-ink-tertiary">
              {technique.id}
            </span>{" "}
            · {technique.name}
          </CardTitle>
          <StatusBadge status={coverage?.status ?? null} />
        </div>
        <CardDescription>
          Tactics: {technique.tactics.join(", ")}
          {technique.parent_id ? ` · parent ${technique.parent_id}` : ""}
        </CardDescription>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <div
          role="radiogroup"
          aria-label="Coverage status"
          className="flex flex-wrap gap-2"
        >
          {ALL_STATUSES.map((s) => {
            const def = coverageDefinitions.find((d) => d.status === s);
            const active = coverage?.status === s;
            return (
              <button
                key={s}
                type="button"
                role="radio"
                aria-checked={active}
                disabled={readOnly}
                title={def?.description ?? s}
                onClick={() => void onPatch({ status: active ? null : s })}
                className={[
                  "rounded-md border px-3 py-1.5 text-xs font-semibold transition",
                  active
                    ? "border-brand-500 bg-brand-500 text-ink-on-accent"
                    : "border-border bg-surface-card text-ink-secondary hover:bg-surface-sunken",
                  readOnly ? "cursor-not-allowed opacity-50" : "",
                ].join(" ")}
              >
                {def?.short_label ?? s}
              </button>
            );
          })}
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium uppercase tracking-wide text-ink-tertiary">
            Notes
          </span>
          <textarea
            key={coverage?.id ?? "no-coverage"}
            aria-label={`Notes for ${technique.id}`}
            defaultValue={coverage?.notes ?? ""}
            disabled={readOnly}
            rows={4}
            placeholder="Evidence, controls, detections, exceptions…"
            onBlur={(e) => {
              const v = e.currentTarget.value.trim();
              if (v === (coverage?.notes ?? "")) return;
              void onPatch({ notes: v });
            }}
            className="w-full rounded-md border border-border bg-surface-card p-2 text-sm text-ink-primary focus:border-brand-500 focus:outline-none"
          />
        </label>
      </CardBody>
    </Card>
  );
}
