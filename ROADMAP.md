# SHIELD Roadmap

_Rewritten 2026-08-06 by sprint, superseding the phase-based version of 2026-08-05.
Owner: David Catarious. Supersedes `DELIVERY_PLAN.md` (historical, Sprints 1 to 5) and
`IMPLEMENTATION.md` (the June 2026 v2 work order); both are kept as record._

**What this file is.** The sequence of work that closes SHIELD, one sprint per entry,
written so a reader learns what we are adding and why it comes where it does. It does
not restate the backlog. Per-item technical detail stays in `CONTEXT.md` (the deferred
list, including the H1 to H5 audit findings) and in the `docs/SPRINTS.md` Log. The
standing claim contract is `docs/PRINCIPLES.md`. When this file and `CONTEXT.md`
disagree on a fact, `CONTEXT.md` is the fact and this file gets corrected.

## Status as of 2026-08-06

Sprint 10 "Reports you can defend" **merged to `main`** as PR #58, merge commit
`874d0ca`, tagged toward `v3.6.0`. CI ran green on `bc4d1c4` across all five jobs,
including the full Playwright suite on a fresh runner in 13m19s. That run is the first
authoritative full-suite green the batch ever had, and it settles the question four
local attempts could not. The dev-box suite still cannot finish green, for a measured
reason, and that is now a test-infrastructure item rather than an open verdict.

Merged as a merge commit rather than a squash, deliberately: `CONTEXT.md` and the
`docs/SPRINTS.md` Log cite per-sprint SHAs, and a squash would have orphaned every one
of them.

**H1 is fixed** on `fix/h1-csf-playbook-export-honesty`, ahead of Sprint 11, because it
was the one finding that shipped a false statement on the artifact a consultant
actually hands over.

### Three decisions taken 2026-08-06

Each needs a D-number in the sprint that implements it.

1. **SHIELD adopts Ledger**, Variation 1 of `docs/design-systems.md`. The thesis is
   that the app is the instrument of record for an audit and should look like the
   document it produces. Cloud Mod is retrofitted to match, which retires
   `kentro.teal` as the primary brand ramp.
2. **Cloud Mod becomes SHIELD's fifth assessment service**, with its six-domain
   readiness rubric, AHP-weighted MCDA and CSP comparison ported from TypeScript to
   Python under `apps/api`. It feeds the Risk Register natively. The standalone
   deployment retires.
3. **Two claim mechanisms become gates**: the frozen claim inventory and the
   empty-input render test per exporter. Both are specified in `docs/PRINCIPLES.md`.
   An external golden set for the four existing engines was considered and not
   adopted; the reasoning is recorded there so it does not get rediscovered.

### What is proven

Roughly 25,900 lines of Python and 25,600 of TS/TSX, 34 migrations, 114 endpoints,
about 745 unit tests green in-container, 118 vitest cases, 28 Playwright spec files,
all green on CI's fresh runner. All four services plus the Risk Register drive end to
end in a real browser. "AI suggests, code computes" is enforced rather than
aspirational: the shutdown audit verified zero-line diffs on every scoring engine and
every prompt. The LLM egress seam is one client with a mandatory redactor and
counts-only audit rows, proven live against Anthropic (2026-07-12) and Vertex via ADC
(2026-07-15). Tenant isolation is tested at three layers.

### What is not

Four client-facing false statements remain, H2 through H5. Two questionnaire loaders
run in no environment, so the features they feed cannot render for any real user. The
demo database predates Sprint 10 S5, so a prospect demo today shows the thinner story.
Live AI has two validation days total and has never been soaked at engagement scale.
The MFA and email-verify enforcement flags have never been on in any deployment.
`infra/terraform/` contains one `.gitkeep`.

## The shape of the plan

Sprints 11 and 12 remove everything false or unsafe that a client can reach. Sprints
13 and 14 settle what the product looks like, on screen and on paper, and bring Cloud
Mod onto the same surface. Sprint 15 is the machine it runs on. Sprint 16 is the
feature work that makes a second and third engagement cheaper than the first. Sprints
17 through 19 absorb Cloud Mod.

Nothing client-facing ships before Sprint 12 closes.

---

## Sprint 11. Truth pass on everything a client can read

**What we are adding.** The four remaining false statements, corrected, and the two
mechanisms that stop a sixth appearing.

H2: `app/csf/playbook_export.py` manufactures 91 Priority 1 criticals out of unscored
rows when targets are set, because `maturity_level(0)` returns 1 and an unscored row is
indistinguishable from a real Level 1. This one needs a schema change. `CsfDimensionScore`
types all five dimensions `default=0, nullable=False`, so a row nobody assessed is
byte-identical to a deliberate all-zeros finding, and no heuristic can separate them
honestly. Migration 0035 adds the marker.

