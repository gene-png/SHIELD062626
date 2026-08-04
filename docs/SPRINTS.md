# SHIELD Sprints

The plan of record for the autonomous loop. `.claude/sprint-plan` names this file, and
`/loop-sprint-cron` resolves it against the repository root. The narrative rationale for
the current batch of work lives in `SPRINT_10.md`; this file is the executable form of it,
and where the two disagree, this file is what runs.

Durable facts, real commands, and environment gotchas are in `CLAUDE.md`. Read it first.

## Loop protocol

### Verification gate

The gate is a precondition, never a pass. Green commands prove the commands ran. They do
not prove the product works, and no box gets checked on gate output alone.

Run it through the pipeline rather than by hand, so local and CI agree:

```
bash .claude/hooks/run-gate.sh commit    # stack, prettier, ruff+black, tsc, eslint
bash .claude/hooks/run-gate.sh push      # the above, plus vitest and pytest -m unit
```

Those resolve `.claude/profile` (`shield`) to `.claude/profiles/shield.sh`, which is the
single place the commands are written down. The underlying commands, for reference when a
step fails and you need to run it in isolation:

| Step      | Command                                                                                     |
| --------- | ------------------------------------------------------------------------------------------- |
| format    | `npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`                     |
| python    | `docker compose exec -T api sh -lc "cd /app && ruff check --no-cache . && black --check ."` |
| typecheck | `docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"`              |
| lint      | `docker compose exec -T web sh -lc "cd /app && pnpm -F web lint"`                           |
| webtest   | `docker compose exec -T web sh -lc "cd /app && pnpm -F web test"`                           |
| apitest   | `docker compose exec -T api pytest -m unit -q`                                              |

Two suites sit outside the gate on purpose, and they are named here rather than left to be
discovered:

- **e2e** is host-run (`cd e2e && npx playwright test`), takes roughly 17 minutes, needs
  the web container force-recreated after any `apps/web` edit, and needs a seeded
  database. CI's fresh-runner E2E job is the authoritative run. S9 and S11 require it
  locally anyway.
- **bandit** is CI-only (`bandit -q -c pyproject.toml -r apps/api/app`). Ruff's
  `# noqa: S1xx` does not suppress it. A flagged string needs its own `# nosec BXXX`.

### Branch and identity

- Branch: `feat/defensible-reports-sprint-10`, cut from `main`. Never commit to `main`.
- Pushes and PRs run as `SpearheadAnalytica`. Start the loop with
  `--account SpearheadAnalytica` so the identity guard is armed rather than warned past.
- The local git email must be `davidcatarious@spearheadanalytica.com`. The
  `.claude/hooks/identity.sh` PreToolUse hook refuses every `git push` and every `gh`
  call otherwise, so a wrong identity halts the loop at its first push rather than
  producing misattributed commits.

### Commit conventions

Conventional commits, one per sprint task, scoped to that task's files. End every commit
body with the co-author line naming the model that actually did the work. Touching files
outside the current sprint's declared file set is a failure, not a bonus.

### Environment facts every runner must know

All `CLAUDE.md` gotchas hold. These are the ones this batch trips over:

- **The fixture-cycle pin, this batch's e2e landmine.** The deterministic status, stage,
  and score cycles in `app/ai/fixtures.py` (`_MITRE_STATUS_CYCLE`, the ZT current/target
  arithmetic, the CSF dimension arithmetic) are byte-frozen. S5 deepens prose only. The
  structural pins that must keep behaving identically: `s4-techdebt:115/119/134` (the
  exact "AI 60%"), `s5-attack:119/131/194` (changed-count, tool, status), `s6-zt:186`,
  `s7-csf-playbook:238/249` (changed fields including `what_we_found`). One literal prose
  pin moves with the prose: `s5-attack.spec.ts:151`, updated in the same commit.
- **New Python modules need `docker compose restart api`.** S1 adds
  `app/export_style.py`; uvicorn `--reload` may miss new files. Never restart api
  mid-pytest (SIGKILL 137).
- **Migration 0034 (S4)** applies in-container before any later e2e:
  `docker compose exec -T api alembic upgrade head`. Unit tests build their own SQLite
  schema.
- **Re-seed after S5** (`docker compose exec -T api python scripts/seed_demo.py`,
  idempotent) so demo rows carry the new evidence before S9's suite.
- **No new dependencies, compose changes, or feature flags.** pypdf, openpyxl, reportlab,
  and python-docx are already installed. Anything needing `docker compose build` is a
  plan violation.
- **After any `apps/web` source edit:** `docker compose up -d --force-recreate web`
  before e2e. S6, S7, S8 touch web, and S10 usually will.
- **The LLM stays in fixture mode for the entire batch.** No live-AI or cloud credentials
  are needed. Fixture is the committed default and e2e always runs fixture.
- Playwright traps, recurring: `getByRole` name matching is substring; use `click()` plus
  `waitForResponse` on auto-save controls; assert post-Run-AI state after `page.reload()`;
  spec-created users need unique timestamped emails.

### Cut order if the batch must shrink

S10 first, folding a minimal em-dash pass into S11. Then S8's HowAiWorks disclosure,
keeping the banner mounts, the honest fixture copy, and the risk badge. Then S4's
migration half, keeping the `build_roadmap()` section and heatmap, with narratives staying
run-response-only and 0034 moving to the next batch. Then S7 trimmed to the CSF stepper,
Impact Profile explainer, and home legend. Never cut S1, S2, S3, S5, or S9.

### Out of scope

- **Launching the loop.** The human dev at the keyboard runs `/loop-sprint-cron start`.
  Agents plan and stage; they never start it.
- The per-claim evidence and substantiation model, and the client evidence-attach UI.
  That is the next batch. This one renders references to artifacts already attached
  through the admin PATCH, being a filename or the explicit empty state, and nothing more.
- Any client-facing AI disclosure. The section 6.4 AI-silent boundary in `home/page.tsx`
  stays intact.
- The live-Vertex flip. Post-batch, env-only, per D-029, never committed.

## Backlog

Version at close: `3.6.0`, tag and CHANGELOG level only. Package manifests are not
touched. New decisions land in the task that makes them: D-035 (S2), D-036 (S1), D-037
(S8). D-034 is taken by merged PR #49. One migration, `0034_zt_narratives` (S4).

**S0 was added on 2026-07-30, after the Codex review of `SPRINT_10.md`.** It is not in
that document and was not reviewed with the rest. It comes from the design sprint
recorded in `docs/design-systems.md`, which found web-side color that no theme can reach.
It runs first because it is pure refactor with no visual change, and because it touches
files S7 and S8 also touch.

- [x] **S0 · Web color moves onto tokens. No visual change.**
      Scope: `apps/web/src/lib/risk/matrix.ts`, `components/admin/risk/RiskRegisterDashboard.tsx`,
      `packages/design-system/src/tokens.css`, `src/tailwind-preset.ts`, and the six files
      using a token that does not exist. Every hex stays the value it is today; this task
      only moves it somewhere a second theme can override. Adopting a visual system is a
      later sprint and is NOT in scope here.
      Acceptance criteria:
  - The five risk tiers become `--tier-{negligible,low,medium,high,critical}-{bg,fg}` in
    `tokens.css`, carrying the exact values `TIER_COLOR` hard-codes today
    (`#fee2e2`/`#991b1b`, `#ffedd5`/`#9a3412`, `#fef9c3`/`#854d0e`, `#dcfce7`/`#166534`,
    `#f1f5f9`/`#475569`), exposed through the Tailwind preset, and `matrix.ts` reads them
    instead of inlining hexes. Evidence: a vitest case asserting each of the ten resolved
    values equals the literal it replaced, so the refactor is provably colorless.
  - The 5x5 matrix no longer separates cells with `border-white`
    (`RiskRegisterDashboard.tsx:90`), which would glow on any dark canvas. It uses a gap in
    the surface color. Evidence: a vitest case asserting no `border-white` class on a
    matrix cell.
  - `bg-surface-muted` and `hover:bg-surface-muted` resolve to real CSS. The token does not
    exist, so all 8 occurrences across 6 files (`AiPreviewButton.tsx` x2,
    `CsfPlaybookPanel.tsx`, `DiscardDraftButton.tsx`, `RiskRegisterDashboard.tsx` x2,
    `KeycloakSignInButton.tsx`, `MfaEnrollment.tsx`) currently emit nothing. Replace with
    `bg-surface-sunken`. Evidence: `grep -r "surface-muted" apps/web/src` returns no
    matches, quoted in the log line.
  - The full `s16-axe` sweep still passes, and no existing vitest or e2e assertion changed.
    Evidence: the gate output plus a diff showing no edits to existing test assertions.

