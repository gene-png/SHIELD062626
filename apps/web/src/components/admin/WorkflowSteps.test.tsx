import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as attackClient from "@/lib/attack/client";
import * as csfClient from "@/lib/csf/client";
import * as techDebtClient from "@/lib/tech_debt/client";
import * as ztClient from "@/lib/zt/client";
import type { AttackAssessmentStatus } from "@/lib/attack/types";
import type { CsfAssessmentStatus } from "@/lib/csf/types";
import type { CapabilityListStatus } from "@/lib/tech_debt/types";
import type { ZtAssessmentStatus } from "@/lib/zt/types";

import { AttackWorkspace } from "./attack/AttackWorkspace";
import { CsfWorkspace } from "./csf/CsfWorkspace";
import { TechDebtWorkspace } from "./TechDebtWorkspace";
import {
  CLIENT_ANSWER_OWNERSHIP,
  currentStepNumber,
  workflowSteps,
  WORKFLOW_SERVICES,
  WorkflowSteps,
} from "./WorkflowSteps";
import { ZtWorkspace } from "./zt/ZtWorkspace";

/**
 * S7. Two things get proved here, and the second is why this file mounts four
 * workspaces instead of one.
 *
 * 1. The status-to-step mapping, as a table keyed by each service's own status
 *    union. Keying the expectation `Record<Status, number>` makes tsc, not the
 *    author, enforce that the table is exhaustive: adding a status to the union
 *    without adding a row here fails the typecheck gate. A status no step claims
 *    must raise rather than fall back to step 1.
 * 2. The strip actually renders in all four consultant workspaces. A case that
 *    mounts one workspace proves one workspace.
 *
 * Deterministic and offline: all four service client libs are mocked and every
 * child that fetches on mount is stubbed.
 */

vi.mock("@/lib/csf/client", () => ({
  CsfProxyError: class extends Error {},
  fetchCatalog: vi.fn(),
  fetchInterviewQuestionnaire: vi.fn(),
  fetchLatestAssessment: vi.fn(),
  fetchLatestDeliverable: vi.fn(),
  fetchScore: vi.fn(),
  fetchGapAnalysis: vi.fn(),
  createAssessment: vi.fn(),
  approveAssessment: vi.fn(),
  discardAssessment: vi.fn(),
  patchAnswer: vi.fn(),
}));
vi.mock("@/lib/zt/client", () => ({
  ZtProxyError: class extends Error {},
  fetchCatalog: vi.fn(),
  fetchLatestAssessment: vi.fn(),
  fetchLatestDeliverable: vi.fn(),
  fetchScore: vi.fn(),
  fetchGapAnalysis: vi.fn(),
  createAssessment: vi.fn(),
  approveAssessment: vi.fn(),
  discardAssessment: vi.fn(),
  patchAnswer: vi.fn(),
  runZtAi: vi.fn(),
}));
vi.mock("@/lib/attack/client", () => ({
  AttackProxyError: class extends Error {},
  fetchCatalog: vi.fn(),
  fetchHeatmap: vi.fn(),
  fetchLatestAssessment: vi.fn(),
  fetchLatestDeliverable: vi.fn(),
  createAssessment: vi.fn(),
  approveAssessment: vi.fn(),
  discardAssessment: vi.fn(),
  patchCoverage: vi.fn(),
  runAttackAi: vi.fn(),
}));
vi.mock("@/lib/tech_debt/client", () => ({
  TechDebtProxyError: class extends Error {},
  fetchLatestList: vi.fn(),
  fetchOverlapAnalysis: vi.fn(),
  fetchConsolidationPlan: vi.fn(),
  fetchLatestDeliverable: vi.fn(),
  extractCapabilities: vi.fn(),
  approveCapabilityList: vi.fn(),
  discardCapabilityList: vi.fn(),
}));

