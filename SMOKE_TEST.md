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

- [x] `/admin/management`: create another client + add/remove a domain; list reflects changes. (s2-management.spec.ts drives the `/admin/management` UI ITSELF, not the admin API: creates a timestamped client via the form, approves a `.example` domain, asserts both reflected in the rendered list, removes the domain, asserts the removal reflected.)
- [x] Client switcher works; the active client scopes what admin sees. (s13-isolation.spec.ts — the active-client switch is driven via the `/api/active-client` cookie API, not the UI widget; the scoping itself — X-Client-Id data plane — is fully asserted)

## 3. Intake & client self-assessment (C6, C8, A2, A4)

- [x] As a client, run intake; UI says "**assessment**" everywhere (not "engagement") (A2). (s3-selfassessment.spec.ts)
- [x] Open a CSF self-assessment; fill a few, **Save-and-exit**, return → answers persist. (s3-selfassessment.spec.ts persist test — reopens the exact created draft)
- [x] CSF questions are the **verbatim** interview prompts (C8). (s3-selfassessment.spec.ts — "CSF questionnaire renders the verbatim subcategory outcome prompts" asserts the rendered GV.OC-01/02/03 outcome text matches the catalog VERBATIM. Source of record: apps/api/app/csf/catalog.py SUBCATEGORIES — the deterministic CSF catalog the questionnaire renders from, transcribing the canonical NIST CSF 2.0 Final outcome statements; SHIELDv2_Master_Spec.txt §7 defines the subcategory model, not the per-item text.)
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

> **Ready for review:** s7/s8 save 8 generated artifacts to `e2e/artifacts/`
> (gitignored). As of Sprint 3 T4 every download name follows Master Spec §15.5
> — `{Company}_{Service}{MMDDYY}(_v{n})?(_{variant})?.{ext}` — so the files now
> land as e.g. `Atlas_Defense_Solutions_CSF_Playbook070926_v18.xlsx`,
> `…_v18_Executive.pdf/.docx`, `…_v18_Full.pdf/.docx`, and
> `Atlas_Defense_Solutions_Risk_Register070926_v20.xlsx/.pdf/.docx` (date +
> version vary per run; v1 carries no `_v{n}` suffix). Each was asserted HTTP 200
> with the correct content-type; **eyeballed by David 2026-07-09** against the
> `Atlas_Defense_Solutions_*` v19 (CSF) / v22 (Risk Register) artifact set.

- [x] **CSF executive briefing** PDF: cover, exec summary, scorecard with **colored maturity cells**, top gaps, next steps — spacing / page-breaks look right. (David, 2026-07-09)
- [x] **CSF full playbook** PDF: contents, methodology, per-function tables, appendix; colors render. (David, 2026-07-09)
- [x] Both **CSF .docx** files in Word: tables + **shaded level cells** render. (David, 2026-07-09)
- [x] **CSF .xlsx**: Enterprise sheet + per-tier sheets + About cover. (David, 2026-07-09)
- [x] **Risk Register** XLSX / PDF / Word: 5×5 matrix + entries + blank governance columns. (David, 2026-07-09)

## 11. Auto-versioned docs (C3)

- [x] After a Run-AI on any service, the workspace shows the **"regenerate to refresh"** nudge. (s11-staleness.spec.ts)
- [x] Finalize / export → nudge clears on reload. (s11-staleness.spec.ts — approve + finalize clears the nudge)

## 12. Navigation / a11y / no-dead-ends (C6, F)

- [ ] Every admin + client page has top-nav; **no 404s** clicking around.
- [x] **Tab** from page load → first focusable is **"Skip to content"**; activating it jumps to `#main-content` (test on admin + on `/account`, `/messages`, `/assessments`). (s12-a11y-nav.spec.ts — asserts hash becomes `#main-content` AND focus lands ON the landmark; the final-audit pass added `tabindex="-1"` to every `<main id=main-content>` per WAI-ARIA skip-link practice)
- [x] Keyboard-navigate a workspace (radios, selects, buttons all reachable/operable). (s12-a11y-nav.spec.ts — CSF radio Space-to-answer + submit button enabled, plus arrow-key roving-tabindex on the TierPicker radiogroup (ArrowRight moves focus + follows `tabindex`, wraps at the ends) added in S2 T6; `select` controls are not keyboard-driven by the spec)
- [x] Each terminal state has an onward link (no dead ends). (s12-notfound.spec.ts — 404 recovery links asserted; the admin not-authorized state renders onward links via `admin/layout.tsx` with its copy asserted in s13; other terminal states are not enumerated)

