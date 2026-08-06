import { expect, test, type Page } from "@playwright/test";

import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  CLIENT_EMAIL,
  CLIENT_PASSWORD,
  signIn,
} from "../helpers/auth";
import { atlasClientId, atlasServiceId } from "../helpers/ids";

/**
 * SMOKE_TEST.md section 35: can the person looking at a surface tell what it is
 * for, what its notation means, and where a value came from?
 *
 * Four proofs, on four different surfaces:
 *   1. /admin/management says what the page is FOR before asking for input.
 *   2. /home explains the phase words a client sees on their service cards.
 *   3. /admin/risk-register attributes every entry's provenance on the row.
 *   4. An admin workspace discloses what AI drafts vs what code computes.
 *
 * Two of these span tenants, so each test signs in for itself rather than
 * sharing state — the suite is serialized (workers=1) and a leaked active-client
 * cookie is the classic cross-spec flake here.
 */

/** Align the admin session's active tenant, the way s8 does. */
async function setActiveClient(page: Page, clientId: string): Promise<void> {
  const res = await page.request.post("/api/active-client", {
    data: { clientId },
  });
  expect(res.ok(), "align active client").toBeTruthy();
}

/**
 * 1. Management purpose copy.
 *
 * The paragraph predates Sprint 10 (commit 0fe1096, 2026-06-25) but nothing
 * asserted it: s2-management.spec.ts drives the same page and pins the heading,
 * the create form and the domain list, never the sentence that says what the
 * page is for. So this bites — deleting the purpose line today breaks no test.
 * Source of record: apps/web/src/app/admin/management/page.tsx.
 */
test("the Management page says what it is for before it asks for anything", async ({
  page,
}) => {
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await page.goto("/admin/management");
  await expect(
    page.getByRole("heading", { name: "Management", exact: true }),
  ).toBeVisible({ timeout: 30000 });

  // The purpose names both halves of the job — create the company, then approve
  // the domains — which is the ordering the empty state also depends on.
  await expect(
    page.getByText(
      "Create client companies and approve the email domains their teams use to register.",
    ),
  ).toBeVisible();
});

/**
 * 2. Home status legend.
 *
 * The legend lives on the CLIENT home at /home (HomeDashboard), not on an admin
 * page, and it renders only when the tenant has at least one engagement — hence
 * the seeded Atlas client rather than a fresh registrant. It is a collapsed
 * <details>, so the body has to be opened before anything in it is visible.
 *
 * Scoping note: every phase label is ALSO a status pill on the service cards
 * above, so "In progress" and friends match twice once the legend is open. Every
 * assertion below is scoped to the legend list by its accessible name.
 * Source of record: apps/web/src/components/home/HomeDashboard.tsx PHASES.
 */
const PHASE_LEGEND: ReadonlyArray<readonly [string, string]> = [
  [
    "Getting started",
    "We have your request. Your analyst is setting the assessment up.",
  ],
  [
    "In progress",
    "The assessment is open. Anything that needs you is listed under Waiting on you.",
  ],
  [
    "Under review",
    "You have sent your answers in and your analyst is going through them.",
  ],
  [
    "Finalizing your report",
    "Your answers are settled and your analyst is writing the report up.",
  ],
  ["Report ready", "The report is released. Open it under your reports."],
];

test("a client can look up what each phase word on their home page means", async ({
  page,
}) => {
  await signIn(page, CLIENT_EMAIL, CLIENT_PASSWORD);
  await page.goto("/home");
  await expect(page.getByRole("heading", { name: /Welcome back/ })).toBeVisible(
    {
      timeout: 30000,
    },
  );

  const trigger = page.getByText("What each phase means");
  await expect(trigger).toBeVisible({ timeout: 30000 });
  await trigger.click();

  const legend = page.getByRole("list", { name: "What each phase means" });
  await expect(legend).toBeVisible();
  await expect(legend.getByRole("listitem")).toHaveCount(PHASE_LEGEND.length);

  // Every phase the cards can show is defined, and defined in plain language —
  // a legend listing the labels without their meanings would pass a count-only
  // check and fail here.
  for (const [i, [label, meaning]] of PHASE_LEGEND.entries()) {
    const item = legend.getByRole("listitem").nth(i);
    await expect(item).toContainText(label);
    await expect(item).toContainText(meaning);
  }
});

/**
 * 3. Risk Register provenance badge.
 *
 * Every seeded and generated entry badges: routes/risk.py:270 is the only writer
 * of RiskEntry.origin and always passes "ai_generated" (the model default is the
 * same string), so OriginCell's non-AI branch is unreachable against a real API.
 * This asserts the badge IS present and attributed; it deliberately does NOT
 * assert an unbadged consultant row, because no such row can exist yet.
 *
 * The badge text is "AI-drafted", not "AI-suggested" — source of record is
 * apps/web/src/components/admin/risk/RiskRegisterDashboard.tsx OriginCell.
 */
