---
description: Interactive interview to fully flesh out a project idea and produce a proposed architecture. Ask me questions until we have a solid foundation.
allowed-tools: Read, Write
---

You are going to interview me about my project idea until we have enough to build on. Do not generate architecture or make decisions yet — your job right now is to ask good questions and listen.

## How to run this interview

Ask questions **one or a few at a time**. Do not dump a list of 20 questions at once. Let my answers guide where you go next. If an answer raises new questions, follow that thread before moving on.

## Topic areas to cover — in roughly this order

**1. Purpose & problem**
- What problem does this solve? For whom?
- Why does this need to exist — what's wrong with current solutions?
- What does success look like in 3 months? In a year?

**2. Users**
- Who are the primary users?
- Are there secondary users or admins?
- What does a typical session look like for the main user?

**3. Core features**
- What are the must-have features for a first version?
- What is explicitly out of scope for now?
- Are there any integrations with external services or APIs?

**4. Data**
- What data does the app create, store, or consume?
- Where does data come from — user input, external APIs, files?
- Any sensitive data that affects security or compliance requirements?

**5. Technical preferences**
- Any language, framework, or runtime preferences or constraints?
- Is there an existing codebase, or is this greenfield?
- Any deployment or hosting constraints?
- What's the target device/platform — mobile, desktop, both?

**6. Non-functional requirements**
- Any performance requirements that matter early?
- Offline support needed?
- Authentication — who logs in, how?

## When to stop interviewing

Keep asking until **both** conditions are true:
1. You have enough to propose a concrete architecture
2. I say I'm satisfied or ready to move on

When ready, produce a `ARCHITECTURE.md` file at the project root with:

```markdown
# Project Architecture

## Purpose
[One clear paragraph]

## Users
[Who they are and what they do]

## Core Features — v1
[Bulleted list, each with a one-line description]

## Out of Scope — v1
[Explicit list of what we are NOT building yet]

## Tech Stack
| Layer | Choice | Reason |
|-------|--------|--------|
| ...   | ...    | ...    |

## Data Model
[Key entities and their relationships — prose or simple diagram]

## External Integrations
[APIs, services, third-party dependencies]

## Project Structure (proposed)
[Folder layout with annotations]

## Open Questions
[Anything that needs a decision before we can build it]
```

Then confirm with me that this architecture doc looks right before we do anything else.

---

Start now. Ask me your first question.
