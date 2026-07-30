---
description: Open and execute one work unit. Spec, then a TDD cycle per behaviour in dependency order, then verify against the criteria.
argument-hint: [sprint number or goal, or blank to take the next one from the tracker]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(bash .claude/hooks/*), Bash(git:*), Bash(echo:*), Bash(rm:*), Agent
---

# /sprint

## The sprint
$ARGUMENTS

If blank, take the next unstarted sprint from the tracker. `.claude/sprint-plan` names
the file when a repo has more than one; where that file is absent the tracker is
`docs/SPRINTS.md`. Resolve it from the pointer rather than from the working directory, and
say which one you are reading.

---

## Stage 1. Specify, and stop for David

Run `/spec` on the sprint goal. That produces the invariants, the journey matrix, the
acceptance criteria, the closed-list register and the counterexample fixtures.

Then **stop and show David**:
- the acceptance criteria, verbatim
- which ones are already `needs-human`
- anything in the sprint that the spec could not phrase as an observable outcome

**REFUSE** to start work until he has replied. This is one of the two gates in the whole
pipeline that reaches a person, and it is the cheap one: a wrong direction costs a
sentence here and a day later.

## Stage 2. Build, one behaviour at a time

For each behaviour in the spec, **in dependency order**, run the `/tdd` cycle including
every one of its stop conditions.

**Do not parallelise this across subagents.** The old version of this command spawned one
subagent per function, each writing its own test and then implementing against it. That
is the arrangement that produced tests encoding the implementation, which is defect 6 in
`docs/workflow-lessons.md`. One cycle at a time, and the test comes from the spec.

Keep each change small enough to read. If a single behaviour is producing more than about
400 lines, it was more than one behaviour.

## Stage 3. Smoke it

Run `/smoke`. Fresh state, public interactions, all six rows of the matrix, artifacts
saved to disk.

**REFUSE** to move on while the empty-input row is unrun. That is the row that catches
invention, and it is the row nobody ever did.

## Stage 4. Verify

Run `/verify` against the acceptance criteria from Stage 1.

Then update the tracker. **A box is checked only when its criterion has an evidence line
in the verify table.** A criterion marked `needs-human` leaves its box unchecked and
gains a `needs-human:` note beside it saying what a person must look at.

**REFUSE** to mark the sprint delivered while any criterion lacks evidence. Exit codes
and test counts are not evidence. Neither is your own account of having checked.

## Stage 5. Report

```
SPRINT: <id> - <goal>
TRACKER: <which file>

CRITERIA
| # | Criterion | Evidence | Result |

SMOKE: <artifact paths, one per matrix row>
BUILT: <one line per behaviour, with its red/green/mutation cycle referenced>
NOT DELIVERED: <criteria not met, and why>
needs-human: <what David must look at, and where>
```

Then say plainly whether the sprint is delivered, delivered except the `needs-human`
items, or not delivered. There is no fourth answer.

## What this command does not do

It does not commit, push, or close out. That is `/ship`, and keeping them apart means the
decision to ship is a separate decision from the decision that the work is finished.