vi.mock("@/components/messages/MessageThread", () => ({
  MessageThread: () => null,
}));
vi.mock("@/components/admin/StaleDocsNudge", () => ({
  StaleDocsNudge: () => null,
}));
vi.mock("@/components/admin/AiPreviewButton", () => ({
  AiPreviewButton: () => null,
}));
vi.mock("./csf/CsfScoreCard", () => ({ CsfScoreCard: () => null }));
vi.mock("./csf/CsfPlaybookPanel", () => ({ CsfPlaybookPanel: () => null }));
vi.mock("./csf/CsfGapList", () => ({ CsfGapList: () => null }));
vi.mock("./csf/CsfDeliverableCard", () => ({ CsfDeliverableCard: () => null }));
vi.mock("./csf/CsfQuestionnaire", () => ({ CsfQuestionnaire: () => null }));
vi.mock("./zt/ZtScoreCard", () => ({ ZtScoreCard: () => null }));
vi.mock("./zt/ZtGapList", () => ({ ZtGapList: () => null }));
vi.mock("./zt/ZtRoadmapCard", () => ({ ZtRoadmapCard: () => null }));
vi.mock("./zt/ZtDeliverableCard", () => ({ ZtDeliverableCard: () => null }));
vi.mock("./zt/ZtQuestionnaire", () => ({ ZtQuestionnaire: () => null }));
vi.mock("./attack/AttackDeliverableCard", () => ({
  AttackDeliverableCard: () => null,
}));
vi.mock("./attack/AttackHeatmapCard", () => ({
  AttackHeatmapCard: () => null,
}));
vi.mock("./attack/AttackMatrix", () => ({ AttackMatrix: () => null }));
vi.mock("./attack/AttackTechniquePanel", () => ({
  AttackTechniquePanel: () => null,
}));
vi.mock("./AiStatusBanner", () => ({ AiStatusBanner: () => null }));
vi.mock("./ConsolidationPlanCard", () => ({
  ConsolidationPlanCard: () => null,
}));
vi.mock("./DeliverableCard", () => ({ DeliverableCard: () => null }));
vi.mock("./EditableCapabilityTable", () => ({
  EditableCapabilityTable: () => null,
}));
vi.mock("./IntakeDocumentsPanel", () => ({ IntakeDocumentsPanel: () => null }));
vi.mock("./OverlapDashboard", () => ({ OverlapDashboard: () => null }));
vi.mock("@/components/intake/Dropzone", () => ({ Dropzone: () => null }));
vi.mock("@/components/intake/RedactionDisclosure", () => ({
  RedactionDisclosure: () => null,
}));

/**
 * Step numbers each status lands on. `Record<Status, number>` is deliberate: a
 * new member on the wire type breaks the typecheck gate until it is mapped here
 * and in WorkflowSteps.
 */
const CSF_MAPPING: Record<CsfAssessmentStatus, number> = {
  draft: 2,
  submitted: 3,
  approved: 4,
  released: 5,
  discarded: 1,
};
const ZT_MAPPING: Record<ZtAssessmentStatus, number> = {
  draft: 2,
  submitted: 3,
  approved: 4,
  released: 5,
  discarded: 1,
};
const ATTACK_MAPPING: Record<AttackAssessmentStatus, number> = {
  draft: 2,
  approved: 3,
  released: 4,
  discarded: 1,
};
const TECH_DEBT_MAPPING: Record<CapabilityListStatus, number> = {
  draft: 2,
  approved: 3,
  released: 4,
  discarded: 1,
};

const MAPPINGS = {
  csf: CSF_MAPPING,
  zt: ZT_MAPPING,
  attack: ATTACK_MAPPING,
  tech_debt: TECH_DEBT_MAPPING,
} as const;

/** The step marked current in a rendered strip, by its `Step N` eyebrow. */
function highlightedStep(container: HTMLElement): string {
  const current = container.querySelectorAll('[data-step-state="current"]');
  if (current.length !== 1) {
    throw new Error(
      `expected exactly one current step, found ${current.length}`,
    );
  }
  const eyebrow = current[0].querySelector("p");
  return eyebrow?.textContent ?? "";
}

