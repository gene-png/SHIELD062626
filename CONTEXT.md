# Project Context
_Last updated: 2026-07-03 (end of sprint-1 "smoke sweep" — autonomous loop, branch `qa/smoke-sweep-sprint-1`)_

## What This Project Is
SHIELD is Kentro's multi-tenant cybersecurity assessment platform for consultant-led client engagements, targeting high-compliance environments (FedRAMP Moderate/High, AWS GovCloud / Azure Government). It delivers four assessment services — Technical Debt Review, Zero Trust (CISA ZTMM 2.0 + DoD ZTRA), NIST CSF 2.0 (full 10-step Playbook), and MITRE ATT&CK coverage mapping — plus a greenfield Risk Register (5x5 NIST 800-30) that synthesizes from them. Core principle: "AI suggests, code computes" — deterministic scoring lives in Python engines (`apps/api/app/csf/playbook.py`, `app/risk/engine.py`, `app/zt/scoring.py`); the LLM only drafts values and narrative through a single redacting egress client.

Stack: pnpm monorepo. Next.js 14 App Router (`apps/web`), FastAPI + SQLAlchemy 2 + Alembic (`apps/api`), Postgres 16 / Redis / MinIO / Keycloak / MailHog via `docker-compose.yml`. There is no Celery worker — AI jobs run synchronously in `api`. Version 3.0.0.

