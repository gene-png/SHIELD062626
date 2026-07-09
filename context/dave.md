# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-09_

## Branch / in flight

- **Sprint 3 MERGED** (PR #26, merge commit `995b403`): all 8 tasks via the
  `/loop-sprint-cron` autonomous loop + closing audit (which caught a real
  non-atomic INCR/EXPIRE lockout bug in the new rate limiter) + one manual
  ruff fix (`753d765` — in-container lint missed the root config; becomes
  Sprint 4 T0). Branch deleted after merge.
- `chore/sprint-4-plan` — **Sprint 4 planned**: SPRINT_4.md + staged queue
  `.claude/sprint-queue.sprint-4.json`. Theme: D-018 framework majors
  (Next 15/React 19/Tailwind 4/ESLint 10/Node 22 → audit-to-zero) +
  **multi-provider LLM** (OpenAI + Gemini adapters behind the existing
  `_build_provider` seam — Dave asked "do we have to use anthropic?" — no,
  spec §4.4 already mandates env-configurable provider) + T0 lint-gate CI
  parity. SMOKE_TEST §10 checked off in this PR (Dave eyeballed the v19/v22
  §15.5 artifacts 2026-07-09).

## Next steps

1. Merge the sprint-4 planning PR.
2. **SMOKE_TEST §14** (live AI): Dave getting an `ANTHROPIC_API_KEY` shortly.
   Set it + `SHIELD_LLM_MODE=live` in `.env`, restart api, one CSF Run-AI,
   verify redacted `llm_calls` row with `client_id` set, no PII; revert to
   fixture. Any defects found → append as tasks to the sprint-4 queue.
3. Launch Sprint 4: cut `feat/majors-providers-sprint-4` from `main`, swap
   the staged queue in, `/loop-sprint-cron` (checklist in SPRINT_4.md).
4. Sprint 5 candidates: client deliverable release + /home value loop +
   POA&M + redaction preview + audit viewer (audit §4c). Needs-me:
   cloud/account/region decisions (gates terraform/deploy/DR).

## Personal todos (human-only)

- SMOKE_TEST §14 live-AI run (see step 2 above). §10 done 2026-07-09.
- Decide cloud/account/region for the infra work (Sprint 5+/6).
- Optional: OpenAI/Gemini API keys if I want a live smoke of the new
  adapters after Sprint 4 T6 (unit tests don't need them).

## Notes for Gene

- This box runs SHIELD web on **:3001** (machine-local `.env WEB_PORT`);
  canonical/CI port stays 3000 — see CONTEXT.md machine-local facts.
- Loop lesson from Sprint 3: in-container ruff/black DON'T see the root
  pyproject config (api container mounts only apps/api) — CI does. Sprint 4
  T0 fixes it with a compose mount; until then run lint checks from a full
  checkout context before pushing python changes.
- The cron loop is session-bound: if the Claude session dies, re-invoking
  `/loop-sprint-cron` re-bootstraps from the queue file — state lives in
  `.claude/sprint-queue.json`, nothing is lost.
