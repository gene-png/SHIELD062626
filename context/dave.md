# Dave: current status

_Owner: Dave (SpearheadAnalytica). Only Dave's sessions write this file._
_Last updated: 2026-08-04 (Sprint 10 "Reports you can defend" complete on its
branch through S11; the loop ran S0 through S11 and stopped at push, no PR)._

## Branch / in flight

- **`feat/defensible-reports-sprint-10` (this branch, targeting `v3.6.0`):** the
  autonomous loop ran twelve sprints (S0 through S11) against `docs/SPRINTS.md`.
  Eleven boxes are checked. **S9's box is deliberately open** on two `needs-human`
  criteria. The shutdown ceremony stopped at push because the loop was started
  without `--pr`, so **opening the PR is yours**.
- **Nothing else in flight.** `main` is clean; PR #53 (ops pipeline) and the
  identity self-heal merged before the launch.

## What needs you, in the order I would do it

1. **Open the Sprint 10 PR.** The body wants: the twelve-sprint task table with
   commits (it is in `CHANGELOG.md` `[3.6.0]` and `CONTEXT.md` already), the two
   `needs-human` criteria stated plainly, and the deferred list. Opening it is also
   what produces the first green CI `e2e` run, which is the honest arbiter for the
   full-suite question below.
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
- Dependabot **#47** (npm-minor-patch, 6 updates) still open and green.
- A second phantom Tailwind token, `border-border-default`, 7 uses across 5 files.
  S0 swept `surface-muted` only, so the class was never swept systematically. The
  real fix is a check that every colour utility resolves to a class Tailwind actually
  generates.
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
