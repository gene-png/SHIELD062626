import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ZT_STAGES, ztStageGuidance } from "@/lib/guidance";
import type {
  CatalogStage,
  ZtAnswer,
  ZtCatalog,
  ZtFramework,
} from "@/lib/zt/types";

import { ZtQuestionnaire } from "./ZtQuestionnaire";

/**
 * S6 guidance cases for the Zero Trust questionnaire, run against both ladders:
 * CISA ZTMM 2.0 has four stages, DoD ZTRA has three. Stage labels and
 * descriptions are sentinels here, so any stage text the web layer sources from
 * a local copy of `CISA_STAGES` or `DOD_STAGES` instead of the catalog payload
 * fails these cases.
 */

const CAPABILITY_CODE = "ID-01";

function wireStages(framework: ZtFramework): CatalogStage[] {
  return ZT_STAGES[framework].map((stage) => ({
    stage,
    label: `WIRE-STAGE-${stage}`,
    description: `WIRE-STAGE-DESCRIPTION-${stage}`,
  }));
}

function catalog(framework: ZtFramework): ZtCatalog {
  return {
    framework,
    pillars: [
      {
        code: "ID",
        name: "Identity",
        purpose: "Verify who is asking before anything else.",
        capabilities: [
          {
            code: CAPABILITY_CODE,
            pillar_code: "ID",
            name: "User inventory",
            outcome: "Every account is known and attributed to a person.",
          },
        ],
      },
    ],
    stages: wireStages(framework),
    total_capabilities: 1,
  };
}

const ANSWER: Record<string, ZtAnswer> = {
  [CAPABILITY_CODE]: {
    id: "ans-1",
    assessment_id: "assess-1",
    capability_code: CAPABILITY_CODE,
    maturity_stage: null,
    target_stage: null,
    notes: null,
    evidence_artifact_id: null,
    answered_by: null,
    answered_at: null,
  },
};

function disclosure(container: HTMLElement): HTMLElement {
  const found = container.querySelector<HTMLElement>(
    `[data-guidance-for="${CAPABILITY_CODE}"]`,
  );
  if (!found) throw new Error("no stage guidance rendered for the capability");
  return found;
}

describe.each<ZtFramework>(["cisa_ztmm_2_0", "dod_ztra"])(
  "ZtQuestionnaire stage guidance (%s)",
  (framework) => {
    it("discloses every stage the framework offers, with its explainer and worked example", () => {
      const { container } = render(
        <ZtQuestionnaire
          catalog={catalog(framework)}
          answersByCode={ANSWER}
          onAnswerUpdate={() => {}}
        />,
      );

      const text = disclosure(container).textContent ?? "";
      for (const stage of ZT_STAGES[framework]) {
        const guidance = ztStageGuidance(framework, stage);
        expect(text).toContain(`WIRE-STAGE-DESCRIPTION-${stage}`);
        expect(text).toContain(guidance.explainer);
        expect(text).toContain(guidance.example);
      }
    });

    it("takes every stage label from the catalog payload, never a local copy", () => {
      const { container } = render(
        <ZtQuestionnaire
          catalog={catalog(framework)}
          answersByCode={ANSWER}
          onAnswerUpdate={() => {}}
        />,
      );

      const headings = Array.from(
        disclosure(container).querySelectorAll("dt"),
      ).map((dt) => dt.textContent);
      expect(headings).toEqual(
        ZT_STAGES[framework].map(
          (stage) => `Stage ${stage} · WIRE-STAGE-${stage}`,
        ),
      );
    });

    it("tells the consultant what a note should name", () => {
      render(
        <ZtQuestionnaire
          catalog={catalog(framework)}
          answersByCode={ANSWER}
          onAnswerUpdate={() => {}}
        />,
      );

      expect(
        screen.getByLabelText(`Notes for ${CAPABILITY_CODE}`),
      ).toHaveAttribute(
        "placeholder",
        "Name the tool, policy, or process behind this answer: what enforces it, where it is written down, and who runs it.",
      );
    });
  },
);

describe("ZtQuestionnaire stage guidance", () => {
  it("refuses to render a disclosure when the catalog carries no stages", () => {
    // Fail loudly: an empty ladder would read as "no guidance exists".
    expect(() =>
      render(
        <ZtQuestionnaire
          catalog={{ ...catalog("cisa_ztmm_2_0"), stages: [] }}
          answersByCode={ANSWER}
          onAnswerUpdate={() => {}}
        />,
      ),
    ).toThrow(/no stage definitions/);
  });
});
