# Project Context — state of `main`

_Last updated: 2026-08-04 (Sprint 10 "Reports you can defend" complete on
`feat/defensible-reports-sprint-10`, targeting `v3.6.0`, PR not yet opened; Sprint 9
"activate the seam" merged as PR #44, `v3.5.0`). This file describes the project as
of the branch it sits on and is updated ONLY as part of a PR. Durable facts and
environment gotchas live in `CLAUDE.md`; personal in-flight status lives in
`context/<name>.md`; per-sprint detail lives in `SPRINT_<n>.md`, and the executable
backlog with the driver's per-sprint Log lives in `docs/SPRINTS.md`._

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
- **Sprint 5 "client value loop"** (PR #31, `v3.2.0`): deliverable release flow
  (D-025), `/home` executive dashboard, `/documents`, a CSF POA&M step, a
  pre-egress redaction preview, and the first read surface over the append-only
  audit stores (`/admin/audit`).
- **Sprint 6 "real demo"** (PR #33, `v3.3.0`): runnable live-AI path with
  boot-time fail-loud (D-026), seed to MinIO storage parity, real TOTP MFA
  (D-027) and real email verification / password reset (D-028), a full-matrix
  `/ready` plus `/admin/health`, a coherent downloadable Atlas demo seed, and a
  hosted-demo production compose. Migrations 0030 and 0031.
- **Sprint 7 "GCP live path + close the client loop"** (PR #36, `v3.4.0`): the
  live-AI path proven against a real provider with no static key, Vertex AI via
  Application Default Credentials (D-029), validated across all five AI purposes
  on Dave's box (2026-07-15). Client release notification email (D-030); the web
  auth stack migrated to Auth.js v5.
- **Sprint 8 "prove it in the browser"** (PR #42, `v3.4.1`): eight tasks
  converting human-eyeball SMOKE debt into committed Playwright specs. Headline
  was an out-of-plan product fix: MFA sign-in never revealed the TOTP field in a
  browser because `SignInForm` sent `totp: undefined`, which `URLSearchParams`
  coerced to the string `"undefined"` (fixed in `f10b803`).
- **Sprint 9 "activate the seam"** (PR #44, `v3.5.0`): hybrid Keycloak OIDC
  sign-in beside the credentials form, flag-gated and default off (D-032,
  migration 0032); a first-class draft-discard affordance in all four services
  (D-031); the demo compose and export eyeball debt under committed automation
  (D-033). Migration 0032.
- **Sprint 10 "Reports you can defend" COMPLETE on its branch**
  (`feat/defensible-reports-sprint-10`, targeting `v3.6.0`): twelve sprints (S0
  through S11) run by the autonomous loop against `docs/SPRINTS.md`. A
  deliverable is defensible when a reader can find the number, find what it rests
  on, and find what to do about it, in that order, without leaving the document.
  This batch builds that out per service. It renders the ATT&CK citations the AI
  already produced (D-035), puts the CSF POA&M into the released report, gives
  Zero Trust a roadmap and persisted narratives (migration 0034), moves
  deliverable styling into one module (D-036), makes the demo seed evidence-rich,
  explains every maturity level where the question is asked, tells the person
  looking at a workspace what its notation means, and stops the AI-status copy
  claiming AI is disabled when Run AI works (D-037). Minor bump for the new
  sections in four client-visible deliverables and the new consultant-facing
  guidance and transparency surfaces; tag and CHANGELOG level only, package
  manifests untouched. `SPRINT_10.md` was reviewed read-only by OpenAI Codex
  before the planning PR merged; S0 was added after that review and was not part
  of it.

  **Two boxes are deliberately unchecked, S9 and S11.** Ten of the twelve are
  checked. Two of S9's five criteria carry `needs-human`: the interview prompt has
  no data path in any environment, and no green full-suite e2e run exists on this
  box. Its other three criteria are met with evidence. S11 carries one
  `needs-human`: four of its five are met, and the "full e2e green on a quiet box"
  half of the last one is that same unmet run. All three are carried into the
  deferred list below rather than papered over.

### Sprint 10 sprint → commit

Each sprint carries an implementation commit and a driver verification commit
that checks the box and appends the Log line. The Log in `docs/SPRINTS.md` is the
primary record of what actually happened, including what the driver rejected.

| Sprint | What shipped                                                                                                                                                                             | Impl                   | Verify    |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | --------- |
| S0     | Web risk-tier color onto `--tier-*` tokens; the phantom `surface-muted` utility removed; the 5x5 matrix separates cells with a surface gap instead of `border-white`. Provably colorless   | `5b575c3`              | `87c6df7` |
| S1     | `app/export_style.py` as the single home for deliverable styling, adopted by six exporters; `graded_hex` raises rather than clamps; page geometry stays per-exporter; D-036                | `57068f3`              | `777f1f1` |
| S2     | ATT&CK deliverable renders curated citations, an evidence reference, a citation-phrased defensibility stat, a methodology note, and a tactic heatmap; D-035                                | `e7cd945`              | `2fc9af0` |
| S3     | CSF deliverable adopts the POA&M rows, a tier-model methodology block, computed next steps, and a tier heatmap                                                                            | `19a1fe6` + `d3864f3`  | `9c49382` |
| S4     | Migration `0034_zt_narratives`; the check-then-write race replaced by a conditional UPDATE; ZT roadmap and narratives; framework-aware stage heatmap                                      | `3590500`              | `2861df0` |
| S5     | Seed evidence depth; deepened fixture prose with the cycles frozen; computed tech-debt portfolio paragraph; DoD stage clamp fix                                                           | `ed639e3`              | `729fb9a` |
| S6     | `lib/guidance/`, `CsfMaturityReference.tsx`, per-question level disclosures, client interview labels                                                                                      | `1251a18`              | `b250c4c` |
| S7     | `WorkflowSteps.tsx` in all four workspaces, playbook column legend, home phase legend, Impact Profile explainer                                                                           | `517b4b3`              | `f58332b` |
| S8     | `AiStatusBanner` in three workspaces, honest fixture copy, tone split, risk provenance badge, `HowAiWorks.tsx`; D-037                                                                     | `56373e2`              | `1191a7e` |
| S9     | `s27-comprehension.spec.ts`, s3/s4/s5/s6/s7 extensions, four PDF acceptance contracts, SMOKE 33 to 35. **Box left OPEN, two `needs-human` criteria**                                      | `718234b`              | `5f88172` |
| S10    | Prose scrub, 61 em-dashes rewritten, seven pins moved at identical strictness                                                                                                             | `73ae76b`              | `ca18ce3` |
| S11    | Wrap-up: SMOKE final pass, CHANGELOG `[3.6.0]`, BUILD_REPORT sync, this snapshot, `context/dave.md`. **Box left OPEN, one `needs-human` criterion**                                       | this commit            | —         |

Two mid-batch verification and security checkpoints ran at `9c49382` (after four
sprints) and `f58332b` (after eight). Both passed. Neither fixed or committed
anything itself; both produced findings, which are in the deferred list below.

One migration this batch: **0034** (`zt_assessment.roadmap_summary`,
`executive_summary`, `pillar_narratives`, all nullable, `batch_alter_table`,
`JSON().with_variant(JSONB, "postgresql")`, additive and SQLite-safe, C0). New
DECISIONS: **D-035** (the ATT&CK deliverable labels citations, never causes or
remedies, `DECISIONS.md:880`), **D-036** (one shared export style module, page
geometry stays per-exporter, `:938`), **D-037** (AI transparency is
consultant-facing, the client screen stays silent, `:985`).

## Machine-local facts (this box)

- **Web runs on port 3001**, not 3000: root `.env` `WEB_PORT=3001` /
  `NEXTAUTH_URL=:3001` (a separate next-dev holds `:3000`). Playwright resolves
  the port via `e2e/helpers/baseUrl.ts`. Never hardcode `:3000` in a new spec.
  Canonical/CI stays `:3000`.
- **gh CLI has two accounts:** active `SpearheadAnalytica` (full write) and
  `david-catarious_kentro` (Kentro EMU, reads only). `gh auth switch --user <name>`
  to flip; `git push` authenticates as SpearheadAnalytica via GCM regardless.
  `.claude/setup.sh` re-checks the active account at every SessionStart and
  switches back if the expected one is already authenticated, so a stale account
  self-heals instead of halting the loop at its first push.
- **Tooling not on default PATH:** `node.exe` and `gh.exe` live under
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages`; the host binary this batch ran e2e
  with is `node-v24.18.0-win-x64`, which is the host only and not container parity.
  Run e2e via that `node.exe` plus `e2e/node_modules/@playwright/test/cli.js`.
  Docker CLI may need `export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"`
  per shell.
- **Seven gate steps, one runner.** `bash .claude/hooks/run-gate.sh push` reads
  `.claude/profile` (`shield`) and sources `.claude/profiles/shield.sh`, which is
  the single place the commands are written down. Green prints
  `gate: shield/push passed (7 steps)`; a smaller step count means the gate is
  broken, never that it passed. Bandit stays CI-only, and a ruff `# noqa` does not
  suppress it (a flagged string needs its own `# nosec`).
- **The LLM stayed in fixture mode for the entire batch.** Root `.env` is
  `SHIELD_LLM_MODE=fixture`, compose defaults to `fixture`, and `.env` is
  gitignored. No live-AI or cloud credential was needed by any sprint. Live
  Vertex needs `SHIELD_LLM_MODE=live`, `SHIELD_LLM_PROVIDER=vertex`,
  `SHIELD_LLM_MODEL=gemini-2.5-flash`, `GCP_PROJECT_ID=kentro-cloudmod-dev`,
  `GCP_REGION=us-central1`, and host gcloud ADC bind-mounted read-only, all in
  the gitignored `.env` and reverted after validation. There is NO static Google
  API key anywhere.
- **Framework/module reinstall dance:** after editing any `apps/web` source,
  `docker compose up -d --force-recreate web` before any e2e (next-dev
  hot-reload does not fire through the Windows bind mount). A NEW python module
  under `app/` needs `docker compose restart api`; S1 added `app/export_style.py`
  and needed exactly that. NEVER restart api while an in-container pytest is
  running (SIGKILL 137). Migration 0034 applies in-container with
  `alembic upgrade head`; `alembic current` reports `0034 (head)`.
- **Hybrid OIDC flag is default OFF and must never be committed on** (D-032).
  The `s26-oidc-login` opt-in spec runs with `E2E_OIDC=1`; always restore the flag
  off afterward and re-prove one credentials sign-in.
- **`demo-reset --demo` is destructive and opt-in** (D-033). Never run it
  implicitly. It is currently the only way to get S5's evidence-rich seed into
  this box's database (see the deferred list).

## Deferred / needs a human

Nothing in this list is a regression introduced by this batch unless it says so.
It is recorded here so none of it gets rediscovered as a bug in three months.
Roughly in priority order.

1. **A swallowed error on the client's only write path.**
   `CsfSelfAssessment.tsx:172-174` is a bare `catch {}` around the answer PATCH, a
   direct violation of `CLAUDE.md` principle 2, and it predates this batch. Its
   comment reads "Best-effort optimistic save; a reload reconciles if it failed",
   which is the part to distrust: nothing forces the client to reload, and if they do
   not, the lost answer is indistinguishable from an unanswered one. The consequence compounds with what
   this batch built: a client picks a tier, the optimistic UI shows it saved, the
   PATCH fails silently, the answer is lost, and the deliverable then reports
   honestly (thanks to S3) that the subcategory is unscored and carries no
   finding. The newly truthful reporting faithfully describes a gap that a silent
   save failure created. The client answered and the report says they did not.
   Fixing it means deciding what a client sees on failure, which is a product
   decision, not an agent's. **Highest-value item in this list.**
2. **The interview prompt has no data path in any environment.** The `questions`
   table is empty, `seed_demo.py` never populates it, and the loader
   `scripts/load_csf_tier_questionnaires.py` is invoked by nothing: not CI, not
   compose, not `demo-reset`. Only a docstring and a SMOKE line mention it. So
   `questionsByCode` is always `{}` and the `Consider:` eyebrow never renders.
   **S6 was credited for this feature on a mocked vitest**, whose criterion asked
   for "a vitest case asserting the client label" and got one, with the fetch
   mocked. The test is honest; the criterion asked for the wrong proof. This is
   the Sprint-8 lesson recurring with a different cause. Running reference data
   into the shared demo database is a human decision. SMOKE §34 carries the
   unchecked box.
3. **No green full-suite e2e run exists on this box, after four attempts.**
   Checkpoint 1 (2 failed / 49 passed), checkpoint 2 (1 failed / 50 passed), the S9
   driver's warmed and uncontended run (2 failed / 56 passed / 6 skipped in 34.6m),
   and S11's own warmed quiet-box run: **1 failed / 57 passed / 6 skipped in 33.2m**,
   failing at `s4-techdebt.spec.ts:40` inside `signIn` at `auth.ts:63`, the test's
   first action, before any content assertion. That test passes standalone. **This is
   not a timeout bump:** `e2e/helpers/auth.ts:60-63` already wraps a 15s
   `waitForURL` in `toPass({ timeout: 60000 })` and still loses, because the
   post-login chain pays three sequential cold compiles and each retry can re-enter
   them. Measured directly in S11: after 33 minutes of continuous browser work the
   four warmed routes had gone cold again (`/` back to 6.3s from 0.5s), so next-dev
   evicts compiled routes under sustained load and the back half of the suite pays
   cold-compile costs the front half already paid. Warming belongs in the harness.
   **A second, weaker observation worth keeping:** the standalone arbitration passed
   `:40` and failed `:154`, which had passed in the full run, on a 120s
   `waitForResponse` for the extract POST with an existing `Draft v37` on the page
   and an error banner showing. The failure moving between runs is the
   non-deterministic signature rather than a selector or logic break, but `:154` may
   also carry an order-coupling to the draft `:40` leaves behind. One observation is
   not a diagnosis; it was deliberately not chased, since re-running a suite hoping
   for green is what the protocol forbids. Real test-infra work, small but not
   trivial. The loop protocol names CI's fresh-runner E2E job as authoritative, and
   that is the honest arbiter.
4. **Absent versus zero at the summary-header layer, in three of four services.**
   One root cause, found by three independent empty-input runs. Tech-debt prints
   `Total annual cost: $0` for rows whose cost is unrecorded, asserting zero where
   the truth is "not recorded". CSF headlines `Overall maturity: Repeatable` at
   2.8% coverage with no qualifier. ZT does qualify, since S4: unscored
   capabilities are excluded from every average, "so no stage here describes
   them". The fix pattern therefore already exists one service over, which makes
   this copying an established pattern rather than making a new decision. Wants
   one consistent treatment across all four, not three separate nits.
5. **A second phantom Tailwind token.** `border-border-default` emits nothing: the
   preset declares `border: { subtle, DEFAULT, strong, focus }` and Tailwind
   flattens `DEFAULT` to the bare name. Proven against the served stylesheet
   rather than by reasoning, 0 occurrences against 1 for `border-border-subtle`.
   Seven uses across five files: `AiPreviewButton.tsx`, `csf/CsfPlaybookPanel.tsx`,
   `DiscardDraftButton.tsx`, `risk/RiskRegisterDashboard.tsx`,
   `messages/MessageThread.tsx`. **S0 existed to sweep this exact class of defect
   and swept only `surface-muted`**, the one instance the design sprint had
   grepped for, so a second phantom survived it. The general fix is a check that
   every color utility resolves to a class Tailwind actually generates, not
   another one-off grep.
6. **CI's bandit never scans `apps/api/scripts`.** `.github/workflows/ci.yml:48`
   targets `apps/api/app` only, so the whole `scripts/` tree is invisible to it.
   Scanning it anyway finds 7 LOW including `B105` on the documented demo password
   at `seed_demo.py:129`, harmless and pre-existing. The credential is not the
   finding; the blind spot is, because a future script could carry a real secret
   unscanned.
7. **Dependency posture, corrected.** This file previously recorded one HIGH plus
   one moderate. Root `pnpm audit`, measured at both checkpoints, is **5 high + 2
   moderate**: `sharp@0.34.5` (1 high, libvips CVEs, transitive via next@15's
   image optimizer, not exploitable in our use since we process no untrusted
   images), `postcss@8.4.31` (**4 advisories, 2 of them high**, not the one
   moderate previously recorded), and `brace-expansion@1.1.16` (**2 high,
   previously undocumented anywhere**, transitive via `minimatch@3.1.5`). None is
   branch-introduced: this batch touches no lockfile or manifest, so `main` audits
   identically. `npm audit` in `e2e/` is clean. All three want the same
   unscheduled lockfile bump, a Dependabot run or a root pnpm override on `main`.
   SMOKE §28's stale line was corrected in this sprint.
8. **Unvalidated `evidence_artifact_id` write at three sites**, not the two
   previously recorded: `attack.py:401`, `csf.py:528`, `zt.py:786`. A nonexistent
   UUID raises IntegrityError while a foreign-tenant UUID commits, which is a
   boolean existence oracle at PATCH. Admin-gated and dating to `fb9c99d`, so a
   data-integrity gap rather than privilege escalation, since platform admins hold
   cross-tenant reach by design. What stops it leaking into a deliverable is the
   read join, which filters `Artifact.client_id == client_id` in SQL at all three
   services (`attack.py:919`, `csf.py:1782`, `zt.py:1305`) and raises on an
   unresolved id rather than degrading into `No evidence attached`.
9. **XLSX formula injection**, pre-existing across all six exporters. openpyxl
   types a leading `=` as a formula, and free-form Notes and Rationale cells
   already carry user text. S2 and S3 add one more user-controlled column to a
   vector that already existed. A real fix spans six modules and is not a
   one-pass TDD change.
10. **The demo database still carries pre-S5 ATT&CK evidence.** `seed_demo.py`
    returns early whenever any `Service` row exists and prints
    `Services already present; skipping seeding.`, so S5's richer evidence is in
    code only. The S9 run's census read `attack_prevention_cited=0` against a code
    path that now cites prevention tools. Only `demo-reset --demo` or a wipe picks
    it up, and that path is destructive and opt-in per D-033. SMOKE §26 carries the
    unchecked box, and it is unchecked for this reason as well as for having no
    spec.
11. **Zero Trust clients get no guidance.** `ZtSelfAssessment.tsx` mounts
    `ZtStagePicker` directly rather than `ZtQuestionnaire`, and that file was
    absent from S6's scope list. CSF's questionnaire is shared, so one disclosure
    serves both audiences; ZT's is not. All seven stages of guidance data exist and
    are tested, but nothing client-side consumes them. Closing it is an import plus
    one element beside the picker. SMOKE §34 carries the unchecked box. The other
    half of that box closed in S10: the stale `ZtSelfAssessment.tsx:371` Notes
    placeholder, which S6's commit message claimed to have updated and had not, is
    now byte-identical to the other three questionnaires.
12. **The risk provenance badge cannot discriminate.** `routes/risk.py:270` is the
    only writer of `RiskEntry.origin` and always passes `"ai_generated"`, the model
    default is the same string, and `consultant_entered` appears nowhere in app
    code. So every register row badges. Honest, since every row really is
    AI-drafted, but a constant rather than a distinction until a consultant-entered
    write path exists, which the plan places in the next batch. The spec asserts
    presence only, deliberately.
13. **`/admin/management` is named in S7's Scope line with no acceptance criterion
    and no evidence clause anywhere.** A plan defect, not a code one. The runner
    left it untouched rather than inventing work, which was correct. Either it needs
    a criterion in a later sprint or that scope line is stale from an earlier draft.
14. **The ATT&CK PDF and DOCX still head the gap list `Top remediation gaps (N of M
    shown)`** (`attack/exporters.py:435` and `:540`). It predates the batch (Work
    Order C4) and is a heading rather than a Gap Direction cell, so it sat outside
    S2's criteria, but it frames gaps as remediation targets immediately above cells
    D-035 forbids from doing so. The empty-input render showed it reading
    `Top remediation gaps (0 of 0 shown)` on a report that scored nothing. Recorded
    in D-035; S10's scrub did not take it because it is a claim change, not a prose
    one.
15. **The client-PDF-versus-client-screen AI asymmetry.** S2 put an AI-drafting
    disclosure in the client's deliverable; S8 keeps the client's screen silent.
    D-037 records it as an open boundary rather than resolving it, on the reasoning
    that an unrecorded inconsistency is the one silently "fixed" by whoever notices
    it first.
16. **Two gate gaps.** `.css` is outside the prettier glob in both
    `.claude/profiles/shield.sh` and CI, so `tokens.css` formatting is unenforced by
    any gate. And `packages/design-system/src/tailwind-preset.ts` cannot be
    typechecked outside `apps/web`, because `tailwindcss` resolves only there;
    fixing it needs a devDependency, so a lockfile change.
17. **The CSF stepper is 5 steps, not 10.** "10-step Playbook" survives only as
    intake marketing prose. The engine and the workspace both model five.
18. **SMOKE §14 / §14.1 live-AI boxes** stay opt-in and self-skip keyless. They
    were run for real against Vertex via ADC across all five purposes on
    2026-07-15 (Sprint 7 T1). Re-verify with a keyed or ADC run.
19. **CI `demo` and `e2e` job green runs** are cited on the sprint PR open, because
    this repo's CI triggers only on push or PR to `main`. SMOKE §27's CI-job box
    carries its first green run (PR #44, run 29939798138).
20. **ESLint 10** stays deferred upstream (D-018 dated deferral): no published Next
    lint stack runs on it today.
21. **Needs David (cloud infra + full federation):** `infra/terraform`
    (cloud/account/region/network) and DR runbooks are stubs; the FedRAMP-authorized
    LLM connector is unbuilt; `azure_openai`/`bedrock`/`local` LLM adapters stay
    loud not-implemented. Keycloak SSO stays at hybrid depth (D-032): full token
    federation (the backend accepting Keycloak tokens as API bearers), JIT
    provisioning, migrating register/MFA/email flows into Keycloak, and an
    un-discard endpoint (DISCARDED is terminal in v1; rows stay DB-recoverable) all
    stay out of scope. Dave's 2026-07-13 call: local containers for now.

## Test coverage status

- Backend: full `pytest -m unit` green in-container. This batch added
  `test_export_style.py` (S1: the `graded_hex` raise on both out-of-range ends,
  `escaped_title` escaping without org-name repetition, per-exporter margin parity
  contracts), `test_attack_evidence_join.py` (S2), and substantial additions to
  `test_attack_exporters.py`, `test_csf_exporters.py`, `test_csf_deliverable_routes.py`,
  `test_zt_exporters.py`, `test_zt_routes.py`, `test_zt_run_ai.py` (S4's race case
  injects a discard strictly between the status check and the durable write, and
  carries `assert fired, "the seam moved out of the window"` so it cannot silently
  stop biting), `test_ai_runtime_fixtures.py` and `test_exporters.py` (S5), and
  `test_admin_routes.py` (S8). S9 added four PDF acceptance contracts, one per
  service, which assert section order as a **subsequence** over real extracted
  bytes: each string is searched for only after the previous match, so a section
  rendering in the wrong place fails where a set of `in` checks would pass.
  Verified to bite by reversing pairs of sections against real bytes.
- Web unit tests: `pnpm -F web test` (vitest) green in-container, grown from 47 to
  118 across 22 files over the batch (S0 +9, S6 +23, S7 +27, S8 +12). The guidance
  suite iterates the full 6x4 CSF set plus CISA 4 and DoD 3 rather than sampling,
  and asserts the lookups raise on a missing entry.
- Web `tsc --noEmit` clean; eslint 0 errors (1 pre-existing postcss warning).
- e2e: **28 spec files** (host, resolves `:3001`), 64 tests, of which 6 skip by
  design (4 `e2e/demo/*` need `SHIELD_DEMO_SMOKE=1`, 2 `s26-oidc-login` need
  `E2E_OIDC=1`), leaving 58 runnable. S9 added `s27-comprehension.spec.ts` (4
  tests) and extended s3/s4/s5/s6/s7. **S11's exit run: 1 failed / 57 passed / 6
  skipped in 33.2m**, warmed and uncontended, the single failure being a sign-in
  cold-compile timeout at `s4-techdebt.spec.ts:40` that passes standalone. **No green
  full-suite run exists on this box** after four attempts; see deferred item 3 for
  each attempt, the arbitration, the measured route-cache eviction, and why it is not
  a timeout bump. Per-spec standalone is the flake arbiter here: a spec that dies at
  `auth.ts` sign-in under load is a documented cold-compile flake, never a logic bug.
- Format: repo-wide prettier `--check` clean at 3.9.5. Python ruff/black clean
  (root-config parity). Note that `.css` is outside the prettier glob (deferred
  item 16).
- Audit: bandit CI-only, exit 0 over `apps/api/app`, which does not include
  `scripts/` (deferred item 6). Root `pnpm audit` is 5 high + 2 moderate, none
  branch-introduced (deferred item 7); `e2e/` npm audit clean. No secret or token
  committed this batch, and no live-LLM configuration reached a committed file.

## Lessons learned (Sprint 10)

- **Nine of eleven executed sprints had at least one defective acceptance
  criterion, and the defects had a shape.** One was structurally unrunnable (S6
  asked for a vitest pin against Python constants in a directory the web container
  does not mount). One was already satisfied before the work began (S1's
  `grep -c 'html.escape'` returned 0 on the pre-S1 tree too, because the hotfix had
  written `from html import escape` and called bare `escape(...)`). One named two
  surfaces and could only fail on one (S2 required the stat in PDF **and** DOCX but
  named only extracted PDF text as evidence). One could not fail by construction
  (S4's `tsc --noEmit` green after adding three *optional* interface fields).
  Several passed on a bare no-exception. S0's criterion listed the tier tokens in
  one order and their hexes starting from a different tier, so a positional reading
  would have inverted the whole ramp with every frozen-table test still passing.
  The transferable rule: **an evidence command that passes before the work begins
  certifies nothing.** Write the criterion so that it is red on the tree you are
  starting from, and check that it is, before trusting it. Every one of these was
  caught by a runner reading its own criterion sceptically and substituting a check
  that bites, then saying so.
- **A truthful report can faithfully describe a gap that a silent failure created.**
  S3 made the CSF deliverable honest about unscored subcategories. The client's
  answer PATCH swallows its error. Those two correct-looking behaviours compose
  into a report that tells a client they never answered a question they did answer.
  Honesty at the reporting layer is not a substitute for failing loudly at the
  write, and improving one can make the absence of the other harder to see.
- **An empty-input render is the cheapest way to find a false reassurance.** Three
  of the four services printed something untrue when given nothing to say: CSF
  advised maintaining current controls at 3 of 106 subcategories scored, ZT
  reported no gaps at target when nothing had been scored, and tech-debt asserted
  `$0` where the cost was unrecorded. Each passed every test it had, because every
  zero-gap case those tests exercised used a fully scored assessment. The branch
  was correct for the only input it was ever given. Render the report from nothing
  and read what it says.
- **A raising helper turns silently-bad data into a crash, which is the point.**
  S1 made `graded_hex` raise instead of clamp. S5 then found the seed could not run
  on an empty database at all, because the shared stage pattern handed DoD ZTRA a
  stage 4 on a 3-rung ladder. That bad data had been accepted silently for months
  and nobody had seen it, because the live demo database predates S1. FAIL LOUDLY
  earning its keep on a schedule of its own choosing.
- **A phantom utility class is invisible to every gate the repo has.** Tailwind
  emits nothing for a class naming a token that does not exist, and no build step
  complains. S0 swept `bg-surface-muted`; S8 found `border-border-default` doing
  the same thing seven more times, because the preset flattens `DEFAULT` to the
  bare name. Both were proven against the **served stylesheet** rather than by
  reading the config, which is the only check that distinguishes a class that
  exists from one that merely looks right. Grepping for the instance you already
  know about does not sweep a class of defect.
- **Disclosure is what makes a sprint checkable.** S7's runner reported that it had
  written one component before its test, so no red run was observed. The driver
  reverted that component and re-ran the suite (2 failed of 4), recording a
  recovered check rather than an observed red and deliberately not overstating it,
  since one of the two failures was a missing module export rather than behaviour.
  A runner that had quietly reordered its narrative would have produced an
  identical-looking green sprint. The same is true of S8 volunteering which of its
  reds were collection failures, and of S9 leaving its own box unchecked.
- **Grepping prose in this codebase needs a multiline search.** Nine protected
  honesty strings were checked with a single-line grep and four came back
  "missing". All nine were present: Python splits them across adjacent string
  literals, so `"...read as "` `"verified..."` never matches `read as verified` on
  one line. A false alarm was one trusted grep away, and the same trap catches
  anyone auditing the export prose.

## Lessons learned (Sprint 9)

- **Activating a state means auditing every reader, not just the writer.** Adding
  `DISCARDED` was the easy part. Codex's two blockers were both hidden consumers:
  the risk-register synthesis has its own `_latest()` that would have read a
  discarded highest-version assessment straight into the gate, and the intake
  engagement cards reported the raw latest version. A dormant status is only as safe
  as the query that forgot about it.
- **The version trap is a real IntegrityError, not a hypothetical.** The
  `_latest_*` helpers must skip `DISCARDED` while the mint's next-version
  computation must read `max(version)` unfiltered, so it does not reuse the
  discarded version's number and collide on the `(service_id, version)` unique
  constraint.
- **A mocked unit test cannot prove a flag-off no-op or a beta integration.** The
  only honest proof that flag-off changes nothing is a vitest trap that fails on an
  unexpected Keycloak fetch. Beta-sensitive seams need a real round trip before the
  full wiring, so the verdict lands early.
- **Fail loudly at the wait, not at the far-downstream death.** The demo-reset web
  poll printed its success banner even on a 120s timeout, so a stalled production
  build looked like a clean reset until Playwright died opaquely much later.
- **Changing a shared default in one task silently breaks another task's hardcoded
  fixture, and the final full-suite gate is where it surfaces.** T5 flipped the
  canonical Keycloak issuer; T4's test had baked in the pre-T5 value and leaned on
  the config default. The running system stayed correct throughout; only the unit
  fixture lagged.

## Lessons learned (Sprint 8)

- **A flow that unit tests call green can be broken for every real user.** MFA
  sign-in passed `pytest -m unit` and a Sprint-7 vitest, yet the TOTP field never
  appeared in a browser. `SignInForm` sent `totp: undefined`, next-auth serializes
  credentials through `URLSearchParams`, and `URLSearchParams` stringifies
  `undefined` to `"undefined"`, so the backend `!totp` guard saw a truthy value.
  The vitest could not catch it because it mocks `signIn()` and never runs the real
  serialization. **This lesson recurred in Sprint 10** as deferred item 2: the
  interview prompt is credited to a mocked vitest and cannot render for any real
  user.
- **Send the key only when you have a value.** A default of `undefined` is not the
  absence of a field once it crosses a string-serializing boundary.
- **Idempotency belongs before the expensive side effect, not at the write.**
  Guarding at the cheapest correct point is the difference between a fix and a
  half-fix.
- **On an overload-prone box, the per-spec standalone run is the flake arbiter.** A
  spec that dies at `auth.ts` sign-in under load is a documented load flake, never
  a logic bug; the authoritative full run is the quiet-box shutdown checkpoint,
  and failing that, CI's fresh runner.
</content>
