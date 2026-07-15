# SHIELD v3.0 — Build Report

> Live build status. The single-page snapshot of what is built, what gates it,
> and what is deferred. Narrative history lives in `CHANGELOG.md`; non-obvious
> choices in `DECISIONS.md`; state-of-`main` in `CONTEXT.md`.

## Latest change — 2026-07-12 (Sprint 6 · real demo, `[3.3.0]`)

**The platform is now a real, self-standing demo.** Twelve tasks (T0–T11) on
`feat/real-demo-sprint-6`. See `CHANGELOG.md` `[3.3.0]` and `SPRINT_6.md` for the
full record.

Highlights:

- **Live-AI enablement + boot preflight (T0, D-026):** `anthropic` is a real
  declared runtime dep, the stale `claude-opus-4-7` default is replaced with
  `claude-sonnet-5`, and a misconfigured live deploy (missing key / unimportable
  SDK / placeholder model) now fails LOUDLY at boot instead of 500ing on first
  use. Fixture mode untouched.
- **Live-AI opt-in specs + parity sweep (T1/T7):** the 2026-07-12 manual smoke is
  a committed `@pytest.mark.live` spec + one-command script, extended to all five
  purposes (redaction + `llm_calls` + response-parse per adapter); self-skips
  keyless so CI/loop stay green.
- **Seed → storage parity (T2):** the seed writes artifact bytes through
  `get_storage()` (the same backend the API reads — MinIO), so seeded deliverables
  download 200 (410 before).
- **Full dependency-health readiness (T3):** `/ready` is now a per-dependency
  matrix (db/redis/minio/keycloak-dormant/LLM) that flips false + names the
  offender; `/admin/health` renders it.
- **Real TOTP MFA (T4, D-027):** migration `0030`; RFC 6238 TOTP on the custom-JWT
  stack (enroll / verify / login-challenge + recovery codes); the D-020 boot-refusal
  is gone — the flag now gates enforcement.
- **Real email verification + password reset (T5, D-028):** migration `0031`;
  hashed single-use time-bounded tokens over SMTP/MailHog, enumeration-safe; the
  D-020 boot-refusal is gone — the flag now gates login.
- **OpenAI reasoning-model token param (T6):** `max_completion_tokens` per model
  family (Sprint 4 D-024 follow-up).
- **Demo realism + one-command reset (T8):** the seed synthesizes a coherent Atlas
  Risk Register (code-derived tiers, downloadable exports); `scripts/demo-reset.*`
  does `down -v` → build → wait `/ready` → seed → print URLs+creds.
- **Hosted-demo compose (T9):** `docker-compose.demo.yml` runs web as a production
  build; cloud/terraform explicitly untouched.
- **Security + audit pass (T10):** MFA second-factor failures feed account lockout;
  `/ready` detail redacted for anonymous callers; audits clean/documented, no
  secret committed.

## Overall status

