import { test, expect, type Page } from "@playwright/test";
import { ADMIN_EMAIL, ADMIN_PASSWORD, signIn } from "./helpers/auth";

/**
 * Screenshot capture for a walkthrough, NOT a test. Produces the deck of
 * full-page PNGs used to show the product without driving it live.
 *
 *   SHIELD_CAPTURE=1 npx playwright test capture-demo.spec.ts
 *
 * Every shot lands in e2e/artifacts/screenshots/, which is gitignored.
 *
 * Opt-in, following the same convention as `demo/` (SHIELD_DEMO_SMOKE) and
 * `s26-oidc-login` (E2E_OIDC), and for the same reason those are: CI's e2e job
 * runs a bare `npx playwright test` with no filter, and `playwright.config.ts`
 * sets `testDir: "."` with no testIgnore, so anything matching *.spec.ts is
 * collected. The SERVICE_IDS below are rows in one particular demo database and
 * do not exist on a fresh CI stack, so an unguarded version of this file would
 * fail every CI run.
 *
 * It asserts almost nothing on purpose: a missed selector should still leave a
 * usable picture rather than aborting the run, so each step is guarded and the
 * console says what it got. The one thing it does assert is sign-in, because
 * every later shot is worthless when signed out.
 */

test.skip(
  process.env.SHIELD_CAPTURE !== "1",
  "Walkthrough screenshot capture, opt-in: set SHIELD_CAPTURE=1. Needs the SERVICE_IDS below to exist in the local demo database, so it cannot run on a fresh stack.",
);

const OUT = "artifacts/screenshots";

// Atlas Defense Solutions, one service per kind, read off THIS box's demo
// database on 2026-08-06. Re-read them if the database is reseeded:
//   docker compose exec -T api python -c "..."  (see the PR that added this file)
const SERVICES = {
  techDebt: "43290084-ff27-4940-a16a-ac4e788cef2e",
  csf: "cca6b910-2ee9-4339-8a25-90d5a8b59983",
  attack: "d61e2d25-e8ac-4046-81d5-6f86b0f34748",
  ztCisa: "62dba521-570a-49e0-884a-0baaa2882330",
  ztDod: "dc00446d-fc3a-4f42-944c-5c04dc85997a",
};

/**
 * next-dev compiles a route on first visit and can take 20s+ cold, so give each
 * navigation room and settle before shooting. Returns false instead of throwing
 * when a route will not load, so one bad screen does not cost the whole set.
 */
async function shoot(page: Page, name: string, path: string): Promise<boolean> {
  try {
    await page.goto(path, { waitUntil: "domcontentloaded", timeout: 120_000 });
    await page
      .waitForLoadState("networkidle", { timeout: 60_000 })
      .catch(() => undefined);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
    console.log(`  captured  ${name}  <- ${path}`);
    return true;
  } catch (err) {
    console.log(
      `  MISSED    ${name}  <- ${path}  (${(err as Error).message.split("\n")[0]})`,
    );
    return false;
  }
}

test("capture the consultant walkthrough", async ({ page }) => {
  test.setTimeout(20 * 60_000);
  await page.setViewportSize({ width: 1600, height: 1000 });

  // Signed-out surfaces first, before a session exists.
  await shoot(page, "01-landing", "/");
  await shoot(page, "02-sign-in", "/sign-in");

  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  console.log("  signed in as", ADMIN_EMAIL);

  await shoot(page, "03-home-dashboard", "/home");
  await shoot(page, "04-admin-queue", "/admin/queue");
  await shoot(page, "05-admin-active", "/admin/active");

  await shoot(
    page,
    "06-tech-debt",
    `/admin/services/${SERVICES.techDebt}/tech-debt`,
  );
  await shoot(page, "07-csf-playbook", `/admin/services/${SERVICES.csf}/csf`);
  await shoot(
    page,
    "08-attack-coverage",
    `/admin/services/${SERVICES.attack}/attack-coverage`,
  );
  await shoot(
    page,
    "09-zero-trust-cisa",
    `/admin/services/${SERVICES.ztCisa}/zero-trust-cisa`,
  );
  await shoot(
    page,
    "10-zero-trust-dod",
    `/admin/services/${SERVICES.ztDod}/zero-trust-dod`,
  );

  // The 5x5 matrix is the one heatmap that lives on screen rather than only in
  // the deliverables, so it gets a focused shot as well as the full page.
  if (await shoot(page, "11-risk-register", "/admin/risk-register")) {
    const matrix = page.locator("table").first();
    if (await matrix.isVisible().catch(() => false)) {
      await matrix
        .screenshot({ path: `${OUT}/11b-risk-matrix-closeup.png` })
        .catch(() => undefined);
      console.log("  captured  11b-risk-matrix-closeup");
    }
  }

  await shoot(page, "12-documents", "/documents");
  await shoot(page, "13-admin-audit", "/admin/audit");
  await shoot(page, "14-admin-health", "/admin/health");
});
