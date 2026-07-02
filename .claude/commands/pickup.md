---
description: Start-of-session orientation. Reads project state and briefs you in plain English — what's done, what's in flight, what to do next. Run this first when picking up after a break.
allowed-tools: Read, Bash(git log:*), Bash(git status:*), Bash(git diff:*), Bash(npx playwright test:*)
---

Orient me quickly. I'm picking up after a break and need to know exactly where things stand.

## Gather context

Read all of these before writing anything:
- `CONTEXT.md` — full project state
- `ARCHITECTURE.md` — overall structure (skim for orientation, not deep read)
- `SPRINT.md` if it exists — what the current sprint contains
- Recent git history: !`git log --oneline -10`
- Uncommitted work: !`git status --short`
- Any uncommitted diff: !`git diff HEAD`

## Then give me a crisp briefing in this format

---

### 📍 Where We Are
[2–3 sentences. What is this project and what phase is it in right now?]

### ✅ Just Completed
[Bullet list — specific things finished in the last session or recent commits. Reference files and function names, not vague summaries.]

### 🔧 In Progress / Unfinished
[Anything started but not done. Uncommitted work, stubbed functions, known broken things.]

### ⚠️ Blockers or Risks
[Anything broken, deferred, or flagged in CONTEXT.md that I should know before diving in. If none, say so.]

### 🎯 Recommended Next Action
[The single most important thing to do right now — one concrete action, not a list. Be specific: name the command, function, or file.]

### 📋 Full Next Steps (after that)
[Ordered list of what follows — pulled from CONTEXT.md and SPRINT.md]

---

Keep this tight. The goal is to get me oriented in under 60 seconds, not to reproduce CONTEXT.md at me. If there's uncommitted work, flag it prominently — I may have left something half-done.

**Finish with:** "Ready. What would you like to do?" — then wait for me.
