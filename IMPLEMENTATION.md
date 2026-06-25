# SHIELD v2 — Implementation Plan

| | |
|---|---|
| **Version** | v1 |
| **Date** | 2026-06-24 |
| **Repo (this snapshot)** | `C:\repos\SHIELD062426v1` (copy of `SHIELD061626v1`) |
| **Branch** | `feat/multi-tenant-engagement-flow` |
| **Source of truth** | `C:\repos\Jun24codeinstrucitons\SHIELD_v2_Developer_Work_Order.md` + cited companion specs |
| **Author** | SHIELD Build Agent |

This is the living implementation plan for the remaining SHIELD v2 build, derived from the Developer Work Order and verified against the live code. It is the work order, made executable and tracked. Update the status checkboxes and the Progress Log as items land.

---

## Status legend

- `[ ]` not started · `[~]` in progress · `[x]` done & verified
- Each item is **done** only when: code complete, migrations applied, unit/isolation tests pass, the web build is green, and any new page passes the no-dead-end checks.

---

## Decisions confirmed with the product owner (2026-06-24)

1. Plan lives at `IMPLEMENTATION.md` (this file), versioned.
2. **C0 status reconciliation approved** — all four services standardize on one status enum.
3. No Zero Trust assessment data to preserve (test data) — A4 may remap/drop freely.
4. No CSF assessment data to preserve — D4 may replace the simplified model cleanly.
5. Build straight through A→F without stopping for review; verify navigation, links, and inputs before committing ("publishing").
6. All work saved in the dated folder `SHIELD062426v1`.

---

## Verification findings — deltas from the Work Order

Checked every concrete reference in the work order against the live code. Corrections that change scope:

| Item | Work order assumption | Verified actual state | Effect |
|---|---|---|---|
| Export deps | concern from earlier review | `reportlab`, `openpyxl`, **and `python-docx` already declared** (`apps/api/pyproject.toml:25-29`) | No dep work; C4 just *uses* python-docx |
| ATT&CK proxy route | the old headline 404 bug | `apps/web/src/app/api/proxy/attack/coverage/[id]/route.ts` **already exists** | Bug already fixed; D2 is D/P/R + dashboard only |
| Next migration | `0015` | migrations end at `0014_questions.py` | ✅ accurate |
| `REVIEWER` role | `user.py` 23-26 | confirmed `user.py:23-26`; also `dependencies.py:9,98,115` | ✅ A3 valid |
| `current_client` | `dependencies.py` | confirmed `dependencies.py:89` | ✅ accurate |
| `Deliverable` cols | has `released_to_client_at`,`version`,`superseded_by` | confirmed `deliverable.py:46,32,48`; `finalized_at` also already exists `:41` | ✅ A1 drops `released_to_client_at` |
| ZT scale | single 0-4, DoD = Pre-ZT/Baseline/Target/Advanced/Optimal | confirmed `zt/maturity.py` exactly | ✅ A4 valid |
| CSF model | simplified single `maturity_tier` 1-4 | confirmed `csf_assessment.py:114` | ✅ D4 is the big rebuild |
| ATT&CK coverage | status/notes/evidence only | confirmed `attack_assessment.py:88-101`, no D/P/R | ✅ D2 valid |
| AI engine | single `LLMClient.invoke(purpose=...)`, no registry | confirmed `ai/llm.py:176`; Anthropic + fixture providers | ✅ C1 valid |
| Status enums | inconsistent across services | CSF `draft→submitted→approved→released`; ZT/ATT&CK `draft→approved→released` | **Added item C0** to reconcile |

---

## Ground rules (definition-of-done for every item)

