import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as ztClient from "@/lib/zt/client";
import type { GapAnalysis, ZtAssessment, ZtCatalog } from "@/lib/zt/types";

import { ZtWorkspace } from "./ZtWorkspace";

/**
 * S8 / D-037. The Zero Trust workspace had no AI status banner and no
 * disclosure, so a consultant running zt_score could not tell whether the
 * stages on screen came from a model or from a person, nor whether a live call
 * was even being made.
 *
 * Deterministic + offline: the ZT client lib is fully mocked and every child
 * that fetches on its own is stubbed.
 */
vi.mock("@/lib/zt/client", () => ({
  ZtProxyError: class extends Error {},
  approveAssessment: vi.fn(),
  createAssessment: vi.fn(),
  discardAssessment: vi.fn(),
  fetchCatalog: vi.fn(),
  fetchGapAnalysis: vi.fn(),
  fetchLatestAssessment: vi.fn(),
  fetchLatestDeliverable: vi.fn(),
  fetchScore: vi.fn(),
  patchAnswer: vi.fn(),
  runZtAi: vi.fn(),
}));

vi.mock("./ZtDeliverableCard", () => ({ ZtDeliverableCard: () => null }));
vi.mock("./ZtGapList", () => ({ ZtGapList: () => null }));
vi.mock("./ZtRoadmapCard", () => ({ ZtRoadmapCard: () => null }));
vi.mock("./ZtQuestionnaire", () => ({ ZtQuestionnaire: () => null }));
vi.mock("./ZtScoreCard", () => ({ ZtScoreCard: () => null }));
vi.mock("@/components/messages/MessageThread", () => ({
  MessageThread: () => null,
}));
vi.mock("@/components/admin/StaleDocsNudge", () => ({
  StaleDocsNudge: () => null,
}));
vi.mock("@/components/admin/AiPreviewButton", () => ({
  AiPreviewButton: () => null,
}));
// Sentinels, so the mount case proves placement without either child's own
// fetch or its own copy.
vi.mock("@/components/admin/AiStatusBanner", () => ({
  AiStatusBanner: () => <div data-testid="ai-status-banner" />,
}));
vi.mock("@/components/admin/HowAiWorks", () => ({
  HowAiWorks: ({ service }: { service: string }) => (
    <div data-testid="how-ai-works">{service}</div>
  ),
}));

const fetchCatalog = vi.mocked(ztClient.fetchCatalog);
const fetchLatestAssessment = vi.mocked(ztClient.fetchLatestAssessment);
const fetchScore = vi.mocked(ztClient.fetchScore);
const fetchGapAnalysis = vi.mocked(ztClient.fetchGapAnalysis);
const fetchLatestDeliverable = vi.mocked(ztClient.fetchLatestDeliverable);

const CATALOG = { pillars: [], capabilities: [] } as unknown as ZtCatalog;
const GAP = {} as unknown as GapAnalysis;

function draft(): ZtAssessment {
  return {
    id: "zt-assess-1",
    status: "draft",
    version: 1,
    answers: [],
    client_target_stage: 3,
    documents_stale: false,
  } as unknown as ZtAssessment;
}

describe("ZtWorkspace AI transparency (S8)", () => {
  it("mounts the AI status banner and puts the disclosure beside Run AI", async () => {
    fetchCatalog.mockResolvedValue(CATALOG);
    fetchLatestAssessment.mockResolvedValue(draft());
    fetchScore.mockResolvedValue({} as never);
    fetchGapAnalysis.mockResolvedValue(GAP);
    fetchLatestDeliverable.mockResolvedValue(null);

    render(
      <ZtWorkspace
        serviceId="svc-zt"
        framework="cisa_ztmm_2_0"
        serviceTitle="Atlas Zero Trust"
      />,
    );

    expect(await screen.findByTestId("ai-status-banner")).toBeInTheDocument();
    const disclosure = await screen.findByTestId("how-ai-works");
    expect(disclosure).toHaveTextContent("zt");

    // Proximity, asserted structurally: the closest ancestor shared by Run AI
    // and the disclosure must not also contain the page title, which it would
    // if the disclosure were parked elsewhere on the page.
    const runAi = screen.getByRole("button", { name: "Run AI" });
    let shared: HTMLElement | null = runAi.parentElement;
    while (shared && !shared.contains(disclosure))
      shared = shared.parentElement;
    if (!shared) {
      throw new Error("the disclosure shares no ancestor with Run AI");
    }
    expect(shared.querySelector("h1")).toBeNull();
  });
});
