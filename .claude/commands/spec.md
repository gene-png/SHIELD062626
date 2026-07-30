---
description: Turn a requirement into written invariants and acceptance criteria, each with a negative case. Produces the document every later command checks against.
argument-hint: <the requirement, feature or sprint to specify>
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git diff:*), Bash(git log:*)
---

# /spec

Write the specification before the test, so the test has a source other than the
implementation. This replaces the old `/feature` and `/planfunction`.

## What to specify
$ARGUMENTS

---

## Step 1. Restate the requirement in the client's or the business's words

Quote the source: the sprint line, the client's message, the wiki page. If no source
exists, say so and write down who decided this and when.

**REFUSE** to continue if the requirement cannot be traced to something outside your own
reasoning. Write `needs-human: no source for this requirement` and stop.

## Step 2. Write the invariants

An invariant is a statement that must be true of every run, phrased so it can be checked
without knowing the algorithm. Aim for three to six. Examples of the shape:

- The output never contains a figure preceded by a currency symbol.
- Every proper noun in the document appears somewhere in the captured facts.
- Given no input, the function produces an explicit unknown state and never a default.
- `parse(render(x))` equals `x` for every `x` the renderer accepts.

For each invariant, write the sentence and then the assertion that would test it. If you
cannot write the assertion, the invariant is too vague. Rewrite it.

## Step 3. Write the journey matrix

Every specification covers these rows. Mark a row `not applicable` only with a reason.

| Case | What happens | Observable outcome |
|---|---|---|
| Fresh state, first use | | |
| Empty input | | |
| Partial input | | |
| The first dependency call fails | | |
| Retry after that failure | | |
| Success | | |
| An input outside the known list | | |

The empty-input row is the one that matters most. One assertion on it would have caught
the worst defect this repo has produced. **Empty input must produce an explicit unknown
state or fail loudly. It must never produce an invented fact.**

## Step 4. Write the acceptance criteria

Each criterion names an outcome a person could observe, and how it will be evidenced.

**REFUSE** to write a criterion whose text is a command run, a file changed, a test
passing, or a count of anything. "The suite is green" is not a criterion. "A brief
generated from an interview with no answers shows every field as not captured" is.

Each criterion gets an evidence plan from this list, chosen now rather than later:
- a named test with an assertion on the value in question
- an artifact produced through the public interface and inspected
- `needs-human`, with the reason it cannot be automated

## Step 5. Register the closed lists

List every allowlist, enum, catalog, taxonomy or knowledge file this work reads or
writes. For each: the owner, the source of truth, the review date, and what happens for
a value not on the list.

**REFUSE** to leave a closed list without defined unknown-case behaviour. A three-item
platform list with no owner sat unchanged in this repo for 137 commits while the business
sold four other things.

## Step 6. Name the counterexample fixtures

For each invariant, name a fixture value that **differs on purpose** from any constant
the implementation is likely to contain. Write the differing values down here.

This is the sharpest rule in the set and it is the one that failed before: the brief
tests used a client whose real reference matched the hardcoded string, so the bug looked
correct for 138 commits. A fixture that matches a hardcoded value is a coincidence that
looks like evidence.

---

## Output

Write the whole thing to `docs/specs/<kebab-name>.md` with a date and a one-line summary
at the top. Print the path.

Then print the three numbers a later command will check against: how many invariants,
how many acceptance criteria, and how many criteria are already marked `needs-human`.

## What this command must never do

Propose an implementation, name a file to create, or sketch a function signature. The
specification is written so the test can come from somewhere other than the code. If it
describes the code, it has failed at the only job it has.
