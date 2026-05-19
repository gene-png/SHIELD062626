# Changelog

All notable changes to SHIELD by Kentro v2.0. Format roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the phase template in AI Prompt §9.

## [Unreleased]

### Opening commit — 2026-05-19

- Repo scaffolded per Master Spec §16 and AI Prompt §8.
- Reference documents relocated to `reference-docs/` with normalized filenames (see DECISIONS.md D-013).
- Dev container configured with `appuser` + passwordless sudo per AI Prompt §3.10–§3.11.
- Docker Compose stack defined for 8 services (db, redis, minio, keycloak, mailhog, api, worker, web).
- Pre-commit hooks and CI workflow seeded per AI Prompt §5 / §8.6.
- Documentation skeleton seeded under `docs/`.
- Seven spec §17 open questions answered in DECISIONS.md (D-003 through D-009); Q5 flipped to full ATT&CK matrix per Eugene's direction.

### Phase 1 stage 1 — API skeleton (`v0.1.1`) — 2026-05-19

- FastAPI app factory with lifespan (`apps/api/app/main.py`).
- Structured JSON logging via `structlog` with merged correlation-IDs (`apps/api/app/logging.py`).
- `CorrelationIdMiddleware` reads/echoes `X-Request-ID` (validated; 1–128 chars, alnum + `-_`).
- Global exception handler returns correlation-ID-only 500 responses; stack traces never leak (Master Spec §6.3).
- `app.config.Settings` (pydantic-settings) loads every env var, refuses production with `SHIELD_REDACTION_MODE=off` or placeholder `JWT_SIGNING_SECRET`.
- SQLAlchemy 2 + Alembic wiring (`alembic.ini`, `alembic/env.py`, `script.py.mako`), shared metadata naming convention.
- `/health` liveness endpoint.
- Runtime Dockerfile under `apps/api/Dockerfile` with least-privilege `shield` user (uid 10001), no shell, no sudo (production posture per AI Prompt §3.10 note).
- Unit tests (9 passing): health, correlation-ID middleware, exception handler, config safety asserts.

### Phase 1 stage 2 — Data model + audit log (`v0.1.2`) — 2026-05-19

- ORM models for the three Phase 1 tables: `client` (singleton org), `users` (with `UserRole` enum: admin/reviewer/client), `audit_entries` (append-only) — `apps/api/app/models/`.
- Cross-dialect first Alembic migration (`alembic/versions/0001_initial_schema.py`): creates tables on both Postgres and SQLite; installs Postgres-only `audit_entries_block_mutation()` trigger function + `BEFORE UPDATE`/`BEFORE DELETE` triggers.
- Application-layer append-only guard: `SQLAlchemy` `before_flush` event listener raises `AuditEntryImmutableError` on any update or delete of an `AuditEntry`. Catches logic bugs even when running against SQLite or if the prod trigger is somehow missing.
- `app.audit.spine.audit()` is the only blessed write surface for audit rows; automatically merges the current correlation ID from the request context.
- `/ready` readiness probe that touches the DB (`SELECT 1`) and reports per-dependency status (returns 200 with `status=degraded` rather than 5xx, so load balancers get a clean signal but readiness sweeps stay green).
- Alembic env honors any `sqlalchemy.url` already set in the config (tests override it for SQLite).
- 16 unit tests passing: migration applies cleanly on SQLite; ORM round-trips a User + audit row; audit immutability fires on UPDATE and DELETE; client singleton inserts; `audit()` row carries correlation_id; everything from stage 1 still green.

### Phase 1 stage 3 — Auth backbone (`v0.1.3`) — 2026-05-19

- Argon2id password hashing tuned per OWASP Password Storage Cheat Sheet (`apps/api/app/security/password.py`).
- HS256 JWT issue + verify with typed claims (`apps/api/app/security/jwt.py`); separate access / refresh `typ` claim; `verify_token(expected_type=...)` prevents token-confusion attacks.
- Lockout bookkeeping columns added to `users` via migration `0002_user_lockout_columns.py`: `failed_login_count`, `last_failed_login_at`, `locked_until_at`. 10 failed attempts in 15 minutes locks the account (Master Spec §4.5).
- Auth routes (`apps/api/app/routes/auth.py`):
  - `POST /auth/register` — self-registration per D-004. First registrant becomes Primary POC with `admin` role; subsequent registrants are `client`.
  - `POST /auth/login` — email + password. Account-existence oracle defended (wrong-email runs a dummy Argon2 verify so timing matches wrong-password).
  - `POST /auth/refresh` — refresh token → new access + refresh pair. Refuses access tokens.
  - `POST /auth/logout` — audited.
  - `GET /auth/me` — current user.
- `current_user` FastAPI dependency: validates `Authorization: Bearer <access>` and loads the user (`apps/api/app/dependencies.py`).
- 14 new auth route tests + 13 primitive tests = 43 unit tests all passing.

### Phase 1 stage 4 — Keycloak realm (`v0.1.4`) — 2026-05-19

