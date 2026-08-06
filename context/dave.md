# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-08-05 (Sprint 10 complete on its branch through S11; the loop
ran S0 through S11 and stopped at push, no PR. The 2026-08-05 pass corrected the
box count and pulled the shutdown audit's findings forward)._

## Branch / in flight

- **`feat/defensible-reports-sprint-10` (this branch, targeting `v3.6.0`):** the
  autonomous loop ran twelve sprints (S0 through S11) against `docs/SPRINTS.md`.
  **Ten boxes are checked, not eleven. Two are open: S9 and S11.** The earlier
  reading of this file said one, which is the same false claim the shutdown audit
  found in CHANGELOG, BUILD_REPORT and CONTEXT.md and corrected in `575f17c`. S9
  carries two `needs-human` criteria, S11 carries one, and all three trace to two
  facts: the interview prompt has no data path anywhere, and no green full-suite
  e2e run exists on this box. The shutdown ceremony stopped at push because the loop
  was started without `--pr`, so **opening the PR is yours**.
- **This branch is 1 commit behind `origin/main`.** `41f194c` (PR #57, merged
  2026-08-05) is a one-line change to `.claude/settings.json` that makes the
  PreToolUse hooks match PowerShell calls as well as Bash. Until it lands here, the
  guards do not fire on a PowerShell tool call on this branch. Merge it in before
  opening the PR.
- **Nothing else in flight.** No open PRs. PR #53 (ops pipeline), the identity
  self-heal (#56) and the hook matcher (#57) are all merged to `main`.

## What needs you, in the order I would do it

0. **`app/csf/playbook_export.py` tells a real client they have no gaps when no
   target has been set.** Shutdown-audit HIGH-1, and it outranks everything below
   including the old number 1. It is a second CSF exporter that S3's honesty fix
   never touched: 0 coverage-qualifier phrases against 18 in `csf/exporters.py`. At
   `routes/csf.py:1128`, `gap = is_gap(rollup.score, target) if target is not None
   else False` makes "no target recorded" and "target met" the same value, and
   `target_level` is nullable with `csf.py:1331` writing `None` explicitly. **This
   fires on the default state of a real engagement, not on an empty input.** The
   same file also manufactures 91 Priority 1 criticals from unscored rows when
   targets are set (HIGH-2), because `maturity_level(0)` returns 1. Both are claim
   changes on a client-visible deliverable, so per D-035 they are your call rather
   than an agent's scrub. Full finding set in `CONTEXT.md` under H1 to H5.
1. **Open the Sprint 10 PR.** The body wants: the twelve-sprint task table with
   commits (it is in `CHANGELOG.md` `[3.6.0]` and `CONTEXT.md` already), the three
   `needs-human` criteria across S9 and S11 stated plainly, and the deferred list
   including H1 to H5. Opening it is also what produces the first green CI `e2e`
   run, which is the honest arbiter for the full-suite question below. Decide first
   whether H1 blocks the merge; it ships a client-facing false statement.
2. **Decide what a client sees when their answer fails to save.**
   `CsfSelfAssessment.tsx:173` is a bare `catch {}` around the answer PATCH. It
   predates the batch, and this batch made it worse in effect rather than in code: S3
   made the CSF deliverable honest about unscored subcategories, so a silently lost
   answer now produces a report that truthfully tells a client they never answered a
   question they did answer. The fix is small; the product call (inline error, retry,
   blocking toast) is yours. **This is the highest-value item out of the whole
   batch.**
3. **Decide whether the CSF tier questionnaires get loaded into the demo
   database.** `scripts/load_csf_tier_questionnaires.py` has never been run here and
   is invoked by nothing: not CI, not compose, not `demo-reset`. So the `questions`
   table is empty, `questionsByCode` is always `{}`, and the client interview prompt
   cannot render for any real user. S6 was credited for that feature on a mocked
   vitest. Running reference data into a shared database is a human decision, which
   is why the loop left it. SMOKE §34 carries the unchecked box.
4. **Decide whether to run `demo-reset --demo`.** S5's evidence-rich seed is in code
   only: `seed_demo.py` returns early whenever any `Service` row exists, so this
   box's demo rows still carry the pre-S5 ATT&CK evidence. Only a wipe picks it up,
   and that path is destructive and opt-in per D-033. SMOKE §26's box stays unchecked
   until a spec reads the new evidence off a database that actually seeded it.
5. **Schedule the e2e sign-in infra work.** It is NOT a timeout bump:
   `e2e/helpers/auth.ts:60-63` already wraps a 15s `waitForURL` in
   `toPass({ timeout: 60000 })` and still loses, because the post-login chain pays
   three sequential cold compiles and each retry can re-enter them. Warming `/`,
   `/sign-in`, `/admin` and `/admin/queue` before the run is what got S11's run its
   result; that warm-up belongs in the harness, not in an operator's head.
6. **The lockfile bump.** Root `pnpm audit` is **5 high + 2 moderate**, not the 1
   high + 1 moderate the docs used to claim: `sharp@0.34.5`, `postcss@8.4.31` (4
   advisories, 2 high), and `brace-expansion@1.1.16` (2 high, previously undocumented
   anywhere). None is branch-introduced. Dependabot or a root pnpm override on `main`.
7. **Sprint 11 "Evidence and access" planning PR**, with **dark mode pulled out** of
   it, then the visual-system batch. Both unchanged from the last plan.

## Not done, by decision

- **Gene has no identity mapping and cannot push.** `identity.sh` maps one owner to
  one email, which conflates "which company authors this repo" with "which human is
  pushing". Supporting a second developer means a per-repo allowlist of (email,
  gh-account) pairs. You said not to worry about it on 2026-08-03, so it is
  deliberately unbuilt rather than forgotten.
