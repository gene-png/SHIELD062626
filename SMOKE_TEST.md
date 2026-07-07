# SHIELD v2 — Pre-Prod Smoke Test

A human runtime pass over the core flows. The deterministic logic is unit-tested;
this covers what needs eyes on a running app (UI, navigation, generated
documents, live AI). Work top-to-bottom in one sitting.

> **Automation note (sprint-1 smoke sweep):** items annotated `(sN-*.spec.ts)`
> are now covered by a green Playwright smoke spec under `e2e/smoke/`. Run the
> whole suite with `cd e2e && npx playwright test`. Items left unchecked still
> need a human: section 10 (eyeball generated documents), section 14 (one
> live-AI run with a real key), plus a few UI-visibility nuances noted inline.

## 0. Bring-up

- [ ] Copy `.env.example` → `.env`; set `NEXTAUTH_SECRET` (a long random string).
- [ ] `docker-compose up --build`; wait for `db`, `minio`, `keycloak`, `api`, `web` to report healthy.
- [ ] API docs load: `http://localhost:8000/docs`.
- [x] Web loads: `http://localhost:3000` (marketing home renders, no console errors). (s0-home.spec.ts)
- [ ] No `worker` service starts — AI is synchronous (confirm none is referenced).

## 1. Onboarding & auth (A1, A3, B1)

- [ ] Register the **first** user → becomes **admin** (bootstrap).
- [ ] As admin, create a client (e.g. "Acme") and approve a domain (e.g. `acme.test`).
- [x] Register a user whose email is **not** on any approved domain → **rejected**. (s1-signup-errors.spec.ts)
- [x] Register a user `@acme.test` → joins as a **client** role. (s3-selfassessment.spec.ts registers `qa+<stamp>@atlas.example`; s13-isolation.spec.ts proves a fresh approved-domain registrant gets the **client** role — `/admin/*` renders "Not authorized" for them)
- [ ] Sign out / sign in works; session persists on refresh.
- [x] Client user sees **no** "Deliverables"/admin links anywhere (A1). (s3-selfassessment.spec.ts — zero admin/deliverables links on the client shell `/assessments`; s13-isolation.spec.ts — admin URLs blocked. "Anywhere" is not an exhaustive crawl of every page.)
- [x] No "reviewer" role exists anywhere in the UI (A3). (s0-home.spec.ts asserts the home copy; T1 additionally verified a repo-wide grep — zero "reviewer" matches anywhere in `apps/web/src`)

## 2. Admin management (B2)

- [ ] `/admin/management`: create another client + add/remove a domain; list reflects changes. (PARTIAL: client creation + domain approval exercised via the same admin API the UI calls, in s13-isolation.spec.ts setup. The `/admin/management` UI itself, domain REMOVAL, and list-reflects-changes are NOT exercised — needs a human pass or a follow-up spec.)
- [x] Client switcher works; the active client scopes what admin sees. (s13-isolation.spec.ts — the active-client switch is driven via the `/api/active-client` cookie API, not the UI widget; the scoping itself — X-Client-Id data plane — is fully asserted)

## 3. Intake & client self-assessment (C6, C8, A2, A4)

- [x] As a client, run intake; UI says "**assessment**" everywhere (not "engagement") (A2). (s3-selfassessment.spec.ts)
- [x] Open a CSF self-assessment; fill a few, **Save-and-exit**, return → answers persist. (s3-selfassessment.spec.ts persist test — reopens the exact created draft)
- [ ] CSF questions are the **verbatim** interview prompts (C8). (NOT asserted by any spec — comparing rendered text to the master-spec prompt source needs a human eye or a follow-up fixture)
- [x] **DoD ZT shows only 3 levels** (A4). (s3-selfassessment.spec.ts — DoD ZtStagePicker asserts exactly 3 radios. NOTE: only the DoD client questionnaire is run; a CISA *client self-assessment* pass is not exercised — CISA is covered admin-side in s6-zt.spec.ts.)
- [x] Submit a self-assessment → status moves to submitted / under review. (s3-selfassessment.spec.ts submit test)

## 4. Tech Debt service (D1)

