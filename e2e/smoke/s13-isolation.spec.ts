import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from "@playwright/test";

import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  register,
  signIn,
} from "../helpers/auth";

/**
 * SMOKE_TEST.md section 13 (T9): multi-tenant isolation.
 *
 * A second tenant ("Beacon Labs") must be walled off from the seeded Atlas
 * Defense tenant:
 *
 *   1. A Beacon-tenant CLIENT cannot reach admin-only URLs — the /admin shell
 *      shows the Navigation_Spec §6 "Not authorized" page, never Atlas data.
 *   2. A Beacon-tenant CLIENT never sees Atlas data on any surface (their
 *      assessment list is empty and a direct fetch of an Atlas service 404s).
 *   3. An ADMIN whose active client is Beacon gets a 404 (not data) when the
 *      tenant-scoped data plane is asked for an Atlas service — proving the
 *      X-Client-Id scoping is the security boundary.
 *
 * DOMAIN NOTE: the running DB carries an approved `beacon.test` domain from a
 * prior UI session, but `.test` is a reserved TLD that the API's email
 * validator refuses ("special-use or reserved name"), so NO user can ever
 * register against it. We therefore provision `beacon.example` for Beacon Labs
 * (registrable, exactly like the seeded `atlas.example`) so a real Beacon
 * client user exists to test isolation with. The unusable `beacon.test`
 * approval is logged as a minor product inconsistency for the backlog/T10.
 *
 * SETUP NOTE: the Beacon client + domain are provisioned through the same admin
 * endpoints the Management UI calls (admin bearer against the API), find-or-
 * create so the shared DB stays clean across re-runs.
 */

const PASSWORD = "correct horse battery staple!";
const BEACON_DOMAIN = "beacon.example";

// Seeded Atlas Defense tenant + services (scripts/seed_demo.py; ids are stable
// constants the other smoke specs also hardcode).
const ATLAS_CLIENT_ID = "1b9c80e3-4ad2-4d5a-ae5a-ab310aff58fd";
const ATLAS_ATTACK_SERVICE_ID = "7c2ec112-2ed2-4b23-88b4-0d6a996ed46c";
const ATLAS_SERVICE_IDS = new Set([
  "7c2ec112-2ed2-4b23-88b4-0d6a996ed46c", // attack_coverage
  "0290f4e2-b615-451a-8b17-22351d9299ea", // zero_trust_dod
  "2a2c1b0d-a969-4852-bccd-cffe90c0e28d", // zero_trust_cisa
  "55eb8797-0b7a-4fe6-95cd-76b5e692cfe6", // nist_csf
  "3c73a6cb-802a-4fd8-937b-69d9af0fe6de", // tech_debt
]);

const API_BASE = "http://localhost:8000";

interface Client {
  id: string;
  legal_name: string;
}

/**
 * Find-or-create the "Beacon Labs" tenant with an approved, registrable email
 * domain, using the admin API directly (the endpoints the Management UI calls).
 * Returns the Beacon client id. Idempotent against the shared seeded DB.
 */
