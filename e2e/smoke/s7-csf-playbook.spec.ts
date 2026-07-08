import fs from "node:fs";
import path from "node:path";

import { expect, test, type APIResponse, type Page } from "@playwright/test";

import { ADMIN_EMAIL, ADMIN_PASSWORD, signIn } from "../helpers/auth";
import { atlasServiceId } from "../helpers/ids";

/**
 * SMOKE_TEST.md section 7 (T7): the NIST CSF 2.0 full Playbook (Work Order D4).
 *
 * Admin opens the seeded Atlas CSF service, layers a fresh DRAFT on top (the
 * seeded assessment is RELEASED, i.e. read-only), then walks the Playbook:
 *   1. Seed Working Profiles -> ~106 subcategories x 3 tiers.
 *   2. Run AI (csf_score) drafts the five dimensions + narrative (fixture-mode
 *      LLM, T6b); the panel echoes "AI updated N fields across M subcategories".
 *   3. Dimension editor: the five 0/1/2 scores + the Evidence toggle update
 *      total/level/cap LIVE, and the no-evidence cap clamps the level to <= 2
 *      (and Implementation to <= 1, hence total 9 not 10).
 *   4. Enterprise roll-up: tier levels, enterprise level, rule #, target, gap,
 *      P1/P2/P3 priority.
 *   5. Export produces 5 files (XLSX, exec PDF/Word, full PDF/Word) whose
 *      download links stream real bytes (HTTP 200 + correct content-type).
 *      Each file is saved to e2e/artifacts/ for David's section-10 eyeball.
 */

const ARTIFACTS_DIR = path.resolve(__dirname, "..", "artifacts");