1. **Tenancy:** every new query scoped by `client_id` via the `current_client` dependency (`apps/api/app/dependencies.py`). Never return/accept a row whose `client_id` ≠ active client. Add an isolation test for every new table.
2. **AI suggests, code computes:** the AI never sets a number that rolls up a score or tier. Deterministic math = pure Python functions with unit tests. AI proposes draft values + narrative only.
3. **Audit + redaction:** every state change writes an audit row via the audit spine; every external AI call goes through `LLMClient` (`apps/api/app/ai/llm.py`).
4. **Clients never see deliverables** in the app (A1). Scoring + dashboards are admin-only.
5. **Migrations:** all schema changes are Alembic migrations, sequential from `0015`.
6. **No dead ends:** every new page satisfies `Navigation_Spec.md` (global nav present, breadcrumb if nested, onward link on every terminal state, skip-to-content).

---

## Migration sequence (planned)

| # | Item(s) | Change |
|---|---|---|
| `0015` | A1 + A3 + A4 | drop `Deliverable.released_to_client_at`; ZT scale framework-aware + remap; (reviewer is a string enum, no DB change) |
| `0016` | B1 | `client_domain` table |
| `0017` | C2 | `locked` flag on all grid tables |
| `0018` | C0 + C7 | unify service status enums + `message` table + `returned_for_info` |
| `0019` | D2 | ATT&CK `detection_tools` / `prevention_tools` / `response_tools` |
| `0020` | D3 | ZT per-capability `target_stage` |
| `0021…` | D4 | CSF tier working profiles, enterprise profile, 5-dimension scoring, reference data |
| `00xx` | E | risk register tables |

Numbers may shift slightly as items merge; the table is updated as migrations are written.

---

# PART A — Reconciliation cleanup (do first) — migration `0015`

### A1 — Remove client access to deliverables `[x]`
- BE: delete `routes/deliverables.py` + its include in `main.py`; remove `release_deliverable` endpoints from `routes/{tech_debt,csf,zt,attack}.py` + any `released_to_client_at` gating; `routes/artifacts.py` must not grant client-role users deliverable artifacts.
- Migration `0015`: drop `Deliverable.released_to_client_at` (keep `version`, `superseded_by`, `finalized_at`).
- FE: delete `app/deliverables/page.tsx` + `app/api/proxy/deliverables/*`; remove Deliverables link from `components/site/PublicHeader.tsx`; strip deliverable links from `IntakeSubmitted`, `SelfAssessmentSubmitted`, `EngagementsView`.
- **Acceptance:** no client route/link/API returns a deliverable file; admin finalize + download intact.

### A2 — Rename "engagement" → "assessment" (UI only) `[ ]`
- FE: `app/engagements/`→`app/assessments/`; `EngagementsView`→`AssessmentsView`; `lib/intake` `createEngagement→createAssessment`, `fetchEngagements→fetchAssessments`, `EngagementResponse→AssessmentResponse`; proxy `api/proxy/intake/engagements/`→`.../assessments/`; replace user-facing copy.
- **Acceptance:** zero `engagement` in `apps/web/src` outside comments; flow still works.

### A3 — Remove the reviewer role `[~]`
> Backend complete: `REVIEWER` removed from `UserRole`; no reviewer ever issued; `artifacts.py` staff check is admin-only; `PublicHeader`/`ClientSwitcher` gated to admin. Remaining: prune dead `reviewer` branches from ~10 web role-union/conditional files (harmless — backend never issues the role; typecheck green).
- BE: remove `REVIEWER` from `UserRole` (`user.py:25`); purge refs in `dependencies.py`, `routes/admin.py`, `routes/artifacts.py`, `security/jwt.py`, seeds. Admin-or-reviewer → admin only.
- FE: remove reviewer handling from `PublicHeader.tsx`; `ClientSwitcher.tsx` admin-only.
- **Acceptance:** zero `reviewer`/`REVIEWER`; auth + switching + gating work with admin+client only.

### A4 — Zero Trust DoD scale → 3 levels `[ ]`
- BE (`zt/maturity.py`): framework-aware scale. DoD = {1 Not Started, 2 Target, 3 Advanced}; CISA stays 1-4. Add `level_count(framework)`; update `stage_label`; drop DoD stage-0. Update `zt/scoring.py` roll-ups to normalize by `level_count` (% of max).
- Migration `0015`: remap any existing DoD rows (test data; safe to coerce).
- FE: stage picker shows 3 for DoD, 4 for CISA (self-assessment + admin workspace).
- **Acceptance:** DoD offers exactly Not Started/Target/Advanced; CISA four; roll-ups correct for both.

