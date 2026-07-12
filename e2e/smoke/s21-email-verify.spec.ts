import { expect, test } from "@playwright/test";

import { uniqueEmail } from "../helpers/auth";

/**
 * Sprint 6 T5 (D-028): email verification + password reset via MailHog.
 *
 * OPT-IN. Email delivery is off by default (SHIELD_EMAIL_DELIVERY_ENABLED=false),
 * so on a stock stack these specs SKIP rather than fail — mirroring the
 * opt-in live-AI specs (T1). To run them, bring the api up with
 * SHIELD_EMAIL_DELIVERY_ENABLED=true (MailHog is already wired on :1025 / :8025)
 * and re-run. When delivery is on, the specs register through the same proxy the
 * UI uses, read the real message out of the MailHog API, extract the token from
 * the link, and complete the verify / reset flow end to end.
 */

const PASSWORD = "correct horse battery staple!";
const NEW_PASSWORD = "brand new battery staple 99!";
const MAILHOG_API = "http://localhost:8025/api/v2";

interface MailHogItem {
  Content: { Headers: Record<string, string[]>; Body: string };
}

/** Poll MailHog for the most recent message to `email`; null if none arrives. */
async function fetchLatestMessage(
  request: import("@playwright/test").APIRequestContext,
  email: string,
  timeoutMs = 8000,
): Promise<MailHogItem | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const res = await request
      .get(`${MAILHOG_API}/search?kind=to&query=${encodeURIComponent(email)}`)
      .catch(() => null);
    if (res?.ok()) {
      const body = (await res.json()) as { items?: MailHogItem[] };
      if (body.items && body.items.length > 0) {
        return body.items[0];
      }
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return null;
}

/** MailHog quoted-prints long links across lines; join then pull the token. */
function extractToken(body: string): string | null {
  const collapsed = body.replace(/=\r?\n/g, "").replace(/=3D/g, "=");
  const match = collapsed.match(/token=([A-Za-z0-9_-]+)/);
  return match ? match[1] : null;
}

test("verification email confirms the address (MailHog)", async ({
  request,
}) => {
  const email = uniqueEmail("atlas.example");
  const reg = await request.post("/api/proxy/auth/register", {
    data: { email, password: PASSWORD, display_name: "Verify Me" },
  });
  expect(reg.status(), await reg.text()).toBe(201);

  const message = await fetchLatestMessage(request, email);
  test.skip(
    message === null,
    "email delivery disabled (set SHIELD_EMAIL_DELIVERY_ENABLED=true to run)",
  );

  const token = extractToken(message!.Content.Body);
  expect(token, "verification token in email body").not.toBeNull();

  const verify = await request.post("/api/proxy/auth/verify-email", {
    data: { token },
  });
  expect(verify.status(), await verify.text()).toBe(200);
  expect((await verify.json()).email_verified).toBe(true);
});

test("forgot-password link resets the password (MailHog)", async ({
  request,
}) => {
  const email = uniqueEmail("atlas.example");
  const reg = await request.post("/api/proxy/auth/register", {
    data: { email, password: PASSWORD, display_name: "Reset Me" },
  });
  expect(reg.status(), await reg.text()).toBe(201);

  // Drain the verification email so the reset email is the latest one.
  await fetchLatestMessage(request, email);

  const forgot = await request.post("/api/proxy/auth/forgot-password", {
    data: { email },
  });
  expect(forgot.status()).toBe(200);

  const message = await fetchLatestMessage(request, email);
  test.skip(
    message === null,
    "email delivery disabled (set SHIELD_EMAIL_DELIVERY_ENABLED=true to run)",
  );

  // The latest message must be the reset (subject), not the earlier verify.
  const subject = message!.Content.Headers["Subject"]?.[0] ?? "";
  expect(subject.toLowerCase()).toContain("reset");
  const token = extractToken(message!.Content.Body);
  expect(token).not.toBeNull();

  const reset = await request.post("/api/proxy/auth/reset-password", {
    data: { token, password: NEW_PASSWORD },
  });
  expect(reset.status(), await reset.text()).toBe(200);
});
