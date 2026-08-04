# SHIELD v3.0 — Build Report

> Live build status. The single-page snapshot of what is built, what gates it,
> and what is deferred. Narrative history lives in `CHANGELOG.md`; non-obvious
> choices in `DECISIONS.md`; state-of-`main` in `CONTEXT.md`.

## Latest change: 2026-08-04 (Sprint 10 · reports you can defend, `[3.6.0]`)

**A deliverable is defensible when a reader can find the number, find what it
rests on, and find what to do about it, in that order, without leaving the
document. Sprint 10 builds that out per service.** Twelve sprints (S0 through S11)
run by the autonomous loop against `docs/SPRINTS.md` on
`feat/defensible-reports-sprint-10`. See `CHANGELOG.md` `[3.6.0]`, `SPRINT_10.md`,
the per-sprint Log in `docs/SPRINTS.md`, and DECISIONS **D-035/D-036/D-037**.

Highlights:

- **One shared export style module (S1; D-036):** `app/export_style.py` is the
  single home for deliverable styling, adopted by the five service exporters and
  `playbook_export.py`. `graded_hex()` raises on an out-of-ladder level rather than
  clamping, `escaped_title()` replaces the hotfix's inline escapes, and page
  geometry stays per-exporter (0.6in services, 0.7in playbook). Rendered output is
  byte-identical pre- and post-adoption across extracted PDF text and every XLSX
  cell value, fill ARGB and bold flag.
- **Evidence and action reach the client-visible reports (S2, S3, S4; D-035):**
  ATT&CK renders Detection/Prevention/Response citations, an evidence reference
  resolved through a tenant-filtered join, a citation-phrased defensibility stat,
  and Gap Direction cells that state citation facts only, never a cause or a
  remedy. CSF adopts the POA&M rows, a tier-model methodology block and computed
  next steps. Zero Trust gains a roadmap and persisted narratives. All three carry
  heatmap fills, ZT's on its own framework's ladder (3 rungs DoD, 4 CISA).
- **Migration 0034 plus a real race fix (S4):** `0034_zt_narratives` adds three
  nullable narrative columns. The narrative persist stopped being check-then-write
  and became a conditional parent `UPDATE ... WHERE status IN (editable)` requiring
  exactly one affected row (the D-031 shape), verified by injecting a discard
  strictly between the status check and the durable write; the pre-fix shape
  returned 200 and persisted into a discarded assessment.
- **Comprehension surfaces (S6, S7):** a per-question `What do these levels mean?`
  disclosure explains every rung with a worked example keyed to the CSF function or
  ZT stage; a `WorkflowSteps` strip in all four workspaces says where the engagement
  stands, failing loudly on an unrecognised status rather than defaulting to step 1;
  the playbook panel defines its own columns and the client home defines its five
  phase words.
- **AI transparency, consultant-facing (S8; D-037):** the fixture-mode copy stops
  claiming AI is "disabled" when Run AI works and returns the registered fixture,
  `HowAiWorks.tsx` discloses what AI drafts versus what code computes and what
  leaves the API, and risk rows badge their provenance. The client surface stays
  silent on AI, asserted by a diff guard.
- **Honesty repairs no criterion asked for:** three of four services printed
  something untrue on empty input (CSF advising maintenance at 3 of 106 scored, ZT
  reporting no gaps at target with nothing scored, tech-debt asserting `$0` for
  unrecorded cost). Two were fixed in-batch; the tech-debt and CSF header cases are
  carried as one consistent absent-versus-zero item.

**S9 did not close.** Two of its five criteria carry `needs-human` (the interview
prompt has no data path in any environment; no green full-suite e2e run exists on
this box). Its other three are met with evidence. Both are carried in `CONTEXT.md`.

One migration this batch (0034, additive and SQLite-safe). New DECISIONS
D-035/D-036/D-037. Version is a minor bump (new sections in four client-visible
deliverables plus new consultant-facing guidance and transparency surfaces);
tag/CHANGELOG level only, package manifests untouched. The LLM stayed in fixture
mode throughout and no live-LLM configuration reached a committed file.

## Overall status