> **a11y roving-tabindex — FIXED in S2 T6** (`137727b`; asserted green by
> s12-a11y-nav.spec.ts): `TierPicker` / `ZtStagePicker` now implement WAI-ARIA
> radiogroup roving-tabindex — the selected radio (or the first, if none) is the
> sole `tabIndex=0` and Arrow Right/Down / Left/Up move focus with wrap. Focus
> movement does NOT auto-select (select stays on Space/Enter/click) so the
> auto-save PATCH is not flooded — see the inline comment in the components. The
> risk heatmap likelihood labels also gained `scope="row"` so Chromium exposes
> them as `rowheader` (s8 asserts `getByRole('rowheader')`). (The earlier
> skip-link landmark-focus gap was FIXED in the final-audit pass: `tabindex=-1`
> on every `main#main-content`.)

## 13. Access control & tenant isolation (F)

- [x] As a **client** user, hitting an admin URL (e.g. `/admin/risk-register`) is blocked. (s13-isolation.spec.ts — renders "Not authorized", not data)
- [x] As admin, switch to client **B**: client **A**'s data is unreachable on the B-scoped data plane → **404**, not data. (s13-isolation.spec.ts — X-Client-Id data plane: Beacon active → Atlas latest 404. NOTE the original "open A's service URL → 404" wording does not match the shipped app: navigating an admin *workspace URL* deliberately auto-switches the active client to the service's owner (`EnsureActiveClient`, an admin convenience — Kentro consultants serve all tenants) and then shows data. The security boundary is the server-side X-Client-Id scoping, which IS asserted.)
- [x] Client never sees another client's data anywhere. (s13-isolation.spec.ts — client is server-side scoped to its own client_id; cross-tenant GETs return 404 / empty)

## 14. Live AI (optional but recommended)

> **Provider-agnostic (Sprint 4 T6):** the live path is now selectable across
> `anthropic` / `openai` / `gemini` via `SHIELD_LLM_PROVIDER` (D-024). The egress
> contract is identical for all three — redaction and the `llm_calls` audit row
> run above the provider seam — so this check proves the *selected* provider,
> whichever it is. Left **unchecked on purpose**: it needs a real API key on
> David's machine; no committed spec can prove it, and the fixture-mode suite
> (D-017) does not exercise any live provider path.