H3: `ZtWorkspace.tsx:68-79` casts dict-detail as `detail?: string` and renders an
object as a React child, so a lost Run-AI race crashes the workspace instead of showing
the typed 409. The bad cast is at 16 sites across 15 files, so this is a sweep.

H4: `fixtures.py:209` derives the ZT pillar key as `code.split(".")[0]`, filing every
narrative under `"CISA"` or `"DOD"`. Fixture mode is the default, so it persists.

H5: `seed_demo.py:797` writes Python-computed narratives under an exporter note saying
Run AI drafted them.

Then the summary headers, one consistent treatment across all four services rather than
three separate nits. Tech debt prints `Total annual cost: $0` where the cost is
unrecorded; CSF headlines a maturity tier at 2.8% coverage. Zero Trust already carries
the right pattern from Sprint 10 S4, so this is copying rather than deciding. Then
ATT&CK's `Overall coverage: 100.0%` off one scored technique in 633
(`attack/analytics.py:105` divides by scored-only) and the
`Top remediation gaps (0 of 0 shown)` heading that frames gaps as remediation targets
directly above cells D-035 forbids from doing so.

Finally the two gates from `docs/PRINCIPLES.md`: the frozen claim inventory in
`app/claims.py`, and an empty-input render test for each of the six exporters.

**Why here.** Shipping a report that says something false is worse than shipping no
report, and it is the one failure mode that costs a client rather than a sprint. The
mechanisms belong in the same sprint as the fixes because a fix that cannot be
expressed as a check does not stop the next one. Sprint 10 proved that: S0 swept one
phantom token and two more survived it.

**Needs David.** Nothing. Every item is a claim correction with an established
precedent or a mechanical sweep.

**Numbering.** Migration 0035. D-038 (the unscored marker), D-039 (one absent-versus-
zero treatment for all four summary headers). SMOKE 36 to 37.

---

## Sprint 12. The client's write path, and the injectable exporters

**What we are adding.** `CsfSelfAssessment.tsx:172-174` is a bare `catch {}` around the
answer PATCH, a direct violation of the second engineering principle, and it sits on
the only write path a client has. Nothing forces a reload, so a lost answer is
indistinguishable from an unanswered one. It composes badly with what Sprint 10 built:
the client picks a tier, the optimistic UI shows it saved, the PATCH fails silently,
and the newly honest report then tells them they never answered a question they did
answer.

Then XLSX formula injection across all six exporters. openpyxl types a leading `=` as a
formula, free-form Notes and Rationale cells already carry user text, and Sprint 10
added six injectable columns of its own at `csf/exporters.py:70-77`.

Then the deferred security items that are small but real: the unvalidated
`evidence_artifact_id` write at `attack.py:401`, `csf.py:528` and `zt.py:786`, which is
a boolean existence oracle at PATCH; the upload path trusting the client-declared MIME
type at `artifacts.py:100` with no server-side sniffing; and bandit's blind spot, since
`.github/workflows/ci.yml:48` scans `apps/api/app` and never `apps/api/scripts`.

One dependency bump, measured on `main` rather than quoted from the Sprint 10 branch.

**Why here.** These are the items where the product does something unsafe or loses data
rather than merely describing it wrongly. They come second only because a false report
reaches every client and a lost answer reaches some.

**Needs David.** What the client sees when the answer PATCH fails. The fix is small and
the failure UX is a product decision.

**Numbering.** D-040 (the client-facing save-failure treatment). SMOKE 38.

---

## Sprint 13. Ledger, part one: the application

**What we are adding.** Variation 1 of `docs/design-systems.md`, adopted with a
D-number, applied to `apps/web`. Warm paper surfaces, hairline rules instead of
shadows, square corners, serif headings over a working sans, tabular numerals, status
as printed tags rather than glowing pills.

Four things ride along because this batch has to touch them anyway. The faces get
self-hosted through `next/font/local`, which is the sprint where the type contract
becomes true: `--font-sans` has named Inter since the beginning and there is no
`next/font` usage and no `@font-face` anywhere, so the app has always rendered Segoe UI
on Windows. Dark mode gets defined once, with the `s16-axe` sweep running in both modes
as a gate. The `--heat-1` through `--heat-5` and `--tier-*` families land as real
tokens. And the phantom-utility defect gets a check rather than a fourth grep: a gate
step asserting every colour utility in the tree resolves against the served stylesheet.
That closes `border-border-default` at seven sites and `bg-surface-default` at one, and
it is the only form of the fix that stops a fourth instance.

`.css` also joins the prettier glob in `.claude/profiles/shield.sh` and in CI, where it
has never been.

