import { expect, test } from "@playwright/test";

import { register, uniqueEmail } from "../helpers/auth";

/**
 * SMOKE_TEST.md defect 4 (T4): the sign-up form must surface friendly,
 * field-scoped copy for a rejected registration - never the raw upstream
 * "Request validation failed." string. Covers the two disclosure cases the
 * spec calls out: a duplicate email and an unapproved email domain. Disclosure
 * posture is documented in DECISIONS.md D-016 (consistent with the pre-existing
 * domain-rejection copy).
 */

const PASSWORD = "correct horse battery staple!";

test("duplicate-email registration shows friendly copy on the email field", async ({
  page,
  request,
}) => {
  const email = uniqueEmail("atlas.example");

  // Pre-create the account through the same proxy the form uses, so the UI
  // attempt below is a guaranteed duplicate regardless of run order.
  const seeded = await request.post("/api/proxy/auth/register", {
    data: { email, password: PASSWORD, display_name: "Dupe First" },
  });
  expect(seeded.status(), await seeded.text()).toBe(201);

  // Now attempt the same email through the sign-up UI (fresh, unauthenticated).
  await register(page, "Dupe Second", email, PASSWORD);

  await expect(
    page.getByText("An account already exists for that email. Sign in instead."),
  ).toBeVisible();
  // The raw upstream validation string must never reach the user.
  await expect(page.getByText(/request validation failed/i)).toHaveCount(0);
  // The failed attempt stays on the sign-up page (no navigation to /intake).
  expect(new URL(page.url()).pathname).toContain("/sign-up");
});

test("unapproved-domain registration shows domain-not-approved copy", async ({
  page,
}) => {
  // A syntactically valid but never-approved domain -> the API's domain gate,
  // not a schema-validation error.
  const email = uniqueEmail(`notapproved-${Date.now()}.com`);

  await register(page, "No Org", email, PASSWORD);

  await expect(
    page.getByText(/no organization is registered for that email domain/i),
  ).toBeVisible();
  await expect(page.getByText(/request validation failed/i)).toHaveCount(0);
  expect(new URL(page.url()).pathname).toContain("/sign-up");
});
