# Project Context — state of `main`

_Last updated: 2026-07-09 (Sprint 3 close — audit correctness & honesty). This
file describes the project as of the branch it sits on and is updated ONLY as
part of a PR. Durable facts and environment gotchas live in `CLAUDE.md`;
personal in-flight status lives in `context/<name>.md`; per-sprint detail lives
in `SPRINT_<n>.md`._

## Current state

- **v2 work order (Parts A–F) merged to `main`** (PR #1, migrations 0015–0025,
  `v3.0.0`): all four service surfaces, multi-tenant onboarding, AI job
  registry, CSF Playbook engine, Risk Register, F hardening pass.
- **Sprint 1 "smoke sweep" complete** (`qa/smoke-sweep-sprint-1`, PR #16,
  `v3.0.1`): `SMOKE_TEST.md` backed by a green Playwright smoke suite under
  `e2e/smoke/`; offline fixture-mode AI (D-017), typed registration errors
  (D-016).
- **Sprint 2 "findings burn-down" complete and MERGED** (PR #19, `v3.0.2`):
  11 tasks, CI `e2e` job added, suite grew to 16 files / 34 tests.
- **Sprint 3 "audit correctness & honesty" COMPLETE** (this branch
  `fix/audit-correctness-sprint-3`, `v3.0.3`): 8 tasks (T0–T7) burning down the
  2026-07-08 deep repo audit. Full exit gate set green — 34-test e2e, `pytest
  -m unit`, web `tsc`, and the new repo-wide prettier `--check` (3.9.4). The
  headline fix: CSF live-mode Run-AI silently discarded responses (prompt/parser
  schema mismatch) — now aligned and grounded, with a contract test. Auth grew
  real forced-reauth + refresh-token rotation, run-AI/auth routes got Redis rate
  limiting, exports follow spec §15.5, `llm_calls` are tenant-attributable, and
  the docs set (architecture.md especially) stopped describing a system that
  doesn't exist.

### Sprint 3 task → commit

| Task | What shipped | Commit |
| --- | --- | --- |
| T0 | CSF Run-AI prompt/parser schema align + payload grounding + contract test | `03175f8` |
| T1 | Draft-exists guard ported to ATT&CK + ZT mint routes (idempotent 200) | `4056170` |
| T2 | Auth: real forced re-auth + refresh rotation; dead flags fail loud (D-020) | `bc491b9` |
| T3 | Rate limiting on auth + run-AI (Redis fixed-window, typed 429, fail-open) | `b48a39f` |
| T4 | Spec §15.5 filenames for CSF Playbook + Risk Register exports | `b14ccd5` |
| T5 | `llm_calls.client_id` tenant attribution (migration 0027, C0) | `cea0c5a` |
| T6 | Docs truth pass: architecture rewrite, reviewer purge, DECISIONS dedupe | `aeac503` |
| T7 | Loop hygiene + wrap-up (prettier gate, SMOKE_TEST sync, snapshot) | `a4ff3dd` |
| — | Final audit + CONTEXT refresh (rate-limiter atomicity fix, coverage) | this commit |

New migrations this sprint: `0026` (`users.active_refresh_jti`, T2), `0027`
(`llm_calls.client_id`, T5) — both additive/SQLite-safe (C0). New DECISIONS:
**D-020** (auth posture), **D-021** + erratum **D-022** (duplicate-D-015 dedupe),
**D-023** (D-005/D-006 reviewer-role + release-flow supersession).

The closing audit (this commit) found one real hardening item and fixed it:
the T3 Redis limiter armed the window TTL with a **separate** `EXPIRE` after
`INCR`, so a Redis error landing between the two calls could leave a key
counting up forever with no expiry — a permanent lockout, the opposite of the
module's fail-open promise. It now runs `INCR` + `EXPIRE … NX` in one
`MULTI/EXEC`, self-healing and window-preserving. Coverage grew to match: an
atomic-TTL test, a route-dependency 429 test for the run-AI path, and a
`client_id` assertion on the tech_debt extract call site (the one egress path
that bypasses `run_job`). Spec-compliance and security sub-audits came back
clean — no other code changes.

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
- **Prettier gate:** run `npx -y prettier@3.9.4 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`
  from the repo root before every commit — CI enforces the same version.

## Deferred / needs a human

- **Sprint 4 — framework-majors bundle** (D-018, rescheduled by David
  2026-07-08): Next 15/16, React 19, Tailwind 4, eslint 10, Node 22. The 7
  dependabot major PRs were closed unmerged pending this. Root `pnpm audit`
  shows 17 advisories, all in `next < 15.5.16` — cleared by the Next major, not
  a branch regression.
- **Sprint 5 candidates — client-facing features:** deliverable release-to-client
  flow (note: D-023 records that sprint-5 may deliberately reintroduce the
  release flow D-005/D-006 removed), `/home` value-loop card, POA&M step.
- **Needs David (infra):** `infra/terraform` (cloud/account/region/network) and
  DR runbooks are empty `.gitkeep` stubs — README now marks them planned, not
  present. FedRAMP LLM connector still Sprint-4+.
- **SMOKE_TEST §14 (live-AI):** now meaningful post-T0 — one live `csf_score`
  run with a real `ANTHROPIC_API_KEY`; confirm a redacted `llm_calls` row with a
  `client_id` set and no PII. Left unchecked (no committed spec can prove it).
- **SMOKE_TEST §10:** eyeball the 8 export artifacts in `e2e/artifacts/` (now
  §15.5-named); each already asserted 200 + content-type.
- **The v2 Developer Work Order document** for `reference-docs/` was not
  supplied — `reference-docs/README.md` records that Parts A–F decisions live in
  DECISIONS.md + code, and the spec's 108-vs-implemented-106 CSF subcategory
  discrepancy (verified live: `len(SUBCATEGORIES)==106`; NIST CSF 2.0 Final = 106).

## Test coverage status

- Backend: full `pytest -m unit` green in-container (engines, cross-tenant
  isolation, AI fixtures, draft guards for CSF/attack/zt, auth reauth+rotation,
  rate limiter incl. fail-open + atomic-TTL arming + run-AI dependency 429,
  deliverable filenames, llm_call attribution incl. the tech_debt extract path).
  Note: the `integration` pytest marker is declared but unused; there is no
  `pnpm test` script (documented in T6's docs pass).
- Web: `tsc --noEmit` clean.
- e2e: 34/34 green across 16 spec files (host, resolves `:3001`). Known
  cold-compile flake under load documented in `CLAUDE.md` — a re-run clears it.
- Format: repo-wide prettier `--check` clean at 3.9.4.

## Lessons learned (Sprint 3)

- **A schema mismatch is a silent-failure bug, not a style nit.** T0's CSF
  prompt told the model to return one shape while the parser read another — live
  mode threw away every suggestion and no one noticed because fixture mode used
  the parser's shape. Fail-loudly means a zero-change parse now logs a warning.
- **Enforce or retract — never document a control you don't have.** T2's README
  claimed forced re-auth + idle timeout that nothing enforced. The honest fix was
  to build the real thing (auth_time claim + refresh rotation) AND correct the
  docs, plus make the dead MFA/email-verify flags refuse boot rather than lie.
- **Docs drift is a correctness bug at consultant scale.** architecture.md
  described a single-tenant Celery-worker system that never shipped; a reader
  orienting from it would design against fiction. T6 rewrote it to the real
  multi-tenant, synchronous-AI, no-worker system.
- **Additive-only migrations keep the SQLite suite honest (C0).** Both new
  columns (`active_refresh_jti`, `client_id`) are nullable via
  `batch_alter_table`, so old rows parse unchanged and tests stay on SQLite.
- **The format gate is a real gate.** The Sprint 2 loop shipped unformatted
  files that only CI caught; running host prettier `--check` (lockfile-pinned)
  before every commit is now in CLAUDE.md and this sprint enforced it each task.