async function ensureBeaconTenant(request: APIRequestContext): Promise<string> {
  const login = await request.post(`${API_BASE}/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  expect(login.ok()).toBeTruthy();
  const token = ((await login.json()) as { access_token: string }).access_token;
  const auth = { Authorization: `Bearer ${token}` };

  const listed = await request.get(`${API_BASE}/admin/clients`, {
    headers: auth,
  });
  expect(listed.ok()).toBeTruthy();
  const clients = ((await listed.json()) as { clients: Client[] }).clients;
  let beacon = clients.find(
    (c) => c.legal_name.toLowerCase() === "beacon labs",
  );

  if (!beacon) {
    const created = await request.post(`${API_BASE}/admin/clients`, {
      headers: auth,
      data: { legal_name: "Beacon Labs" },
    });
    expect(created.ok()).toBeTruthy();
    beacon = (await created.json()) as Client;
  }

  // Approve the registrable Beacon domain (409 = already approved — fine).
  const domainRes = await request.post(
    `${API_BASE}/admin/clients/${beacon.id}/domains`,
    { headers: auth, data: { domain: BEACON_DOMAIN } },
  );
  expect(
    domainRes.status() === 201 || domainRes.status() === 409,
    `approve ${BEACON_DOMAIN}: ${domainRes.status()}`,
  ).toBeTruthy();

  return beacon.id;
}

/** A unique Beacon-tenant email for a throwaway registration. */
function beaconEmail(): string {
  const stamp = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  return `bob+${stamp}@${BEACON_DOMAIN}`;
}

/** Point the admin's client switcher at `clientId` via the cookie route. */
async function setActiveClient(page: Page, clientId: string): Promise<void> {
  const res = await page.request.post("/api/active-client", {
    data: { clientId },
  });
  expect(res.ok()).toBeTruthy();
}

test("a Beacon-tenant client is denied admin URLs and sees no Atlas data", async ({
  page,
  request,
}) => {
  test.slow();
  await ensureBeaconTenant(request);

  // A real Beacon client self-registers on the approved Beacon domain.
  await register(page, "Bob Beacon", beaconEmail(), PASSWORD);
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible({
    timeout: 20000,
  });

  // 1. Admin-only URLs show the "Not authorized" page (never Atlas data). The
  //    /admin shell (admin/layout.tsx) gates on role for every /admin/* route.
  for (const adminUrl of ["/admin/risk-register", "/admin/queue"]) {
    await page.goto(adminUrl);
    await expect(
      page.getByRole("heading", { name: "Not authorized" }),
    ).toBeVisible({ timeout: 20000 });
    await expect(
      page.getByText(/restricted to Kentro consultants/i),
    ).toBeVisible();
    // No admin action leaked onto the refusal page.
    await expect(
      page.getByRole("button", { name: /Generate|Regenerate/ }),
    ).toHaveCount(0);
  }

  // 2a. The client's own assessment list is empty — no Atlas services leak in.
  const mine = await page.request.get("/api/proxy/intake/assessments");
  expect(mine.ok()).toBeTruthy();
  const services = (await mine.json()) as Array<{ service_id: string }>;
  for (const svc of services) {
    expect(
      ATLAS_SERVICE_IDS.has(svc.service_id),
      `Atlas service ${svc.service_id} must not appear in a Beacon client's list`,
    ).toBe(false);
  }

  // 2b. A direct fetch of an Atlas service is refused (not served as data).
  const crossTenant = await page.request.get(
    `/api/proxy/attack/services/${ATLAS_ATTACK_SERVICE_ID}/assessments/latest`,
  );
  expect(crossTenant.status(), "Beacon client fetching Atlas service").toBe(
    404,
  );

  // 2c. The rendered assessments surface shows no Atlas data.
  await page.goto("/assessments");
  await expect(
    page.getByRole("heading", { name: "My assessments" }),
  ).toBeVisible({ timeout: 20000 });
  const mainText = (
    await page.locator("#main-content").innerText()
  ).toLowerCase();
  expect(mainText).not.toContain("atlas");
});

test("an admin scoped to Beacon gets 404 (not data) for an Atlas service", async ({
  page,
  request,
}) => {
  test.slow();
  const beaconId = await ensureBeaconTenant(request);
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);

  // NOTE: navigating the admin *workspace URL* itself (/admin/services/<id>/...)
  // would auto-correct the active tenant — the workspace shell resolves a
  // service's owner via a deliberately cross-tenant admin lookup and switches to
  // it (EnsureActiveClient). That is an admin convenience, not a data leak. The
  // real isolation boundary is the tenant-scoped DATA plane (X-Client-Id), which
  // is what the proxy forwards from the active-client cookie — so we assert
  // there.

  // Admin active client = Beacon -> an Atlas service's data 404s.
  await setActiveClient(page, beaconId);
  const scopedToBeacon = await page.request.get(
    `/api/proxy/attack/services/${ATLAS_ATTACK_SERVICE_ID}/assessments/latest`,
  );
  expect(
    scopedToBeacon.status(),
    "admin scoped to Beacon must not receive Atlas data",
  ).toBe(404);

  // Control: switching the active client to Atlas serves the SAME URL (200),
  // proving the 404 above was tenant isolation, not a broken endpoint.
  await setActiveClient(page, ATLAS_CLIENT_ID);
  const scopedToAtlas = await page.request.get(
    `/api/proxy/attack/services/${ATLAS_ATTACK_SERVICE_ID}/assessments/latest`,
  );
  expect(
    scopedToAtlas.status(),
    "admin scoped to Atlas receives Atlas data",
  ).toBe(200);
});
