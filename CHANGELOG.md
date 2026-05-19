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