**Why here.** The product's whole argument is that its deliverables are defensible, and
Ledger is the visual form of that argument. It comes after the truth pass because a
beautiful report that says something false is a worse outcome than a plain one that
does not. It comes before Cloud Mod because SHIELD's own system has to be decided
before another product can be merged onto it.

**Needs David.** Nothing further. The choice is made; the sprint records it.

**Numbering.** D-041 (Ledger adopted). SMOKE 39.

---

## Sprint 14. Ledger, part two: the deliverables and the Cloud Mod retrofit

**What we are adding.** The Ledger light ramp mirrored into the six Python exporter
modules through `app/export_style.py`, which Sprint 10 S1 built as the single home for
deliverable styling precisely so this sprint would be one module rather than six. Then
Cloud Mod's `tailwind.config.ts` retired onto the same tokens, so `kentro.teal` stops
being a second brand.

**Why here.** If the screen and the PDF disagree, the instrument-of-record argument
collapses, and that is the credibility failure the product cannot afford. This is also
the first sprint where a client looking at both products sees one company.

**Needs David.** Nothing.

**Numbering.** SMOKE 40.

---

## Sprint 15. Minimum defensible hosting

**What we are adding.** One hardened Linux VM or small managed equivalent running the
demo compose behind TLS, with real secrets handling, a nightly `pg_dump` plus MinIO
sync offsite, one rehearsed restore, an uptime ping and an error alert that reaches a
phone. Terraform and GovCloud are explicitly not required for client one.

Two things get fixed before they become policy. Rotating `JWT_SIGNING_SECRET` currently
destroys every user's MFA enrollment, because `security/totp.py:112-113` derives the
Fernet key wrapping every TOTP secret as `sha256(jwt_signing_secret)`; a routine
rotation, which is the standard response to any suspected leak, would become a
company-wide re-enrollment across all tenants at once. And the two reference-data
loaders, `scripts/load_csf_tier_questionnaires.py` and `scripts/load_zt_questionnaires.py`,
get wired into deployment. Neither runs in any environment today, which is why the
interview prompt cannot render for any real user, and it is a defect class rather than
one bug: any future loader-fed feature defaults to silently empty.

**Why here.** Nothing is sellable without it, and it is the first item that cannot be
done by an agent loop.

**Needs David.** All of it. This is infrastructure work with credentials attached.

**Numbering.** D-042 (the hosting posture for client one).

---

## Sprint 16. Evidence and access

**What we are adding.** The batch drafted before Sprint 10 closed: substantiation
states (tool present, configured, validated), per-claim evidence attach plus
post-intake upload, a client inbox, client risk-register release, and client
self-start.

**Why here.** This is what makes the second engagement cheaper than the first. Today
every AI-drafted cell must be re-reviewed on every regeneration, so consultant
throughput is the binding constraint on delivering more than one client at a time. It
comes after hosting because there is no point making delivery efficient before there is
somewhere to deliver from.

**Needs David.** Scope confirmation on client self-start, which changes who can create
an engagement.

**Numbering.** Migration 0036. D-043 through D-046. SMOKE 41 to 44. Specs s28, s29.

---

## Sprints 17 to 19. Cloud Mod as the fifth service

Three sprints, sequenced so the risky part is proven before anything depends on it.

**Sprint 17, the engine port.** The six-domain readiness rubric, the AHP-weighted WSM
disposition and the CSP comparison move from `lib/modules/analysis/` in TypeScript to
`apps/api/app/cloudmod/` in Python. The 14-case golden set ports with them and becomes
the acceptance oracle for the port: the Python engine must reproduce the TypeScript
engine's labels case for case. A miss means the port is wrong. It never means the label
is wrong, which is the rule Cloud Mod's own baseline document already states.

**Why the golden set here and not for the existing engines.** A port is exactly the
situation an external oracle is built for, because there is a known-correct answer to
port against. SHIELD's four current engines have no such external reference and their
scoring is already pinned by zero-line diffs and unit coverage.

**Sprint 18, the surface.** The Cloud Mod workspace, intake and deliverables as a fifth
service beside Technical Debt, Zero Trust, CSF and ATT&CK, rendered in Ledger, using
SHIELD's tenancy, artifacts, release gating and audit stores.

**Sprint 19, synthesis and retirement.** The Risk Register synthesises from five
services rather than four. The standalone Cloud Mod deployment retires, and its repo
becomes record.

**Needs David.** The call on whether Cloud Mod's existing engagements, if any, migrate
or finish where they are.

**Numbering.** Migrations 0037 and 0038. D-047 through D-050. SMOKE 45 to 50. Specs
s30 to s32.

---

## Outside the sprint loop

