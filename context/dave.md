# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-21 (Sprint 8 complete on `feat/browser-proof-sprint-8`; PR
not yet opened)._

## Branch / in flight

- **Sprint 8 "prove it in the browser" is DONE on `feat/browser-proof-sprint-8`**
  (target `v3.4.1`). Eight tasks (T0 through T7): shared MailHog helper (T0), the
  tech-debt extract draft-guard (T1, the last mint-route debt), s22 release-notify
  e2e (§29), s23 verify/forgot/reset pages e2e, s24 MFA e2e split into TOTP (T4)
  and recovery-code (T5), s25 admin-health + `/documents` empty state (T6), and
  this wrap-up (T7). All committed; gates green per task.
- **I launched this sprint myself.** The ONBOARDING "hand it to a new dev"
  handoff did not happen: I ran `/loop-sprint-cron` on my own box and babysat the
  fires. The human-launches-the-loop rule held (an agent never started it), but
  the launching human was me, not an incoming dev.
- **The headline was an out-of-plan product bug.** MFA sign-in never revealed the
  TOTP field in the browser: `SignInForm` sent `totp: undefined`, next-auth
  serialized it through `URLSearchParams` into the string `"undefined"`, and the
  backend `!totp` guard treated that as a real (bogus) code, so the second step
  never appeared. The T4 browser spec caught it; the Sprint-7 vitest had missed it
  because it mocks `signIn()`. Fixed in `f10b803` (send `totp` only when present)
  with a vitest regression guard. This was a launch-blocker for MFA (D-027).
- **NEXT: open the Sprint 8 PR** off `feat/browser-proof-sprint-8` into `main`.
  The branch is complete; the authoritative full-suite e2e + security audit at the
  shutdown checkpoint is the last gate before the PR body is finalized.

## Decisions made / carried (recorded for agents)

- **Agents never launch the sprint loop.** The human dev at the keyboard starts
  `/loop-sprint-cron`. For Sprint 8 that human was me (a CLAUDE.md rule of the
  road).
- **Mint-route history (settled):** attack/zt were already fixed in Sprint 3 T1
  (`attack.py:258-273`, `zt.py:539-554`); only tech-debt still carried the
  unbounded-version pattern, and Sprint 8 T1 paid it. All four assessment services
  now share the idempotent draft-reuse shape. This supersedes the older "all three
  still share it" note.
- **Codex stays a read-only plan reviewer.** The Sprint 8 plan was reviewed by
  OpenAI Codex (CLI v0.144.5, read-only, 2026-07-16, verdict "ship-with-changes");
  its two blockers (T1 guard placement before the LLM call, the explicit
  re-contract of `test_extract_versions_subsequent_lists`) and the rest of its
  findings are folded into `SPRINT_8.md`.
- **My manual MFA walkthrough is retired.** T4 and T5 drive the enrollment / TOTP
  / recovery-code UI for real, so I no longer owe that hand-check.
- **Infra: local containers for now** (2026-07-13 call unchanged); the GCP live
  path was validated 2026-07-15 and `.env` is back to fixture.
- **Keycloak SSO / OIDC cutover stays deferred** (my 2026-07-16 call, unchanged).

## Next steps

1. Open the Sprint 8 PR into `main` with a rich body: the task table, the MFA-fix
   writeup (the sprint's most consequential outcome), the SMOKE eligibility note
   (unit-proven backend-invariant boxes such as §16 release deny paths, §20
   preview internals, §21 audit filters, plus the end-of-file sign-off boxes, stay
   unchecked because nothing this sprint proves them in a browser), and the Codex
   findings table.
2. Let the shutdown checkpoint run the authoritative full e2e + security audit;
   fold the results into the PR test plan.
3. After Sprint 8 merges: candidates are the Keycloak SSO cutover, the tech-debt
   "replace/re-extract draft" UI affordance (now that the route is idempotent), and
   a demo-reset automation decision.

## Notes for Gene

- Sprint 8 shipped all e2e/spec work plus one api idempotency fix (T1) and one
  out-of-plan web auth fix (the MFA `totp: undefined` bug, `f10b803`). No
  migrations. The only dependency change is a TOTP lib (`otpauth`) inside `e2e/`,
  which is the host-run harness, not a container.
- Sprint 8 T1 deliberately re-contracts `test_extract_versions_subsequent_lists`
  (tech-debt extract is now idempotent-200 on an open draft, like CSF/attack/zt);
  flagged here so the test change does not read as weakening.
- The MFA fix is worth a look: a flow that unit tests and a vitest called green was
  broken for every real user, because the vitest mocks `signIn()` and never
  exercised the real `URLSearchParams` serialization. The browser spec is what
  caught it.
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject; do not remove.