## Current State
- **v2 work order (Parts A-F) is merged to main** (PR #1, migrations 0015-0025). All four service surfaces, multi-tenant onboarding, AI job registry, CSF Playbook engine, Risk Register, and the F hardening pass are built.
- **Sprint-1 "smoke sweep" is COMPLETE** on branch `qa/smoke-sweep-sprint-1` (T0 through T10, plus inserted T0b and T6b). The `SMOKE_TEST.md` checklist is now backed by a green 14-file Playwright smoke suite under `e2e/smoke/`; only the human-only items remain (see "Needs David").
- AI defaults to `fixture` mode. As of T6b, fixture mode serves deterministic, demo-plausible suggestions for all five AI purposes fully OFFLINE (no API key) — the demo/dev stack is now exercisable end-to-end without live LLM. Live mode still needs `ANTHROPIC_API_KEY` + `SHIELD_LLM_MODE=live`.

## What Shipped This Sprint (sprint-1 smoke sweep)
Every task committed on `qa/smoke-sweep-sprint-1`:
- **T0** (c15a8da) — scaffolded the Playwright smoke harness (`e2e/`: package.json, lockfile, playwright.config.ts chromium-only + fullyParallel:false, helpers/auth.ts, s0-home spec). The `e2e/` dir was empty despite the README claiming a suite.
- **T0b** (e017480) — PRE-EXISTING defect: `tests/unit/test_zt_questionnaire.py` did `parents[4]` which IndexErrors at COLLECTION time in-container (killed the whole unit suite). Resolved the zt-data dir defensively + mounted `packages/zt-data` read-only into `api` so the test still runs. Unblocked the queue-wide pytest gate.
- **T1** (dd0e23b) — stale marketing/sign-up copy: renamed the ATT&CK card to "MITRE ATT&CK Coverage Mapping", removed the reviewer-role blurb (removed in A3), fixed B1 bootstrap copy, scrubbed 8 stale admin/reviewer code comments.
- **T2** (63a2d2a) — `seed_demo.py` now idempotently approves the `atlas.example` client domain so a fresh stack supports self-registration.
- **T3** (22e79e9) — custom `not-found.tsx` (app shell + Home / My Assessments / Sign in recovery links); added `id=main-content` for the skip-link work.
- **T4** (a350e9e) — typed registration errors (`{reason, message}` dict-detail) mapped to friendly per-field sign-up copy; disclosure posture logged DECISIONS D-016.
- **T5** (aaae28c) — s3 client self-assessment spec: "assessment" terminology, CSF answer persistence across save-and-exit, DoD ZT 3-level ladder, submit-moves-status.
- **T6b** (8a9743c) — DAVID-APPROVED product decision: fixture-mode AI now serves deterministic runtime suggestions offline. New `app/ai/fixtures.py` (`RuntimeFixtureProvider`, payload-aware per purpose); missing fixture -> typed 503 (never raw 500). Logged DECISIONS D-017. Unblocked T6/T7/T8.
- **T6** (dfa432b) — s4-techdebt / s5-attack / s6-zt admin smoke specs; found + fixed a REAL app defect (see below).
- **T7** (c01aaa6) — s7-csf-playbook / s8-risk-register specs; downloaded 8 export artifacts to `e2e/artifacts/` for the section-10 eyeball.
- **T8** (da3c822) — s9-messaging (thread + inbox round-trip) and s11-staleness (C3 nudge set/clear) specs.
- **T9** (4375816) — s12-a11y-nav (skip-link + keyboard) and s13-isolation (tenant isolation) specs.
- **T10** (this commit) — s15-headers spec (all six security headers verified present); synced SMOKE_TEST.md checkboxes to green specs; fixed README worker/e2e drift; this CONTEXT snapshot.

## Real Bug Found + Fixed This Sprint
- **T6, attack coverage PATCH route (dfa432b):** the ATT&CK technique panel's status/notes/lock edits were dead in the browser — `/api/proxy/attack/coverage/[id]` PATCH route did not exist (the zt/answers equivalent did), so edits 404'd. Added the route (mirrors zt). GOTCHA: the repo-wide `.gitignore` `coverage/` pattern silently ignored the new `.../attack/coverage/` dir — needed a `.gitignore` negation. **Check `git status` after creating any dir named `coverage`.**

## Needs David (human-only, cannot be automated)
- **SMOKE_TEST section 10** — eyeball the 8 generated documents. They are saved (gitignored) to `e2e/artifacts/`: `CSF_Playbook_v8.xlsx`, `CSF_Playbook_v8_Executive.pdf/.docx`, `CSF_Playbook_v8_Full.pdf/.docx`, `Risk_Register_v5.xlsx/.pdf/.docx`. Each was asserted HTTP 200 + correct content-type; only the visual look-right check remains.
- **SMOKE_TEST section 14** — one live-AI run: set `ANTHROPIC_API_KEY` + `SHIELD_LLM_MODE=live`, run one Run-AI, confirm a redacted `llm_calls` entry with no PII.
- **PR push** — the sprint branch is ready to open as a PR but that is `review-required` per autonomy rules; also pending Gene's collaborator access on the repo.

## Backlog (found this sprint, not in scope to fix)
- **`next@14.2.15` CRITICAL vuln + ~29 pnpm advisories** — dependency audit surfaced a critical Next.js advisory plus a stack of transitive pnpm vulnerabilities. Needs a dependency-bump pass (verify no App-Router breakage).
- **`beacon.test` is unregistrable** — the seeded Beacon Labs approved domain uses `.test`, a reserved/special-use TLD the API email-validator rejects (422 "special-use or reserved name") BEFORE the domain-approval check, so no user can ever register on it. Admin can approve a `.test`/`.invalid`/`.localhost` domain in the UI but it can never onboard a user. s13 uses `beacon.example` instead. Product inconsistency to resolve (reject reserved TLDs at approval time, or document).
- ~~**Skip-link landmark focus**~~ — FIXED in the final-audit pass: `tabindex={-1}` added to every `main#main-content` (6 files); s12 now asserts focus lands ON the landmark.
- **Roving-tabindex on radiogroups** — TierPicker / ZtStagePicker radios are Tab-reachable and Space/Enter-operable but lack arrow-key navigation within the radiogroup.
- **Hardcoded seeded UUIDs in e2e specs** (final-audit finding) — s4/s5/s6/s7/s8/s9/s11/s13 hardcode the seeded Atlas client/service UUIDs. `seed_demo.py` mints random UUIDs (`default=uuid.uuid4`), so the constants hold only for a DB seeded once and persisted; a re-seeded-from-scratch DB would break all eight specs. Fix: resolve ids at runtime (s9's `atlasClientId()` pattern, via the admin API) or make the seed deterministic (`uuid5`).
- **`/admin/management` UI not e2e-covered** (final-audit finding) — client creation + domain approval are exercised via the admin API only; the management UI, domain removal, and list-reflects-changes need a human pass or a follow-up spec (SMOKE_TEST §2 unchecked accordingly).
- **CSF verbatim interview prompts (C8) not asserted** (final-audit finding) — no spec compares the rendered questionnaire text against the master-spec prompt source (SMOKE_TEST §3 clause unchecked accordingly).
- **Heatmap `scope=row`** — tbody `<th>` likelihood labels lack `scope=row`, so Chromium's a11y tree does not treat them as row headers (thead `<th>`s do resolve to columnheader).
- **Unlimited CSF draft versions** — `POST csf/services/<id>/assessments` has no draft-exists guard; versions just increment on every call. Fine for tests (fresh draft each run) but unbounded in practice.

## Environment Notes (carried forward — still true)
- Docker CLI is NOT on Git Bash PATH: `export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"` in every shell.
- **next dev hot-reload does NOT fire through the Windows bind mount** — after ANY `apps/web` source edit run `docker compose up -d --force-recreate web` (~10-20s) before e2e; in-container touch/restart does not help. Adding a NEW python module to `app/` needs `docker compose restart api` (uvicorn --reload picks up edits to existing modules but may miss new files).
- e2e specs run on the HOST: `cd e2e && npx playwright test [file]`, base URL `http://localhost:3000`, Chromium installed.
- In-container `pytest -m unit` takes ~3min alone but ~13-16min under concurrent load; run gates sequentially, capture exit via `sh -c 'pytest; echo PYTEST_EXIT=$?'`, and poll a detached log rather than a foreground wait.
- next-dev under back-to-back e2e load queues requests for tens of seconds -> cold-compile timeouts on signIn/register (`auth.ts` toPass 60s). This is a documented dev-server flake, not a spec defect; re-run passes clean.
- Demo logins: `admin@kentro.example` / `DemoPass!2026` (Kentro consultant), `client@atlas.example` / `DemoPass!2026` (Atlas tenant). Seeded Atlas service ids are stable constants: attack_coverage=`7c2ec112-...`, zero_trust_cisa=`2a2c1b0d-...`, zero_trust_dod=`0290f4e2-...`, nist_csf=`55eb8797-...`, tech_debt=`3c73a6cb-...`; Atlas client=`1b9c80e3-...`.

## Test Coverage Status
- **Backend:** full `pytest -m unit` suite green in-container (T0b unblocked collection). Includes CSF Playbook engine, risk engine, cross-tenant isolation, and the new `test_ai_runtime_fixtures.py` (T6b).
- **Web:** tsc `--noEmit` clean (the standing repo-health gate for spec-only tasks).
- **Playwright e2e:** 14 smoke spec files under `e2e/smoke/` mapping to SMOKE_TEST sections 0-15. Prior checkpoint ran 25/25 green; T10 targeted s15 run green.
- Known flake: dev-server cold-compile timeouts under concurrent load (above) — re-run clears it.

## Lessons Learned — This Codebase (preserved history)
- Demo logins seeded by dev-up: `admin@kentro.example` / `DemoPass!2026` and `client@atlas.example` / `DemoPass!2026`. Web :3000, API docs :8000/docs, Keycloak :8080, MinIO :9001, MailHog :8025.
- Migrations must stay SQLite-safe (`batch_alter_table`) — tests use SQLite, prod uses Postgres.
- New persisted analysis fields should be additive/optional so older assessments parse unchanged (the C0 pattern).
- The tiered CSF model coexists with the simpler `CsfAnswer` (which still backs the client self-assessment) — do not consolidate them casually.
- Tests run inside containers: `docker compose exec api pytest -m unit|integration`, `docker compose exec web pnpm test`. e2e is host-run Playwright (`cd e2e && npx playwright test`).
- Playwright gotchas learned this sprint: `getByRole` name matching is SUBSTRING (use `exact:true` near sibling widgets); `check()/uncheck()` fail on auto-save checkboxes (use `click()` + `waitForResponse`); assert post-Run-AI UI state after `page.reload()` (dodges the next-dev StrictMode double-load clobber race); a body click before the first Tab moves the sequential-focus start point past the skip link.

## Final Audit (post-T10 shutdown pass, 2026-07-03)
Three parallel sub-audits (type/logic, spec compliance, test-coverage honesty) ran over the 18-commit sprint diff. Fixed in `chore(sprint-1): final audit`:
- **Skip-link landmark focus (WAI-ARIA)** — `tabIndex={-1}` + `outline-none` added to all six `main#main-content` landmarks (`account/page`, `admin/layout`, `assessments/page`, `messages/page`, `not-found`, `AdminShell`); s12 strengthened to assert `document.activeElement` IS the landmark after activating the skip link.
- **s3 wrong-draft race** — the persist test reopened via the FIRST "Continue" link, which could open another run's accumulated draft; it now captures the created workspace URL and reopens that exact assessment by service id.
- **s3 A1 assertion added** — a freshly-registered client sees zero admin/deliverables links on the client shell.
- **s0 console-error filter** — the home no-console-errors test now filters known benign next-dev noise (resource 404s, DevTools notice) so it asserts app errors, not dev-server noise (mirrors s15's CSP-only filter approach).
- **SMOKE_TEST.md honesty pass** — every checkbox re-scoped to what its spec actually proves: §2 management UNCHECKED (API-only coverage), §3 verbatim-prompts clause split out + UNCHECKED, §13 admin-URL line reworded to the real shipped behavior (`EnsureActiveClient` auto-switch is a deliberate admin convenience; the asserted security boundary is X-Client-Id server-side scoping), plus scope notes on §1/§2 switcher/§4/§6/§7/§12 items.

Audit verdicts: security — e2e `npm audit` 0 vulns; root `pnpm audit` 29 vulns ALL pre-existing backlog (no dependency changes outside `e2e/` in the diff); no hardcoded secrets beyond the known-intentional demo/test creds. Type/logic — no tsc/pytest/runtime errors in new code; `fixtures.py` payload contract verified against all five callers. Spec compliance — 11/13 tasks fully compliant; the T9 narrowings are now either fixed (skip-link) or honestly documented (admin URL auto-switch).
Final gates: full e2e 27/27 passed (16.7m), in-container `pytest -m unit` EXIT=0, web `tsc --noEmit` EXIT=0.
Not fixed (documented backlog): hardcoded seeded UUIDs across eight specs (test fragility vs a re-seeded DB — needs runtime id resolution or a deterministic seed).
