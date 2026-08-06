# S9 evidence — two criteria that cannot be met here

Captured 2026-08-04T20:47:30Z by the loop driver. **S9's box stays unchecked.**
Three of five criteria are met with evidence; two carry `needs-human`.

## Met: the new specs, the PDF contracts, and SMOKE 33-35

`s27-comprehension.spec.ts` (4 tests) and the extensions to s3, s4, s5, s6 and s7 all
passed inside the driver's own full-suite run. Four PDF acceptance contracts assert
section order as a subsequence over real extracted bytes, each needle searched only after
the previous match, and the runner mutation-checked three of them (roadmap-before-gaps,
attribution-before-narrative, score-after-gap-list all raise).

## needs-human 1 — the interview prompt has no data path anywhere

Criterion 1 requires `s3-selfassessment.spec.ts` to prove a client sees an interview
prompt. It cannot, because the prompt cannot render in any environment:

```
$ docker compose exec -T db psql -U shield -d shield -c "select count(*) from questions;"
 0
$ grep -c "CsfTierQuestion\|questions" apps/api/scripts/seed_demo.py
0
```

The loader that would populate it, `scripts/load_csf_tier_questionnaires.py`, is
referenced in exactly two places in the repository: a docstring in
`models/questionnaire.py` and the SMOKE line S9's runner wrote. Nothing in CI, compose,
`demo-reset`, or any script invokes it. So `questionsByCode` is always `{}` and the
`Consider:` eyebrow never appears — not here, not in CI, not in the demo stack.

**S6 was credited for this feature on a mocked vitest.** Its criterion asked for a
"vitest case asserting the client label" and got one: the test mocks the fetch and
asserts `findByText("Consider:")`. The test is honest about what it tests; the criterion
asked for the wrong proof. This is `CONTEXT.md`'s Sprint-8 lesson recurring verbatim —
"a flow that unit tests call green can be broken for every real user" — written after the
MFA TOTP field never appeared in a browser despite green units. Same shape, different
cause: the mock stood in for the thing that does not work.

Resolving it means running a reference-data loader against the shared demo database,
which is the same class of human decision as the S5 evidence refresh. Not a driver's call.

## needs-human 2 — no green full-suite run exists, on the third attempt

Criterion 5 wants a green full-suite summary. Three attempts, none green:

| Run                            | Result                                       |
| ------------------------------ | -------------------------------------------- |
| checkpoint 1                   | 2 failed / 49 passed                         |
| checkpoint 2                   | 1 failed / 50 passed                         |
| driver, warmed and uncontended | **2 failed / 56 passed / 6 skipped (34.6m)** |

Every runnable test passes across runs — 56 in-suite plus the 2 failures arbitrated
standalone at `2 passed (1.3m)` — but there is no single green summary, so the criterion's
own evidence clause is unsatisfied.

**A correction the driver owes the record.** Both failures were `s18-home`, and
`s18-home:180` had also failed in the runner's contended run, so the driver first called
it a reproducible regression rather than a flake. That was wrong. `s18-home:180` is a
pure timing test (sign in, `goto("/")`, wait 20s for the redirect) with no state
dependency, `s18-home:125` builds its own isolated tenant so earlier specs cannot poison
it, and `s27` mutates nothing — every grep hit was a string literal inside an assertion.
The reasoning error was treating "quiet box" as a property of how the run started: after
34 minutes of continuous browser work the box is under sustained self-load, and a 20s
redirect budget is the first thing to give out.

This is the same structural fragility checkpoint 2 measured. `e2e/helpers/auth.ts:60-63`
already wraps a 15s `waitForURL` in `toPass({ timeout: 60000 })` and still loses to
sequential cold compiles. The plan's own loop protocol says **"CI's fresh-runner E2E job
is the authoritative run"**, and that is the honest resolution: a clean 64-test local run
does not appear achievable on this box, so CI decides. S11 requires the same thing and
will hit the same wall.

## Criteria that describe things the running system does not do

The runner reported five, all verified as accurate:

- The interview prompt (above).
- ZT client stage guidance: consultant render only. Proven on `ZtQuestionnaire`.
- The badge text is `AI-drafted · Admin Assisted`, not "AI-suggested", and every row
  badges because `OriginCell`'s non-AI branch is unreachable.
- "Management purpose copy" predates Sprint 10 (`0fe1096`, 2026-06-25). Nothing asserted
  it before, so the new spec still bites.
- The CSF stepper is 5 steps, not the 10 the service name implies; "10-step Playbook"
  survives only as intake marketing prose.

Plus a bug it declined to fix, correctly: `ZtSelfAssessment.tsx:371` still reads the old
`"Evidence, references, exceptions…"` placeholder even though S6's commit message claims
both Notes placeholders were updated. That file was outside S6's scope and outside S9's.

## Hygiene

No application source touched (`git status --short -- apps/web/src apps/api/app` empty).
Zero deletion lines in `git diff -U0 -- e2e/smoke/ apps/api/tests/unit/`, so no existing
assertion moved. The only two deletions in the whole diff are SMOKE lines that were
rewritten stronger and left unchecked. Four SMOKE boxes deliberately unchecked with
precise reasons, which is the honesty convention working as designed.
