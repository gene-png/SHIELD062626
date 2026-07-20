# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-16 (Sprint 8 planning merged #37; handoff docs for the
new dev)_

## Branch / in flight

- **Sprint 7 MERGED** to `main` as PR #36 (`v3.4.0`, squash `4796429`) —
  Vertex via ADC (D-029), release notification (D-030), MailHog delivery
  default-on, reqSeq sweep done, Auth.js v5. Done and closed.
- **Sprint 8 "prove it in the browser" PLANNED & MERGED** (PR #37, squash
  `59699ed`): `SPRINT_8.md` + staged queue
  `.claude/sprint-queue.sprint-8.json`, target `v3.4.1`. Eight tasks (T0–T7):
  shared MailHog helper, tech-debt extract draft-guard (the last mint-route
  debt), s22 release-notify e2e (§29), s23 verify/forgot/reset pages e2e,
  s24 MFA e2e split into TOTP (T4) + recovery-code (T5) parts, s25
  admin-health + `/documents` empty state, wrap-up.
- **A NEW DEV will launch the Sprint 8 loop** (not me): `ONBOARDING.md` §5 now
  stages Sprint 8 and carries the human-launches-the-loop rule; this handoff
  PR is the last docs step before they take it.
- **Plan was reviewed by OpenAI Codex** (CLI v0.144.5, read-only,
  2026-07-16): verdict "ship-with-changes"; its two blockers (T1 guard
  placement before the LLM call; explicit re-contract of
  `test_extract_versions_subsequent_lists`) and the rest of its findings are
  folded into `SPRINT_8.md`. Codex CLI is installed + authenticated on this
  box for future plan reviews.

## Decisions made / carried (recorded for agents)

- **Agents never launch the sprint loop.** The human dev at the keyboard
  starts `/loop-sprint-cron` — for Sprint 8 that's the incoming new dev (now
  a CLAUDE.md rule of the road).
- **Corrected a stale note:** attack/zt mint routes were ALREADY fixed in
  Sprint 3 T1 (`attack.py:258-273`, `zt.py:539-554`) — only tech-debt still
  had the unbounded-version pattern; Sprint 8 T1 pays it.
- **Keycloak SSO / OIDC cutover excluded** from Sprint 8 (my call,
  2026-07-16); stays on the deferred list.
- **Infra: local containers for now** (2026-07-13 call unchanged); GCP live
  path validated 2026-07-15, `.env` back to fixture.
- Sprint 8 retires my manual MFA walkthrough (T4/T5 drive the UI for real) —
  I no longer owe that hand-check once the sprint lands.

## Next steps

1. Hand the new dev the repo + `ONBOARDING.md` (zero → loop launch is §1–§5;
   Sprint 8 is the staged sprint). They run the launch checklist on THEIR box:
   archive any old runtime queue, copy `.claude/sprint-queue.sprint-8.json` →
   `.claude/sprint-queue.json`, set `working_dir`/`expected_gh_user`,
   `git checkout -b feat/browser-proof-sprint-8 main`, then
   `/loop-sprint-cron`.
2. Stay reachable for loop babysitting questions (monitor-stall nudge,
   cold-compile flake) while the new dev's first fires run.
3. After Sprint 8: candidates are Keycloak SSO cutover, tech-debt
   replace-draft affordance, demo-reset automation decision.

## Notes for Gene

- Sprint 8 is planned and staged (`SPRINT_8.md` + queue) — all e2e/spec work
  plus one api idempotency fix; no migrations, no dep changes except a TOTP
  lib inside `e2e/` (host-run harness).
- Sprint 8 T1 deliberately re-contracts
  `test_extract_versions_subsequent_lists` (tech-debt extract becomes
  idempotent-200 on an open draft, like CSF/attack/zt) — flagged here so the
  test change doesn't read as weakening.
- We now run OpenAI Codex as a read-only plan reviewer before sprint PRs
  (`npm i -g @openai/codex`, `codex login`, `codex exec --sandbox read-only`).
  Its review is summarized in the Sprint 8 planning PR body.
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject — don't remove.
