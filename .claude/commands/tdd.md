---
description: One test-first cycle with an observed red run, a counterexample fixture, and a mutation check before it counts as done.
argument-hint: <the behaviour to build, or the spec file to build from>
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(bash .claude/hooks/*), Bash(echo:*), Bash(rm:*), Bash(git diff:*)
---

# /tdd

## What to build
$ARGUMENTS

---

Test-first ordering has weaker evidence behind it than its advocates claim. Fucci's
industrial experiment with 24 professionals found no significant difference in external
quality from the ordering alone. The rule survives here for a better reason: **an
observed red run is the only proof that the assertion existed before the code that could
have authored it.** Everything below serves that one purpose.

The phase marker at `.claude/state/phase` is enforced by a hook, not by good intentions.
During `implement` you cannot edit a test file.

---

## 1. Find the source of the expectation

Read the spec in `docs/specs/` if one exists. If none does, write down in one sentence
where the expected behaviour comes from: the requirement, a boundary rule, a client's
words.

**REFUSE** to proceed on "what the function should obviously do". That is the
implementation talking.

## 2. Enter the spec phase

```
echo spec > .claude/state/phase
```

Source files are now locked. Tests and documents stay writable.

## 3. Write the test

Rules, all of them mechanical:

- Every expected value carries a comment naming its source: the spec line, the boundary
  rule, or the counterexample it encodes.
- **Never paste actual output into an expected value.** If you ran the code to learn what
  to expect, you have written a snapshot wearing a test's clothes.
- Fixture data differs on purpose from any constant the implementation will contain. Say
  in the file header which values differ and from what.
- Include the empty-input case. For anything producing user-facing output, include an
  assertion that no fact absent from the input appears in the output.
- Assert through the public interface. Setting internal state directly does not count.

## 4. Run it and paste the failure

Run the suite. **Paste the failing output verbatim, including the assertion message.**

That pasted failure is your licence to write implementation code. Without it in the
session, write none.

**REFUSE** on either of these:
- The test passes on its first run. Delete it, say so, and write a different test. A test
  whose first recorded run is green does not count toward this work.
- The test fails on an import or syntax error rather than a missing behaviour. That is a
  broken file, not a red run.

## 5. Enter the implement phase

```
echo implement > .claude/state/phase
```

Test files are now locked by the hook. If the test turns out to be wrong, stop and say
so rather than editing it: state what the test asserts, what the requirement says, and
which one is mistaken. Only then switch to `fix`.

## 6. Write the minimum that passes

No speculative generality, no defensive abstraction. Errors throw rather than returning a
fallback that hides them. Assert the preconditions you rely on with `invariant()`, which
throws in every environment including production.

## 7. Run it and paste the pass

## 8. Mutate, and watch it go red

Break the code on purpose: flip a comparison, delete a line, return a constant where a
derived value belongs. Run the test. **Paste the failure.** Revert.

Thirty seconds, and it is the only mechanical way to tell a test that protects behaviour
from one that mirrors the implementation.

**REFUSE** to report this cycle complete if the mutation leaves the suite green. A test
that stays green when the code is broken asserts nothing, whatever its name says.

## 9. Clear the phase

```
rm -f .claude/state/phase
```

---

## Report

Five things, and nothing else:

1. The source of the expectation, quoted.
2. The pasted red run.
3. The pasted green run.
4. The mutation applied and the pasted failure it caused.
5. Anything that could not be tested this way, written as `needs-human: <reason>`.

A report missing item 2 or item 4 is an incomplete cycle, not a finished one.
