# S8 evidence — a second phantom token, and a badge that cannot discriminate

Captured 2026-08-04T18:02:10Z by the loop driver. S8's runner was killed
mid-sprint by a process exit and resumed from its transcript; its work survived
uncommitted and it finished on attempt 2.

## The client surface stayed byte-silent

S8's sharpest constraint. Verified on the diff rather than by test, since a diff property
cannot fail during a test run:

```
$ git diff --name-only 4bdc6d8..HEAD | grep -E "app/home/|components/home/|components/self-assessment/"
exit=1  (no matches)
```

The runner also added a standing guard that enumerates the six client-surface sources
from disk, strips comments so the deliberate section 6.4 discussion of AI does not
self-trigger, and fails on eight AI-vocabulary patterns reaching rendered markup — with a
case asserting the enumeration actually found files, so the guard cannot pass by scanning
nothing. That is stronger than the criterion asked for, and it protects later sprints.

## The fixture banner no longer lies

Reassembled from `routes/admin.py:514-517`, exactly the criterion's string:

```
AI runs in offline fixture mode: Run AI returns deterministic demo drafts, not live model output
```

## A SECOND phantom Tailwind token, empirically proven

The runner found that `border-border-default` emits nothing. The preset declares
`border: { subtle, DEFAULT, strong, focus }` and Tailwind flattens `DEFAULT` to the bare
name, so `border-border` and `border-border-subtle` generate but `border-border-default`
does not. Proven against the served stylesheet rather than by reasoning about flattening:

```
$ curl -s http://localhost:3001/_next/static/css/app/layout.css   # 41130 bytes
$ grep -c "border-border-default"   ->  0
$ grep -c "border-border-subtle"    ->  1
```

7 uses across 5 files (`AiPreviewButton.tsx`, `csf/CsfPlaybookPanel.tsx`,
`DiscardDraftButton.tsx`, `risk/RiskRegisterDashboard.tsx`, `messages/MessageThread.tsx`)
against 94 uses of the working `border-border-subtle`.

**This matters beyond the seven lines.** S0 existed to sweep exactly this class of defect
and swept only `surface-muted`, the one instance the design sprint happened to grep for.
A second phantom token survived that sweep, which means the class was never swept
systematically. The general fix is a check that every colour utility in `apps/web/src`
resolves to a real generated class, not another one-off grep.

The runner moved its own new component onto `border-border-subtle` and left the other
seven alone, since changing them is a visible change in five files and outside S8's scope.

## The provenance badge is correct and currently cannot discriminate

The criterion is met: the badge renders for an AI-origin row and not for a consultant one,
with fixtures that genuinely differ in both `origin` and `trust`. But in the running app
every register row will badge, because nothing writes a non-AI origin:

```
$ grep -rn "origin" apps/api/app/routes/risk.py
270:                origin="ai_generated",          # the only RiskEntry writer
$ grep -rn "consultant_entered" apps/api/app --include=*.py
exit=1  (no writer anywhere)
```

`models/risk_register.py` also defaults `origin` to `ai_generated`. So the badge is
honest — every row really is AI-drafted today — but it is a constant label rather than a
distinction, and it conveys nothing to a consultant scanning the register. It becomes
informative only when a consultant-entered write path exists, which the plan places in the
next batch. Recorded so nobody reads the register as discriminating provenance today.

The runner disclosed this itself rather than letting the passing test speak for it.

## Red runs: what was observed, and what was not

The runner volunteered a precise account instead of a blanket claim. Observed red before
implementation: the info-tone case, the risk badge, and all three banner-mount cases. The
`HowAiWorks` content case was red as a suite-level collection failure (the module did not
exist) rather than an assertion failure.

Not red, disclosed:

- The **warning-tone** case and **renders-nothing** case both passed pre-change, because
  the old banner was already warning-toned for every state. They cannot fail on the old
  tree. The info case is what bites; these two guard against flattening everything to info.
- The **client-silence guard** cases never ran red, and could not: demonstrating red would
  require adding AI vocabulary to a client-surface file, which is forbidden. The runner
  instead proved the detector fires by running its pattern list against files that do
  carry AI vocabulary, hitting two and coming back clean on all six client files.
- The **pytest** red was reconstructed: the first run raced the runner's own `admin.py`
  edit and passed spuriously, so it stashed the file, re-ran, observed
  `FAILED test_ai_status_reports_fixture_mode`, and popped. A genuine red obtained by
  reverting, and flagged as such rather than presented as a clean first red.
- **One test was edited after seeing implementation behaviour**: the CSF proximity
  assertion. The shared-ancestor check used for attack and zt failed against a correct
  implementation, because CSF's Run AI lives in a child component so their nearest common
  ancestor legitimately contains the page title. Replaced with
  `expect(panel.previousElementSibling).toBe(disclosure)`, a tighter claim — immediate
  adjacency in reading order rather than a shared subtree. Disclosed rather than buried.

## D-037 records the asymmetry without resolving it

Asked whether D-037 should record that S2 put an AI disclosure in the client's PDF while
S8 keeps the client's screen silent, the runner wrote it in as an open boundary rather than
a ruling, reasoning that a future reader hitting both surfaces would otherwise read one as
a bug and "fix" it. That is the right instinct: the distinction is a human's to make, and
an unrecorded inconsistency is the one that gets silently resolved by whoever notices it
first.
