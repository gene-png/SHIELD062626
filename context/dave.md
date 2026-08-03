# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-30 (ops pipeline fixed and merged as #53; design sprint
produced three candidate visual systems; Sprint 10 is staged and launchable)._

## Branch / in flight

- **`docs/design-systems-and-remediation` (this branch):** the design sprint
  output plus the plan for four defects it uncovered. Adds
  `docs/design-systems.md` (three complete visual systems, full light and dark
  token sets, 234 contrast pairings verified) and
  `docs/design-systems-contrast.mjs` (re-run with `node`, exits non-zero on
  failure). Adds **S0** to `docs/SPRINTS.md` and one criterion to **S1**.
  No product code changed.
- **Nothing else in flight.** Main is green at `9c16a3f`.

## Merged this session

- **#53** ops-pipeline reconciliation. PR #52 had installed the shared pipeline
  wired for a generic repo, which left the loop unlaunchable four ways: the
  duplicate `loop-sprint-cron` command shadowed the new skill so neither
  resolved; `.claude/sprint-plan` pointed at the Sprint-5-era
  `DELIVERY_PLAN.md`; `.claude/profile` named `node-pnpm`, whose gate refuses
  every commit because pnpm is not installed on this box and which declares no
  Python steps at all; and the identity hook blocked every `git push` and `gh`
  call. Also fixed three bugs in the hooks themselves, each with a regression
  test (suite 26 to 33 green): `run-gate.sh` fed its step list on stdin so
  `docker compose exec -T` ate the rest and a five-step gate reported "passed
  (1 steps)"; `no-bulk-stage.sh` matched `git add .` as a substring so every
  dotfile path read as a bulk stage; `identity.sh` blocked `gh auth switch`,
  the command its own refusal prints as the fix.
- Earlier: **#49** auth refresh reuse storm (migration 0033, D-034), **#50**
  export header mangling, **#51** the Sprint 10 plan, **#52** the ops pipeline,
  dependabot **#45**, **#46**, **#48**.

## The four defects the design sprint found, and where each lands

All four verified against the code, not taken on the agent's word.

| Defect | Home | Why there |
|---|---|---|
| `bg-surface-muted` is a silent no-op, 8 places across 6 files | **S0** | Trivial, and it touches files S7/S8 also touch, so it runs first |
| `lib/risk/matrix.ts` hard-codes tier hexes inline; `border-white` cell gaps | **S0** | Prerequisite for any dark mode. Values stay identical, so it is provably colorless |
| `risk/exporters.py:123` duplicates `--surface-sunken` as `FFEEF2F7` | **S1** | S1 already exists to be the single home for deliverable styling |
| Inter has never loaded (no `next/font`, no `@font-face`) | **The visual-system batch** | That batch self-hosts faces anyway; fixing it alone changes every screen for no gain |

## Next steps

1. **Merge this docs PR.**
2. **Launch Sprint 10** (agents never do this): confirm
   `bash .claude/hooks/run-gate.sh commit` is green with the stack up, cut
   `feat/defensible-reports-sprint-10` from `main`, then
   `/loop-sprint-cron start --account SpearheadAnalytica`. Backlog is
   `docs/SPRINTS.md` (now S0 through S11); rationale is `SPRINT_10.md`.
3. **Pick a visual system** from `docs/design-systems.md`. Recommendation is
   Ledger, because the artifact a skeptical client challenges is a printed
   document and Ledger is the only one where screen and report share a
   typographic voice. The pick takes a D-number and updates that file's status
   line. Not urgent, but it gates step 5.
4. **Sprint 11 "Evidence and access"** planning PR, with **dark mode pulled
   out** of it.
5. **The visual-system batch**: adopt the chosen system, self-host faces (fixes
   Inter), define dark mode, dual-mode axe sweep, mirror the ramps into the
   exporters.

## Before the loop runs, two things to settle

- **The gh account reverts on its own.** It was switched to `SpearheadAnalytica`
  twice this session and both times came back as `david-catarious_kentro`, with
  no `GH_TOKEN` in the environment. `identity.sh` refuses every push and `gh`
  call under the wrong account, so if it flips mid-sprint the loop halts at its
  first push. Worth finding the culprit (VS Code's GitHub auth provider is the
  likely suspect) before a long unattended run.
- **`.env` is now `SHIELD_LLM_MODE=fixture`.** It was live-Vertex, which failed
  two pytest cases; both pass in fixture, and fixture is what the sprint and e2e
  require. Set it back to `live` plus
  `docker compose up -d --force-recreate api` when evaluating real Run-AI output.

## Decisions made / carried (recorded for agents)

- **The 2026-07-23 walkthrough set the roadmap:** hotfixes now, Sprint 10
  "Reports you can defend" (render the evidence the AI already produces, CSF
  POA&M into the released deliverable, ZT roadmap + persisted narratives,
  shared export styling + heatmaps, per-question tier guidance, workspace
  steppers, honest AI-status copy), Sprint 11 "Evidence and access"
  (substantiation model tool-present/configured/validated, per-claim evidence
  attach + post-intake upload, dark mode, client inbox, client risk-register
  release, client self-start for tech-debt/ATT&CK). Sprint 11's full design is
  drafted and re-anchors against post-Sprint-10 main at its own planning PR.
- **Numbering ledger:** hotfix took migration 0033 + D-034; Sprint 10 takes
  0034 + D-035/036/037, SMOKE §33–§35, spec s27; Sprint 11 takes 0035/0036 +
  D-038…D-042, SMOKE §36–§40, specs s28/s29.
- **Dave's box goes live-Vertex after the hotfixes merge** (env-only, D-029
  path, gitignored `.env`; fixture stays the committed default and e2e always
  runs fixture).
- **Keycloak SSO stays at hybrid depth** (D-032); infra stays local containers.

## Carried, not scheduled

- **`sharp <0.35.0` HIGH advisory on `main`:** Dependabot bump or a root pnpm
  override. The `postcss` moderate rides along.
- Dependabot **#47** (npm-minor-patch, 6 updates) is still open and green.

## Notes for Gene

- **The `.claude/` hooks are committed, so they apply to you too.** Before your
  first push here: `git config --local user.email` must be
  `davidcatarious@spearheadanalytica.com` and the active gh account must be
  `SpearheadAnalytica`, or `identity.sh` refuses every `git push` and every `gh`
  call. That mapping is Dave's account boundary and it currently has no entry for
  a second developer; if you need to push under your own identity, say so and the
  `case` block in `.claude/hooks/identity.sh` gets a `gene-png` mapping.
- Gate commands now live in one place, `.claude/profiles/shield.sh`, run via
  `bash .claude/hooks/run-gate.sh commit|push`. They need Docker Desktop running
  and the stack up, because everything except prettier runs in the containers.
- The 2026-07-23 product walkthrough (Dave, both roles, all four reports) is
  the source of the current roadmap; the triaged 25-item feedback inventory
  lives in the Sprint 10 planning PR body.
- PR #49 changes refresh-token semantics (anchored one-step reuse grace,
  default 900s, `JWT_REFRESH_REUSE_GRACE_SECONDS=0` restores strict rotation)
  — trade-off stated in D-034.
- `demo-reset --demo` is destructive; never run it implicitly. Opt-in specs
  unchanged (`s26` on `E2E_OIDC`, `demo/` on `SHIELD_DEMO_SMOKE`).
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject; do not remove.