- [x] **S1 · Shared export style module and five-exporter adoption (D-036).**
      Scope: new `apps/api/app/export_style.py` as the single home for deliverable styling,
      adopted by `app/{tech_debt,attack,csf,zt,risk}/exporters.py` and `playbook_export.py`.
      Brand hexes documented against `packages/design-system` tokens: ink `#0e1220`, border
      `#d6dae3`, sunken `#eef2f7`, brand navy `#1b3a7a`. `LEVEL_HEX` relocates from
      `playbook_export.py:204-210` and is re-exported there for compat. Consult `/dataviz` for
      ramp construction (sequential, AA-checked text on fills).
      Acceptance criteria:
  - `graded_hex(level, n_levels)` raises on out-of-range input rather than clamping.
    Evidence: `tests/unit/test_export_style.py`, a case asserting the raise on both a
    negative level and one above `n_levels`.
  - `escaped_title(service_title, client_name)` escapes `&` and `<`, and never repeats the
    org name. Evidence: same file, a case asserting the rendered title for an org named
    with an ampersand equals the escaped single-org string.
  - Hotfix PR #50's inline `html.escape()` calls are gone from all five exporters and the
    behaviour now comes from `escaped_title()`. Evidence: `grep -c 'html.escape' ` over the
    five exporter modules returns 0, plus the existing header tests still pass unchanged.
  - Per-exporter page geometry is preserved, not unified: the four service exporters keep
    0.6in margins and the playbook keeps 0.7in, with `new_pdf_doc()` parameterizing them.
    Evidence: `tests/unit/test_export_style.py` parity contracts asserting each exporter's
    margin value, plus PDF page-count pins on a fixed context.
  - No rendered text changes. Evidence: every existing exporter content test passes with
    no edits to the test files, shown by the diff touching no `tests/unit/test_*exporters*`
    assertion lines.
  - No exporter carries a duplicated palette literal. `risk/exporters.py:123` fills XLSX
    headers with `FFEEF2F7`, which is `--surface-sunken` written out by hand; the six
    exporter modules using `PatternFill`/`RGBColor` all draw from the new module instead.
    Evidence: a grep for `PatternFill(start_color="FF` outside `export_style.py` returns
    nothing, quoted in the log line. Found in the 2026-07-30 design sprint and added after
    the Codex review.
  - D-036 appended to DECISIONS.md.
    Note: new module under `app/` means `docker compose restart api`.

- [x] **S2 · ATT&CK deliverable renders curated evidence and a tactic heatmap (D-035).**
      Scope: `app/attack/exporters.py` and the `routes/attack.py` context builder.
      Acceptance criteria:
  - The Coverage sheet carries Detection tools, Prevention tools, Response tools, and
    Rationale columns, lists joined with `", "`. Evidence:
    `tests/unit/test_attack_exporters.py`, an XLSX header contract case plus a case
    asserting a joined-tools cell equals `"Okta, CrowdStrike"` for a two-tool row.
  - An Evidence reference column resolves the attached artifact's filename from
    `evidence_artifact_id` through a join in the route context builder, and renders
    `"No evidence attached"` when NULL. Evidence: same file, one case per branch.
  - Gap Direction cells state citation facts only, never causal or remediation inference:
    `"No detection, prevention, or response tool is cited for this technique"`, or
    `"Cited: <tools> (partial)"`. Evidence: same file, a tool-less gap case asserting the
    first string verbatim.
  - The PDF and DOCX carry a defensibility stat phrased on citations,
    `"N of M scored techniques cite at least one tool"`, and a methodology note disclosing
    that tools and rationale are drafted by Run AI, are consultant-editable, have a per-row
    lock, and that substantiation states arrive next batch. Evidence: same file, substring
    assertions over extracted PDF text.
  - Heatmap Summary Coverage % cells carry `coverage_hex` fills. Evidence: same file,
    asserting `cell.fill.start_color`.
  - D-035 appended to DECISIONS.md recording the label discipline: citation facts only, no
    remediation column, no migration, no prompt change.
    Source-faithful labeling is the blocker Codex raised: Run AI overwrites every unlocked
    row's tools and rationale at `routes/attack.py:593-599`, so those fields are AI-applied
    unless the consultant edited or locked them, and no acceptance state exists yet.

- [x] **S3 · CSF released deliverable adopts the POA&M machinery and tier heatmap.**
      Scope: `routes/csf.py` release/export path plus `app/csf/exporters.py`.
      Acceptance criteria:
  - The release path loads `CsfGapAction` rows and passes them into `build_context`.
    Evidence: `tests/unit/test_csf_deliverable_routes.py`, a case asserting the context
    carries the action rows.
  - The XLSX Gap Plan carries Characterization, Owner, Deadline, Resources, Success
    criteria, and POA&M ref, with `priority_override` winning, mirroring the
    `playbook_export.py:137-178` contract. Evidence: `tests/unit/test_csf_exporters.py`,
    a header contract case, a case asserting an action row renders its owner and deadline,
    and a case asserting the override value wins over the computed one.
  - The PDF and DOCX carry an Action Plan section, a tier-model methodology block built
    from `TIER_DEFINITIONS`, and computed next-step sentences. Evidence: same file, a
    tier-definition substring assertion and a next-step line assertion over extracted text.
    The playbook's five-dimension METHODOLOGY text is not copied; it describes a different
    scoring model.
  - Answers-sheet Tier cells and per-function Average-tier cells carry `graded_hex(tier, 4)`
    fills. Evidence: same file, asserting `cell.fill.start_color`.
  - An Evidence reference resolves `CsfAnswer.evidence_artifact_id` to a filename, or
    renders `"No evidence attached"`. Evidence: same file, one case per branch.
  - A zero-actions assessment still renders. Evidence:
    `tests/unit/test_csf_deliverable_routes.py`, the C0-pattern case.

