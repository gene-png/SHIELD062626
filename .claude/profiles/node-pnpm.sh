#!/usr/bin/env bash
# Profile: node-pnpm
#
# Same phase split as node-app. What differs is the runner, and the reason it needs its own
# file rather than a branch inside node-app.sh is how run-gate.sh detects a missing tool.
#
# run-gate.sh resolves only the FIRST word of a step. In a pnpm workspace the root scripts
# are thin fan-outs: SHIELD062626's root `lint` is `pnpm -r run lint`. Written as
# `npm run lint`, the first word is `npm`, which exists, so the missing-tool check passes
# and the step runs anyway. pnpm is not installed on the D: machine, so the gate then
# reports a lint failure that is really an absent package manager. That is the exact
# failure the profiles README calls out: a gate reporting a code failure that never
# happened.
#
# Naming pnpm as the first word makes the check honest. When pnpm is absent the gate
# refuses with "needs 'pnpm'" and names the fix, instead of blaming the code.
#
# Use node-app for npm and node-pnpm for pnpm. Check packageManager in package.json, or
# which lockfile is present.

# No --silent, unlike node-app. npm consumes that flag itself; pnpm forwards trailing args
# to the script, so `pnpm -r run lint --silent` reached eslint as an unknown option and
# `tsc --noEmit --silent` failed with TS5023. Moving it to `pnpm --silent run lint` parses,
# but sets the silent reporter and swallows the per-package output, and the gate only
# prints anything at all when a step has already failed. Header noise on a passing run is
# cheaper than an unreadable failure.

GATE_COMMIT="lint=pnpm run lint
typecheck=pnpm run typecheck"

GATE_PUSH="lint=pnpm run lint
typecheck=pnpm run typecheck
build=pnpm run build
test=pnpm run test"
