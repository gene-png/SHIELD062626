---
description: Generate a pull request description from the current branch's commits and diff. Produces a clear, honest PR that explains what changed and why.
argument-hint: [optional: base branch, defaults to main]
allowed-tools: Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(npx playwright test:*), Read
---

Generate a pull request description for the current branch.

## Gather context

<base_branch>
!`echo "${ARGUMENTS:-main}"`
</base_branch>

<current_branch>
!`git branch --show-current`
</current_branch>

<commits_on_branch>
!`git log origin/${ARGUMENTS:-main}..HEAD --oneline`
</commits_on_branch>

<full_diff>
!`git diff origin/${ARGUMENTS:-main}...HEAD --stat`
</full_diff>

Read `CONTEXT.md` and `ARCHITECTURE.md` for background on the project.

## Run tests first

```bash
npx playwright test --reporter=line
```

If tests fail, **stop and report the failures**. Do not generate a PR description for broken code.

## Generate the PR description

Write a PR description in this format:

---

```markdown
## What this PR does
[2–4 sentences. Plain English. What problem does this solve or what feature does it add? Write for someone who hasn't been in this codebase for a week.]

## Why it was built this way
[1–3 sentences on key design decisions — especially anything non-obvious. If you chose approach A over approach B, say why. This is the most important section for future-you.]

## Changes

### New
- [list new files/functions/features]

### Modified
- [list changed files and what changed]

### Removed
- [anything deleted]

## Testing
- [ ] All existing tests pass
- [ ] New tests added for: [list what's covered]
- [ ] Tested manually: [list any scenarios that were manually verified]

## Known limitations / follow-up work
[Anything deliberately deferred, edge cases not handled, or follow-up tickets needed. If none, say "None — this is complete."]
```

---

Present the description to me. I'll copy it into GitHub. If anything in the diff looks like it shouldn't be in this PR (unrelated changes, debug code left in, accidentally committed files), flag it before I review.
