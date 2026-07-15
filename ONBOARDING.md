# SHIELD — new developer onboarding (zero to sprint loop)

_One sitting, ~45 min (mostly Docker pulls). At the end you can run the full
e2e suite and launch the autonomous sprint loop. Durable project facts live in
`CLAUDE.md`; current state of `main` in `CONTEXT.md`; your personal status file
is `context/<your-name>.md` (create it from the template in `context/`)._

## 1. Prerequisites (install once)

| Tool           | How                                                       | Notes                                                                                                                                          |
| -------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Docker Desktop | docker.com installer                                      | The whole stack runs in compose; first `up` pulls ~2 GB                                                                                        |
| Node.js 22 LTS | `winget install OpenJS.NodeJS.LTS --scope user` (Windows) | Host-run Playwright + prettier. The stack runs Node 22 (Docker + CI); match it on the host. `--scope user` needs no admin; new shells get PATH |
| GitHub CLI     | `winget install GitHub.cli --scope user`                  | Then `gh auth login` → github.com → HTTPS → browser, with YOUR personal account                                                                |
| Git            | you have it                                               | Credential Manager stores your push identity on first push                                                                                     |

Windows PATH gotchas (this repo's docs assume them): Docker CLI is not on Git
Bash PATH (`export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"`
per shell); winget-installed node/gh land in new shells only.

If you have MULTIPLE GitHub accounts in gh (e.g. a corporate EMU + personal):
the active account can silently flip. `gh auth switch --user <your-login>`
before PR operations. EMU accounts cannot write to this repo at all.

## 2. Clone + stack up

```bash
git clone https://github.com/gene-png/SHIELD062626.git && cd SHIELD062626
docker compose up -d          # first run pulls images + installs web deps (minutes)
# wait until healthy:
curl http://localhost:8000/health
docker compose exec -T api python scripts/seed_demo.py   # idempotent demo seed
```

Web: http://localhost:3000 · API docs: :8000/docs · Keycloak :8080 ·
MinIO :9001 · MailHog :8025.
Logins: `admin@kentro.example` / `DemoPass!2026` (Kentro consultant),
`client@atlas.example` / `DemoPass!2026` (Atlas tenant).

**Port 3000 taken on your machine?** Create a root `.env` (gitignored) with
`WEB_PORT=3001` and `NEXTAUTH_URL=http://localhost:3001`, then
`docker compose up -d --force-recreate web`. Host-run e2e picks the port up
automatically (`e2e/helpers/baseUrl.ts`); CI and the committed defaults stay
on 3000.

**Need a clean slate?** `bash scripts/demo-reset.sh` (or
`powershell -ExecutionPolicy Bypass -File scripts/demo-reset.ps1`) runs
`docker compose down -v` → `up -d --build`, waits for the full-matrix `/ready`
probe to go all-green, reseeds the coherent Atlas demo (4 services + a
synthesized Risk Register, all released + downloadable), and prints the URLs +
logins. `down -v` **deletes all demo data** — that is the point.

**Hosted demo (production web build)?** Day-to-day dev uses the base compose
(`next dev`, hot-reload). For a shared demo host, add the override to run web as
a Next.js standalone production build:
`docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build`.
Fixture-mode by default; live AI only with a key + `SHIELD_LLM_MODE=live`.
Cloud/terraform is out of scope. See README → _Hosted-demo compose_.

## 3. e2e harness (host-run, not docker)

```bash
cd e2e
npm ci
npx playwright install chromium
npx playwright test smoke/s0-home.spec.ts   # 3-test sanity, ~2 min cold
```

Full suite: `npx playwright test` (~17–23 min, serialized against the shared
seeded DB). Known flake: next-dev cold-compile timeout under load — an
isolated re-run clears it. Full bring-up-from-scratch sequence: `e2e/README.md`.

## 4. The gate set (what must be green before any commit)

Six gates (the same array the sprint-loop queue carries) plus e2e:

```bash
# 1. backend unit tests (in-container):
docker compose exec -T api pytest -m unit -q
# 2. web typecheck (in-container):
docker compose exec -T web sh -lc "cd /app && pnpm -F web exec tsc --noEmit"
# 3. formatting (host; use the version pinned in pnpm-lock.yaml):
npx -y prettier@3.9.5 --check "**/*.{ts,tsx,js,jsx,json,md,yml,yaml}"
# 4. python lint/format (in-container, CI-parity — pins ruff==0.15.20 black==26.5.1):
docker compose exec -T api sh -lc "cd /app && ruff check --no-cache . && black --check ."
# 5. web unit tests (vitest, in-container):
docker compose exec -T web sh -lc "cd /app && pnpm -F web test"
# 6. web lint (in-container):
docker compose exec -T web sh -lc "cd /app && pnpm -F web lint"
# full e2e (host): cd e2e && npx playwright test
```

CI additionally runs **bandit** (`bandit -q -c pyproject.toml -r apps/api/app`)
and **gitleaks** — bandit findings need `# nosec BXXX` (ruff's `noqa` does not
suppress bandit).

## 5. Launching a sprint loop

Sprints are executed by an autonomous cron loop
(`.claude/commands/loop-sprint-cron.md` orchestrator dispatching fresh-context
agents per `.claude/commands/loop-sprint.md`). Each sprint ships a plan doc
(`SPRINT_<n>.md`) and a committed staged queue
(`.claude/sprint-queue.sprint-<n>.json`).

**The staged, ready-to-launch sprint is `SPRINT_7.md`** (queue
`.claude/sprint-queue.sprint-7.json`, branch `feat/gcp-vertex-sprint-7`,
target v3.4.0): Vertex-AI-via-ADC provider, release notification email,
dev MailHog delivery, reqSeq sweep, Auth.js v5.

1. Follow the sprint doc's launch checklist (`SPRINT_7.md` → _Prerequisites_).
2. Copy the staged queue to `.claude/sprint-queue.json` (gitignored — your
   machine-local runtime copy).
3. **Edit your runtime copy**: set `working_dir` to your absolute repo path
   and `expected_gh_user` to your GitHub login. The loop halts on either
   being wrong. Confirm the `gates` array's command strings match YOUR
   OS/Docker/Node layout — the six gates themselves are the invariant.
4. Create the sprint branch named in the queue, from `main`.
5. In Claude Code, run `/loop-sprint-cron`. It fires every ~10 min, one task
   per fire, checkpoints (full suite + audit) every 4 done. Watch
   `.claude/scheduler-debug.log`. Known babysitting duty: dispatched agents
   sometimes park on a background monitor mid-gate — nudge them to
   foreground-poll (the orchestrator usually does this for you).
6. The cron is session-scoped: if you close Claude Code, re-run
   `/loop-sprint-cron` to resume (queue state survives on disk; a `halt` in
   the queue explains any stop).

**Sprint 7 specific:** the live-AI tasks (T1) authenticate to Google Vertex
via **gcloud Application Default Credentials** — verify
`gcloud auth application-default print-access-token` works on your box before
launching (project `kentro-cloudmod-dev`, region `us-central1`). No API key
exists or is needed. Without ADC the live tasks self-skip and the loop stays
green — you just won't get the live validation payoff.

## 6. Collaboration rules (short version — full table in CLAUDE.md)

- Never commit to `main`; branch + PR, conventional commits, rich PR bodies.
- `CONTEXT.md` changes only inside a PR. Your `context/<name>.md` is yours
  alone; read others', never write them.
- Decisions get a D-number in `DECISIONS.md`, in the PR that makes them.
- SMOKE_TEST.md boxes are checked ONLY by a green committed spec, annotated
  with the spec filename.
- Dependabot: majors are suppressed by policy (D-018) — framework majors are
  sprint-planned, never auto-merged.
