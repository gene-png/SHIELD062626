# S5 evidence — the pin, the cycles, and thin data

Captured 2026-08-04T04:37:17Z by the loop driver.

## The one pin allowed to move, diffed

S5 is the only task permitted to change an existing e2e assertion, and only as
alignment. Loosening it — equality to substring, literal to permissive regex — would be
the quiet way to make this sprint look clean, so the line was diffed rather than taken
on report:

```diff
-    page.getByText(/Fixture-mode draft coverage assessment for T1001/),
+    page.getByText(/Fixture-mode draft coverage evidence for T1001/),
```

Same matcher, same `toBeVisible()`, one word changed in the literal. Across all of S5,
the only lines removed from any test or spec are that pin and one widened import:

```
$ git diff -U0 2861df0..HEAD -- apps/api/tests e2e | grep "^-[^-]"
-from app.tech_debt.exporters import build_context, render_pdf, render_xlsx
-    page.getByText(/Fixture-mode draft coverage assessment for T1001/),
```

## The frozen cycles did not move

`docs/SPRINTS.md` calls these the batch's e2e landmine. `_MITRE_STATUS_CYCLE` is
byte-identical at `fixtures.py:98`, and no cycle tuple or arithmetic line was removed or
modified — the only diff lines mentioning `max_stage` are additions inside new narrative
functions:

```
98:_MITRE_STATUS_CYCLE = ("covered", "partial", "gap", "covered", "not_applicable")
```

The runner also ran a mutation check: moving cycle position 4 to `partial` turns the
pin red, so the pin bites rather than merely existing.

## Idempotency is now observable, which it was not

The criterion asked for two runs' row counts "captured in the log line", but no such log
line existed and the skip path printed no counts at all — the criterion was
unevidenceable as written. `_print_row_census` now runs on **both** paths
(`seed_demo.py:1369` skip, `:1420` seed), counting 14 quantities including per-field
evidence coverage, so a duplicating second run is visible.

## S5's portfolio paragraph under thin data

Three sprints running, this batch has produced the same defect: a sentence asserting a
finding on data nobody supplied. A paragraph reporting disposition counts, cost drivers
and a savings figure is the same shape of risk, so it was rendered four ways.

```
=== S5's PORTFOLIO PARAGRAPH under thin data ===

[empty list]
  paragraph: No capabilities are recorded on this list, so there is no portfolio to summarize, no cost drivers to rank, and no savings to estimate.
  (pre-existing header: Capabilities reviewed: 0 · Total annual cost: $0 · Estimated annual savings: $0)
[PASS] empty: states there is nothing to summarize
[PASS] empty: paragraph prints no dollar figure :: money=[]

[2 rows, no costs, one Cut]
  paragraph: Of the 2 capabilities reviewed, 1 Keep, 0 Consolidate and 1 Cut. No annual cost is recorded on any row, so no cost drivers can be ranked and no savings can be estimated. 1 row marked Cut carries no annual cost, so no savings figure can be computed from this list.
  (pre-existing header: Capabilities reviewed: 2 · Total annual cost: $0 · Estimated annual savings: ≥ $0)
[PASS] uncosted: says no cost is recorded
[PASS] uncosted: refuses a savings figure
[PASS] uncosted: paragraph prints no dollar figure :: money=[]

[2 costed rows, no dispositions]
  paragraph: None of the 2 capabilities carries a disposition yet, so this list records the inventory only and no keep, consolidate or cut split can be reported. The 2 rows carrying a cost total $830,000 a year; the largest are Splunk ($480,000), Wiz ($350,000). No row is marked Cut, so no annual savings are claimed.
[PASS] undecided: no keep/consolidate/cut split claimed
[PASS] undecided: claims no savings
[PASS] undecided: reports the honest recorded total

[mixed: one Cut costed, one Cut uncosted]
  paragraph: Of the 3 capabilities reviewed, 1 Keep, 0 Consolidate and 2 Cut. The 2 rows carrying a cost total $470,000 a year, and 1 of the 3 rows carries no cost, so that total is a floor; the largest are Wiz ($350,000), Lacework ($120,000). Cutting the 2 rows marked Cut removes at least $120,000 of annual spend; 1 Cut row carries no cost, so the figure is a lower bound.
[PASS] mixed: savings framed as a lower bound
[PASS] mixed: reports the costed savings honestly

THIN-DATA RESULT: CLEAN
```

S5's paragraph is clean in every case: each absent input produces an explicit statement
of absence, and no dollar figure is printed unless a Cut row carries a recorded cost.
The pre-existing lower-bound caveat survives.

## The pattern this run keeps finding, now at the header layer

A first pass flagged `$0` in the **pre-existing Summary header** rather than in S5's
paragraph. Rescoping cleared S5 — but the header itself is the same defect one layer up,
and this is now the third service where it appears:

| Service   | Header on thin data                                            | Qualified                            |
| --------- | -------------------------------------------------------------- | ------------------------------------ |
| ZT        | `Overall stage: Optimal` at 8.1% coverage                      | **yes**, S4 added it                 |
| CSF       | `Overall maturity: Repeatable` at 2.8% coverage                | no                                   |
| Tech-debt | `Total annual cost: $0` with 2 rows whose cost is _unrecorded_ | paragraph mitigates, number does not |

The tech-debt case is the plainest: `$0` asserts zero where the truth is "not
recorded". S5's new paragraph directly beneath says `No annual cost is recorded on any
row`, so the document as a whole is honest and the header alone is not. One root cause,
found by three independent empty-input runs, with the fix pattern already present in ZT.
It wants one consistent treatment of absent-versus-zero across all four services.

## An operational gap S9 will hit

The seed's guard is "skip if any Service exists", so the **live demo database still
carries the old ATT&CK evidence** — the runner measured `zt_narrated=0` against
`services=37` there. Only a `demo-reset --demo` or a wipe picks up the new seed, and
that path is destructive and opt-in by D-033. S9's criteria assume the evidence-rich
seed is live, so somebody has to run that reset deliberately before S9's suite.
