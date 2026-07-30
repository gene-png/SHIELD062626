# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-30 (ops-pipeline reconciliation: #49, #50, #51 all
merged; PR #52 landed the shared pipeline and broke the loop launch; this
session fixes that)._

## Branch / in flight

- **`chore/reconcile-ops-pipeline` (this branch):** makes PR #52's shared ops
  pipeline actually work in SHIELD. #52 merged a generic multi-repo pipeline
  that left the loop unlaunchable in four ways, all fixed here: the duplicate
  `loop-sprint-cron` command shadowed the new skill so neither resolved;
  `.claude/sprint-plan` pointed at the Sprint-5-era `DELIVERY_PLAN.md`;
  `.claude/profile` named `node-pnpm`, whose gate refuses every commit because
  pnpm is not installed on this box and which declares no Python steps at all;
  and the identity hook blocked every `git push` and `gh` call. New
  `docs/SPRINTS.md` carries Sprint 10 as an S1 to S11 backlog in the format the
  skill requires. New `.claude/profiles/shield.sh` runs the real containerized
  gates.
- **Three hook bugs found and fixed while verifying, each with a regression
  test** (suite is 33 green): `run-gate.sh` fed its step list on stdin, so
  `docker compose exec -T` ate the remaining steps and the five-step gate
  reported "passed (1 steps)"; `no-bulk-stage.sh` matched `git add .` as a
  substring, so every dotfile path read as a bulk stage; `identity.sh` blocked
  `gh auth switch`, the command its own refusal message tells you to run.

## Merged since the last update

- **#49** auth refresh reuse storm (migration 0033, D-034), **#50** export
  header mangling, **#51** the Sprint 10 plan, **#52** the ops pipeline, plus
  dependabot #45, #46, #48. Main CI green at `f9e40aa` across all five jobs.

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

## Next steps

1. Merge the ops-pipeline reconciliation PR once CI is green.
2. Launch Sprint 10 myself (agents never launch it): confirm
   `bash .claude/hooks/run-gate.sh commit` is green with the stack up, cut
   `feat/defensible-reports-sprint-10` from `main`, then
   `/loop-sprint-cron start --account SpearheadAnalytica`. The backlog is
   `docs/SPRINTS.md`; `SPRINT_10.md` holds the rationale.
3. After Sprint 10 merges: Sprint 11 planning PR (design already drafted).
4. **`sharp <0.35.0` HIGH advisory follow-up on `main`:** Dependabot bump or a
   root pnpm override. The `postcss` moderate rides along.
5. Flip live Vertex on this box for real Run-AI output while evaluating.

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
