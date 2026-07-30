---
description: Fresh-subagent review of the diff against the spec. Traces every customer-visible fact to its input and its test. A FAIL blocks the commit.
argument-hint: [what to review, or blank for the working diff]
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git status:*), Bash(git log:*), Agent
---

# /review

## What to review
$ARGUMENTS

If blank, review the working diff against `main`.

---

## This runs in a subagent, and that is not a style choice

Self-Correction Bench (arXiv:2507.02778) measured a 64.5 percent average self-correction
blind spot across 14 models: they reliably fix errors handed to them as external input
that they cannot find in their own output. On multi-step reasoning it reaches 79.2
percent.

So: **spawn a subagent and give it the diff and the criteria and nothing else.** No
conversation history, no memory of having written the code, no account of what you were
trying to do. If you review your own work in your own context, this command has not run.

Keep the diff under 400 lines per reviewer. Detection drops sharply above that
(SmartBear's Cisco study, 2,500 reviews). Split it and spawn more.

---

## What each reviewer is asked

### 1. Provenance of every customer-visible fact

For each string, number, name or claim that reaches a customer:

- Which input does it come from?
- What happens when that input is absent?
- Which test asserts it?

**FAIL** any fact with no input behind it. Unconditional prose in a generated document is
the defect that put another client's name into every brief this tool ever produced.

### 2. Tests that can fail

List every new or changed exported function. Beside each:

- the test file and test title that calls it **directly**, and
- one expected value from that test that appears **nowhere in the implementation source**.

**FAIL** on a function with no direct test, or on a test whose every expected value can be
found in the code it is testing. A test that executes a function while asserting on
something else is not coverage of that function.

### 3. Fail loudly

- Any `catch` that does not rethrow or surface. Quote it.
- Any fallback return that hides a failure.
- Any default value standing in for a missing input in customer-visible output.

GitClear's 2026 corpus of 600 million commits shows error-masking catch blocks up 47
percent in AI-assisted code, so look for this one hard.

### 4. Contamination

Any client name, tenant identifier, or customer-specific string in shared code, prompts,
or knowledge files. Grep, do not skim.

### 5. Closed lists

Any allowlist, enum or catalog touched by this diff. Does it have an owner, a source, a
review date, and defined behaviour for the unknown case?

### 6. Scope

Compare the diff to the spec. Name anything changed that no criterion asked for.

---

## Output

```
REVIEW of <n> changed files, <n> lines

| Check | Result | Evidence |
|-------|--------|----------|
| Provenance | PASS/FAIL | <fact> <- <input> <- <test> |
| Tests that can fail | PASS/FAIL | <function> <- <test>: "<quoted expectation>" |
| Fail loudly | PASS/FAIL | <file:line> |
| Contamination | PASS/FAIL | <grep result> |
| Closed lists | PASS/FAIL | <list>: owner, reviewed <date> |
| Scope | PASS/FAIL | <out-of-scope change> |

BLOCKING: <the FAILs, or none>
```

## The refusal

**A FAIL on provenance, tests, or contamination blocks the commit.** Fix the cause, rerun
this command, and put both outputs in the session. Do not classify a failure as minor and
carry on. If you are unsure which side something falls on, it blocks.

**REFUSE** to approve when a customer-visible fact has no provenance, whatever else in
the diff is clean.

## What this command is not for

Style, naming, and structure. Bacchelli and Bird (ICSE 2013) found human review yields
fewer defect findings than developers expect, with most of its value in knowledge
transfer, and there is nobody here to transfer knowledge to. So this command only does
the mechanical checks above. Aesthetics go to `/refactor`.
