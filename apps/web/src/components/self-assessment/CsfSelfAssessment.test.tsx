import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as csfClient from "@/lib/csf/client";
import { CSF_TIERS, csfLevelGuidance, csfTierExplainer } from "@/lib/guidance";
import type {
  CatalogTier,
  CsfAssessment,
  CsfCatalog,
  CsfInterviewQuestionnaire,
} from "@/lib/csf/types";

import { CsfSelfAssessment } from "./CsfSelfAssessment";

/**
 * S6 guidance cases for the client render. The consultant and the client see the
 * same questionnaire component, and these cases hold the two things that differ
 * for a client: the interview prompts are labelled as things to consider rather
 * than as an interview script, and a failed prompt fetch says so instead of
 * showing a question with no context.
 *
 * Deterministic and offline: the CSF client lib is fully mocked.
 */
vi.mock("@/lib/csf/client", () => ({
  CsfProxyError: class extends Error {},
  fetchCatalog: vi.fn(),
  fetchInterviewQuestionnaire: vi.fn(),
  fetchSelfAssessment: vi.fn(),
  patchSelfAssessmentAnswer: vi.fn(),
  submitSelfAssessment: vi.fn(),
}));

const SUBCATEGORY_CODE = "GV.OC-01";

function wireTiers(): CatalogTier[] {
  return CSF_TIERS.map((tier) => ({
    tier,
    short_label: `WIRE-LABEL-${tier}`,
    description: `WIRE-DESCRIPTION-${tier}`,
  }));
}

const CATALOG: CsfCatalog = {
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
  tiers: wireTiers(),
  total_subcategories: 1,
};

const ASSESSMENT: CsfAssessment = {
  id: "assess-1",
  service_id: "svc-1",
  version: 1,
  status: "draft",
  approved_at: null,
  approved_by: null,
  answers: [
    {
      id: "ans-1",
      assessment_id: "assess-1",
      subcategory_code: SUBCATEGORY_CODE,
      maturity_tier: null,
      notes: null,
      evidence_artifact_id: null,
      answered_by: null,
      answered_at: null,
    },
  ],
  client_target_tier: 3,
  client_profile: null,
};

const QUESTIONNAIRE: CsfInterviewQuestionnaire = {
  framework_key: "csf-tier-high",
  profile: null,
  questions: [
    {
      external_id: "q-1",
      section_name: "Governance",
      order_index: 1,
      stem: "Who signs off on the security policy?",
      cues: ["Named owner", "Review date"],
      csf_subcategories: [SUBCATEGORY_CODE],
    },
  ],
};

beforeEach(() => {
  vi.mocked(csfClient.fetchCatalog).mockResolvedValue(CATALOG);
  vi.mocked(csfClient.fetchSelfAssessment).mockResolvedValue(ASSESSMENT);
  vi.mocked(csfClient.fetchInterviewQuestionnaire).mockResolvedValue(
    QUESTIONNAIRE,
  );
});

describe("CsfSelfAssessment guidance for clients", () => {
  it("discloses every level with its description, explainer and worked example", async () => {
    const { container } = render(<CsfSelfAssessment serviceId="svc-1" />);

    await screen.findByText("Mission is understood");
    const details = container.querySelector<HTMLElement>(
      `[data-guidance-for="${SUBCATEGORY_CODE}"]`,
    );
    if (!details) throw new Error("no level guidance in the client render");

    const text = details.textContent ?? "";
    for (const tier of CSF_TIERS) {
      expect(text).toContain(`WIRE-DESCRIPTION-${tier}`);
      expect(text).toContain(csfTierExplainer(tier));
      expect(text).toContain(csfLevelGuidance("GV", tier).example);
    }
    expect(
      Array.from(details.querySelectorAll("dt")).map((dt) => dt.textContent),
    ).toEqual([
      "Tier 1 · WIRE-LABEL-1",
      "Tier 2 · WIRE-LABEL-2",
      "Tier 3 · WIRE-LABEL-3",
      "Tier 4 · WIRE-LABEL-4",
    ]);
  });

  it("shows the interview prompts to the client as things to consider", async () => {
    render(<CsfSelfAssessment serviceId="svc-1" />);

    expect(await screen.findByText("Consider:")).toBeInTheDocument();
    expect(
      screen.getByText("Who signs off on the security policy?"),
    ).toBeInTheDocument();
    expect(screen.getByText("Named owner")).toBeInTheDocument();
    expect(
      screen.queryByText("Interview · Governance"),
    ).not.toBeInTheDocument();
  });

  it("tells the client what a note should name", async () => {
    render(<CsfSelfAssessment serviceId="svc-1" />);

    const notes = await screen.findByLabelText(`Notes for ${SUBCATEGORY_CODE}`);
    expect(notes).toHaveAttribute(
      "placeholder",
      "Name the tool, policy, or process behind this answer: what enforces it, where it is written down, and who runs it.",
    );
  });

  it("explains the impact profile where the profile label is shown", async () => {
    // The profile line only renders for a client who has one, so the explainer
    // has to arrive with it rather than as a second, separate mechanism.
    vi.mocked(csfClient.fetchSelfAssessment).mockResolvedValue({
      ...ASSESSMENT,
      client_profile: "MOD",
    });

    const { container } = render(<CsfSelfAssessment serviceId="svc-1" />);

    await screen.findByText("Mission is understood");
    const profileLine = screen.getByText("Moderate impact");
    const details = container.querySelector<HTMLElement>(
      '[data-guidance-for="impact-profile"]',
    );
    if (!details)
      throw new Error("no impact-profile explainer in the client render");
    // Same disclosure mechanism S6 used, sitting with the line it explains.
    expect(details.querySelector("summary")?.textContent).toBe(
      "What is an impact profile?",
    );
    expect(details.textContent).toContain(
      "It is how sensitive the systems in this assessment are, on the FIPS 199 scale federal programs use. The higher the profile, the more outcomes are in scope, because a higher profile covers everything a lower one does and more. Your analyst set yours during intake, so tell them if it looks wrong.",
    );
    expect(profileLine).toBeInTheDocument();
  });

  it("shows no impact-profile explainer when the client has no profile", async () => {
    const { container } = render(<CsfSelfAssessment serviceId="svc-1" />);

    await screen.findByText("Mission is understood");
    expect(
      container.querySelector('[data-guidance-for="impact-profile"]'),
    ).toBeNull();
  });

  it("surfaces a failed prompt fetch instead of a question with no context", async () => {
    vi.mocked(csfClient.fetchInterviewQuestionnaire).mockRejectedValue(
      new Error("boom-questionnaire"),
    );

    render(<CsfSelfAssessment serviceId="svc-1" />);

    expect(await screen.findByText("boom-questionnaire")).toBeInTheDocument();
    expect(screen.queryByText("Mission is understood")).not.toBeInTheDocument();
  });
});
