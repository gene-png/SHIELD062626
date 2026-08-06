# S4 evidence — the race window, and the sparse render

Captured 2026-08-04T03:15:07Z by the loop driver.

## The race criterion, verified structurally rather than accepted

S4's race criterion is the only one in this batch that guards data integrity rather
than presentation, and it explicitly rejects the cheap proof: a discard arranged
_before_ the status check proves nothing about the window. So the injection point was
located in the code rather than taken from the runner's report.

The test patches `app.routes.zt.audit`. Line positions on both sides of the fix:

```
PRE-S4  (b53b6af:apps/api/app/routes/zt.py)
  :510  if current_status in (...)      <- the status check
  :524  audit(...)                      <- THE SEAM, inside the window
  :532  db.commit()                     <- the write lands

POST-S4 (apps/api/app/routes/zt.py)
  :584  audit(...)                      <- THE SEAM
  :596  _persist_run_ai_narratives(...) <- conditional UPDATE, predicate reads DISCARDED
  :603  db.commit()
```

In both shapes the seam sits strictly after the status observation and strictly before
the durable write, so the injected discard is inside the window the criterion names.

The runner reported the required RED run against the pre-fix shape: it returned **200**
with `"executive_summary":"Draft executive summary."` in the body — the old code
persisted narrative into a parent that had gone DISCARDED mid-window. After the fix it
returns a typed 409 `assessment_not_editable`.

The fix is D-031's shape, not a third mechanism:

```
UPDATE zt_assessments SET documents_stale, pillar_narratives, executive_summary,
       roadmap_summary WHERE id = :id AND status IN ('draft','submitted')
if result.rowcount != 1: log + raise HTTPException(409, assessment_not_editable)
```

The test also carries `assert fired, "the discard hook never fired — the seam moved out
of the window"`, so it cannot silently stop biting if that call is later moved.

**One honest limitation, the runner's own disclosure.** The injection is emitted SQL on
the request's session, not a second connection: under SQLite the request already holds a
RESERVED write lock at that point, so a genuine second connection cannot commit there.
The criterion asks for a monkeypatch, and what it tests — the predicate guarding the
write observing DISCARDED — is exercised faithfully. The old shape fails it, the new one
passes.

## Sparse and empty render, re-run by the driver

S3 shipped a false reassurance that fired on zero gaps regardless of coverage. The same
shape existed three times in `zt/exporters.py` and the runner fixed all three, none of
which any criterion covered. Verified independently:

```

--- nothing scored (0/37), no narratives · gaps=0 ---
  > Maturity summary
  > Overall stage: Unscored · Average stage: — · Coverage: 0/37 (0.0%)
  > Top remediation gaps (target S3)
  > No capability in this assessment has been scored, so no gap to target stage 3 (Advanced) can be identified. This is
  > an absence of data, not an absence of gaps.
  > Remediation roadmap (12 months)
  > No capability has been scored, so there is nothing to sequence. This roadmap is empty for want of input, not
[PASS] empty: no bare no-gaps assertion
[PASS] empty: attributes the emptiness to missing data
[PASS] empty: no Assessment narrative header
[PASS] empty: no Consultant summary header

--- sparse (3/37 at stage 4, target 3) · gaps=0 ---
  > Maturity summary
  > Overall stage: Optimal · Average stage: 4.00 · Coverage: 3/37 (8.1%)
  > are unscored and are excluded from every average on this page, so no stage here describes them.
  > Top remediation gaps (target S3)
  > No gap to target stage 3 (Advanced) among the 3 of 37 capabilities scored. The remaining 34 are unscored and this
  > Remediation roadmap (12 months)
  > Nothing to sequence: none of the 3 of 37 capabilities scored sits below its target stage. The 34 unscored capabilities
[PASS] sparse: genuinely the zero-gap branch :: gaps=0
[PASS] sparse: states its own coverage
[PASS] sparse: names the unscored remainder
[PASS] sparse: no bare no-gaps assertion

--- narratives persisted ---
[PASS] persisted: Assessment narrative renders
[PASS] persisted: Consultant summary renders

ZT SPARSE RESULT: CLEAN
```

## What this hands the CSF open item

The ZT headline also reads `Overall stage: Optimal` at 8.1% coverage, but it follows
with a sentence stating the unscored capabilities are excluded from every average "so no
stage here describes them". CSF's `Overall maturity: Repeatable` at 2.8% coverage has no
such qualifier. The remedy for that open item therefore already exists one service over
and is a copy of an established pattern rather than a new decision.