const EXPECTED_ARTIFACTS: Record<string, string> = {
  // kind -> expected Content-Type of the download stream
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  exec_pdf: "application/pdf",
  exec_docx:
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  full_pdf: "application/pdf",
  full_docx:
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

const DIM_LABELS = [
  "Governance",
  "Policy & Process",
  "Implementation",
  "Monitoring & Measurement",
  "Continuous Improvement",
];

/**
 * Open the CSF workspace and make sure the latest assessment is a DRAFT.
 * With `fresh: true` a new draft version is always minted, so seeding and the
 * AI run start from empty rows (deterministic on every re-run).
 */
async function openWorkspaceOnDraft(
  page: Page,
  opts: { fresh?: boolean } = {},
): Promise<void> {
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  // Seeded Atlas Defense "NIST CSF 2.0" service (scripts/seed_demo.py).
  const csfServiceId = await atlasServiceId(page, "nist_csf");
  await page.goto(`/admin/services/${csfServiceId}/csf`);
  await expect(
    page.getByRole("heading", { name: "NIST CSF 2.0 Assessment" }),
  ).toBeVisible({ timeout: 30000 });
  // Wait for the status pill so we know the latest-assessment fetch resolved.
  await expect(
    page
      .getByText(/(Draft|Submitted|Approved|Released) v\d+|No assessment yet/)
      .first(),
  ).toBeVisible({ timeout: 30000 });

  const draftVisible = await page.getByText(/Draft v\d+/).isVisible();
  if (opts.fresh) {
    // The seeded assessment is RELEASED (read-only) and re-runs need clean
    // rows. T7 added a draft-exists guard: POST now REUSES an open draft
    // instead of minting a new version, so a plain POST would hand back the
    // previous run's already-seeded/AI-drafted draft. Close any open draft
    // first (self-assessment/submit moves it out of DRAFT; a 404/409 when
    // there's nothing open is expected and ignored), so the following POST
    // cuts a genuinely fresh v+1 with empty rows.
    await page.request.post(
      `/api/proxy/csf/services/${csfServiceId}/self-assessment/submit`,
      { data: {} },
    );
    const created = await page.request.post(
      `/api/proxy/csf/services/${csfServiceId}/assessments`,
    );
    expect(created.ok()).toBeTruthy();
    await page.reload();
    await expect(page.getByText(/Draft v\d+/)).toBeVisible({ timeout: 30000 });
  } else if (!draftVisible) {
    // No open draft yet: mint one. The T7 guard makes any later POST reuse it,
    // so this stays idempotent across re-runs (the active-client cookie is
    // already set by EnsureActiveClient).
    const created = await page.request.post(
      `/api/proxy/csf/services/${csfServiceId}/assessments`,
    );
    expect(created.ok()).toBeTruthy();
    await page.reload();
    await expect(page.getByText(/Draft v\d+/)).toBeVisible({ timeout: 30000 });
  }
  // Let the (StrictMode-duplicated) initial loads settle so a stale duplicate
  // response can't land mid-test and clobber fresher state.
  await page.waitForLoadState("networkidle").catch(() => undefined);
}

/** Wait for one dimension-scores PATCH triggered by `action` to succeed. */
async function patched(page: Page, action: () => Promise<void>): Promise<void> {
  const done = page.waitForResponse(
    (r) =>
      r.url().includes("/csf/dimension-scores/") &&
      r.request().method() === "PATCH" &&
      r.ok(),
    { timeout: 90000 },
  );
  await action();
  await done;
}

test("Seed Working Profiles (~106 subcats), Run AI drafts dimensions + narrative, editor math is live with the evidence cap", async ({
  page,
}) => {
  // Long flow (sign-in + draft + seed 318 rows + run-ai + 7 PATCHes) against a
  // next-dev server; requests can queue for tens of seconds under load.
  test.slow();
  test.setTimeout(300_000);
  await openWorkspaceOnDraft(page, { fresh: true });

  // --- Seed Working Profiles -> 106 subcategories across 3 tiers -----------
  // A fresh draft is always unseeded (the branch guards a crashed re-entry).
  const seedBtn = page.getByRole("button", { name: "Seed Working Profiles" });
  const runBtn = page.getByRole("button", { name: "Run AI (csf_score)" });
  await expect(seedBtn.or(runBtn)).toBeVisible({ timeout: 30000 });
  if (await seedBtn.isVisible()) {
    const seeded = page.waitForResponse(
      (r) =>
        r.url().includes("/csf/services/") &&
        r.url().includes("/profiles/seed") &&
        r.request().method() === "POST" &&
        r.ok(),
      { timeout: 90000 },
    );
    const enterpriseLoaded = page.waitForResponse(
      (r) =>
        r.url().includes("/enterprise-profile") &&
        r.request().method() === "GET" &&
        r.ok(),
      { timeout: 90000 },
    );
    await seedBtn.click();
    await seeded;
    const enterprise = (await (await enterpriseLoaded).json()) as {
      tiers_in_use: string[];
      subcategories: unknown[];
    };
    // Server truth: the full CSF 2.0 catalog is 106 subcategories, seeded for
    // all three tiers.
    expect(enterprise.subcategories.length).toBe(106);
    expect(enterprise.tiers_in_use.sort()).toEqual(["high", "low", "moderate"]);
  }
  // Text spans nested <span>s, so filter on the containing element (T6 lesson).
  await expect(
    page.locator("span", { hasText: /3 tier\(s\) in use/ }).first(),
  ).toBeVisible({ timeout: 30000 });

  // --- Run AI (csf_score): dimensions + narrative ---------------------------
  const runDone = page.waitForResponse(
    (r) =>
      r.url().includes("/csf/services/") &&
      r.url().includes("/run-ai") &&
      r.request().method() === "POST" &&
      r.ok(),
    { timeout: 120000 },
  );
  await expect(runBtn).toBeVisible({ timeout: 30000 });
  await runBtn.click();
  const runBody = (await (await runDone).json()) as {
    changed: Array<{ tier: string; subcategory_code: string; field: string }>;
  };
  expect(runBody.changed.length).toBeGreaterThan(0);
  // Dimensions were drafted...
  const dimFields = new Set([
    "governance",
    "policy",
    "implementation",
    "monitoring",
    "improvement",
  ]);
  expect(runBody.changed.some((c) => dimFields.has(c.field))).toBeTruthy();
  // ...and so was the narrative (what_we_found).
  expect(runBody.changed.some((c) => c.field === "what_we_found")).toBeTruthy();
  // The panel echoes the what-changed summary.
  await expect(
    page.locator("p", { hasText: /AI updated/ }).first(),
  ).toBeVisible({ timeout: 30000 });

  // --- Dimension editor: live total/level/cap math --------------------------
  // High tier is the default tab; the first subcategory is auto-selected.
  const subcatSelect = page.getByRole("combobox", { name: "Subcategory" });
  await expect(subcatSelect).toBeVisible({ timeout: 30000 });
  await expect
    .poll(async () => subcatSelect.locator("option").count(), {
      timeout: 30000,
    })
    .toBeGreaterThan(1);

  // Set all five dimensions to 2 (each click auto-saves via PATCH).
  for (const label of DIM_LABELS) {
    const group = page.getByRole("radiogroup", { name: label, exact: true });
    const two = group.getByRole("radio").nth(2);
    await patched(page, () => two.click());
    await expect(two).toHaveAttribute("aria-checked", "true");
  }

  // Make sure "Evidence on file" is OFF so the cap applies. NOTE: click(),
  // not check()/uncheck() — the checkbox is React-controlled and only flips
  // after the auto-save PATCH round-trips, so check()'s immediate post-click
  // state verification fails under load.
  const evidence = page.getByRole("checkbox", { name: "Evidence on file" });
  if (await evidence.isChecked()) {
    await patched(page, () => evidence.click());
  }
  // No evidence: Implementation is clamped to 1 (total 9, not 10) AND the
  // level is capped at L2 even though a total of 9 would otherwise be L4.
  const totalLine = (re: RegExp) =>
    page.locator("span", { hasText: re }).first();
  await expect(totalLine(/Total\s*9\s*·\s*Level\s*L2/)).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByText(/capped .* no evidence/)).toBeVisible();

  // Toggle Evidence ON: the cap lifts live -> total 10, level L5.
  await patched(page, () => evidence.click());
  await expect(evidence).toBeChecked({ timeout: 30000 });
  await expect(totalLine(/Total\s*10\s*·\s*Level\s*L5/)).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByText(/capped .* no evidence/)).toBeHidden();
});

