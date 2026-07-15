# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-13 (Sprint 6 merged, Sprint 7 planned)_

## Branch / in flight

- **Sprint 6 "make it real" MERGED** (PR #33, squash `9ffee69`, `v3.3.0`,
  2026-07-13). All 12 tasks via `/loop-sprint-cron` + 2 checkpoints + shutdown
  deep audit, single day. Live-AI enablement (D-026), real TOTP MFA (D-027),
  real email verify/reset (D-028), seed→MinIO parity, `/ready` dependency
  matrix + `/admin/health`, seeded Risk Register + demo-reset, hosted-demo
  compose, security hardening (MFA lockout integration, `/ready` detail gate).
  One post-shutdown fix: a bandit B105 false positive (ruff noqa doesn't cover
  bandit — needed `# nosec B105`) that CI caught and local gates missed;
  bandit is CI-only, not in the six-gate loop set.
- **Sprint 7 "GCP live path + close the client loop" PLANNED — PR #34 open**
  (https://github.com/gene-png/SHIELD062626/pull/34: SPRINT_7.md + staged
  queue + this file). NOT launched yet.

## Decisions made 2026-07-13 (recorded for agents)

- **Infra: local containers for now.** No terraform/cloud deploy in Sprint 7;
  `infra/` stubs stay stubs. Revisit when I pick cloud/account/region.
- **GCP, not Anthropic, for live-AI validation.** There is NO static Google
  API key — my GCP posture (from kentro-cloud-modernization) is **Vertex AI
  via Application Default Credentials** (project `kentro-cloudmod-dev`,
  `us-central1`). This box's ADC was validated 2026-07-13: direct
  `generateContent` to Vertex `gemini-2.5-flash` returned HTTP 200. SHIELD's
  `gemini` provider is API-key-only, so Sprint 7 T0 adds a `vertex` provider
  (D-029 pending).
- **MFA**: I'm doing the manual UI walkthrough myself (enroll → TOTP sign-in →
  recovery code). Email-verify flags stay default-off until Sprint 7 T3 turns
  dev delivery on (enforcement flag stays off regardless).

## Next steps

1. Merge the Sprint 7 planning PR, then launch: cut
   `feat/gcp-vertex-sprint-7`, copy `.claude/sprint-queue.sprint-7.json` →
   runtime queue, set working_dir/expected_gh_user, `/loop-sprint-cron`.
2. My manual MFA walkthrough (SMOKE_TEST eyeball item).
3. After Sprint 7 T0/T1: confirm the five-purpose live sweep on Vertex.

## Notes for Gene

- Sprint 6 changed auth: real TOTP MFA + email verification/password reset
  exist now (flags `SHIELD_AUTH_REQUIRE_MFA` / `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY`
  gate enforcement, both default off — nothing changes for you until flipped).
- The runtime loop gate set is now SIX gates (web eslint added mid-Sprint-6
  after a latent lint error slipped through the five-gate set).
- Sprint 7 plan assumes gcloud ADC on the launching box for the live tasks
  (they self-skip without it, so the loop stays green regardless).
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject — don't remove.
