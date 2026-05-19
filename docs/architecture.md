# Architecture

> Authoritative spec: [`reference-docs/SHIELDv2_Master_Spec.txt`](../reference-docs/SHIELDv2_Master_Spec.txt) §§ 4, 11, 16. This document is the narrative version.

## 10,000-foot view

SHIELD is a single-tenant web platform. One deployment per client engagement. Each deployment exposes:

- A **public-facing experience** for unauthenticated users (marketing, intake start).
- An **operational dashboard** for Admins (Kentro consultants) and Reviewers.
- An **executive experience** for Client leadership.

All three experiences are delivered by one Next.js app talking to one FastAPI service, with shared infrastructure (Postgres, Redis, S3, Keycloak, Celery workers).

## Components

```
┌────────────────────────────────────────────────────────────┐
│                  Browser (3 experiences)                   │
└──────────────────┬─────────────────────────────────────────┘
                   │ TLS 1.2+
                   ▼
┌────────────────────────────────────────────────────────────┐
│  apps/web — Next.js 14 (App Router, TS strict)             │
│  • NextAuth (Credentials → SHIELD-issued JWT for v1;       │
│    OIDC via Keycloak for v1.x onward)                      │
│  • Tailwind + shadcn (Round 6 design language)             │
│  • Server Components + Server Actions for write paths      │
└──────────────────┬─────────────────────────────────────────┘
                   │ HTTPS (server-side calls)
                   ▼
┌────────────────────────────────────────────────────────────┐
│  apps/api — FastAPI (Python 3.12)                          │
│  • Pydantic v2 schemas                                     │
│  • SQLAlchemy 2 + Alembic                                  │
│  • Global exception handler → correlation-id-only 500      │
│  • JSON structured logs to stdout                          │
│  • PII redactor as a SECURITY BOUNDARY on every LLM call   │
└──────┬──────────────┬──────────────┬──────────────┬────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
   Postgres 16    Redis 7        MinIO (S3)    Keycloak 25
   (data model)  (Celery +     (object        (OIDC IdP,
                  cache)        storage)       realm export)

                  Celery worker (apps/worker, same image as api)
                  ├── extraction jobs (LLM)
                  ├── PDF/XLSX export jobs
                  └── notification fan-out
```

## Tech stack (Master Spec §2 - locked)

| Layer          | Choice                                                                                     | Rationale                                                               |
| -------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| Frontend       | Next.js 14 App Router + React + TypeScript + Tailwind + shadcn/ui (self-hosted, copied in) | Locked by spec; matches Round 6 design language; SSR for executive PDFs |
| Backend        | FastAPI on Python 3.12                                                                     | Locked by spec; native async; OpenAPI for type generation               |
| Database       | PostgreSQL 16                                                                              | Locked by spec; row-level security available; Alembic migrations        |
| Cache + queue  | Redis 7                                                                                    | Locked by spec; Celery broker                                           |
| Object storage | S3-compatible (MinIO in dev; AWS S3 + KMS or Azure Blob in prod)                           | Locked by spec                                                          |
| IdP            | Keycloak 25 (OIDC)                                                                         | Federable to any external IdP for v1.x                                  |
| Async          | Celery 5                                                                                   | Standard Python async pattern                                           |
| Migrations     | Alembic                                                                                    | Locked by spec - no manual schema edits, ever                           |
| Tests          | pytest + Playwright + axe-core/Pa11y                                                       | Tests run as part of CI; accessibility enforced                         |

## Data isolation

Single-tenant deployment means there is **no tenant-id column** on tables. Isolation is at the deployment level (separate Postgres + Redis + bucket per client). Per Master Spec §2, this is intentional — multi-tenancy is explicitly out of scope for v1.

## Audit log

Every state-changing route writes one row to `audit_events`. Backed by an append-only DB trigger; no application code path can delete an audit row. Helper: `apps/api/app/audit/spine.py::audit()`. The audit row records: actor user id, actor role, action verb, resource type + id, before/after diff (JSON), correlation id, timestamp.

## AI integration boundary

```
caller → redactor.redact(text) → LLM provider → redactor.unredact(text)
              │                                       │
              └── audit row written before send ──────┘
```

- The redactor is `apps/api/app/ai/redact.py`. It is the security boundary, not a convenience.
- Provider is selected by `SHIELD_LLM_PROVIDER`. No code references a specific endpoint.
- `SHIELD_LLM_MODE=fixture` short-circuits to canned responses for offline tests.

## Failure model

- 4xx renders a plain-English page; never a JSON body in the user surface.
- 5xx returns a page with the correlation ID only — no stack trace, no internal error message.
- Async jobs have explicit status, retry policy, and failure notifications.
