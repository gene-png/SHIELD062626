#!/usr/bin/env bash
# Profile: node-app
#
# Commands run from the repo root. In a workspaces monorepo the root script is expected to
# fan out to every workspace; spearhead-business's own `npm run gate` already does.
#
# Build and test move to push. A commit gate that runs a full Next.js build is slow enough
# to get bypassed, and lint plus typecheck already catch the majority of what an agent
# gets wrong in a single commit.

GATE_COMMIT="lint=npm run lint --silent
typecheck=npm run typecheck --silent"

GATE_PUSH="lint=npm run lint --silent
typecheck=npm run typecheck --silent
build=npm run build --silent
test=npm test --silent"
