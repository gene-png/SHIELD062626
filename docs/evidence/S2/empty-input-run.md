# S2 evidence — the empty-input run

Captured 2026-08-03T23:11:44Z by the loop driver. S2 changes a
customer-visible artifact, so the loop protocol requires proving it in both
directions: every supplied fact present, and **no unsupported fact present**. The
second is what an empty input catches. A document handed nothing must claim nothing.

The ATT&CK deliverable was rendered for an approved assessment in which every one of
the 633 techniques is unscored and nothing has been curated: no tools, no rationale,
no evidence artifacts.

## Assertions

```
[PASS] invents no tool name: 'Okta'
[PASS] invents no tool name: 'CrowdStrike'
[PASS] invents no tool name: 'Splunk'
[PASS] invents no tool name: 'Wiz'
[PASS] invents no tool name: 'Defender'
[PASS] invents no tool name: 'Sentinel'
[PASS] citation stat present :: 0 of 0 scored techniques cite at least one tool
[PASS] citation numerator is 0 :: numerator=0
[PASS] every evidence cell is the explicit empty state :: 633 cells, distinct=['No evidence attached']
[FAIL] no causal/remediation vocabulary in rendered prose :: hits=['remediat', 'should']
EMPTY-INPUT RESULT: 1 FAILURE(S): ['no causal/remediation vocabulary in rendered prose']
```

Nine of ten pass outright. The document invents no tool name, reports an honest
`0 of 0 scored techniques cite at least one tool`, and fills all 633 evidence cells
with the explicit `No evidence attached` empty state rather than leaving them blank
or guessing.

## The one failure, and what it is

The vocabulary scan flagged two words. One is a false positive of a crude check:

> ... so no field here **should** be read as verified.

That is a disclaimer, the opposite of a claim. The other is real:

```
121:Top remediation gaps (0 of 0 shown)
136:Top remediation gaps (0 of 0 shown)
```

`Top remediation gaps` is inherited from Work Order C4, predates S2, and sits at
`app/attack/exporters.py:435` (DOCX) and `:540` (PDF). It is a section heading, not a
Gap Direction cell, so it falls outside S2's criteria — but it frames gaps as
remediation targets directly above cells that D-035 forbids from doing exactly that.
The empty-input render makes it starker: the heading reads `Top remediation gaps
(0 of 0 shown)` on a report that has scored nothing.

The S2 runner found this, declined to change client-visible copy outside its stated
criteria, and recorded it in D-035. That call is right. It needs a human decision,
not a driver one, and it is carried in the plan Log as an open item.

## The two strings the Gap Direction column can emit

```
No detection, prevention, or response tool is cited for this technique
Cited: <comma-joined distinct tools> (partial)
```

Verified as the only two returns of `gap_direction()` by reading the function, not
by trusting the report.
