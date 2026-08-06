import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AiStatusBanner } from "./AiStatusBanner";

/**
 * S8 / D-037. Two properties are under test. First, the tone: fixture mode is
 * information, a live mode that will not reach its provider is a warning, and
 * the old single warning tone conflated them. Second, the sentence explaining
 * the mode arrives on the wire from GET /admin/ai-status; the web layer keeps no
 * copy of it (the S6 rule), so every fixture here feeds a sentinel string a
 * duplicated copy could not produce.
 *
 * Deterministic + offline: fetch is stubbed per case.
 */
function mockStatus(body: Record<string, unknown>): void {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(body) }),
  ) as unknown as typeof fetch;
}

const FIXTURE_MODE = {
  mode: "fixture",
  provider: "anthropic",
  model: "claude-sentinel",
  ready: false,
  detail: "SENTINEL-fixture-sentence-served-by-the-api",
};

const LIVE_MISCONFIGURED = {
  mode: "live",
  provider: "anthropic",
  model: "",
  ready: false,
  detail: "SENTINEL-live-readiness-sentence-served-by-the-api",
};

describe("AiStatusBanner tones", () => {
  it("uses the info tone in fixture mode and does not claim AI produces nothing", async () => {
    mockStatus(FIXTURE_MODE);

    render(<AiStatusBanner />);
    const banner = await screen.findByRole("status");

    expect(banner.className).toContain("bg-status-info-bg");
    expect(banner.className).toContain("text-status-info-fg");
    expect(banner.className).toContain("border-status-info-border");
    expect(banner.className).not.toContain("status-warning");

    // The API's sentence is rendered verbatim, and the banner adds no claim of
    // its own about what fixture mode does or does not produce.
    expect(banner).toHaveTextContent(FIXTURE_MODE.detail);
    expect(banner.textContent ?? "").not.toMatch(/produce results/i);
    expect(banner.textContent ?? "").not.toMatch(/disabled/i);
    expect(banner.textContent ?? "").not.toMatch(/not live/i);
  });

  it("uses the warning tone when live mode will not reach its provider", async () => {
    mockStatus(LIVE_MISCONFIGURED);

    render(<AiStatusBanner />);
    const banner = await screen.findByRole("status");

    expect(banner.className).toContain("bg-status-warning-bg");
    expect(banner.className).toContain("text-status-warning-fg");
    expect(banner.className).toContain("border-status-warning-border");
    expect(banner.className).not.toContain("status-info");

    expect(banner).toHaveTextContent("AI is not live.");
    expect(banner).toHaveTextContent(LIVE_MISCONFIGURED.detail);
  });

  it("renders nothing when a live call will be made", async () => {
    mockStatus({ ...LIVE_MISCONFIGURED, ready: true, model: "claude-real" });

    const { container } = render(<AiStatusBanner />);
    // Let the mount fetch settle before asserting on the empty tree.
    await Promise.resolve();
    await Promise.resolve();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(container.textContent).toBe("");
  });
});
