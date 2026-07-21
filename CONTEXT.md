# Project Context — state of `main`

_Last updated: 2026-07-21 (Sprint 8 "prove it in the browser" MERGED as PR
#42, `v3.4.1`; Sprint 9 "activate the seam" planned — see `SPRINT_9.md` and
the staged `.claude/sprint-queue.sprint-9.json`, not yet launched). This file
describes the project as of the branch it sits on and is
updated ONLY as part of a PR. Durable facts and environment gotchas live in
`CLAUDE.md`; personal in-flight status lives in `context/<name>.md`; per-sprint
detail lives in `SPRINT_<n>.md`._

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
- **Sprint 6 "real demo"** (PR #33, `v3.3.0`): the platform became a real,
  self-standing demo — runnable live-AI path with boot-time fail-loud (D-026),
  seed→MinIO storage parity, real TOTP MFA (D-027) + real email verification /
  password reset (D-028) on the custom-JWT stack (D-020 boot-refusals gone, flags
  now gate enforcement), a full-matrix `/ready` + `/admin/health` operator view,
  a coherent downloadable Atlas demo seed with one-command reset, and a
  hosted-demo production compose. Migrations 0030 (MFA TOTP) + 0031 (email
  tokens).
- **Sprint 7 "GCP live path + close the client loop" MERGED** (PR #36,
  `v3.4.0`): the live-AI path is now **proven against
  a real provider with no static key** — Vertex AI via Application Default
  Credentials (D-029), validated end-to-end across all five AI purposes on Dave's
  box (2026-07-15). The client loop is closed with a best-effort release
  notification email (D-030); dev/CI email delivery is on by default so the
  MailHog register/verify/reset loop is real every run (s21 runs, not skips); the
  Sprint-5 `reqSeq` stale-fetch guard sweep is finished; and the web auth stack
  migrated from next-auth v4 to Auth.js v5, clearing the `uuid@8.3.2` moderate
  advisory. No new migrations. New user-facing surface (release notification) + a
  real GCP live path justify the **minor** bump. Full exit gate set green — full
  Playwright e2e, `pytest -m unit`, web `tsc`, in-container web vitest (12/12),
  in-container web eslint (0 errors), host prettier `--check` (3.9.5), and
  in-container ruff/black.

### Sprint 7 task → commit

| Task | What shipped | Commit |
| --- | --- | --- |
| T0 | Vertex AI provider adapter via ADC — `VertexProvider` on `{region}-aiplatform.googleapis.com` generateContent, Bearer ADC (no static key), shared body-build/parse with `gemini`, token never logged, `live_llm_readiness()` boot preflight; D-029 | `7dcf159` |
| T1 | GCP live validation sweep (opt-in) — all five purposes live on `vertex`/`gemini-2.5-flash` (ADC-only) through the redaction seam; found+fixed 2 adapter defects (`google-auth[requests]`; loud `finishReason` guard + cap 4096→8192 + `thinkingBudget` for 2.5+); SMOKE §14/§14.1 GCP-annotated | `329f9a5` |
| T2 | Client release notification email — shared release helper emails the tenant's active client users on release (best-effort, release is source of truth); D-030 | `4420b53` |
| T3 | Email delivery on by default in dev/CI compose (MailHog); s21 email-verify now RUNS instead of self-skipping; REQUIRE_EMAIL_VERIFY stays off | `d95f5c7` |
| T4 | reqSeq stale-fetch guard sweep remainder (Sprint-5 carry-over) across admin workspaces/panels; guards only where a stale mount-fetch clobbers newer state; two vitest guards | `37f9bd6` |
| T5 | Auth.js (next-auth) v5 migration — `getServerSession`→`auth()` at 34 sites, MFA code-signal re-wired, behavior-identical; clears the `uuid@8.3.2` moderate | `3de0626` |
| T6 | Wrap-up: SMOKE §14 GCP annotation / §25 checked / new §29 release-notification, CHANGELOG `[3.4.0]`, BUILD_REPORT sync, DECISIONS D-029/D-030 verify, full gates, this snapshot | `4796429` (PR #36 squash) |

No new migrations this sprint. New DECISIONS: **D-029** (Vertex AI via ADC as the
GCP live path) + **D-030** (client release notification, best-effort notify).

- **Sprint 8 "prove it in the browser" MERGED** (PR #42,
  `v3.4.1`): eight tasks (T0 through T7) that convert
  human-eyeball SMOKE debt into committed Playwright specs and pay the last
  mint-route debt. The release notification is now eyeballed in MailHog (§29,
  s22), the verify/forgot/reset pages and the MFA enrollment / TOTP / recovery-code
  UI are browser-driven (s23, s24), `/admin/health` and the `/documents` empty
  state have specs (s25, s17), and a double-POST to the tech-debt extract route
  reuses the open draft instead of burning a second LLM call (T1). The sprint's
  headline was an out-of-plan product fix: **MFA sign-in never revealed the TOTP
  field in the browser** because `SignInForm` sent `totp: undefined`, which
  next-auth coerced through `URLSearchParams` into the string `"undefined"`,
  defeating the backend `!totp` guard (fixed in `f10b803`; the new T4 browser spec
  caught what the Sprint-7 vitest could not). No migrations, no new DECISIONS.
  Version is tag/CHANGELOG level only; package manifests untouched. Plan was
  reviewed read-only by OpenAI Codex pre-merge (findings table in PR #37).

### Sprint 8 task → commit

| Task | What shipped | Commit |
| --- | --- | --- |
| T0 | Shared MailHog reader helper (`e2e/helpers/mailhog.ts`): `fetchLatestMessage` / `extractToken` / `subjectOf`, polls by recipient plus subject; s21 consumes it with zero behavior change | `3b7bfb7` |
| T1 | Tech-debt extract draft-exists guard: a second POST while a draft is open returns it idempotent-200 before the LLM call (no re-extract, consultant edits survive), matching CSF/attack/zt; `test_extract_versions_subsequent_lists` re-contracted to the APPROVED/RELEASED boundary | `4396f60` (+ e2e realign `b4fe0ba`) |
| T2 | `s22-release-notify.spec.ts`: isolated tenant + unique-email client, release a CSF deliverable, assert the notification in MailHog by recipient + subject + `/documents` link (SMOKE §29) | `d023226` |
| T3 | `s23-auth-pages.spec.ts`: browser-drive verify-email / forgot-password / reset-password pages end to end, then sign in with the new password | `442fca5` |
| T4 | `s24-mfa.spec.ts` part A: enroll on `/account` with a generated TOTP (otpauth dep), assert shown-once recovery codes, sign in through the UI TOTP step. **Surfaced the MFA sign-in browser bug** | `f70a8cc` (fix `f10b803`) |
| T5 | `s24-mfa.spec.ts` part B: redeem a recovery code at sign-in, prove it single-use on reuse. T4+T5 retire the manual MFA walkthrough | `1e782de` |
| T6 | `s25-admin-health.spec.ts` asserts the all-green `/admin/health` matrix on the live stack; `s17-documents.spec.ts` gains a `/documents` empty-state assertion in a fresh throwaway tenant | `57277ea` |
| T7 | Wrap-up: SMOKE annotations, CHANGELOG `[3.4.1]`, BUILD_REPORT sync, this snapshot, `context/dave.md` refresh | `b7d482d` |

No new migrations and no new DECISIONS this sprint: T1 applies the existing
CSF/attack/zt idempotency pattern, and MFA (D-027), email verify/reset (D-028),
and the release notification (D-030) all shipped earlier and were only proven in
the browser here.

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
- **Six queue gates:** `pytest -m unit`, web `tsc`, host prettier 3.9.5
  `--check`, in-container ruff/black (root-config parity), in-container web vitest
  (`pnpm -F web test`), in-container web eslint (`pnpm -F web lint`). Bandit is
  CI-only (a ruff `# noqa` does NOT suppress it — a flagged string needs its own
  `# nosec`).
- **GCP live path (Sprint 7):** live Vertex needs `SHIELD_LLM_MODE=live`,
  `SHIELD_LLM_PROVIDER=vertex`, `SHIELD_LLM_MODEL=gemini-2.5-flash`,
  `GCP_PROJECT_ID=kentro-cloudmod-dev`, `GCP_REGION=us-central1`, and host gcloud
  ADC bind-mounted read-only (`GCLOUD_CONFIG_DIR`, `%APPDATA%\gcloud` on this box)
  with `GOOGLE_APPLICATION_CREDENTIALS` pointing at the mounted file — all in the
  **gitignored** `.env`, reverted to fixture after validation. There is NO static
  Google API key anywhere. Adding `google-auth` (T0) required
  `docker compose build api` — a plain restart won't install it.
- **Framework/module reinstall dance:** after editing any `apps/web` source,
  `docker compose up -d --force-recreate web` before any e2e (next-dev hot-reload
  does not fire through the Windows bind mount). After `apps/web/package.json`
  changes (T5 Auth.js v5), reinstall INSIDE the web container. A NEW python module
  under `app/` needs `docker compose restart api`; NEVER restart api while an
  in-container pytest is running (SIGKILL 137).

## Deferred / needs a human

- **SMOKE_TEST §14 / §14.1 — GCP-validated 2026-07-15 (Sprint 7 T1):** the
  opt-in `@pytest.mark.live` specs were run for real against Vertex (ADC-only)
  across all five purposes; still self-skip keyless so CI/loop stay green without
  credentials. Re-verify with a keyed/ADC run.
- **SMOKE_TEST §29 (release notification), done in Sprint 8 T2:**
  `s22-release-notify.spec.ts` now reads the notification out of MailHog for a real
  registered client of an isolated tenant, matching on recipient, subject, and the
  `/documents` link, on top of the four `test_release_notification.py` unit tests.
- **SMOKE_TEST §10 (eyeball exports):** human review of the generated artifacts in
  `e2e/artifacts/` (each asserted HTTP 200 by s7/s8).
- **MFA / email web UI eyeball, done in Sprint 8 (T3 through T5):** the sign-in
  MFA step, the enrollment section, and the verify/forgot/reset pages are now
  browser-driven (`s24-mfa.spec.ts`, `s23-auth-pages.spec.ts`); the manual MFA
  walkthrough is retired. Driving the UI for real surfaced the `f10b803` MFA
  sign-in bug (the TOTP field never appeared in the browser).
- **Hosted-demo + demo-reset (manual):** `docker-compose.demo.yml` and
  `scripts/demo-reset.*` verified by hand; no automated spec drives them.
- **ESLint 10** — deferred upstream (D-018 dated deferral): no published Next lint
  stack runs on it today.
- **One documented moderate audit finding** left deliberately open: `postcss`
  8.4.31 (pinned in `next@15`; XSS-stringify path N/A at build). The `uuid@8.3.2`
  moderate is GONE as of Sprint 7 T5 (Auth.js v5; `uuid` no longer in the
  lockfile). The npm audit HTTP endpoint currently 410s upstream; posture verified
  from the lockfile dependency graph.
- **Needs David (cloud infra):** `infra/terraform` (cloud/account/region/network)
  and DR runbooks are stubs; FedRAMP-authorized LLM connector; the Auth.js v5
  Credentials→OIDC / Keycloak SSO cutover (the seam exists but stays dormant);
  `azure_openai`/`bedrock`/`local` LLM adapters stay loud not-implemented until a
  deployment needs one. Dave's 2026-07-13 call: local containers for now.

## Test coverage status

- Backend: full `pytest -m unit` green in-container. Sprint 8 T1 re-contracted
  `test_extract_versions_subsequent_lists` to prove versioning across the
  APPROVED/RELEASED boundary and added the tech-debt extract draft-reuse contracts
  (idempotent-200 with the same id/version/items, exactly one LLM call, exactly one
  `capability_list.extracted` audit row, and a different-artifact POST still
  returning the open draft). Sprint 7 added: the Vertex
  adapter contract + shared generateContent helpers + bearer-token-never-logged
  lock + the `finishReason`/`thinkingBudget`/output-cap fixes
  (`test_llm_providers.py`); the vertex live-readiness boot preflight
  (`test_config.py`); and release-notification recipient selection / body /
  delivery-off / SMTP-failure-doesn't-roll-back (`test_release_notification.py`).
  Live-AI parity has committed opt-in specs (`tests/live/test_live_ai.py`,
  `@pytest.mark.live`) excluded from `-m unit` and CI — GCP-validated 2026-07-15.
- Web unit tests: `pnpm -F web test` (vitest) 13/13. Sprint 8 T4 added a
  `SignInForm` guard asserting an empty-code submit omits the `totp` key (the
  regression guard for the `f10b803` MFA fix), beside the Sprint-7
  `SignInForm.test.tsx` (Auth.js v5 code-based MFA signal), the reqSeq guard tests,
  and `HealthMatrix.test.tsx`.
- Web `tsc --noEmit` clean on Next 15 / React 19 / Tailwind 4 / Auth.js v5. ESLint
  0 errors (1 pre-existing postcss warning).
- e2e: 25 spec files (host, resolves `:3001`). Sprint 8 added
  `s22-release-notify`, `s23-auth-pages`, `s24-mfa`, and `s25-admin-health`, and
  gave `s17-documents` a `/documents` empty-state test; each new spec passes
  standalone. `s21-email-verify.spec.ts` RUNS (not skips) since Sprint 7 T3 turned
  MailHog delivery on by default. Known cold-compile flake under load documented
  in `CLAUDE.md`; the authoritative full-suite run is the quiet-box shutdown
  checkpoint.
- Format: repo-wide prettier `--check` clean at 3.9.5. Python ruff/black clean
  (root-config parity).
- Audit: bandit CI-only, exit 0. Root `pnpm audit` posture: 0 high; the
  `uuid@8.3.2` moderate cleared this sprint (T5), one documented `postcss`
  moderate remains. No secret / ADC file / token committed this sprint.

## Lessons learned (Sprint 8)

- **A flow that unit tests call green can be broken for every real user.** MFA
  sign-in passed `pytest -m unit` and a Sprint-7 vitest, yet the TOTP field never
  appeared in a browser. The cause sat three layers deep: `SignInForm` sent
  `totp: undefined`, next-auth serializes credentials through `URLSearchParams`,
  and `URLSearchParams` stringifies `undefined` to `"undefined"`, so the backend
  `!totp` guard saw a truthy value and verified a bogus code. The vitest could not
  catch it because it mocks `signIn()` and never runs the real serialization. Only
  a spec driving the actual browser through the real client library exposed it.
  That is the thesis of this sprint, proven the hard way.
- **Send the key only when you have a value.** The fix was one line,
  `...(totp ? { totp } : {})` in place of always passing `totp`. A default of
  `undefined` is not the absence of a field once it crosses a string-serializing
  boundary; the silent coercion made a broken auth path look like a routine
  bad-password rejection.
- **Idempotency belongs before the expensive side effect, not at the write.** The
  tech-debt extract guard had to sit before `extract_capabilities()`, not at the
  version-mint site, or a double-click would still fire the LLM call it was meant
  to prevent. Guarding at the cheapest correct point is the difference between a
  fix and a half-fix (Codex flagged exactly this in the plan review).
- **On an overload-prone box, the per-spec standalone run is the flake arbiter.**
  Full-suite e2e here repeatedly failed on cold-compile sign-in timeouts under
  load while every spec passed alone. A spec that dies at `auth.ts` sign-in under
  load is a documented load flake, never a logic bug; the authoritative full run
  is the quiet-box shutdown checkpoint.

## Lessons learned (Sprint 7)

- **"Feasible with curl" is not "works through the adapter."** T0's Vertex path
  was proven by a raw ADC `generateContent` curl, but the first live sweep (T1)
  still found two defects a keyless unit test could never hit: `google-auth`'s
  token-refresh transport needs the `[requests]` extra (the unit test mocked
  `_bearer_token`, so it never exercised the real transport), and gemini-2.5
  "thinking" ate the output budget and truncated JSON. A real end-to-end sweep is
  the only thing that exercises the transport and the model's real output shape.
- **A silent "completed" on a truncated response is a lie.** `_parse_generate_content`
  returned a half-JSON draft as "completed" and it died downstream as an opaque
  `JSONDecodeError`. The fix is to fail LOUDLY at the seam: any non-`STOP`
  `finishReason` now raises and marks the `llm_call` failed with the real reason.
- **The token rides the header, not the URL.** The Vertex bearer token is sent as
  an `Authorization` header so an `HTTPStatusError` (which embeds only the request
  URL) cannot leak it into logs or `llm_calls.error_message` — mirroring the
  Gemini key-in-header lesson, and unit-locked.
- **Best-effort side effects must not roll back durable state.** A
  release-notification SMTP failure is logged loudly but the release still stands
  — the release is the source of truth. "Fail loudly" means surface the failure,
  not undo the thing the user already asked for.
- **A major auth dep bump is behavior-preservation work, not a feature.** The
  Auth.js v5 migration touched 34 call sites and re-wired the MFA signal (v5
  normalizes every credentials failure to `CredentialsSignin`, so the MFA branch
  surfaces via `signIn(...).code`, not `.error`). The bar was every auth e2e green
  and not one weakened test.
