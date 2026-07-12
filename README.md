# SHIELD by Kentro v2.0

Enterprise cybersecurity assessment platform. Multi-tenant — one deployment serves many client organizations, every business row carries a `client_id` (DECISIONS.md D-015). FedRAMP Moderate/High target. Four assessment services plus a Risk Register (5x5, NIST 800-30) synthesized from them:

1. **Technical Debt Review** — capability inventory, overlap analysis, consolidation plan.
2. **Zero Trust Assessment** — CISA ZTMM 2.0 and DoD ZTRA, scored per pillar with current/target maturity.
3. **NIST CSF 2.0 Assessment** — full 10-step Playbook with HIGH/MOD/LOW tiered profiles, 5-dimension scoring, weighted-floor roll-up, gap analysis, action plan.
4. **MITRE ATT&CK Coverage Mapping** — full Enterprise matrix (~600 techniques) scored against the approved capability list.

> **Authoritative spec:** [`reference-docs/SHIELDv2_Master_Spec.txt`](reference-docs/SHIELDv2_Master_Spec.txt).
> **AI build prompt:** [`reference-docs/AI_Prompt`](reference-docs/AI_Prompt).
> **Design language contract (governs UI on conflict):** [`reference-docs/Shield_UX_Round6_Design_Contract.txt`](reference-docs/Shield_UX_Round6_Design_Contract.txt).
> **Decision log:** [`DECISIONS.md`](DECISIONS.md).
> **Build status:** [`BUILD_REPORT.md`](BUILD_REPORT.md).

## Repository layout

```
apps/
  web/              Next.js 14 (App Router, TS strict, Tailwind, shadcn/ui)
  api/              FastAPI (Python 3.12) - REST API + OpenAPI, synchronous AI jobs
packages/
  design-system/    Tailwind tokens + shadcn components + label maps + copy
  shared-types/     TS types generated from apps/api OpenAPI
  csf-data/         CSF 2.0 subcategory CSV + IG metric crosswalk
  attack-data/      Vendored MITRE ATT&CK Enterprise JSON (full matrix)
  zt-data/          CISA + DoD questionnaire seed JSON
infra/
  docker/           Runtime Dockerfiles (least-privilege, no sudo)
  terraform/        Placeholder only (empty) - IaC is planned, not present
  keycloak/         Realm export imported on container start
docs/               Architecture, security, operations, development, guides
scripts/            Seed loaders + dev helpers
reference-docs/     Locked SHIELD v2 reference documents (spec, mockup, questionnaires)
e2e/                Playwright end-to-end tests
.devcontainer/      VS Code Dev Container config (appuser + passwordless sudo)
```

## Prerequisites

- Docker Desktop (or Docker Engine) with Docker Compose v2
- VS Code with the Dev Containers extension (recommended)
- An `ANTHROPIC_API_KEY` if running real LLM calls (defaults to `fixture` mode otherwise)

All development happens inside the dev container. Nothing installs to the host.

## Quick start

### Option A - VS Code Dev Containers (recommended)

1. Open the repo in VS Code with the **Dev Containers** extension installed.
2. When prompted, **Reopen in Container**. VS Code builds the dev image and brings up the compose services (db, redis, minio, keycloak, mailhog, api, web). There is no `worker` service — AI jobs run synchronously in `api`.
3. Once VS Code attaches, run:
   ```bash
   cp .env.example .env
   # edit .env: paste your ANTHROPIC_API_KEY and run `openssl rand -hex 32` for NEXTAUTH_SECRET
   bash scripts/dev-web.sh
   ```
4. In a second terminal:
   ```bash
   docker compose logs -f api
   ```
5. Open http://localhost:3000 once you see Next.js boot output.

### Option B - plain Docker Compose

```bash
cp .env.example .env
docker compose up -d db redis minio keycloak mailhog
docker compose up -d --build api
docker compose run --service-ports --rm web bash scripts/dev-web.sh
```

### URLs once everything is up

| Service        | URL                        |
| -------------- | -------------------------- |
| Web (Next.js)  | http://localhost:3000      |
| API (FastAPI)  | http://localhost:8000/docs |
| Keycloak admin | http://localhost:8080      |
| MinIO console  | http://localhost:9001      |
| MailHog UI     | http://localhost:8025      |
| Postgres       | postgres://localhost:5432  |

## Environment variables

Every variable in [`.env.example`](.env.example) is required. Summary:

