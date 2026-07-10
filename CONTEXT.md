# Project Context — state of `main`

_Last updated: 2026-07-10 (Sprint 5 close — client value loop). This file
describes the project as of the branch it sits on and is updated ONLY as part of
a PR. Durable facts and environment gotchas live in `CLAUDE.md`; personal
in-flight status lives in `context/<name>.md`; per-sprint detail lives in
`SPRINT_<n>.md`._

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
- **Sprint 5 "client value loop" COMPLETE** (this branch
  `feat/client-value-loop-sprint-5`, `v3.2.0`): consultant output now delivers
  visible value to the CLIENT role. Deliverable release-to-client flow (D-025),
  the `/home` executive dashboard (§6.4) with the cross-service value-loop card
  (§2.5, deterministic — no LLM), the `/documents` page (§6.7), a CSF POA&M
  action-plan step (step 10), a pre-egress redaction preview gate, and the first
  read surface over the append-only audit stores (`/admin/audit`). Plus three
  engineering follow-ups: a web unit-test harness (vitest + testing-library),
  adoption of all 14 react-hooks v6 rules (zero configured off), and a prettier
  3.9.5 pin sync. Two additive/C0 migrations (0028 release fields, 0029
  `csf_gap_actions`). New client-facing features justify the **minor** bump. Full
  exit gate set green — 39-test e2e, `pytest -m unit`, web `tsc`, host prettier
  `--check` (3.9.5), in-container ruff/black, and the new in-container web vitest
  gate (T8).

### Sprint 5 task → commit

