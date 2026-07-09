# Decision Log

Append-only record of every choice made during the SHIELD v2.0 autonomous build. Per AI Prompt §7 / §4.9, every time a non-obvious option is picked over an alternative, it must land here.

Each entry: `D-NNN` · date (UTC) · category · subject · decision · rationale · spec/AI-Prompt reference.

---

## D-001 — Tech stack confirmation

**2026-05-19 · architecture**
Confirm locked stack from Master Spec §2: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui (frontend), FastAPI on Python 3.12 (backend), PostgreSQL 16, Redis, S3-compatible object storage (MinIO in dev, S3 + KMS in prod), Keycloak/OIDC, Celery workers, Alembic migrations, Playwright E2E.
**Rationale:** Locked by Eugene in spec §2. No deviation.
**Ref:** Master Spec §2, AI Prompt §2, §8.2 (D-001).

## D-002 — AI provider for v1

**2026-05-19 · ai**
Default LLM provider is **Anthropic Claude** via `ANTHROPIC_API_KEY`, configured by `SHIELD_LLM_PROVIDER` and `SHIELD_LLM_MODEL`. Default model `claude-opus-4-7`. Env-configurable; never hardcoded.
**Rationale:** Eugene answered spec §17 Q6 with "developer's choice"; Anthropic Claude is the recommended default in spec §2 and `.env.example`. Best output quality for analytic prompts, cleanest API for redacted-payload pattern. Risk of non-FedRAMP egress accepted by Eugene; PII redaction (§12) is the primary compensating control.
**Ref:** Master Spec §2, §4.4, §17 Q6, AI Prompt §8.2 (D-002).

## D-003 — Marketing landing page (spec §17 Q1)

**2026-05-19 · ux**
Implement a polished one-page marketing landing at `/` (hero, mission, service cards, resource center, contact, footer). NOT a redirect to `/sign-in`.
**Rationale:** Eugene confirmed recommended option. Aligns with Round 6 design contract's PUBLIC / EXTERNAL EXPERIENCE tier (USWDS + Microsoft public portal styling).
**Ref:** Master Spec §17 Q1, Round 6 Design Contract (public-experience tier).

## D-004 — Self-registration allowed (spec §17 Q2)

**2026-05-19 · auth**
Allow self-registration. The first registrant on a fresh deployment becomes that deployment's Primary POC. A Kentro consultant verifies and attaches them post-registration.
**Rationale:** Eugene confirmed recommended option. Preserves the v1 onboarding process Eugene wants to keep. Compensating controls for the open-door surface: account lockout, short JWT TTLs, idle timeout, forced re-auth (Master Spec §4.5).
**Ref:** Master Spec §17 Q2, §4.5.

## D-005 — Reviewer assignment is deployment-wide (spec §17 Q3)

**2026-05-19 · auth**
Any admin in a deployment may attach a reviewer. A reviewer's scope is the entire deployment — they see all services in this single-tenant deployment, not service-by-service.
**Rationale:** Eugene confirmed recommended option. Single-tenant means one deployment = one client engagement; per-service slicing is over-engineering for v1.
**Ref:** Master Spec §17 Q3, §2 (single-tenant).

## D-006 — Deliverable approval flow (spec §17 Q4)

**2026-05-19 · workflow**
Approval flow: **admin marks deliverable "final"** → **reviewer (if any) approves** → **admin releases to client**. Reviewer step is skipped when no reviewer is attached to the engagement.
**Rationale:** Eugene confirmed recommended option. Matches Phase 5 reviewer audit-walk surface (Master Spec §15 Phase 5). The "if any" guard handles engagements without a reviewer without needing a second release path.
**Ref:** Master Spec §17 Q4, §15 Phase 5.

## D-007 — ATT&CK technique scope (spec §17 Q5) **[FLIPPED FROM RECOMMENDATION]**

**2026-05-19 · service**
**Use the full MITRE ATT&CK Enterprise matrix (~600 techniques)** for every engagement. NOT the recommended curated 33–40 most-relevant subset.
**Rationale:** Eugene explicitly flipped this answer ("we should build it to use all of the 600+ items").
**Implications and requirements:**

1. `packages/attack-data/` vendors the full MITRE ATT&CK Enterprise JSON (STIX 2.1 bundle) and is load-bearing.
2. The ATT&CK questionnaire UI MUST be designed for ~600 items from day one: tactic-grouped sections (14 tactics), pagination or virtualization, search by technique ID / name / data source / platform, filter by tactic / platform / data-source-availability, bulk-mark workflows, progress persistence, auto-save on every cell.
3. Master Spec §6.10 already forbids "single massive scroll" questionnaires; this decision reinforces it.
4. Coverage scoring math is unchanged per technique; only rendering scales.
5. Coverage Report deliverable (Phase 5) must paginate by tactic to remain readable as PDF/XLSX.
   **Ref:** Master Spec §17 Q5, §15 Phase 5, §6.10.