describe("WorkflowSteps status-to-step mapping", () => {
  for (const service of WORKFLOW_SERVICES) {
    const mapping: Record<string, number> = MAPPINGS[service];

    it(`maps every ${service} status, plus the no-assessment state, to one step`, () => {
      // The pre-creation state is step 1 for every service.
      expect(currentStepNumber(service, null)).toBe(1);
      for (const [status, step] of Object.entries(mapping)) {
        expect(currentStepNumber(service, status)).toBe(step);
      }
      // Every step the strip draws is reachable from some real status, so the
      // strip never shows a phase the lifecycle cannot produce.
      const reached = new Set([
        1,
        ...Object.values(mapping).map((step) => step),
      ]);
      expect([...reached].sort((a, b) => a - b)).toEqual(
        workflowSteps(service).map((_, i) => i + 1),
      );
    });

    it(`raises rather than defaulting to step 1 on an unmapped ${service} status`, () => {
      expect(() => currentStepNumber(service, "quantum_reviewed")).toThrow(
        /defines no step for status "quantum_reviewed"/,
      );
    });

    it(`highlights the mapped step for each ${service} status`, () => {
      for (const [status, step] of Object.entries(mapping)) {
        const { container, unmount } = render(
          <WorkflowSteps service={service} status={status} />,
        );
        expect(highlightedStep(container)).toBe(`Step ${step}`);
        unmount();
      }
    });
  }
});

describe("WorkflowSteps renders in every consultant workspace", () => {
  it("renders the tech-debt strip on the current list status", async () => {
    vi.mocked(techDebtClient.fetchLatestList).mockResolvedValue({
      id: "list-1",
      status: "approved",
      version: 2,
      items: [],
    } as never);
    vi.mocked(techDebtClient.fetchOverlapAnalysis).mockResolvedValue(
      {} as never,
    );
    vi.mocked(techDebtClient.fetchConsolidationPlan).mockResolvedValue(
      null as never,
    );
    vi.mocked(techDebtClient.fetchLatestDeliverable).mockResolvedValue(
      null as never,
    );

    const { container } = render(
      <TechDebtWorkspace serviceId="svc-1" serviceTitle="Atlas Tech Debt" />,
    );

    await screen.findByText("Approved v2");
    const strip = container.querySelector<HTMLElement>(
      '[data-workflow-service="tech_debt"]',
    );
    if (!strip) throw new Error("no workflow strip in TechDebtWorkspace");
    expect(strip.textContent).toContain("Capability list");
    expect(highlightedStep(strip)).toBe("Step 3");
  });

  it("renders the CSF strip on the current assessment status", async () => {
    vi.mocked(csfClient.fetchCatalog).mockResolvedValue({
      functions: [],
      tiers: [],
      total_subcategories: 0,
    } as never);
    vi.mocked(csfClient.fetchInterviewQuestionnaire).mockResolvedValue(
      null as never,
    );
    vi.mocked(csfClient.fetchLatestAssessment).mockResolvedValue({
      id: "a-1",
      status: "submitted",
      version: 1,
      answers: [],
      documents_stale: false,
      client_target_tier: 3,
    } as never);
    vi.mocked(csfClient.fetchScore).mockResolvedValue({} as never);
    vi.mocked(csfClient.fetchGapAnalysis).mockResolvedValue({} as never);
    vi.mocked(csfClient.fetchLatestDeliverable).mockResolvedValue(
      null as never,
    );

    const { container } = render(
      <CsfWorkspace serviceId="svc-1" serviceTitle="Atlas CSF" />,
    );

    await screen.findByText("Submitted v1");
    const strip = container.querySelector<HTMLElement>(
      '[data-workflow-service="csf"]',
    );
    if (!strip) throw new Error("no workflow strip in CsfWorkspace");
    expect(strip.textContent).toContain("Client answers");
    expect(highlightedStep(strip)).toBe("Step 3");
  });

  it("renders the ZT strip on the current assessment status", async () => {
    vi.mocked(ztClient.fetchCatalog).mockResolvedValue({
      pillars: [],
      stages: [],
    } as never);
    vi.mocked(ztClient.fetchLatestAssessment).mockResolvedValue({
      id: "a-1",
      status: "draft",
      version: 1,
      answers: [],
      documents_stale: false,
      client_target_stage: 3,
    } as never);
    vi.mocked(ztClient.fetchScore).mockResolvedValue({} as never);
    vi.mocked(ztClient.fetchGapAnalysis).mockResolvedValue({} as never);
    vi.mocked(ztClient.fetchLatestDeliverable).mockResolvedValue(null as never);

    const { container } = render(
      <ZtWorkspace
        serviceId="svc-1"
        framework="cisa_ztmm_2_0"
        serviceTitle="Atlas ZT"
      />,
    );

    await screen.findByText("Draft v1");
    const strip = container.querySelector<HTMLElement>(
      '[data-workflow-service="zt"]',
    );
    if (!strip) throw new Error("no workflow strip in ZtWorkspace");
    expect(strip.textContent).toContain("Scoring");
    expect(highlightedStep(strip)).toBe("Step 2");
  });

  it("renders the ATT&CK strip on step 1 before an assessment exists", async () => {
    vi.mocked(attackClient.fetchCatalog).mockResolvedValue({
      techniques: [],
      coverage_definitions: [],
    } as never);
    vi.mocked(attackClient.fetchLatestAssessment).mockResolvedValue(
      null as never,
    );

    const { container } = render(
      <AttackWorkspace serviceId="svc-1" serviceTitle="Atlas ATT&CK" />,
    );

    await screen.findByText("No assessment yet");
    const strip = container.querySelector<HTMLElement>(
      '[data-workflow-service="attack"]',
    );
    if (!strip) throw new Error("no workflow strip in AttackWorkspace");
    expect(strip.textContent).toContain("Coverage");
    expect(highlightedStep(strip)).toBe("Step 1");
  });
});

