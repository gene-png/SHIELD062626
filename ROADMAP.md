# SHIELD Roadmap

_Created 2026-08-05. Owner: David Catarious. This is the current forward plan and
supersedes `DELIVERY_PLAN.md` (historical, Sprints 1 to 5) and `IMPLEMENTATION.md`
(the June 2026 v2 work order). Neither of those is a plan any more; both are kept
as record._

**What this file is for.** The forward plan was scattered across three places: the
"What comes after this batch" section of `docs/SPRINTS.md`, the priority list in
`context/dave.md`, and the 21-item deferred list in `CONTEXT.md`. None of those is
a roadmap, and none of them was written with revenue as the lens. This file is
that lens. It does not restate the backlog; it orders the work by what stands
between the repo and a paying client.

**Where the detail lives.** Per-item technical detail stays in `CONTEXT.md`
(deferred list, including the H1 to H5 audit findings) and in the `docs/SPRINTS.md`
Log. This file carries sequence, sizing and rationale. When the two disagree,
`CONTEXT.md` is the fact and this file is the plan.

## Status as of 2026-08-05

Sprint 10 "Reports you can defend" is complete on `feat/defensible-reports-sprint-10`,
29 commits ahead of `main`, **no PR opened**. Ten of twelve boxes checked, two open
(S9, S11) on three `needs-human` criteria. The branch is 1 commit behind `main`
(PR #57, the PowerShell hook matcher).

The honest summary: the product layer is largely built and largely proven. The
platform layer that turns an application into a sellable service is between thin
and absent. `infra/terraform/` contains one `.gitkeep` and nothing else, verified
2026-08-05.

### What is proven

Roughly 25,900 lines of Python and 25,600 of TS/TSX, 34 migrations, 114 endpoints,
about 745 unit tests green in-container, 118 vitest cases, 28 Playwright spec files.
All four services plus the Risk Register drive end to end in a real browser. "AI
suggests, code computes" is enforced rather than aspirational: the shutdown audit
verified zero-line diffs on every scoring engine and every prompt this batch. The
LLM egress seam is one client with a mandatory redactor and counts-only audit rows,
proven live against Anthropic (2026-07-12) and Vertex via ADC (2026-07-15). Tenant
isolation is tested at three layers. Deliverable release gating works.

### What is not

No full e2e run has ever finished green on the dev box, and the Sprint 10 branch has
never been through CI at all. Two questionnaire loaders run in no environment, so the
features they feed cannot render for any real user. The demo database predates S5, so
a prospect demo today shows the thinner story. Live AI has two validation days total
and has never been soaked or run at engagement scale. The MFA and email-verify
enforcement flags have never been on in any deployment.

## The reframe that orders everything below

The code is not the long pole. What stands between this repo and revenue is a short
list of client-visible falsehoods, one machine somewhere that can host it with
backups, and commercial scaffolding no agent loop can sign on Kentro's behalf.

That is why Phase 1 is not feature work. Sprint 10 spent twelve sprints making
deliverables defensible, and its own closing audit found the flagship CSF artifacts
were never covered by the fix. Shipping a report that says something false is worse
than shipping no report, and it is the one failure mode that costs a client rather
than a sprint.

## Phase 0. Close Sprint 10

**1 to 3 days. Blocked on nobody.**

1. Merge `origin/main` into the branch (one commit, the hook matcher).
2. Open the PR. This produces the first authoritative CI `e2e` and `demo` run the
   batch has ever had, which is also the honest arbiter for the full-suite question
   that four local attempts could not settle.
3. Decide whether H1 blocks the merge. It ships a client-facing false statement, and
   the deliverable it affects is the one a consultant actually hands over.

## Phase 1. Truth pass on everything a client can see

**1.5 to 3 weeks. Needs David for the product calls, not just an agent.**

Nothing client-facing ships before this closes. Several items are claim changes on a
client-visible deliverable, which D-035's precedent makes a decision rather than a
scrub.

1. **H1 and H2 in `app/csf/playbook_export.py`.** With no target recorded, the five
   flagship playbook artifacts print `No gaps: every in-scope subcategory meets its
target.` and advise maintaining current controls. Root cause at
   `routes/csf.py:1129`, where `target is not None else False` makes "no target
   recorded" and "target met" the same value, with `target_level` nullable
   (`models/csf_profile.py:62`) and `routes/csf.py:1331` writing `None` explicitly.
   Measured 2026-08-05: **1 coverage-qualifier phrase in `playbook_export.py`
   against 27 in `csf/exporters.py`**, which S3 fixed and this file never was. It
   fires on the default state of a real engagement. H2 is the same file
   manufacturing 91 Priority 1 criticals from unscored rows when targets are set.
2. **The client's only write path.** `CsfSelfAssessment.tsx:172-174` is a bare
   `catch {}` around the answer PATCH. A lost answer is indistinguishable from an
   unanswered one, and the newly honest reports then tell a client they never
   answered a question they did answer. The fix is small; the failure UX is a
   product decision.
3. **Absent versus zero at the summary headers**, in three of four services.
   Tech-debt prints `Total annual cost: $0` where the cost is unrecorded; CSF
   headlines a maturity tier at 2.8% coverage. ZT already carries the correct
   pattern since S4, so this is copying an established fix rather than making a new
   decision.
4. **`Overall coverage: 100.0%` off one scored technique in 633**
   (`attack/analytics.py:105` divides by scored-only), and the
   `Top remediation gaps (0 of 0 shown)` heading that frames gaps as remediation
   targets immediately above cells D-035 forbids from doing so.
5. **Add the empty-input render test per exporter.** S3 and S4 proved this out: three
   of four services printed something untrue when given nothing to say, and each
   passed every test it had. This is the check that would have caught H1.
6. **XLSX formula injection across the six exporters.** Pre-existing, and this batch
   added six injectable columns of its own at `csf/exporters.py:70-77`. Do this
   before any XLSX reaches a client.

## Phase 2. The floor for a first paying client

**4 to 6 weeks, partly parallel with Phase 1.**

Framing: sell the engagement. The client touches the portal for intake,
self-assessment and released documents. Kentro hosts.

1. **Truth pass on public claims.** `apps/web/src/app/security/page.tsx:17` currently
   states SHIELD "runs in AWS GovCloud or Azure Government". Verified 2026-08-05: it
   runs in Docker on a laptop. The same page lists `security@kentro.local`, which is
   not a routable address. Prospect diligence finds both, and each one taxes every
   true claim near it. Also align the "10-step Playbook" copy with the 5-step
   product. **1 day, and it is the cheapest credibility in the whole plan.**
2. **Wire the reference-data loaders into deployment**, or cut the interview-prompt
   feature from the offer. `scripts/load_csf_tier_questionnaires.py` and
   `scripts/load_zt_questionnaires.py` are invoked by nothing: not CI, not compose,
   not `demo-reset`. Add the ZT client guidance element while here, which is an
   import plus one element. 2 to 4 days.
3. **Minimum defensible hosting.** One hardened Linux VM or small managed equivalent
   running the demo compose behind TLS, real secrets handling, nightly `pg_dump` plus
   MinIO sync offsite, **one rehearsed restore**, an uptime ping and an error alert
   that reaches a phone. Terraform and GovCloud are explicitly not required for
   client one. 1 to 2 weeks.
4. **Live-mode burn-in.** Pick the engagement provider (Vertex via ADC is the proven
   path), run all five purposes at realistic scale, time the synchronous path, and
   write the one-page egress disclosure a client security team will ask for. 1 week.
5. **Commercial paper.** SOW language scoping SHIELD as consultant tooling, a
   data-handling annex with a documented and rehearsed deletion procedure, a
   subprocessor disclosure naming the LLM provider, a breach-notification commitment.
   Lawyer time runs in parallel. 1 week elapsed.
6. **One full dress rehearsal.** Fresh empty tenant, a fake engagement driven end to
   end as both consultant and client, every deliverable eyeballed. The stale demo
   database makes this non-optional. 2 to 3 days.

**Phase 0 through 2 total: 6 to 9 calendar weeks.**

A faster variant exists. Use SHIELD internally and deliver documents only, with no
client portal exposure. That drops item 2 and most of item 3's client-facing surface
and reaches defensible revenue in **3 to 4 weeks**, at the cost of the portal not
being part of the pitch.

## Phase 3. Repeatable delivery, clients three through five

**8 to 12 weeks beyond Phase 2.**

1. **Sprint 11 "Evidence and access"** as already drafted: substantiation states
   (tool-present / configured / validated), per-claim evidence attach plus
   post-intake upload, client inbox, client risk-register release, client self-start.
   Numbering is reserved: migrations 0035/0036, D-038 through D-042, SMOKE 36 to 40,
   specs s28/s29. This is also what unblocks consultant throughput, because today
   every AI-drafted cell must be re-reviewed on every regeneration.
2. **The visual system batch.** Adopt one of the three in `docs/design-systems.md`
   (the standing recommendation is Ledger), self-host the faces, define dark mode,
   and mirror the ramps into the exporters. Note that Inter has never actually
   loaded, so this batch is where the type contract becomes true. S0 and S1 already
   built the groundwork. Blocked on David choosing, and the choice takes a D-number.
3. **e2e test infrastructure.** The suite cannot go green under next-dev on a loaded
   box, and the cause is measured rather than assumed: next-dev evicts compiled
   routes under sustained load, so the back half of a serialized suite re-pays cold
   compiles the front half already paid. Warming cannot fix it and neither can a
   larger timeout. A production-build test target or sharding would.
4. **Dependency cadence.** `pnpm audit` on this branch is 5 high plus 2 moderate.
   Dependabot #47 has since merged to `main`, so that count is now unmeasured there
   and wants re-running before it is quoted again. Establish a cadence rather than a
   one-off bump.
5. **Real IdP federation for at least one client**, if any of the first five asks.
   See Phase 4 for what that actually means.

## Phase 4. What breaks at the tenth client

**6 to 12 months beyond Phase 3. The gating item is organizational, not technical.**

- **Tenancy.** Ten clients in one Postgres with app-layer-only isolation, one backup
  file commingling everyone, no per-tenant restore, and no offboarding path at all.
  Security-conscious clients will demand isolation, at which point the Master Spec's
  original one-deployment-per-client model returns, and ten deployments need the
  automation that does not exist for even one.
- **Identity.** The backend accepts only its own HS256 tokens. Keycloak tokens are
  exchanged at login and never borne on an API call, so SSO today is a login veneer
  by design (D-032). Ten client orgs means ten IdPs, and no JIT provisioning means
  hand-creating every user of every client. Token federation, SCIM, and moving
  register/MFA/email into Keycloak are all explicitly out of scope today.
- **Tenant lifecycle.** No deletion path, no retention enforcement in app code. The
  spec's retention setting was never built. Standard DPA data-return and destruction
  clauses are currently satisfiable only by hand-written SQL.
- **Operations.** No on-call, no SLA, no support channel, no patch cadence. Ten
  clients means someone gets paged, and today there is no pager and no second person.
- **The operating model.** One person cannot simultaneously sell, deliver
  engagements, drive the loop and operate production for ten tenants. Sprint 10's
  own record shows the autonomous loop works only with a skilled sceptical human
  driver, and that the written record accumulates false claims without periodic deep
  audits. Four were corrected in this batch alone.

## FedRAMP, stated honestly

The Master Spec locked single-tenant, one deployment per client, each its own
FedRAMP boundary. D-015 flipped the shipped product to shared-database
multi-tenancy for operational convenience, and **nobody has re-derived the
compliance story under the new model.** The decision log records the how and never
asks what it does to the sales motion. The two postures sell to different buyers at
different price points, which makes this a commercial question rather than a
technical one.

A real FedRAMP authorization is a 12-to-18-month programme with a 3PAO, continuous
monitoring, and a mid-six-figure external budget. Nothing in this repo starts it:
no SSP, no SAR, no POA&M, no boundary, no authorized environment.

The honest near-term posture is the one the spec itself already records:
risk-accepted commercial LLM, redaction as the primary control, consultant-reviewed
deliverables, and **no FedRAMP claim**. Schedule the authorization only when a
client contractually requires it rather than preferring it.

## Risks not previously tracked anywhere

None of these appears in the `CONTEXT.md` deferred list, in `DECISIONS.md`, or in
the sprint logs as a commercial risk. Each was verified against the tree on
2026-08-05.

1. **The public security page misstates the present tense.** `security/page.tsx:17`
   claims GovCloud or Azure Government hosting. Contact is `security@kentro.local`,
   non-routable. **Verified.**
2. **The spec-versus-shipped tenancy inversion has never been priced.** See the
   FedRAMP section. **Verified against the spec and D-015.**
3. **No tenant deletion path exists**, so ordinary DPA clauses are unexecutable.
   **Verified by absence.**
4. **Rotating `JWT_SIGNING_SECRET` destroys every user's MFA enrollment.**
   `security/totp.py:112-113` derives the Fernet key wrapping every TOTP secret as
   `sha256(jwt_signing_secret)`. A routine secret rotation, which is the standard
   response to any suspected leak, becomes a company-wide MFA re-enrollment event
   across all tenants at once. **Verified.**
5. **The upload path trusts the client-declared MIME type.** `artifacts.py:100` reads
   `file.content_type` and checks it against an allowlist with no server-side
   sniffing, and there is no AV scanning. Consultants download and open client files.
   **Verified.**
6. **Reference-data loaders are a defect class, not one bug.** Both loaders run in no
   environment. The interview prompt was the instance that got caught; the ZT
   verbatim interview endpoint reads the same empty table. Any future loader-fed
   feature defaults to silently empty until loaders become part of deployment.
   **Verified.**
7. **Synchronous AI at engagement scale is unmeasured.** A full 633-technique live
   ATT&CK run occupies an API worker for its whole duration. No queue, no concurrency
   plan, no load test anywhere in the record. The first heavy real engagement is the
   test.

## Assumptions behind the estimates

David doing the work with agent loops at the cadence Sprint 10 demonstrated, which
was a twelve-sprint batch in roughly five calendar days of supervised loop time plus
planning and review. Gene available for PR review. Lawyer time procured outside the
repo. No new hires. Phase 4's estimate assumes a second engineer or operator is
hired, and it does not hold without one.

## Maintaining this file

Update it when a phase closes or when an estimate is proven wrong, in the PR that
does the work. It is not a living scratchpad: `context/dave.md` carries in-flight
status and `CONTEXT.md` carries state of the branch. If this file and `CONTEXT.md`
disagree on a fact, `CONTEXT.md` wins and this file gets corrected.