## D-008 — AI provider for v1 (spec §17 Q6)

**2026-05-19 · ai**
See D-002. Anthropic Claude API as the v1 default, env-swappable.
**Ref:** Master Spec §17 Q6.

## D-009 — Languages and locale (spec §17 Q7)

**2026-05-19 · i18n**
English only at v1.0. Build i18n-aware (no hardcoded strings; locale-keyed message files via `next-intl` for web and `babel`/`gettext`-style catalogs for API responses). Additional locales added in v1.x as content-only PRs.
**Rationale:** Eugene confirmed recommended option. Avoids translation cost in v1 while preserving zero-rewrite extensibility.
**Ref:** Master Spec §17 Q7.

## D-010 — Repo layout: monorepo with pnpm workspaces + Python workspace

**2026-05-19 · architecture**
Single repository, pnpm workspaces for `apps/web`, `apps/api` consumers (shared TS types), and `packages/*`. Python apps (`apps/api`, `apps/worker`) managed via Poetry with a shared root `pyproject.toml` for tooling config. CI runs all checks from the repo root.
**Rationale:** Spec §16 prescribes the directory shape. Monorepo simplifies sharing of `packages/shared-types`, `packages/csf-data`, `packages/attack-data`, `packages/zt-data` across web and API without publishing.
**Ref:** Master Spec §16, AI Prompt §8.2 (repo layout).

## D-011 — Working directory deviation

**2026-05-19 · environment**
Spec §3.2 mandates working directory `/workspaces/SHIELDV2-051826v2`. Actual working directory is `/workspaces/repos/SHIELDV2-051826v2` because the persistent dev-container mount in this environment is `/workspaces/repos`. All in-container paths in scripts and docs use relative paths from the repo root to remain portable across both mount points.
**Rationale:** `/workspaces/SHIELDV2-051826v2` is on the overlay FS in this environment (ephemeral on container rebuild). The mounted path persists.
**Ref:** AI Prompt §3.2.

## D-012 — Dev container runs as `appuser` with passwordless sudo

**2026-05-19 · environment**
`.devcontainer/Dockerfile` creates non-root `appuser` (uid 1000) with passwordless sudo for development convenience. Production runtime images (separate Dockerfiles under `infra/docker/`) use a least-privilege non-shell user with no sudo.
**Rationale:** Required by AI Prompt §3.10 / §3.11 to prevent the autonomous agent from stalling on sudo prompts. Production posture is unchanged.
**Ref:** AI Prompt §3.10, §3.11.

## D-013 — Reference docs renamed and relocated

**2026-05-19 · housekeeping**
Reference docs in the original GitHub repo root were renamed (whitespace → underscores, parenthetical suffixes removed) and moved to `reference-docs/`. Examples:

- `AI Prompt` → `reference-docs/AI_Prompt`
- `Shield UX fix round 6 full design update for 2.0.txt` → `reference-docs/Shield_UX_Round6_Design_Contract.txt`
- `Ongoing CSF2 Artifact Tracker (1).xlsx` → `reference-docs/CSF2_Artifact_Tracker.xlsx`
- All `Step N.M ... .docx`/`.xlsx` → `reference-docs/Step_N_M_...` (underscores, no spaces, no parentheticals).
  Moves use `git mv` so history is preserved. No file deletions.
  **Rationale:** Whitespace and parentheses in filenames are hostile to scripts, CI, and Windows paths. `reference-docs/` keeps the spec library separate from build artifacts.
  **Ref:** Master Spec §15.5 (slugifier conventions apply to deliverables; we apply the same hygiene to reference filenames).

## D-015 — Multi-tenant: shared DB with `client_id` on every row

**2026-05-21 · architecture**
Platform now supports many `client` rows per deployment instead of exactly one. Tenant isolation is enforced at the data-access layer (every business table carries `client_id`; every data route filters by it) rather than via per-tenant schemas or databases. Platform-level admin/reviewer users (`User.client_id IS NULL`) pick the active tenant via an `X-Client-Id` request header surfaced as a top-nav client switcher in the frontend; client-role users are pinned to their `User.client_id` and cannot escape it. New client tenants are created by either an admin via `POST /admin/clients` or implicitly when a non-admin self-registers (a fresh `Client(legal_name="(pending intake)")` row is created and bound to the new user, which the intake wizard then fills in).
**Rationale:** Eugene requested multi-client support. The schema already denormalized `client_id` on assessment tables (Master Spec §11.1 future-proofing); this migration (0013) adds it to the remaining business tables (`services`, `service_requests`, `artifacts`) and makes every business `client_id` `NOT NULL`. Shared-DB-with-tenant-column was chosen over schema-per-tenant and DB-per-tenant because: (1) the existing data model is one column short of being ready, (2) cross-tenant admin/reporting features remain cheap, (3) operational burden (one DB to back up, migrate, monitor) does not scale with tenant count.
**Implications and requirements:**