describe("client-answer ownership copy", () => {
  it("states who reviews, who sees the outcome, and who owns the quality", () => {
    expect(CLIENT_ANSWER_OWNERSHIP).toBe(
      "The client answers what they can. You review and edit those answers here, and you own the quality of what ships. They see the outcome, not this workspace.",
    );
  });

  it("renders in the CSF workspace whatever the status, and keeps the submitted banner", async () => {
    vi.mocked(csfClient.fetchCatalog).mockResolvedValue({
      functions: [],
      tiers: [],
      total_subcategories: 0,
    } as never);
    vi.mocked(csfClient.fetchInterviewQuestionnaire).mockResolvedValue(
      null as never,
    );
    vi.mocked(csfClient.fetchLatestAssessment).mockResolvedValue({
      id: "a-1",
      status: "submitted",
      version: 1,
      answers: [],
      documents_stale: false,
      client_target_tier: 3,
    } as never);
    vi.mocked(csfClient.fetchScore).mockResolvedValue({} as never);
    vi.mocked(csfClient.fetchGapAnalysis).mockResolvedValue({} as never);
    vi.mocked(csfClient.fetchLatestDeliverable).mockResolvedValue(
      null as never,
    );

    render(<CsfWorkspace serviceId="svc-1" serviceTitle="Atlas CSF" />);

    expect(
      await screen.findByText(CLIENT_ANSWER_OWNERSHIP),
    ).toBeInTheDocument();
    // The S6-era submitted banner is not replaced by the ownership line.
    expect(
      screen.getByText("Client self-assessment submitted."),
    ).toBeInTheDocument();
  });

  it("renders in the ZT workspace before any assessment exists", async () => {
    vi.mocked(ztClient.fetchCatalog).mockResolvedValue({
      pillars: [],
      stages: [],
    } as never);
    vi.mocked(ztClient.fetchLatestAssessment).mockResolvedValue(null as never);

    render(
      <ZtWorkspace
        serviceId="svc-1"
        framework="dod_ztra"
        serviceTitle="Atlas ZT"
      />,
    );

    expect(
      await screen.findByText(CLIENT_ANSWER_OWNERSHIP),
    ).toBeInTheDocument();
  });
});
