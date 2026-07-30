---
description: Start-of-session orientation. Reads the project state, then checks it against reality rather than trusting it.
allowed-tools: Read, Grep, Glob, Bash(git:*), Bash(bash .claude/hooks/*), Bash(ls:*)
---

# /pickup

Orient David in under sixty seconds. He is picking up after a break.

## Read

- `CONTEXT.md`, the whole file, and its "Active business exceptions" section twice.
  Those are requirements this business means to hold and is not holding right now, on
  purpose. The one that started the section was a decision that stayed correct for two
  days and then stopped, with nothing making anybody look at it again.
- `CLAUDE.md` at the repo root, and any nested one covering the area in play
- The tracker. `.claude/sprint-plan` names the file when a repo has more than one, so
  read that first and take the path from it. Where the file is absent, the tracker is
  `docs/SPRINTS.md`. Say which one you read.
- `git log --oneline -10`, `git status --short`, and the diff if the tree is dirty

## Then check what you read

`CONTEXT.md` is a document written by an agent. It records what was believed at the time.
Before repeating any of it, run:

```
bash .claude/hooks/run-gate.sh commit
```

and `git status --short`.

Where the repo has an overdue-exception check, run it separately rather than chained:
behind a failing typecheck it never runs, and an overdue exception is the one thing here
that gets worse the longer nobody mentions it. In spearhead-business that is
`npm run check:reviews`.

If the tree is dirty or a check fails, that goes at the top of the briefing, above
everything else. **REFUSE** to present a claim from `CONTEXT.md` as current fact when a
thirty-second check contradicts it. Say which one is wrong.

Note anything `CONTEXT.md` claims is working that carries no evidence line. Those are
beliefs, and they get labelled as beliefs.

## The briefing

```
### Where We Are
Two or three sentences. What this is, what phase it is in.

### Just Completed
Specific. File and function names, not summaries.

### In Progress / Unfinished
Uncommitted work first, and prominently. Stubs, known-broken things.

### Active Exceptions
Anything overdue first, in bold, with its title and the date it was due. Then one line
per live exception: number, what is suspended, review date. Never the fallback or the
reasoning; the entry carries those.

### Blockers or Risks
Including anything waiting on David. If none, say so.

### Recommended Next Action
One concrete thing. Name the command or the file.

### Full Next Steps
Ordered, from the tracker.

### Unverified
Anything CONTEXT.md asserts that nothing in this session proved.
```

Keep it tight. The goal is orientation, not a second copy of `CONTEXT.md`. The
exceptions block is the one that has to survive being skimmed: David reads a briefing to
find out what to do next, and an exception is by definition something he decided not to
do and then stopped seeing.

Finish with: "Ready. What would you like to do?" and wait.
