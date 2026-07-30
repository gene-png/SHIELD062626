#!/usr/bin/env bash
# no-bulk-stage: refuse `git add -A`, `git add .`, and `git commit -a`. Always.
#
# Fires on PreToolUse, Bash.
#
# The reason this is unconditional: a bulk stage is the mechanism by which credentials
# reach history. Not the only one, but the common one, and the one that happens when an
# agent is finishing up and reaching for the quickest way to commit.
#
# Live examples from this account's own repos, all of which a bulk stage would have swept
# in: ProcurementAgentAI carries uncommitted .env.* files and Trello runtime state next to
# real work. Six repos hold untracked .claude/settings.local.json. proposal-companion and
# kentro-cloud-modernization hold runtime locks.
#
# Staging named paths costs a few seconds and makes the diff something a human chose.

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$HOOK_DIR/lib.sh"

PAYLOAD="$(read_payload)"
CMD="$(payload_command "$PAYLOAD")"
require_parsed "$CMD"

[ -n "$CMD" ] || allow

# Normalise runs of whitespace so `git   add   -A` matches too.
NORM="$(printf '%s' "$CMD" | tr -s '[:space:]' ' ')"

case "$NORM" in
  *"git add -A"*|*"git add --all"*|*"git add ."*|*"git add -u"*)
    refuse "bulk staging is refused. Stage named paths instead.

  git add path/to/file.ts path/to/other.ts

This repo has untracked runtime state and env files that a bulk stage would sweep into
the commit. Naming paths is what makes the diff something you chose."
    ;;
  *"git commit -a"*|*"git commit --all"*)
    refuse "\`git commit -a\` stages every tracked change without showing you the set.
Stage named paths, then commit."
    ;;
esac

allow
