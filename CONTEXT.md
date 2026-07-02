# Project Context
_Last updated: 2026-07-02 (morning session — first Claude Code session in this repo)_

## What This Project Is
SHIELD is Kentro's multi-tenant cybersecurity assessment platform for consultant-led client engagements, targeting high-compliance environments (FedRAMP Moderate/High, AWS GovCloud / Azure Government). It delivers four assessment services — Technical Debt Review, Zero Trust (CISA ZTMM 2.0 + DoD ZTRA), NIST CSF 2.0 (full 10-step Playbook), and MITRE ATT&CK coverage mapping — plus a greenfield Risk Register (5x5 NIST 800-30) that synthesizes from them. Core principle: "AI suggests, code computes" — deterministic scoring lives in Python engines (`apps/api/app/csf/playbook.py`, `app/risk/engine.py`, `app/zt/scoring.py`); the LLM only drafts values and narrative through a single redacting egress client.

Stack: pnpm monorepo. Next.js 14 App Router (`apps/web`), FastAPI + SQLAlchemy 2 + Alembic (`apps/api`), Postgres 16 / Redis / MinIO / Keycloak / MailHog via `docker-compose.yml`. Version 3.0.0.

## Current State
- **v2 work order (Parts A-F) is merged to main** (PR #1, migrations 0015-0025). All four service surfaces, multi-tenant onboarding, AI job registry, CSF Playbook engine, Risk Register, and the F hardening pass are built.
- All local CI-equivalent gates were green at merge: ruff, black, bandit, prettier, tsc, eslint, `pytest -m unit` (incl. deterministic-engine and tenant-isolation suites); `next build` compiles all 35 pages.
- **Nothing has been human-QA'd at runtime yet.** The entire `SMOKE_TEST.md` checklist (browser walkthrough, eyeballing generated PDF/Word/XLSX, one live-AI run) is unchecked. This is the gate before prod.
- AI defaults to `fixture` mode (no API key needed); live mode needs `ANTHROPIC_API_KEY` + `SHIELD_LLM_MODE=live` in `.env`.
- The Celery worker was REMOVED in Part F (AI is synchronous). README references to a worker are stale.

## Just Completed
- (This session) Copied the standard 20-command Claude workflow set from kentro-cloud-modernization into `.claude/commands/`; gitignored `.claude` runtime state; created this CONTEXT.md.
- (This session) **Fixed seed_demo.py crash**: it still passed `released_to_client_at` to `Deliverable` (column dropped by migration 0015 / Work Order A1) and seeded a `.released` audit event for the removed release-to-client path. Removed both (`apps/api/scripts/seed_demo.py:253-263`). Seed now completes; demo data fully loaded. UNCOMMITTED.
- `scripts/dev-up.ps1` — one-shot stack startup (starts Docker Desktop, compose up, waits for health, seeds demo accounts, prints creds banner). Auto-runs via `.vscode/tasks.json`.
- `SMOKE_TEST.md` — the pre-prod runtime QA checklist (15 sections + sign-off).
- PR #1 merged: the full A-F work order. Details in `PR_DESCRIPTION.md`; part-by-part log in `IMPLEMENTATION.md`; decisions in `DECISIONS.md`.

## Active / In Progress
- **Pre-prod smoke test (`SMOKE_TEST.md`)** — Section 0 (bring-up) effectively passes: stack healthy, web 200, API healthy, no worker service, admin sign-in works via Playwright with no console errors. Rest unchecked.
- Smoke-test finding (open): marketing home service cards say "INCLUDES: reviewer audit walk" — stale copy; the reviewer role was removed in A3. Also home page calls the ATT&CK service "Attack Surface Mapping" (verify against spec naming).
- Uncommitted in working tree: `.claude/commands/` (20 files), the `.gitignore` addition, and the seed_demo.py fix (below).

## Session 2026-07-02 environment notes
- Docker Desktop + WSL2 were installed fresh on this machine today (WSL platform install needs an elevated shell; `winget install Microsoft.WSL` fails non-elevated).
- Docker CLI is NOT on Git Bash PATH: use `export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"` (also fixes the `docker-credential-desktop not found` pull error).
- PowerShell script execution is deny-ruled in Claude Code here — replicate dev-up.ps1 steps in bash instead.
- Playwright 1.61.1 + Chromium installed on host; scripted browsing works from the session scratchpad (`npm install playwright` there).

## Important Next Steps
1. Run the `SMOKE_TEST.md` checklist top to bottom against a running stack (`scripts/dev-up.ps1`). Fix what it surfaces; check off items as they pass.
2. Section 10 (eyeball the generated CSF/Risk Register documents) and Section 14 (one live-AI run) need David specifically.
3. `infra/terraform` for AWS GovCloud / Azure Government — blocked on account/region/network decisions.
4. Runtime axe/Pa11y in CI (static jsx-a11y is enforced; runtime needs a built-app harness).
5. Import IG Core/Supporting cross-reference metadata so CSF roll-up Rules 2/5 and `is_core` priority stop using safe defaults.

## Known Issues & Blockers
- `BUILD_REPORT.md` and `CHANGELOG.md` are STALE (stuck at Phase 2, 2026-05-21, still describe the removed worker). Trust `PR_DESCRIPTION.md` + `IMPLEMENTATION.md` + git log instead.
- MFA and email verification are deliberately feature-flagged OFF (compensating controls documented); FedRAMP-authorized LLM connector deferred.
- CI on GitHub runs only on main/PRs — PR #1 was its first real run; watch for CI-vs-local drift.
- Host has no node_modules installed (everything ran in Docker so far); Docker Desktop not running at session start.

## Lessons Learned — This Codebase
- Demo logins seeded by dev-up: `admin@kentro.example` / `DemoPass!2026` and `client@atlas.example` / `DemoPass!2026`. Web :3000, API docs :8000/docs, Keycloak :8080, MinIO :9001, MailHog :8025.
- Migrations must stay SQLite-safe (`batch_alter_table`) — tests use SQLite, prod uses Postgres.
- New persisted analysis fields should be additive/optional so older assessments parse unchanged (the C0 pattern).
- The tiered CSF model coexists with the simpler `CsfAnswer` (which still backs the client self-assessment) — do not consolidate them casually.
- Tests run inside containers: `docker compose exec api pytest -m unit|integration`, `docker compose exec web pnpm test`, `docker compose run --rm e2e pnpm e2e|a11y`.

## Test Coverage Status
- **Backend:** full unit suite green, including 20 CSF Playbook engine tests, risk engine tests, and cross-tenant isolation tests for every new table. Integration suite exists (`pytest -m integration`, real DB).
- **Web:** unit tests via `pnpm test`; tsc + eslint clean.
- **Playwright e2e:** suite lives in `e2e/` and runs via the `e2e` compose service; also a11y (axe/Pa11y). Coverage of the new v2 surfaces vs. the checklist has not been audited — the smoke test exists precisely because runtime coverage is unverified.
- No known flaky tests recorded yet.