- [x] **S4 · ZT roadmap and persisted AI narratives, migration `0034_zt_narratives`.**
      Highest risk in the batch. Scope: the migration, `schemas/zt.py`, `routes/zt.py`,
      `app/zt/exporters.py`, `apps/web/src/lib/zt/types.ts`.
      Acceptance criteria:
  - Migration `0034_zt_narratives` adds `roadmap_summary` Text, `executive_summary` Text,
    and `pillar_narratives` JSON using the `JSON().with_variant(JSONB, "postgresql")`
    pattern from `attack_assessment.py:34`. All three nullable, `batch_alter_table`,
    additive. Evidence: `tests/unit/test_zt_routes.py`, a case parsing a row with all three
    columns NULL (the C0 pattern).
  - The narrative persist is atomic against a racing discard. The existing shape is
    check-then-write (flush, re-read parent status at `zt.py:504`, write), leaving a window
    a discard can commit into. It becomes a conditional parent
    `UPDATE ... WHERE status IN (<editable statuses>)` requiring exactly one affected row
    (the D-031 pattern from the previous batch), or a row lock held through commit.
    Evidence: `tests/unit/test_zt_run_ai.py`, a race case that injects the discard through
    a monkeypatch **between** the status check and the write, asserting the persist loses
    loudly. A discard arranged before the check proves nothing about this window and does
    not satisfy this criterion.
  - The three new fields leave the API and reach the web type: `ZtAssessmentResponse` gains
    them as optional with `pillar_narratives` defaulting to `None` and never a mutable
    `{}`; the manual enumeration in `routes/zt.py` `_serialize_assessment` (`:159`) is
    extended; `apps/web/src/lib/zt/types.ts:52` gains them as optional. Evidence:
    `tests/unit/test_zt_routes.py` asserting the serialized payload carries all three keys,
    plus `tsc --noEmit` green with the web type consumed.
  - Every persisted-narrative write sets `documents_stale`. Evidence:
    `tests/unit/test_zt_run_ai.py`, a case asserting the flag after persist.
  - The exporter renders a Roadmap section from `build_roadmap(gap.gaps)` carrying month,
    capability, pillar, and current to target. Evidence: `tests/unit/test_zt_exporters.py`,
    a month and capability contract case.
  - Narrative sections render only when persisted; absent means the section is omitted, not
    an empty header. Labels are "Assessment narrative" and "Consultant summary", with AI
    attribution living in the methodology note the way the playbook does it. Evidence: same
    file, one case rendering with narratives set and one asserting no section header when
    NULL.
  - The stage heatmap is framework-aware: `graded_hex(stage, level_count(framework))`, DoD
    being a 3-rung ladder and CISA 4. Evidence: same file, a case asserting the DoD ramp
    uses 3 rungs.
  - An Evidence reference resolves `ZtAnswer.evidence_artifact_id` to a filename, or
    renders `"No evidence attached"`. Evidence: same file, one case per branch.
    Note: `alembic upgrade head` in-container before any later e2e.

- [x] **S5 · Demo evidence depth: seed, fixtures, tech-debt narrative.**
      Scope: `scripts/seed_demo.py`, `app/ai/fixtures.py`, `app/tech_debt/exporters.py`.
      Acceptance criteria:
  - The seed replaces the every-25th hardcoded sentence at `:811-815` with systematic
    structured evidence: covered and partial rows get deterministic detection, prevention,
    and response tools drawn from seeded Atlas capability names plus a per-(status, tactic)
    rationale; gap rows get a rationale explaining the miss; a deterministic subset of CSF
    and ZT answers gets evidence-flavored notes; the seeded ZT assessment gets
    `roadmap_summary` and `pillar_narratives`. Idempotency is preserved. Evidence: two
    consecutive `python scripts/seed_demo.py` runs produce identical row counts, captured
    in the log line.
  - Fixture prose deepens with the cycles byte-identical. Evidence:
    `tests/unit/test_ai_runtime_fixtures.py`, a regression pin asserting
    `_MITRE_STATUS_CYCLE` and the ZT and CSF arithmetic are unchanged, plus a case
    asserting the rationale names the cited tool.
  - The e2e prose pin moves with the prose in the same commit:
    `s5-attack.spec.ts:151` currently pins `"Fixture-mode draft coverage assessment for
T1001"`. Alignment, never weakening. Evidence: the commit diff shows the spec pin and
    the fixture string changing together.
  - The tech-debt PDF, DOCX, and XLSX summaries carry a computed portfolio paragraph:
    counts by disposition, top cost drivers, and savings framing including the existing
    lower-bound caveat. Computed sentences only. Evidence:
    `tests/unit/test_exporters.py`, a narrative contract case.
  - SMOKE section 26 boxes re-pointed to the evidence-rich seed.

- [x] **S6 · Questionnaire guidance: make every question answerable.**
      Scope: `CsfQuestionnaire.tsx`, `ZtQuestionnaire.tsx`, `CsfSelfAssessment.tsx`, new
      `apps/web/src/lib/guidance/`, new `CsfMaturityReference.tsx`. Author content under
      `/writing-style`.
      Acceptance criteria:
  - A per-question "What do these levels mean?" disclosure renders full level descriptions
    plus a worked example, in both the admin and client renders. Evidence: vitest case
    asserting the disclosure content in the client configuration.
  - The guidance module carries a plain-language explainer per tier, one worked example per
    CSF function per tier (6x4), and one per ZT stage (CISA 4 and DoD 3). Evidence: vitest
    case asserting every tier and stage has both a description and an example, iterating
    the full set rather than sampling.
  - Web and backend label text cannot drift. Evidence: vitest parity pin asserting the four
    tier labels match `TIER_DEFINITIONS` and the stage labels match `CISA_STAGES` and
    `DOD_STAGES`.
  - Clients see the interview prompts: `CsfSelfAssessment.tsx` fetches
    `GET /csf/services/{id}/questionnaire` (already any-role tenant-scoped at
    `routes/csf.py:226-238`, so zero backend change) and passes `questionsByCode` labeled
    `"Consider:"` rather than `"Interview ·"`. Evidence: vitest case asserting the client
    label.
  - The Notes textarea carries instructive copy naming the tool, policy, or process behind
    an answer. Evidence: vitest case on the copy.
  - `TierPicker` and `ZtStagePicker` internals are untouched, keeping the roving-tabindex
    and select-on-Enter contract and the auto-save PATCH-flood guard at
    `TierPicker.tsx:32-37`. Evidence: the diff touches neither file.

- [x] **S7 · Workspace and platform comprehension.**
      Scope: new `components/admin/WorkflowSteps.tsx`, `CsfPlaybookPanel.tsx`,
      `/admin/management`, `HomeDashboard.tsx`, `CsfSelfAssessment.tsx`. Scheduled before S8,
      which touches the same workspace files.
      Acceptance criteria:
  - A static ordered step strip renders in all four workspaces with per-service copy and
    the current step derived from assessment or list status. Evidence: vitest
    step-highlight table case covering each status to step mapping.
  - The CSF and ZT copy carries the ownership line: the consultant reviews and edits the
    client's answers, the client sees the outcome, the consultant owns the quality. The
    existing banner at `CsfWorkspace.tsx:385-394` stays. Evidence: vitest case on the copy.
  - `CsfPlaybookPanel.tsx` carries a header legend explaining Tiers, Enterprise, Rule, and
    the Gap priority chips at `:70-109`. Evidence: vitest disclosure-renders case.
  - The home "Your services" legend explains all five `phaseFor` labels at `:76-93`, and an
    Impact Profile explainer renders where `profileLabel` does at
    `CsfSelfAssessment.tsx:253-261`. Evidence: vitest case asserting all five labels.

- [x] **S8 · AI transparency, consultant-facing (D-037).**
      Scope: `routes/admin.py`, the four workspaces, new `HowAiWorks.tsx`, risk register rows.
      Acceptance criteria:
  - `AiStatusBanner` mounts in the three unbannered workspaces (attack, csf, zt). Evidence:
    vitest mount case per workspace.
  - The fixture-mode copy stops lying. `routes/admin.py:502-512` becomes `"AI runs in
offline fixture mode: Run AI returns deterministic demo drafts, not live model
output"`. Evidence: `tests/unit/test_admin_routes.py` asserting the detail string
    verbatim.
  - The banner distinguishes tones, fixture being info and live-misconfigured being
    warning. Evidence: vitest case per tone.
  - Risk-register rows badge AI-suggested entries using the existing origin and trust
    fields at `models/risk_register.py:87-88`, admin surface only. Evidence: vitest case
    asserting the badge renders for an AI-origin row and not for a consultant one.
  - A compact `HowAiWorks.tsx` disclosure renders near Run AI in the four workspaces
    covering what AI drafts per service, what code computes, the redaction gate, and
    fixture versus live. Evidence: vitest content case.
  - The client surface stays byte-silent on AI. Evidence: the diff touches no client-surface
    file, and the section 6.4 AI-silent comment in `home/page.tsx` is intact.
  - D-037 appended to DECISIONS.md.