1. Every data route (`csf`, `zt`, `attack`, `tech_debt`, `artifacts`, `deliverables`) takes a `current_client` FastAPI dependency that resolves the active tenant; reads filter by `client_id`; writes set `client_id` at row creation; id-based fetches (`db.get(Service, id)` etc.) verify ownership via `app/tenant.py` helpers that return 404 on tenant mismatch (no existence oracle).
2. `User.client_id` stays nullable for platform admins/reviewers; everyone else's is set on registration.
3. The frontend forwards the cookie-driven `shield_active_client_id` as `X-Client-Id` through `lib/api.ts`; admin-only cross-tenant routes (e.g. `GET /admin/clients`, `POST /admin/clients`) pass `clientId: ""` to suppress that header.
4. Backwards compatibility: migration `0013` backfills all existing rows to the deployment's existing singleton `client` row (or creates a `"(legacy backfill)"` placeholder if business data exists but no `client` row does).
5. D-005 ("reviewer attachment is deployment-wide") still holds _within a tenant_; a reviewer can see every service for the active client they're scoped to.

**Ref:** Master Spec §11.1 (denormalized client_id), §2 (single-tenant — now superseded for this platform), §4.5 (auth), DECISIONS D-004 (self-registration extends to per-tenant client creation).

## D-014 — Opening commit on `main`, push deferred

**2026-05-19 · git**
Opening commit lands directly on `main`. Push is deferred until the dev container has credentials configured per AI Prompt §3.3 (no agent-introduced credentials).
**Rationale:** AI Prompt §3.9 prescribes "push frequently" but §3.3 forbids the agent from introducing its own credentials. Eugene will push when he attaches a PAT or SSH key to the container.
**Ref:** AI Prompt §3.3, §3.9.

## D-015 — Part F: harden and ship decisions

**2026-06-26 · F (harden)**

- **Worker / async:** AI runs are **synchronous** — the `run-ai` endpoints invoke
  the LLM inline via `app.ai.engine.run_job`. There is no Celery worker; the
  orphaned `worker` service (which referenced a non-existent `app.worker`) was
  removed from `docker-compose.yml`. `redis` remains as a config placeholder for
  future rate-limiting/async but has no consumer today.
- **Auth seam:** NextAuth stays pluggable. The active login is `CredentialsProvider`
  (against the API); a Keycloak realm is scaffolded under `infra/keycloak/` so a
  SAML/OIDC provider can be added without touching call sites. MFA stays deferred.
- **Dependency audits:** `pip-audit` (API) and `pnpm audit --audit-level high`
  (web) run in CI (non-blocking; surface advisories), and `.github/dependabot.yml`
  opens the fix PRs (pip / npm / github-actions, weekly). pip-audit is clean today.
- **Accessibility:** static `jsx-a11y` rules are enforced in CI via
  `next/core-web-vitals` (the eslint step); skip-to-content links + a
  `#main-content` landmark are present in every shell (admin + client pages).
  Runtime axe/Pa11y in CI is the remaining a11y item (needs a dev-dep + a built
  app harness in CI — pnpm-lockfile change to be made in a pnpm environment).
- **IaC:** `apps/api/Dockerfile` exists; a production `apps/web/Dockerfile`
  (Next standalone) was added. `infra/terraform` for AWS GovCloud / Azure
  Government remains a skeleton — it needs concrete account/region/network
  decisions and is intentionally left as the next infra task.
- **Isolation:** `test_new_surface_authz.py` covers cross-tenant isolation for the
  new tables (messages, client_domain, risk register, CSF tier profiles); these
  run under `pytest -m unit` in CI.

**Ref:** Work Order Part F.

## D-016 — Duplicate-email registration discloses existence (typed error copy)