---

# PART B — Tenant onboarding — migration `0016`

### B1 — Approved email-domain join `[ ]`
- Migration `0016`: `client_domain` (`id`, `client_id` FK, `domain` unique+lowercased, `created_by`, `created_at`).
- BE: rewrite `routes/auth.py::register` — domain lookup → attach as `client`; generic-provider denylist → reject with "contact your administrator"; unknown → reject (no placeholder client). First admin via seed/bootstrap.
- **Acceptance:** approved domain auto-joins; generic/unknown rejected; no placeholder clients.

### B2 — Admin client & domain management `[ ]`
- BE: admin-only routes in `routes/admin.py` — create/list/edit client, add/remove domain, remove (archive) service. All audited.
- FE: Management area in admin shell (depends on C6).
- **Acceptance:** admin CRUD works + audited; client users 403 everywhere.

---

# PART C — Shared platform

### C0 — Status-model reconciliation (prerequisite) `[ ]`
- Canonical enum: `draft → submitted → returned_for_info → accepted → in_analysis → finalized` (no `released`).
- Migration `0018`: map existing CSF/ZT/ATT&CK statuses onto it; apply uniformly.
- **Acceptance:** all services share one status set; transitions enforced; no `released`/`approved` left.

### C1 — One AI engine with job types `[ ]`
- BE: add `ai/engine.py` with `run_job(job_name, *, client, service, inputs)` → look up job def (prompt + parser) → `LLMClient.invoke` → parse. Jobs: `tech_debt_extract` (move existing behind registry), `csf_score`, `zt_score`, `mitre_map`, `risk_synthesize`. Score/map/synthesize return draft suggestions only. Record prompt version on `llm_calls`.
- **Acceptance:** each job runs fixture + live; redaction counts + tokens logged; new job = prompt + parser only.

### C2 — Edit-and-rerun safeguards `[ ]`
- Migration `0017`: per-row `locked` boolean on every grid table (`csf_answers`, ZT capability rows, `attack_coverage`, tech-debt items).
- BE: rerun skips locked rows; compute "what changed" diff (field, old, new) vs prior version; admin edit clears AI-confidence marker.
- **Acceptance:** locked row survives rerun; diff correct; edit clears confidence.

### C3 — Auto-versioned documents on every AI run `[ ]`
- BE: after a successful AI run, generate PDF+Word+XLSX → store as new `Deliverable` version (artifacts scoped by `client_id`); keep history; mark newest current; filenames `{Company}_{Service}{MMDDYY}[_vN].{ext}` (generalize `tech_debt/filename.py`).
- **Acceptance:** two runs → two versions; newest current; older still admin-downloadable.

### C4 — Word (.docx) export `[ ]`
- BE: add `.docx` renderer in each `{tech_debt,csf,zt,attack}/exporters.py` matching the PDF content per flow spec.
- **Acceptance:** every service document set includes a Word file with content parity.

### C5 — Two dashboards per service (executive + technical) `[ ]`
- FE: shared dashboard shell with Technical/Executive toggle. Executive = KPI cards + charts (Recharts) modeled on Atlas uploads (Software Portfolio→Tech Debt, CISA→ZT, MITRE→ATT&CK; CSF from spec §6), read-only. Technical = existing grids.
- **Acceptance:** each workspace shows both; executive renders cards/charts; editing only in technical.