**`v3.0.0` shipped (PR #1, v2 work order Parts A–F). Sprints 1–6 complete on
their branches. Real MFA + email verification now SHIP (Sprint 6); cloud infra
(terraform, FedRAMP LLM connector) remains blocked on David's
cloud/account/region decisions.**

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
| Sprint 6 — real demo (`feat/real-demo-sprint-6`)                                    | **Complete (this branch)** | `SPRINT_6.md`, CHANGELOG `[3.3.0]` |
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

| Gate                  | Command                                                                                                              | Where                 |
| --------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------- |
| Backend unit tests    | `docker compose exec -T api pytest -m unit -q`                                                                       | api container         |
| Web typecheck         | `docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"`                                       | web container         |
| Web unit tests        | `docker compose exec -T web sh -lc "cd /app && pnpm -F web test"` (vitest, Sprint 5 T8; Sprint 6 added HealthMatrix) | web container         |
| Web eslint            | `docker compose exec -T web sh -lc "cd /app && pnpm -F web lint"` (in the queue gate set, Sprint 6)                  | web container         |
| Full e2e smoke suite  | `cd e2e && npx playwright test` (21 spec files; s21 email-verify opt-in, self-skips without MailHog delivery)        | host → composed stack |
| Runtime axe WCAG A/AA | `s16-axe.spec.ts` (part of the suite)                                                                                | host → composed stack |
| Python lint/format    | `docker compose exec -T api sh -lc "ruff check --no-cache . && black --check ."` (root-config parity, Sprint 4 T0)   | api container         |
| Repo format           | `npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`                                              | host                  |
| Dependency audit      | `pnpm audit` (root) / `npm audit` (`e2e/`)                                                                           | host                  |

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

## Gate results at HEAD (Sprint 6 close)

```
pytest -m unit         → green (in api container, full suite; Sprint 6 auth/health/config tests added)
web tsc --noEmit       → clean (Next 15 / React 19 / Tailwind 4)
web vitest (pnpm test) → green (in web container; Sprint 6 added HealthMatrix.test.tsx)
web eslint (pnpm lint) → 0 errors (in the queue gate set this sprint)
prettier --check       → clean (3.9.5, repo-wide)
ruff / black --check   → clean (root-config parity)
e2e (host)             → full suite green (s21 email-verify opt-in self-skips without MailHog delivery)
```

(Exact figures recorded in the T11 commit / CONTEXT.md. The machine running this
sprint serves web on **:3001**; Playwright resolves the port via
`e2e/helpers/baseUrl.ts`, canonical/CI is `:3000`.)

## OWASP Top 10 cumulative review (through Sprint 6, `v3.3.0`)

| ID  | Category                  | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Broken Access Control     | PASS — `current_user` + `require_role`; multi-tenant `X-Client-Id` scoping returns 404 on cross-tenant access (no existence oracle); admin layout double-checks server-side. Sprint 5: the client deliverable list + artifact download are released-only and tenant-scoped (404, never 403; unit-tested deny matrix); `/admin/audit` read routes and `/ai/preview` are admin-only                                                                                                                                                                                                                                                                        |
| A02 | Cryptographic Failures    | PASS — Argon2id + HS256 JWT; placeholder secret refused in prod; sha256 on every upload; S3 SSE=KMS in prod                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| A03 | Injection                 | PASS — SQLAlchemy parameterized queries only; app-generated storage keys; filename sanitization                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| A04 | Insecure Design           | PASS — append-only audit log (two layers); MIME allowlist + size cap; redaction disclosure before upload; explicit service-request lifecycle                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| A05 | Security Misconfiguration | PASS — `assert_safe_for_runtime`; HSTS + CSP + X-Frame-Options + Permissions-Policy + Referrer-Policy at the edge (asserted by `s15-headers.spec.ts`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| A06 | Vulnerable Components     | PASS — pip-audit + `pnpm audit` in CI, Dependabot opens fix PRs; on the Next 15 / React 19 / Tailwind 4 / ESLint 9 / Node 22 stack (Sprint 4). Root `pnpm audit` and `e2e/` `npm audit` both report **0 critical / 0 high** (Sprint 4 T5); two root moderates (`postcss` 8.4.31 pinned in next@15, `uuid` 8.3.2 via next-auth@4) are deliberately open and documented — not exploitable in our use, clear on upstream/Auth.js-v5 bumps                                                                                                                                                                                                                   |
| A07 | ID & Auth Failures        | PASS WITH NOTES — email+password + Argon2id + lockout + account-existence oracle defense + typed reg errors (D-016); refresh-token rotation (replay rejected) + daily forced-reauth ceiling (`auth_time` claim, typed 401) + 30-min refresh TTL as idle timeout. **Sprint 6: real TOTP MFA (D-027, RFC 6238, encrypted secret at rest, single-use recovery codes, second-factor failures feed account lockout) and real email verification + password reset (D-028, hashed single-use time-bounded tokens, enumeration-safe) now SHIP** — the D-020 flags gate enforcement instead of refusing boot. Keycloak SSO cutover remains a needs-David deferral |
| A08 | Software & Data Integrity | PASS — audit rows immutable by contract; sha256 stored + audited on upload                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A09 | Logging & Monitoring      | PASS — structured JSON + correlation IDs; audit + notification fan-out on state change; `llm_calls` rows record redacted-count only. Sprint 5: the append-only `audit_entries` + `llm_calls` stores gained their first read surface (`/admin/audit`, admin-only, read-only, correlation-linked) — the trail is now reviewable, not just written                                                                                                                                                                                                                                                                                                          |
| A10 | SSRF                      | PASS — LLM endpoint env-configured only; no user-supplied URLs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

## Open items / deferred (needs-David or Sprint 7)

1. **PR push / merge** of `feat/real-demo-sprint-6` — review-required.
2. **SMOKE_TEST §10** — human eyeball of the generated export artifacts in
   `e2e/artifacts/` (each already asserted HTTP 200 + content-type by s7/s8),
   including the Sprint-5 CSF Action Plan XLSX sheet.
3. **SMOKE_TEST §14 / §14.1 (key-gated):** the live-AI opt-in specs are committed
   but self-skip keyless; run one real live sweep with a provider key to confirm
   the redacted `llm_calls` row (correct provider/model/client_id), no PII, and
   the per-adapter response parse for all five purposes (Sprint 6 T1/T7). No adapter
   parse fix was possible without a key this sprint.
4. **SMOKE_TEST §25 (MailHog opt-in):** `s21-email-verify.spec.ts` self-skips
   unless the api is up with `SHIELD_EMAIL_DELIVERY_ENABLED=true`; run it once
   against MailHog to prove the end-to-end token flow through the wire.
5. **Cloud infra (needs-David):** `infra/terraform` (AWS GovCloud / Azure Gov —
   needs account/region/network decisions), FedRAMP-authorized LLM connector,
   Auth.js v5 / Keycloak SSO cutover, DR runbooks. Sprint 6 T9 delivered only a
   local hosted-demo compose, not cloud provisioning. See `DELIVERY_PLAN.md`.
6. **Sprint 7 candidates:** the `reqSeq` guard sweep across the remaining
   mount-fetch components (only where the react-hooks rules force it is done; the
   broader sweep remains); ESLint 10 (blocked upstream — no Next lint stack runs
   on it, D-018); the attack/zt/tech-debt assessment mint routes still share
   CSF's old unbounded-version pattern (Sprint 2 T7 guarded CSF only).

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

## How to resume

Read `BUILD_REPORT.md` (this file), `CONTEXT.md`, the last `git log --oneline
-15`, `CHANGELOG.md`, and `DECISIONS.md`. The sprint loop's machine-local facts
(port 3001, tool paths, gh read-only posture) live in
`.claude/sprint-queue.json` `scratch` and `CONTEXT.md`.
