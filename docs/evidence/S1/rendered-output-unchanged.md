# S1 evidence — the refactor changes no rendered byte

Captured 2026-08-03T22:19:19Z by the loop driver, independently of the
runner. The tech-debt deliverable was rendered from a fixed context (pinned UUIDs, so
output is byte-stable) on the post-S1 tree, then again with `apps/api/app` checked out
at the pre-S1 commit `87c6df7`, and the two dumps diffed. The dump covers extracted
PDF text plus every XLSX cell's value, fill ARGB and bold flag.

The org name carries an ampersand on purpose: that is the character PR #50 hotfixed
and S1 moved into `escaped_title()`, so it is the likeliest thing to regress.

```
$ diff -u dump_before.txt dump_after.txt
IDENTICAL — no rendered text, fill or bold change
```

## The rendered output both trees produce

```
===== PDF TEXT =====
pages=1
--- page 0 ---
Technical Debt Review
Atlas Defense & Solutions
Summary
Capabilities reviewed: 3 · Total annual cost: $950,000 · Estimated annual savings: $120,000
Capability list
Name
Vendor
Category
Annual cost
Disposition
Wiz
Wiz, Inc.
CNAPP
$350,000
Keep
Lacework
Wiz, Inc.
CNAPP
$120,000
Cut
Splunk
Wiz, Inc.
SIEM
$480,000
Consolidate
===== XLSX CELLS =====
--- sheet Capability List dims=A1:J7 ---
A1	value='Name'	fill=FFEEF2F7	bold=True
B1	value='Vendor'	fill=FFEEF2F7	bold=True
C1	value='Category'	fill=FFEEF2F7	bold=True
D1	value='Function'	fill=FFEEF2F7	bold=True
E1	value='Annual Cost (USD)'	fill=FFEEF2F7	bold=True
F1	value='Licenses'	fill=FFEEF2F7	bold=True
G1	value='Disposition'	fill=FFEEF2F7	bold=True
H1	value='Rationale'	fill=FFEEF2F7	bold=True
I1	value='Notes'	fill=FFEEF2F7	bold=True
J1	value='AI Confidence %'	fill=FFEEF2F7	bold=True
A2	value='Wiz'	fill=00000000	bold=False
B2	value='Wiz, Inc.'	fill=00000000	bold=False
C2	value='CNAPP'	fill=00000000	bold=False
D2	value='Cloud posture'	fill=00000000	bold=False
E2	value=350000	fill=00000000	bold=False
F2	value=200	fill=00000000	bold=False
G2	value='Keep'	fill=00000000	bold=False
H2	value=None	fill=00000000	bold=False
I2	value=None	fill=00000000	bold=False
J2	value=92	fill=00000000	bold=False
A3	value='Lacework'	fill=00000000	bold=False
B3	value='Wiz, Inc.'	fill=00000000	bold=False
C3	value='CNAPP'	fill=00000000	bold=False
D3	value='Cloud posture'	fill=00000000	bold=False
E3	value=120000	fill=00000000	bold=False
F3	value=200	fill=00000000	bold=False
G3	value='Cut'	fill=00000000	bold=False
H3	value=None	fill=00000000	bold=False
I3	value=None	fill=00000000	bold=False
J3	value=92	fill=00000000	bold=False
A4	value='Splunk'	fill=00000000	bold=False
B4	value='Wiz, Inc.'	fill=00000000	bold=False
C4	value='SIEM'	fill=00000000	bold=False
D4	value='Cloud posture'	fill=00000000	bold=False
E4	value=480000	fill=00000000	bold=False
F4	value=200	fill=00000000	bold=False
G4	value='Consolidate'	fill=00000000	bold=False
H4	value=None	fill=00000000	bold=False
I4	value=None	fill=00000000	bold=False
J4	value=92	fill=00000000	bold=False
A5	value=None	fill=00000000	bold=False
B5	value=None	fill=00000000	bold=False
C5	value=None	fill=00000000	bold=False
D5	value=None	fill=00000000	bold=False
E5	value=None	fill=00000000	bold=False
F5	value=None	fill=00000000	bold=False
G5	value=None	fill=00000000	bold=False
H5	value=None	fill=00000000	bold=False
I5	value=None	fill=00000000	bold=False
J5	value=None	fill=00000000	bold=False
A6	value='Total annual cost'	fill=00000000	bold=True
B6	value=None	fill=00000000	bold=False
C6	value=None	fill=00000000	bold=False
D6	value=None	fill=00000000	bold=False
E6	value=950000	fill=00000000	bold=False
F6	value=None	fill=00000000	bold=False
G6	value=None	fill=00000000	bold=False
H6	value=None	fill=00000000	bold=False
I6	value=None	fill=00000000	bold=False
J6	value=None	fill=00000000	bold=False
A7	value='Estimated annual savings'	fill=00000000	bold=True
B7	value=None	fill=00000000	bold=False
C7	value=None	fill=00000000	bold=False
D7	value=None	fill=00000000	bold=False
E7	value=120000	fill=00000000	bold=False
F7	value=None	fill=00000000	bold=False
G7	value=None	fill=00000000	bold=False
H7	value=None	fill=00000000	bold=False
I7	value=None	fill=00000000	bold=False
J7	value=None	fill=00000000	bold=False
```

## A criterion that could not fail

S1's third acceptance criterion asks for `grep -c 'html.escape'` over the five
exporters to return 0. It returned 0 on the pre-S1 tree as well, for all five modules,
because PR #50 wrote `from html import escape` and called bare `escape(...)`:

```
$ git show 87c6df7:apps/api/app/attack/exporters.py | grep -n "import.*escape\|escape("
18:from html import escape
301:    story.append(Paragraph(escape(ctx.service_title), h1))
302:    story.append(Paragraph(escape(ctx.client_legal_name), body))
```

So the criterion as written was satisfied before any work started. The meaningful
check is bare `escape(` over the six modules, which now returns nothing:

```
$ grep -rn "escape(" app/{tech_debt,attack,csf,zt,risk}/exporters.py app/csf/playbook_export.py
exit=1  (no matches)
```
