---
description: Overwrite CONTEXT.md with a status snapshot in which every claim of working cites its proof.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git:*), Bash(bash .claude/hooks/*), Bash(ls:*)
---

# /snapshot

`CONTEXT.md` is the file every later session trusts. A wrong line here propagates into
every briefing until someone catches it, and `/pickup` will read it aloud with total
confidence. So it carries citations.

## Before writing anything

Run the gate and capture the output:

```
bash .claude/hooks/run-gate.sh push
```

Paste the suite summary line into the snapshot. Not the count on its own, the line.

## The rule for the state section

**Every claim that something works cites its proof from this session:** the command run
and its output, or the path of an artifact generated now through the public interface.

Anything you did not verify this session goes under **"Believed working, unverified"**
with the date it was last proven. That heading is not a failure. It is the honest shape
of a project nobody has time to re-verify end to end, and it tells the next session where
to look first.

**REFUSE** to put an uncited claim in the working section. Move it down or prove it.

## The shape

```
# Project Context
_Last updated <date>. <One line: the single most important thing in this file.>_

## 1. What this repo is
Layout, and which rules apply where.

## 2. What happened last, worst first
The defects and the fixes, with commit shas.

## 3. Verified working
Each line: the claim, then the evidence.

## 4. Believed working, unverified
Each line: the claim, and when it was last proven.

## 5. What to do next, in order
A table. What, and what it waits on.

## 6. Waiting on David
Numbered, specific, actionable.

## 7. Rules that are not negotiable
The ones enforced by a test or a hook, and which one enforces each.

## 8. Things that will waste your time
The traps. This section earns its keep every time.

## 9. Where the reasoning lives
Pointers to the wiki log and the reviews.
```

## After writing

Print what changed against the previous version, in three or four lines. If a claim moved
from "verified" to "believed working", say so: that is the most important kind of change
in this file and the easiest to miss.