**`v3.0.0` shipped (PR #1, v2 work order Parts A–F). Sprints 1–9 merged (Sprint 9
as PR #44); Sprint 10 complete on its branch. The live-AI path is proven against
real Vertex AI via ADC with no static key (Sprint 7 D-029); the client
release-notification loop is closed (D-030) and the web auth stack is on Auth.js
v5. Sprint 9 activated the long-dormant Keycloak seam as a hybrid OIDC sign-in
(flag-gated, default off, D-032, migration 0032), added a first-class draft-discard
affordance to all four services (D-031), and put the demo compose and export
eyeballs under committed automation (D-033). Sprint 10 makes the four
client-visible deliverables defensible: the citations, POA&M actions, roadmap and
narratives the engine already held now render in the report, styled from one module
(D-035, D-036, migration 0034), with the consultant workspaces gaining per-question
maturity guidance, a workflow step strip, and honest AI-status disclosure (D-037).
Cloud infra (terraform, FedRAMP LLM connector) and full Keycloak token federation
remain blocked on David's cloud/account/region decisions. Sprint 10's S9 stayed
open on two `needs-human` criteria: the interview prompt has no data path in any
environment, and no green full-suite e2e run exists on this box.**

| Milestone                                                                           | Status                     | Reference                           |
| ----------------------------------------------------------------------------------- | -------------------------- | ----------------------------------- |
| Phase 1 — Foundation (`v0.1.0`)                                                     | Complete                   | CHANGELOG (earlier history)         |
| Phase 2 — Intake (`v0.2.0`)                                                         | Complete                   | CHANGELOG (earlier history)         |
| Phase 3 — Tech Debt service (`v0.3.x`)                                              | Complete                   | CHANGELOG (earlier history)         |
| v2 work order Parts A–F (`v3.0.0`, migrations 0015–0025)                            | **Complete (PR #1)**       | DECISIONS D-021 (Part F)            |
| Sprint 1 — smoke sweep (`qa/smoke-sweep-sprint-1`, PR #16)                          | **Complete**               | `SPRINT_1.md`                       |
| Sprint 2 — findings burn-down (`fix/findings-burndown-sprint-2`)                    | **Complete (PR #19)**      | `SPRINT_2.md`, CHANGELOG `[3.0.2]`  |
| Sprint 3 — audit correctness & honesty (`fix/audit-correctness-sprint-3`)           | **Complete (PR #26)**      | `SPRINT_3.md`, CHANGELOG `[3.0.3]`  |
| Sprint 4 — framework majors + multi-provider LLM (`feat/majors-providers-sprint-4`) | **Complete (PR #28)**      | `SPRINT_4.md`, CHANGELOG `[3.1.0]`  |
| Sprint 5 — client value loop (`feat/client-value-loop-sprint-5`)                    | **Complete (PR #31)**      | `SPRINT_5.md`, CHANGELOG `[3.2.0]`  |
| Sprint 6 — real demo (`feat/real-demo-sprint-6`)                                    | **Complete (PR #33)**      | `SPRINT_6.md`, CHANGELOG `[3.3.0]`  |
| Sprint 7 — GCP live path + close the client loop (`feat/gcp-vertex-sprint-7`)       | **Complete (PR #36)**      | `SPRINT_7.md`, CHANGELOG `[3.4.0]`  |
| Sprint 8 · prove it in the browser (`feat/browser-proof-sprint-8`)                  | **Complete (PR #42)**      | `SPRINT_8.md`, CHANGELOG `[3.4.1]`  |
| Sprint 9 · activate the seam (`feat/sso-discard-demo-sprint-9`)                     | **Complete (PR #44)**      | `SPRINT_9.md`, CHANGELOG `[3.5.0]`  |
| Sprint 10 · reports you can defend (`feat/defensible-reports-sprint-10`)            | **Complete (this branch)** | `SPRINT_10.md`, CHANGELOG `[3.6.0]` |
| Infra (cloud terraform, FedRAMP LLM connector)                                      | **Blocked (needs-David)**  | `DELIVERY_PLAN.md`                  |

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

**Run them through the pipeline, not by hand:** `bash .claude/hooks/run-gate.sh push`
reads the one word in `.claude/profile` (`shield`) and sources
`.claude/profiles/shield.sh`, which is the single place the commands are written
down. Green prints `gate: shield/push passed (7 steps)`. A smaller step count means
the gate is broken, never that it passed. The `commit` variant runs the first five.
The individual commands below are what that profile runs, listed for the case where
one step fails and you need to run it in isolation.

| Gate                  | Command                                                                                                               | Where                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------- |
| Backend unit tests    | `docker compose exec -T api pytest -m unit -q`                                                                        | api container         |
| Web typecheck         | `docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"`                                        | web container         |
| Web unit tests        | `docker compose exec -T web sh -lc "cd /app && pnpm -F web test"` (vitest, Sprint 5 T8; Sprint 6 added HealthMatrix)  | web container         |
| Web eslint            | `docker compose exec -T web sh -lc "cd /app && pnpm -F web lint"` (in the queue gate set, Sprint 6)                   | web container         |
| Full e2e smoke suite  | `cd e2e && npx playwright test` (28 spec files, 64 tests, 6 skipping by design; Sprint 10 S9 added s27-comprehension) | host → composed stack |
| Runtime axe WCAG A/AA | `s16-axe.spec.ts` (part of the suite)                                                                                 | host → composed stack |
| Python lint/format    | `docker compose exec -T api sh -lc "ruff check --no-cache . && black --check ."` (root-config parity, Sprint 4 T0)    | api container         |
| Repo format           | `npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`                                               | host                  |
| Dependency audit      | `pnpm audit` (root) / `npm audit` (`e2e/`)                                                                            | host                  |

### CI jobs (`.github/workflows/ci.yml`)

Five jobs gate every push / PR to `main`:

1. **python** — ruff, black, bandit, `pytest -m unit`.
2. **web** — prettier, eslint (incl. static `jsx-a11y`), tsc, `next build`.
3. **secret-scan** — gitleaks.
4. **e2e** _(Sprint 2 T3)_ — `docker compose up`, fail-loud health waits
   on `:8000` + web, seed, `npm ci` + chromium, `playwright test` (includes the
   axe sweep), `always()` upload of `playwright-report/` + `test-results/`,
   30-min timeout.
5. **demo** _(new Sprint 9, T9)_ — on its own isolated runner (its `down -v`
   cannot touch the e2e job): logs `docker compose version` and hard-fails below
   2.24 (the `!reset` floor), runs `bash scripts/demo-reset.sh --demo` (builds
   `shield-web:demo`, seeds inside the script), then
   `SHIELD_DEMO_SMOKE=1 npx playwright test demo/`, with always-run compose-ps/logs
   diagnostics and an `if: always()` artifact upload under a unique name; 25-min
   timeout, triggers shared with e2e (push + PR to `main`).

> **CI-proof note (honesty):** the `e2e` and `demo` jobs' first real runs need
> the review-required branch push, which is Dave-manual, so their green runs are
> cited on the sprint PR open. The `demo` step block was proven locally end-to-end
> (Sprint 9 T8's destructive proving run), and the YAML validated
> (5 jobs, `demo` runs-on ubuntu-latest, 9 steps in order).

## Gate results at HEAD (Sprint 10 close)

One runner, seven steps: `bash .claude/hooks/run-gate.sh push`. Green prints
`gate: shield/push passed (7 steps)`; a smaller count means the gate is broken.

```
$ bash .claude/hooks/run-gate.sh push
gate: shield/push passed (7 steps)          → exit 0, at S11 HEAD with all five doc edits in the tree

  step 1 stack      docker compose exec -T api true                                   reachable (refuses by name if the stack is down)
  step 2 format     prettier@3.9.5 --check '**/*.{ts,tsx,js,jsx,json,md,yml,yaml}'   clean (.css is NOT in this glob; open item 14)
  step 3 python     ruff check --no-cache . && black --check .                        clean (root-config parity, in api container)
  step 4 typecheck  pnpm -F web exec tsc --noEmit                                     clean (Next 15 / React 19 / Tailwind 4 / Auth.js v5)
  step 5 lint       pnpm -F web lint                                                  0 errors (1 pre-existing postcss warning)
  step 6 webtest    pnpm -F web test                                                  118 passed (118) across 22 files, 0 skipped
  step 7 apitest    pytest -m unit -q                                                 green in api container
```

e2e sits outside the gate and was run separately at HEAD, once, warmed and
uncontended:

```
e2e (host)             → 28 spec files, 64 tests. 1 failed / 57 passed / 6 skipped in 33.2m. The 6 skips are by design (4 e2e/demo/* need SHIELD_DEMO_SMOKE=1, 2 s26-oidc-login need E2E_OIDC=1), leaving 58 runnable. The single failure was s4-techdebt.spec.ts:40 inside signIn at helpers/auth.ts:63, the test's FIRST action, before any content assertion: no strict-mode violation, no "resolved to N elements". It passes standalone. NOT a green run, and not claimed as one; see CONTEXT.md deferred item 3
```

Bandit stays CI-only (`bandit -q -c pyproject.toml -r apps/api/app`, exit 0) and a
ruff `# noqa` does not suppress it. That target excludes `apps/api/scripts`, which is
open item 5. The machine running this sprint serves web on **:3001**; Playwright
resolves the port via `e2e/helpers/baseUrl.ts`, canonical/CI is `:3000`.

## OWASP Top 10 cumulative review (through Sprint 6, `v3.3.0`)

| ID  | Category                  | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Broken Access Control     | PASS — `current_user` + `require_role`; multi-tenant `X-Client-Id` scoping returns 404 on cross-tenant access (no existence oracle); admin layout double-checks server-side. Sprint 5: the client deliverable list + artifact download are released-only and tenant-scoped (404, never 403; unit-tested deny matrix); `/admin/audit` read routes and `/ai/preview` are admin-only                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| A02 | Cryptographic Failures    | PASS — Argon2id + HS256 JWT; placeholder secret refused in prod; sha256 on every upload; S3 SSE=KMS in prod                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| A03 | Injection                 | PASS — SQLAlchemy parameterized queries only; app-generated storage keys; filename sanitization                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| A04 | Insecure Design           | PASS — append-only audit log (two layers); MIME allowlist + size cap; redaction disclosure before upload; explicit service-request lifecycle                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| A05 | Security Misconfiguration | PASS — `assert_safe_for_runtime`; HSTS + CSP + X-Frame-Options + Permissions-Policy + Referrer-Policy at the edge (asserted by `s15-headers.spec.ts`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| A06 | Vulnerable Components     | PASS WITH NOTES — pip-audit + `pnpm audit` in CI, Dependabot opens fix PRs; on the Next 15 / React 19 / Tailwind 4 / ESLint 9 / Node 22 stack (Sprint 4). Sprint 7 T5's Auth.js v5 migration removed the `uuid@8.3.2` moderate (`uuid` no longer in the lockfile). Two root advisories are now documented and deferred (both blocked on a lockfile bump this sprint deliberately did not touch): `sharp <0.35.0` **HIGH** (libvips CVEs), transitive via next@15's image optimizer and NOT introduced by this branch, and `postcss` 8.4.31 moderate (pinned in next@15, XSS-stringify path N/A at build). Neither is exploitable in our use; both clear on a Dependabot bump or a root pnpm override on `main`. (The npm audit HTTP endpoint 410s upstream; posture verified from the lockfile dependency graph.) |
| A07 | ID & Auth Failures        | PASS WITH NOTES — email+password + Argon2id + lockout + account-existence oracle defense + typed reg errors (D-016); refresh-token rotation (replay rejected) + daily forced-reauth ceiling (`auth_time` claim, typed 401) + 30-min refresh TTL as idle timeout. **Sprint 6: real TOTP MFA (D-027, RFC 6238, encrypted secret at rest, single-use recovery codes, second-factor failures feed account lockout) and real email verification + password reset (D-028, hashed single-use time-bounded tokens, enumeration-safe) now SHIP** — the D-020 flags gate enforcement instead of refusing boot. Keycloak SSO cutover remains a needs-David deferral                                                                                                                                                          |
| A08 | Software & Data Integrity | PASS — audit rows immutable by contract; sha256 stored + audited on upload                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| A09 | Logging & Monitoring      | PASS — structured JSON + correlation IDs; audit + notification fan-out on state change; `llm_calls` rows record redacted-count only. Sprint 5: the append-only `audit_entries` + `llm_calls` stores gained their first read surface (`/admin/audit`, admin-only, read-only, correlation-linked) — the trail is now reviewable, not just written                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| A10 | SSRF                      | PASS — LLM endpoint env-configured only; no user-supplied URLs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

## Open items / deferred (needs-David or a future sprint)

`CONTEXT.md` carries the full end-of-batch list with per-file line references. The
items below are the ones that gate a release decision or need David.

1. **A swallowed error on the client's only write path (Sprint 10, highest-value
   finding):** `CsfSelfAssessment.tsx:173` is a bare `catch {}` around the answer
   PATCH, violating `CLAUDE.md` principle 2 and predating the batch. A client picks
   a tier, the optimistic UI shows it saved, the PATCH fails silently, and the
   now-truthful deliverable reports the subcategory as unscored. Fixing it means
   deciding what a client sees on failure, a product decision.
2. **No green full-suite e2e run exists on this box (Sprint 10 S9, `needs-human`):**
   four attempts, the last being S11's warmed quiet-box run at 1 failed / 57 passed /
   6 skipped in 33.2m, failing inside `signIn` before any content assertion and
   passing standalone. NOT a timeout bump: `e2e/helpers/auth.ts:60-63` already wraps a
   15s `waitForURL` in `toPass({ timeout: 60000 })` and still loses to three
   sequential cold compiles. S11 measured why: after 33 minutes of browser work the
   pre-warmed routes had gone cold again (`/` back to 6.3s from 0.5s), so next-dev
   evicts compiled routes under sustained load and the back half of the suite re-pays
   what the front half already paid. Warming belongs in the harness. CI's
   fresh-runner E2E job is the authoritative arbiter per the loop protocol.
3. **The interview prompt has no data path in any environment (Sprint 10 S9,
   `needs-human`):** the `questions` table is empty, `seed_demo.py` never populates
   it, and `scripts/load_csf_tier_questionnaires.py` is invoked by nothing. Running
   reference data into the shared demo database is a human decision. SMOKE §34 box
   unchecked.
4. **Dependency posture is 5 high + 2 moderate, not the 1 high + 1 moderate
   previously recorded here (needs-David / Dependabot):** `sharp@0.34.5` (1 high,
   libvips CVEs via next@15's image optimizer, not exploitable in our use),
   `postcss@8.4.31` (4 advisories, 2 high), `brace-expansion@1.1.16` (2 high,
   previously undocumented, transitive via `minimatch@3.1.5`). None
   branch-introduced; no lockfile or manifest was touched this batch, so `main`
   audits identically. All three want the same bump: Dependabot or a root pnpm
   override on `main`. `e2e/` npm audit is clean.
5. **CI's bandit never scans `apps/api/scripts`:** `.github/workflows/ci.yml:48`
   targets `apps/api/app` only. Scanning `scripts/` finds 7 LOW including `B105` on
   the documented demo password at `seed_demo.py:129`, harmless and pre-existing.
   The credential is not the finding; the blind spot is.
6. **Two pre-existing security findings, reported not fixed, neither a batch
   regression:** XLSX formula injection (openpyxl types a leading `=` as a formula
   and free-form Notes/Rationale cells carry user text across all six exporters; a
   real fix spans six modules), and unvalidated `evidence_artifact_id` writes at
   `attack.py:401`, `csf.py:528` and `zt.py:786` (a nonexistent UUID raises
   IntegrityError while a foreign-tenant UUID commits, a boolean existence oracle at
   an admin-gated PATCH). The tenant-filtered read join is what stops the latter
   reaching a deliverable.
7. **The demo database still carries pre-S5 ATT&CK evidence:** `seed_demo.py`
   returns early whenever any `Service` row exists, so S5's richer seed is in code
   only. Only `demo-reset --demo` or a wipe picks it up, and that path is destructive
   and opt-in per D-033.
8. **SMOKE_TEST §27 — CI `demo` job:** first green PR run recorded (PR #44, run
   29939798138). The `e2e` job keeps the same posture: its green run is cited on the
   sprint-PR open, because CI triggers only on push/PR to `main`.
9. **SMOKE_TEST §10 aesthetics line:** the one explicitly-manual box that remains
   after Sprint 9 T2 replaced the five export eyeballs with content assertions.
   Sprint 10 widened it to cover heatmap coloring, since S2/S3/S4 added fills. Unit
   tests pin the fill VALUE each cell carries; whether the ramp reads as a ramp on a
   printed page, and whether text on each fill stays legible, no test can assert.
10. **Two more open Sprint 10 items with no home yet:** a second phantom Tailwind
    token (`border-border-default` emits nothing, 7 uses across 5 files; S0 swept only
    `surface-muted`, so the class was never swept systematically), and one consistent
    absent-versus-zero treatment for the summary headers (tech-debt prints
    `Total annual cost: $0` for unrecorded cost, CSF headlines a maturity rating at
    2.8% coverage unqualified; ZT already carries the fix pattern). See `CONTEXT.md`
    items 4 and 5.
11. **SMOKE_TEST §14 / §14.1, GCP-VALIDATED 2026-07-15 (Sprint 7 T1):** the
    live-AI opt-in specs were run for real against Vertex AI (`vertex`/
    `gemini-2.5-flash`, ADC-only) across all five purposes; redacted `llm_calls`
    row, no PII, per-adapter response parse all confirmed. The specs still self-skip
    keyless, so CI/loop stay green without a key; a keyed/ADC re-run re-verifies.
12. **Full Keycloak token federation / JIT provisioning (needs-David):** Sprint 9
    activated the hybrid OIDC exchange (D-032) but deliberately stopped short of the
    backend accepting Keycloak tokens as API bearers, JIT user provisioning, and
    migrating register/MFA/email flows into Keycloak. An un-discard/recovery endpoint
    (DISCARDED is terminal in v1; rows stay DB-recoverable) and stamping local
    `email_verified_at` from a Keycloak `email_verified` claim are also deferred.
13. **Cloud infra (needs-David):** `infra/terraform` (AWS GovCloud / Azure Gov,
    needs account/region/network decisions), FedRAMP-authorized LLM connector, DR
    runbooks. Sprint 6 T9 plus Sprint 9 T8/T9 deliver only a local hosted-demo
    compose and its CI proof, not cloud provisioning. See `DELIVERY_PLAN.md`.
14. **Two gate gaps (Sprint 10):** `.css` sits outside the prettier glob in both
    `.claude/profiles/shield.sh` and CI, so `tokens.css` formatting is unenforced;
    and `packages/design-system/src/tailwind-preset.ts` cannot be typechecked outside
    `apps/web` because `tailwindcss` resolves only there, which needs a devDependency
    and therefore a lockfile change.
15. **Standing upstream-blocked items:** ESLint 10 (no published Next lint stack
    runs on it, D-018); `azure_openai`/`bedrock`/`local` LLM adapters (loud
    not-implemented until a deployment needs one).

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
- **D-031 (Sprint 9):** draft discard is an admin-only soft-delete state
  transition (`DISCARDED`), with a conditional-UPDATE concurrency contract so a
  racing child write loses loudly. **D-032 (Sprint 9):** hybrid Keycloak SSO is a
  flag-gated token exchange at `POST /auth/oidc/exchange`, never a bearer; local
  HS256 JWTs stay authoritative and there is no JIT provisioning. **D-033
  (Sprint 9):** destructive-by-design automation is opt-in-gated — reset specs
  self-skip, destructive scripts never run implicitly, CI isolation is the only
  unattended venue.
- **D-035 (Sprint 10):** the ATT&CK deliverable labels citations, never causes or
  remedies. Run AI overwrites every unlocked row's tools and rationale, so those
  fields are AI-applied unless a consultant edited or locked them, and no acceptance
  state exists yet; Gap Direction cells therefore state what a row cites and nothing
  about why it is missing. No remediation column, no migration, no prompt change.
- **D-036 (Sprint 10):** one shared export style module (`app/export_style.py`) is
  the single home for deliverable styling, but page geometry stays per-exporter
  (0.6in for the four services, 0.7in for the playbook). `graded_hex()` raises on an
  out-of-ladder level rather than clamping, which is how S5 found a seed that could
  not run on an empty database.
- **D-037 (Sprint 10):** AI transparency is consultant-facing; the client screen
  stays silent. Records the client-PDF-versus-client-screen asymmetry as an open
  boundary rather than resolving it, on the reasoning that an unrecorded
  inconsistency is the one silently "fixed" by whoever notices it first.

## How to resume

Read `BUILD_REPORT.md` (this file), `CONTEXT.md`, the last `git log --oneline
-15`, `CHANGELOG.md`, and `DECISIONS.md`. The loop's plan of record and its
per-sprint Log are `docs/SPRINTS.md`, named by `.claude/sprint-plan`; the JSON
sprint queues it replaced are retired and `.claude/sprint-queue.sprint-3..9.json`
remain only as history. Machine-local facts (port 3001, tool paths, gh account
posture) live in `CONTEXT.md`.