### C6 — Navigation shells + no dead ends (build early) `[ ]`
- FE: admin left-sidebar shell (`app/admin/layout.tsx`: Dashboard, Clients, Intake Queue, Active Work, Messages, Management) for all `admin/*`; client top-nav shell (Home, My Assessments, Messages, Account) with real client Home; no Deliverables. Breadcrumbs on nested pages. Workspace tabbed sub-nav (Technical/Executive/Documents/AI history). Intake wizard "Save and exit" → client Home. Not-authorized page → role-aware onward links + Sign out. Skip-to-content first focusable in both shells. Replace bare Loading/error with shell + Retry + onward link.
- **Acceptance:** Navigation_Spec §9 checks pass (crawl, keyboard, role).

### C7 — Messaging + return-for-info loop `[ ]`
- Migration `0018`: `message` (`id`, `client_id`, `service_id`, `author_user_id`, `body`, `created_at`, `read_at`).
- BE: list/post message routes (tenant-scoped); `returned_for_info` status + admin "request more info" action; client responds + re-submits → `submitted`.
- FE: Messages surface in both shells; per-service thread; admin action; client view/respond.
- **Acceptance:** full loop works; thread persists; isolation test on `message`.

### C8 — Wire verbatim interview questions into self-assessment `[ ]`
- BE: questions seeded (migration `0014`, `models/questionnaire.py`). Add per-service response table keyed to seeded questions; serve stem + cues + hidden subcategory/IG/dimension tags; map answers → subcategories to seed the admin grid. Content per `CSF_Interview_Questions_Verbatim.md` + `ZT_Interview_Questions_Verbatim.md`.
- FE: render questions + cues via `components/questionnaire/` in the real CSF + ZT flows.
- **Acceptance:** client answers verbatim per tier/framework; admin sees them mapped to subcategories.

---

# PART D — Services

### D1 — Tech Debt `[ ]`
Remaining: C5 (dashboards) + C2 (rerun safeguards). Extraction/versioned lists/overlap already built. Dashboard content per `TechDebt_Template_Spec.md`.

### D2 — ATT&CK `[ ]`
- Migration `0019`: add `detection_tools`, `prevention_tools`, `response_tools` (JSON) to `AttackCoverage`.
- BE: `mitre_map` job suggests status + D/P/R + rationale, validating tools against the capability list. Coverage math unchanged: `(Covered + 0.5·Partial)/addressable`, addressable = Covered+Partial+Gap, per tactic + overall.
- FE: executive dashboard (3 number cards, coverage mix, tactic heatmap, top-5 blind spots) modeled on MITRE upload; technique panel gains D/P/R fields.
- **Acceptance:** D/P/R persist; AI prefill constrained; coverage math unit-tested; report renders.

### D3 — Zero Trust `[ ]`
- Migration `0020`: per-capability `target_stage` alongside `maturity_stage`.
- BE: `zt_score` job suggests current+target+pillar narrative; gap = current<target per capability; 12-month roadmap weighting Identity/User + Data higher (weighting exists in `zt/scoring.py`). DoD 3-level from A4.
- FE: two dashboards (CISA Atlas executive model); per-capability current+target pickers.
- **Acceptance:** per-capability current+target; gaps + roadmap compute; both frameworks correct level counts.

### D4 — CSF full Playbook (largest) `[ ]`
- Migrations `0021…`: tiered Working Profiles (HIGH/MOD/LOW, all ~108 subcategories); per subcategory per tier — 5 dimension scores (G/P/I/M/C, 0-2), in-scope flag+rationale, "what we found", evidence refs, per-subcategory target maturity; Enterprise Profile (rolled-up score, rule used, target, gap); import IG metric metadata + ZT/ATT&CK cross-refs. **Replaces** simplified `csf_answers.maturity_tier`.
- Deterministic engine (pure fns, unit-tested vs methodology doc):
  - total = Σ5 dims (0-10); levels 0-2→L1, 3-5→L2, 6-7→L3, 8-9→L4, 10→L5.
  - evidence cap: no evidence → Implementation ≤1 AND level ≤2 (clamp).
  - weighted-floor roll-up, 6 rules in order, first-match-wins, record rule #; **Rule 2 overrides Rule 5**.
  - gap = current<target; priority P1/P2/P3 per rules.
