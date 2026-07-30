---
name: loop-sprint-cron
description: Autonomous sprint driver. Executes the repo's sprint plan one focused sprint at a time, each in a fresh headless subagent context (replicating `claude -p`) with a pinned model and a wall-clock cap. The plan is the path named in `.claude/sprint-plan`, resolved against the repository root, falling back to docs/SPRINTS.md. Every command runs from the repository root regardless of where the plan lives. Event-driven continuation, deadline kill switch, cron watchdog. Runs periodic verification+security checkpoints and a deep-audit + PR shutdown ceremony automatically — these are built into the skill, not the sprint doc. Invoke as /loop-sprint-cron [tick|start|stop|status]. Never asks the user questions; blockers are marked in SPRINTS.md instead.
---

# loop-sprint-cron

Drive the repo's sprint plan autonomously: one sprint per fresh runner context, a pinned
model, time-capped, zero questions to the user.

## Which file is the plan, and where commands run

**Resolve the plan BEFORE anything else, and never assume `docs/SPRINTS.md`.**

1. If `.claude/sprint-plan` exists, the plan is the single repo-relative path it names.
   Blank lines and `#` comments are ignored. Resolve it against the REPOSITORY ROOT, not
   against the working directory.
2. Otherwise the plan is `docs/SPRINTS.md`, as before.

The pointer exists because guessing the plan from a directory is wrong in any repo with
more than one tracker. A workspace holding a backlog with no loop protocol will be read as
the plan if resolution starts from the launch directory, and the run then either refuses or
executes the wrong backlog, unattended, having been told not to ask anyone anything.
Trackers usually cannot be renumbered to disambiguate, because commit messages already
reference their numbers.

**Every command runs from the repository root**, whatever the plan's path says. Reading a
plan out of a subdirectory does NOT mean working in that subdirectory: a sprint declares
which paths it owns, and the plan's location says nothing about them. Where a root task
fans out to workspaces, run it from the root.

Where the repo can test it, assert that `.claude/sprint-plan` satisfies the prerequisites
below, so a plan that would make this skill refuse at run time fails on a push instead of
during an unattended run.

## Prerequisites (per repo)

The resolved plan must exist and contain:
1. A **Loop protocol** section defining the repo's **verification gate** — the exact
   commands that must pass (tests, typecheck, build, E2E, linters), the branch to push
   to, and commit-message conventions. **The gate is a precondition, never a pass.**
   Passing commands prove the commands ran. They do not prove the product works, and
   this skill once marked 45 sprints done on exactly that evidence.
2. A **Backlog** of checkbox sprints (`- [ ] **S<N> · Title.** …`), each precise and
   focused enough that a FRESH context can execute it without asking anything —
   scope, file set, and explicit acceptance criteria. Vague sprint = derailed run.
   Each acceptance criterion must name an **observable outcome** and its evidence plan:
   a named test with a quoted assertion, or an artifact produced through the public
   interface. A criterion that reads "tests pass" or "file changed" is malformed;
   STOP and say so rather than executing against it.
3. A **Log** section the driver appends to.

