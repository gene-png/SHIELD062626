# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-09_

## Branch / in flight

- **Sprint 5 PLANNED — PR #30 open** (`chore/sprint-5-plan`,
  https://github.com/gene-png/SHIELD062626/pull/30): SPRINT_5.md + staged
  queue (11 tasks). Theme: client value loop — deliverable release-to-client
  (D-025), /documents (§6.7), /home dashboard (§6.4) + value card (§2.5),
  CSF POA&M step, redaction preview, /admin/audit viewer, vitest harness,
  react-hooks v6 adoption, prettier 3.9.5 pin sync (supersedes dependabot
  #29). DELIVERY_PLAN.md refreshed to match real sprint history.
- **Sprint 4 MERGED** (PR #28, merge commit `c5f9367`, `v3.1.0`). All 9
  tasks via `/loop-sprint-cron` + 2 checkpoints + shutdown deep audit.
  Highlights:
  - Framework majors landed: Next 15.5.20 / React 19.2.7 / Tailwind 4 /
    **ESLint 9 flat config** (ESLint 10 blocked upstream — no published
    eslint-plugin-react supports v10; deferral annotated on D-018) / Node 22.
    Audit-to-zero met (0 high/critical; 2 documented moderates postcss/uuid).
  - Multi-provider LLM: OpenAI + Gemini httpx adapters below the egress seam
    (D-024); fixture default untouched.
  - 3 stale-fetch race bugs found+fixed along the way (CsfPlaybookPanel s7,
    MessageThread s9/T8, plus panel error-swallowing at shutdown audit);
    shutdown audit also moved the Gemini key from URL param to header
    (key was leaking into `llm_calls.error_message` on HTTP errors).
  - next-auth needed NO Auth.js v5 migration (peer range already allows
    Next 15/React 19 — the planning-time risk note was stale).
  - Mid-sprint I approved: dev-DB cleanup of 26 QA-junk clients (unblocked
    s2), and the T3 retarget to ESLint 9.

## Next steps

1. **Review + merge PR #30** (Sprint 5 plan).
2. Launch Sprint 5: cut `feat/client-value-loop-sprint-5` from `main`, swap
   the staged queue in, `/loop-sprint-cron` (checklist in SPRINT_5.md).
   Leave dependabot #29 open until T0 lands, then close as superseded.
3. **SMOKE_TEST §14** (live AI — provider-agnostic): no key in `.env` yet
   (confirmed 2026-07-10). Add a provider key + `SHIELD_LLM_MODE=live`,
   restart api, one CSF Run-AI, verify redacted `llm_calls` row with
   `client_id`, no PII; revert to fixture. Defects → sprint-5 queue tasks.
4. Needs-me: cloud/account/region decisions (gates terraform/deploy/DR).

## Personal todos (human-only)

- Merge PR #30; launch the Sprint 5 loop.
- SMOKE_TEST §14 live-AI run (see step 3). §10 done 2026-07-09.
- Decide cloud/account/region for the infra work (Sprint 5+/6).
- Optional: OpenAI/Gemini API keys for a live smoke of the new adapters
  (unit tests don't need them).

## Notes for Gene

- This box runs SHIELD web on **:3001** (machine-local `.env WEB_PORT`);
  canonical/CI port stays 3000 — see CONTEXT.md machine-local facts.
- The T0 compose mount fixed in-container ruff/black root-config parity —
  the loop's lint gate now equals CI (new 4th gate in the runtime queue).
- Loop lesson (recurred all sprint): dispatched iteration agents tend to
  park on background monitors mid-e2e-gate; the orchestrator must nudge
  them to foreground-poll. Logged as `stage=agent-stalled-resumed` in
  `.claude/scheduler-debug.log`.
- The cron loop is session-bound: if the Claude session dies, re-invoking
  `/loop-sprint-cron` re-bootstraps from the queue file — state lives in
  `.claude/sprint-queue.json`, nothing is lost.
