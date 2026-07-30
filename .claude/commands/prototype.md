---
description: Produce two or three deliberately rough alternatives, shown together, to get honest client reaction before anything is built.
argument-hint: <what to prototype, and who it is for>
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(npm:*), Bash(npx:*)
---

# /prototype

## What to prototype
$ARGUMENTS

---

## Read this before starting, because the obvious version of this is wrong

One polished mock produces false agreement rather than agreement.

Tohidi, Buxton, Baecker and Sellen (CHI 2006) showed people a single design and then the
same design among three alternatives. Shown one, they rated it significantly higher and
gave significantly less negative feedback. Alternatives, in the authors' words, "gave
users license to be more critical."

Boehm, Gray and Seewaldt (1984), seven teams building the same application, found
prototyping produced roughly 45 percent less effort and rated higher on ease of use. The
same study found the prototyped products rated **lower on functionality and robustness**.
Both halves are real.

So the cheapness of generating a realistic frontend does not mean generate one realistic
frontend. It means generate three rough ones, which is what the evidence supports and
what used to be unaffordable.

## Before drawing anything

Write down the two or three most expensive assumptions in this project, the ones shaped
like "this data exists and is clean" or "this API permits what we need".

**REFUSE** to prototype a screen that sits on top of an unproven assumption. On fixed
price a wrong assumption costs the margin and a wrong layout costs an afternoon. Spike
the assumption first, or mark the screen as conditional in front of the client.

Then sketch the domain: eight to twelve entities with their fields and where each field
comes from. A screen showing a field nobody can supply is the classic UI-first failure.

## The rules

**Two or three alternatives, shown together.** Never one. They should differ in approach,
not in colour.

**Deliberately unpolished.** Rough type, no brand, no imagery, visible seams. Polish
suppresses criticism and it teaches the client the work is nearly finished.

**Fake data is labelled fake**, visibly, on every screen. A watermark, a banner, obvious
placeholder values. This one is specific to this business: the product that burned us
presented fabricated content convincingly, and a prototype full of plausible invented
data rehearses that habit in front of a client.

**Record what was rejected and why.** The rejections are scope evidence later, and they
are worth more than the choice.

## What this does not do

It does not lock scope. Scope is locked by written acceptance criteria and a change
process, which is what the scope-creep literature actually supports. The prototype is the
conversation. The signature is the protection.

Say this to the client out loud during the walkthrough: the visible part is the cheap
part. Otherwise the demo sets the schedule expectation and every later week reads as
stalling.

## After the walkthrough

Run `/spec` on what was agreed, and get the acceptance criteria signed. Then `/skeleton`.
The hi-fi frontend comes after the skeleton proves it can be backed, not before.

## Report

```
ALTERNATIVES: <n>, each in a sentence
SHOWN TOGETHER: yes
FAKE DATA LABELLED: yes
CHOSEN: <which, and the client's words for why>
REJECTED: <which, and why> <- keep this, it is scope evidence
ASSUMPTIONS STILL UNPROVEN: <list>
NEXT: /spec, then signed criteria, then /skeleton
```
