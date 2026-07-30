---
description: Start the product from a fresh empty state, drive it the way a customer would, save the artifact it produces, and assert on it.
argument-hint: [the journey to run, or blank for the primary one]
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(bash .claude/hooks/*), Bash(mkdir:*), Bash(ls:*), Bash(cat:*), Agent
---

# /smoke

## The journey
$ARGUMENTS

If blank, run the product's primary journey: the thing a paying customer does.

---

This command exists because David found four defects in thirty seconds by using the
product, against a suite of 650 passing tests. Nothing else in the command set ever
started the product as a customer. This does.

---

## The rules, and they are the whole command

**Fresh, empty state.** New session, new record, nothing seeded. If the product needs a
prior state to be interesting, reach it by performing the earlier steps, not by writing
the state.

**Public interactions only.** Click the control. Type in the box. Follow the redirect.
Use `getByRole` and `getByLabel`. **No CSS selectors, no direct state, no calling
internals, no seeding the database.** The admin bulk bar reported "2 selected" with
nothing selected, and that was invisible for 138 commits because the tests set selection
state instead of clicking a checkbox.

**REFUSE** to count a run that touched anything other than the public interface. If a
journey cannot be driven that way, that is a finding about the product, and you write it
down rather than working around it.

## The matrix

Run all six. Each one saves its artifact.

| # | Run |
|---|---|
| 1 | First use, fresh state, nothing supplied. The empty case |
| 2 | Partial input, then stop halfway |
| 3 | The first dependency call fails. Force it |
| 4 | Retry after that failure |
| 5 | Normal, complete, successful use |
| 6 | One input outside the known list |

Row 1 is the one that catches fabrication, and it is the run nobody ever did. David's
opening turn failed, he supplied nothing, and the brief described a complete project.

Run each row through the `hostile-user` subagent, one per row, in parallel. It has no
memory of the code being written and it reports what it saw as a customer rather than as
a test result. That separation is the point: Self-Correction Bench measured a 64.5 percent
blind spot for finding faults in your own output, so the reader has to be someone else.

## Save the artifact

Whatever the customer actually receives - the brief, the email, the export, the rendered
page - is written to:

```
docs/evidence/smoke/<YYYY-MM-DD>/<journey>-<case>.<ext>
```

**REFUSE** to report a pass without the files on disk. Print the paths.

## Assert on what you saved

For every saved artifact, both directions:

- **Every fact the customer supplied appears, correctly.**
- **No fact the customer did not supply appears at all.** Not a sensible default, not a
  placeholder that reads as content, not a plausible example. Absent renders as absent.

Then the contamination check: no other client's name, no other tenant's identifier, no
value that came from a fixture rather than this run.

Where you can, turn the assertion into a test that runs without you. Where you cannot,
read the artifact yourself and quote the line you checked.

## Report

```
JOURNEY: <name>
INTERFACE: public only / VIOLATED at <step>

| Case | Artifact | Supplied facts present | Unsupported facts | Result |
|------|----------|------------------------|-------------------|--------|
| empty | path | n/a | none / <quote> | PASS/FAIL |
| ...

FINDINGS: <what a customer would have seen>
needs-human: <anything that could not be driven or judged mechanically>
```

A `FAIL` on any row blocks the ship. An empty artifact column is an incomplete run.
