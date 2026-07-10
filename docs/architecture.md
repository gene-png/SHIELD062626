# Architecture

> Authoritative spec: [`reference-docs/SHIELDv2_Master_Spec.txt`](../reference-docs/SHIELDv2_Master_Spec.txt) §§ 4, 11, 16 — as amended by
> [`DECISIONS.md`](../DECISIONS.md) (notably D-015 multi-tenant and the Work
> Order Parts A–F entries). Where this document and the spec disagree, the
> decision log wins; this document describes what is actually running.

## 10,000-foot view

SHIELD is a **multi-tenant** web platform (D-015): one deployment serves many
client organizations. Every business table carries a `client_id` column and
every data route filters by the resolved tenant. One Next.js app talks to one
FastAPI service, with shared infrastructure (Postgres, Redis, MinIO/S3,
Keycloak, MailHog). There is **no worker service** — AI jobs run synchronously
inside the `api` process.

Two user roles:

- **admin** — Kentro consultant, platform-wide (`User.client_id IS NULL`);
  picks the active tenant per request via the `X-Client-Id` header (surfaced
  as a client switcher in the web nav). An earlier read-only "reviewer" role
  was folded into admin by Work Order A3 (see the DECISIONS.md supersession
  erratum for D-005/D-006).
- **client** — a customer user, pinned to their own `client_id` at
  registration; requests cannot escape it.

Four assessment services — Technical Debt Review, Zero Trust (CISA ZTMM 2.0 +
DoD ZTRA), NIST CSF 2.0 (10-step Playbook), MITRE ATT&CK coverage — plus a
Risk Register (5x5, NIST 800-30) synthesized from them.

## Components

```
┌────────────────────────────────────────────────────────────┐
│                         Browser                            │
└──────────────────┬─────────────────────────────────────────┘
                   │ TLS
                   ▼
┌────────────────────────────────────────────────────────────┐
│  apps/web — Next.js 14 (App Router, TS strict)             │
│  • NextAuth Credentials → SHIELD-issued JWT                │
│    (Keycloak realm scaffolded for later OIDC federation)   │
│  • Tailwind + shadcn (Round 6 design language)             │
│  • /api/proxy/* server routes forward to the API with the  │
│    session bearer + X-Client-Id; API host never reaches    │
│    the browser                                             │
└──────────────────┬─────────────────────────────────────────┘
                   │ HTTP (server-side calls)
                   ▼
┌────────────────────────────────────────────────────────────┐
│  apps/api — FastAPI (Python 3.12)                          │
│  • Pydantic v2 schemas; SQLAlchemy 2 + Alembic             │
│  • Tenant resolution (current_client) + app/tenant.py      │
│    ownership checks on every data route                    │
│  • Deterministic scoring engines (csf/risk/zt)             │
│  • Synchronous AI jobs via app/ai/engine.run_job           │
│  • PII redactor on every LLM egress (app/ai/redact.py)     │
│  • Typed error envelope {reason, message} (D-016)          │
│  • JSON structured logs (structlog) + correlation IDs      │
└──────┬──────────────┬──────────────┬──────────────┬────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
   Postgres 16    Redis 7        MinIO (S3)    Keycloak 25
   (data model)  (rate          (artifact      (realm export;
                  limiting)      storage)       future OIDC)
```

Dev stack also runs MailHog (SMTP capture, `:8025`). There is no Celery, no
queue, and no `apps/worker` — the orphaned worker service was removed in Work
Order Part F (see DECISIONS.md D-021). Redis's real job
today is the fixed-window **rate limiting** on auth and run-AI routes
(`app/security/rate_limit.py`, Sprint 3 T3); the limiter fails open with a
loud warning if Redis is down.

## Tech stack

| Layer          | Choice                                                                    | Notes                                                                                                |
| -------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Frontend       | Next.js 14 App Router + React 18 + TypeScript strict + Tailwind + shadcn  | Round 6 design language; `@shield/design-system` package                                             |
| Backend        | FastAPI on Python 3.12                                                    | OpenAPI at `:8000/docs`                                                                              |
| Database       | PostgreSQL 16 (prod/dev), SQLite (unit tests)                             | Alembic migrations, `batch_alter_table` for SQLite safety                                            |
| Cache          | Redis 7                                                                   | Rate limiting only — no queue, no Celery                                                             |
| Object storage | S3-compatible (MinIO in dev)                                              | Artifact uploads + generated deliverables                                                            |
| IdP            | SHIELD-issued JWT (HS256) via NextAuth Credentials                        | Keycloak realm scaffolded under `infra/keycloak/` for later                                          |
| AI             | Single egress client `app/ai/llm.py`; Anthropic/OpenAI/Gemini or fixtures | `SHIELD_LLM_MODE=fixture` is the offline default (D-017); provider via `SHIELD_LLM_PROVIDER` (D-024) |
| Tests          | pytest (unit, SQLite) + Playwright e2e (host-run) + axe sweep             | See `docs/development.md` for the real command matrix                                                |

