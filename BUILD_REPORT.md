# SHIELD v2.0 — Build Report

> Live build status. Per AI Prompt §14, Eugene reads this first.
> See [`How to resume an interrupted build`](#how-to-resume-an-interrupted-build) below for resume instructions.

## Overall status

**Phase 1 complete (`v0.1.0`). Phase 2 (Intake) next.**

| Phase                                                          | Status                     | Last tag   |
| -------------------------------------------------------------- | -------------------------- | ---------- |
| Opening commit (scaffold)                                      | Complete                   | (untagged) |
| Phase 1 stage 1 — API skeleton                                 | Complete                   | `v0.1.1`   |
| Phase 1 stage 2 — Data model + audit log                       | Complete                   | `v0.1.2`   |
| Phase 1 stage 3 — Auth backbone                                | Complete                   | `v0.1.3`   |
| Phase 1 stage 4 — Keycloak realm                               | Complete                   | `v0.1.4`   |
| Phase 1 stage 5 — Web skeleton (Next.js + Tailwind + NextAuth) | Complete                   | `v0.1.5`   |
| Phase 1 stage 6 — Design-system primitives (Round-6)           | Complete                   | `v0.1.6`   |
| Phase 1 stage 7 — Landing + auth screens                       | Complete                   | `v0.1.7`   |
| Phase 1 stage 8 — CI green                                     | Complete                   | `v0.1.8`   |
| Phase 1 stage 9 — Phase 1 acceptance gate                      | **Complete (this commit)** | `v0.1.0`   |
| Phase 2 — Intake                                               | **Next**                   | —          |
| Phase 3 — Tech Debt service                                    | Not started                | —          |
| Phase 4 — CSF service                                          | Not started                | —          |
| Phase 5 — Zero Trust + ATT&CK                                  | Not started                | —          |
| Phase 6 — Polish and harden                                    | Not started                | —          |

## Phase 1 acceptance criteria (Master Spec §15 Phase 1)

| Criterion                                                          | Status                                                                                                                      | Evidence                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| User can self-register, **verify email**, **enroll MFA**, sign in. | **PARTIAL** — self-register + sign in shipped; email-verify + MFA feature-flag-deferred per Master Spec §2 locked decision. | `apps/api/app/routes/auth.py` register/login; `SHIELD_AUTH_REQUIRE_EMAIL_VERIFY=false` + `SHIELD_AUTH_REQUIRE_MFA=false`. Flag schema columns already exist on `users` (`email_verified_at`, `mfa_enrolled`); flip the flags in v1.x with no code change.                                                                                    |
| Three roles distinguishable (admin / reviewer / client).           | **PASS**                                                                                                                    | `UserRole` enum in `apps/api/app/models/user.py`; first registrant becomes `admin` (Primary POC) per D-004, subsequent registrants are `client`; `reviewer` role assignable in Phase 4 (D-005).                                                                                                                                              |
| Audit log records every login.                                     | **PASS**                                                                                                                    | `audit()` helper writes `user.login` audit row on every successful login (`apps/api/app/routes/auth.py:_register_successful_login`); `user.created`, `user.locked`, `user.logout` audit rows also written. Append-only enforced at two layers (Postgres trigger in migration `0001` + SQLAlchemy event listener in `models/audit_entry.py`). |
| No stack trace surfaces to user under any forced error.            | **PASS**                                                                                                                    | Verified by `test_unhandled_exception_returns_500_without_stack_trace` — forces `RuntimeError("internal secret value ...")`, asserts the response body contains no `RuntimeError`, no `Traceback`, no internal message — only `correlation_id` and a plain-English message.                                                                  |

Net: **3/4 acceptance criteria fully met; 1/4 partially met by explicit Master Spec §2 risk acceptance** (email-verify + MFA are feature-flagged off for v1, with compensating controls: short JWT TTL, 30-minute idle timeout, daily forced re-auth, account lockout after 10 failed attempts in 15 minutes).

## OWASP Top 10 cumulative review (as of `v0.1.0`)

| ID  | Category                       | Status                                                                                                                                                                                                             |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A01 | Broken Access Control          | PARTIAL — `current_user` dep enforces authenticated routes; role-based guards land in Phase 2 (admin queue)                                                                                                        |
| A02 | Cryptographic Failures         | PASS — Argon2id (OWASP cheat-sheet parameters) + HS256 JWT; placeholder secret refused in production by `assert_safe_for_runtime`                                                                                  |
| A03 | Injection                      | PASS — SQLAlchemy parameterized queries only; no raw SQL in app code                                                                                                                                               |
| A04 | Insecure Design                | PASS — threat model documented, audit immutability at two layers, redaction-as-boundary policy documented (redactor module lands in Phase 3 with Tech Debt extraction)                                             |
| A05 | Security Misconfiguration      | PASS — `assert_safe_for_runtime()` refuses unsafe production combos; HSTS + X-Frame-Options + X-Content-Type-Options + Permissions-Policy + Referrer-Policy enforced by `next.config.mjs`; `X-Powered-By` disabled |
| A06 | Vulnerable Components          | PARTIAL — versions pinned; pip-audit + pnpm audit + Dependabot land in Phase 6                                                                                                                                     |
| A07 | Identification & Auth Failures | PARTIAL — email+password + Argon2id + lockout + account-existence-oracle defense done; MFA + email verification deferred per Master Spec §2 (compensating controls listed above)                                   |
| A08 | Software & Data Integrity      | PASS — audit rows immutable by contract                                                                                                                                                                            |
| A09 | Logging & Monitoring           | PASS — structured JSON + correlation IDs everywhere; audit log on every state change; correlation ID surfaces in user-facing 500s                                                                                  |
| A10 | SSRF                           | PASS — LLM endpoint env-configured only; no user-supplied URLs anywhere in v1                                                                                                                                      |

## Tests at HEAD

```
$ /tmp/shield-api-venv/bin/python -m pytest -m unit \
    /workspaces/repos/SHIELDV2-051826v2/apps/api/tests/unit \
    --rootdir /workspaces/repos/SHIELDV2-051826v2/apps/api -q
43 passed

$ pnpm format:check && pnpm -F web lint && pnpm -F web typecheck && pnpm -F web build
prettier: All matched files use Prettier code style!
eslint:   No ESLint warnings or errors
tsc:      No errors
next:     9 routes built; 87.2 kB First Load JS shared
```

## Open items

1. **Docker not available in current container.** Postgres-specific audit-trigger smoke + 8-service stack integration smoke await a devcontainer rebuild with `docker-outside-of-docker`.
2. **axe-core accessibility scan** is intentionally deferred to Phase 6 hardening — Playwright install + browser binaries is heavy and the spec acceptance criterion is "no stack trace surfaces to user", not "axe-core green", for Phase 1. WCAG-2.1-AA is implemented at the component layer (Round-6 tokens, `aria-*` on dialogs, focus-visible outlines, semantic landmarks); third-party audit lands in Phase 6 per Master Spec §15 Phase 6.
3. **Phase 2 (Intake) ready to start.** Six-step wizard, section-tabbed questionnaire renderer (shared component used by CSF/ZT/ATT&CK later), auto-save, document upload with redaction disclosure.

## Significant decisions

See [`DECISIONS.md`](DECISIONS.md) for the full log. Highlights:

- **D-007 (FLIPPED):** ATT&CK uses full Enterprise matrix (~600 techniques), not curated subset.
- **D-011:** Working directory is `/workspaces/repos/SHIELDV2-051826v2`, not the spec's `/workspaces/SHIELDV2-051826v2`.
- **D-014:** Opening commit lands on `main`; push is performed when credentials are present.

## How to resume an interrupted build

If you stop me mid-stream (close the terminal, restart the container, lose the chat tab, etc.), here is exactly how to restart and have me pick up where I left off:

### One-line resume prompt

> **"Resume the SHIELD v2 build at `/workspaces/repos/SHIELDV2-051826v2`. Read `BUILD_REPORT.md`, `DECISIONS.md`, the last `git log --oneline -15`, and `CHANGELOG.md` to find where we left off. Continue with the next stage."**

That's it — paste that into a new Claude Code session and I'll figure out the state from the repo.

### What I look at to figure out where I am

1. **Last tag** = the last completed stage or phase:

   ```bash
   git -C /workspaces/repos/SHIELDV2-051826v2 describe --tags --abbrev=0
   git -C /workspaces/repos/SHIELDV2-051826v2 tag -l 'v*'
   ```

   Tag pattern: `v0.<phase>.<stage>` per stage, `v0.<phase>.0` per phase (AI Prompt §3.9). Yes, v0.1.0 ranks numerically below v0.1.8 — it's a phase-completion marker, not a strict semver progression.

2. **Recent commits**:

   ```bash
   git -C /workspaces/repos/SHIELDV2-051826v2 log --oneline -15
   ```

3. **This file** — the phase/stage table at the top is the canonical "what's done" view.

4. **`CHANGELOG.md`** — phase-by-phase narrative.

5. **`DECISIONS.md`** — every non-spec choice.

6. **`git status`** — should be clean at a stage boundary.

### What you do NOT need to re-provide on resume

- Anthropic API key (already in `.env`, gitignored)
- The plan, spec answers, Q1–Q7 from session memory
- Any prior conversation context

### What you DO need to provide on resume (one-time)

- Push credentials when ready (already attached and working as of `v0.1.4` — pushes are now automatic).
- Docker availability if you want me to integration-test the full 8-service stack.

## Recommended next steps for Eugene

1. **Rebuild the dev container** if you want to integration-test the full stack. The new `.devcontainer/devcontainer.json` already declares `docker-outside-of-docker`.
2. **Tell me to start Phase 2.** The intake wizard is the next chunk; it builds on the auth backbone shipped here.
3. **Optional:** review the Phase 1 OWASP matrix above and flag any item you want hardened before Phase 2 starts.

## How to deploy to a real FedRAMP environment

Stub — populated at Phase 6 per Master Spec §15.

## Estimated effort for deferred items

| Item                                                | Estimate                    |
| --------------------------------------------------- | --------------------------- |
| MFA enrollment + verification                       | 1.5 weeks (TOTP + WebAuthn) |
| Email verification flow                             | 0.5 weeks                   |
| FedRAMP-authorized LLM connector (Azure OpenAI Gov) | 0.5 weeks                   |
| Additional locales (per language)                   | 0.5 weeks content-only      |
| Postgres audit-trigger integration smoke            | 0.1 weeks (waits on Docker) |
| axe-core / Playwright a11y CI job                   | 0.3 weeks                   |