- [ ] **S9 · e2e proofs and SMOKE sections 33, 34, 35.**
      `needs-human: criterion 1's interview-prompt clause` — the prompt cannot render in ANY
      environment. The `questions` table is empty, `seed_demo.py` never populates it, and the
      loader `scripts/load_csf_tier_questionnaires.py` is referenced only by a docstring and a
      SMOKE line; nothing in CI, compose or `demo-reset` invokes it. Running reference data into
      the shared demo database is a human decision.
      `needs-human: criterion 5's green full-suite run` — three attempts, none green (checkpoint 1
      2 failed/49 passed, checkpoint 2 1 failed/50 passed, driver warmed+uncontended 2 failed/56
      passed). All 58 runnable tests pass across runs, but no single green summary exists. The
      plan's own loop protocol says CI's fresh-runner E2E job is authoritative; that is the
      honest arbiter here.
      Criteria 2, 3 and 4 are met with evidence — see the Log line.
      Scope: extend existing specs, add exactly one new file.
      Acceptance criteria:
  - `s3-selfassessment.spec.ts` proves a client sees tier guidance, an interview prompt,
    and the notes helper copy. `s6-zt.spec.ts` proves stage guidance and that the DoD
    ladder shows 3 stages. `s7-csf-playbook.spec.ts` proves the column legend and stepper.
    `s4` and `s5` prove the fixture-info banner is visible. Evidence: each named spec
    green, quoted in the log line.
  - One new `s27-comprehension.spec.ts` proves the management purpose copy, the home status
    legend, the risk AI-suggested badge, and the HowAiWorks disclosure. Evidence: the spec
    committed and green.
  - One PDF acceptance contract per service, unit-level over real bytes in the existing
    exporter test files, asserts section order via extracted-text index ordering plus one
    representative linkage: a score, its evidence or citation reference, and its gap or
    action appearing in the expected sequence. Evidence: the four named test cases.
  - SMOKE gains section 33 (Defensible deliverables, boxes citing the S1 to S5 unit test
    filenames), section 34 (Questionnaire guidance, spec filenames), and section 35
    (Workspace comprehension and AI transparency, spec filenames). Section 26 is
    re-pointed to the evidence-rich seed. Section 10 keeps exactly its one manual
    aesthetics line, now also covering heatmap coloring, which is the only thing tests
    cannot see in a PDF.
  - The full host e2e suite is green after `--force-recreate web`, `alembic upgrade head`,
    and a re-seed. Evidence: the Playwright run summary pasted into the log line.

- [x] **S10 · Prose scrub.**
      First to cut. Load `/writing-style` and sweep UI copy plus export, fixture, and seed
      prose, including everything S2 through S8 authored. Code identifiers, log prefixes, and
      UI glyphs are exempt.
      Acceptance criteria:
  - Where the scrub changes a substring a unit test pins, prose and pin move together in
    one commit. Alignment, never weakening. Evidence: the commit diff showing both sides.
  - The full push gate is green afterwards. Evidence: gate output in the log line.

- [ ] **S11 · Wrap-up.**
      Acceptance criteria:
  - SMOKE final pass over the section 10 note, section 26, and sections 33 to 35. Every box
    is checked only with its proving spec or test filename beside it. Evidence: the diff.
  - CHANGELOG `[3.6.0]` carries a per-task entry with its commit. BUILD_REPORT syncs gate
    results at HEAD, e2e spec count, migration 0034, and D-035, D-036, D-037.
  - `CONTEXT.md` is overwritten with the end-of-batch snapshot, and the launching dev's own
    `context/<name>.md` is refreshed. Owner-only rule applies: never write the other dev's
    file.
  - No live-LLM config reached a committed file. Evidence:
    `git diff main --stat` showing no `.env`, and a grep for `SHIELD_LLM_MODE=live`
    returning nothing outside documentation.
  - Full push gate plus full e2e green on a quiet box. Deferred items carried forward.

## What comes after this batch

Not backlog entries. Recorded here so the sequencing survives a session boundary.

1. **Evidence and access** (the drafted next batch): substantiation states
   tool-present/configured/validated, per-claim evidence attach plus post-intake upload,
   client inbox, client risk-register release, client self-start. **Dark mode should come
   out of it.** Adopting a visual system and defining a dark mode from scratch is a batch
   on its own, and leaving it inside this one would blow the scope.
2. **The visual system**: adopt one of the three in `docs/design-systems.md`, self-host its
   faces, define dark mode, and mirror the chosen ramps into the exporters so the app and
   the deliverable match. Prerequisites already handled: S0 puts web color on tokens, and
   S1 puts export color in one module, which is most of the groundwork. Blocked on Dave
   choosing a system; the recommendation is Ledger and the choice takes a D-number.
   Note that Inter has never actually loaded (see `CLAUDE.md`), so this batch is where the
   type contract becomes true rather than aspirational.

## Log

The driver appends one line per completed sprint: `date · sprint · evidence-paths · sha`.
Checkpoints append `checkpoint · pass|fixed · counts`. Shutdown appends
`shutdown · pass|fixed|blocked · pushed=<t/f> · pr=<url|none>`.

- 2026-07-30 · backlog authored from SPRINT_10.md, translated to the loop-sprint-cron
  format on `chore/reconcile-ops-pipeline`. Not yet launched.
- 2026-08-03 · S0 · `docs/evidence/S0/served-css-colourless.md`,
  `apps/web/src/lib/risk/matrix.test.ts`,
  `apps/web/src/components/admin/risk/RiskRegisterDashboard.test.tsx` · `5b575c3`.
  Driver-verified independently of the runner: `gate: shield/push passed (7 steps)`;
  `s16-axe` 5 passed (1.6m) re-run after `--force-recreate web` because the runner's own
  sweep predated two later edits; all ten tier values identical in the **served**
  stylesheet to `git show main:apps/web/src/lib/risk/matrix.ts`;
  `grep -rn "surface-muted" apps/web/src` exit 1, no output; both test files added, zero
  existing assertions modified. vitest 47→56.
  Two notes for later tasks. **The criterion text contains an ordering trap**: it names the
  tokens `negligible,low,medium,high,critical` but lists the hexes starting with
  _critical's_ pair, so a positional reading inverts the whole ramp and every frozen-table
  test still passes. The runner keyed by name and got all ten right. And **the axe sweep
  never visits the risk register**, so its pass proves no regression on the surfaces it
  does visit, not that the recoloured matrix is accessible; what carries that is the
  byte-identical values, which make a cell-text contrast change impossible.
