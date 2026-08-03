#!/usr/bin/env bash
# Shared helpers for the ops hooks.
#
# Sourced, never executed. Every function here is expected to work identically on Git Bash
# under Windows and on a Linux cloud sandbox, because the same repo is opened from both.
#
# Two portability rules learned the hard way:
#
#   1. `gh` does not exist in the Claude Code cloud sandbox. Verified 2026-07-29: the
#      environment has git, python3, node and jq, and no gh at all. A hook that shells out
#      to gh must degrade to a stated partial check, never fail open silently.
#
#   2. Paths differ. The Playwright cache lives at $HOME/.cache/ms-playwright on Linux and
#      $LOCALAPPDATA/ms-playwright on Windows. A check that knows only the Linux path
#      concludes "not installed" on every Windows session and reinstalls forever. That is
#      ttx-engine commit e38232c, and spearhead-business still carries the unfixed version.

set -uo pipefail

# --- output ------------------------------------------------------------------

# Hooks communicate with the model through stderr. Exit 2 blocks the tool call.
refuse() { printf 'BLOCKED: %s\n' "$*" >&2; exit 2; }
warn()   { printf 'warning: %s\n' "$*" >&2; }
allow()  { exit 0; }

# --- input -------------------------------------------------------------------
#
# A PreToolUse hook receives the tool call as JSON on stdin. Read it once; stdin cannot be
# read twice.
#
# The first version of this parsed with jq, and every blocking test failed open. jq is
# present in the Claude Code cloud sandbox and absent from Git Bash on Windows, so on the
# machine where the hooks were written they silently extracted an empty command and
# allowed `git add -A`, `git add .` and a Canmore identity pushing a Spearhead repo. The
# hooks ran, printed nothing, and enforced nothing.
#
# So: three extraction methods, and a sentinel when all three fail. A hook that cannot read
# its input must refuse, not shrug.

UNPARSEABLE='__UNPARSEABLE__'

read_payload() {
  local raw
  raw="$(cat 2>/dev/null || true)"
  [ -n "$raw" ] || raw='{}'
  printf '%s' "$raw"
}

# json_field <payload> <key>
# Extracts a string value from tool_input. Returns empty when the key is genuinely absent,
# and $UNPARSEABLE when the key is present but no method could read its value.
json_field() {
  local json="$1" key="$2" out=''

  if have jq; then
    out="$(printf '%s' "$json" | jq -r --arg k "$key" '.tool_input[$k] // ""' 2>/dev/null || printf '')"
    [ -n "$out" ] && { printf '%s' "$out"; return; }
  fi

  if have perl; then
    out="$(printf '%s' "$json" | perl "$(dirname "${BASH_SOURCE[0]}")/json-field.pl" "$key" 2>/dev/null || printf '')"
    [ -n "$out" ] && { printf '%s' "$out"; return; }
  fi

  # Last resort. Correct only when the value contains no escaped quote.
  out="$(printf '%s' "$json" | sed -n "s/.*\"$key\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1)"
  [ -n "$out" ] && { printf '%s' "$out"; return; }

  # Nothing extracted. Distinguish "key absent" from "key present, unreadable".
  if printf '%s' "$json" | grep -q "\"$key\"[[:space:]]*:"; then
    printf '%s' "$UNPARSEABLE"
  else
    printf ''
  fi
}

payload_command() { json_field "$1" command; }
payload_path()    {
  local p; p="$(json_field "$1" file_path)"
  [ -n "$p" ] && { printf '%s' "$p"; return; }
  json_field "$1" path
}

# Call immediately after extracting. Refuses when the payload existed and could not be read,
# because a guard that cannot see the command it is guarding is not a guard.
require_parsed() {
  [ "$1" = "$UNPARSEABLE" ] || return 0
  refuse "this hook could not parse the tool payload, so it cannot tell what is being run.
Refusing rather than allowing. Install jq, or check that perl is on PATH."
}

# --- platform ----------------------------------------------------------------

is_windows() {
  case "$(uname -s 2>/dev/null || echo unknown)" in
    MINGW*|MSYS*|CYGWIN*) return 0 ;;
    *) return 1 ;;
  esac
}