If the resolved plan is missing or lacks these, STOP and tell the user what to create
(offer to draft it from the project's roadmap). Do not invent sprints silently.

## Configuration (defaults, overridable via args like `--max 45m --model opus`)

- `MODEL`: `opus` for coding sprints (the point is a strong coder in a cheap fresh
  context); doc-only sprints may use the session model.
- `MAX`: `30m` wall-clock per runner attempt (the enforced cap).
- `RETRIES`: 1 respawn after a timeout/failure, with narrowed scope; then mark blocked.
- `CHECKPOINT_EVERY`: `4` — after every N completed sprints, run a **Checkpoint**
  (full verification gate + security audit) before starting the next one.
- `EXPECTED_ACCOUNT`: the VCS account all pushes/PRs MUST run under (guards against
  credential/account drift). Supplied at invocation (e.g. `--account <name>`), NOT
  read from SPRINTS.md. If set, the driver and every runner verify it before any push
  or PR and refuse under a different account. If unset, the check is skipped and a
  one-line warning is logged.
- State file: `<scratchpad>/loop-sprint-state.json` →
  `{sprint, runner_task_id, started_at, cap_minutes, attempt, watchdog_cron_id,
  completed_count, expected_account}`.
- Watchdog cron: every ~15 min on an off-minute (e.g. `4-59/15 * * * *`), recurring,
  prompt `/loop-sprint-cron tick`. Create once — check CronList first. Recurring
  crons auto-expire after 7 days; re-arm when reviving a long-lived loop.

## The tick algorithm (every invocation is a tick; derive state, act, re-arm, end turn)

1. Read the state file and TaskList; resolve the plan per "Which file is the plan" above and read it.
2. **Runner alive, within cap** → do nothing except ensure a ScheduleWakeup exists for
   the remaining cap time. Brief one-line status. End turn.
3. **Runner alive, over cap** → TaskStop it. Inspect what it committed/left. If the
   verification gate passes and acceptance criteria are met, treat as complete
   (step 4-pass). Else if `attempt ≤ RETRIES`: respawn (attempt+1) with the timeout
   report and a narrower scope instruction. Else mark the sprint
   `⛔ BLOCKED: timed out ×N`, log it, report in the turn's final text, continue to
   step 5.
4. **No runner, sprint in flight** (runner finished or died) → run the repo's
   **verification gate YOURSELF** (from SPRINTS.md's loop protocol — never trust the
   runner's claim).
   - Gate green → **this is not yet a pass.** Now collect evidence per criterion:
     - For **each** acceptance criterion, record one evidence line: the command run
       with its captured output, or the path of an artifact produced through the
       product's public interface this turn.
     - If the sprint touched anything a customer sees, generate that artifact from a
       **fresh, empty session**, save it under `docs/evidence/S<N>/`, and assert both
       directions: every supplied fact present, and **no unsupported fact present**.
       An empty-input run is mandatory here. It is the run that catches invention.
     - Any criterion with no evidence line → write `needs-human: <criterion>` beside
       the checkbox and **leave the box unchecked**. Do not round it to done.
     - Only when every criterion carries evidence: check the box, append a log line
       (`date · sprint · evidence-paths · sha`), commit+push (identity-guarded).
       Exit codes and test counts are never evidence on their own.
     Increment `completed_count` only for a fully-evidenced sprint. If
     `completed_count` is now a nonzero multiple of `CHECKPOINT_EVERY`, run a
     **Checkpoint** (below) as a barrier before continuing. Continue to step 5.
   - Fail → retry policy as in step 3 (respawn once with the failure report attached),
     then block-and-move-on.
5. **No runner, nothing in flight** → find the first unchecked, unblocked sprint.
   - None left → run the **Shutdown ceremony** (below) — deep audit, security audit,
     CONTEXT/docs refresh, and PR — then STOP THE LOOP: CronDelete the watchdog, delete
     the state file, final summary of ✅/⛔ per sprint. Do not re-arm. End.
   - Otherwise spawn it (below) and write the state file.
6. Re-arm: as the LAST action of the turn, ScheduleWakeup for
   `min(remaining cap + 2m, 30m)` with prompt `/loop-sprint-cron tick`. Runner
   completion events usually wake the loop first; the wakeup is the deadline/backstop.

## Spawning a runner (the `claude -p` replication)

`Agent(subagent_type: "general-purpose", model: MODEL, run_in_background: true)` with a
self-contained prompt — the runner sees ONLY this, so it must carry everything:

- Repo root path and the branch to push to.
- The sprint's spec **verbatim** from SPRINTS.md, plus any pointers it needs (paths to
  design docs, plan files, prior reports) — a fresh context knows nothing else.
- Protocol block:
  - TDD: failing test first for all behavior changes; fail loudly (no silent
    fallbacks on critical paths).
  - Stay strictly inside the sprint scope. Touching unrelated files is failure.
  - Time budget ≈ MAX minutes: if running long, land the smallest green state, commit,
    and report what remains — never leave the tree red or half-edited.
  - Run the repo's verification commands before claiming done.
  - Commit (imperative message + the repo's required trailers, crediting the actual
    runner model) and push to the designated branch (identity-guarded — see
    **Identity guard**), with retry/backoff on network failure.
  - Do NOT check off SPRINTS.md — the driver does that after independent verification.
  - You cannot ask the user anything. If blocked on missing credentials/decisions,
    stop and report `BLOCKED: <reason>` as your final message.
  - Final message = structured report: done / not done, files touched, test counts,
    commit sha, blockers. Raw data, no prose padding.

## Checkpoint (every `CHECKPOINT_EVERY` completed sprints)

A barrier health-sweep, NOT feature work. Spawn a fresh runner
(`general-purpose`, MODEL, background) whose entire job is:

- Run the **full verification gate** from SPRINTS.md (tests, typecheck, build, E2E,
  linters) AND a **security audit** — dependency-vulnerability scan + a scan of
  recently-committed code for hardcoded secrets and OWASP-Top-10 issues.
- All green → append log `checkpoint · pass · <counts>` and return.
- Fixable in one pass without violating TDD → fix test-first, commit (identity-guarded)
  on the branch, log `checkpoint · fixed · <sha>`.
- Broken and NOT one-pass fixable → mark `⛔ BLOCKED: checkpoint regression — <reason>`
  in SPRINTS.md, log it, surface it in the turn's final text.

Never spawn the next sprint until the checkpoint has returned. A checkpoint block
halts the loop's advance (the regression is more important than the next feature).

## Shutdown ceremony (backlog complete)

Spawn one final fresh runner (`general-purpose`, MODEL, background) with a
self-contained prompt covering, IN ORDER:

1. **Deep audit** — parallel sub-audits for type errors, logic/runtime bugs, spec
   compliance against SPRINTS.md + the architecture docs, and test-coverage gaps. Fix
   findings in committable chunks, test-first. Anything not one-pass fixable → mark
   `⛔ BLOCKED` in SPRINTS.md and stop the ceremony there.
2. **Security audit** — dependency-vulnerability scan + hardcoded-secret + OWASP-Top-10
   scan of the branch's commits. Fix or document.
3. **Refresh CONTEXT/docs** — update the project's status snapshot (what shipped per
   sprint + sha, deferrals, known issues, lessons) in the repo's existing style.