- 2026-08-03 · S1 · `docs/evidence/S1/rendered-output-unchanged.md`,
  `apps/api/tests/unit/test_export_style.py` · `57068f3`. Driver-verified independently:
  the tech-debt deliverable was rendered from a fixed context on the post-S1 tree and again
  with `apps/api/app` checked out at `87c6df7`, and the two dumps — extracted PDF text plus
  every XLSX cell value, fill ARGB and bold flag — diffed `IDENTICAL`, ampersand org name
  included. `gate: shield/push passed (7 steps)`. Margins stay split, 0.6in across the five
  service exporters and 0.7in in `playbook_export.py`, with `new_pdf_doc()` parameterizing
  rather than unifying. `grep -rn 'PatternFill(start_color="FF' apps/api/app` exit 1. One
  test file added, zero existing assertions modified. pytest 734→762. D-036 at
  `DECISIONS.md:880`.
  **This task's third criterion could not fail.** It asks `grep -c 'html.escape'` over the
  five exporters to return 0; it returned 0 on the pre-S1 tree too, because PR #50 wrote
  `from html import escape` and called bare `escape(...)`. The runner caught this, said so,
  and substituted the check that bites — bare `escape(` over the six modules, now empty.
  Together with S0's inverted-hex ordering, that is two of the first two sprints whose
  written evidence clause was defective. Read the remaining clauses as drafts, not as
  contracts: an evidence command that passes before the work begins certifies nothing.
  The brand-navy 7-step ramp S1 built is AA-checked but **renders nothing yet**; adopting it
  would change a colour clients have already received, so it waits for the visual batch.
- 2026-08-03 · S2 · `docs/evidence/S2/empty-input-run.md`,
  `apps/api/tests/unit/test_attack_exporters.py`,
  `apps/api/tests/unit/test_attack_evidence_join.py` · `e7cd945`. Driver-verified with the
  protocol's mandatory **empty-input run**, since S2 changes a customer-visible artifact:
  the ATT&CK deliverable rendered for an assessment with all 633 techniques unscored and
  nothing curated invents no tool name, reports an honest `0 of 0 scored techniques cite at
least one tool`, and fills all 633 evidence cells with the explicit `No evidence
attached` state. `gate: shield/push passed (7 steps)`. `gap_direction()` read directly:
  exactly two returns, both citation facts. Both grep guards from S1 still empty. One import
  line removed from the existing attack test, zero assertions changed; DECISIONS.md a pure
  addition with D-035 ordered between D-034 and D-036.
  **Open item, needs a human, carried out of S2 deliberately.** The PDF and DOCX head the
  gap list `Top remediation gaps (N of M shown)` (`app/attack/exporters.py:435` and `:540`).
  It predates S2 (Work Order C4) and is a heading rather than a Gap Direction cell, so it is
  outside S2's criteria — but it frames gaps as remediation targets immediately above cells
  D-035 forbids from doing so, and the empty-input render shows it reading `Top remediation
gaps (0 of 0 shown)` on a report that scored nothing. The runner declined to change
  client-visible copy outside its criteria, which was the right call. Either pull the fix
  forward or let S10's prose scrub take it, but do not let it close unnoticed.
  Third consecutive sprint with a defective evidence clause: criterion 4 requires the stat
  and methodology note in **PDF and DOCX** but its evidence names only "substring assertions
  over extracted PDF text", so the DOCX half could not fail. The runner substituted a real
  DOCX paragraph extraction and said so.
- 2026-08-03 · S3 · `docs/evidence/S3/coverage-defect.md`,
  `apps/api/tests/unit/test_csf_exporters.py`,
  `apps/api/tests/unit/test_csf_deliverable_routes.py` · `19a1fe6` + fix `d3864f3`.
  **Rejected on first submission, then accepted.** The empty-input run caught a
  client-facing false reassurance in code S3 wrote: at 3 of 106 subcategories scored, the
  report advised `maintain the current controls and re-assess on the next cycle`, because
  `analyze_gaps` raises a gap only for an ANSWERED subcategory below target, so 0/106 and
  106/106 both reach the zero-gap branch. The first commit's gate was green and all fourteen
  of its tests passed; every zero-gap case they exercised used a fully scored assessment, so
  the branch was correct for the only input it was ever given. Fixed into three branches —
  nothing scored, partially scored, fully scored — with the adequacy claim surviving only at
  full coverage. Driver re-rendered all three and each asserts `total_gap_count == 0` first,
  proving the branch was narrowed rather than bypassed. `gate: shield/push passed (7 steps)`.
  Both grep guards empty; one import line widened, zero assertions changed across both
  commits. pytest `test_csf_exporters` 10→24, `test_csf_deliverable_routes` 6→8.
  The runner found three weak criteria on its own before the driver found the fourth:
  "a zero-actions assessment still renders" passes on a bare no-exception, so it substituted
  assertions about what renders; the `priority_override` fixture needed the computed value to
  differ from the override, and it added `assert computed != "P1"` as a vacuity guard; and one
  of its own new tests passed against the old tree, so it strengthened it.
  **Open item, needs a human.** The same render headlines `Overall maturity: Repeatable` on
  2.8% coverage. The coverage figure sits beside it so it is not a lie, but a headline
  maturity rating computed from 3 of 106 answers is the same class of problem one layer up.
  Predates S3, covered by no criterion. Whether a coverage floor should gate the headline
  rating is a product decision.
- 2026-08-03 · checkpoint · pass · gate 7/7 · bandit clean · secrets clean · e2e 49 passed /
  6 skipped by design / 2 load-flakes green standalone · tenant isolation holds.
  Ran at `9c49382` after four completed sprints. Nothing fixed, nothing committed by the
  checkpoint itself. The three things the per-sprint gates never cover all ran here: bandit
  (CI-only), the dependency audits, and the full host e2e suite, which had not run since S0
  changed how the risk matrix renders. `s8-risk-register:206` exercises that 5x5 matrix and
  passed even under load, which is the S0 concern cleared end to end. The two e2e failures
  were both `waitForURL` timeouts in the shared sign-in helper, never a content assertion;
  `/sign-in` measured 14.4s cold against a 15s budget, and both specs passed standalone.
  **Driver-verified the security claim rather than accepting it.** Both new evidence joins
  carry `Artifact.client_id == client_id` in the SQL predicate (`routes/attack.py:919`,
  `routes/csf.py:1782`), so a foreign artifact never enters the result map; both exporters
  then raise on an unresolved id rather than degrading into `No evidence attached`
  (`attack/exporters.py:94`, `csf/exporters.py:115`). A cross-tenant artifact cannot reach a
  deliverable, and the 409 is not an existence oracle because a foreign id and a nonexistent
  id take the identical path.
  **The documented dependency posture is stale and should be corrected.** `CONTEXT.md`
  records one HIGH (`sharp`) plus one moderate (`postcss`). Actual root `pnpm audit` is
  **5 high + 2 moderate**: `sharp@0.34.5` HIGH as documented, `postcss@8.4.31` now carrying
  four advisories of which **two are HIGH** rather than one moderate, and
  `brace-expansion@1.1.16` **2× HIGH, undocumented anywhere** (transitive via
  `minimatch@3.1.5`). None is branch-introduced — this branch touches no lockfile or
  manifest, so `main` audits identically — but the recorded posture understates reality and
  all three want the same unscheduled lockfile bump. `npm audit` in `e2e/` is clean, and the
  endpoint did not 410 this time.
  **Two pre-existing security findings, reported not fixed, neither a branch regression.**
  (1) XLSX formula injection: openpyxl types a leading `=` as a formula, and free-form
  `Notes`/`Rationale` cells already carry user text across all six exporters; S2 and S3 add
  one more user-controlled column to a vector that already existed. A real fix spans six
  modules and is not a one-pass TDD change. (2) `evidence_artifact_id` is written
  unvalidated at `attack.py:401` and `csf.py:528`, both admin-gated and both unchanged by
  this branch: a nonexistent UUID raises IntegrityError while a foreign-tenant UUID commits,
  which is a boolean existence oracle at PATCH. Data-integrity gap rather than privilege
  escalation, since platform admins hold cross-tenant reach by design; the new join is what
  stops it becoming a leak in a deliverable.
