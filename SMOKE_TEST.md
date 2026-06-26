# SHIELD v2 — Pre-Prod Smoke Test

A human runtime pass over the core flows. The deterministic logic is unit-tested;
this covers what needs eyes on a running app (UI, navigation, generated
documents, live AI). Work top-to-bottom in one sitting.

## 0. Bring-up

- [ ] Copy `.env.example` → `.env`; set `NEXTAUTH_SECRET` (a long random string).
- [ ] `docker-compose up --build`; wait for `db`, `minio`, `keycloak`, `api`, `web` to report healthy.
- [ ] API docs load: `http://localhost:8000/docs`.
- [ ] Web loads: `http://localhost:3000` (marketing home renders, no console errors).
- [ ] No `worker` service starts — AI is synchronous (confirm none is referenced).

## 1. Onboarding & auth (A1, A3, B1)

- [ ] Register the **first** user → becomes **admin** (bootstrap).
- [ ] As admin, create a client (e.g. "Acme") and approve a domain (e.g. `acme.test`).
- [ ] Register a user whose email is **not** on any approved domain → **rejected**.
- [ ] Register a user `@acme.test` → joins Acme as a **client** role.
- [ ] Sign out / sign in works; session persists on refresh.
- [ ] Client user sees **no** "Deliverables"/admin links anywhere (A1).
- [ ] No "reviewer" role exists anywhere in the UI (A3).

## 2. Admin management (B2)

- [ ] `/admin/management`: create another client + add/remove a domain; list reflects changes.
- [ ] Client switcher works; the active client scopes what admin sees.

## 3. Intake & client self-assessment (C6, C8, A2, A4)

- [ ] As a client, run intake; UI says "**assessment**" everywhere (not "engagement") (A2).
- [ ] Open a CSF self-assessment → questions are the **verbatim** interview prompts (C8); fill a few, **Save-and-exit**, return → answers persist.
- [ ] Repeat for a ZT (CISA) self-assessment; **DoD ZT shows only 3 levels** (A4).
- [ ] Submit a self-assessment → status moves to submitted / under review.

## 4. Tech Debt service (D1)

- [ ] Admin opens / extracts a Tech Debt capability list.
- [ ] **Dashboard row** shows: capabilities count, annual cost, categories, to-consolidate/cut, low-confidence rows.
- [ ] Edit a capability cell → its AI-confidence badge clears (human-curated).

## 5. ATT&CK service (D2, C2)

- [ ] Start an assessment; matrix + **heatmap** render.
- [ ] Click **Run AI (mitre_map)** → "Updated N fields across M techniques"; matrix/heatmap refresh.
- [ ] Open a technique panel → **D/P/R tool chips + rationale** show; **Lock** checkbox toggles.
- [ ] Lock a technique, Run AI again → locked row **unchanged** + absent from "what changed" (C2).
- [ ] Approve → workspace goes read-only.

## 6. Zero Trust service (D3)

- [ ] Questionnaire renders by pillar; set a capability's **current** and **Target**.
- [ ] **Run AI (zt_score)** → current/target suggestions applied (DoD clamps to ≤3).
- [ ] Gap list reflects per-capability targets; **12-month roadmap** card groups gaps by month.

## 7. CSF full Playbook (D4)

- [ ] Admin reviews the client's CSF self-assessment.
- [ ] In the **Playbook panel**: **Seed Working Profiles** → ~106 subcats × tiers.
- [ ] **Run AI (csf_score)** → dimensions + narrative drafted.
- [ ] **Dimension editor**: pick tier + subcategory, set the five 0/1/2 scores, toggle **Evidence on file** → confirm **total/level/cap** update live (no-evidence caps level ≤ 2).
- [ ] **Enterprise roll-up** table: each subcategory shows tier levels, enterprise level, **rule #**, target, gap, **P1/P2/P3**.
- [ ] **Export** → 5 files appear (XLSX, exec PDF/Word, full PDF/Word) with download links.

## 8. Risk Register (E)

- [ ] `/admin/risk-register` for a client with **only** ATT&CK → **locked** state lists what's missing.
- [ ] Add a CSF or ZT assessment → gate **unlocks**.
- [ ] **Generate** → entries appear; **tier is code-derived** (e.g. High × Catastrophic = Critical); KPI cards + **5×5 heatmap** render; cited links are only ones from the client's assessments.
- [ ] **Regenerate** → version increments.
- [ ] **Export** → XLSX/PDF/Word download.

## 9. Messaging (C7)

- [ ] On a service workspace (admin) and the client's self-assessment page, the **message thread** shows.
- [ ] Client posts a message → appears for admin; admin replies → appears for client.
- [ ] `/admin/messages` **inbox** lists threads with **"N new"** unread badges; opening a thread clears its unread.

## 10. Exports & documents — eyeball each file

The part only a human can do — confirm the documents actually _look_ right.

- [ ] **CSF executive briefing** PDF: cover, exec summary, scorecard with **colored maturity cells**, top gaps, next steps — spacing / page-breaks look right.
- [ ] **CSF full playbook** PDF: contents, methodology, per-function tables, appendix; colors render.
- [ ] Both **CSF .docx** files in Word: tables + **shaded level cells** render.
- [ ] **CSF .xlsx**: Enterprise sheet + per-tier sheets + About cover.
- [ ] **Risk Register** XLSX / PDF / Word: 5×5 matrix + entries + blank governance columns.

## 11. Auto-versioned docs (C3)

- [ ] After a Run-AI on any service, the workspace shows the **"regenerate to refresh"** nudge.
- [ ] Finalize / export → nudge clears on reload.

## 12. Navigation / a11y / no-dead-ends (C6, F)

- [ ] Every admin + client page has top-nav; **no 404s** clicking around.
- [ ] **Tab** from page load → first focusable is **"Skip to content"**; activating it jumps to `#main-content` (test on admin + on `/account`, `/messages`, `/assessments`).
- [ ] Keyboard-navigate a workspace (radios, selects, buttons all reachable/operable).
- [ ] Each terminal state has an onward link (no dead ends).

## 13. Access control & tenant isolation (F)

- [ ] As a **client** user, hitting an admin URL (e.g. `/admin/risk-register`) is blocked.
- [ ] As admin, switch to client **B** and open client **A**'s service URL → **404**, not data.
- [ ] Client never sees another client's data anywhere.

## 14. Live AI (optional but recommended)

- [ ] Set `ANTHROPIC_API_KEY` (and `SHIELD_LLM_MODE=live`) in `.env`; restart `api`.
- [ ] Run **one** Run-AI (e.g. csf_score) → real suggestions return; `llm_calls` has a logged, **redacted** entry; no PII in the log.

## 15. Security headers

- [ ] `curl -I http://localhost:3000`: confirm **CSP**, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Strict-Transport-Security`, `Permissions-Policy`.
- [ ] App still functions under CSP (no blocked resources in the console).

---

## Sign-off

- [ ] All core flows pass
- [ ] Documents look right
- [ ] No cross-tenant leak
- [ ] No stack traces in `api` logs
- [ ] **Ready for prod**
