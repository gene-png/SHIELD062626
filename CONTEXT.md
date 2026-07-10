# Project Context — state of `main`

_Last updated: 2026-07-09 (Sprint 4 close — framework majors + multi-provider
LLM). This file describes the project as of the branch it sits on and is updated
ONLY as part of a PR. Durable facts and environment gotchas live in `CLAUDE.md`;
personal in-flight status lives in `context/<name>.md`; per-sprint detail lives
in `SPRINT_<n>.md`._

## Current state

- **v2 work order (Parts A–F) merged to `main`** (PR #1, migrations 0015–0025,
  `v3.0.0`): all four service surfaces, multi-tenant onboarding, AI job
  registry, CSF Playbook engine, Risk Register, F hardening pass.
- **Sprint 1 "smoke sweep"** (`qa/smoke-sweep-sprint-1`, PR #16, `v3.0.1`):
  `SMOKE_TEST.md` backed by a green Playwright smoke suite; offline fixture-mode
  AI (D-017), typed registration errors (D-016).
- **Sprint 2 "findings burn-down"** (PR #19, `v3.0.2`): 11 tasks, CI `e2e` job
  added, suite grew to 16 files / 34 tests.
- **Sprint 3 "audit correctness & honesty"** (PR #26, `v3.0.3`): 8 tasks burning
  down the 2026-07-08 deep repo audit — CSF live-mode Run-AI schema align, real
  forced-reauth + refresh rotation, Redis rate limiting, §15.5 export filenames,
  `llm_calls.client_id` tenant attribution, architecture.md truth pass.
- **Sprint 4 "framework majors + multi-provider LLM" COMPLETE** (this branch
  `feat/majors-providers-sprint-4`, `v3.1.0`): the D-018 framework-majors bundle
  deferred from Sprint 2/3 executed one major at a time with the full e2e suite
  as the regression net, ending at **zero high/critical audit findings** at root
  and in `e2e/`, plus multi-provider LLM egress. The web stack is now **Next 15 /
  React 19 / Tailwind 4 / ESLint 9 / Node 22**. ESLint 10 is honestly deferred
  (no published Next lint stack runs on it today; see below). `OpenAIProvider`
  and `GeminiProvider` join `AnthropicProvider` behind the unchanged redacting
  egress seam (D-024). Full exit gate set green — 34-test e2e, `pytest -m unit`,
  web `tsc`, host prettier `--check` (3.9.4), and the new in-container ruff/black
  gate with root-config parity (T0). The minor version bump is justified by the
  runtime/framework majors.

### Sprint 4 task → commit

| Task | What shipped | Commit |
| --- | --- | --- |
| T0 | Lint-gate CI parity: compose-mount root `pyproject.toml` into api so in-container ruff/black match CI; gate added to runtime queue | `4c068d0` |
| T1 | Next 15.5.20 + React 19.2.7 (codemods, async request APIs, dynamic-render verify); next-auth 4 runs on 15 without Auth.js v5 | `77bd360` |
| T2 | Tailwind 4 CSS-first (`@tailwindcss/postcss`, `@theme`, utility renames); design-system tokens + `--ink-tertiary` contrast survive (s16) | `f6d816a` |
| T3 | ESLint 9 flat config (`eslint.config.js` + eslint-config-next 16 `./core-web-vitals`); 47-rule parity kept; ESLint 10 deferred upstream | `bf82fd2` |
| — | Checkpoint 1: fix CsfPlaybookPanel stale-fetch race breaking s7 (request-sequence guard) | `efcbbfc` |
| T8 | Fix MessageThread.onSend stale-fetch race (mirror the efcbbfc seq-guard); s9 deterministically green | `67e79ad` |
| T4 | Node 20→22 (three Dockerfile stages, compose image, `engines`, both CI setup-node, ONBOARDING) | `bf6ccdd` |
| T5 | Audit to zero: root pnpm 0 high/0 critical, e2e npm 0; 2 documented moderates left open; dependabot policy comment refreshed | `987a4f2` |
| — | Checkpoint 2: clean pass (full e2e green, security clean, no fix) | `05121de` |
| T6 | Multi-provider LLM egress: OpenAI + Gemini httpx adapters beside Anthropic; egress contract untouched; 11 unit tests; D-024 | `05121de` |
| T7 | Wrap-up: CHANGELOG `[3.1.0]`, BUILD_REPORT A06 zero-audit, SMOKE_TEST §14 verify, this snapshot | this commit |

No new migrations this sprint (T6 added only nullable settings, no schema).
New DECISIONS: **D-024** (multi-provider LLM egress below the seam). The D-018
"ESLint 10" line item is honestly annotated as deferred-upstream in the T3
commit body and CHANGELOG.

## Machine-local facts (this box)

- **Web runs on port 3001**, not 3000: root `.env` `WEB_PORT=3001` /
  `NEXTAUTH_URL=:3001` (a separate next-dev holds `:3000`). Playwright resolves
  the port via `e2e/helpers/baseUrl.ts` — never hardcode `:3000` in new specs.
  Canonical/CI stays `:3000`.
- **gh CLI has two accounts:** active `SpearheadAnalytica` (full write) and
  `david-catarious_kentro` (Kentro EMU — reads only; GitHub blocks EMU writes
  outside its enterprise). `gh auth switch --user <name>` to flip; `git push`
  authenticates as SpearheadAnalytica via GCM regardless.
- **Tooling not on default PATH:** `node.exe` + `gh.exe` live under
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages`. Run e2e via that `node.exe` +
  `e2e/node_modules/@playwright/test/cli.js`. Docker CLI needs
  `export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"` per shell.
  Host Node LTS is now 22 (matches the container after T4).
- **Prettier gate:** run `npx -y prettier@3.9.4 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"`
  from the repo root before every commit — CI enforces the same version.
- **Lint gate (new, T0):** the api compose service now read-only-mounts the root
  `./pyproject.toml` at `/pyproject.toml` so `docker compose exec -T api sh -lc
  "cd /app && ruff check --no-cache . && black --check ."` sees the ROOT config
  and reproduces CI exactly. This is in the runtime queue `gates` array.
- **Framework-bump reinstall dance:** after editing `apps/web/package.json`,
  reinstall INSIDE the web container, then `docker compose up -d
  --force-recreate web` before any e2e (next-dev hot-reload does not fire
  through the Windows bind mount).

## Deferred / needs a human

- **ESLint 10** — deferred upstream, not by choice: no published Next lint stack
  runs on ESLint 10 today (`eslint-plugin-react` 7.37.5 uses the removed
  `context.getFilename()`; Next's compiled babel parser hits an `eslint-scope`
  `scopeManager.addGlobals` gap). Revisit when `eslint-plugin-react` ships v10
  support. The D-018 "ESLint 10" line item is annotated accordingly.
- **14 `react-hooks` v6 rules disabled for parity** — the ESLint 9 flat-config
  migration (T3) preserved the exact prior rule set; the newer
  `eslint-plugin-react-hooks` v6 rules are disabled to hold parity rather than
  silently adopt them. Adopting them is a future task (a deliberate lint
  tightening, not a regression).
- **Two documented moderate audit findings** left deliberately open (Sprint 4
  T5, root `pnpm audit`): `postcss` 8.4.31 (pinned inside `next@15.5.20`;
  XSS-stringify path only on untrusted CSS, N/A at build time) and `uuid` 8.3.2
  (via `next-auth@4.24.14`; buffer-bounds bug is v3/v5/v6-only). Neither is
  overridden — forcing a bump risks regressing the e2e-validated stack for zero
  real security gain. Both clear on the upstream / Auth.js v5 bumps.
- **SMOKE_TEST §14 (live-AI):** David's pending item, independent of this
  sprint's close. Now provider-agnostic (T6 / D-024): set `SHIELD_LLM_MODE=live`
  + `SHIELD_LLM_PROVIDER=<anthropic|openai|gemini>` + that provider's key +
  a matching `SHIELD_LLM_MODEL`, run one Run-AI, confirm a redacted `llm_calls`
  row with the correct `provider`/`model`/`client_id` and no PII. Left unchecked
  (no committed spec can prove it, and fixture mode exercises no live path). If
  the run surfaces defects, triage them into a follow-up task.
- **Sprint 5 candidates — client-facing features:** deliverable
  release-to-client flow (D-023 notes Sprint 5 may deliberately reintroduce the
  release flow D-005/D-006 removed), `/home` value-loop card, POA&M step,
  redaction preview gate, `/admin/audit` viewer.
- **Needs David (infra):** `infra/terraform` (cloud/account/region/network) and
  DR runbooks are empty `.gitkeep` stubs — gated on David's cloud decisions.
  Real MFA + email-verification flows (flags fail loudly at boot, D-020).
  Auth.js v5 migration (not forced by T1). `azure_openai`/`bedrock`/`local` LLM
  adapters stay loud not-implemented until a deployment needs one.

## Test coverage status

- Backend: full `pytest -m unit` green in-container. Sprint 4 added
  `test_llm_providers.py` (11 tests): OpenAI + Gemini request shape / response
  parsing / token counts via monkeypatched `httpx`, missing-key loud raise,
  unimplemented-provider raise, HTTP 500 → `llm_calls` status=failed — no live
  calls. Fixture-mode determinism (D-017) untouched and green.
- Web: `tsc --noEmit` clean on Next 15 / React 19 / Tailwind 4. ESLint 9 flat
  config green with the 47-rule parity set.
- e2e: 34/34 green across 16 spec files (host, resolves `:3001`) on the new
  stack. The two stale-fetch races found this sprint (CsfPlaybookPanel s7,
  MessageThread s9) are fixed and now deterministic. Known cold-compile flake
  under load documented in `CLAUDE.md` — a re-run clears it.
- Format: repo-wide prettier `--check` clean at 3.9.4.
- Lint (Python): in-container ruff/black now see the root config (T0) and match
  CI — green at sprint close.
- Audit: root `pnpm audit` 0 critical / 0 high (2 documented moderates); `e2e/`
  `npm audit` 0 total.

## Lessons learned (Sprint 4)

- **The loop's gate must equal CI's gate, byte for byte.** Sprint 3's only red
  CI was 6 ruff/black findings the loop never saw because the api container
  mounted only `apps/api` and config discovery never reached the root
  `pyproject.toml`. T0 mounting the root config as the FIRST task protected every
  later commit — a gate that diverges from CI is not a gate.
- **Sequence one major per commit, full e2e each time.** Landing Next+React,
  Tailwind, ESLint, and Node as separate commits (T1→T2→T3→T4) meant every
  regression pointed at exactly one bump. Node deliberately went last so a Node
  failure could not be confounded with framework breakage.
- **Stale-fetch races hide behind slow mounts.** Two components
  (CsfPlaybookPanel, MessageThread) let a slow mount-time GET resolve after a
  user action and clobber fresh state. The full e2e suite surfaced both as
  deterministic failures once timing shifted under the new stack; the fix is a
  request-sequence guard where only the newest response writes state. Same class
  of bug, same fix — worth grepping for other mount-fetch-then-mutate patterns.
- **Defer honestly, in the log and the changelog.** ESLint 10 genuinely cannot
  run on any published Next lint stack today. The honest move was to land ESLint
  9 flat config (the real, runnable target) and annotate the D-018 "ESLint 10"
  line item as deferred-upstream — not to claim a version we can't actually run.
- **The provider seam was already there; keep the contract above it.** T6 added
  two live providers without touching redaction, the `llm_calls` audit row, or
  "AI suggests, code computes" — because the spec (§4.4) and config already put
  the provider choice below the egress seam. Thin httpx adapters that only
  translate prompt→REST→text, no SDK dependency, fixture mode still the default.
- **Leave audit moderates open on purpose, with the reasoning written down.**
  Overriding `postcss`/`uuid` transitives to chase a green `moderate` count would
  have risked the e2e-validated stack for bugs that don't fire in our use. Zero
  high/critical is the bar; documented, non-exploitable moderates stay open until
  the upstream bump arrives.