4. **Commit** any audit/doc changes on the branch.
5. **Identity-guarded push** — verify `EXPECTED_ACCOUNT` (see below), then push with
   retry/backoff.
6. **Open or update the PR** — read the full branch commit log, write a body with a
   Summary reflecting ALL commits, the sprint table (id · title · sha · status), a
   Test-plan section covering every gate command, and an Out-of-scope section listing
   any pending `⛔ BLOCKED` items. Only create a PR if the invoking config asked for one
   (`--pr`) or a PR for the branch already exists; otherwise stop at push and report.
7. Log `shutdown · <pass|fixed|blocked> · pushed=<t/f> · pr=<url|none>` and return a
   one-line summary.

## Identity guard (before every push or PR)

If `EXPECTED_ACCOUNT` is set, the driver and every runner MUST confirm the active VCS
account matches it (e.g. `gh auth status`) immediately before any push or PR, and
refuse — logging `⛔ identity-mismatch` — if it differs. Never push or open a PR under a
different account. If `EXPECTED_ACCOUNT` is unset, log a one-line warning and proceed.

## Invariants

- The Checkpoint and Shutdown ceremonies are part of THIS skill, not SPRINTS.md — they
  run regardless of what the sprint doc says. SPRINTS.md supplies the gate commands and
  the backlog; it cannot opt out of verification, the security sweep, or the shutdown PR.
- Never check a box whose acceptance criteria you did not verify yourself this turn.
  **Verify** here means: produced an evidence line of an admissible kind, being a pasted
  command output, a saved artifact generated through the public interface, or a named
  test with its assertion quoted. Re-running the same gate commands the runner already
  ran is not verification. When a suite has zero tests on the function that matters,
  running it twice proves it twice.
- There are three outcomes for a criterion, not two: met, blocked, and `needs-human`.
  A criterion that cannot be checked mechanically gets `needs-human` and stays open.
  With only met and blocked available the unverifiable ones get rounded to met, because
  blocked stops the loop and met does not. That rounding is how 45 sprints closed while
  the product was fabricating client documents.
- Never run two runners at once.
- One sprint may block only itself; the loop always advances to the next unblocked
  sprint.
- Every turn ends with either a re-armed ScheduleWakeup or an explicit loop-stop.
- The user is notified (final turn text) on: sprint completion, block, timeout,
  loop finish. No questions, only reports.
- State lives in the repo (SPRINTS.md checkboxes + log) so the loop survives session
  loss; the scratchpad state file is a cache, not the source of truth.

## stop / status

- `stop`: TaskStop any runner, CronDelete the watchdog, delete the state file, keep
  SPRINTS.md truthful, summary.
- `status`: one screen: current sprint, runner state, elapsed vs cap, boxes
  checked/remaining, blocks.

## Installing in a new repo

1. Copy this file to `.claude/skills/loop-sprint-cron/SKILL.md`.
2. Create `docs/SPRINTS.md` (loop protocol w/ verification gate + precise backlog + log).
3. Say `/loop-sprint-cron start` (add `--account <name>` to guard against push/PR
   account drift, `--pr` to have the shutdown ceremony open a PR) — the driver arms the
   watchdog, spawns the first sprint, and runs until the backlog is done or everything
   is blocked, running a checkpoint every `CHECKPOINT_EVERY` sprints and the shutdown
   ceremony at the end.
