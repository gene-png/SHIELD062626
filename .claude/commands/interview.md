---
description: Start a project. Interview until the shape is clear, then produce the architecture, the risks, and the first spec. Absorbs the old /kickoff.
argument-hint: <the project idea>
allowed-tools: Read, Write, Edit, Grep, Glob, WebSearch
---

# /interview

## The idea
$ARGUMENTS

---

Ask questions one or two at a time and wait for answers. This is a conversation, not a
form. Follow what David says rather than the running order below when the two disagree.

## What to establish

**Who it is for, and what they do today instead.** If the answer is "nothing", either it
does not matter to them or you have not found the workaround yet.

**What the customer receives.** Screens they operate, or artifacts they read? This one
question decides the whole sequencing:

- Screens they operate: `/prototype` two or three rough alternatives first.
- Artifacts they read: draft a **sample deliverable** first, from their own material, and
  read it together. That is the artifact both parties can point at later, and for
  document-producing work it beats a mock, because content is what clients dispute.

**The three largest technical risks, ranked.** Shaped like "this data exists and is
clean" or "this integration permits what we need". The walking skeleton goes through the
top one.

**What must never happen.** The prohibitions. Every one of these becomes an executable
assertion later, so phrase each so it could be tested. "Never states a price" is testable.
"Feels professional" is not.

**Every closed list.** Any catalog, enum, allowlist or taxonomy the client rattles off.
For each, ask who owns it, where the truth lives, when it should be revisited, and what
happens for a value not on it.

**REFUSE** to record a closed list without those four. A three-item platform list written
on day one sat unchanged for 137 commits in this repo while the business sold four other
things, and nobody owned it because nobody was ever asked.

**Scale, budget shape, and the deadline that is real.** Fixed price changes what a wrong
assumption costs, so name the assumptions.

## Stop and check

When you believe you have enough, say so and summarise in ten lines. Ask whether anything
is missing or wrong. **REFUSE** to write the architecture until David has answered.

Self-judged sufficiency is the weak point of this command, and the summary is the thing
that fixes it.

## Then produce

1. **`ARCHITECTURE.md`** - the components, the data shape, the boundaries, what runs
   where, and the three ranked risks. Say what is decided and what is open. An open
   decision written down as open beats a page that reads as settled.

2. **`docs/specs/<first-slice>.md`** - run `/spec` on the thinnest useful slice.

3. **`CONTEXT.md`** - run `/snapshot`.

## Then say what comes next, and in this order

```
1. /prototype   (screens) or a sample deliverable (artifacts)
2. signed acceptance criteria
3. /skeleton    one slice through the real deploy
4. /sprint      the first real work unit
```

**REFUSE** to end this command with "you are now ready to build". Three documents exist
and nothing has been verified. Say what exists and what the next command is.
