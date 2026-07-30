---
description: Remove complexity without changing behaviour. Contract tests survive, assertions never weaken, and the mutations get rerun around what moved.
argument-hint: [area to refactor, or blank for the whole codebase]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(bash .claude/hooks/*), Bash(git diff:*), Bash(git status:*), Agent
---

# /refactor

## Scope
$ARGUMENTS

---

This command finds smell. `/debugloop` finds defects. Keep them apart, because a refactor
that also fixes a bug is a change nobody can review.

## Take the baseline first

Run the suite and record the exact numbers before touching anything. Without a baseline
you cannot tell a defect you introduced from one that was already there, and this repo
has three known-unstable admin-bulk tests that move between runs.

Paste the baseline.

## What to look for

- The same logic in more than one place, especially a hardcoded value repeated across
  renderers.
- A function doing several jobs, where the seam is obvious rather than imagined.
- Dead code, unreached branches, unused exports.
- Types that permit states the domain does not: a string where an enum belongs, an
  optional field that is never absent in practice, an `as` at an I/O boundary.
- Drift between two copies of something that was meant to stay in step.

## What to leave alone

No abstraction before it is needed. A second occurrence is a coincidence. A third is a
pattern. Extracting a shared helper from two callers usually costs more than it saves.

## The refusals

**REFUSE** to weaken an assertion. If a test fails after a change, the change is wrong
until proven otherwise. Revert it and say what happened.

**REFUSE** to replace a public interaction with state injection to make a test faster. An
acceptance test that stops clicking has stopped testing.

**REFUSE** to change what happens for a missing or unknown input. That behaviour is the
specification, however incidental it looks.

**REFUSE** to change behaviour at all. If you find a defect, stop, write it down, and
finish the refactor first. Then run `/debugloop` on it separately.

## After each change

Run the suite. Compare to the baseline, not to green: the same tests pass that passed
before, and no new failure appears.

## Rerun the mutations around what moved

For each boundary you changed, break the code on purpose and confirm a test still goes
red. **Paste it.** A refactor can silently sever a test from the thing it was testing,
and the suite stays green either way, which is the failure mode this whole command set
exists to catch.

## Report

```
BASELINE: <n> passed, <n> failed, <n> skipped
CHANGES: <one line each, with the smell removed>
AFTER: <n> passed, <n> failed, <n> skipped  (identical to baseline, or explained)
MUTATIONS RERUN: <boundary> -> <pasted failure>
DEFECTS FOUND, NOT FIXED: <list for /debugloop>
```
