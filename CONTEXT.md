# Project Context — state of `main`

_Last updated: 2026-07-12 (Sprint 6 close — real demo). This file describes the
project as of the branch it sits on and is updated ONLY as part of a PR. Durable
facts and environment gotchas live in `CLAUDE.md`; personal in-flight status
lives in `context/<name>.md`; per-sprint detail lives in `SPRINT_<n>.md`._

## Current state

- **v2 work order (Parts A–F) merged to `main`** (PR #1, migrations 0015–0025,
  `v3.0.0`): all four service surfaces, multi-tenant onboarding, AI job
  registry, CSF Playbook engine, Risk Register, F hardening pass.
- **Sprint 1 "smoke sweep"** (PR #16, `v3.0.1`): `SMOKE_TEST.md` backed by a
  green Playwright smoke suite; offline fixture-mode AI (D-017), typed
  registration errors (D-016).
- **Sprint 2 "findings burn-down"** (PR #19, `v3.0.2`): 11 tasks, CI `e2e` job
  added.
- **Sprint 3 "audit correctness & honesty"** (PR #26, `v3.0.3`): 8 tasks burning
  down the 2026-07-08 deep repo audit.
- **Sprint 4 "framework majors + multi-provider LLM"** (PR #28, `v3.1.0`): the
  web stack moved to Next 15 / React 19 / Tailwind 4 / ESLint 9 / Node 22, and
  multi-provider LLM egress (OpenAI + Gemini beside Anthropic, D-024) landed
  below the unchanged redacting seam.
- **Sprint 5 "client value loop"** (PR #31, `v3.2.0`): consultant output now
  delivers visible value to the CLIENT role — deliverable release flow (D-025),
  `/home` executive dashboard + §2.5 value-loop card, `/documents`, a CSF POA&M
  step, a pre-egress redaction preview, and the first read surface over the
  append-only audit stores (`/admin/audit`).
- **Sprint 6 "real demo" COMPLETE** (this branch `feat/real-demo-sprint-6`,
  `v3.3.0`): the platform is now a real, self-standing demo. The live-AI path is
  runnable and fails LOUDLY at boot when misconfigured (D-026); seeded
  deliverables actually download (seed→storage parity); real TOTP MFA (D-027) and
  real email verification + password reset (D-028) ship on the custom-JWT stack —
  the D-020 boot-refusals are gone, the flags now gate enforcement; a full-matrix
  `/ready` + `/admin/health` operator view lands; the demo seed tells a coherent,
  downloadable Atlas story with a one-command reset; and `docker-compose.demo.yml`
  runs web as a production build. Two additive/C0 migrations (0030 MFA TOTP, 0031
  email tokens). New user-facing auth features + a runnable live path justify the
  **minor** bump. Full exit gate set green — full Playwright e2e, `pytest -m
  unit`, web `tsc`, in-container web vitest, in-container web eslint, host
  prettier `--check` (3.9.5), and in-container ruff/black.

### Sprint 6 task → commit

| Task | What shipped | Commit |
| --- | --- | --- |
| T0 | Live-AI enablement: declared `anthropic` dep, replaced stale `claude-opus-4-7` default with `claude-sonnet-5`, live-mode boot preflight (fails loudly on missing key / unimportable SDK / placeholder model); D-026 | `8aebe51` |
| T1 | Live-AI opt-in integration spec (`@pytest.mark.live`, self-skips keyless) + `smoke_live_ai.py`; SMOKE_TEST §14 codified | `a19fded` |
| T2 | Seed → storage parity: seed writes bytes via `get_storage()` so seeded deliverables download 200 (410 before); s17 parity test | `0bbabac` |
| T3 | Full dependency-health `/ready` matrix (db/redis/minio/keycloak-dormant/LLM) + `/admin/health` operator view (`HealthMatrix`, vitest) | `9b2c74b` |
| T4 | Real TOTP MFA: migration 0030, RFC 6238 (`totp.py`), enroll/verify/login-challenge + recovery codes, flag gates enforcement; D-027 | `bf8e7c6` |
| T5 | Real email verification + password reset: migration 0031, hashed single-use tokens over SMTP/MailHog, enumeration-safe, flag gates login; D-028 | `f67c79f` |
| T6 | OpenAI reasoning models send `max_completion_tokens` per model family (Sprint 4 D-024 follow-up) | `19636b5` |
| T7 | Live-AI parity sweep across all five purposes (opt-in, self-skips keyless); SMOKE_TEST §14.1 | `8761d91` |
| T8 | Demo realism: seed synthesizes a coherent Atlas Risk Register (code-derived tiers, downloadable exports) + `scripts/demo-reset.*` one-command reset; s8 read-only test | `39b3cfc` |
| T9 | Hosted-demo compose (`docker-compose.demo.yml`, web prod build); root `.dockerignore` + Dockerfile rewrite; fixed latent HealthMatrix CI lint failure; cloud/terraform NOT touched | `db33372` |
| T10 | Security + audit pass: MFA second-factor failures feed account lockout, `/ready` detail redacted for anonymous callers; audits clean/documented, no secret committed | `18b7d85` |
| T11 | Wrap-up: SMOKE_TEST §22–§28, CHANGELOG `[3.3.0]`, BUILD_REPORT sync, DECISIONS D-026/027/028 verify, full gates, this snapshot | this commit |

New migrations: **0030** (MFA TOTP secret + recovery codes, T4) + **0031**
(email verification/reset tokens, T5), both additive/SQLite-safe (C0). New
DECISIONS: **D-026** (live-AI enablement + boot preflight), **D-027** (real TOTP
MFA), **D-028** (real email verification + password reset).

## Machine-local facts (this box)

- **Web runs on port 3001**, not 3000: root `.env` `WEB_PORT=3001` /
  `NEXTAUTH_URL=:3001` (a separate next-dev holds `:3000`). Playwright resolves
  the port via `e2e/helpers/baseUrl.ts` — never hardcode `:3000` in new specs.
  Canonical/CI stays `:3000`.
- **gh CLI has two accounts:** active `SpearheadAnalytica` (full write) and
  `david-catarious_kentro` (Kentro EMU — reads only; GitHub blocks EMU writes
  outside its enterprise). `gh auth switch --user <name>` to flip; `git push`
  authenticates as SpearheadAnalytica via GCM regardless.
- **Tooling not on default PATH:** `node.exe` + `gh.exe` live under
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages`. Run e2e via that `node.exe` +
  `e2e/node_modules/@playwright/test/cli.js`. Docker CLI needs
  `export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"` per shell.
  Host Node LTS is 22 (matches the container after Sprint 4 T4).
- **Six queue gates (Sprint 6):** the runtime queue `gates` array now runs
  `pytest -m unit`, web `tsc`, host prettier 3.9.5 `--check`, in-container
  ruff/black (root-config parity), in-container web vitest (`pnpm -F web test`),
  and in-container web eslint (`pnpm -F web lint` — added this sprint after T9's
  HealthMatrix lint failure slipped a loop that omitted eslint).
- **Framework/module reinstall dance:** after editing any `apps/web` source,
  `docker compose up -d --force-recreate web` before any e2e (next-dev hot-reload
  does not fire through the Windows bind mount). A NEW python module under `app/`
  needs `docker compose restart api`; NEVER restart api while an in-container
  pytest is running (SIGKILL 137). After editing `apps/web/package.json`,
  reinstall INSIDE the web container.
- **`anthropic` SDK is now a real dep (T0):** adding it required
  `docker compose build api` (a plain restart won't install it). Live mode also
  needs a **current** model (`claude-sonnet-5`, not the rejected `claude-opus-4-7`
  placeholder) or the boot preflight refuses to start.

## Deferred / needs a human

- **SMOKE_TEST §14 / §14.1 (live AI, key-gated):** the opt-in `@pytest.mark.live`
  specs and `smoke_live_ai.py` are committed but self-skip without a real provider
  key — no committed spec runs a live call in a keyless pipeline. Run one real
  sweep with a key to confirm the redacted `llm_calls` row and per-adapter parse
  for all five purposes. Provider-agnostic since Sprint 4 (D-024). No adapter parse
  fix was possible without a key this sprint.
- **SMOKE_TEST §25 (MailHog e2e, opt-in):** `s21-email-verify.spec.ts` self-skips
  unless the api is up with `SHIELD_EMAIL_DELIVERY_ENABLED=true`; run it once
  against MailHog to prove the token flow end-to-end through the wire.
- **SMOKE_TEST §10 (eyeball exports):** human review of the generated artifacts in
  `e2e/artifacts/`, incl. the CSF Action Plan XLSX sheet (asserted HTTP 200 by s7).
- **MFA / email web UI eyeball:** the sign-in MFA step, account enrollment section,
  and verify/forgot/reset pages have no e2e driving the UI (backend flows are
  `pytest -m unit` proven); eyeball them in a browser.
- **Hosted-demo + demo-reset (manual):** `docker-compose.demo.yml` (T9) and
  `scripts/demo-reset.*` (T8) were verified end-to-end by hand this sprint; no
  automated spec drives them.
- **reqSeq guard sweep remainder:** the broader mount-fetch-then-mutate sweep
  across the components the react-hooks rules did not force stays a Sprint 7
  candidate.
- **ESLint 10** — deferred upstream: no published Next lint stack runs on it today
  (`eslint-plugin-react` 7.37.5 uses the removed `context.getFilename()`; Next's
  babel parser hits an `eslint-scope` gap). D-018 carries a dated deferral.
- **Two documented moderate audit findings** left deliberately open (Sprint 4 T5):
  `postcss` 8.4.31 (pinned in `next@15.5.20`; XSS-stringify path N/A at build) and
  `uuid` 8.3.2 (via `next-auth@4.24.14`; buffer bug is v3/v5/v6-only). No JS dep
  manifests changed this sprint, so the posture carries unchanged.
- **Needs David (cloud infra):** `infra/terraform` (cloud/account/region/network)
  and DR runbooks are stubs; FedRAMP-authorized LLM connector; Auth.js v5 /
  Keycloak SSO cutover (the Credentials→OIDC seam exists but stays dormant);
  `azure_openai`/`bedrock`/`local` LLM adapters stay loud not-implemented until a
  deployment needs one. T9 delivered only a local hosted-demo compose.

## Test coverage status

- Backend: full `pytest -m unit` green in-container. Sprint 6 added: the live-mode
  boot preflight (`test_config.py` — missing key / unimportable SDK / placeholder
  model raise, valid boots, fixture unaffected, default-not-stale); the full
  `/ready` dependency matrix incl. offender-naming on a simulated-down dep,
  keycloak-dormant, fixture-LLM informational-only, and the anonymous-vs-authenticated
  detail redaction (`test_readiness.py`); RFC 6238 TOTP + at-rest encrypt roundtrip
  (`test_totp.py`) and the MFA enroll/verify/login-challenge + recovery-code +
  lockout-integration flow (`test_mfa_routes.py`); email verification + reset with
  hashed single-use tokens, enumeration-safety, and the login gate
  (`test_email_verification.py`); and the OpenAI token-key-per-model-family adapter
  (`test_llm_providers.py`). Live-AI parity has committed opt-in specs
  (`tests/live/test_live_ai.py`, `@pytest.mark.live`) excluded from `-m unit` and CI.
- Web unit tests: `pnpm -F web test` (vitest + testing-library + jsdom) — Sprint 6
  added `HealthMatrix.test.tsx` (renders every dependency row + all-green badge;
  degraded badge names the offender) beside the two Sprint-5 `reqSeq` guard tests.
- Web `tsc --noEmit` clean on Next 15 / React 19 / Tailwind 4. ESLint green (all 14
  react-hooks v6 rules enabled; the in-container `pnpm -F web lint` gate joined the
  queue this sprint).
- e2e: full suite green across 21 spec files (host, resolves `:3001`). Sprint 6
  added `s21-email-verify.spec.ts` (MailHog end-to-end, OPT-IN — 2 tests self-skip
  without `SHIELD_EMAIL_DELIVERY_ENABLED=true`), a seed→storage parity test to
  `s17-documents.spec.ts` (seeded client downloads a seeded released deliverable →
  200), and a seeded-Risk-Register read-only test to `s8-risk-register.spec.ts`
  (code-derived tiers + downloadable exports). Known cold-compile flake under load
  documented in `CLAUDE.md`.
- Format: repo-wide prettier `--check` clean at 3.9.5. Python ruff/black clean
  (root-config parity).
- Audit: bandit exit 0. No JS dep manifests changed this sprint, so root `pnpm
  audit` / `e2e/` `npm audit` posture carries from Sprint 5 (0 high, 2 documented
  moderates). The only python dep added is the official `anthropic` SDK (T0). No
  secret committed this sprint (manual `main...HEAD` diff scan clean).

## Lessons learned (Sprint 6)

- **A feature flag that refuses to boot is worse than a real control.** The D-020
  MFA / email-verify flags used to refuse startup because no flow existed. Sprint 6
  built the flows (D-027/D-028) and flipped the flags to GATE enforcement — an
  enrolled user is always challenged; the flag decides what happens to the
  not-yet-enrolled. "Fail loudly" means fail on the real misconfiguration, not on
  a control you simply haven't built yet.
- **"Declared" is not "installed."** T0's live-AI dep (`anthropic`) surfaced only
  as an `ImportError` on the first live Run-AI because the adapter lazy-imports and
  the image was never rebuilt. The boot preflight now explicitly checks SDK
  importability, not just that the key is set — guarding the "declared but image
  not rebuilt" trap that a config check alone would miss.
- **The seed must write where the API reads.** T2's 410 was a pure storage-backend
  mismatch: the seed wrote to a local-FS stub while the S3-backed API read MinIO.
  Routing the seed through the SAME `get_storage()` factory the API uses is the
  fix, and the e2e now downloads a seeded deliverable to prove the two agree.
- **Reset counters ONLY on a fully successful login.** T10's subtle MFA bug: the
  login path cleared the password-failure counter the moment the password was
  correct — before the SECOND factor gate. A password-holding attacker could then
  re-login between TOTP guesses to evade second-factor lockout. The rule is now
  invariant: counters reset only on `_register_successful_login`, and both
  second-factor endpoints feed the same lockout counter.
- **A public probe must not leak operator detail to anonymous callers.** T10's
  `/ready` reduced each dependency's `detail` (exception types, LLM config state)
  to a generic per-status string for anonymous callers while still naming offenders
  + statuses (LBs/k8s need those); authenticated callers get the full detail. A
  health endpoint is an information-disclosure surface, not just a boolean.
- **Run every gate the pipeline runs.** T9 caught a latent CI lint failure
  (`HealthMatrix.tsx`, react-hooks set-state-in-effect) that slipped because the
  loop's gate set omitted eslint. The in-container `pnpm -F web lint` gate is now in
  the queue array — the loop's gates now equal CI's.
- **Poll long gates in the foreground to the end of the iteration.** The loop's
  recurring failure mode is parking on a background monitor and returning
  mid-iteration. Run pytest/e2e detached and poll synchronously in sub-timeout
  bursts within the iteration.