- [x] Admin opens / extracts a Tech Debt capability list. (s4-techdebt.spec.ts)
- [x] **Dashboard row** shows: capabilities count, annual cost, categories, to-consolidate/cut, low-confidence rows. (s4-techdebt.spec.ts — asserts the KPI cards render with their labels; the numeric values are not cross-checked against the uploaded data)
- [x] Edit a capability cell → its AI-confidence badge clears (human-curated). (s4-techdebt.spec.ts)

## 5. ATT&CK service (D2, C2)

- [x] Start an assessment; matrix + **heatmap** render. (s5-attack.spec.ts)
- [x] Click **Run AI (mitre_map)** → "Updated N fields across M techniques"; matrix/heatmap refresh. (s5-attack.spec.ts)
- [x] Open a technique panel → **D/P/R tool chips + rationale** show; **Lock** checkbox toggles. (s5-attack.spec.ts)
- [x] Lock a technique, Run AI again → locked row **unchanged** + absent from "what changed" (C2). (s5-attack.spec.ts)
- [ ] Approve → workspace goes read-only.

## 6. Zero Trust service (D3)

- [x] Questionnaire renders by pillar; set a capability's **current** and **Target**. (s6-zt.spec.ts)
- [x] **Run AI (zt_score)** → current/target suggestions applied (DoD clamps to ≤3). (s6-zt.spec.ts)
- [x] Gap list reflects per-capability targets; **12-month roadmap** card groups gaps by month. (s6-zt.spec.ts — spot-checks: gap list renders against the target stage + roadmap shows "Month N" groups; not every capability/month is cross-checked)

## 7. CSF full Playbook (D4)

- [ ] Admin reviews the client's CSF self-assessment.
- [x] In the **Playbook panel**: **Seed Working Profiles** → ~106 subcats × tiers. (s7-csf-playbook.spec.ts — enterprise roll-up = 106 rows)
- [x] **Run AI (csf_score)** → dimensions + narrative drafted. (s7-csf-playbook.spec.ts)
- [x] **Dimension editor**: pick tier + subcategory, set the five 0/1/2 scores, toggle **Evidence on file** → confirm **total/level/cap** update live (no-evidence caps level ≤ 2). (s7-csf-playbook.spec.ts — evidence-cap math asserted)
- [x] **Enterprise roll-up** table: each subcategory shows tier levels, enterprise level, **rule #**, target, gap, **P1/P2/P3**. (s7-csf-playbook.spec.ts — 106-row table asserted; the full column contract (rule #, gap_priority P2) is verified end-to-end for one representative row, not per-subcategory)
- [x] **Export** → 5 files appear (XLSX, exec PDF/Word, full PDF/Word) with download links. (s7-csf-playbook.spec.ts — all 5 downloaded to `e2e/artifacts/`)

## 8. Risk Register (E)

- [x] `/admin/risk-register` for a client with **only** ATT&CK → **locked** state lists what's missing. (s8-risk-register.spec.ts)
- [x] Add a CSF or ZT assessment → gate **unlocks**. (s8-risk-register.spec.ts — adds ZT service, unlocks on reload)
- [x] **Generate** → entries appear; **tier is code-derived** (e.g. High × Catastrophic = Critical); KPI cards + **5×5 heatmap** render; cited links are only ones from the client's assessments. (s8-risk-register.spec.ts — engine tier mirror asserted per entry)
- [x] **Regenerate** → version increments. (s8-risk-register.spec.ts — delta-asserts version bump)
- [x] **Export** → XLSX/PDF/Word download. (s8-risk-register.spec.ts — all 3 downloaded to `e2e/artifacts/`)

## 9. Messaging (C7)

- [x] On a service workspace (admin) and the client's self-assessment page, the **message thread** shows. (s9-messaging.spec.ts)
- [x] Client posts a message → appears for admin; admin replies → appears for client. (s9-messaging.spec.ts — two-context round-trip)
- [x] `/admin/messages` **inbox** lists threads with **"N new"** unread badges; opening a thread clears its unread. (s9-messaging.spec.ts)

## 10. Exports & documents — eyeball each file

The part only a human can do — confirm the documents actually _look_ right.

> **Ready for review:** the sprint-1 sweep saved 8 generated artifacts to
> `e2e/artifacts/` (gitignored) — `CSF_Playbook_v8.xlsx`,
> `CSF_Playbook_v8_Executive.pdf/.docx`, `CSF_Playbook_v8_Full.pdf/.docx`, and
> `Risk_Register_v5.xlsx/.pdf/.docx`. Each was asserted HTTP 200 with the correct
> content-type; the visual eyeball below still needs David.

