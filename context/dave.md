# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-24 (product-walkthrough burn-down session: two hotfix
PRs open, Sprint 10 planning PR in flight, Sprint 11 designed)._

## Branch / in flight

- **PR #49 `fix/auth-refresh-reuse-storm` (open):** kills the ~15-minute
  forced sign-out ("Intake proxy 401") found in the 2026-07-23 walkthrough.
  Web chain-cache single-flight refresh (`apps/web/src/lib/auth/refresh.ts`),
  backend anchored one-step reuse grace (migration 0033, D-034), typed
  `refresh_expired` idle expiry. Proven with a 3-phase shortened-TTL browser
  run (7 min continuous use across ~7 token boundaries, web-restart survival,
  clean idle redirect) plus a live grace demo; all six gates green.
- **PR #50 `fix/export-pdf-headers` (open):** the `ATT&CK;` header mangling
  (unescaped `&` into reportlab) and the duplicated org name (H1 was the
  org-prefixed `Service.title`) fixed across all five exporters; export routes
  now pass `service_display_label(kind)`; sign-out button looks like a button.
  Rides a test-only fix for a latent race in `s7-csf-playbook` (pre-seed
  response capture) that started failing deterministically on this box.
- **`docs/sprint-10-plan` (this branch):** Sprint 10 planning PR — SPRINT_10.md
  + staged queue, Codex read-only review per convention.

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

1. Merge PR #49 and PR #50 once CI is green (fresh-runner e2e + demo jobs are
   the authoritative suite runs — this box's back-to-back e2e was flaking on
   the documented sign-in/cold-compile pattern by end of session).
2. Merge the Sprint 10 planning PR, then stage the queue and launch
   `/loop-sprint-cron` myself (agents never launch it).
3. After Sprint 10 merges: Sprint 11 planning PR (design already drafted).
4. **`sharp <0.35.0` HIGH advisory follow-up on `main`:** Dependabot bump or a
   root pnpm override. The `postcss` moderate rides along.
5. Flip live Vertex on this box for real Run-AI output while evaluating.

## Notes for Gene

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
