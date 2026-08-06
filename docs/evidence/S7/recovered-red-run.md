# S7 evidence — a recovered red run, and a scope line with no criterion

Captured 2026-08-04T06:39:57Z by the loop driver.

## The TDD violation, and what was done about it

The runner disclosed, unprompted, that for the playbook-legend criterion it wrote the
component before its test, so no red run was observed. `CLAUDE.md` principle 3 requires
test-first with an observed failure. The other three criteria did have observed reds.

An observed red cannot be recovered retroactively — you cannot un-write code. What can be
recovered is the property the red run exists to establish: that the test fails without the
implementation. So the driver reverted `CsfPlaybookPanel.tsx` to its pre-S7 state and ran
its suite:

```
$ git checkout b250c4c -- apps/web/src/components/admin/csf/CsfPlaybookPanel.tsx
$ pnpm -F web test -- CsfPlaybookPanel

 Test Files  1 failed (1)
      Tests  2 failed | 2 passed (4)
```

The tests cannot pass without S7's implementation. **Being precise about how strong that
is:** one failure is an assertion on the rendered legend, the other is
`gapPriorityMeaning is not a function` — an import-level failure rather than a render
assertion. Part of what fails is the module surface rather than the behaviour, which is a
slightly weaker signal than a genuine test-first red would have given. It is recorded as a
recovered check, not as an observed red run, because those are not the same thing.

The runner's disclosure is the reason this could be checked at all. A runner that quietly
reordered its narrative would have produced an identical-looking green sprint.

## Unmapped statuses fail loudly rather than defaulting

The step strip claims to say where an engagement stands, so a status it does not
understand must not quietly render step 1. `currentStepNumber` raises:

```
[WorkflowSteps] service "csf" defines no step for status "quantum_reviewed",
so the strip cannot say where the engagement stands
```

One test per service covers it, and the expectation type is `Record<Status, number>`, so
**tsc** rejects a new wire status until it is mapped in both the test and the component.
The same discipline covers the home legend (`phaseFor` returns one of five shared objects,
so a label without a legend entry is structurally impossible) and the Gap chips (the
legend renders from the same map that colours the chips, and raises on a missing reading).

## Pickers and known defects untouched

```
$ git diff --name-only b250c4c..HEAD | grep -E "TierPicker|ZtStagePicker|ZtSelfAssessment"
exit=1  (no matches)
```

The bare `catch {}` on the client answer PATCH is byte-identical, still at
`CsfSelfAssessment.tsx:173`, despite S7 working inside that file. Third sprint in a row
to be in or beside it and leave it, deliberately: fixing it means choosing what a client
sees when a save fails, which is a product decision.

## A scope line with no criterion

`/admin/management` is named in S7's Scope line but carries no acceptance criterion and
no evidence clause anywhere in the plan. The runner left it untouched rather than
inventing work, which was right — a runner guessing at unscoped work is how a sprint
sprawls past its declared file set. Either it needs a criterion in a later sprint or that
scope line is stale from an earlier draft.
