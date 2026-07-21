import { expect, test, type Page } from "@playwright/test";
import * as OTPAuth from "otpauth";

import { signIn, uniqueEmail } from "../helpers/auth";

/**
 * Sprint 8 T4 (SMOKE MFA eyeball -> spec-backed), part A: enrollment UI + TOTP
 * sign-in, driven end-to-end in the browser.
 *
 * The manual MFA walkthrough (enable 2FA on /account, then sign in through the
 * authenticator second step) had no committed spec — only the backend flows are
 * pytest-proven. This drives the real UI: enroll on /account, confirm with a
 * GENERATED TOTP code (enrollment itself demands a valid code -
 * MfaEnrollment.tsx:39-78, there is no recovery-only shortcut), assert the
 * recovery codes are shown once, then sign out and sign back in through the
 * SignInForm TOTP second step (Auth.js v5 result.code === "mfa_required" reveals
 * the field - SignInForm.tsx:32-41).
 *
 * The backend TOTP is the standard RFC 6238 shape: SHA1 / 6 digits / 30s period
 * with a +/-1 verify window (app/security/totp.py) - the otpauth defaults match,
 * so codes generated here validate server-side.
 *
 * Isolation: this test creates its OWN fresh user and only enrolls/signs-in that
 * user, so the serialized shared-DB suite is untouched. SHIELD_AUTH_REQUIRE_MFA
 * stays default-off; enrollment is per-user opt-in.
 *
 * T5 (recovery-code sign-in + single-use rejection) is a separate test added to
 * this same file later.
 */

const PASSWORD = "correct horse battery staple!";

/**
 * Give the App Router client bundle time to hydrate before interacting: an
 * unhydrated submit/button click triggers a native GET submit (or a no-op) that
 * reloads the page and drops React state. Mirrors the settle in helpers/auth.ts.
 */
async function settleForHydration(page: Page): Promise<void> {
  await page.waitForLoadState("networkidle").catch(() => undefined);
  await page.waitForTimeout(1500);
}

/**
 * A current TOTP code for `totp`, generated at a safe distance from the window
 * edge. The server accepts +/-1 step, but if the current 30s step has almost
 * expired we wait for the next full window so the submit lands well inside it -
 * this is the window-edge guard the sprint plan calls for, done deterministically
 * instead of retrying blind.
 */
async function freshTotp(totp: OTPAuth.TOTP): Promise<string> {
  const period = totp.period;
  const remaining = period - (Math.floor(Date.now() / 1000) % period);
  if (remaining <= 3) {
    await new Promise((r) => setTimeout(r, (remaining + 1) * 1000));
  }
  return totp.generate();
}

/**
 * Sign out via the header control. On /account there are TWO "Sign out" buttons
 * (header + profile card, identical accessible names), so target the first
 * rather than tripping strict mode - either tears down the same session.
 */
async function signOutHeader(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Sign out" }).first().click();
  // The logged-out landing ("/") has two "Sign in" links (header nav + hero
  // CTA); the header link is the reliable "signed out" signal.
  await expect(page.getByRole("link", { name: "Sign in" }).first()).toBeVisible(
    {
      timeout: 15000,
    },
  );
}

test("account MFA enrollment + authenticator sign-in, driven in the browser", async ({
  page,
  request,
}) => {
  // Precondition (not one of the surfaces under proof): a fresh user via the
  // same proxy the sign-up UI uses. atlas.example is an approved client domain.
  const email = uniqueEmail("atlas.example");
  const reg = await request.post("/api/proxy/auth/register", {
    data: { email, password: PASSWORD, display_name: "MFA Enroller" },
  });
  expect(reg.status(), await reg.text()).toBe(201);

  // Sign in (no MFA yet) and open the account page's 2FA section.
  await signIn(page, email, PASSWORD);
  await page.goto("/account");

  // Begin enrollment. Retry through the pre-hydration click race: an unhydrated
  // click on the type="button" is a no-op, so re-clicking after hydration
  // performs exactly one real enroll (the setup key appears only once it fires).
  await expect(async () => {
    if (!(await page.getByText("Setup key", { exact: true }).isVisible())) {
      await settleForHydration(page);
      await page
        .getByRole("button", { name: "Enable two-factor authentication" })
        .click();
      await expect(page.getByText("Setup key", { exact: true })).toBeVisible({
        timeout: 8000,
      });
    }
  }).toPass({ timeout: 45000 });

  // Capture the displayed secret (MfaEnrollment.tsx:126) and build the same TOTP
  // the authenticator app would. The secret <code> is the sibling of the
  // "Setup key" label span.
  const secret = (
    await page
      .getByText("Setup key", { exact: true })
      .locator("xpath=following-sibling::code")
      .innerText()
  ).trim();
  expect(secret, "setup key rendered").not.toBe("");

  const totp = new OTPAuth.TOTP({
    issuer: "SHIELD by Kentro",
    label: email,
    algorithm: "SHA1",
    digits: 6,
    period: 30,
    secret: OTPAuth.Secret.fromBase32(secret),
  });

  // Confirm enrollment with a generated code. Regenerate a fresh code per retry
  // so a rare window-edge miss self-heals rather than failing the whole flow.
  await expect(async () => {
    const code = await freshTotp(totp);
    await page.locator("#mfa-code").fill(code);
    await page.getByRole("button", { name: "Confirm" }).click();
    await expect(
      page.getByText("Two-factor authentication is now enabled."),
    ).toBeVisible({ timeout: 8000 });
  }).toPass({ timeout: 40000 });

  // Recovery codes are shown exactly once, in the "save these now" alert.
  const recoveryAlert = page
    .getByRole("alert")
    .filter({ hasText: "recovery codes" });
  await expect(recoveryAlert).toBeVisible();
  const codes = recoveryAlert.locator("li");
  await expect(codes).toHaveCount(10);
  expect((await codes.first().innerText()).trim()).toMatch(
    /^[A-Z0-9]{4}-[A-Z0-9]{4}$/,
  );

  // Sign out, then sign back in - MFA is now enrolled, so the second factor is
  // required.
  await signOutHeader(page);

  await page.goto("/sign-in");
  // Password step: correct password reveals the authenticator field (the backend
  // signals mfa_required; SignInForm keeps the code field shown for retries).
  // Retry through the pre-hydration native-submit race (a native GET submit
  // reloads /sign-in and clears the fields).
  await expect(async () => {
    if (
      !(await page
        .locator("#totp")
        .isVisible()
        .catch(() => false))
    ) {
      await settleForHydration(page);
      await page.locator('input[type="email"]').fill(email);
      await page.locator('input[type="password"]').fill(PASSWORD);
      await page.getByRole("button", { name: "Sign in" }).click();
      await expect(page.locator("#totp")).toBeVisible({ timeout: 15000 });
    }
  }).toPass({ timeout: 60000 });

  // Code step: a fresh code, regenerated per retry. Skip the fill if a slow
  // (but successful) nav already left /sign-in after a prior waitForURL gave up.
  await expect(async () => {
    if (new URL(page.url()).pathname.startsWith("/sign-in")) {
      const code = await freshTotp(totp);
      await page.locator("#totp").fill(code);
      await page.getByRole("button", { name: "Verify code" }).click();
    }
    await page.waitForURL((url) => !url.pathname.startsWith("/sign-in"), {
      timeout: 15000,
    });
  }).toPass({ timeout: 45000 });

  // Authenticated landing: the header sign-out control renders.
  await expect(
    page.getByRole("button", { name: "Sign out" }).first(),
  ).toBeVisible({ timeout: 20000 });
});