test("every Risk Register entry carries its provenance on the row", async ({
  page,
}) => {
  test.slow();
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  await setActiveClient(page, await atlasClientId(page));
  await page.goto("/admin/risk-register");
  await expect(
    page.getByRole("heading", { name: "Risk Register", exact: true }),
  ).toBeVisible({ timeout: 60000 });

  // Scope to the register table: the 5x5 heat matrix on this page is also a
  // <table>, so an unscoped row count would mix the two.
  const register = page
    .getByRole("table")
    .filter({ has: page.getByRole("columnheader", { name: "Provenance" }) });
  await expect(register).toBeVisible({ timeout: 30000 });

  // The badge repeats once per entry, so count rather than match a single node.
  const badges = register.getByText("AI-drafted");
  await expect(badges.first()).toBeVisible({ timeout: 30000 });
  const badgeCount = await badges.count();
  expect(badgeCount).toBeGreaterThan(0);

  // The badge names the trust level as well as the origin, and its title carries
  // the raw wire values a consultant can quote back at the API.
  await expect(badges.first()).toHaveText("AI-drafted · Admin Assisted");
  await expect(badges.first()).toHaveAttribute(
    "title",
    "origin ai_generated, trust admin_assisted",
  );

  // Provenance is on EVERY rendered entry, not just the first: one badge per
  // data row. A single attributed row among many unattributed ones would pass
  // the .first() assertions above and fail here.
  const dataRowCount = (await register.getByRole("row").count()) - 1;
  expect(dataRowCount).toBeGreaterThan(0);
  expect(badgeCount).toBe(dataRowCount);
});

/**
 * 4. The HowAiWorks disclosure.
 *
 * Proven on the ATT&CK workspace, one of its four mount sites (Tech Debt, ATT&CK,
 * CSF, ZT). It is a collapsed <details> inside a role="group" labelled "How AI is
 * used here", so the body is not visible until the summary is clicked — and the
 * summary names the AI purpose the page runs, which is what ties the disclosure
 * to the button beside it.
 *
 * The seeded ATT&CK assessment is RELEASED, which is enough: the disclosure
 * renders whenever an assessment exists, so no draft has to be minted.
 * Source of record: apps/web/src/components/admin/HowAiWorks.tsx.
 */
test("an admin workspace discloses what AI drafts, what code computes, and what leaves the API", async ({
  page,
}) => {
  test.slow();
  await signIn(page, ADMIN_EMAIL, ADMIN_PASSWORD);
  const attackServiceId = await atlasServiceId(page, "attack_coverage");
  await page.goto(`/admin/services/${attackServiceId}/attack-coverage`);
  await expect(
    page.getByRole("heading", { name: "MITRE ATT&CK Coverage" }),
  ).toBeVisible({ timeout: 30000 });

  const disclosure = page.getByRole("group", { name: "How AI is used here" });
  await expect(disclosure).toBeVisible({ timeout: 30000 });

  // The summary names THIS page's AI purpose, so the disclosure cannot be a
  // generic blurb pasted onto every workspace.
  const trigger = disclosure.getByText("How AI is used here (mitre_map)");
  await expect(trigger).toBeVisible();
  // Collapsed by default: the body is present in the DOM but not shown.
  await expect(disclosure.getByText("What AI drafts here")).toBeHidden();
  await trigger.click();

  for (const term of [
    "What AI drafts here",
    "What code computes",
    "Before a prompt leaves",
    "Fixture mode and live mode",
  ]) {
    await expect(disclosure.getByText(term, { exact: true })).toBeVisible();
  }

  // The ATT&CK-specific split of the "AI suggests, code computes" boundary.
  await expect(disclosure).toContainText(
    "A coverage status per technique, plus the detection, prevention, and response tooling behind it",
  );
  await expect(disclosure).toContainText(
    "The tactic heatmap, the coverage counts, and the deliverable's remediation priorities are computed from the coverage rows you save.",
  );
  // Redaction, and that only counts of what was removed are kept.
  await expect(disclosure).toContainText(
    "Every prompt passes through one redactor before it leaves the API.",
  );
  await expect(disclosure).toContainText(
    "Only counts of what was removed are recorded, never the text.",
  );
  // And the honest limit on what approving an assessment means.
  await expect(disclosure).toContainText(
    "A drafted value carries no sign-off. Approving the assessment records that you approved that version, not that you read each drafted field.",
  );
});