## Data isolation (multi-tenant, D-015)

- Every business table carries `client_id`; reads filter by it, writes set it
  at row creation.
- `current_client` (in `app/dependencies.py`) resolves the active tenant:
  client-role users are pinned to `user.client_id`; platform admins name a
  tenant with `X-Client-Id`.
- Id-based fetches go through `app/tenant.py` `require_*_in_tenant` helpers,
  which return **404 on tenant mismatch** — no existence oracle.
- Cross-tenant isolation is unit-tested (`test_new_surface_authz.py` and the
  tenant/draft-guard suites) under `pytest -m unit`.

## Audit log

Every state-changing route writes one row to **`audit_entries`** via the only
blessed write surface, `app/audit/spine.py::audit()`. Append-only at two
layers: a Postgres `BEFORE UPDATE/DELETE` trigger in production, plus a
SQLAlchemy `before_flush` guard that raises `AuditEntryImmutableError` on any
dialect (so SQLite tests catch violations too). Rows carry actor user id,
action verb, target type + id, JSON details, and the request correlation id.

## AI integration boundary

"**AI suggests, code computes.**" The LLM only drafts values and narrative;
every score, tier, roll-up and roadmap is computed by deterministic Python
engines (`app/csf/playbook.py`, `app/risk/engine.py`, `app/zt/scoring.py`).

```
route → engine.run_job(purpose, payload, client_id)
          → redact_payload(payload)            # app/ai/redact.py, counts only
          → llm_calls row opened (status=running, client_id, service_id)
          → provider call (Anthropic | OpenAI | Gemini | runtime fixtures)
          → llm_calls row finalized (tokens, duration, redacted_counts)
          → route parses the draft and writes rows; engines compute totals
```

- The redactor is one-way. There is **no `unredact`** — redacted content
  never needs to come back, because the LLM's draft references stable codes
  (technique ids, subcategory codes), not the redacted prose.
- `llm_calls` records **counts only, never payload content** (§12.1), and is
  attributed to the tenant via `client_id` (Sprint 3 T5) plus `service_id`
  where a service is in play.
- Five job purposes: `extract.capabilities`, `mitre_map`, `zt_score`,
  `csf_score`, `risk_synthesize`. In fixture mode (the offline default,
  D-017) each has a deterministic, payload-aware canned response; live mode
  needs `SHIELD_LLM_MODE=live` plus the selected provider's API key.
- **Provider seam (D-024).** `SHIELD_LLM_PROVIDER` selects the live adapter;
  every adapter lives below the egress seam and only translates prompt +
  redacted payload → provider REST API → text back. Redaction, the
  `llm_calls` audit row, and "AI suggests, code computes" all sit _above_ the
  seam and are provider-independent. Thin `httpx` adapters (no SDK) for
  OpenAI (chat/completions) and Gemini (generateContent); Anthropic
  lazy-imports its SDK.

  | Provider              | Status          | Key env var         |
  | --------------------- | --------------- | ------------------- |
  | `anthropic` (default) | Implemented     | `ANTHROPIC_API_KEY` |
  | `openai`              | Implemented     | `OPENAI_API_KEY`    |
  | `gemini`              | Implemented     | `GEMINI_API_KEY`    |
  | `azure_openai`        | Not implemented | —                   |
  | `bedrock`             | Not implemented | —                   |
  | `local`               | Not implemented | —                   |

  A missing key for the selected provider, or a not-implemented provider,
  raises a loud `RuntimeError` at construction.

- Run-AI endpoints are rate-limited per client (T3).

## Auth

- SHIELD-issued HS256 JWTs: 15-minute access tokens, 30-minute refresh tokens
  (the refresh TTL **is** the idle timeout).
- Refresh rotation: single active refresh jti per user; a replayed token is
  rejected (`reason=refresh_reused`). Forced re-auth ceiling: `auth_time`
  claim, 24h default (`reason=reauth_required`). See D-020.
- Account lockout (10 failures / 15 min) and per-IP + per-account rate limits
  on login/register, checked before Argon2 work (T3).
- MFA / email-verification flows do not exist; setting their flags true
  refuses boot (fail loudly, D-020).

## Failure model

- API errors use the typed `{reason, message}` dict-detail envelope (D-016);
  the web maps reasons to friendly copy. Never a raw validation dump, never a
  silent success-lie.
- 5xx responses carry the correlation ID only — no stack traces.
- AI jobs are synchronous: the run-AI request returns the outcome directly
  (typed 4xx/5xx on failure — e.g. 502 on an unparseable LLM response, 503 on
  a missing runtime fixture).