test("Enterprise roll-up shows tier levels/rule/target/priority and Export produces 5 downloadable files", async ({
  page,
}) => {
  test.slow();
  test.setTimeout(300_000);
  // Reuses the seeded + AI-drafted draft from the previous test (same DB);
  // openWorkspaceOnDraft + the seed fallback below make it self-sufficient.
  await openWorkspaceOnDraft(page);

  const seedBtn = page.getByRole("button", { name: "Seed Working Profiles" });
  const runBtn = page.getByRole("button", { name: "Run AI (csf_score)" });
  await expect(seedBtn.or(runBtn)).toBeVisible({ timeout: 30000 });
  if (await seedBtn.isVisible()) {
    const enterpriseLoaded = page.waitForResponse(
      (r) => r.url().includes("/enterprise-profile") && r.ok(),
      { timeout: 90000 },
    );
    await seedBtn.click();
    await enterpriseLoaded;
  }
  await page.waitForLoadState("networkidle").catch(() => undefined);

  // --- Force a deterministic gap: target L5 on the second subcategory ------
  // (the first one may carry the previous test's all-2s + evidence = L5 row).
  const subcatSelect = page.getByRole("combobox", { name: "Subcategory" });
  await expect(subcatSelect).toBeVisible({ timeout: 30000 });
  await expect
    .poll(async () => subcatSelect.locator("option").count(), {
      timeout: 30000,
    })
    .toBeGreaterThan(2);
  const code = await subcatSelect
    .locator("option")
    .nth(1)
    .getAttribute("value");
  expect(code).toBeTruthy();
  await subcatSelect.selectOption(code!);

  const enterpriseReload = page.waitForResponse(
    (r) => r.url().includes("/enterprise-profile") && r.ok(),
    { timeout: 90000 },
  );
  // exact: true — the gap-analysis card has a separate "Target tier" select.
  const targetSelect = page.getByRole("combobox", {
    name: "Target",
    exact: true,
  });
  await patched(page, () => targetSelect.selectOption("5"));
  const enterprise = (await (await enterpriseReload).json()) as {
    subcategories: Array<{
      subcategory_code: string;
      tier_levels: Record<string, number>;
      enterprise_level: number;
      rollup_rule: number;
      target_level: number | null;
      gap: boolean;
      priority: string | null;
    }>;
  };

  // Server truth for the edited row: 3 tier levels, an enterprise level, a
  // roll-up rule #, our L5 target, a gap, and a computed priority. The row has
  // no evidence, so its level caps at <= 2 -> the L5 target guarantees a gap.
  // Priority: HIGH tier is always in play here (3 tiers), so gap_priority
  // never yields P3 - it's P1 when this subcategory maps to a Core IG metric
  // (Core + HIGH tier + multi-system), else P2. Before T5 the route hard-coded
  // is_core=False so this row was always P2; now that the IG Core/Supporting
  // metadata is imported (catalog.is_core), a Core subcategory correctly rolls
  // up to P1. We assert against server truth + the {P1,P2} invariant rather
  // than a stale constant so the check survives which subcategory is nth(1).
  const row = enterprise.subcategories.find((s) => s.subcategory_code === code);
  expect(row).toBeTruthy();
  expect(Object.keys(row!.tier_levels).sort()).toEqual([
    "high",
    "low",
    "moderate",
  ]);
  expect(row!.enterprise_level).toBeGreaterThanOrEqual(1);
  expect(row!.enterprise_level).toBeLessThanOrEqual(5);
  expect(row!.rollup_rule).toBeGreaterThanOrEqual(1);
  expect(row!.target_level).toBe(5);
  expect(row!.gap).toBe(true);
  expect(["P1", "P2"]).toContain(row!.priority);

  // And the roll-up table renders that row: rule # + the server's priority pill.
  const tableRow = page.getByRole("row").filter({ hasText: code! }).first();
  await expect(tableRow).toBeVisible({ timeout: 30000 });
  await expect(tableRow).toContainText(`#${row!.rollup_rule}`);
  await expect(tableRow).toContainText(row!.priority!);
  await expect(tableRow).toContainText(`L${row!.enterprise_level}`);

  // --- Export: 5 files, each link streaming the right content-type ---------
  const exportDone = page.waitForResponse(
    (r) =>
      r.url().includes("/playbook/export") &&
      r.request().method() === "POST" &&
      r.ok(),
    { timeout: 180000 },
  );
  await page.getByRole("button", { name: "Export XLSX" }).click();
  const exported = (await (await exportDone).json()) as {
    artifacts: Array<{
      kind: string;
      label: string;
      artifact_id: string;
      filename: string;
    }>;
  };
  expect(exported.artifacts.length).toBe(5);
  expect(exported.artifacts.map((a) => a.kind).sort()).toEqual(
    Object.keys(EXPECTED_ARTIFACTS).sort(),
  );

  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
  for (const artifact of exported.artifacts) {
    // The panel renders a working download link per artifact...
    await expect(page.getByRole("link", { name: artifact.label })).toBeVisible({
      timeout: 30000,
    });
    // ...and the link's proxy endpoint streams the file (200 + content-type).
    const download: APIResponse = await page.request.get(
      `/api/proxy/artifacts/${artifact.artifact_id}/download`,
    );
    expect(download.status(), `${artifact.kind} download status`).toBe(200);
    expect(
      download.headers()["content-type"],
      `${artifact.kind} content-type`,
    ).toContain(EXPECTED_ARTIFACTS[artifact.kind]);
    const body = await download.body();
    expect(body.length, `${artifact.kind} byte size`).toBeGreaterThan(0);
    // Saved for David's manual section-10 review (dir is gitignored).
    fs.writeFileSync(path.join(ARTIFACTS_DIR, artifact.filename), body);
  }
});
