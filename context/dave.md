# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-10 (Sprint 5 executed + shipped)_

## Branch / in flight

- **Sprint 5 EXECUTED — PR #31 open** (`feat/client-value-loop-sprint-5`,
  https://github.com/gene-png/SHIELD062626/pull/31, targets `v3.2.0`). All 11
  tasks (T0–T10) ran via `/loop-sprint-cron` + 2 checkpoints + shutdown deep
  audit, this session. Merging once CI is green (see the gate-divergence fix
  below).
  - **Client value loop shipped:** deliverable release-to-client backend
    (D-025, migration 0028) + `/documents` (§6.7); `/home` dashboard (§6.4)
    with role-based landing; cross-service value-loop card (§2.5, deterministic
    aggregation — no LLM); CSF POA&M step (migration 0029, XLSX Action Plan
    sheet); redaction preview gate (`POST /ai/preview`, no egress/no llm_calls
    row); `/admin/audit` read-only viewer; vitest harness + reqSeq guard tests;
    all 14 react-hooks v6 rules adopted (zero off).
  - **Shutdown deep-audit caught a HIGH §12 leak:** the value-loop card
    recomputed from the LATEST assessment version, so a post-release DRAFT
    re-assessment could leak in-progress numbers to the client. Fixed
    test-first by pinning recompute to APPROVED/RELEASED (`d4de35d`).
  - **CI gate divergence fixed post-shutdown (`c7c5121`):** `ruff>=0.15,<0.16`
    floated on CI to a newer 0.15.x whose isort re-flagged
    test_llm_providers.py imports the loop's in-container ruff (0.15.20) called
    clean → PR #31 Python job red while every local gate was green. Pinned
    `ruff==0.15.20` / `black==26.5.1` exactly (the loop's validated versions)
    so the loop gate and CI stay byte-for-byte equal. Same class as the
    Sprint-4 T0 lesson: a gate that diverges from CI is not a gate.
  - Mid-sprint recoveries I let the orchestrator handle: a **session-limit
    kill** mid-T4 (recovered via the loop's resume path — widened
    expected_paths for the /home wiring, verified in-tree work rather than
    rewriting); two agents **parked on background monitors** mid-gate (T1, T9)
    and needed a foreground-poll nudge (the known stall).
- **Sprint 4 MERGED** (PR #28, `c5f9367`, `v3.1.0`): Next 15 / React 19 /
  Tailwind 4 / ESLint 9 / Node 22; OpenAI + Gemini adapters (D-024); audit to
  zero (2 documented moderates postcss/uuid).

## Next steps

1. **Merge PR #31** once CI green → `v3.2.0` on `main`. (dependabot #29 already
   closed as superseded 2026-07-10.)
2. **SMOKE_TEST §14 live-AI** — the big remaining "is it real?" item. No
   provider key in `.env` yet. Add `SHIELD_LLM_MODE=live` +
   `SHIELD_LLM_PROVIDER=<anthropic|openai|gemini>` + that provider's key +
   matching `SHIELD_LLM_MODEL`, restart api, run one CSF Run-AI, verify a
   redacted `llm_calls` row (correct provider/model/client_id, no PII), revert
   to fixture. Defects → a follow-up task. **Anthropic key recommended** (it's
   the reference adapter with the most test coverage).
3. **Demo-readiness gaps** (see the assessment I wrote up 2026-07-10): the two
   real blockers to an all-real demo are (a) the live-AI smoke above and (b)
   the seed→MinIO storage mismatch — seeded deliverable artifact bytes go to
   LocalFilesystemStorage but the API reads S3/MinIO, so seeded downloads 410;
   only runtime-finalized artifacts download. Plus real MFA/email-verification
   (currently flags fail loudly, D-020) and Keycloak wired for the demo login.
4. Needs-me: cloud/account/region decisions (gates terraform/deploy/DR).

## Personal todos (human-only)

- Merge PR #31 (or confirm my agent did once CI green).
- Get an Anthropic API key for the §14 live-AI smoke + all-real demo.
- Decide cloud/account/region for the infra work (Sprint 6).
- Fix the seed→storage-backend mismatch so demo deliverables download from a
  clean seed (or document "finalize at runtime for the demo").

## Notes for Gene

- This box runs SHIELD web on **:3001** (machine-local `.env WEB_PORT`);
  canonical/CI port stays 3000 — see CONTEXT.md machine-local facts.
- **Lint gate pinned exactly now** (`ruff==0.15.20`, `black==26.5.1` in
  apps/api/pyproject.toml): a floating range bit us on PR #31. If you bump
  either, do it deliberately with a format pass and re-pin.
- Loop lesson (recurred again in Sprint 5): dispatched iteration agents park on
  background monitors mid-gate; the orchestrator must nudge them to
  foreground-poll. Logged in `.claude/scheduler-debug.log`.
- The cron loop is session-bound: re-invoking `/loop-sprint-cron` re-bootstraps
  from `.claude/sprint-queue.json` — nothing is lost if the session dies.
