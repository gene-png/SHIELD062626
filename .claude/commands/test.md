---
description: Run the suite, then produce the evidence block. A green suite is a precondition, never a result.
argument-hint: [specific test file or pattern, or blank for everything]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(bash .claude/hooks/*), Bash(git diff:*)
---

# /test

## What to run
$ARGUMENTS

---

Run the suite. Then do the part that matters.

## If tests fail

Fix the code, not the test.

**REFUSE** to reach green by deleting a test, skipping it, loosening an assertion, or
widening an expected value. If going green requires changing an existing test, stop and
show the test, what it asserts, and why it is wrong. That is a conversation, not an edit.

Watch for `.skip`, `.only`, `xit`, and a falling assertion count. Each is a green suite
bought by removing the thing that was checking.

## If tests pass

A green suite proves the tests you wrote pass. It says nothing about the ones you did not
write, and that is where the last four defects lived.

**Print the evidence block before reporting anything.** Three parts, all required.

### Part 1. What changed and what covers it

```
git diff --name-only main
```

For each changed source file, name the test file and title that exercises it **directly**.
Any changed file with no direct test is listed as `UNCOVERED`.

### Part 2. The empty case

For every changed function that produces user-facing output, run it with empty input and
**paste the output**. Absent must render as absent. A sensible default is a defect.

If nothing changed produces user-facing output, say so in one line.

### Part 3. One mutation

Take the most substantial change in the diff. Break it: flip a comparison, return a
constant, delete an input read. Run the suite. **Paste the failure.** Revert.

**REFUSE** to report a pass if the suite stays green under mutation. It means the suite
executes that code without checking it, which is what 650 tests did to `buildBriefRows`.

## Report

```
SUITE: <n> passed, <n> failed, <n> skipped
UNCOVERED: <files, or none>
EMPTY CASE: <pasted output, or not applicable>
MUTATION: <what was broken> -> <pasted failure>
```

Report the suite result last, and never on its own. A report with only a pass count is an
incomplete run.

## Not this

No coverage percentage, and no gate on one. Inozemtseva and Holmes (ICSE 2014, 31,000
suites) found the correlation with effectiveness disappears once suite size is
controlled. Read a coverage report to find untested files. Never quote the number as a
result.
