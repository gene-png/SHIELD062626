# SHIELD v3.0 — Build Report

> Live build status. The single-page snapshot of what is built, what gates it,
> and what is deferred. Narrative history lives in `CHANGELOG.md`; non-obvious
> choices in `DECISIONS.md`; state-of-`main` in `CONTEXT.md`.

## Latest change — 2026-07-10 (Sprint 5 · client value loop, `[3.2.0]`)

**Consultant output now delivers visible value to the CLIENT role.** Eleven
tasks (T0–T10) on `feat/client-value-loop-sprint-5`. See `CHANGELOG.md`
`[3.2.0]` and `SPRINT_5.md` for the full record.

Highlights:

- **Deliverable release-to-client (T1, D-025):** migration `0028` adds nullable
  `released_at` / `released_by`; a shared helper backs four per-service release
  routes (admin-only, requires finalized, idempotent, audited); a new client
  list route returns released-only deliverables tenant-scoped, and artifact
  download admits clients for released own-tenant deliverables.
- **Client `/home` + value-loop card (T3/T4):** the §6.4 dashboard (hero only
  when a report is released, per-service phase grid, waiting-on-you — no scoring
  math) and the §2.5 `GET /clients/{cid}/value-summary` DETERMINISTIC aggregation
  (no LLM, nulls render "Pending", never fake numbers). Signed-in clients land on
  `/home`.
- **Client `/documents` (T2):** the §6.7 "WHAT YOU'VE RECEIVED" table with
  per-format §15.5 downloads.
- **CSF POA&M step (T5):** migration `0029` `csf_gap_actions` (characterize /
  prioritize / owner / deadline / resources / success criteria / POA&M ref),
  autosave CRUD, and an Action Plan sheet in the playbook XLSX — engine untouched.
- **Redaction preview gate (T6):** `POST /ai/preview` shows the exact redacted
  payload a Run-AI would egress, with no `llm_calls` row and no egress.
- **`/admin/audit` viewer (T7):** the first read surface over the append-only
  `audit_entries` + `llm_calls` stores — two-tab, cursor-paginated, filtered,
  correlation-linked, read-only.
- **Web unit-test harness (T8):** vitest + testing-library + jsdom in `apps/web`;
  the two `reqSeq` guards now have deterministic unit tests, wired into CI and
  the queue gates.
- **react-hooks v6 adoption (T9):** all 14 rules enabled (zero configured off),
  every violation fixed by pattern.

## Overall status

