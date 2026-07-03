import { expect, test, type Page } from "@playwright/test";

import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  CLIENT_EMAIL,
  CLIENT_PASSWORD,
  register,
  signIn,
  uniqueEmail,
} from "../helpers/auth";

/**
 * SMOKE_TEST.md section 12 (T9): keyboard navigation + skip-to-content.
 *
 * Navigation_Spec §7 requires every shell to expose a "Skip to content" link
 * as the first focusable element, targeting the `#main-content` landmark, plus a
 * persistent top-nav. We assert on the real app shells:
 *
 *   1. On /account, /messages, /assessments (client shell) and one admin page,
 *      the FIRST Tab from a fresh page load focuses "Skip to content"; a visible
 *      Primary top-nav is present.
 *   2. Activating the skip link jumps the browser to the `#main-content`
 *      landmark, so the NEXT Tab moves focus INTO the main content (past the
 *      nav). NOTE: the app's `<main id="main-content">` has no `tabindex="-1"`,
 *      so activation moves the *sequential focus starting point* to the landmark
 *      (location.hash === "#main-content") rather than programmatically focusing
 *      <main> itself. That is the current behavior; adding tabindex=-1 so screen
 *      readers land directly on <main> is a minor a11y follow-up logged for T10.
 *   3. Workspace spot-check: a self-assessment maturity control (radiogroup) is
 *      keyboard-focusable and operable (Space toggles + auto-saves).
 */

const PASSWORD = "correct horse battery staple!";

/**
 * From a freshly loaded `path`, prove the skip-link contract and top-nav:
 *   - the first Tab focuses the "Skip to content" link;
 *   - a visible Primary nav landmark is present;
 *   - activating the link targets #main-content and the next Tab enters it.
 */
async function assertSkipLinkAndNav(page: Page, path: string): Promise<void> {
  await page.goto(path);
  // Wait for the shell to render (skip link is the first body child of every
  // shell) before probing keyboard focus.
  await page.locator('a[href="#main-content"]').first().waitFor();
  await expect(
    page.getByRole("navigation", { name: "Primary" }).first(),
  ).toBeVisible();

  // First Tab from a fresh load lands on the skip link. (Do NOT click anywhere
  // first: a click would move the sequential-focus starting point past it.)
  await page.keyboard.press("Tab");
  const firstStop = await page.evaluate(() => {
    const a = document.activeElement;
    return {
      tag: a?.tagName ?? null,
      text: a?.textContent?.trim() ?? null,
      href: a?.getAttribute?.("href") ?? null,
    };
  });
  expect(firstStop.tag, `${path}: first Tab focuses a link`).toBe("A");
  expect(firstStop.text, `${path}: first Tab focuses skip link`).toBe(
    "Skip to content",
  );
  expect(firstStop.href, `${path}: skip link targets main`).toBe(
    "#main-content",
  );

  // Activate it: the browser jumps to the #main-content landmark (this is the
  // content-independent contract — every shell targets the same landmark).
  await page.keyboard.press("Enter");
  await expect
    .poll(() => page.evaluate(() => location.hash), {
      message: `${path}: activating skip link targets #main-content`,
    })
    .toBe("#main-content");

  // When the landmark holds a focusable control, the next Tab moves focus INTO
  // it (proving the nav was actually skipped). Some shells render a main with no
  // focusable descendant yet (e.g. an empty/loading admin queue), so gate this
  // stronger check on the landmark actually containing a focusable element.
  const hasFocusable = await page.evaluate(() => {
    const main = document.getElementById("main-content");
    if (!main) return false;
    return (
      main.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ).length > 0
    );
  });
  if (hasFocusable) {
    await page.keyboard.press("Tab");
    const insideMain = await page.evaluate(() => {
      const main = document.getElementById("main-content");
      return main ? main.contains(document.activeElement) : false;
    });
    expect(insideMain, `${path}: focus enters #main-content after skip`).toBe(
      true,
    );
  }
}

test("client shell: skip link + top nav on /account, /messages, /assessments", async ({
  page,
}) => {
  test.slow();
  await signIn(page, CLIENT_EMAIL, CLIENT_PASSWORD);
  for (const path of ["/account", "/messages", "/assessments"]) {
    await assertSkipLinkAndNav(page, path);
  }
});

test("admin shell: skip link + top nav on /admin/queue", async ({ page }) => {
  test.slow();
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await assertSkipLinkAndNav(page, "/admin/queue");
});

test("workspace controls are keyboard-reachable and operable", async ({
  page,
}) => {
  test.slow();
  // A fresh @atlas.example self-registrant (approved domain, seeded by T2) so
  // the CSF questionnaire renders live maturity controls we can drive.
  await register(
    page,
    "A11y Keyboard Tester",
    uniqueEmail("atlas.example"),
    PASSWORD,
  );
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible({
    timeout: 20000,
  });

  // Start a CSF self-assessment -> the questionnaire workspace.
  await page.goto("/assessments");
  await expect(
    page.getByRole("heading", { name: "My assessments" }),
  ).toBeVisible({ timeout: 20000 });
  await page.getByRole("button", { name: "+ Start a new assessment" }).click();
  await page
    .getByRole("combobox", { name: "Assessment type" })
    .selectOption("nist_csf");
  await page.getByRole("combobox", { name: "Target tier" }).selectOption("3");
  await page
    .getByRole("combobox", { name: "Impact profile" })
    .selectOption("LOW");
  await page.getByRole("button", { name: "Start assessment" }).click();
  await page.waitForURL(/\/self-assessment\//, { timeout: 30000 });
  await expect(
    page.getByRole("heading", { name: "CSF 2.0 questionnaire" }),
  ).toBeVisible({ timeout: 30000 });

  // The maturity picker is a radiogroup of role=radio <button>s (TierPicker).
  const firstRadio = page
    .getByRole("radiogroup")
    .first()
    .getByRole("radio")
    .first();
  await expect(firstRadio).toBeVisible();

  // Reachable: it is a real focusable control (not removed from the tab order).
  await expect(firstRadio).not.toHaveAttribute("tabindex", "-1");
  await firstRadio.focus();
  const focused = await firstRadio.evaluate(
    (el) => el === document.activeElement,
  );
  expect(focused, "radio is keyboard-focusable").toBe(true);

  // Operable by keyboard: Space activates the radio, which auto-saves via PATCH
  // .../csf/self-assessment/answers/<id> and flips aria-checked.
  const saved = page.waitForResponse(
    (r) =>
      r.url().includes("/csf/self-assessment/answers/") &&
      r.request().method() === "PATCH" &&
      r.ok(),
    { timeout: 30000 },
  );
  await page.keyboard.press("Space");
  await saved;
  await expect(firstRadio).toHaveAttribute("aria-checked", "true");

  // A primary action button in the same workspace is reachable + operable.
  await expect(
    page.getByRole("button", { name: "Submit for review" }),
  ).toBeEnabled();
});