- [ ] **CSF executive briefing** PDF: cover, exec summary, scorecard with **colored maturity cells**, top gaps, next steps — spacing / page-breaks look right.
- [ ] **CSF full playbook** PDF: contents, methodology, per-function tables, appendix; colors render.
- [ ] Both **CSF .docx** files in Word: tables + **shaded level cells** render.
- [ ] **CSF .xlsx**: Enterprise sheet + per-tier sheets + About cover.
- [ ] **Risk Register** XLSX / PDF / Word: 5×5 matrix + entries + blank governance columns.

## 11. Auto-versioned docs (C3)

- [x] After a Run-AI on any service, the workspace shows the **"regenerate to refresh"** nudge. (s11-staleness.spec.ts)
- [x] Finalize / export → nudge clears on reload. (s11-staleness.spec.ts — approve + finalize clears the nudge)

## 12. Navigation / a11y / no-dead-ends (C6, F)

- [ ] Every admin + client page has top-nav; **no 404s** clicking around.
- [x] **Tab** from page load → first focusable is **"Skip to content"**; activating it jumps to `#main-content` (test on admin + on `/account`, `/messages`, `/assessments`). (s12-a11y-nav.spec.ts — asserts hash becomes `#main-content` AND focus lands ON the landmark; the final-audit pass added `tabindex="-1"` to every `<main id=main-content>` per WAI-ARIA skip-link practice)
- [x] Keyboard-navigate a workspace (radios, selects, buttons all reachable/operable). (s12-a11y-nav.spec.ts — spot-check: CSF radio Space-to-answer + submit button enabled; `select` controls are not keyboard-driven by the spec)
- [x] Each terminal state has an onward link (no dead ends). (s12-notfound.spec.ts — 404 recovery links asserted; the admin not-authorized state renders onward links via `admin/layout.tsx` with its copy asserted in s13; other terminal states are not enumerated)

> **Minor a11y gap logged as backlog** (specs assert the real, shipped behavior
> and are green): TierPicker / ZtStagePicker radios are individually
> Tab-reachable and Space/Enter-operable but lack arrow-key roving-tabindex
> within the radiogroup. (The skip-link landmark-focus gap noted here previously
> was FIXED in the final-audit pass: `tabindex=-1` on every `main#main-content`.)

## 13. Access control & tenant isolation (F)

- [x] As a **client** user, hitting an admin URL (e.g. `/admin/risk-register`) is blocked. (s13-isolation.spec.ts — renders "Not authorized", not data)
- [x] As admin, switch to client **B**: client **A**'s data is unreachable on the B-scoped data plane → **404**, not data. (s13-isolation.spec.ts — X-Client-Id data plane: Beacon active → Atlas latest 404. NOTE the original "open A's service URL → 404" wording does not match the shipped app: navigating an admin *workspace URL* deliberately auto-switches the active client to the service's owner (`EnsureActiveClient`, an admin convenience — Kentro consultants serve all tenants) and then shows data. The security boundary is the server-side X-Client-Id scoping, which IS asserted.)
- [x] Client never sees another client's data anywhere. (s13-isolation.spec.ts — client is server-side scoped to its own client_id; cross-tenant GETs return 404 / empty)

## 14. Live AI (optional but recommended)

- [ ] Set `ANTHROPIC_API_KEY` (and `SHIELD_LLM_MODE=live`) in `.env`; restart `api`.
- [ ] Run **one** Run-AI (e.g. csf_score) → real suggestions return; `llm_calls` has a logged, **redacted** entry; no PII in the log.

## 15. Security headers

- [x] `curl -I http://localhost:3000`: confirm **CSP**, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Strict-Transport-Security`, `Permissions-Policy`. (s15-headers.spec.ts — all six present, set in `apps/web/next.config.mjs`)
- [x] App still functions under CSP (no blocked resources in the console). (s15-headers.spec.ts — signed-in admin dashboard shows zero CSP-blocked resources)

---

## Sign-off

- [ ] All core flows pass
- [ ] Documents look right
- [ ] No cross-tenant leak
- [ ] No stack traces in `api` logs
- [ ] **Ready for prod**