**`v3.0.0` shipped (PR #1, v2 work order Parts A–F). Sprints 1–5 complete on
their branches. Infra (terraform, MFA/email-verify, FedRAMP LLM connector)
remains blocked on David's cloud/account/region decisions.**

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
| Sprint 5 — client value loop (`feat/client-value-loop-sprint-5`)                    | **Complete (this branch)** | `SPRINT_5.md`, CHANGELOG `[3.2.0]` |
| Infra (terraform, MFA/email-verify, FedRAMP LLM connector)                          | **Blocked (needs-David)**  | `DELIVERY_PLAN.md`                 |

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

| Gate                  | Command                                                                                                            | Where                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------- |
| Backend unit tests    | `docker compose exec -T api pytest -m unit -q`                                                                     | api container         |
| Web typecheck         | `docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"`                                     | web container         |
| Web unit tests        | `docker compose exec -T web sh -lc "cd /app && pnpm -F web test"` (vitest, Sprint 5 T8)                            | web container         |
| Full e2e smoke suite  | `cd e2e && npx playwright test` (20 spec files / 39 tests)                                                         | host → composed stack |
| Runtime axe WCAG A/AA | `s16-axe.spec.ts` (part of the suite)                                                                              | host → composed stack |
| Python lint/format    | `docker compose exec -T api sh -lc "ruff check --no-cache . && black --check ."` (root-config parity, Sprint 4 T0) | api container         |
| Repo format           | `npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`                                            | host                  |
| Dependency audit      | `pnpm audit` (root) / `npm audit` (`e2e/`)                                                                         | host                  |

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

## Gate results at HEAD (Sprint 5 close)

```
pytest -m unit         → green (in api container, full suite)
web tsc --noEmit       → clean (Next 15 / React 19 / Tailwind 4)
web vitest (pnpm test) → green (4 tests, in web container; Sprint 5 T8)
eslint .               → 0 errors (all 14 react-hooks v6 rules enabled; T9)
prettier --check       → clean (3.9.5, repo-wide)
ruff / black --check   → clean (root-config parity)
e2e (host, :3001)      → 39/39 green, 20 spec files
```

(Exact figures recorded in the T10 commit / CONTEXT.md. The machine running this
sprint serves web on **:3001**; Playwright resolves the port via
`e2e/helpers/baseUrl.ts`, canonical/CI is `:3000`.)

## OWASP Top 10 cumulative review (through Sprint 5, `v3.2.0`)

| ID  | Category                  | Status                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Broken Access Control     | PASS — `current_user` + `require_role`; multi-tenant `X-Client-Id` scoping returns 404 on cross-tenant access (no existence oracle); admin layout double-checks server-side. Sprint 5: the client deliverable list + artifact download are released-only and tenant-scoped (404, never 403; unit-tested deny matrix); `/admin/audit` read routes and `/ai/preview` are admin-only                                                      |
| A02 | Cryptographic Failures    | PASS — Argon2id + HS256 JWT; placeholder secret refused in prod; sha256 on every upload; S3 SSE=KMS in prod                                                                                                                                                                                                                                                                                                                            |
| A03 | Injection                 | PASS — SQLAlchemy parameterized queries only; app-generated storage keys; filename sanitization                                                                                                                                                                                                                                                                                                                                        |
| A04 | Insecure Design           | PASS — append-only audit log (two layers); MIME allowlist + size cap; redaction disclosure before upload; explicit service-request lifecycle                                                                                                                                                                                                                                                                                           |
| A05 | Security Misconfiguration | PASS — `assert_safe_for_runtime`; HSTS + CSP + X-Frame-Options + Permissions-Policy + Referrer-Policy at the edge (asserted by `s15-headers.spec.ts`)                                                                                                                                                                                                                                                                                  |
| A06 | Vulnerable Components     | PASS — pip-audit + `pnpm audit` in CI, Dependabot opens fix PRs; on the Next 15 / React 19 / Tailwind 4 / ESLint 9 / Node 22 stack (Sprint 4). Root `pnpm audit` and `e2e/` `npm audit` both report **0 critical / 0 high** (Sprint 4 T5); two root moderates (`postcss` 8.4.31 pinned in next@15, `uuid` 8.3.2 via next-auth@4) are deliberately open and documented — not exploitable in our use, clear on upstream/Auth.js-v5 bumps |
| A07 | ID & Auth Failures        | PARTIAL — email+password + Argon2id + lockout + account-existence oracle defense + typed reg errors (D-016); refresh-token rotation (replay rejected) + daily forced-reauth ceiling (`auth_time` claim, typed 401) + 30-min refresh TTL as idle timeout; MFA + email verification flows not built — flags fail loudly at startup (Master Spec §2; Sprint 3 T2, D-020)                                                                  |
| A08 | Software & Data Integrity | PASS — audit rows immutable by contract; sha256 stored + audited on upload                                                                                                                                                                                                                                                                                                                                                             |
| A09 | Logging & Monitoring      | PASS — structured JSON + correlation IDs; audit + notification fan-out on state change; `llm_calls` rows record redacted-count only. Sprint 5: the append-only `audit_entries` + `llm_calls` stores gained their first read surface (`/admin/audit`, admin-only, read-only, correlation-linked) — the trail is now reviewable, not just written                                                                                        |
| A10 | SSRF                      | PASS — LLM endpoint env-configured only; no user-supplied URLs                                                                                                                                                                                                                                                                                                                                                                         |

## Open items / deferred (needs-David or Sprint 6)

1. **PR push / merge** of `feat/client-value-loop-sprint-5` — review-required.
2. **SMOKE_TEST §10** — human eyeball of the generated export artifacts in
   `e2e/artifacts/` (each already asserted HTTP 200 + content-type by s7/s8),
   now including the Sprint-5 CSF Action Plan XLSX sheet.
3. **SMOKE_TEST §14** — one live-AI run with a real provider key; confirm a
   redacted `llm_calls` row (correct provider/model/client_id) and no PII.
   Provider-agnostic since Sprint 4 (D-024).
4. **Infra (needs-David):** `infra/terraform` (AWS GovCloud / Azure Gov — needs
   account/region/network decisions), MFA enrollment + email verification
   (D-020 flags fail loudly at boot), FedRAMP-authorized LLM connector, Auth.js
   v5 migration. See `DELIVERY_PLAN.md`.
5. **Sprint 6 candidates:** the `reqSeq` guard sweep across the ~12 other
   mount-fetch components (only where T9's rules force it — done; the broader
   sweep remains); ESLint 10 (blocked upstream); the attack/zt/tech-debt
   assessment mint routes still share CSF's old unbounded-version pattern
   (Sprint 2 T7 guarded CSF only).

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
