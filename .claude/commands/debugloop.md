---
description: Reproduce a defect through the public interface, keep the reproduction as a regression test, then fix it.
argument-hint: <the defect, or blank to audit recent work for defects>
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(bash .claude/hooks/*), Bash(echo:*), Bash(rm:*), Bash(git diff:*), Agent
---

# /debugloop

## The defect
$ARGUMENTS

---

## The sequence, and the order is the command

### 1. Reproduce through the public interface, before reading the code

Click the control. Type the input. Call the exported function with the arguments a caller
would use. **Paste what happened.**

**REFUSE** to start fixing before a reproduction exists. A defect you cannot reproduce is
a hypothesis, and hypotheses get fixed by changing code until the symptom moves, which is
how a second defect gets added to the first.

**REFUSE** to reproduce by setting internal state, calling a private helper, or seeding
the database. If the defect will not appear through the public interface, say so plainly.
That is a finding: either the defect is not what you think, or the interface hides it.

### 2. Turn the reproduction into a failing test

Before any fix. The test asserts the behaviour a user should have seen, not the behaviour
the code currently produces.

```
echo spec > .claude/state/phase
```

Paste the red run.

### 3. Fix it

```
echo implement > .claude/state/phase
```

Test files are locked by the hook while you do this. Fix the cause, not the symptom. If
the fix needs the test changed, the test was wrong: stop and say so.

### 4. Paste the green run, then mutate

Break the fix on purpose. Confirm the new test goes red. Revert. Paste it.

### 5. Ask what class this belongs to

One question, and it is the difference between fixing a bug and fixing a kind of bug:

**Where else does this same mistake live?** Grep for the pattern. A hardcoded value in
one renderer is usually in three. The contamination scan that caught the client name
immediately found a second copy nobody knew about.

List what you found, and either fix each or write it down as `needs-human`.

### 6. Clear the phase

```
rm -f .claude/state/phase
```

---

## When run with no argument

Do not sweep the whole codebase. Take the diff since the last commit and ask four
questions of it, each in its own fresh subagent so none of them is defending work it did:

1. Which changed function produces customer-visible output, and what does it do with
   empty input?
2. Which changed function has no direct test?
3. Which changed `catch` swallows its error?
4. Which changed value is hardcoded that should have come from an input?

Each subagent returns findings with file and line, or `none found` **above a list of the
files it inspected**. A bare `none found` is not a result, it is a shrug.

## Report

```
DEFECT: <what a user saw>
REPRODUCED: <pasted, via public interface>
REGRESSION TEST: <file>::<title>, red then green, both pasted
MUTATION: <break> -> <pasted failure>
CLASS: <where else this pattern lives> or <searched <n> files, this is the only one>
needs-human: <anything left>
```
