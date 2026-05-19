# Development guide

## Prerequisites

- Docker Desktop (or Docker Engine) with Compose v2.
- VS Code with the Dev Containers extension (recommended).
- A GitHub account with push access to `github.com/gene-png/SHIELDV2-051826v2`.

## First-time setup

1. Open the repo in VS Code → **Reopen in Container**.
2. The container build runs `.devcontainer/post-create.sh` (per AI Prompt §3.11), which:
   - chowns the repo and caches to `appuser`.
   - Marks the repo a safe directory for git.
   - Copies `.env.example` → `.env` if missing.
   - Runs `pnpm install`.
   - Installs `pre-commit` hooks.
3. Edit `.env`:
   - Paste your `ANTHROPIC_API_KEY` (or leave blank if running in `SHIELD_LLM_MODE=fixture`).
   - Generate `NEXTAUTH_SECRET` with `openssl rand -hex 32`.

## Daily workflow

```bash
# Bring the stack up
docker compose up -d db redis minio keycloak mailhog
docker compose up -d --build api worker

# Start the web dev server (inside the web container)
docker compose exec web bash scripts/dev-web.sh

# Watch api logs
docker compose logs -f api

# Run tests
docker compose exec api pytest -m unit
docker compose exec api pytest -m integration
docker compose exec web pnpm test
```

## Commit discipline

Per AI Prompt §3.9, every commit:

1. Uses Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `security:`).
2. References the spec section being implemented.
3. Has a smoke test documented in the body (command + expected vs observed).
4. Passes pre-commit hooks (no `--no-verify` without a follow-up fix).

Stage tags: `v0.<phase>.<stage>`. Phase tags: `v0.<phase>.0`. Final tag: `v1.0.0`.

## Adding a route

1. Create the SQLAlchemy model under `apps/api/app/models/`.
2. Generate the Alembic migration: `docker compose exec api alembic revision --autogenerate -m "add <thing>"`.
3. Add the Pydantic schema under `apps/api/app/schemas/`.
4. Add the route under `apps/api/app/routes/`.
5. Add the audit-log call inside the route (every state-changing route writes an audit row).
6. Add unit + integration tests under `apps/api/tests/`.
7. Regenerate shared types: `docker compose exec api python -m app.codegen.types > packages/shared-types/src/index.ts`.
8. Add the client call in `apps/web/src/lib/api/`.

## Adding a page

1. Add the route file under `apps/web/app/`.
2. Compose from existing primitives in `packages/design-system/` (Round 6 design language).
3. Write the Playwright test under `e2e/`.
4. Run `pnpm -F web a11y <route>` to confirm WCAG 2.1 AA.
5. Verify every `<Link href=...>` resolves (linkrot check).

## Debugging

- API debugger: `apps/api/app/main.py` honors `DEBUGPY_PORT` env var.
- Web debugger: standard Chrome DevTools or VS Code "Attach to Node" against port 9229.
- DB shell: `docker compose exec db psql -U shield -d shield`.
- Redis shell: `docker compose exec redis redis-cli`.
- MinIO console: http://localhost:9001 (user/pass from `.env`).
