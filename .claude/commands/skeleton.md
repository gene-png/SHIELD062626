---
description: Build the walking skeleton. One thin slice through the real production toolchain before any feature work.
argument-hint: <the project or the slice to build>
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(npm:*), Bash(npx:*), Bash(git:*), Bash(gh:*)
---

# /skeleton

## The project
$ARGUMENTS

---

The thinnest slice of real functionality that can be built, deployed and tested end to
end, linking every architectural component that matters. Cockburn's walking skeleton.
Hunt and Thomas call the same thing a tracer bullet.

It looks like no progress and it retires architecture, integration and deployment risk at
once, which is the risk that costs the most on fixed price and shows up latest.

**This is production code, not a prototype.** It is not thrown away. Brooks withdrew
"plan to throw one away" in the 1995 edition and endorsed incremental build instead:
grow, do not build.

## What the slice must touch

Every one of these, however trivially:

- Real authentication, even if one user with one role
- One real request that reaches the real backend
- One real write to the real database, with the real access rules on
- One real render of what was written
- The real deployment pipeline, to a real URL, from a commit

If any of those is faked, the skeleton has not done its job, because the fake is where
the risk was hiding.

## What it must not include

Features. Styling beyond legibility. Error handling beyond failing loudly. Any second
case of anything.

**REFUSE** to add a feature during this command. The value comes from the slice being
thin. A skeleton that grows a feature is an ordinary first sprint with a grander name.

## The order

1. Name the three largest technical risks in the project, ranked. The slice goes through
   the top one.
2. Deploy an empty page through the real pipeline first, before writing anything. Prove
   the pipeline before proving the code.
3. Add auth. Deploy.
4. Add the write. Deploy.
5. Add the read and render. Deploy.
6. Add one test that drives the whole slice through the public interface.

Deploying between each is the point. A pipeline that works four times is known to work.

## Report

```
SLICE: <what it does, one sentence>
URL: <the live one>
TOUCHED: auth <how> | request <where> | write <table> | render <page> | deploy <pipeline>
RISKS RETIRED: <which of the three, and what you learned>
RISKS REMAINING: <the ones the slice did not touch>
FAKED: <anything, and why> or nothing
```

Anything in `FAKED` is a risk still live. Say so plainly rather than counting the
skeleton as complete.
