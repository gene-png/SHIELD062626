# SPRINT 10: Reports you can defend (defensible deliverables + questionnaire guidance + honest AI)

_Branch: `feat/defensible-reports-sprint-10` (cut from `main` only AFTER hotfix
PRs #49 and #50 merge; see the launch checklist). Queue:
`.claude/sprint-queue.sprint-10.json` (copy to `.claude/sprint-queue.json` to
launch). Driver: `/loop-sprint-cron` (or execute tasks by hand). Created
2026-07-24 after Sprint 9 (PR #44, `v3.5.0`) merged._

_Plan reviewed by OpenAI Codex (read-only, 2026-07-24): verdict REWORK on 8
findings (3 blockers: T3's narrative persist raced a discard between status
check and write; T1's Direction labels overstated the provenance of
AI-applied fields; the goal promised evidence the exporters never resolved).
ALL 8 adopted, finding 6 scoped: minimal evidence-reference rendering lands
now, full evidence capture is Sprint 11. The findings table is in the
planning PR body._

## Why this sprint exists

Every deliverable this platform releases makes claims a skeptical client will
challenge, and today the evidence behind those claims dies inside the app. Six
verified findings:

1. **The ATT&CK deliverable drops the consultant's evidence.** The exporter
   renders only status and notes. The curated `detection_tools` /
   `prevention_tools` / `response_tools` / `rationale` fields (model:
   `apps/api/app/models/attack_assessment.py:112-115`; applied and
   re-validated in `routes/attack.py:590-608`) never reach the XLSX, PDF, or
   DOCX. The "Heatmap Summary" sheet has zero fills; the Gaps tab is
   technique + notes with no direction.
2. **The released CSF deliverable ignores the POA&M machinery.**
   `app/csf/exporters.py` never loads the `CsfGapAction` rows
   (`models/csf_profile.py:68-107`) that `playbook_export.py` already renders
   (Action Plan sheet at `:137-178`, `_next_steps()` at `:310-326`).
3. **The ZT deliverable loses both the roadmap and the narratives.** The
   exporter never calls `build_roadmap()` (`app/zt/scoring.py:297-321`), and
   the AI-drafted `roadmap_summary` / `pillar_narratives` /
   `executive_summary` are returned in the run response
   (`routes/zt.py:501-543`) and then dropped. No columns exist to hold them.
4. **The demo cannot show evidence depth.** The seed's only "evidence" is one
   hardcoded sentence on every 25th covered attack row
   (`scripts/seed_demo.py:811-815`), and the fixtures emit one-line
   placeholder prose (`app/ai/fixtures.py:122,155,187`).
5. **The questionnaire is not answerable by a client.** Tier and stage
   definitions exist (`app/csf/maturity.py:34-71` `TIER_DEFINITIONS`,
   `app/zt/maturity.py:40-85`) but the per-question UI is bare T1..T4 chips
   with a title-attribute tooltip (`TierPicker.tsx:96`,
   `ZtStagePicker.tsx:91`). Interview prompts are served tenant-wide to any
   role by `GET /csf/services/{id}/questionnaire` (`routes/csf.py:221-264`),
   yet the client render (`CsfSelfAssessment.tsx:262-266`) omits
   `questionsByCode`.
6. **The platform does not explain itself, and its AI story is stale.**
   `AiStatusBanner` is mounted in exactly one of four workspaces
   (`TechDebtWorkspace.tsx:239`), and its fixture-mode copy ("AI features are
   disabled", `routes/admin.py:508-511`) has been false since D-017.

## Sprint goal

A consultant can hand any deliverable to a skeptical client and point at
everything the platform HOLDS behind every score: the ATT&CK export names
the curated tools and rationale plus a citation-fact Direction for every
gap; the released CSF export carries the action plan, the tier methodology,
and computed next steps; the ZT export carries the code-computed roadmap and
the persisted narratives; row sheets reference attached evidence artifacts
by filename where one exists and say "No evidence attached" where none does;
every heatmap is colored through one shared, tested style module. Tool
citations and plans justify recommendations; proving scores requires the
Sprint 11 evidence model (a client attach UI, per-claim substantiation
states), and this sprint does not claim it. A client filling in a
questionnaire sees what every tier and stage means, with a worked example
and the consultant's interview prompts. Every workspace shows where the
engagement stands and what AI actually does; the client surface stays
AI-silent.

Version at close: **`3.6.0`** (minor: new user-facing deliverable content +
questionnaire guidance). Tag/CHANGELOG-level only; package manifests are NOT
touched.

**New decisions this sprint (append in the tasks that make them):**
**D-035** (T1): the attack gap Direction is derived from the curated tools +
rationale; no new column. **D-036** (T0): one shared export style module.
**D-037** (T7): AI transparency is consultant-facing only; the client stays
AI-silent per the §6.4 boundary in `home/page.tsx`. (D-034 is TAKEN by
hotfix PR #49.) One migration: `0034_zt_narratives` (T3, additive; 0033
belongs to PR #49).

**Cut order if the sprint must shrink:** (1) T9, folding a minimal em-dash
pass into T10; (2) T7's HowAiWorks disclosure (keep the banner mounts, the
honest fixture copy, and the risk badge); (3) T3's migration half (keep the
`build_roadmap()` section + heatmap; narratives stay run-response-only and
0034 moves to Sprint 11); (4) T6 trimmed to the CSF stepper + Impact Profile
explainer + home legend. Never cut T0-T2, T4, or T8.

## Prerequisites / launch checklist

1. **Wait for both open hotfix PRs to merge BEFORE cutting the sprint
   branch:**
   - PR #49 `fix/auth-refresh-reuse-storm`: the 15-minute forced sign-out
     fix (web refresh chain-cache in the new
     `apps/web/src/lib/auth/refresh.ts`; backend anchored one-step refresh
     reuse grace with migration `0033_user_prev_refresh_jti`; typed
     `refresh_expired`). It takes **D-034**.
   - PR #50 `fix/export-pdf-headers`: `html.escape()` inlined on the header
     Paragraph pair in all five exporters; four export routes now pass
     `service_display_label(kind)` (promoted public in
     `app/deliverable_release.py`) in place of the org-prefixed
     `Service.title`; sign-out button styled. T0 hoists these inline escapes
     into the shared style module, so #50 must be on `main` first.
2. Run the Codex read-only review of this plan, then merge this planning PR.
3. `git checkout -b feat/defensible-reports-sprint-10 main` BEFORE the first
   fire.
4. Archive the old runtime queue if one exists on your box, then COPY
   `.claude/sprint-queue.sprint-10.json` to `.claude/sprint-queue.json`; set
   `working_dir` + `expected_gh_user` for YOUR box; confirm the `gates` array
   matches your environment (six gates unchanged from Sprint 9).
5. The human dev launching this sprint runs `/loop-sprint-cron` themselves;
   agents do NOT start the loop.
6. No live-AI or cloud credentials needed; the LLM stays in fixture mode for
   the entire sprint. **Launch note for Dave's post-sprint live-Vertex flip
   (env-only, per D-029):** `SHIELD_LLM_MODE=live` +
   `SHIELD_LLM_PROVIDER=vertex` + a valid `SHIELD_LLM_MODEL` + ADC. NEVER
   committed; fixture stays the CI/demo default; e2e always runs fixture.

## Environment facts the loop must know

All CLAUDE.md gotchas hold, plus:

- **THE FIXTURE-CYCLE PIN, this sprint's e2e landmine:** the deterministic
  status/stage/score cycles in `app/ai/fixtures.py` (`_MITRE_STATUS_CYCLE`,
  the zt current/target arithmetic, the csf dimension arithmetic) are
  BYTE-FROZEN. s5's "AI 60%" and changed-count assertions depend on them. T4
  deepens PROSE ONLY. One literal prose pin moves WITH the prose:
  `s5-attack.spec.ts:151` pins the fixture rationale sentence, and T4
  updates spec pin + prose in the same commit. The structural pins that must
  keep behaving identically: `s4-techdebt:115/119/134` (the exact "AI 60%"),
  `s5-attack:119/131/194` (changed-count/tool/status), `s6-zt:186`,
  `s7-csf-playbook:238/249` (changed-fields including `what_we_found`).
- **New python module `app/export_style.py` (T0) needs
  `docker compose restart api`** (uvicorn --reload may miss new files).
  Never restart api mid-pytest (SIGKILL 137).
- **Migration 0034 (T3):** apply in-container (`docker compose exec -T api
  alembic upgrade head`) before any later e2e; unit tests build their own
  SQLite schema.
- **Re-seed after T4** (`docker compose exec -T api python
  scripts/seed_demo.py`, idempotent) so demo rows carry the new evidence
  before T8's suite.
- **NO new dependencies, compose changes, or feature flags this sprint.**
  pypdf, openpyxl, reportlab, and python-docx are already installed; anything
  that needs `docker compose build` is a plan violation.
- T0's color ramps: consult the `/dataviz` skill (sequential ramp,
  AA-checked text on fills) and document the brand hexes against the
  `packages/design-system` tokens.
- Load `/writing-style` before authoring T5's guidance content and before
  T9's sweep.
- After ANY `apps/web` source edit: `docker compose up -d --force-recreate
  web` before e2e (T5/T6/T7 touch web; T9 usually will).
- Playwright traps (recurring): `getByRole` name matching is SUBSTRING;
  `click()` + `waitForResponse` on auto-save controls; assert post-Run-AI
  state after `page.reload()`; spec-created users need unique timestamped
  emails.

## Tasks

### T0: Shared export style module + five-exporter adoption (D-036)

- New `apps/api/app/export_style.py`, the single home for deliverable
  styling:
  - Brand hexes documented against the `packages/design-system` tokens: ink
    `#0e1220`, border `#d6dae3`, sunken `#eef2f7`, brand navy `#1b3a7a`.
  - `LEVEL_HEX` relocated from `playbook_export.py:204-210` (re-exported
    there for compat).
  - `graded_hex(level, n_levels)` for arbitrary ladders; out-of-range input
    RAISES (fail loudly), never clamps.
  - `coverage_hex(pct)`, a 0-100 sequential ramp.
  - `escaped_title(service_title, client_name)`: HOIST hotfix PR #50's
    inline `html.escape()` calls into this one helper and replace them at
    all five call sites.
  - reportlab helpers: `table_style()`, `new_pdf_doc()` (page geometry,
    author), and a color-column helper generalizing
    `playbook_export._pdf_table`'s `color_col`/`color_levels`.
  - openpyxl header-styling + cell-fill helpers.
  - docx shading reuses `app/docx_export.py:40-50` `shade_cell` (import it,
    never duplicate it).
- Adopt in all five exporters (`app/{tech_debt,attack,csf,zt,risk}/exporters.py`)
  plus `playbook_export.py`. The risk PDF 5x5 matrix
  (`risk/exporters.py:242-259`) gets graded severity fills via the shared
  helper (counts unchanged).
- Consult the `/dataviz` skill for ramp construction: a sequential ramp with
  AA-checked text on fills.
- TDD-first in new `tests/unit/test_export_style.py`: ramp boundaries;
  out-of-range raise; `escaped_title` escapes `&`/`<` and never duplicates
  the org name; the `table_style()` command contract.
- Parity CONTRACT tests, beyond the unchanged content tests (Codex
  should-fix): per-exporter page geometry preserved (the four service
  exporters use 0.6in margins, the playbook 0.7in; the shared
  `new_pdf_doc()` PARAMETERIZES margins, never unifies them), the table
  style-command contract per exporter, PDF page-count pins on a fixed
  context, and XLSX column-width/wrap/alignment pins for the sheets T1-T3
  will widen.
- All existing exporter content tests pass UNCHANGED: the refactor may not
  alter any rendered text.
- New module under `app/` means `docker compose restart api`. Append
  **D-036** to DECISIONS.md.

### T1: ATT&CK deliverable renders the curated evidence + tactic heatmap (D-035)

- Coverage sheet gains Detection tools / Prevention tools / Response tools /
  Rationale columns (lists joined with `", "`) plus an Evidence reference
  column: resolve the attached artifact's filename from
  `evidence_artifact_id` in the route context builder (a cheap join); render
  "No evidence attached" when NULL. Never invent anything.
- Gaps sheet gains Rationale plus a derived Direction cell, PURE CODE over
  existing fields. **SOURCE-FAITHFUL (Codex blocker):** Run AI overwrites
  every unlocked row's tools/rationale (`routes/attack.py:593-599`), so
  these fields are AI-applied unless the consultant edited or locked them,
  and no acceptance state exists yet. Direction cells state citation facts
  only: "No detection, prevention, or response tool is cited for this
  technique", or "Cited: \<tools\> (partial)". Never causal or remediation
  inference.
- The Heatmap Summary sheet's Coverage % cells get `coverage_hex` fills.
- PDF/DOCX gap tables add the rationale (wrapped cell style) plus a computed
  defensibility stat phrased on citations: "N of M scored techniques cite at
  least one tool". The PDF/DOCX methodology note discloses provenance: tools
  and rationale are drafted by Run AI and consultant-editable, a per-row
  lock exists, and substantiation states land in Sprint 11.
- **D-035** stated in DECISIONS.md and recording exactly this label
  discipline: Direction and the stat state citation facts only; no
  remediation column, no migration, no prompt change this sprint. The gap
  plan derives from what the consultant already curated; per-claim
  substantiation status is Sprint 11's evidence model.
- TDD-first: extend `tests/unit/test_attack_exporters.py` before touching
  the exporter: XLSX header contracts, the joined-tools cell, the
  citation-fact Direction line for a tool-less gap, PDF rationale substring
  + the citation-phrased stat, DOCX gap rationale, heatmap fill via
  `cell.fill.start_color`, a row with an attached artifact renders its
  filename and a row without renders the explicit empty state.

### T2: CSF released deliverable adopts the POA&M machinery + tier heatmap

- The CSF release/export path in `routes/csf.py` loads the assessment's
  `CsfGapAction` rows and passes them into `build_context`.
- XLSX Gap Plan gains Characterization / Owner / Deadline / Resources /
  Success criteria / POA&M ref, with `priority_override` winning (mirror the
  `playbook_export.py:137-178` contract).
- PDF/DOCX gain an Action Plan section, a tier-model methodology block built
  from `TIER_DEFINITIONS` (do NOT copy the playbook's five-dimension
  METHODOLOGY; that text describes a different scoring model), and computed
  next-steps sentences (adapt the `_next_steps()` shape to tier-gap data;
  computed prose only).
- Answers-sheet Tier cells + per-function Average-tier cells get
  `graded_hex(tier, 4)` fills; PDF/DOCX color columns via the T0 helper +
  `shade_cell`.
- Evidence reference on the Answers sheet (and the PDF answer/gap tables
  where sane): resolve the attached artifact's filename from
  `CsfAnswer.evidence_artifact_id` in the route context builder (a cheap
  join); render "No evidence attached" when NULL.
- TDD: extend `tests/unit/test_csf_exporters.py` (Gap Plan header contract;
  an action row renders owner/deadline; override wins; PDF tier-definition
  substring + a next-step line; an answer row with an attached artifact
  renders its filename, a row without renders the explicit empty state) and
  `tests/unit/test_csf_deliverable_routes.py` (the route loads gap actions;
  a zero-actions assessment still renders, the C0 pattern).

### T3: ZT roadmap + persisted AI narratives, migration `0034_zt_narratives` (HIGHEST RISK)

- Migration `0034_zt_narratives`: `zt_assessments` gains `roadmap_summary`
  Text, `executive_summary` Text, `pillar_narratives` JSON (the
  `JSON().with_variant(JSONB, "postgresql")` pattern from
  `attack_assessment.py:34`). All three nullable, `batch_alter_table`,
  additive (C0: older rows parse unchanged).
- **ATOMIC PERSIST (Codex blocker):** the existing shape is check-then-write
  (flush answer mutations, re-read parent status at `zt.py:504`, then
  write), which leaves a window where a discard commits between the read and
  the write. The narrative/`documents_stale` persist therefore rides a
  CONDITIONAL parent `UPDATE ... WHERE status IN (<the editable statuses>)`
  requiring exactly one affected row (the D-031 conditional-UPDATE pattern
  from Sprint 9 T0), or a row lock held through commit. A racing discard
  loses loudly; the run response is unchanged.
- The new columns must LEAVE THE API explicitly (Codex should-fix):
  `ZtAssessmentResponse` (`schemas/zt.py`, which stops at
  `client_target_stage` today) gains the three fields as optional, with
  `pillar_narratives` defaulting to `None` (never a mutable `{}`); the
  manual field enumeration in `routes/zt.py` `_serialize_assessment`
  (`:159`) is extended; the web `ZtAssessment` type
  (`apps/web/src/lib/zt/types.ts:52`) gains the three fields as optional.
- Every persisted-narrative write sets `documents_stale` via the existing
  mechanism (the `routes/zt.py:1371` area) so finalize re-renders the
  approved assessment; a test pins it.
- Exporter: a new Roadmap section from `build_roadmap(gap.gaps)`
  (month/capability/pillar/current→target; code-computed sequencing).
- Per-pillar narrative section + summary paragraph rendered only when
  persisted: absent means the section is omitted, never an empty header.
  Label them "Assessment narrative" / "Consultant summary"; the deliverable
  is consultant-owned prose, and AI attribution lives in the methodology
  note the way the playbook does it.
- Framework-aware stage heatmap: `graded_hex(stage, level_count(framework))`
  (DoD is a 3-rung ladder, CISA 4) on Answers Stage cells + per-pillar
  averages; PDF/DOCX color columns.
- Evidence reference on the Answers sheet (and the PDF answer tables where
  sane): resolve the attached artifact's filename from
  `ZtAnswer.evidence_artifact_id` in the route context builder (a cheap
  join); render "No evidence attached" when NULL.
- TDD: extend `tests/unit/test_zt_exporters.py` (roadmap month/capability
  contract; narrative renders when set; no empty section when NULL; the DoD
  ramp uses 3 rungs; an answer row with an attached artifact renders its
  filename, a row without renders the explicit empty state) and
  `tests/unit/test_zt_run_ai.py` (fields persisted post-run;
  `documents_stale` set on persist; THE RACE TEST exercises the
  interleaving AFTER the status check via a monkeypatch/hook between check
  and write that injects the discard, and the persist loses; a discard
  arranged before the check proves nothing about this window); a
  NULL-columns parse case in `tests/unit/test_zt_routes.py`.
- Gotcha: `alembic upgrade head` in-container before any later e2e.

### T4: Demo evidence depth: seed + fixtures + tech-debt narrative

- `scripts/seed_demo.py`: replace the every-25th hardcoded sentence
  (`:811-815`) with systematic structured evidence. Covered/partial rows get
  deterministic detection/prevention/response tools drawn from the seeded
  Atlas capability names plus a per-(status, tactic) rationale sentence; gap
  rows get a rationale explaining the miss; a deterministic subset of CSF/ZT
  answers gets evidence-flavored notes; the seeded ZT assessment gets
  `roadmap_summary`/`pillar_narratives` (the T3 columns) so regenerated demo
  deliverables show the full shape. Idempotency preserved.
- `fixtures.py`: deepen PROSE ONLY. THE FIXTURE-CYCLE PIN applies: the
  deterministic status/stage/score cycles (`_MITRE_STATUS_CYCLE`, the zt
  current/target arithmetic, the csf dimension arithmetic) are BYTE-FROZEN;
  s5's "AI 60%" and changed-count assertions depend on them. `mitre_map`
  rationale becomes technique-aware sentences naming the cited tool;
  `zt_score` gets full per-pillar narratives + a multi-sentence roadmap
  summary; `csf_score` `what_we_found` becomes a real finding sentence;
  tech-debt fixture rows gain category inference + fuller function
  sentences. All deterministic pure functions of the payload.
- Tech-debt narrative bump (Dave's ask): a computed portfolio paragraph in
  `app/tech_debt/exporters.py` PDF/DOCX/XLSX summaries (counts by
  disposition, top cost drivers, savings framing including the existing
  lower-bound caveat). Computed sentences only.
- **Pin alignment (Codex should-fix):** e2e `s5-attack.spec.ts:151` pins the
  literal fixture prose "Fixture-mode draft coverage assessment for T1001";
  the rationale deepening MUST update that pin in the same commit
  (alignment, never weakening). The structural pins that must keep behaving
  identically: `s4-techdebt:115/119/134` (the exact "AI 60%"),
  `s5-attack:119/131/194` (changed-count/tool/status), `s6-zt:186`,
  `s7-csf-playbook:238/249` (changed-fields including `what_we_found`).
  Prose-only changes keep the same FIELDS populated so changed-counts do not
  shift.
- TDD: extend `tests/unit/test_ai_runtime_fixtures.py` FIRST (rationale
  names the cited tool; regression pin: the cycles are unchanged) and
  `tests/unit/test_exporters.py` (the tech-debt narrative contract).
- Re-run the idempotent seed after; re-point the SMOKE §26 boxes.

### T5: Questionnaire guidance: make every question answerable

- Per-question "What do these levels mean?" disclosure in the question card
  (`CsfQuestionnaire.tsx` / `ZtQuestionnaire.tsx`, which serve BOTH the
  admin and client renders), rendering the full level descriptions + a
  worked example scenario.
- DO NOT touch picker internals: `TierPicker` / `ZtStagePicker` keep their
  roving-tabindex / select-on-Enter contract (the auto-save PATCH-flood
  comment at `TierPicker.tsx:32-37`).
- Content authoring is the task's real work: a new
  `apps/web/src/lib/guidance/` module. Per-tier generic plain-language
  explainers ("what does Risk Informed mean" in client words) + one worked
  example per CSF function per tier (6x4 short scenarios) + one per ZT stage
  (CISA 4 + DoD 3). Descriptions mirror `TIER_DEFINITIONS` / `CISA_STAGES` /
  `DOD_STAGES`, with a vitest parity pin on the four tier labels + the stage
  labels so web and backend text cannot drift. Author under
  `/writing-style` rules.
- Expose the interview prompts to clients: `CsfSelfAssessment.tsx` fetches
  `GET /csf/services/{id}/questionnaire` (already any-role tenant-scoped,
  `routes/csf.py:226-238`, so ZERO backend change) and passes
  `questionsByCode` with a client-appropriate label ("Consider:" in place of
  "Interview ·").
- New `CsfMaturityReference.tsx` (a mirror of `ZtMaturityReference.tsx`)
  linking NIST CSF 2.0 (CSWP 29), mounted beside both CSF questionnaires.
  The Notes textarea gets instructive copy ("Name the tool, policy, or
  process behind your answer: 'Okta enforces MFA for all staff' beats
  'yes'.").
- TDD vitest-first: guidance content tests (every tier/stage has a
  description + an example; the parity pins); `CsfQuestionnaire` renders
  guidance + prompts in the client configuration; the notes copy test.
- The web-recreate dance applies.

### T6: Workspace + platform comprehension

- New shared `components/admin/WorkflowSteps.tsx` (+ test): a static ordered
  step strip with the current step derived from assessment/list status,
  rendered in all four workspaces with per-service step copy. The CSF/ZT
  copy includes an explicit line: "you review and edit the client's answers;
  they see the outcome, and you own the quality". This extends the lone
  banner at `CsfWorkspace.tsx:385-394`, which stays.
- `CsfPlaybookPanel.tsx`: a header legend/disclosure explaining Tiers (H/M/L
  working-profile levels), Enterprise (the weighted-floor roll-up), Rule
  (the #n roll-up rule), and the Gap priority chips (`:70-109`).
- `/admin/management` purpose copy; the `HomeDashboard.tsx` "Your services"
  status legend explaining the five `phaseFor` labels (`:76-93`); an Impact
  Profile explainer where `profileLabel` renders
  (`CsfSelfAssessment.tsx:253-261`): the FIPS-199 band set at intake scopes
  which outcomes apply.
- TDD vitest-first: the WorkflowSteps step-highlight table; the legend
  disclosure renders; the home legend labels.
- Scheduled before T7 (same workspace files).

### T7: AI transparency, consultant-facing (D-037)

- Mount `AiStatusBanner` in the three unbannered workspaces (attack, csf,
  zt).
- Fix the fixture-mode lie: the `routes/admin.py:502-512` detail becomes "AI
  runs in offline fixture mode: Run AI returns deterministic demo drafts,
  not live model output". The banner distinguishes tones (fixture=info,
  live-misconfigured=warning). Pytest on the detail copy
  (`tests/unit/test_admin_routes.py`); vitest on both tones.
- An "AI suggested" provenance badge on risk-register rows: origin/trust
  already exist (`models/risk_register.py:87-88`) and are already fetched.
  Badge only where it is cheap; admin surface only.
- New compact `HowAiWorks.tsx` disclosure near Run AI in the four
  workspaces: what AI drafts per service, what code computes, the redaction
  gate, fixture-vs-live.
- The client boundary (D-037): ZERO client-surface changes; the §6.4
  AI-silent comment in `home/page.tsx` is the review criterion. Append
  **D-037** to DECISIONS.md.

### T8: e2e proofs + SMOKE §33/§34/§35

- Extend existing specs; add only one new file. `s3-selfassessment.spec.ts`
  (client sees tier guidance, an interview prompt, the notes helper copy);
  `s6-zt.spec.ts` (stage guidance; the DoD ladder shows 3 stages);
  `s7-csf-playbook.spec.ts` (column legend + stepper); `s4`/`s5` (the
  fixture-info banner is visible).
- One new `s27-comprehension.spec.ts`: the management purpose copy, the home
  status legend, the risk AI-suggested badge, the HowAiWorks disclosure.
- Deliverable-content proof stays unit-level (the Sprint 9 T2 pattern owns
  the bytes); e2e re-proves that one released download transports.
- One PDF acceptance contract per service (Codex should-fix), unit-level
  over real bytes in the existing exporter test files: assert SECTION ORDER
  via extracted-text index ordering plus one representative linkage (a
  score, its evidence/citation reference, and its gap/action appear in the
  expected sequence). Visual legibility/clipping stays SMOKE §10's single
  manual line.
- New SMOKE §33 Defensible deliverables (boxes cite the T0-T4 unit test
  filenames), §34 Questionnaire guidance (spec filenames), §35 Workspace
  comprehension + AI transparency (spec filenames); §26 re-pointed to the
  evidence-rich seed; §10 keeps exactly its one manual aesthetics line, now
  also covering heatmap coloring (the only thing tests cannot see in a PDF).
- Full host e2e suite green: `--force-recreate web` first, `alembic upgrade
  head` applied, stack re-seeded.

### T9: Prose scrub (the /writing-style sweep)

- Load the writing-style skill; sweep UI copy and export/fixture/seed prose,
  including everything T1-T7 authored, for the house ruleset.
- Code identifiers, log prefixes, and UI glyphs are exempt.
- Where the scrub changes a substring a unit test pins, update prose + pin
  together (alignment, never weakening).
- Prettier + all six gates after.
- FIRST TO CUT if the sprint shrinks; a minimal em-dash pass folds into T10.

### T10: Wrap-up

- SMOKE final pass (§10 note, §26, §33-§35); every box checked only with its
  proving spec or test filename.
- CHANGELOG `[3.6.0]` per-task entries with commits; BUILD_REPORT sync (gate
  results at HEAD, e2e spec count, migration 0034, D-035/D-036/D-037).
- `CONTEXT.md` overwritten with the end-of-sprint snapshot; the LAUNCHING
  dev's own `context/<name>.md` refreshed (owner-only rule).
- Verify no live-LLM config leaked into committed files: Dave's live-Vertex
  flip is a launch-notes item in this doc only (env-only per D-029; NEVER
  committed; fixture stays the CI/demo default; e2e must run fixture).
- Full exit gate set (all six) + full e2e on a quiet box; carry the deferred
  list forward.

## Definition of done

- The ATT&CK deliverable (XLSX/PDF/DOCX) carries the curated
  detection/prevention/response tools and rationale on every scored row, a
  citation-fact Direction on every gap, an Evidence reference (artifact
  filename or the explicit "No evidence attached"), `coverage_hex` heatmap
  fills, the citation-phrased defensibility stat, and the provenance
  methodology note; unit tests over real bytes prove each.
- The released CSF deliverable carries the POA&M action plan (override
  wins), the tier-model methodology, computed next steps, graded tier
  fills, and the Evidence reference; a zero-actions assessment still
  renders.
- The ZT deliverable carries the code-computed roadmap, the Evidence
  reference, and, when persisted, the narratives; the persist is a
  conditional parent update that a racing discard defeats even after the
  status check; `documents_stale` is set on persist; the new fields reach
  the API response and the web type; migration 0034 is additive and
  SQLite-safe; NULL columns parse (C0).
- All five exporters plus the playbook draw styling from one tested module;
  hotfix #50's inline escapes live in `escaped_title()`; per-exporter parity
  contracts hold (margins parameterized 0.6in/0.7in, page counts, XLSX
  column widths); no existing content test changed.
- The demo seed and fixtures produce evidence-rich deterministic output; the
  fixture cycles are byte-identical; s5's assertions pass untouched.
- A client can answer every questionnaire item: level guidance + worked
  examples in both renders, interview prompts on the client surface, parity
  pins on the tier/stage labels.
- All four workspaces show the workflow stepper and the AI status banner;
  the fixture copy tells the truth; the risk register badges AI-suggested
  rows; the client surface is byte-silent on AI (the §6.4 boundary).
- SMOKE §33/§34/§35 are spec-backed; §26 is re-pointed; §10 keeps its single
  manual line; one PDF acceptance contract per service asserts section order
  and a score-evidence-action linkage; `s27-comprehension.spec.ts` is
  committed and green; the full suite is green.
- D-035/D-036/D-037 appended in their tasks; no live-LLM config committed;
  every commit conventional and task-scoped; CONTEXT.md snapshot written.

## Explicitly out of scope (needs-Dave / later)

- **Loop launch**: the human dev at the keyboard starts `/loop-sprint-cron`;
  agents never do.
- The per-claim evidence/substantiation model and the client evidence-attach
  UI: Sprint 11. This sprint renders references to artifacts already
  attached via the admin PATCH (filename or the explicit empty state) and
  nothing more; D-035 keeps the sprint to derivation over already-curated
  fields (no remediation column, no attack migration, no prompt changes).
- Any client-facing AI disclosure (D-037; the §6.4 AI-silent boundary in
  `home/page.tsx` stays intact).
- The live-Vertex flip itself: post-sprint, env-only, per D-029; never
  committed.
- New dependencies, compose changes, or feature flags of any kind.
- §10 visual aesthetics (the one explicitly-manual line remains, now also
  covering heatmap coloring).
- ESLint 10 + the `postcss` moderate (upstream-blocked, D-018).
- Sprint 9's deferred list carries forward: full token federation, JIT
  provisioning, migrating register/MFA/email flows into Keycloak,
  `email_verified_at` stamping, un-discard/recovery; cloud deploy /
  terraform / DR runbooks; FedRAMP LLM connector;
  `azure_openai`/`bedrock`/`local` adapters (loud not-implemented).
