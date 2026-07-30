# SHIELD — new developer onboarding (zero to sprint loop)

_One sitting, ~45 min (mostly Docker pulls). At the end you can run the full
e2e suite and launch the autonomous sprint loop. Durable project facts live in
`CLAUDE.md`; current state of `main` in `CONTEXT.md`; your personal status file
is `context/<your-name>.md` (create it from the template in `context/`)._

## 1. Prerequisites (install once)

| Tool           | How                                                       | Notes                                                                                                                                                                                     |
| -------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Docker Desktop | docker.com installer                                      | The whole stack runs in compose; first `up` pulls ~2 GB                                                                                                                                   |
| Node.js 22 LTS | `winget install OpenJS.NodeJS.LTS --scope user` (Windows) | Host-run Playwright + prettier. The stack runs Node 22 (Docker + CI); match it on the host. `--scope user` needs no admin; new shells get PATH                                            |
| GitHub CLI     | `winget install GitHub.cli --scope user`                  | Then `gh auth login` → github.com → HTTPS → browser, with YOUR personal account                                                                                                           |
| Git            | you have it                                               | Credential Manager stores your push identity on first push. Also set `git config --global user.name` / `user.email` — loop agents commit as you; the first commit fails without them      |
| Claude Code    | `npm install -g @anthropic-ai/claude-code`                | The sprint loop runs inside it — sign in with an account that has Opus-class model access. Babysit the first `/loop-sprint-cron` fire: it raises tool-permission prompts you must approve |

**Repo access first:** ask Gene (gene-png, repo owner) to add your GitHub
account as a collaborator with write access. Verify before launching anything:
`gh api repos/gene-png/SHIELD062626 --jq .permissions` — `push` must be `true`
(EMU/corporate accounts cannot write here at all; see below).

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

Sprints are executed by an autonomous loop, the skill at
`.claude/skills/loop-sprint-cron/SKILL.md`. It reads one plan file, the path
named in `.claude/sprint-plan`, and runs one backlog entry per fresh subagent
context. Each sprint still ships a narrative plan doc (`SPRINT_<n>.md`); the
executable form of it lives in `docs/SPRINTS.md`.

The JSON sprint queues this replaced are retired. `.claude/sprint-queue.sprint-3`
through `-9.json` remain in the tree as history only; nothing reads them.

**The staged, ready-to-launch backlog is `docs/SPRINTS.md`**, S1 through S11,
translated from `SPRINT_10.md` "Reports you can defend" (branch
`feat/defensible-reports-sprint-10`, target v3.6.0): shared export style module,
ATT&CK and CSF and ZT deliverable evidence, demo evidence depth, questionnaire
guidance, workspace comprehension, AI transparency, e2e proofs, prose scrub,
wrap-up. The plan was reviewed by OpenAI Codex before merge (PR #51 carries the
findings table). Convention: the staged sprint is the backlog in
`docs/SPRINTS.md`, and each planning PR bumps this paragraph.

**Launching the loop is a HUMAN action.** Agents stage the backlog but never
start `/loop-sprint-cron`. You, the dev at the keyboard, do that after walking
the checklist below.

1. Follow the launch checklist in `docs/SPRINTS.md` (_Loop protocol_) and the
   rationale in `SPRINT_10.md` (_Prerequisites_).
2. Set your identity, or the loop halts at its first push:
   `git config --local user.email "davidcatarious@spearheadanalytica.com"` and
   `gh auth switch --user SpearheadAnalytica`.
3. Confirm the gate runs on your box: `bash .claude/hooks/run-gate.sh commit`.
   It needs Docker Desktop running and the stack up (`docker compose up -d`),
   because every step except prettier runs inside the containers. The gate
   commands live in `.claude/profiles/shield.sh`, which is the one place to
   change them.
4. Create the sprint branch named in the backlog, from `main`.
5. **YOU (the human) run `/loop-sprint-cron start --account SpearheadAnalytica`
   in Claude Code.** Never ask an agent to start the loop (rule of the road, see
   `CLAUDE.md`). The driver arms a watchdog cron, runs one backlog entry per
   fresh runner, and runs a checkpoint (full gate plus security audit) every 4
   completed entries. Known babysitting duty: dispatched agents sometimes park
   on a background monitor mid-gate, so nudge them to foreground-poll.
6. The loop's state of record is the checkboxes and Log in `docs/SPRINTS.md`, so
   it survives session loss. `/loop-sprint-cron status` reports where it is, and
   `stop` shuts the watchdog down.

**Sprint 8 specific:** no cloud credentials or API keys are needed —
everything runs against the fixture-mode dev stack + MailHog (delivery is on
by default in dev compose since Sprint 7). Two things to know before your
first fire:

- T4 adds a TOTP dependency to `e2e/package.json`; after it lands, run
  `npm ci` inside `e2e/` on the **host** (the e2e harness is not
  containerized — no image rebuild involved).
- T1 deliberately re-contracts one pytest
  (`test_extract_versions_subsequent_lists`) — the sprint doc calls this out;
  it is a changed API contract, not a weakened test.

## 6. Collaboration rules (short version — full table in CLAUDE.md)

- Never commit to `main`; branch + PR, conventional commits, rich PR bodies.
- `CONTEXT.md` changes only inside a PR. Your `context/<name>.md` is yours
  alone; read others', never write them.
- Decisions get a D-number in `DECISIONS.md`, in the PR that makes them.
- SMOKE_TEST.md boxes are checked ONLY by a green committed spec, annotated
  with the spec filename.
- Dependabot: majors are suppressed by policy (D-018) — framework majors are
  sprint-planned, never auto-merged.
- Sprint planning PRs get a **read-only OpenAI Codex review** before merge
  (`npm i -g @openai/codex`, `codex login`, `codex exec --sandbox read-only`
  with the draft plan); fold findings in and table the verdict in the PR body
  (see PR #37 for the format). Codex reviews — it never authors.
