# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-06_

## Branch / in flight

- `qa/smoke-sweep-sprint-1` — pushed, **PR #16 open** to `main`
  (Sprint 1: 14-file Playwright smoke suite + runtime fixes, 19 commits,
  all gates green). Awaiting review/merge.
- `chore/collab-docs` — this collaboration-docs restructure (CLAUDE.md,
  context/, command updates), stacked on the sprint-1 branch.

## Next steps

1. Merge PR #16, then the collab-docs PR.
2. Cut `fix/findings-burndown-sprint-2` from `main`, swap
   `.claude/sprint-queue.sprint-2.json` into place, launch `/loop-sprint-cron`.
   Plan: `SPRINT_2.md` (11 tasks — dep bump, runtime e2e ids, CI e2e+axe,
   CSF IG metadata, small-fix burn-down).

## Personal todos (human-only)

- SMOKE_TEST §10: eyeball the 8 export documents in `e2e/artifacts/`.
- SMOKE_TEST §14: one live-AI run (`ANTHROPIC_API_KEY` +
  `SHIELD_LLM_MODE=live`), confirm redacted `llm_calls`, no PII.
- Do both BEFORE sprint-2 T2 runs — it wipes the local demo DB.
