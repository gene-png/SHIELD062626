# SHIELD v3.0 — Build Report

> Live build status. The single-page snapshot of what is built, what gates it,
> and what is deferred. Narrative history lives in `CHANGELOG.md`; non-obvious
> choices in `DECISIONS.md`; state-of-`main` in `CONTEXT.md`.

## Latest change — 2026-07-16 (Sprint 7 · GCP live path + close the client loop, `[3.4.0]`)

**The live-AI path is now proven against a real provider with no static key, and
the client loop is closed.** Seven tasks (T0–T6) on `feat/gcp-vertex-sprint-7`.
See `CHANGELOG.md` `[3.4.0]` and `SPRINT_7.md` for the full record.

Highlights:

- **Vertex AI provider via ADC (T0, D-029):** a live `VertexProvider` beside
  `GeminiProvider`, selected by `SHIELD_LLM_PROVIDER=vertex`, calling the regional
  `{region}-aiplatform.googleapis.com` `generateContent` endpoint authenticated
  with **Application Default Credentials — no static API key**. `google-auth` is a
  real dep; the bearer token never reaches logs / `llm_calls.error_message` /
  exception text (rides the header, not the URL — unit-locked). Shared
  body-build/parse with `gemini`; `live_llm_readiness()` requires project +
  importable SDK + resolvable ADC or fails loudly at boot (D-026 parity). Compose
  bind-mounts the host gcloud dir read-only; ADC never enters the repo or image.
- **GCP live validation sweep (T1):** all five AI purposes exercised live through
  the redaction seam on Dave's box (`vertex`/`gemini-2.5-flash`, ADC-only,
  2026-07-15). Two adapter defects found + fixed (`google-auth[requests]` extra;
  loud `finishReason` guard + output cap 4096→8192 + bounded `thinkingBudget` for
  gemini-2.5+), all `pytest -m unit` locked. SMOKE §14/§14.1 annotated
  GCP-validated; `.env` reverted to fixture; keyless self-skips clean.
- **Client release notification email (T2, D-030):** the shared release helper
  emails the tenant's active client-role users on release (service, title/version,
  `/documents` link) when delivery is on — best-effort, release is the source of
  truth; cross-tenant users/admins never notified. Four `pytest -m unit` tests.
- **Email delivery on by default in dev/CI (T3):** `SHIELD_EMAIL_DELIVERY_ENABLED`
  defaults `true` (SMTP → the `mailhog` service) so the register/verify/reset loop
  is real every run and `s21-email-verify.spec.ts` runs instead of self-skipping;
  `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY` stays `false` (flipping it breaks every e2e
  sign-in).
- **reqSeq stale-fetch guard sweep remainder (T4):** finished the Sprint-5
  carry-over across the admin workspaces/panels the react-hooks rules didn't force,
  guarding only where a stale mount-fetch can clobber newer state; vitest guards
  for the two highest-traffic newly-guarded components.
- **Auth.js v5 migration (T5):** `next-auth@4.24.14` → Auth.js v5
  (`5.0.0-beta.31` + `@auth/core`); `getServerSession` → `auth()` at 34 sites, MFA
  code-signal re-wired, behavior-identical (auth e2e green). Clears the
  `uuid@8.3.2` moderate (`uuid` gone from the lockfile); only the documented
  `postcss` moderate remains.

## Overall status

