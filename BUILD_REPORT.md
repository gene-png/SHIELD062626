# SHIELD v3.0 — Build Report

> Live build status. The single-page snapshot of what is built, what gates it,
> and what is deferred. Narrative history lives in `CHANGELOG.md`; non-obvious
> choices in `DECISIONS.md`; state-of-`main` in `CONTEXT.md`.

## Latest change — 2026-07-07 (Sprint 2 · findings burn-down)

**The Sprint-1 smoke sweep's defect + coverage backlog is burned down.** Ten
tasks (T0–T9) on `fix/findings-burndown-sprint-2` plus this docs refresh (T10).
See `CHANGELOG.md` `[3.0.2]` and `SPRINT_2.md` for the full record.

Highlights:

- **Dependency hygiene:** `next` → 14.2.35 (latest 14 App-Router patch, no 15.x
  jump); `pnpm audit` clean of criticals, 5 remaining highs are 15.x-only and
  documented as no-non-breaking-fix (T0).
- **e2e durability + CI:** all hardcoded seeded UUIDs replaced with runtime id
  resolution (`e2e/helpers/ids.ts`, T1); fresh-stack bring-up documented in
  `e2e/README.md` (T2); a new **CI `e2e` job** runs the composed stack + seeded
  Playwright suite with artifact upload (T3); a new **runtime axe WCAG A/AA
  sweep** (`s16-axe.spec.ts`) clears all public/client/admin surfaces (T4).
- **Engine correctness:** real IG Core/Supporting metadata imported into the CSF
  catalog so Playbook Rules 2/5 fire (T5); CSF `POST assessments` now guards
  against unbounded draft minting (T7).
- **a11y:** roving tabindex on `TierPicker`/`ZtStagePicker`, heatmap
  `scope="row"` (T6); tertiary-ink contrast token darkened to WCAG AA (T4).
- **Correctness/UX:** admin domain approval rejects reserved/special-use TLDs
  with a typed 422 (T9); `/admin/management` UI + verbatim CSF prompts now
  spec-covered (T8).

## Overall status

