"use client";
import { csfLevelGuidance } from "@/lib/guidance";
import type { CatalogTier } from "@/lib/csf/types";

import type { JSX } from "react";

export interface CsfMaturityReferenceProps {
  /** Tier ladder as the API sent it, built from TIER_DEFINITIONS. */
  tiers: CatalogTier[];
  /** CSF function the question belongs to, which picks the worked examples. */
  functionCode: string;
  /** Subcategory the disclosure sits under, used to address it in tests and e2e. */
  subcategoryCode: string;
}

/**
 * Per-question answering aid for a CSF maturity question (S6).
 *
 * Label and full description for every tier come from the `tiers` payload, so
 * this component never restates NIST wording. On top of each it renders the
 * plain-language explainer and the worked example for the function being
 * answered, which is what makes an unfamiliar question answerable without a
 * consultant on the call.
 *
 * Shared by the consultant workspace and the client self-assessment, because
 * both render `CsfQuestionnaire`.
 */
export function CsfMaturityReference({
  tiers,
  functionCode,
  subcategoryCode,
}: CsfMaturityReferenceProps): JSX.Element {
  if (tiers.length === 0) {
    // An empty ladder would render a disclosure that reads as "no guidance
    // exists". Say what actually went wrong instead.
    throw new Error(
      `[CsfMaturityReference] the catalog carried no tier definitions, so the levels for ${subcategoryCode} cannot be explained`,
    );
  }
  return (
    <details className="mt-2" data-guidance-for={subcategoryCode}>
      <summary className="cursor-pointer text-xs font-medium text-brand-600 hover:text-brand-700">
        What do these levels mean?
      </summary>
      <dl className="mt-2 flex flex-col gap-2.5 rounded-md border border-border-subtle bg-surface-sunken p-2.5">
        {tiers.map((tier) => {
          const { explainer, example } = csfLevelGuidance(
            functionCode,
            tier.tier,
          );
          return (
            <div key={tier.tier}>
              <dt className="text-xs font-semibold text-ink-primary">
                Tier {tier.tier} · {tier.short_label}
              </dt>
              <dd className="mt-0.5 text-xs text-ink-secondary">
                <p>{tier.description}</p>
                <p className="mt-1">{explainer}</p>
                <p className="mt-1">
                  <span className="font-semibold text-ink-primary">
                    For example:
                  </span>{" "}
                  {example}
                </p>
              </dd>
            </div>
          );
        })}
      </dl>
    </details>
  );
}
