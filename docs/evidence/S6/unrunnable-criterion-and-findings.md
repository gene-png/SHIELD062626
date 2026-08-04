# S6 evidence — an unrunnable criterion, and two findings

Captured 2026-08-04T05:31:37Z by the loop driver.

## The pickers were not touched

Criterion 6's evidence is literally "the diff touches neither file". `TierPicker.tsx`
and `ZtStagePicker.tsx` hold a roving-tabindex accessibility contract and the auto-save
PATCH-flood guard, and hanging a disclosure off a level button would have been the
obvious shortcut.

```
$ git diff --name-only 729fb9a..HEAD | grep -E "TierPicker|ZtStagePicker"
exit=1  (no matches)
```

## The parity criterion was not unfalsifiable — it was unrunnable

Criterion 3 asks for a "vitest parity pin asserting the four tier labels match
`TIER_DEFINITIONS` and the stage labels match `CISA_STAGES` and `DOD_STAGES`". Those
constants live in `apps/api`. The web service mounts only `./apps/web`, `./packages`,
`./package.json` and `./pnpm-workspace.yaml`:

```
$ docker compose exec -T web sh -lc "ls /app/apps"
web
```

vitest runs at `/app/apps/web`, so no pin it could write is able to read those three
constants. Worse, the only in-container way to satisfy the criterion literally is to
compare against a hardcoded web-side copy of the labels — which passes while the
component ignores the wire entirely, the exact drift the criterion exists to prevent.

The substitute inverts it: **the web layer now carries no label or description text at
all.** Labels render from the catalog payload the API builds from those constants, and
the tests feed sentinel values (`WIRE-LABEL-1`, `WIRE-STAGE-3`) so a reintroduced local
copy fails. Verified independently:

```
$ grep -rE "Partial|Risk Informed|Repeatable|Adaptive|Traditional|Initial|Advanced|Optimal" \
    apps/web/src/lib/guidance/ apps/web/src/components/csf/CsfMaturityReference.tsx
exit=1  (no matches)
```

That is strictly stronger than the criterion asked for: it proves provenance rather than
agreement between two copies. This is the seventh consecutive sprint whose written
evidence clause was defective, and the first that was impossible rather than merely weak.

## Finding 1 — Zero Trust clients get no guidance, and the gap is in the plan

The CSF questionnaire is shared, so one disclosure serves consultant and client. Zero
Trust is not shared:

```
13:import { ZtStagePicker } from "@/components/admin/zt/ZtStagePicker";
339:                        <ZtStagePicker
```

`ZtSelfAssessment.tsx` mounts `ZtStagePicker` directly rather than `ZtQuestionnaire`,
and that file is absent from S6's scope list. So a client answering a Zero Trust
self-assessment sees no stage guidance while a CSF client does. The guidance data for all
seven stages exists and is tested; nothing on the client side consumes it. The runner
honoured the scope instruction and flagged it rather than widening the diff, which was
correct. Closing it is an import plus one element beside the picker.

## Finding 2 — a swallowed error on the client's only write path

```
172:    } catch {
173-      // Best-effort optimistic save; a reload reconciles if it failed.
174-    }
```

`CLAUDE.md` principle 2 is explicit and non-negotiable: no `catch` that swallows, no
default-value fallback on error. This is a bare swallow on the path a client uses to save
an answer, and it predates S6.

The consequence is worth stating precisely, because it interacts with what this batch
just built. A client picks a tier, the optimistic UI shows it saved, the PATCH fails, and
nothing tells them. The answer is gone. The CSF deliverable then reports coverage that
excludes it — and after S3's fix it will report that honestly, saying the subcategory is
unscored and carries no finding. So the newly honest reporting will faithfully describe a
gap that a silent save failure created. The client answered the question and the report
says they did not.

Pre-existing, outside S6's scope, and the highest-value open item this run has found.
