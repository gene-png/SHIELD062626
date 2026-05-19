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
