import { expect, test, type APIRequestContext } from "@playwright/test";

import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  register,
  signIn,
  uniqueEmail,
} from "../helpers/auth";
import { adminApiToken, API_BASE } from "../helpers/ids";

/**
 * SMOKE_TEST §6.4 (Sprint 5 T3): the signed-in client /home dashboard.
 *
 * Proves the two hero states and the role-based landing:
 *   1. A client with NO released report sees next-step guidance (never a dead
 *      end, §12) — the "report is ready" hero is absent.
 *   2. After an admin finalizes+releases a deliverable for that tenant, the same
 *      client's /home shows the hero ("report is ready" + View/Download).
 *   3. A signed-in client hitting `/` lands on /home; a signed-in admin lands on
 *      /admin.
 *   4. /home never leaks scoring math (§6.4) — no percentage renders.
 *
 * Isolated in its own throwaway tenant (mirrors s17): it never perturbs the
 * shared seeded Atlas services, and the release/download path needs artifact
 * bytes in the live object store, which only runtime-finalized deliverables get.
 */

const TENANT_NAME = "Home QA";
const TENANT_DOMAIN = "homeqa.example";
const PASSWORD = "correct horse battery staple!";

interface ClientRow {
  id: string;
  legal_name: string;
}

interface DeliverableRow {
  id: string;
  title: string;
  pdf_artifact_id: string | null;
}

function tenantHeaders(
  token: string,
  clientId: string,
): Record<string, string> {
  return { Authorization: `Bearer ${token}`, "X-Client-Id": clientId };
}

/** Find-or-create the throwaway "Home QA" tenant with an approved domain. */
async function ensureHomeTenant(
  request: APIRequestContext,
  token: string,
): Promise<string> {
  const auth = { Authorization: `Bearer ${token}` };
  const listed = await request.get(`${API_BASE}/admin/clients`, {
    headers: auth,
  });
  expect(listed.ok()).toBeTruthy();
  const clients = ((await listed.json()) as { clients: ClientRow[] }).clients;
  let tenant = clients.find(
    (c) => c.legal_name.toLowerCase() === TENANT_NAME.toLowerCase(),
  );
  if (!tenant) {
    const created = await request.post(`${API_BASE}/admin/clients`, {
      headers: auth,
      data: { legal_name: TENANT_NAME },
    });
    expect(created.ok()).toBeTruthy();
    tenant = (await created.json()) as ClientRow;
  }
  const domain = await request.post(
    `${API_BASE}/admin/clients/${tenant.id}/domains`,
    { headers: auth, data: { domain: TENANT_DOMAIN } },
  );
  expect(
    domain.status() === 201 || domain.status() === 409,
    `approve ${TENANT_DOMAIN}: ${domain.status()}`,
  ).toBeTruthy();
  return tenant.id;
}

/** Finalize a fresh CSF deliverable in the tenant and release it. */
async function releaseCsfDeliverable(
  request: APIRequestContext,
  headers: Record<string, string>,
): Promise<DeliverableRow> {
  const svcRes = await request.post(`${API_BASE}/csf/services`, {
    headers,
    data: { kind: "nist_csf", title: `Home QA CSF ${Date.now()}` },
  });
  expect(svcRes.ok(), `open CSF service (${svcRes.status()})`).toBeTruthy();
  const serviceId = ((await svcRes.json()) as { id: string }).id;

  const assessRes = await request.post(
    `${API_BASE}/csf/services/${serviceId}/assessments`,
    { headers },
  );
  expect(
    assessRes.ok(),
    `create assessment (${assessRes.status()})`,
  ).toBeTruthy();
  const assessmentId = ((await assessRes.json()) as { id: string }).id;
  const approveRes = await request.post(
    `${API_BASE}/csf/assessments/${assessmentId}/approve`,
    { headers },
  );
  expect(approveRes.ok(), `approve (${approveRes.status()})`).toBeTruthy();

  const fin = await request.post(
    `${API_BASE}/csf/services/${serviceId}/deliverables/finalize`,
    { headers },
  );
  expect(fin.status(), `finalize (${await fin.text()})`).toBe(201);
  const deliverable = (await fin.json()) as DeliverableRow;
  const release = await request.post(
    `${API_BASE}/csf/deliverables/${deliverable.id}/release`,
    { headers },
  );
  expect(release.ok(), `release (${release.status()})`).toBeTruthy();
  return deliverable;
}

test.describe("s18 /home — client dashboard hero states + role landing", () => {
  test("guidance before a report, hero after release, client / -> /home", async ({
    page,
    request,
  }) => {
    test.slow();
    const token = await adminApiToken(request);
    const clientId = await ensureHomeTenant(request, token);

    // A real client of this tenant self-registers (auto signed-in).
    await register(page, "Hank Home", uniqueEmail(TENANT_DOMAIN), PASSWORD);
    await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible({
      timeout: 20000,
    });

    // Hero-absent state: no released report yet -> next-step guidance.
    await page.goto("/home");
    await expect(
      page.getByRole("heading", { name: /Welcome back/ }),
    ).toBeVisible({ timeout: 20000 });
    await expect(
      page.getByText("get your first assessment started"),
    ).toBeVisible();
    await expect(page.getByText(/report is ready/)).toHaveCount(0);
    await expect(
      page.getByRole("link", { name: "Start an assessment" }),
    ).toBeVisible();

    // A signed-in client hitting `/` lands on /home (not the marketing page).
    await page.goto("/");
    await page.waitForURL((url) => url.pathname === "/home", {
      timeout: 20000,
    });
    await expect(
      page.getByRole("heading", { name: /Welcome back/ }),
    ).toBeVisible();

    // Admin releases a report for this tenant via the API.
    await releaseCsfDeliverable(request, tenantHeaders(token, clientId));

    // Hero-present state: the same client now sees the "report is ready" hero.
    await page.goto("/home");
    await expect(page.getByText(/report is ready/)).toBeVisible({
      timeout: 20000,
    });
    await expect(
      page.getByRole("link", { name: "View reports" }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Download PDF" }),
    ).toBeVisible();

    // §6.4: /home must not leak scoring math — no percentage renders anywhere.
    await expect(page.getByText(/\d+%/)).toHaveCount(0);
  });

  test("signed-in admin landing on / goes to /admin", async ({ page }) => {
    test.slow();
    await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
    await page.goto("/");
    await page.waitForURL((url) => url.pathname.startsWith("/admin"), {
      timeout: 20000,
    });
    expect(new URL(page.url()).pathname.startsWith("/admin")).toBeTruthy();
  });
});
