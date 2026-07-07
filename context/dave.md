# Dave — current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-07-07_

## Branch / in flight

- **Sprint 2 loop RUNNING** — `fix/findings-burndown-sprint-2` (from `main`
  post-#16/#18), queue `.claude/sprint-queue.json` (11 tasks T0–T10),
  driver `/loop-sprint-cron`. Heads-up: T2 does `docker compose down -v` —
  local demo DB state is disposable until it completes.
- `chore/dependabot-policy` — dependabot majors-ignore + grouping (D-018),
  CONTEXT/DECISIONS/context refresh. Pushed; PR open for review.

## Next steps

1. **Dependabot triage (needs my personal-account gh auth — the Kentro EMU
   account is blocked from writing to Gene's repo).** One-time:
   `gh auth login` → github.com → HTTPS → login as **SpearheadAnalytica**.
   Then:
   - `foreach ($n in 1,2,3,4,5,7,13,14) { gh pr comment $n --body "@dependabot rebase" }`
     (their CI failures are stale 07-03 runs from before the pnpm double-pin
     fix `f65e36f`; rebase re-runs CI on green main)
   - after checks go green: merge #1–#5 (Actions) then #7, #13, #14 one at a
     time (`gh pr merge <n> --squash`; dependabot auto-rebases the lockfile
     conflicts between the npm ones)
   - close the majors: `foreach ($n in 6,8,9,10,11,12,15) { gh pr close $n --comment "Closing per D-018: majors are sprint-planned; the framework bundle (Next 15/16, React 19, Tailwind 4, ESLint 10, Node 22) lands after e2e is in CI." }`
2. Review/merge the `chore/dependabot-policy` PR.
3. Monitor the sprint loop (`.claude/scheduler-debug.log`); when the queue
   completes, push the branch + open the PR (that push is also T3's first
   real CI e2e run).

## Personal todos (human-only)

- SMOKE_TEST §10: eyeball the 8 export documents in `e2e/artifacts/`
  (host files — survive the T2 wipe).
- SMOKE_TEST §14: one live-AI run (`ANTHROPIC_API_KEY` +
  `SHIELD_LLM_MODE=live`) — now planned AGAINST THE RESEEDED DB after T2
  (accepted the wipe 2026-07-07; no need to beat T2 to it).
