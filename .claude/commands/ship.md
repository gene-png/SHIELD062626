---
description: Close out a work unit. Review, gate, smoke, audit, commit, snapshot. Absorbs the old /commit and /pr.
argument-hint: [what is being shipped, or blank]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(bash .claude/hooks/*), Bash(git:*), Bash(gh:*), Agent
---

# /ship

## What is shipping
$ARGUMENTS

---

Six stages. Each produces evidence that goes in the final report. A stage that produces
no evidence has not run.

## Stage 1. Review

Run `/review`. It spawns a fresh subagent that did not write the code.

**A FAIL on provenance, tests, or contamination stops the ship.** Fix the cause, rerun,
and put both review outputs in the report. There is no minor category here: if you are
unsure which side an issue falls on, it blocks.

## Stage 2. The gate

```
bash .claude/hooks/run-gate.sh push
```

Check by exit code, never by reading piped output.

The pre-push hook runs this too, so a failure here means a failure there. Fix the code.
Do not reach for `GATE_OVERRIDE`.

Green is a precondition. It is not a result, and it is not what Stage 3 is for.

## Stage 3. Smoke, and read the artifact yourself

Run `/smoke`. Then **open the artifact a customer would receive and read it**, line by
line, as the customer.

This stage exists because David found four defects in thirty seconds doing exactly this,
against 650 passing tests. Nothing mechanical replaces it, and that is not a failure of
automation: a human reading the document is the correct oracle for a document.

**REFUSE** to ship without the empty-input artifact saved and read.

## Stage 4. Audit

Run `/audit` on the diff. Report only, fix nothing here.

**Stop and show David** any finding that reaches client data, a credential, or a tenant
boundary. This is the second of the two human gates.

## Stage 5. Commit

Stage the paths you changed, **by name**. The hook refuses `git add -A`, and the reason
is that staging everything is how a credential file reaches history.

```
git status --short
git add <path> <path>
git diff --cached
```

Read the staged diff before writing the message. Then show David the message before
committing.

Conventional commit, David's plain style, and end with:

```
Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

## Stage 6. Snapshot and open the PR

Run `/snapshot` to bring `CONTEXT.md` up to date.

If this is a branch, push it and open a PR. The pre-push hook checks the `gh` account and
the git identity first, and refuses under the wrong one.

**Never push to `main` without David saying so.** `/ship` is his approval to merge and
push, and nothing else is.

The PR body says what changed, what it fixes, what evidence exists, and what is still
`needs-human`. End with:

```
Generated with [Claude Code](https://claude.com/claude-code)
```

## The report

```
SHIP: <what>

| Stage | Result | Evidence |
|-------|--------|----------|
| Review | PASS/BLOCKED | <subagent output reference> |
| Gate | PASS/FAIL | <exit codes> |
| Smoke | PASS/FAIL | <artifact paths, and that you read them> |
| Audit | CLEAN/FINDINGS | <findings> |
| Commit | <sha> | <staged paths> |
| Context | updated | |

needs-human: <list, or none>
```

**REFUSE** to end with a success announcement. The old version of this command finished
with "You're done", printed regardless of what happened, which is the green-only
completion failure written into the document in advance. Report what the evidence shows
and let David draw the conclusion.
