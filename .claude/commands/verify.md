---
description: Take acceptance criteria and produce an evidence table. Every criterion gets a proof, or it gets marked needs-human. Never a tick.
argument-hint: <path to the spec or sprint whose criteria to verify>
allowed-tools: Read, Write, Grep, Glob, Bash(bash .claude/hooks/*), Bash(cat:*), Bash(ls:*), Agent
---

# /verify

## What to verify
$ARGUMENTS

---

This is the command the old set did not have, and its absence is why forty-five sprints
were marked done while the product was broken. An agent with only `done` and `blocked`
available will round an unverifiable criterion to `done`, because `blocked` stops the
work and `done` does not. The third state costs nothing and stops the rounding.

---

## What counts as evidence

Exactly three things. Nothing else is admissible.

1. **A pasted command output.** Not the exit code. The output.
2. **An artifact produced through the public interface this session**, saved to disk,
   with the path given and the relevant line quoted.
3. **A named test with its assertion quoted**, where the assertion is on the value the
   criterion is about.

What is **not** evidence, and this list is closed:

- An exit code. It proves the command ran.
- A test count. 650 tests concealed a critical path with none.
- A coverage percentage. Two large studies found the number does not predict defects.
- A green suite. It proves the tests you wrote pass, and says nothing about the ones you
  did not write.
- Your own summary of having checked.

## The procedure

1. Read the criteria from the spec or sprint file. List them, numbered, verbatim.

2. For each criterion, gather evidence of one of the three admissible kinds. Run what
   needs running. Read what needs reading.

3. Fill the table. One row per criterion, no row left out.

```
| # | Criterion (verbatim) | Evidence kind | Evidence | Result |
|---|----------------------|---------------|----------|--------|
```

`Result` is `MET`, `NOT MET`, or `needs-human`.

4. **REFUSE** to complete with an empty evidence cell. A criterion whose evidence you
   cannot produce is written `needs-human: <the specific thing a person must check>`, and
   it stays unchecked in the tracker.

5. **REFUSE** to mark a criterion `MET` on the strength of a criterion that is not this
   one. Each row stands alone.

## When a criterion cannot be phrased for evidence

Say so, and say why, and treat it as a defect in the specification rather than a problem
with this command. Then rewrite the criterion in `/spec` terms: an outcome a person could
observe. "The interview feels natural" becomes `needs-human`. "The interview never states
a price" becomes a test.

## Report

The table, then three counts: met, not met, needs-human.

Then one line, and it is the only conclusion this command is allowed to draw:

- All criteria `MET`, none `needs-human`: **verified**.
- Any `needs-human`: **verified except <n> items requiring a person**, listed.
- Any `NOT MET`: **not verified**.

There is no fourth outcome and no rounding between them.
