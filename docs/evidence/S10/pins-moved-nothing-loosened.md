# S10 evidence — seven pins moved, nothing loosened, no claim re-inflated

Captured 2026-08-04T22:05:50Z by the loop driver.

## Every removed line across all tests and specs

A prose scrub's whole risk is a quietly loosened assertion, so the complete deletion set
was extracted rather than sampled:

```
$ git diff -U0 5f88172..HEAD -- apps/api/tests e2e | grep "^-[^-]"
-        "T3 (Repeatable) — they carry the largest lift." in text
-        "T4 (Adaptive) — they carry the largest lift." in text
-        "T4 (Adaptive) — they carry the largest lift." in text
-        "No subcategory scored below target T3 (Repeatable) — maintain the current "
-FULL_COVERAGE_REASSURANCE = "maintain the current controls and re-assess on the next cycle"
-    assert wb["Gap Plan"].cell(row=2, column=3).value == "No capability scored — gaps unknown"
-  await expect(page.getByText(/capped .* no evidence/)).toBeVisible();
-  await expect(page.getByText(/capped .* no evidence/)).toBeHidden();
```

Eight lines, and every one is a literal substitution at the same strictness: five
substring `in text` checks, one `==` cell equality, one module constant consumed by two
`not in` absence checks, and two regexes. **The two regexes got stricter**, losing a
`.*` wildcard: `/capped .* no evidence/` became `/capped, no evidence/`. Nothing became
a `toContain`, nothing became a permissive regex, nothing was deleted or made conditional.

## The byte-frozen things did not move

```
$ git diff 5f88172..HEAD --stat -- apps/api/app/ai/          # empty
$ git diff 5f88172..HEAD --stat -- s4-techdebt s5-attack s6-zt  # empty
$ git diff 5f88172..HEAD --numstat -- s7-csf-playbook.spec.ts
2	2	e2e/smoke/s7-csf-playbook.spec.ts
```

`_MITRE_STATUS_CYCLE` is byte-identical at `fixtures.py:98`, and the whole `app/ai/` tree
has no diff, so the ZT and CSF arithmetic are untouched. The structural pins at
`s4:115/119/134`, `s5:119/131/194` and `s6:186` cannot have moved because those three
files have no diff at all. `s7` changed exactly two lines, both at 301/309, so
`s7:238/249` are unaffected.

## No honesty claim was re-inflated

This is the check that mattered. Five sprints in this batch produced content that claimed
more than the data supported, and every fix made a sentence narrower. A scrub is the
easiest way to reverse that by accident, so each protected string was located in the
current tree. Note that a single-line grep gives false negatives here, because Python
splits these across f-string continuations — the first pass appeared to show four missing
and a multiline search found all four present:

```
zt/exporters.py:200  "This is an absence of data, not an absence of gaps."
zt/exporters.py:206  "The remaining N are unscored and this statement says nothing about them."
attack/exporters.py:61  "...so no field here should be read as verified"
tech_debt/exporters.py:173,350,430  "The savings figure is a lower bound."
```

`tech_debt/exporters.py` has an **empty diff**, so its savings hedges are byte-identical.
`csf/exporters.py` kept "N of M subcategories are unscored and carry no finding". The
D-035 gap-direction string "No detection, prevention, or response tool is cited for this
technique" is unchanged, so no cause or remedy was smuggled in while tightening. And
`HowAiWorks.tsx`'s "A drafted value carries no sign-off." survives.

## What the scrub actually did

61 em-dashes in product prose plus 5 in the pins, rewritten rather than swapped: 41 became
a sentence split, 12 a colon, 5 a comma, 3 parentheses. Rules 2 through 7 produced **zero**
changes — every hype-list grep hit was a code identifier, and the two antithesis-shaped
hits carry real technical meaning, so rewriting either would have changed a claim.

Two things the runner declined, both correctly. Title separators (`"{org} — {label}"`,
`export_style.py`'s `_TITLE_SEPARATORS`) are load-bearing: `test_export_style.py:109`
parametrizes over the separator set, `test_deliverable_release.py:426` asserts an em-dash
is _absent_ from a stripped label, and `s6-zt.spec.ts:30` pins a service title. Changing
them is structural work wearing a prose costume. And ~180 em-dashes in code comments and
docstrings are not product-visible prose.

It also caught its own subagent rewriting three out-of-scope lines in
`ZtSelfAssessment.tsx` and reverted all three before committing.

## The stale placeholder S6's commit message claimed to have fixed

`ZtSelfAssessment.tsx:371` read `"Evidence, references, exceptions…"` even though S6's
commit message said both Notes placeholders were updated. Now byte-identical to the other
two questionnaires, and the old string is gone from `apps/web/src` entirely. Nothing
pinned it, so no pin moved.

## On the second criterion

"The full push gate is green afterwards" is a floor, not a proof — a green gate says the
commands ran, not that the prose improved. The runner said so unprompted and treated it
accordingly. The real evidence is the deletion set above and the pin table.
