import { expect, test } from "@playwright/test";

import { ADMIN_EMAIL, ADMIN_PASSWORD, signIn } from "../helpers/auth";

/**
 * SMOKE_TEST.md section 4 (T6): the Tech Debt admin workspace.
 *
 * Admin opens the seeded Atlas Tech Debt service, uploads an inventory CSV, and
 * the fixture-mode AI (T6b) extracts a fresh DRAFT capability list — one row per
 * CSV line, each stamped with an AI confidence percentage. We assert the spec's
 * two contract points:
 *   1. The dashboard summarizes the extracted list (capability count, annual
 *      cost, categories, to-consolidate/cut, low-confidence counts).
 *   2. Editing any cell clears that row's AI-confidence badge and re-labels it
 *      "Human-curated" (the API sets confidence_pct = NULL on a human edit).
 *
 * The seeded capability list is RELEASED/read-only, so each extraction layers a
 * new editable DRAFT version on top; fetchLatestList always returns our fresh
 * four-row draft, keeping the "AI 60%" row deterministic across re-runs.
 */

// Seeded Atlas Defense "Tech Debt Review" service (scripts/seed_demo.py).
const TECH_DEBT_SERVICE_ID = "3c73a6cb-802a-4fd8-937b-69d9af0fe6de";

// A tiny inventory. The fixture extractor reads the redacted rows and stamps a
// deterministic confidence per row (60, 70, 80, 90) — so exactly one row is
// "AI 60%", which we edit to prove the badge clears.
const INVENTORY_CSV =
  "name,vendor,category,annual_cost_usd,license_count\n" +
  "CrowdStrike Falcon,CrowdStrike,EDR,120000,500\n" +
  "Splunk Enterprise,Splunk,SIEM,200000,100\n" +
  "Okta,Okta,IAM,60000,500\n" +
  "Tenable Nessus,Tenable,VulnScan,40000,50\n";

test("tech-debt extract builds the dashboard, and editing a cell clears the AI-confidence badge", async ({
  page,
}) => {
  // Upload + extraction + auto-save PATCH against a next-dev server that is
  // also serving the other smoke specs; requests can queue for tens of
  // seconds, so triple the budget.
  test.slow();
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await page.goto(`/admin/services/${TECH_DEBT_SERVICE_ID}/tech-debt`);

  // EnsureActiveClient aligns the active tenant to Atlas before the workspace
  // renders its header.
  await expect(
    page.getByRole("heading", { name: "Tech Debt Review" }),
  ).toBeVisible({ timeout: 30000 });

  // Upload the inventory via the hidden Dropzone file input. The upload triggers
  // a fixture-mode extraction that mints a fresh draft capability list.
  const extractDone = page.waitForResponse(
    (r) =>
      r.url().includes("/capability-lists/extract") &&
      r.request().method() === "POST",
    { timeout: 120000 },
  );
  await page
    .locator('input[type="file"]')
    .first()
    .setInputFiles({
      name: "inventory.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(INVENTORY_CSV),
    });
  await extractDone;

  // The extraction produced a fresh editable draft (never "Released vN").
  await expect(page.getByText(/Draft v\d+/)).toBeVisible({ timeout: 30000 });

  // Dashboard NumberCards summarize the extracted list.
  await expect(page.getByText("Capabilities", { exact: true })).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByText("Annual cost", { exact: true })).toBeVisible();
  await expect(page.getByText("Categories", { exact: true })).toBeVisible();
  await expect(page.getByText("To consolidate / cut")).toBeVisible();
  // exact: the "N low-confidence rows" StatusPill would otherwise also match.
  await expect(
    page.getByText("Low-confidence rows", { exact: true }),
  ).toBeVisible();

  // Exactly one extracted row is stamped "AI 60%". Editing any cell in that row
  // must clear the AI badge and re-label the row "Human-curated".
  const aiBadge = page.getByText("AI 60%", { exact: true });
  await expect(aiBadge).toBeVisible({ timeout: 30000 });

  const editRow = page.locator("tr", {
    has: page.getByText("AI 60%", { exact: true }),
  });
  const patchDone = page.waitForResponse(
    (r) =>
      r.url().includes("/tech-debt/capability-items/") &&
      r.request().method() === "PATCH" &&
      r.ok(),
    { timeout: 90000 },
  );
  const nameCell = editRow.getByLabel("Name");
  await nameCell.fill("CrowdStrike Falcon (curated)");
  await nameCell.blur();
  await patchDone;

  // The AI-authored badge is gone, replaced by a human-curated one on that row.
  await expect(page.getByText("AI 60%", { exact: true })).toHaveCount(0, {
    timeout: 15000,
  });
  await expect(page.getByText("Human-curated").first()).toBeVisible();
});
