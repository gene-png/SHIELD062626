# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-08_

## Branch / in flight

- **Sprint 2 MERGED** (PR #19) and **dependabot fully triaged**: PR #20
  (policy) merged, 7 majors closed (D-018), 5 Actions + autoprefixer +
  next-auth + prettier-3.9.4 (+reformat) + grouped-Actions #21 merged;
  grouped-npm #22 pending rebase+CI at last check.
- `chore/sprint-3-plan` — **Sprint 3 planned from the deep repo audit**
  (`docs/audits/2026-07-08-repo-audit.md`): SPRINT_3.md + staged queue
  `.claude/sprint-queue.sprint-3.json`. Theme: correctness & honesty —
  CSF live-AI fix (CRITICAL: live mode silently broken), attack/zt draft
  guards, auth controls enforce-or-retract, rate limiting, §15.5 filenames,
  llm_calls.client_id, docs truth pass. Framework majors → Sprint 4;
  client-facing features → Sprint 5.

## Next steps

1. Merge the sprint-3 planning PR; merge #22 when green.
2. Launch: cut `fix/audit-correctness-sprint-3` from `main`, swap the staged
   queue into `.claude/sprint-queue.json`, invoke `/loop-sprint-cron`
   (checklist in SPRINT_3.md).
3. AFTER sprint-3 T0 lands: run SMOKE_TEST §14 (live-AI) — meaningful only
   once the CSF schema/grounding fix is in.
4. Sprint 4 = framework majors (D-018 bundle). Sprint 5 candidates = client
   deliverable release + /home value loop + POA&M (audit §4c). Needs-me:
   cloud/account/region decisions (terraform), v2 Work Order doc for
   reference-docs, backup-restore drill.

## Personal todos (human-only)

- SMOKE_TEST §10: eyeball the 8 export documents in `e2e/artifacts/`.
- SMOKE_TEST §14: one live-AI run (`ANTHROPIC_API_KEY` +
  `SHIELD_LLM_MODE=live`), confirm redacted `llm_calls`, no PII.

## Notes for Gene

- This box runs SHIELD web on **:3001** (machine-local `.env WEB_PORT`);
  canonical/CI port stays 3000 — see CONTEXT.md machine-local facts.
- Loop-agent gate gap found in Sprint 2: in-container gates don't run the
  host prettier `format:check` — add it to the sprint-3 queue gates.