- **The visual system is still unchosen**, so S0 and S1 built the groundwork and
  stopped. S1's brand-navy 7-step ramp is AA-checked and **renders nothing yet**:
  adopting it would change a colour clients have already received. Recommendation is
  still Ledger, and the pick takes a D-number.

## How the loop behaved, worth knowing before the next one

- **Nine of eleven executed sprints had at least one defective acceptance
  criterion.** One was structurally unrunnable (a vitest pin against Python constants
  in a directory the web container does not mount). One was already satisfied before
  the work began. One named two surfaces and could only fail on one. One could not
  fail by construction. Several passed on a bare no-exception. Every one was caught
  by a runner reading its own criterion sceptically and substituting a check that
  bites, then saying so in the Log. **When you write the Sprint 11 criteria, check
  that each evidence command is RED on the tree the sprint starts from.** That single
  habit would have caught all nine.
- **The empty-input render is the cheapest review tool in this repo.** Three of four
  services printed something untrue when given nothing to say, and each passed every
  test it had, because every zero-case those tests exercised used a fully scored
  assessment. Two got fixed mid-batch because a driver rendered the report from
  nothing and read it.
- **The loop survived a process exit mid-sprint (S8)** with its work uncommitted and
  the tree intact; it was resumed from transcript rather than respawned. Its first
  gate after resuming correctly reported BLOCKED because Docker Desktop had died,
  instead of reading five unreachable steps as green.
- **S7 disclosed its own TDD violation** (component written before test, no red run
  observed). The driver reverted the component and re-ran to get a recovered check.
  A runner that had quietly reordered its narrative would have produced an
  identical-looking green sprint, which is the argument for keeping the disclosure
  culture in the prompt.

## Before the loop runs

- **The gh account** self-heals at SessionStart (`.claude/setup.sh` switches back if
  the expected account is already authenticated). It is machine state shared by every
  repo on the box, so it drifts when another project needs a different account. It
  only ever switches to an account already logged in; it never prompts.
- **`.env` is `SHIELD_LLM_MODE=fixture`** and stayed that way for the whole batch.
  Fixture is what the sprints and e2e require. Set it to `live` plus
  `docker compose up -d --force-recreate api` when evaluating real Run-AI output, and
  revert after.
- **Web is `:3001` on this box.** `e2e/helpers/baseUrl.ts` resolves it; never
  hardcode a port in a spec.
- **Migration 0034 is applied here** (`alembic current` reports `0034 (head)`). After
  any `apps/web` edit, `docker compose up -d --force-recreate web` before e2e; a new
  python module under `app/` needs `docker compose restart api`.

## Decisions made / carried (recorded for agents)