- `infra/keycloak/shield-realm.json` imported on `keycloak` service start (compose mounts the dir at `/opt/keycloak/data/import` and starts with `--import-realm`).
- Realm + 3 realm roles (admin / reviewer / client) + 2 clients (`shield-web` public OIDC w/ PKCE S256, `shield-api` bearer-only).
- Brute-force protection mirrors API lockout counters (10 failures, 60s/900s waits).
- SSO session idle 1800s, max 86400s — matches Master Spec §4.5.
- Bootstrap dev-admin user with temporary password (dev only).

### Phase 1 stage 5 — Next.js skeleton (`v0.1.5`) — 2026-05-19

- `apps/web` baseline: Next.js 14.2 App Router + React 18 + TS strict + Tailwind 3.4 + NextAuth 4.24.
- `next.config.mjs` ships `output: "standalone"` for slim prod image, security headers (`X-Frame-Options: DENY`, HSTS, Permissions-Policy, no `X-Powered-By`).
- NextAuth Credentials provider (`src/lib/auth/options.ts`) posts to `/auth/login` on the API and stores access + refresh tokens in the encrypted JWT session. 401/423 from the API map to `null` (sign-in failure); other errors propagate.
- Server-side `apiFetch<T>()` helper (`src/lib/api.ts`) attaches Bearer tokens, surfaces correlation IDs from `X-Request-ID`, raises `ApiError` with status + payload on non-2xx.
- Typed session augmentation in `src/types/next-auth.d.ts` exposes `session.role` and `session.accessToken`.
- Placeholder landing at `/` (real Round-6 landing arrives in stage 7).
- Smoke: `pnpm typecheck` clean; `pnpm build` succeeded — 4 routes built (`/`, `/_not-found`, `/api/auth/[...nextauth]`), 87.2 kB First Load JS shared.

### Phase 1 stage 6 — Design-system primitives (`v0.1.6`) — 2026-05-19

- New workspace package `@shield/design-system` (`packages/design-system/`).
- Round-6 tokens in `src/tokens.css` as CSS custom properties: surface, ink, border, brand navy, status palette (saturated colors reserved for status per Round-6), type scale, 4-px spacing scale, radii, soft shadows, motion tokens that collapse under `prefers-reduced-motion`.
- Tailwind preset (`src/tailwind-preset.ts`) wires the tokens to classnames.
- 8 primitives, all keyboard-accessible and WCAG-2.1-AA-targeted:
  - `Card` + sub-parts — modular, soft shadow.
  - `StatusPill` — saturated colors only here per Round-6.
  - `NumberCard` — KPI card for executive surfaces.
  - `DataTable` — sticky header, sortable columns with `aria-sort`, row click, empty-state slot.
  - `Toast` + `ToastProvider` + `useToast()` — `aria-live=polite` region, auto-dismiss.
  - `Modal` + `SlideOver` — native `<dialog>` (browser focus trap + ESC), backdrop click closes.
  - `EmptyState` — icon + title + description + action slot.
- Wired into `apps/web`: package dep, Tailwind preset, token CSS import, placeholder `/` now uses `Card` + `StatusPill`.
- Smoke: `pnpm typecheck` clean across workspace; `pnpm build` succeeded — `/` route now 8.57 kB First Load JS (up from 138 B placeholder); 4 routes, 87.1 kB shared.

### Phase 1 stage 7 — Landing + auth screens (`v0.1.7`) — 2026-05-19

- Marketing landing (`/`): `PublicHeader` + `Hero` + `ServiceGrid` (4 service cards using `Card` from `@shield/design-system`) + trust strip with `StatusPill`s + `PublicFooter`. Round-6 PUBLIC EXPERIENCE tier.
- `/sign-in`: NextAuth Credentials-backed form (`SignInForm`) wrapped in `<Suspense>` (uses `useSearchParams` for `callbackUrl`). Errors render inline; 401/423 from the API surface as "Invalid email or password" to avoid an account-existence oracle.
- `/sign-up`: form (`SignUpForm`) posting to `/api/proxy/auth/register`, which proxies to the FastAPI `/auth/register` via the server-side `apiFetch` helper. On success, immediately calls `signIn("credentials")` so the user lands in an authenticated session.
- `/api/proxy/auth/register`: thin server route that keeps API host names off the wire to the browser and maps `ApiError` → `NextResponse` with the upstream status preserved.
- Footer pages stubbed at `/accessibility`, `/privacy`, `/security` so the footer nav doesn't 404; each carries a real mailto contact for the relevant team.
- `AuthSessionProvider` (NextAuth `SessionProvider`) and `ToastProvider` wired into the root layout.
- `next.config.mjs` `typedRoutes` left OFF intentionally (requires `next build` to populate the route manifest before `tsc --noEmit`, which we run as a pre-build smoke).
- Smoke: `pnpm typecheck` clean across workspace; `pnpm build` succeeded — 9 routes total (`/`, `/_not-found`, `/sign-in`, `/sign-up`, `/accessibility`, `/privacy`, `/security`, `/api/auth/[...nextauth]`, `/api/proxy/auth/register`). First Load JS shared 87.2 kB; biggest route (`/sign-up`) at 105 kB.
