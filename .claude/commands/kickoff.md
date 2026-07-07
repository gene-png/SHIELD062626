---
description: First-session orchestrator for a brand new project. Runs the full discovery sequence: interview → function planning → context snapshot. Use this once at the start of a new project.
allowed-tools: Read, Write
---

This is the start of a new project. Run the full discovery sequence in order.

**Do not skip stages. Do not start building yet.**

---

## Stage 1 — Interview

Run `/interview` inline now.

Conduct the full project interview — purpose, users, features, tech stack, data model. Ask questions one at a time. Do not proceed to Stage 2 until:
- I have confirmed the architecture document looks correct
- `ARCHITECTURE.md` has been written to the project root

---

## Stage 2 — Plan functions

Run `/planfunction` inline now.

Read `ARCHITECTURE.md` and plan every function needed for the first sprint. Write `SPRINT.md` with full typed signatures, process outlines, and test plans for each function.

Present the sprint plan to me. Wait for confirmation before proceeding.

---

## Stage 3 — Snapshot context

Run `/context` inline now.

Write the initial `CONTEXT.md` capturing:
- What the project is
- Current state (pre-implementation — scaffold only)
- The full list of next steps from `SPRINT.md`
- No lessons learned yet (first session)

---

## Final output

Print a startup summary:
- Project name and one-line description
- Number of functions planned
- Suggested first command to run next

**You are now ready to build. The suggested next command is `/execute` to implement the first sprint, or `/feature <name>` to scaffold a specific feature first.**
