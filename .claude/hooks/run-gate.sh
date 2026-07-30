#!/usr/bin/env bash
# run-gate.sh <commit|push>
#
# The single entry point every command and hook calls instead of naming a package manager.
# Reads .claude/profile, sources the matching file from pipeline/profiles/, and runs the
# steps for the requested phase.
#
# Why phases exist. ttx-engine's suite is 2288 tests and takes 6 minutes 2 seconds. A
# commit gate that costs six minutes gets bypassed within a day, and pipeline-design.md
# already names where that ends: an escape used routinely is the same as no gate. So the
# commit gate runs only what is fast, and the full suite runs at push, where waiting is
# expected and the cost is paid once per batch of commits rather than once per commit.
#
# Why a missing tool blocks rather than skips. A step that silently skips because its tool
# is absent reports success without checking, which is exactly the process-status failure
# the evidence rule exists to stop. It blocks once, names both fixes, and gets resolved.
#
# Per-repo override: .claude/profile.local, sourced after the profile, may redefine
# GATE_COMMIT or GATE_PUSH. ttx-engine has no ruff, so its local file drops that step
# rather than carrying a permanently red gate.

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$HOOK_DIR/lib.sh"

PHASE="${1:-commit}"
case "$PHASE" in commit|push) ;; *) refuse "run-gate.sh takes 'commit' or 'push', got '$PHASE'" ;; esac

ROOT="$(repo_root)"
[ -n "$ROOT" ] || allow
cd "$ROOT" || allow

PROFILE="$(repo_profile)"
if [ -z "$PROFILE" ] || [ "$PROFILE" = "none" ]; then
  warn "no .claude/profile in this repo, so no build gate ran."
  allow
fi

PROFILE_FILE="$HOOK_DIR/../profiles/$PROFILE.sh"
[ -f "$PROFILE_FILE" ] || refuse "this repo names profile '$PROFILE' but $PROFILE_FILE does not exist."

# shellcheck source=/dev/null
. "$PROFILE_FILE"
# shellcheck source=/dev/null
[ -f "$ROOT/.claude/profile.local" ] && . "$ROOT/.claude/profile.local"

case "$PHASE" in
  commit) STEPS="${GATE_COMMIT:-}" ;;
  push)   STEPS="${GATE_PUSH:-}" ;;
esac

[ -n "$STEPS" ] || allow

FAILED=""
MISSING=""
RAN=0

while IFS= read -r step; do
  [ -n "$step" ] || continue
  name="${step%%=*}"
  run="${step#*=}"

  # First word of the command is the tool. Resolve it before running.
  first="${run%% *}"
  resolved="$(tool "$first")"
  if [ -z "$resolved" ] && ! command -v "$first" >/dev/null 2>&1; then
    MISSING="$MISSING\n  $name  (needs '$first')"
    continue
  fi
  # Quote the resolved path before splicing it back in. The string goes through eval, and
  # on Windows npm resolves to /c/Program Files/nodejs/npm, so an unquoted substitution
  # made eval split on the space and report "/c/Program: No such file or directory" as a
  # lint failure. ttx-engine never saw it: python-app resolves through venv/Scripts, and
  # that path has no space. printf %q rather than hand-added quotes, so a path containing
  # any other shell metacharacter survives too.
  [ -n "$resolved" ] && run="$(printf '%q' "$resolved")${run#"$first"}"

  RAN=$((RAN+1))
  out="$(eval "$run" 2>&1)" || FAILED="$FAILED

--- $name ---
$(printf '%s' "$out" | tail -30)"
done <<EOF
$(printf '%s' "$STEPS")
EOF

if [ -n "$MISSING" ]; then
  refuse "the $PROFILE $PHASE gate declares steps whose tools are not installed:
$MISSING

Either install them into this repo's virtualenv, or drop the step by creating
.claude/profile.local with a narrowed GATE_$(printf '%s' "$PHASE" | tr '[:lower:]' '[:upper:]').

Refusing rather than skipping: a step that skips silently reports a pass it never checked."
fi

if [ -n "$FAILED" ]; then
  refuse "the $PROFILE $PHASE gate failed.$FAILED"
fi

printf 'gate: %s/%s passed (%s steps)\n' "$PROFILE" "$PHASE" "$RAN" >&2
allow