- **The 2026-07-23 walkthrough set the roadmap:** hotfixes, then Sprint 10 "Reports
  you can defend" (done), then Sprint 11 "Evidence and access" (substantiation model
  tool-present/configured/validated, per-claim evidence attach plus post-intake
  upload, client inbox, client risk-register release, client self-start), with **dark
  mode moved out** into the visual-system batch.
- **Numbering ledger:** the hotfix took 0033 + D-034; **Sprint 10 took 0034 +
  D-035/D-036/D-037, SMOKE §33 to §35, and spec s27** (all now spent). Sprint 11
  takes 0035/0036 + D-038 through D-042, SMOKE §36 to §40, specs s28/s29.
- **Keycloak SSO stays at hybrid depth** (D-032); infra stays local containers.
- **Live-Vertex is env-only and never committed** (D-029). The batch needed no
  credential of any kind.

## Carried, not scheduled

- The five high and two moderate advisories above, all wanting one lockfile bump.
- **Dependabot #47 merged** (`25c0d8a` on `main`, npm-minor-patch, 6 updates). This
  file previously called it open, which is stale. Its effect on the 5 high and 2
  moderate count is **unmeasured**: that audit was taken on this branch, which does
  not carry the bump, so re-run `pnpm audit` on `main` before quoting the number
  again.
- **Three phantom Tailwind tokens, and the sweep is now done.** `border-border-default`
  (7 uses across 5 files) and `bg-surface-default` at `AiPreviewButton.tsx:106`,
  which the shutdown audit's systematic served-CSS sweep of all 55 colour utilities
  found after S0 had swept `surface-muted` alone. The sweep that was the recommended
  fix has therefore happened once by hand; making it a gate step is what stops a
  fourth.
- **Shutdown-audit HIGH-3, HIGH-4 and HIGH-5**, none of them one-pass fixes. H3: the
  dict-detail cast at `ZtWorkspace.tsx:68-79` renders an object as a React child and
  crashes the workspace on a lost Run-AI race, with the same bad cast at 16 sites
  across 15 files. H4: `fixtures.py:209` splits ZT codes on `.` so every pillar
  narrative is filed under `"CISA"` or `"DOD"`, and no web surface renders
  `pillar_narratives` to catch it. H5: `seed_demo.py:797` writes Python-computed
  narratives under an exporter note claiming Run AI drafted them.
- **Cannot-fail tests found across the suite.** Heatmap-fill assertions pinning only
  that a fill was applied, length-not-value assertions, and an `AiStatusBanner` case
  awaiting two microtasks where the state needs four. Green tests that would stay
  green with the guard removed.
- One consistent absent-versus-zero treatment for the four summary headers. ZT
  already carries the pattern, so this is copying, not deciding.
- `/admin/management` is named in S7's Scope line with no acceptance criterion
  anywhere. Either give it one or delete the scope line.

## Notes for Gene

- **The `.claude/` hooks are committed, so they apply to you too.** Before your
  first push here: `git config --local user.email` must be
  `davidcatarious@spearheadanalytica.com` and the active gh account must be
  `SpearheadAnalytica`, or `identity.sh` refuses every `git push` and every `gh`
  call. That mapping is Dave's account boundary and it currently has no entry for a
  second developer; if you need to push under your own identity, say so and the
  `case` block in `.claude/hooks/identity.sh` gets a `gene-png` mapping.
- Gate commands live in one place, `.claude/profiles/shield.sh`, run via
  `bash .claude/hooks/run-gate.sh commit|push`. They need Docker Desktop running and
  the stack up, because everything except prettier runs in the containers. Green
  prints `gate: shield/push passed (7 steps)`; a smaller step count means the gate is
  broken, not that it passed.
- **The loop's plan of record is `docs/SPRINTS.md`**, and its Log is the primary
  record of what happened in Sprint 10, including what the driver rejected and
  re-verified. Read the Log before the diff.
- `demo-reset --demo` is destructive; never run it implicitly. Opt-in specs
  unchanged (`s26` on `E2E_OIDC`, `demo/` on `SHIELD_DEMO_SMOKE`).
- Lint pins unchanged: `ruff==0.15.20` / `black==26.5.1` exact,
  `known-first-party=["app"]` in root pyproject; do not remove.
</content>