- 2026-08-03 · S4 · `docs/evidence/S4/race-window-and-sparse-render.md`,
  `apps/api/tests/unit/test_zt_run_ai.py`, `apps/api/tests/unit/test_zt_exporters.py`,
  `apps/api/tests/unit/test_zt_routes.py` · `3590500`. The highest-risk task in the batch,
  accepted first time.
  **The race criterion was verified structurally, not accepted.** The test patches
  `app.routes.zt.audit`, and that call sits strictly after the status check and strictly
  before the durable write in BOTH shapes: pre-fix `b53b6af` had check `:510` → audit `:524`
  → commit `:532`; post-fix has audit `:584` → conditional UPDATE `:596` → commit `:603`. So
  the injection is genuinely inside the window the criterion names, and the required red run
  against the pre-fix shape returned **200** with the narrative persisted into a parent that
  had gone DISCARDED mid-window. The fix is D-031's shape — conditional
  `UPDATE ... WHERE status IN ('draft','submitted')`, `rowcount != 1` raises typed 409
  `assessment_not_editable` — not a third mechanism. The test carries
  `assert fired, "the seam moved out of the window"` so it cannot silently stop biting.
  Disclosed limitation, the runner's own: the injection is emitted SQL on the request session
  rather than a second connection, because SQLite already holds a RESERVED write lock there.
  The criterion asks for a monkeypatch and what it tests is exercised faithfully.
  Migration `0034` → `down_revision "0033"`, `batch_alter_table`, all three nullable and
  additive, `JSON().with_variant(JSONB, "postgresql")`; `alembic current` reports
  `0034 (head)` in-container. `gate: shield/push passed (7 steps)`. Both grep guards empty;
  the evidence join filters `Artifact.client_id == client_id` in SQL at `zt.py:1305`, matching
  attack and csf exactly. One line removed from tests: the `_ctx` signature, widened with
  keyword-only args defaulting to prior behaviour. pytest 796→814.
  **Fifth consecutive defective evidence clause**, and this one could not fail by
  construction: criterion 3 asks for `tsc --noEmit` green with the web type consumed, but
  adding three _optional_ fields to a TS interface cannot make tsc red, and the scope forbade
  touching any web file that could consume them. The runner substituted wire-level assertions
  on the real serialized payload, which is where the contract actually lives.
  **The runner fixed three S3-shaped defects no criterion covered**, after being warned about
  the pattern: the ZT PDF/DOCX printed `No gaps at target stage 3 (Advanced).` identically
  whether all 37 capabilities sat at target or none was scored, the XLSX placeholder was a
  flat string, and the headline printed against 8% coverage unqualified. Driver re-rendered
  0/37 and 3/37 and both now state their own coverage — `This is an absence of data, not an
absence of gaps.`
  **This answers the CSF open item.** ZT's headline reads `Overall stage: Optimal` at 8.1%
  coverage but follows with a sentence saying unscored capabilities are excluded from every
  average "so no stage here describes them". CSF's `Overall maturity: Repeatable` at 2.8% has
  no such qualifier. The remedy already exists one service over, so closing that item is
  copying an established pattern rather than making a new decision.
  Noted, not a defect: `ZtRunAiResponse.pillar_narratives` carries a mutable `{}` default
  (`schemas/zt.py:173`), but it is pre-existing at `b53b6af`, outside the criterion's named
  class `ZtAssessmentResponse` (which correctly uses `| None = None`), and Pydantic v2
  deep-copies defaults per instance.
- 2026-08-04 · S5 · `docs/evidence/S5/pin-cycles-and-thin-data.md`,
  `apps/api/tests/unit/test_ai_runtime_fixtures.py`, `apps/api/tests/unit/test_exporters.py`
  · `ed639e3`. `gate: shield/push passed (7 steps)`. The four pinning specs green: 8 passed
  (8.5m), no flake, no standalone re-run needed.
  **The one sanctioned pin was diffed, not trusted.** `s5-attack.spec.ts:151` changed
  `assessment` to `evidence` inside the same `page.getByText(/…/)` and the same
  `toBeVisible()` — alignment at identical strictness. Across all of S5 the only lines removed
  from any test or spec are that pin and one widened import. `_MITRE_STATUS_CYCLE` is
  byte-identical at `fixtures.py:98`; no cycle tuple or arithmetic line was removed or
  modified, and the runner's mutation check confirms the pin goes red when a cycle value moves.
  Driver re-rendered the tech-debt paragraph four ways (empty list, uncosted rows, no
  dispositions, mixed): clean in every case, no dollar figure printed without a costed Cut row,
  lower-bound caveat intact.
  **S5 found a bug that made the seed unrunnable on a fresh database.** `_zt_stage_for` emitted
  stage 4 for DoD ZTRA, whose ladder stops at 3, and S1's `graded_hex` raises rather than
  clamps, so `render_zt_xlsx` died with `ValueError: level must be within 1..3, got 4`. Fixed
  by clamping per framework via `level_count`. This is FAIL LOUDLY earning its keep: bad seed
  data that had been silently accepted became a crash the moment a raising helper touched it,
  and the live demo DB predates S1, which is why nobody had seen it.
  Three criteria could not fail and were substituted: the cycle regression pin (passes with no
  work, and re-deriving expected values from the code under test can never fail — replaced with
  literal pins plus a mutation check), the two-run row-count evidence (no such log line
  existed and the skip path printed nothing — replaced with `_print_row_census` on both paths,
  `seed_demo.py:1369` and `:1420`), and the SMOKE re-point (no failure condition — replaced
  with an explicitly unchecked box naming what proves what). The runner also caught its own
  prose committing this batch's defect once, claiming "a documented response play exists" for a
  covered row citing no response tool, and pinned the fix.
  **Same defect, third service, now at the header layer.** Rescoping a driver check revealed
  the pre-existing Summary header reads `Total annual cost: $0` when rows carry _unrecorded_
  costs — asserting zero where the truth is "not recorded". With CSF's unqualified
  `Overall maturity` and ZT's now-qualified `Overall stage`, that is three of four services with
  one root cause, found by three independent empty-input runs, and ZT already holds the fix
  pattern. Wants one consistent absent-versus-zero treatment across all four, not three nits.
  **Operational gap S9 will hit.** The seed skips when any Service exists, so the live demo
  database still carries the OLD ATT&CK evidence (`zt_narrated=0` against `services=37`). Only
  `demo-reset --demo` or a wipe picks up the new seed, and that path is destructive and opt-in
  per D-033. S9's criteria assume the evidence-rich seed is live, so that reset has to be run
  deliberately before S9's suite.