**2026-07-02 · auth**
Self-registration surfaces a friendly, field-scoped error for a duplicate email
("An account already exists for that email. Sign in instead.") rather than a
generic enumeration-resistant message. The `/auth/register` endpoint returns a
typed error envelope on every rejection — `error.reason` (machine code) plus
`error.message` (human copy) — and the web sign-up form maps each `reason` to the
right field: `email_exists` (409) and `email_domain_not_allowed` /
`email_domain_not_approved` / `email_domain_unavailable` (422) attach to the email
field; `password_policy` (422) attaches to the password field; a raw
`RequestValidationError` (no `reason`) shows a plain-language form-level prompt
instead of leaking the internal "Request validation failed." string.

**Rationale:** Disclosure posture is kept **consistent with the pre-existing
domain-rejection copy**, which already tells a caller whether their domain is
approved. Registration is gated behind admin-approved email domains, so an
attacker must already control an approved-domain mailbox to probe for account
existence — the marginal enumeration surface a duplicate-email message adds over
the domain-approval oracle is negligible, and the usability win (the user learns
to sign in instead of retrying) is real. The **login** path keeps its stricter
enumeration-resistant posture unchanged (generic "Invalid email or password." +
constant-time dummy-hash compare, OWASP A07); the two surfaces differ
deliberately because login is unauthenticated-probe-heavy while register is
domain-gated. No new information beyond the existing domain oracle is disclosed.

**Ref:** Master Spec §17 Q2, §4.5; SPRINT_1.md T4; OWASP A07 (login path unchanged).

## D-017 — Fixture-mode AI serves deterministic runtime suggestions offline

**2026-07-03 · ai**
Fixture mode (`SHIELD_LLM_MODE=fixture`) now registers a deterministic,
demo-plausible canned response for every one of the five AI job purposes
(`mitre_map`, `zt_score`, `csf_score`, `extract.capabilities`,
`risk_synthesize`) via a new `app/ai/fixtures.py` module. `_build_provider`
returns a `RuntimeFixtureProvider` preloaded with those fixtures instead of a
bare, empty `FixtureProvider`. Each fixture is payload-aware — it reads the
redacted job payload (technique codes, capability codes, tiers/subcategories,
findings) so the drafted suggestions line up with the live assessment and
"Run AI" actually changes rows. The demo/dev stack is now fully exercisable
OFFLINE with no provider API key.

A missing fixture at runtime is surfaced as a typed configuration error mapped
to HTTP 503 (`reason=ai_fixture_unavailable`, mirroring the D-016 / T4 typed-error
pattern), never a raw 500 `KeyError`. The bare `FixtureProvider` keeps its loud
`KeyError` for tests, and pytest's own dependency-override fixtures still take
precedence over the runtime provider.

**Rationale:** David-approved product decision (2026-07-03) after the T6 halt
(Run-AI 500'd because the runtime provider had zero fixtures registered — only
pytest registered them). "AI suggests, code computes" is preserved: fixtures
only DRAFT values (statuses, stages, dimension scores, risk links); the
deterministic engines still compute every total, tier, roll-up and roadmap. DoD
ZTRA fixture values respect the framework's `<=3` stage clamp. Live-mode behavior
is unchanged.

**Ref:** Master Spec §4.4 (LLM env-configurable), §12 (redaction on egress);
SPRINT_1.md T6b; DECISIONS D-016 (typed-error pattern reused for the 503).

## D-018 — Dependabot majors suppressed; framework upgrades are sprint-planned

**2026-07-07 · dependencies**
Merging PR #16 activated Dependabot (config landed with Work Order F but the
repo had no CI/dependabot before that merge), and it filed its whole backlog at
once: 15 PRs, of which 7 were major framework jumps (react 19, next 16,
tailwindcss 4, eslint 10, tailwind-merge 3, @types/node 26, eslint-config-next
16). Decision (David, 2026-07-07): `.github/dependabot.yml` now ignores
`version-update:semver-major` for the entire npm ecosystem and groups
minor/patch updates into one weekly PR per ecosystem; the 7 major PRs are
closed unmerged. The 8 safe PRs (5 GitHub Actions bumps; autoprefixer,
next-auth, prettier minors/patches) are merged after a `@dependabot rebase` —
their original CI failures were stale runs from 2026-07-03 against the pre-fix
`main` (the pnpm double-pin bug fixed in `f65e36f`), not real breakage.

**Rationale:** Sprint 2 T0 deliberately stays on the Next 14.2.x App Router
line, and CI has no e2e job yet (S2 T3), so a green dependabot check proves
lint/tsc/build only — nowhere near enough verification for a framework major.
Majors move as one deliberate, e2e-netted upgrade bundle instead: Next 15/16 +
React 19 + Tailwind 4 + ESLint 10 + Node 22 LTS/@types/node (Node 20 passed
EOL 2026-04-30), targeted at Sprint 3/4 after e2e runs in CI. Trade-off
accepted: a security fix that ships only in a major is suppressed too — the
non-blocking `pnpm audit` / `pip-audit` CI steps remain the tripwire for that
case.

