#!/usr/bin/env bash
# Profile: shield
#
# SHIELD is polyglot and containerized, which breaks both assumptions the generic profiles
# make. node-pnpm assumes a host pnpm; python-app assumes a host virtualenv. Neither is
# true here, and naming node-pnpm cost this repo two separate failures at once:
#
#   1. pnpm is not installed on the host. run-gate.sh resolves the first word of a step,
#      finds no pnpm, and refuses every commit with "needs 'pnpm'". The gate was not
#      loose, it was closed.
#   2. Even with pnpm present, node-pnpm declares no Python steps. CLAUDE.md requires
#      ruff and black before every commit touching apps/api, and records two red CI runs
#      caused by exactly that gap (Sprint 2 shipped unformatted files, Sprint 3 shipped
#      six ruff errors). A Node-only gate on a repo that is half Python is a gate that
#      reports green on unchecked code.
#
# So every step runs where the toolchain actually lives: inside the compose services. The
# first word is docker, which does resolve on this host, so the missing-tool check stays
# honest instead of blaming the code for an absent package manager.
#
# Prettier is the exception and runs on the host at the version the lockfile pins. CI runs
# 3.9.5, and a container's resolved version drifting from CI is how formatting failures
# reach a pull request. Pinning the host invocation makes local and CI agree by
# construction.
#
# The stack preflight runs first so a stopped Docker Desktop names itself as the cause at
# the top of the report. run-gate.sh runs every step regardless and collects all failures,
# so the raw npipe errors still follow it; the preflight buys the first readable line, not
# a short circuit.
#
# Phase split follows the pipeline rule: commit carries only what is fast, push carries the
# suites. pytest -m unit is 3 minutes on a quiet box and 13 to 16 under load, which is a
# push cost, never a per-commit one.
#
# NOT gated here, deliberately, and named rather than left silent:
#   e2e         Playwright, host-run, roughly 17 minutes, and it needs the web container
#               force-recreated after any apps/web edit plus a seeded database. CI's
#               fresh-runner E2E job is the authoritative run.
#   bandit      CI-only by decision. Note that ruff's `# noqa: S1xx` does not suppress it;
#               a flagged string needs its own `# nosec BXXX`.

STACK_PREFLIGHT="docker compose exec -T api true >/dev/null 2>&1 || { echo 'the SHIELD gate runs inside the dev stack, and it is not reachable. Start Docker Desktop, then: docker compose up -d'; exit 1; }"

GATE_COMMIT="stack=$STACK_PREFLIGHT
format=npx -y prettier@3.9.5 --check '**/*.{ts,tsx,js,jsx,json,md,yml,yaml}'
python=docker compose exec -T api sh -lc 'cd /app && ruff check --no-cache . && black --check .'
typecheck=docker compose exec -T web sh -lc 'cd /app && pnpm -F web exec tsc --noEmit'
lint=docker compose exec -T web sh -lc 'cd /app && pnpm -F web lint'"

GATE_PUSH="stack=$STACK_PREFLIGHT
format=npx -y prettier@3.9.5 --check '**/*.{ts,tsx,js,jsx,json,md,yml,yaml}'
python=docker compose exec -T api sh -lc 'cd /app && ruff check --no-cache . && black --check .'
typecheck=docker compose exec -T web sh -lc 'cd /app && pnpm -F web exec tsc --noEmit'
lint=docker compose exec -T web sh -lc 'cd /app && pnpm -F web lint'
webtest=docker compose exec -T web sh -lc 'cd /app && pnpm -F web test'
apitest=docker compose exec -T api pytest -m unit -q"