have() { command -v "$1" >/dev/null 2>&1; }

# Does the command actually INVOKE this tool, rather than merely mention it?
#
#   cmd_invokes "gh" "$NORM"        gh, as a command
#   cmd_invokes "git push" "$NORM"  git push, as a command
#
# Matching `*"gh "*` as a substring was wrong in both directions people hit. It fired on
# `grep -E "gh account|identity"`, on `echo "high "`, and on a commit message that mentions
# the tool, none of which run anything. Over-blocking is not the safe side of this trade:
# `pipeline-design.md` names a hook that cries wolf as the one that gets switched off, and
# a guard nobody runs protects nothing. It also fired on the hook's own remediation output.
#
# So split on shell separators and test the FIRST word of each segment. `gh auth switch`
# matches, `echo "gh account"` does not, and `foo && gh pr create` still matches because
# the separator starts a new segment.
cmd_invokes() {
  printf '%s' "$2" \
    | sed -E 's/(\|\||&&|[;|&()`\n])/\n/g' \
    | grep -qE "^[[:space:]]*(sudo[[:space:]]+)?$1([[:space:]]|\$)"
}

# --- repo config -------------------------------------------------------------

repo_root() { git rev-parse --show-toplevel 2>/dev/null || printf ''; }

# Which gate profile this repo uses. One word in .claude/profile, or empty.
# Externalising this is what lets one hook set serve a Next.js monorepo, a pytest project
# and a wiki without branching inside the hook.
repo_profile() {
  local root; root="$(repo_root)"
  [ -n "$root" ] || { printf ''; return; }
  if [ -f "$root/.claude/profile" ]; then
    grep -vE '^\s*(#|$)' "$root/.claude/profile" 2>/dev/null | head -1 | tr -d '[:space:]'
  else
    printf ''
  fi
}

# Which GitHub account is allowed to push this repo. One line in .claude/expected-owner.
# Falls back to parsing the origin remote, which is right often enough to be useful and
# wrong exactly when a remote was retargeted, which is the case worth catching.
expected_owner() {
  local root; root="$(repo_root)"
  if [ -n "$root" ] && [ -f "$root/.claude/expected-owner" ]; then
    grep -vE '^\s*(#|$)' "$root/.claude/expected-owner" 2>/dev/null | head -1 | tr -d '[:space:]'
    return
  fi
  git remote get-url origin 2>/dev/null \
    | sed -E 's#^git@[^:]+:##; s#^https://[^/]+/##; s#/.*$##; s#\.git$##' \
    || printf ''
}

# --- tool resolution ---------------------------------------------------------
#
# Tools live in the repo's virtualenv, not on PATH, and the directory differs by platform:
# venv/Scripts on Windows, venv/bin on Linux. ttx-engine on 2026-07-29 had pytest and mypy
# installed in venv/ and neither visible to `command -v`, so a gate resolving through PATH
# would have reported both missing and blocked every commit.
#
# The venv directory name also varies. ttx-engine uses venv/, most projects use .venv/.

venv_bin() {
  local root; root="$(repo_root)"
  [ -n "$root" ] || { printf ''; return; }
  for v in .venv venv env; do
    for d in Scripts bin; do
      [ -d "$root/$v/$d" ] && { printf '%s' "$root/$v/$d"; return; }
    done
  done
  printf ''
}

# Resolve a tool through the venv first, then PATH. Prints nothing when absent.
tool() {
  local name="$1" vb; vb="$(venv_bin)"
  if [ -n "$vb" ]; then
    for ext in "" ".exe"; do
      [ -x "$vb/$name$ext" ] && { printf '%s' "$vb/$name$ext"; return; }
    done
  fi
  command -v "$name" 2>/dev/null || printf ''
}

# The venv python, or the system one.
venv_python() {
  local vb; vb="$(venv_bin)"
  if [ -n "$vb" ]; then
    for c in python.exe python python3; do
      [ -x "$vb/$c" ] && { printf '%s' "$vb/$c"; return; }
    done
  fi
  command -v python3 2>/dev/null || command -v python 2>/dev/null || printf ''
}
