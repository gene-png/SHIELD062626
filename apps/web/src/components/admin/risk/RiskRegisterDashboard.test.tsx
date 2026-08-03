import "@testing-library/jest-dom/vitest";

import { readFileSync } from "node:fs";
// Node's own URL: the jsdom environment replaces the global one, and
// fileURLToPath rejects the object jsdom's URL returns.
import { fileURLToPath, URL as NodeUrl } from "node:url";

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as riskClient from "@/lib/risk/client";
import type { RiskEntry, RiskGate, RiskRegister } from "@/lib/risk/types";

import { RiskRegisterDashboard } from "./RiskRegisterDashboard";

/**
 * S0 theming guard for the risk dashboard. The 5x5 heatmap used to separate its
 * cells with `border-white`, a literal white that glows on any dark canvas; the
 * separation is now a gap that shows the surface behind the table. These cases
 * hold that line and the `surface-sunken` rename, both of which are invisible to
 * a screenshot but not to a second theme.
 *
 * Deterministic + offline: the risk client lib is fully mocked, so the dashboard
 * mounts against fixtures and never touches the network.
 */
vi.mock("@/lib/risk/client", () => ({
  describeRiskError: vi.fn(),
  exportRiskRegister: vi.fn(),
  fetchRiskGate: vi.fn(),
  fetchRiskRegisterLatest: vi.fn(),
  generateRiskRegister: vi.fn(),
  getActiveClientId: vi.fn(),
  getClientName: vi.fn(),
}));

const TOKENS_CSS = readFileSync(
  fileURLToPath(
    new NodeUrl(
      "../../../../../../packages/design-system/src/tokens.css",
      import.meta.url,
    ),
  ),
  "utf8",
);

const UNLOCKED: RiskGate = {
  unlocked: true,
  has_attack: true,
  has_csf: true,
  has_zt: true,
  missing: [],
};

function entry(likelihood: string, impact: string, tier: string): RiskEntry {
  return {
    id: `risk-${likelihood}-${impact}`,
    title: "Unpatched edge appliance",
    description: null,
    axis: "prevention",
    source: "attack",
    source_id: "T1190",
    linked_techniques: null,
    linked_controls: null,
    likelihood,
    impact,
    tier,
    compensating_controls: null,
    residual_risk: null,
    recommended_action: "mitigate",
    rationale: null,
    origin: "engine",
    trust: null,
  };
}

const REGISTER: RiskRegister = {
  id: "reg-1",
  client_id: "client-1",
  version: 2,
  generated_by: "admin@kentro.example",
  finalized_at: null,
  created_at: "2026-08-03T00:00:00Z",
  xlsx_artifact_id: "art-xlsx",
  pdf_artifact_id: null,
  docx_artifact_id: null,
  xlsx_filename: "risk.xlsx",
  pdf_filename: null,
  docx_filename: null,
  entries: [
    entry("very_high", "catastrophic", "critical"),
    entry("low", "minor", "low"),
  ],
  tier_counts: { critical: 1, low: 1 },
  axis_counts: { prevention: 2 },
  action_counts: { mitigate: 2 },
};

beforeEach(() => {
  vi.mocked(riskClient.getActiveClientId).mockResolvedValue("client-1");
  vi.mocked(riskClient.getClientName).mockResolvedValue("Atlas");
  vi.mocked(riskClient.fetchRiskGate).mockResolvedValue(UNLOCKED);
  vi.mocked(riskClient.fetchRiskRegisterLatest).mockResolvedValue(REGISTER);
});

describe("RiskRegisterDashboard heatmap", () => {
  it("separates cells with a gap in the surface colour, never border-white", async () => {
    render(<RiskRegisterDashboard />);
    const cell = await screen.findByTitle("Very High × Catastrophic");
    const heatmap = cell.closest("table");
    if (!heatmap) throw new Error("the heatmap cell is not inside a table");

    const cells = Array.from(heatmap.querySelectorAll("tbody td"));
    expect(cells).toHaveLength(25);
    for (const td of cells) {
      expect(td.className).not.toContain("border-white");
    }

    expect(heatmap.className).toContain("border-separate");
    expect(heatmap.className).toContain("border-spacing-px");
    expect(heatmap.className).not.toContain("border-collapse");
  });

  it("names only surface tokens that tokens.css actually declares", async () => {
    const { container } = render(<RiskRegisterDashboard />);
    await screen.findByTitle("Very High × Catastrophic");

    // A Tailwind utility naming a token that does not exist emits no CSS and
    // no build step complains, so the class silently does nothing. Every
    // surface utility the dashboard renders must resolve to a declared token.
    const used = new Set(
      Array.from(container.innerHTML.matchAll(/bg-surface-([a-z]+)/g)).map(
        (m) => m[1],
      ),
    );
    expect(used.size).toBeGreaterThan(0);
    for (const name of used) {
      expect(TOKENS_CSS).toContain(`--surface-${name}:`);
    }

    expect(
      screen.getByRole("button", { name: "Export XLSX / PDF / Word" })
        .className,
    ).toContain("hover:bg-surface-sunken");
  });
});