**Ref:** SPRINT_2.md T0/T3; CLAUDE.md (migrations/e2e gotchas); D-015 (Part F
dependency-audit posture).

## D-019 — Reject reserved/special-use TLDs at domain-approval time

**2026-07-07 · admin**
The admin add-domain route (`POST /admin/clients/{cid}/domains`) now rejects
reserved / special-use domains — RFC 2606/6761 names like `.test`, `.invalid`,
`.localhost` — with a typed 422 (`reason=domain_reserved_tld`, plus friendly
`message`), following the D-016 dict-detail envelope. The check reuses
email-validator's own reserved-name logic (a throwaway `validate_email` probe
via the new `app/security/email_domains.is_reserved_domain` helper) rather than a
hand-rolled TLD list — the exact check pydantic's `EmailStr` runs at
registration. `.example` is NOT reserved and still approves.

**Rationale:** Before this guard, the email validator 422'd special-use TLDs at
self-registration _before_ the domain-approval check, so an admin could approve a
domain (e.g. the demo's `beacon.test`) that no user could ever register on —
approved-but-unregistrable, a silent dead end. Rejecting at approval time fails
loudly at the point of the mistake. The web Management client (`_detail`) was
also reading the wrong error field (`detail` vs the D-016 `error.message`); it now
prefers the typed message so the rejection copy actually surfaces in the form.
The guard is add-time only: rows approved before it (legacy reserved domains)
still list and remove unchanged (C0/additive). `seed_demo.py` was checked — it
only seeds `atlas.example` and never created `beacon.test`, so no seed migration
was needed (s13 find-or-creates `beacon.example` itself).

**Ref:** SPRINT_2.md T9; DECISIONS D-016 (typed-error pattern); D-004/B1
(domain-gated registration); `email-validator` `SPECIAL_USE_DOMAIN_NAMES`.

## D-020 — Auth compensating controls: enforce the real ones, retract the fiction

**2026-07-09 · admin**
README §Risk-acceptance and BUILD_REPORT A07 claimed "30-minute idle timeout"
and "daily forced re-auth" as MFA offsets, and said the deferred
`SHIELD_AUTH_REQUIRE_MFA` / `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY` flags "enable
both in v1.x with no code changes". None of that was true: the reauth/idle
config knobs were referenced nowhere and `/auth/refresh` re-issued token pairs
indefinitely with no rotation or ceiling. Sprint 3 T2 makes the claims honest:

- **Forced re-auth ceiling (real):** access + refresh tokens now carry an
  `auth_time` claim (original login time) that rides forward unchanged across
  refreshes. `/auth/refresh` rejects a refresh whose session age exceeds
  `SHIELD_FORCED_REAUTH_SECONDS` (default 24h) with a typed 401
  `reason=reauth_required` (D-016 envelope).
- **Refresh-token rotation (real):** each refresh mints a new refresh token and
  stores its jti on the user (`users.active_refresh_jti`, additive/nullable
  migration 0026, C0). Only the most recently issued refresh token is valid; a
  replayed/rotated-out token is rejected `reason=refresh_reused`. This is a
  **single active session per user** posture — a new login supersedes the prior
  session's refresh token. Acceptable for a consultant-led tool; revisit if
  concurrent multi-device sessions become a requirement.
- **Idle timeout (documented, not new machinery):** the 30-minute refresh-token
  TTL already IS the idle timeout — an idle session cannot refresh past it. We
  document that rather than invent a second timer.
- **Dead flags fail loudly:** `assert_safe_for_runtime` now refuses to boot if
  `SHIELD_AUTH_REQUIRE_MFA` or `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY` is true,
  because the enrollment/challenge and email-verification flows do not exist.
  Silently ignoring a security flag is worse than refusing to start.
- **Web:** the NextAuth refresh callback surfaces the reauth/rotation reasons as
  a distinct `REAUTH_REQUIRED_ERROR`; a `SessionExpiryGuard` clears the dead
  session and routes to `/sign-in?reason=session_expired` with friendly copy.

**Why DB rotation, not Redis:** a jti denylist in Redis (T3's territory) would
also work, but the rotating-pair check needs only one nullable column, is fully
testable under the SQLite unit suite with no Redis dependency, and survives
restarts/multi-worker without an outage fail-open/closed dilemma.

**Ref:** SPRINT_3.md T2; DECISIONS D-016 (typed errors); migration 0026;
`app/config.py`, `app/security/jwt.py`, `app/routes/auth.py`.