**`v3.0.0` shipped (PR #1, v2 work order Parts A–F). Sprint 1 (smoke sweep) and
Sprint 2 (findings burn-down) complete. Sprint 3 = infra (blocked on David's
cloud/account/region decisions).**

| Milestone                                                             | Status                     | Reference                          |
| --------------------------------------------------------------------- | -------------------------- | ---------------------------------- |
| Phase 1 — Foundation (`v0.1.0`)                                       | Complete                   | CHANGELOG (earlier history)        |
| Phase 2 — Intake (`v0.2.0`)                                           | Complete                   | CHANGELOG (earlier history)        |
| Phase 3 — Tech Debt service (`v0.3.x`)                                | Complete                   | CHANGELOG (earlier history)        |
| v2 work order Parts A–F (`v3.0.0`, migrations 0015–0025)              | **Complete (PR #1)**       | DECISIONS D-021 (Part F)           |
| Sprint 1 — smoke sweep (`qa/smoke-sweep-sprint-1`, PR #16)            | **Complete**               | `SPRINT_1.md`                      |
| Sprint 2 — findings burn-down (`fix/findings-burndown-sprint-2`)      | **Complete (this branch)** | `SPRINT_2.md`, CHANGELOG `[3.0.2]` |
| Sprint 3 — infra (terraform, MFA/email-verify, FedRAMP LLM connector) | **Next (needs-David)**     | `DELIVERY_PLAN.md`                 |

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

| Gate                  | Command                                                                        | Where                 |
| --------------------- | ------------------------------------------------------------------------------ | --------------------- |
| Backend unit tests    | `docker compose exec -T api pytest -m unit -q`                                 | api container         |
| Web typecheck         | `docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"` | web container         |
| Full e2e smoke suite  | `cd e2e && npx playwright test` (16 spec files / 34 tests)                     | host → composed stack |
| Runtime axe WCAG A/AA | `s16-axe.spec.ts` (part of the suite)                                          | host → composed stack |
| Dependency audit      | `pnpm audit` (root) / `npm audit` (`e2e/`)                                     | host                  |

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

## Gate results at HEAD (Sprint 2 close)

```
pytest -m unit         → green (in api container)
web tsc --noEmit       → clean
e2e (host, :3001)      → 34/34 green, 16 spec files (recorded as 32 at the
                         time; the Sprint 3 audit's `playwright test --list`
                         count is 34)
```

(Exact figures recorded in the T10 commit / CONTEXT.md. The machine running this
sprint serves web on **:3001**; Playwright resolves the port via
`e2e/helpers/baseUrl.ts`, canonical/CI is `:3000`.)

## OWASP Top 10 cumulative review (as of `v3.0.0`)

| ID  | Category                  | Status                                                                                                                                                                                                                                                                                                                                                                |
| --- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Broken Access Control     | PASS — `current_user` + `require_role`; multi-tenant `X-Client-Id` scoping returns 404 on cross-tenant access (no existence oracle); admin layout double-checks server-side                                                                                                                                                                                           |
| A02 | Cryptographic Failures    | PASS — Argon2id + HS256 JWT; placeholder secret refused in prod; sha256 on every upload; S3 SSE=KMS in prod                                                                                                                                                                                                                                                           |
| A03 | Injection                 | PASS — SQLAlchemy parameterized queries only; app-generated storage keys; filename sanitization                                                                                                                                                                                                                                                                       |
| A04 | Insecure Design           | PASS — append-only audit log (two layers); MIME allowlist + size cap; redaction disclosure before upload; explicit service-request lifecycle                                                                                                                                                                                                                          |
| A05 | Security Misconfiguration | PASS — `assert_safe_for_runtime`; HSTS + CSP + X-Frame-Options + Permissions-Policy + Referrer-Policy at the edge (asserted by `s15-headers.spec.ts`)                                                                                                                                                                                                                 |
| A06 | Vulnerable Components     | PASS — pip-audit + `pnpm audit` in CI, Dependabot opens fix PRs; `next` on latest 14.2.x (T0). Remaining highs are 15.x-only, documented                                                                                                                                                                                                                              |
| A07 | ID & Auth Failures        | PARTIAL — email+password + Argon2id + lockout + account-existence oracle defense + typed reg errors (D-016); refresh-token rotation (replay rejected) + daily forced-reauth ceiling (`auth_time` claim, typed 401) + 30-min refresh TTL as idle timeout; MFA + email verification flows not built — flags fail loudly at startup (Master Spec §2; Sprint 3 T2, D-020) |
| A08 | Software & Data Integrity | PASS — audit rows immutable by contract; sha256 stored + audited on upload                                                                                                                                                                                                                                                                                            |
| A09 | Logging & Monitoring      | PASS — structured JSON + correlation IDs; audit + notification fan-out on state change; `llm_calls` rows record redacted-count only                                                                                                                                                                                                                                   |
| A10 | SSRF                      | PASS — LLM endpoint env-configured only; no user-supplied URLs                                                                                                                                                                                                                                                                                                        |

## Open items / deferred (needs-David or Sprint 3)

1. **PR push / merge** of `fix/findings-burndown-sprint-2` — review-required;
   also proves the new CI `e2e` job on a real runner.
2. **SMOKE_TEST §10** — human eyeball of the 8 generated export artifacts in
   `e2e/artifacts/` (each already asserted HTTP 200 + content-type by s7/s8).
3. **SMOKE_TEST §14** — one live-AI run with a real `ANTHROPIC_API_KEY`; confirm
   a redacted `llm_calls` row and no PII.
4. **Sprint 3 infra:** `infra/terraform` (AWS GovCloud / Azure Gov — needs
   account/region/network decisions), MFA enrollment + email verification,
   FedRAMP-authorized LLM connector. See `DELIVERY_PLAN.md`.
5. **Backlog carried from Sprint 2:** the attack/zt/tech-debt assessment mint
   routes share CSF's old unbounded-version pattern (T7 guarded CSF only).

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
