---
description: Read the current project state and overwrite CONTEXT.md with a complete status snapshot — what's done, what's next, lessons learned.
allowed-tools: Read, Write, Bash(git log:*), Bash(git status:*), Bash(git diff:*), Bash(find:*), Bash(npx playwright test:*)
---

Generate a complete project context snapshot and write it to `CONTEXT.md` at the project root, overwriting whatever is there.

## Gather context first

Before writing anything, read:
- The existing `CONTEXT.md` if it exists (for lessons learned history)
- `CLAUDE.md` for project fundamentals
- Recent git log: !`git log --oneline -15`
- Current git status: !`git status --short`
- Current diff of uncommitted work: !`git diff HEAD`
- Any planning docs in `.claude/` or project root (`*.md` files)
- Test files in `tests/` to understand what has been built and verified

## Then write CONTEXT.md with this exact structure

```markdown
# Project Context
_Last updated: [date and time]_

## What This Project Is
[2–4 sentence plain-English description of the project purpose and current scope]

## Current State
[Honest assessment: what is working, what is partially built, what is stubbed or missing]

## Just Completed
[Bullet list of work finished in the most recent session or recent commits — be specific, reference files]

## Active / In Progress
[Anything started but not finished, with notes on where it was left]

## Important Next Steps
[Ordered list — most important first. Each item should be actionable, not vague]

## Known Issues & Blockers
[Anything broken, flaky, or deliberately deferred. If none, say so.]

## Lessons Learned — This Codebase
[Specific things discovered about this codebase that future sessions should know:
- Gotchas, quirks, things that broke unexpectedly
- Patterns that worked well
- Things to avoid
Preserve lessons from previous CONTEXT.md versions — do not discard history here]

## Test Coverage Status
[Which features have Playwright tests, which don't, and any known flaky tests]
```

After writing the file, print a short confirmation: what changed vs. the previous version, and flag anything that looks like a risk or blocker that I should know about.
