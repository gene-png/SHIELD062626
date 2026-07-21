# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-21 (Sprint 8 merged as PR #42; Sprint 9 planned, loop
not yet launched)._

## Branch / in flight

- **Sprint 8 "prove it in the browser" is MERGED** (PR #42, `1b26e2e`,
  `v3.4.1`). The headline was the out-of-plan MFA sign-in fix (`f10b803` —
  `totp: undefined` coerced to `"undefined"` by `URLSearchParams`, defeating
  the backend `!totp` guard; only the real browser spec caught it).
- **Sprint 9 "activate the seam" is PLANNED** on the planning branch this file
  rides in: `SPRINT_9.md` + staged `.claude/sprint-queue.sprint-9.json`,
  branch-to-be `feat/sso-discard-demo-sprint-9`, target `v3.5.0`. Three
  themes, 11 tasks: hybrid Keycloak OIDC exchange flag-gated default OFF
  (T4–T7; D-032; migration 0032 `users.keycloak_sub`), discard-draft
  affordance across all four services (T0–T3; D-031), demo/export automation
  (T2, T8–T9; D-033; pypdf test dep; every-PR CI demo job).
- **Codex read-only review done** (v0.144.5, 2026-07-21, initial verdict
  "rework", 12 findings, 2 blockers). ALL 12 folded into the plan — the
  blockers were real: risk.py's own `_latest()` would have read discarded
  assessments into the risk-register gate, and discard needed a
  conditional-UPDATE concurrency contract, not just state checks. Findings
  table in the planning PR body.

## Decisions made / carried (recorded for agents)

- **Sprint 9 scoping calls (mine, 2026-07-21):** hybrid OIDC depth (NOT full
  federation — MFA/email flows stay local; Keycloak tokens never accepted as
  API bearers); discard on all four services, client-touched CSF/ZT drafts
  discardable with a warning dialog; pypdf added for PDF content assertions;
  CI demo job on every PR; the T6 confidential-client fallback is
  PRE-APPROVED (dev-realm secret) so the loop doesn't halt on the next-auth
  beta.
- **Agents never launch the sprint loop.** I start `/loop-sprint-cron` myself
  after walking the SPRINT_9.md launch checklist.
- **Keycloak SSO deferral is LIFTED at hybrid depth** (supersedes my
  2026-07-16 "stays deferred" call). Full federation / JIT provisioning stays
  out of scope.
- **Infra: local containers still** (2026-07-13 call unchanged); `.env` stays
  fixture-mode; no live-AI or cloud credentials needed for Sprint 9.

## Next steps

1. Merge the Sprint 9 planning PR.
2. Walk the SPRINT_9.md launch checklist: cut
   `feat/sso-discard-demo-sprint-9` from `main`, copy the staged queue to
   `.claude/sprint-queue.json`, set `working_dir`/`expected_gh_user` for this
   box, then launch `/loop-sprint-cron` myself.
3. Watch T6 (web OIDC, the sprint's highest-risk task) — the secret-less PKCE
   client on next-auth 5.0.0-beta.31 is the beta-sensitive seam; the fallback
   is pre-approved if it fights.

## Notes for Gene

- Sprint 9 is planned but NOT launched — nothing is in flight on a feature
  branch yet. The plan of record is `SPRINT_9.md` + the staged queue.
- The OIDC work is deliberately hybrid: Keycloak authenticates, the backend
  keeps minting its own HS256 JWTs through a new `POST /auth/oidc/exchange`
  (RS256/JWKS validation, no JIT provisioning, TOFU `keycloak_sub` binding).
  Every existing auth surface is untouched with the flag off.
- T0 deliberately touches `risk.py` and `intake.py` beside the four service
  route files — Codex caught that both have their own "latest assessment"
  queries that must skip the new DISCARDED status; flagged here so the wider
  diff doesn't read as scope creep.
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject; do not remove.