- `csf_score` job: 5 dimension scores + narratives only; never totals/levels/roll-up/gap/priority.
- FE: 10 Playbook sub-pages (Landing hub, Scope, Systems, Artifacts, Profile HIGH/MOD/LOW, Enterprise Profile, Gap Analysis, Action Plan), section-tabbed, reference-data side panel; interview via shared questionnaire component (C8).
- Exports: tier Working Profile XLSX + Enterprise Profile XLSX (grouped IDENTIFICATION/SCOPE/FINDINGS/5-DIMENSION/RESULT/TARGET+GAP/DOCUMENTATION) + Gap Analysis XLSX + 20-30pp PDF/Word.
- **Acceptance:** worked example reproduces methodology roll-up + tiers exactly; Enterprise Profile XLSX matches reference shape; AI only proposes dimension scores + narrative.

---

# PART E — Risk Register (greenfield) — migration `00xx`

- Generation gate: enabled only when client has ATT&CK coverage AND ≥1 of CSF/ZT; uses both if both exist; locked otherwise with "what is missing".
- Migration: versioned register; per entry — id, title, description, axis, source(+source_id), linked techniques+controls, likelihood, impact, code-derived tier, compensating, residual, recommended_action+rationale, provenance (origin/trust). Blank export columns: decision-maker, approval date, expiry, next review, status.
- `risk_synthesize` job: one candidate entry per finding; may only cite techniques/controls present in the client's assessments; code validates links against catalogs, rejects invented IDs.
- Deterministic tier engine: likelihood/impact orders; score=(li+1)·(ii+1); High/VeryHigh+Catastrophic→Critical; VeryHigh+Major+→Critical; ≥15→High; ≥9→Medium; ≥4→Low; else Negligible. Tier never AI-set.
- Dashboard + exports modeled on Atlas Risk Register (KPI cards, inherent-risk-by-axis, 5×5 matrix, tier legend, table with required Linked Source per row); XLSX + PDF/Word; each generate = new version.
- **Acceptance:** gate works; every entry traces to a source; tiers match matrix; AI can't invent IDs; each generation = clean new version.

---

# PART F — Harden and ship

- Expand isolation test suite to every new table (`client_domain`, `message`, risk register, CSF tier profiles); run in CI.
- Accessibility (axe/Pa11y) + skip link in CI.
- Dependency audits: pip-audit, pnpm audit, Dependabot.
- IaC: fill `infra/terraform` (AWS GovCloud or Azure Gov) + production images under `infra/docker`.
- Worker decision: **keep AI synchronous**, remove the dead `celery -A app.worker` line from `docker-compose.yml` (module does not exist); defer a real worker.
- Auth seam: keep login pluggable for SAML/external MFA; MFA deferred.
- **Acceptance:** green CI incl. isolation + a11y; reproducible deploy; no cross-tenant leak / stack trace under test.

---

## Delivery order

A (cleanup) → B (onboarding) → C0/C1/C6 first (unblock the most), then C2/C3/C4/C5/C7/C8 → D1/D2/D3 → D4 (CSF) → E (Risk Register) → F (harden).

---

## Progress log

| Date | Item | Notes |
|---|---|---|
| 2026-06-24 | Setup | Copied `SHIELD061626v1` → `SHIELD062426v1`; reinstalled frontend (pnpm) + backend (venv) deps; wrote this plan (v1). Baseline green. |
| 2026-06-24 | A1 done | Deleted client deliverables route/page/proxies + 4 release endpoints + 4 release proxies; dropped `released_to_client_at` (migration 0015, round-trips); `latest` deliverable endpoints admin-only; artifact download admin-only; 4 admin DeliverableCards finalize+download only; client confirmation links no longer point at deliverables. Full API unit suite green; web typecheck green. |
| 2026-06-24 | A3 backend | Removed `REVIEWER` from `UserRole` + all functional usages; header/switcher admin-only. FE reviewer-union dead-branch cleanup pending. |