Work that runs in parallel and that no agent can finish.

- **Public claims.** `apps/web/src/app/security/page.tsx:17` says SHIELD runs in AWS
  GovCloud or Azure Government. It runs in Docker on a laptop. The same page lists
  `security@kentro.local`, which is not routable. Also align the "10-step Playbook"
  copy with the five-step product. One day of work, and the cheapest credibility in the
  plan. Do it whenever; it blocks nothing and blocks on nothing.
- **Live-mode burn-in.** Pick the engagement provider, Vertex via ADC being the proven
  path, run all five purposes at realistic scale, time the synchronous path, and write
  the one-page egress disclosure a client security team will ask for. A full
  633-technique live ATT&CK run occupies an API worker for its whole duration and there
  is no queue and no load test anywhere in the record, so the first heavy engagement is
  currently the test.
- **Commercial paper.** SOW language scoping SHIELD as consultant tooling, a
  data-handling annex with a rehearsed deletion procedure, a subprocessor disclosure
  naming the LLM provider, a breach-notification commitment. Lawyer time runs in
  parallel.
- **One full dress rehearsal.** Fresh empty tenant, a fake engagement driven end to end
  as both consultant and client, every deliverable read. The stale demo database makes
  this non-optional.
- **e2e on the dev box.** CI's fresh runner is green and is the authoritative arbiter,
  so this is no longer a verdict question. The cause is measured: next-dev evicts
  compiled routes under sustained load, so the back half of a serialized suite re-pays
  cold compiles the front half already paid. Warming cannot fix it and neither can a
  larger timeout. A production-build test target or sharding would.

## What closes this project

SHIELD is done when all five hold:

1. No client-visible surface asserts anything its input does not support, and the claim
   inventory plus the empty-input renders prove it rather than assert it.
2. One Kentro visual system across the app, the deliverables and Cloud Mod.
3. One deployment a client can reach, with a restore that has actually been rehearsed.
4. Five assessment services feeding one Risk Register, with Cloud Mod's engine in
   Python and its golden set green.
5. One engagement delivered end to end, on that deployment, by a consultant who is not
   David.

Everything after that is operations, and the honest constraint there is organizational
rather than technical. One person cannot simultaneously sell, deliver engagements,
drive the loop and operate production. Sprint 10's record shows the autonomous loop
works only with a skilled sceptical human driver, and that the written record
accumulates false claims without periodic deep audits. Four were corrected in that
batch alone.

## FedRAMP, stated honestly

The Master Spec locked single-tenant, one deployment per client, each its own FedRAMP
boundary. D-015 flipped the shipped product to shared-database multi-tenancy for
operational convenience, and nobody has re-derived the compliance story under the new
model. The two postures sell to different buyers at different price points, which makes
this a commercial question rather than a technical one.

A real authorization is a 12-to-18-month programme with a 3PAO, continuous monitoring,
and a mid-six-figure external budget. Nothing in this repo starts it: no SSP, no SAR, no
POA&M, no boundary, no authorized environment. The honest near-term posture is the one
the spec already records: risk-accepted commercial LLM, redaction as the primary
control, consultant-reviewed deliverables, and no FedRAMP claim. Schedule the
authorization when a client contractually requires it rather than prefers it.

## Risks carried into this plan

Verified against the tree on 2026-08-05 and still open.

1. **Tenancy at scale.** Ten clients in one Postgres with app-layer isolation, one
   backup file commingling everyone, no per-tenant restore, no offboarding path.
   Security-conscious clients will demand isolation, at which point the Master Spec's
   one-deployment-per-client model returns and ten deployments need automation that
   does not exist for one.
2. **Identity.** The backend accepts only its own HS256 tokens; Keycloak tokens are
   exchanged at login and never borne on an API call, so SSO is a login veneer by
   design (D-032). Ten client orgs means ten IdPs, and no JIT provisioning means
   hand-creating every user.
3. **No tenant deletion path**, so ordinary DPA data-return and destruction clauses are
   satisfiable only by hand-written SQL.
4. **The spec-versus-shipped tenancy inversion has never been priced.**

## Assumptions behind the estimates

David doing the work with agent loops at the cadence Sprint 10 demonstrated, which was
a twelve-sprint batch in roughly five calendar days of supervised loop time plus
planning and review. Gene available for PR review. Lawyer time procured outside the
repo. No new hires. The Cloud Mod port assumes its TypeScript engine is well covered by
its own tests, which the golden set will confirm or refute in Sprint 17.

## Maintaining this file

Update it when a sprint closes or an estimate is proven wrong, in the PR that does the
work. It is not a scratchpad: `context/dave.md` carries in-flight status and
`CONTEXT.md` carries state of the branch.
