# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-16 (Sprint 7 complete on branch)_

## Branch / in flight

- **Sprint 7 "GCP live path + close the client loop" COMPLETE** on
  `feat/gcp-vertex-sprint-7` (`v3.4.0`). All 7 tasks (T0–T6) via
  `/loop-sprint-cron`, one day. T1 (the live GCP sweep) was run by me in the
  foreground — real Vertex, ADC-only, all five purposes green, two adapter
  defects found + fixed (`329f9a5`). Vertex provider via ADC (D-029), client
  release-notification email (D-030), dev/CI email delivery on by default (s21
  runs), reqSeq sweep finished, Auth.js v5 migration (clears the `uuid`
  moderate). No new migrations.
- **Next:** open the Sprint 7 PR (rich body — task table + test plan + the
  D-029/D-030 decisions + the "GCP-validated 2026-07-15" note), get it reviewed,
  squash-merge to `main`.

## Decisions made / carried (recorded for agents)

- **Infra: local containers for now.** No terraform/cloud deploy; `infra/` stubs
  stay stubs. Revisit when I pick cloud/account/region.
- **GCP, not Anthropic, for live-AI validation — DONE.** Vertex AI via ADC
  (project `kentro-cloudmod-dev`, `us-central1`), no static key. The five-purpose
  live sweep passed 2026-07-15 on `gemini-2.5-flash`. `.env` is back to fixture.
- **MFA manual UI walkthrough** is still mine to do by hand (SMOKE eyeball item);
  email-verify enforcement flag stays default-off.

## Next steps

1. Open + merge the Sprint 7 PR.
2. My manual MFA walkthrough (SMOKE_TEST eyeball item) + eyeball the
   verify/forgot/reset web pages (§25 / §24 UI).
3. Sprint 8 planning candidates: an e2e that eyeballs the release notification in
   MailHog (SMOKE §29); the attack/zt/tech-debt mint routes still share CSF's old
   unbounded-version pattern; ESLint 10 / `postcss` moderate (both blocked
   upstream); Auth.js v5 Credentials→OIDC / Keycloak SSO cutover.

## Notes for Gene

- Sprint 7 added a `vertex` LLM provider (ADC, no API key) beside `gemini`. Live
  mode now selects `SHIELD_LLM_PROVIDER=vertex` and needs host gcloud ADC
  bind-mounted read-only — all in the gitignored `.env`. Fixture mode (the
  default) is untouched; nothing changes for you unless you flip to live.
- Web auth is now Auth.js v5 (next-auth `5.0.0-beta.31`). `getServerSession` is
  gone — server code calls `auth()`. The MFA sign-in signal moved from
  `result.error` to `result.code`. Behavior is identical; all auth e2e green.
- Email delivery is ON by default in dev/CI compose now (MailHog on `:8025`), so
  `s21-email-verify` runs. `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY` still defaults off —
  flipping it breaks every e2e sign-in (seeded users are unverified).
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject — don't remove.