| Group          | Vars                                                                                                                                           | Notes                                         |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Runtime        | `ENVIRONMENT`, `LOG_LEVEL`                                                                                                                     |                                               |
| Database       | `DATABASE_URL`                                                                                                                                 | Postgres 16, locked in Master Spec §2         |
| Redis          | `REDIS_URL`                                                                                                                                    | Rate limiting (auth + run-AI); no queue       |
| Object storage | `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_KMS_KEY_ID`                                                              | MinIO in dev, S3+KMS in prod                  |
| OIDC           | `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`                                      |                                               |
| NextAuth       | `NEXTAUTH_URL`, `NEXTAUTH_SECRET`                                                                                                              | Generate secret with `openssl rand -hex 32`   |
| LLM            | `SHIELD_LLM_PROVIDER`, `SHIELD_LLM_MODEL`, `SHIELD_LLM_MODE`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`                          | `MODE=fixture` for offline tests              |
| Feature flags  | `SHIELD_AUTH_REQUIRE_MFA`, `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY`, `SHIELD_EMAIL_DELIVERY_ENABLED`                                                 | All `false` for v1                            |
| Redaction      | `SHIELD_REDACTION_MODE`                                                                                                                        | `strict` in prod; `off` forbidden outside dev |
| Sessions       | `JWT_ACCESS_TTL_SECONDS`, `JWT_REFRESH_TTL_SECONDS`, `SHIELD_ACCOUNT_LOCKOUT_*`, `SHIELD_IDLE_TIMEOUT_SECONDS`, `SHIELD_FORCED_REAUTH_SECONDS` | Compensating controls for deferred MFA        |
| Mail           | `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`                                                                                                          | MailHog locally                               |

### LLM providers

`SHIELD_LLM_PROVIDER` selects the live egress adapter; `SHIELD_LLM_MODEL` is
the single model knob (set it to a model the chosen provider serves). Fixture
mode (`SHIELD_LLM_MODE=fixture`, the default) is fully offline and never touches
any provider. Every provider sits below the same egress seam — redaction and the
`llm_calls` audit row run identically regardless of provider.

| Provider              | Status          | Key env var         | Example `SHIELD_LLM_MODEL` |
| --------------------- | --------------- | ------------------- | -------------------------- |
| `anthropic` (default) | Implemented     | `ANTHROPIC_API_KEY` | `claude-opus-4-7`          |
| `openai`              | Implemented     | `OPENAI_API_KEY`    | `gpt-4o-mini`              |
| `gemini`              | Implemented     | `GEMINI_API_KEY`    | `gemini-1.5-pro`           |
| `azure_openai`        | Not implemented | —                   | —                          |
| `bedrock`             | Not implemented | —                   | —                          |
| `local`               | Not implemented | —                   | —                          |

Selecting a provider whose key is unset fails loudly at construction; selecting
a not-implemented provider raises a loud `RuntimeError`. FedRAMP deployments pick
the provider that sits inside their authorization boundary (D-024).

## Running tests

The real test matrix (all of it runs in CI):

```bash
# API unit tests (SQLite in-process; the whole backend suite)
docker compose exec -T api pytest -m unit -q

# Web typecheck
docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"

# Formatting (lockfile-pinned prettier; CI enforces it)
npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"

# End-to-end (Playwright) - host-run against the running stack on :3000.
# 16 spec files / 34 tests under e2e/smoke/. Chromium only, serialized;
# needs the stack up and the demo seed loaded (scripts/seed_demo.py).
cd e2e && npm install && npx playwright test          # whole suite
cd e2e && npx playwright test smoke/s15-headers.spec.ts   # one spec
```

There is no separate web unit-test runner (`pnpm test` does not exist) and no
`pytest -m integration` suite — the marker is declared but unused; Playwright
covers the integrated stack end-to-end.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) - system architecture
- [`docs/security.md`](docs/security.md) - OWASP review, redaction, audit
- [`docs/development.md`](docs/development.md) - developer onboarding
- [`docs/operations.md`](docs/operations.md) - what runs today + planned production posture
- [`docs/admin-guide.md`](docs/admin-guide.md) - Kentro consultant guide (filled across phases)
- [`docs/client-guide.md`](docs/client-guide.md) - client-facing guide (filled across phases)

Runbooks (incident, backup, key rotation, DR) are **planned, not written** —
`docs/runbooks/` is currently empty. Terraform IaC is likewise planned
(`infra/terraform/` is an empty placeholder); cloud/account/region decisions
are pending.

## Risk acceptance log

Per Master Spec §2, two risks are explicitly accepted for v1:

1. **Commercial LLM provider may not be FedRAMP-authorized.** Egress may leave the FedRAMP boundary. Mandatory PII redaction (`apps/api/app/ai/redact.py`) is the primary control. See [`docs/security.md`](docs/security.md).
2. **MFA and email verification deferred for v1.** Compensating controls that are actually enforced: 15-minute access-token lifetime; a 30-minute refresh-token TTL that functions as the idle timeout (an idle session cannot refresh past it); a daily (24h) forced re-auth ceiling enforced at `/auth/refresh` via an `auth_time` claim (typed 401 `reason=reauth_required`, tunable with `SHIELD_FORCED_REAUTH_SECONDS`); single-use refresh-token rotation (a replayed/rotated-out refresh token is rejected, `reason=refresh_reused`); and account lockout after 10 failed attempts in 15 minutes. The MFA and email-verification **flows do not exist yet** — the `SHIELD_AUTH_REQUIRE_MFA` / `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY` flags therefore **fail loudly at startup** if set true (the app refuses to boot rather than silently pretend a control is active); wiring the flows up is planned for a later sprint.

## License

Proprietary. See [`LICENSE`](LICENSE). Operated by Kentro on behalf of customer engagements.