- [ ] Set `SHIELD_LLM_MODE=live`, `SHIELD_LLM_PROVIDER=<anthropic|openai|gemini>`, that provider's key (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY`), and a matching `SHIELD_LLM_MODEL` (e.g. `claude-opus-4-7` / `gpt-4o-mini` / `gemini-1.5-pro`) in `.env`; restart `api`.
- [ ] Run **one** Run-AI (e.g. csf_score) → real suggestions return; `llm_calls` has a logged, **redacted** entry with the correct **`provider`**/**`model`** and a **`client_id`** set (Sprint 3 T5 tenant attribution); no PII in the log.
- [ ] Selecting a provider with its key unset, or a not-implemented provider (`azure_openai`/`bedrock`/`local`), fails loudly at startup — no silent fallback.

## 15. Security headers

- [x] `curl -I http://localhost:3000`: confirm **CSP**, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Strict-Transport-Security`, `Permissions-Policy`. (s15-headers.spec.ts — all six present, set in `apps/web/next.config.mjs`)
- [x] App still functions under CSP (no blocked resources in the console). (s15-headers.spec.ts — signed-in admin dashboard shows zero CSP-blocked resources)

## 16. Deliverable release flow (Sprint 5, §12 / §6.7 — T1)

The §12 release rule: a client sees a deliverable ONLY after a consultant
explicitly releases the finalized deliverable. Backend contract (release route,
client list, artifact access) is `pytest -m unit` covered; the runtime effects
below are e2e-proven.

- [x] Admin finalizes a deliverable, then **releases** it; a real client of that tenant sees the released row. (s17-documents.spec.ts — API finalize+release v1, client sees the row)
- [x] A **finalized-but-unreleased** deliverable never appears for the client. (s17-documents.spec.ts — v2 finalized, left unreleased, absent from the client page)
- [x] A client can **download** an artifact of a released own-tenant deliverable (200 + §15.5 filename). (s17-documents.spec.ts — client PDF download 200, content-disposition carries the §15.5 name)
- [ ] Release requires `finalized_at` (typed 409 `not_finalized`); re-release is an idempotent 200 no-op; audit row `*.deliverable.released` written; artifact deny paths (unreleased / cross-tenant / non-deliverable). (`pytest -m unit` contract tests, not an e2e checkbox — no runtime UI eyeball surface)

## 17. Client `/documents` — WHAT YOU'VE RECEIVED (Sprint 5, §6.7 — T2)

- [x] Client nav gains a **Documents** entry; the page lists released deliverables (service label, title, **Final** badge). (s17-documents.spec.ts)
- [x] Per-format **download link** streams 200 with a §15.5 filename. (s17-documents.spec.ts — PDF download 200, `application/pdf`, §15.5 content-disposition)
- [ ] Empty state renders per the no-dead-ends rule when a client has no released deliverables (§12). (built; not asserted by a dedicated spec — the s17 tenant always has a released row)

## 18. Client `/home` dashboard + value-loop card (Sprint 5, §6.4 / §2.5 — T3/T4)

- [x] Client with **no** released report sees next-step guidance (Welcome heading + "Start an assessment"), **not** the "report is ready" hero. (s18-home.spec.ts — hero-absent guidance state)
- [x] After a release, the same client's `/home` shows the **hero** ("report is ready" + View reports / Download PDF). (s18-home.spec.ts — hero-present state)
- [x] A signed-in **client** hitting `/` lands on `/home`; a signed-in **admin** lands on `/admin`. (s18-home.spec.ts — both role landings)
- [x] `/home` leaks **no scoring math** (§6.4) — no percentage renders. (s18-home.spec.ts — `/\d+%/` count 0)
- [x] **Value-loop card** (§2.5) is absent before any release and, after a scored+released CSF, renders a **NIST CSF 2.0** gap count with **Pending** for services lacking released data (never a fake 0). (s19-value-loop.spec.ts)
- [x] The value card leaks no scoring math — no percentage renders. (s19-value-loop.spec.ts — `/\d+%/` count 0)

## 19. CSF POA&M / action plan (Sprint 5, step 10 — T5)

- [x] The gap-analysis view renders an **action-plan editor** card per enterprise gap; Characterize (accept/mitigate/transfer/avoid) + owner **auto-save** and survive a `page.reload()`. (s7-csf-playbook.spec.ts — `gap-action-{code}` card, `selectOption("mitigate")` + owner blur each waits on the gap-actions PUT, values survive reload)
- [ ] The playbook **XLSX** gains an **Action Plan** sheet (characterization / owner / deadline / resources / success criteria / poam_ref; priority defaults from `gap_priority()`, override wins). (`pytest -m unit` export-content test; the s7 5-file export assertion covers download presence, not the sheet's cell content — that stays a §10 human eyeball item)

## 20. Redaction preview gate (Sprint 5 — T6)

- [x] From a Run-AI surface, the **offered** "preview what will be sent" affordance shows the **redacted payload** + **removed counts** WITHOUT egress, then Run-AI still works. (s7-csf-playbook.spec.ts — `ai-preview-button` → POST `/ai/preview`, payload has `subcategories`, `ai-preview-removed-total` visible, then the real Run-AI runs)
- [ ] Preview creates **no** `llm_calls` row and constructs no provider; admin-only; the AI rate limiter applies; preview output equals `redact_payload()` of the run-ai builder's payload for the same state. (`pytest -m unit` contract tests — no runtime eyeball surface for the "no row created" invariant)

## 21. `/admin/audit` viewer (Sprint 5 — T7)

- [x] Admin nav gains **Audit**; the page renders the **Audit log** two-tab viewer (Activity / AI calls). (s20-audit.spec.ts)
- [x] An audited action performed in-test (`csf.run_ai`) appears in the **Activity** tab (filter by action prefix). (s20-audit.spec.ts)
- [x] The **AI calls** tab lists the fixture-mode `llm_calls` row (purpose `csf_score`, `fixture`). (s20-audit.spec.ts)
- [x] **Correlation-id click-through** links the two tabs (clicking an AI call's correlation jumps to Activity filtered by that id). (s20-audit.spec.ts)
- [x] The viewer is **read-only** — no mutation affordances on the append-only store. (s20-audit.spec.ts — only filter/apply/clear controls; construction-level per T7)
- [ ] Every filter (target_type, actor, date range / client_id, provider, status) and cursor pagination; client-role 403. (`pytest -m unit` filter/pagination contract tests)

---

## Sign-off

- [ ] All core flows pass
- [ ] Documents look right
- [ ] No cross-tenant leak
- [ ] No stack traces in `api` logs
- [ ] **Ready for prod**
