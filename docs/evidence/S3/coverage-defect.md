# S3 evidence — the coverage defect the empty-input run caught

Captured 2026-08-04T00:47:54Z by the loop driver.

## What the first S3 commit shipped

`19a1fe6` passed its own gate and all fourteen of its new tests. Rendering the CSF
deliverable with only 3 of 106 subcategories scored, all at target T3, produced:

```
Overall maturity: Repeatable · Average tier: 3.00 · Coverage: 3/106 (2.8%)
Action plan (0 of 0 gaps shown)
No subcategory scored below target T3 (Repeatable) — maintain the current controls
and re-assess on the next cycle.
```

A report covering 2.8% of the framework advised the client to maintain their current
controls. Narrowly true — no _scored_ subcategory fell below target — but the
actionable line reads as a finding of adequacy across 103 subcategories that were
never assessed. `analyze_gaps` raises a gap only for an ANSWERED subcategory below
target, so 0/106 and 106/106 both yield zero gaps and hit the same branch.

The tests missed it because every zero-gap case they exercised used a FULLY scored
assessment. The branch was correct for the only input it was ever given.

## After the fix (`d3864f3`), all three branches re-rendered by the driver

```

--- nothing scored: answered=0 gaps=0 ---
[PASS] nothing scored: gap count is 0 (this is the zero-gap branch) :: gaps=0
[PASS] nothing scored: adequacy claim ABSENT as required :: 'maintain the current controls' present=False
[PASS] nothing scored: states no maturity finding
[PASS] nothing scored: names all 106 as unassessed

--- partial 3/106: answered=3 gaps=0 ---
[PASS] partial 3/106: gap count is 0 (this is the zero-gap branch) :: gaps=0
[PASS] partial 3/106: adequacy claim ABSENT as required :: 'maintain the current controls' present=False
[PASS] partial: names the unscored count
[PASS] partial: scopes the finding to scored subcategories only

--- full 106/106: answered=106 gaps=0 ---
[PASS] full 106/106: gap count is 0 (this is the zero-gap branch) :: gaps=0
[PASS] full 106/106: adequacy claim present as earned :: 'maintain the current controls' present=True

THREE-BRANCH RESULT: CLEAN
```

Each case asserts `total_gap_count == 0` first, so all three genuinely traverse the
zero-gap branch: the fix narrowed it rather than routing around it. The adequacy claim
now appears only at full coverage, where it is earned.

## Why this is recorded rather than just fixed

A green gate, fourteen passing tests, and a runner that had already caught three weak
criteria on its own still produced a client-facing false reassurance. The only thing
that surfaced it was rendering the artifact with data missing. That is the argument for
the empty-input run being mandatory rather than discretionary, and it is why a gate is
a precondition and never a pass.

## Adjacent, not fixed, needs a human

The same render headlines **`Overall maturity: Repeatable`** on 2.8% coverage. The
coverage figure sits beside it, so it is not a lie, but a headline maturity rating
computed from 3 of 106 answers is the same class of problem one layer up. It predates
S3 and no criterion covers it. Whether a coverage floor should gate the headline rating
is a product decision.