| Task | What shipped | Commit |
| --- | --- | --- |
| T0 | Prettier 3.9.4→3.9.5 pin sync (supersedes dependabot #29); all four gate pins synced | `37330cc` |
| T1 | Deliverable release flow backend (D-025): migration 0028 `released_at`/`released_by`, shared release helper + 4 per-service routes, client list route, client artifact download | `1863f9a` |
| T2 | `/documents` client page (§6.7): released-deliverables table + §15.5 downloads; Documents nav; s17 | `dd2ff1b` |
| T3 | `/home` client dashboard (§6.4): hero/guidance, per-service phase grid, waiting-on-you; role landing; s18 | `bb981a5` |
| T4 | Cross-service value-loop card (§2.5): deterministic `GET /clients/{cid}/value-summary`, nulls render Pending; s19 | `3ccddca` |
| T5 | CSF POA&M step: migration 0029 `csf_gap_actions`, autosave CRUD, gap-action editor, XLSX Action Plan sheet; s7 | `2a43a13` |
| T6 | Redaction preview gate: `POST /ai/preview` (no egress, no `llm_calls` row), shared run-ai payload builders, preview UI; s7 | `0a92110` |
| T7 | `/admin/audit` viewer: `audit-entries` + `llm-calls` read routes (cursor paginated, filtered), read-only two-tab UI; s20 | `a14c1b0` |
| T8 | Web unit-test harness: vitest + testing-library + jsdom, two reqSeq guard tests, CI + runtime queue gate | `3bc2b54` |
| T9 | Adopt all 14 react-hooks v6 rules (zero off); fix every violation by pattern | `f590d99` |
| T10 | Wrap-up: SMOKE_TEST §16–§21, CHANGELOG `[3.2.0]`, BUILD_REPORT sync, D-025 verify, full gates, this snapshot | this commit |

New migrations: **0028** (deliverable release fields, T1) + **0029**
(`csf_gap_actions`, T5), both additive/SQLite-safe (C0). New DECISIONS: **D-025**
(deliverable release-to-client as a new admin-only action — explicitly not a
revival of the removed D-005/D-006 reviewer gate; D-023 anticipated it).

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
- **Prettier gate:** run `npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`
  from the repo root before every commit — CI enforces the same version (bumped
  3.9.4→3.9.5 in Sprint 5 T0).
- **Python lint gate:** the api compose service read-only-mounts the root
  `./pyproject.toml` at `/pyproject.toml` so `docker compose exec -T api sh -lc
  "cd /app && ruff check --no-cache . && black --check ."` sees the ROOT config
  and reproduces CI exactly. In the runtime queue `gates` array.
- **Web unit-test gate (new, Sprint 5 T8):** `docker compose exec -T web sh -lc
  "cd /app && pnpm -F web test"` (vitest, deterministic, mocked fetch) is now in
  the runtime queue `gates` array and the CI web job. After editing
  `apps/web/package.json`, reinstall INSIDE the web container.
- **Framework-bump reinstall dance:** after editing any `apps/web` or
  `packages/*` source, `docker compose up -d --force-recreate web` before any
  e2e (next-dev hot-reload does not fire through the Windows bind mount).
- **New python module under `app/`** needs `docker compose restart api`; NEVER
  restart api while an in-container pytest is running (SIGKILL 137).

## Deferred / needs a human

- **SMOKE_TEST §14 (live AI):** still David's pending item — needs a real
  provider key in `.env` (no committed spec can prove it; fixture mode exercises
  no live path). Provider-agnostic since Sprint 4 (D-024).
- **SMOKE_TEST §10 (eyeball exports):** human review of the generated artifacts
  in `e2e/artifacts/`, now including the Sprint-5 CSF **Action Plan** XLSX sheet
  (asserted HTTP 200 by s7; the sheet's cell content is a human eyeball item).
- **reqSeq guard sweep remainder:** T9 fixed only the components the 14 rules
  flagged; the broader mount-fetch-then-mutate sweep across the other components
  stays a Sprint 6 candidate.
- **ESLint 10** — deferred upstream: no published Next lint stack runs on it
  today (`eslint-plugin-react` 7.37.5 uses the removed `context.getFilename()`;
  Next's babel parser hits an `eslint-scope` gap). D-018 carries a dated deferral
  annotation.
- **Two documented moderate audit findings** left deliberately open (Sprint 4
  T5): `postcss` 8.4.31 (pinned in `next@15.5.20`; XSS-stringify path N/A at
  build) and `uuid` 8.3.2 (via `next-auth@4.24.14`; buffer bug is v3/v5/v6-only).
  Neither overridden; both clear on the upstream / Auth.js v5 bumps.
- **Needs David (infra):** `infra/terraform` (cloud/account/region/network) and
  DR runbooks are `.gitkeep` stubs; real MFA + email-verification flows (D-020);
  Auth.js v5 migration; `azure_openai`/`bedrock`/`local` LLM adapters stay loud
  not-implemented until a deployment needs one.
- **Client notifications/email on release** — release is visible on `/home` and
  `/documents`; an outbound notification is a deliberate future decision (Sprint
  5 out-of-scope).

## Test coverage status

- Backend: full `pytest -m unit` green in-container. Sprint 5 added contract
  tests for the release route (409 not_finalized, idempotency, audit row), the
  client deliverable list + artifact allow/deny matrix incl. the cross-tenant
  download deny (T1), the value-summary aggregation with full/partial/no data +
  the zero-`llm_calls`/no-`app.ai`-import invariant + the post-release-draft
  §12 pin (T4), `csf_gap_actions` CRUD + default-vs-override priority +
  empty-string-clears + XLSX Action Plan sheet (T5), `/ai/preview`
  equals-redaction + no-row/no-egress (T6), and the audit read routes'
  filters/cursor pagination (incl. `client_id` + date range on llm-calls) +
  client-role 403 (T7). The final-audit pass (post-T10) hardened these: it
  fixed a §12 leak where the value summary recomputed from the LATEST assessment
  version instead of the released/finalized one (a post-release DRAFT
  re-assessment would have leaked its in-progress numbers to the client card),
  and gave the tech-debt release audit action its `tech_debt.` prefix so it
  groups/filters like the other three services in the audit viewer.
- Web unit tests (NEW, T8): `pnpm -F web test` (vitest + testing-library + jsdom)
  runs 4 deterministic tests covering the two `reqSeq` stale-fetch guards
  (`MessageThread`, `CsfPlaybookPanel`) — stale-response discard + error surfaces
  to `role=alert`; each verified to bite.
- Web `tsc --noEmit` clean on Next 15 / React 19 / Tailwind 4. ESLint green with
  **all 14 react-hooks v6 rules enabled** (zero configured off, T9).
- e2e: 39/39 green across 20 spec files (host, resolves `:3001`). Sprint 5 added
  s17-documents, s18-home, s19-value-loop, s20-audit, and extended s7-csf-playbook
  (POA&M autosave + redaction preview). Known cold-compile flake under load
  documented in `CLAUDE.md` — an isolated re-run clears it.
- Format: repo-wide prettier `--check` clean at 3.9.5. Python ruff/black clean
  (root-config parity).
- Audit: root `pnpm audit` 0 critical / 0 high (2 documented moderates); `e2e/`
  `npm audit` 0 total.

## Lessons learned (Sprint 5)

- **The spec-12 release rule is the invariant, and it must be enforced server-side
  at every read.** A client sees a deliverable only after an explicit release —
  so the client list route, the artifact download path, AND the value-loop card's
  per-service numbers all gate on `released_at`. The card renders "Pending" for
  an unreleased service rather than a fake 0; leaking a draft number would be the
  same class of bug as leaking a draft document. **The final audit caught the
  subtle half of this:** gating the card's *visibility* on `released_at` is not
  enough — the *number itself* must be recomputed from the finalized
  (approved/released) assessment version, not merely the latest one, or a
  post-release DRAFT re-assessment leaks its working numbers. The
  `_latest_finalized` helper now pins the recompute to `status in
  (APPROVED, RELEASED)`.
- **"AI suggests, code computes" extends to aggregation.** The §2.5 value card is
  the most valuable page in the platform, and the temptation is to have the LLM
  "summarize the engagement." T4 kept it a deterministic sum over already-computed
  engine outputs — a unit test asserts zero `llm_calls` rows and no `app.ai`
  import in the module, so the guarantee can't silently rot.
- **Preview must share the egress builder, not re-derive it.** T6's whole value is
  that the preview shows exactly what will be sent — so run-ai and preview call
  ONE payload builder per service, and a test locks their equivalence. A preview
  that computed its own payload could drift from reality and give false comfort.
- **A read surface over an append-only store stays read-only by construction.**
  The `/admin/audit` viewer has no mutation route and no mutation affordance —
  the append-only guarantee (PG trigger + before_flush) is upheld by simply never
  offering a write, not by trusting the UI.
- **Enable lint rules by fixing the code's shape, never by suppressing.** T9
  adopted 14 react-hooks v6 rules by moving setState out of render/effect bodies
  (async IIFEs, adjust-state-during-render, interval-driven clocks) — zero rules
  configured off, zero inline disables. The full e2e suite is the regression net
  for the behavioral edits to shared components.
- **Poll long gates in the foreground to the end of the iteration.** The loop's
  recurring failure mode is parking on a background monitor and returning
  mid-iteration; a 10-minute foreground poll can also hit the Bash tool timeout
  and cascade SIGTERM to detached gate tasks (T9 hit this). Run pytest/e2e
  detached and poll in sub-timeout bursts, synchronously, within the iteration.