- 2026-08-04 · S6 · `docs/evidence/S6/unrunnable-criterion-and-findings.md`,
  `apps/web/src/lib/guidance/guidance.test.ts`, plus vitest beside each of the three
  components · `1251a18`. `gate: shield/push passed (7 steps)`. vitest 56→79 across 13→17
  files, zero skips. Pickers verified untouched: `git diff --name-only | grep -E
"TierPicker|ZtStagePicker"` returns nothing, so the roving-tabindex contract and the
  PATCH-flood guard are intact. No new hex; all six colour utilities added exist in
  `tokens.css` and the preset.
  **Criterion 3 was not weak, it was unrunnable.** It asks for a vitest pin against
  `TIER_DEFINITIONS`, `CISA_STAGES` and `DOD_STAGES`, which live in `apps/api` — but the web
  service mounts only `./apps/web`, `./packages`, `./package.json` and `./pnpm-workspace.yaml`,
  and `docker compose exec -T web sh -lc "ls /app/apps"` prints `web` alone. No pin vitest can
  write is able to read those constants, and the only literal satisfaction is comparing against
  a hardcoded web-side copy, which passes while the component ignores the wire — the exact drift
  the criterion exists to prevent. Substitute inverts it: the web layer now carries **no** label
  or description text, labels render from the catalog payload, and tests feed sentinels
  (`WIRE-LABEL-1`) so a reintroduced copy fails. Driver-verified by grep: no label string in
  `lib/guidance/` or `CsfMaturityReference.tsx`. Seventh consecutive defective clause and the
  first that was impossible rather than merely unfalsifiable.
  The 6x4 + 4 + 3 completeness test asserts 24 and 7 unique examples and the lookups raise on a
  missing entry; the runner confirmed it goes red by deleting `PR` tier 3.
  **Open item: Zero Trust clients get no guidance, and the gap is in the plan.**
  `ZtSelfAssessment.tsx` mounts `ZtStagePicker` directly (`:13`, `:339`) rather than
  `ZtQuestionnaire`, and that file is absent from S6's scope list. CSF's questionnaire is shared
  so one disclosure serves both audiences; ZT's is not. All seven stages of guidance data exist
  and are tested, but nothing client-side consumes them. The runner honoured scope and flagged
  it. Closing it is an import plus one element beside the picker.
  **Open item, highest value found in this run: a swallowed error on the client's only write
  path.** `CsfSelfAssessment.tsx:172` is a bare `catch {}` around the answer PATCH, a direct
  violation of `CLAUDE.md` principle 2, and it predates S6. The consequence compounds with what
  this batch built: a client picks a tier, the optimistic UI shows it saved, the PATCH fails
  silently, the answer is lost, and the deliverable then reports — honestly, thanks to S3 — that
  the subcategory is unscored and carries no finding. The newly truthful reporting will
  faithfully describe a gap that a silent save failure created. The client answered and the
  report says they did not.
- 2026-08-04 · S7 · `docs/evidence/S7/recovered-red-run.md`,
  `apps/web/src/components/admin/WorkflowSteps.test.tsx`, `CsfPlaybookPanel.test.tsx`,
  `HomeDashboard.test.tsx`, `CsfSelfAssessment.test.tsx` · `517b4b3`.
  `gate: shield/push passed (7 steps)`. vitest 79→106 across 17→19 files. Pickers,
  `ZtSelfAssessment.tsx` and the bare `catch {}` all verified untouched, the last byte-identical
  at `CsfSelfAssessment.tsx:173` despite S7 working inside that file.
  **A TDD violation, disclosed by the runner and then recovered.** For the playbook-legend
  criterion it wrote the component before the test, so no red run was observed; the other three
  criteria had observed reds. An observed red cannot be recreated after the fact, so the driver
  reverted `CsfPlaybookPanel.tsx` to `b250c4c` and ran its suite: **2 failed | 2 passed (4)**.
  The tests cannot pass without the implementation. Recorded as a _recovered check_ rather than
  an observed red, and deliberately not overstated: one failure is a render assertion, the other
  is `gapPriorityMeaning is not a function`, so part of what fails is the module surface rather
  than the behaviour. The disclosure is why this was checkable at all — a runner that quietly
  reordered its narrative would have produced an identical-looking green sprint.
  Unrecognised statuses fail loudly instead of defaulting to step 1, and the expectation type is
  `Record<Status, number>` so tsc rejects a new wire status until it is mapped. The home legend
  makes an unexplained phase structurally impossible (`phaseFor` returns one of five shared
  objects) and the Gap chips render their legend from the same map that colours them, raising on
  a missing reading. All four workspaces proved by name, two at non-trivial statuses.
  **Plan defect, not a code one: `/admin/management` is named in S7's Scope line but carries no
  acceptance criterion and no evidence clause anywhere.** The runner left it untouched rather
  than inventing work, which was correct. Either it needs a criterion in a later sprint or that
  scope line is stale from an earlier draft.
- 2026-08-04 · checkpoint · pass · gate 7/7 · bandit clean · secrets clean · audits unchanged
  (5 high + 2 moderate, no lockfile touched) · e2e 50 passed / 6 skipped by design / 1 load
  flake arbitrated green. Ran at `f58332b` after eight sprints; nothing fixed, nothing
  committed by the checkpoint.
  This checkpoint's specific risk was S6 and S7 pouring new copy onto the surfaces the specs
  drive, where `getByRole` matches by substring — a strict-mode violation would have been a real
  regression, not a flake. **None occurred.** The single failure
  (`s7-csf-playbook.spec.ts:312`) was arbitrated as the documented cold-compile flake on four
  strands: it failed in `signIn`, the test's first action, before any assertion on rendered
  content; no strict-mode violation or "resolved to N elements" anywhere; **the failure moved**
  between runs (`:312` failed in-suite then passed standalone while `:150` did the reverse,
  whereas a selector break is deterministic); and the logs show sign-in succeeding, then the
  redirect chain paying `/` 10.5s + `/admin` 3.2s + `/admin/queue` 3.4s. Warming those routes
  and re-running gave `1 passed`, so all 51 runnable tests are green across runs.
  Driver-verified: the ZT evidence join at `routes/zt.py:1305` carries
  `Artifact.client_id == client_id` identically to `attack.py:919` and `csf.py:1782`, so no
  cross-tenant artifact reaches a ZT deliverable; `_persist_run_ai_narratives` needs no
  client_id predicate because it targets a primary key already authorised by
  `require_service_in_tenant`.
  **New finding: CI's bandit never scans `apps/api/scripts`.** `.github/workflows/ci.yml:48`
  runs `bandit -q -c pyproject.toml -r apps/api/app`, so the whole `scripts/` tree is invisible
  to it. Scanning it anyway found 7 LOW including `B105` on the documented demo password at
  `seed_demo.py:129` — harmless and pre-existing from `20afb3d`. The credential is not the
  finding; the coverage gap is, because a future script could carry a real secret unscanned.
  **The recorded `evidence_artifact_id` finding has a third instance:** `zt.py:786` joins
  `attack.py:401` and `csf.py:528`. Same pattern, dating to `fb9c99d`, not a regression.
  **Correction to how the e2e flake should be fixed.** It is NOT a one-line timeout bump:
  `e2e/helpers/auth.ts:60-63` already wraps a 15s inner `waitForURL` in
  `expect(...).toPass({ timeout: 60000 })` and still lost, because the post-login chain pays
  three sequential cold compiles and each retry can re-enter them. S9 and S11 both require a
  green full suite, so this will keep recurring on any cold-start run — real test-infra work,
  small but not trivial, and outside a checkpoint's remit.
