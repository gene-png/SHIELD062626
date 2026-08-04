import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CSF_TIERS, csfLevelGuidance, csfTierExplainer } from "@/lib/guidance";
import type {
  CatalogTier,
  CsfAnswer,
  CsfCatalog,
  CsfInterviewQuestion,
} from "@/lib/csf/types";

import { CsfQuestionnaire } from "./CsfQuestionnaire";

/**
 * S6 guidance cases for the consultant render of the questionnaire.
 *
 * The tier ladder arrives as sentinel text rather than the real NIST wording on
 * purpose. Every label and description on screen has to be the one the API sent,
 * so a copy of `TIER_DEFINITIONS` reintroduced anywhere in the web layer fails
 * these cases instead of quietly diverging from the backend.
 */

const SUBCATEGORY_CODE = "GV.OC-01";

function wireTiers(): CatalogTier[] {
  return CSF_TIERS.map((tier) => ({
    tier,
    short_label: `WIRE-LABEL-${tier}`,
    description: `WIRE-DESCRIPTION-${tier}`,
  }));
}

function catalog(tiers: CatalogTier[] = wireTiers()): CsfCatalog {
  return {
    functions: [
      {
        code: "GV",
        name: "Govern",
        purpose: "Establish and monitor the cybersecurity risk strategy.",
        categories: [
          {
            code: "GV.OC",
            function: "GV",
            name: "Organizational Context",
            purpose: "The circumstances around the risk decisions.",
            subcategories: [
              {
                code: SUBCATEGORY_CODE,
                function: "GV",
                category: "GV.OC",
                name: "Mission is understood",
                outcome: "The organizational mission is understood.",
                min_profile: "LOW",
              },
            ],
          },
        ],
      },
    ],
    tiers,
    total_subcategories: 1,
  };
}

const ANSWER: Record<string, CsfAnswer> = {
  [SUBCATEGORY_CODE]: {
    id: "ans-1",
    assessment_id: "assess-1",
    subcategory_code: SUBCATEGORY_CODE,
    maturity_tier: null,
    notes: null,
    evidence_artifact_id: null,
    answered_by: null,
    answered_at: null,
  },
};

const PROMPT: CsfInterviewQuestion = {
  external_id: "q-1",
  section_name: "Governance",
  order_index: 1,
  stem: "Who signs off on the security policy?",
  cues: ["Named owner", "Review date"],
  csf_subcategories: [SUBCATEGORY_CODE],
};

function disclosure(container: HTMLElement): HTMLElement {
  const found = container.querySelector<HTMLElement>(
    `[data-guidance-for="${SUBCATEGORY_CODE}"]`,
  );
  if (!found) throw new Error("no level guidance rendered for the question");
  return found;
}

describe("CsfQuestionnaire level guidance (consultant render)", () => {
  it("discloses every level with its description, explainer and worked example", () => {
    const { container } = render(
      <CsfQuestionnaire
        catalog={catalog()}
        answersByCode={ANSWER}
        onAnswerUpdate={() => {}}
      />,
    );

    expect(
      screen.getAllByText("What do these levels mean?").length,
    ).toBeGreaterThan(0);

    const text = disclosure(container).textContent ?? "";
    for (const tier of CSF_TIERS) {
      expect(text).toContain(`WIRE-DESCRIPTION-${tier}`);
      expect(text).toContain(csfTierExplainer(tier));
      expect(text).toContain(csfLevelGuidance("GV", tier).example);
    }
  });

  it("takes every level label from the catalog payload, never a local copy", () => {
    const { container } = render(
      <CsfQuestionnaire
        catalog={catalog()}
        answersByCode={ANSWER}
        onAnswerUpdate={() => {}}
      />,
    );

    const headings = Array.from(
      disclosure(container).querySelectorAll("dt"),
    ).map((dt) => dt.textContent);
    expect(headings).toEqual([
      "Tier 1 · WIRE-LABEL-1",
      "Tier 2 · WIRE-LABEL-2",
      "Tier 3 · WIRE-LABEL-3",
      "Tier 4 · WIRE-LABEL-4",
    ]);
  });

  it("refuses to render a disclosure when the catalog carries no tiers", () => {
    // Fail loudly: an empty ladder would read as "no guidance exists".
    expect(() =>
      render(
        <CsfQuestionnaire
          catalog={catalog([])}
          answersByCode={ANSWER}
          onAnswerUpdate={() => {}}
        />,
      ),
    ).toThrow(/no tier definitions/);
  });

  it("tells the consultant what a note should name", () => {
    render(
      <CsfQuestionnaire
        catalog={catalog()}
        answersByCode={ANSWER}
        onAnswerUpdate={() => {}}
      />,
    );

    const notes = screen.getByLabelText(`Notes for ${SUBCATEGORY_CODE}`);
    expect(notes).toHaveAttribute(
      "placeholder",
      "Name the tool, policy, or process behind this answer: what enforces it, where it is written down, and who runs it.",
    );
  });

  it("keeps the Interview label on the consultant render", () => {
    render(
      <CsfQuestionnaire
        catalog={catalog()}
        answersByCode={ANSWER}
        questionsByCode={{ [SUBCATEGORY_CODE]: [PROMPT] }}
        onAnswerUpdate={() => {}}
      />,
    );

    expect(screen.getByText("Interview · Governance")).toBeInTheDocument();
    expect(screen.queryByText("Consider:")).not.toBeInTheDocument();
  });
});
