import type { JSX } from "react";

/**
 * Consultant-facing disclosure of what AI does and does not do in a service
 * (D-037). It sits beside Run AI so the answer is where the question is asked.
 *
 * Every sentence has to hold in fixture mode and in live mode, and none of it
 * may imply a person has checked a drafted value: no acceptance state exists to
 * back that up (D-035). This surface is admin-only; the client's screen says
 * nothing about AI.
 */
export const HOW_AI_WORKS_SERVICES = [
  "tech_debt",
  "attack",
  "csf",
  "zt",
] as const;

export type HowAiWorksService = (typeof HOW_AI_WORKS_SERVICES)[number];

interface ServiceCopy {
  /** The AI job purpose, so the disclosure matches the audit log. */
  purpose: string;
  drafts: string;
  computes: string;
}

const COPY: Record<HowAiWorksService, ServiceCopy> = {
  tech_debt: {
    purpose: "extract.capabilities",
    drafts:
      "A structured capability list read out of the inventory file you upload: vendor, product, category, annual cost, license count, and a confidence percentage per row.",
    computes:
      "Spend totals, category counts, the overlap view, and the consolidation plan are computed from the rows you save.",
  },
  attack: {
    purpose: "mitre_map",
    drafts:
      "A coverage status per technique, plus the detection, prevention, and response tooling behind it, read from this client's Tech Debt capability list. Locked rows are left untouched.",
    computes:
      "The tactic heatmap, the coverage counts, and the deliverable's remediation priorities are computed from the coverage rows you save.",
  },
  csf: {
    purpose: "csf_score",
    drafts:
      "Dimension scores for the 106 subcategories, against the tiers this client uses.",
    computes:
      "Coverage, the per-function rollup, and the prioritized gap list are computed by the Playbook engine from the answers you save.",
  },
  zt: {
    purpose: "zt_score",
    drafts:
      "A current and target maturity stage per capability on this framework's scale, plus a narrative per pillar. Locked rows are left untouched.",
    computes:
      "The per-pillar rollup, the gap list, and the roadmap are computed from the answers you save.",
  },
};

const REDACTION =
  "Every prompt passes through one redactor before it leaves the API. Emails, phone numbers, government identifiers, and personal names are replaced with placeholders; strict mode also replaces street addresses and the client's own name. Only counts of what was removed are recorded, never the text.";

const MODES =
  "In fixture mode, Run AI returns a fixed offline draft for the purpose and no request leaves this deployment. In live mode the redacted prompt goes to the configured provider. The status banner at the top of this page names the current mode whenever no live call will be made.";

const SIGN_OFF =
  "A drafted value carries no sign-off. Approving the assessment records that you approved that version, not that you read each drafted field.";

function Row({
  term,
  children,
}: {
  term: string;
  children: string;
}): JSX.Element {
  return (
    <div>
      <dt className="font-semibold text-ink-primary">{term}</dt>
      <dd className="mt-0.5 text-ink-secondary">{children}</dd>
    </div>
  );
}

export function HowAiWorks({
  service,
}: {
  service: HowAiWorksService;
}): JSX.Element {
  const copy = COPY[service];
  return (
    <div
      role="group"
      aria-label="How AI is used here"
      className="rounded-md border border-border-subtle bg-surface-sunken px-4 py-3 text-sm"
    >
      <details>
        <summary className="cursor-pointer font-semibold text-ink-primary">
          How AI is used here ({copy.purpose})
        </summary>
        <dl className="mt-3 flex flex-col gap-3">
          <Row term="What AI drafts here">{copy.drafts}</Row>
          <Row term="What code computes">{copy.computes}</Row>
          <Row term="Before a prompt leaves">{REDACTION}</Row>
          <Row term="Fixture mode and live mode">{MODES}</Row>
        </dl>
        <p className="mt-3 text-ink-secondary">{SIGN_OFF}</p>
      </details>
    </div>
  );
}