**`v3.0.0` shipped (PR #1, v2 work order Parts A–F). Sprints 1–6 merged; Sprint 7
complete on its branch. The live-AI path is now proven against real Vertex AI via
ADC with no static key (Sprint 7 D-029); the client release-notification loop is
closed (D-030) and the web auth stack is on Auth.js v5. Cloud infra (terraform,
FedRAMP LLM connector) remains blocked on David's cloud/account/region
decisions.**

| Milestone                                                                           | Status                     | Reference                          |
| ----------------------------------------------------------------------------------- | -------------------------- | ---------------------------------- |
| Phase 1 — Foundation (`v0.1.0`)                                                     | Complete                   | CHANGELOG (earlier history)        |
| Phase 2 — Intake (`v0.2.0`)                                                         | Complete                   | CHANGELOG (earlier history)        |
| Phase 3 — Tech Debt service (`v0.3.x`)                                              | Complete                   | CHANGELOG (earlier history)        |
| v2 work order Parts A–F (`v3.0.0`, migrations 0015–0025)                            | **Complete (PR #1)**       | DECISIONS D-021 (Part F)           |
| Sprint 1 — smoke sweep (`qa/smoke-sweep-sprint-1`, PR #16)                          | **Complete**               | `SPRINT_1.md`                      |
| Sprint 2 — findings burn-down (`fix/findings-burndown-sprint-2`)                    | **Complete (PR #19)**      | `SPRINT_2.md`, CHANGELOG `[3.0.2]` |
| Sprint 3 — audit correctness & honesty (`fix/audit-correctness-sprint-3`)           | **Complete (PR #26)**      | `SPRINT_3.md`, CHANGELOG `[3.0.3]` |
| Sprint 4 — framework majors + multi-provider LLM (`feat/majors-providers-sprint-4`) | **Complete (PR #28)**      | `SPRINT_4.md`, CHANGELOG `[3.1.0]` |
| Sprint 5 — client value loop (`feat/client-value-loop-sprint-5`)                    | **Complete (PR #31)**      | `SPRINT_5.md`, CHANGELOG `[3.2.0]` |
| Sprint 6 — real demo (`feat/real-demo-sprint-6`)                                    | **Complete (PR #33)**      | `SPRINT_6.md`, CHANGELOG `[3.3.0]` |
| Sprint 7 — GCP live path + close the client loop (`feat/gcp-vertex-sprint-7`)       | **Complete (this branch)** | `SPRINT_7.md`, CHANGELOG `[3.4.0]` |
| Infra (cloud terraform, FedRAMP LLM connector)                                      | **Blocked (needs-David)**  | `DELIVERY_PLAN.md`                 |

## Product surface at `v3.0.0`

- **Four assessment services:** Technical Debt Review, Zero Trust (CISA ZTMM 2.0
  - DoD ZTRA), NIST CSF 2.0 (10-step Playbook), MITRE ATT&CK coverage (full
    Enterprise matrix per D-007).
- **Risk Register** (5×5 NIST 800-30) synthesized from the four services; tier
  is code-derived, never prompted.
- **Multi-tenant** consultant-led onboarding (shared DB + `client_id`, D-015).
- **AI job registry** behind the single redacting egress client (`app/ai/llm.py`);
  fixture-mode is fully offline + deterministic (D-017). "AI suggests, code
  computes" — deterministic engines own every total/tier/roll-up.

## Current gate set

The repo-wide gates enforced this sprint (and encoded in the sprint queue):

| Gate                  | Command                                                                                                                        | Where                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| Backend unit tests    | `docker compose exec -T api pytest -m unit -q`                                                                                 | api container         |
| Web typecheck         | `docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"`                                                 | web container         |
| Web unit tests        | `docker compose exec -T web sh -lc "cd /app && pnpm -F web test"` (vitest, Sprint 5 T8; Sprint 6 added HealthMatrix)           | web container         |
| Web eslint            | `docker compose exec -T web sh -lc "cd /app && pnpm -F web lint"` (in the queue gate set, Sprint 6)                            | web container         |
| Full e2e smoke suite  | `cd e2e && npx playwright test` (21 spec files; s21 email-verify now RUNS — Sprint 7 T3 turned MailHog delivery on by default) | host → composed stack |
| Runtime axe WCAG A/AA | `s16-axe.spec.ts` (part of the suite)                                                                                          | host → composed stack |
| Python lint/format    | `docker compose exec -T api sh -lc "ruff check --no-cache . && black --check ."` (root-config parity, Sprint 4 T0)             | api container         |
| Repo format           | `npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`                                                        | host                  |
| Dependency audit      | `pnpm audit` (root) / `npm audit` (`e2e/`)                                                                                     | host                  |

### CI jobs (`.github/workflows/ci.yml`)

Four jobs gate every push / PR to `main`:

1. **python** — ruff, black, bandit, `pytest -m unit`.
2. **web** — prettier, eslint (incl. static `jsx-a11y`), tsc, `next build`.
3. **secret-scan** — gitleaks.
4. **e2e** _(new this sprint, T3)_ — `docker compose up`, fail-loud health waits
   on `:8000` + web, seed, `npm ci` + chromium, `playwright test` (includes the
   axe sweep, T4), `always()` upload of `playwright-report/` + `test-results/`,
   30-min timeout.

> **CI-proof note (honesty):** the `e2e` job's first real run needs the
> review-required branch push, which is Dave-manual. The step block was proven
> locally end-to-end against `e2e/README.md` (T2), and the YAML validated.

## Gate results at HEAD (Sprint 7 close)

```
pytest -m unit         → green (in api container, full suite; Sprint 7 added Vertex adapter + release-notification tests)
web tsc --noEmit       → clean (Next 15 / React 19 / Tailwind 4; Auth.js v5)
web vitest (pnpm test) → green 12/12 (in web container; Sprint 7 added SignInForm.test.tsx)
web eslint (pnpm lint) → 0 errors (1 pre-existing postcss warning)
prettier --check       → clean (3.9.5, repo-wide)
ruff / black --check   → clean (root-config parity)
e2e (host)             → full suite green (s21 email-verify now RUNS — T3 turned MailHog delivery on by default)
```

(Exact figures recorded in the T11 commit / CONTEXT.md. The machine running this
sprint serves web on **:3001**; Playwright resolves the port via
`e2e/helpers/baseUrl.ts`, canonical/CI is `:3000`.)

## OWASP Top 10 cumulative review (through Sprint 6, `v3.3.0`)

| ID  | Category                  | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Broken Access Control     | PASS — `current_user` + `require_role`; multi-tenant `X-Client-Id` scoping returns 404 on cross-tenant access (no existence oracle); admin layout double-checks server-side. Sprint 5: the client deliverable list + artifact download are released-only and tenant-scoped (404, never 403; unit-tested deny matrix); `/admin/audit` read routes and `/ai/preview` are admin-only                                                                                                                                                                                                                                                                                                                     |
| A02 | Cryptographic Failures    | PASS — Argon2id + HS256 JWT; placeholder secret refused in prod; sha256 on every upload; S3 SSE=KMS in prod                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| A03 | Injection                 | PASS — SQLAlchemy parameterized queries only; app-generated storage keys; filename sanitization                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| A04 | Insecure Design           | PASS — append-only audit log (two layers); MIME allowlist + size cap; redaction disclosure before upload; explicit service-request lifecycle                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| A05 | Security Misconfiguration | PASS — `assert_safe_for_runtime`; HSTS + CSP + X-Frame-Options + Permissions-Policy + Referrer-Policy at the edge (asserted by `s15-headers.spec.ts`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| A06 | Vulnerable Components     | PASS — pip-audit + `pnpm audit` in CI, Dependabot opens fix PRs; on the Next 15 / React 19 / Tailwind 4 / ESLint 9 / Node 22 stack (Sprint 4). Root `pnpm audit` and `e2e/` `npm audit` both report **0 critical / 0 high** (Sprint 4 T5); Sprint 7 T5's Auth.js v5 migration (next-auth `5.0.0-beta.31` + `@auth/core@0.41.2`) removed the `uuid@8.3.2` moderate entirely — `uuid` no longer appears in the lockfile — leaving **one** documented root moderate (`postcss` 8.4.31 pinned in next@15, XSS-stringify path N/A at build), deliberately open and not exploitable in our use. (The npm audit HTTP endpoint currently 410s upstream; posture verified from the lockfile dependency graph.) |
| A07 | ID & Auth Failures        | PASS WITH NOTES — email+password + Argon2id + lockout + account-existence oracle defense + typed reg errors (D-016); refresh-token rotation (replay rejected) + daily forced-reauth ceiling (`auth_time` claim, typed 401) + 30-min refresh TTL as idle timeout. **Sprint 6: real TOTP MFA (D-027, RFC 6238, encrypted secret at rest, single-use recovery codes, second-factor failures feed account lockout) and real email verification + password reset (D-028, hashed single-use time-bounded tokens, enumeration-safe) now SHIP** — the D-020 flags gate enforcement instead of refusing boot. Keycloak SSO cutover remains a needs-David deferral                                              |
| A08 | Software & Data Integrity | PASS — audit rows immutable by contract; sha256 stored + audited on upload                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| A09 | Logging & Monitoring      | PASS — structured JSON + correlation IDs; audit + notification fan-out on state change; `llm_calls` rows record redacted-count only. Sprint 5: the append-only `audit_entries` + `llm_calls` stores gained their first read surface (`/admin/audit`, admin-only, read-only, correlation-linked) — the trail is now reviewable, not just written                                                                                                                                                                                                                                                                                                                                                       |
| A10 | SSRF                      | PASS — LLM endpoint env-configured only; no user-supplied URLs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

## Open items / deferred (needs-David or Sprint 7)

1. **PR push / merge** of `feat/real-demo-sprint-6` — review-required.
2. **SMOKE_TEST §10** — human eyeball of the generated export artifacts in
   `e2e/artifacts/` (each already asserted HTTP 200 + content-type by s7/s8),
   including the Sprint-5 CSF Action Plan XLSX sheet.
3. **SMOKE_TEST §14 / §14.1 — GCP-VALIDATED 2026-07-15 (Sprint 7 T1):** the
   live-AI opt-in specs were run for real against Vertex AI (`vertex`/
   `gemini-2.5-flash`, ADC-only) across all five purposes — redacted `llm_calls`
   row, no PII, per-adapter response parse all confirmed; two adapter defects found
   - fixed (D-029 addendum). The specs still self-skip keyless, so CI/loop stay
     green without a key; a keyed/ADC re-run remains the way to re-verify.
4. **SMOKE_TEST §25 — now CI-green (Sprint 7 T3):** `s21-email-verify.spec.ts`
   RUNS (not skips) in dev + CI because `SHIELD_EMAIL_DELIVERY_ENABLED` now
   defaults `true` (SMTP → the `mailhog` service); the end-to-end token flow is
   exercised on every run. **Still open:** SMOKE §29 (release-notification) has no
   e2e eyeballing the mail in MailHog — the four `test_release_notification.py`
   unit tests prove recipient selection + body + best-effort semantics with the
   sender stubbed.
5. **Cloud infra (needs-David):** `infra/terraform` (AWS GovCloud / Azure Gov —
   needs account/region/network decisions), FedRAMP-authorized LLM connector,
   Keycloak OIDC/SSO cutover (the Auth.js v5 migration landed in Sprint 7 T5;
   the Credentials→OIDC provider swap stays dormant), DR runbooks. Sprint 6 T9 delivered only a
   local hosted-demo compose, not cloud provisioning. See `DELIVERY_PLAN.md`.
6. **Sprint 8 candidates:** ESLint 10 (blocked upstream — no Next lint stack runs
   on it, D-018); the `postcss` 8.4.31 moderate (clears on the next upstream Next
   bump); the attack/zt/tech-debt assessment mint routes still share CSF's old
   unbounded-version pattern (Sprint 2 T7 guarded CSF only); the Auth.js v5
   Credentials→OIDC/Keycloak SSO cutover (the seam exists, stays dorment);
   `azure_openai`/`bedrock`/`local` LLM adapters (loud not-implemented until a
   deployment needs one); an e2e that eyeballs the release notification in MailHog
   (SMOKE §29). The Sprint-5 `reqSeq` stale-fetch sweep is now COMPLETE (Sprint 7
   T4).

## Significant decisions

See [`DECISIONS.md`](DECISIONS.md) for the full log. Highlights:

- **D-007 (FLIPPED):** ATT&CK uses the full Enterprise matrix (~600 techniques).
- **D-015:** Multi-tenant shared DB with `client_id` on every row. **D-021:**
  Part F harden-and-ship posture (renumbered from a duplicate D-015 heading,
  erratum D-022).
- **D-016 / D-017:** typed registration errors; offline deterministic
  fixture-mode AI.
- **D-019:** reject reserved/special-use TLDs at domain-approval time
  (renumbered from D-018 this sprint to avoid a collision with the unmerged
  `chore/dependabot-policy` branch, which owns D-018).
- **D-026 / D-024 / D-017:** live-AI enablement + boot preflight; multi-provider
  LLM egress; offline deterministic fixture mode.
- **D-029 (Sprint 7):** Vertex AI via Application Default Credentials as the GCP
  live path — a `vertex` provider with no static key, ADC-authenticated, token
  never logged. **D-030 (Sprint 7):** client release-notification email —
  best-effort notify, the release is the source of truth.

## How to resume

Read `BUILD_REPORT.md` (this file), `CONTEXT.md`, the last `git log --oneline
-15`, `CHANGELOG.md`, and `DECISIONS.md`. The sprint loop's machine-local facts
(port 3001, tool paths, gh read-only posture) live in
`.claude/sprint-queue.json` `scratch` and `CONTEXT.md`.
