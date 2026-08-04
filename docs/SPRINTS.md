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

- [ ] **S4 · ZT roadmap and persisted AI narratives, migration `0034_zt_narratives`.**
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

- [ ] **S5 · Demo evidence depth: seed, fixtures, tech-debt narrative.**
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

- [ ] **S6 · Questionnaire guidance: make every question answerable.**
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

- [ ] **S7 · Workspace and platform comprehension.**
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

- [ ] **S8 · AI transparency, consultant-facing (D-037).**
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

- [ ] **S10 · Prose scrub.**
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