- 2026-08-04 · S8 · `docs/evidence/S8/phantom-token-and-badge.md`,
  `apps/web/src/components/admin/HowAiWorks.test.tsx`, `AiStatusBanner.test.tsx`,
  `ZtWorkspace.test.tsx`, `apps/api/tests/unit/test_admin_routes.py` · `56373e2`.
  **The loop survived a process exit mid-sprint.** The runner was killed with its work
  uncommitted; HEAD stayed at `4bdc6d8`, the branch stayed in sync, and the work was intact in
  the tree. Resumed from transcript rather than respawned, since a fresh agent would inherit a
  half-finished tree it did not write. Finished on attempt 2. Its first gate after resuming
  correctly reported `BLOCKED` because Docker Desktop had died with the earlier crash; it
  restarted the stack and re-ran rather than reading five unreachable steps as green.
  `gate: shield/push passed (7 steps)`. vitest 106→118 across 19→22 files. Client-surface
  constraint held: `git diff --name-only | grep -E "app/home/|components/home/|
components/self-assessment/"` returns nothing, and the section 6.4 comment is intact and
  asserted. The fixture string reassembles to the criterion's text exactly.
  **A SECOND phantom Tailwind token, and this one matters beyond its seven lines.**
  `border-border-default` emits nothing: the preset declares `border: { subtle, DEFAULT, strong,
focus }` and Tailwind flattens `DEFAULT` to the bare name. Proven against the served
  stylesheet (41130 bytes) rather than by reasoning — `grep -c "border-border-default"` returns
  **0** while `border-border-subtle` returns 1. Seven uses across five files against 94 of the
  working class. S0 existed to sweep this exact class of defect and swept only `surface-muted`,
  the one instance the design sprint grepped for, so a second phantom survived it. The class was
  never swept systematically; the general fix is a check that every colour utility resolves to a
  real generated class, not another one-off grep.
  **The provenance badge is correct and currently cannot discriminate.** The criterion is met
  with fixtures differing in both `origin` and `trust`, but nothing writes a non-AI origin:
  `routes/risk.py:270` is the only `RiskEntry` writer and passes `origin="ai_generated"`, the
  model defaults to the same, and `consultant_entered` appears nowhere in app code. So every
  register row badges — honest, since every row really is AI-drafted, but a constant label rather
  than a distinction. It becomes informative only when a consultant-entered write path exists,
  which the plan places in the next batch. The runner disclosed this itself instead of letting a
  passing test speak for it.
  **Red-run honesty, volunteered.** Observed red: info tone, risk badge, all three banner
  mounts; `HowAiWorks` content was red as a collection failure rather than an assertion. NOT
  red and disclosed: the warning-tone and renders-nothing cases both passed pre-change because
  the old banner was warning-toned for every state; the three client-silence guards could not
  go red without adding AI vocabulary to a forbidden file, so the runner proved the detector
  fires against files that do carry it; the pytest red was reconstructed by stashing `admin.py`
  after a first run raced its own edit and passed spuriously. **One test was edited after seeing
  implementation behaviour** — the CSF proximity assertion, because CSF's Run AI lives in a child
  component so the shared-ancestor check used for attack and zt legitimately failed against
  correct code. Replaced with `previousElementSibling`, a tighter claim, and disclosed.
  D-037 records the client-PDF-versus-client-screen asymmetry as an open boundary rather than
  resolving it, on the reasoning that an unrecorded inconsistency is the one silently "fixed" by
  whoever notices it first.
- 2026-08-04 · S9 · `docs/evidence/S9/two-unmet-criteria.md`, `e2e/smoke/s27-comprehension.spec.ts`,
  four PDF acceptance contracts in the existing exporter test files · `718234b`.
  **BOX LEFT UNCHECKED. Two criteria carry `needs-human`; three are met.**
  Met: `s27-comprehension.spec.ts` (4 tests) plus the s3/s4/s5/s6/s7 extensions all passed inside
  the driver's own full-suite run; the four PDF contracts assert section order as a subsequence
  over real extracted bytes with three mutation-checked; SMOKE 33-35 added with per-box spec
  filenames and four boxes deliberately left unchecked. `gate: shield/push passed (7 steps)`.
  No application source touched; zero deletion lines across specs and unit tests.
  **needs-human 1: the interview prompt has no data path in any environment.** `questions` is
  empty, `seed_demo.py` contains zero references to it, and `load_csf_tier_questionnaires.py` is
  invoked by nothing — only a docstring and a SMOKE line mention it. **S6 was credited for this
  feature on a mocked vitest**: its criterion asked for "a vitest case asserting the client label"
  and got one, with the fetch mocked. The test is honest; the criterion asked for the wrong proof.
  This is `CONTEXT.md`'s Sprint-8 lesson verbatim — a flow unit tests call green can be broken for
  every real user — recurring with a different cause.
  **needs-human 2: no green full-suite run exists after three attempts** (2/49, 1/50, and the
  driver's warmed uncontended 2 failed/56 passed/6 skipped in 34.6m). All 58 runnable tests pass
  across runs; the 2 failures arbitrate standalone at `2 passed (1.3m)`. **Driver correction:**
  both were `s18-home`, and `:180` had failed in the runner's run too, so the driver first called
  it a reproducible regression. Wrong — `:180` is a pure timing test with no state dependency,
  `:125` builds its own isolated tenant, and `s27` mutates nothing. The error was treating "quiet
  box" as a property of how the run started; after 34 minutes of continuous browser work a 20s
  redirect budget is the first thing to give out. Same structural fragility checkpoint 2
  measured. The plan's loop protocol names CI's fresh-runner E2E job as authoritative, which is
  the honest arbiter. **S11 requires the same green run and will hit the same wall.**
  Five criteria describing things the system does not do, all verified: the interview prompt; ZT
  client stage guidance (consultant render only); the badge reads `AI-drafted · Admin Assisted`
  and every row badges; "management purpose copy" predates Sprint 10 (`0fe1096`); the CSF stepper
  is 5 steps, not 10. Plus a bug correctly left alone: `ZtSelfAssessment.tsx:371` still carries
  the old Notes placeholder although S6's commit message claims both were updated.
- 2026-08-04 · S10 · `docs/evidence/S10/pins-moved-nothing-loosened.md` · `73ae76b`.
  `gate: shield/push passed (7 steps)`. Seven pinned literals moved, prose and pin in the same
  commit at identical strictness.
  **Nothing was loosened.** The complete deletion set across `apps/api/tests` and `e2e` is eight
  lines: five substring `in text` checks, one `==` cell equality, one module constant consumed by
  two `not in` absence checks, and two regexes — and the regexes got **stricter**, losing a `.*`
  wildcard (`/capped .* no evidence/` → `/capped, no evidence/`). Nothing became a `toContain`,
  a permissive regex, conditional, or deleted.
  **Nothing frozen moved.** `apps/api/app/ai/` has an empty diff, so `_MITRE_STATUS_CYCLE` and the
  ZT/CSF arithmetic are byte-identical; `s4-techdebt`, `s5-attack` and `s6-zt` have no diff at all,
  so `s4:115/119/134`, `s5:119/131/194` and `s6:186` could not have moved; `s7` changed exactly two
  lines at 301/309, leaving `s7:238/249` alone.
  **No honesty claim was re-inflated** — the check that mattered, since five sprints in this batch
  made sentences narrower and a scrub is the easiest way to reverse that while looking like an
  improvement. `zt/exporters.py:200,206` still carry "This is an absence of data, not an absence of
  gaps" and "this statement says nothing about them"; `attack/exporters.py:61` still says "no field
  here should be read as verified"; `tech_debt/exporters.py` has an **empty diff** so its lower-bound
  hedges are byte-identical; the D-035 gap-direction string is unchanged.
  **Driver methodology note:** a single-line grep for those protected strings showed four of nine
  "missing". All nine were present — Python splits them across f-string continuations, so only a
  multiline search finds them. A false alarm was one trusted grep away, and anyone auditing prose in
  this codebase will hit the same trap.
  61 em-dashes rewritten rather than swapped (41 sentence splits, 12 colons, 5 commas, 3
  parentheses); rules 2 through 7 produced zero changes, every hype-list hit being a code
  identifier. Correctly declined: title separators like `"{org} — {label}"`, which are load-bearing
  (`test_export_style.py:109` parametrizes the separator set, `test_deliverable_release.py:426`
  asserts an em-dash is _absent_ from a stripped label, `s6-zt.spec.ts:30` pins a service title),
  and ~180 em-dashes in comments and docstrings. The runner caught its own subagent editing three
  out-of-scope lines in `ZtSelfAssessment.tsx` and reverted them pre-commit.
  Also fixed the stale placeholder S6's commit message claimed to have updated:
  `ZtSelfAssessment.tsx:371` is now byte-identical to the other two questionnaires and the old
  string is gone from `apps/web/src`. Nothing pinned it.
  The runner noted unprompted that criterion 2 ("the full push gate is green afterwards") is a
  floor rather than a proof, and treated it as one.
