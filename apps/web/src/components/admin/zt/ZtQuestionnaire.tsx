"use client";

import * as React from "react";

import type {
  CatalogPillar,
  ZtAnswer,
  ZtAnswerPatch,
  ZtCatalog,
} from "@/lib/zt/types";

import { ZtStagePicker } from "./ZtStagePicker";

export interface ZtQuestionnaireProps {
  catalog: ZtCatalog;
  answersByCode: Record<string, ZtAnswer>;
  readOnly?: boolean;
  onAnswerUpdate: (
    answerId: string,
    patch: ZtAnswerPatch,
  ) => void | Promise<void>;
}

function PillarTabBar({
  pillars,
  active,
  onChange,
}: {
  pillars: CatalogPillar[];
  active: string;
  onChange: (code: string) => void;
}): JSX.Element {
  return (
    <div
      role="tablist"
      aria-label="Zero Trust pillars"
      className="flex flex-wrap gap-1 border-b border-border-subtle"
    >
      {pillars.map((p) => {
        const selected = p.code === active;
        return (
          <button
            key={p.code}
            role="tab"
            type="button"
            aria-selected={selected}
            id={`zt-tab-${p.code}`}
            aria-controls={`zt-panel-${p.code}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(p.code)}
            className={[
              "rounded-t-md px-3 py-2 text-sm font-semibold border-b-2 -mb-px transition",
              selected
                ? "border-brand-500 text-ink-primary"
                : "border-transparent text-ink-tertiary hover:text-ink-secondary",
            ].join(" ")}
          >
            {p.code} · {p.name}
          </button>
        );
      })}
    </div>
  );
}

export function ZtQuestionnaire({
  catalog,
  answersByCode,
  readOnly = false,
  onAnswerUpdate,
}: ZtQuestionnaireProps): JSX.Element {
  const [active, setActive] = React.useState<string>(
    catalog.pillars[0]?.code ?? "",
  );

  const activePillar = catalog.pillars.find((p) => p.code === active);

  return (
    <section
      aria-labelledby="zt-questionnaire-heading"
      className="flex flex-col gap-4"
    >
      <h2
        id="zt-questionnaire-heading"
        className="text-lg font-semibold text-ink-primary"
      >
        Zero Trust questionnaire
      </h2>
      {catalog.framework === "cisa_ztmm_2_0" ? (
        <p className="text-sm text-ink-secondary">
          The{" "}
          <a
            href="https://www.cisa.gov/sites/default/files/2023-04/zero_trust_maturity_model_v2_508.pdf#page=9"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-brand-600 underline hover:text-brand-700"
          >
            CISA Zero Trust Maturity Model v2 (PDF, opens at page 9)
          </a>{" "}
          defines each pillar and what each maturity stage looks like. Keep it
          open in another tab while you answer.
        </p>
      ) : null}
      <PillarTabBar
        pillars={catalog.pillars}
        active={active}
        onChange={setActive}
      />
      {activePillar ? (
        <div
          role="tabpanel"
          id={`zt-panel-${activePillar.code}`}
          aria-labelledby={`zt-tab-${activePillar.code}`}
          className="flex flex-col gap-4"
        >
          <p className="text-sm text-ink-secondary">{activePillar.purpose}</p>
          <ul className="flex flex-col gap-3">
            {activePillar.capabilities.map((cap) => {
              const ans = answersByCode[cap.code];
              if (!ans) return null;
              return (
                <li
                  key={cap.code}
                  className="rounded-md border border-border-subtle bg-surface-card p-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-mono text-ink-tertiary">
                        {cap.code}
                      </p>
                      <p className="text-sm font-medium text-ink-primary">
                        {cap.name}
                      </p>
                      <p className="mt-1 text-sm text-ink-secondary">
                        {cap.outcome}
                      </p>
                    </div>
                    <ZtStagePicker
                      value={ans.maturity_stage}
                      stages={catalog.stages}
                      disabled={readOnly}
                      ariaLabel={`Maturity stage for ${cap.code}`}
                      onChange={(next) => {
                        void onAnswerUpdate(ans.id, { maturity_stage: next });
                      }}
                    />
                  </div>
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs font-medium text-ink-tertiary hover:text-ink-secondary">
                      Notes {ans.notes ? "·" : ""}{" "}
                      {ans.notes ? (
                        <span className="font-normal text-ink-secondary">
                          {ans.notes.length > 60
                            ? `${ans.notes.slice(0, 60)}…`
                            : ans.notes}
                        </span>
                      ) : null}
                    </summary>
                    <textarea
                      aria-label={`Notes for ${cap.code}`}
                      defaultValue={ans.notes ?? ""}
                      disabled={readOnly}
                      rows={3}
                      onBlur={(e) => {
                        const v = e.currentTarget.value.trim();
                        if (v === (ans.notes ?? "")) return;
                        void onAnswerUpdate(ans.id, { notes: v });
                      }}
                      className="mt-2 w-full rounded-md border border-border bg-surface-card p-2 text-sm text-ink-primary focus:border-brand-500 focus:outline-none"
                      placeholder="Evidence, references, exceptions…"
                    />
                  </details>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
